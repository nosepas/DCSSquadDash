import sys
from pathlib import Path

import pytest
from tacview_samples import BASIC, age, write_plain

from fox3_agent.config import ConfigError, from_mapping
from fox3_agent.detect import DRIVE_NOTE, detect
from fox3_agent.sources.tacview import TacviewSource
from fox3_agent.sources.tacview.cloud import (
    ONLINE_ONLY_MASK,
    SizeTracker,
    folder_missing_message,
    is_online_only,
    is_transient_name,
    looks_like_google_drive,
)
from fox3_agent.sources.tacview.record import IndexRecord
from fox3_agent.sources.tacview.scanner import AcmiFile, scan_folder, select_pending

NOW = 1_800_000_000.0


class Cfg:
    def __init__(self, folder):
        self.folder = folder

    def __call__(self):
        return self.folder, True


def make(tmp_path, rel="a.acmi", old=1000, text=BASIC):
    p = write_plain(tmp_path / rel, text)
    age(p, old, NOW)
    return p


def codes(src):
    return {w.code: w.message for w in src.warnings()}


def drain(src):
    out = []
    for _ in range(3):
        out += src.poll()
        if src._thread is not None:      # noqa: SLF001 - wait for the worker thread of this cycle
            src._thread.join(10)          # noqa: SLF001
    return out


# --- attributes ---------------------------------------------------------------------------------------------------------
@pytest.mark.parametrize("attr", [0x1000, 0x40000, 0x400000, 0x1000 | 0x20])
def test_online_only_attribute_bits(attr):
    assert is_online_only(attr)


@pytest.mark.parametrize("attr", [0, 0x20, 0x1, 0x2000, 0x20 | 0x80])
def test_normal_attributes_are_not_online_only(attr):
    assert not is_online_only(attr) and not attr & ONLINE_ONLY_MASK


def test_scan_reads_file_attributes_when_available(tmp_path):
    make(tmp_path)
    (f,) = scan_folder(tmp_path)
    assert f.attrs == getattr(f.path.stat(), "st_file_attributes", 0) and f.online_only is False


# --- transient names / stable size ----------------------------------------------------------------------------------------
@pytest.mark.parametrize("name", ["a.acmi.tmp", "x.crdownload", "y.part", "z.gdownload", ".~lock.a.acmi#", ".~lockx.acmi", "A.TMP"])
def test_transient_names(name):
    assert is_transient_name(name)


def test_normal_names_are_not_transient():
    assert not is_transient_name("Tacview-2024.zip.acmi") and not is_transient_name("lock.acmi")


def test_lock_file_with_acmi_name_is_not_scanned(tmp_path):
    make(tmp_path, ".~lockrec.acmi")
    make(tmp_path, "rec.acmi")
    assert [f.rel for f in scan_folder(tmp_path)] == ["rec.acmi"]


def test_size_tracker_needs_two_equal_scans():
    t = SizeTracker()
    assert t.observe([("a", 10)]) == set()
    assert t.observe([("a", 10), ("b", 5)]) == {"a"}
    assert t.observe([("a", 12), ("b", 5)]) == {"b"}        # a is still growing
    assert t.observe([]) == set()


def test_select_pending_waits_for_stable_size(tmp_path):
    make(tmp_path)
    rec = IndexRecord(tmp_path / "state", tmp_path)
    files = scan_folder(tmp_path)
    assert select_pending(files, rec, NOW, 120, stable=set()) == ([], 1)
    assert len(select_pending(files, rec, NOW, 120, stable={"a.acmi"})[0]) == 1
    assert len(select_pending(files, rec, NOW, 120)[0]) == 1              # legacy call without the size rule


def test_source_indexes_only_after_two_scans_with_same_size(tmp_path):
    folder = tmp_path / "rec"
    make(folder)
    src = TacviewSource(Cfg(folder), tmp_path / "state", settle_s=120, rescan_s=0, clock=lambda: NOW)
    assert drain_once(src) == []                     # first scan only records sizes
    assert any(m.kind == "tacview_index" for m in drain(src))
    src.stop()


def drain_once(src):
    out = src.poll()
    if src._thread is not None:                      # noqa: SLF001
        src._thread.join(10)                         # noqa: SLF001
    return out


def test_growing_file_is_not_indexed(tmp_path):
    folder = tmp_path / "rec"
    p = make(folder)
    src = TacviewSource(Cfg(folder), tmp_path / "state", settle_s=120, rescan_s=0, clock=lambda: NOW)
    sent = []
    for i in range(4):
        sent += drain_once(src)
        write_plain(p, BASIC + "#99\n" * (i + 1))      # size changes between every scan
        age(p, 1000, NOW)
    assert not [m for m in sent if m.kind == "tacview_index"]
    src.stop()


# --- cloud policy -----------------------------------------------------------------------------------------------------------
@pytest.fixture
def cloud(monkeypatch):
    """Pretend every scanned file is an online-only placeholder."""
    orig = scan_folder

    def fake(folder, *a, **k):
        return [AcmiFile(f.rel, f.path, f.size, f.mtime_ns, 0x400000) for f in orig(folder, *a, **k)]

    monkeypatch.setattr("fox3_agent.sources.tacview.worker.scan_folder", fake)


def test_cloud_files_read_indexes_one_by_one_and_warns(tmp_path, cloud):
    folder = tmp_path / "rec"
    make(folder, "a.acmi")
    make(folder, "b.acmi", old=900)
    src = TacviewSource(Cfg(folder), tmp_path / "state", settle_s=120, rescan_s=0, clock=lambda: NOW)
    msgs = drain(src)
    assert len([m for m in msgs if m.kind == "tacview_index"]) == 2
    src.poll()
    src._thread.join(10)       # noqa: SLF001
    assert "TACVIEW_CLOUD_FILES" not in codes(src)                      # nothing pending any more
    src.stop()


def test_cloud_warning_text_while_pending(tmp_path, cloud):
    folder = tmp_path / "rec"
    make(folder)
    src = TacviewSource(Cfg(folder), tmp_path / "state", settle_s=120, rescan_s=0, clock=lambda: NOW)
    drain_once(src)
    worker = src._worker                                                 # noqa: SLF001
    files = scan_folder(folder)
    worker._apply_cloud_policy([AcmiFile(f.rel, f.path, f.size, f.mtime_ns, 0x1000) for f in files])  # noqa: SLF001
    assert codes(src)["TACVIEW_CLOUD_FILES"] == "1 recordings are online-only; reading them downloads them first"
    src.stop()


def test_cloud_files_skip_leaves_them_unindexed(tmp_path, cloud):
    folder = tmp_path / "rec"
    make(folder)
    src = TacviewSource(Cfg(folder), tmp_path / "state", settle_s=120, rescan_s=0, clock=lambda: NOW, cloud_files="skip")
    msgs = drain(src) + drain(src)
    assert not [m for m in msgs if m.kind == "tacview_index"]
    assert "skipped" in codes(src)["TACVIEW_CLOUD_FILES"]
    src.stop()


def test_cloud_files_config_option():
    base = {"central": {"url": "https://x.example.org"}}
    assert from_mapping(base).tacview.cloud_files == "read"
    assert from_mapping({**base, "sources": {"tacview": {"cloud_files": "skip"}}}).tacview.cloud_files == "skip"
    for bad in ({"cloud_files": "download"}, {"folder": "G:/x"}, {"cloud_files": True}):
        with pytest.raises(ConfigError):
            from_mapping({**base, "sources": {"tacview": bad}})


def test_live_sources_passes_cloud_files(tmp_path):
    from fox3_agent.runtime.source_set import LiveSources
    from fox3_agent.runtime.state import AgentState

    cfg = from_mapping({"central": {"url": "https://x.example.org"}, "sources": {"tacview": {"cloud_files": "skip"}}}, tmp_path)
    live = LiveSources(cfg, AgentState(tmp_path))
    assert live.tacview._settings.cloud_files == "skip"        # noqa: SLF001
    live.stop()


# --- service-account trap / Google Drive recognition ---------------------------------------------------------------------------
@pytest.mark.skipif(sys.platform != "win32", reason="drive letters only exist on Windows")
def test_missing_folder_message_adds_service_hint_for_drive_paths():
    hint = "install it again while logged in as that user"
    assert hint in folder_missing_message(Path("G:/My Drive/Tacview"), drive_ready=lambda p: True)
    assert hint in folder_missing_message(Path("C:/Users/x/Google Drive/Tacview"), drive_ready=lambda p: True)
    assert hint in folder_missing_message(Path("Z:/anything"), drive_ready=lambda p: False)


def test_missing_folder_message_plain_when_drive_is_fine():
    assert folder_missing_message(Path("C:/Tacview"), drive_ready=lambda p: True) == "Tacview folder does not exist."


def test_worker_reports_hint_for_missing_drive_folder(tmp_path):
    src = TacviewSource(Cfg(Path("G:/My Drive/Tacview-nope")), tmp_path / "state", rescan_s=0, clock=lambda: NOW)
    drain_once(src)
    assert "logged in as that user" in codes(src)["TACVIEW_FOLDER_MISSING"]
    src.stop()


def test_looks_like_google_drive():
    assert looks_like_google_drive("G:\\My Drive\\Tacview") and looks_like_google_drive("C:/Users/a/Google Drive/x")
    assert not looks_like_google_drive("C:/Tacview")


def test_discover_annotates_google_drive_folders(tmp_path):
    tv = tmp_path / "Google Drive" / "Tacview"
    tv.mkdir(parents=True)
    (tv / "a.acmi").write_text("x")
    found = detect(tmp_path).tacview
    assert [d.path for d in found] == [tv] and DRIVE_NOTE in found[0].note and "1 .acmi files" in found[0].note
    assert len(found[0].note) <= 120            # fits the heartbeat `detected` note limit


def test_discover_leaves_plain_folders_unannotated(tmp_path):
    tv = tmp_path / "Documents" / "Tacview"
    tv.mkdir(parents=True)
    assert "Google" not in detect(tmp_path).tacview[0].note


def test_in_cycle_recheck_indexes_a_stable_new_file_without_waiting_a_rescan(tmp_path):
    folder = tmp_path / "rec"
    make(folder)
    src = TacviewSource(Cfg(folder), tmp_path / "state", settle_s=120, rescan_s=0, clock=lambda: NOW, recheck_s=0.05)
    assert [m.kind for m in drain_once(src)] == []         # worker thread started; result is drained by the next poll
    assert [m.kind for m in drain_once(src)] == ["tacview_index"]
    src.stop()


def test_in_cycle_recheck_still_rejects_a_growing_file(tmp_path):
    import threading
    import time

    folder = tmp_path / "rec"
    p = make(folder)
    src = TacviewSource(Cfg(folder), tmp_path / "state", settle_s=120, rescan_s=0, clock=lambda: NOW, recheck_s=0.5)

    def grow():
        time.sleep(0.15)
        write_plain(p, BASIC + "#99\n" * 5)
        age(p, 1000, NOW)

    threading.Thread(target=grow).start()
    sent = drain_once(src) + drain_once(src)
    assert [m for m in sent if m.kind == "tacview_index"] == []
    src.stop()
