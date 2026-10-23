"""Synthetic ACMI builders for the Tacview tests (no real recordings are available)."""
from __future__ import annotations

import os
import zipfile
from pathlib import Path

HEADER = "FileType=text/acmi/tacview\nFileVersion=2.2\n0,ReferenceTime=2024-05-01T18:00:00Z,Title=Test mission,DataSource=DCS 2.9\n"


def acmi(*body: str, header: str = HEADER) -> str:
    return header + "\n".join(body) + "\n"


BASIC = acmi(
    "#0", "3000100,T=1|2|3,Type=Air+FixedWing,Name=F-16C-52,Pilot=Viper 1-1,Color=Blue,Group=Uzi,Coalition=Allies",
    "3000200,T=1|2|3,Type=Air+Rotary,Name=AH-64D,Pilot=Apache,Coalition=Enemies,Color=Red",
    "4000300,T=1|2|3,Type=Ground+Vehicle,Name=T-72",
    "#10.5", "3000100,T=4|5|6", "4000300,T=2|2|2",
    "#30", "3000100,T=4|5|7", "-3000200",
    "#60.25", "3000100,T=9|9|9",
)


def write_plain(path: Path, text: str, encoding: str = "utf-8") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode(encoding))
    return path


def write_zip(path: Path, text: str, member: str = "Tacview-test.txt.acmi") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr(member, text.encode("utf-8"))
    return path


def age(path: Path, seconds_old: float, now: float) -> None:
    """Set the mtime of `path` to `now - seconds_old`."""
    t = now - seconds_old
    os.utime(path, (t, t))
