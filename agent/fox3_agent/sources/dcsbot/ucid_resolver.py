"""nick -> ucid resolution with positive/negative caching and a bounded request rate.

DCSServerBot's /servers lists players by nick only. /getuser does a substring (ILIKE) search, so we keep only exact
(case-insensitive) matches, preferring the entry whose `current_server` is ours, then the most recent (API order).
"""
from __future__ import annotations

from collections.abc import Callable
from typing import Any

Lookup = Callable[[str], list[dict[str, Any]]]


class UcidResolver:
    def __init__(self, lookup: Lookup, clock: Callable[[], float], *, server_name: str = "", max_lookups_per_cycle: int = 5,
                 ttl_s: float = 600.0, negative_ttl_s: float = 60.0) -> None:
        self._lookup, self._clock, self._server = lookup, clock, server_name
        self._max, self._ttl, self._neg_ttl = max_lookups_per_cycle, ttl_s, negative_ttl_s
        self._cache: dict[str, tuple[str | None, float]] = {}
        self._budget = max_lookups_per_cycle

    def new_cycle(self) -> None:
        self._budget = self._max

    def cached(self, name: str) -> str | None:
        hit = self._cache.get(name)
        return hit[0] if hit and hit[1] > self._clock() else None

    def resolve(self, name: str) -> str | None:
        """Cached ucid, or one bounded lookup. Lookup failures propagate (the caller backs off) and are not cached."""
        hit = self._cache.get(name)
        if hit and hit[1] > self._clock():
            return hit[0]
        if self._budget <= 0:
            return None
        self._budget -= 1
        ucid = self._pick(name, self._lookup(name))
        self._cache[name] = (ucid, self._clock() + (self._ttl if ucid else self._neg_ttl))
        if len(self._cache) > 5000:
            self._evict()
        return ucid

    def _pick(self, name: str, entries: list[dict[str, Any]]) -> str | None:
        exact = [e for e in entries if isinstance(e.get("ucid"), str) and str(e.get("nick", "")).casefold() == name.casefold()]
        if not exact:
            return None
        for pred in (lambda e: e.get("nick") == name and e.get("current_server") == self._server,
                     lambda e: e.get("current_server") == self._server and bool(self._server),
                     lambda e: e.get("nick") == name):
            for e in exact:
                if pred(e):
                    return e["ucid"]
        return exact[0]["ucid"]

    def _evict(self) -> None:
        now = self._clock()
        self._cache = {k: v for k, v in self._cache.items() if v[1] > now}
