"""Helpers to build and read neutral-model points (contracts/schemas/dtc_mission.json)."""
from __future__ import annotations

from typing import Any

MODEL_VERSION = 1
Point = dict[str, Any]


def num(value: float) -> int | float:
    """Clean a number for output: integral -> int, else 14 significant digits (the precision DCS itself writes)."""
    if isinstance(value, bool):
        raise TypeError("bool is not a number")
    if isinstance(value, int) or float(value).is_integer():
        return int(value)
    return float(f"{float(value):.14g}")


def is_number(value: Any) -> bool:
    return isinstance(value, int | float) and not isinstance(value, bool)


def make_point(lat: float, lon: float, elevation: float | None, *, name: str | None = None, note: str | None = None,
               pid: str | None = None, kind: str | None = None, extra: dict[str, Any] | None = None) -> Point:
    """Neutral point; optional fields are omitted when None."""
    p: Point = {"lat": lat, "lon": lon, "elevation_m": elevation}
    for key, val in (("name", name), ("note", note), ("id", pid), ("kind", kind)):
        if val is not None:
            p[key] = val
    p["extra"] = dict(extra or {})
    return p


def split(src: dict[str, Any], consumed: tuple[str, ...]) -> dict[str, Any]:
    """Fields of `src` not consumed by the neutral mapping, kept verbatim as the point's `extra`."""
    return {k: v for k, v in src.items() if k not in consumed}


def empty_model(aircraft: str, terrain: str | None) -> dict[str, Any]:
    return {"model_version": MODEL_VERSION, "terrain": terrain, "aircraft": aircraft, "dcs_version": None,
            "waypoints": [], "routes": [], "lines": [], "aircraft_extra": {}}
