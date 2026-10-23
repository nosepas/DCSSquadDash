"""F-16C_50 serializer: MPD.NAV_PTS (steerpoints) and MPD.GEO_LINES. THREAT_PTS / DEST are left untouched (structure unknown)."""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from . import convert
from .errors import DtcError
from .keys import check_keys, need
from .model import Point, make_point, num, split
from .numbering import renumber

FORMAT_VERSION = "f16c_50/sample-1"
AIRCRAFT_ID = "F-16C_50"
MAX_STEERPOINTS = 25  # from the owner's description (STPT1-25); NOT verified in game
LINE_COUNT = 4  # GEO_LINES entries carry flags L1..L4
_ID_KEYS = ("id", "idOA1", "idOA1_Line", "idOA2", "idOA2_Line")
_CONSUMED = ("x", "y", "alt", "note", "id", "number")
_LINE_FLAGS = tuple(f"L{i}" for i in range(1, LINE_COUNT + 1))


def _point(raw: dict[str, Any], terrain: str | None, keep: tuple[str, ...]) -> Point:
    lat, lon = convert.from_xy(terrain, raw["x"], raw["y"])
    extra = split(raw, _CONSUMED + keep)
    extra[convert.XY_KEY] = [raw["x"], raw["y"]]
    return make_point(lat, lon, raw.get("alt"), note=raw.get("note", ""), pid=raw.get("id"), extra=extra)


def _mpd(template: dict[str, Any]) -> dict[str, Any]:
    return template["data"]["MPD"]


def collect_defaults(template: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    mpd = _mpd(template)
    for key, name in (("NAV_PTS", "steerpoint"), ("GEO_LINES", "geo_line")):
        if mpd.get(key):
            out[name] = deepcopy(mpd[key][0])
    return out


def to_model(template: dict[str, Any], terrain: str | None) -> tuple[dict[str, Any], list[str]]:
    mpd = _mpd(template)
    warns = need(mpd, "NAV_PTS", "MPD") + need(mpd, "GEO_LINES", "MPD")
    nav, geo_lines = mpd.get("NAV_PTS", []), mpd.get("GEO_LINES", [])
    warns += check_keys(nav, "MPD.NAV_PTS") + check_keys(geo_lines, "MPD.GEO_LINES")
    waypoints = [_point(p, terrain, ()) for p in nav if isinstance(p, dict)]
    lines: list[dict[str, Any]] = [{"name": f"L{i}", "points": []} for i in range(1, LINE_COUNT + 1)]
    for g in geo_lines:
        flags = [i for i, f in enumerate(_LINE_FLAGS) if g.get(f)]
        if len(flags) != 1:
            warns.append(f"MPD.GEO_LINES entry {g.get('id')!r} is in {len(flags)} lines; placed in line {(flags or [0])[0] + 1} only")
        lines[(flags or [0])[0]]["points"].append(_point(g, terrain, _LINE_FLAGS))
    return {"waypoints": waypoints, "lines": lines}, warns


def _build(p: Point, base: dict[str, Any], terrain: str, n: int, warns: list[str], where: str, keep_flags: dict[str, Any]) -> dict[str, Any]:
    out = deepcopy(base)
    out.update({k: v for k, v in p.get("extra", {}).items() if k != convert.XY_KEY and k not in _ID_KEYS})
    out.update(keep_flags)
    out["x"], out["y"] = convert.to_xy(terrain, p)
    elev = p.get("elevation_m")
    if elev is None:
        warns.append(f"{where}: elevation unknown, 0 written")
    out["alt"] = num(elev or 0)
    out["note"] = p.get("note") or ""
    return renumber(out, "number", _ID_KEYS, n)


def apply(model: dict[str, Any], template: dict[str, Any], defaults: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    for name, what in (("steerpoint", "NAV_PTS"), ("geo_line", "GEO_LINES")):
        if name not in defaults:
            raise DtcError([f"cannot add MPD.{what} entries: the template has no example entry; supply a .dtc with at least one"])
    out, warns, terrain = deepcopy(template), [], model["terrain"]
    out["data"]["terrain"] = _mpd(out)["terrain"] = terrain
    wps = model.get("waypoints", [])
    nav = [_build(p, defaults["steerpoint"], terrain, i, warns, f"waypoint {i}", {}) for i, p in enumerate(wps, 1)]
    geo: list[dict[str, Any]] = []
    for li, line in enumerate(model.get("lines", [])):
        for p in line["points"]:
            flags = {f: (j == li) for j, f in enumerate(_LINE_FLAGS)}
            geo.append(_build(p, defaults["geo_line"], terrain, len(geo) + 1, warns, f"line {li + 1} point", flags))
    _mpd(out)["NAV_PTS"], _mpd(out)["GEO_LINES"] = nav, geo
    return out, warns
