"""Login, logout and current user."""
from __future__ import annotations

from fastapi import APIRouter, Query, Request
from fastapi.responses import RedirectResponse, Response

from ..core.errors import RateLimited
from ..repositories import users
from ..services import auth as auth_service
from ..services import profile
from .deps import SESSION_COOKIE, Ctx, User

router = APIRouter(tags=["auth"])
OAUTH_COOKIE = "fox3_oauth"
OAUTH_PATH = "/api/v1/auth/discord"


def _session_redirect(ctx, tokens: tuple[str, str]) -> RedirectResponse:
    resp = RedirectResponse("/", status_code=302)
    resp.set_cookie(SESSION_COOKIE, tokens[0], httponly=True, samesite="lax", secure=ctx.settings.cookie_secure,
                    max_age=ctx.settings.session_ttl_hours * 3600, path="/")
    return resp


def _throttle(ctx, request: Request) -> None:
    ip = request.client.host if request.client else "unknown"
    if not ctx.limiter.allow(f"login:{ip}", 20):
        raise RateLimited()


@router.get("/auth/discord/login")
def discord_login(ctx: Ctx, request: Request):
    _throttle(ctx, request)
    url, nonce = auth_service.authorize_url(ctx)
    resp = RedirectResponse(url, status_code=302)  # the nonce ties the login to THIS browser (prevents login CSRF)
    resp.set_cookie(OAUTH_COOKIE, nonce, httponly=True, samesite="lax", secure=ctx.settings.cookie_secure, max_age=600, path=OAUTH_PATH)
    return resp


@router.get("/auth/discord/callback")
def discord_callback(ctx: Ctx, request: Request, code: str, state: str):
    _throttle(ctx, request)
    resp = _session_redirect(ctx, auth_service.login_with_code(ctx, code, state, request.cookies.get(OAUTH_COOKIE)))
    resp.delete_cookie(OAUTH_COOKIE, path=OAUTH_PATH)
    return resp


@router.get("/auth/demo")
def demo(ctx: Ctx, request: Request, admin: bool = Query(False)):
    """Passwordless login for the local demo only (FOX3_DEMO_LOGIN=1); 404 otherwise."""
    _throttle(ctx, request)
    return _session_redirect(ctx, auth_service.demo_login(ctx, admin))


@router.post("/auth/logout", status_code=204)
def logout(ctx: Ctx, user: User):
    with ctx.tx() as cn:
        users.delete_session(cn, user.session_token)
    resp = Response(status_code=204)
    resp.delete_cookie(SESSION_COOKIE, path="/")
    return resp


@router.get("/me")
def me(ctx: Ctx, user: User):
    return {"user_id": user.user_id, "name": user.name, "role": user.role, "csrf_token": user.csrf,
            "linked_ucids": profile.linked(ctx, user.user_id)}


@router.get("/auth/config")
def auth_config(ctx: Ctx):
    """Which login methods the frontend should offer (public)."""
    return {"discord": ctx.settings.discord_enabled, "demo": ctx.settings.demo_login}
