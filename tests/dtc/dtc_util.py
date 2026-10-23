"""Shared helpers for edit tests."""
from __future__ import annotations

import json
from typing import Any

from dtc_cases import CASES, F14_TERRAIN, load

from fox3_dtc import ImportResult, export_dtc, import_dtc


def cases_for(aircraft_key: str) -> list[str]:
    return [c for c in CASES if aircraft_key in c]


def prepare(case: str) -> ImportResult:
    aircraft, raw = load(case)
    res = import_dtc(raw)
    if aircraft == "F-14BU":
        res.model["terrain"] = F14_TERRAIN
    return res


def export_json(res: ImportResult) -> dict[str, Any]:
    return json.loads(export_dtc(res.model, res.template))


def diff_paths(a: Any, b: Any, path: tuple = ()) -> set[tuple]:
    """Paths (dict keys only; lists are leaves) where a and b differ."""
    if isinstance(a, dict) and isinstance(b, dict) and list(a) == list(b):
        out: set[tuple] = set()
        for k in a:
            out |= diff_paths(a[k], b[k], path + (k,))
        return out
    return set() if a == b else {path}


def only_under(paths: set[tuple], *allowed: tuple) -> bool:
    return all(any(p[: len(al)] == al for al in allowed) for p in paths)


def new_point(lat: float, lon: float, elev: float | None = 10, **kw: Any) -> dict[str, Any]:
    return {"lat": lat, "lon": lon, "elevation_m": elev, "extra": {}, **kw}
