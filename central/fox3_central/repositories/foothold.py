from __future__ import annotations

from typing import Any

from sqlalchemy import insert, select
from sqlalchemy.engine import Connection

from ..core.clock import now
from ..db import tables as t
from ..db.utils import upsert

Row = dict[str, Any]


def get_state(cn: Connection, server_id: str) -> Row | None:
    return cn.execute(select(t.foothold_state.c.state).where(t.foothold_state.c.server_id == server_id)).scalar()


def save_state(cn: Connection, server_id: str, state: Row) -> None:
    """Store the snapshot and record every zone whose coalition changed since the previous one."""
    previous = {z["name"]: z["coalition"] for z in (get_state(cn, server_id) or {}).get("zones", [])}
    for z in state["zones"]:
        if previous.get(z["name"]) != z["coalition"]:
            cn.execute(insert(t.zone_history).values(server_id=server_id, zone=z["name"], coalition=z["coalition"], at=state["snapshot_at"]))
    upsert(cn, t.foothold_state, {"server_id": server_id}, snapshot_at=state["snapshot_at"], state=state, updated_at=now())


def zone_history(cn: Connection, server_id: str, limit: int = 500) -> list[Row]:
    q = select(t.zone_history).where(t.zone_history.c.server_id == server_id).order_by(t.zone_history.c.at.desc()).limit(limit)
    return [dict(r) for r in cn.execute(q).mappings()]
