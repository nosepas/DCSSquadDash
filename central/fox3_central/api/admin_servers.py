"""Admin: servers and their settings (everything the agent needs is configured here, not on the server PC)."""
from __future__ import annotations

from typing import Annotated, Literal

from fastapi import APIRouter, Depends, Response
from pydantic import BaseModel, Field, StringConstraints

from ..core.errors import NotFound
from ..models.settings import ADDRESS, ServerSettings
from ..repositories import servers
from ..services import agents as agent_service
from ..services import status
from .deps import Ctx, require_admin

router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)], tags=["admin"])
Address = Annotated[str | None, StringConstraints(strip_whitespace=True, max_length=120, pattern=ADDRESS.pattern)]


class ServerIn(BaseModel):
    name: str = Field(min_length=1, max_length=80)
    mission_type: Literal["foothold", "generic"] = "foothold"


class ServerPatch(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=80)
    mission_type: Literal["foothold", "generic"] | None = None
    address: Address = None  # public IP:port players use to join (informative)
    description: str | None = Field(None, max_length=500)
    enabled: bool | None = None
    settings: ServerSettings | None = None  # replaced as a whole (validated, defaults filled in)


def _existing(cn, server_id: str) -> dict:
    server = servers.get(cn, server_id)
    if not server:
        raise NotFound("server not found")
    return server


@router.get("/servers")
def list_servers(ctx: Ctx):
    with ctx.engine.connect() as cn:
        return [status.admin_detail(ctx, cn, s) for s in servers.list_all(cn)]


@router.post("/servers", status_code=201)
def create_server(body: ServerIn, ctx: Ctx):
    with ctx.tx() as cn:
        created = servers.create(cn, body.name, body.mission_type)
        return status.admin_detail(ctx, cn, created)


@router.get("/servers/{server_id}")
def server_detail(server_id: str, ctx: Ctx):
    with ctx.engine.connect() as cn:
        return status.admin_detail(ctx, cn, _existing(cn, server_id))


@router.patch("/servers/{server_id}")
def patch_server(server_id: str, body: ServerPatch, ctx: Ctx):
    changes = body.model_dump(exclude_unset=True)
    with ctx.tx() as cn:
        _existing(cn, server_id)
        servers.update_fields(cn, server_id, **changes)
        return status.admin_detail(ctx, cn, _existing(cn, server_id))


@router.delete("/servers/{server_id}", status_code=204)
def delete_server(server_id: str, ctx: Ctx):
    with ctx.tx() as cn:
        servers.delete_server(cn, server_id)
    return Response(status_code=204)


@router.post("/servers/{server_id}/pairing-code", status_code=201)
def pairing_code(server_id: str, ctx: Ctx):
    return agent_service.create_pairing_code(ctx, server_id)
