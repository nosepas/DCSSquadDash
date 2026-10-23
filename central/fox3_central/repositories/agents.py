from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import insert, select, update
from sqlalchemy.engine import Connection

from ..core.clock import now
from ..db import tables as t
from ..db.utils import insert_ignore

Row = dict[str, Any]


def create_pending(cn: Connection, server_id: str, pairing_hash: str, expires_at: str) -> str:
    agent_id = str(uuid.uuid4())
    cn.execute(insert(t.agents).values(agent_id=agent_id, server_id=server_id, pairing_hash=pairing_hash, pairing_expires_at=expires_at))
    return agent_id


def get(cn: Connection, agent_id: str) -> Row | None:
    r = cn.execute(select(t.agents).where(t.agents.c.agent_id == agent_id)).mappings().first()
    return dict(r) if r else None


def find_by_pairing_hash(cn: Connection, pairing_hash: str) -> Row | None:
    r = cn.execute(select(t.agents).where(t.agents.c.pairing_hash == pairing_hash)).mappings().first()
    return dict(r) if r else None


def complete_pairing(cn: Connection, agent_id: str, key_hash: str, name: str | None, version: str | None) -> None:
    cn.execute(update(t.agents).where(t.agents.c.agent_id == agent_id)
               .values(key_hash=key_hash, pairing_hash=None, name=name, agent_version=version))


def touch(cn: Connection, agent_id: str) -> None:
    cn.execute(update(t.agents).where(t.agents.c.agent_id == agent_id).values(last_seen_at=now()))


def revoke(cn: Connection, agent_id: str) -> bool:
    return cn.execute(update(t.agents).where(t.agents.c.agent_id == agent_id, t.agents.c.revoked_at.is_(None))
                      .values(revoked_at=now())).rowcount > 0


def list_all(cn: Connection) -> list[Row]:
    cols = [c for c in t.agents.c if c.name not in ("key_hash", "pairing_hash")]
    return [dict(r) for r in cn.execute(select(*cols).order_by(t.agents.c.created_at)).mappings()]


def mark_seen(cn: Connection, server_id: str, message_id: str) -> bool:
    """Idempotency: True if this message_id is new for the server."""
    return insert_ignore(cn, t.messages_seen, server_id=server_id, message_id=message_id, received_at=now())
