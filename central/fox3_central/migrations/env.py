"""Alembic environment. Used programmatically (db/migrate.py passes the engine connection) and by the `alembic` CLI."""
from __future__ import annotations

from alembic import context
from sqlalchemy import create_engine, pool

from fox3_central.db import auth_tables, tacview_tables  # noqa: F401  (register every table on the shared metadata)
from fox3_central.db.tables import md

config = context.config
target_metadata = md


def run_migrations_online() -> None:
    connection = config.attributes.get("connection")
    if connection is None:  # CLI use: build an engine from sqlalchemy.url
        engine = create_engine(config.get_main_option("sqlalchemy.url"), poolclass=pool.NullPool)
        with engine.connect() as cn:
            _run(cn)
        return
    _run(connection)


def _run(connection) -> None:  # noqa: ANN001
    context.configure(connection=connection, target_metadata=target_metadata, compare_type=True, render_as_batch=False)
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    raise SystemExit("offline migrations are not supported; run against a database")
run_migrations_online()
