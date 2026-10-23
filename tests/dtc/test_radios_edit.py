"""Radio editing: only the exposed fields change, everything else in the file stays as DCS wrote it."""
import pytest
from dtc_util import cases_for, diff_paths, export_json, prepare

from fox3_dtc import DtcError, default_model, export_dtc, export_with_warnings, validate_model
from fox3_dtc.io import write_json
from fox3_dtc.templates import default_template


def _channel(res, radio, n):
    return next(c for r in res.model["radios"]["radios"] if r["id"] == radio for c in r["channels"] if c["channel"] == n)


@pytest.mark.parametrize("case", cases_for("F-16") + cases_for("AH-64"))
def test_import_exposes_radios_without_warnings(case):
    res = prepare(case)
    assert res.model["radios"]
    assert not any("radio" in w.lower() for w in res.warnings)


def test_f14_has_no_radios_key():
    assert "radios" not in prepare(cases_for("F-14")[0]).model


@pytest.mark.parametrize("case", cases_for("F-16"))
def test_f16_edit_one_channel_changes_only_that_value(case):
    res = prepare(case)
    ch = _channel(res, "COMM1", 3)
    ch["frequency_mhz"] = 251 if ch["frequency_mhz"] != 251 else 252
    out = export_json(res)
    assert diff_paths(res.template, out) == {("data", "COMM", "COMM1", "Channel_3", "freq")}
    assert out["data"]["COMM"]["COMM1"]["Channel_3"]["modulation"] == res.template["data"]["COMM"]["COMM1"]["Channel_3"]["modulation"]


@pytest.mark.parametrize("case", cases_for("F-16"))
def test_f16_fractional_is_float_and_integral_is_int(case):
    res = prepare(case)
    _channel(res, "COMM2", 1)["frequency_mhz"] = 251.075
    _channel(res, "COMM2", 2)["frequency_mhz"] = 130.0
    comm = export_json(res)["data"]["COMM"]["COMM2"]
    assert comm["Channel_1"]["freq"] == 251.075 and isinstance(comm["Channel_1"]["freq"], float)
    assert comm["Channel_2"]["freq"] == 130 and isinstance(comm["Channel_2"]["freq"], int)
    assert b"251.075" in export_dtc(res.model, res.template)


def test_f16_new_channel_copies_sibling_modulation():
    res = prepare("synth:F-16C_50")
    del res.template["data"]["COMM"]["COMM1"]["Channel_20"]
    res.model["radios"]["radios"][0]["channels"][-1] = {"channel": 20, "frequency_mhz": 300}
    assert export_json(res)["data"]["COMM"]["COMM1"]["Channel_20"] == {"freq": 300, "modulation": 1}


def test_f16_export_needs_comm_section_in_template():
    res = prepare("synth:F-16C_50")
    del res.template["data"]["COMM"]
    with pytest.raises(DtcError, match="data.COMM"):
        export_dtc(res.model, res.template)


@pytest.mark.parametrize("case", cases_for("AH-64"))
def test_ah64_preset_edit_changes_only_those_fields(case):
    res = prepare(case)
    p = res.model["radios"]["presets"][1]
    p["radios"]["UHF"]["frequency_mhz"] = 251.5
    p["call_sign"] = "VIPER"
    p["extra"]["COMMS"]["HF_ALE"] = 0
    out = export_json(res)
    base = ("data", "Presets", "COMM")
    assert diff_paths(res.template, out) == {base}
    a, b = res.template["data"]["Presets"]["COMM"], out["data"]["Presets"]["COMM"]
    assert a[:1] == b[:1] and a[2:] == b[2:]
    assert (b[1]["COMMS"]["UHF"]["Frequency"], b[1]["InitialMode"]["CallSign"], b[1]["COMMS"]["HF_ALE"]) == (251.5, "VIPER", 0)
    b[1]["COMMS"]["UHF"]["Frequency"] = a[1]["COMMS"]["UHF"]["Frequency"]
    b[1]["InitialMode"]["CallSign"] = a[1]["InitialMode"]["CallSign"]
    b[1]["COMMS"]["HF_ALE"] = a[1]["COMMS"]["HF_ALE"]
    assert a == b and out["data"]["Radios"] == res.template["data"]["Radios"]


@pytest.mark.parametrize("case", cases_for("AH-64"))
def test_ah64_initial_settings_and_guard_edit(case):
    res = prepare(case)
    ini = res.model["radios"]["initial"]
    ini["VHF"]["frequency_mhz"] = 123.45
    ini["HF"]["rx"]["frequency_mhz"] = 5
    ini["FM1"]["preset"] = 3
    res.model["radios"]["guard_receiver"] = not res.model["radios"]["guard_receiver"]
    out = export_json(res)
    root = ("data", "Radios", "InitialRadioSettings")
    assert diff_paths(res.template, out) == {root + ("VHF", "Frequency"), root + ("HF", "RxFrequency"), root + ("FM1", "Preset"),
                                             ("data", "Radios", "UHF_GuardReceiver")}
    assert out["data"]["Radios"]["InitialRadioSettings"]["VHF"]["Frequency"] == 123.45


def test_ah64_preset_count_mismatch_with_template_is_an_error():
    res = prepare("synth:AH-64D_BLK_II")
    del res.template["data"]["Presets"]["COMM"][9]
    with pytest.raises(DtcError, match="presets"):
        export_dtc(res.model, res.template)


@pytest.mark.parametrize("aircraft", ["F-16C_50", "AH-64D_BLK_II"])
def test_default_model_validates_and_exports_the_template_bytes(aircraft):
    model = default_model(aircraft)
    assert validate_model(model) == [] and model["waypoints"] == [] and model["radios"]
    assert export_dtc(model) == write_json(default_template(aircraft))
    assert default_model(aircraft, "Caucasus")["terrain"] == "Caucasus"


def test_default_model_f14_has_no_radios_and_needs_terrain():
    model = default_model("F-14BU")
    assert model["terrain"] is None and "radios" not in model
    model["terrain"] = "Caucasus"
    export_dtc(model)
    with pytest.raises(DtcError):
        default_model("F-16C_50", "Atlantis")
    with pytest.raises(DtcError):
        default_model("FA-18C_hornet")


def test_model_without_radios_key_leaves_template_radios_alone():
    res = prepare("synth:F-16C_50")
    del res.model["radios"]
    assert export_json(res)["data"]["COMM"] == res.template["data"]["COMM"]
    res.model["radios"] = None
    assert export_with_warnings(res.model, res.template).warnings == []
