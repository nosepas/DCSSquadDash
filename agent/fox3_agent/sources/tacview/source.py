"""TacviewSource: non-blocking Source that indexes finished `.acmi` recordings in a background thread."""
from __future__ import annotations

import threading
import time
from collections.abc import Callable
from pathlib import Path

from ..base import Message, Warning_
from .acmi_reader import ReaderLimits
from .payload import MAX_APPEARANCES
from .record import IndexRecord
from .worker import IndexWorker, WorkerSettings

RECHECK_S = 3.0      # default pause before the second size observation (see WorkerSettings.recheck_s)
FolderProvider = Callable[[], tuple[Path | None, bool]]     # (folder, enabled); managed from the central admin panel


class TacviewSource:
    name = "tacview"

    def __init__(self, folder_provider: FolderProvider, state_dir: Path, settle_s: float = 120.0, *,
                 rescan_s: float = 30.0, compute_sha256: bool = False, max_appearances: int = MAX_APPEARANCES,
                 limits: ReaderLimits | None = None, side_map: dict[str, str] | None = None, cloud_files: str = "read",
                 recheck_s: float | None = None,
                 clock: Callable[[], float] = time.time) -> None:
        self._provider, self._state_dir, self._clock, self._rescan_s = folder_provider, state_dir, clock, rescan_s
        self._settings = WorkerSettings(settle_s, compute_sha256, max_appearances, limits or ReaderLimits(), side_map,
                                       RECHECK_S if recheck_s is None else recheck_s, cloud_files)
        self._worker: IndexWorker | None = None
        self._thread: threading.Thread | None = None
        self._retired: list[tuple[IndexWorker, threading.Thread | None]] = []
        self._last_cycle = float("-inf")
        self._config_warning: Warning_ | None = None

    def _retire(self) -> None:
        if self._worker is not None:
            self._worker.stop_event.set()
            self._retired.append((self._worker, self._thread))
        self._worker, self._thread = None, None
        self._retired = [(w, t) for w, t in self._retired if t is not None and t.is_alive()]

    def _sync_folder(self) -> None:
        folder, enabled = self._provider()
        self._config_warning = None
        if not enabled:
            return self._retire()
        if folder is None:
            self._retire()
            self._config_warning = Warning_("TACVIEW_FOLDER_MISSING", "No Tacview folder configured")
            return
        if self._worker is None or self._worker.folder != folder:
            self._retire()
            self._worker = IndexWorker(folder, IndexRecord(self._state_dir, folder), self._settings, self._clock)
            self._last_cycle = float("-inf")

    def poll(self) -> list[Message]:
        self._sync_folder()
        worker = self._worker
        if worker is None:
            return []
        messages = worker.drain()
        worker.record.save()
        running = self._thread is not None and self._thread.is_alive()
        now = self._clock()
        if not running and now - self._last_cycle >= self._rescan_s:
            self._last_cycle = now
            self._thread = threading.Thread(target=worker.run_cycle, name="fox3-tacview", daemon=True)
            self._thread.start()
        return messages

    def warnings(self) -> list[Warning_]:
        if self._config_warning is not None:
            return [self._config_warning]
        return self._worker.warnings() if self._worker is not None else []

    def stop(self, timeout: float = 10.0) -> None:
        """Signal the worker (checked every 256 time frames) and join it. Safe to call repeatedly."""
        self._retire()
        for worker, thread in self._retired:
            worker.stop_event.set()
            if thread is not None:
                thread.join(timeout)
            worker.record.save()
        self._retired = []
