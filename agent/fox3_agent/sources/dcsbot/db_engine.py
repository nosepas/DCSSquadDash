"""SQLAlchemy engine factory for the DCSServerBot database.

PRODUCTION REQUIREMENT: the database user used here MUST be a read-only role (GRANT SELECT only on missionstats,
missions and players). This module only ever issues SELECTs, but the database must enforce it too. For PostgreSQL the
session is additionally opened with default_transaction_read_only=on and a statement_timeout.

The URL (with credentials) comes from an environment variable chosen by the configuration, never from code. The driver
(e.g. `postgresql+psycopg://`, needs the optional `psycopg` package) is imported lazily by SQLAlchemy, so importing this
module never requires it.
"""
from __future__ import annotations

from sqlalchemy import Engine, create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError, NoSuchModuleError

from .errors import DbError

CONNECT_TIMEOUT_S = 5
STATEMENT_TIMEOUT_MS = 5000


def make_engine(url: str) -> Engine:
    try:
        parsed = make_url(url)
        kwargs: dict = {"pool_pre_ping": True, "pool_size": 1, "max_overflow": 0}
        if parsed.get_backend_name() == "postgresql":
            kwargs["connect_args"] = {
                "connect_timeout": CONNECT_TIMEOUT_S,
                "options": f"-c statement_timeout={STATEMENT_TIMEOUT_MS} -c default_transaction_read_only=on",
            }
        elif parsed.get_backend_name() == "sqlite":
            kwargs = {"pool_pre_ping": True}
        return create_engine(parsed, **kwargs)
    except (ArgumentError, NoSuchModuleError, ImportError) as exc:
        # never include the URL (it may carry a password)
        raise DbError(f"cannot create the DCSServerBot database engine ({type(exc).__name__}); is the driver installed?") from exc
