"""Logging for the agent: console when there is one, and a rotating file in the state folder when it runs unattended.

The Scheduled Task runs the windowless executable (no console, `sys.stderr` is None), so without a file nothing could be diagnosed.
"""
from __future__ import annotations

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path

FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"
FILE_NAME = "agent.log"


def silence_missing_streams() -> None:
    """A windowless PyInstaller build has no stdout/stderr: give them a sink so print() and logging never crash."""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115  (lives as long as the process)
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")  # noqa: SIM115


def configure(state_dir: Path | None, to_file: bool, console: bool = True) -> None:
    handlers: list[logging.Handler] = []
    if console:
        handlers.append(logging.StreamHandler())
    if to_file and state_dir is not None:
        try:
            state_dir.mkdir(parents=True, exist_ok=True)
            handlers.append(RotatingFileHandler(state_dir / FILE_NAME, maxBytes=1_000_000, backupCount=3, encoding="utf-8"))
        except OSError:
            pass  # logging must never stop the agent
    logging.basicConfig(level=logging.INFO, format=FORMAT, handlers=handlers or [logging.NullHandler()], force=True)
