"""Baseline for the existing account, session, and trading book records."""

from alembic import op

revision = "0001_persistent_books"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY, metadata TEXT NOT NULL,
            revision INTEGER NOT NULL, updated_at TEXT NOT NULL)
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS commands (
            session_id TEXT NOT NULL REFERENCES sessions(session_id),
            position INTEGER NOT NULL, event TEXT NOT NULL,
            PRIMARY KEY(session_id, position))
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS receipts (
            session_id TEXT NOT NULL REFERENCES sessions(session_id),
            request_key TEXT NOT NULL, fingerprint TEXT NOT NULL, response TEXT NOT NULL,
            PRIMARY KEY(session_id, request_key))
    """)
    op.execute("""
        CREATE TABLE IF NOT EXISTS trader_accounts (
            username TEXT PRIMARY KEY, password_hash TEXT NOT NULL,
            workspace_id TEXT NOT NULL UNIQUE REFERENCES sessions(session_id),
            tutorial_seen BOOLEAN NOT NULL DEFAULT FALSE,
            last_active_at TIMESTAMPTZ)
    """)
    op.execute("ALTER TABLE trader_accounts ADD COLUMN IF NOT EXISTS last_active_at TIMESTAMPTZ")
    op.execute("""
        CREATE TABLE IF NOT EXISTS trader_logins (
            token_digest TEXT PRIMARY KEY,
            username TEXT NOT NULL REFERENCES trader_accounts(username) ON DELETE CASCADE,
            expires_at TIMESTAMPTZ NOT NULL)
    """)
    op.execute("CREATE INDEX IF NOT EXISTS trader_logins_expiration ON trader_logins(expires_at)")


def downgrade():
    raise RuntimeError("The baseline holds user and trading data. Use a compatible application rollback.")
