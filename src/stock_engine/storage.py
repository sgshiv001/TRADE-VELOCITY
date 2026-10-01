"""Transactional local session storage. Legacy JSON files are never deleted."""

from contextlib import closing
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3


class SessionStore:
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
