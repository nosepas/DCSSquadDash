"""lat/lon (WGS84, source of truth) <-> DCS x/y for one terrain, with exact reuse of unchanged original coordinates."""
from __future__ import annotations

from typing import Any

from fox3_common import geo

from .errors import DtcError
from .model import num

LATLON_DECIMALS = 10  # ~10 micrometres; keeps the model free of float noise
REUSE_TOLERANCE_DEG = 2e-9  # original DCS x/y are reused when they still match lat/lon within ~0.2 mm
XY_KEY = "dcs_xy"  # point.extra key holding the original [x, y] seen on import


def from_xy(terrain: str | None, x: float, y: float) -> tuple[float, float]:
    ll = geo.xy_to_latlon(terrain, x, y)
    if ll is None:
        raise DtcError([f"terrain {terrain!r} is not calibrated; cannot convert DCS coordinates"])
    return round(ll[0], LATLON_DECIMALS), round(ll[1], LATLON_DECIMALS)


def to_xy(terrain: str, point: dict[str, Any]) -> tuple[float, float]:
    """DCS (x, y) for a neutral point. Reuses extra['dcs_xy'] when it is still consistent with lat/lon on this terrain."""
    lat, lon = point["lat"], point["lon"]
    orig = (point.get("extra") or {}).get(XY_KEY)
    if isinstance(orig, list) and len(orig) == 2:
        back = geo.xy_to_latlon(terrain, orig[0], orig[1])
        if back and abs(back[0] - lat) < REUSE_TOLERANCE_DEG and abs(back[1] - lon) < REUSE_TOLERANCE_DEG:
            return orig[0], orig[1]
    xy = geo.latlon_to_xy(terrain, lat, lon)
    if xy is None:
        raise DtcError([f"terrain {terrain!r} is not calibrated"])
    return num(xy[0]), num(xy[1])


def guess_terrains(samples: list[tuple[float, float, float, float]]) -> list[str]:
    """Terrains whose projection maps each (x, y, lat, lon) sample to its lat/lon within 1e-6 deg."""
    found = []
    for terrain in geo.PARAMS:
        ok = bool(samples)
        for x, y, lat, lon in samples:
            ll = geo.xy_to_latlon(terrain, x, y)
            ok = ok and ll is not None and abs(ll[0] - lat) < 1e-6 and abs(ll[1] - lon) < 1e-6
        if ok:
            found.append(terrain)
    return found
