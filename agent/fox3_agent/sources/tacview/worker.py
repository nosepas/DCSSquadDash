"""Background worker: one scan cycle = scan folder, then index the pending files one at a time, oldest first."""
from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from ..base import Message, Warning_
from .acmi_reader import ReaderLimits
from .cloud import SizeTracker, folder_missing_message
from .errors import AcmiCancelledError, AcmiUnsupportedError
from .indexer import index_file
from .payload import MAX_APPEARANCES, build_payload, file_sha256
from .record import IndexRecord
from .scanner import AcmiFile, FolderMissingError, FolderUnreadableError, scan_folder, select_pending


@dataclass(frozen=True)
class WorkerSettings:
    settle_s: float = 120.0
    compute_sha256: bool = False
    max_appearances: int = MAX_APPEARANCES
    limits: ReaderLimits = ReaderLimits()
    side_map: dict[str, str] | None = None
    recheck_s: float = 3.0          # pause before the second size observation of a new file (0 = only compare across scans)
    cloud_files: str = "read"      # "read": index online-only files (downloads them) | "skip": leave them alone


class IndexWorker:
    """State for one configured folder. `run_cycle` executes in a thread owned by TacviewSource."""

    def __init__(self, folder: Path, record: IndexRecord, settings: WorkerSettings, clock: Callable[[], float]) -> None:
        self.folder, self.record, self.settings, self._clock = folder, record, settings, clock
        self.stop_event = threading.Event()
        self._lock = threading.Lock()
        self._results: list[Message] = []
        self._warns: dict[str, Warning_] = {}       # folder-level warnings
        self._file_warns: dict[str, Warning_] = {}  # per-file warnings, keyed by relative path
        self._failed: dict[str, tuple[int, int]] = {}
        self._info: Warning_ | None = None          # informational (cloud files)
        self._sizes = SizeTracker()
        self.pending = 0

    def drain(self) -> list[Message]:
        with self._lock:
            out, self._results = self._results, []
        return out

    def warnings(self) -> list[Warning_]:
        with self._lock:
            warns = [*self._warns.values(), *self._file_warns.values(), *([self._info] if self._info else [])]
            if self.pending:
                warns.append(Warning_("TACVIEW_INDEXING", f"Indexing Tacview recordings: {self.pending} file(s) pending"))
            return warns

    def _set_folder_warning(self, code: str | None, message: str = "") -> None:
        with self._lock:
            self._warns = {code: Warning_(code, message)} if code else {}

    def run_cycle(self) -> None:
        try:
            files = scan_folder(self.folder)
        except FolderMissingError:
            return self._set_folder_warning("TACVIEW_FOLDER_MISSING", folder_missing_message(self.folder))
        except FolderUnreadableError:
            return self._set_folder_warning("TACVIEW_FOLDER_UNREADABLE", "Tacview folder cannot be read")
        self._set_folder_warning(None)
        present = {f.rel for f in files}
        self.record.forget_missing(present)
        with self._lock:
            self._file_warns = {k: v for k, v in self._file_warns.items() if k.split("|")[0] in present}
            self._failed = {k: v for k, v in self._failed.items() if k in present}
        stable = self._sizes.observe((f.rel, f.size) for f in files)
        pending, _ = select_pending(files, self.record, self._clock(), self.settings.settle_s, stable)
        if self.settings.recheck_s > 0 and self._waiting_for_size(files, stable):
            # first sight of these sizes: look again shortly instead of waiting a whole rescan interval
            if self.stop_event.wait(self.settings.recheck_s):
                return
            try:
                files = scan_folder(self.folder)
            except (FolderMissingError, FolderUnreadableError):
                return
            stable = self._sizes.observe((f.rel, f.size) for f in files)
            pending, _ = select_pending(files, self.record, self._clock(), self.settings.settle_s, stable)
        pending = [f for f in pending if self._failed.get(f.rel) != (f.size, f.mtime_ns)]
        pending = self._apply_cloud_policy(pending)
        with self._lock:
            self.pending = len(pending)
        try:
            for f in pending:
                if self.stop_event.is_set():
                    break
                self._index_one(f)
                with self._lock:
                    self.pending -= 1
        finally:
            with self._lock:
                self.pending = 0

    def _waiting_for_size(self, files: list[AcmiFile], stable: set[str]) -> bool:
        """True when some file is old enough and not yet indexed, and only lacks a second equal-size observation."""
        now, settle = self._clock(), self.settings.settle_s
        return any(f.rel not in stable and now - f.mtime_ns / 1e9 >= settle and not self.record.is_current(f.rel, f.size, f.mtime_ns)
                   for f in files)

    def _apply_cloud_policy(self, pending: list[AcmiFile]) -> list[AcmiFile]:
        """Online-only files are still indexed one at a time (the read downloads them); `skip` leaves them out."""
        cloud = [f for f in pending if f.online_only]
        skip = self.settings.cloud_files == "skip"
        text = None
        if cloud:
            text = (f"{len(cloud)} recordings are online-only and skipped (cloud_files = skip)" if skip
                    else f"{len(cloud)} recordings are online-only; reading them downloads them first")
        with self._lock:
            self._info = Warning_("TACVIEW_CLOUD_FILES", text) if text else None
        return [f for f in pending if not (skip and f.online_only)]

    def _fail(self, f: AcmiFile, code: str, text: str) -> None:
        with self._lock:
            self._failed[f.rel] = (f.size, f.mtime_ns)
            self._file_warns[f.rel] = Warning_(code, f"{Path(f.rel).name}: {text}")

    def _index_one(self, f: AcmiFile) -> None:
        try:
            idx = index_file(f.path, limits=self.settings.limits, side_map=self.settings.side_map, cancel=self.stop_event.is_set)
            sha = file_sha256(f.path) if self.settings.compute_sha256 else None
        except AcmiCancelledError:
            return
        except AcmiUnsupportedError as exc:
            return self._fail(f, "TACVIEW_FORMAT_UNSUPPORTED", str(exc))
        except Exception as exc:  # noqa: BLE001 - worker boundary: one bad file must not stop the others
            return self._fail(f, "TACVIEW_FILE_FAILED", f"{type(exc).__name__}: {exc}"[:200])
        built = build_payload(idx, f.rel, f.size, f.mtime_ns, sha256=sha, max_appearances=self.settings.max_appearances)
        with self._lock:
            self._file_warns.pop(f.rel, None)
            if built.capped:
                self._file_warns[f.rel] = Warning_("TACVIEW_APPEARANCES_CAPPED",
                                                   f"{Path(f.rel).name}: appearances capped at {self.settings.max_appearances}")
            self._results.append(Message("tacview_index", built.payload))
        self.record.mark(f.rel, f.size, f.mtime_ns)
