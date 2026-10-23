"""Simulated agent: pairs with central and streams simulated data through the real outbox/sender."""
from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

from .. import __version__
from ..client import CentralClient
from ..outbox import Outbox
from ..protocol import PATHS, envelope
from ..sender import Sender
from .scenarios import CAUCASUS, Scenario
from .world import SimWorld

log = logging.getLogger("fox3.agent.sim")


class SimAgent:
    def __init__(self, central_url: str, pairing_code: str, workdir: Path, tick_s: float = 2.0, seed: int | None = None,
                 scenario: Scenario = CAUCASUS):
        self.world, self.tick_s = SimWorld(seed, scenario), tick_s
        workdir.mkdir(parents=True, exist_ok=True)
        creds = CentralClient(central_url).pair(pairing_code, "sim-agent", __version__)
        self.client = CentralClient(central_url, creds["api_key"])
        self.outbox = Outbox(workdir / "queue.sqlite")
        self.sender = Sender(self.outbox, self.client, retry_initial_s=1, retry_max_s=10)
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._loop, name="fox3-sim", daemon=True)
        self._started = time.monotonic()

    def warmup(self, ticks: int) -> None:
        """Pre-generate history so a fresh demo is not empty (events are sent in one batch)."""
        batch: list[dict] = []
        for _ in range(ticks):
            self.world.tick()
            if (ev := self.world.drain_events()):
                batch.extend(ev["events"])
        for i in range(0, len(batch), 500):
            self._queue("events", {"events": batch[i:i + 500]})
        for payload in self.world.tacview_indexes():
            self._queue("tacview_index", payload)

    def start(self) -> None:
        self.sender.start()
        self._thread.start()

    def stop(self) -> None:
        self._stop.set()
        self._thread.join(timeout=5)
        self.sender.stop()
        self.client.close()

    def _queue(self, kind: str, payload: dict | None) -> None:
        if payload is not None:
            self.outbox.put(PATHS[kind], envelope(payload))

    def _loop(self) -> None:
        n = 0
        while not self._stop.is_set():
            if n % 30 == 0:
                self._queue("server_info", self.world.server_info())
            self.world.tick()
            if self.world.sc.mission_type == "foothold":  # a training server has no campaign state
                self._queue("foothold_state", self.world.foothold_state())
            self._queue("players", self.world.players())
            self._queue("events", self.world.drain_events())
            self._queue("heartbeat", {"agent_version": __version__, "uptime_s": int(time.monotonic() - self._started),
                                      "queue_depth": len(self.outbox), "dcs_running": True})
            self.sender.notify()
            n += 1
            self._stop.wait(self.tick_s)
