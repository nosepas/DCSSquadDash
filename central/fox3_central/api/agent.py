"""Agent -> central endpoints (contracts/openapi-agent.yaml). Thin: validation and logic live in services."""
from __future__ import annotations

from fastapi import APIRouter, Request
from pydantic import BaseModel, Field

from ..models.settings import revision
from ..repositories import servers
from ..services import agents as agent_service
from ..services import ingest, profile
from .deps import AgentServer, Ctx

router = APIRouter(prefix="/agent/v1", tags=["agent"])


def _ack(applied: bool) -> dict:
    return {"ok": True} if applied else {"ok": True, "duplicate": True}


class PairIn(BaseModel):
    pairing_code: str = Field(max_length=32)
    agent_name: str | None = Field(None, max_length=80)
    agent_version: str | None = Field(None, max_length=40)
    host_os: str | None = Field(None, max_length=80)


@router.post("/pair")
def pair(body: PairIn, request: Request, ctx: Ctx):
    ip = request.client.host if request.client else "unknown"
    return agent_service.pair(ctx, body.pairing_code, body.agent_name, body.agent_version, ip)


@router.get("/config")
def config(ctx: Ctx, server_id: AgentServer):
    """Settings the admin edits in the web panel. `revision` changes whenever they do; the agent applies them live."""
    with ctx.engine.connect() as cn:
        s = servers.get(cn, server_id)
    settings = servers.settings_of(s)
    return {"revision": revision(settings, s["mission_type"]), "mission_type": s["mission_type"], "settings": settings,
            "intervals": {"heartbeat_s": 30, "players_s": 10, "foothold_s": 15, "server_info_s": 60},
            "max_raw_bytes": ctx.settings.max_raw_bytes}


def _register(path: str, kind: str) -> None:
    @router.post(path, name=kind)
    def endpoint(body: dict, ctx: Ctx, server_id: AgentServer):
        return _ack(ingest.ingest(ctx, server_id, kind, body))


for _path, _kind in (("/heartbeat", "heartbeat"), ("/server-info", "server_info"), ("/foothold-state", "foothold_state"),
                     ("/players", "players"), ("/events", "events"), ("/tacview-index", "tacview_index"),
                     ("/discord-links", "discord_links")):
    _register(_path, _kind)


@router.post("/link-codes")
def link_codes(body: dict, ctx: Ctx, _server_id: AgentServer):
    ucid = profile.validate_ucid(str(body.get("ucid", "")))
    profile.complete_link(ctx, str(body.get("code", "")), ucid, body.get("player_name"))
    return {"ok": True}
