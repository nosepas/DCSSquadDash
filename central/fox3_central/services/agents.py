"""Agent pairing and API-key authentication."""
from __future__ import annotations

import uuid

from ..context import Context
from ..core.clock import after, now
from ..core.errors import BadRequest, NotFound, RateLimited, Unauthorized
from ..core.security import safe_equal, sha256, short_code, token
from ..repositories import agents, servers


def create_pairing_code(ctx: Context, server_id: str, ttl_minutes: int = 15) -> dict:
    """Create a pending agent for the server and return the one-time code (shown once)."""
    code = short_code()
    with ctx.tx() as cn:
        if not servers.get(cn, server_id):
            raise NotFound("server not found")
        agent_id = agents.create_pending(cn, server_id, sha256(code), after(minutes=ttl_minutes))
    return {"agent_id": agent_id, "pairing_code": code, "expires_in_minutes": ttl_minutes}


def pair(ctx: Context, code: str, name: str | None, version: str | None, client_ip: str) -> dict:
    if not ctx.limiter.allow(f"pair:{client_ip}", 10):
        raise RateLimited()
    with ctx.tx() as cn:
        agent = agents.find_by_pairing_hash(cn, sha256(code)) if code else None
        if not agent or agent["key_hash"] or (agent["pairing_expires_at"] or "") < now():
            raise BadRequest("invalid, used or expired pairing code")
        secret = token()
        agents.complete_pairing(cn, agent["agent_id"], sha256(secret), name, version)
    return {"agent_id": agent["agent_id"], "api_key": f"{agent['agent_id']}.{secret}", "server_id": agent["server_id"]}


def authenticate(ctx: Context, authorization: str, client_ip: str = "unknown") -> tuple[str, str]:
    """Validate 'Bearer <agent_id>.<secret>'. Returns (agent_id, server_id)."""
    scheme, _, key = authorization.partition(" ")
    agent_id, _, secret = key.partition(".")
    if scheme.lower() != "bearer" or not secret or not _is_uuid(agent_id):
        _failed(ctx, client_ip)
        raise Unauthorized("missing or malformed key")
    with ctx.tx() as cn:
        agent = agents.get(cn, agent_id)
        if not agent or agent["revoked_at"] or not agent["key_hash"] or not safe_equal(agent["key_hash"], sha256(secret)):
            _failed(ctx, client_ip)
            raise Unauthorized("invalid or revoked key")
        agents.touch(cn, agent_id)
    if not ctx.limiter.allow(f"agent:{agent_id}", 600):  # only a VALID agent is counted per agent id: no lock-out by guessing
        raise RateLimited()
    return agent_id, agent["server_id"]


def _is_uuid(value: str) -> bool:
    try:
        return str(uuid.UUID(value)) == value.lower()
    except ValueError:
        return False


def _failed(ctx: Context, client_ip: str) -> None:
    """Bad credentials are limited per client address, never per attacker-supplied identifier."""
    if not ctx.limiter.allow(f"agent-auth-fail:{client_ip}", 60):
        raise RateLimited()
