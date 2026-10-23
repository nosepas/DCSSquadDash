"""`fox3-agent uninstall` and `fox3-agent status`."""
from __future__ import annotations

import argparse
import contextlib
import json
import shutil
from datetime import datetime
from pathlib import Path

from ..config import ConfigError, load_config
from . import bundle as bd
from . import pairing, scheduler
from .messages import tr


def _lang(target: Path, override: str | None = None) -> str:
    return bd.ui_language(target / "agent.toml", override)


def run_uninstall(args: argparse.Namespace) -> int:
    target = bd.resolve_install_dir(args.install_dir)
    lang = _lang(target, getattr(args, "language", None))
    exe = target / bd.EXE_NAME
    if not target.exists() and not scheduler.query_task().exists:
        print(tr(lang, "un_none"))
        return 0
    print(tr(lang, "un_stop"))
    scheduler.end_task()
    scheduler.kill_exe(exe)  # only processes whose full path is OUR installed exe
    scheduler.kill_exe(target / bd.WINDOWED_NAME)
    print(tr(lang, "un_task"))
    scheduler.delete_task()
    if args.keep_data:
        print(tr(lang, "un_kept", path=target))
        _remove_exe(exe)
        _remove_exe(target / bd.WINDOWED_NAME)
    elif target.exists():
        print(tr(lang, "un_dir", path=target))
        failed: list[str] = []
        shutil.rmtree(target, onexc=lambda _f, p, _e: failed.append(p))
        if failed:
            print(tr(lang, "un_partial", path=target))
            return 1
    print(tr(lang, "un_done"))
    return 0


def _remove_exe(exe: Path) -> None:
    with contextlib.suppress(OSError):
        exe.unlink(missing_ok=True)


def _activity(state_dir: Path) -> str | None:
    """Last time central accepted data (status.json written by the running agent); else the queue file's modification time."""
    try:
        sent = json.loads((state_dir / "status.json").read_text("utf-8")).get("last_success_at")
        if isinstance(sent, str) and sent:
            return sent.replace("T", " ").rstrip("Z") + " UTC"
    except (OSError, ValueError):
        pass
    q = state_dir / "queue.sqlite"
    try:
        return datetime.fromtimestamp(q.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
    except OSError:
        return None


def run_status(args: argparse.Namespace) -> int:
    target = bd.resolve_install_dir(args.install_dir)
    lang = _lang(target, getattr(args, "language", None))
    if (target / bd.EXE_NAME).is_file():
        print(tr(lang, "st_installed", path=target))
    else:
        print(tr(lang, "st_not_installed"))
    info = scheduler.query_task()
    print(tr(lang, "st_task", status=info.status or "?") if info.exists else tr(lang, "st_task_missing"))
    if info.exists:
        print(tr(lang, "st_last", result=info.last_result or "?"))
    try:
        cfg = load_config(target / "agent.toml")
    except ConfigError:
        return 0
    print(tr(lang, "st_paired" if pairing.is_paired(cfg) else "st_not_paired"))
    when = _activity(cfg.state_dir)
    if when:
        print(tr(lang, "st_activity", when=when))
    return 0
