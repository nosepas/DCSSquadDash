"""Build the built-in DTC templates from the owner's sample files (samples/ is git-ignored).

Usage: python tools/make_templates.py [samples_dir]

Only mission-specific navigation content is emptied (points/lines/routes) and free-text cartridge names are reset; every
other value is copied untouched. Also prints a review report (top-level keys and string values that could be personal).
"""
from __future__ import annotations

import gzip
import json
import sys
from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "dtc"), str(ROOT / "common")]

from fox3_dtc.templates import FILES  # noqa: E402


def _load(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _neutral(point: dict[str, Any], **over: Any) -> dict[str, Any]:
    """Example point with position/text neutralised (these are always overwritten on export)."""
    p = deepcopy(point)
    for k in ("x", "y", "alt", "elev", "lat", "lon"):
        if k in p:
            p[k] = 0
    for k in ("note", "name"):
        if k in p:
            p[k] = ""
    p.update(over)
    return p


def f16(src: dict[str, Any]) -> dict[str, Any]:
    mpd = src["data"]["MPD"]
    defaults = {"steerpoint": _neutral(mpd["NAV_PTS"][0]), "geo_line": _neutral(mpd["GEO_LINES"][0])}
    mpd["NAV_PTS"], mpd["GEO_LINES"] = [], []
    mpd["THREAT_PTS"], mpd["DEST"] = [], []
    return {"template": src, "defaults": defaults}


def f14(srcs: list[dict[str, Any]]) -> dict[str, Any]:
    defaults: dict[str, Any] = {}
    for src in srcs:
        for slot in src["data"]["NAV"]:
            if slot["waypoints"]:
                defaults.setdefault("waypoint", _neutral(slot["waypoints"][0]))
            if slot["lines"]:
                defaults.setdefault("line_point", _neutral(slot["lines"][0]["points"][0]))
    tpl = srcs[0]
    for slot in tpl["data"]["NAV"]:
        slot.update(name="", route_as_line=False, waypoints=[], lines=[])
    tpl["data"]["cartridge_name"] = "DEFAULT"
    defaults["slot"] = deepcopy(tpl["data"]["NAV"][0])
    return {"template": tpl, "defaults": defaults}


def ah64(src: dict[str, Any]) -> dict[str, Any]:
    defaults: dict[str, Any] = {}
    for m in ("Mission_1", "Mission_2"):
        for kind, grp in src["data"]["NAV"][m]["Points"].items():
            if grp["POINTS"]:
                defaults.setdefault(kind, _neutral(grp["POINTS"][0], text=""))
            grp["POINTS"] = []
    return {"template": src, "defaults": defaults}


def report(name: str, bundle: dict[str, Any]) -> None:
    data = bundle["template"]["data"]
    print(f"\n== {name}: top-level keys of data: {', '.join(data)}")
    found: dict[str, set[str]] = defaultdict(set)

    def walk(o: Any, key: str) -> None:
        if isinstance(o, dict):
            for k, v in o.items():
                walk(v, k)
        elif isinstance(o, list):
            for v in o:
                walk(v, key)
        elif isinstance(o, str) and o:
            found[key].add(o)

    walk(bundle, "")
    for key, vals in sorted(found.items()):
        shown = sorted(vals)[:5]
        print(f"   string '{key}': {len(vals)} distinct, e.g. {shown}")


def main(argv: list[str]) -> int:
    samples = Path(argv[1]) if len(argv) > 1 else ROOT / "samples"
    out_dir = ROOT / "dtc" / "fox3_dtc" / "templates"
    if not samples.is_dir():
        print(f"samples folder not found: {samples}")
        return 1
    f14_files = [_load(samples / "F-14BU_DTC.dtc"), _load(samples / "F-14BU_DTC modernos.dtc")]
    bundles = {"F-16C_50": f16(_load(samples / "F-16C_50_DTC.dtc")), "F-14BU": f14(f14_files),
               "AH-64D_BLK_II": ah64(_load(samples / "AH-64D_BLK_II_DTC.dtc"))}
    for aircraft, bundle in bundles.items():
        raw = json.dumps(bundle, ensure_ascii=False).encode("utf-8")
        (out_dir / FILES[aircraft]).write_bytes(gzip.compress(raw, mtime=0))
        report(aircraft, bundle)
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
