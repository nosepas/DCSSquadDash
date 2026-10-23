"""REST half of the source: turns /servers (+ /getuser for ucids) into `server_info` and `players` messages."""
from __future__ import annotations

from collections.abc import Callable
from datetime import datetime
from typing import Any

import httpx

from ..base import Message, Warning_
from .backoff import Backoff
from .config import DcsBotConfig
from .errors import RestAuthError, RestProtocolError, RestUnreachable
from .players_mapper import map_players
from .rest_client import RestClient
from .server_mapper import map_server_info, select_server
from .ucid_resolver import UcidResolver


class RestFeed:
    def __init__(self, cfg: DcsBotConfig, clock: Callable[[], datetime], transport: httpx.BaseTransport | None = None) -> None:
        self._cfg, self._clock = cfg, clock
        self.client = RestClient(cfg.rest_url, prefix=cfg.rest_prefix, api_key=cfg.resolved_api_key(), verify=cfg.verify_tls,
                                 timeout_s=cfg.request_timeout_s, max_bytes=cfg.max_response_bytes, transport=transport)
        self.resolver = UcidResolver(self.client.get_users, lambda: clock().timestamp(), server_name=cfg.server_name,
                                     max_lookups_per_cycle=cfg.max_lookups_per_cycle)
        self._backoff = Backoff(max_s=cfg.backoff_max_s)
        self._next_fetch = 0.0
        self._sent: dict[str, tuple[str, float]] = {}      # kind -> (fingerprint, sent_at)
        self.players_by_name: dict[str, dict[str, Any]] = {}
        self.warnings: list[Warning_] = []

    def poll(self) -> list[Message]:
        now_dt = self._clock()
        now = now_dt.timestamp()
        if now < self._next_fetch or not self._backoff.ready(now):
            return []
        self._next_fetch = now + self._cfg.rest_poll_s
        try:
            msgs = self._fetch(now_dt, now)
        except RestAuthError as exc:
            return self._fail(now, "DCSBOT_AUTH_FAILED", str(exc) + self._env_hint())
        except (RestUnreachable, RestProtocolError) as exc:
            return self._fail(now, "DCSBOT_UNREACHABLE", str(exc))
        self._backoff.succeeded()
        return msgs

    def _env_hint(self) -> str:
        cfg = self._cfg
        return f" (environment variable {cfg.api_key_env} is empty in this process)" if cfg.api_key_env and not cfg.resolved_api_key() else ""

    def _fail(self, now: float, code: str, message: str) -> list[Message]:
        self._backoff.failed(now)
        self.warnings = [Warning_(code, message)]
        return []

    def _fetch(self, now_dt: datetime, now: float) -> list[Message]:
        cfg = self._cfg
        info = select_server(self.client.get_servers(), cfg.server_name)
        if info is None:
            self.warnings = [Warning_("DCSBOT_SERVER_NOT_FOUND", f"DCSServerBot has no server matching {cfg.server_name!r}")]
            return []
        self.warnings = []
        server_info = map_server_info(info, mission_type=cfg.mission_type, now=now_dt, dcsbot_db=cfg.db_enabled)
        msgs = self._due("server_info", server_info, now, cfg.info_refresh_s, ignore=("mission_started_at",))
        raw = info.get("players") if isinstance(info.get("players"), list) else []
        players, unresolved = map_players(raw, self.resolver, now_dt)
        if unresolved:
            self.warnings.append(Warning_("DCSBOT_UCID_UNRESOLVED", f"{unresolved} player(s) not matched to a ucid, omitted"))
        self.players_by_name = {p["name"]: {"ucid": p["ucid"], "coalition": p["coalition"], "unit_type": p["aircraft"]}
                                for p in players["players"]}
        return msgs + self._due("players", players, now, cfg.players_refresh_s, ignore=("snapshot_at",))

    def _due(self, kind: str, payload: dict[str, Any], now: float, refresh_s: float, ignore: tuple[str, ...]) -> list[Message]:
        fingerprint = repr(sorted((k, repr(v)) for k, v in payload.items() if k not in ignore))
        last = self._sent.get(kind)
        if last and last[0] == fingerprint and now - last[1] < refresh_s:
            return []
        self._sent[kind] = (fingerprint, now)
        return [Message(kind, payload)]
