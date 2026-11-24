"""Transactional session storage with SQLite and optional PostgreSQL."""

from contextlib import closing, contextmanager
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import sqlite3
from threading import RLock
from urllib.parse import urlsplit


class StorageError(Exception):
    """A database operation failed without exposing connection credentials."""


class SessionStore:
    kind = "sqlite"

    def __init__(self, directory: Path):
        self.directory = Path(directory)
        self.path = self.directory / "workspace.sqlite3"

    def connect(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=10, isolation_level="IMMEDIATE")
        connection.execute("PRAGMA foreign_keys=ON")
        connection.execute("PRAGMA synchronous=FULL")
        connection.executescript("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY, metadata TEXT NOT NULL, revision INTEGER NOT NULL,
                updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS commands (
                session_id TEXT NOT NULL REFERENCES sessions(session_id),
                position INTEGER NOT NULL, event TEXT NOT NULL,
                PRIMARY KEY(session_id, position));
            CREATE TABLE IF NOT EXISTS receipts (
                session_id TEXT NOT NULL REFERENCES sessions(session_id),
                request_key TEXT NOT NULL, fingerprint TEXT NOT NULL, response TEXT NOT NULL,
                PRIMARY KEY(session_id, request_key));
        """)
        return connection

    def check(self):
        with closing(self.connect()) as connection:
            connection.execute("SELECT 1").fetchone()

    def load(self, session_id: str) -> dict | None:
        if self.path.exists():
            with closing(self.connect()) as connection:
                row = connection.execute("SELECT metadata,revision FROM sessions WHERE session_id=?", (session_id,)).fetchone()
                if row:
                    events = [json.loads(record[0]) for record in connection.execute(
                        "SELECT event FROM commands WHERE session_id=? ORDER BY position", (session_id,))]
                    return {**json.loads(row[0]), "revision": row[1], "lab": {"version": 2, "events": events}}
        legacy = self.directory / f"{session_id}.json"
        return json.loads(legacy.read_text(encoding="utf-8")) if legacy.exists() else None

    def receipt(self, session_id: str, key: str) -> tuple[str, dict] | None:
        if not self.path.exists():
            return None
        with closing(self.connect()) as connection:
            row = connection.execute("SELECT fingerprint,response FROM receipts WHERE session_id=? AND request_key=?", (session_id, key)).fetchone()
            return (row[0], json.loads(row[1])) if row else None

    def save(self, session_id: str, events: list[dict], metadata: dict, revision: int,
             *, replace_events: bool = False, receipt: tuple[str, str, dict] | None = None):
        with closing(self.connect()) as connection, connection:
            connection.execute("INSERT INTO sessions VALUES (?,?,?,?) ON CONFLICT(session_id) DO UPDATE SET metadata=excluded.metadata,revision=excluded.revision,updated_at=excluded.updated_at",
                               (session_id, json.dumps(metadata), revision, datetime.now(timezone.utc).isoformat()))
            if replace_events:
                connection.execute("DELETE FROM commands WHERE session_id=?", (session_id,))
            count = connection.execute("SELECT COUNT(*) FROM commands WHERE session_id=?", (session_id,)).fetchone()[0]
            if count > len(events):
                raise ValueError("stored history is ahead of the active session")
            connection.executemany("INSERT INTO commands VALUES (?,?,?)", (
                (session_id, index, json.dumps(events[index])) for index in range(count, len(events))))
            if receipt:
                key, fingerprint, response = receipt
                connection.execute("INSERT INTO receipts VALUES (?,?,?,?)", (session_id, key, fingerprint, json.dumps(response)))


class PostgresSessionStore:
    kind = "postgresql"

    def __init__(self, directory: Path, database_url: str):
        try:
            import psycopg
        except ImportError:
            raise RuntimeError('Install the PostgreSQL extra with pip install -e ".[app,postgres]"') from None
        self.directory = Path(directory)
        self._database_url = database_url
        self._driver = psycopg
        self._schema_lock = RLock()
        self._initialized = False

    @contextmanager
    def connect(self):
        try:
            with self._driver.connect(self._database_url, connect_timeout=5,
                                      options="-c statement_timeout=10000 -c lock_timeout=5000") as connection:
                with self._schema_lock:
                    if not self._initialized:
                        connection.execute("""
                            CREATE TABLE IF NOT EXISTS sessions (
                                session_id TEXT PRIMARY KEY, metadata TEXT NOT NULL,
                                revision INTEGER NOT NULL, updated_at TEXT NOT NULL)
                        """)
                        connection.execute("""
                            CREATE TABLE IF NOT EXISTS commands (
                                session_id TEXT NOT NULL REFERENCES sessions(session_id),
                                position INTEGER NOT NULL, event TEXT NOT NULL,
                                PRIMARY KEY(session_id, position))
                        """)
                        connection.execute("""
                            CREATE TABLE IF NOT EXISTS receipts (
                                session_id TEXT NOT NULL REFERENCES sessions(session_id),
                                request_key TEXT NOT NULL, fingerprint TEXT NOT NULL, response TEXT NOT NULL,
                                PRIMARY KEY(session_id, request_key))
                        """)
                        connection.commit()
                        self._initialized = True
                yield connection
        except self._driver.Error:
            raise StorageError("PostgreSQL is unavailable. Check the database connection and permissions.") from None

    def check(self):
        with self.connect() as connection:
            connection.execute("SELECT 1").fetchone()

    def load(self, session_id: str) -> dict | None:
        with self.connect() as connection:
            # Keep metadata and its event log in the same database snapshot.
            connection.execute("SET TRANSACTION ISOLATION LEVEL REPEATABLE READ")
            row = connection.execute("SELECT metadata,revision FROM sessions WHERE session_id=%s", (session_id,)).fetchone()
            if row:
                events = [json.loads(record[0]) for record in connection.execute(
                    "SELECT event FROM commands WHERE session_id=%s ORDER BY position", (session_id,))]
                return {**json.loads(row[0]), "revision": row[1], "lab": {"version": 2, "events": events}}
        legacy = self.directory / f"{session_id}.json"
        return json.loads(legacy.read_text(encoding="utf-8")) if legacy.exists() else None

    def receipt(self, session_id: str, key: str) -> tuple[str, dict] | None:
        with self.connect() as connection:
            row = connection.execute(
                "SELECT fingerprint,response FROM receipts WHERE session_id=%s AND request_key=%s", (session_id, key)).fetchone()
            return (row[0], json.loads(row[1])) if row else None

    def save(self, session_id: str, events: list[dict], metadata: dict, revision: int,
             *, replace_events: bool = False, receipt: tuple[str, str, dict] | None = None):
        with self.connect() as connection:
            now = datetime.now(timezone.utc).isoformat()
            inserted = connection.execute(
                "INSERT INTO sessions VALUES (%s,%s,%s,%s) ON CONFLICT(session_id) DO NOTHING RETURNING session_id",
                (session_id, json.dumps(metadata), revision, now)).fetchone()
            previous = connection.execute(
                "SELECT revision FROM sessions WHERE session_id=%s FOR UPDATE", (session_id,)).fetchone()[0]
            if inserted is None and previous != revision - 1:
                raise StorageError("The saved session changed. Run one backend worker and reload the session.")
            connection.execute("UPDATE sessions SET metadata=%s,revision=%s,updated_at=%s WHERE session_id=%s",
                               (json.dumps(metadata), revision, now, session_id))
            if replace_events:
                connection.execute("DELETE FROM commands WHERE session_id=%s", (session_id,))
            count = connection.execute("SELECT COUNT(*) FROM commands WHERE session_id=%s", (session_id,)).fetchone()[0]
            if count > len(events):
                raise ValueError("stored history is ahead of the active session")
            with connection.cursor() as cursor:
                cursor.executemany("INSERT INTO commands VALUES (%s,%s,%s)", (
                    (session_id, index, json.dumps(events[index])) for index in range(count, len(events))))
            if receipt:
                key, fingerprint, response = receipt
                connection.execute("INSERT INTO receipts VALUES (%s,%s,%s,%s)",
                                   (session_id, key, fingerprint, json.dumps(response)))


def create_store(directory: Path, database_url: str | None = None):
    if database_url is None:
        database_url = os.environ.get("TRADEVELOCITY_DATABASE_URL", os.environ.get("DATABASE_URL", ""))
    if not database_url:
        return SessionStore(directory)
    if urlsplit(database_url).scheme not in ("postgres", "postgresql"):
        raise ValueError("Database URL must use postgres:// or postgresql://. Unset it to use SQLite.")
    return PostgresSessionStore(directory, database_url)
