"""Application factory."""
from __future__ import annotations

import logging
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .api import admin, admin_agent_package, admin_servers, agent, auth, data, dtc, dtc_support, public, stream, tacview, transfers
from .config import Settings
from .context import Context
from .core.bodylimit import BodyLimitMiddleware
from .core.errors import AppError
from .db.engine import make_engine
from .services.maintenance import lifespan

log = logging.getLogger("fox3")
SECURITY_HEADERS = {
    "X-Content-Type-Options": "nosniff", "X-Frame-Options": "DENY", "Referrer-Policy": "same-origin",
    "Content-Security-Policy": "default-src 'self'; img-src 'self' data: https://*.tile.openstreetmap.org https://*.basemaps.cartocdn.com "
                               "https://server.arcgisonline.com https://cdn.discordapp.com; style-src 'self' 'unsafe-inline'; connect-src 'self'; "
                               "object-src 'none'; base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
}


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings()
    docs = settings.demo_login  # the interactive API docs are a local-demo feature only
    app = FastAPI(title="FOX3", version=__version__, docs_url="/api/docs" if docs else None, redoc_url=None, lifespan=lifespan,
                  openapi_url="/api/openapi.json" if docs else None)
    app.state.ctx = Context(settings, make_engine(settings.db_url))
    app.add_middleware(BodyLimitMiddleware)

    @app.exception_handler(AppError)
    async def _app_error(_: Request, exc: AppError):
        body = {"error": {"code": exc.code, "message": exc.message}}
        if exc.details:
            body["error"]["details"] = exc.details
        return JSONResponse(body, status_code=exc.status)

    @app.middleware("http")
    async def _headers(request: Request, call_next):
        resp = await call_next(request)
        for k, v in SECURITY_HEADERS.items():
            resp.headers.setdefault(k, v)
        if settings.cookie_secure:
            resp.headers.setdefault("Strict-Transport-Security", "max-age=31536000")
        return resp

    routers = (public.router, auth.router, data.router, stream.router, tacview.router, admin.router, admin_servers.router, admin_agent_package.router,
               dtc_support.router, dtc.router)
    for r in routers:
        app.include_router(r, prefix="/api/v1")
    app.include_router(transfers.user_router, prefix="/api/v1")
    app.include_router(agent.router)
    app.include_router(transfers.agent_router)
    _mount_frontend(app, settings.web_dir)
    return app


def _mount_frontend(app: FastAPI, web_dir: Path | None) -> None:
    if not web_dir or not (web_dir / "index.html").exists():
        log.info("frontend not built (%s); serving API only", web_dir)
        return
    index = web_dir / "index.html"
    if (web_dir / "assets").is_dir():
        app.mount("/assets", StaticFiles(directory=web_dir / "assets"), name="assets")

    @app.get("/{path:path}", include_in_schema=False)
    def spa(path: str):
        if path.startswith(("api/", "agent/")):
            return JSONResponse({"error": {"code": "not_found", "message": "not found"}}, status_code=404)
        f = (web_dir / path).resolve()
        return FileResponse(f if f.is_file() and web_dir.resolve() in f.parents else index)
