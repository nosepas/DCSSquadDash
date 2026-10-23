import json

import pytest
from dtc_util import cases_for, diff_paths, export_json, new_point, only_under, prepare

from fox3_dtc import DtcError, export_dtc

NAV = ("data", "NAV")
CASE = pytest.mark.parametrize("case", cases_for("F-14"))


def _first_route(res):
    return next(i for i, r in enumerate(res.model["routes"]) if r["points"])


@CASE
def test_add_waypoint_only_changes_nav(case):
    res = prepare(case)
    i = _first_route(res)
    res.model["routes"][i]["points"].append(new_point(43.0, 41.0, 321, name="NEW", extra={"spd": 300, "tot": "10:00:00"}))
    out = export_json(res)
    assert only_under(diff_paths(res.template, out), NAV)
    w = out["data"]["NAV"][i]["waypoints"][-1]
    assert (w["name"], w["elev"], w["spd"], w["tot"]) == ("NEW", 321, 300, "10:00:00")
    assert w["x"] != 0 and set(w) == set(res.template["data"]["NAV"][i]["waypoints"][0])
    assert len(out["data"]["NAV"]) == 12


@CASE
def test_remove_reorder_rename_and_elevation(case):
    res = prepare(case)
    i = _first_route(res)
    pts = res.model["routes"][i]["points"]
    orig = res.template["data"]["NAV"][i]["waypoints"]
    pts.reverse()
    pts[0]["elevation_m"] = 99
    res.model["routes"][i]["name"] = "RENAMED"
    out = export_json(res)["data"]["NAV"][i]
    assert out["name"] == "RENAMED"
    assert [w["lat"] for w in out["waypoints"]] == [w["lat"] for w in reversed(orig)]
    assert out["waypoints"][0]["elev"] == 99 and out["waypoints"][1:] == list(reversed(orig))[1:]
    pts.pop()
    assert len(export_json(res)["data"]["NAV"][i]["waypoints"]) == len(orig) - 1


@CASE
def test_lines_and_additional_points(case):
    res = prepare(case)
    meta = res.model["aircraft_extra"]["f14"]
    res.model["lines"].append({"name": "", "closed": False, "points": [new_point(43.0, 41.0, 5), new_point(43.1, 41.1, 6)]})
    meta["line_route"].append(5)
    out = export_json(res)
    assert [len(ln["points"]) for ln in out["data"]["NAV"][5]["lines"]][-1] == 2
    assert out["data"]["NAV"][5]["lines"][-1]["closed"] is False
    for a, b in zip(res.template["data"]["NAV"], out["data"]["NAV"], strict=True):
        assert a["additional_points"] == b["additional_points"]


@CASE
def test_terrain_is_required(case):
    res = prepare(case)
    res.model["terrain"] = None
    with pytest.raises(DtcError, match="terrain"):
        export_dtc(res.model, res.template)


@CASE
def test_choosing_another_terrain_recomputes_xy(case):
    res = prepare(case)
    i = _first_route(res)
    res.model["terrain"] = "Syria"
    w = export_json(res)["data"]["NAV"][i]["waypoints"][0]
    assert (w["x"], w["y"]) != tuple(res.template["data"]["NAV"][i]["waypoints"][0][k] for k in ("x", "y"))


def test_template_less_export_matches_structure():
    res = prepare(cases_for("F-14")[0])
    i = _first_route(res)
    got = json.loads(export_dtc(res.model))
    assert set(got["data"]) == set(res.template["data"])
    assert set(got["data"]["NAV"][i]["waypoints"][0]) == set(res.template["data"]["NAV"][i]["waypoints"][0])
    assert set(got["data"]["NAV"][i]) == set(res.template["data"]["NAV"][i])
