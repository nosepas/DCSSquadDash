"""FootholdSource: polls the persistence file and emits a `foothold_state` message when its content changes."""
from __future__ import annotations

import hashlib
import time
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path

from ...diagnose.redact import local_user_names, redact_text
from ..base import Message, Warning_
from .farps import farps_file, read_farps
from .locator import locate_persistence_file
from .lua_errors import LuaParseError
from .lua_parser import parse_lua
from .normalize import normalize

DEFAULT_MAX_BYTES = 64 * 1024 * 1024
Signature = tuple[str, int, int, tuple[int, int] | None]  # (path, mtime_ns, size, (FARP csv mtime_ns, size))


def _iso(epoch_s: float) -> str:
    return datetime.fromtimestamp(epoch_s, UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


class FootholdSource:
    name = "foothold"

    def __init__(self, saves_dir: Path, stale_after_s: int = 900, max_bytes: int = DEFAULT_MAX_BYTES,
                 clock: Callable[[], float] = time.time) -> None:
        self.saves_dir = Path(saves_dir)
        self.stale_after_s = stale_after_s
        self.max_bytes = max_bytes
        self._clock = clock
        self._warnings: list[Warning_] = []
        self._state: dict | None = None
        self._positions: list[dict] = []
        self._hash: str | None = None
        self._mtime: float | None = None  # mtime of the file seen by the current poll
        self._seen: Signature | None = None  # last signature fully handled (sent, deduped or rejected as invalid)
        self._problem: Warning_ | None = None  # why `_seen` was rejected, re-reported on every poll until the file changes

    def last_state(self) -> dict | None:
        return self._state

    def positions(self) -> list[dict]:
        return list(self._positions)

    def warnings(self) -> list[Warning_]:
        return list(self._warnings)

    def poll(self) -> list[Message]:
        self._warnings = []
        self._mtime = None
        messages = self._poll()
        if self._mtime is not None and self._state is not None and self._clock() - self._mtime > self.stale_after_s:
            self._warnings.append(Warning_("FOOTHOLD_FILE_STALE", f"Foothold file not updated for over {self.stale_after_s} s"))
        return messages

    def _poll(self) -> list[Message]:
        if not self.saves_dir.is_dir():
            return self._warn("FOOTHOLD_FOLDER_MISSING", f"Foothold saves folder not found: {redact_text(str(self.saves_dir), local_user_names())}")
        path = locate_persistence_file(self.saves_dir)
        if path is None:
            return self._warn("FOOTHOLD_FILE_MISSING", "No Foothold persistence file (foothold*.lua) in the saves folder")
        try:
            st = path.stat()
        except OSError as exc:
            return self._warn("FOOTHOLD_FILE_UNREADABLE", f"Cannot stat {path.name}: {exc.strerror or exc}")
        self._mtime = st.st_mtime
        csv = farps_file(path)
        csv_sig = (csv.stat().st_mtime_ns, csv.stat().st_size) if csv else None
        sig: Signature = (str(path), st.st_mtime_ns, st.st_size, csv_sig)
        if sig == self._seen:
            if self._problem:
                self._warnings.append(self._problem)
            return []
        self._problem = None
        if st.st_size > self.max_bytes:
            return self._reject(sig, True, f"{path.name} is larger than the {self.max_bytes} byte limit")
        try:
            data = path.read_bytes()
            after = path.stat()
        except OSError as exc:
            return self._warn("FOOTHOLD_FILE_UNREADABLE", f"Cannot read {path.name}: {exc.strerror or exc}")
        stable = (after.st_mtime_ns, after.st_size) == (st.st_mtime_ns, st.st_size) == (st.st_mtime_ns, len(data))
        farps, farps_raw = read_farps(path)  # player-built FARPs live in a sibling csv: a change there is a change of state
        digest = hashlib.sha256(data + b"\0" + farps_raw).hexdigest()
        if digest == self._hash:
            self._seen = sig
            return []
        try:
            parsed = parse_lua(data, max_bytes=self.max_bytes)
            if "zones" not in parsed:
                raise LuaParseError(1, 1, "no 'zones' table in the file")
        except LuaParseError as exc:
            return self._reject(sig, stable, f"{path.name} could not be parsed ({exc}); keeping the last good state")
        result = normalize(parsed, source_file=path.name, source_mtime=_iso(st.st_mtime), snapshot_at=_iso(self._clock()))
        if farps:
            result.payload["farps"] = farps
        self._state, self._positions, self._hash = result.payload, result.positions, digest
        if stable:
            self._seen = sig
        return [Message("foothold_state", result.payload)]

    def _warn(self, code: str, message: str) -> list[Message]:
        self._warnings.append(Warning_(code, message))
        return []

    def _reject(self, sig: Signature, stable: bool, message: str) -> list[Message]:
        """Invalid content. A file that was stable while read is complete, so it is not re-read until it changes;
        one that changed during the read is retried on the next poll (the game was still writing it)."""
        self._problem = Warning_("FOOTHOLD_FILE_INVALID", message) if stable else None
        if stable:
            self._seen = sig
        return self._warn("FOOTHOLD_FILE_INVALID", message)
