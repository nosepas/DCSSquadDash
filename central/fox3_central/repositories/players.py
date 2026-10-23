from __future__ import annotations

from typing import Any

from sqlalchemy import delete, func, insert, select, update
from sqlalchemy.engine import Connection

from ..core.clock import now
from ..db import tables as t
from ..db.auth_tables import player_links
from ..db.utils import insert_ignore, upsert
from .sql_text import ESCAPE, like_contains

Row = dict[str, Any]


def touch(cn: Connection, ucid: str, name: str | None) -> None:
    ts = now()
    if not insert_ignore(cn, t.players, ucid=ucid, last_name=name, first_seen_at=ts, last_seen_at=ts):
        cn.execute(update(t.players).where(t.players.c.ucid == ucid)
                   .values(last_seen_at=ts, **({"last_name": name} if name else {})))


def get(cn: Connection, ucid: str) -> Row | None:
    r = cn.execute(select(t.players).where(t.players.c.ucid == ucid)).mappings().first()
    return dict(r) if r else None


def search(cn: Connection, q: str, limit: int) -> list[Row]:
    match = func.lower(t.players.c.last_name).like(like_contains(q), escape=ESCAPE)
    stmt = select(t.players).where(match).order_by(t.players.c.last_name).limit(limit)
    return [dict(r) for r in cn.execute(stmt).mappings()]


def find_ucid_by_name(cn: Connection, name: str) -> str | None:
    """UCID of the player whose last known name is exactly `name`; None if unknown or ambiguous."""
    rows = cn.execute(select(t.players.c.ucid).where(t.players.c.last_name == name).limit(2)).all()
    return rows[0][0] if len(rows) == 1 else None


def count(cn: Connection) -> int:
    return cn.execute(select(func.count()).select_from(t.players)).scalar_one()


def replace_online(cn: Connection, server_id: str, players: list[Row]) -> None:
    cn.execute(delete(t.online_players).where(t.online_players.c.server_id == server_id))
    ts = now()
    for p in players:
        cn.execute(insert(t.online_players).values(
            server_id=server_id, ucid=p["ucid"], name=p["name"], coalition=p.get("coalition"), aircraft=p.get("aircraft"),
            slot=p.get("slot"), in_air=p.get("in_air", False), position=p.get("position"),
            connected_at=p.get("connected_at"), updated_at=ts))


def list_online(cn: Connection, server_id: str) -> list[Row]:
    stmt = select(t.online_players).where(t.online_players.c.server_id == server_id).order_by(t.online_players.c.name)
    return [dict(r) for r in cn.execute(stmt).mappings()]


def save_stats(cn: Connection, server_id: str, ucid: str, points: float | None, stats: dict) -> None:
    upsert(cn, t.player_stats, {"server_id": server_id, "ucid": ucid}, points=points or 0, stats=stats, updated_at=now())


def stats_for(cn: Connection, ucid: str) -> list[Row]:
    return [dict(r) for r in cn.execute(select(t.player_stats).where(t.player_stats.c.ucid == ucid)).mappings()]


def points_by_ucid(cn: Connection, server_id: str) -> dict[str, float]:
    rows = cn.execute(select(t.player_stats.c.ucid, t.player_stats.c.points).where(t.player_stats.c.server_id == server_id))
    return {u: p or 0 for u, p in rows}


def linked_ucids(cn: Connection, user_id: int) -> list[str]:
    return [r[0] for r in cn.execute(select(player_links.c.ucid).where(player_links.c.user_id == user_id))]


def link_owner(cn: Connection, ucid: str) -> int | None:
    return cn.execute(select(player_links.c.user_id).where(player_links.c.ucid == ucid)).scalar()


def link_if_absent(cn: Connection, ucid: str, user_id: int) -> bool:
    """Atomic: creates the link only if nobody owns the ucid (the primary key decides a race). True when this call created it."""
    return insert_ignore(cn, player_links, ucid=ucid, user_id=user_id, linked_at=now())


def link(cn: Connection, ucid: str, user_id: int) -> None:
    upsert(cn, player_links, {"ucid": ucid}, user_id=user_id, linked_at=now())
