"""Discord OAuth2 (authorization code + PKCE + state) and session creation."""
from __future__ import annotations

import base64
import hashlib
from urllib.parse import urlencode

import httpx

from ..context import Context
from ..core.errors import BadRequest, Forbidden, NotFound
from ..core.security import safe_equal, sha256, token
from ..repositories import users
from . import discord_links

DISCORD = "https://discord.com/api"


def _role_for(ctx: Context, discord_id: str) -> str:
    return "admin" if discord_id in ctx.settings.admin_ids else "user"


def authorize_url(ctx: Context) -> tuple[str, str]:
    """Returns (Discord URL, browser nonce). The nonce goes into a cookie so only THIS browser can finish the login."""
    s = ctx.settings
    if not s.discord_enabled:
        raise NotFound("Discord login is not configured")
    state, verifier, nonce = token(24), token(48), token(24)
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    with ctx.tx() as cn:
        users.save_oauth_state(cn, state, verifier, sha256(nonce))
    q = urlencode({"client_id": s.discord_client_id, "response_type": "code", "scope": "identify", "state": state,
                   "redirect_uri": f"{s.public_base_url}/api/v1/auth/discord/callback",
                   "code_challenge": challenge, "code_challenge_method": "S256"})
    return f"{DISCORD}/oauth2/authorize?{q}", nonce


def login_with_code(ctx: Context, code: str, state: str, nonce: str | None) -> tuple[str, str]:
    """Complete the OAuth flow. Returns (session token, csrf token).

    The state must have been created by the SAME browser (cookie nonce): otherwise an attacker could log a victim into the
    attacker's account by sending them a callback link ("login CSRF").
    """
    s = ctx.settings
    with ctx.tx() as cn:
        found = users.pop_oauth_state(cn, state)
    if not found:
        raise BadRequest("invalid or expired state")
    verifier, browser_hash = found
    if not nonce or not browser_hash or not safe_equal(sha256(nonce), browser_hash):
        raise BadRequest("this login was not started in this browser")
    with httpx.Client(timeout=10) as http:
        tok = http.post(f"{DISCORD}/oauth2/token", data={
            "client_id": s.discord_client_id, "client_secret": s.discord_client_secret, "grant_type": "authorization_code",
            "code": code, "redirect_uri": f"{s.public_base_url}/api/v1/auth/discord/callback", "code_verifier": verifier})
        if tok.status_code != 200:
            raise Forbidden("Discord rejected the login")
        me = http.get(f"{DISCORD}/users/@me", headers={"Authorization": f"Bearer {tok.json()['access_token']}"})
        if me.status_code != 200:
            raise Forbidden("could not read the Discord profile")
    d = me.json()
    return _open_session(ctx, d["id"], d.get("global_name") or d.get("username"), d.get("avatar"))


def demo_login(ctx: Context, as_admin: bool) -> tuple[str, str]:
    if not ctx.settings.demo_login:
        raise NotFound("demo login is disabled")
    return _open_session(ctx, "demo-admin" if as_admin else "demo-user", "Demo Admin" if as_admin else "Demo Pilot",
                         None, force_role="admin" if as_admin else "user")


def _open_session(ctx: Context, discord_id: str, name: str | None, avatar: str | None, force_role: str | None = None) -> tuple[str, str]:
    with ctx.tx() as cn:
        user = users.upsert_discord(cn, discord_id, name, avatar, force_role or _role_for(ctx, discord_id))
        discord_links.link_for_user(cn, user)
        return users.create_session(cn, user["user_id"], ctx.settings.session_ttl_hours)
