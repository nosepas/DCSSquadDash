"""On-demand file relay: browser asks -> agent (outbound-only) uploads a stream -> central pipes it to the browser.

Nothing is stored on central. State is in memory (single central process): a restart cancels running transfers.
Bounded queues give back-pressure, so a slow browser slows the upload instead of filling memory.
"""
from __future__ import annotations

import asyncio
import contextlib
import uuid
from collections.abc import AsyncIterator
from dataclasses import dataclass, field

from ..core.errors import AppError

_END = object()


class Busy(AppError):
    status, code = 429, "transfer_busy"


class Unavailable(AppError):
    status, code = 504, "server_unreachable"


class TransferAborted(RuntimeError):
    """Raised inside the response stream: headers are already sent, so the connection is cut and the browser sees a failed download."""


class Gone(AppError):
    status, code = 410, "transfer_cancelled"


@dataclass
class Transfer:
    server_id: str
    relative_path: str
    filename: str
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    owner: int | None = None  # user who asked for the download
    size: int | None = None
    failure: str | None = None
    cancelled: bool = False
    claimed: asyncio.Event = field(default_factory=asyncio.Event)
    queue: asyncio.Queue = field(default_factory=lambda: asyncio.Queue(maxsize=8))
    received: int = 0

    def cancel(self) -> None:
        self.cancelled = True
        self.claimed.set()


class TransferBroker:
    def __init__(self, max_per_server: int = 2, max_total: int = 8, max_bytes: int = 4 * 1024**3, idle_s: float = 60.0):
        self._items: dict[str, Transfer] = {}
        self._wakeups: dict[str, asyncio.Event] = {}
        self.max_per_server, self.max_total, self.max_bytes, self.idle_s = max_per_server, max_total, max_bytes, idle_s

    def _active(self, server_id: str | None = None) -> list[Transfer]:
        return [t for t in self._items.values() if server_id in (None, t.server_id)]

    def request(self, server_id: str, relative_path: str, filename: str, owner: int | None = None) -> Transfer:
        if len(self._active(server_id)) >= self.max_per_server or len(self._active()) >= self.max_total:
            raise Busy("too many downloads in progress, try again in a moment")
        if owner is not None and any(t.owner == owner for t in self._items.values()):  # one at a time per user: nobody hogs the slots
            raise Busy("you already have a download in progress")
        t = Transfer(server_id, relative_path, filename, owner=owner)
        self._items[t.id] = t
        self._wakeups.setdefault(server_id, asyncio.Event()).set()
        return t

    async def pending_for(self, server_id: str, wait_s: float) -> list[Transfer]:
        """Long poll used by the agent: requests nobody has claimed yet."""
        def unclaimed() -> list[Transfer]:
            return [t for t in self._active(server_id) if not t.claimed.is_set()]

        ev = self._wakeups.setdefault(server_id, asyncio.Event())
        if not unclaimed():
            ev.clear()
            with contextlib.suppress(TimeoutError):
                await asyncio.wait_for(ev.wait(), wait_s)
        return unclaimed()

    def claim(self, transfer_id: str, server_id: str, size: int | None) -> Transfer:
        t = self._items.get(transfer_id)
        if not t or t.server_id != server_id or t.cancelled:
            raise Gone("unknown, foreign or cancelled transfer")
        if t.claimed.is_set():
            raise Gone("transfer already started")
        if size is not None and size > self.max_bytes:
            self.fail(transfer_id, server_id, "file too large")
            raise Gone("file exceeds the maximum transfer size")
        t.size = size
        t.claimed.set()
        return t

    def fail(self, transfer_id: str, server_id: str, reason: str) -> None:
        t = self._items.get(transfer_id)
        if t and t.server_id == server_id and not t.cancelled:
            t.failure = reason[:200]
            t.claimed.set()
            t.queue.put_nowait(_END)

    def discard(self, transfer_id: str) -> None:
        t = self._items.pop(transfer_id, None)
        if t:
            t.cancel()

    async def push(self, t: Transfer, chunk: bytes) -> None:
        """Called by the agent upload. Raises Gone if the browser went away."""
        if t.cancelled:
            raise Gone("download cancelled by the browser")
        t.received += len(chunk)
        if t.received > self.max_bytes or (t.size is not None and t.received > t.size):
            raise Gone("upload larger than announced")
        try:
            await asyncio.wait_for(t.queue.put(chunk), self.idle_s)  # a browser that stops reading must not hold the slot forever
        except TimeoutError:
            t.cancel()
            raise Gone("the browser stopped reading the download") from None

    async def finish(self, t: Transfer) -> None:
        await t.queue.put(_END)

    async def stream(self, t: Transfer) -> AsyncIterator[bytes]:
        """Browser side. Aborts the response (not a silent truncation) if the upload ended early or failed."""
        try:
            while True:
                try:
                    item = await asyncio.wait_for(t.queue.get(), self.idle_s)
                except TimeoutError:  # the agent stopped sending: free the slot and cut the connection
                    raise TransferAborted("the server stopped sending the file") from None
                if item is _END:
                    if t.failure or (t.size is not None and t.received != t.size):
                        raise TransferAborted(t.failure or "the upload ended before the whole file arrived")
                    return
                yield item
        finally:
            self.discard(t.id)
