"""Helpers for recordings that live in a cloud-synced folder (Google Drive for desktop, OneDrive...).

Only plain `os.stat` data is used; nothing here talks to any cloud API. Behaviour on a real Drive for desktop volume is
unverified (no such PC was available when this was written).
"""
from __future__ import annotations

import os
from collections.abc import Callable, Iterable
from pathlib import Path

# FILE_ATTRIBUTE_OFFLINE, FILE_ATTRIBUTE_RECALL_ON_OPEN, FILE_ATTRIBUTE_RECALL_ON_DATA_ACCESS
ONLINE_ONLY_MASK = 0x1000 | 0x40000 | 0x400000
TRANSIENT_SUFFIXES = (".tmp", ".crdownload", ".part", ".gdownload")
TRANSIENT_PREFIXES = (".~lock",)
CLOUD_CHOICES = ("read", "skip")
_DRIVE_NAMES = ("google drive", "my drive")

DRIVE_HINT = ("If this is a Google Drive for desktop folder, the agent must run as the Windows user that is signed in to Drive: "
              "install it again while logged in as that user.")


def is_online_only(file_attributes: int) -> bool:
    """True when Windows marks the file as a not-yet-downloaded cloud placeholder."""
    return bool(file_attributes & ONLINE_ONLY_MASK)


def is_transient_name(name: str) -> bool:
    """Temporary names written by Drive / browsers / editors while a file is being copied."""
    low = name.lower()
    return low.endswith(TRANSIENT_SUFFIXES) or low.startswith(TRANSIENT_PREFIXES)


class SizeTracker:
    """Remembers the size seen in the previous scan: a file is 'stable' only when two consecutive scans agree."""

    def __init__(self) -> None:
        self._last: dict[str, int] = {}

    def observe(self, sizes: Iterable[tuple[str, int]]) -> set[str]:
        current = dict(sizes)
        stable = {rel for rel, size in current.items() if self._last.get(rel) == size}
        self._last = current
        return stable


def looks_like_google_drive(folder: Path | str) -> bool:
    low = str(folder).replace("\\", "/").lower()
    return any(name in low for name in _DRIVE_NAMES)


def _drive_ready(folder: Path) -> bool:
    return bool(folder.drive) and os.path.isdir(folder.drive + "\\")


def folder_missing_message(folder: Path, drive_ready: Callable[[Path], bool] = _drive_ready) -> str:
    """Warning text for a Tacview folder that does not exist (never contains the path itself)."""
    text = "Tacview folder does not exist."
    if looks_like_google_drive(folder) or (folder.drive and not drive_ready(folder)):
        text += " " + DRIVE_HINT
    return text
