"""UTC time helpers. Timestamps are stored as ISO-8601 strings ending in Z (sortable, DB-portable)."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

_FMT = "%Y-%m-%dT%H:%M:%SZ"


def now() -> str:
    return datetime.now(UTC).strftime(_FMT)


def after(**delta: float) -> str:
    return (datetime.now(UTC) + timedelta(**delta)).strftime(_FMT)


def ago(**delta: float) -> str:
    return (datetime.now(UTC) - timedelta(**delta)).strftime(_FMT)
