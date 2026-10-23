"""Effective agent settings: what the admin panel sends wins; the local agent.toml is only a fallback.

Secrets (DCSServerBot API key, database URL) never travel through central: they come from the local file or environment.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from ..config import LOCAL_HOSTS, AgentConfig


@dataclass(frozen=True)
class Effective:
    mission_type: str
    foothold_enabled: bool
    foothold_dir: Path | None
    tacview_enabled: bool
    tacview_dir: Path | None
    dcsbot: dict | None  # keyword arguments for DcsBotConfig.from_mapping, or None when DCSServerBot is not used
    rest_url_refused: bool = False  # central sent a REST URL whose host is neither loopback nor in allowed_rest_hosts


def _path(value: object) -> Path | None:
    return Path(str(value)) if value else None


def _host_allowed(url: object, allowed: tuple[str, ...]) -> bool:
    try:
        host = (urlparse(str(url)).hostname or "").lower()
    except ValueError:
        return False
    return bool(host) and (host in LOCAL_HOSTS or host in allowed)


def _dcsbot(local: dict | None, remote: dict | None, allowed: tuple[str, ...]) -> tuple[dict | None, bool]:
    if remote is None:  # central not reached yet: trust the local file
        return (dict(local) if local else None), False
    if not (remote.get("rest_enabled") or remote.get("db_enabled")):
        return None, False
    merged = dict(local or {})
    merged.update({"rest_enabled": bool(remote.get("rest_enabled")), "rest_prefix": remote.get("rest_prefix", ""),
                   "db_enabled": bool(remote.get("db_enabled"))})
    refused = False
    if remote.get("rest_url"):  # the REST call carries the API key: central may only aim it at trusted hosts
        if _host_allowed(remote["rest_url"], allowed):
            merged["rest_url"] = remote["rest_url"]
        else:
            refused = True
    if remote.get("server_name"):
        merged["server_name"] = remote["server_name"]
    return merged, refused


def merge(local: AgentConfig, remote: dict | None) -> Effective:
    """`remote` is the body of GET /agent/v1/config (or None before the first successful fetch)."""
    rs = (remote or {}).get("settings") or {}
    fh, tv = rs.get("foothold", {}), rs.get("tacview", {})
    dcsbot, refused = _dcsbot(local.dcsbot, rs.get("dcsbot") if remote else None, local.allowed_rest_hosts)
    return Effective(
        mission_type=(remote or {}).get("mission_type", local.mission_type),
        foothold_enabled=bool(fh.get("enabled", local.foothold.enabled)) if remote else local.foothold.enabled,
        foothold_dir=_path(fh.get("saves_dir")) or local.foothold.saves_dir,
        tacview_enabled=bool(tv.get("enabled", False)),
        tacview_dir=_path(tv.get("folder")),
        dcsbot=dcsbot,
        rest_url_refused=refused,
    )
