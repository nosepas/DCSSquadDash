"""Body limits, relay slot limits and the periodic cleanup (security review findings H1, L6, L7)."""
import asyncio

import httpx
import pytest

from fox3_agent.protocol import envelope
from fox3_central.core.bodylimit import DEFAULT_LIMIT, limit_for
from fox3_central.repositories import maintenance
from fox3_central.services.transfers import Busy, Gone, TransferAborted, TransferBroker


def test_limits_per_route():
    assert limit_for("PUT", "/agent/v1/file-requests/abc/content") is None
    assert limit_for("POST", "/api/v1/dtc/import") == 8 * 1024 * 1024
    assert limit_for("POST", "/agent/v1/pair") == DEFAULT_LIMIT and limit_for("POST", "/api/v1/admin/servers") == DEFAULT_LIMIT


def test_oversized_declared_body_is_refused_before_it_is_read(client):
    r = client.post("/agent/v1/pair", content=b"x" * (DEFAULT_LIMIT + 1), headers={"content-type": "application/json"})
    assert r.status_code == 413 and r.json()["error"]["code"] == "payload_too_large"


def test_oversized_chunked_body_is_refused_too(client):
    def chunks():
        for _ in range(8):
            yield b"x" * (DEFAULT_LIMIT // 4)  # no Content-Length: streamed in pieces

    r = client.post("/agent/v1/pair", content=chunks(), headers={"content-type": "application/json"})
    assert r.status_code == 413


def test_normal_requests_and_the_relay_route_are_not_affected(client, agent_headers):
    assert client.post("/agent/v1/heartbeat", json=envelope({"agent_version": "1", "uptime_s": 1, "queue_depth": 0}),
                       headers=agent_headers).status_code == 200
    big = client.put("/agent/v1/file-requests/nope/content", content=b"x" * (DEFAULT_LIMIT * 4), headers=agent_headers)
    assert big.status_code != 413  # exempt: the transfer broker bounds it (unknown transfer => 410)


def test_pairing_fields_are_bounded(client):
    assert client.post("/agent/v1/pair", json={"pairing_code": "A" * 500}).status_code == 422
    assert client.post("/agent/v1/pair", json={"pairing_code": "x", "agent_name": "n" * 500}).status_code == 422


def test_one_download_at_a_time_per_user():
    broker = TransferBroker()
    broker.request("s1", "a.acmi", "a.acmi", owner=7)
    with pytest.raises(Busy):
        broker.request("s1", "b.acmi", "b.acmi", owner=7)
    broker.request("s1", "c.acmi", "c.acmi", owner=8)  # another user is unaffected


def test_a_browser_that_stops_reading_frees_the_slot():
    async def scenario():
        broker = TransferBroker(idle_s=0.2)
        t = broker.request("s1", "a.acmi", "a.acmi", owner=1)
        broker.claim(t.id, "s1", size=None)
        with pytest.raises(Gone):
            for _ in range(20):  # the bounded queue fills up and nobody consumes it
                await broker.push(t, b"x")
        assert t.cancelled

    asyncio.run(scenario())


def test_an_agent_that_stops_sending_frees_the_slot():
    async def scenario():
        broker = TransferBroker(idle_s=0.2)
        t = broker.request("s1", "a.acmi", "a.acmi", owner=1)
        broker.claim(t.id, "s1", size=None)
        with pytest.raises(TransferAborted):
            async for _chunk in broker.stream(t):
                pass
        assert t.id not in broker._items  # noqa: SLF001

    asyncio.run(scenario())


def test_maintenance_removes_only_what_is_obsolete(app):
    from sqlalchemy import insert, select

    from fox3_central.core.clock import after, ago
    from fox3_central.db import auth_tables as a
    from fox3_central.db import tables as t
    with app.state.ctx.tx() as cn:
        cn.execute(insert(t.messages_seen).values(server_id="s", message_id="old", received_at=ago(days=30)))
        cn.execute(insert(t.messages_seen).values(server_id="s", message_id="new", received_at=ago(hours=1)))
        cn.execute(insert(a.sessions).values(session_hash="x", user_id=1, csrf="c", expires_at=ago(hours=1)))
        cn.execute(insert(a.sessions).values(session_hash="y", user_id=1, csrf="c", expires_at=after(hours=1)))
        removed = maintenance.purge(cn)
        left = {r[0] for r in cn.execute(select(t.messages_seen.c.message_id)).fetchall()}
    assert removed["messages_seen"] == 1 and removed["sessions"] == 1 and left == {"new"}


def test_the_server_runs_the_maintenance_loop_with_its_lifespan(app):
    from fastapi.testclient import TestClient
    with TestClient(app) as c:  # entering the context runs the lifespan (maintenance task starts and stops cleanly)
        assert c.get("/api/v1/servers").status_code == 200
    _ = httpx  # keep the import used in older pythons
