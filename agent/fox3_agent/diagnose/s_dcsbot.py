"""Section 5a: DCSServerBot REST probe (GET /servers through our allowlisted client). Structure only: no names, no addresses."""
from __future__ import annotations

from collections import Counter
from typing import Any

import httpx

from ..runtime.settings import merge
from ..sources.dcsbot.config import DcsBotConfig
from ..sources.dcsbot.errors import ConfigError, DcsBotError, RestAuthError
from ..sources.dcsbot.rest_client import RestClient
from ..sources.dcsbot.server_mapper import select_server
from .context import Context
from .redact import safe_error
from .report import Section

FORBIDDEN_VALUES = ("password", "address")     # keys we mention only by name, never with a value
MAX_KEYS = 40


def effective_dcsbot(ctx: Context) -> dict | None:
    """The DCSServerBot options the running agent would use (admin panel values merged over the local file)."""
    if ctx.config is None:
        return None
    return merge(ctx.config, ctx.remote).dcsbot


def build_config(ctx: Context) -> DcsBotConfig | None:
    raw = effective_dcsbot(ctx)
    if not raw:
        return None
    return DcsBotConfig.from_mapping({"mission_type": ctx.config.mission_type if ctx.config else "foothold", **raw})


def _keys(items: list[dict[str, Any]]) -> list[str]:
    return sorted({str(k)[:40] for d in items for k in d})[:MAX_KEYS]


def _describe(servers: list[dict[str, Any]], sec: Section, name: str) -> None:
    sec.kv("servers returned", len(servers))
    sec.kv("top-level keys", ", ".join(_keys(servers)))
    present = [k for k in FORBIDDEN_VALUES if any(k in s for s in servers)]
    if present:
        sec.kv("sensitive keys present (values not shown)", ", ".join(present))
    missions = [s["mission"] for s in servers if isinstance(s.get("mission"), dict)]
    sec.kv("mission keys", ", ".join(_keys(missions)) or "(no mission object)")
    sec.kv("mission.theatre present", bool(missions) and all("theatre" in m for m in missions))
    weather = [s["weather"] for s in servers if isinstance(s.get("weather"), dict)]
    sec.kv("weather keys", ", ".join(_keys(weather)) or "(none)")
    players = [p for s in servers if isinstance(s.get("players"), list) for p in s["players"] if isinstance(p, dict)]
    sec.kv("players listed", len(players))
    sec.kv("player keys", ", ".join(_keys(players)) or "(none)")
    sides = Counter(repr(p.get("side"))[:30] for p in players)
    sec.kv("exact `side` values seen", dict(sides))
    if players and not sides.keys() <= {"'blue'", "'red'", "'neutral'", "'BLUE'", "'RED'", "'NEUTRAL'"}:
        sec.flag("player `side` values outside blue/red/neutral: our players mapper would give 'unknown'")
    sec.kv("server matching the configured name", select_server(servers, name) is not None)


def dcsbot_rest(ctx: Context, sec: Section) -> None:
    try:
        cfg = build_config(ctx)
    except ConfigError as exc:
        sec.flag(f"DCSServerBot configuration invalid: {safe_error(exc)}")
        return
    if cfg is None:
        sec.line("  not configured (neither locally nor in the admin panel): skipped")
        return
    sec.kv("rest_enabled / db_enabled", f"{cfg.rest_enabled} / {cfg.db_enabled}")
    ctx.extras["dcsbot_cfg"] = cfg
    if not cfg.rest_enabled:
        sec.line("  REST probe skipped (rest_enabled is false)")
        return
    key = cfg.resolved_api_key(ctx.environ)
    sec.kv("api key available to this process", "yes" if key else "NO")
    client = RestClient(cfg.rest_url, prefix=cfg.rest_prefix, api_key=key, verify=cfg.verify_tls, timeout_s=cfg.request_timeout_s,
                        max_bytes=cfg.max_response_bytes,
                        transport=ctx.extras.get("rest_transport"))
    try:
        servers = client.get_servers()
        sec.kv("GET /servers", "HTTP 200, JSON list of objects")
    except RestAuthError as exc:
        sec.flag(f"GET /servers rejected the credentials: {safe_error(exc)}")
        return
    except (DcsBotError, httpx.HTTPError) as exc:
        sec.flag(f"GET /servers failed: {safe_error(exc)}")
        return
    finally:
        client.close()
    _describe(servers, sec, cfg.server_name)
