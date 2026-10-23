from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import delete, insert, select, update
from sqlalchemy.engine import Connection

from ..db import tables as t
from ..db.utils import upsert
from . import link_claims, tacview

Row = dict[str, Any]


def create(cn: Connection, name: str, mission_type: str = "generic") -> Row:
    sid = str(uuid.uuid4())
    cn.execute(insert(t.servers).values(server_id=sid, name=name, mission_type=mission_type))
    return get(cn, sid)  # type: ignore[return-value]


def get(cn: Connection, server_id: str) -> Row | None:
    r = cn.execute(select(t.servers).where(t.servers.c.server_id == server_id)).mappings().first()
    return dict(r) if r else None


def list_all(cn: Connection, only_enabled: bool = False) -> list[Row]:
    q = select(t.servers).order_by(t.servers.c.name)
    if only_enabled:
        q = q.where(t.servers.c.enabled.is_(True))
    return [dict(r) for r in cn.execute(q).mappings()]


def update_fields(cn: Connection, server_id: str, **values: object) -> None:
    if values:
        cn.execute(update(t.servers).where(t.servers.c.server_id == server_id).values(**values))


def delete_server(cn: Connection, server_id: str) -> None:
    tacview.delete_for_server(cn, server_id)
    link_claims.delete_for_server(cn, server_id)
    for table in (t.online_players, t.foothold_state, t.zone_history, t.server_status, t.events, t.player_stats, t.agents):
        cn.execute(delete(table).where(table.c.server_id == server_id))
    cn.execute(delete(t.servers).where(t.servers.c.server_id == server_id))


def settings_of(server: Row) -> dict:
    """Validated settings of a server with defaults filled in (what the admin panel shows and the agent receives)."""
    from ..models.settings import ServerSettings
    return ServerSettings.model_validate(server.get("settings") or {}).model_dump()


def get_status(cn: Connection, server_id: str) -> Row:
    r = cn.execute(select(t.server_status).where(t.server_status.c.server_id == server_id)).mappings().first()
    return dict(r) if r else {"server_id": server_id, "info": {}, "heartbeat": {}, "updated_at": None}


def set_status(cn: Connection, server_id: str, **values: object) -> None:
    from ..core.clock import now
    upsert(cn, t.server_status, {"server_id": server_id}, updated_at=now(), **values)
