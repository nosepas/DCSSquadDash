"""The agent loop: poll every source, enrich, queue messages for central, send heartbeats, follow remote settings."""
from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable

import httpx

from .. import __version__
from ..outbox import Outbox
from ..protocol import PATHS, envelope, utc_now
from ..sender import Sender
from ..sources.base import Message, Source
from .info import minimal_server_info
from .merge import attach_positions, resolve_stat_ucids
from .source_set import SourceProvider
from .state import AgentState

log = logging.getLogger("fox3.agent")


class Agent:
    def __init__(self, *, provider: SourceProvider, outbox: Outbox, sender: Sender, state: AgentState, tick_s: float = 2.0,
                 heartbeat_s: float = 30.0, server_info_s: float = 60.0, config_fetch: Callable[[], dict] | None = None,
                 config_refresh_s: float = 60.0, detect: Callable[[], dict] | None = None, detect_every_s: float = 600.0,
                 responder=None, clock: Callable[[], float] = time.monotonic):
        self._p, self._outbox, self._sender, self._state, self._responder = provider, outbox, sender, state, responder
        self._tick_s, self._hb_s, self._info_s, self._clock = tick_s, heartbeat_s, server_info_s, clock
        self._fetch, self._cfg_every, self._detect, self._detect_every = config_fetch, config_refresh_s, detect, detect_every_s
        self._started = clock()
        self._last_hb = self._last_info = self._last_cfg = self._last_detect = -1e12
        self._revision: str | None = None
        self._saw_server_info = False
        self._last_ok: dict[str, str | None] = {}
        self._crashed: dict[str, str] = {}
        self._stop = threading.Event()

    # ---- one iteration (also called directly by tests) -------------------------------------------------------------
    def tick(self) -> None:
        self._refresh_settings()
        for source in list(self._p.sources):
            self._poll(source)
        self._maybe_minimal_info()
        self._maybe_heartbeat()
        self._persist_state()
        self._sender.notify()

    def _refresh_settings(self) -> None:
        now = self._clock()
        if not self._fetch or now - self._last_cfg < self._cfg_every:
            return
        self._last_cfg = now
        try:
            remote = self._fetch()
        except httpx.HTTPError as exc:  # central unreachable: keep working with the settings we have
            log.warning("could not fetch settings (%s)", type(exc).__name__)
            return
        if remote.get("revision") != self._revision:
            self._revision = remote.get("revision")
            self._saw_server_info = False
            self._p.apply(remote)

    def _poll(self, source: Source) -> None:
        try:
            messages = source.poll()
            self._crashed.pop(source.name, None)
        except Exception as exc:  # a faulty source must not stop the agent
            log.exception("source %s crashed", source.name)
            self._crashed[source.name] = type(exc).__name__
            return
        for msg in messages:
            self._enqueue(self._enrich(msg))
        if not source.warnings():
            self._last_ok[source.name] = utc_now()

    def _enrich(self, msg: Message) -> Message:
        if msg.kind == "players" and self._p.foothold:
            attach_positions(msg.payload, self._p.foothold.positions())
        elif msg.kind == "foothold_state" and self._p.dcsbot:
            resolve_stat_ucids(msg.payload, self._p.dcsbot.resolve_ucid)
        elif msg.kind == "server_info":
            self._saw_server_info = True
            self._last_info = self._clock()
        return msg

    def _enqueue(self, msg: Message) -> None:
        self._outbox.put(PATHS[msg.kind], envelope(msg.payload))

    def _maybe_minimal_info(self) -> None:
        now = self._clock()
        if self._saw_server_info or now - self._last_info < self._info_s:
            return
        self._last_info = now
        rest = self._p.dcsbot is not None
        self._enqueue(Message("server_info", minimal_server_info(self._p.mission_type, self._p.foothold is not None, rest, rest)))

    def _maybe_heartbeat(self) -> None:
        now = self._clock()
        if now - self._last_hb < self._hb_s:
            return
        self._last_hb = now
        warnings = [{"code": w.code, "message": w.message} for s in self._p.sources for w in s.warnings()]
        warnings += [{"code": "SOURCE_CRASHED", "message": f"{n}: {e}"} for n, e in self._crashed.items()]
        if self._sender.rejected:  # usually an agent/central version mismatch: data is being lost
            detail = ", ".join(f"{p} x{n}" for p, n in sorted(self._sender.rejected.items()))
            warnings.append({"code": "CENTRAL_REJECTED_MESSAGES", "message": detail})
        if self._sender.auth_rejections:
            warnings.append({"code": "CENTRAL_AUTH_FAILED",
                             "message": "the agent key was rejected: it may have been revoked; pair the agent again"})
        if self._outbox.dropped:  # queue cap reached (central down or key revoked for long): oldest low-value data was discarded
            warnings.append({"code": "OUTBOX_OVERFLOW", "message": f"{self._outbox.dropped} queued messages were dropped because the outbox is full"})
        payload = {"agent_version": __version__, "uptime_s": int(now - self._started), "queue_depth": len(self._outbox),
                   "last_success": dict(self._last_ok), "warnings": warnings}
        if self._detect and now - self._last_detect >= self._detect_every:  # folders found on this PC, as suggestions for the admin
            self._last_detect = now
            payload["detected"] = self._detect()
        self._enqueue(Message("heartbeat", payload))

    def _persist_state(self) -> None:
        dcsbot = self._p.dcsbot
        if dcsbot is not None and dcsbot.watermark is not None:
            current = self._state.load()
            if current.get("dcsbot_watermark") != dcsbot.watermark:
                self._state.save({**current, "dcsbot_watermark": dcsbot.watermark})

    # ---- lifecycle ----------------------------------------------------------------------------------------------------
    def run(self) -> None:
        self._sender.start()
        if self._responder:
            self._responder.start()
        try:
            while not self._stop.is_set():
                self.tick()
                self._stop.wait(self._tick_s)
        finally:
            if self._responder:
                self._responder.stop()
            self._p.stop()
            self._sender.stop()

    def stop(self) -> None:
        self._stop.set()
