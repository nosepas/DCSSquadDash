"""Structural validation of the neutral `radios` part (errors, blocking). Plausibility warnings live in radio_warn.py."""
from __future__ import annotations

import math
from typing import Any

from .aircraft import AIRCRAFT
from .model import is_number
from .radios_f16 import RADIOS as F16_RADIOS


def is_int(v: Any) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def check_freq(v: Any, where: str, errs: list[str], *, required: bool = True) -> None:
    if v is None and not required:
        return
    if not is_number(v) or not math.isfinite(v):
        errs.append(f"{where}: frequency_mhz must be a finite number (MHz)")
    elif v <= 0:
        errs.append(f"{where}: frequency_mhz must be greater than 0 (got {v})")


def check_ints(obj: dict[str, Any], names: tuple[str, ...], where: str, errs: list[str]) -> None:
    errs += [f"{where}: {n} must be an integer" for n in names if n in obj and not is_int(obj[n])]


def check_extra(obj: dict[str, Any], where: str, errs: list[str]) -> None:
    if "extra" in obj and not isinstance(obj["extra"], dict):
        errs.append(f"{where}: extra must be an object")


def _f16(radios: dict[str, Any]) -> list[str]:
    errs = [f"F-16C_50 radios have no '{k}'" for k in radios if k != "radios"]
    limit = AIRCRAFT["F-16C_50"].limits["radio_channels"]
    items = radios.get("radios", [])
    if not isinstance(items, list):
        return errs + ["radios.radios must be a list"]
    seen: set[Any] = set()
    for i, rad in enumerate(items):
        where = f"radios.radios[{i}]"
        if not isinstance(rad, dict):
            errs.append(f"{where}: not an object")
            continue
        rid = rad.get("id")
        if rid not in F16_RADIOS:
            errs.append(f"{where}: unknown radio id {rid!r} (allowed: {', '.join(F16_RADIOS)})")
        elif rid in seen:
            errs.append(f"{where}: duplicate radio id {rid!r}")
        seen.add(rid)
        check_extra(rad, where, errs)
        chans = rad.get("channels", [])
        if not isinstance(chans, list):
            errs.append(f"{where}: channels must be a list")
            continue
        if len(chans) > limit:
            errs.append(f"{where}: at most {limit} channels allowed; got {len(chans)}")
        nums: set[Any] = set()
        for j, ch in enumerate(chans):
            cw = f"{where}.channels[{j}]"
            if not isinstance(ch, dict):
                errs.append(f"{cw}: not an object")
                continue
            if not is_int(ch.get("channel")) or not 1 <= ch["channel"] <= limit:
                errs.append(f"{cw}: channel must be an integer 1-{limit}")
            elif ch["channel"] in nums:
                errs.append(f"{cw}: duplicate channel {ch['channel']}")
            nums.add(ch.get("channel"))
            check_freq(ch.get("frequency_mhz"), cw, errs)
            check_extra(ch, cw, errs)
    return errs


def radio_errors(model: dict[str, Any]) -> list[str]:
    """Errors in model['radios'] (absent or null = fine). Aircraft without radio support reject any radios."""
    radios = model.get("radios")
    if radios is None:
        return []
    info = AIRCRAFT[model["aircraft"]]
    if "radios" not in info.supports:
        return [f"{info.id} does not support editing 'radios'"]
    if not isinstance(radios, dict):
        return ["radios must be an object"]
    if info.id == "F-16C_50":
        return _f16(radios)
    from .radio_check_ah64 import ah64_errors
    return ah64_errors(radios)
