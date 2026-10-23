"""F-14BU serializer: data.NAV, 12 route slots, each with waypoints and lines. `additional_points` are left untouched (unknown).

Model mapping: routes[i] <-> NAV[i] (slot index kept, empty slots have name ""); every line of every route is a top-level
model line, and aircraft_extra['f14']['line_route'][j] is the slot of line j; ['route_as_line'][i] is NAV[i].route_as_line.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from . import convert
from .errors import DtcError
from .keys import check_keys, need
from .model import Point, make_point, num

FORMAT_VERSION = "f14bu/sample-1"
AIRCRAFT_ID = "F-14BU"
ROUTE_SLOTS = 12
_WP_CONSUMED = ("lat", "lon", "x", "y", "elev", "name")
_LP_CONSUMED = ("lat", "lon", "x", "y", "elev")


def _point(raw: dict[str, Any], consumed: tuple[str, ...], named: bool) -> Point:
    extra = {k: v for k, v in raw.items() if k not in consumed}
    extra[convert.XY_KEY] = [raw["x"], raw["y"]]
    return make_point(raw["lat"], raw["lon"], raw.get("elev"), name=raw.get("name") if named else None, extra=extra)


def collect_defaults(template: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for slot in template["data"].get("NAV", []):
        if slot.get("waypoints") and "waypoint" not in out:
            out["waypoint"] = deepcopy(slot["waypoints"][0])
        if slot.get("lines") and "line_point" not in out and slot["lines"][0].get("points"):
            out["line_point"] = deepcopy(slot["lines"][0]["points"][0])
        if "slot" not in out:
            out["slot"] = {**deepcopy(slot), "name": "", "route_as_line": False, "waypoints": [], "lines": []}
    return out


def to_model(template: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    nav = template["data"].get("NAV", [])
    warns = need(template["data"], "NAV", "data")
    if len(nav) != ROUTE_SLOTS:
        warns.append(f"data.NAV has {len(nav)} routes, expected {ROUTE_SLOTS}")
    warns += check_keys(nav, "data.NAV", {"additional_points", "lines", "name", "route_as_line", "waypoints"})
    routes, lines, line_route, as_line = [], [], [], []
    for i, slot in enumerate(nav):
        routes.append({"name": slot.get("name", ""), "points": [_point(w, _WP_CONSUMED, True) for w in slot.get("waypoints", [])]})
        as_line.append(bool(slot.get("route_as_line")))
        for ln in slot.get("lines", []):
            lines.append({"name": "", "closed": bool(ln.get("closed")), "points": [_point(p, _LP_CONSUMED, False) for p in ln["points"]]})
            line_route.append(i)
    extra = {"f14": {"route_as_line": as_line, "line_route": line_route}}
    return {"routes": routes, "lines": lines, "aircraft_extra": extra}, warns


def _dcs_point(base: dict[str, Any], p: Point, terrain: str, warns: list[str], where: str, named: bool) -> dict[str, Any]:
    out = deepcopy(base)
    out.update({k: v for k, v in p.get("extra", {}).items() if k != convert.XY_KEY})
    out["lat"], out["lon"] = p["lat"], p["lon"]
    out["x"], out["y"] = convert.to_xy(terrain, p)
    if p.get("elevation_m") is None:
        warns.append(f"{where}: elevation unknown, 0 written")
    out["elev"] = num(p.get("elevation_m") or 0)
    if named:
        out["name"] = p.get("name") or ""
    return out


def _line(ln: dict[str, Any], defaults: dict[str, Any], terrain: str, warns: list[str], where: str) -> dict[str, Any]:
    return {"closed": bool(ln.get("closed")), "points": [_dcs_point(defaults["line_point"], p, terrain, warns, where, False) for p in ln["points"]]}


def apply(model: dict[str, Any], template: dict[str, Any], defaults: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    for key, what in (("waypoint", "waypoints"), ("line_point", "line points"), ("slot", "route slots")):
        if key not in defaults and _needs(model, template, key):
            raise DtcError([f"cannot add F-14 {what}: the template has no example; supply a .dtc with at least one"])
    out, warns, terrain = deepcopy(template), [], model["terrain"]
    meta = model.get("aircraft_extra", {}).get("f14", {})
    as_line, line_route = meta.get("route_as_line", []), meta.get("line_route", [])
    old = template["data"].get("NAV", [])
    nav = []
    for i in range(ROUTE_SLOTS):
        slot = deepcopy(old[i]) if i < len(old) else deepcopy(defaults["slot"])
        route = model["routes"][i] if i < len(model.get("routes", [])) else {"name": "", "points": []}
        slot["name"] = route["name"]
        slot["route_as_line"] = bool(as_line[i]) if i < len(as_line) else False
        slot["waypoints"] = [_dcs_point(defaults["waypoint"], p, terrain, warns, f"route {i + 1} waypoint {j}", True)
                             for j, p in enumerate(route["points"], 1)]
        mine = [ln for ln, r in zip(model.get("lines", []), line_route, strict=False) if r == i]
        slot["lines"] = [_line(ln, defaults, terrain, warns, f"route {i + 1} line point") for ln in mine]
        nav.append(slot)
    out["data"]["NAV"] = nav
    return out, warns


def _needs(model: dict[str, Any], template: dict[str, Any], key: str) -> bool:
    if key == "waypoint":
        return any(r["points"] for r in model.get("routes", []))
    if key == "line_point":
        return any(ln["points"] for ln in model.get("lines", []))
    return len(template["data"].get("NAV", [])) < ROUTE_SLOTS
