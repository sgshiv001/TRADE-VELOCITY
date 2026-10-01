"""Local React application's API. Run with one worker on the loopback interface."""

from dataclasses import asdict, dataclass, field
import asyncio
import csv
import hashlib
import json
import math
import os
import sys
import sqlite3
from pathlib import Path
from threading import RLock
from typing import Annotated, Literal
from uuid import UUID, uuid4

from anyio import CancelScope
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .companies import COMPANIES
from .analysis import analyze_history
from .anomaly import detect_anomalies
from .experiments import compare_workload
from .market_data import SNAPSHOT_PATH, MarketData, download_market_data, history_metrics, indicators, load_market_data, market_rows, period_history, save_snapshot
from .session import ExchangeSession
from .storage import SessionStore
from .watchdog import ExecutionMonitor
from .security import COOKIE, SecurityGuard, SecuritySettings

PROJECT_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))


class OrderRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=16, pattern=r"^[A-Za-z][A-Za-z0-9.]*$")
    side: Literal["BUY", "SELL"]
    quantity: int = Field(gt=0, le=1_000_000, strict=True)


class LabOrder(OrderRequest):
    order_id: str = Field(min_length=1, max_length=100)
    price: str | None = None


class Modification(BaseModel):
    quantity: int = Field(gt=0, le=1_000_000, strict=True)
    price: str


class Comparison(BaseModel):
    workload: Literal["mixed", "deep", "cancel"] = "deep"
    count: int = Field(default=1000, ge=100, le=10_000, strict=True)


class Review(BaseModel):
    status: Literal["open", "reviewed", "dismissed"]
    note: str = Field(default="", max_length=2000)


class Login(BaseModel):
    access_key: str = Field(min_length=1, max_length=1024)


RequestKey = Annotated[str | None, Header(alias="Idempotency-Key", min_length=1, max_length=100, pattern=r"^[A-Za-z0-9.:_-]+$")]


@dataclass
class Session:
    lab: ExchangeSession = field(default_factory=ExchangeSession)
    lock: RLock = field(default_factory=RLock)
    # Preserve old virtual-account records on disk, without operating that account.
    legacy_account: dict | None = None
    reviews: dict = field(default_factory=dict)
    revision: int = 0
    monitor: ExecutionMonitor = field(default_factory=ExecutionMonitor)
    listeners: list = field(default_factory=list)


def create_app(market: MarketData | None = None, data_dir: Path | None = None, serve_frontend: bool = True,
               security: SecuritySettings | None = None) -> FastAPI:
    app = FastAPI(title="TradeVelocity", version="0.3.3", docs_url=None, redoc_url=None, openapi_url=None)
    app.state.security = guard = SecurityGuard(security or SecuritySettings.from_environment())
    app.middleware("http")(guard.protect)
    app.state.data_dir = Path(data_dir) if data_dir is not None else Path(os.environ.get("TRADEVELOCITY_DATA_DIR",str(PROJECT_ROOT / ".marketlab" / "sessions")))
    cached_market = app.state.data_dir.parent / "market-history.json"
    app.state.market = market if market is not None else load_market_data(cached_market if cached_market.exists() else SNAPSHOT_PATH)
    app.state.sessions = {}
    app.state.registry_lock = RLock()
    app.state.store = SessionStore(app.state.data_dir)
    app.state.market_lock = RLock()

    @app.middleware("http")
    async def fresh_application_state(request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/") or request.url.path in ("/", "/index.html"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(ValueError)
    async def input_error(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    def metadata(session: Session):
        payload = {"reviews": session.reviews}
        if session.legacy_account is not None:
            payload["broker"] = session.legacy_account
        return payload

    @app.exception_handler(sqlite3.Error)
    async def storage_error(request, exc):
        return JSONResponse(status_code=503, content={"detail": "Local storage is unavailable. Check disk space and folder permissions."})

    def notify(session: Session):
        def latest(queue, update):
            if queue.full():
                queue.get_nowait()
            queue.put_nowait(update)
        for loop, queue in session.listeners:
            if not loop.is_closed():
                loop.call_soon_threadsafe(latest, queue, {"type": "changed", "revision": session.revision})

    def commit(context, operation, fingerprint: str, key: str | None = None, *, replace_events=False):
        session_id, session = context
        with session.lock:
            if key:
                prior = app.state.store.receipt(session_id, key)
                if prior:
                    if prior[0] != fingerprint:
                        raise HTTPException(409, "This request key was already used for different inputs.")
                    return prior[1]
            before, count = session.lab, len(session.lab.events)
            reviews, monitor = session.reviews.copy(), session.monitor
            try:
                response = jsonable_encoder(operation())
                app.state.store.save(session_id, session.lab.events, metadata(session), session.revision + 1,
                                     replace_events=replace_events,
                                     receipt=(key, fingerprint, response) if key else None)
            except Exception as exc:
                # No reader sees uncommitted work: all session reads use this lock.
                session.lab = ExchangeSession.from_dict({"version": 2, "events": before.events[:count]}) if session.lab is before else before
                session.reviews, session.monitor = reviews, monitor
                if isinstance(exc, (sqlite3.Error, OSError)):
                    raise HTTPException(503, "Could not save this change. Nothing was committed; check disk space and folder permissions, then retry.") from exc
                raise
            session.revision += 1
            notify(session)
            return response

    def fingerprint(action: str, payload=None):
        return hashlib.sha256(json.dumps([action, payload], sort_keys=True).encode()).hexdigest()

    def get_session(x_session_id: Annotated[str, Header()]) -> tuple[str, Session]:
        try:
            session_id = str(UUID(x_session_id))
        except ValueError as exc:
            raise HTTPException(401, "invalid local session") from exc
        with app.state.registry_lock:
            if session_id not in app.state.sessions:
                payload = app.state.store.load(session_id)
                if payload is None:
                    raise HTTPException(404, "local session was not found")
                try:
                    lab = ExchangeSession.from_dict(payload["lab"])
                except (KeyError, TypeError, ValueError) as exc:
                    raise HTTPException(503, "Saved session is unreadable. Its records have been preserved; restore a valid export.") from exc
                app.state.sessions[session_id] = Session(lab=lab, legacy_account=payload.get("broker"), reviews=payload.get("reviews", {}), revision=payload.get("revision", 0))
            return session_id, app.state.sessions[session_id]

    SessionDependency = Annotated[tuple[str, Session], Depends(get_session)]

    @app.get("/api/health")
    def health():
        return {"status": "ok", "application": "trade-velocity", "version": app.version, "execution": "local_matching_engine", "real_money": False, "storage": "sqlite", "live_updates": True}

    @app.get("/api/auth/status")
    def auth_status(request: Request):
        return {"required":guard.settings.mode == "private", "authenticated":guard.authorized(request.headers,request.cookies)}

    @app.post("/api/auth/login")
    def login(payload: Login, request: Request):
        if guard.settings.mode == "local":
            raise HTTPException(404,"Sign-in is not enabled for the local app")
        if guard.limited(request.client.host if request.client else "unknown", "login", 5):
            raise HTTPException(429,"Too many sign-in attempts; retry after one minute",headers={"Retry-After":"60"})
        token = guard.issue(payload.access_key)
        if not token:
            raise HTTPException(401,"Access key is invalid")
        response = JSONResponse({"authenticated":True})
        response.set_cookie(COOKIE,token,max_age=8*60*60,secure=True,httponly=True,samesite="strict",path="/")
        return response

    @app.post("/api/auth/logout")
    def logout(request: Request):
        guard.revoke(request.cookies)
        response = JSONResponse({"authenticated":False})
        response.delete_cookie(COOKIE,secure=True,httponly=True,samesite="strict",path="/")
        return response

    @app.post("/api/session")
    def new_session():
        session_id = str(uuid4())
        session = Session()
        with app.state.registry_lock:
            app.state.store.save(session_id, [], metadata(session), 0)
            app.state.sessions[session_id] = session
        return {"session_id": session_id}

    @app.websocket("/api/live")
    async def live(websocket: WebSocket, session_id: str):
        if (not guard.valid_host(websocket.headers) or not guard.valid_origin(websocket.headers)
                or not guard.local_client(websocket.client)
                or not guard.authorized(websocket.headers,websocket.cookies)
                or guard.limited(websocket.client.host if websocket.client else "unknown", "websocket", 60)):
            await websocket.close(code=1008)
            return
        try:
            _, session = get_session(session_id)
        except (HTTPException, ValueError, sqlite3.Error, OSError):
            await websocket.close(code=1008)
            return
        await websocket.accept()
        queue = asyncio.Queue(maxsize=1)
        listener = (asyncio.get_running_loop(), queue)
        with session.lock:
            session.listeners.append(listener)
            revision = session.revision
        incoming = asyncio.create_task(websocket.receive_text())
        outgoing = asyncio.create_task(queue.get())
        try:
            await websocket.send_json({"type": "connected", "revision": revision})
            while True:
                done, _ = await asyncio.wait([incoming, outgoing], timeout=25, return_when=asyncio.FIRST_COMPLETED)
                if not guard.authorized(websocket.headers,websocket.cookies):
                    await websocket.close(code=1008)
                    break
                if incoming in done:
                    incoming.result()  # Detect disconnects even when the session is idle.
                    incoming = asyncio.create_task(websocket.receive_text())
                if outgoing in done:
                    await websocket.send_json(outgoing.result())
                    outgoing = asyncio.create_task(queue.get())
                if not done:
                    await websocket.send_json({"type": "heartbeat"})
        except WebSocketDisconnect:
            pass
        finally:
            with session.lock:
                session.listeners.remove(listener)
            for task in (incoming, outgoing):
                task.cancel()
            # Disconnect teardown can cancel the request while it drains its
            # child tasks. Finish cleanup without suppressing request cancellation.
            with CancelScope(shield=True):
                await asyncio.gather(incoming, outgoing, return_exceptions=True)

    @app.get("/api/market")
    def market_overview():
        data = app.state.market
        rows = market_rows(data)
        companies = []
        for row in rows:
            company = COMPANIES[row["Symbol"]]
            frame = data.histories[company.symbol]
            companies.append({**asdict(company), "ticker": company.ticker, "quote_url": company.quote_url,
                              "price": row["Price (₹)"], "day_change": row["Day %"], "year_growth": row["1Y growth %"],
                              "volume": row["Volume"], "as_of": row["As of"],
                              "sparkline": [float(value) for value in frame["Adj Close"].tail(30)]})
        changes = [company["day_change"] for company in companies if company["day_change"] is not None]
        return {"source": data.source, "as_of": data.as_of, "fetched_at": data.fetched_at,
                "message": data.message, "companies": companies,
                "gainers": sum(value > 0 for value in changes),
                "losers": sum(value < 0 for value in changes),
                "available": bool(companies),
                "basket_change": sum(changes) / len(changes) if changes else None}

    @app.post("/api/market/refresh")
    def refresh_market():
        with app.state.market_lock:
            try:
                data = download_market_data()
                save_snapshot(data, app.state.data_dir.parent / "market-history.json")
            except Exception as exc:
                raise HTTPException(503, "Market provider is unavailable. Existing market history and matching orders were preserved.") from exc
            app.state.market = data
        return market_overview()

    @app.get("/api/companies/{symbol}")
    def company_history(symbol: str, period: Literal["1M", "3M", "6M", "1Y", "5Y"] = "1Y"):
        symbol = symbol.upper()
        if symbol not in COMPANIES:
            raise HTTPException(404, "company was not found")
        if symbol not in app.state.market.histories:
            raise HTTPException(503, "Market history is unavailable. Refresh the provider data.")
        full = indicators(app.state.market.histories[symbol])
        frame = period_history(full, period)
        history = []
        for date, row in frame.iterrows():
            ratio = row["Adj Close"] / row["Close"]
            finite = lambda value: float(value) if math.isfinite(value) else None
            history.append({"date": date.strftime("%Y-%m-%d"), "open": float(row["Open"] * ratio),
                            "high": float(row["High"] * ratio), "low": float(row["Low"] * ratio),
                            "close": float(row["Adj Close"]), "raw_close": float(row["Close"]),
                            "volume": int(row["Volume"]), "ma20": finite(row["MA20"]), "ma50": finite(row["MA50"]),
                            "rsi": finite(row["RSI14"]), "drawdown": finite(row["Drawdown %"])})
        return {"company": asdict(COMPANIES[symbol]), "period": period, "history": history,
                "metrics": history_metrics(frame), "source": app.state.market.source,
                "performance": [{"period": p, "return_pct": history_metrics(period_history(full, p))["growth_pct"]}
                                for p in ["1M", "3M", "6M", "1Y", "5Y"]],
                "basis": "Chart and growth use split/dividend-adjusted prices. The last daily close uses the raw provider bar; engine orders are separate."}

    @app.get("/api/analysis/{symbol}")
    def market_analysis(symbol: str, period: Literal["1M", "3M", "6M", "1Y", "5Y"] = "1Y"):
        if symbol.upper() in COMPANIES and symbol.upper() not in app.state.market.histories:
            raise HTTPException(503, "Market history is unavailable. Refresh the provider data.")
        try:
            return analyze_history(symbol, app.state.market.histories, period)
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc

    @app.get("/api/ai/anomalies/{symbol}")
    def anomaly_report(symbol: str, period: Literal["1M", "3M", "6M", "1Y", "5Y"] = "1Y"):
        """Analyze dated observations; scores are not fraud probabilities."""

        if symbol.upper() in COMPANIES and symbol.upper() not in app.state.market.histories:
            raise HTTPException(503, "Market history is unavailable. Refresh the provider data.")
        try:
            return detect_anomalies(app.state.market.histories, symbol, period)
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc

    @app.get("/api/lab")
    def lab_state(context: SessionDependency, symbol: str = "RELIANCE"):
        _, session = context
        with session.lock:
            return {"symbols": session.lab.engine.symbols(), "orders": session.lab.engine.active_orders(),
                    "book": session.lab.engine.order_book(symbol, 30), "stats": session.lab.engine.symbol_stats(symbol),
                    "trades": jsonable_encoder(session.lab.engine.trades(limit=100)), "events": len(session.lab.events),
                    "total_trades": len(session.lab.engine.trades()), "revision": session.revision}

    @app.get("/api/lab/watchdog")
    def lab_watchdog(context: SessionDependency, symbol: str = Query(default="RELIANCE", min_length=1, max_length=16, pattern=r"^[A-Za-z][A-Za-z0-9.]*$")):
        _, session = context
        with session.lock:
            rows = [row.copy() for row in session.lab.observations if row["symbol"] == symbol.upper()]
            monitor, revision = session.monitor, session.revision
        result = monitor.report(rows, symbol)
        with session.lock:
            reviews = session.reviews.copy() if session.monitor is monitor else {}
        result["as_of_revision"] = revision
        result["alerts"] = [{**row, "review": reviews.get(str(row["event"]), {"status": "open", "note": ""})} for row in result["alerts"]]
        result["open_alerts"] = sum(row["review"]["status"] == "open" for row in result["alerts"])
        return result

    @app.patch("/api/lab/watchdog/reviews/{event}")
    def review_alert(event: int, request: Review, context: SessionDependency, symbol: str = "RELIANCE", key: RequestKey = None):
        session = context[1]
        report = lab_watchdog(context, symbol)
        if not any(row["event"] == event for row in report["alerts"]):
            raise HTTPException(404, "flagged execution was not found in the review queue")
        def change():
            if session.revision != report["as_of_revision"]:
                raise HTTPException(409, "Session changed. Refresh the review queue and try again.")
            review = request.model_dump()
            session.reviews[str(event)] = review
            return review
        return commit(context, change, fingerprint(f"review:{event}", request.model_dump()), key)

    @app.post("/api/lab/orders")
    def lab_order(order: LabOrder, context: SessionDependency, key: RequestKey = None):
        return commit(context, lambda: context[1].lab.place_order(order.order_id, order.symbol, order.side, order.quantity, order.price), fingerprint("place", order.model_dump()), key)

    @app.delete("/api/lab/orders/{order_id}")
    def cancel_lab_order(order_id: str, context: SessionDependency, key: RequestKey = None):
        session = context[1]
        def cancel():
            if not session.lab.cancel_order(order_id):
                raise HTTPException(404, "order is no longer active")
            return {"canceled": order_id}
        return commit(context, cancel, fingerprint(f"cancel:{order_id}"), key)

    @app.patch("/api/lab/orders/{order_id}")
    def modify_lab_order(order_id: str, request: Modification, context: SessionDependency, key: RequestKey = None):
        def modify():
            try:
                return context[1].lab.modify_order(order_id, request.quantity, request.price)
            except KeyError as exc:
                raise HTTPException(404, "order is no longer active") from exc
        return commit(context, modify, fingerprint(f"modify:{order_id}", request.model_dump()), key)

    @app.get("/api/lab/trades")
    def trade_history(context: SessionDependency, offset: int = Query(default=0, ge=0),
                      limit: int = Query(default=50, ge=1, le=1000), query: str = Query(default="", max_length=100)):
        _, session = context
        with session.lock:
            trades = session.lab.engine.trades()
            if query:
                needle = query.casefold()
                trades = [trade for trade in trades if needle in f"{trade.trade_id} {trade.symbol} {trade.buy_order_id} {trade.sell_order_id}".casefold()]
            return {"total": len(trades), "trades": jsonable_encoder(list(reversed(trades))[offset:offset + limit])}

    @app.get("/api/lab/trades/export")
    def export_trades(context: SessionDependency):
        _, session = context
        with session.lock:
            return jsonable_encoder(session.lab.engine.trades())

    @app.post("/api/lab/reset")
    def reset_lab(context: SessionDependency, key: RequestKey = None):
        session = context[1]
        def reset():
            session.lab = ExchangeSession()
            session.reviews = {}
            session.monitor = ExecutionMonitor()
            return {"events": 0}
        return commit(context, reset, fingerprint("reset"), key, replace_events=True)

    @app.get("/api/lab/export")
    def export_lab(context: SessionDependency):
        _, session = context
        with session.lock:
            return session.lab.to_dict()

    @app.post("/api/lab/import")
    def import_lab(payload: dict, context: SessionDependency, key: RequestKey = None):
        session = context[1]
        if isinstance(payload.get("events"), list) and len(payload["events"]) > 100_000:
            raise HTTPException(400, "Session import is limited to 100,000 commands.")
        replacement = ExchangeSession.from_dict(payload)
        def restore():
            session.lab = replacement
            session.reviews = {}
            session.monitor = ExecutionMonitor()
            return {"events": len(replacement.events)}
        return commit(context, restore, fingerprint("import", payload), key, replace_events=True)

    @app.get("/api/experiments")
    def recorded_experiments():
        output = {}
        for key, name in [("scaling", "custom-structures.csv"), ("comparison", "comparison.csv")]:
            path = PROJECT_ROOT / "benchmarks" / name
            if path.exists():
                with path.open(encoding="utf-8", newline="") as source:
                    output[key] = list(csv.DictReader(source))
            else:
                output[key] = []
        return output

    @app.post("/api/experiments")
    def run_experiment(request: Comparison):
        return compare_workload(request.workload, request.count)

    if serve_frontend:
        frontend = PROJECT_ROOT / "frontend" / "dist"
        if frontend.exists():
            app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
    return app


app = create_app()
