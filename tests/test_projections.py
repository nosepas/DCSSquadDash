"""Every supported map: DCS airport coordinates (x = north, y = east, from pydcs' airport tables) must land on the real-world
airport. A wrong projection parameter would be off by hundreds of km, so a 2 km tolerance is a strict check of the parameters."""
import math

import pytest

from fox3_common import geo


def _km(a, b, c, d):
    p = math.radians
    return 6371 * math.hypot((p(d) - p(b)) * math.cos(p((a + c) / 2)), p(c) - p(a))


@pytest.mark.parametrize("terrain", sorted(geo.PARAMS))
def test_every_map_has_a_calibration_level(terrain):
    assert geo.calibration(terrain) in ("exact", "plausible", "airports") and geo.is_calibrated(terrain)


def test_unknown_map_is_not_calibrated():
    assert geo.calibration("Atlantis") is None and not geo.is_calibrated("Atlantis")


@pytest.mark.parametrize("terrain,lat,lon", [
    ("Nevada", 36.2362, -115.0342), ("MarianaIslands", 15.1190, 145.7290), ("PersianGulf", 24.2482, 54.5477),
    ("Sinai", 30.7761, 34.6667), ("Falklands", -51.8228, -58.4472), ("Normandy", 49.1733, -0.4503),
    ("TheChannel", 51.3422, 1.3461), ("GermanyCW", 49.4369, 7.6003), ("Kola", 68.7817, 32.7508),
    ("Caucasus", 41.6103, 41.5997), ("Syria", 37.0021, 35.4259),
])
def test_round_trip_is_exact_for_every_map(terrain, lat, lon):
    x, y = geo.latlon_to_xy(terrain, lat, lon)
    assert _km(*geo.xy_to_latlon(terrain, x, y), lat, lon) < 1e-6


# (terrain, DCS x, DCS y, real lat, real lon): DCS airport coordinates (pydcs airport tables) and the public coordinates of the same airport
REAL = [
    ("Caucasus", -355810.703125, 617386.1875, 41.6103, 41.5997),  # Batumi
    ("Syria", 221207.773438, -35240.347656, 37.0021, 35.4259),  # Incirlik
    ("Nevada", -398195.375, -17233.236816, 36.2362, -115.0342),  # Nellis
    ("MarianaIslands", 180035.4375, 101855.960938, 15.119, 145.729),  # Saipan_Intl
    ("PersianGulf", -211027.78125, -173240.007812, 24.2482, 54.5477),  # Al_Dhafra_AFB
    ("Sinai", 80825.4375, 328661.15625, 30.7761, 34.6667),  # Ramon_Airbase
    ("Falklands", 73318.320313, 47168.748047, -51.8228, -58.4472),  # Mount_Pleasant
    ("Normandy", -34769.425781, -10001.302734, 49.1733, -0.4503),  # Carpiquet
    ("TheChannel", 52264.839844, -15815.91748, 51.3422, 1.3461),  # Manston
    ("GermanyCW", -498696.890625, -934641.75, 49.4369, 7.6003),  # Ramstein
    ("Kola", 131730.496094, 409479.0, 68.7817, 32.7508),  # Murmansk_International
]


@pytest.mark.parametrize("terrain,x,y,lat,lon", REAL)
def test_dcs_airport_lands_on_the_real_airport(terrain, x, y, lat, lon):
    assert _km(*geo.xy_to_latlon(terrain, x, y), lat, lon) < 2.0
