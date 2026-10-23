"""Public = servers, map, missions only. Everything else needs login; admin routes need the admin role."""
import pytest

PRIVATE_GET = ["/servers/{sid}/overview", "/servers/{sid}/objectives", "/servers/{sid}/ranking", "/servers/{sid}/kills",
               "/servers/{sid}/players/online", "/servers/{sid}/stream", "/players?q=ab", "/players/{ucid}", "/me",
               "/admin/servers", "/admin/agents", "/admin/users"]


def test_public_endpoints_open(client, server_id, feed):
    feed()
    assert client.get("/api/v1/servers").status_code == 200
    m = client.get(f"/api/v1/servers/{server_id}/map")
    assert m.status_code == 200 and m.json()["calibrated"] and all(z["lat"] for z in m.json()["zones"])
    assert client.get(f"/api/v1/servers/{server_id}/missions").json()[0]["mission_type"] == "foothold"


def test_public_servers_expose_no_internal_fields(client, server_id):
    row = client.get("/api/v1/servers").json()[0]
    assert set(row) == {"server_id", "name", "mission_type", "terrain", "online"}


@pytest.mark.parametrize("path", PRIVATE_GET)
def test_private_endpoints_need_login(client, server_id, path):
    assert client.get("/api/v1" + path.format(sid=server_id, ucid="x" * 10)).status_code == 401


def test_user_cannot_use_admin_routes(user_client):
    for p in ("/admin/servers", "/admin/agents", "/admin/users"):
        assert user_client.get("/api/v1" + p).status_code == 403


def test_admin_can_manage_servers(admin_client):
    r = admin_client.post("/api/v1/admin/servers", json={"name": "S2", "mission_type": "generic"})
    assert r.status_code == 201
    sid = r.json()["server_id"]
    patched = admin_client.patch(f"/api/v1/admin/servers/{sid}", json={"settings": {"tacview": {"enabled": True, "folder": "D:/tv"}}})
    assert patched.json()["settings"]["tacview"]["folder"] == "D:/tv"
    code = admin_client.post(f"/api/v1/admin/servers/{sid}/pairing-code").json()
    assert len(code["pairing_code"]) == 10


def test_state_change_requires_csrf(admin_client):
    admin_client.headers.pop("X-CSRF-Token")
    assert admin_client.post("/api/v1/admin/servers", json={"name": "x"}).status_code == 403


def test_logout_invalidates_session(user_client):
    assert user_client.post("/api/v1/auth/logout").status_code == 204
    assert user_client.get("/api/v1/me").status_code == 401


def test_demo_login_disabled_outside_demo(tmp_path):
    from fastapi.testclient import TestClient

    from fox3_central.app import create_app
    from fox3_central.config import Settings
    app = create_app(Settings(db_url=f"sqlite:///{(tmp_path / 'p.sqlite').as_posix()}", demo_login=False, web_dir=None))
    assert TestClient(app, follow_redirects=False).get("/api/v1/auth/demo").status_code == 404
