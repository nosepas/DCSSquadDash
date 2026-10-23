"""Discord <-> UCID pairs claimed by agents (read from DCSServerBot). Claims are not links: see services/discord_links."""
from __future__ import annotations

from sqlalchemy import exists, func, select
from sqlalchemy.engine import Connection

from ..core.clock import ago, now
from ..db import tables as t
from ..db.auth_tables import discord_link_claims as c
from ..db.utils import upsert


def save(cn: Connection, server_id: str, ucid: str, discord_id: int) -> bool:
    """Stores or renews the claim. True when it is new or names a different Discord id (worth an audit line)."""
    before = cn.execute(select(c.c.discord_id).where(c.c.server_id == server_id, c.c.ucid == ucid)).scalar()
    upsert(cn, c, {"server_id": server_id, "ucid": ucid}, discord_id=discord_id, updated_at=now())
    return before != discord_id


def count_for_server(cn: Connection, server_id: str) -> int:
    return cn.execute(select(func.count()).select_from(c).where(c.c.server_id == server_id)).scalar() or 0


# Agents resend every pair every few hours, so a claim nobody renewed for this long is stale (unlinked, or server gone).
FRESH_DAYS = 3


def _fresh():
    return c.c.updated_at >= ago(days=FRESH_DAYS)


def ucids_for_discord(cn: Connection, discord_id: int) -> list[str]:
    return sorted({r[0] for r in cn.execute(select(c.c.ucid).where(c.c.discord_id == discord_id, _fresh()))})


def seen_on_claiming_server(cn: Connection, ucid: str, discord_id: int) -> bool:
    """True when a server that claims this pair has really seen the ucid (stats or online) - a bare claim is not enough."""
    seen = (exists().where(t.player_stats.c.server_id == c.c.server_id, t.player_stats.c.ucid == c.c.ucid)
            | exists().where(t.online_players.c.server_id == c.c.server_id, t.online_players.c.ucid == c.c.ucid))
    q = select(c.c.server_id).where(c.c.ucid == ucid, c.c.discord_id == discord_id, _fresh(), seen).limit(1)
    return cn.execute(q).first() is not None


def delete_for_server(cn: Connection, server_id: str) -> None:
    cn.execute(c.delete().where(c.c.server_id == server_id))


def discord_ids_for_ucid(cn: Connection, ucid: str) -> set[int]:
    """Every Discord id any server claims for this ucid (more than one means the claims disagree)."""
    return {r[0] for r in cn.execute(select(c.c.discord_id).where(c.c.ucid == ucid, _fresh()))}
