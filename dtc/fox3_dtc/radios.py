"""Radio support dispatch: import (template -> neutral `radios`) and export patch (neutral `radios` -> template copy)."""
from __future__ import annotations

from typing import Any

from . import radios_ah64, radios_f16

_MODULES = {"F-16C_50": radios_f16, "AH-64D_BLK_II": radios_ah64}


def to_model(aircraft: str, template: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    """(`radios` object or None when the aircraft/file has none, warnings)."""
    mod = _MODULES.get(aircraft)
    return mod.to_model(template) if mod else (None, [])


def apply(model: dict[str, Any], out: dict[str, Any]) -> None:
    """Patch only the radio fields we expose into `out`; a model without `radios` leaves it untouched."""
    if model.get("radios") is not None:
        _MODULES[model["aircraft"]].apply(model["radios"], out)
