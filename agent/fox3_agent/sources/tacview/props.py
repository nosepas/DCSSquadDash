"""Cheap helpers to parse ACMI property lines, only used on the few lines that need a full parse."""
from __future__ import annotations

from datetime import UTC, datetime

MAX_TEXT = 256

# Documented side rule: Color wins (Red/Blue); otherwise the Coalition text, only when unambiguous.
# "Enemies"/"Allies" are relative to the recording player in Tacview, so they stay 'unknown'.
_COLOR = {"red": "red", "blue": "blue"}
_COALITION = {"red": "red", "blue": "blue", "neutral": "neutral", "neutrals": "neutral"}


def split_props(line: bytes) -> list[bytes]:
    """Split on commas that are not escaped with an odd number of backslashes."""
    if b"\\" not in line:
        return line.split(b",")
    parts: list[bytes] = []
    cur: bytes | None = None
    for piece in line.split(b","):
        cur = piece if cur is None else cur + b"," + piece
        if (len(cur) - len(cur.rstrip(b"\\"))) % 2 == 0:
            parts.append(cur)
            cur = None
    if cur is not None:
        parts.append(cur)
    return parts


def parse_props(line: bytes) -> dict[str, str]:
    """`id,A=1,B=2` -> {"A": "1", "B": "2"} (text after the first '=' of each part; escapes resolved)."""
    props: dict[str, str] = {}
    for part in split_props(line)[1:]:
        key, sep, value = part.partition(b"=")
        if sep and key:
            props[key.decode("ascii", "replace")] = value.replace(b"\\,", b",").decode("utf-8", "replace")
    return props


def clean(value: str | None) -> str | None:
    if value is None:
        return None
    value = value.strip()[:MAX_TEXT]
    return value or None


def map_side(color: str | None, coalition: str | None, extra: dict[str, str] | None = None) -> str:
    """Contract coalition (red|blue|neutral|unknown). `extra` maps additional lowercase Coalition texts."""
    if color and color.strip().lower() in _COLOR:
        return _COLOR[color.strip().lower()]
    if coalition:
        key = coalition.strip().lower()
        if extra and key in extra:
            return extra[key]
        return _COALITION.get(key, "unknown")
    return "unknown"


def normalize_utc(value: str | None) -> str | None:
    """ACMI ReferenceTime -> '2011-06-02T05:00:00Z'; None if unparsable."""
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.strip())
    except ValueError:
        return None
    dt = dt.replace(tzinfo=UTC) if dt.tzinfo is None else dt.astimezone(UTC)
    return dt.strftime("%Y-%m-%dT%H:%M:%SZ")
