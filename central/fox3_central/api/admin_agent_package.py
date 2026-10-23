"""Admin: download a personalised agent installer for a server (the squad's admin never touches a config file)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Response

from ..services import agent_package
from .deps import Admin, Ctx, require_admin

router = APIRouter(prefix="/admin", dependencies=[Depends(require_admin)], tags=["admin"])


@router.get("/agent-package")
def package_status(ctx: Ctx):
    return agent_package.package_status(ctx)


@router.post("/servers/{server_id}/agent-package")
def download_package(server_id: str, ctx: Ctx, user: Admin, language: str = "es"):
    data, filename = agent_package.build_package(ctx, server_id, language, user.user_id)
    return Response(data, media_type="application/zip", headers={
        "Content-Disposition": f'attachment; filename="{filename}"',
        "X-Pairing-Expires-Minutes": str(agent_package.PAIRING_MINUTES),
        "Cache-Control": "no-store"})
