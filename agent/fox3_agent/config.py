"""Agent configuration (TOML). Validated on load; secrets are never read from this file."""
from __future__ import annotations

import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from urllib.parse import urlparse

from .sources.tacview.cloud import CLOUD_CHOICES

LOCAL_HOSTS = {"localhost", "127.0.0.1", "::1"}


class ConfigError(ValueError):
    pass


@dataclass(frozen=True)
class CentralConfig:
    url: str
    verify_tls: bool = True
    ca_file: str | None = None
    api_key_env: str = "FOX3_AGENT_KEY"


@dataclass(frozen=True)
class Intervals:
    tick_s: float = 2.0
    heartbeat_s: float = 30.0
    server_info_s: float = 60.0


@dataclass(frozen=True)
class FootholdConfig:
    enabled: bool = True
    saves_dir: Path | None = None
    stale_after_s: int = 900


@dataclass(frozen=True)
class TacviewLocalConfig:
    """Local-only Tacview options (the folder itself is managed from the admin panel)."""
    cloud_files: str = "read"   # "read": also index online-only cloud files (downloads them) | "skip": ignore them


@dataclass(frozen=True)
class QueueConfig:
    """Bounds of the persistent outbox (oldest low-value messages are dropped beyond them)."""
    max_messages: int = 50_000
    max_mb: int = 200

    @property
    def max_bytes(self) -> int:
        return self.max_mb * 1024 * 1024


@dataclass(frozen=True)
class AgentConfig:
    central: CentralConfig
    state_dir: Path
    mission_type: str = "foothold"
    foothold: FootholdConfig = field(default_factory=FootholdConfig)
    dcsbot: dict | None = None  # raw mapping, validated by DcsBotConfig.from_mapping
    intervals: Intervals = field(default_factory=Intervals)
    tacview: TacviewLocalConfig = field(default_factory=TacviewLocalConfig)
    queue: QueueConfig = field(default_factory=QueueConfig)
    allowed_rest_hosts: tuple[str, ...] = ()  # non-loopback hosts that central may point the DCSServerBot REST URL at

    @property
    def queue_path(self) -> Path:
        return self.state_dir / "queue.sqlite"


def _central(raw: dict) -> CentralConfig:
    url = str(raw.get("url", "")).rstrip("/")
    try:
        parsed = urlparse(url)
    except ValueError as exc:
        raise ConfigError("central.url is not a valid URL") from exc
    if parsed.scheme not in ("http", "https") or not parsed.hostname:
        raise ConfigError("central.url must be a full http(s) URL")
    if parsed.scheme == "http" and parsed.hostname not in LOCAL_HOSTS and not raw.get("allow_insecure_http", False):
        raise ConfigError("central.url must use https (plain http is only allowed for localhost)")
    return CentralConfig(url=url, verify_tls=bool(raw.get("verify_tls", True)), ca_file=raw.get("ca_file"),
                         api_key_env=str(raw.get("api_key_env", "FOX3_AGENT_KEY")))


def _path(value: object) -> Path | None:
    return Path(str(value)) if value else None


def _tacview(raw: object) -> TacviewLocalConfig:
    if not isinstance(raw, dict):
        raise ConfigError("[sources.tacview] must be a table")
    unknown = sorted(set(raw) - {"cloud_files"})
    if unknown:
        raise ConfigError(f"unknown [sources.tacview] option(s): {', '.join(unknown)} (the folder is set in the admin panel)")
    mode = raw.get("cloud_files", "read")
    if mode not in CLOUD_CHOICES:
        raise ConfigError("sources.tacview.cloud_files must be 'read' or 'skip'")
    return TacviewLocalConfig(cloud_files=mode)


def _queue(raw: object) -> QueueConfig:
    if not isinstance(raw, dict):
        raise ConfigError("[queue] must be a table")
    unknown = sorted(set(raw) - {"max_messages", "max_mb"})
    if unknown:
        raise ConfigError(f"unknown [queue] option(s): {', '.join(unknown)}")
    values = {}
    for key, default, low, high in (("max_messages", 50_000, 100, 10_000_000), ("max_mb", 200, 1, 100_000)):
        v = raw.get(key, default)
        if isinstance(v, bool) or not isinstance(v, int) or not low <= v <= high:
            raise ConfigError(f"queue.{key} must be a whole number between {low} and {high}")
        values[key] = v
    return QueueConfig(**values)


def _allowed_hosts(raw: object) -> tuple[str, ...]:
    if not isinstance(raw, list) or not all(isinstance(h, str) and h.strip() for h in raw):
        raise ConfigError("sources.dcsserverbot.allowed_rest_hosts must be a list of host names")
    return tuple(h.strip().lower() for h in raw)


def from_mapping(raw: dict, base_dir: Path | None = None) -> AgentConfig:
    if "central" not in raw:
        raise ConfigError("missing [central] section")
    mission_type = raw.get("mission_type", "foothold")
    if mission_type not in ("foothold", "generic"):
        raise ConfigError("mission_type must be 'foothold' or 'generic'")
    paths, sources = raw.get("paths", {}), raw.get("sources", {})
    state_dir = _path(paths.get("state_dir")) or (base_dir or Path.cwd()) / "state"
    fh = sources.get("foothold", {})
    foothold = FootholdConfig(enabled=bool(fh.get("enabled", mission_type == "foothold")),
                              saves_dir=_path(fh.get("saves_dir") or paths.get("foothold_saves")),
                              stale_after_s=int(fh.get("stale_after_s", 900)))
    iv = raw.get("intervals", {})
    intervals = Intervals(**{k: float(v) for k, v in iv.items() if k in Intervals.__dataclass_fields__})
    dcsbot = dict(sources.get("dcsserverbot") or {})
    allowed = _allowed_hosts(dcsbot.pop("allowed_rest_hosts", []))
    return AgentConfig(central=_central(raw["central"]), state_dir=state_dir, mission_type=mission_type,
                       foothold=foothold, dcsbot=dcsbot or None, intervals=intervals,
                       tacview=_tacview(sources.get("tacview", {})), queue=_queue(raw.get("queue", {})), allowed_rest_hosts=allowed)


def load_config(path: Path) -> AgentConfig:
    try:
        raw = tomllib.loads(path.read_text("utf-8-sig"))
    except (OSError, tomllib.TOMLDecodeError) as e:
        raise ConfigError(f"cannot read {path}: {e}") from e
    return from_mapping(raw, base_dir=path.parent)
