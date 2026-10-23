"""FARPs built by players (CTLD), listed in `<persistence file stem>_CTLD_FARPS.csv` next to the Foothold persistence file.

Two layouts are known from third-party documentation (not verified on Foothold 5.3.5): an old one with a title line
(`FARP COORDINATES`) followed by `seq;name;x;y;` rows (DCS x/y), and a newer one with a header
`seq;name;x;y;zell;latitude;longitude;`. Parsing is tolerant: bad rows are skipped, nothing is invented.
"""
from __future__ import annotations

from pathlib import Path

MAX_BYTES = 256 * 1024
MAX_FARPS = 200


def farps_file(persistence: Path) -> Path | None:
    exact = persistence.with_name(f"{persistence.stem}_CTLD_FARPS.csv")
    if exact.is_file():
        return exact
    wanted = exact.name.lower()  # tolerate a different letter case on the file name
    return next((p for p in persistence.parent.glob("*_CTLD_FARPS.csv") if p.name.lower() == wanted), None)


def _num(value: str) -> float | None:
    try:
        n = float(value.replace(",", "."))
    except ValueError:
        return None
    return n if n == n and abs(n) != float("inf") else None


def _farp(row: list[str], cols: dict[str, int]) -> dict | None:
    def cell(key: str) -> str:
        i = cols.get(key)
        return row[i] if i is not None and i < len(row) else ""

    name = cell("name")[:80]
    if not name:
        return None
    farp: dict = {"name": name}
    lat, lon = _num(cell("latitude")), _num(cell("longitude"))
    if lat is not None and lon is not None and -90 <= lat <= 90 and -180 <= lon <= 180:
        farp["geo"] = {"lat": lat, "lon": lon}
    x, y = _num(cell("x")), _num(cell("y"))
    if x is not None and y is not None:
        farp["position"] = {"x": x, "y": y}
    return farp if ("geo" in farp or "position" in farp) else None


def parse_farps(text: str) -> list[dict]:
    rows = [[c.strip() for c in line.split(";")] for line in text.splitlines() if line.strip()]
    cols = {"name": 1, "x": 2, "y": 3}
    if rows and any(c.lower() == "name" for c in rows[0]):  # header row: map columns by name
        cols = {c.lower(): i for i, c in enumerate(rows[0]) if c}
        rows = rows[1:]
    elif rows and len(rows[0]) < 3:  # title line such as "FARP COORDINATES"
        rows = rows[1:]
    farps = (_farp(r, cols) for r in rows)
    return [f for f in farps if f][:MAX_FARPS]


def read_farps(persistence: Path) -> tuple[list[dict], bytes]:
    """FARPs next to the given persistence file and the raw bytes read (for change detection). ([], b'') when absent/unreadable."""
    path = farps_file(persistence)
    if path is None:
        return [], b""
    try:
        if path.stat().st_size > MAX_BYTES:
            return [], b""
        raw = path.read_bytes()
    except OSError:
        return [], b""
    return parse_farps(raw.decode("utf-8", errors="replace")), raw
