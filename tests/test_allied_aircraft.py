from fox3_agent.protocol import envelope

BLUE, RED = "b" * 32, "r" * 32


def _players(client, headers):
    pl = [{"ucid": BLUE, "name": "Blue1", "coalition": "blue", "aircraft": "F-16C_50", "in_air": True,
           "position": {"lat": 43.0, "lon": 41.0, "alt_m": 5000}},
          {"ucid": "c" * 32, "name": "Blue2", "coalition": "blue", "aircraft": "AH-64D_BLK_II", "in_air": True,
           "position": {"lat": 43.5, "lon": 41.5}},
          {"ucid": RED, "name": "Red1", "coalition": "red", "aircraft": "Su-27", "in_air": True,
           "position": {"lat": 44.0, "lon": 39.0, "alt_m": 8000}},
          {"ucid": "d" * 32, "name": "Parked", "coalition": "blue", "aircraft": "F-14B", "in_air": False}]
    body = envelope({"snapshot_at": "2026-01-01T00:00:00Z", "players": pl})
    assert client.post("/agent/v1/players", json=body, headers=headers).status_code == 200


def _link(client, headers, user_client, ucid):
    code = user_client.post("/api/v1/link/start").json()["code"]
    assert client.post("/agent/v1/link-codes", json={"code": code, "ucid": ucid}, headers=headers).status_code == 200


def test_viewer_sees_only_their_own_coalition(client, agent_headers, user_client, server_id):
    _players(client, agent_headers)
    _link(client, agent_headers, user_client, BLUE)
    r = user_client.get(f"/api/v1/servers/{server_id}/aircraft").json()
    assert r["viewer_coalition"] == "blue" and r["hint"] is None
    assert {a["name"] for a in r["aircraft"]} == {"Blue1", "Blue2"}  # no enemy, and no aircraft without a known position
    # asking for the enemy side explicitly must not work for a normal user
    assert {a["name"] for a in user_client.get(f"/api/v1/servers/{server_id}/aircraft?coalition=red").json()["aircraft"]} == {"Blue1", "Blue2"}


def test_red_pilot_sees_red_only(client, agent_headers, user_client, server_id):
    _players(client, agent_headers)
    _link(client, agent_headers, user_client, RED)
    assert [a["name"] for a in user_client.get(f"/api/v1/servers/{server_id}/aircraft").json()["aircraft"]] == ["Red1"]


def test_unlinked_or_offline_viewer_gets_nothing_and_a_hint(client, agent_headers, user_client, server_id):
    _players(client, agent_headers)
    r = user_client.get(f"/api/v1/servers/{server_id}/aircraft").json()
    assert r["aircraft"] == [] and r["hint"] == "link_account"
    _link(client, agent_headers, user_client, "z" * 32)  # linked, but that account is not online
    assert user_client.get(f"/api/v1/servers/{server_id}/aircraft").json()["hint"] == "not_online"


def test_admin_can_pick_a_side_and_anonymous_is_refused(client, agent_headers, admin_client, server_id):
    _players(client, agent_headers)
    both = admin_client.get(f"/api/v1/servers/{server_id}/aircraft").json()["aircraft"]
    assert {a["coalition"] for a in both} == {"blue", "red"}
    red = admin_client.get(f"/api/v1/servers/{server_id}/aircraft?coalition=red").json()["aircraft"]
    assert [a["name"] for a in red] == ["Red1"]
    assert client.get(f"/api/v1/servers/{server_id}/aircraft").status_code == 401
