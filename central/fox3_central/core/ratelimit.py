"""In-process sliding-window rate limiter (single central process; swap for a shared store if scaled out)."""
from __future__ import annotations

import threading
import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_keys: int = 50_000) -> None:
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()
        self._max_keys = max_keys

    def allow(self, key: str, limit: int, window_s: int = 60) -> bool:
        t = time.monotonic()
        with self._lock:
            q = self._hits[key]
            while q and q[0] < t - window_s:
                q.popleft()
            if len(q) >= limit:
                return False
            q.append(t)
            if len(self._hits) > self._max_keys:
                self._prune(t, window_s)
            return True

    def _prune(self, now: float, window_s: int) -> None:
        """Drop keys with no recent hits; if still over the cap, drop the oldest keys (bounded memory under attack)."""
        for k in [k for k, q in self._hits.items() if not q or q[-1] < now - window_s]:
            del self._hits[k]
        for k in list(self._hits)[: max(0, len(self._hits) - self._max_keys)]:
            del self._hits[k]
