"""Player profile (single identity across servers, stats separated per server) and Discord<->UCID linking."""
from __future__ import annotations

from ..context import Context
from ..core.errors import BadRequest, Forbidden, NotFound
from ..repositories import events, players, servers, users


def build(ctx: Context, ucid: str) -> dict:
    with ctx.engine.connect() as cn:
        p = players.get(cn, ucid)
        if not p:
            raise NotFound("player not found")
        names = {s["server_id"]: s for s in servers.list_all(cn, only_enabled=True)}
        ev = {e["server_id"]: e for e in events.player_summary(cn, ucid)}
        pts = {s["server_id"]: s for s in players.stats_for(cn, ucid)}
        per_server = []
        for sid in (set(ev) | set(pts)) & set(names):  # servers that are disabled (or deleted) are not shown
            e, s = ev.get(sid, {}), pts.get(sid, {})
            per_server.append({"server_id": sid, "server_name": names.get(sid, {}).get("name"),
                               "kills": e.get("kills", 0), "deaths": e.get("deaths", 0),
                               "points": s.get("points", 0), "stats": s.get("stats", {})})
        owner = players.link_owner(cn, ucid)
    return {"ucid": ucid, "name": p["last_name"], "first_seen_at": p["first_seen_at"], "last_seen_at": p["last_seen_at"],
            "discord_linked": owner is not None, "servers": sorted(per_server, key=lambda s: s["server_name"] or "")}


def start_link(ctx: Context, user_id: int) -> dict:
    with ctx.tx() as cn:
        return users.create_link_code(cn, user_id)


def complete_link(ctx: Context, code: str, ucid: str, name: str | None) -> None:
    with ctx.tx() as cn:
        user_id = users.take_link_code(cn, code.strip().upper())
        if user_id is None:
            raise NotFound("unknown or expired code")
        owner = players.link_owner(cn, ucid)
        if owner is not None and owner != user_id:
            raise Forbidden("this DCS account is already linked to another user")
        players.touch(cn, ucid, name)
        players.link(cn, ucid, user_id)


def linked(ctx: Context, user_id: int) -> list[str]:
    with ctx.engine.connect() as cn:
        return players.linked_ucids(cn, user_id)


def validate_ucid(ucid: str) -> str:
    if not (8 <= len(ucid) <= 64):
        raise BadRequest("invalid ucid")
    return ucid
