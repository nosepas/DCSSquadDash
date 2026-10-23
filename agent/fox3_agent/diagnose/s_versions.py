"""Section 1: versions, configuration summary and pairing status (never prints keys)."""
from __future__ import annotations

import platform
import sys
from urllib.parse import urlparse

import httpx

from .. import __version__
from ..credentials import CredentialStore
from ..runtime.builder import NotPairedError, central_client
from .context import Context
from .redact import safe_error
from .report import Section


def versions(ctx: Context, sec: Section) -> None:
    sec.kv("fox3-agent", __version__)
    sec.kv("python", platform.python_version() + f" ({platform.python_implementation()})")
    sec.kv("os", f"{platform.system()} {platform.release()} {platform.version()} {platform.machine()}")
    sec.kv("frozen/venv", "venv" if sys.prefix != getattr(sys, "base_prefix", sys.prefix) else "system python")


def config_summary(ctx: Context, sec: Section) -> None:
    cfg = ctx.config
    if cfg is None:
        sec.flag(f"config not loaded: {ctx.config_error}")
        return
    u = urlparse(cfg.central.url)
    sec.kv("central host", f"{u.scheme}://{u.hostname}" + (f":{u.port}" if u.port else ""))
    sec.kv("verify_tls", "custom CA" if cfg.central.ca_file else cfg.central.verify_tls)
    sec.kv("mission_type", cfg.mission_type)
    sec.kv("foothold", f"enabled={cfg.foothold.enabled}, local saves_dir set={cfg.foothold.saves_dir is not None}")
    sec.kv("tacview.cloud_files", cfg.tacview.cloud_files)
    bot = cfg.dcsbot
    if not bot:
        sec.kv("dcsserverbot (local file)", "not configured")
        return
    sec.kv("dcsserverbot (local file)", "configured")
    key_env, db_env = bot.get("api_key_env"), bot.get("db_url_env")
    sec.kv("  api key source", f"environment variable {key_env} ({'set' if ctx.environ.get(key_env) else 'EMPTY'})" if key_env
           else ("inline api_key in agent.toml (move it to api_key_env)" if bot.get("api_key") else "none"))
    sec.kv("  db url source", f"environment variable {db_env} ({'set' if ctx.environ.get(db_env) else 'EMPTY'})" if db_env else "none")


def pairing(ctx: Context, sec: Section) -> None:
    cfg = ctx.config
    if cfg is None:
        return
    try:
        creds = CredentialStore(cfg.state_dir, cfg.central.api_key_env).load()
    except Exception as exc:  # noqa: BLE001 - DPAPI/JSON problems are exactly what we want to see
        sec.flag(f"credentials unreadable: {safe_error(exc)}")
        return
    sec.kv("paired", "yes" if creds else "no")
    if creds is None:
        return
    try:
        ctx.remote = central_client(cfg).get_config()
        sec.kv("central reachable and key accepted", "yes")
    except NotPairedError:
        sec.kv("central reachable and key accepted", "not paired")
    except httpx.HTTPStatusError as exc:
        sec.flag(f"central answered HTTP {exc.response.status_code}")
    except httpx.HTTPError as exc:
        sec.flag(f"central not reachable: {type(exc).__name__}")
