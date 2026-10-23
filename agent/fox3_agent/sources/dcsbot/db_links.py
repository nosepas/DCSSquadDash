"""Read-only reader of the verified (ucid, discord_id) pairs in DCSServerBot's `players` table.

DCSServerBot fills `players.discord_id` only after the player proved ownership of the Discord account (its `/linkme` flow);
-1 means "not linked". Column names are constants in `db_mapping` so a different DCSServerBot version needs one edit.
FOX3 never shows or sends a link code in public chat: it only forwards pairs DCSServerBot already verified.
"""
from __future__ import annotations

import logging

from sqlalchemy import Engine, column, select, table
from sqlalchemy.exc import SQLAlchemyError

from .db_mapping import LINK_COLUMNS, map_link_row
from .errors import DbError

log = logging.getLogger("fox3.agent.dcsbot")
MAX_ROWS = 100_000   # hard cap per read: a huge or corrupt table must not exhaust the agent's memory
_PL = table("players", *(column(c) for c in LINK_COLUMNS))


class DiscordLinkReader:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def read_all(self) -> dict[str, str]:
        """ucid -> discord_id (decimal string) for every valid linked player. Raises DbError."""
        ucid_col, discord_col = (_PL.c[c] for c in LINK_COLUMNS)
        query = select(ucid_col, discord_col).where(discord_col > 0).order_by(ucid_col).limit(MAX_ROWS)
        try:
            with self._engine.connect() as cn:
                rows = cn.execute(query).all()
        except SQLAlchemyError as exc:
            raise DbError(f"DCSServerBot database read failed ({type(exc).__name__})") from exc
        if len(rows) >= MAX_ROWS:
            log.warning("DCSServerBot players table has at least %d linked rows: the rest are ignored", MAX_ROWS)
        return dict(pair for r in rows if (pair := map_link_row(r[0], r[1])) is not None)
