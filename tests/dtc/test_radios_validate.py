"""Radio validation (errors block) and frequency plausibility (warnings never block)."""
import pytest
from dtc_util import cases_for, prepare

from fox3_dtc import AIRCRAFT, DtcError, export_dtc, export_with_warnings, validate_model


def _f16():
    return prepare("synth:F-16C_50")


def _ah():
    return prepare("synth:AH-64D_BLK_II")


def _freq(i, v):
    return lambda r: r["radios"][0]["channels"][i].update(frequency_mhz=v)


F16_BAD = [
    (lambda r: r.__setitem__("x", 1), "no 'x'"),
    (lambda r: r["radios"][0].update(id="COMM9"), "unknown radio id"),
    (lambda r: r["radios"][1].update(id="COMM1"), "duplicate radio"),
    (lambda r: r["radios"][0]["channels"].append({"channel": 21, "frequency_mhz": 250}), "at most 20"),
    (lambda r: r["radios"][0]["channels"][0].update(channel=21), "channel must be"),
    (lambda r: r["radios"][0]["channels"][1].update(channel=1), "duplicate channel"),
    (_freq(0, 0), "greater than 0"),
    (_freq(0, -5), "greater than 0"),
    (_freq(0, float("inf")), "finite"),
    (_freq(0, float("nan")), "finite"),
    (_freq(0, "250"), "finite"),
    (_freq(0, True), "finite"),
    (lambda r: r["radios"][0].update(channels="no"), "channels must be a list"),
    (lambda r: r.update(presets=[]), "no 'presets'"),
]


@pytest.mark.parametrize(("mutate", "text"), F16_BAD)
def test_f16_radio_errors(mutate, text):
    res = _f16()
    mutate(res.model["radios"])
    errs = validate_model(res.model)
    assert any(text in e for e in errs), errs
    with pytest.raises(DtcError):
        export_dtc(res.model, res.template)


def test_radios_must_be_an_object():
    res = _f16()
    res.model["radios"] = []
    assert validate_model(res.model) == ["radios must be an object"]


AH_BAD = [
    (lambda r: r["presets"].pop(), "exactly 10"),
    (lambda r: r["presets"][0].update(index=2), "each of 1-10"),
    (lambda r: r["presets"][0].update(call_sign=5), "call_sign"),
    (lambda r: r["presets"][0].update(dl_net="yes"), "dl_net"),
    (lambda r: r["presets"][0].update(primary_frequency=-1), "primary_frequency"),
    (lambda r: r["presets"][0]["radios"].update(GPS={}), "unknown radio"),
    (lambda r: r["presets"][0]["radios"]["UHF"].update(frequency_mhz=0), "greater than 0"),
    (lambda r: r["presets"][0]["radios"]["UHF"].update(modulation=1.5), "modulation must be an integer"),
    (lambda r: r["initial"]["VHF"].update(frequency_mhz=float("nan")), "finite"),
    (lambda r: r["initial"]["HF"]["tx"].update(frequency_mhz=-1), "greater than 0"),
    (lambda r: r["initial"].update(XX={}), "unknown radio"),
    (lambda r: r.update(guard_receiver=1), "guard_receiver"),
    (lambda r: r.update(radios=[]), "no 'radios'"),
]


@pytest.mark.parametrize(("mutate", "text"), AH_BAD)
def test_ah64_radio_errors(mutate, text):
    res = _ah()
    mutate(res.model["radios"])
    errs = validate_model(res.model)
    assert any(text in e for e in errs), errs


def test_f14_rejects_radios_and_says_it_is_unsupported():
    res = prepare(cases_for("F-14")[0])
    res.model["radios"] = {"radios": []}
    assert any("does not support editing 'radios'" in e for e in validate_model(res.model))
    with pytest.raises(DtcError, match="radios"):
        export_dtc(res.model, res.template)
    assert "radios" in AIRCRAFT["F-14BU"].unsupported and "radios" not in AIRCRAFT["F-14BU"].supports


def test_capabilities_declare_radios_and_limits():
    assert "radios" in AIRCRAFT["F-16C_50"].supports and AIRCRAFT["F-16C_50"].limits["radio_channels"] == 20
    assert "radios" in AIRCRAFT["AH-64D_BLK_II"].supports and AIRCRAFT["AH-64D_BLK_II"].limits["presets"] == 10


def test_valid_unedited_radios_give_no_warnings():
    for res in (_f16(), _ah()):
        assert export_with_warnings(res.model, res.template).warnings == []


def test_f16_out_of_band_frequency_warns_but_exports():
    res = _f16()
    res.model["radios"]["radios"][0]["channels"][0]["frequency_mhz"] = 130  # VHF value on the UHF radio
    res.model["radios"]["radios"][1]["channels"][0]["frequency_mhz"] = 300  # UHF value on the VHF radio
    out = export_with_warnings(res.model, res.template)
    assert len(out.warnings) == 2 and "COMM1 channel" in out.warnings[0] and "not verified" in out.warnings[0]
    assert b"130" in out.raw


def test_ah64_out_of_band_frequencies_warn():
    res = _ah()
    r = res.model["radios"]
    r["presets"][0]["radios"]["FM1"]["frequency_mhz"] = 120
    r["presets"][0]["radios"]["HF_TX"]["frequency_mhz"] = 40
    r["initial"]["UHF"]["frequency_mhz"] = 100
    r["initial"]["HF"]["rx"]["frequency_mhz"] = 1
    warns = export_with_warnings(res.model, res.template).warnings
    assert len(warns) == 4
    assert any("preset 1 FM1" in w for w in warns) and any("initial HF rx" in w for w in warns)


def test_band_edges_are_inclusive():
    res = _ah()
    r = res.model["radios"]["presets"][0]["radios"]
    r["FM1"]["frequency_mhz"], r["FM2"]["frequency_mhz"] = 30, 87.975
    r["UHF"]["frequency_mhz"], r["HF_RX"]["frequency_mhz"] = 399.975, 29.999
    assert export_with_warnings(res.model, res.template).warnings == []
