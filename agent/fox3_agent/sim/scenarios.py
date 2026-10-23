"""Demo scenarios: three fictional servers (two Foothold maps and one training server that is not Foothold)."""
from __future__ import annotations

from dataclasses import dataclass

from . import data


@dataclass(frozen=True)
class Scenario:
    key: str
    server_name: str
    terrain: str
    mission_name: str
    mission_type: str  # foothold | generic
    zones: tuple  # (name, lat, lon, coalition, is_hq); empty for generic missions
    connections: tuple
    center: tuple[float, float]  # where aircraft spawn when there are no zones
    farps: tuple = ()  # (name, lat, lon) of player-built FARPs


SYRIA_ZONES = (
    ("Hmeimim", 35.401, 35.949, "red", False), ("Latakia", 35.52, 35.78, "red", False), ("Tartus", 34.89, 35.88, "red", False),
    ("Homs", 34.73, 36.72, "red", False), ("Damascus", 33.41, 36.51, "red", True), ("Palmyra", 34.55, 38.28, "neutral", False),
    ("Aleppo", 36.18, 37.22, "neutral", False), ("Incirlik", 37.0, 35.43, "blue", True), ("Hatay", 36.36, 36.28, "blue", False),
    ("Beirut", 33.82, 35.49, "blue", False), ("Ramat David", 32.67, 35.18, "blue", False), ("Haifa", 32.81, 35.04, "blue", False),
)
SYRIA_LINKS = (("Hmeimim", "Latakia"), ("Latakia", "Tartus"), ("Tartus", "Homs"), ("Homs", "Damascus"), ("Homs", "Palmyra"),
               ("Hmeimim", "Hatay"), ("Hatay", "Aleppo"), ("Hatay", "Incirlik"), ("Tartus", "Beirut"), ("Beirut", "Haifa"),
               ("Haifa", "Ramat David"), ("Aleppo", "Palmyra"))

CAUCASUS = Scenario("caucasus", "FOX3 Foothold Caucasus", "Caucasus", "Foothold Caucasus (demo)", "foothold",
                    tuple(data.ZONES), tuple(data.CONNECTIONS), (43.5, 40.5),
                    (("CTLD FARP Alpha", 43.0, 40.9), ("CTLD FARP Bravo", 42.5, 42.2)))
SYRIA = Scenario("syria", "FOX3 Foothold Syria", "Syria", "Foothold Syria (demo)", "foothold", SYRIA_ZONES, SYRIA_LINKS, (35.0, 36.5),
               (("CTLD FARP Cedar", 34.1, 36.0), ("CTLD FARP Dune", 35.4, 37.6)))
TRAINING = Scenario("training", "FOX3 Training", "Caucasus", "Free flight training (demo)", "generic", (), (), (43.1, 41.0))
SCENARIOS = {s.key: s for s in (CAUCASUS, SYRIA, TRAINING)}
