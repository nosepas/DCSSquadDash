"""Admin: agents (list, revoke) and user roles. Every mutation is admin-only and CSRF-protected."""
from __future__ import annotations

from typing import Literal

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel

from ..core.errors import NotFound
from ..repositories import agents, users
from .deps import Ctx, require_admin

router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)], tags=["admin"])


class RoleIn(BaseModel):
    role: Literal["user", "admin"]


@router.get("/agents")
def list_agents(ctx: Ctx):
    with ctx.engine.connect() as cn:
        return agents.list_all(cn)


@router.post("/agents/{agent_id}/revoke", status_code=204)
def revoke_agent(agent_id: str, ctx: Ctx):
    with ctx.tx() as cn:
        if not agents.revoke(cn, agent_id):
            raise NotFound("agent not found or already revoked")
    return Response(status_code=204)


@router.get("/users")
def list_users(ctx: Ctx):
    with ctx.engine.connect() as cn:
        return users.list_all(cn)


@router.put("/users/{user_id}/role", status_code=204)
def set_role(user_id: int, body: RoleIn, ctx: Ctx):
    with ctx.tx() as cn:
        if not users.set_role(cn, user_id, body.role):
            raise NotFound("user not found")
    return Response(status_code=204)
