"""Relay of Tacview recordings from a remote agent to the browser (nothing stored on central)."""
import asyncio

import httpx
import pytest

from fox3_agent.protocol import envelope
from fox3_central.api import transfers as transfers_api
from fox3_central.services.transfers import TransferAborted

PATH = "m1/Tacview 2026:03.zip.acmi"
DATA = bytes(range(256)) * 4096  # 1 MiB


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.fixture
def file_id(client, agent_headers, user_client):
    body = envelope({"index_version": 1, "file": {"relative_path": PATH, "size_bytes": len(DATA), "mtime": "2026-03-01T19:00:00Z",
                                                  "reference_time": "2026-03-01T18:00:00Z"},
                     "appearances": [{"pilot": "Iceman", "first_offset_s": 0, "last_offset_s": 9}]})
    assert client.post("/agent/v1/tacview-index", json=body, headers=agent_headers).status_code == 200
    return user_client.get("/api/v1/tacview/search?pilot=Iceman").json()[0]["file_id"]


async def _chunks(data: bytes, size: int = 64 * 1024):
    for i in range(0, len(data), size):
        yield data[i:i + size]
        await asyncio.sleep(0)


def _apps(app, agent_headers):
    transport = httpx.ASGITransport(app=app)
    user = httpx.AsyncClient(transport=transport, base_url="http://t", follow_redirects=False)
    agent = httpx.AsyncClient(transport=transport, base_url="http://t/agent/v1", headers=agent_headers)
    return user, agent


async def _login(user):
    assert (await user.get("/api/v1/auth/demo")).status_code == 302


async def _first_request(agent):
    r = await agent.get("/file-requests", params={"wait": 5})
    return r.json()[0]


@pytest.mark.anyio
async def test_file_travels_agent_to_browser_intact(app, agent_headers, file_id):
    user, agent = _apps(app, agent_headers)
    await _login(user)
    download = asyncio.create_task(user.get(f"/api/v1/tacview/files/{file_id}/download"))
    req = await _first_request(agent)
    assert req["relative_path"] == PATH
    up = await agent.put(f"/file-requests/{req['request_id']}/content", content=_chunks(DATA), headers={"X-File-Size": str(len(DATA))})
    assert up.status_code == 200 and up.json()["bytes"] == len(DATA)
    r = await download
    assert r.status_code == 200 and r.content == DATA
    assert r.headers["content-disposition"] == 'attachment; filename="Tacview_2026_03.zip.acmi"'  # sanitised name
    assert not app.state.ctx.transfers._items  # noqa: SLF001  (nothing is kept after the transfer)


@pytest.mark.anyio
async def test_truncated_upload_aborts_the_download_instead_of_truncating_silently(app, agent_headers, file_id):
    user, agent = _apps(app, agent_headers)
    await _login(user)
    download = asyncio.create_task(user.get(f"/api/v1/tacview/files/{file_id}/download"))
    req = await _first_request(agent)
    await agent.put(f"/file-requests/{req['request_id']}/content", content=_chunks(DATA[:1000]), headers={"X-File-Size": str(len(DATA))})
    with pytest.raises(TransferAborted):
        await download


@pytest.mark.anyio
async def test_agent_can_report_a_missing_file(app, agent_headers, file_id):
    user, agent = _apps(app, agent_headers)
    await _login(user)
    download = asyncio.create_task(user.get(f"/api/v1/tacview/files/{file_id}/download"))
    req = await _first_request(agent)
    assert (await agent.post(f"/file-requests/{req['request_id']}/fail", json={"reason": "file not found"})).status_code == 204
    assert (await download).status_code == 404


@pytest.mark.anyio
async def test_offline_agent_gives_a_clear_timeout(app, agent_headers, file_id, monkeypatch):
    monkeypatch.setattr(transfers_api, "START_TIMEOUT_S", 0.2)
    user, _ = _apps(app, agent_headers)
    await _login(user)
    r = await user.get(f"/api/v1/tacview/files/{file_id}/download")
    assert r.status_code == 504 and r.json()["error"]["code"] == "server_unreachable"
    assert not app.state.ctx.transfers._items  # noqa: SLF001


@pytest.mark.anyio
async def test_limits_login_and_foreign_agents(app, agent_headers, file_id, server_id):
    user, agent = _apps(app, agent_headers)
    anon = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t")
    assert (await anon.get(f"/api/v1/tacview/files/{file_id}/download")).status_code == 401
    await _login(user)
    broker = app.state.ctx.transfers
    for _ in range(broker.max_per_server):
        broker.request(server_id, PATH, "a.acmi")
    assert (await user.get(f"/api/v1/tacview/files/{file_id}/download")).status_code == 429
    # an agent of another server cannot claim these transfers
    other = httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://t/agent/v1", headers={"Authorization": "Bearer x.y"})
    assert (await other.put("/file-requests/whatever/content", content=b"x")).status_code == 401
    rid = next(iter(broker._items))  # noqa: SLF001
    assert (await agent.put(f"/file-requests/{rid}/content", content=b"x", headers={"X-File-Size": str(10**12)})).status_code == 410


@pytest.mark.anyio
async def test_downloads_are_rate_limited_per_user(app, agent_headers, file_id, monkeypatch):
    monkeypatch.setattr(transfers_api, "START_TIMEOUT_S", 0.01)
    user, _ = _apps(app, agent_headers)
    await _login(user)
    codes = [(await user.get(f"/api/v1/tacview/files/{file_id}/download")).status_code for _ in range(22)]
    assert codes[:20] == [504] * 20 and codes[20:] == [429, 429]
