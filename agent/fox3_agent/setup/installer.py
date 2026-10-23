"""`fox3-agent setup`: copy, configure, pair, check and register the per-user Scheduled Task."""
from __future__ import annotations

import argparse
import getpass
import shutil
from collections.abc import Callable
from pathlib import Path

from ..config import AgentConfig, ConfigError, load_config
from . import bundle as bd
from . import pairing, scheduler
from .messages import tr
from .taskxml import TASK_NAME, agent_task_xml
from .tomlout import with_state_dir


def _install_files(src_exe: Path | None, bundle: Path, target: Path, lang: str, dry: bool) -> Path:
    exe_dst = target / bd.EXE_NAME
    cfg_dst = target / "agent.toml"
    text = with_state_dir((bundle / "agent.toml").read_text("utf-8"), str(target / "state"))
    if src_exe is None:
        print(tr(lang, "copy_dev"))
    elif src_exe == exe_dst:
        print(tr(lang, "copy_same"))
    else:
        print(tr(lang, "copy_exe", path=exe_dst))
    print(tr(lang, "config_written", path=cfg_dst))
    if dry:
        return cfg_dst
    target.mkdir(parents=True, exist_ok=True)
    if src_exe is not None and src_exe != exe_dst:
        if exe_dst.exists():
            print(tr(lang, "stopping"))
            scheduler.end_task()
            scheduler.kill_exe(exe_dst)
        shutil.copy2(src_exe, exe_dst)
    if src_exe is not None:
        windowed_src, windowed_dst = src_exe.with_name(bd.WINDOWED_NAME), target / bd.WINDOWED_NAME
        if windowed_src.is_file() and windowed_src != windowed_dst:
            if windowed_dst.exists():
                scheduler.kill_exe(windowed_dst)
            shutil.copy2(windowed_src, windowed_dst)
    cfg_dst.write_text(text, "utf-8", newline="\n")
    return cfg_dst


def _obtain_code(bundle: Path, prompt: Callable[[str], str], lang: str) -> str:
    code = bd.read_code(bundle)
    return code if code else bd.valid_code(prompt(tr(lang, "ask_code")))


def _register_task(exe: Path, cfg_path: Path, lang: str, start: bool) -> bool:
    ok, detail = scheduler.create_task(agent_task_xml(exe, cfg_path))
    if not ok or not scheduler.query_task().exists:
        print(tr(lang, "task_fail", detail=detail[:200] or "schtasks"))
        return False
    print(tr(lang, "task_ok"))
    if start and scheduler.run_task():
        print(tr(lang, "started"))
    return True


def run_setup(args: argparse.Namespace, factory: pairing.ClientFactory = pairing.default_client,
              prompt: Callable[[str], str] = getpass.getpass) -> int:
    bundle = bd.bundle_dir(args.here)
    lang = bd.ui_language(bundle / "agent.toml", args.language)
    dry = bool(args.dry_run)
    print(tr(lang, "tip"))
    print(tr(lang, "bundle", path=bundle))
    try:
        if not (bundle / "agent.toml").is_file():
            raise bd.SetupError("no_toml")
        try:
            load_config(bundle / "agent.toml")
        except ConfigError as exc:
            raise bd.SetupError("bad_toml", detail=str(exc)[:200]) from exc
        target = bd.resolve_install_dir(args.install_dir)
        cfg_path = _install_files(bd.running_exe(), bundle, target, lang, dry)
        cfg: AgentConfig = load_config(cfg_path) if not dry else load_config(bundle / "agent.toml")
        if dry:
            print("[dry-run] pair, check connection and register task '" + TASK_NAME + "'")
            print(tr(lang, "dry_note"))
            return 0
        if pairing.is_paired(cfg):
            print(tr(lang, "paired_already"))
        else:
            pairing.pair(cfg, _obtain_code(bundle, prompt, lang), factory)
            bd.wipe_code_file(bundle)
            print(tr(lang, "pair_ok"))
        print(tr(lang, "check_ok" if pairing.check_connection(cfg, factory) else "check_fail"))
        exe = target / bd.EXE_NAME
        run_exe = target / bd.WINDOWED_NAME if (target / bd.WINDOWED_NAME).is_file() else exe
        if exe.is_file() and not _register_task(run_exe, cfg_path, lang, not args.no_start):
            return 1
    except bd.SetupError as exc:
        print(tr(lang, exc.key, **exc.kw))
        return 1
    except (OSError, ValueError) as exc:
        print(f"Error: {type(exc).__name__}: {str(exc)[:200]}")
        return 1
    print(tr(lang, "summary", path=target))
    return 0
