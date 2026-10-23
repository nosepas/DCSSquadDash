"""Message envelope (contracts/schemas/common.json#/$defs/envelope)."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

SCHEMA_VERSION = 1

# message kind -> agent API path
PATHS = {"heartbeat": "/heartbeat", "server_info": "/server-info", "foothold_state": "/foothold-state",
         "players": "/players", "events": "/events", "tacview_index": "/tacview-index",
         "discord_links": "/discord-links"}


def utc_now() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")


def envelope(payload: dict) -> dict:
    return {"schema_version": SCHEMA_VERSION, "message_id": str(uuid.uuid4()), "sent_at": utc_now(), "payload": payload}
