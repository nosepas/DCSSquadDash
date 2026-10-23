"""Periodic cleanup of tables that would otherwise grow without bound."""
from __future__ import annotations

from sqlalchemy import delete, or_
from sqlalchemy.engine import Connection

from ..core.clock import ago, now
from ..db import auth_tables as a
from ..db import tables as t


def purge(cn: Connection, seen_days: int = 7) -> dict[str, int]:
    """Delete expired/obsolete rows. Returns how many were removed per table (for the log)."""
    current = now()
    removed = {
        "messages_seen": cn.execute(delete(t.messages_seen).where(t.messages_seen.c.received_at < ago(days=seen_days))).rowcount,
        "sessions": cn.execute(delete(a.sessions).where(a.sessions.c.expires_at < current)).rowcount,
        "oauth_states": cn.execute(delete(a.oauth_states).where(a.oauth_states.c.expires_at < current)).rowcount,
        "link_codes": cn.execute(delete(a.link_codes).where(
            or_(a.link_codes.c.expires_at < ago(days=1), a.link_codes.c.used_at.is_not(None)))).rowcount,
        "pending_agents": cn.execute(delete(t.agents).where(t.agents.c.key_hash.is_(None), t.agents.c.pairing_expires_at < ago(days=1))).rowcount,
    }
    return removed
