"""playerStats (both layouts), ejected pilots and live player positions."""
from __future__ import annotations

from typing import Any

from .coerce import Notes, get, items, lat_lon, num, text


def _figures(table: Any) -> dict[str, float]:
    return {str(k): v for k, v in items(table) if isinstance(k, str) and num(v) is not None}


def _identity_like(entry: Any) -> bool:
    return isinstance(entry, dict) and ("name" in entry or isinstance(entry.get("stats"), dict))


def _record(name: str, identifier: str | None, figures: dict[str, float]) -> dict:
    points = figures.pop("Points", None)
    return {"name": name, "ucid": None, "points": points, "stats": figures, "identifier": identifier}


def normalize_player_stats(raw: Any, version: Any, notes: Notes) -> list[dict]:
    """version None -> legacy layout (keyed by player name); 1 -> identity layout (keyed by identifier, nested
    `name` + `stats`); anything else -> decided entry by entry, with a note."""
    marker = num(version)
    if version is not None and marker != 1:
        shown = repr(marker) if marker is not None else f"<{type(version).__name__}>"
        notes.add(f"playerStats: unknown playerStatsIdentityVersion={shown}, layout detected per entry")
    out, dropped = [], 0
    for key, entry in items(raw):
        if not isinstance(entry, dict):
            dropped += 1
            continue
        key_s = str(key)
        if marker == 1 or (version is not None and _identity_like(entry)):
            name = text(entry.get("name"), 100)
            out.append(_record(name if name and name.strip() else key_s, key_s, _figures(entry.get("stats"))))
        else:
            out.append(_record(key_s, None, _figures(entry)))
    notes.dropped("playerStats", dropped)
    return out


def normalize_ejected(raw: Any, notes: Notes) -> list[dict]:
    out, dropped = [], 0
    for _, rec in items(raw):
        pos = lat_lon(get(rec, "latitude"), get(rec, "longitude"))
        if pos is None:
            dropped += 1
            continue
        pilot: dict[str, Any] = {"name": text(get(rec, "playerName"), 100), "lat": pos[0], "lon": pos[1]}
        if num(get(rec, "altitude")) is not None:
            pilot["alt_m"] = rec["altitude"]
        if num(get(rec, "lostCredits")) is not None:
            pilot["lost_credits"] = rec["lostCredits"]
        out.append(pilot)
    notes.dropped("ejectedPilots", dropped)
    return out


def normalize_positions(raw: Any, notes: Notes) -> list[dict]:
    """Live player positions (NOT part of the foothold_state contract: the agent merges them elsewhere)."""
    out, dropped = [], 0
    for _, rec in items(raw):
        pos = lat_lon(get(rec, "latitude"), get(rec, "longitude"))
        name = text(get(rec, "playerName"), 100)
        if pos is None or not name:
            dropped += 1
            continue
        coalition = get(rec, "coalition")
        out.append({
            "name": name,
            "coalition": coalition.lower() if isinstance(coalition, str) and coalition.lower() in ("red", "blue") else "unknown",
            "unit_type": text(get(rec, "unitType"), 60),
            "lat": pos[0],
            "lon": pos[1],
            "alt_m": num(get(rec, "altitude")),
        })
    notes.dropped("players", dropped)
    return out
