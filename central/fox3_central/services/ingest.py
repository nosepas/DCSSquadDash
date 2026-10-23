"""Agent message ingestion: validate against contracts, de-duplicate, persist."""
from __future__ import annotations

from collections.abc import Callable

from sqlalchemy.engine import Connection

from ..context import Context
from ..core.errors import Invalid
from ..core.validation import ENVELOPE
from ..repositories import agents, events, foothold, players, servers, tacview
from . import discord_links
from . import tacview as tacview_service

Handler = Callable[[Context, Connection, str, dict], None]


def _heartbeat(ctx: Context, cn: Connection, sid: str, p: dict) -> None:
    from ..core.clock import now
    servers.set_status(cn, sid, heartbeat={**p, "received_at": now()})


def _server_info(ctx: Context, cn: Connection, sid: str, p: dict) -> None:
    servers.set_status(cn, sid, info=p)
    changes = {"mission_type": p["mission_type"]}
    if p.get("terrain"):
        changes["terrain"] = p["terrain"]
    servers.update_fields(cn, sid, **changes)


def _foothold_state(ctx: Context, cn: Connection, sid: str, p: dict) -> None:
    if len(str(p.get("raw", ""))) > ctx.settings.max_raw_bytes:
        p.pop("raw")
    foothold.save_state(cn, sid, p)
    for s in p.get("player_stats", []):
        ucid = s.get("ucid") or players.find_ucid_by_name(cn, s["name"])  # Foothold may key stats by name only
        if ucid:
            players.touch(cn, ucid, s["name"])
            players.save_stats(cn, sid, ucid, s.get("points"), s.get("stats", {}))


def _players(ctx: Context, cn: Connection, sid: str, p: dict) -> None:
    for pl in p["players"]:
        players.touch(cn, pl["ucid"], pl["name"])
    players.replace_online(cn, sid, p["players"])


def _events(ctx: Context, cn: Connection, sid: str, p: dict) -> None:
    for e in p["events"]:
        for side in (e.get("actor"), e.get("target")):
            if side and side.get("ucid"):
                players.touch(cn, side["ucid"], side.get("name"))
        events.insert_event(cn, sid, e)


def _tacview_index(ctx: Context, cn: Connection, sid: str, p: dict) -> None:
    tacview_service.check_payload(p)
    tacview.replace_file(cn, sid, p)


def _discord_links(ctx: Context, cn: Connection, sid: str, p: dict) -> None:
    discord_links.ingest_claims(cn, sid, p["links"])


HANDLERS: dict[str, Handler] = {
    "tacview_index": _tacview_index,
    "heartbeat": _heartbeat, "server_info": _server_info, "foothold_state": _foothold_state,
    "players": _players, "events": _events, "discord_links": _discord_links,
}


def ingest(ctx: Context, server_id: str, kind: str, body: dict) -> bool:
    """Process one agent message. Returns False if it was a duplicate (already applied)."""
    errors = ctx.validators.errors(ENVELOPE, body) or ctx.validators.errors(kind, body.get("payload"))
    if errors:
        raise Invalid("payload does not match the contract", errors)
    if body["schema_version"] != 1:
        raise Invalid("unsupported schema_version")
    with ctx.tx() as cn:
        if not agents.mark_seen(cn, server_id, body["message_id"]):
            return False
        HANDLERS[kind](ctx, cn, server_id, body["payload"])
    ctx.bump(server_id)
    return True
