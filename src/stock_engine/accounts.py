"""Accounts and browser sessions for the hosted trading workspace."""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import secrets
from threading import BoundedSemaphore, Lock
from uuid import uuid4

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from .storage import PostgresSessionStore

SESSION_LIFETIME = 7 * 24 * 60 * 60


@dataclass(frozen=True)
class Trader:
    username: str
    workspace_id: str
    tutorial_seen: bool


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class Accounts:
    def __init__(self, store: PostgresSessionStore):
        self.store = store
        self.hasher = PasswordHasher()
        self.schema_lock = Lock()
        self.initialized = False
        self.password_workers = BoundedSemaphore(2)
        self.dummy_hash = self.hasher.hash(secrets.token_urlsafe(32))

    def check(self):
        with self.schema_lock:
            with self.store.connect() as connection:
                if self.initialized:
                    connection.execute("SELECT 1 FROM trader_accounts LIMIT 0")
                    connection.execute("SELECT 1 FROM trader_logins LIMIT 0")
                    return
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS trader_accounts (
                        username TEXT PRIMARY KEY,
                        password_hash TEXT NOT NULL,
                        workspace_id TEXT NOT NULL UNIQUE REFERENCES sessions(session_id),
                        tutorial_seen BOOLEAN NOT NULL DEFAULT FALSE)
                """)
                connection.execute("""
                    CREATE TABLE IF NOT EXISTS trader_logins (
                        token_digest TEXT PRIMARY KEY,
                        username TEXT NOT NULL REFERENCES trader_accounts(username) ON DELETE CASCADE,
                        expires_at TIMESTAMPTZ NOT NULL)
                """)
                connection.execute("CREATE INDEX IF NOT EXISTS trader_logins_expiration ON trader_logins(expires_at)")
            self.initialized = True

    def register(self, username: str, password: str, previous_token: str = "") -> str | None:
        if not self.initialized:
            self.check()
        with self.password_workers:
            password_hash = self.hasher.hash(password)
        workspace_id = str(uuid4())
        token = secrets.token_urlsafe(32)
        with self.store.connect() as connection:
            connection.execute(
                "INSERT INTO sessions VALUES (%s, %s, 0, %s)",
                (workspace_id, '{"reviews":{}}', datetime.now(timezone.utc).isoformat()))
            created = connection.execute("""
                INSERT INTO trader_accounts (username, password_hash, workspace_id)
                VALUES (%s, %s, %s) ON CONFLICT (username) DO NOTHING RETURNING username
            """, (username, password_hash, workspace_id)).fetchone()
            if not created:
                connection.rollback()
                return None
            self._issue(connection, username, token, previous_token)
        return token

    def login(self, username: str, password: str, previous_token: str = "") -> str | None:
        if not self.initialized:
            self.check()
        with self.store.connect() as connection:
            row = connection.execute(
                "SELECT password_hash FROM trader_accounts WHERE username=%s", (username,)).fetchone()
        password_hash = row[0] if row else self.dummy_hash
        with self.password_workers:
            try:
                self.hasher.verify(password_hash, password)
            except VerifyMismatchError:
                return None
            if not row:
                return None
            updated = self.hasher.hash(password) if self.hasher.check_needs_rehash(password_hash) else None
        token = secrets.token_urlsafe(32)
        with self.store.connect() as connection:
            if updated:
                connection.execute(
                    "UPDATE trader_accounts SET password_hash=%s WHERE username=%s AND password_hash=%s",
                    (updated, username, password_hash))
            self._issue(connection, username, token, previous_token)
        return token

    def _issue(self, connection, username: str, token: str, previous_token: str):
        connection.execute("DELETE FROM trader_logins WHERE expires_at <= now()")
        if previous_token:
            connection.execute("DELETE FROM trader_logins WHERE token_digest=%s",
                               (token_digest(previous_token),))
        connection.execute("""
            INSERT INTO trader_logins VALUES (%s, %s, now() + %s * interval '1 second')
        """, (token_digest(token), username, SESSION_LIFETIME))

    def identity(self, token: str) -> Trader | None:
        if not token or len(token) != 43:
            return None
        if not self.initialized:
            self.check()
        with self.store.connect() as connection:
            row = connection.execute("""
                SELECT account.username, account.workspace_id, account.tutorial_seen
                FROM trader_logins AS login
                JOIN trader_accounts AS account USING (username)
                WHERE login.token_digest=%s AND login.expires_at > now()
            """, (token_digest(token),)).fetchone()
        return Trader(*row) if row else None

    def logout(self, token: str):
        if token:
            with self.store.connect() as connection:
                connection.execute("DELETE FROM trader_logins WHERE token_digest=%s", (token_digest(token),))

    def finish_tutorial(self, trader: Trader):
        with self.store.connect() as connection:
            connection.execute("UPDATE trader_accounts SET tutorial_seen=TRUE WHERE username=%s",
                               (trader.username,))
