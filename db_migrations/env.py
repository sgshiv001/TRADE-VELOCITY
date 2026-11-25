"""Run reviewed PostgreSQL migrations using a server-side connection string."""

import os

from alembic import context
from sqlalchemy import create_engine, pool
from sqlalchemy.engine import make_url


def migrate():
    raw = os.environ.get("DATABASE_URL", "")
    if not raw:
        raise RuntimeError("Set DATABASE_URL to the PostgreSQL database to migrate.")
    if raw.startswith("postgres://"):
        raw = "postgresql://" + raw[len("postgres://"):]
    url = make_url(raw)
    if url.get_backend_name() != "postgresql":
        raise RuntimeError("TradeVelocity migrations require PostgreSQL.")
    if context.is_offline_mode():
        context.configure(dialect_name="postgresql", literal_binds=True)
        with context.begin_transaction():
            context.run_migrations()
        return
    engine = create_engine(url.set(drivername="postgresql+psycopg"), poolclass=pool.NullPool,
                           connect_args={"connect_timeout": 5, "options": "-c lock_timeout=5000"})
    with engine.connect() as connection:
        context.configure(connection=connection)
        with context.begin_transaction():
            connection.exec_driver_sql("SELECT pg_advisory_xact_lock(215492874)")
            context.run_migrations()


migrate()
