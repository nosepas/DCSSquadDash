import json

import pytest
from dtc_util import cases_for, diff_paths, export_json, new_point, only_under, prepare

from fox3_dtc import DtcError, export_dtc, export_with_warnings

NAV = ("data", "MPD", "NAV_PTS")
GEO = ("data", "MPD", "GEO_LINES")
CASE = pytest.mark.parametrize("case", cases_for("F-16"))


@CASE
def test_add_waypoint_numbers_like_the_originals(case):
    res = prepare(case)
    orig = res.template
    n = len(res.model["waypoints"])
    res.model["waypoints"].append(new_point(36.0, 37.0, 500, note="new"))
    out = export_json(res)
    assert only_under(diff_paths(orig, out), NAV)
    new = out["data"]["MPD"]["NAV_PTS"][-1]
    assert (new["number"], new["id"], new["idOA1"], new["idOA2_Line"]) == (n + 1, f"STPT{n + 1}", f"OA1{n + 1}", f"OA2{n + 1}Line")
    assert new["alt"] == 500 and new["note"] == "new" and set(new) == set(orig["data"]["MPD"]["NAV_PTS"][0])
    assert out["data"]["MPD"]["NAV_PTS"][:n] == orig["data"]["MPD"]["NAV_PTS"]


@CASE
def test_move_rename_and_elevation_touch_only_that_point(case):
    res = prepare(case)
    orig = res.template
    p = res.model["waypoints"][1]
    p.update(lat=p["lat"] + 0.1, elevation_m=1234, note="moved")
    out = export_json(res)
    assert only_under(diff_paths(orig, out), NAV)
    a, b = orig["data"]["MPD"]["NAV_PTS"], out["data"]["MPD"]["NAV_PTS"]
    assert a[0] == b[0] and a[2:] == b[2:]
    assert (b[1]["alt"], b[1]["note"]) == (1234, "moved") and b[1]["x"] != a[1]["x"]
    skip = ("x", "y", "alt", "note")
    assert {k: v for k, v in a[1].items() if k not in skip} == {k: v for k, v in b[1].items() if k not in skip}


@CASE
def test_remove_and_reorder_renumber_and_keep_each_points_extras(case):
    res = prepare(case)
    a = res.template["data"]["MPD"]["NAV_PTS"]
    res.model["waypoints"].reverse()
    b = export_json(res)["data"]["MPD"]["NAV_PTS"]
    assert [p["number"] for p in b] == list(range(1, len(a) + 1))
    assert [p["id"] for p in b] == [f"STPT{i}" for i in range(1, len(a) + 1)]
    assert [p["TOS"] for p in b] == [p["TOS"] for p in reversed(a)]
    res.model["waypoints"].pop(0)
    c = export_json(res)["data"]["MPD"]["NAV_PTS"]
    assert len(c) == len(a) - 1 and c[0]["id"] == "STPT1"


@CASE
def test_lines_add_and_remove(case):
    res = prepare(case)
    orig = res.template
    res.model["lines"][1]["points"].append(new_point(36.0, 37.0, 5))
    out = export_json(res)
    assert only_under(diff_paths(orig, out), GEO)
    geo = out["data"]["MPD"]["GEO_LINES"]
    assert [g["number"] for g in geo] == list(range(1, len(geo) + 1))
    assert geo[-1]["L2"] and not geo[-1]["L1"] and geo[-1]["id"].endswith(str(len(geo)))
    assert out["data"]["MPD"]["GEO_LINES"][: len(orig["data"]["MPD"]["GEO_LINES"])] == orig["data"]["MPD"]["GEO_LINES"]


@CASE
def test_terrain_change_updates_both_terrain_fields_and_coordinates(case):
    res = prepare(case)
    res.model["terrain"] = "Caucasus"
    out = export_json(res)
    assert out["data"]["terrain"] == out["data"]["MPD"]["terrain"] == "Caucasus"
    assert out["data"]["MPD"]["NAV_PTS"][0]["x"] != res.template["data"]["MPD"]["NAV_PTS"][0]["x"]


@CASE
def test_unknown_parts_survive(case):
    res = prepare(case)
    res.model["waypoints"].clear()
    out = export_json(res)
    for key in ("THREAT_PTS", "DEST", "VIPVRP", "ROE", "CMDS"):
        assert out["data"]["MPD"][key] == res.template["data"]["MPD"][key]
    assert out["data"]["COLR"] == res.template["data"]["COLR"]


@CASE
def test_unknown_elevation_is_zero_with_warning(case):
    res = prepare(case)
    res.model["waypoints"][0]["elevation_m"] = None
    result = export_with_warnings(res.model, res.template)
    assert any("elevation unknown" in w for w in result.warnings)
    assert export_json(res)["data"]["MPD"]["NAV_PTS"][0]["alt"] == 0


def test_template_less_export_has_all_keys_of_the_original():
    res = prepare(cases_for("F-16")[0])
    out = export_dtc(res.model)  # built-in template
    got = json.loads(out)
    assert got["type"] == "F-16C_50" and got["data"]["terrain"] == res.model["terrain"]
    assert set(got["data"]["MPD"]["NAV_PTS"][0]) >= set(res.template["data"]["MPD"]["NAV_PTS"][0])
    assert set(got["data"]["MPD"]["GEO_LINES"][0]) >= set(res.template["data"]["MPD"]["GEO_LINES"][0])
    assert set(got["data"]["MPD"]) >= set(res.template["data"]["MPD"])


def test_too_many_steerpoints_is_refused():
    res = prepare(cases_for("F-16")[0])
    res.model["waypoints"] = [new_point(36.0, 37.0) for _ in range(26)]
    with pytest.raises(DtcError, match="at most 25"):
        export_dtc(res.model, res.template)
