"""Map and mission views built from the Foothold snapshot (coordinates converted to lat/lon here)."""
from __future__ import annotations

from sqlalchemy.engine import Connection

from fox3_common import geo

from ..repositories import foothold, servers


def build_map(cn: Connection, server_id: str) -> dict:
    srv = servers.get(cn, server_id)
    info = servers.get_status(cn, server_id)["info"]
    terrain = (srv or {}).get("terrain") or info.get("terrain")
    state = foothold.get_state(cn, server_id) or {}
    zones = [_zone_view(z, terrain) for z in state.get("zones", [])]
    located = bool(zones) and all(z["lat"] is not None for z in zones)
    return {"terrain": terrain, "calibrated": located or geo.is_calibrated(terrain), "zones": zones,
            "connections": state.get("connections", [])}


def _zone_view(z: dict, terrain: str | None) -> dict:
    """Public zone data. lat/lon come from the file itself (`geo`) when present, else from the DCS x/y projection."""
    if z.get("geo"):
        lat, lon = z["geo"]["lat"], z["geo"]["lon"]
    elif z.get("position") and (ll := geo.xy_to_latlon(terrain, z["position"]["x"], z["position"]["y"])):
        lat, lon = ll
    else:
        lat = lon = None
    return {"name": z["name"], "coalition": z["coalition"], "is_hq": z.get("is_hq", False),
            "at_risk": z.get("at_risk", False), "level": z.get("level"), "lat": lat, "lon": lon}


def farps(cn: Connection, server_id: str) -> list[dict]:
    """Player-built FARPs. lat/lon come from the file when present, else from the DCS x/y with the map projection."""
    srv = servers.get(cn, server_id)
    terrain = (srv or {}).get("terrain") or servers.get_status(cn, server_id)["info"].get("terrain")
    out = []
    for f in (foothold.get_state(cn, server_id) or {}).get("farps", []):
        pos = f.get("position")
        ll = (f["geo"]["lat"], f["geo"]["lon"]) if f.get("geo") else (geo.xy_to_latlon(terrain, pos["x"], pos["y"]) if pos else None)
        if ll:
            out.append({"name": f["name"], "lat": ll[0], "lon": ll[1]})
    return out


def front_line(map_data: dict) -> list[list[list[float]]]:
    """Connections between zones of opposing coalitions, as [[lat, lon], [lat, lon]] segments."""
    by_name = {z["name"]: z for z in map_data["zones"] if z["lat"] is not None}
    sides = {"red", "blue"}
    out = []
    for c in map_data["connections"]:
        a, b = by_name.get(c["from"]), by_name.get(c["to"])
        if a and b and {a["coalition"], b["coalition"]} == sides:
            out.append([[a["lat"], a["lon"]], [b["lat"], b["lon"]]])
    return out


def missions(cn: Connection, server_id: str) -> list[dict]:
    """Current mission of the server (history of past missions arrives with rounds in a later phase)."""
    srv = servers.get(cn, server_id)
    info = servers.get_status(cn, server_id)["info"]
    if not srv or not info.get("mission_name"):
        return []
    return [{"name": info["mission_name"], "terrain": srv.get("terrain"), "mission_type": srv["mission_type"],
             "current": True, "started_at": info.get("mission_started_at")}]
