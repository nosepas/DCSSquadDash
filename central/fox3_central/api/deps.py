"""FastAPI dependencies: context, session/CSRF, role checks, agent identity."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends, Request

from ..context import Context
from ..core.errors import Forbidden, NotFound, Unauthorized
from ..repositories import servers, users
from ..services import agents as agent_service

SESSION_COOKIE = "fox3_session"
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def get_ctx(request: Request) -> Context:
    return request.app.state.ctx


Ctx = Annotated[Context, Depends(get_ctx)]


@dataclass
class SessionUser:
    user_id: int
    name: str | None
    role: str
    csrf: str
    session_token: str

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"


def optional_user(request: Request, ctx: Ctx) -> SessionUser | None:
    tok = request.cookies.get(SESSION_COOKIE)
    if not tok:
        return None
    with ctx.engine.connect() as cn:
        found = users.session_user(cn, tok)
    if not found:
        return None
    u, csrf = found
    return SessionUser(u["user_id"], u["discord_name"], u["role"], csrf, tok)


def require_user(request: Request, user: Annotated[SessionUser | None, Depends(optional_user)]) -> SessionUser:
    """Any logged-in user. State-changing requests must carry the session's CSRF token."""
    if user is None:
        raise Unauthorized("login required")
    if request.method not in SAFE_METHODS and request.headers.get("x-csrf-token") != user.csrf:
        raise Forbidden("invalid CSRF token")
    return user


def require_admin(user: Annotated[SessionUser, Depends(require_user)]) -> SessionUser:
    if not user.is_admin:
        raise Forbidden("administrator only")
    return user


def known_server(server_id: str, ctx: Ctx) -> str:
    with ctx.engine.connect() as cn:
        srv = servers.get(cn, server_id)
    if not srv or not srv["enabled"]:
        raise NotFound("server not found")
    return server_id


def agent_server_id(request: Request, ctx: Ctx) -> str:
    ip = request.client.host if request.client else "unknown"
    return agent_service.authenticate(ctx, request.headers.get("authorization", ""), ip)[1]


User = Annotated[SessionUser, Depends(require_user)]
Admin = Annotated[SessionUser, Depends(require_admin)]
ServerId = Annotated[str, Depends(known_server)]
AgentServer = Annotated[str, Depends(agent_server_id)]
