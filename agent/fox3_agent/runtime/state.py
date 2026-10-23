"""Small persistent agent state (survives restarts): the DCSServerBot event watermark."""
from __future__ import annotations

import json
import logging
from pathlib import Path

log = logging.getLogger("fox3.agent.state")


class AgentState:
    def __init__(self, state_dir: Path):
        self._file = state_dir / "state.json"

    def load(self) -> dict:
        try:
            return json.loads(self._file.read_text("utf-8"))
        except FileNotFoundError:
            return {}
        except (OSError, ValueError):
            log.warning("ignoring unreadable state file %s", self._file)
            return {}

    def save(self, data: dict) -> None:
        self._file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._file.with_suffix(".tmp")
        tmp.write_text(json.dumps(data), "utf-8")
        tmp.replace(self._file)
