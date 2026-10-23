"""Per-aircraft validation rules (limits, kinds, required fields). Run only on structurally valid models."""
from __future__ import annotations

from typing import Any

from . import ah64, f14, f16
from .aircraft import AIRCRAFT


def _f16(model: dict[str, Any]) -> list[str]:
    errs = []
    limit = AIRCRAFT["F-16C_50"].limits["waypoints"]
    n = len(model.get("waypoints", []))
    if n > limit:
        errs.append(f"F-16C_50 allows at most {limit} steerpoints (owner's description, unverified); got {n}")
    if len(model.get("lines", [])) > f16.LINE_COUNT:
        errs.append(f"F-16C_50 allows at most {f16.LINE_COUNT} lines; got {len(model['lines'])}")
    return errs


def _f14(model: dict[str, Any]) -> list[str]:
    errs = []
    routes = model.get("routes", [])
    if len(routes) > f14.ROUTE_SLOTS:
        errs.append(f"F-14BU allows at most {f14.ROUTE_SLOTS} routes; got {len(routes)}")
    for i, r in enumerate(routes):
        if not isinstance(r.get("name"), str) or not isinstance(r.get("points"), list):
            errs.append(f"routes[{i}]: name (string) and points (list) are required")
    lines = model.get("lines", [])
    line_route = model.get("aircraft_extra", {}).get("f14", {}).get("line_route", [])
    if lines and (len(line_route) != len(lines) or any(not isinstance(r, int) or not 0 <= r < f14.ROUTE_SLOTS for r in line_route)):
        errs.append("F-14BU: aircraft_extra.f14.line_route must give a route slot (0-11) for every line")
    return errs


def _ah64(model: dict[str, Any]) -> list[str]:
    errs = []
    for i, p in enumerate(model.get("waypoints", [])):
        if p.get("kind") not in ah64.KINDS:
            errs.append(f"waypoints[{i}]: kind must be one of {', '.join(ah64.KINDS)}")
        if p.get("extra", {}).get("mission", 1) not in ah64.MISSIONS:
            errs.append(f"waypoints[{i}]: extra.mission must be 1 or 2")
    return errs


_RULES = {"F-16C_50": _f16, "F-14BU": _f14, "AH-64D_BLK_II": _ah64}


def aircraft_rules(model: dict[str, Any]) -> list[str]:
    return _RULES[model["aircraft"]](model)
