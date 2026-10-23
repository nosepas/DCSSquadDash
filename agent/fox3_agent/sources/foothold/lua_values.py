"""Small value helpers of the Lua parser."""
from __future__ import annotations

import math

KEYWORDS = {"true": True, "false": False, "nil": None, "inf": math.inf, "nan": math.nan}


def is_number(v: object) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def sequence_or_table(table: dict) -> dict | list:
    """A table whose keys are exactly 1..n becomes a list."""
    n = len(table)
    if n and all(type(k) is int for k in table) and min(table) == 1 and max(table) == n:
        return [table[i] for i in range(1, n + 1)]
    return table
