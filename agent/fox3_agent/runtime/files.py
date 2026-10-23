"""Which local files the agent may ever send: only `.acmi` recordings inside the configured Tacview folder."""
from __future__ import annotations

from pathlib import Path, PurePosixPath


def safe_recording_path(folder: Path, relative_path: str) -> Path | None:
    """Resolve `relative_path` (as announced in the index) under `folder`; None if it is unsafe or not a recording.

    Rejects absolute paths, drive letters, `..`, and anything that resolves (symlinks included) outside the folder.
    """
    rel = PurePosixPath(relative_path.replace("\\", "/"))
    if rel.is_absolute() or not rel.parts or any(p in ("..", "") or ":" in p for p in rel.parts):
        return None
    if not rel.name.lower().endswith(".acmi"):
        return None
    try:
        root = folder.resolve(strict=True)
        candidate = (root / Path(*rel.parts)).resolve(strict=True)
    except OSError:
        return None
    if not candidate.is_relative_to(root) or not candidate.is_file():
        return None
    return candidate
