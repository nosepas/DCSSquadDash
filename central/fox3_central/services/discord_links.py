"""Automatic Discord <-> UCID linking from pairs DCSServerBot already verified (reported by an authenticated agent).

A claim becomes a player_link only when (a) a FOX3 user with that Discord id exists, (b) all claims for the ucid agree and
(c) the ucid is not already linked to a DIFFERENT user (a link is never stolen). No code is ever shown in public chat.
"""
from __future__ import annotations

import logging

from sqlalchemy.engine import Connection

from ..repositories import link_claims, players, users

audit = logging.getLogger("fox3.audit")
MAX_INT64 = 2**63 - 1
MAX_CLAIMS_PER_SERVER = 50_000   # far above any squadron's player count; stops a hostile agent from filling the table


def _snowflake(value: str) -> int | None:
    return int(value) if value.isdigit() and 0 < int(value) <= MAX_INT64 else None


def _try_link(cn: Connection, user_id: int, discord_id: int, ucid: str) -> bool:
    if link_claims.discord_ids_for_ucid(cn, ucid) != {discord_id}:
        audit.warning("auto-link skipped, conflicting claims: ucid=%s user=%s", ucid, user_id)
        return False
    owner = players.link_owner(cn, ucid)
    if owner == user_id:
        return False
    if owner is not None:
        audit.warning("auto-link refused, ucid already linked to another user: ucid=%s user=%s owner=%s", ucid, user_id, owner)
        return False
    if not link_claims.seen_on_claiming_server(cn, ucid, discord_id):   # a bare claim for a ucid no server ever saw proves nothing
        return False
    players.touch(cn, ucid, None)
    if not players.link_if_absent(cn, ucid, user_id):   # lost a race against another link: keep theirs
        audit.warning("auto-link lost a race, ucid linked meanwhile: ucid=%s user=%s", ucid, user_id)
        return False
    audit.info("auto-linked from DCSServerBot: ucid=%s user=%s", ucid, user_id)
    return True


def ingest_claims(cn: Connection, server_id: str, links: list[dict]) -> None:
    """Store the claims, then link the ones whose Discord user already exists in FOX3."""
    room = MAX_CLAIMS_PER_SERVER - link_claims.count_for_server(cn, server_id)
    for item in links:
        discord_id = _snowflake(item["discord_id"])
        if discord_id is None:   # the schema already requires a snowflake; this guards the int64 column
            continue
        if room <= 0:
            audit.warning("link claims over the per-server limit, rest ignored: server=%s", server_id)
            break
        room -= 1
        if link_claims.save(cn, server_id, item["ucid"], discord_id):
            audit.info("link claim changed: server=%s ucid=%s discord=%s", server_id, item["ucid"], discord_id)
        user = users.get_by_discord_id(cn, str(discord_id))
        if user:
            _try_link(cn, user["user_id"], discord_id, item["ucid"])


def link_for_user(cn: Connection, user: dict) -> int:
    """Called at login: link every claimed ucid of this Discord account. Returns how many links were created."""
    discord_id = _snowflake(str(user["discord_id"]))
    if discord_id is None:   # e.g. the demo accounts have non-numeric ids
        return 0
    return sum(_try_link(cn, user["user_id"], discord_id, u) for u in link_claims.ucids_for_discord(cn, discord_id))
