"""Persistent FIFO outbox so data survives central outages and agent restarts.

The queue is bounded (rows and bytes). Over the cap the oldest low-value messages (snapshots that newer ones
supersede) are dropped first; events, discord links and the tacview index are only dropped when nothing else is left.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
from pathlib import Path

log = logging.getLogger("fox3.agent.outbox")

DEFAULT_MAX_MESSAGES = 50_000
DEFAULT_MAX_BYTES = 200 * 1024 * 1024
SNAPSHOT_PATHS = ("/heartbeat", "/server-info", "/foothold-state", "/players")  # a newer message replaces the older one
COALESCE_BACKLOG = 20  # queued rows from which superseded snapshots are collapsed on enqueue


class Outbox:
    def __init__(self, path: str | Path, max_messages: int = DEFAULT_MAX_MESSAGES, max_bytes: int = DEFAULT_MAX_BYTES):
        self._path, self._max, self._max_bytes, self._lock = str(path), max_messages, max_bytes, threading.Lock()
        self.dropped = 0  # messages discarded because of the cap since start (surfaced in the heartbeat)
        self._overflowing = False  # inside a drop episode: warn only once per episode
        with self._conn() as cn:
            cn.execute("CREATE TABLE IF NOT EXISTS outbox (id INTEGER PRIMARY KEY AUTOINCREMENT, path TEXT NOT NULL, body TEXT NOT NULL)")

    def _conn(self) -> sqlite3.Connection:
        return sqlite3.connect(self._path, timeout=10)

    def put(self, path: str, body: dict) -> None:
        with self._lock, self._conn() as cn:
            if path in SNAPSHOT_PATHS and self._count(cn) >= COALESCE_BACKLOG:
                cn.execute("DELETE FROM outbox WHERE path = ?", (path,))
            cn.execute("INSERT INTO outbox (path, body) VALUES (?, ?)", (path, json.dumps(body)))
            self._enforce_cap(cn)

    @staticmethod
    def _count(cn: sqlite3.Connection) -> int:
        return cn.execute("SELECT COUNT(*) FROM outbox").fetchone()[0]

    def _over(self, cn: sqlite3.Connection) -> bool:
        rows, size = cn.execute("SELECT COUNT(*), COALESCE(SUM(LENGTH(body) + LENGTH(path)), 0) FROM outbox").fetchone()
        return rows > 1 and (rows > self._max or size > self._max_bytes)

    def _enforce_cap(self, cn: sqlite3.Connection) -> None:
        dropped = 0
        while self._over(cn):
            snapshots = ",".join("?" * len(SNAPSHOT_PATHS))
            victim = cn.execute(f"SELECT id FROM outbox WHERE path IN ({snapshots}) ORDER BY id LIMIT 1", SNAPSHOT_PATHS).fetchone()
            victim = victim or cn.execute("SELECT id FROM outbox ORDER BY id LIMIT 1").fetchone()
            cn.execute("DELETE FROM outbox WHERE id = ?", (victim[0],))
            dropped += 1
        if not dropped:
            self._overflowing = False
            return
        self.dropped += dropped
        if not self._overflowing:
            self._overflowing = True
            log.warning("outbox is full (max %d messages / %d bytes): dropping the oldest low-value messages", self._max, self._max_bytes)

    def peek(self, limit: int = 50) -> list[tuple[int, str, dict]]:
        with self._lock, self._conn() as cn:
            rows = cn.execute("SELECT id, path, body FROM outbox ORDER BY id LIMIT ?", (limit,)).fetchall()
        return [(i, p, json.loads(b)) for i, p, b in rows]

    def delete(self, msg_id: int) -> None:
        with self._lock, self._conn() as cn:
            cn.execute("DELETE FROM outbox WHERE id = ?", (msg_id,))

    def __len__(self) -> int:
        with self._lock, self._conn() as cn:
            return self._count(cn)
