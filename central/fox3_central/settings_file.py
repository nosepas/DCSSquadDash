"""Central configuration from a TOML file (contracts/config/central.example.toml). Strict: unknown keys are errors.

Secrets never live in the file: the Discord client secret and the database URL are read from environment variables
whose NAMES are given in the file.
"""
from __future__ import annotations

import os
import tomllib
from pathlib import Path
from urllib.parse import urlparse

from .config import Settings

ALLOWED = {
    "server": {"bind", "port", "public_base_url"},
    "database": {"url_env", "url"},
    "discord": {"client_id", "client_secret_env", "admin_ids"},
    "security": {"session_ttl_hours", "max_raw_bytes"},
    "elevation": {"url"},
    "paths": {"web_dir", "agent_dir"},
}


class SettingsError(ValueError):
    pass


def _section(raw: dict, name: str) -> dict:
    sec = raw.get(name, {})
    unknown = set(sec) - ALLOWED[name]
    if unknown:
        raise SettingsError(f"[{name}] has unknown key(s): {', '.join(sorted(unknown))}")
    return sec


def _env(name: str | None, what: str, required: bool = False) -> str:
    value = os.environ.get(name, "") if name else ""
    if required and not value:
        raise SettingsError(f"environment variable {name or '(not configured)'} must hold the {what}")
    return value


def from_mapping(raw: dict) -> tuple[Settings, dict]:
    """Returns (settings, listen) where listen = {'bind': ..., 'port': ...}."""
    unknown = set(raw) - set(ALLOWED)
    if unknown:
        raise SettingsError(f"unknown section(s): {', '.join(sorted(unknown))}")
    srv, db, dc, sec, el, paths = (_section(raw, n) for n in ALLOWED)
    base = str(srv.get("public_base_url", "")).rstrip("/")
    parsed = urlparse(base)
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise SettingsError("[server] public_base_url must be a full URL such as https://fox3.example.org")
    if parsed.scheme == "http" and parsed.hostname not in ("localhost", "127.0.0.1"):
        raise SettingsError("[server] public_base_url must be https (Discord login and agent keys need it); http only for localhost")
    db_url = _env(db.get("url_env"), "database URL", required=True) if db.get("url_env") else str(db.get("url", ""))
    if not db_url:
        raise SettingsError("[database] set url_env (preferred) or url")
    secret = _env(dc.get("client_secret_env"), "Discord client secret") if dc.get("client_id") else ""
    if dc.get("client_id") and not secret:
        raise SettingsError(f"Discord is configured but environment variable {dc.get('client_secret_env')} is empty")
    kw: dict = {"db_url": db_url, "public_base_url": base, "demo_login": False, "discord_client_id": str(dc.get("client_id", "")),
                "discord_client_secret": secret, "admin_ids": [str(i) for i in dc.get("admin_ids", [])]}
    for key in ("session_ttl_hours", "max_raw_bytes"):
        if key in sec:
            kw[key] = int(sec[key])
    if "url" in el:
        kw["elevation_url"] = str(el["url"])
    for key in ("web_dir", "agent_dir"):
        if key in paths:
            if not isinstance(paths[key], str) or not paths[key].strip():
                raise SettingsError(f"[paths] {key} must be a non-empty folder path")
            kw[key] = Path(paths[key])
    return Settings(**kw), {"bind": str(srv.get("bind", "127.0.0.1")), "port": int(srv.get("port", 8000))}


def load(path: Path) -> tuple[Settings, dict]:
    try:
        raw = tomllib.loads(path.read_text("utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        raise SettingsError(f"cannot read {path}: {exc}") from exc
    return from_mapping(raw)
