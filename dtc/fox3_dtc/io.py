"""Read/write DCS .dtc JSON preserving the exact style DCS writes.

Style facts (verified on the owner's samples, see tests): UTF-8 without BOM, LF newlines, no trailing newline, non-ASCII kept
literal, dict key order preserved. Inside an object the keys are right-aligned: a child object's keys start at column
``key_start + len(quoted_key) + 6`` and the longest key starts there; the closing bracket sits 4 columns left of that column.
Empty list is ``[  ]``; scalar lists are ``[ 1, 2 ]``; object lists are ``[ {`` ... ``}, {`` ... ``} ]``.
"""
from __future__ import annotations

import json
from typing import Any

from .errors import DtcError
from .limits import check_limits


def read_json(raw: bytes) -> dict[str, Any]:
    """Parse a .dtc payload (tolerates a UTF-8 BOM); raises DtcError when it is not a JSON object or exceeds the structural limits."""
    try:
        data = json.loads(raw.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise DtcError([f"not a valid .dtc (JSON) file: {exc}"]) from exc
    except (RecursionError, MemoryError) as exc:
        raise DtcError(["unsupported .dtc: JSON too deeply nested or too large"]) from exc
    if not isinstance(data, dict):
        raise DtcError(["not a valid .dtc file: top level is not an object"])
    check_limits(data)
    return data


class _Budget:
    """Running byte counter: charged before each piece is built, so an oversized export aborts without materialising it."""

    def __init__(self, limit: int) -> None:
        self.left = limit

    def charge(self, n: int) -> None:
        self.left -= n
        if self.left < 0:
            raise DtcError(["the .dtc would be too large to export"])


def _scalar(v: Any) -> str:
    return json.dumps(v, ensure_ascii=False)


def _is_scalar(v: Any) -> bool:
    return not isinstance(v, dict | list)


def _array(v: list[Any], base: int, b: _Budget) -> str:
    if not v:
        return "[  ]"
    if all(_is_scalar(x) for x in v):
        parts = [_scalar(x) for x in v]
        b.charge(sum(map(len, parts)) + 2 * len(parts) + 2)
        return "[ " + ", ".join(parts) + " ]"
    if all(isinstance(x, dict) for x in v):
        b.charge(2 * len(v) + 2)
        return "[ " + ", ".join(_object(x, base, b) for x in v) + " ]"
    raise DtcError(["unsupported mixed/nested list in .dtc"])


def _width(s: str) -> int:
    return len(s.encode("utf-8"))  # DCS aligns by UTF-8 byte length (verified: en dash in F-16 threat names)


def _object(d: dict[str, Any], base: int, b: _Budget) -> str:
    if not d:
        return "{  }"
    width = max(_width(_scalar(k)) for k in d)
    b.charge(base + 4 + len(d) * 3)  # closing indent, braces and separators
    lines = []
    for k, v in d.items():
        q = _scalar(k)
        start = base + width - _width(q)
        child = start + _width(q) + 6
        b.charge(start + len(q) + 2)  # BEFORE the indentation string exists
        val = _object(v, child, b) if isinstance(v, dict) else _array(v, child, b) if isinstance(v, list) else _scalar(v)
        if _is_scalar(v):
            b.charge(len(val))
        lines.append(" " * start + q + ": " + val)
    return "{\n" + ",\n".join(lines) + "\n" + " " * (base - 4) + "}"


MIN_OUTPUT_CAP = 16 * 1024 * 1024


def write_json(data: dict[str, Any]) -> bytes:
    """Serialise in DCS style (see module docstring); raises DtcError past max(16 MiB, 4 x the compact JSON size)."""
    try:
        compact = len(json.dumps(data, ensure_ascii=False, separators=(",", ":")).encode("utf-8"))
        return _object(data, 4, _Budget(max(MIN_OUTPUT_CAP, 4 * compact))).encode("utf-8")
    except (RecursionError, MemoryError) as exc:
        raise DtcError(["the .dtc is too deeply nested or too large to export"]) from exc
