from fox3_agent.protocol import envelope
from fox3_central.repositories import agents


def test_pairing_code_is_single_use(client, app, server_id):
    from fox3_central.services import agents as svc
    code = svc.create_pairing_code(app.state.ctx, server_id)["pairing_code"]
    body = {"pairing_code": code, "agent_name": "a", "agent_version": "1"}
    assert client.post("/agent/v1/pair", json=body).status_code == 200
    assert client.post("/agent/v1/pair", json=body).status_code == 400
    assert client.post("/agent/v1/pair", json={"pairing_code": "WRONG"}).status_code == 400


def test_requires_valid_key(client):
    assert client.post("/agent/v1/heartbeat", json={}).status_code == 401
    assert client.post("/agent/v1/heartbeat", json={}, headers={"Authorization": "Bearer x.y"}).status_code == 401


def test_message_is_idempotent(client, agent_headers):
    msg = envelope({"agent_version": "1", "uptime_s": 1, "queue_depth": 0})
    assert client.post("/agent/v1/heartbeat", json=msg, headers=agent_headers).json() == {"ok": True}
    assert client.post("/agent/v1/heartbeat", json=msg, headers=agent_headers).json() == {"ok": True, "duplicate": True}


def test_invalid_payload_is_rejected_with_details(client, agent_headers):
    r = client.post("/agent/v1/players", json=envelope({"players": "nope"}), headers=agent_headers)
    assert r.status_code == 422
    assert r.json()["error"]["code"] == "invalid_payload" and r.json()["error"]["details"]


def test_revoked_key_stops_working(client, app, agent_headers):
    with app.state.ctx.tx() as cn:
        agent_id = agents.list_all(cn)[0]["agent_id"]
        assert agents.revoke(cn, agent_id)
    msg = envelope({"agent_version": "1", "uptime_s": 1, "queue_depth": 0})
    assert client.post("/agent/v1/heartbeat", json=msg, headers=agent_headers).status_code == 401


def test_events_are_deduplicated_by_event_id(client, agent_headers, user_client, server_id):
    ev = {"event_id": "e1", "type": "kill", "time_utc": "2026-01-01T00:00:00Z",
          "actor": {"ucid": "u" * 10, "name": "A", "coalition": "blue"}, "target": {"name": "T", "is_player": False}}
    for _ in range(2):
        assert client.post("/agent/v1/events", json=envelope({"events": [ev]}), headers=agent_headers).status_code == 200
    assert len(user_client.get(f"/api/v1/servers/{server_id}/kills").json()) == 1
