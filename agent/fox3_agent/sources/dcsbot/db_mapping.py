"""missionstats row -> contract event.

Verified against DCSServerBot v3.0.4.27 (plugins/missionstats): `event` holds the DCS world.event key
(S_EVENT_KILL, S_EVENT_PILOT_DEAD, S_EVENT_TAKEOFF, S_EVENT_LAND, S_EVENT_CRASH, S_EVENT_EJECT [S_EVENT_EJECTION in DCS]);
init_side/target_side hold DCS coalition ids (0 neutral, 1 red, 2 blue, 3 neutral); init_id/target_id are the player
ucid or NULL for AI units (AI rows exist only with persist_ai_statistics).
"""
from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import Any

EVENT_TYPES = {
    "S_EVENT_KILL": "kill",
    "S_EVENT_PILOT_DEAD": "death",
    "S_EVENT_TAKEOFF": "takeoff",
    "S_EVENT_LAND": "landing",
    "S_EVENT_CRASH": "crash",
    "S_EVENT_EJECT": "eject",
    "S_EVENT_EJECTION": "eject",
}
_SIDES = {"0": "neutral", "3": "neutral", "1": "red", "2": "blue", "red": "red", "blue": "blue", "neutral": "neutral"}


def coalition_from_side(side: Any) -> str:
    return _SIDES.get(str(side).strip().lower(), "unknown") if side is not None else "unknown"


def to_utc_iso(value: Any) -> str:
    """Row time is a naive UTC timestamp (datetime on PostgreSQL, text on SQLite)."""
    dt = value if isinstance(value, datetime) else datetime.fromisoformat(str(value))
    dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _party(ucid: Any, name: Any, side: Any, unit_type: Any) -> dict[str, Any] | None:
    if ucid is None and name is None and side is None and unit_type is None:
        return None
    return {"ucid": ucid or None, "name": name or None, "coalition": coalition_from_side(side),
            "unit_type": unit_type or None, "is_player": bool(ucid)}


def map_row(row: Any) -> dict[str, Any] | None:
    """Returns None for event names the contract does not know."""
    etype = EVENT_TYPES.get(row.event)
    if etype is None:
        return None
    event: dict[str, Any] = {"event_id": f"dcsbot-{row.id}", "type": etype, "time_utc": to_utc_iso(row.time),
                             "actor": _party(row.init_id, row.init_name, row.init_side, row.init_type)}
    if etype == "kill":
        event["target"] = _party(row.target_id, row.target_name, row.target_side, row.target_type)
        event["weapon"] = row.weapon or None
    if row.place:
        event["data"] = {"place": row.place}   # airbase for takeoff/land: not a Foothold zone, so `zone` stays unset
    return event


# DCSServerBot `players` columns holding the verified link (discord_id = -1 means "not linked").
LINK_COLUMNS = ("ucid", "discord_id")
_SNOWFLAKE = re.compile(r"[1-9][0-9]{16,19}")
_MAX_INT64 = 2**63 - 1


def map_link_row(ucid: Any, discord_id: Any) -> tuple[str, str] | None:
    """(ucid, discord_id) -> validated pair, or None when the row is not a usable link."""
    if not isinstance(ucid, str) or not 8 <= len(ucid) <= 64 or isinstance(discord_id, bool):
        return None
    text = str(discord_id).strip()
    if not _SNOWFLAKE.fullmatch(text) or int(text) > _MAX_INT64:
        return None
    return ucid, text
