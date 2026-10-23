"""Built-in default templates (gzip JSON bundles in ./templates, built by tools/make_templates.py)."""
from __future__ import annotations

import gzip
import json
from copy import deepcopy
from importlib import resources
from typing import Any

from .errors import DtcError

FILES = {"F-16C_50": "f16c_50.json.gz", "F-14BU": "f14bu.json.gz", "AH-64D_BLK_II": "ah64d_blk_ii.json.gz"}


def load_bundle(aircraft: str) -> dict[str, Any]:
    """{'template': parsed .dtc with empty navigation, 'defaults': example points} for `aircraft`."""
    name = FILES.get(aircraft)
    if name is None:
        raise DtcError([f"no built-in template for aircraft {aircraft!r}"])
    res = resources.files("fox3_dtc").joinpath("templates", name)
    try:
        return json.loads(gzip.decompress(res.read_bytes()).decode("utf-8"))
    except FileNotFoundError as exc:
        raise DtcError([f"built-in template {name} is missing; run tools/make_templates.py"]) from exc


def default_template(aircraft: str) -> dict[str, Any]:
    return deepcopy(load_bundle(aircraft)["template"])


def default_points(aircraft: str) -> dict[str, Any]:
    return deepcopy(load_bundle(aircraft).get("defaults", {}))
