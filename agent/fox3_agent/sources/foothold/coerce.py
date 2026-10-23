"""Defensive accessors over parsed Lua data: every helper returns None / empty instead of raising."""
from __future__ import annotations

import math
from typing import Any

MAX_NOTES = 40


def items(value: Any) -> list[tuple[Any, Any]]:
    """(key, value) pairs of a parsed table, whether it came out as a dict or as a 1..n list."""
    if isinstance(value, dict):
        return list(value.items())
    if isinstance(value, list):
        return list(enumerate(value, 1))
    return []


def get(record: Any, key: str) -> Any:
    return record.get(key) if isinstance(record, dict) else None


def num(value: Any) -> int | float | None:
    """A finite number (bool, nan and inf are rejected: they cannot be serialised to JSON)."""
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return value if math.isfinite(value) else None


def integer(value: Any) -> int | None:
    n = num(value)
    return int(n) if n is not None and float(n).is_integer() else None


def text(value: Any, limit: int = 200) -> str | None:
    return value[:limit] if isinstance(value, str) else None


def flag(value: Any) -> bool | None:
    return value if isinstance(value, bool) else None


def lat_lon(lat: Any, lon: Any) -> tuple[float, float] | None:
    la, lo = num(lat), num(lon)
    if la is None or lo is None or not (-90 <= la <= 90 and -180 <= lo <= 180):
        return None
    return float(la), float(lo)


class Notes:
    """Ordered, de-duplicated, capped list of parser remarks (goes into `format_notes`)."""

    def __init__(self) -> None:
        self._notes: list[str] = []

    def add(self, note: str) -> None:
        if note not in self._notes:
            if len(self._notes) < MAX_NOTES:
                self._notes.append(note)
            elif len(self._notes) == MAX_NOTES:
                self._notes.append("further notes omitted")

    def dropped(self, section: str, count: int, what: str = "invalid entries") -> None:
        if count:
            self.add(f"{section}: dropped {count} {what}")

    def as_list(self) -> list[str]:
        return list(self._notes)
