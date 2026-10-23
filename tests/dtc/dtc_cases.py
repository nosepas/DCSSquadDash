"""Parametrisation helper: every synthetic case plus every real sample present on disk."""
from __future__ import annotations

from pathlib import Path

import pytest
from dtc_synth import synth_raw

SAMPLES = Path(__file__).resolve().parents[2] / "samples"
REAL = {"F-16C_50": ["F-16C_50_DTC.dtc"], "F-14BU": ["F-14BU_DTC.dtc", "F-14BU_DTC modernos.dtc"], "AH-64D_BLK_II": ["AH-64D_BLK_II_DTC.dtc"]}
F14_TERRAIN = "Caucasus"


def load(case: str) -> tuple[str, bytes]:
    """case = 'synth:<aircraft>' or 'real:<file>' -> (aircraft, raw)."""
    kind, _, name = case.partition(":")
    if kind == "synth":
        return name, synth_raw(name)
    path = SAMPLES / name
    if not path.is_file():
        pytest.skip(f"sample {name} not available")
    aircraft = next(a for a, files in REAL.items() if name in files)
    return aircraft, path.read_bytes()


CASES = [f"synth:{a}" for a in REAL] + [f"real:{f}" for files in REAL.values() for f in files]
