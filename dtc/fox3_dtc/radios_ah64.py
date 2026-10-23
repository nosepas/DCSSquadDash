"""AH-64D_BLK_II radios: data.Presets.COMM[10], data.Radios.InitialRadioSettings, data.Radios.UHF_GuardReceiver.

Neutral (frequencies in decimal MHz):
 presets[] = {index (1-based), call_sign, unit_id, primary_frequency (index), dl_net,
              radios: {FM1, FM2, UHF, VHF, HF_RX, HF_TX: {frequency_mhz, modulation, encryption}},
              extra: {COMMS: {HF_ALE, HF_Pre}, DoNotUploadTabData}}
 initial = {FM1, FM2, UHF, VHF: {frequency_mhz, modulation, encryption, mode, preset},
            HF: {mode, preset, rx: {...}, tx: {...}}};  guard_receiver (UHF guard receiver on/off)
`modulation` is the raw DCS code (UHF/VHF 0, FM 1 seen; HF 2 seen but meaning unverified). Not modelled, kept untouched:
Radios.IFF, Radios.FM (CUE frequencies/power), Radios_HF, and anything in `extra` (preserved raw; not for the UI).
"""
from __future__ import annotations

from typing import Any

from . import radio_fields as rf
from .errors import DtcError

RADIO_KEYS = {"FM1": "FM1", "FM2": "FM2", "UHF": "UHF", "VHF": "VHF", "HF_RX": "HF_Rx", "HF_TX": "HF_Tx"}
INITIAL_KEYS = ("FM1", "FM2", "UHF", "VHF")
PRESET_COUNT = 10
_RF = {"frequency_mhz": "Frequency", "modulation": "Modulation", "encryption": "Encryption"}
_INIT = {**_RF, "mode": "Mode", "preset": "Preset"}
_IM = {"call_sign": "CallSign", "unit_id": "UnitID", "primary_frequency": "PrimaryFrequency", "dl_net": "DLNet"}
_HF = {"mode": "Mode", "preset": "Preset"}
_HF_SIDES = {"rx": {k: f"Rx{v}" for k, v in _RF.items()}, "tx": {k: f"Tx{v}" for k, v in _RF.items()}}


def _preset(index: int, raw: dict[str, Any]) -> dict[str, Any]:
    comms, im = raw.get("COMMS") or {}, raw.get("InitialMode") or {}
    out: dict[str, Any] = {"index": index, **rf.pick(im, _IM)}
    out["radios"] = {mk: rf.read(comms[dk], _RF) for mk, dk in RADIO_KEYS.items() if isinstance(comms.get(dk), dict)}
    extra = rf.rest(raw, ("COMMS", "InitialMode"))
    for name, src, used in (("COMMS", comms, RADIO_KEYS), ("InitialMode", im, _IM)):
        sub = rf.rest(src, used)
        if sub:
            extra[name] = sub
    out["extra"] = extra
    return out


def _initial(ini: dict[str, Any]) -> dict[str, Any]:
    out = {k: rf.read(ini[k], _INIT) for k in INITIAL_KEYS if isinstance(ini.get(k), dict)}
    hf = ini.get("HF")
    if isinstance(hf, dict):
        out["HF"] = {**rf.pick(hf, _HF), **{side: rf.pick(hf, fm) for side, fm in _HF_SIDES.items()}}
        extra = rf.rest(hf, _HF, *_HF_SIDES.values())
        if extra:
            out["HF"]["extra"] = extra
    return out


def to_model(template: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    data = template["data"]
    comm = (data.get("Presets") or {}).get("COMM")
    radios = data.get("Radios")
    if not isinstance(comm, list) or not isinstance(radios, dict):
        return None, ["data: Presets.COMM or Radios missing; radios are not editable"]
    out: dict[str, Any] = {"presets": [_preset(i, p) for i, p in enumerate(comm, 1) if isinstance(p, dict)]}
    if isinstance(radios.get("InitialRadioSettings"), dict):
        out["initial"] = _initial(radios["InitialRadioSettings"])
    if "UHF_GuardReceiver" in radios:
        out["guard_receiver"] = radios["UHF_GuardReceiver"]
    return out, []


def _apply_preset(dst: dict[str, Any], p: dict[str, Any]) -> None:
    extra = dict(p.get("extra") or {})
    comms, im = dst.setdefault("COMMS", {}), dst.setdefault("InitialMode", {})
    for mk, obj in (p.get("radios") or {}).items():
        rf.write(comms.setdefault(RADIO_KEYS[mk], {}), obj, _RF)
    rf.write(comms, {"extra": extra.pop("COMMS", {})}, {})
    rf.write(im, {**p, "extra": extra.pop("InitialMode", {})}, _IM)
    rf.write(dst, {"extra": extra}, {})


def apply(radios: dict[str, Any], out: dict[str, Any]) -> None:
    data = out["data"]
    if "presets" in radios:
        comm = rf.section(data, "Presets", "COMM")
        if len(comm) != len(radios["presets"]):
            raise DtcError([f"the template has {len(comm)} COMM presets, the model {len(radios['presets'])}"])
        for p in radios["presets"]:
            _apply_preset(comm[p["index"] - 1], p)
    if "initial" in radios:
        ini = rf.section(data, "Radios", "InitialRadioSettings")
        for k in INITIAL_KEYS:
            if k in radios["initial"]:
                rf.write(ini.setdefault(k, {}), radios["initial"][k], _INIT)
        hf = radios["initial"].get("HF")
        if hf:
            dst = ini.setdefault("HF", {})
            rf.write(dst, hf, _HF)
            for side, fm in _HF_SIDES.items():
                rf.write(dst, hf.get(side) or {}, fm)
    if "guard_receiver" in radios:
        rf.put(rf.section(data, "Radios"), "UHF_GuardReceiver", radios["guard_receiver"])
