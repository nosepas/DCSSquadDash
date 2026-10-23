"""Endpoints open without login: server list, map and missions. Nothing else may be added here."""
from __future__ import annotations

from fastapi import APIRouter

from ..repositories import servers
from ..services import mapdata
from ..services.status import is_online
from .deps import Ctx, ServerId

router = APIRouter(tags=["public"])


@router.get("/servers")
def list_servers(ctx: Ctx):
    with ctx.engine.connect() as cn:
        return [{"server_id": s["server_id"], "name": s["name"], "mission_type": s["mission_type"], "terrain": s["terrain"],
                 "online": is_online(ctx, servers.get_status(cn, s["server_id"]))}
                for s in servers.list_all(cn, only_enabled=True)]


@router.get("/servers/{server_id}/map")
def server_map(server_id: ServerId, ctx: Ctx):
    with ctx.engine.connect() as cn:
        return mapdata.build_map(cn, server_id)


@router.get("/servers/{server_id}/missions")
def server_missions(server_id: ServerId, ctx: Ctx):
    with ctx.engine.connect() as cn:
        return mapdata.missions(cn, server_id)
