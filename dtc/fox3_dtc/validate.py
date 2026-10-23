"""Model validation: human-readable messages, never raises."""
from __future__ import annotations

from collections import Counter
from typing import Any

from fox3_common import geo

from .aircraft import AIRCRAFT
from .model import is_number
from .radio_check import radio_errors
from .rules import aircraft_rules

_PARTS = ("waypoints", "routes", "lines")


def _point_errors(p: Any, where: str) -> list[str]:
    if not isinstance(p, dict):
        return [f"{where}: not an object"]
    errs = []
    for key, lo, hi in (("lat", -90, 90), ("lon", -180, 180)):
        v = p.get(key)
        if not is_number(v):
            errs.append(f"{where}: {key} is required and must be a number")
        elif not lo <= v <= hi:
            errs.append(f"{where}: {key} {v} outside [{lo}, {hi}]")
    el = p.get("elevation_m")
    if el is not None and not is_number(el):
        errs.append(f"{where}: elevation_m must be a number or null")
    if "extra" in p and not isinstance(p["extra"], dict):
        errs.append(f"{where}: extra must be an object")
    return errs


def all_points(model: dict[str, Any]) -> list[tuple[str, Any]]:
    out = [(f"waypoints[{i}]", p) for i, p in enumerate(model.get("waypoints") or [])]
    for i, r in enumerate(model.get("routes") or []):
        if isinstance(r, dict):
            out += [(f"routes[{i}].points[{j}]", p) for j, p in enumerate(r.get("points") or [])]
    for i, ln in enumerate(model.get("lines") or []):
        if isinstance(ln, dict):
            out += [(f"lines[{i}].points[{j}]", p) for j, p in enumerate(ln.get("points") or [])]
    return out


def validate_model(model: Any) -> list[str]:
    """All problems found in a neutral model (empty list = exportable)."""
    if not isinstance(model, dict):
        return ["model must be an object"]
    info = AIRCRAFT.get(model.get("aircraft"))
    if info is None:
        return [f"unknown aircraft {model.get('aircraft')!r}"]
    if not info.enabled:
        return [f"aircraft {info.id} is not supported yet (no sample file exists)"]
    errs: list[str] = []
    if model.get("terrain") not in geo.PARAMS:
        errs.append(f"terrain {model.get('terrain')!r} is missing or not calibrated (allowed: {', '.join(geo.PARAMS)})")
    for part in _PARTS:
        if not isinstance(model.get(part, []), list):
            errs.append(f"{part} must be a list")
        elif model.get(part) and part not in info.supports:
            errs.append(f"{info.id} does not support editing '{part}'")
    if errs and any("must be a list" in e for e in errs):
        return errs
    for where, p in all_points(model):
        errs += _point_errors(p, where)
    ids = Counter(p["id"] for _, p in all_points(model) if isinstance(p, dict) and p.get("id"))
    errs += [f"duplicate point id {i!r} ({n} times)" for i, n in ids.items() if n > 1]
    errs += radio_errors(model)
    return errs if errs else aircraft_rules(model)
