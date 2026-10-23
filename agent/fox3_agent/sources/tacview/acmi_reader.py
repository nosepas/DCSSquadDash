"""Bounded streaming line reader for ACMI recordings (plain text or zip container).

Never loads a whole file: lines are read through a buffered binary stream. Zip members are streamed through
`zipfile` (never extracted) behind a byte counter, so a lying zip header cannot defeat the size limit.
"""
from __future__ import annotations

import io
import zipfile
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import BinaryIO

from .errors import AcmiFormatError, AcmiLimitError, AcmiUnsupportedError

MAX_LINE = 1 << 20          # longer lines are skipped (and counted) instead of buffered
BUFFER = 1 << 20
_SEVEN_Z = bytes([0x37, 0x7A, 0xBC, 0xAF, 0x27, 0x1C])
_ZIP = b"PK\x03\x04"
_BOM = b"\xef\xbb\xbf"


@dataclass(frozen=True)
class ReaderLimits:
    max_uncompressed: int = 8 << 30     # bytes of text a zip member may expand to
    max_entries: int = 64               # zip entries allowed in the container
    max_ratio: float = 1000.0           # declared uncompressed / compressed size


@dataclass
class ReadStats:
    oversized: int = 0                  # lines longer than MAX_LINE that were skipped
    truncated: bool = False             # stream ended without a final newline (file still being written)


class _Bounded(io.RawIOBase):
    def __init__(self, raw: BinaryIO, limit: int) -> None:
        self._raw, self._limit, self._count = raw, limit, 0

    def readable(self) -> bool:
        return True

    def readinto(self, b) -> int:  # type: ignore[no-untyped-def]
        n = self._raw.readinto(b) or 0  # type: ignore[attr-defined]
        self._count += n
        if self._count > self._limit:
            raise AcmiLimitError("zip member exceeds the maximum uncompressed size")
        return n

    def close(self) -> None:
        self._raw.close()
        super().close()


def _pick_member(zf: zipfile.ZipFile, limits: ReaderLimits) -> zipfile.ZipInfo:
    infos = zf.infolist()
    if len(infos) > limits.max_entries:
        raise AcmiLimitError("too many entries in the zip container")
    for info in infos:
        if not info.is_dir() and info.filename.lower().endswith((".acmi", ".txt")):
            if info.file_size > limits.max_uncompressed:
                raise AcmiLimitError("zip member too large")
            if info.file_size > 1024 and info.file_size > limits.max_ratio * max(info.compress_size, 1):
                raise AcmiLimitError("suspicious compression ratio")
            return info
    raise AcmiFormatError("no .acmi/.txt member in the zip container")


@contextmanager
def open_stream(path: Path, limits: ReaderLimits) -> Iterator[BinaryIO]:
    with open(path, "rb") as probe:
        magic = probe.read(6)
    if magic.startswith(_SEVEN_Z):
        raise AcmiUnsupportedError("7z containers are not supported")
    if magic.startswith(_ZIP):
        try:
            zf = zipfile.ZipFile(path)
        except zipfile.BadZipFile as exc:
            raise AcmiFormatError("unreadable zip container") from exc
        with zf:
            info = _pick_member(zf, limits)
            with zf.open(info) as member:
                yield io.BufferedReader(_Bounded(member, limits.max_uncompressed), BUFFER)  # type: ignore[arg-type]
        return
    with open(path, "rb", buffering=BUFFER) as f:
        yield f


def _skip_rest(readline, stats: ReadStats) -> bool:  # type: ignore[no-untyped-def]
    """Discard the remainder of an oversized line; False if EOF came first."""
    stats.oversized += 1
    while True:
        chunk = readline(MAX_LINE)
        if not chunk:
            stats.truncated = True
            return False
        if chunk[-1] == 10:
            return True


def _strip_eol(raw: bytes) -> bytes:
    line = raw[:-1]
    return line[:-1] if line.endswith(b"\r") else line


def _continued(line: bytes) -> bool:
    return line.endswith(b"\\") and (len(line) - len(line.rstrip(b"\\"))) % 2 == 1


def logical_lines(f: BinaryIO, stats: ReadStats) -> Iterator[bytes]:
    """Yield EOL-stripped logical lines (backslash continuations joined with a newline)."""
    readline = f.readline
    first = True
    while True:
        raw = readline(MAX_LINE + 1)
        if not raw:
            return
        if raw[-1] != 10:
            if len(raw) > MAX_LINE and _skip_rest(readline, stats):
                continue
            stats.truncated = True      # partial last line: dropped, the file is still being written
            return
        line = _strip_eol(raw)
        if first:
            first = False
            if line.startswith(_BOM):
                line = line[3:]
        while _continued(line):
            nxt = readline(MAX_LINE + 1)
            if not nxt or nxt[-1] != 10:
                stats.truncated = True
                return
            line = line[:-1] + b"\n" + _strip_eol(nxt)
            if len(line) > MAX_LINE:
                stats.oversized += 1
                line = b""
                break
        if line:
            yield line


def iter_lines(path: Path, limits: ReaderLimits | None = None, stats: ReadStats | None = None) -> Iterator[bytes]:
    """Open `path` (plain or zip) and stream its logical lines."""
    stats = stats if stats is not None else ReadStats()
    with open_stream(path, limits or ReaderLimits()) as f:
        yield from logical_lines(f, stats)
