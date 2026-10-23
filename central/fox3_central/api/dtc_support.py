"""DTC generator: supporting endpoints (maps, elevation). Login required."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field

from fox3_common import geo
from fox3_common.airfields import airfields

from ..core.errors import NotFound, RateLimited
from .deps import Ctx, User, require_user

router = APIRouter(prefix="/dtc", dependencies=[Depends(require_user)], tags=["dtc"])
LEVEL_NOTE = {"exact": "verified against a real DCS file", "plausible": "consistent with a real DCS file",
              "airports": "checked against real airport positions, not yet in the game"}


class Point(BaseModel):
    lat: float = Field(ge=-90, le=90)
    lon: float = Field(ge=-180, le=180)


class ElevationIn(BaseModel):
    points: list[Point] = Field(min_length=1, max_length=100)


@router.get("/terrains")
def terrains():
    """Maps the generator can use, with how far each projection is trusted."""
    return [{"id": t, "calibration": geo.calibration(t), "note": LEVEL_NOTE[geo.calibration(t) or "airports"]} for t in sorted(geo.PARAMS)]


@router.get("/airfields")
def airfield_list(terrain: Annotated[str, Query(min_length=2, max_length=40)]):
    """Airfields of a map (name and position), to show on the DTC map and to use as waypoints."""
    found = airfields(terrain)
    if found is None:
        raise NotFound("unknown map")
    return found


@router.post("/elevation")
def elevation(body: ElevationIn, ctx: Ctx, user: User):
    """Approximate ground elevation (m) per point; null where unavailable (type it by hand)."""
    if not ctx.limiter.allow(f"elev:{user.user_id}", 60):
        raise RateLimited("too many elevation requests")
    values = ctx.elevation.lookup([(p.lat, p.lon) for p in body.points])
    return {"enabled": ctx.elevation.enabled, "elevations": values,
            "attribution": "Copernicus DEM GLO-90 via Open-Meteo.com (approximate, not the DCS terrain)"}
