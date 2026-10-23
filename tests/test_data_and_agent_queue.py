from fox3_agent.client import Outcome
from fox3_agent.outbox import Outbox
from fox3_agent.sender import Sender


def test_overview_ranking_and_profile(user_client, server_id, feed):
    w = feed(ticks=80)
    o = user_client.get(f"/api/v1/servers/{server_id}/overview").json()
    assert o["online"] == len(w.online)
    assert sum(o["objectives"].values()) == len(w.zones)
    rank = user_client.get(f"/api/v1/servers/{server_id}/ranking?sort=kills").json()
    kills = [r["kills"] for r in rank]
    assert rank and kills == sorted(kills, reverse=True)
    ucid = rank[0]["ucid"]
    prof = user_client.get(f"/api/v1/players/{ucid}").json()
    assert prof["ucid"] == ucid and prof["servers"][0]["kills"] == rank[0]["kills"]
    assert user_client.get(f"/api/v1/players?q={rank[0]['name'][:3]}").json()
    assert user_client.get("/api/v1/players/doesnotexist1").status_code == 404


def test_discord_ucid_link_flow(user_client, client, agent_headers, feed):
    feed()
    code = user_client.post("/api/v1/link/start").json()["code"]
    ucid = "a1f3c9d0b2e44d7f9c1a000000000001"
    r = client.post("/agent/v1/link-codes", json={"code": code, "ucid": ucid}, headers=agent_headers)
    assert r.status_code == 200
    assert ucid in user_client.get("/api/v1/me").json()["linked_ucids"]
    assert client.post("/agent/v1/link-codes", json={"code": code, "ucid": ucid}, headers=agent_headers).status_code == 404


class FlakyClient:
    def __init__(self, outcomes):
        self.outcomes, self.sent = list(outcomes), []

    def send(self, path, body):
        out = self.outcomes.pop(0) if self.outcomes else Outcome.OK
        if out is not Outcome.RETRY:
            self.sent.append(body["n"])
        return out


def test_outbox_survives_outage_and_keeps_order(tmp_path):
    box = Outbox(tmp_path / "q.sqlite")
    for n in range(4):
        box.put("/x", {"n": n})
    client = FlakyClient([Outcome.OK, Outcome.RETRY])
    sender = Sender(box, client)
    assert sender.drain_once() is False and len(box) == 3      # outage: message 1 stays queued
    assert Outbox(tmp_path / "q.sqlite").peek()[0][2]["n"] == 1  # survives a restart
    assert sender.drain_once() is True and len(box) == 0
    assert client.sent == [0, 1, 2, 3]


def test_outbox_rejected_message_is_dropped(tmp_path):
    box = Outbox(tmp_path / "q.sqlite")
    box.put("/x", {"n": 0})
    box.put("/x", {"n": 1})
    assert Sender(box, FlakyClient([Outcome.DROP, Outcome.OK])).drain_once() and len(box) == 0


def test_outbox_is_bounded(tmp_path):
    box = Outbox(tmp_path / "q.sqlite", max_messages=5)
    for n in range(20):
        box.put("/x", {"n": n})
    assert len(box) <= 6
