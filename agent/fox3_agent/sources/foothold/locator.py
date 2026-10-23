"""Find the active Foothold persistence file from `foothold.status` (or, failing that, by name in the folder)."""
from __future__ import annotations

from pathlib import Path

STATUS_NAME = "foothold.status"


def _read_status(saves_dir: Path) -> str | None:
    try:
        raw = (saves_dir / STATUS_NAME).read_text("utf-8-sig", errors="replace")
    except OSError:
        return None
    for line in raw.splitlines():
        line = line.strip().strip("\"'").strip()
        if line:
            return line
    return None


def _candidates(saves_dir: Path, entry: str) -> list[Path]:
    path = Path(entry.replace("\\", "/"))
    absolute = path.is_absolute() or (len(entry) > 1 and entry[1] == ":")
    # relative: try the saves dir, then its parents (Saves -> Missions -> server folder -> Saved Games)
    out = [path] if absolute else [base / path for base in (saves_dir, *list(saves_dir.parents)[:4])]
    out.append(saves_dir / path.name)  # last resort: same file name inside the saves dir
    return out


def _is_persistence(p: Path) -> bool:
    return p.suffix.lower() == ".lua" and p.is_file()


def newest_persistence(saves_dir: Path) -> Path | None:
    best: tuple[int, Path] | None = None
    try:
        for p in saves_dir.iterdir():
            n = p.name.lower()
            if n.startswith("foothold") and n.endswith(".lua") and "ctld" not in n and p.is_file():
                mtime = p.stat().st_mtime_ns
                if best is None or mtime > best[0]:
                    best = (mtime, p)
    except OSError:
        return None
    return best[1] if best else None


def locate_persistence_file(saves_dir: Path) -> Path | None:
    entry = _read_status(saves_dir)
    if entry:
        for cand in _candidates(saves_dir, entry):
            try:
                if _is_persistence(cand):
                    return cand
            except OSError:
                continue
    return newest_persistence(saves_dir)


def status_entry(saves_dir: Path) -> str | None:
    """Text of the first non-empty line of `foothold.status` (None when the file is absent or empty)."""
    return _read_status(saves_dir)
