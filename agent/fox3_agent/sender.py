"""Background sender: drains the outbox in order, with exponential backoff while central is unreachable."""
from __future__ import annotations

import logging
import threading

from .client import CentralClient, Outcome
from .outbox import Outbox
from .protocol import utc_now

log = logging.getLogger("fox3.agent.sender")
MAX_REJECTED_PATHS = 50


class Sender:
    def __init__(self, outbox: Outbox, client: CentralClient, retry_initial_s: float = 2, retry_max_s: float = 300):
        self._outbox, self._client = outbox, client
        self._initial, self._max = retry_initial_s, retry_max_s
        self.rejected: dict[str, int] = {}  # path -> messages central refused (kept for the heartbeat, at most MAX_REJECTED_PATHS)
        self.last_success_at: str | None = None  # UTC time central last accepted a message
        self.auth_rejections = 0  # consecutive 401 answers (revoked key?); reset by the first success
        self._stop, self._wake = threading.Event(), threading.Event()
        self._thread = threading.Thread(target=self._run, name="fox3-sender", daemon=True)

    def start(self) -> None:
        self._thread.start()

    def notify(self) -> None:
        self._wake.set()

    def stop(self) -> None:
        self._stop.set()
        self._wake.set()
        self._thread.join(timeout=5)

    def drain_once(self) -> bool:
        """Send queued messages in order. Returns False if central could not be reached (stop and back off)."""
        for msg_id, path, body in self._outbox.peek():
            outcome = self._client.send(path, body)
            if outcome is Outcome.AUTH:
                self.auth_rejections += 1  # keep the queue untouched: nothing is lost if the operator pairs the agent again
                log.error("central rejected the agent key (401): it may have been revoked, pair the agent again")
                return False
            if outcome is Outcome.RETRY:
                return False
            if outcome is Outcome.OK:
                self.auth_rejections = 0
                self.last_success_at = utc_now()
            elif path in self.rejected or len(self.rejected) < MAX_REJECTED_PATHS:  # DROP: discard it, never retried
                log.warning("dropping rejected message for %s", path)
                self.rejected[path] = self.rejected.get(path, 0) + 1
            self._outbox.delete(msg_id)
        return True

    def _run(self) -> None:
        delay = self._initial
        while not self._stop.is_set():
            if self.drain_once():
                delay = self._initial
                self._wake.wait(timeout=1.0)
                self._wake.clear()
            else:
                log.warning("central unreachable, retrying in %.0fs (%d queued)", delay, len(self._outbox))
                delay = self._max if self.auth_rejections else delay  # revoked key: do not hammer central
                self._stop.wait(delay)
                delay = min(delay * 2, self._max)
