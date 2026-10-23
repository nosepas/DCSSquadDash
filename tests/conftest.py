from __future__ import annotations

import os
import uuid

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text

from fox3_agent.protocol import PATHS, envelope
from fox3_agent.sim.world import SimWorld
from fox3_central.app import create_app
from fox3_central.config import Settings
from fox3_central.repositories import servers
from fox3_central.services import agents as agent_service


@pytest.fixture
def db_url(tmp_path):
    """SQLite file per test; with FOX3_TEST_PG=postgresql+psycopg://user@host:port the whole suite runs on a fresh PostgreSQL database."""
    pg = os.environ.get("FOX3_TEST_PG")
    if not pg:
        yield f"sqlite:///{(tmp_path / 't.sqlite').as_posix()}"
        return
    name = "t_" + uuid.uuid4().hex[:12]
    admin = create_engine(f"{pg}/postgres", isolation_level="AUTOCOMMIT")
    with admin.connect() as cn:
        cn.execute(text(f"CREATE DATABASE {name}"))
    yield f"{pg}/{name}"
    with admin.connect() as cn:
        cn.execute(text(f"DROP DATABASE {name} WITH (FORCE)"))
    admin.dispose()


@pytest.fixture
def app(db_url):
    # elevation_url="" so that tests never touch the network
    return create_app(Settings(db_url=db_url, demo_login=True, web_dir=None, elevation_url=""))


@pytest.fixture
def client(app):
    return TestClient(app)


@pytest.fixture
def server_id(app):
    with app.state.ctx.tx() as cn:
        return servers.create(cn, "Test", "foothold")["server_id"]


@pytest.fixture
def agent_headers(client, app, server_id):
    code = agent_service.create_pairing_code(app.state.ctx, server_id)["pairing_code"]
    key = client.post("/agent/v1/pair", json={"pairing_code": code, "agent_name": "t", "agent_version": "0"}).json()["api_key"]
    return {"Authorization": f"Bearer {key}"}


@pytest.fixture
def feed(client, agent_headers):
    """Send simulated world data through the real agent API."""
    def _feed(world: SimWorld | None = None, ticks: int = 40) -> SimWorld:
        w = world or SimWorld(seed=1)
        for _ in range(ticks):
            w.tick()
        sends = [("server_info", w.server_info()), ("foothold_state", w.foothold_state()), ("players", w.players()),
                 ("events", w.drain_events())]
        for kind, payload in sends:
            if payload is not None:
                r = client.post(f"/agent/v1{PATHS[kind]}", json=envelope(payload), headers=agent_headers)
                assert r.status_code == 200, (kind, r.text)
        return w
    return _feed


@pytest.fixture
def user_client(app):
    """Logged-in normal user (demo login) with CSRF token."""
    c = TestClient(app, follow_redirects=False)
    assert c.get("/api/v1/auth/demo").status_code == 302
    c.headers["X-CSRF-Token"] = c.get("/api/v1/me").json()["csrf_token"]
    return c


@pytest.fixture
def admin_client(app):
    c = TestClient(app, follow_redirects=False)
    assert c.get("/api/v1/auth/demo?admin=true").status_code == 302
    c.headers["X-CSRF-Token"] = c.get("/api/v1/me").json()["csrf_token"]
    return c
