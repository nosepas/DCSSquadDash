import pytest
from dtc_util import cases_for, new_point, prepare

from fox3_dtc import AIRCRAFT, DtcError, export_dtc, import_dtc, terrains, validate_model
from fox3_dtc.io import write_json
from fox3_dtc.templates import FILES, default_points, default_template


def _f16():
    return prepare(cases_for("F-16")[0])


def test_valid_models_have_no_errors():
    for key in ("F-16", "F-14", "AH-64"):
        assert validate_model(prepare(cases_for(key)[0]).model) == []


@pytest.mark.parametrize(("mutate", "text"), [
    (lambda m: m.update(terrain="Atlantis"), "terrain"),
    (lambda m: m.update(terrain=None), "terrain"),
    (lambda m: m["waypoints"][0].update(lat=91), "lat"),
    (lambda m: m["waypoints"][0].update(lon="x"), "lon"),
    (lambda m: m["waypoints"][0].update(elevation_m="high"), "elevation_m"),
    (lambda m: m["waypoints"][1].update(id=m["waypoints"][0]["id"]), "duplicate"),
    (lambda m: m["routes"].append({"name": "r", "points": []}), "does not support"),
    (lambda m: m.update(aircraft="Su-27"), "unknown aircraft"),
    (lambda m: m.update(waypoints="nope"), "must be a list"),
])
def test_errors_are_reported_and_export_raises_the_same(mutate, text):
    res = _f16()
    mutate(res.model)
    errs = validate_model(res.model)
    assert errs and any(text in e for e in errs)
    with pytest.raises(DtcError) as exc:
        export_dtc(res.model, res.template)
    assert exc.value.errors == errs


def test_validate_never_raises_on_garbage():
    assert validate_model(None)
    assert validate_model({"aircraft": "F-16C_50", "terrain": "Syria", "waypoints": [1, None]})


def test_fa18c_is_reserved_and_disabled():
    assert AIRCRAFT["FA-18C_hornet"].enabled is False
    assert [a for a, i in AIRCRAFT.items() if i.enabled] == ["F-16C_50", "F-14BU", "AH-64D_BLK_II"]
    assert validate_model({"aircraft": "FA-18C_hornet", "terrain": "Syria"})
    with pytest.raises(DtcError, match="not supported"):
        import_dtc(write_json({"data": {}, "name": "", "type": "FA-18C_hornet"}))


def test_bad_files_raise_dtcerror():
    for raw in (b"not json", b"[1]", b'{"data": 1, "type": "F-16C_50"}', b'{"data": {}, "type": "Su-27"}'):
        with pytest.raises(DtcError):
            import_dtc(raw)


def test_support_table_and_terrains():
    assert AIRCRAFT["F-16C_50"].supports == ("waypoints", "lines", "radios") and "threat_points" in AIRCRAFT["F-16C_50"].unsupported
    assert AIRCRAFT["F-14BU"].limits["routes"] == 12 and AIRCRAFT["AH-64D_BLK_II"].limits["waypoints"] is None
    t = terrains()
    assert t["Caucasus"] == "exact" and t["Syria"] == "plausible" and len(t) == 11


def test_builtin_templates_load_without_samples_and_are_empty():
    for aircraft in FILES:
        tpl = default_template(aircraft)
        assert tpl["type"] == aircraft and default_points(aircraft)
    assert default_template("F-16C_50")["data"]["MPD"]["NAV_PTS"] == []
    assert all(s["waypoints"] == [] and s["name"] == "" for s in default_template("F-14BU")["data"]["NAV"])
    assert default_template("AH-64D_BLK_II")["data"]["NAV"]["Mission_1"]["Points"]["TGT"]["POINTS"] == []


def test_builtin_defaults_fill_in_when_the_template_has_no_example_point():
    model = _f16().model
    model["waypoints"] = [new_point(36.0, 37.0)]
    assert b"STPT1" in export_dtc(model, default_template("F-16C_50"))
