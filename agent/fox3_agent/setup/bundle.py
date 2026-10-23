"""Locate the downloaded bundle (exe + agent.toml + pairing-code.txt) and the install folder."""
from __future__ import annotations

import contextlib
import os
import re
import sys
import tomllib
from pathlib import Path

from .messages import DEFAULT_LANGUAGE, LANGUAGES

CODE_FILE = "pairing-code.txt"
EXE_NAME = "fox3-agent.exe"
WINDOWED_NAME = "fox3-agentw.exe"  # same program without a console window: this is what the Scheduled Task runs
CODE_RE = re.compile(r"[A-Za-z0-9_-]{1,32}")


class SetupError(Exception):
    """User-facing failure; `key` is a message key and `kw` its format arguments."""

    def __init__(self, key: str, **kw: object):
        super().__init__(key)
        self.key, self.kw = key, kw


def running_exe() -> Path | None:
    return Path(sys.executable).resolve() if getattr(sys, "frozen", False) else None


def bundle_dir(here: str | None) -> Path:
    if here:
        return Path(here).resolve()
    exe = running_exe()
    return exe.parent if exe else Path(__file__).resolve().parent


def valid_code(code: str) -> str:
    code = code.strip()
    if not CODE_RE.fullmatch(code):
        raise SetupError("bad_code_file")
    return code


def read_code(bundle: Path) -> str | None:
    f = bundle / CODE_FILE
    if not f.is_file():
        return None
    try:
        return valid_code(f.read_text("utf-8-sig").strip())
    except (OSError, UnicodeDecodeError) as exc:
        raise SetupError("bad_code_file") from exc


def wipe_code_file(bundle: Path) -> None:
    """Best effort: overwrite then delete the one-time code."""
    f = bundle / CODE_FILE
    with contextlib.suppress(OSError):
        f.write_bytes(b"0" * max(f.stat().st_size, 1))
    f.unlink(missing_ok=True)


def ui_language(toml_path: Path, override: str | None = None) -> str:
    if override in LANGUAGES:
        return str(override)
    try:
        lang = tomllib.loads(toml_path.read_text("utf-8")).get("ui", {}).get("language")
    except (OSError, tomllib.TOMLDecodeError, AttributeError):
        return DEFAULT_LANGUAGE
    return lang if lang in LANGUAGES else DEFAULT_LANGUAGE


def default_install_dir() -> Path:
    base = os.environ.get("LOCALAPPDATA")
    return (Path(base) if base else Path.home() / "AppData" / "Local") / "FOX3Agent"


def resolve_install_dir(explicit: str | None) -> Path:
    if explicit:
        return Path(explicit).expanduser().resolve()
    path = default_install_dir().resolve()
    if not path.is_relative_to(Path.home().resolve()):
        raise SetupError("install_refused")
    return path
