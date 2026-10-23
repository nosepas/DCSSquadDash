"""Structural validation of the AH-64 `radios` part (see radios_ah64.py for the shape)."""
from __future__ import annotations

from typing import Any

from .aircraft import AIRCRAFT
from .radio_check import check_extra, check_freq, check_ints, is_int
from .radios_ah64 import INITIAL_KEYS, RADIO_KEYS


def _rf(obj: Any, where: str, errs: list[str], extra_ints: tuple[str, ...] = ()) -> None:
    if not isinstance(obj, dict):
        errs.append(f"{where}: not an object")
        return
    if "frequency_mhz" in obj:
        check_freq(obj["frequency_mhz"], where, errs)
    check_ints(obj, ("modulation", "encryption") + extra_ints, where, errs)
    check_extra(obj, where, errs)


def _preset(p: Any, where: str, errs: list[str]) -> None:
    if not isinstance(p, dict):
        errs.append(f"{where}: not an object")
        return
    for key, kind in (("call_sign", str), ("unit_id", str), ("dl_net", bool)):
        if key in p and not isinstance(p[key], kind):
            errs.append(f"{where}: {key} must be a {kind.__name__}")
    if "primary_frequency" in p and (not is_int(p["primary_frequency"]) or p["primary_frequency"] < 0):
        errs.append(f"{where}: primary_frequency must be an integer >= 0")
    check_extra(p, where, errs)
    radios = p.get("radios", {})
    if not isinstance(radios, dict):
        errs.append(f"{where}: radios must be an object")
        return
    for key, obj in radios.items():
        if key not in RADIO_KEYS:
            errs.append(f"{where}: unknown radio {key!r} (allowed: {', '.join(RADIO_KEYS)})")
        else:
            _rf(obj, f"{where}.radios.{key}", errs)


def _initial(ini: Any, errs: list[str]) -> None:
    if not isinstance(ini, dict):
        errs.append("radios.initial must be an object")
        return
    for key, obj in ini.items():
        where = f"radios.initial.{key}"
        if key in INITIAL_KEYS:
            _rf(obj, where, errs, ("mode", "preset"))
        elif key == "HF" and isinstance(obj, dict):
            check_ints(obj, ("mode", "preset"), where, errs)
            check_extra(obj, where, errs)
            for side in ("rx", "tx"):
                if side in obj:
                    _rf(obj[side], f"{where}.{side}", errs)
        else:
            errs.append(f"{where}: unknown radio (allowed: {', '.join(INITIAL_KEYS)}, HF)")


def ah64_errors(radios: dict[str, Any]) -> list[str]:
    errs = [f"AH-64D_BLK_II radios have no '{k}'" for k in radios if k not in ("presets", "initial", "guard_receiver")]
    if "guard_receiver" in radios and not isinstance(radios["guard_receiver"], bool):
        errs.append("radios.guard_receiver must be a boolean")
    if "initial" in radios:
        _initial(radios["initial"], errs)
    if "presets" in radios:
        presets, count = radios["presets"], AIRCRAFT["AH-64D_BLK_II"].limits["presets"]
        if not isinstance(presets, list):
            return errs + ["radios.presets must be a list"]
        if len(presets) != count:
            errs.append(f"AH-64D_BLK_II needs exactly {count} presets; got {len(presets)}")
        for i, p in enumerate(presets):
            _preset(p, f"radios.presets[{i}]", errs)
        idx = [p.get("index") for p in presets if isinstance(p, dict)]
        if sorted(idx, key=str) != sorted(range(1, count + 1), key=str):
            errs.append(f"radios.presets: index must be each of 1-{count} exactly once")
    return errs
