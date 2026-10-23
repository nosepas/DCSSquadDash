from __future__ import annotations

import pytest
from dcsbot_fakes import UCID1, UCID2, VALIDATORS
from sqlalchemy import create_engine, event, text
from sqlalchemy.pool import StaticPool

from fox3_agent.sources.dcsbot.db_engine import make_engine
from fox3_agent.sources.dcsbot.db_events import DbEventReader
from fox3_agent.sources.dcsbot.errors import DbError

DDL = [
    "CREATE TABLE players (ucid TEXT PRIMARY KEY, discord_id INTEGER, name TEXT, last_seen TIMESTAMP)",
    "CREATE TABLE missions (id INTEGER PRIMARY KEY, server_name TEXT NOT NULL, mission_name TEXT)",
    """CREATE TABLE missionstats (id INTEGER PRIMARY KEY, mission_id INTEGER NOT NULL, event TEXT NOT NULL, init_id TEXT,
       init_side TEXT, init_type TEXT, init_cat TEXT, target_id TEXT, target_side TEXT, target_type TEXT, target_cat TEXT,
       weapon_id INTEGER, weapon TEXT, place TEXT, comment TEXT, time TIMESTAMP NOT NULL)""",
]


@pytest.fixture
def engine():
    eng = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
    with eng.begin() as cn:
        for stmt in DDL:
            cn.execute(text(stmt))
        cn.execute(text("INSERT INTO players VALUES (:u, -1, :n, '2026-01-01 00:00:00')"), [
            {"u": UCID1, "n": "Pilot1"}, {"u": UCID2, "n": "Pilot2"}])
        cn.execute(text("INSERT INTO missions VALUES (1, 'FOX3 Test', 'm'), (2, 'Other Server', 'm')"))
    return eng


def add(eng, event_name, *, mission=1, **kw):
    cols = {"mission_id": mission, "event": event_name, "time": "2026-01-01 12:00:05.123456", **kw}
    with eng.begin() as cn:
        cn.execute(text(f"INSERT INTO missionstats ({', '.join(cols)}) VALUES ({', '.join(':' + c for c in cols)})"), cols)


def test_maps_every_supported_event_type(engine):
    add(engine, "S_EVENT_KILL", init_id=UCID1, init_side="2", init_type="FA-18C_hornet", target_id=UCID2, target_side="1",
        target_type="Su-27", weapon="AIM-120C")
    add(engine, "S_EVENT_PILOT_DEAD", init_id=UCID2, init_side="1", init_type="Su-27")
    add(engine, "S_EVENT_TAKEOFF", init_id=UCID1, init_side="2", init_type="FA-18C_hornet", place="Incirlik")
    add(engine, "S_EVENT_LAND", init_id=UCID1, init_side="2", init_type="FA-18C_hornet", place="Incirlik")
    add(engine, "S_EVENT_CRASH", init_id=UCID1, init_side="2", init_type="FA-18C_hornet")
    add(engine, "S_EVENT_EJECT", init_id=UCID1, init_side="2", init_type="FA-18C_hornet")
    reader = DbEventReader(engine, "FOX3 Test", watermark=0)
    events = reader.fetch_batch()
    assert [e["type"] for e in events] == ["kill", "death", "takeoff", "landing", "crash", "eject"]
    assert VALIDATORS.errors("events", {"events": events}) == []
    kill = events[0]
    assert kill["event_id"] == "dcsbot-1" and kill["time_utc"] == "2026-01-01T12:00:05.123Z" and kill["weapon"] == "AIM-120C"
    assert kill["actor"] == {"ucid": UCID1, "name": "Pilot1", "coalition": "blue", "unit_type": "FA-18C_hornet", "is_player": True}
    assert kill["target"]["coalition"] == "red" and kill["target"]["name"] == "Pilot2"
    assert events[2]["data"] == {"place": "Incirlik"} and "zone" not in events[2]
    assert reader.watermark == 6


def test_ai_target_and_unknown_events_ignored(engine):
    add(engine, "S_EVENT_KILL", init_id=UCID1, init_side="2", init_type="F-16C", target_side="1", target_type="T-72B")
    add(engine, "S_EVENT_SHOT", init_id=UCID1, init_side="2")
    add(engine, "S_EVENT_HIT", init_id=UCID1, init_side="2")
    events = DbEventReader(engine, "FOX3 Test", watermark=0).fetch_batch()
    assert len(events) == 1
    t = events[0]["target"]
    assert t["ucid"] is None and t["is_player"] is False and t["name"] is None and t["unit_type"] == "T-72B"
    assert VALIDATORS.errors("events", {"events": events}) == []


def test_other_server_filtered_and_watermark_advances(engine):
    add(engine, "S_EVENT_CRASH", mission=2, init_id=UCID1, init_side="2")
    add(engine, "S_EVENT_CRASH", init_id=UCID1, init_side="2")
    reader = DbEventReader(engine, "FOX3 Test", watermark=0)
    assert [e["event_id"] for e in reader.fetch_batch()] == ["dcsbot-2"]
    assert reader.fetch_batch() == []
    add(engine, "S_EVENT_LAND", init_id=UCID1, init_side="2")
    assert [e["event_id"] for e in reader.fetch_batch()] == ["dcsbot-3"]


def test_batching_orders_by_id(engine):
    for _ in range(5):
        add(engine, "S_EVENT_TAKEOFF", init_id=UCID1, init_side="2")
    reader = DbEventReader(engine, "FOX3 Test", batch_size=2, watermark=0)
    ids = [[e["event_id"] for e in reader.fetch_batch()] for _ in range(3)]
    assert ids == [["dcsbot-1", "dcsbot-2"], ["dcsbot-3", "dcsbot-4"], ["dcsbot-5"]]


def test_first_run_seeds_from_max_id_minus_n(engine):
    for _ in range(10):
        add(engine, "S_EVENT_TAKEOFF", init_id=UCID1, init_side="2")
    reader = DbEventReader(engine, "FOX3 Test", seed_back=3)
    assert reader.watermark is None
    assert [e["event_id"] for e in reader.fetch_batch()] == ["dcsbot-8", "dcsbot-9", "dcsbot-10"]


def test_seed_on_empty_db_and_explicit_watermark(engine):
    reader = DbEventReader(engine, "FOX3 Test")
    assert reader.fetch_batch() == [] and reader.watermark == 0
    add(engine, "S_EVENT_CRASH", init_id=UCID1, init_side="2")
    assert len(reader.fetch_batch()) == 1
    assert DbEventReader(engine, "FOX3 Test", watermark=1).fetch_batch() == []


def test_side_values(engine):
    for side in ("0", "3", "1", "2", None, "7"):
        add(engine, "S_EVENT_CRASH", init_id=UCID1, init_side=side)
    got = [e["actor"]["coalition"] for e in DbEventReader(engine, "FOX3 Test", watermark=0).fetch_batch()]
    assert got == ["neutral", "neutral", "red", "blue", "unknown", "unknown"]


def test_only_select_statements_are_issued(engine):
    add(engine, "S_EVENT_KILL", init_id=UCID1, init_side="2", target_id=UCID2)
    statements: list[str] = []
    event.listen(engine, "before_cursor_execute", lambda c, cur, stmt, *a: statements.append(stmt))
    reader = DbEventReader(engine, "FOX3 Test")
    reader.fetch_batch()
    reader.fetch_batch()
    reader.find_ucid("Pilot1")
    assert statements and all(s.lstrip().upper().startswith("SELECT") for s in statements)
    with engine.connect() as cn:
        assert cn.execute(text("SELECT count(*) FROM missionstats")).scalar() == 1


def test_find_ucid(engine):
    reader = DbEventReader(engine, "FOX3 Test")
    assert reader.find_ucid("Pilot2") == UCID2 and reader.find_ucid("nobody") is None


def test_db_error_wrapped_without_secrets():
    eng = create_engine("sqlite://")   # no tables
    with pytest.raises(DbError) as exc:
        DbEventReader(eng, "x", watermark=0).fetch_batch()
    assert "missionstats" not in str(exc.value)


def test_make_engine_never_leaks_url_and_works_without_driver():
    assert make_engine("sqlite://").dialect.name == "sqlite"
    with pytest.raises(DbError) as exc:
        make_engine("nosuchdialect://user:hunter2@host/db")
    assert "hunter2" not in str(exc.value)
    try:
        import psycopg  # noqa: F401
    except ImportError:
        with pytest.raises(DbError):
            make_engine("postgresql+psycopg://u:hunter2@localhost/db")
    else:
        assert make_engine("postgresql+psycopg://u:p@localhost/db").dialect.name == "postgresql"
