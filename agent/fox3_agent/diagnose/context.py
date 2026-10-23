"""Inputs shared by the diagnose sections."""
from __future__ import annotations

import os
import time
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from ..config import AgentConfig


@dataclass
class Context:
    config_path: Path
    config: AgentConfig | None = None
    config_error: str | None = None
    saves_dir: Path | None = None
    tacview_dir: Path | None = None
    remote: dict | None = None                 # body of GET /agent/v1/config when central answered
    settle_s: float = 120.0
    now: Callable[[], float] = time.time
    environ: Mapping[str, str] = field(default_factory=lambda: os.environ)
    home: Path | None = None                   # forwarded to discover (tests / other user's profile)
    extras: dict = field(default_factory=dict)  # section results other sections reuse (e.g. discovered folders)
