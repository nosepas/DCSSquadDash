import json

import pytest
from dtc_util import cases_for, diff_paths, export_json, new_point, only_under, prepare

from fox3_dtc import DtcError, export_dtc

CASE = pytest.mark.parametrize("case", cases_for("AH-64"))


def _pts(out, m, kind):
    return out["data"]["NAV"][f"Mission_{m}"]["Points"][kind]["POINTS"]


@CASE
def test_add_waypoint_numbers_and_codes(case):
    res = prepare(case)
    n = sum(1 for p in res.model["waypoints"] if p["kind"] == "WPTHZ" and p["extra"]["mission"] == 1)
    res.model["waypoints"].append(new_point(43.3, 41.3, 800, kind="WPTHZ", extra={"mission": 1}))
    out = export_json(res)
    assert only_under(diff_paths(res.template, out), ("data", "NAV", "Mission_1", "Points", "WPTHZ"))
    last = _pts(out, 1, "WPTHZ")[-1]
    assert (last["num"], last["text"], last["alt"]) == (n + 1, f"W{n + 1:02d}", 800)
    assert set(last) == set(_pts(res.template, 1, "WPTHZ")[0])


@CASE
def test_mission_two_and_target_defaults_from_other_mission(case):
    res = prepare(case)
    res.model["waypoints"].append(new_point(43.3, 41.3, 800, kind="TGT", name="ALPHA", extra={"mission": 2}))
    out = export_json(res)
    assert only_under(diff_paths(res.template, out), ("data", "NAV", "Mission_2", "Points", "TGT"))
    assert (_pts(out, 2, "TGT")[0]["num"], _pts(out, 2, "TGT")[0]["text"]) == (1, "ALPHA")


@CASE
def test_move_remove_and_rename(case):
    res = prepare(case)
    w = [p for p in res.model["waypoints"] if p["kind"] == "WPTHZ"]
    orig = _pts(res.template, 1, "WPTHZ")
    w[0]["name"], w[0]["elevation_m"] = "HOME", 5
    res.model["waypoints"].remove(w[1])
    out = export_json(res)
    pts = _pts(out, 1, "WPTHZ")
    assert len(pts) == len(orig) - 1 and (pts[0]["text"], pts[0]["alt"]) == ("HOME", 5)
    assert pts[0]["x"] == orig[0]["x"] and pts[0]["id"] == orig[0]["id"]
    assert only_under(diff_paths(res.template, out), ("data", "NAV", "Mission_1", "Points", "WPTHZ"))


@CASE
def test_untouched_ah64_parts_survive(case):
    res = prepare(case)
    res.model["waypoints"].clear()
    out = export_json(res)
    for m in (1, 2):
        for key in ("Routes", "Zones", "Areas", "Lines", "ADF"):
            assert out["data"]["NAV"][f"Mission_{m}"][key] == res.template["data"]["NAV"][f"Mission_{m}"][key]
    assert out["data"]["NAV"]["MissionFile"] == res.template["data"]["NAV"]["MissionFile"]


@CASE
def test_ctrlm_without_example_is_refused(case):
    res = prepare(case)
    if any(p["kind"] == "CTRLM" for p in res.model["waypoints"]):
        pytest.skip("template has a CTRLM example")
    res.model["waypoints"].append(new_point(43.3, 41.3, 1, kind="CTRLM", extra={"mission": 1}))
    with pytest.raises(DtcError, match="no example CTRLM"):
        export_dtc(res.model, res.template)


def test_template_less_export_matches_structure():
    res = prepare(cases_for("AH-64")[0])
    got = json.loads(export_dtc(res.model))
    assert set(got["data"]) >= set(res.template["data"])
    for m in (1, 2):
        for kind in ("TGT", "WPTHZ"):
            if _pts(res.template, m, kind):
                assert set(_pts(got, m, kind)[0]) == set(_pts(res.template, m, kind)[0])
