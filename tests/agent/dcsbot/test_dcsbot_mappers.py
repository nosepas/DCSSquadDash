from __future__ import annotations

import copy

import pytest
from dcsbot_fakes import SERVER, T0, UCID1, UCID2, USERS, VALIDATORS

from fox3_agent.sources.dcsbot.players_mapper import coalition_of, map_players
from fox3_agent.sources.dcsbot.server_mapper import map_server_info, map_weather, select_server
from fox3_agent.sources.dcsbot.ucid_resolver import UcidResolver


def test_server_info_whitelist_and_contract():
    p = map_server_info(SERVER, mission_type="foothold", now=T0)
    assert VALIDATORS.errors("server_info", p) == []
    blob = repr(p)
    for secret in ("TOPSECRET", "1.2.3.4", "restart", "SRS", "Chevy", "password", "address"):
        assert secret not in blob
    assert p["server_name"] == "FOX3 Test" and p["terrain"] == "Syria" and p["mission_name"] == "Foothold Syria"
    assert p["mission_started_at"] == "2026-01-01T11:00:00Z" and p["max_players"] == 32
    assert p["capabilities"] == {"foothold": True, "tacview": False, "grpc": False, "dcsbot_rest": True, "dcsbot_db": False}


def test_generic_mission_type_and_missing_mission():
    s = copy.deepcopy(SERVER)
    del s["mission"], s["weather"]
    p = map_server_info(s, mission_type="generic", now=T0)
    assert VALIDATORS.errors("server_info", p) == []
    assert p["mission_started_at"] is None and p["mission_name"] is None and "weather" not in p
    assert p["capabilities"]["foothold"] is False


def test_weather_unit_conversions():
    w = map_weather({"temperature": 15.5, "pressure": 760.0, "wind_speed": 10, "wind_direction": 270, "visibility": 9999,
                     "clouds_base": 8000})
    assert w == {"temperature_c": 15.5, "qnh_hpa": 1013.2, "wind_speed_ms": 5.1, "wind_dir_deg": 270.0,
                 "visibility_m": 9999.0, "cloud_base_m": 2438.4}
    assert map_weather(None) is None and map_weather({"temperature": "x"}) is None


def test_select_server():
    a, b = {"name": "A"}, {"name": "B"}
    assert select_server([a, b], "B") is b
    assert select_server([a, b], "") is None
    assert select_server([a], "") is a
    assert select_server([a], "Z") is None


def make_resolver(calls: list[str], now: list[float], **kw) -> UcidResolver:
    def lookup(name: str):
        calls.append(name)
        return USERS.get(name, [])
    return UcidResolver(lookup, lambda: now[0], server_name="FOX3 Test", **kw)


def test_ucid_resolution_exact_match_and_cache():
    calls: list[str] = []
    r = make_resolver(calls, [0.0])
    assert r.resolve("Pilot1") == UCID1   # not the substring match "Pilot10"
    assert r.resolve("Pilot1") == UCID1
    assert r.resolve("Pilot2") == UCID2   # case-insensitive fallback
    assert calls == ["Pilot1", "Pilot2"]


def test_negative_cache_and_expiry_and_rate_limit():
    calls: list[str] = []
    now = [0.0]
    r = make_resolver(calls, now, max_lookups_per_cycle=2, negative_ttl_s=60)
    assert r.resolve("ghost") is None and r.resolve("ghost") is None
    assert calls == ["ghost"]
    now[0] = 61
    r.resolve("ghost")
    assert calls == ["ghost", "ghost"]
    r.new_cycle()
    assert r.resolve("a") is None and r.resolve("b") is None and r.resolve("c") is None
    assert calls[-2:] == ["a", "b"]   # budget of 2 per cycle: "c" is never looked up


def test_players_mapping_omits_unresolved_and_drops_extras():
    r = make_resolver([], [0.0])
    raw = [*SERVER["players"], {"nick": "Ghost", "side": "blue"}, {"nick": ""}, "junk"]
    payload, unresolved = map_players(raw, r, T0)
    assert unresolved == 1 and VALIDATORS.errors("players", payload) == []
    assert [p["name"] for p in payload["players"]] == ["Pilot1", "Pilot2"]
    p1, p2 = payload["players"]
    assert p1["coalition"] == "blue" and p1["aircraft"] == "FA-18C_hornet" and p1["in_air"] is False
    assert p2["coalition"] == "red" and p2["aircraft"] is None
    assert "Chevy" not in repr(payload) and "radios" not in repr(payload)


@pytest.mark.parametrize("side,exp", [("BLUE", "blue"), ("neutral", "neutral"), ("UNKNOWN", "unknown"), (None, "unknown")])
def test_side_strings(side, exp):
    assert coalition_of(side) == exp
