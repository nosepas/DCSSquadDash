"""Unit conversions from DCSServerBot REST units to the FOX3 contract units."""
from __future__ import annotations

MMHG_TO_HPA = 1.33322
KNOT_TO_MS = 0.514444
FOOT_TO_M = 0.3048


def mmhg_to_hpa(value: float) -> float:
    return round(value * MMHG_TO_HPA, 1)


def knots_to_ms(value: float) -> float:
    return round(value * KNOT_TO_MS, 1)


def feet_to_m(value: float) -> float:
    return round(value * FOOT_TO_M, 1)
