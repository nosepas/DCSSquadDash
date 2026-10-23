"""Aggregated, value-free shape of parsed Lua data (the basis of the redacted outline in describe.py)."""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any

from .normalize import KNOWN_TOP_KEYS

# Tables whose KEYS are data (zone names, player names, item names...): keys are never shown, only their count.
MAP_PATHS = frozenset({
    ("zones",), ("zonesDetails",), ("playerStats",), ("tankers",), ("customFlags",), ("ewrsSettings",), ("shops", "[]"),
    ("zones", "*", "remainingUnits"), ("zones", "*", "destroyed"), ("zones", "*", "extraUpgrade"), ("zones", "*", "triggers"),
})
KNOWN_NAMES = frozenset({
    "side", "active", "level", "upgradesUsed", "upgradesUsedRed", "upgradesUsedBlue", "logisticCenter", "firstCaptureByRed",
    "wasBlue", "lat_long", "latitude", "longitude", "altitude", "remainingUnits", "destroyed", "extraUpgrade", "triggers",
    "randomUpgradesRed", "randomUpgradesBlue", "flavorText", "hidden", "name", "stats", "Points", "Points spent", "Deaths", "Air",
    "SAM", "Ground Units", "Infantry", "Helo", "Structure", "Zone capture", "Zone upgrade", "CAS mission", "CAP mission",
    "Recon mission", "Pilot Rescue", "Flight time", "Warehouse delivery", "Bomb runway", "Intercept cargo plane", "playerName",
    "lostCredits", "title", "description", "isEscortMission", "isRunning", "from", "to", "coalition", "unitType", "stock",
    "heading", "leg", "speed", "unlocked",
})
COORD_NAMES = frozenset({"latitude", "longitude", "altitude", "lat", "lon", "x", "y", "z"})
_IDENT = re.compile(r"^[A-Za-z][A-Za-z0-9_ ]{0,30}$")


@dataclass
class Shape:
    count: int = 0
    types: Counter = field(default_factory=Counter)
    lo: float | None = None
    hi: float | None = None
    size_lo: int | None = None
    size_hi: int | None = None
    bools: Counter = field(default_factory=Counter)
    fields: dict[str, Shape] = field(default_factory=dict)
    entry: Shape | None = None
    redacted: Counter = field(default_factory=Counter)


def _type(v: Any) -> str:
    if isinstance(v, bool):
        return "bool"
    if isinstance(v, int):
        return "int"
    if isinstance(v, float):
        return "float" if math.isfinite(v) else "float(non-finite)"
    return {str: "str", dict: "table", list: "sequence"}.get(type(v), type(v).__name__)


def _visible(key: Any, value: Any, path: tuple[str, ...]) -> bool:
    """Whether a record key may be printed. Unknown names are printed only when they look like a field name and
    sit on a scalar, near the root: a table under an unknown key could hold player or unit names."""
    if not isinstance(key, str):
        return False
    if not path:
        return bool(_IDENT.match(key))
    if path[0] not in KNOWN_TOP_KEYS:
        return key in KNOWN_NAMES
    return key in KNOWN_NAMES or (bool(_IDENT.match(key)) and not isinstance(value, (dict, list)) and len(path) <= 3)


def _sized(shape: Shape, size: int) -> None:
    shape.size_lo = size if shape.size_lo is None else min(shape.size_lo, size)
    shape.size_hi = size if shape.size_hi is None else max(shape.size_hi, size)


def add(shape: Shape, value: Any, path: tuple[str, ...] = ()) -> None:
    kind = _type(value)
    shape.count += 1
    shape.types[kind] += 1
    if kind in ("int", "float"):
        shape.lo = value if shape.lo is None else min(shape.lo, value)
        shape.hi = value if shape.hi is None else max(shape.hi, value)
    elif kind == "bool":
        shape.bools[value] += 1
    elif kind == "sequence":
        _sized(shape, len(value))
        shape.entry = shape.entry or Shape()
        for element in value:
            add(shape.entry, element, (*path, "[]"))
    elif kind == "table":
        _sized(shape, len(value))
        is_map = path in MAP_PATHS
        for key, child in value.items():
            if not is_map and _visible(key, child, path):
                add(shape.fields.setdefault(key, Shape()), child, (*path, key))
            else:
                shape.redacted[type(key).__name__] += 1
                shape.entry = shape.entry or Shape()
                add(shape.entry, child, (*path, "*"))
