"""Several agents write at the same time (SQLite is single-writer): nothing may fail with 'database is locked'.

Goes through the real HTTP path: agent authentication reads and then writes inside one transaction, which is the pattern
that fails in SQLite unless write transactions take the lock up front.
"""
import threading

from fastapi.testclient import TestClient

from fox3_agent.protocol import envelope
from fox3_central.repositories import events, servers
from fox3_central.services import agents as agent_service


def _paired_agent(app, name: str) -> tuple[str, dict]:
    ctx = app.state.ctx
    with ctx.tx() as cn:
        sid = servers.create(cn, name, "foothold")["server_id"]
    code = agent_service.create_pairing_code(ctx, sid)["pairing_code"]
    key = TestClient(app).post("/agent/v1/pair", json={"pairing_code": code}).json()["api_key"]
    return sid, {"Authorization": f"Bearer {key}"}


def test_concurrent_agents_do_not_lock_each_other_out(app):
    agents = [_paired_agent(app, f"S{i}") for i in range(3)]
    failures: list[str] = []

    def worker(n: int) -> None:
        sid, headers = agents[n % 3]
        client = TestClient(app)
        for i in range(20):
            ev = {"event_id": f"{n}-{i}", "type": "kill", "time_utc": "2026-01-01T00:00:00Z",
                  "actor": {"ucid": f"u{n}" * 8, "name": f"P{n}", "coalition": "blue"}, "target": {"name": "T", "is_player": False}}
            for path, payload in (("events", {"events": [ev]}), ("players", {"snapshot_at": "2026-01-01T00:00:00Z", "players": [
                    {"ucid": f"u{n}" * 8, "name": f"P{n}", "coalition": "blue"}]})):
                try:
                    r = client.post(f"/agent/v1/{path}", json=envelope(payload), headers=headers)
                    if r.status_code != 200:
                        failures.append(f"{path}: {r.status_code}")
                except Exception as exc:  # noqa: BLE001  (a locked database surfaces as a server exception)
                    failures.append(f"{path}: {type(exc).__name__}")

    threads = [threading.Thread(target=worker, args=(n,)) for n in range(9)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=120)
    assert failures == []
    with app.state.ctx.engine.connect() as cn:
        assert sum(len(events.list_events(cn, sid, ("kill",), 500)) for sid, _ in agents) == 9 * 20
