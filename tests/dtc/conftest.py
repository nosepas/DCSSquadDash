"""Make the dtc package importable even if pyproject's pythonpath lacks `dtc`."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
for sub in ("dtc", "common"):
    p = str(ROOT / sub)
    if p not in sys.path:
        sys.path.insert(0, p)
