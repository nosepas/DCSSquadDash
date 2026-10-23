"""Short-lived server-side cache of uploaded .dtc files, so the (large) template is not sent back and forth with every export."""
from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass

from ..core.errors import BadRequest, NotFound
from ..core.security import token


@dataclass
class _Entry:
    owner: int
    template: dict
    expires: float
    cost: int = 0


class TemplateCache:
    def __init__(self, ttl_s: float = 3600, max_entries: int = 40, max_per_user: int = 5,
                 max_bytes: int = 64 * 1024 * 1024, clock=time.monotonic):
        self._items: OrderedDict[str, _Entry] = OrderedDict()
        self._ttl, self._max, self._per_user, self._clock = ttl_s, max_entries, max_per_user, clock
        self._budget = max_bytes

    def _evict(self) -> None:
        now = self._clock()
        for k in [k for k, e in self._items.items() if e.expires < now]:
            del self._items[k]

    def _used(self) -> int:
        return sum(e.cost for e in self._items.values())

    def _make_room(self, owner: int, cost: int) -> None:
        """Evict oldest entries (same owner first) until `cost` more bytes fit in the budget."""
        used = self._used()
        for mine in (True, False):
            for k in [k for k, e in self._items.items() if (e.owner == owner) == mine]:
                if used + cost <= self._budget:
                    return
                used -= self._items.pop(k).cost

    def put(self, owner: int, template: dict, cost: int = 0) -> str:
        """Store `template`; `cost` = size in bytes of the original upload. Raises BadRequest when it alone exceeds the budget."""
        if cost > self._budget:
            raise BadRequest("the uploaded file is too large to keep for export")
        self._evict()
        mine = [k for k, e in self._items.items() if e.owner == owner]
        for k in mine[: max(0, len(mine) - self._per_user + 1)]:  # oldest of this user go first
            del self._items[k]
        while len(self._items) >= self._max:
            self._items.popitem(last=False)
        self._make_room(owner, cost)
        tid = token(16)
        self._items[tid] = _Entry(owner, template, self._clock() + self._ttl, cost)
        return tid

    def get(self, owner: int, tid: str) -> dict:
        self._evict()
        e = self._items.get(tid)
        if e is None or e.owner != owner:  # unknown, expired or someone else's: indistinguishable on purpose
            raise NotFound("the uploaded file expired: upload it again or use the built-in template")
        return e.template
