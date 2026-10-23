"""argparse registration and dispatch for setup / uninstall / status / secret."""
from __future__ import annotations

import argparse
import getpass
from collections.abc import Callable
from pathlib import Path

from ..config import ConfigError, load_config
from ..secrets_store import SecretError, SecretStore
from . import bundle as bd
from .installer import run_setup
from .lifecycle import run_status, run_uninstall
from .messages import LANGUAGES, tr


def register(sub: argparse._SubParsersAction) -> None:
    s = sub.add_parser("setup", help="install this agent for the current Windows user (downloaded bundle)")
    s.add_argument("--here", metavar="DIR", help="folder with agent.toml and pairing-code.txt (default: next to the exe)")
    s.add_argument("--no-start", action="store_true", help="register but do not start now")
    s.add_argument("--dry-run", action="store_true", help="print what would be done, change nothing")
    for p in (s, sub.add_parser("uninstall", help="remove the task and the installed files"),
              sub.add_parser("status", help="is it installed, running and paired?")):
        p.add_argument("--install-dir", metavar="DIR", help=r"default: %%LOCALAPPDATA%%\FOX3Agent")
        p.add_argument("--language", choices=LANGUAGES)
    sub.choices["uninstall"].add_argument("--keep-data", action="store_true", help="keep the state folder (credentials, queue)")
    sec = sub.add_parser("secret", help="store small secrets encrypted for this Windows user")
    sec.add_argument("action", choices=("set", "delete", "list"))
    sec.add_argument("name", nargs="?")
    sec.add_argument("--config", help=r"default: the installed agent.toml, else .\agent.toml")
    sec.add_argument("--language", choices=LANGUAGES)


def _state_dir(config: str | None) -> Path:
    path = Path(config) if config else bd.default_install_dir() / "agent.toml"
    if not config and not path.exists():
        path = Path("agent.toml")
    return load_config(path).state_dir


def run_secret(args: argparse.Namespace, prompt: Callable[[str], str] = getpass.getpass) -> int:
    lang = args.language or "es"
    try:
        store = SecretStore(_state_dir(args.config))
        if args.action == "list":
            names = store.names()
            print("\n".join(names) if names else tr(lang, "sec_none"))
            return 0
        if not args.name:
            print(tr(lang, "sec_bad"))
            return 2
        if args.action == "set":
            value = prompt(tr(lang, "sec_prompt", name=args.name))
            if not value:
                print(tr(lang, "sec_empty"))
                return 1
            store.set(args.name, value)
            print(tr(lang, "sec_saved", name=args.name))
        elif store.delete(args.name):
            print(tr(lang, "sec_deleted", name=args.name))
        else:
            print(tr(lang, "sec_missing", name=args.name))
            return 1
    except SecretError:
        print(tr(lang, "sec_bad"))
        return 2
    except (ConfigError, OSError, ValueError) as exc:
        print(f"Error: {type(exc).__name__}")
        return 1
    return 0


HANDLERS = {"setup": run_setup, "uninstall": run_uninstall, "status": run_status, "secret": run_secret}
