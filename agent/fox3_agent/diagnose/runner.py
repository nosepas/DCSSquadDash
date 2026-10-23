"""Runs every diagnose section best-effort and renders the redacted report."""
from __future__ import annotations

import os
from pathlib import Path

from ..config import ConfigError, load_config
from ..runtime.settings import merge
from .context import Context
from .report import Report
from .s_dcsbot import dcsbot_rest
from .s_dcsbot_db import dcsbot_db
from .s_discover import discover
from .s_foothold import foothold
from .s_tacview import tacview
from .s_versions import config_summary, pairing, versions

FOOTER = [
    "## What to send",
    "Paste this whole report in the chat (it is redacted: no names, keys, ucids or user folders).",
    "Read it once before sending; if anything personal slipped through, replace it with <x>.",
]


def build_context(config_path: Path, saves_dir: Path | None, tacview_dir: Path | None, home: Path | None = None) -> Context:
    ctx = Context(config_path=config_path, saves_dir=saves_dir, tacview_dir=tacview_dir, home=home, environ=os.environ)
    try:
        ctx.config = load_config(config_path)
    except ConfigError:
        ctx.config_error = "agent.toml missing or invalid (run `fox3-agent init`)"
    return ctx


def _first(items: list | None) -> Path | None:
    return items[0].path if items else None


def _resolve_folders(ctx: Context) -> None:
    """Folders not given on the command line: admin-panel values, then the local file, then the first discovered one."""
    det = ctx.extras.get("detected")
    eff = merge(ctx.config, ctx.remote) if ctx.config else None
    if ctx.saves_dir is None:
        ctx.saves_dir = (eff.foothold_dir if eff else None) or _first(det.foothold_saves if det else None)
    if ctx.tacview_dir is None:
        ctx.tacview_dir = (eff.tacview_dir if eff else None) or _first(det.tacview if det else None)


def run_diagnose(ctx: Context) -> str:
    rep = Report()
    rep.run("1. Versions", lambda s: versions(ctx, s))
    rep.run("1b. Configuration summary", lambda s: config_summary(ctx, s))
    rep.run("1c. Pairing", lambda s: pairing(ctx, s))
    rep.run("2. Discover", lambda s: discover(ctx, s))
    _resolve_folders(ctx)
    rep.run("3. Foothold", lambda s: foothold(ctx, s))
    rep.run("4. Tacview", lambda s: tacview(ctx, s))
    rep.run("5. DCSServerBot REST", lambda s: dcsbot_rest(ctx, s))
    rep.run("5b. DCSServerBot database", lambda s: dcsbot_db(ctx, s))
    return rep.render(FOOTER)
