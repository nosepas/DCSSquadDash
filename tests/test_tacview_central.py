import pytest

from fox3_agent.protocol import envelope


def _index(path="mission1/Tacview-1.zip.acmi", ref="2026-03-01T18:00:00Z", pilots=(("Iceman", "F-14B", 120.0, 3600.5),), **file):
    f = {"relative_path": path, "size_bytes": 123456, "mtime": "2026-03-01T19:05:00Z", "reference_time": ref, "complete": True, **file}
    apps = [{"pilot": p, "aircraft": a, "coalition": "blue", "first_offset_s": s, "last_offset_s": e} for p, a, s, e in pilots]
    return envelope({"index_version": 1, "file": f, "appearances": apps})


def _post(client, headers, body):
    return client.post("/agent/v1/tacview-index", json=body, headers=headers)


def test_search_returns_server_file_aircraft_utc_and_offset(client, agent_headers, user_client):
    assert _post(client, agent_headers, _index()).status_code == 200
    hit = user_client.get("/api/v1/tacview/search?pilot=iceman").json()[0]  # case-insensitive
    assert hit["server_name"] == "Test" and hit["file"] == "mission1/Tacview-1.zip.acmi" and hit["aircraft"] == "F-14B"
    assert hit["first_utc"] == "2026-03-01T18:02:00Z" and hit["last_utc"] == "2026-03-01T19:00:00Z"  # reference_time + offset
    assert (hit["first_offset_s"], hit["last_offset_s"]) == (120.0, 3600.5)


def test_reindexing_a_file_replaces_its_appearances(client, agent_headers, user_client):
    _post(client, agent_headers, _index(pilots=(("Iceman", "F-14B", 1, 2), ("Goose", "F-14B", 3, 4))))
    _post(client, agent_headers, _index(pilots=(("Iceman", "F-14B", 5, 6),)))
    assert len(user_client.get("/api/v1/tacview/search?pilot=Iceman").json()) == 1
    assert user_client.get("/api/v1/tacview/search?pilot=Goose").json() == []


def test_search_can_be_limited_to_a_server_and_hides_disabled_ones(client, agent_headers, user_client, admin_client, server_id):
    _post(client, agent_headers, _index())
    assert user_client.get("/api/v1/tacview/search?pilot=Ice&server_id=nope").json() == []
    admin_client.patch(f"/api/v1/admin/servers/{server_id}", json={"enabled": False})
    assert user_client.get("/api/v1/tacview/search?pilot=Ice").json() == []


@pytest.mark.parametrize("path", ["/etc/passwd", "C:/Tacview/a.acmi", "../outside.acmi", "a/../../b.acmi"])
def test_unsafe_paths_are_rejected(client, agent_headers, path):
    assert _post(client, agent_headers, _index(path=path)).status_code == 422


def test_oversized_index_is_rejected(client, agent_headers):
    many = tuple((f"P{i}", "F-16C", 0, 1) for i in range(5001))
    assert _post(client, agent_headers, _index(pilots=many)).status_code == 422


def test_search_needs_login_and_a_real_term(client, user_client):
    assert client.get("/api/v1/tacview/search?pilot=abc").status_code == 401
    assert user_client.get("/api/v1/tacview/search?pilot=a").status_code == 422


def test_deleting_a_server_removes_its_index(client, agent_headers, admin_client, user_client, server_id):
    _post(client, agent_headers, _index())
    assert admin_client.delete(f"/api/v1/admin/servers/{server_id}").status_code == 204
    assert user_client.get("/api/v1/tacview/search?pilot=Iceman").json() == []
