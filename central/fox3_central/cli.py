"""`fox3-central` command line: check-config | migrate | serve."""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import scaffold
from .db import migrate
from .settings_file import SettingsError, load


def _settings(args: argparse.Namespace):
    return load(Path(args.config))


def cmd_init(args: argparse.Namespace) -> int:
    out = Path(args.out)
    written = scaffold.write_missing(out, {
        "central.toml": scaffold.central_toml(args.hostname, args.port, args.admin_id, args.discord_client_id, args.agent_dir),
        "Caddyfile": scaffold.caddyfile(args.hostname, args.port)})
    print(f"Written: {', '.join(written) if written else 'nothing (the files already exist and were kept)'} in {out}")
    return 0


def cmd_check(args: argparse.Namespace) -> int:
    settings, listen = _settings(args)
    print(f"Configuration OK: public URL {settings.public_base_url}, listening on {listen['bind']}:{listen['port']}, "
          f"Discord {'on' if settings.discord_enabled else 'off'}, {len(settings.admin_ids)} admin id(s).")
    return 0


def cmd_migrate(args: argparse.Namespace) -> int:
    settings, _ = _settings(args)
    from sqlalchemy import create_engine
    migrate.upgrade(create_engine(settings.db_url))
    print("Database is up to date.")
    return 0


def cmd_serve(args: argparse.Namespace) -> int:
    import uvicorn

    from .app import create_app

    settings, listen = _settings(args)
    app = create_app(settings)  # runs the migrations before serving
    # ONE process: live updates (SSE) and the Tacview relay keep their state in memory
    uvicorn.run(app, host=listen["bind"], port=listen["port"], workers=1, proxy_headers=True, forwarded_allow_ips="127.0.0.1")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="fox3-central")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, helptext in (("check-config", "validate the configuration file"), ("migrate", "bring the database schema up to date"),
                           ("serve", "run the web server (applies migrations first)")):
        sub.add_parser(name, help=helptext).add_argument("--config", default="central.toml")
    init = sub.add_parser("init", help="write central.toml and the Caddyfile (existing files are kept)")
    init.add_argument("--hostname", required=True)
    init.add_argument("--out", required=True)
    init.add_argument("--port", type=int, default=8000)
    init.add_argument("--admin-id", action="append", default=[], help="Discord user id of an administrator (repeatable)")
    init.add_argument("--discord-client-id", default="")
    init.add_argument("--agent-dir", default="", help="folder with the built agent (fox3-agent.exe) offered for download")
    args = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(name)s %(message)s")
    try:
        return {"init": cmd_init, "check-config": cmd_check, "migrate": cmd_migrate, "serve": cmd_serve}[args.cmd](args)
    except (SettingsError, migrate.LegacyDatabaseError, ValueError) as exc:
        print(f"Error: {exc}")
        return 2


if __name__ == "__main__":
    sys.exit(main())
