"""Section 3: the Foothold persistence file, its structure outline, the FARPS csv and how our parser normalises it."""
from __future__ import annotations

import re
import time
from pathlib import Path

from ..sources.foothold.describe import describe_structure
from ..sources.foothold.farps import farps_file, parse_farps
from ..sources.foothold.locator import locate_persistence_file, status_entry
from ..sources.foothold.lua_errors import LuaParseError
from ..sources.foothold.lua_parser import parse_lua
from ..sources.foothold.normalize import normalize
from .context import Context
from .foothold_csv import MAX_BYTES, outline_csv
from .redact import safe_error
from .report import Section


def _age(seconds: float) -> str:
    return f"{seconds:.0f} s" if seconds < 120 else f"{seconds / 60:.0f} min" if seconds < 7200 else f"{seconds / 3600:.1f} h"


def status_kind(entry: str) -> str:
    """Generic shape of the path stored in foothold.status (no drive letter, no names)."""
    seps = [name for ch, name in (("\\", "backslashes"), ("/", "forward slashes")) if ch in entry]
    if entry.startswith(("\\\\", "//")):
        kind = "absolute (network/UNC)"
    elif re.match(r"^[A-Za-z]:[\\/]", entry):
        kind = "absolute (Windows drive path)"
    elif entry.startswith("/"):
        kind = "absolute (POSIX)"
    else:
        kind = "relative"
    return f"{kind}, uses {' and '.join(seps) or 'no separators (bare file name)'}, {len(entry)} characters"


def _status(saves: Path, located: Path | None, sec: Section) -> None:
    entry = status_entry(saves)
    if entry is None:
        sec.kv("foothold.status", "absent or empty (file located by name instead)")
        return
    sec.kv("foothold.status", f"present; holds a {status_kind(entry)}")
    if located is not None:
        sec.kv("  its file name equals the located file", re.split(r"[\\/]", entry)[-1].lower() == located.name.lower())


def _farps(located: Path, sec: Section) -> list[dict]:
    csv = farps_file(located)
    if csv is None:
        sec.kv("FARPS csv", "none next to the persistence file (normal if nobody built a FARP)")
        return []
    sec.kv("FARPS csv", f"{csv.name} ({csv.stat().st_size} bytes)")
    if csv.stat().st_size > MAX_BYTES:
        sec.flag("FARPS csv larger than the agent limit; it would be ignored")
        return []
    text = csv.read_bytes().decode("utf-8", errors="replace")
    o = outline_csv(text)
    sec.kv("  header line", o.header or "(no header: rows start immediately)")
    sec.kv("  columns / data rows", f"{o.columns} / {o.rows}")
    sec.kv("  latitude+longitude columns", o.has_lat_lon)
    sec.kv("  first row (masked)", o.first_row or "(none)")
    return parse_farps(text)


def foothold(ctx: Context, sec: Section) -> None:
    saves = ctx.saves_dir
    if saves is None:
        sec.flag("no Foothold saves folder known (use --saves-dir, or set it in the admin panel)")
        return
    if not saves.is_dir():
        sec.flag("Foothold saves folder does not exist or is not readable")
        return
    located = locate_persistence_file(saves)
    _status(saves, located, sec)
    if located is None:
        sec.flag("no Foothold persistence file located (foothold*.lua)")
        return
    st = located.stat()
    sec.kv("persistence file", f"{located.name}, {st.st_size} bytes, modified {_age(max(0.0, ctx.now() - st.st_mtime))} ago")
    sec.line("  structure outline (redacted):")
    sec.lines.extend("    " + ln for ln in describe_structure(located).splitlines())
    farps = _farps(located, sec)
    try:
        parsed = parse_lua(located.read_bytes())
    except (OSError, LuaParseError) as exc:
        sec.flag(f"our parser cannot read the file: {safe_error(exc)}")
        return
    t0 = time.perf_counter()
    payload = normalize(parsed, source_file=located.name, source_mtime="-", snapshot_at="-").payload
    sec.line(f"  normalised by our parser in {(time.perf_counter() - t0) * 1000:.0f} ms:")
    for key in ("zones", "connections", "missions", "player_stats", "ejected_pilots"):
        sec.kv("    " + key, len(payload[key]))
    sec.kv("    farps (csv)", len(farps))
    zones = payload["zones"]
    sec.kv("    zones by coalition", {c: sum(z["coalition"] == c for z in zones) for c in sorted({z["coalition"] for z in zones})})
    sec.kv("    at_risk derivable", any("at_risk" in z for z in zones))
    sec.kv("    zones with coordinates", sum(1 for z in zones if z.get("geo")))
    notes = payload["format_notes"]
    sec.kv("    format_notes", len(notes))
    for n in notes[:20]:
        sec.line(f"      - {n[:200]}")
    if any("unknown" in n or "missing" in n for n in notes):
        sec.flag("format_notes mention unknown or missing keys (Foothold 5.3.5 differs from the documented format?)")
