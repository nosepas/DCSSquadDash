"""Anonymous statistics of one ACMI recording (one extra streaming pass): object counts, Color/Coalition/Type of Pilot objects.

Pilot names are never stored: only their count and a look-alike-AI classification.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from ..sources.tacview.acmi_reader import iter_lines
from ..sources.tacview.props import parse_props

MAX_BYTES_READ = 1_500_000_000
MAX_OBJECTS = 2_000_000
KEPT = ("Pilot", "Color", "Coalition", "Type", "Group")
_TYPE = re.compile(rb",Type=([^,]*)")
_AI_NAME = re.compile(r"(?i)^(aerial|ground|naval|helicopter|static|unit)[ _-]?\d+([ _-]\d+)*$")


def looks_ai(pilot: str, group: str | None) -> bool:
    """Heuristic (unverified): AI units usually carry DCS default names ('Aerial-1-1') or a Pilot equal to their Group."""
    return bool(_AI_NAME.match(pilot.strip())) or (group is not None and pilot.strip() == group.strip())


@dataclass
class AcmiStats:
    objects: int = 0
    pilot_objects: int = 0
    ai_like: int = 0
    colors: Counter = field(default_factory=Counter)
    coalitions: Counter = field(default_factory=Counter)
    color_x_coalition: Counter = field(default_factory=Counter)
    pilot_types: Counter = field(default_factory=Counter)
    all_types: Counter = field(default_factory=Counter)
    rows: list[tuple[str, str, str, str, bool]] = field(default_factory=list)   # (<pilot N>, color, coalition, type, ai)
    partial: bool = False


def collect(path: Path, max_bytes: int = MAX_BYTES_READ) -> AcmiStats:
    st = AcmiStats()
    seen: set[bytes] = set()
    pilots: dict[bytes, dict[str, str]] = {}
    read = 0
    for line in iter_lines(path):
        read += len(line) + 1
        if read > max_bytes:
            st.partial = True
            break
        if line[:1] in (b"#", b"/", b"-"):
            continue
        comma = line.find(b",")
        if comma <= 0:
            continue
        oid = line[:comma]
        if oid not in seen and oid != b"0" and len(seen) < MAX_OBJECTS:
            seen.add(oid)
            if (m := _TYPE.search(line)):
                st.all_types[m.group(1).decode("ascii", "replace")] += 1
        if b",Pilot=" in line:
            props = parse_props(line)
            if props.get("Pilot", "").strip():
                pilots.setdefault(oid, {}).update({k: v for k, v in props.items() if k in KEPT})
        elif oid in pilots and (b"Color=" in line or b"Coalition=" in line):
            props = parse_props(line)
            pilots[oid].update({k: v for k, v in props.items() if k in ("Color", "Coalition")})
    st.objects = len(seen)
    for n, p in enumerate(pilots.values(), 1):
        color, coal, typ = p.get("Color", "<absent>"), p.get("Coalition", "<absent>"), p.get("Type", "<absent>")
        ai = looks_ai(p["Pilot"], p.get("Group"))
        st.pilot_objects += 1
        st.ai_like += ai
        st.colors[color] += 1
        st.coalitions[coal] += 1
        st.color_x_coalition[(color, coal)] += 1
        st.pilot_types[typ] += 1
        if n <= 15:
            st.rows.append((f"<pilot {n}>", color, coal, typ, ai))
    return st
