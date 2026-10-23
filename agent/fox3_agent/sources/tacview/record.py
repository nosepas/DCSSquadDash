"""Persisted record of already indexed files: (relative_path -> size, mtime_ns), one JSON file per folder."""
from __future__ import annotations

import hashlib
import json
import os
import threading
from pathlib import Path


class IndexRecord:
    def __init__(self, state_dir: Path, folder: Path) -> None:
        digest = hashlib.sha1(str(folder).encode("utf-8", "replace")).hexdigest()[:12]
        self._path = state_dir / f"tacview_index_{digest}.json"
        self._lock = threading.Lock()
        self._files: dict[str, tuple[int, int]] = {}
        self._dirty = False
        self._load()

    def _load(self) -> None:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            self._files = {str(k): (int(v[0]), int(v[1])) for k, v in data["files"].items()}
        except (OSError, ValueError, KeyError, TypeError, IndexError, AttributeError):
            self._files = {}        # missing or corrupted: start over

    def is_current(self, rel: str, size: int, mtime_ns: int) -> bool:
        with self._lock:
            return self._files.get(rel) == (size, mtime_ns)

    def mark(self, rel: str, size: int, mtime_ns: int) -> None:
        with self._lock:
            self._files[rel] = (size, mtime_ns)
            self._dirty = True

    def forget_missing(self, present: set[str]) -> None:
        with self._lock:
            for rel in [r for r in self._files if r not in present]:
                del self._files[rel]
                self._dirty = True

    def save(self) -> None:
        """Atomic write (temp file + replace). Silent on I/O errors: the worst case is a re-index."""
        with self._lock:
            if not self._dirty:
                return
            payload = json.dumps({"files": {k: list(v) for k, v in self._files.items()}})
            self._dirty = False
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self._path.with_suffix(".tmp")
            tmp.write_text(payload, encoding="utf-8")
            os.replace(tmp, self._path)
        except OSError:
            with self._lock:
                self._dirty = True
