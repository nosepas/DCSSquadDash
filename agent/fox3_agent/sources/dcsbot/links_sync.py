"""Turns the verified Discord<->UCID pairs into `discord_links` messages: only changes, plus a periodic full resync."""
from __future__ import annotations

from ..base import Message

BATCH = 500   # matches maxItems in contracts/schemas/discord_links.json


class LinkSync:
    def __init__(self, poll_s: float, resync_s: float) -> None:
        self._poll_s, self._resync_s = poll_s, resync_s
        self._sent: dict[str, str] = {}
        self._next_poll = 0.0
        self._next_resync = 0.0

    def due(self, now: float) -> bool:
        return now >= self._next_poll

    def schedule(self, now: float) -> None:
        self._next_poll = now + self._poll_s

    def messages(self, current: dict[str, str], now: float) -> list[Message]:
        """Messages for the pairs that are new/changed (all of them when the resync is due)."""
        full = now >= self._next_resync
        pending = [(u, d) for u, d in current.items() if full or self._sent.get(u) != d]
        if full:
            self._next_resync = now + self._resync_s
        self._sent = dict(current)
        return [Message("discord_links", {"links": [{"ucid": u, "discord_id": d} for u, d in pending[i:i + BATCH]]})
                for i in range(0, len(pending), BATCH)]
