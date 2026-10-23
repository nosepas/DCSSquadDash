"""Folder scan: which `.acmi` files exist and which of them need (re)indexing."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .cloud import is_online_only, is_transient_name
from .record import IndexRecord

MAX_DEPTH = 8


class FolderMissingError(Exception):
    pass


class FolderUnreadableError(Exception):
    pass


@dataclass(frozen=True)
class AcmiFile:
    rel: str            # relative path, forward slashes
    path: Path
    size: int
    mtime_ns: int
    attrs: int = 0      # Windows st_file_attributes (0 where unavailable)

    @property
    def online_only(self) -> bool:
        return is_online_only(self.attrs)


def _walk(root: Path, directory: Path, depth: int, max_depth: int, out: list[AcmiFile]) -> None:
    try:
        entries = list(os.scandir(directory))
    except OSError:
        if directory == root:
            raise
        return
    for entry in entries:
        try:
            if entry.is_symlink():
                if entry.is_dir() or not Path(entry.path).resolve().is_relative_to(root):
                    continue                    # never follow directory links; file links must stay inside
            elif entry.is_dir():
                if depth < max_depth:
                    _walk(root, Path(entry.path), depth + 1, max_depth, out)
                continue
            if entry.name.lower().endswith(".acmi") and not is_transient_name(entry.name) and entry.is_file():
                st = entry.stat()
                rel = Path(entry.path).relative_to(root).as_posix()
                out.append(AcmiFile(rel, Path(entry.path), st.st_size, st.st_mtime_ns, getattr(st, "st_file_attributes", 0)))
        except OSError:
            continue                            # vanished or unreadable entry


def scan_folder(folder: Path, max_depth: int = MAX_DEPTH) -> list[AcmiFile]:
    if not folder.is_dir():
        raise FolderMissingError("Tacview folder does not exist")
    root = folder.resolve()
    out: list[AcmiFile] = []
    try:
        _walk(root, root, 0, max_depth, out)
    except OSError as exc:
        raise FolderUnreadableError("Tacview folder cannot be read") from exc
    return out


def select_pending(files: list[AcmiFile], record: IndexRecord, now_s: float, settle_s: float,
                   stable: set[str] | None = None) -> tuple[list[AcmiFile], int]:
    """Files to index (oldest first) and the number of files skipped because they may still be written.

    A file is settled when its mtime is older than `settle_s` and, if `stable` is given, its size was the same in the
    previous scan too (a cloud client may create the file before it is completely copied)."""
    pending: list[AcmiFile] = []
    unsettled = 0
    for f in files:
        if record.is_current(f.rel, f.size, f.mtime_ns):
            continue
        if now_s - f.mtime_ns / 1e9 < settle_s or (stable is not None and f.rel not in stable):
            unsettled += 1
            continue
        pending.append(f)
    pending.sort(key=lambda f: (f.mtime_ns, f.rel))
    return pending, unsettled
