"""`fox3-agent` command line: discover | pair | check | run."""
from __future__ import annotations

import argparse
import logging
import signal
import sys
from pathlib import Path

import httpx

from . import __version__, logsetup
from .cli_tools import cmd_diagnose, cmd_init
from .client import CentralClient
from .config import ConfigError, load_config
from .credentials import Credentials, CredentialStore
from .detect import detect
from .runtime import build_agent
from .runtime.builder import NotPairedError, central_client
from .secrets_store import SecretStore
from .setup.commands import HANDLERS as SETUP_HANDLERS
from .setup.commands import register as register_setup
from .sources.foothold.describe import describe_structure
from .sources.foothold.locator import locate_persistence_file


def cmd_discover(args: argparse.Namespace) -> int:
    d = detect(Path(args.home) if args.home else None)
    for title, items in (("Saved Games", d.saved_games), ("Foothold saves", d.foothold_saves),
                         ("DCSServerBot (candidates)", d.dcsserverbot), ("Tacview", d.tacview)):
        print(f"{title}:")
        print("\n".join(f"  {i.path}  {('- ' + i.note) if i.note else ''}" for i in items) or "  (none found)")
    if args.describe:
        found = locate_persistence_file(Path(args.describe))
        print(f"\nStructure of the Foothold file (values redacted):\n{describe_structure(found)}" if found
              else f"\nNo Foothold file found in {args.describe}")
    return 0


def _pairing_code(args: argparse.Namespace) -> str:
    """From --code, or (preferred, keeps it out of the process list and shell history) the first line of stdin."""
    return (args.code if args.code is not None else sys.stdin.readline()).strip()


def cmd_pair(args: argparse.Namespace) -> int:
    cfg = load_config(Path(args.config))
    verify: bool | str = cfg.central.ca_file or cfg.central.verify_tls
    client = CentralClient(cfg.central.url, verify=verify)
    code = _pairing_code(args)
    if not code:
        print("Error: no pairing code given")
        return 2
    try:
        r = client.pair(code, args.name, __version__)
    except httpx.HTTPStatusError as e:
        print(f"Pairing refused ({e.response.status_code}): the code is invalid, already used or expired.")
        return 1
    except httpx.TransportError as e:
        print(f"Cannot reach {cfg.central.url}: {type(e).__name__}")
        return 1
    CredentialStore(cfg.state_dir, cfg.central.api_key_env).save(Credentials(r["agent_id"], r["api_key"], r["server_id"]))
    print("Paired. The key is stored protected on this PC.")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    cfg = load_config(Path(args.config))
    try:
        central_client(cfg).get_config()
        print("Central: OK (authenticated)")
    except (NotPairedError, httpx.HTTPError) as e:
        print(f"Central: FAILED ({e})")
        return 1
    agent = build_agent(cfg)
    agent.tick()
    for s in agent._p.sources:  # noqa: SLF001  (diagnostic command)
        w = s.warnings()
        print(f"{s.name}: " + ("OK" if not w else "; ".join(f"{x.code} {x.message}" for x in w)))
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    agent = build_agent(load_config(Path(args.config)))
    signal.signal(signal.SIGTERM, lambda *_: agent.stop())
    try:
        agent.run()
    except KeyboardInterrupt:
        agent.stop()
    return 0


def _state_dir(args: argparse.Namespace) -> Path | None:
    """State folder of the configured agent (where agent.log lives); None when there is no usable config."""
    if getattr(args, "cmd", "") not in ("run", "check", "diagnose"):
        return None
    try:
        return load_config(Path(args.config)).state_dir
    except ConfigError:
        return None


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="fox3-agent")
    sub = ap.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("discover", help="find DCS, Foothold, DCSServerBot and Tacview folders")
    d.add_argument("--home", help="user profile folder to scan (default: current user)")
    d.add_argument("--describe", metavar="SAVES_DIR", help="print a redacted outline of the Foothold file in this folder")
    g = sub.add_parser("diagnose", help="redacted support report to send us after the first test on a real server")
    g.add_argument("--config", default="agent.toml")
    g.add_argument("--saves-dir", help="Foothold saves folder (default: the configured or discovered one)")
    g.add_argument("--tacview-dir", help="Tacview recordings folder (default: the configured or discovered one)")
    g.add_argument("--home", help="user profile folder to scan (default: current user)")
    g.add_argument("--out", metavar="FILE", help="also write the report to this file")
    i = sub.add_parser("init", help="write a minimal agent.toml (never overwrites)")
    i.add_argument("--central-url", required=True)
    i.add_argument("--out", required=True, metavar="DIR")
    i.add_argument("--state-dir", help="default: <out>/state")
    i.add_argument("--dcsbot-api-key-env", metavar="NAME", help="NAME of the environment variable holding the DCSServerBot API key")
    for name in ("pair", "check", "run"):
        p = sub.add_parser(name)
        p.add_argument("--config", default="agent.toml")
        if name == "pair":
            group = p.add_mutually_exclusive_group(required=True)
            group.add_argument("--code", help="pairing code (visible in the process list: prefer --code-stdin)")
            group.add_argument("--code-stdin", dest="code", action="store_const", const=None, help="read the code from standard input")
            p.add_argument("--name", default="fox3-agent")
    register_setup(sub)
    args = ap.parse_args(argv)
    logsetup.silence_missing_streams()
    state_dir = _state_dir(args)
    logsetup.configure(state_dir, to_file=args.cmd == "run")
    if state_dir is not None:
        SecretStore(state_dir).export_to_environ()  # `fox3-agent secret set fox3_dcsbot_api_key` -> env FOX3_DCSBOT_API_KEY
    try:
        handlers = {"init": cmd_init, "diagnose": cmd_diagnose, "discover": cmd_discover, "pair": cmd_pair, "check": cmd_check,
                    "run": cmd_run, **SETUP_HANDLERS}
        return handlers[args.cmd](args)
    except (ConfigError, NotPairedError) as e:
        print(f"Error: {e}")
        logging.getLogger("fox3_agent").error("%s", e)  # windowless runs have no console: the log file is the only trace
        return 2


if __name__ == "__main__":
    sys.exit(main())
