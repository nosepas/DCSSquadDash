import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "agent" / "tacview"))  # reuse the synthetic ACMI builders
