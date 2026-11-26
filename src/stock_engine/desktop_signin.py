"""Short-lived browser approvals for the connected desktop clients."""

from dataclasses import dataclass
from hashlib import sha256
from hmac import compare_digest
from secrets import randbelow, token_urlsafe
from threading import Lock
from time import monotonic

from fastapi import HTTPException


DESKTOP_SIGNIN_SECONDS = 300


@dataclass
class DesktopRequest:
    challenge: str
    code: str
    view: str
    expires: float
    attempts: int = 0
    approved_login: str | None = None


class DesktopSignIn:
    def __init__(self, clock=monotonic):
        self.clock = clock
        self.requests: dict[str, DesktopRequest] = {}
        self.lock = Lock()

    def start(self, challenge: str, view: str):
        with self.lock:
            now = self.clock()
            self.requests = {key: grant for key, grant in self.requests.items() if grant.expires > now}
            if len(self.requests) >= 512:
                raise HTTPException(503, "Desktop sign-in is busy. Try again shortly.")
            request_id = token_urlsafe(24)
            code = f"{randbelow(100_000_000):08d}"
            self.requests[request_id] = DesktopRequest(challenge, code, view, now + DESKTOP_SIGNIN_SECONDS)
        return {"request_id": request_id, "code": code, "expires_in": DESKTOP_SIGNIN_SECONDS, "interval": 3}

    def _active(self, request_id: str):
        grant = self.requests.get(request_id)
        if grant is None or grant.expires <= self.clock():
            self.requests.pop(request_id, None)
            raise HTTPException(404, "Start a new sign-in from the desktop app.")
        return grant

    def approve(self, request_id: str, code: str, browser_login: str, administrator: bool):
        with self.lock:
            grant = self._active(request_id)
            if grant.approved_login:
                raise HTTPException(409, "This desktop sign-in has already been approved.")
            if not compare_digest(grant.code, code):
                grant.attempts += 1
                if grant.attempts >= 5:
                    self.requests.pop(request_id)
                    raise HTTPException(429, "Too many tries. Start a new sign-in from the desktop app.")
                raise HTTPException(400, "Enter the code shown in the desktop app.")
            if grant.view == "admin" and not administrator:
                raise HTTPException(403, "Sign in with an administrator account to continue.")
            grant.approved_login = sha256(browser_login.encode()).hexdigest()

    def take_approval(self, request_id: str, verifier: str):
        with self.lock:
            grant = self._active(request_id)
            if not compare_digest(grant.challenge, sha256(verifier.encode()).hexdigest()):
                raise HTTPException(404, "Start a new sign-in from the desktop app.")
            if grant.approved_login is None:
                return None
            self.requests.pop(request_id)
            return grant.approved_login
