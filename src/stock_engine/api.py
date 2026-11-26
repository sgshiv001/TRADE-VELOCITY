"""Local React application's API. Run with one worker on the loopback interface."""

from dataclasses import asdict, dataclass, field
import asyncio
import csv
import hashlib
import json
import math
import os
import re
import sys
import sqlite3
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path
from threading import RLock
from typing import Annotated, Literal
from uuid import UUID, uuid4

from anyio import CancelScope
from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, WebSocket, WebSocketDisconnect
from fastapi.encoders import jsonable_encoder
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from starlette.concurrency import run_in_threadpool

from .companies import COMPANIES
from .account_summary import account_portfolio, order_journal
from .funded import refresh_virtual_depth, validate_limit
from .web_assets import app_pages, inline_script_hashes
from .analysis import analyze_history
from .analyst import stock_analysis
from .anomaly import detect_anomalies
from .experiments import compare_workload
from .market_data import SNAPSHOT_PATH, MarketData, MarketQuotes, download_market_data, history_metrics, indicators, load_market_data, market_rows, period_history, save_snapshot
from .session import ExchangeSession
from .storage import PostgresSessionStore, StorageError, create_store
from .watchdog import ExecutionMonitor
from .security import COOKIE, SecurityGuard, SecuritySettings, account_token
from .signup_verification import (BrevoEmail, DeliveryUnavailable, SignupVerification, VerificationRequired,
                                  VERIFICATION_SECONDS, normalize_email)

PROJECT_ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[2]))


class OrderRequest(BaseModel):
    symbol: str = Field(min_length=1, max_length=16, pattern=r"^[A-Za-z][A-Za-z0-9.&-]*$")
    side: Literal["BUY", "SELL"]
    quantity: int = Field(gt=0, le=1_000_000, strict=True)


class LabOrder(OrderRequest):
    order_id: str = Field(min_length=1, max_length=100)
    price: str | None = None
    confirmed: bool = False


class Modification(BaseModel):
    quantity: int = Field(gt=0, le=1_000_000, strict=True)
    price: str
    confirmed: bool = False


class Comparison(BaseModel):
    workload: Literal["mixed", "deep", "cancel"] = "deep"
    count: int = Field(default=1000, ge=100, le=10_000, strict=True)


class Review(BaseModel):
    status: Literal["open", "reviewed", "dismissed"]
    note: str = Field(default="", max_length=2000)


class Login(BaseModel):
    access_key: str = Field(min_length=1, max_length=1024)


class Credentials(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_]+$")
    password: str = Field(min_length=1, max_length=128)


class SignupContacts(BaseModel):
    username: str = Field(min_length=3, max_length=32, pattern=r"^[A-Za-z0-9_]+$")
    email: str = Field(min_length=3, max_length=254)


class Registration(Credentials):
    verification_token: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{43}$")
    email_code: str | None = Field(default=None, pattern=r"^[0-9]{6}$")


class Watchlist(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    symbols: list[Annotated[str, Field(pattern=r"^[A-Z][A-Z0-9.&-]{0,15}$")]] = Field(max_length=50)


class ProfileUpdate(BaseModel):
    revision: int = Field(ge=0, strict=True)
    name: str = Field(max_length=80)
    watchlists: list[Watchlist] = Field(min_length=1, max_length=12)


class PaperCredit(BaseModel):
    amount: int = Field(ge=1000, le=1000000, strict=True)


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
    needs_reload: bool = False
    account_data: dict = field(default_factory=dict)


def create_app(market: MarketData | None = None, data_dir: Path | None = None, serve_frontend: bool = True,
               security: SecuritySettings | None = None, database_url: str | None = None) -> FastAPI:
    app = FastAPI(title="TradeVelocity", version="2.0.0-beta.1", docs_url=None, redoc_url=None, openapi_url=None)
    settings = security or SecuritySettings.from_environment()
    app.state.data_dir = Path(data_dir) if data_dir is not None else Path(os.environ.get("TRADEVELOCITY_DATA_DIR",str(PROJECT_ROOT / ".marketlab" / "sessions")))
    app.state.store = store = create_store(app.state.data_dir, database_url)
    accounts = None
    signup_verification = None
    if settings.mode == "accounts":
        if not isinstance(store, PostgresSessionStore):
            raise ValueError("Hosted trader accounts require a PostgreSQL database")
        from .accounts import ACTIVE_SECONDS, FUNDED_BOOK, SHARED_BOOK, Accounts
        if os.getenv("TRADEVELOCITY_SIGNUP_OTP") == "1":
            signup_verification = SignupVerification(store, BrevoEmail.from_environment(),
                                                     os.getenv("TRADEVELOCITY_SIGNUP_OTP_SECRET", "").encode())
        accounts = Accounts(store, signup_verification)
    app.state.accounts = accounts
    app.state.security = guard = SecurityGuard(settings, accounts=accounts)
    app.middleware("http")(guard.protect)
    cached_market = app.state.data_dir.parent / "market-history.json"
    app.state.market = market if market is not None else load_market_data(cached_market if cached_market.exists() else SNAPSHOT_PATH)
    app.state.sessions = {}
    app.state.registry_lock = RLock()
    app.state.market_lock = RLock()
    quotes = MarketQuotes()
    admin_username = os.environ.get("TRADEVELOCITY_ADMIN_USERNAME", "").strip().lower()
    frontend = Path(os.environ.get("TRADEVELOCITY_WEB_DIR") or PROJECT_ROOT / "frontend" / "dist")
    pages = app_pages(frontend) if serve_frontend else {}
    if pages and settings.mode != "accounts":
        pages["/"] = pages["/app"]
    script_hashes = inline_script_hashes(frontend, pages) if serve_frontend else {}

    def is_admin(trader):
        return bool(trader and admin_username and trader.username == admin_username)

    @app.middleware("http")
    async def fresh_application_state(request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.startswith("/api/") or path in pages or path.endswith(".html"):
            response.headers["Cache-Control"] = "no-store"
        hashes = script_hashes.get(path)
        policy = response.headers.get("Content-Security-Policy")
        if hashes and policy and response.headers.get("Content-Type", "").startswith("text/html"):
            response.headers["Content-Security-Policy"] = policy.replace("script-src 'self';", f"script-src 'self' {hashes};")
        return response

    @app.exception_handler(ValueError)
    async def input_error(request, exc):
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(RequestValidationError)
    async def invalid_request(request: Request, exc: RequestValidationError):
        if request.url.path in ("/api/auth/login", "/api/auth/register", "/api/auth/device/login",
                                "/api/auth/device/register", "/api/auth/signup/start"):
            return JSONResponse(status_code=422, content={"detail": "Check your sign-in details and try again"})
        return await request_validation_exception_handler(request, exc)

    def metadata(session: Session):
        payload = {"reviews": session.reviews, "account_data": session.account_data}
        if session.legacy_account is not None:
            payload["broker"] = session.legacy_account
        return payload

    @app.exception_handler(sqlite3.Error)
    @app.exception_handler(OSError)
    @app.exception_handler(StorageError)
    async def storage_error(request, exc):
        return JSONResponse(status_code=503, content={"detail": "Workspace storage is unavailable. Check the database connection or local folder permissions."})

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
            if session.needs_reload:
                reload_session(session_id, session)
            if key:
                prior = app.state.store.receipt(session_id, key)
                if prior:
                    if prior[0] != fingerprint:
                        raise HTTPException(409, "This request key was already used for different inputs.")
                    return prior[1]
            before, count = session.lab, len(session.lab.events)
            reviews, monitor, account_data = session.reviews.copy(), session.monitor, session.account_data
            try:
                response = jsonable_encoder(operation())
                app.state.store.save(session_id, session.lab.events, metadata(session), session.revision + 1,
                                     replace_events=replace_events,
                                     receipt=(key, fingerprint, response) if key else None)
            except Exception as exc:
                # No reader sees uncommitted work: all session reads use this lock.
                session.lab = ExchangeSession.from_dict({"version": 2, "events": before.events[:count]}) if session.lab is before else before
                session.reviews, session.monitor = reviews, monitor
                session.account_data = account_data
                if isinstance(exc, (sqlite3.Error, OSError, StorageError)):
                    # A disconnected database can have committed before its acknowledgement was lost.
                    session.needs_reload = True
                    raise HTTPException(503, "Could not save this change. Check storage availability, then retry the same action.") from exc
                raise
            session.revision += 1
            notify(session)
            return response

    def fingerprint(action: str, payload=None):
        return hashlib.sha256(json.dumps([action, payload], sort_keys=True).encode()).hexdigest()

    def reload_session(session_id: str, session: Session):
        payload = app.state.store.load(session_id)
        if payload is None:
            raise HTTPException(404, "local session was not found")
        try:
            lab = ExchangeSession.from_dict(payload["lab"])
        except (KeyError, TypeError, ValueError) as exc:
            raise HTTPException(503, "Saved session is unreadable. Its records have been preserved; restore a valid export.") from exc
        session.lab = lab
        session.legacy_account = payload.get("broker")
        session.reviews = payload.get("reviews", {})
        session.account_data = payload.get("account_data", {})
        session.revision = payload.get("revision", 0)
        session.monitor = ExecutionMonitor()
        session.needs_reload = False
        notify(session)

    def load_session(x_session_id: str) -> tuple[str, Session]:
        try:
            session_id = str(UUID(x_session_id))
        except ValueError as exc:
            raise HTTPException(401, "invalid local session") from exc
        with app.state.registry_lock:
            session = app.state.sessions.get(session_id)
            if session is None:
                session = Session(needs_reload=True)
            with session.lock:
                if session.needs_reload:
                    reload_session(session_id, session)
            app.state.sessions[session_id] = session
            return session_id, session

    def get_session(request: Request, x_session_id: Annotated[str, Header()]) -> tuple[str, Session]:
        if accounts and request.state.trader.workspace_id != x_session_id:
            raise HTTPException(401, "Sign in to access this workspace")
        return load_session(x_session_id)

    SessionDependency = Annotated[tuple[str, Session], Depends(get_session)]

    def shared_context():
        if not accounts:
            raise HTTPException(404, "Shared trading is available in the hosted app")
        return load_session(SHARED_BOOK)

    def funded_context():
        if not accounts:
            raise HTTPException(404, "Funded trading is available in the hosted app")
        return load_session(FUNDED_BOOK)

    def is_funded(context):
        return bool(accounts and context[0] == FUNDED_BOOK)

    def order_owner(request: Request, context):
        return request.state.trader.workspace_id if accounts and context[0] in (SHARED_BOOK, FUNDED_BOOK) else None

    def session_for_orders(request: Request, private: SessionDependency):
        if request.url.path.startswith("/api/paper"):
            return funded_context()
        return shared_context() if request.url.path.startswith("/api/exchange") else private

    OrderBookDependency = Annotated[tuple[str, Session], Depends(session_for_orders)]

    def trader_trades(session, owner):
        trades = session.lab.engine.trades()
        if owner is None:
            return trades
        owners = session.lab.owners
        return [trade for trade in trades if owner in (owners.get(trade.buy_order_id), owners.get(trade.sell_order_id))]

    def private_key(owner, key):
        return f"{owner}:{key}" if owner and key else key

    def account_profile(session):
        return session.account_data.get("profile", {
            "revision": 0, "name": "", "watchlists": [{"name": "Watchlist", "symbols": []}],
        })

    @app.get("/api/account/profile")
    def profile(context: SessionDependency):
        with context[1].lock:
            return account_profile(context[1])

    @app.put("/api/account/profile")
    def update_profile(payload: ProfileUpdate, context: SessionDependency, key: RequestKey = None):
        names = [row.name.strip() for row in payload.watchlists]
        if any(not name for name in names) or len(set(name.casefold() for name in names)) != len(names):
            raise HTTPException(422, "Watchlist names must be nonempty and unique")
        watchlists = [{"name": name, "symbols": list(dict.fromkeys(row.symbols))}
                      for name, row in zip(names, payload.watchlists)]
        session = context[1]

        def update():
            if payload.revision != account_profile(session)["revision"]:
                raise HTTPException(409, "Your profile changed on another device. Reload before saving.")
            updated = {"revision": payload.revision + 1, "name": payload.name.strip(),
                       "watchlists": watchlists}
            session.account_data = {**session.account_data, "profile": updated}
            return updated

        return commit(context, update, fingerprint("profile", payload.model_dump()), key)

    @app.get("/api/account/portfolio")
    def portfolio(context: SessionDependency):
        owner, _ = context
        _, funded = funded_context()
        market = app.state.market
        references = quotes.current_marks()
        with funded.lock:
            data = account_portfolio(funded.lab, owner, market.marks(), funded_credits(funded, owner), references)
        return {**data, "market_as_of": market.as_of, "market_source": market.source}

    def funded_credits(session, owner):
        return session.account_data.get("credits", {}).get(owner, [])

    @app.post("/api/account/funds")
    def add_funds(payload: PaperCredit, context: SessionDependency, key: RequestKey = None):
        if not accounts:
            raise HTTPException(404, "The virtual wallet is available in the hosted app")
        if not key:
            raise HTTPException(400, "A request key is required to add virtual funds")
        owner, _ = context
        funded = funded_context()
        session = funded[1]

        def credit():
            previous = funded_credits(session, owner)
            if len(previous) >= 100:
                raise HTTPException(409, "The practice wallet has reached its top-up limit")
            entry = {"id": str(uuid4()), "amount": str(payload.amount),
                     "timestamp": datetime.now(timezone.utc).isoformat(), "description": "Virtual funds added"}
            credits = {**session.account_data.get("credits", {}), owner: [*previous, entry]}
            session.account_data = {**session.account_data, "credits": credits}
            return entry

        return commit(funded, credit, fingerprint("add-funds", payload.model_dump()), private_key(owner, key))

    @app.get("/api/account/notifications")
    def notifications(context: SessionDependency):
        owner, private = context
        _, shared = funded_context()
        with private.lock:
            read_through = private.account_data.get("notifications_read_through", 0)
        with shared.lock:
            fills = trader_trades(shared, owner)
        return {"unread": sum(trade.trade_id > read_through for trade in fills),
                "items": [{"id": trade.trade_id, "symbol": trade.symbol, "quantity": trade.quantity,
                           "price": float(trade.price), "timestamp": trade.timestamp,
                           "read": trade.trade_id <= read_through} for trade in reversed(fills[-100:])]}

    @app.post("/api/account/notifications/read")
    def read_notifications(context: SessionDependency, key: RequestKey = None):
        owner, private = context
        _, shared = funded_context()
        with shared.lock:
            fills = trader_trades(shared, owner)
            read_through = fills[-1].trade_id if fills else 0

        def mark():
            previous = private.account_data.get("notifications_read_through", 0)
            private.account_data = {**private.account_data,
                                    "notifications_read_through": max(previous, read_through)}
            return {"read_through": private.account_data["notifications_read_through"]}

        return commit(context, mark, fingerprint("read-notifications"), key)

    @app.get("/api/health")
    def health():
        return {"status": "ok", "application": "trade-velocity", "version": app.version, "execution": "local_matching_engine", "real_money": False, "storage": app.state.store.kind, "live_updates": True}

    @app.get("/api/ready")
    def ready():
        (accounts or store).check()
        return {"status": "ready", "storage": app.state.store.kind}

    @app.get("/api/auth/status")
    def auth_status(request: Request):
        if accounts:
            trader = accounts.identity(account_token(request.headers, request.cookies))
            return {"required": True, "mode": "accounts", "authenticated": trader is not None,
                    "signup_verification_required": signup_verification is not None,
                    "trader": {**asdict(trader), "admin": is_admin(trader)} if trader else None}
        return {"required":guard.settings.mode == "private", "authenticated":guard.authorized(request.headers,request.cookies)}

    @app.post("/api/auth/signup/start", status_code=201)
    def start_signup_verification(payload: SignupContacts, request: Request):
        if not signup_verification:
            raise HTTPException(404, "Signup verification is unavailable")
        email = normalize_email(payload.email)
        username = payload.username.lower()
        client = request.client.host if request.client else "unknown"
        if (guard.limited(client, "signup-codes", 12)
                or guard.limited(username, "signup-code-username", 1)
                or guard.limited(email, "signup-code-email", 1)):
            raise HTTPException(429, "Wait one minute before requesting a new code", headers={"Retry-After": "60"})
        if not accounts.initialized:
            accounts.check()
        try:
            token = signup_verification.start(username, email)
        except DeliveryUnavailable:
            raise HTTPException(503, "The verification email could not be sent. Try again shortly") from None
        return {"verification_token": token, "expires_in": VERIFICATION_SECONDS}

    def sign_in_account(payload: Credentials, request: Request, *, register: bool, device: bool = False):
        from .accounts import SESSION_LIFETIME

        if register and len(payload.password) < 12:
            raise HTTPException(400, "Use a password with at least 12 characters")
        username = payload.username.lower()
        client = request.client.host if request.client else "unknown"
        action = "register" if register else "sign-in"
        if guard.limited(client, action, 30) or guard.limited(username, "account-" + action, 8):
            raise HTTPException(429, "Too many attempts. Try again in one minute.", headers={"Retry-After": "60"})
        previous_token = account_token(request.headers, request.cookies)
        if register:
            verification_token = ""
            try:
                if signup_verification:
                    if not (isinstance(payload, Registration) and payload.verification_token and payload.email_code):
                        raise VerificationRequired("Verify your email to create an account")
                    verification_token = payload.verification_token
                    signup_verification.verify(username, verification_token, payload.email_code)
                token = accounts.register(username, payload.password, previous_token,
                                          verification_token=verification_token)
            except VerificationRequired as exc:
                raise HTTPException(400, str(exc)) from None
        else:
            token = accounts.login(username, payload.password, previous_token)
        if token is None:
            if register:
                if signup_verification:
                    raise HTTPException(409, "Could not create an account with those details")
                raise HTTPException(409, "Choose a different username")
            raise HTTPException(401, "Incorrect username or password")
        if device:
            return JSONResponse({"token": token, "expires_in": SESSION_LIFETIME}, status_code=201 if register else 200)
        response = JSONResponse({"authenticated": True}, status_code=201 if register else 200)
        response.set_cookie(COOKIE, token, max_age=SESSION_LIFETIME, secure=True, httponly=True, samesite="strict", path="/")
        return response

    @app.post("/api/auth/register")
    def register(payload: Registration, request: Request):
        if not accounts:
            raise HTTPException(404, "Account creation is available in the hosted app")
        return sign_in_account(payload, request, register=True)

    @app.post("/api/auth/device/{action}")
    def device_sign_in(action: Literal["login", "register"], payload: Registration, request: Request):
        if not accounts:
            raise HTTPException(404, "Device sign-in requires a hosted workspace")
        if "origin" in request.headers or any(key.startswith("sec-fetch-") for key in request.headers):
            raise HTTPException(403, "Use the browser sign-in form")
        return sign_in_account(payload, request, register=action == "register", device=True)

    @app.post("/api/auth/tutorial")
    def finish_tutorial(request: Request):
        if not accounts:
            raise HTTPException(404, "Tutorial preferences are stored in hosted accounts")
        accounts.finish_tutorial(request.state.trader)
        return {"tutorial_seen": True}

    @app.post("/api/auth/activity")
    def record_activity(request: Request):
        if not accounts:
            raise HTTPException(404, "Account activity is available in the hosted app")
        accounts.record_activity(request.state.trader)
        return {"recorded": True}

    @app.get("/api/admin/activity")
    def admin_activity(request: Request):
        if not accounts or not is_admin(request.state.trader):
            raise HTTPException(403, "Administrator access required")
        rows = accounts.activity()
        submitted, executions = {}, {}
        for _, session in (shared_context(), funded_context()):
            with session.lock:
                for owner in session.lab.owners.values():
                    submitted[owner] = submitted.get(owner, 0) + 1
                for trade in session.lab.engine.trades():
                    for owner in {session.lab.owners.get(trade.buy_order_id), session.lab.owners.get(trade.sell_order_id)}:
                        executions[owner] = executions.get(owner, 0) + 1
        return {"active_seconds": ACTIVE_SECONDS, "registered": len(rows),
                "active": sum(row[3] for row in rows), "active_today": sum(row[4] for row in rows),
                "users": [{"username": username, "last_active_at": last_active, "active": active,
                           "orders": submitted.get(workspace, 0), "executions": executions.get(workspace, 0)}
                          for username, workspace, last_active, active, _ in rows]}

    @app.post("/api/auth/login")
    def login(payload: Login | Credentials, request: Request):
        if accounts:
            if not isinstance(payload, Credentials):
                raise HTTPException(400, "Enter your username and password")
            return sign_in_account(payload, request, register=False)
        if guard.settings.mode == "local":
            raise HTTPException(404,"Sign-in is not enabled for the local app")
        if not isinstance(payload, Login):
            raise HTTPException(400, "Enter the workspace access key")
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
        if accounts:
            accounts.logout(account_token(request.headers, request.cookies))
        else:
            guard.revoke(request.cookies)
        response = JSONResponse({"authenticated":False})
        response.delete_cookie(COOKIE,secure=True,httponly=True,samesite="strict",path="/")
        return response

    @app.post("/api/session")
    def new_session(request: Request):
        if accounts:
            return {"session_id": request.state.trader.workspace_id}
        session_id = str(uuid4())
        session = Session()
        with app.state.registry_lock:
            app.state.store.save(session_id, [], metadata(session), 0)
            app.state.sessions[session_id] = session
        return {"session_id": session_id}

    @app.websocket("/api/live")
    async def live(websocket: WebSocket, session_id: str):
        async def allowed():
            if not accounts:
                return guard.authorized(websocket.headers, websocket.cookies)
            try:
                trader = await run_in_threadpool(accounts.identity, account_token(websocket.headers, websocket.cookies))
            except StorageError:
                return False
            return trader is not None and trader.workspace_id == session_id

        if (not guard.valid_host(websocket.headers) or not guard.valid_origin(websocket.headers)
                or not guard.local_client(websocket.client)
                or guard.limited(websocket.client.host if websocket.client else "unknown", "websocket", 600 if accounts else 60)
                or not await allowed()):
            await websocket.close(code=1008)
            return
        try:
            _, session = await run_in_threadpool(load_session, session_id)
            books = [(await run_in_threadpool(context))[1] for context in (shared_context, funded_context)] if accounts else []
        except (HTTPException, ValueError, sqlite3.Error, OSError, StorageError):
            await websocket.close(code=1008)
            return
        await websocket.accept()
        queue = asyncio.Queue(maxsize=1)
        shared_queue = asyncio.Queue(maxsize=1)
        listener = (asyncio.get_running_loop(), queue)
        shared_listener = (asyncio.get_running_loop(), shared_queue)
        with session.lock:
            session.listeners.append(listener)
            revision = session.revision
        for book in books:
            with book.lock:
                book.listeners.append(shared_listener)
        incoming = asyncio.create_task(websocket.receive_text())
        outgoing = asyncio.create_task(queue.get())
        shared_update = asyncio.create_task(shared_queue.get()) if books else None
        try:
            await websocket.send_json({"type": "connected", "revision": revision})
            while True:
                tasks = [incoming, outgoing] + ([shared_update] if shared_update else [])
                done, _ = await asyncio.wait(tasks, timeout=25, return_when=asyncio.FIRST_COMPLETED)
                if not await allowed():
                    await websocket.close(code=1008)
                    break
                if incoming in done:
                    incoming.result()  # Detect disconnects even when the session is idle.
                    incoming = asyncio.create_task(websocket.receive_text())
                if outgoing in done:
                    await websocket.send_json(outgoing.result())
                    outgoing = asyncio.create_task(queue.get())
                if shared_update in done:
                    await websocket.send_json({"type": "exchange_changed"})
                    shared_update = asyncio.create_task(shared_queue.get())
                if not done:
                    await websocket.send_json({"type": "heartbeat"})
        except WebSocketDisconnect:
            pass
        finally:
            with session.lock:
                session.listeners.remove(listener)
            for book in books:
                with book.lock:
                    book.listeners.remove(shared_listener)
            tasks = [incoming, outgoing] + ([shared_update] if shared_update else [])
            for task in tasks:
                task.cancel()
            # Disconnect teardown can cancel the request while it drains its
            # child tasks. Finish cleanup without suppressing request cancellation.
            with CancelScope(shield=True):
                await asyncio.gather(*tasks, return_exceptions=True)

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

    @app.get("/api/quote/{symbol}")
    def market_quote(symbol: str, request: Request):
        if not re.fullmatch(r"[A-Za-z][A-Za-z0-9.&-]{0,15}", symbol):
            raise HTTPException(400, "Enter a valid NSE symbol")
        symbol = symbol.upper()
        client = request.state.trader.username if accounts else "local"
        fetch_allowed = not guard.limited(client, "quotes", 30)
        quote = quotes.lookup(symbol, app.state.market, fetch_allowed=fetch_allowed)
        return {**quote, "simulation_supported": symbol in COMPANIES}

    @app.post("/api/paper/liquidity/{symbol}")
    def paper_liquidity(symbol: str, request: Request, context: OrderBookDependency,
                        follow: bool = False, key: RequestKey = None):
        symbol = symbol.upper()
        if symbol not in COMPANIES:
            raise HTTPException(404, "Simulated liquidity is available for supported market symbols")
        owner = order_owner(request, context)
        if guard.limited(owner, "paper-liquidity", 8):
            raise HTTPException(429, "Wait one minute before refreshing simulated liquidity")
        quote = quotes.lookup(symbol, app.state.market, fetch_allowed=True)
        if not quote["price"] or not quote["as_of"]:
            raise HTTPException(503, "A market reference price is unavailable")
        stamp = datetime.fromisoformat(quote["as_of"])
        age = (datetime.now(timezone.utc).date() - stamp.date()).days
        if not 0 <= age <= 7:
            raise HTTPException(503, "Refresh market data before generating simulated depth")
        session = context[1]
        price = Decimal(str(quote["price"])).quantize(Decimal("0.01"))
        result = {"symbol": symbol, "simulated": True, "reference_price": quote["price"],
                  "as_of": quote["as_of"], "source": quote["source"]}

        def timestamp(value):
            parsed = datetime.fromisoformat(value)
            return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)

        def update():
            refresh_virtual_depth(session.lab, symbol, price)
            references = session.account_data.get("maker_references", {})
            session.account_data = {**session.account_data, "maker_references": {
                **references, symbol: {"as_of": quote["as_of"], "price": str(price)},
            }}
            return {**result, "updated": True}

        with session.lock:
            if session.needs_reload:
                reload_session(context[0], session)
            prior = session.account_data.get("maker_references", {}).get(symbol)
            if prior:
                published_at, previous_at = timestamp(quote["as_of"]), timestamp(prior["as_of"])
                if published_at < previous_at or (
                    follow and published_at == previous_at and price == Decimal(prior["price"])
                ):
                    return {**result, "updated": False}
            payload = {"symbol": symbol, "follow": True} if follow else symbol
            return commit(context, update, fingerprint("liquidity", payload), private_key(owner, key))

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

    @app.get("/api/analyst/{symbol}")
    def analyst(symbol: str):
        try:
            return stock_analysis(app.state.market, symbol)
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

    @app.get("/api/paper")
    @app.get("/api/exchange")
    @app.get("/api/lab")
    def lab_state(request: Request, context: OrderBookDependency, symbol: str = "RELIANCE"):
        _, session = context
        owner = order_owner(request, context)
        with session.lock:
            orders = session.lab.engine.active_orders()
            trades = trader_trades(session, owner)
            if owner:
                orders = [order for order in orders if session.lab.owners.get(order["order_id"]) == owner]
            return {"symbols": session.lab.engine.symbols(), "orders": orders,
                    "book": session.lab.engine.order_book(symbol, 30), "stats": session.lab.engine.symbol_stats(symbol),
                    "trades": jsonable_encoder(trades[-100:]), "events": len(session.lab.events),
                    "total_trades": len(trades), "revision": session.revision}

    @app.get("/api/paper/order-history")
    @app.get("/api/exchange/order-history")
    @app.get("/api/lab/order-history")
    def orders_history(request: Request, context: OrderBookDependency, offset: int = Query(0, ge=0)):
        session = context[1]
        with session.lock:
            rows = order_journal(session.lab, order_owner(request, context))
        return {"total": len(rows), "orders": rows[offset:offset + 50]}

    @app.get("/api/exchange/watchdog")
    @app.get("/api/lab/watchdog")
    def lab_watchdog(request: Request, context: OrderBookDependency, symbol: str = Query(default="RELIANCE", min_length=1, max_length=16, pattern=r"^[A-Za-z][A-Za-z0-9.&-]*$")):
        _, session = context
        owner = order_owner(request, context)
        with session.lock:
            rows = [row.copy() for row in session.lab.observations if row["symbol"] == symbol.upper()
                    and (owner is None or session.lab.owners.get(row["order_id"]) == owner)]
            monitor, revision = session.monitor, session.revision
        result = monitor.report(rows, symbol)
        with session.lock:
            reviews = session.reviews.copy() if session.monitor is monitor else {}
        result["as_of_revision"] = revision
        result["alerts"] = [{**row, "review": reviews.get(str(row["event"]), {"status": "open", "note": ""})} for row in result["alerts"]]
        result["open_alerts"] = sum(row["review"]["status"] == "open" for row in result["alerts"])
        return result

    @app.patch("/api/exchange/watchdog/reviews/{event}")
    @app.patch("/api/lab/watchdog/reviews/{event}")
    def review_alert(event: int, review_data: Review, context: OrderBookDependency, request: Request,
                     symbol: str = "RELIANCE", key: RequestKey = None):
        session = context[1]
        report = lab_watchdog(request, context, symbol)
        if not any(row["event"] == event for row in report["alerts"]):
            raise HTTPException(404, "flagged execution was not found in the review queue")
        def change():
            if session.revision != report["as_of_revision"]:
                raise HTTPException(409, "Session changed. Refresh the review queue and try again.")
            review = review_data.model_dump()
            session.reviews[str(event)] = review
            return review
        return commit(context, change, fingerprint(f"review:{event}", review_data.model_dump()),
                      private_key(order_owner(request, context), key))

    @app.post("/api/paper/orders")
    @app.post("/api/exchange/orders")
    @app.post("/api/lab/orders")
    def lab_order(order: LabOrder, context: OrderBookDependency, request: Request, key: RequestKey = None):
        owner = order_owner(request, context)
        # Assign opaque IDs for the shared book; caller supplied IDs are for private sessions.
        order_id = f"TV-{uuid4()}" if owner else order.order_id
        session = context[1]
        def place():
            if is_funded(context):
                if not order.confirmed or not order.price or not key:
                    raise HTTPException(400, "Confirm a limit order before submitting it")
                validate_limit(session.lab, owner, order.symbol, order.side, order.quantity,
                               order.price, funded_credits(session, owner))
            return session.lab.place_order(order_id, order.symbol, order.side, order.quantity, order.price, owner=owner)
        payload = order.model_dump(exclude={"confirmed"} if not is_funded(context) else None)
        return commit(context, place, fingerprint("place", payload), private_key(owner, key))

    @app.delete("/api/paper/orders/{order_id}")
    @app.delete("/api/exchange/orders/{order_id}")
    @app.delete("/api/lab/orders/{order_id}")
    def cancel_lab_order(order_id: str, context: OrderBookDependency, request: Request, key: RequestKey = None):
        session = context[1]
        owner = order_owner(request, context)
        def cancel():
            if owner and session.lab.owners.get(order_id) != owner:
                raise HTTPException(404, "order is no longer active")
            if not session.lab.cancel_order(order_id):
                raise HTTPException(404, "order is no longer active")
            return {"canceled": order_id}
        return commit(context, cancel, fingerprint(f"cancel:{order_id}"), private_key(owner, key))

    @app.patch("/api/paper/orders/{order_id}")
    @app.patch("/api/exchange/orders/{order_id}")
    @app.patch("/api/lab/orders/{order_id}")
    def modify_lab_order(order_id: str, amendment: Modification, context: OrderBookDependency, request: Request, key: RequestKey = None):
        owner = order_owner(request, context)
        def modify():
            if owner and context[1].lab.owners.get(order_id) != owner:
                raise HTTPException(404, "order is no longer active")
            if is_funded(context):
                previous = context[1].lab.engine.get_order(order_id)
                if previous is None:
                    raise HTTPException(404, "order is no longer active")
                if not amendment.confirmed or not key:
                    raise HTTPException(400, "Confirm the amended order before submitting it")
                validate_limit(context[1].lab, owner, previous["symbol"], previous["side"], amendment.quantity,
                               amendment.price, funded_credits(context[1], owner), replacing=previous)
            try:
                return context[1].lab.modify_order(order_id, amendment.quantity, amendment.price)
            except KeyError as exc:
                raise HTTPException(404, "order is no longer active") from exc
        payload = amendment.model_dump(exclude={"confirmed"} if not is_funded(context) else None)
        return commit(context, modify, fingerprint(f"modify:{order_id}", payload), private_key(owner, key))

    @app.get("/api/paper/trades")
    @app.get("/api/exchange/trades")
    @app.get("/api/lab/trades")
    def trade_history(request: Request, context: OrderBookDependency, offset: int = Query(default=0, ge=0),
                      limit: int = Query(default=50, ge=1, le=1000), query: str = Query(default="", max_length=100)):
        _, session = context
        with session.lock:
            trades = trader_trades(session, order_owner(request, context))
            if query:
                needle = query.casefold()
                trades = [trade for trade in trades if needle in f"{trade.trade_id} {trade.symbol} {trade.buy_order_id} {trade.sell_order_id}".casefold()]
            return {"total": len(trades), "trades": jsonable_encoder(list(reversed(trades))[offset:offset + limit])}

    @app.get("/api/paper/trades/export")
    @app.get("/api/exchange/trades/export")
    @app.get("/api/lab/trades/export")
    def export_trades(request: Request, context: OrderBookDependency):
        _, session = context
        with session.lock:
            return jsonable_encoder(trader_trades(session, order_owner(request, context)))

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

    if serve_frontend and frontend.exists():
        @app.get("/")
        @app.get("/app")
        @app.get("/login")
        @app.get("/signup")
        @app.get("/download")
        def account_page(request: Request):
            return FileResponse(pages[request.url.path])
        app.mount("/", StaticFiles(directory=frontend, html=True), name="frontend")
    return app


app = create_app()
