"""Validated, immutable configuration of the DCSServerBot source."""
from __future__ import annotations

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass, field, fields
from typing import Any

from .errors import ConfigError
from .rest_url import clean_prefix, parse_base

_MISSION_TYPES = ("foothold", "generic")
ENV_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_]{0,63}")


@dataclass(frozen=True)
class DcsBotConfig:
    rest_enabled: bool = False
    rest_url: str = "http://localhost:9876"
    rest_prefix: str = ""
    api_key: str | None = field(default=None, repr=False)
    api_key_env: str | None = None         # name of the env var holding the API key (preferred: the key stays out of files)
    verify_tls: bool | str = True          # True / False / path of a CA bundle (self-signed local setups)
    server_name: str = ""
    db_enabled: bool = False
    db_url: str | None = field(default=None, repr=False)   # may embed a password: hidden from repr
    db_url_env: str | None = None          # name of the env var holding the SQLAlchemy URL (preferred)
    mission_type: str = "foothold"
    info_refresh_s: float = 60.0
    players_refresh_s: float = 10.0
    rest_poll_s: float = 3.0               # how often /servers is fetched at most
    db_poll_s: float = 2.0
    links_poll_s: float = 300.0            # how often the verified Discord<->UCID pairs are read (only changes are sent)
    links_resync_s: float = 21_600.0       # all pairs are re-sent this often, in case central lost them
    request_timeout_s: float = 5.0
    max_response_bytes: int = 2_000_000
    db_batch_size: int = 200
    db_seed_back: int = 100
    backoff_max_s: float = 120.0
    max_lookups_per_cycle: int = 5

    def resolved_api_key(self, environ: Mapping[str, str] | None = None) -> str | None:
        env = os.environ if environ is None else environ
        if self.api_key_env:
            return env.get(self.api_key_env) or None
        return self.api_key

    def resolved_db_url(self, environ: Mapping[str, str] | None = None) -> str | None:
        env = os.environ if environ is None else environ
        if self.db_url_env:
            return env.get(self.db_url_env) or None
        return self.db_url

    @classmethod
    def from_mapping(cls, raw: Mapping[str, Any]) -> DcsBotConfig:
        known = {f.name: f for f in fields(cls)}
        unknown = sorted(set(raw) - set(known))
        if unknown:
            raise ConfigError(f"unknown dcsbot option(s): {', '.join(unknown)}")
        defaults = cls()
        values: dict[str, Any] = {}
        for key, value in raw.items():
            values[key] = _check(key, value, getattr(defaults, key))
        cfg = cls(**values)
        cfg._validate()
        return cfg

    def _validate(self) -> None:
        if self.mission_type not in _MISSION_TYPES:
            raise ConfigError(f"mission_type must be one of {_MISSION_TYPES}")
        if self.api_key and self.api_key_env:
            raise ConfigError("use either api_key or api_key_env, not both")
        for name in ("api_key_env", "db_url_env"):
            value = getattr(self, name)
            if value is not None and not ENV_NAME.fullmatch(value):
                raise ConfigError(f"{name} must be the NAME of an environment variable (letters, digits, underscore), not a value")
        if self.rest_enabled:
            if not self.rest_url.startswith(("http://", "https://")):
                raise ConfigError("rest_url must start with http:// or https://")
            parse_base(self.rest_url)
            clean_prefix(self.rest_prefix)
        if self.db_enabled and not self.db_url and not self.db_url_env:
            raise ConfigError("db_enabled requires db_url_env (recommended) or db_url")
        for name in ("info_refresh_s", "players_refresh_s", "rest_poll_s", "db_poll_s", "links_poll_s", "links_resync_s",
                     "request_timeout_s", "backoff_max_s"):
            if getattr(self, name) <= 0:
                raise ConfigError(f"{name} must be > 0")
        if not 1 <= self.db_batch_size <= 500:
            raise ConfigError("db_batch_size must be between 1 and 500")
        if self.db_seed_back < 0 or self.max_lookups_per_cycle < 1 or self.max_response_bytes < 1024:
            raise ConfigError("db_seed_back >= 0, max_lookups_per_cycle >= 1 and max_response_bytes >= 1024 required")


def _check(key: str, value: Any, default: Any) -> Any:
    if key == "verify_tls":
        if isinstance(value, bool) or (isinstance(value, str) and value):
            return value
        raise ConfigError("verify_tls must be a boolean or a CA bundle path")
    if default is None:   # optional strings (api_key, api_key_env, db_url, db_url_env)
        if value is None or (isinstance(value, str) and value):
            return value
        raise ConfigError(f"{key} must be a non-empty string")
    if isinstance(default, bool):
        if isinstance(value, bool):
            return value
    elif isinstance(default, int):
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    elif isinstance(default, float):
        if isinstance(value, int | float) and not isinstance(value, bool):
            return float(value)
    elif isinstance(default, str) and isinstance(value, str):
        return value
    raise ConfigError(f"{key} has an invalid type ({type(value).__name__})")
