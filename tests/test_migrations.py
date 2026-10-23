"""The schema is owned by Alembic migrations: they must build exactly what the models describe, and be reversible."""
import pytest
from alembic.autogenerate import compare_metadata
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from fox3_central.db import auth_tables, migrate, tacview_tables  # noqa: F401  (register every table on the metadata)
from fox3_central.db.engine import make_engine
from fox3_central.db.tables import md


@pytest.fixture
def url(tmp_path):
    return f"sqlite:///{(tmp_path / 'm.sqlite').as_posix()}"


def test_migrations_build_exactly_the_models(url):
    engine = make_engine(url)
    with engine.connect() as cn:
        diff = compare_metadata(MigrationContext.configure(cn, opts={"compare_type": True}), md)
    assert diff == [], f"models and migrations disagree, run tools/make_migration.py: {diff}"


def test_upgrade_is_idempotent_and_downgrade_removes_everything(url):
    engine = make_engine(url)
    migrate.upgrade(engine)  # second run: nothing to do
    assert {"servers", "events", "tacview_files", "users"} <= set(inspect(engine).get_table_names())
    migrate.downgrade(engine)
    assert set(inspect(engine).get_table_names()) <= {"alembic_version"}


def test_a_database_created_before_migrations_is_refused_not_corrupted(url):
    engine = create_engine(url)
    md.create_all(engine)  # what the old code did: tables without migration history
    with pytest.raises(migrate.LegacyDatabaseError):
        migrate.upgrade(engine)
