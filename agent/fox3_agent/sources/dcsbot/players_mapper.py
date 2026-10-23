"""DCSServerBot ServerInfo.players -> contract `players` payload. Callsign, radios and slot data are never forwarded."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from .ucid_resolver import UcidResolver

_SIDES = {"blue": "blue", "red": "red", "neutral": "neutral", "2": "blue", "1": "red"}


def coalition_of(side: Any) -> str:
    return _SIDES.get(str(side).strip().lower(), "unknown")


def map_players(raw_players: list[Any], resolver: UcidResolver, now: datetime) -> tuple[dict[str, Any], int]:
    """Returns (payload, unresolved_count). Players without a resolvable ucid are omitted."""
    resolver.new_cycle()
    players: list[dict[str, Any]] = []
    unresolved = 0
    for p in raw_players:
        name = p.get("nick") if isinstance(p, dict) else None
        if not isinstance(name, str) or not name:
            continue
        ucid = resolver.resolve(name)
        if not ucid:
            unresolved += 1
            continue
        unit = p.get("unit_type")
        players.append({"ucid": ucid, "name": name, "coalition": coalition_of(p.get("side")),
                        "aircraft": unit if isinstance(unit, str) and unit else None, "slot": None, "in_air": False})
    payload = {"snapshot_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"), "players": players}
    return payload, unresolved
