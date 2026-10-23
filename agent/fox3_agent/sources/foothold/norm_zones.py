"""Zones and supply connections of the persistence file -> contract shapes."""
from __future__ import annotations

from typing import Any

from .coerce import Notes, flag, get, integer, items, lat_lon, num, text

KNOWN_ZONE_KEYS = frozenset({
    "side", "active", "level", "upgradesUsed", "upgradesUsedRed", "upgradesUsedBlue", "logisticCenter", "firstCaptureByRed",
    "wasBlue", "lat_long", "remainingUnits", "destroyed", "extraUpgrade", "triggers", "randomUpgradesRed", "randomUpgradesBlue",
})
_COALITIONS = {0: "neutral", 1: "red", 2: "blue"}
MAX_TRIGGERS = 20


def count_units(remaining: Any) -> int:
    """remainingUnits is group -> slot -> unit type: count the slots (units) over all groups."""
    return sum(len(items(group)) if isinstance(group, (dict, list)) else 1 for _, group in items(remaining))


def _geo(lat_long: Any) -> dict | None:
    pos = lat_lon(get(lat_long, "latitude"), get(lat_long, "longitude"))
    if pos is None:
        return None
    geo = {"lat": pos[0], "lon": pos[1]}
    alt = num(get(lat_long, "altitude"))
    if alt is not None:
        geo["alt_m"] = alt
    return geo


def _extra(rec: dict, detail: Any) -> dict:
    extra: dict[str, Any] = {}
    for src, dst in (("wasBlue", "was_blue"), ("firstCaptureByRed", "first_capture_by_red")):
        if flag(rec.get(src)) is not None:
            extra[dst] = rec[src]
    for src, dst in (("upgradesUsedRed", "upgrades_used_red"), ("upgradesUsedBlue", "upgrades_used_blue")):
        if integer(rec.get(src)) is not None:
            extra[dst] = integer(rec[src])
    if flag(get(detail, "hidden")) is not None:
        extra["hidden"] = detail["hidden"]
    if text(get(detail, "flavorText"), 120) is not None:
        extra["flavor_text"] = text(detail["flavorText"], 120)
    triggers = {str(k): v for k, v in items(rec.get("triggers"))[:MAX_TRIGGERS] if flag(v) is not None or num(v) is not None}
    if triggers:
        extra["triggers"] = triggers
    if items(rec.get("destroyed")):
        extra["destroyed_count"] = len(items(rec["destroyed"]))
    return extra


def normalize_zones(zones: Any, details: Any, notes: Notes) -> list[dict]:
    out: list[dict] = []
    dropped = unknown_side = bad_geo = 0
    unknown_keys: set[str] = set()
    detail_map = dict(items(details))
    for key, rec in items(zones):
        if not isinstance(rec, dict) or isinstance(key, bool):
            dropped += 1
            continue
        unknown_keys.update(str(k) for k in rec if k not in KNOWN_ZONE_KEYS)
        side = integer(rec.get("side"))
        coalition = _COALITIONS.get(side) if side is not None else None
        if coalition is None:
            unknown_side += 1
        zone: dict[str, Any] = {"name": str(key), "coalition": coalition or "unknown"}
        geo = _geo(rec.get("lat_long"))
        if geo:
            zone["geo"] = geo
        elif "lat_long" in rec:
            bad_geo += 1
        zone["level"] = integer(rec.get("level"))
        if flag(rec.get("active")) is not None:
            zone["active"] = rec["active"]
        if flag(rec.get("logisticCenter")) is not None:
            zone["logistic_center"] = rec["logisticCenter"]
        if "remainingUnits" in rec:
            zone["units_remaining"] = count_units(rec["remainingUnits"])
        used = integer(rec.get("upgradesUsed"))
        if used is not None and used >= 0:
            zone["upgrades_used"] = used
        zone["extra"] = _extra(rec, detail_map.get(key))
        out.append(zone)
    notes.dropped("zones", dropped, "non-table entries")
    if unknown_side:
        notes.add(f"zones: {unknown_side} entries with a missing or unknown side (coalition 'unknown')")
    notes.dropped("zones", bad_geo, "invalid lat_long values")
    if unknown_keys:
        notes.add("zones: unknown keys ignored: " + ", ".join(sorted(unknown_keys)[:15]))
    return out


def normalize_connections(raw: Any, notes: Notes) -> list[dict]:
    out, dropped = [], 0
    for _, rec in items(raw):
        a, b = get(rec, "from"), get(rec, "to")
        if isinstance(a, str) and isinstance(b, str) and a and b:
            out.append({"from": a, "to": b})
        else:
            dropped += 1
    notes.dropped("connections", dropped)
    return out


def mark_at_risk(zones: list[dict], connections: list[dict]) -> None:
    """DERIVED, not read from the file: a red/blue zone is `at_risk` when a supply connection links it to a zone of
    the opposite coalition. Only set when the file has connections (otherwise there is nothing to derive it from)."""
    if not connections:
        return
    side = {z["name"]: z["coalition"] for z in zones}
    exposed: set[str] = set()
    for c in connections:
        a, b = side.get(c["from"]), side.get(c["to"])
        if {a, b} == {"red", "blue"}:
            exposed.update((c["from"], c["to"]))
    for z in zones:
        if z["coalition"] in ("red", "blue"):
            z["at_risk"] = z["name"] in exposed
