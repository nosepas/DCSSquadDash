"""Users, web sessions, OAuth state and Discord<->UCID link codes."""
from __future__ import annotations

from typing import Any

from sqlalchemy import delete, insert, select, update
from sqlalchemy.engine import Connection

from ..core.clock import after, now
from ..core.security import sha256, short_code, token
from ..db import auth_tables as a
from ..db.utils import insert_ignore

Row = dict[str, Any]


def upsert_discord(cn: Connection, discord_id: str, name: str | None, avatar: str | None, role: str) -> Row:
    ts = now()
    if not insert_ignore(cn, a.users, discord_id=discord_id, discord_name=name, avatar=avatar, role=role, last_login_at=ts):
        vals = {"discord_name": name, "avatar": avatar, "last_login_at": ts}
        if role == "admin":  # config-listed admins are always admin; DB-granted admin is never downgraded here
            vals["role"] = "admin"
        cn.execute(update(a.users).where(a.users.c.discord_id == discord_id).values(**vals))
    return dict(cn.execute(select(a.users).where(a.users.c.discord_id == discord_id)).mappings().one())


def get(cn: Connection, user_id: int) -> Row | None:
    r = cn.execute(select(a.users).where(a.users.c.user_id == user_id)).mappings().first()
    return dict(r) if r else None


def get_by_discord_id(cn: Connection, discord_id: str) -> Row | None:
    r = cn.execute(select(a.users).where(a.users.c.discord_id == discord_id)).mappings().first()
    return dict(r) if r else None


def list_all(cn: Connection) -> list[Row]:
    return [dict(r) for r in cn.execute(select(a.users).order_by(a.users.c.user_id)).mappings()]


def set_role(cn: Connection, user_id: int, role: str) -> bool:
    return cn.execute(update(a.users).where(a.users.c.user_id == user_id).values(role=role)).rowcount > 0


def create_session(cn: Connection, user_id: int, ttl_hours: int) -> tuple[str, str]:
    """Returns (session token for the cookie, csrf token). Only the token hash is stored."""
    tok, csrf = token(), token(16)
    cn.execute(insert(a.sessions).values(session_hash=sha256(tok), user_id=user_id, csrf=csrf, expires_at=after(hours=ttl_hours)))
    return tok, csrf


def session_user(cn: Connection, tok: str) -> tuple[Row, str] | None:
    s = cn.execute(select(a.sessions).where(a.sessions.c.session_hash == sha256(tok))).mappings().first()
    if not s or s["expires_at"] < now():
        return None
    user = get(cn, s["user_id"])
    return (user, s["csrf"]) if user else None


def delete_session(cn: Connection, tok: str) -> None:
    cn.execute(delete(a.sessions).where(a.sessions.c.session_hash == sha256(tok)))


def save_oauth_state(cn: Connection, state: str, verifier: str, browser_hash: str) -> None:
    cn.execute(delete(a.oauth_states).where(a.oauth_states.c.expires_at < now()))
    cn.execute(insert(a.oauth_states).values(state=state, verifier=verifier, browser_hash=browser_hash, expires_at=after(minutes=10)))


def pop_oauth_state(cn: Connection, state: str) -> tuple[str, str | None] | None:
    """Consume a login state (single use). Returns (PKCE verifier, browser hash) if it exists and has not expired."""
    r = cn.execute(select(a.oauth_states).where(a.oauth_states.c.state == state)).mappings().first()
    cn.execute(delete(a.oauth_states).where(a.oauth_states.c.state == state))
    return (r["verifier"], r["browser_hash"]) if r and r["expires_at"] >= now() else None


def create_link_code(cn: Connection, user_id: int) -> Row:
    code, exp = short_code(), after(minutes=15)
    cn.execute(insert(a.link_codes).values(code=code, user_id=user_id, expires_at=exp))
    return {"code": code, "expires_at": exp}


def take_link_code(cn: Connection, code: str) -> int | None:
    """Consume a valid code; return the owning user_id."""
    r = cn.execute(select(a.link_codes).where(a.link_codes.c.code == code)).mappings().first()
    if not r or r["used_at"] or r["expires_at"] < now():
        return None
    cn.execute(update(a.link_codes).where(a.link_codes.c.code == code).values(used_at=now()))
    return r["user_id"]
