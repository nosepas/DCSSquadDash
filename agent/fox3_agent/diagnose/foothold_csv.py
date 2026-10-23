"""Structure-only view of the CTLD FARPS csv: header, column count, row count, and one masked row (numbers rounded, text -> <name>)."""
from __future__ import annotations

import re
from dataclasses import dataclass

from ..sources.foothold.farps import MAX_BYTES

_HEADER_OK = re.compile(r"[A-Za-z_ ;,]+")


@dataclass(frozen=True)
class CsvOutline:
    header: str | None
    columns: int
    rows: int
    has_lat_lon: bool
    first_row: str | None


def _round(n: float) -> str:
    return f"{n:.1f}" if abs(n) < 1000 else str(int(round(n, -2)))


def mask_cell(cell: str) -> str:
    cell = cell.strip()
    if not cell:
        return ""
    try:
        return _round(float(cell.replace(",", ".")))
    except ValueError:
        return "<name>"


def mask_row(line: str, sep: str = ";") -> str:
    return sep.join(mask_cell(c) for c in line.split(sep))


def outline_csv(text: str) -> CsvOutline:
    lines = [ln for ln in text.splitlines() if ln.strip()]
    if not lines:
        return CsvOutline(None, 0, 0, False, None)
    first = lines[0]
    named = any(c.strip().lower() == "name" for c in first.split(";"))
    title = not named and len(first.split(";")) < 3                    # "FARP COORDINATES"-style title line
    head_idx = 0 if named or title else None
    header = first if head_idx is not None and _HEADER_OK.fullmatch(first.strip()) else None
    if head_idx is not None and header is None:
        header = mask_row(first)                                         # unexpected header content: show only its shape
    data = lines[1:] if head_idx is not None else lines
    cols = [c.strip().lower() for c in first.split(";")] if named else []
    lat_lon = any(c in ("latitude", "lat") for c in cols) and any(c in ("longitude", "lon", "long") for c in cols)
    sample = first if named or not data else data[0]
    ncols = sum(1 for c in sample.split(";") if c.strip())                # a trailing ';' does not add a column
    return CsvOutline(header, ncols, len(data), lat_lon, mask_row(data[0]) if data else None)


__all__ = ["MAX_BYTES", "CsvOutline", "mask_cell", "mask_row", "outline_csv"]
