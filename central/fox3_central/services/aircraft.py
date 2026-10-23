"""Live friendly aircraft for the map. A viewer only ever sees the coalition they fly for (never the enemy);
administrators may pick any side. Anonymous visitors get nothing (the public map shows zones only)."""
from __future__ import annotations

from sqlalchemy.engine import Connection

from ..repositories import players

SIDES = ("red", "blue")


def _view(p: dict) -> dict:
    pos = p.get("position") or {}
    return {"ucid": p["ucid"], "name": p["name"], "coalition": p["coalition"], "aircraft": p["aircraft"],
            "lat": pos.get("lat"), "lon": pos.get("lon"), "alt_m": pos.get("alt_m"), "in_air": p["in_air"]}


def _viewer_side(online: list[dict], linked: set[str]) -> str | None:
    """Coalition of the viewer's own linked DCS account, if it is online on this server."""
    return next((p["coalition"] for p in online if p["ucid"] in linked and p["coalition"] in SIDES), None)


def allied_aircraft(cn: Connection, server_id: str, user_id: int, is_admin: bool, requested: str | None = None) -> dict:
    online = players.list_online(cn, server_id)
    side = _viewer_side(online, set(players.linked_ucids(cn, user_id)))
    if is_admin:  # noqa: SIM108  (a nested ternary would be less readable)
        sides = {requested} if requested in SIDES else set(SIDES)
    else:
        sides = {side} if side else set()
    hint = None
    if not sides:
        hint = "link_account" if not players.linked_ucids(cn, user_id) else "not_online"
    aircraft = [_view(p) for p in online if p["coalition"] in sides and (p.get("position") or {}).get("lat") is not None]
    return {"viewer_coalition": side, "coalitions": sorted(sides), "hint": hint, "aircraft": aircraft}
