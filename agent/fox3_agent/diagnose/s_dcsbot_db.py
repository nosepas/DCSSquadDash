"""Section 5b: optional read-only probe of the DCSServerBot database. Schema, counts and enumerations only: no row data."""
from __future__ import annotations

from sqlalchemy import Engine, inspect, text
from sqlalchemy.exc import SQLAlchemyError

from ..sources.dcsbot.db_engine import make_engine
from ..sources.dcsbot.db_mapping import EVENT_TYPES, coalition_from_side
from ..sources.dcsbot.errors import DbError
from .context import Context
from .report import Section

TABLES = ("missionstats", "missions", "players", "statistics")   # constants: never built from external input
MAX_VALUES = 50


def _counts(engine: Engine, sql: str) -> list[tuple[str, int]]:
    with engine.connect() as cn:
        return [(str(r[0]), int(r[1])) for r in cn.execute(text(sql)).all()]


def probe(engine: Engine, sec: Section) -> None:
    insp = inspect(engine)
    found = [t for t in TABLES if insp.has_table(t)]
    sec.kv("tables found among " + "/".join(TABLES), ", ".join(found) or "(none)")
    for missing in (t for t in ("missionstats", "missions", "players") if t not in found):
        sec.flag(f"table {missing} not found (the events feed needs it)")
    with engine.connect() as cn:
        for t in found:
            sec.kv(f"rows in {t}", cn.execute(text(f"SELECT count(*) FROM {t}")).scalar())   # noqa: S608 - constant table names
    if "missionstats" not in found:
        return
    cols = [c["name"] for c in insp.get_columns("missionstats")]
    sec.kv("missionstats columns", ", ".join(cols))
    needed = {"id", "mission_id", "event", "init_id", "init_side", "init_type", "target_id", "target_side", "target_type", "weapon", "place", "time"}
    if needed - set(cols):
        sec.flag("missionstats lacks columns our reader selects: " + ", ".join(sorted(needed - set(cols))))
        return
    with engine.connect() as cn:
        sec.kv("max(id)", cn.execute(text("SELECT max(id) FROM missionstats")).scalar())
    events = _counts(engine, f"SELECT event, count(*) FROM missionstats GROUP BY event ORDER BY 2 DESC, 1 LIMIT {MAX_VALUES}")
    sec.kv("distinct event values", dict(events))
    unmapped = [e for e, _ in events if e not in EVENT_TYPES]
    sec.kv("  of which mapped by our reader", ", ".join(e for e, _ in events if e in EVENT_TYPES) or "(none)")
    sec.kv("  not mapped (ignored)", ", ".join(unmapped[:20]) or "(none)")
    if not any(e in EVENT_TYPES for e, _ in events):
        sec.flag("none of the event values is one our reader maps: the event names differ from what we expect")
    sides = _counts(engine, f"SELECT init_side, count(*) FROM missionstats GROUP BY init_side ORDER BY 2 DESC, 1 LIMIT {MAX_VALUES}")
    sec.kv("distinct init_side values", dict(sides))
    bad = [s for s, _ in sides if s != "None" and coalition_from_side(s) == "unknown"]
    if bad:
        sec.flag("init_side values our mapper reads as 'unknown': " + ", ".join(bad[:10]))


def dcsbot_db(ctx: Context, sec: Section) -> None:
    cfg = ctx.extras.get("dcsbot_cfg")
    if cfg is None or not cfg.db_enabled:
        sec.line("  database probe skipped (DCSServerBot database not enabled)")
        return
    url = cfg.resolved_db_url(ctx.environ)
    if not url:
        sec.flag(f"database URL not available: environment variable {cfg.db_url_env!r} is empty in this process")
        return
    try:
        engine = make_engine(url)
        probe(engine, sec)
        engine.dispose()
    except DbError as exc:
        sec.flag(str(exc))
    except SQLAlchemyError as exc:
        sec.flag(f"database probe failed: {type(exc).__name__}")   # SQLAlchemy messages can echo SQL and hosts: type only
