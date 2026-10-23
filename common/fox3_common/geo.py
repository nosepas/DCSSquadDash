"""DCS map projections (Transverse Mercator, k=0.9996, WGS84). DCS x = northing, y = easting, in metres.

Parameters of the 11 maps come from the projection exporter of the open-source pydcs project (numeric constants), which is
generated from DCS itself. How far each one is trusted (`CALIBRATION`):
- "exact":     reproduces a real DCS file of ours with sub-millimetre error (Caucasus, F-14 sample).
- "plausible": consistent with a real DCS file of ours, which carries no lat/lon to compare (Syria, F-16 sample), and identical
               to the pydcs value.
- "airports":  not checked against our own files; pydcs airport positions (DCS x,y) land within ~1 km of the real-world airport
               coordinates (tests/test_projections.py). A wrong parameter would be off by hundreds of km. NOT verified in the game.
"""
from __future__ import annotations

from functools import cache

from pyproj import Transformer

# terrain id -> (central meridian, false easting, false northing)
PARAMS = {
    "Caucasus": (33, -99516.9999999732, -4998114.999999984),
    "Syria": (39, 282801.00000003993, -3879865.9999999935),
    "Nevada": (-117, -193996.80999964548, -4410028.063999966),
    "PersianGulf": (57, 75755.99999999645, -2894933.0000000377),
    "MarianaIslands": (147, 238417.99999989968, -1491840.000000048),
    "Sinai": (33, 169221.9999999585, -3325312.9999999693),
    "Falklands": (-57, 147639.99999997593, 5815417.000000032),
    "Normandy": (-3, -195526.00000000204, -5484812.999999951),
    "TheChannel": (3, 99376.00000000288, -5636889.00000001),
    "GermanyCW": (21, 35427.619999985734, -6061633.128000011),
    "Kola": (21, -62702.00000000087, -7543624.999999979),
}
CALIBRATION = {"Caucasus": "exact", "Syria": "plausible", **{t: "airports" for t in PARAMS if t not in ("Caucasus", "Syria")}}


@cache
def _tr(terrain: str, inverse: bool) -> Transformer | None:
    p = PARAMS.get(terrain)
    if not p:
        return None
    lon0, fe, fn = p
    tm = f"+proj=tmerc +lat_0=0 +lon_0={lon0} +k_0=0.9996 +x_0={fe} +y_0={fn} +ellps=WGS84 +units=m"
    return Transformer.from_crs(tm, "EPSG:4326", always_xy=True) if inverse else Transformer.from_crs("EPSG:4326", tm, always_xy=True)


def is_calibrated(terrain: str | None) -> bool:
    return terrain in PARAMS


def calibration(terrain: str | None) -> str | None:
    """'exact' | 'plausible' | 'airports' | None (unknown map)."""
    return CALIBRATION.get(terrain or "")


def xy_to_latlon(terrain: str | None, x: float, y: float) -> tuple[float, float] | None:
    t = _tr(terrain, True) if terrain else None
    if t is None:
        return None
    lon, lat = t.transform(y, x)
    return lat, lon


def latlon_to_xy(terrain: str | None, lat: float, lon: float) -> tuple[float, float] | None:
    t = _tr(terrain, False) if terrain else None
    if t is None:
        return None
    e, n = t.transform(lon, lat)
    return n, e
