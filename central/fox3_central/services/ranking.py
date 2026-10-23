"""Per-server player ranking (stats are separate per server; identity is the UCID)."""
from __future__ import annotations

from sqlalchemy.engine import Connection

from ..repositories import events, players

SORTS = ("points", "kills", "kd")


def build(cn: Connection, server_id: str, sort: str = "points", limit: int = 50) -> list[dict]:
    kills = events.kill_counts(cn, server_id)
    deaths = events.death_counts(cn, server_id)
    points = players.points_by_ucid(cn, server_id)
    rows = []
    for ucid in set(kills) | set(deaths) | set(points):
        name, k = kills.get(ucid, (None, 0))
        d = deaths.get(ucid, 0)
        rows.append({"ucid": ucid, "name": name or (players.get(cn, ucid) or {}).get("last_name"),
                     "kills": k, "deaths": d, "kd": round(k / d, 2) if d else float(k), "points": points.get(ucid, 0)})
    key = sort if sort in SORTS else "points"
    rows.sort(key=lambda r: (r[key], r["kills"]), reverse=True)
    return rows[:limit]
