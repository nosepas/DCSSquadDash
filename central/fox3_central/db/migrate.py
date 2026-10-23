"""Run database migrations (Alembic) from code. The schema is owned by migrations, never by `create_all`."""
from __future__ import annotations

from pathlib import Path

from alembic import command
from alembic.config import Config
from sqlalchemy import inspect
from sqlalchemy.engine import Engine

MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"


class LegacyDatabaseError(RuntimeError):
    """The database has FOX3 tables but no migration history (created before migrations existed)."""


def _config(connection) -> Config:  # noqa: ANN001
    cfg = Config()
    cfg.set_main_option("script_location", str(MIGRATIONS))
    cfg.attributes["connection"] = connection
    return cfg


def upgrade(engine: Engine, revision: str = "head") -> None:
    names = set(inspect(engine).get_table_names())
    if "servers" in names and "alembic_version" not in names:
        raise LegacyDatabaseError("this database was created before migrations existed: start from an empty database "
                                  "(demo: use --reset) or stamp it manually after checking its schema")
    with engine.begin() as cn:
        command.upgrade(_config(cn), revision)


def downgrade(engine: Engine, revision: str = "base") -> None:
    with engine.begin() as cn:
        command.downgrade(_config(cn), revision)
