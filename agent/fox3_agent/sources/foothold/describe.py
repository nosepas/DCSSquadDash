"""Redacted outline of a Foothold persistence file, safe to send for format verification.

Shows key names of the known format, types, counts and numeric ranges. Never shows string values, player/unit/zone
names, or coordinate values. Keys that are data (zone/player/item names) are replaced by a count.
"""
from __future__ import annotations

from pathlib import Path

from .describe_shape import COORD_NAMES, Shape, add
from .lua_errors import LuaParseError
from .lua_parser import parse_lua


def _fmt(n: float) -> str:
    return str(int(n)) if float(n).is_integer() else f"{n:.4g}"


def _summary(name: str, shape: Shape) -> str:
    parts = [f"{'|'.join(sorted(shape.types))} x{shape.count}"]
    if shape.lo is not None and name not in COORD_NAMES:
        parts.append(f"range {_fmt(shape.lo)}..{_fmt(shape.hi)}")
    if shape.bools:
        parts.append(f"true={shape.bools[True]} false={shape.bools[False]}")
    if shape.size_lo is not None:
        parts.append(f"size {shape.size_lo}..{shape.size_hi}")
    if shape.redacted:
        parts.append("keys redacted: " + ", ".join(f"{n} {t}" for t, n in sorted(shape.redacted.items())))
    return ", ".join(parts)


def _render(name: str, shape: Shape, depth: int, out: list[str]) -> None:
    out.append(f"{'  ' * depth}{name}: {_summary(name, shape)}")
    for key, child in shape.fields.items():
        _render(key, child, depth + 1, out)
    if shape.entry is not None:
        _render("<entry>", shape.entry, depth + 1, out)


def describe_structure(source: Path | str | dict) -> str:
    """Outline of a parsed dict, or of the file at the given path."""
    if isinstance(source, dict):
        parsed = source
    else:
        try:
            parsed = parse_lua(Path(source).read_bytes())
        except OSError as exc:
            return f"CANNOT READ FILE: {exc.strerror or type(exc).__name__}"
        except LuaParseError as exc:
            return f"PARSE ERROR: {exc}"
    root = Shape()
    add(root, parsed)
    out = ["zonePersistance (redacted outline: no names, no values, no coordinates)"]
    for key, child in root.fields.items():
        _render(key, child, 1, out)
    if root.redacted:
        out.append(f"  <{sum(root.redacted.values())} top-level key(s) with non-identifier names omitted>")
    return "\n".join(out)


__all__ = ["describe_structure"]
