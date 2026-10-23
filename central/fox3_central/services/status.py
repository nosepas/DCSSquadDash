"""Server/agent liveness and the admin view of one server."""
from __future__ import annotations

from sqlalchemy.engine import Connection

from ..context import Context
from ..core.clock import ago
from ..repositories import agents, servers


def is_online(ctx: Context, status: dict) -> bool:
    seen = (status.get("heartbeat") or {}).get("received_at")
    return bool(seen) and seen >= ago(seconds=ctx.settings.online_timeout_s)


def admin_detail(ctx: Context, cn: Connection, server: dict) -> dict:
    """Everything the admin panel needs about one server: settings with defaults, agent health, detected folders."""
    status = servers.get_status(cn, server["server_id"])
    hb = status.get("heartbeat") or {}
    return {
        **{k: v for k, v in server.items() if k != "settings"},
        "settings": servers.settings_of(server),
        "online": is_online(ctx, status),
        "agents": [a for a in agents.list_all(cn) if a["server_id"] == server["server_id"]],
        "agent": {"version": hb.get("agent_version"), "last_seen": hb.get("received_at"), "queue_depth": hb.get("queue_depth"),
                  "warnings": hb.get("warnings", []), "detected": hb.get("detected", {}), "last_success": hb.get("last_success", {})},
    }
