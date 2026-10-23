import json
from pathlib import Path

import pytest

from fox3_agent.sim.world import SimWorld
from fox3_central.core.validation import ENVELOPE, Validators
from fox3_common import geo

ROOT = Path(__file__).resolve().parents[1]
SAMPLES = ROOT / "samples"


@pytest.fixture(scope="module")
def validators():
    return Validators(ROOT / "contracts" / "schemas")


def test_simulated_payloads_match_contracts(validators):
    w = SimWorld(seed=3)
    for _ in range(60):
        w.tick()
    for name, payload in [("server_info", w.server_info()), ("foothold_state", w.foothold_state()),
                          ("players", w.players()), ("events", w.drain_events())]:
        assert validators.errors(name, payload) == [], name
    for payload in w.tacview_indexes():
        assert validators.errors("tacview_index", payload) == []


def test_envelope_rejects_missing_fields(validators):
    assert validators.errors(ENVELOPE, {"schema_version": 1})


@pytest.mark.parametrize("terrain", ["Caucasus", "Syria"])
def test_projection_round_trip(terrain):
    x, y = geo.latlon_to_xy(terrain, 36.0, 35.5 if terrain == "Syria" else 41.0)
    lat, lon = geo.xy_to_latlon(terrain, x, y)
    assert abs(lat - 36.0) < 1e-9


def test_uncalibrated_terrain_is_refused():
    assert not geo.is_calibrated("Marianas")
    assert geo.xy_to_latlon("Marianas", 0, 0) is None


@pytest.mark.skipif(not (SAMPLES / "F-14BU_DTC.dtc").exists(), reason="sample .dtc not present")
def test_caucasus_reproduces_f14_sample():
    data = json.loads((SAMPLES / "F-14BU_DTC.dtc").read_bytes().decode("utf-8-sig"))["data"]
    pts = [w for r in data["NAV"] for w in r["waypoints"]]
    assert pts
    for w in pts:
        x, y = geo.latlon_to_xy("Caucasus", w["lat"], w["lon"])
        assert abs(x - w["x"]) < 0.01 and abs(y - w["y"]) < 0.01
