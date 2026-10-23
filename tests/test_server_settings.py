"""Everything the agent needs is configured in the admin panel; the agent receives it and reports its health back."""
import pytest

from fox3_agent.protocol import envelope

URL = "/api/v1/admin/servers"


def _patch(admin_client, sid, **body):
    return admin_client.patch(f"{URL}/{sid}", json=body)


def test_new_server_has_sensible_defaults(admin_client, server_id):
    s = admin_client.get(f"{URL}/{server_id}").json()
    assert s["settings"]["foothold"] == {"enabled": True, "saves_dir": None}
    assert s["settings"]["dcsbot"]["rest_url"] == "http://localhost:9876" and s["online"] is False


def test_admin_configures_folders_addresses_and_dcsbot(admin_client, server_id):
    body = {"address": "203.0.113.7:10308", "description": "Server 2",
            "settings": {"foothold": {"saves_dir": "C:/Users/x/Saved Games/DCS.s2/Missions/Saves"},
                         "tacview": {"enabled": True, "folder": "D:/Tacview"}, "missions": {"folder": "D:/Missions"},
                         "dcsbot": {"rest_enabled": True, "rest_url": "http://10.0.0.5:9876/", "server_name": "FOX3 #2"}}}
    s = _patch(admin_client, server_id, **body).json()
    assert s["address"] == "203.0.113.7:10308" and s["settings"]["missions"]["folder"] == "D:/Missions"
    assert s["settings"]["dcsbot"]["rest_url"] == "http://10.0.0.5:9876"  # normalised
    assert admin_client.get(f"{URL}/{server_id}").json()["settings"] == s["settings"]  # persisted


@pytest.mark.parametrize("settings", [
    {"tacview": {"folder": "x\x00y"}}, {"dcsbot": {"rest_url": "ftp://x"}}, {"dcsbot": {"rest_url": "http://u:p@host"}},
    {"dcsbot": {"rest_prefix": "../etc"}}, {"unknown": {}}, {"tacview": {"enabled": "maybe"}}, {"tacview": {"folder": "C" * 300}},
])
def test_invalid_settings_are_rejected(admin_client, server_id, settings):
    assert _patch(admin_client, server_id, settings=settings).status_code == 422


def test_bad_address_is_rejected(admin_client, server_id):
    assert _patch(admin_client, server_id, address="<script>").status_code == 422


def test_agent_receives_settings_and_a_revision_that_changes(client, agent_headers, admin_client, server_id):
    first = client.get("/agent/v1/config", headers=agent_headers).json()
    assert first["settings"]["tacview"]["enabled"] is False
    _patch(admin_client, server_id, settings={"tacview": {"enabled": True, "folder": "D:/tv"}})
    second = client.get("/agent/v1/config", headers=agent_headers).json()
    assert second["settings"]["tacview"]["folder"] == "D:/tv" and second["revision"] != first["revision"]
    assert client.get("/agent/v1/config", headers=agent_headers).json()["revision"] == second["revision"]  # stable when unchanged


def test_admin_sees_agent_health_and_detected_folders(client, agent_headers, admin_client, server_id):
    hb = {"agent_version": "1.2", "uptime_s": 5, "queue_depth": 3,
          "warnings": [{"code": "TACVIEW_FOLDER_MISSING", "message": "x"}],
          "detected": {"tacview": [{"path": "C:/Users/x/Documents/Tacview", "note": "4 .acmi files"}]}}
    assert client.post("/agent/v1/heartbeat", json=envelope(hb), headers=agent_headers).status_code == 200
    s = admin_client.get(f"{URL}/{server_id}").json()
    assert s["online"] is True and s["agent"]["version"] == "1.2" and s["agent"]["queue_depth"] == 3
    assert s["agent"]["warnings"][0]["code"] == "TACVIEW_FOLDER_MISSING"
    assert s["agent"]["detected"]["tacview"][0]["path"].endswith("Tacview")
    assert len(s["agents"]) == 1 and "key_hash" not in s["agents"][0]  # secrets never leave the server


def test_settings_endpoints_are_admin_only(user_client, client, server_id):
    assert user_client.get(f"{URL}/{server_id}").status_code == 403
    assert user_client.patch(f"{URL}/{server_id}", json={"name": "x"}).status_code == 403
    assert client.get(f"{URL}/{server_id}").status_code == 401
