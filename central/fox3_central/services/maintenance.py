"""Background maintenance: runs the purge once at start-up and then every few hours."""
from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from ..context import Context
from ..repositories import maintenance

log = logging.getLogger("fox3.maintenance")
INTERVAL_S = 6 * 3600


def run_once(ctx: Context) -> dict[str, int]:
    with ctx.tx() as cn:
        removed = maintenance.purge(cn)
    if any(removed.values()):
        log.info("maintenance removed: %s", {k: v for k, v in removed.items() if v})
    return removed


async def _loop(ctx: Context) -> None:
    while True:
        try:
            await asyncio.to_thread(run_once, ctx)
        except Exception:  # noqa: BLE001  (maintenance must never take the server down)
            log.exception("maintenance failed")
        await asyncio.sleep(INTERVAL_S)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    task = asyncio.create_task(_loop(app.state.ctx))
    try:
        yield
    finally:
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task
