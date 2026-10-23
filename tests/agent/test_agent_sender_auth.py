"""401 handling, bounded rejection bookkeeping and the upload timeout of the central client."""
from __future__ import annotations

import httpx
import pytest

from fox3_agent.client import UPLOAD_TIMEOUT, CentralClient, Outcome
from fox3_agent.outbox import Outbox
from fox3_agent.runtime import Agent
from fox3_agent.runtime.source_set import StaticSources
from fox3_agent.runtime.state import AgentState
from fox3_agent.sender import MAX_REJECTED_PATHS, Sender


class ScriptedClient:
    def __init__(self, *outcomes: Outcome):
        self.outcomes, self.calls = list(outcomes), 0

    def send(self, path, body):
        self.calls += 1
        return self.outcomes.pop(0) if self.outcomes else Outcome.OK


def http_client(status: int) -> CentralClient:
    http = httpx.Client(base_url="http://c/agent/v1", transport=httpx.MockTransport(lambda r: httpx.Response(status)))
    return CentralClient("", http=http)


@pytest.mark.parametrize(("status", "outcome"), [(401, Outcome.AUTH), (429, Outcome.RETRY), (503, Outcome.RETRY),
                                                 (422, Outcome.DROP), (200, Outcome.OK)])
def test_status_to_outcome(status, outcome):
    assert http_client(status).send("/x", {}) is outcome


def test_401_keeps_the_queue_counts_and_resets_on_success(tmp_path):
    box = Outbox(tmp_path / "q.sqlite")
    for n in range(3):
        box.put("/x", {"n": n})
    sender = Sender(box, ScriptedClient(Outcome.AUTH, Outcome.AUTH, Outcome.OK))
    assert sender.drain_once() is False and sender.drain_once() is False
    assert len(box) == 3 and sender.auth_rejections == 2 and not sender.rejected  # nothing dropped
    assert sender.drain_once() is True and len(box) == 0 and sender.auth_rejections == 0


def test_heartbeat_warns_about_a_rejected_key(tmp_path):
    box = Outbox(tmp_path / "q.sqlite")
    sender = Sender(box, ScriptedClient())
    agent = Agent(provider=StaticSources([]), outbox=box, sender=sender, state=AgentState(tmp_path))
    sender.auth_rejections = 3
    agent.tick()
    heartbeat = next(b for _, p, b in box.peek() if p.endswith("heartbeat"))
    assert "CENTRAL_AUTH_FAILED" in [w["code"] for w in heartbeat["payload"]["warnings"]]


def test_drop_never_loops_and_rejected_is_bounded(tmp_path):
    box = Outbox(tmp_path / "q.sqlite")
    total = MAX_REJECTED_PATHS + 20
    for n in range(total):
        box.put(f"/p{n}", {"n": n})
    client = ScriptedClient(*[Outcome.DROP] * total)
    sender = Sender(box, client)
    while len(box):  # peek() hands out batches
        assert sender.drain_once() is True
    assert client.calls == total
    assert len(sender.rejected) == MAX_REJECTED_PATHS


def test_upload_uses_idle_timeouts_without_a_total_deadline():
    assert (UPLOAD_TIMEOUT.connect, UPLOAD_TIMEOUT.read, UPLOAD_TIMEOUT.write, UPLOAD_TIMEOUT.pool) == (10.0, 120.0, 120.0, 10.0)
    seen: dict = {}

    def handler(req: httpx.Request) -> httpx.Response:
        seen.update(req.extensions["timeout"])
        req.read()
        return httpx.Response(204)

    http = httpx.Client(base_url="http://c/agent/v1", transport=httpx.MockTransport(handler))
    CentralClient("", http=http).upload_file("r1", iter([b"abc"]), 3)
    assert seen == {"connect": 10.0, "read": 120.0, "write": 120.0, "pool": 10.0}
