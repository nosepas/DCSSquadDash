"""Several servers on one central: data never leaks between them, a player is one identity, generic servers work."""
import pytest

from fox3_agent.protocol import envelope
from fox3_central.repositories import servers
from fox3_central.services import agents as agent_service

UCID = "p" * 32


@pytest.fixture
def two(client, app):
    """Two servers (A foothold, B generic) each with its own paired agent."""
    out = {}
    for key, mission_type in (("a", "foothold"), ("b", "generic")):
        with app.state.ctx.tx() as cn:
            sid = servers.create(cn, f"Server {key.upper()}", mission_type)["server_id"]
        code = agent_service.create_pairing_code(app.state.ctx, sid)["pairing_code"]
        api_key = client.post("/agent/v1/pair", json={"pairing_code": code}).json()["api_key"]
        out[key] = (sid, {"Authorization": f"Bearer {api_key}"})
    return out


def _post(client, headers, path, payload):
    r = client.post(f"/agent/v1/{path}", json=envelope(payload), headers=headers)
    assert r.status_code == 200, r.text


def _kill(n, killer=UCID):
    return {"event_id": f"k{n}", "type": "kill", "time_utc": f"2026-01-01T00:00:0{n}Z",
            "actor": {"ucid": killer, "name": "Ace", "coalition": "blue"}, "target": {"name": "T-72", "is_player": False}}


def _player(coalition="blue", ucid=UCID, **extra):
    return {"ucid": ucid, "name": "Ace", "coalition": coalition, "aircraft": "F-16C_50", "in_air": True,
            "position": {"lat": 43.0, "lon": 41.0, "alt_m": 4000}, **extra}


def test_data_never_leaks_between_servers(client, two, user_client):
    (sa, ha), (sb, hb) = two["a"], two["b"]
    _post(client, ha, "foothold-state", {"snapshot_at": "2026-01-01T00:00:00Z", "zones": [{"name": "OnlyInA", "coalition": "red",
                                                                                          "geo": {"lat": 1.0, "lon": 2.0}}]})
    _post(client, ha, "events", {"events": [_kill(1), _kill(2)]})
    _post(client, hb, "events", {"events": [_kill(3)]})
    _post(client, ha, "players", {"snapshot_at": "2026-01-01T00:00:00Z", "players": [_player()]})
    assert [z["name"] for z in client.get(f"/api/v1/servers/{sa}/map").json()["zones"]] == ["OnlyInA"]
    assert client.get(f"/api/v1/servers/{sb}/map").json()["zones"] == []
    assert len(user_client.get(f"/api/v1/servers/{sa}/kills").json()) == 2
    assert len(user_client.get(f"/api/v1/servers/{sb}/kills").json()) == 1
    assert user_client.get(f"/api/v1/servers/{sa}/players/online").json() != []
    assert user_client.get(f"/api/v1/servers/{sb}/players/online").json() == []
    assert user_client.get(f"/api/v1/servers/{sb}/overview").json()["online"] == 0


def test_one_identity_with_separate_stats_per_server(client, two, user_client):
    (sa, ha), (sb, hb) = two["a"], two["b"]
    _post(client, ha, "events", {"events": [_kill(1), _kill(2), _kill(3)]})
    _post(client, hb, "events", {"events": [_kill(4)]})
    assert len(user_client.get("/api/v1/players?q=Ace").json()) == 1  # one player, not one per server
    prof = user_client.get(f"/api/v1/players/{UCID}").json()
    kills = {s["server_name"]: s["kills"] for s in prof["servers"]}
    assert kills == {"Server A": 3, "Server B": 1}
    assert [r["kills"] for r in user_client.get(f"/api/v1/servers/{sa}/ranking").json()] == [3]
    assert [r["kills"] for r in user_client.get(f"/api/v1/servers/{sb}/ranking").json()] == [1]


def test_account_link_applies_on_every_server(client, two, user_client):
    (sa, ha), (sb, hb) = two["a"], two["b"]
    code = user_client.post("/api/v1/link/start").json()["code"]
    assert client.post("/agent/v1/link-codes", json={"code": code, "ucid": UCID}, headers=ha).status_code == 200
    _post(client, hb, "players", {"snapshot_at": "2026-01-01T00:00:00Z", "players": [_player("red")]})  # flying on B, linked via A
    r = user_client.get(f"/api/v1/servers/{sb}/aircraft").json()
    assert r["viewer_coalition"] == "red" and [a["name"] for a in r["aircraft"]] == ["Ace"]
    assert user_client.get(f"/api/v1/servers/{sa}/aircraft").json()["hint"] == "not_online"


def test_non_foothold_server_works_without_campaign_data(client, two, user_client):
    sb, hb = two["b"]
    _post(client, hb, "server-info", {"mission_type": "generic", "agent_version": "t", "terrain": "Caucasus",
                                      "mission_name": "Training", "capabilities": {"foothold": False, "tacview": False, "grpc": False,
                                                                                    "dcsbot_rest": True, "dcsbot_db": False}})
    m = client.get(f"/api/v1/servers/{sb}/map").json()
    assert m["zones"] == [] and m["terrain"] == "Caucasus"
    assert client.get(f"/api/v1/servers/{sb}/missions").json()[0]["mission_type"] == "generic"
    ov = user_client.get(f"/api/v1/servers/{sb}/overview").json()
    assert ov["objectives"] == {"red": 0, "blue": 0, "neutral": 0} and ov["at_risk"] == 0
    assert {s["name"]: s["mission_type"] for s in client.get("/api/v1/servers").json()} == {"Server A": "foothold", "Server B": "generic"}


def test_disabled_server_disappears_everywhere(client, two, admin_client, user_client):
    sa, _ = two["a"]
    admin_client.patch(f"/api/v1/admin/servers/{sa}", json={"enabled": False})
    assert "Server A" not in [s["name"] for s in client.get("/api/v1/servers").json()]
    assert client.get(f"/api/v1/servers/{sa}/map").status_code == 404
    assert user_client.get(f"/api/v1/servers/{sa}/overview").status_code == 404


def test_agent_key_is_bound_to_its_own_server(client, two, user_client):
    (sa, _), (_sb, hb) = two["a"], two["b"]
    _post(client, hb, "events", {"events": [_kill(9)]})  # B's key can only ever write into B
    assert user_client.get(f"/api/v1/servers/{sa}/kills").json() == []


def test_farps_are_private_and_converted_from_dcs_coordinates(client, two, user_client):
    from fox3_common import geo
    sa, ha = two["a"]
    x, y = geo.latlon_to_xy("Caucasus", 43.0, 41.0)
    _post(client, ha, "server-info", {"mission_type": "foothold", "agent_version": "t", "terrain": "Caucasus", "capabilities": {
        "foothold": True, "tacview": False, "grpc": False, "dcsbot_rest": False, "dcsbot_db": False}})
    _post(client, ha, "foothold-state", {"snapshot_at": "2026-01-01T00:00:00Z", "zones": [{"name": "Z", "coalition": "red"}], "farps": [
        {"name": "From x/y", "position": {"x": x, "y": y}}, {"name": "From lat/lon", "geo": {"lat": 42.0, "lon": 40.0}}]})
    farps = {f["name"]: f for f in user_client.get(f"/api/v1/servers/{sa}/farps").json()}
    assert abs(farps["From x/y"]["lat"] - 43.0) < 1e-6 and abs(farps["From x/y"]["lon"] - 41.0) < 1e-6
    assert farps["From lat/lon"]["lat"] == 42.0
    assert client.get(f"/api/v1/servers/{sa}/farps").status_code == 401  # not part of the public map
    assert "farps" not in client.get(f"/api/v1/servers/{sa}/map").json()
