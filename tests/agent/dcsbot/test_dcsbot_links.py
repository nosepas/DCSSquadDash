"""Verified Discord<->UCID pairs: DB reader (fake DB), change detection and the contract."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from dcsbot_fakes import UCID1, UCID2, VALIDATORS
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool

from fox3_agent.sources.dcsbot.config import DcsBotConfig
from fox3_agent.sources.dcsbot.db_feed import DbFeed
from fox3_agent.sources.dcsbot.db_links import DiscordLinkReader
from fox3_agent.sources.dcsbot.db_mapping import map_link_row
from fox3_agent.sources.dcsbot.errors import DbError
from fox3_agent.sources.dcsbot.links_sync import BATCH, LinkSync

SNOW1, SNOW2 = "123456789012345678", "223456789012345678"

DDL = [
    "CREATE TABLE players (ucid TEXT PRIMARY KEY, discord_id INTEGER, name TEXT, last_seen TIMESTAMP)",
    "CREATE TABLE missions (id INTEGER PRIMARY KEY, server_name TEXT)",
    """CREATE TABLE missionstats (id INTEGER PRIMARY KEY, mission_id INTEGER, event TEXT, init_id TEXT, init_side TEXT,
       init_type TEXT, target_id TEXT, target_side TEXT, target_type TEXT, weapon TEXT, place TEXT, time TIMESTAMP)""",
]


@pytest.fixture
def engine():
    eng = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    with eng.begin() as cn:
        for stmt in DDL:
            cn.execute(text(stmt))
        cn.execute(text("INSERT INTO players (ucid, discord_id) VALUES (:u, :d)"), [
            {"u": UCID1, "d": int(SNOW1)}, {"u": UCID2, "d": -1}, {"u": "shortid", "d": int(SNOW2)}, {"u": "x" * 20, "d": 5}])
    return eng


def test_reader_returns_only_valid_linked_pairs(engine):
    assert DiscordLinkReader(engine).read_all() == {UCID1: SNOW1}


def test_reader_reports_a_missing_table_as_dberror():
    with pytest.raises(DbError):
        DiscordLinkReader(create_engine("sqlite://")).read_all()


@pytest.mark.parametrize("ucid,did", [(UCID1, -1), (UCID1, 0), (UCID1, "abc"), (UCID1, True), (UCID1, 2**63), (None, SNOW1), ("short", SNOW1)])
def test_map_link_row_rejects_invalid_rows(ucid, did):
    assert map_link_row(ucid, did) is None


def test_sync_sends_changes_then_full_resync():
    sync = LinkSync(poll_s=10, resync_s=100)
    cur = {UCID1: SNOW1}
    assert len(sync.messages(cur, 0)) == 1          # first read: everything
    assert sync.messages(cur, 10) == []             # nothing changed
    cur = {UCID1: SNOW1, UCID2: SNOW2}
    (msg,) = sync.messages(cur, 20)
    assert msg.payload["links"] == [{"ucid": UCID2, "discord_id": SNOW2}]
    assert VALIDATORS.errors("discord_links", msg.payload) == []
    assert len(sync.messages(cur, 101)[0].payload["links"]) == 2   # resync


def test_sync_batches_within_the_contract_limit():
    sync = LinkSync(1, 100)
    cur = {f"{i:032d}": SNOW1 for i in range(BATCH + 1)}
    assert [len(m.payload["links"]) for m in sync.messages(cur, 0)] == [BATCH, 1]


def test_feed_emits_discord_links_once_and_keeps_events_independent(engine):
    now = [datetime(2026, 1, 1, tzinfo=UTC)]
    feed = DbFeed(DcsBotConfig(db_enabled=True, db_url="sqlite://", server_name="S"), lambda: now[0], engine, watermark=0)
    assert [m.kind for m in feed.poll()] == ["discord_links"]
    now[0] += timedelta(seconds=3)
    assert feed.poll() == []   # unchanged and not due
