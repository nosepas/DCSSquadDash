"""Folders found on this PC, in the shape of the heartbeat `detected` field (suggestions for the admin, never applied automatically)."""
from __future__ import annotations

from ..detect import detect


def detected_folders() -> dict:
    d = detect()
    out = {"saved_games": d.saved_games, "foothold_saves": d.foothold_saves, "dcsserverbot": d.dcsserverbot, "tacview": d.tacview}
    return {k: [{"path": str(i.path)[:260], "note": i.note[:120]} for i in items[:10]] for k, items in out.items() if items}
