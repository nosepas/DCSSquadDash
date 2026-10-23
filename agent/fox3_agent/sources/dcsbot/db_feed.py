"""Database half of the source: new `missionstats` rows -> `events` messages, with backoff."""
from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime

from sqlalchemy import Engine

from ..base import Message, Warning_
from .backoff import Backoff
from .config import DcsBotConfig
from .db_engine import make_engine
from .db_events import DbEventReader
from .db_links import DiscordLinkReader
from .errors import DbError
from .links_sync import LinkSync

MAX_BATCHES_PER_POLL = 4


class DbFeed:
    def __init__(self, cfg: DcsBotConfig, clock: Callable[[], datetime], engine: Engine | None = None,
                 watermark: int | None = None, environ: Mapping[str, str] | None = None) -> None:
        self._cfg, self._clock, self._engine, self._environ = cfg, clock, engine, environ
        self._watermark = watermark
        self.reader: DbEventReader | None = None
        self._backoff = Backoff(max_s=cfg.backoff_max_s)
        self._next = 0.0
        self.warnings: list[Warning_] = []
        self._links = LinkSync(cfg.links_poll_s, cfg.links_resync_s)

    @property
    def watermark(self) -> int | None:
        return self.reader.watermark if self.reader else self._watermark

    def poll(self) -> list[Message]:
        now = self._clock().timestamp()
        if now < self._next or not self._backoff.ready(now):
            return []
        self._next = now + self._cfg.db_poll_s
        try:
            msgs = self._read()
        except DbError as exc:
            self._backoff.failed(now)
            self.warnings = [Warning_("DCSBOT_DB_ERROR", str(exc))]
            return []
        self._backoff.succeeded()
        self.warnings = []
        return msgs + self._poll_links(now)

    def _poll_links(self, now: float) -> list[Message]:
        """Independent of the events read: a failure here never drops events (their watermark already moved)."""
        if self.reader is None or not self._links.due(now):
            return []
        self._links.schedule(now)
        try:
            current = DiscordLinkReader(self.reader.engine).read_all()
        except DbError as exc:
            self.warnings = [Warning_("DCSBOT_DB_ERROR", str(exc))]
            return []
        return self._links.messages(current, now)

    def _reader(self) -> DbEventReader:
        if self.reader is None:
            engine = self._engine
            if engine is None:
                url = self._cfg.resolved_db_url(self._environ)
                if not url:
                    raise DbError(f"database URL not available (environment variable {self._cfg.db_url_env!r} is empty)")
                engine = make_engine(url)
            self.reader = DbEventReader(engine, self._cfg.server_name, batch_size=self._cfg.db_batch_size,
                                        seed_back=self._cfg.db_seed_back, watermark=self._watermark)
        return self.reader

    def _read(self) -> list[Message]:
        reader = self._reader()
        msgs: list[Message] = []
        for _ in range(MAX_BATCHES_PER_POLL):
            events = reader.fetch_batch()
            if events:
                msgs.append(Message("events", {"events": events}))
            if len(events) < self._cfg.db_batch_size:
                break
        return msgs
