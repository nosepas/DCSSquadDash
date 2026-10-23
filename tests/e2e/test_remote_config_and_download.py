"""Real HTTP (uvicorn) end to end: the admin configures Tacview in the web API, a running agent picks it up without restart,
indexes the recording, and a browser downloads the file back through the relay while the file stays on the server PC."""
import os
import socket
import threading
import time

import httpx
import pytest
import uvicorn
from tacview_samples import BASIC, write_zip

from fox3_agent.client import CentralClient
from fox3_agent.config import from_mapping
from fox3_agent.credentials import Credentials, CredentialStore
from fox3_agent.outbox import Outbox
from fox3_agent.runtime import Agent
from fox3_agent.runtime.source_set import LiveSources
from fox3_agent.runtime.state import AgentState
from fox3_agent.runtime.transfers import TransferResponder
from fox3_agent.sender import Sender
from fox3_central.app import create_app
from fox3_central.config import Settings


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _wait(cond, timeout=25.0):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if (value := cond()):
            return value
        time.sleep(0.1)
    raise AssertionError("condition not met in time")


@pytest.fixture
def central(tmp_path):
    port = _free_port()
    app = create_app(Settings(db_url=f"sqlite:///{(tmp_path / 'c.sqlite').as_posix()}", demo_login=True, web_dir=None,
                              public_base_url=f"http://127.0.0.1:{port}"))
    server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
    threading.Thread(target=server.run, daemon=True).start()
    _wait(lambda: server.started)
    yield f"http://127.0.0.1:{port}", app
    server.should_exit = True


def _admin(base):
    c = httpx.Client(base_url=base + "/api/v1", follow_redirects=False)
    assert c.get("/auth/demo", params={"admin": "true"}).status_code == 302
    c.headers["X-CSRF-Token"] = c.get("/me").json()["csrf_token"]
    return c


def test_admin_config_reaches_a_running_agent_and_the_file_comes_back(central, tmp_path):
    base, _ = central
    admin = _admin(base)
    sid = admin.post("/admin/servers", json={"name": "Remote PC"}).json()["server_id"]
    code = admin.post(f"/admin/servers/{sid}/pairing-code").json()["pairing_code"]

    # the "remote PC": a recordings folder that only the agent can see, and an agent with a minimal local config
    folder = tmp_path / "pc" / "Tacview"
    original = write_zip(folder / "mission1" / "Tacview-20240501.zip.acmi", BASIC)
    os.utime(original, (time.time() - 3600, time.time() - 3600))  # finished long ago (not still being written)
    creds = httpx.post(f"{base}/agent/v1/pair", json={"pairing_code": code}).json()
    state_dir = tmp_path / "pc" / "state"
    CredentialStore(state_dir, "FOX3_E2E_UNUSED").save(Credentials(creds["agent_id"], creds["api_key"], creds["server_id"]))
    cfg = from_mapping({"central": {"url": base}, "paths": {"state_dir": str(state_dir)}, "sources": {"foothold": {"enabled": False}}})
    client = CentralClient(base, creds["api_key"])
    live = LiveSources(cfg, AgentState(state_dir))
    outbox = Outbox(state_dir / "q.sqlite")
    agent = Agent(provider=live, outbox=outbox, sender=Sender(outbox, client), state=AgentState(state_dir), tick_s=0.2,
                  heartbeat_s=0.5, config_fetch=client.get_config, config_refresh_s=0.3,
                  detect=lambda: {"tacview": [{"path": str(folder), "note": "1 .acmi files"}]},
                  responder=TransferResponder(client, lambda: live.tacview_folder, wait_s=2))
    threading.Thread(target=agent.run, daemon=True).start()
    try:
        # nothing configured yet: the admin sees the agent online and the folder it detected as a suggestion
        detail = _wait(lambda: (d := admin.get(f"/admin/servers/{sid}").json())["online"] and d["agent"]["detected"] and d)
        assert detail["agent"]["detected"]["tacview"][0]["path"] == str(folder)
        assert detail["settings"]["tacview"]["enabled"] is False

        # the admin applies the suggestion in the panel; the agent follows without a restart
        assert admin.patch(f"/admin/servers/{sid}", json={"settings": {"tacview": {"enabled": True, "folder": str(folder)}}}).status_code == 200
        hit = _wait(lambda: (h := admin.get("/tacview/search", params={"pilot": "viper"}).json()) and h[0])
        assert hit["file"] == "mission1/Tacview-20240501.zip.acmi" and hit["first_utc"] == "2024-05-01T18:00:00Z"

        # a browser downloads it; the bytes travel agent -> central -> browser and match the original
        got = admin.get(f"/tacview/files/{hit['file_id']}/download", timeout=30)
        assert got.status_code == 200 and got.content == original.read_bytes()
        assert [p for p in (tmp_path / "c.sqlite").parent.iterdir() if p.suffix == ".acmi"] == []  # nothing stored on central
    finally:
        agent.stop()
