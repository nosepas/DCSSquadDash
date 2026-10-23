"""DcsBotSource: combines the REST feed (server_info, players) and the read-only DB feed (events)."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import UTC, datetime
from typing import Any

import httpx
from sqlalchemy import Engine

from ..base import Message, Warning_
from .config import DcsBotConfig
from .db_feed import DbFeed
from .errors import DcsBotError
from .rest_feed import RestFeed


def _utc_now() -> datetime:
    return datetime.now(UTC)


class DcsBotSource:
    name = "dcsbot"

    def __init__(self, config: DcsBotConfig, *, clock: Callable[[], datetime] = _utc_now,
                 transport: httpx.BaseTransport | None = None, engine: Engine | None = None,
                 watermark: int | None = None, environ: Mapping[str, str] | None = None) -> None:
        self.config = config
        self._rest = RestFeed(config, clock, transport) if config.rest_enabled else None
        self._db = DbFeed(config, clock, engine, watermark, environ) if config.db_enabled else None

    @property
    def watermark(self) -> int | None:
        """DB event watermark to persist (None when the DB feed is off or not yet seeded)."""
        return self._db.watermark if self._db else None

    def poll(self) -> list[Message]:
        msgs: list[Message] = []
        for feed in (self._rest, self._db):
            if feed is not None:
                msgs.extend(feed.poll())
        return msgs

    def warnings(self) -> list[Warning_]:
        return [w for feed in (self._rest, self._db) if feed is not None for w in feed.warnings]

    def players_by_name(self) -> dict[str, dict[str, Any]]:
        """Latest connected players (name -> ucid, coalition, unit_type) as seen by the REST feed."""
        return dict(self._rest.players_by_name) if self._rest else {}

    def resolve_ucid(self, name: str) -> str | None:
        """Best-effort ucid of a player name (used for Foothold names). Never raises for expected failures."""
        known = self.players_by_name().get(name)
        if known:
            return known["ucid"]
        try:
            if self._rest is not None and (ucid := self._rest.resolver.resolve(name)):
                return ucid
            if self._db is not None and self._db.reader is not None:
                return self._db.reader.find_ucid(name)
        except DcsBotError:
            return None
        return None
