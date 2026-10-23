"""Public API: import_dtc / export_dtc / export_with_warnings / validate_model / AIRCRAFT."""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass, field
from typing import Any

from . import ah64, convert, f14, f16, radios
from .aircraft import AIRCRAFT, AircraftInfo, terrains
from .errors import DtcError
from .io import read_json, write_json
from .model import empty_model
from .radio_warn import radio_warnings
from .templates import default_points, default_template
from .validate import all_points, validate_model

__all__ = ["AIRCRAFT", "AircraftInfo", "DtcError", "ExportResult", "ImportResult", "default_model", "export_dtc", "export_with_warnings",
           "import_dtc", "terrains", "validate_model"]

_MODULES = {"F-16C_50": f16, "F-14BU": f14, "AH-64D_BLK_II": ah64}


@dataclass
class ImportResult:
    model: dict[str, Any]
    template: dict[str, Any]
    warnings: list[str] = field(default_factory=list)


@dataclass
class ExportResult:
    raw: bytes
    warnings: list[str] = field(default_factory=list)


def _f14_hint(model: dict[str, Any]) -> str:
    samples = [(p["extra"][convert.XY_KEY][0], p["extra"][convert.XY_KEY][1], p["lat"], p["lon"]) for _, p in all_points(model)][:5]
    found = convert.guess_terrains(samples)
    return f" The coordinates are consistent with: {', '.join(found)}." if found else ""


def _check_type(template: dict[str, Any]) -> str:
    aircraft = template.get("type")
    info = AIRCRAFT.get(aircraft)
    if info is None:
        raise DtcError([f"unsupported .dtc: aircraft type {aircraft!r}"])
    if not info.enabled:
        raise DtcError([f"aircraft {aircraft} is not supported yet (no sample file exists)"])
    if not isinstance(template.get("data"), dict):
        raise DtcError(["not a .dtc file: no 'data' object"])
    return aircraft


def _build_model(template: dict[str, Any], terrain: str | None = None) -> tuple[dict[str, Any], list[str]]:
    """Neutral model + warnings of a template; `terrain` (if given) overrides the file's terrain."""
    aircraft = _check_type(template)
    warns: list[str] = []
    file_terrain = None if aircraft == "F-14BU" else template["data"].get("terrain")
    if aircraft != "F-14BU" and file_terrain not in terrains():
        warns.append(f"terrain {file_terrain!r} in the file is missing or not calibrated; choose one before exporting")
        file_terrain = None
    chosen = terrain or file_terrain
    mod = _MODULES[aircraft]
    part, w = mod.to_model(template) if aircraft == "F-14BU" else mod.to_model(template, chosen)
    model = {**empty_model(aircraft, chosen), **part}
    rad, rw = radios.to_model(aircraft, template)
    if rad is not None:
        model["radios"] = rad
    return model, warns + w + rw


def import_dtc(raw: bytes) -> ImportResult:
    """Parse a native .dtc into (neutral model, template to hand back to export_dtc, warnings)."""
    template = read_json(raw)
    model, warns = _build_model(template)
    if model["aircraft"] == "F-14BU":
        warns.append("the F-14 file carries no terrain: the user must choose it." + _f14_hint(model))
    return ImportResult(model, template, warns)


def default_model(aircraft: str, terrain: str | None = None) -> dict[str, Any]:
    """Neutral model of the aircraft's built-in template: empty navigation, radios as DCS wrote them in the source sample.

    `terrain` defaults to the template's terrain (None for the F-14, whose file has none: the user must choose it)."""
    if terrain is not None and terrain not in terrains():
        raise DtcError([f"terrain {terrain!r} is not calibrated (allowed: {', '.join(terrains())})"])
    return _build_model(default_template(aircraft), terrain)[0]


def export_with_warnings(model: dict[str, Any], template: dict[str, Any] | None = None) -> ExportResult:
    """Like export_dtc but also returns warnings (e.g. unknown elevations written as 0)."""
    errs = validate_model(model)
    if errs:
        raise DtcError(errs)
    aircraft = model["aircraft"]
    tpl = deepcopy(template) if template is not None else default_template(aircraft)
    if tpl.get("type") != aircraft:
        raise DtcError([f"template is for {tpl.get('type')!r}, model is for {aircraft!r}"])
    mod = _MODULES[aircraft]
    defaults = {**default_points(aircraft), **mod.collect_defaults(tpl)}
    out, warns = mod.apply(model, tpl, defaults)
    radios.apply(model, out)
    return ExportResult(write_json(out), warns + radio_warnings(model))


def export_dtc(model: dict[str, Any], template: dict[str, Any] | None = None) -> bytes:
    """Neutral model -> native .dtc bytes. Raises DtcError (same messages as validate_model) when invalid.

    Unknown elevations (None) are written as 0; use export_with_warnings() to receive that notice."""
    return export_with_warnings(model, template).raw
