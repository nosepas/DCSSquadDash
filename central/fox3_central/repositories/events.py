from __future__ import annotations

from typing import Any

from sqlalchemy import func, select
from sqlalchemy.engine import Connection

from ..db import tables as t
from ..db.utils import insert_ignore

Row = dict[str, Any]
E = t.events.c


def insert_event(cn: Connection, server_id: str, e: Row) -> bool:
    a, tg = e.get("actor") or {}, e.get("target") or {}
    return insert_ignore(
        cn, t.events, server_id=server_id, event_id=e["event_id"], type=e["type"], time_utc=e["time_utc"],
        actor_ucid=a.get("ucid"), actor_name=a.get("name"), actor_coalition=a.get("coalition"), actor_unit=a.get("unit_type"),
        target_ucid=tg.get("ucid"), target_name=tg.get("name"), target_coalition=tg.get("coalition"),
        target_unit=tg.get("unit_type"), target_is_player=tg.get("is_player"), weapon=e.get("weapon"),
        zone=e.get("zone"), data=e.get("data"))


def list_events(cn: Connection, server_id: str, types: tuple[str, ...], limit: int, before: str | None = None) -> list[Row]:
    q = select(t.events).where(E.server_id == server_id, E.type.in_(types))
    if before:
        q = q.where(E.time_utc < before)
    return [dict(r) for r in cn.execute(q.order_by(E.time_utc.desc(), E.id.desc()).limit(limit)).mappings()]


def count_since(cn: Connection, server_id: str, type_: str, since: str) -> int:
    q = select(func.count()).select_from(t.events).where(E.server_id == server_id, E.type == type_, E.time_utc >= since)
    return cn.execute(q).scalar_one()


def kill_counts(cn: Connection, server_id: str) -> dict[str, tuple[str, int]]:
    """ucid -> (last known name, kills) for player killers."""
    q = (select(E.actor_ucid, func.max(E.actor_name), func.count())
         .where(E.server_id == server_id, E.type == "kill", E.actor_ucid.is_not(None)).group_by(E.actor_ucid))
    return {u: (n, c) for u, n, c in cn.execute(q)}


def death_counts(cn: Connection, server_id: str) -> dict[str, int]:
    q = (select(E.target_ucid, func.count())
         .where(E.server_id == server_id, E.type == "kill", E.target_ucid.is_not(None)).group_by(E.target_ucid))
    return {u: c for u, c in cn.execute(q)}


def player_summary(cn: Connection, ucid: str) -> list[Row]:
    """Per-server kills/deaths for one player."""
    kills = {s: c for s, c in cn.execute(select(E.server_id, func.count()).where(E.type == "kill", E.actor_ucid == ucid).group_by(E.server_id))}
    deaths = {s: c for s, c in cn.execute(select(E.server_id, func.count()).where(E.type == "kill", E.target_ucid == ucid).group_by(E.server_id))}
    return [{"server_id": s, "kills": kills.get(s, 0), "deaths": deaths.get(s, 0)} for s in set(kills) | set(deaths)]
