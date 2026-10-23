"""DCSServerBot ServerInfo -> contract `server_info` payload, built from an explicit whitelist of fields.

Never read or forwarded: password, address, restart_time, extensions, players' callsign/radios, slot counts.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .units import feet_to_m, knots_to_ms, mmhg_to_hpa

AGENT_VERSION_DEFAULT = "0.1.0"


def select_server(servers: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    """First server whose name equals `name`; with an empty `name` only if exactly one server exists."""
    if name:
        return next((s for s in servers if s.get("name") == name), None)
    return servers[0] if len(servers) == 1 else None


def map_server_info(info: dict[str, Any], *, mission_type: str, now: datetime, agent_version: str = AGENT_VERSION_DEFAULT,
                    dcsbot_db: bool = False) -> dict[str, Any]:
    mission = info.get("mission") if isinstance(info.get("mission"), dict) else {}
    payload: dict[str, Any] = {
        "server_name": str(info.get("name", "")),
        "terrain": mission.get("theatre"),
        "mission_name": mission.get("name"),
        "mission_started_at": _started_at(mission, now),
        "mission_type": mission_type,
        "max_players": info.get("max_players") if isinstance(info.get("max_players"), int) else None,
        "agent_version": agent_version,
        "capabilities": {"foothold": mission_type == "foothold", "tacview": False, "grpc": False,
                         "dcsbot_rest": True, "dcsbot_db": dcsbot_db},
        "weather": map_weather(info.get("weather")),
    }
    return {k: v for k, v in payload.items() if v is not None or k in ("mission_name", "mission_started_at", "max_players")}


def _started_at(mission: dict[str, Any], now: datetime) -> str | None:
    uptime = mission.get("uptime")
    if not isinstance(uptime, int | float) or isinstance(uptime, bool) or uptime < 0:
        return None
    started = (now - timedelta(seconds=uptime)).replace(microsecond=0)
    return started.strftime("%Y-%m-%dT%H:%M:%SZ")


def map_weather(w: Any) -> dict[str, Any] | None:
    if not isinstance(w, dict):
        return None
    conv = (("temperature", "temperature_c", float), ("pressure", "qnh_hpa", mmhg_to_hpa),
            ("wind_direction", "wind_dir_deg", float), ("wind_speed", "wind_speed_ms", knots_to_ms),
            ("visibility", "visibility_m", float), ("clouds_base", "cloud_base_m", feet_to_m))
    out: dict[str, Any] = {}
    for src, dst, fn in conv:
        v = w.get(src)
        if isinstance(v, int | float) and not isinstance(v, bool):
            out[dst] = fn(v)
    return out or None
