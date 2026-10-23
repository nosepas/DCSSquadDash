import io
import zipfile
from pathlib import Path

import pytest
from tacview_samples import write_plain, write_zip

from fox3_agent.sources.tacview.acmi_reader import ReaderLimits, ReadStats, _Bounded, iter_lines
from fox3_agent.sources.tacview.errors import AcmiFormatError, AcmiLimitError, AcmiUnsupportedError


def lines(path: Path, **kw) -> list[bytes]:
    return list(iter_lines(path, **kw))


def test_plain_lf(tmp_path):
    p = write_plain(tmp_path / "a.acmi", "a=1\nb=2\n")
    assert lines(p) == [b"a=1", b"b=2"]


def test_bom_and_crlf(tmp_path):
    p = write_plain(tmp_path / "a.acmi", "FileType=x\r\n0,a=1\r\n", encoding="utf-8-sig")
    assert lines(p) == [b"FileType=x", b"0,a=1"]


def test_continuation_lines(tmp_path):
    p = write_plain(tmp_path / "a.acmi", "0,Briefing=one\\\ntwo\\\nthree,x=1\nnext\n")
    assert lines(p) == [b"0,Briefing=one\ntwo\nthree,x=1", b"next"]


def test_double_backslash_is_not_continuation(tmp_path):
    p = write_plain(tmp_path / "a.acmi", "a\\\\\nb\n")
    assert lines(p) == [b"a\\\\", b"b"]


def test_zip_member_streamed(tmp_path):
    p = write_zip(tmp_path / "a.zip.acmi", "x=1\ny=2\n")
    assert lines(p) == [b"x=1", b"y=2"]


def test_zip_without_acmi_member(tmp_path):
    p = write_zip(tmp_path / "a.zip.acmi", "x\n", member="readme.md")
    with pytest.raises(AcmiFormatError):
        lines(p)


def test_zip_bomb_declared_size(tmp_path):
    p = write_zip(tmp_path / "a.zip.acmi", "x=1\n" * 10000)
    with pytest.raises(AcmiLimitError):
        lines(p, limits=ReaderLimits(max_uncompressed=1000))


def test_zip_bomb_ratio(tmp_path):
    p = write_zip(tmp_path / "a.zip.acmi", "A" * 2_000_000 + "\n")
    with pytest.raises(AcmiLimitError):
        lines(p, limits=ReaderLimits(max_ratio=50))


def test_byte_counter_stops_lying_header():
    """The counter enforces the limit on real bytes, independent of what the zip header declares."""
    raw = _Bounded(io.BytesIO(b"x" * 5000), 1000)
    with pytest.raises(AcmiLimitError):
        io.BufferedReader(raw).read()


def test_zip_too_many_entries(tmp_path):
    p = tmp_path / "a.zip.acmi"
    with zipfile.ZipFile(p, "w") as zf:
        for i in range(5):
            zf.writestr(f"f{i}.txt", "x\n")
    with pytest.raises(AcmiLimitError):
        lines(p, limits=ReaderLimits(max_entries=3))


def test_7z_unsupported(tmp_path):
    p = tmp_path / "a.7z.acmi"
    p.write_bytes(bytes([0x37, 0x7A, 0xBC, 0xAF, 0x27, 0x1C]) + b"\x00" * 50)
    with pytest.raises(AcmiUnsupportedError):
        lines(p)


def test_truncated_last_line_dropped_and_flagged(tmp_path):
    p = write_plain(tmp_path / "a.acmi", "a=1\nb=2\npartial")
    st = ReadStats()
    assert lines(p, stats=st) == [b"a=1", b"b=2"]
    assert st.truncated


def test_oversized_line_skipped(tmp_path):
    p = write_plain(tmp_path / "a.acmi", "a=1\n" + "x" * (2 << 20) + "\nb=2\n")
    st = ReadStats()
    assert lines(p, stats=st) == [b"a=1", b"b=2"]
    assert st.oversized == 1 and not st.truncated
