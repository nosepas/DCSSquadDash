"""Build common/fox3_common/data/airfields.json.gz: name and position of every airfield of the 11 supported DCS maps.

Source: the airport tables of the open-source pydcs project (LGPL-3.0), which hold DCS's own x/y coordinates. Only facts
(names, positions, civil flag) are extracted. Positions are converted with fox3_common.geo; the projections themselves were checked
against real airport coordinates (tests/test_projections.py).

Usage: python tools/make_airfields.py [DIR_WITH_ap_<map>.py_FILES]   (downloads from GitHub when no folder is given)
"""
from __future__ import annotations

import gzip
import json
import re
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "common"))
from fox3_common import geo  # noqa: E402

# pydcs folder -> DCS terrain id
MAPS = {"caucasus": "Caucasus", "syria": "Syria", "nevada": "Nevada", "persiangulf": "PersianGulf", "marianaislands": "MarianaIslands",
        "sinai": "Sinai", "falklands": "Falklands", "normandy": "Normandy", "thechannel": "TheChannel", "germany": "GermanyCW",
        "kola": "Kola"}
URL = "https://raw.githubusercontent.com/pydcs/dcs/HEAD/dcs/terrain/{m}/airports.py"
BLOCK = re.compile(r'class \w+\(Airport\):\s*id = \d+\s*name = "([^"]+)".*?civilian = (True|False).*?'
                   r"super\(\).__init__\(mapping\.Point\(([-0-9.]+), ([-0-9.]+),", re.S)


def source_text(folder: Path | None, m: str) -> str:
    if folder:
        return (folder / f"ap_{m}.py").read_text("utf-8")
    with urllib.request.urlopen(URL.format(m=m), timeout=60) as r:  # noqa: S310  (fixed https URL)
        return r.read().decode("utf-8")


def extract(text: str, terrain: str) -> list[dict]:
    out = []
    # split on class boundaries so a regex never spans two airports
    for chunk in re.split(r"(?=^class \w+\(Airport\):)", text, flags=re.M):
        m = BLOCK.search(chunk)
        if not m:
            continue
        name, civil, x, y = m.group(1), m.group(2) == "True", float(m.group(3)), float(m.group(4))
        ll = geo.xy_to_latlon(terrain, x, y)
        if ll:
            out.append({"name": name, "lat": round(ll[0], 5), "lon": round(ll[1], 5), "civil": civil})
    return sorted(out, key=lambda a: a["name"])


def main() -> None:
    folder = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    data = {terrain: extract(source_text(folder, m), terrain) for m, terrain in MAPS.items()}
    target = ROOT / "common" / "fox3_common" / "data" / "airfields.json.gz"
    with gzip.open(target, "wt", encoding="utf-8") as f:
        json.dump({"source": "pydcs airport tables (LGPL-3.0), positions converted with fox3_common.geo", "terrains": data}, f,
                  separators=(",", ":"), ensure_ascii=False)
    for terrain, aps in data.items():
        print(f"{terrain:15} {len(aps):4} airfields")
    print(f"written {target} ({target.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
