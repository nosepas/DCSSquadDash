"""Generate a new Alembic migration from the difference between the current models and the migrated schema.

Usage: python tools/make_migration.py "short message"
The generated file must be REVIEWED (renames appear as drop+add; data migrations are not generated).
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in ("common", "central", "dtc", "agent"):
    sys.path.insert(0, str(ROOT / p))

from alembic import command  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402

from fox3_central.db import migrate  # noqa: E402


def main() -> None:
    message = sys.argv[1] if len(sys.argv) > 1 else "schema change"
    with tempfile.TemporaryDirectory() as tmp:
        engine = create_engine(f"sqlite:///{(Path(tmp) / 'scratch.db').as_posix()}")
        migrate.upgrade(engine)  # bring a scratch database to the current head, then diff the models against it
        with engine.begin() as cn:
            command.revision(migrate._config(cn), message=message, autogenerate=True)  # noqa: SLF001
    print("migration written to central/fox3_central/migrations/versions/ - review it before committing")


if __name__ == "__main__":
    main()
