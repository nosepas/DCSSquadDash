"""Tacview search: where and when did a pilot appear (server, file, aircraft, UTC time, offset). No replay."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from ..context import Context
from ..core.errors import Invalid
from ..repositories import tacview

MAX_APPEARANCES = 5000


def check_payload(p: dict) -> None:
    """Defence in depth on top of the JSON Schema: no absolute or escaping paths, bounded size."""
    path = p["file"]["relative_path"].replace("\\", "/")
    if path.startswith("/") or ":" in path.split("/")[0] or ".." in path.split("/"):
        raise Invalid("relative_path must be relative to the Tacview folder")
    if len(p["appearances"]) > MAX_APPEARANCES:
        raise Invalid(f"too many appearances (max {MAX_APPEARANCES})")


def _utc(reference: str | None, offset_s: float) -> str | None:
    if not reference:
        return None
    base = datetime.fromisoformat(reference.replace("Z", "+00:00")).astimezone(UTC)
    return (base + timedelta(seconds=offset_s)).strftime("%Y-%m-%dT%H:%M:%SZ")


def search(ctx: Context, pilot: str, limit: int, server_id: str | None) -> list[dict]:
    with ctx.engine.connect() as cn:
        rows = tacview.search(cn, pilot, limit, server_id)
    return [{"file_id": r["file_id"], "server_id": r["server_id"], "server_name": r["server_name"], "file": r["relative_path"], "pilot": r["pilot"],
             "aircraft": r["aircraft"], "coalition": r["coalition"], "complete": r["complete"],
             "first_utc": _utc(r["reference_time"], r["first_offset_s"]), "last_utc": _utc(r["reference_time"], r["last_offset_s"]),
             "first_offset_s": r["first_offset_s"], "last_offset_s": r["last_offset_s"]} for r in rows]
