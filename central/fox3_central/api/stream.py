"""Server-Sent Events: tells the browser when a server's data changed; the client then refetches what it shows."""
from __future__ import annotations

import asyncio
import json

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse

from .deps import Ctx, ServerId, require_user

router = APIRouter(dependencies=[Depends(require_user)], tags=["stream"])
POLL_S, KEEPALIVE_S = 1.0, 15.0


@router.get("/servers/{server_id}/stream")
async def stream(server_id: ServerId, ctx: Ctx, request: Request):
    async def gen():
        last, idle = -1, 0.0
        while not await request.is_disconnected():
            v = ctx.version(server_id)
            if v != last:
                last, idle = v, 0.0
                yield f"event: update\ndata: {json.dumps({'version': v})}\n\n"
            elif idle >= KEEPALIVE_S:
                idle = 0.0
                yield ": keepalive\n\n"
            await asyncio.sleep(POLL_S)
            idle += POLL_S

    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})
