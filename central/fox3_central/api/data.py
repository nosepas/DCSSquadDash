"""Login-required read endpoints: overview, objectives, ranking, kills, pilots, profiles, account linking."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ..repositories import events, players
from ..services import aircraft, mapdata, overview, profile, ranking
from .deps import Ctx, ServerId, User, require_user

router = APIRouter(dependencies=[Depends(require_user)], tags=["data"])
Limit = Annotated[int, Query(ge=1, le=200)]


@router.get("/servers/{server_id}/overview")
def get_overview(server_id: ServerId, ctx: Ctx):
    with ctx.engine.connect() as cn:
        return overview.build(cn, server_id)


@router.get("/servers/{server_id}/objectives")
def objectives(server_id: ServerId, ctx: Ctx):
    with ctx.engine.connect() as cn:
        return mapdata.build_map(cn, server_id)["zones"]


@router.get("/servers/{server_id}/farps")
def farps(server_id: ServerId, ctx: Ctx):
    """Player-built FARPs of a Foothold server (login required: they are tactical information, unlike the zone map)."""
    with ctx.engine.connect() as cn:
        return mapdata.farps(cn, server_id)


@router.get("/servers/{server_id}/ranking")
def get_ranking(server_id: ServerId, ctx: Ctx, sort: str = "points", limit: Limit = 50):
    with ctx.engine.connect() as cn:
        return ranking.build(cn, server_id, sort, limit)


@router.get("/servers/{server_id}/kills")
def kills(server_id: ServerId, ctx: Ctx, limit: Limit = 50, before: str | None = None):
    with ctx.engine.connect() as cn:
        return events.list_events(cn, server_id, ("kill",), limit, before)


@router.get("/servers/{server_id}/aircraft")
def allied_aircraft(server_id: ServerId, ctx: Ctx, user: User, coalition: str | None = None):
    """Friendly aircraft only: the viewer's own coalition (admins may choose)."""
    with ctx.engine.connect() as cn:
        return aircraft.allied_aircraft(cn, server_id, user.user_id, user.is_admin, coalition)


@router.get("/servers/{server_id}/players/online")
def online(server_id: ServerId, ctx: Ctx, user: User):
    """Who is connected. Only administrators get coalition, aircraft, slot and position (the allied-aircraft rule must not be bypassed)."""
    with ctx.engine.connect() as cn:
        rows = players.list_online(cn, server_id)
    return rows if user.is_admin else [{"name": r["name"]} for r in rows]


@router.get("/players")
def search_players(ctx: Ctx, q: Annotated[str, Query(min_length=2, max_length=64)], limit: Limit = 20):
    with ctx.engine.connect() as cn:
        return players.search(cn, q, limit)


@router.get("/players/{ucid}")
def get_profile(ucid: str, ctx: Ctx):
    return profile.build(ctx, profile.validate_ucid(ucid))


@router.post("/link/start")
def link_start(ctx: Ctx, user: User):
    return profile.start_link(ctx, user.user_id)
