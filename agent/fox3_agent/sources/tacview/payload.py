"""TacviewIndex + file facts -> `tacview_index` contract payload (contracts/schemas/tacview_index.json)."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from .model import TacviewIndex

INDEX_VERSION = 1
MAX_APPEARANCES = 5000


@dataclass(frozen=True)
class BuiltPayload:
    payload: dict
    capped: bool            # True if appearances were cut to max_appearances


def file_sha256(path: Path) -> str:
    """Streamed SHA-256 of the file as stored. Cost: one extra full read (I/O bound, ~1 GB/s on SSD); off by default."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(1 << 20):
            h.update(chunk)
    return h.hexdigest()


def utc_from_ns(mtime_ns: int) -> str:
    return datetime.fromtimestamp(mtime_ns / 1e9, tz=UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def build_payload(index: TacviewIndex, relative_path: str, size_bytes: int, mtime_ns: int, *,
                  sha256: str | None = None, max_appearances: int = MAX_APPEARANCES) -> BuiltPayload:
    rel = relative_path.replace("\\", "/").lstrip("/")
    apps = sorted(index.appearances, key=lambda a: (a.first_offset_s, a.pilot))
    capped = len(apps) > max_appearances
    return BuiltPayload({
        "index_version": INDEX_VERSION,
        "file": {
            "relative_path": rel,
            "size_bytes": size_bytes,
            "mtime": utc_from_ns(mtime_ns),
            "sha256": sha256,
            "reference_time": index.reference_time,
            "duration_s": None if index.duration_s is None else round(index.duration_s, 3),
            "title": index.title,
            "data_source": index.data_source,
            "complete": index.complete,
        },
        "appearances": [{
            "pilot": a.pilot,
            "aircraft": a.aircraft,
            "coalition": a.coalition,
            "group": a.group,
            "object_id": a.object_id,
            "first_offset_s": round(a.first_offset_s, 3),
            "last_offset_s": round(a.last_offset_s, 3),
        } for a in apps[:max_appearances]],
    }, capped)
