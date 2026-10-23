"""Tacview file download (browser) and the agent side of the relay (poll, upload, fail)."""
from __future__ import annotations

import asyncio
import re
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Query, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from ..core.errors import NotFound, RateLimited
from ..repositories import tacview
from ..services.transfers import Unavailable
from .deps import AgentServer, Ctx, User, require_user

user_router = APIRouter(dependencies=[Depends(require_user)], tags=["tacview"])
agent_router = APIRouter(prefix="/agent/v1", tags=["agent"])
START_TIMEOUT_S = 30
_SAFE = re.compile(r"[^A-Za-z0-9._-]+")


class Failure(BaseModel):
    reason: str


def _attachment_name(relative_path: str) -> str:
    return _SAFE.sub("_", relative_path.replace("\\", "/").rsplit("/", 1)[-1]) or "recording.acmi"


@user_router.get("/tacview/files/{file_id}/download")
async def download(file_id: int, ctx: Ctx, user: User):
    if not ctx.limiter.allow(f"download:{user.user_id}", 20, window_s=600):  # recordings are big: protect the agent's uplink
        raise RateLimited("too many downloads, wait a few minutes")
    row = await run_in_threadpool(_file_row, ctx, file_id)
    broker = ctx.transfers
    t = broker.request(row["server_id"], row["relative_path"], _attachment_name(row["relative_path"]), owner=user.user_id)
    try:
        await asyncio.wait_for(t.claimed.wait(), START_TIMEOUT_S)
    except TimeoutError:
        broker.discard(t.id)
        raise Unavailable("the server's agent did not answer; it may be offline") from None
    if t.failure or t.cancelled:
        broker.discard(t.id)
        raise NotFound(t.failure or "the file is no longer available on the server")
    headers = {"Content-Disposition": f'attachment; filename="{t.filename}"', "Cache-Control": "no-store"}
    if t.size is not None:
        headers["Content-Length"] = str(t.size)
    return StreamingResponse(broker.stream(t), media_type="application/octet-stream", headers=headers)


def _file_row(ctx, file_id: int) -> dict:
    with ctx.engine.connect() as cn:
        row = tacview.get_file(cn, file_id)
    if not row:
        raise NotFound("recording not found")
    return row


@agent_router.get("/file-requests")
async def pending_requests(ctx: Ctx, server_id: AgentServer, wait: Annotated[float, Query(ge=0, le=30)] = 25):
    items = await ctx.transfers.pending_for(server_id, wait)
    return [{"request_id": t.id, "relative_path": t.relative_path} for t in items]


@agent_router.put("/file-requests/{request_id}/content")
async def upload(request_id: str, request: Request, ctx: Ctx, server_id: AgentServer,
                 x_file_size: Annotated[int | None, Header(ge=0)] = None):
    t = ctx.transfers.claim(request_id, server_id, x_file_size)
    async for chunk in request.stream():
        await ctx.transfers.push(t, chunk)
    await ctx.transfers.finish(t)
    return {"ok": True, "bytes": t.received}


@agent_router.post("/file-requests/{request_id}/fail", status_code=204)
async def fail(request_id: str, body: Failure, ctx: Ctx, server_id: AgentServer):
    ctx.transfers.fail(request_id, server_id, body.reason)
