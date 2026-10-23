"""Tacview search (login required)."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ..services import tacview
from .deps import Ctx, require_user

router = APIRouter(dependencies=[Depends(require_user)], tags=["tacview"])


@router.get("/tacview/search")
def search(ctx: Ctx, pilot: Annotated[str, Query(min_length=2, max_length=64)], server_id: str | None = None,
           limit: Annotated[int, Query(ge=1, le=200)] = 50):
    return tacview.search(ctx, pilot, limit, server_id)
