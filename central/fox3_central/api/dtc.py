"""DTC generator: import a native .dtc into the editable model, export the model back to a native .dtc. Login required."""
from __future__ import annotations

import json
from urllib.parse import quote

from fastapi import APIRouter, Depends, Request
from fastapi.responses import Response
from pydantic import BaseModel

from fox3_dtc import AIRCRAFT, DtcError, default_model, export_with_warnings, import_dtc

from ..core.errors import BadRequest, Invalid, RateLimited
from .deps import Ctx, User, require_user

router = APIRouter(prefix="/dtc", dependencies=[Depends(require_user)], tags=["dtc"])
MAX_UPLOAD = 8 * 1024 * 1024


class GenerateIn(BaseModel):
    model: dict
    template_id: str | None = None  # from /dtc/import; absent = the built-in template of the aircraft


@router.get("/aircraft")
def aircraft():
    """Supported aircraft, what each lets you edit and what is preserved but not editable (FA-18C is listed as disabled)."""
    return [{"id": a.id, "label": a.label, "enabled": a.enabled, "supports": sorted(a.supports), "unsupported": list(a.unsupported),
             "limits": a.limits, "notes": list(a.notes)} for a in AIRCRAFT.values()]


@router.get("/default-model")
def new_model(aircraft: str, terrain: str | None = None):
    """A new DTC for the aircraft: empty navigation and the radio configuration of the built-in template (as DCS wrote it)."""
    try:
        return default_model(aircraft, terrain)
    except DtcError as exc:
        raise Invalid("cannot start a DTC for this aircraft/map", exc.errors) from exc


@router.post("/import")
async def import_file(request: Request, ctx: Ctx, user: User):
    """Body = the raw .dtc file (JSON, up to 8 MB). Returns the editable model, warnings and a template id for the export."""
    if not ctx.limiter.allow(f"dtc-import:{user.user_id}", 20):
        raise RateLimited("too many uploads")
    raw = await request.body()
    if not raw or len(raw) > MAX_UPLOAD:
        raise BadRequest("empty file or larger than 8 MB")
    try:
        result = import_dtc(raw)
    except DtcError as exc:
        raise Invalid("this is not a supported .dtc file", exc.errors) from exc
    return {"model": result.model, "warnings": result.warnings, "template_id": ctx.dtc_templates.put(user.user_id, result.template, len(raw))}


@router.post("/generate")
def generate(body: GenerateIn, ctx: Ctx, user: User):
    """Serialise the model to a native .dtc. Warnings (e.g. unknown elevation written as 0) travel in `X-DTC-Warnings`."""
    errors = ctx.validators.errors("dtc_mission", body.model)
    if errors:
        raise Invalid("the model does not match the contract", errors)
    template = ctx.dtc_templates.get(user.user_id, body.template_id) if body.template_id else None
    try:
        out = export_with_warnings(body.model, template)
    except DtcError as exc:
        raise Invalid("the model cannot be exported", exc.errors) from exc
    name = quote(f"{body.model['aircraft']}_{body.model.get('name') or 'FOX3'}".replace(" ", "_"), safe="_-.")
    return Response(out.raw, media_type="application/json", headers={
        "Content-Disposition": f'attachment; filename="{name}.dtc"', "Cache-Control": "no-store",
        "X-DTC-Warnings": quote(json.dumps(out.warnings)[:1500])})

