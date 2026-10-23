from fox3_agent.protocol import envelope
from fox3_central.repositories import players


def _state(zones, stats=()):
    return envelope({"snapshot_at": "2026-01-01T00:00:00Z", "zones": zones, "player_stats": list(stats)})


def test_map_uses_geo_from_the_file_without_a_projection(client, agent_headers, server_id):
    zones = [{"name": "Beirut", "coalition": "blue", "geo": {"lat": 33.82, "lon": 35.49, "alt_m": 12}}]
    assert client.post("/agent/v1/foothold-state", json=_state(zones), headers=agent_headers).status_code == 200
    m = client.get(f"/api/v1/servers/{server_id}/map").json()
    assert m["calibrated"] is True
    assert (m["zones"][0]["lat"], m["zones"][0]["lon"]) == (33.82, 35.49)


def test_map_without_any_position_is_not_calibrated(client, agent_headers, server_id):
    zones = [{"name": "Nowhere", "coalition": "red"}]
    client.post("/agent/v1/foothold-state", json=_state(zones), headers=agent_headers)
    m = client.get(f"/api/v1/servers/{server_id}/map").json()
    assert m["calibrated"] is False and m["zones"][0]["lat"] is None


def test_stats_without_ucid_are_matched_by_unique_name(client, app, agent_headers, server_id, user_client):
    with app.state.ctx.tx() as cn:
        players.touch(cn, "u" * 32, "Alice")
        players.touch(cn, "a" * 32, "Twin")
        players.touch(cn, "b" * 32, "Twin")
    stats = [{"name": "Alice", "points": 42.0}, {"name": "Twin", "points": 1.0}, {"name": "Ghost", "points": 9.0}]
    zones = [{"name": "Z", "coalition": "red"}]
    client.post("/agent/v1/foothold-state", json=_state(zones, stats), headers=agent_headers)
    ranking = user_client.get(f"/api/v1/servers/{server_id}/ranking?sort=points").json()
    assert [(r["name"], r["points"]) for r in ranking] == [("Alice", 42.0)]  # ambiguous and unknown names are not guessed
