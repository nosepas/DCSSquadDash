"""Section 2: what `discover` finds on this PC (user names redacted by the final pass)."""
from __future__ import annotations

from ..detect import detect
from .context import Context
from .report import Section


def discover(ctx: Context, sec: Section) -> None:
    d = detect(ctx.home)
    ctx.extras["detected"] = d
    for title, items in (("Saved Games", d.saved_games), ("Foothold saves", d.foothold_saves),
                         ("DCSServerBot candidates", d.dcsserverbot), ("Tacview", d.tacview)):
        sec.line(f"  {title}:")
        for i in items[:10]:
            sec.line(f"    {i.path}  {('- ' + i.note) if i.note else ''}".rstrip())
        if not items:
            sec.line("    (none found)")
    if not d.saved_games:
        sec.flag("no DCS Saved Games folder found for this Windows user (is the agent run as the user that runs DCS?)")
