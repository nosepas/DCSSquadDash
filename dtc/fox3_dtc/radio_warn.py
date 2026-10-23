"""Frequency plausibility WARNINGS for the neutral `radios` part (never blocking).

Band limits are the commonly documented real-world / DCS-manual ranges, NOT verified in the game. Confidence per range:
 - UHF 225-399.975 MHz (military air band): high for the real radio; DCS acceptance of every value unverified.
 - F-16 COMM2 VHF 108-174 MHz: medium. 108-174 is wider than the AM/FM air band on purpose so only clear mistakes warn.
 - AH-64 VHF 108-174 MHz: medium (documented VHF-AM is narrower, ~116-149.975; widened because unsure).
 - AH-64 FM 30-87.975 MHz: high (VHF-FM tactical band).
 - AH-64 HF 2-29.999 MHz: medium.
"""
from __future__ import annotations

from typing import Any

from .model import is_number

_UHF, _VHF = (225.0, 399.975, "UHF"), (108.0, 174.0, "VHF")
_FM, _HF = (30.0, 87.975, "FM"), (2.0, 29.999, "HF")
F16_RANGES = {"COMM1": _UHF, "COMM2": _VHF}
AH64_RANGES = {"FM1": _FM, "FM2": _FM, "UHF": _UHF, "VHF": _VHF, "HF_RX": _HF, "HF_TX": _HF}


def _check(where: str, obj: Any, rng: tuple[float, float, str], out: list[str]) -> None:
    f = obj.get("frequency_mhz") if isinstance(obj, dict) else None
    if is_number(f) and not rng[0] <= f <= rng[1]:
        out.append(f"{where}: {f} MHz is outside the {rng[2]} range {rng[0]}-{rng[1]} MHz "
                   "(commonly documented range, not verified in the game; written anyway)")


def _f16(radios: dict[str, Any], out: list[str]) -> None:
    for rad in radios.get("radios", []):
        for ch in rad.get("channels", []):
            _check(f"{rad['id']} channel {ch['channel']}", ch, F16_RANGES[rad["id"]], out)


def _ah64(radios: dict[str, Any], out: list[str]) -> None:
    for p in radios.get("presets", []):
        for key, obj in (p.get("radios") or {}).items():
            _check(f"preset {p['index']} {key}", obj, AH64_RANGES[key], out)
    for key, obj in (radios.get("initial") or {}).items():
        if key == "HF":
            _check("initial HF rx", obj.get("rx"), _HF, out)
            _check("initial HF tx", obj.get("tx"), _HF, out)
        else:
            _check(f"initial {key}", obj, AH64_RANGES[key], out)


def radio_warnings(model: dict[str, Any]) -> list[str]:
    """Warnings for an already validated model."""
    out: list[str] = []
    radios = model.get("radios")
    if radios:
        {"F-16C_50": _f16, "AH-64D_BLK_II": _ah64}[model["aircraft"]](radios, out)
    return out
