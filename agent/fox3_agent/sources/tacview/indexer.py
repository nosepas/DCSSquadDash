"""Single-pass streaming indexer of one ACMI recording.

Memory is O(pilot objects). Per line only bytes operations are used: the object id is the text before the first
comma; known pilot ids just get their `last_offset` bumped; a full parse happens only on lines containing
`,Pilot=` (and on the few global header lines). Malformed lines are skipped and counted, never raised.
"""
from __future__ import annotations

import zipfile
import zlib
from collections.abc import Callable
from pathlib import Path

from .acmi_reader import ReaderLimits, ReadStats, iter_lines
from .errors import AcmiCancelledError, AcmiFormatError
from .model import Appearance, TacviewIndex
from .props import clean, map_side, normalize_utc, parse_props

_HASH, _SLASH, _DASH = 35, 47, 45
_PILOT = b",Pilot="
_STREAM_ERRORS = (EOFError, zlib.error, zipfile.BadZipFile)


def _new_appearance(oid: bytes, props: dict[str, str], t: float, side_map: dict[str, str] | None) -> Appearance | None:
    pilot = clean(props.get("Pilot"))
    if pilot is None:
        return None
    return Appearance(pilot, oid.decode("ascii", "replace").lower(), clean(props.get("Name")),
                      map_side(props.get("Color"), props.get("Coalition"), side_map), clean(props.get("Group")), t, t)


def _apply_global(idx: TacviewIndex, line: bytes) -> None:
    props = parse_props(line)
    if "ReferenceTime" in props:
        idx.reference_time = normalize_utc(props["ReferenceTime"])
    if "Title" in props:
        idx.title = clean(props["Title"])
    if "DataSource" in props:
        idx.data_source = clean(props["DataSource"])


def _on_pilot_line(idx: TacviewIndex, tracked: dict[bytes, Appearance], oid: bytes, line: bytes, t: float,
                   side_map: dict[str, str] | None, max_objects: int) -> None:
    props = parse_props(line)
    known = tracked.get(oid)
    if known is not None and clean(props.get("Pilot")) in (None, known.pilot):
        known.aircraft = known.aircraft or clean(props.get("Name"))        # only fill gaps
        known.group = known.group or clean(props.get("Group"))
        if known.coalition == "unknown":
            known.coalition = map_side(props.get("Color"), props.get("Coalition"), side_map)
        return
    if known is None and len(tracked) >= max_objects:
        idx.dropped_objects += 1
        return
    try:
        int(oid, 16)
    except ValueError:
        idx.malformed_lines += 1
        return
    app = _new_appearance(oid, props, t, side_map)
    if app is not None:                     # a new Pilot on a known id (seat change) opens a new appearance
        tracked[oid] = app
        idx.appearances.append(app)


def index_file(path: Path, *, limits: ReaderLimits | None = None, side_map: dict[str, str] | None = None,
               cancel: Callable[[], bool] | None = None, max_objects: int = 200_000) -> TacviewIndex:
    """Index `path` (plain or zip ACMI). Raises AcmiError subclasses for unusable files only."""
    stats = ReadStats()
    idx = TacviewIndex()
    tracked: dict[bytes, Appearance] = {}
    lines = iter_lines(path, limits, stats)
    cur = max_t = 0.0
    in_header, seen_frame, frames, malformed = True, False, 0, 0
    try:
        header = next(lines, b"")
        if not header.startswith(b"FileType=text/acmi/tacview"):
            raise AcmiFormatError("not a text ACMI recording")
        for line in lines:
            c = line[0]
            if c == _HASH:
                try:
                    t = float(line[1:])
                except ValueError:
                    malformed += 1
                    continue
                if t != t or abs(t) > 1e12:
                    malformed += 1
                    continue
                cur, in_header, seen_frame = t, False, True
                if t > max_t:
                    max_t = t
                frames += 1
                if cancel is not None and not frames & 0xFF and cancel():
                    raise AcmiCancelledError("cancelled")
                continue
            if c == _SLASH:
                continue
            if c == _DASH:
                known = tracked.get(line[1:].strip())
                if known is not None and cur > known.last_offset_s:
                    known.last_offset_s = cur
                continue
            comma = line.find(b",")
            if comma < 0:
                if not (in_header and b"=" in line):
                    malformed += 1
                continue
            oid = line[:comma]
            known = tracked.get(oid)
            if known is not None:
                if cur > known.last_offset_s:
                    known.last_offset_s = cur
                elif cur < known.first_offset_s:
                    known.first_offset_s = cur
                if _PILOT not in line:
                    continue
            elif oid == b"0":
                if in_header:
                    _apply_global(idx, line)
                continue
            elif _PILOT not in line:
                continue
            _on_pilot_line(idx, tracked, oid, line, cur, side_map, max_objects)
    except _STREAM_ERRORS:
        idx.complete = False
    finally:
        lines.close()
    idx.malformed_lines += malformed
    idx.duration_s = max_t if seen_frame else None
    if stats.truncated:
        idx.complete = False
    idx.oversized_lines = stats.oversized
    return idx
