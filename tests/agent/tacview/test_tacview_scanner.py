import json

import pytest
from tacview_samples import age, write_plain

from fox3_agent.sources.tacview.record import IndexRecord
from fox3_agent.sources.tacview.scanner import FolderMissingError, scan_folder, select_pending

NOW = 1_800_000_000.0


def make(tmp_path, rel, old=1000, text="x"):
    p = write_plain(tmp_path / rel, text)
    age(p, old, NOW)
    return p


def test_scan_recursive_acmi_only_and_relative(tmp_path):
    make(tmp_path, "a.acmi")
    make(tmp_path, "sub/b.ACMI")
    make(tmp_path, "sub/c.txt")
    files = scan_folder(tmp_path)
    assert sorted(f.rel for f in files) == ["a.acmi", "sub/b.ACMI"]


def test_depth_bounded(tmp_path):
    make(tmp_path, "a/b/c/d.acmi")
    assert scan_folder(tmp_path, max_depth=1) == []
    assert len(scan_folder(tmp_path, max_depth=3)) == 1


def test_missing_folder(tmp_path):
    with pytest.raises(FolderMissingError):
        scan_folder(tmp_path / "nope")


def test_symlink_escaping_skipped(tmp_path):
    outside = tmp_path / "outside"
    root = tmp_path / "root"
    root.mkdir()
    make(outside, "secret.acmi")
    make(root, "ok.acmi")
    try:
        (root / "link.acmi").symlink_to(outside / "secret.acmi")
        (root / "dirlink").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        pytest.skip("symlinks not permitted on this system")
    assert [f.rel for f in scan_folder(root)] == ["ok.acmi"]


def test_settle_rule_and_oldest_first(tmp_path):
    make(tmp_path, "new.acmi", old=10)
    make(tmp_path, "mid.acmi", old=500)
    make(tmp_path, "old.acmi", old=900)
    rec = IndexRecord(tmp_path / "state", tmp_path)
    pending, unsettled = select_pending(scan_folder(tmp_path), rec, NOW, 120)
    assert [f.rel for f in pending] == ["old.acmi", "mid.acmi"] and unsettled == 1


def test_change_detection(tmp_path):
    p = make(tmp_path, "a.acmi")
    rec = IndexRecord(tmp_path / "state", tmp_path)
    f = scan_folder(tmp_path)[0]
    rec.mark(f.rel, f.size, f.mtime_ns)
    assert select_pending(scan_folder(tmp_path), rec, NOW, 120)[0] == []
    p.write_text("longer content")
    age(p, 1000, NOW)
    assert len(select_pending(scan_folder(tmp_path), rec, NOW, 120)[0]) == 1      # size changed
    f2 = scan_folder(tmp_path)[0]
    rec.mark(f2.rel, f2.size, f2.mtime_ns)
    age(p, 2000, NOW)
    assert len(select_pending(scan_folder(tmp_path), rec, NOW, 120)[0]) == 1      # mtime changed


def test_record_persists_and_is_per_folder(tmp_path):
    state = tmp_path / "state"
    rec = IndexRecord(state, tmp_path / "f1")
    rec.mark("a.acmi", 5, 7)
    rec.save()
    assert IndexRecord(state, tmp_path / "f1").is_current("a.acmi", 5, 7)
    assert not IndexRecord(state, tmp_path / "f2").is_current("a.acmi", 5, 7)
    assert list(state.glob("*.tmp")) == []


@pytest.mark.parametrize("garbage", ["{not json", "[]", '{"files": {"a": "x"}}', '{"files": 3}', ""])
def test_corrupted_record_starts_over(tmp_path, garbage):
    state = tmp_path / "state"
    rec = IndexRecord(state, tmp_path / "f")
    rec.mark("a.acmi", 1, 2)
    rec.save()
    next(state.glob("tacview_index_*.json")).write_text(garbage)
    fresh = IndexRecord(state, tmp_path / "f")
    assert not fresh.is_current("a.acmi", 1, 2)
    fresh.mark("b.acmi", 1, 2)
    fresh.save()
    assert json.loads(next(state.glob("tacview_index_*.json")).read_text())["files"] == {"b.acmi": [1, 2]}


def test_forget_missing(tmp_path):
    rec = IndexRecord(tmp_path / "s", tmp_path)
    rec.mark("a", 1, 1)
    rec.mark("b", 1, 1)
    rec.forget_missing({"a"})
    assert rec.is_current("a", 1, 1) and not rec.is_current("b", 1, 1)
