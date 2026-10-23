import time

import pytest
from tacview_samples import BASIC, age, write_plain, write_zip
from test_tacview_payload import SCHEMAS

from fox3_agent.sources.tacview import TacviewSource
from fox3_central.core.validation import Validators

NOW = 1_800_000_000.0


class Cfg:
    def __init__(self, folder, enabled=True):
        self.folder, self.enabled = folder, enabled

    def __call__(self):
        return self.folder, self.enabled


def drain(src, want=1, timeout=10.0):
    out = []
    end = time.time() + timeout
    while len(out) < want and time.time() < end:
        out += src.poll()
        time.sleep(0.01)
    return out


def codes(src):
    return {w.code for w in src.warnings()}


@pytest.fixture
def folder(tmp_path):
    f = tmp_path / "tacview"
    f.mkdir()
    return f


def mk(folder, rel, text=BASIC, old=1000, zipped=False):
    p = (write_zip if zipped else write_plain)(folder / rel, text)
    age(p, old, NOW)
    return p


def source(folder, tmp_path, **kw):
    return TacviewSource(Cfg(folder), tmp_path / "state", settle_s=120, rescan_s=0, clock=lambda: NOW, **kw)


def test_indexes_once_and_validates(folder, tmp_path):
    mk(folder, "a.acmi")
    mk(folder, "sub/b.zip.acmi", zipped=True)
    src = source(folder, tmp_path)
    msgs = drain(src, 2)
    assert {m.kind for m in msgs} == {"tacview_index"} and len(msgs) == 2
    assert sorted(m.payload["file"]["relative_path"] for m in msgs) == ["a.acmi", "sub/b.zip.acmi"]
    assert all(Validators(SCHEMAS).errors("tacview_index", m.payload) == [] for m in msgs)
    time.sleep(0.3)
    assert drain(src, 1, timeout=0.5) == []          # already indexed: nothing again
    src.stop()


def test_oldest_first(folder, tmp_path):
    mk(folder, "newer.acmi", old=500)
    mk(folder, "older.acmi", old=900)
    src = source(folder, tmp_path)
    msgs = drain(src, 2)
    assert [m.payload["file"]["relative_path"] for m in msgs] == ["older.acmi", "newer.acmi"]
    src.stop()


def test_unsettled_file_waits_then_indexes(folder, tmp_path):
    p = mk(folder, "a.acmi", old=5)
    now = [NOW]
    src = TacviewSource(Cfg(folder), tmp_path / "state", settle_s=120, rescan_s=0, clock=lambda: now[0])
    assert drain(src, 1, timeout=0.5) == []
    now[0] += 200
    assert len(drain(src, 1)) == 1 and p.exists()
    src.stop()


def test_poll_does_not_block(folder, tmp_path):
    for i in range(30):
        mk(folder, f"{i}.acmi")
    src = source(folder, tmp_path)
    t0 = time.perf_counter()
    src.poll()
    assert time.perf_counter() - t0 < 0.5
    src.stop()


def test_persistence_across_restart(folder, tmp_path):
    mk(folder, "a.acmi")
    src = source(folder, tmp_path)
    assert len(drain(src, 1)) == 1
    src.poll()
    src.stop()
    again = source(folder, tmp_path)
    assert drain(again, 1, timeout=0.6) == []
    again.stop()


def test_changed_file_reindexed(folder, tmp_path):
    p = mk(folder, "a.acmi")
    src = source(folder, tmp_path)
    assert len(drain(src, 1)) == 1
    time.sleep(0.2)
    write_plain(p, BASIC + "#99\n3000100,T=1\n")
    age(p, 900, NOW)
    msgs = drain(src, 1)
    assert msgs and msgs[0].payload["file"]["duration_s"] == 99
    src.stop()


def test_folder_change_rescans(folder, tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    mk(folder, "a.acmi")
    mk(other, "z.acmi")
    cfg = Cfg(folder)
    src = TacviewSource(cfg, tmp_path / "state", settle_s=120, rescan_s=0, clock=lambda: NOW)
    assert drain(src)[0].payload["file"]["relative_path"] == "a.acmi"
    cfg.folder = other
    assert drain(src)[0].payload["file"]["relative_path"] == "z.acmi"
    src.stop()


def test_disabled_and_unconfigured(folder, tmp_path):
    mk(folder, "a.acmi")
    cfg = Cfg(folder, enabled=False)
    src = TacviewSource(cfg, tmp_path / "state", rescan_s=0, clock=lambda: NOW)
    assert src.poll() == [] and src.warnings() == []
    cfg.enabled, cfg.folder = True, None
    src.poll()
    assert codes(src) == {"TACVIEW_FOLDER_MISSING"}
    src.stop()


def test_missing_folder_warning(tmp_path):
    src = source(tmp_path / "gone", tmp_path)
    src.poll()
    end = time.time() + 5
    while "TACVIEW_FOLDER_MISSING" not in codes(src) and time.time() < end:
        time.sleep(0.01)
    assert "TACVIEW_FOLDER_MISSING" in codes(src)
    src.stop()


def test_failed_file_warning_has_name_only(folder, tmp_path):
    mk(folder, "deep/broken.acmi", text="not an acmi\n")
    mk(folder, "good.acmi")
    src = source(folder, tmp_path)
    assert len(drain(src, 1)) == 1
    end = time.time() + 5
    while "TACVIEW_FILE_FAILED" not in codes(src) and time.time() < end:
        time.sleep(0.01)
    w = next(w for w in src.warnings() if w.code == "TACVIEW_FILE_FAILED")
    assert "broken.acmi" in w.message and str(folder) not in w.message and "deep" not in w.message
    src.stop()


def test_7z_unsupported_warning(folder, tmp_path):
    p = folder / "x.7z.acmi"
    p.write_bytes(bytes([0x37, 0x7A, 0xBC, 0xAF, 0x27, 0x1C]) + b"0" * 40)
    age(p, 1000, NOW)
    src = source(folder, tmp_path)
    end = time.time() + 5
    while "TACVIEW_FORMAT_UNSUPPORTED" not in codes(src) and time.time() < end:
        src.poll()
        time.sleep(0.01)
    assert "TACVIEW_FORMAT_UNSUPPORTED" in codes(src)
    src.stop()


def test_appearances_capped_warning(folder, tmp_path):
    body = ["#0"] + [f"{i + 1:x},Pilot=P{i}" for i in range(20)]
    from tacview_samples import acmi
    mk(folder, "a.acmi", text=acmi(*body))
    src = source(folder, tmp_path, max_appearances=5)
    msgs = drain(src)
    assert len(msgs[0].payload["appearances"]) == 5
    assert "TACVIEW_APPEARANCES_CAPPED" in codes(src)
    src.stop()


def test_indexing_info_and_stop_joins(folder, tmp_path):
    for i in range(3):
        mk(folder, f"{i}.acmi")
    src = source(folder, tmp_path)
    drain(src, 3)
    src.stop()
    assert not any(t.name == "fox3-tacview" and t.is_alive() for t in __import__("threading").enumerate())
    src.stop()          # idempotent
