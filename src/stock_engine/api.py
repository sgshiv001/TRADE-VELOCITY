"""Local React application's API. Run with one worker on the loopback interface."""

from dataclasses import asdict, dataclass, field
import csv
import json
import math
import sys
from pathlib import Path
from threading import RLock
from typing import Annotated, Literal
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from .companies import COMPANIES
from .analysis import analyze_history
from .anomaly import detect_anomalies
from .experiments import compare_workload
from .market_data import MarketData, download_market_data, history_metrics, indicators, load_market_data, market_rows, period_history, save_snapshot
from .portfolio import PaperBroker
from .session import ExchangeSession
from .watchdog import classroom_demo, report as watchdog_report, simulate

PROJECT_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))


class PaperOrder(BaseModel):
    symbol: str
    side: Literal["BUY", "SELL"]
    quantity: int = Field(gt=0, le=1_000_000, strict=True)


class LabOrder(PaperOrder):
    order_id: str = Field(min_length=1, max_length=100)
    price: str | None = None


class Modification(BaseModel):
    quantity: int = Field(gt=0, le=1_000_000, strict=True)
    price: str


class Comparison(BaseModel):
    workload: Literal["mixed", "deep", "cancel"] = "deep"
    count: int = Field(default=1000, ge=100, le=10_000, strict=True)


class Simulation(BaseModel):
    count: int = Field(default=500, ge=10, le=2000, strict=True)
    scenario: Literal["normal", "bull", "bear", "volatile", "low_liquidity", "high_liquidity"] = "normal"
    symbol: Literal["ACME", "TECH"] = "ACME"
    seed: int = Field(default=42, ge=0, le=1_000_000, strict=True)
    buy_probability: int = Field(default=50, ge=0, le=100, strict=True)
    market_percent: int = Field(default=10, ge=0, le=100, strict=True)


@dataclass
class Session:
    broker: PaperBroker
    lab: ExchangeSession = field(default_factory=ExchangeSession)
    lock: RLock = field(default_factory=RLock)


def seed_broker(data: MarketData) -> PaperBroker:
    broker = PaperBroker()
    for symbol, mark in data.marks().items():
        broker.seed_liquidity(symbol, mark)
    broker.record_equity(data.marks())
    return broker


def create_app(market: MarketData | None = None, data_dir: Path | None = None, serve_frontend: bool = True) -> FastAPI:
    app = FastAPI(title="TradeVelocity", version="0.3.0")
    app.state.market = market or load_market_data()
    app.state.sessions = {}
    app.state.registry_lock = RLock()
    app.state.data_dir = Path(data_dir) if data_dir is not None else PROJECT_ROOT / ".marketlab" / "sessions"

    @app.middleware("http")
    async def fresh_application_state(request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/") or request.url.path in ("/", "/index.html"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(ValueError)
    async def input_error(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    def persist(session_id: str, session: Session):
        directory = app.state.data_dir
        directory.mkdir(parents=True, exist_ok=True)
        target = directory / f"{session_id}.json"
        temporary = target.with_suffix(".tmp")
        temporary.write_text(json.dumps({"broker": session.broker.to_dict(), "lab": session.lab.to_dict()}), encoding="utf-8")
        temporary.replace(target)

    def get_session(x_session_id: Annotated[str, Header()]) -> tuple[str, Session]:
        try:
            session_id = str(UUID(x_session_id))
        except ValueError as exc:
            raise HTTPException(401, "invalid local session") from exc
        with app.state.registry_lock:
            if session_id not in app.state.sessions:
                path = app.state.data_dir / f"{session_id}.json"
                if not path.exists():
                    raise HTTPException(404, "local session was not found")
                payload = json.loads(path.read_text(encoding="utf-8"))
                app.state.sessions[session_id] = Session(PaperBroker.from_dict(payload["broker"]), ExchangeSession.from_dict(payload["lab"]))
            return session_id, app.state.sessions[session_id]

    SessionDependency = Annotated[tuple[str, Session], Depends(get_session)]

    def portfolio_payload(broker: PaperBroker) -> dict:
        return jsonable_encoder({**broker.valuation(app.state.market.marks()), "initial_cash": broker.initial_cash,
                                 "fills": broker.fills, "history": broker.equity_history,
                                 "source": app.state.market.source, "as_of": app.state.market.as_of,
                                 "is_demo": app.state.market.is_demo})

    @app.get("/api/health")
    def health():
        return {"status": "ok", "application": "trade-velocity"}

    @app.post("/api/session")
    def new_session():
        session_id = str(uuid4())
        session = Session(seed_broker(app.state.market))
        with app.state.registry_lock:
            app.state.sessions[session_id] = session
            persist(session_id, session)
        return {"session_id": session_id}

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
        return {"source": data.source, "as_of": data.as_of, "fetched_at": data.fetched_at, "is_demo": data.is_demo,
                "message": data.message, "companies": companies,
                "gainers": sum(company["day_change"] > 0 for company in companies),
                "losers": sum(company["day_change"] < 0 for company in companies),
                "basket_change": sum(company["day_change"] for company in companies) / len(companies)}

    @app.post("/api/market/refresh")
    def refresh_market():
        try:
            data = download_market_data()
            save_snapshot(data)
        except Exception as exc:
            raise HTTPException(503, "Market provider is unavailable. Your existing dated snapshot and portfolio were preserved.") from exc
        # Swap only after every company is complete; keep existing portfolios.
        app.state.market = data
        return market_overview()

    @app.get("/api/companies/{symbol}")
    def company_history(symbol: str, period: Literal["1M", "3M", "6M", "1Y", "5Y"] = "1Y"):
        symbol = symbol.upper()
        if symbol not in COMPANIES:
            raise HTTPException(404, "company was not found")
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
                "metrics": history_metrics(frame), "source": app.state.market.source, "is_demo": app.state.market.is_demo,
                "performance": [{"period": p, "return_pct": history_metrics(period_history(full, p))["growth_pct"]}
                                for p in ["1M", "3M", "6M", "1Y", "5Y"]],
                "basis": "Chart and growth use split/dividend-adjusted prices. Latest quote and portfolio marks use the raw daily bar."}

    @app.get("/api/analysis/{symbol}")
    def market_analysis(symbol: str, period: Literal["1M", "3M", "6M", "1Y", "5Y"] = "1Y"):
        try:
            return analyze_history(symbol, app.state.market.histories, period)
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc

    @app.get("/api/ai/anomalies/{symbol}")
    def anomaly_report(symbol: str, period: Literal["1M", "3M", "6M", "1Y", "5Y"] = "1Y"):
        """Return potentially anomalous activity for educational analysis."""

        try:
            return detect_anomalies(app.state.market.histories, symbol, period)
        except ValueError as exc:
            raise HTTPException(404, str(exc)) from exc

    @app.get("/api/portfolio")
    def portfolio(context: SessionDependency):
        _, session = context
        with session.lock:
            return portfolio_payload(session.broker)

    @app.post("/api/portfolio/orders")
    def paper_order(order: PaperOrder, context: SessionDependency):
        session_id, session = context
        symbol = order.symbol.upper()
        if symbol not in COMPANIES:
            raise HTTPException(400, "choose a company from the supported market")
        with session.lock:
            # Replenish synthetic makers using the latest available dated mark.
            session.broker.seed_liquidity(symbol, app.state.market.marks()[symbol])
            result = session.broker.place_market_order(symbol, order.side, order.quantity)
            session.broker.record_equity(app.state.market.marks())
            persist(session_id, session)
            return {"result": jsonable_encoder(result), "portfolio": portfolio_payload(session.broker)}

    @app.post("/api/portfolio/demo")
    def demo_portfolio(context: SessionDependency):
        session_id, session = context
        with session.lock:
            broker = seed_broker(app.state.market)
            for symbol, quantity in [("RELIANCE", 60), ("TCS", 30), ("INFY", 80), ("HDFCBANK", 100)]:
                frame = app.state.market.histories[symbol]
                row = frame.iloc[max(0, len(frame) - 91)]
                day = frame.index[max(0, len(frame) - 91)].strftime("%Y-%m-%d")
                broker.seed_liquidity(symbol, row["Close"])
                broker.place_market_order(symbol, "BUY", quantity, f"Demo fill at historical reference price from {day}; simulated purchase")
            for symbol, mark in app.state.market.marks().items():
                broker.seed_liquidity(symbol, mark)
            broker.record_equity(app.state.market.marks())
            session.broker = broker
            persist(session_id, session)
            return portfolio_payload(broker)

    @app.post("/api/portfolio/reset")
    def reset_portfolio(context: SessionDependency):
        session_id, session = context
        with session.lock:
            session.broker = seed_broker(app.state.market)
            persist(session_id, session)
            return portfolio_payload(session.broker)

    @app.get("/api/portfolio/export")
    def export_portfolio(context: SessionDependency):
        _, session = context
        with session.lock:
            return {"account": session.broker.to_dict(), "valuation": portfolio_payload(session.broker)}

    @app.get("/api/lab")
    def lab_state(context: SessionDependency, symbol: str = "ACME"):
        _, session = context
        with session.lock:
            return {"symbols": session.lab.engine.symbols(), "orders": session.lab.engine.active_orders(),
                    "book": session.lab.engine.order_book(symbol, 30), "stats": session.lab.engine.symbol_stats(symbol),
                    "trades": jsonable_encoder(session.lab.engine.trades(limit=100)), "events": len(session.lab.events),
                    "total_trades": len(session.lab.engine.trades())}

    @app.get("/api/lab/watchdog")
    def lab_watchdog(context: SessionDependency, symbol: Literal["ACME", "TECH"] = "ACME"):
        _, session = context
        with session.lock:
            return watchdog_report(session.lab, symbol)

    @app.post("/api/lab/watchdog/demo")
    def watchdog_demo(context: SessionDependency):
        session_id, session = context
        replacement, result = classroom_demo()
        with session.lock:
            session.lab = replacement
            persist(session_id, session)
        return result

    @app.post("/api/lab/simulate")
    def lab_simulate(request: Simulation, context: SessionDependency):
        session_id, session = context
        with session.lock:
            result = simulate(session.lab, **request.model_dump())
            persist(session_id, session)
            return result

    @app.post("/api/lab/orders")
    def lab_order(order: LabOrder, context: SessionDependency):
        session_id, session = context
        with session.lock:
            result = session.lab.place_order(order.order_id, order.symbol, order.side, order.quantity, order.price)
            persist(session_id, session)
            return jsonable_encoder(result)

    @app.delete("/api/lab/orders/{order_id}")
    def cancel_lab_order(order_id: str, context: SessionDependency):
        session_id, session = context
        with session.lock:
            if not session.lab.cancel_order(order_id):
                raise HTTPException(404, "order is no longer active")
            persist(session_id, session)
            return {"canceled": order_id}

    @app.patch("/api/lab/orders/{order_id}")
    def modify_lab_order(order_id: str, request: Modification, context: SessionDependency):
        session_id, session = context
        with session.lock:
            try:
                result = session.lab.modify_order(order_id, request.quantity, request.price)
            except KeyError as exc:
                raise HTTPException(404, "order is no longer active") from exc
            persist(session_id, session)
            return jsonable_encoder(result)

    @app.post("/api/lab/demo")
    def load_lab_demo(context: SessionDependency):
        session_id, session = context
        with session.lock:
            session.lab = ExchangeSession.from_file(PROJECT_ROOT / "scenarios" / "demo.json")
            persist(session_id, session)
            return {"events": len(session.lab.events)}

    @app.post("/api/lab/reset")
    def reset_lab(context: SessionDependency):
        session_id, session = context
        with session.lock:
            session.lab = ExchangeSession()
            persist(session_id, session)
            return {"events": 0}

    @app.get("/api/lab/export")
    def export_lab(context: SessionDependency):
        _, session = context
        with session.lock:
            return session.lab.to_dict()

    @app.post("/api/lab/import")
    def import_lab(payload: dict, context: SessionDependency):
        session_id, session = context
        replacement = ExchangeSession.from_dict(payload)
        with session.lock:
            session.lab = replacement
            persist(session_id, session)
            return {"events": len(replacement.events)}

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
