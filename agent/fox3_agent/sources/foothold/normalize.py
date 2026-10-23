"""Parsed Foothold persistence dict -> `foothold_state` contract payload (+ player positions kept apart)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .coerce import Notes, items
from .norm_misc import normalize_accounts, normalize_missions
from .norm_players import normalize_ejected, normalize_player_stats, normalize_positions
from .norm_zones import mark_at_risk, normalize_connections, normalize_zones

KNOWN_TOP_KEYS = frozenset({
    "zones", "zonesDetails", "playerStats", "playerStatsIdentityVersion", "ejectedPilots", "missions", "connections", "players",
    "accounts", "shops", "tankers", "customFlags", "ewrsSettings", "difficultyModifier",
})
_NAME_RULE = re.compile(r"^foothold[_\- ]+(?P<mission>.+?)\.lua$", re.IGNORECASE)


@dataclass(frozen=True)
class Normalized:
    payload: dict
    positions: list[dict] = field(default_factory=list)


def mission_name_from_filename(file_name: str) -> str | None:
    """Rule (assumption): Foothold names its save `Foothold_<mission>.lua`; the part after the prefix is the mission.
    Anything else (plain `foothold.lua`, other names) gives None rather than a guess."""
    m = _NAME_RULE.match(file_name)
    return m.group("mission") if m else None


def normalize(parsed: dict, *, source_file: str, source_mtime: str, snapshot_at: str) -> Normalized:
    """`source_file` is reduced to its file name (no server paths leave the machine)."""
    notes = Notes()
    unknown = sorted(str(k) for k in parsed if k not in KNOWN_TOP_KEYS)
    if unknown:
        notes.add("unknown top-level keys ignored: " + ", ".join(k[:40] for k in unknown[:20]))
    if "zones" not in parsed:
        notes.add("missing top-level key: zones")
    file_name = re.split(r"[\\/]", source_file)[-1]
    zones = normalize_zones(parsed.get("zones"), parsed.get("zonesDetails"), notes)
    connections = normalize_connections(parsed.get("connections"), notes)
    mark_at_risk(zones, connections)
    payload: dict[str, Any] = {
        "snapshot_at": snapshot_at,
        "source_file": file_name,
        "source_mtime": source_mtime,
        "foothold_version": None,
        "mission_name": mission_name_from_filename(file_name),
        "zones": zones,
        "connections": connections,
        "missions": normalize_missions(parsed.get("missions"), notes),
        "player_stats": normalize_player_stats(parsed.get("playerStats"), parsed.get("playerStatsIdentityVersion"), notes),
        "accounts": normalize_accounts(parsed.get("accounts")),
        "ejected_pilots": normalize_ejected(parsed.get("ejectedPilots"), notes),
    }
    positions = normalize_positions(parsed.get("players"), notes)
    if not items(parsed.get("zones")):
        notes.add("zones table is empty")
    payload["format_notes"] = notes.as_list()
    return Normalized(payload, positions)
