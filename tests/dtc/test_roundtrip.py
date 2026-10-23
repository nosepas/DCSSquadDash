"""Import -> export without edits is identical (byte-for-byte where DCS style is reproduced) on real samples and synthetic files."""
import json
from copy import deepcopy

import pytest
from dtc_cases import CASES, F14_TERRAIN, load

from fox3_common import geo
from fox3_dtc import export_dtc, import_dtc
from fox3_dtc.io import read_json, write_json


def _prep(case):
    aircraft, raw = load(case)
    res = import_dtc(raw)
    if aircraft == "F-14BU":
        assert res.model["terrain"] is None
        res.model["terrain"] = F14_TERRAIN
    return raw, res


@pytest.mark.parametrize("case", CASES)
def test_style_writer_is_byte_identical(case):
    _, raw = load(case)
    assert write_json(read_json(raw)) == raw


@pytest.mark.parametrize("case", CASES)
def test_unmodified_round_trip_is_identical(case):
    raw, res = _prep(case)
    out = export_dtc(res.model, res.template)
    assert json.loads(out) == json.loads(raw)
    assert out == raw


@pytest.mark.parametrize("case", CASES)
def test_import_does_not_mutate_template_and_export_does_not_either(case):
    raw, res = _prep(case)
    before = deepcopy(res.template)
    export_dtc(res.model, res.template)
    assert res.template == before == json.loads(raw)


@pytest.mark.parametrize("case", [c for c in CASES if "F-14" in c])
def test_f14_latlon_reproduces_original_xy(case):
    raw, res = _prep(case)
    for _, p in _all(res.model):
        p["extra"].pop("dcs_xy")  # force recomputation from lat/lon
    out = json.loads(export_dtc(res.model, res.template))
    orig = json.loads(raw)
    n = 0
    for so, sn in zip(orig["data"]["NAV"], out["data"]["NAV"], strict=True):
        pts_o = so["waypoints"] + [p for ln in so["lines"] for p in ln["points"]]
        pts_n = sn["waypoints"] + [p for ln in sn["lines"] for p in ln["points"]]
        for a, b in zip(pts_o, pts_n, strict=True):
            assert abs(a["x"] - b["x"]) < 0.01 and abs(a["y"] - b["y"]) < 0.01
            n += 1
    assert n > 0


def _all(model):
    from fox3_dtc.validate import all_points
    return all_points(model)


@pytest.mark.parametrize("case", [c for c in CASES if "F-16" in c or "AH-64" in c])
def test_xy_survive_latlon_conversion(case):
    """x/y -> lat/lon (rounded) -> x/y stays within a millimetre even when the original is not reused."""
    raw, res = _prep(case)
    terrain = res.model["terrain"]
    for _, p in _all(res.model):
        x, y = p["extra"]["dcs_xy"]
        bx, by = geo.latlon_to_xy(terrain, p["lat"], p["lon"])
        assert abs(bx - x) < 0.001 and abs(by - y) < 0.001


def test_import_warns_about_f14_terrain():
    _, res = _prep("synth:F-14BU")
    assert any("terrain" in w and "Caucasus" in w for w in res.warnings)
