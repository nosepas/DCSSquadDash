"""Locate DCS Saved Games, Foothold saves, DCSServerBot and Tacview folders on a PC. Read-only, no side effects."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .sources.tacview.cloud import looks_like_google_drive

DRIVE_NOTE = "Google Drive (needs the agent service to run as your Windows user; Mirror mode recommended)"


@dataclass(frozen=True)
class Detected:
    path: Path
    note: str = ""


@dataclass
class Detection:
    saved_games: list[Detected] = field(default_factory=list)
    foothold_saves: list[Detected] = field(default_factory=list)
    dcsserverbot: list[Detected] = field(default_factory=list)
    tacview: list[Detected] = field(default_factory=list)


def _is_dir(p: Path) -> bool:
    try:
        return p.is_dir()
    except OSError:
        return False


def _tacview_note(folder: Path) -> str:
    note = f"{sum(1 for _ in folder.glob('*.acmi'))} .acmi files"
    return f"{note}; {DRIVE_NOTE}" if looks_like_google_drive(folder) else note


def _drive_roots(home: Path) -> list[Path]:
    """Where Google Drive for desktop usually appears: a mirrored `Google Drive` folder or a `X:/My Drive` virtual drive."""
    roots = [home / "Google Drive"]
    roots += [Path(f"{letter}:/My Drive") for letter in "DEFGHIJKLMNOPQRSTUVWXYZ"]
    return [r for r in roots if _is_dir(r)]


def _cloud_tacview(roots: list[Path]) -> list[Detected]:
    """Folders named Tacview* directly inside a Google Drive root."""
    found: list[Detected] = []
    for root in roots:
        try:
            children = sorted(p for p in root.iterdir() if p.name.lower().startswith("tacview") and _is_dir(p))
        except OSError:
            continue
        found += [Detected(c, _tacview_note(c)) for c in children]
    return found


def detect(home: Path | None = None, extra_roots: tuple[Path, ...] = ()) -> Detection:
    explicit_home, home = home, home or Path.home()
    out = Detection()
    sg = home / "Saved Games"
    for d in sorted(sg.glob("DCS*")) if _is_dir(sg) else []:
        if _is_dir(d):
            out.saved_games.append(Detected(d))
            saves = d / "Missions" / "Saves"
            if _is_dir(saves):
                has = (saves / "foothold.status").exists() or any(saves.glob("foothold*.lua"))
                out.foothold_saves.append(Detected(saves, "Foothold files found" if has else "folder exists, no Foothold file yet"))
    roots = (home, home / "Documents", Path("C:/"), Path("D:/"), *extra_roots)
    for root in roots:
        for name in ("DCSServerBot", "DCSServerBot-master"):
            c = root / name
            if _is_dir(c):
                out.dcsserverbot.append(Detected(c, "has config/" if _is_dir(c / "config") else "folder name match only"))
    for tv in (home / "Documents" / "Tacview", home / "OneDrive" / "Documents" / "Tacview"):
        if _is_dir(tv):
            out.tacview.append(Detected(tv, _tacview_note(tv)))
    out.tacview += _cloud_tacview(_drive_roots(home) if explicit_home is None else [home / "Google Drive"])
    return out
