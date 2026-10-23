"""Application context: the only place that wires settings, engine and shared services together."""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager

from sqlalchemy.engine import Connection, Engine

from .config import Settings
from .core.ratelimit import RateLimiter
from .core.validation import Validators
from .services.dtc_templates import TemplateCache
from .services.elevation import ElevationClient
from .services.transfers import TransferBroker


class Context:
    def __init__(self, settings: Settings, engine: Engine):
        self.settings = settings
        self.engine = engine
        self.validators = Validators(settings.contracts_dir / "schemas")
        self.limiter = RateLimiter()
        self.transfers = TransferBroker()
        self.elevation = ElevationClient(settings.elevation_url)
        self.dtc_templates = TemplateCache()
        self._versions: dict[str, int] = defaultdict(int)

    @contextmanager
    def tx(self) -> Iterator[Connection]:
        """Read/write transaction."""
        with self.engine.connect() as cn:
            cn = cn.execution_options(write=True)  # SQLite: BEGIN IMMEDIATE, see db/engine.py
            with cn.begin():
                yield cn

    def version(self, server_id: str) -> int:
        return self._versions[server_id]

    def bump(self, server_id: str) -> None:
        """Signal that a server's data changed (drives the SSE stream)."""
        self._versions[server_id] += 1
