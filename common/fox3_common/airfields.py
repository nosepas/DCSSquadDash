"""Airfields (name, lat/lon, civil flag) of each supported DCS map. Dataset built by tools/make_airfields.py."""
from __future__ import annotations

import gzip
import json
from functools import lru_cache
from importlib import resources


@lru_cache(maxsize=1)
def _load() -> dict[str, list[dict]]:
    with resources.files("fox3_common.data").joinpath("airfields.json.gz").open("rb") as raw, gzip.open(raw, "rt", encoding="utf-8") as f:
        return json.load(f)["terrains"]


def airfields(terrain: str | None) -> list[dict] | None:
    """Airfields of a map, or None when the map is unknown."""
    return _load().get(terrain or "")
