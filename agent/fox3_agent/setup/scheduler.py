"""Thin wrappers over `schtasks` and process control. Always fixed argument lists, shell=False."""
from __future__ import annotations

import csv
import io
import os
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path

from .taskxml import TASK_NAME

_PS_KILL = ("Get-CimInstance Win32_Process -Filter \"Name='fox3-agent.exe'\" | "
            "Where-Object { $_.ExecutablePath -eq $env:FOX3_TARGET_EXE -and $_.ProcessId -ne [int]$env:FOX3_SELF_PID } | "
            "ForEach-Object { Stop-Process -Id $_.ProcessId -Force }")


@dataclass(frozen=True)
class TaskInfo:
    exists: bool
    status: str = ""
    last_result: str = ""


def _run(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(args, shell=False, capture_output=True, text=True, timeout=60, check=False, env=env)


def create_args(xml_path: Path, name: str = TASK_NAME) -> list[str]:
    return ["schtasks", "/Create", "/TN", name, "/XML", str(xml_path), "/F"]


def create_task(xml: bytes, name: str = TASK_NAME) -> tuple[bool, str]:
    fd, tmp = tempfile.mkstemp(suffix=".xml")
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(xml)
        r = _run(create_args(Path(tmp), name))
    finally:
        Path(tmp).unlink(missing_ok=True)
    return r.returncode == 0, (r.stderr or r.stdout or "").strip()


def run_task(name: str = TASK_NAME) -> bool:
    return _run(["schtasks", "/Run", "/TN", name]).returncode == 0


def end_task(name: str = TASK_NAME) -> bool:
    return _run(["schtasks", "/End", "/TN", name]).returncode == 0


def delete_task(name: str = TASK_NAME) -> bool:
    return _run(["schtasks", "/Delete", "/TN", name, "/F"]).returncode == 0


def query_task(name: str = TASK_NAME) -> TaskInfo:
    """CSV output keeps column positions identical in every Windows language (labels are localised)."""
    r = _run(["schtasks", "/Query", "/TN", name, "/FO", "CSV", "/V", "/NH"])
    if r.returncode != 0:
        return TaskInfo(False)
    rows = list(csv.reader(io.StringIO(r.stdout.strip())))
    row = rows[0] if rows else []
    return TaskInfo(True, row[3] if len(row) > 3 else "", row[6] if len(row) > 6 else "")


def kill_exe(exe: Path) -> bool:
    """Stop only processes whose full path is exactly `exe` (never by image name alone), except ourselves."""
    env = {**os.environ, "FOX3_TARGET_EXE": str(exe), "FOX3_SELF_PID": str(os.getpid())}
    r = _run(["powershell", "-NoProfile", "-NonInteractive", "-Command", _PS_KILL], env=env)
    return r.returncode == 0
