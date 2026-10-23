"""Regression tests for the findings of the independent security review (each one was reproduced before being fixed)."""
import uuid

import pytest

from fox3_agent.protocol import envelope
from fox3_central.core.ratelimit import RateLimiter
from fox3_central.repositories import players

BLUE, RED = "b" * 32, "r" * 32


def _players(client, headers):
    pl = [{"ucid": RED, "name": "Red1", "coalition": "red", "aircraft": "Su-27", "in_air": True,
           "position": {"lat": 44.0, "lon": 39.0, "alt_m": 8000}},
          {"ucid": BLUE, "name": "Blue1", "coalition": "blue", "aircraft": "F-16C_50", "in_air": True,
           "position": {"lat": 43.0, "lon": 41.0, "alt_m": 5000}}]
    assert client.post("/agent/v1/players", json=envelope({"snapshot_at": "2026-01-01T00:00:00Z", "players": pl}), headers=headers).status_code == 200


def test_online_list_does_not_reveal_the_enemy_to_normal_users(client, agent_headers, user_client, admin_client, server_id):
    _players(client, agent_headers)
    rows = user_client.get(f"/api/v1/servers/{server_id}/players/online").json()
    assert sorted(r["name"] for r in rows) == ["Blue1", "Red1"]
    assert all(set(r) == {"name"} for r in rows)  # no coalition, aircraft, slot, position or ucid
    full = admin_client.get(f"/api/v1/servers/{server_id}/players/online").json()
    assert all("position" in r and "coalition" in r for r in full)


def test_disabled_server_is_hidden_from_player_profiles(client, agent_headers, user_client, admin_client, server_id):
    ev = {"event_id": "k1", "type": "kill", "time_utc": "2026-01-01T00:00:00Z", "actor": {"ucid": BLUE, "name": "Ace", "coalition": "blue"},
          "target": {"name": "T", "is_player": False}}
    client.post("/agent/v1/events", json=envelope({"events": [ev]}), headers=agent_headers)
    assert len(user_client.get(f"/api/v1/players/{BLUE}").json()["servers"]) == 1
    admin_client.patch(f"/api/v1/admin/servers/{server_id}", json={"enabled": False})
    assert user_client.get(f"/api/v1/players/{BLUE}").json()["servers"] == []


def test_interactive_api_docs_are_not_exposed_in_production(tmp_path):
    from fastapi.testclient import TestClient

    from fox3_central.app import create_app
    from fox3_central.config import Settings
    prod = TestClient(create_app(Settings(db_url=f"sqlite:///{(tmp_path / 'p.sqlite').as_posix()}", demo_login=False, web_dir=None)))
    for path in ("/api/docs", "/api/openapi.json", "/redoc", "/docs"):
        assert prod.get(path).status_code in (401, 404), path


def test_rate_limiter_memory_is_bounded():
    limiter = RateLimiter(max_keys=100)
    for i in range(1000):
        limiter.allow(f"attacker-supplied-{i}", 5)
    assert len(limiter._hits) <= 101  # noqa: SLF001


def test_garbage_agent_ids_are_rejected_without_touching_the_limiter_per_id(client, app):
    ctx = app.state.ctx
    for _ in range(5):
        r = client.post("/agent/v1/heartbeat", json={}, headers={"Authorization": f"Bearer {'A' * 4000}.x"})
        assert r.status_code == 401
    assert not any(k.startswith("agent:") for k in ctx.limiter._hits)  # noqa: SLF001


def test_guessing_a_real_agent_id_cannot_lock_the_real_agent_out(client, agent_headers):
    agent_id = agent_headers["Authorization"].split()[1].split(".")[0]
    for _ in range(70):  # more failures than the per-address budget, using the REAL agent id with wrong secrets
        client.post("/agent/v1/heartbeat", json={}, headers={"Authorization": f"Bearer {agent_id}.wrong"})
    # the failures are counted per client address; a different address (the real agent) is not affected
    from fastapi.testclient import TestClient
    other = TestClient(client.app, client=("203.0.113.9", 5000))
    msg = envelope({"agent_version": "1", "uptime_s": 1, "queue_depth": 0})
    assert other.post("/agent/v1/heartbeat", json=msg, headers=agent_headers).status_code == 200


@pytest.mark.parametrize("term", ["%", "_", "a%b", "\\"])
def test_like_wildcards_typed_by_users_are_literals(app, term):
    with app.state.ctx.tx() as cn:
        players.touch(cn, "u" * 32, "Alice")
        players.touch(cn, "v" * 32, "100%_real")
        found = {p["last_name"] for p in players.search(cn, term, 10)}
    assert "Alice" not in found  # '%' or '_' must not match everything
    if term in ("%", "_"):
        assert found == {"100%_real"}


def test_uuid_helper_only_accepts_canonical_uuids():
    from fox3_central.services.agents import _is_uuid
    assert _is_uuid(str(uuid.uuid4())) and not _is_uuid("x" * 36) and not _is_uuid("") and not _is_uuid(str(uuid.uuid4()).upper() + "0")
