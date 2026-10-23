from __future__ import annotations

import os
from pathlib import Path

from fox3_agent.sources.foothold.locator import locate_persistence_file


def make(tmp_path: Path) -> Path:
    saves = tmp_path / "Saved Games" / "srv" / "Missions" / "Saves"
    saves.mkdir(parents=True)
    return saves


def touch(path: Path, mtime: float | None = None) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("zonePersistance = {}", "utf-8")
    if mtime:
        os.utime(path, (mtime, mtime))
    return path


def test_absolute_path_in_status(tmp_path):
    saves = make(tmp_path)
    target = touch(tmp_path / "elsewhere" / "Foothold_X.lua")
    touch(saves / "foothold_old.lua")
    (saves / "foothold.status").write_text(str(target) + "\n", "utf-8")
    assert locate_persistence_file(saves) == target


def test_relative_to_saves_dir_and_to_parents(tmp_path):
    saves = make(tmp_path)
    a = touch(saves / "Foothold_A.lua", 1000)
    touch(saves / "Foothold_B.lua", 2000)
    (saves / "foothold.status").write_text("Foothold_A.lua", "utf-8")
    assert locate_persistence_file(saves) == a
    (saves / "foothold.status").write_text("Missions\\Saves\\Foothold_A.lua", "utf-8")  # relative to the server folder
    assert locate_persistence_file(saves).resolve() == a.resolve()


def test_quoted_bom_and_windows_separators(tmp_path):
    saves = make(tmp_path)
    a = touch(saves / "Foothold_A.lua")
    (saves / "foothold.status").write_bytes(b'\xef\xbb\xbf  "C:\\Gone\\Missions\\Saves\\Foothold_A.lua"  \r\n')
    assert locate_persistence_file(saves) == a  # absolute path missing here: falls back to the same name in the saves dir


def test_missing_status_falls_back_to_newest(tmp_path):
    saves = make(tmp_path)
    touch(saves / "Foothold_old.lua", 1000)
    new = touch(saves / "foothold_new.lua", 3000)
    touch(saves / "foothold_new_CTLD_FARPS.csv", 5000)
    touch(saves / "foothold_ctld_extra.lua", 9000)
    touch(saves / "unrelated.lua", 9000)
    assert locate_persistence_file(saves) == new


def test_status_pointing_to_missing_file_falls_back(tmp_path):
    saves = make(tmp_path)
    only = touch(saves / "foothold_only.lua")
    (saves / "foothold.status").write_text("nope.lua", "utf-8")
    assert locate_persistence_file(saves) == only


def test_status_must_point_to_lua(tmp_path):
    saves = make(tmp_path)
    csv = touch(saves / "Foothold_A_CTLD_FARPS.csv")
    (saves / "foothold.status").write_text(str(csv), "utf-8")
    assert locate_persistence_file(saves) is None


def test_nothing_found(tmp_path):
    assert locate_persistence_file(make(tmp_path)) is None
    assert locate_persistence_file(tmp_path / "missing") is None
