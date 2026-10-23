"""Missions and coalition accounts."""
from __future__ import annotations

import hashlib
from typing import Any

from .coerce import Notes, flag, get, items, num, text


def mission_id(index: int, title: str) -> str:
    """Stable id: position in the list + short hash of the title (changes only if either changes)."""
    return f"m{index}-{hashlib.sha1(title.encode('utf-8', 'replace')).hexdigest()[:8]}"


def normalize_missions(raw: Any, notes: Notes) -> list[dict]:
    out, dropped = [], 0
    for index, rec in items(raw):
        title = text(get(rec, "title"), 200)
        if not isinstance(rec, dict) or not title:
            dropped += 1
            continue
        extra: dict[str, Any] = {}
        if text(rec.get("description"), 400) is not None:
            extra["description"] = text(rec["description"], 400)
        if flag(rec.get("isEscortMission")) is not None:
            extra["is_escort_mission"] = rec["isEscortMission"]
        state = "active" if rec.get("isRunning") is True else "available"
        out.append({"id": mission_id(index, title), "title": title, "state": state, "extra": extra})
    notes.dropped("missions", dropped, "entries without a title")
    return out


def normalize_accounts(raw: Any) -> dict[str, float]:
    """accounts[1] = red credits, accounts[2] = blue credits."""
    accounts: dict[str, float] = {}
    for key, side in ((1, "red"), (2, "blue")):
        value = dict(items(raw)).get(key)
        if num(value) is not None:
            accounts[side] = value
    return accounts
