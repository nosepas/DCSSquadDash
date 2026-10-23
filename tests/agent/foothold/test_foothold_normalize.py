from __future__ import annotations

from pathlib import Path

import pytest
from foothold_samples import IDENTITY_STATS, LEGACY_STATS, full_file

from fox3_agent.sources.foothold import parse_lua
from fox3_agent.sources.foothold.normalize import mission_name_from_filename, normalize
from fox3_central.core.validation import Validators

SCHEMAS = Path(__file__).resolve().parents[3] / "contracts" / "schemas"
MTIME = "2026-01-02T03:04:05Z"


@pytest.fixture(scope="module")
def validators() -> Validators:
    return Validators(SCHEMAS)


def run(text: str, name: str = "Foothold_Caucasus.lua"):
    return normalize(parse_lua(text), source_file=name, source_mtime=MTIME, snapshot_at="2026-01-02T03:05:00Z")


def zones(result) -> dict:
    return {z["name"]: z for z in result.payload["zones"]}


def test_payload_validates_against_contract(validators):
    for stats in (LEGACY_STATS, IDENTITY_STATS):
        assert validators.errors("foothold_state", run(full_file(stats)).payload) == []
    assert validators.errors("foothold_state", run("zonePersistance = {}").payload) == []


def test_zones(validators):
    z = zones(run(full_file()))
    alpha = z["Alpha"]
    assert alpha["coalition"] == "blue" and z["Bravo"]["coalition"] == "red" and z["Charlie"]["coalition"] == "neutral"
    assert alpha["geo"] == {"lat": 43.118, "lon": 40.572, "alt_m": 12.5}
    assert (alpha["level"], alpha["active"], alpha["logistic_center"], alpha["upgrades_used"]) == (3, True, True, 2)
    assert alpha["units_remaining"] == 3
    assert alpha["extra"] == {
        "was_blue": True, "first_capture_by_red": False, "upgrades_used_red": 0, "upgrades_used_blue": 2,
        "hidden": False, "flavor_text": "WPT 8", "triggers": {"missioncompleted": 3}, "destroyed_count": 2,
    }
    assert z["Bravo"]["units_remaining"] == 0 and z["Bravo"]["extra"]["hidden"] is True
    assert "is_hq" not in alpha


def test_invalid_geo_is_dropped_and_noted():
    result = run(full_file())
    assert "geo" not in zones(result)["Charlie"]
    notes = result.payload["format_notes"]
    assert any("invalid lat_long" in n for n in notes)
    assert any("someNewKey" in n for n in notes)


def test_at_risk_is_derived_from_connections():
    z = zones(run(full_file()))
    assert z["Alpha"]["at_risk"] is True and z["Bravo"]["at_risk"] is True
    assert z["Delta"]["at_risk"] is False
    assert "at_risk" not in z["Charlie"]  # neutral zones are never at risk


def test_no_connections_means_no_at_risk():
    result = run("zonePersistance = {}\nzonePersistance['zones'] = { ['A']={ ['side']=1 }, ['B']={ ['side']=2 } }")
    assert all("at_risk" not in z for z in result.payload["zones"])


def test_connections_missions_accounts_ejected():
    p = run(full_file()).payload
    assert p["connections"] == [{"from": "Alpha", "to": "Bravo"}, {"from": "Bravo", "to": "Charlie"}]
    assert [(m["title"], m["state"]) for m in p["missions"]] == [("Intercept Bombers", "active"), ("CAS", "available")]
    assert p["missions"][0]["id"] != p["missions"][1]["id"]
    assert p["missions"][0]["id"] == run(full_file()).payload["missions"][0]["id"]
    assert p["accounts"] == {"red": 0, "blue": 14524.5}
    assert p["ejected_pilots"] == [{"name": "Unknown", "lat": 43.29, "lon": 40.28, "alt_m": 481.08, "lost_credits": 50}]
    notes = p["format_notes"]
    assert any("connections: dropped 1" in n for n in notes) and any("ejectedPilots: dropped 1" in n for n in notes)


def test_legacy_player_stats():
    stats = run(full_file(LEGACY_STATS)).payload["player_stats"]
    assert stats == [{
        "name": "Mitch", "ucid": None, "identifier": None, "points": 2582.5,
        "stats": {"Deaths": 2, "Air": 2, "Ground Units": 6, "Flight time": 46},
    }]


def test_identity_player_stats():
    p = run(full_file(IDENTITY_STATS)).payload
    by_id = {s["identifier"]: s for s in p["player_stats"]}
    assert by_id["id-aaa"]["name"] == "Mitch" and by_id["id-aaa"]["points"] == 10 and by_id["id-aaa"]["stats"] == {"Deaths": 1}
    assert by_id["id-bbb"]["name"] == "id-bbb"  # blank name falls back to the identifier
    assert by_id["id-ccc"]["name"] == "id-ccc" and by_id["id-ccc"]["points"] is None
    assert all(s["ucid"] is None for s in p["player_stats"])
    assert not any("playerStatsIdentityVersion" in n for n in p["format_notes"])


def test_unknown_identity_version_detects_layout_per_entry(validators):
    text = full_file("zonePersistance['playerStatsIdentityVersion'] = 7\n"
                     "zonePersistance['playerStats'] = { ['u1']={ ['name']='New',['stats']={ ['Points']=1 } }, ['Old']={ ['Points']=2 } }\n")
    p = run(text).payload
    assert {(s["name"], s["identifier"]) for s in p["player_stats"]} == {("New", "u1"), ("Old", None)}
    assert any("unknown playerStatsIdentityVersion=7" in n for n in p["format_notes"])
    assert validators.errors("foothold_state", p) == []


def test_non_numeric_and_non_finite_figures_are_ignored(validators):
    text = full_file("zonePersistance['playerStats'] = { ['P']={ ['Points']=1e309,['Deaths']='x',['Air']=true,['SAM']=4 } }\n")
    p = run(text).payload
    assert p["player_stats"][0]["points"] is None and p["player_stats"][0]["stats"] == {"SAM": 4}
    assert validators.errors("foothold_state", p) == []


def test_positions_are_separate_from_payload():
    result = run(full_file())
    assert result.positions == [
        {"name": "APOLLO | Tomy10", "coalition": "blue", "unit_type": "F-16C_50", "lat": 43.484, "lon": 40.146, "alt_m": 5326.43},
    ]
    assert "players" not in result.payload and "positions" not in result.payload


def test_unknown_top_level_keys_and_missing_keys_are_tolerated(validators):
    result = run("zonePersistance = {}\nzonePersistance['brandNew'] = { 1, 2 }\n"
                 "zonePersistance['zones'] = 'garbage'\nzonePersistance['missions'] = 4")
    assert result.payload["zones"] == [] and result.payload["missions"] == []
    assert any("brandNew" in n for n in result.payload["format_notes"])
    assert validators.errors("foothold_state", result.payload) == []
    assert "zones" in run("zonePersistance = {}").payload["format_notes"][0]


def test_odd_zone_values_never_crash(validators):
    text = ("zonePersistance = {}\nzonePersistance['zones'] = { ['A']={ ['side']='red',['level']='x',['active']=1,['lat_long']=5,"
            "['remainingUnits']=3,['triggers']={ ['t']='s' } }, ['B']=7, [3]={ ['side']=9 } }")
    result = run(text)
    z = zones(result)
    assert z["A"]["coalition"] == "unknown" and z["A"]["level"] is None and "active" not in z["A"]
    assert "B" not in z and z["3"]["coalition"] == "unknown"
    assert validators.errors("foothold_state", result.payload) == []


def test_source_file_is_name_only_and_mission_name_rule():
    result = run(full_file(), name="C:\\Users\\bob\\Saved Games\\srv\\Missions\\Saves\\Foothold_Caucasus.lua")
    assert result.payload["source_file"] == "Foothold_Caucasus.lua" and result.payload["mission_name"] == "Caucasus"
    assert mission_name_from_filename("foothold.lua") is None
    assert mission_name_from_filename("other.lua") is None
    assert mission_name_from_filename("foothold_Syria_v2.lua") == "Syria_v2"
    assert result.payload["source_mtime"] == MTIME and result.payload["snapshot_at"].endswith("Z")
