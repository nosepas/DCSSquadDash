"""Dialect-independent write helpers (no INSERT OR IGNORE / ON CONFLICT dialect code)."""
from __future__ import annotations

from sqlalchemy import Table, insert, update
from sqlalchemy.engine import Connection
from sqlalchemy.exc import IntegrityError


def insert_ignore(cn: Connection, table: Table, **values: object) -> bool:
    """Insert a row; return False (and keep the transaction usable) if it violates a unique/PK constraint."""
    try:
        with cn.begin_nested():
            cn.execute(insert(table).values(**values))
        return True
    except IntegrityError:
        return False


def upsert(cn: Connection, table: Table, key: dict[str, object], **values: object) -> None:
    """Update the row identified by `key`, inserting it if absent."""
    cond = [table.c[k] == v for k, v in key.items()]
    updated = cn.execute(update(table).where(*cond).values(**values)).rowcount
    if updated == 0 and not insert_ignore(cn, table, **key, **values):  # lost a race: the row exists now
        cn.execute(update(table).where(*cond).values(**values))
