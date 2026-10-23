"""Automatic Discord<->UCID linking from agent-reported pairs: ingest, login, conflicts, contract."""
from __future__ import annotations

import logging

import pytest
from sqlalchemy import func, select, update

from fox3_agent.protocol import PATHS, envelope
from fox3_central.db.auth_tables import discord_link_claims
from fox3_central.repositories import link_claims, players, servers, users
from fox3_central.services import auth as auth_service

UCID_A, UCID_B = "a" * 32, "b" * 32
DID_1, DID_2 = "123456789012345678", "223456789012345678"


def send(client, headers, links, status=200):
    r = client.post(f"/agent/v1{PATHS['discord_links']}", json=envelope({"links": links}), headers=headers)
    assert r.status_code == status, r.text
    return r


def make_user(app, discord_id):
    with app.state.ctx.tx() as cn:
        return users.upsert_discord(cn, discord_id, "n", None, "user")["user_id"]


def owner(app, ucid):
    with app.state.ctx.engine.connect() as cn:
        return players.link_owner(cn, ucid)


def seen(app, server_id, *ucids):
    """The server has really seen these players (stats row) - required before a claim can become a link."""
    with app.state.ctx.tx() as cn:
        for ucid in ucids:
            players.touch(cn, ucid, "p")
            players.save_stats(cn, server_id, ucid, 1, {})


def test_pairs_are_stored_and_linked_when_the_user_exists(client, app, agent_headers, server_id):
    seen(app, server_id, UCID_A, UCID_B)
    uid = make_user(app, DID_1)
    send(client, agent_headers, [{"ucid": UCID_A, "discord_id": DID_1}, {"ucid": UCID_B, "discord_id": DID_2}])
    assert owner(app, UCID_A) == uid
    assert owner(app, UCID_B) is None                      # no FOX3 user for that Discord id yet
    with app.state.ctx.engine.connect() as cn:
        assert link_claims.ucids_for_discord(cn, int(DID_2)) == [UCID_B]


def test_pairs_are_linked_at_login(app, client, agent_headers, server_id):
    seen(app, server_id, UCID_A)
    send(client, agent_headers, [{"ucid": UCID_A, "discord_id": DID_1}])
    assert owner(app, UCID_A) is None
    auth_service._open_session(app.state.ctx, DID_1, "Pilot", None)
    with app.state.ctx.engine.connect() as cn:
        uid = users.get_by_discord_id(cn, DID_1)["user_id"]
    assert owner(app, UCID_A) == uid


def test_never_steals_a_ucid_linked_to_another_user(client, app, agent_headers, caplog):
    first = make_user(app, "999999999999999999")
    with app.state.ctx.tx() as cn:
        players.touch(cn, UCID_A, "x")
        players.link(cn, UCID_A, first)
    make_user(app, DID_1)
    with caplog.at_level(logging.WARNING, logger="fox3.audit"):
        send(client, agent_headers, [{"ucid": UCID_A, "discord_id": DID_1}])
    assert owner(app, UCID_A) == first
    assert "already linked to another user" in caplog.text


def test_conflicting_claims_from_two_servers_are_not_applied(client, app, agent_headers, server_id):
    seen(app, server_id, UCID_A)
    make_user(app, DID_1)
    with app.state.ctx.tx() as cn:
        link_claims.save(cn, "other-server", UCID_A, int(DID_2))
    send(client, agent_headers, [{"ucid": UCID_A, "discord_id": DID_1}])
    assert owner(app, UCID_A) is None


def test_a_claim_for_a_ucid_the_server_never_saw_is_not_linked(client, app, agent_headers):
    make_user(app, DID_1)   # squatting attempt: nothing proves this server knows the ucid
    send(client, agent_headers, [{"ucid": UCID_A, "discord_id": DID_1}])
    assert owner(app, UCID_A) is None


def test_stale_claims_are_ignored_and_deleting_the_server_removes_them(client, app, agent_headers, server_id):
    send(client, agent_headers, [{"ucid": UCID_A, "discord_id": DID_1}])
    with app.state.ctx.tx() as cn:
        cn.execute(update(discord_link_claims).values(updated_at="2000-01-01T00:00:00Z"))
    with app.state.ctx.engine.connect() as cn:
        assert link_claims.ucids_for_discord(cn, int(DID_1)) == [] and link_claims.discord_ids_for_ucid(cn, UCID_A) == set()
    with app.state.ctx.tx() as cn:
        servers.delete_server(cn, server_id)
    with app.state.ctx.engine.connect() as cn:
        assert cn.execute(select(func.count()).select_from(discord_link_claims)).scalar() == 0


def test_link_if_absent_never_overwrites(app):
    a, b = make_user(app, DID_1), make_user(app, DID_2)
    with app.state.ctx.tx() as cn:
        players.touch(cn, UCID_A, "x")
        assert players.link_if_absent(cn, UCID_A, a) is True
        assert players.link_if_absent(cn, UCID_A, b) is False
    assert owner(app, UCID_A) == a


def test_resending_updates_the_claim(client, app, agent_headers):
    send(client, agent_headers, [{"ucid": UCID_A, "discord_id": DID_1}])
    send(client, agent_headers, [{"ucid": UCID_A, "discord_id": DID_2}])
    with app.state.ctx.engine.connect() as cn:
        assert link_claims.discord_ids_for_ucid(cn, UCID_A) == {int(DID_2)}


def test_demo_login_with_non_numeric_id_does_not_break(app):
    auth_service.demo_login(app.state.ctx, False)


@pytest.mark.parametrize("links", [
    [{"ucid": UCID_A, "discord_id": "abc"}],
    [{"ucid": UCID_A, "discord_id": "-1"}],
    [{"ucid": UCID_A, "discord_id": "1" * 21}],
    [{"ucid": "short", "discord_id": DID_1}],
    [{"ucid": UCID_A, "discord_id": DID_1, "extra": 1}],
    [{"ucid": f"{i:032d}", "discord_id": DID_1} for i in range(501)],
])
def test_invalid_payloads_are_rejected(client, agent_headers, links):
    send(client, agent_headers, links, status=422)


def test_requires_agent_authentication(client):
    r = client.post(f"/agent/v1{PATHS['discord_links']}", json=envelope({"links": []}))
    assert r.status_code == 401
