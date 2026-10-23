"""Engine factory. SQLite (demo) is tuned for concurrent readers; PostgreSQL needs no special handling. Migrates on creation."""
from __future__ import annotations

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine

from . import migrate


def make_engine(url: str) -> Engine:
    if not url.startswith("sqlite"):
        engine = create_engine(url, pool_pre_ping=True)
    else:
        engine = create_engine(url, connect_args={"check_same_thread": False})

        @event.listens_for(engine, "connect")
        def _on_connect(dbapi, _record):  # noqa: ANN001
            dbapi.isolation_level = None  # we emit BEGIN ourselves so SAVEPOINTs work
            dbapi.execute("PRAGMA journal_mode=WAL")
            dbapi.execute("PRAGMA busy_timeout=5000")

        @event.listens_for(engine, "begin")
        def _on_begin(conn):  # noqa: ANN001
            # write transactions take the write lock up front (and wait for it); reads stay concurrent under WAL
            conn.exec_driver_sql("BEGIN IMMEDIATE" if conn.get_execution_options().get("write") else "BEGIN")

    migrate.upgrade(engine)  # the schema belongs to the migrations (central/fox3_central/migrations), never to create_all
    return engine
