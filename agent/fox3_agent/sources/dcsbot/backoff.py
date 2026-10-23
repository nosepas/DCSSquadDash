"""Exponential backoff so a down service is not hammered. Pure state machine over an injected time value."""
from __future__ import annotations


class Backoff:
    def __init__(self, base_s: float = 2.0, max_s: float = 120.0) -> None:
        self._base, self._max = base_s, max_s
        self._failures = 0
        self._retry_at = 0.0

    def ready(self, now: float) -> bool:
        return now >= self._retry_at

    def failed(self, now: float) -> float:
        """Register a failure; returns the delay before the next attempt."""
        delay = min(self._max, self._base * (2 ** min(self._failures, 16)))
        self._failures += 1
        self._retry_at = now + delay
        return delay

    def succeeded(self) -> None:
        self._failures = 0
        self._retry_at = 0.0
