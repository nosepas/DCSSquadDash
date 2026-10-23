from __future__ import annotations

import copy

import httpx
import pytest
from dcsbot_fakes import SERVER, UCID1, VALIDATORS, Clock, FakeBot
from sqlalchemy import create_engine, text
from sqlalchemy.pool import StaticPool
from test_dcsbot_db_events import DDL, add

from fox3_agent.sources.dcsbot import ConfigError, DcsBotConfig, DcsBotSource


def make(bot: FakeBot, clock: Clock, **cfg) -> DcsBotSource:
    config = DcsBotConfig.from_mapping({"rest_enabled": True, "server_name": "FOX3 Test", "api_key": "k", **cfg})
    return DcsBotSource(config, clock=clock, transport=bot.transport())


def kinds(msgs):
    return [m.kind for m in msgs]


def test_first_poll_emits_valid_info_and_players():
    src = make(FakeBot(api_key="k"), Clock())
    msgs = src.poll()
    assert kinds(msgs) == ["server_info", "players"] and src.warnings() == []
    for m in msgs:
        assert VALIDATORS.errors(m.kind, m.payload) == []
    assert src.players_by_name()["Pilot1"] == {"ucid": UCID1, "coalition": "blue", "unit_type": "FA-18C_hornet"}
    assert src.resolve_ucid("Pilot1") == UCID1


def test_refresh_intervals_and_change_detection():
    bot, clock = FakeBot(api_key="k"), Clock()
    src = make(bot, clock)
    src.poll()
    clock.advance(4)
    assert src.poll() == []                                 # nothing changed, neither refresh is due
    clock.advance(7)                                        # 11s > players_refresh_s (10)
    assert kinds(src.poll()) == ["players"]
    clock.advance(50)                                       # 61s since server_info
    assert "server_info" in kinds(src.poll())
    bot.servers[0]["players"].pop()                         # player left -> immediate players message
    clock.advance(4)
    msgs = src.poll()
    assert kinds(msgs) == ["players"] and len(msgs[0].payload["players"]) == 1


def test_rest_poll_is_rate_limited():
    bot, clock = FakeBot(api_key="k"), Clock()
    src = make(bot, clock)
    src.poll()
    n = len(bot.requests)
    clock.advance(1)
    src.poll()
    assert len(bot.requests) == n


def test_unresolved_players_warn_and_are_omitted():
    bot, clock = FakeBot(api_key="k"), Clock()
    bot.servers[0]["players"].append({"nick": "Ghost", "side": "blue"})
    src = make(bot, clock)
    msgs = src.poll()
    assert [p["name"] for p in msgs[1].payload["players"]] == ["Pilot1", "Pilot2"]
    assert [w.code for w in src.warnings()] == ["DCSBOT_UCID_UNRESOLVED"]


def test_auth_failed_warning_and_backoff():
    bot, clock = FakeBot(api_key="right"), Clock()
    src = make(bot, clock, api_key="wrong")
    assert src.poll() == [] and [w.code for w in src.warnings()] == ["DCSBOT_AUTH_FAILED"]
    assert "wrong" not in src.warnings()[0].message
    n = len(bot.requests)
    clock.advance(1.5)
    src.poll()
    assert len(bot.requests) == n                           # backing off
    clock.advance(10)
    src.poll()
    assert len(bot.requests) == n + 1


def test_unreachable_then_recovery_and_growing_backoff():
    bot, clock = FakeBot(api_key="k"), Clock()
    bot.fail_with = lambda r: (_ for _ in ()).throw(httpx.ConnectError("down", request=r))
    src = make(bot, clock)
    src.poll()
    assert [w.code for w in src.warnings()] == ["DCSBOT_UNREACHABLE"]
    delays = []
    for _ in range(3):
        before = len(bot.requests)
        step = 0
        while len(bot.requests) == before:
            clock.advance(1)
            step += 1
            src.poll()
        delays.append(step)
    assert delays[0] < delays[1] < delays[2]
    bot.fail_with = None
    clock.advance(200)
    assert kinds(src.poll()) == ["server_info", "players"] and src.warnings() == []


def test_server_not_found():
    bot, clock = FakeBot(api_key="k"), Clock()
    src = make(bot, clock, server_name="Nope")
    assert src.poll() == [] and [w.code for w in src.warnings()] == ["DCSBOT_SERVER_NOT_FOUND"]


def test_empty_server_name_uses_single_server_and_generic_type():
    src = make(FakeBot(api_key="k"), Clock(), server_name="", mission_type="generic")
    info = src.poll()[0].payload
    assert info["mission_type"] == "generic" and info["capabilities"]["foothold"] is False


def test_no_forbidden_request_ever_sent_and_password_never_in_messages():
    bot, clock = FakeBot(api_key="k"), Clock()
    src = make(bot, clock)
    msgs = src.poll()
    assert "TOPSECRET" not in repr(msgs)
    assert {(r.method, r.url.path) for r in bot.requests} <= {("GET", "/servers"), ("POST", "/getuser")}


def test_config_validation_and_secret_repr():
    cfg = DcsBotConfig.from_mapping({"rest_enabled": True, "api_key": "topsecret", "db_url": "postgresql://u:pw@h/d",
                                     "db_enabled": True})
    assert "topsecret" not in repr(cfg) and "pw" not in repr(cfg)
    for bad in ({"nope": 1}, {"rest_enabled": "yes"}, {"info_refresh_s": 0}, {"mission_type": "x"}, {"db_enabled": True},
                {"rest_enabled": True, "rest_url": "ftp://x"}, {"db_batch_size": 1000}, {"verify_tls": 3}):
        with pytest.raises(ConfigError):
            DcsBotConfig.from_mapping(bad)
    assert DcsBotConfig.from_mapping({"db_url_env": "X", "db_enabled": True}).resolved_db_url({"X": "sqlite://"}) == "sqlite://"
    assert DcsBotConfig.from_mapping({"verify_tls": False}).verify_tls is False


@pytest.fixture
def db_engine():
    eng = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    with eng.begin() as cn:
        for stmt in DDL:
            cn.execute(text(stmt))
        cn.execute(text("INSERT INTO missions VALUES (1, 'FOX3 Test', 'm')"))
    return eng


def make_db_source(engine, clock, **cfg) -> DcsBotSource:
    config = DcsBotConfig.from_mapping({"db_enabled": True, "db_url_env": "X", "server_name": "FOX3 Test", **cfg})
    return DcsBotSource(config, clock=clock, engine=engine)


def test_db_events_batches_and_watermark(db_engine):
    for _ in range(5):
        add(db_engine, "S_EVENT_TAKEOFF", init_id=None, init_side="2", init_type="F-16C")
    clock = Clock()
    src = make_db_source(db_engine, clock, db_batch_size=2, db_seed_back=100)
    msgs = src.poll()
    assert kinds(msgs) == ["events"] * 3 and [len(m.payload["events"]) for m in msgs] == [2, 2, 1]
    assert all(VALIDATORS.errors("events", m.payload) == [] for m in msgs) and src.watermark == 5
    assert src.poll() == []
    add(db_engine, "S_EVENT_CRASH", init_side="2")
    clock.advance(3)
    assert src.poll()[0].payload["events"][0]["event_id"] == "dcsbot-6"


def test_db_resumes_from_persisted_watermark(db_engine):
    for _ in range(3):
        add(db_engine, "S_EVENT_CRASH", init_side="2")
    src = DcsBotSource(DcsBotConfig.from_mapping({"db_enabled": True, "db_url_env": "X", "server_name": "FOX3 Test"}),
                       clock=Clock(), engine=db_engine, watermark=2)
    assert [e["event_id"] for e in src.poll()[0].payload["events"]] == ["dcsbot-3"]


def test_db_error_warning_backoff_and_missing_env(db_engine):
    clock = Clock()
    broken = create_engine("sqlite://")     # no tables
    src = make_db_source(broken, clock)
    assert src.poll() == [] and [w.code for w in src.warnings()] == ["DCSBOT_DB_ERROR"]
    cfg = DcsBotConfig.from_mapping({"db_enabled": True, "db_url_env": "NOT_SET_ANYWHERE", "server_name": "x"})
    src2 = DcsBotSource(cfg, clock=Clock(), environ={})
    src2.poll()
    assert [w.code for w in src2.warnings()] == ["DCSBOT_DB_ERROR"] and "NOT_SET" in src2.warnings()[0].message


def test_db_fallback_for_resolve_ucid(db_engine):
    with db_engine.begin() as cn:
        cn.execute(text("INSERT INTO players VALUES (:u, -1, 'FootholdGuy', '2026-01-01 00:00:00')"), {"u": UCID1})
    src = make_db_source(db_engine, Clock())
    assert src.resolve_ucid("FootholdGuy") is None      # reader not created yet
    src.poll()
    assert src.resolve_ucid("FootholdGuy") == UCID1


def test_both_paths_combined_and_capability(db_engine):
    add(db_engine, "S_EVENT_CRASH", init_side="2")
    bot, clock = FakeBot(servers=[copy.deepcopy(SERVER)], api_key="k"), Clock()
    config = DcsBotConfig.from_mapping({"rest_enabled": True, "api_key": "k", "db_enabled": True, "db_url_env": "X",
                                        "server_name": "FOX3 Test", "db_seed_back": 10})
    src = DcsBotSource(config, clock=clock, transport=bot.transport(), engine=db_engine)
    msgs = src.poll()
    assert kinds(msgs) == ["server_info", "players", "events"]
    assert msgs[0].payload["capabilities"]["dcsbot_db"] is True
