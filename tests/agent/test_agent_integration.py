"""End to end: synthetic Foothold file + fake DCSServerBot REST -> real Agent -> real central API."""
import pytest
from dcsbot_fakes import UCID1, FakeBot
from fastapi.testclient import TestClient
from foothold_samples import full_file, write_saves

from fox3_agent.client import CentralClient
from fox3_agent.outbox import Outbox
from fox3_agent.runtime import Agent
from fox3_agent.runtime.source_set import StaticSources
from fox3_agent.runtime.state import AgentState
from fox3_agent.sender import Sender
from fox3_agent.sources.dcsbot import DcsBotConfig, DcsBotSource
from fox3_agent.sources.foothold import FootholdSource
from fox3_central.repositories import servers
from fox3_central.services import agents as agent_service

PLAYERS = ("zonePersistance['players'] = { [1]={ ['coalition']='blue',['unitType']='FA-18C_hornet',['playerName']='Pilot1',"
           "['latitude']=43.0,['longitude']=41.0,['altitude']=3000 } }\n")
STATS = "zonePersistance['playerStats'] = { ['Pilot1']={ ['Points']=100,['Deaths']=1 } }\n"


@pytest.fixture
def rig(app, server_id, tmp_path):
    code = agent_service.create_pairing_code(app.state.ctx, server_id)["pairing_code"]
    key = TestClient(app).post("/agent/v1/pair", json={"pairing_code": code}).json()["api_key"]
    http = TestClient(app, base_url="http://testserver/agent/v1", headers={"Authorization": f"Bearer {key}"})
    saves = write_saves(tmp_path, full_file(STATS, PLAYERS)).parent
    bot = FakeBot(api_key="k")
    dcsbot = DcsBotSource(DcsBotConfig.from_mapping({"rest_enabled": True, "api_key": "k", "server_name": "FOX3 Test"}),
                          transport=bot.transport())
    foothold = FootholdSource(saves)
    outbox = Outbox(tmp_path / "q.sqlite")
    sender = Sender(outbox, CentralClient("", http=http))
    agent = Agent(provider=StaticSources([foothold, dcsbot], foothold, dcsbot), outbox=outbox, sender=sender, state=AgentState(tmp_path))
    return agent, sender, bot


def test_agent_feeds_central_end_to_end(rig, user_client, admin_client, client, server_id):
    agent, sender, _ = rig
    agent.tick()
    assert sender.drain_once() is True

    zones = {z["name"]: z for z in client.get(f"/api/v1/servers/{server_id}/map").json()["zones"]}
    assert zones["Alpha"]["lat"] == 43.118 and zones["Alpha"]["coalition"] == "blue"
    assert zones["Charlie"]["lat"] is None  # its invalid coordinates were dropped by the parser, not guessed
    assert client.get("/api/v1/servers").json()[0]["online"] is True

    online = admin_client.get(f"/api/v1/servers/{server_id}/players/online").json()  # positions are admin-only
    by_name = {p["name"]: p for p in online}
    assert set(by_name) == {"Pilot1", "Pilot2"}
    assert by_name["Pilot1"]["position"] == {"lat": 43.0, "lon": 41.0, "alt_m": 3000}  # Foothold position joined to the UCID
    assert by_name["Pilot2"]["position"] is None  # no Foothold entry for this one: nothing is invented

    ranking = user_client.get(f"/api/v1/servers/{server_id}/ranking?sort=points").json()
    assert (ranking[0]["ucid"], ranking[0]["points"]) == (UCID1, 100)  # name-keyed stats resolved to a UCID by the agent


def test_dcsbot_credentials_failure_is_reported_in_heartbeat(rig, app, server_id):
    agent, sender, bot = rig
    bot.api_key = "something-else"
    agent.tick()
    sender.drain_once()
    with app.state.ctx.engine.connect() as cn:
        warnings = servers.get_status(cn, server_id)["heartbeat"]["warnings"]
    assert "DCSBOT_AUTH_FAILED" in [w["code"] for w in warnings]


def test_rejected_messages_are_surfaced_in_the_heartbeat(rig, app, server_id):
    agent, sender, _ = rig
    sender.rejected["/foothold-state"] = 2  # as if central had answered 422 twice (e.g. contract version mismatch)
    agent.tick()
    sender.drain_once()
    with app.state.ctx.engine.connect() as cn:
        warnings = servers.get_status(cn, server_id)["heartbeat"]["warnings"]
    assert any(w["code"] == "CENTRAL_REJECTED_MESSAGES" and "/foothold-state x2" in w["message"] for w in warnings)


def test_a_crashing_source_does_not_stop_the_agent(rig, app, server_id):
    agent, sender, _ = rig

    class Boom:
        name = "boom"

        def poll(self):
            raise RuntimeError("bug")

        def warnings(self):
            return []

    agent._p.sources.append(Boom())  # noqa: SLF001
    agent.tick()
    sender.drain_once()
    with app.state.ctx.engine.connect() as cn:
        codes = [w["code"] for w in servers.get_status(cn, server_id)["heartbeat"]["warnings"]]
    assert "SOURCE_CRASHED" in codes
