"""Home-page aggregates: KPIs, top shooters, war news."""
from __future__ import annotations

from sqlalchemy.engine import Connection

from ..core.clock import ago
from ..repositories import events, players, servers
from . import mapdata, ranking

NEWS_TYPES = ("zone_captured", "zone_lost", "mission_start", "mission_end")


def build(cn: Connection, server_id: str) -> dict:
    online = players.list_online(cn, server_id)
    map_data = mapdata.build_map(cn, server_id)
    objectives = {"red": 0, "blue": 0, "neutral": 0}
    for z in map_data["zones"]:
        if z["coalition"] in objectives:
            objectives[z["coalition"]] += 1
    return {
        "online": len(online),
        "airborne": sum(1 for p in online if p["in_air"]),
        "objectives": objectives,
        "at_risk": sum(1 for z in map_data["zones"] if z["at_risk"]),
        "kills_1h": events.count_since(cn, server_id, "kill", ago(hours=1)),
        "pilots": players.count(cn),
        "weather": servers.get_status(cn, server_id)["info"].get("weather"),
        "front_line": mapdata.front_line(map_data),
        "top_shooters": ranking.build(cn, server_id, "kills", 5),
        "news": [news_item(e) for e in events.list_events(cn, server_id, NEWS_TYPES, 10)],
    }


def news_item(e: dict) -> dict:
    """Language-neutral item; the frontend renders the sentence from `type` + fields (i18n)."""
    return {"type": e["type"], "time_utc": e["time_utc"], "zone": e["zone"],
            "coalition": e["actor_coalition"], "actor": e["actor_name"]}
