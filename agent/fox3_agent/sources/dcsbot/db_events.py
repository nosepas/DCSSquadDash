"""Read-only incremental reader of DCSServerBot's `missionstats` table (portable SQLAlchemy Core, SELECT only)."""
from __future__ import annotations

from typing import Any

from sqlalchemy import Engine, column, func, select, table
from sqlalchemy.exc import SQLAlchemyError

from .db_mapping import EVENT_TYPES, map_row
from .errors import DbError

_MS = table("missionstats", *(column(c) for c in (
    "id", "mission_id", "event", "init_id", "init_side", "init_type", "target_id", "target_side", "target_type", "weapon",
    "place", "time")))
_MI = table("missions", column("id"), column("server_name"))
_PL = table("players", column("ucid"), column("name"), column("last_seen"))
_INIT, _TARGET = _PL.alias("init_p"), _PL.alias("target_p")


class DbEventReader:
    def __init__(self, engine: Engine, server_name: str, *, batch_size: int = 200, seed_back: int = 100,
                 watermark: int | None = None) -> None:
        self._engine, self._server = engine, server_name
        self._batch, self._seed_back = batch_size, seed_back
        self._watermark = watermark

    @property
    def engine(self) -> Engine:
        return self._engine

    @property
    def watermark(self) -> int | None:
        """Last missionstats.id handed out (None until seeded). Persist it to survive restarts."""
        return self._watermark

    def fetch_batch(self) -> list[dict[str, Any]]:
        """Next batch (<= batch_size) of new contract events, advancing the watermark. Raises DbError."""
        try:
            with self._engine.connect() as cn:
                if self._watermark is None:
                    top = cn.execute(select(func.max(_MS.c.id)).select_from(_MS.join(_MI, _MI.c.id == _MS.c.mission_id))
                                     .where(_MI.c.server_name == self._server)).scalar()
                    self._watermark = max(0, int(top or 0) - self._seed_back)
                rows = cn.execute(self._query()).all()
        except SQLAlchemyError as exc:
            raise DbError(f"DCSServerBot database read failed ({type(exc).__name__})") from exc
        if rows:
            self._watermark = int(rows[-1].id)
        return [e for r in rows if (e := map_row(r)) is not None]

    def find_ucid(self, name: str) -> str | None:
        """Most recently seen ucid with exactly this player name."""
        q = select(_PL.c.ucid).where(_PL.c.name == name).order_by(_PL.c.last_seen.desc()).limit(1)
        try:
            with self._engine.connect() as cn:
                return cn.execute(q).scalar()
        except SQLAlchemyError as exc:
            raise DbError(f"DCSServerBot database read failed ({type(exc).__name__})") from exc

    def _query(self):
        j = (_MS.join(_MI, _MI.c.id == _MS.c.mission_id)
             .outerjoin(_INIT, _INIT.c.ucid == _MS.c.init_id).outerjoin(_TARGET, _TARGET.c.ucid == _MS.c.target_id))
        return (select(*_MS.c, _INIT.c.name.label("init_name"), _TARGET.c.name.label("target_name")).select_from(j)
                .where(_MS.c.id > self._watermark, _MI.c.server_name == self._server, _MS.c.event.in_(list(EVENT_TYPES)))
                .order_by(_MS.c.id).limit(self._batch))
