"""Renumbering of DCS point ids (e.g. STPT1 -> STPT7, OA11Line -> OA17Line)."""
from __future__ import annotations

from typing import Any

from .errors import DtcError


def renumber_id(value: str, old: int, new: int) -> str:
    """Replace the trailing number `old` of an id (optionally followed by 'Line') with `new`."""
    suffix = "Line" if value.endswith("Line") else ""
    core = value[: len(value) - len(suffix)]
    if not core.endswith(str(old)):
        raise DtcError([f"cannot renumber id {value!r}: it does not end with its point number {old}"])
    return core[: len(core) - len(str(old))] + str(new) + suffix


def renumber(point: dict[str, Any], number_key: str, id_keys: tuple[str, ...], new: int) -> dict[str, Any]:
    """Return a copy of `point` renumbered to `new` (the number field and every id derived from it)."""
    old = point[number_key]
    out = dict(point)
    for key in id_keys:
        if key in out and isinstance(out[key], str):
            out[key] = renumber_id(out[key], old, new)
    out[number_key] = new
    return out
