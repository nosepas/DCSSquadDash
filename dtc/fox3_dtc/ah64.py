"""AH-64D_BLK_II serializer: data.NAV.Mission_1/Mission_2 .Points.{CTRLM,TGT,WPTHZ}. Routes, Zones, Areas, Lines, ADF: untouched.

Model mapping: every point is a model waypoint with kind CTRLM|TGT|WPTHZ and extra['mission'] in (1, 2). Waypoints are
ordered mission 1 (CTRLM, TGT, WPTHZ) then mission 2; `num` restarts at 1 in each (mission, kind) group.
aircraft_extra['ah64']['enabled'] = {"1": {"CTRLM": bool, ...}, "2": {...}} mirrors each group's `isEnabled`.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from . import convert
from .errors import DtcError
from .keys import check_keys
from .model import Point, make_point, num

FORMAT_VERSION = "ah64d_blk_ii/sample-1"
AIRCRAFT_ID = "AH-64D_BLK_II"
KINDS = ("CTRLM", "TGT", "WPTHZ")
MISSIONS = (1, 2)
_CONSUMED = ("x", "y", "alt", "note", "num", "text")
_CODE_PREFIX = {"TGT": "T", "WPTHZ": "W"}  # inferred from samples: default text T01 / W01


def _groups(template: dict[str, Any]) -> dict[tuple[int, str], dict[str, Any]]:
    nav = template["data"]["NAV"]
    return {(m, k): nav[f"Mission_{m}"]["Points"][k] for m in MISSIONS for k in KINDS
            if k in nav.get(f"Mission_{m}", {}).get("Points", {})}


def collect_defaults(template: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for (_, kind), grp in _groups(template).items():
        if grp.get("POINTS") and kind not in out:
            out[kind] = deepcopy(grp["POINTS"][0])
    return out


def to_model(template: dict[str, Any], terrain: str | None) -> tuple[dict[str, Any], list[str]]:
    warns: list[str] = []
    if "NAV" not in template["data"]:
        return {"waypoints": [], "aircraft_extra": {}}, ["data: missing key 'NAV'"]
    points: list[Point] = []
    enabled: dict[str, dict[str, bool]] = {}
    groups = _groups(template)
    for m in MISSIONS:
        for k in KINDS:
            grp = groups.get((m, k))
            if grp is None:
                warns.append(f"NAV.Mission_{m}.Points.{k} is missing")
                continue
            enabled.setdefault(str(m), {})[k] = bool(grp.get("isEnabled"))
            warns += check_keys(grp.get("POINTS", []), f"NAV.Mission_{m}.Points.{k}.POINTS")
            for raw in grp.get("POINTS", []):
                lat, lon = convert.from_xy(terrain, raw["x"], raw["y"])
                extra = {k2: v for k2, v in raw.items() if k2 not in _CONSUMED}
                extra.update({"mission": m, convert.XY_KEY: [raw["x"], raw["y"]]})
                points.append(make_point(lat, lon, raw.get("alt"), name=raw.get("text", ""), note=raw.get("note", ""), kind=k, extra=extra))
    return {"waypoints": points, "aircraft_extra": {"ah64": {"enabled": enabled}}}, warns


def _build(p: Point, base: dict[str, Any], terrain: str, n: int, warns: list[str], where: str) -> dict[str, Any]:
    out = deepcopy(base)
    out.update({k: v for k, v in p.get("extra", {}).items() if k not in (convert.XY_KEY, "mission")})
    out["x"], out["y"] = convert.to_xy(terrain, p)
    if p.get("elevation_m") is None:
        warns.append(f"{where}: elevation unknown, 0 written")
    out["alt"] = num(p.get("elevation_m") or 0)
    out["note"] = p.get("note") or ""
    out["num"] = n
    code = _CODE_PREFIX.get(p["kind"])
    out["text"] = p.get("name", f"{code}{n:02d}" if code else "")
    return out


def apply(model: dict[str, Any], template: dict[str, Any], defaults: dict[str, Any]) -> tuple[dict[str, Any], list[str]]:
    out, warns, terrain = deepcopy(template), [], model["terrain"]
    out["data"]["terrain"] = terrain
    enabled = model.get("aircraft_extra", {}).get("ah64", {}).get("enabled", {})
    for m in MISSIONS:
        for k in KINDS:
            pts = [p for p in model.get("waypoints", []) if p["kind"] == k and p.get("extra", {}).get("mission", 1) == m]
            if pts and k not in defaults:
                raise DtcError([f"cannot add AH-64 {k} points: the template has no example {k} point; supply a .dtc with at least one"])
            grp = out["data"]["NAV"][f"Mission_{m}"]["Points"][k]
            grp["POINTS"] = [_build(p, defaults[k], terrain, i, warns, f"Mission_{m} {k} {i}") for i, p in enumerate(pts, 1)]
            if k in enabled.get(str(m), {}):
                grp["isEnabled"] = bool(enabled[str(m)][k])
    return out, warns
