import sys
from pathlib import Path

# the sub-packages' fixture modules (foothold_samples, dcsbot_fakes) are plain modules next to their tests
for sub in ("foothold", "dcsbot", "tacview"):
    sys.path.insert(0, str(Path(__file__).parent / sub))
