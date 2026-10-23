"""`init` and `diagnose` command handlers."""
from __future__ import annotations

import argparse
from pathlib import Path

from .diagnose.runner import build_context, run_diagnose
from .scaffold import ScaffoldError, write_agent_toml


def cmd_init(args: argparse.Namespace) -> int:
    try:
        path = write_agent_toml(Path(args.out), args.central_url, Path(args.state_dir) if args.state_dir else None,
                                args.dcsbot_api_key_env)
    except (ScaffoldError, OSError) as e:
        print(f"Error: {e}")
        return 1
    print(f"Wrote {path}. Next: fox3-agent pair --config \"{path}\" --code-stdin")
    return 0


def cmd_diagnose(args: argparse.Namespace) -> int:
    ctx = build_context(Path(args.config), Path(args.saves_dir) if args.saves_dir else None,
                        Path(args.tacview_dir) if args.tacview_dir else None, Path(args.home) if args.home else None)
    text = run_diagnose(ctx)
    print(text)
    if args.out:
        try:
            Path(args.out).write_text(text, "utf-8")
            print(f"Report also saved to {Path(args.out).name}")
        except OSError as e:
            print(f"Could not save the report: {e.strerror or type(e).__name__}")
            return 1
    return 0
