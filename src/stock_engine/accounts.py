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
from .signup_verification import SignupVerification, VerificationRequired

SESSION_LIFETIME = 7 * 24 * 60 * 60
SHARED_BOOK = "00000000-0000-0000-0000-000000000001"
FUNDED_BOOK = "00000000-0000-0000-0000-000000000002"
ACTIVE_SECONDS = 90


@dataclass(frozen=True)
class Trader:
    username: str
    workspace_id: str
    tutorial_seen: bool


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


class Accounts:
    def __init__(self, store: PostgresSessionStore, signup_verification: SignupVerification | None = None):
        self.store = store
        self.signup_verification = signup_verification
        self.hasher = PasswordHasher()
        self.schema_lock = Lock()
        self.initialized = False
        self.password_workers = BoundedSemaphore(2)
        self.dummy_hash = self.hasher.hash(secrets.token_urlsafe(32))

    def check(self):
        with self.schema_lock:
            with self.store.connect() as connection:
                if self.signup_verification:
                    connection.execute("SELECT email_code_digest FROM signup_verifications LIMIT 0")
                    connection.execute("SELECT 1 FROM trader_verified_contacts LIMIT 0")
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
                connection.execute("ALTER TABLE trader_accounts ADD COLUMN IF NOT EXISTS last_active_at TIMESTAMPTZ")
                for book_id in (SHARED_BOOK, FUNDED_BOOK):
                    connection.execute(
                        "INSERT INTO sessions VALUES (%s, %s, 0, %s) ON CONFLICT (session_id) DO NOTHING",
                        (book_id, '{"reviews":{}}', datetime.now(timezone.utc).isoformat()))
            self.initialized = True

    def register(self, username: str, password: str, previous_token: str = "", *,
                 verification_token: str = "") -> str | None:
        if not self.initialized:
            self.check()
        with self.password_workers:
            password_hash = self.hasher.hash(password)
        workspace_id = str(uuid4())
        token = secrets.token_urlsafe(32)
        with self.store.connect() as connection:
            verified_email = None
            if self.signup_verification:
                if not verification_token:
                    raise VerificationRequired("Verify your email to create an account")
                verified_email = self.signup_verification.consume(connection, username, verification_token)
            connection.execute(
                "INSERT INTO sessions (session_id, metadata, revision, updated_at) VALUES (%s, %s, 0, %s)",
                (workspace_id, '{"reviews":{}}', datetime.now(timezone.utc).isoformat()))
            created = connection.execute("""
                INSERT INTO trader_accounts (username, password_hash, workspace_id)
                VALUES (%s, %s, %s) ON CONFLICT (username) DO NOTHING RETURNING username
            """, (username, password_hash, workspace_id)).fetchone()
            if not created:
                connection.rollback()
                return None
            if verified_email and not connection.execute("""
                INSERT INTO trader_verified_contacts (username, email)
                VALUES (%s, %s) ON CONFLICT DO NOTHING RETURNING username
            """, (username, verified_email)).fetchone():
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

    def record_activity(self, trader: Trader):
        with self.store.connect() as connection:
            connection.execute("""
                UPDATE trader_accounts SET last_active_at=now() WHERE username=%s
                AND (last_active_at IS NULL OR last_active_at < now() - interval '15 seconds')
            """, (trader.username,))

    def activity(self):
        with self.store.connect() as connection:
            rows = connection.execute("""
                SELECT username, workspace_id, last_active_at,
                    COALESCE(last_active_at >= now() - %s * interval '1 second', FALSE) AS active,
                    COALESCE(last_active_at >= now() - interval '24 hours', FALSE) AS active_today
                FROM trader_accounts ORDER BY last_active_at DESC NULLS LAST, username
            """, (ACTIVE_SECONDS,)).fetchall()
        return rows
