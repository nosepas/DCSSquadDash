from __future__ import annotations

import os
from pathlib import Path

import pytest
from foothold_samples import IDENTITY_STATS, full_file, write_saves

from fox3_agent.sources.base import Message
from fox3_agent.sources.foothold import FootholdSource
from fox3_central.core.validation import Validators

SCHEMAS = Path(__file__).resolve().parents[3] / "contracts" / "schemas"


def codes(src: FootholdSource) -> list[str]:
    return [w.code for w in src.warnings()]


def bump(path: Path, offset: int = 10) -> None:
    st = path.stat()
    os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + offset * 1_000_000_000))


def test_first_poll_emits_valid_message(tmp_path):
    path = write_saves(tmp_path, full_file())
    src = FootholdSource(path.parent)
    msgs = src.poll()
    assert len(msgs) == 1 and isinstance(msgs[0], Message) and msgs[0].kind == "foothold_state"
    assert Validators(SCHEMAS).errors("foothold_state", msgs[0].payload) == []
    assert src.name == "foothold" and src.warnings() == []
    assert src.last_state() is msgs[0].payload
    assert src.positions()[0]["name"] == "APOLLO | Tomy10"


def test_unchanged_file_is_not_resent(tmp_path):
    path = write_saves(tmp_path, full_file())
    src = FootholdSource(path.parent)
    assert src.poll() and src.poll() == [] and src.poll() == []


def test_touched_but_identical_content_is_deduped(tmp_path):
    path = write_saves(tmp_path, full_file())
    src = FootholdSource(path.parent)
    assert src.poll()
    bump(path)
    assert src.poll() == []
    assert src.last_state() is not None


def test_changed_content_is_resent(tmp_path):
    path = write_saves(tmp_path, full_file())
    src = FootholdSource(path.parent)
    src.poll()
    path.write_text(full_file(IDENTITY_STATS), "utf-8")
    msgs = src.poll()
    assert len(msgs) == 1 and msgs[0].payload["player_stats"][0]["identifier"] == "id-aaa"


def test_partial_file_keeps_last_state_and_recovers(tmp_path):
    good = full_file()
    path = write_saves(tmp_path, good)
    src = FootholdSource(path.parent)
    first = src.poll()[0].payload
    path.write_text(good[: len(good) // 2], "utf-8")  # the game is mid-write
    assert src.poll() == []
    assert codes(src) == ["FOOTHOLD_FILE_INVALID"]
    assert src.last_state() is first
    assert codes(src) == ["FOOTHOLD_FILE_INVALID"]  # reported until the file changes
    assert src.poll() == [] and codes(src) == ["FOOTHOLD_FILE_INVALID"]
    path.write_text(good.replace("14524.5", "99"), "utf-8")
    msgs = src.poll()
    assert len(msgs) == 1 and msgs[0].payload["accounts"]["blue"] == 99 and src.warnings() == []


def test_invalid_first_file_has_no_state(tmp_path):
    path = write_saves(tmp_path, "zonePersistance = {}\nzonePersistance['zones'] = {")
    src = FootholdSource(path.parent)
    assert src.poll() == [] and src.last_state() is None and codes(src) == ["FOOTHOLD_FILE_INVALID"]


def test_file_without_zones_is_invalid(tmp_path):
    src = FootholdSource(write_saves(tmp_path, "zonePersistance = {}\nzonePersistance['accounts'] = { 1, 2 }").parent)
    assert src.poll() == [] and codes(src) == ["FOOTHOLD_FILE_INVALID"]


def test_file_too_large_is_invalid(tmp_path):
    path = write_saves(tmp_path, full_file())
    src = FootholdSource(path.parent, max_bytes=100)
    assert src.poll() == [] and codes(src) == ["FOOTHOLD_FILE_INVALID"]


def test_folder_missing_and_file_missing(tmp_path):
    src = FootholdSource(tmp_path / "nope")
    assert src.poll() == [] and codes(src) == ["FOOTHOLD_FOLDER_MISSING"]
    (tmp_path / "empty").mkdir()
    src = FootholdSource(tmp_path / "empty")
    assert src.poll() == [] and codes(src) == ["FOOTHOLD_FILE_MISSING"]


def test_file_unreadable(tmp_path, monkeypatch):
    path = write_saves(tmp_path, full_file())
    src = FootholdSource(path.parent)

    def boom(self):
        raise PermissionError(13, "denied")

    monkeypatch.setattr(Path, "read_bytes", boom)
    assert src.poll() == [] and codes(src) == ["FOOTHOLD_FILE_UNREADABLE"]
    monkeypatch.undo()
    assert len(src.poll()) == 1 and src.warnings() == []


@pytest.mark.parametrize(("age_s", "stale"), [(10, False), (2000, True)])
def test_stale_warning(tmp_path, age_s, stale):
    path = write_saves(tmp_path, full_file())
    now = path.stat().st_mtime + age_s
    src = FootholdSource(path.parent, stale_after_s=900, clock=lambda: now)
    assert len(src.poll()) == 1
    assert ("FOOTHOLD_FILE_STALE" in codes(src)) is stale
    src.poll()
    assert ("FOOTHOLD_FILE_STALE" in codes(src)) is stale  # still reported while nothing changes


def test_no_stale_warning_without_snapshot(tmp_path):
    path = write_saves(tmp_path, "zonePersistance = {}")
    src = FootholdSource(path.parent, stale_after_s=1, clock=lambda: path.stat().st_mtime + 5000)
    src.poll()
    assert "FOOTHOLD_FILE_STALE" not in codes(src)


def test_uses_status_file(tmp_path):
    a = write_saves(tmp_path, full_file(), "Foothold_A.lua")
    write_saves(tmp_path, full_file(), "Foothold_B.lua")
    bump(a.parent / "Foothold_B.lua", 100)
    (a.parent / "foothold.status").write_text("Foothold_A.lua", "utf-8")
    msg = FootholdSource(a.parent).poll()[0]
    assert msg.payload["source_file"] == "Foothold_A.lua" and msg.payload["mission_name"] == "A"
