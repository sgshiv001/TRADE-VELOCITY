"""Origin validation and access controls for local and hosted workspaces."""
from collections import deque
from dataclasses import dataclass
import hashlib
import hmac
import ipaddress
import os
import secrets
from threading import RLock
from time import monotonic
from urllib.parse import urlsplit

from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.concurrency import run_in_threadpool

from .storage import StorageError

COOKIE = "__Host-tradevelocity-access"
MAX_BODY = 8 * 1024 * 1024


def account_token(headers, cookies):
    authorization = headers.get("authorization", "")
    if authorization.startswith("Bearer "):
        return authorization[7:]
    return cookies.get(COOKIE, "")


@dataclass(frozen=True)
class SecuritySettings:
    mode: str = "local"
    origin: str = ""
    access_key: str = ""

    def __post_init__(self):
        if self.mode not in ("local", "private", "accounts"):
            raise ValueError("TRADEVELOCITY_MODE must be local, private or accounts")
        if self.mode != "local":
            parsed = urlsplit(self.origin)
            if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
                    or parsed.path not in ("", "/") or parsed.query or parsed.fragment):
                raise ValueError("Hosting requires one valid HTTPS TRADEVELOCITY_ORIGIN")
            if self.mode == "private" and (len(self.access_key) < 32 or self.access_key.startswith("REPLACE_")):
                raise ValueError("Private hosting requires a TRADEVELOCITY_ACCESS_KEY of at least 32 characters")
            if self.mode == "accounts" and self.access_key:
                raise ValueError("Workspace access keys are only supported in private mode")
        elif self.access_key or self.origin:
            raise ValueError("Access keys/origins require explicit private hosting mode")

    @classmethod
    def from_environment(cls):
        mode = os.environ.get("TRADEVELOCITY_MODE", "local")
        origin = os.environ.get("TRADEVELOCITY_ORIGIN")
        if origin is None and mode == "accounts":
            origin = os.environ.get("RENDER_EXTERNAL_URL", "")
        return cls(mode, (origin or "").rstrip("/"),
                   os.environ.get("TRADEVELOCITY_ACCESS_KEY", ""))


class SecurityGuard:
    def __init__(self, settings: SecuritySettings, clock=monotonic, accounts=None):
        self.settings, self.clock = settings, clock
        self.accounts = accounts
        self.lock, self.tokens, self.windows = RLock(), {}, {}

    def valid_host(self, headers):
        try:
            parsed = urlsplit("//" + headers.get("host", ""))
            hostname = parsed.hostname
            _ = parsed.port  # Validate port syntax/range, including bracketed IPv6.
            if parsed.username or parsed.password or parsed.path or parsed.query or parsed.fragment:
                return False
        except ValueError:
            return False
        if self.settings.mode != "local":
            return headers.get("host", "").lower() == urlsplit(self.settings.origin).netloc.lower()
        return hostname in ("127.0.0.1", "localhost", "::1", "testserver")

    def valid_origin(self, headers):
        origin = headers.get("origin")
        if not origin:  # CLI/API clients do not send browser Origin headers.
            return True
        if self.settings.mode != "local":
            return origin == self.settings.origin
        return origin in (f"http://{headers.get('host', '')}", f"https://{headers.get('host', '')}")

    def local_client(self, client):
        if self.settings.mode != "local" or not client:
            return True
        if client.host == "testclient":  # Starlette's in-process transport.
            return True
        try:
            return ipaddress.ip_address(client.host).is_loopback
        except ValueError:
            return False

    def limited(self, identifier, category, maximum, period=60):
        now = self.clock()
        with self.lock:
            if len(self.windows) >= 10000:
                self.windows = {key:values for key,values in self.windows.items() if values and values[-1] > now-period}
                if len(self.windows) >= 10000:
                    return True  # Fail closed rather than grow without bound.
            values = self.windows.setdefault((identifier,category), deque())
            while values and values[0] <= now-period:
                values.popleft()
            if len(values) >= maximum:
                return True
            values.append(now)
        return False

    def authorized(self, headers, cookies):
        if self.settings.mode == "local":
            return True
        if self.settings.mode == "accounts":
            return False  # Account requests use a database-backed identity.
        bearer = headers.get("authorization", "")
        if bearer.startswith("Bearer ") and hmac.compare_digest(bearer[7:].encode(), self.settings.access_key.encode()):
            return True
        digest = hashlib.sha256(cookies.get(COOKIE, "").encode()).hexdigest()
        with self.lock:
            expiry = self.tokens.get(digest, 0)
        return expiry > self.clock()

    def issue(self, key):
        if not hmac.compare_digest(key.encode(), self.settings.access_key.encode()):
            return None
        now = self.clock()
        with self.lock:
            self.tokens = {token:expiry for token,expiry in self.tokens.items() if expiry > now}
            if len(self.tokens) >= 4096:
                return None
            token = secrets.token_urlsafe(32)
            self.tokens[hashlib.sha256(token.encode()).hexdigest()] = now + 8*60*60
        return token

    def revoke(self, cookies):
        with self.lock:
            self.tokens.pop(hashlib.sha256(cookies.get(COOKIE, "").encode()).hexdigest(), None)

    async def protect(self, request: Request, call_next):
        path = request.url.path
        railway_probe = (self.settings.mode == "accounts" and request.method == "GET"
                         and path == "/api/ready"
                         and request.headers.get("host") == "healthcheck.railway.app")
        if (not railway_probe and not self.valid_host(request.headers)) or not self.local_client(request.client):
            response = JSONResponse({"detail":"Untrusted host or non-local connection"},status_code=403)
        elif not self.valid_origin(request.headers):
            response = JSONResponse({"detail":"Cross-origin access is not allowed"},status_code=403)
        else:
            response = None
            public = path in ("/api/health", "/api/ready", "/api/auth/status", "/api/auth/login", "/api/auth/register",
                              "/api/auth/device/login", "/api/auth/device/register", "/api/auth/signup/start",
                              "/api/auth/desktop/start", "/api/auth/desktop/exchange")
            is_api = path.startswith("/api/")
            client = request.client.host if request.client else "unknown"
            if is_api and self.limited(client, "requests", 3000 if self.accounts else
                                       600 if self.settings.mode == "local" else 300):
                response = JSONResponse({"detail":"Request limit reached; retry after one minute"},status_code=429,headers={"Retry-After":"60"})
            elif is_api and not public and self.accounts:
                try:
                    request.state.trader = await run_in_threadpool(self.accounts.identity, account_token(request.headers, request.cookies))
                except StorageError:
                    response = JSONResponse({"detail": "Workspace storage is unavailable."}, status_code=503)
            if response is not None:
                pass
            elif is_api and not public and not (
                    request.state.trader if self.accounts else self.authorized(request.headers, request.cookies)):
                response = JSONResponse({"detail":"Sign in to access this workspace"},status_code=401)
            elif path in ("/api/experiments", "/api/market/refresh") and request.method == "POST" and self.limited(
                    request.client.host if request.client else "unknown", path, 2):
                response = JSONResponse({"detail":"Expensive operation limit reached; retry after one minute"},status_code=429,headers={"Retry-After":"60"})
            else:
                size = 0
                if request.method in ("POST", "PATCH", "PUT"):
                    chunks = []
                    async for chunk in request.stream():
                        size += len(chunk)
                        if size > MAX_BODY:
                            break
                        chunks.append(chunk)
                    if size <= MAX_BODY:
                        request._body = b"".join(chunks)
                if size > MAX_BODY:
                    response = JSONResponse({"detail":"Request body exceeds the 8 MiB limit"},status_code=413)
                else:
                    response = await call_next(request)
        response.headers.update({
            "X-Content-Type-Options":"nosniff", "X-Frame-Options":"DENY",
            "Referrer-Policy":"no-referrer", "Permissions-Policy":"camera=(), microphone=(), geolocation=()",
            "Content-Security-Policy":"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'none'; frame-ancestors 'none'",
        })
        if self.settings.mode != "local":
            response.headers["Strict-Transport-Security"] = "max-age=31536000"
        return response
