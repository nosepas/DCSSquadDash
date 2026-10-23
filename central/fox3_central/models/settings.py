"""Per-server settings edited in the admin panel and pushed to the agent. Validated here, applied by the agent without restart.

Secrets (DCSServerBot API key, database URL) are deliberately NOT part of this model: they stay on the server PC.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Annotated
from urllib.parse import urlparse

from pydantic import AfterValidator, BaseModel, ConfigDict, Field


def _path(v: str | None) -> str | None:
    if v is None or not v.strip():
        return None
    v = v.strip()
    if len(v) > 260 or any(ord(c) < 32 for c in v):
        raise ValueError("not a valid folder path")
    return v


def _http_url(v: str) -> str:
    u = urlparse(v.strip())
    if u.scheme not in ("http", "https") or not u.hostname or u.username or u.password:
        raise ValueError("must be a http(s) URL without credentials")
    if u.path not in ("", "/") or u.query or u.fragment or u.params:
        raise ValueError("must be only the address (scheme, host and port): put the API prefix in its own field")
    return v.strip().rstrip("/")


Folder = Annotated[str | None, AfterValidator(_path)]
HttpUrl = Annotated[str, AfterValidator(_http_url)]


class _Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class FootholdSettings(_Strict):
    enabled: bool = True
    saves_dir: Folder = None  # {Saved Games}/<server>/Missions/Saves


class TacviewSettings(_Strict):
    enabled: bool = False
    folder: Folder = None


class MissionsSettings(_Strict):
    folder: Folder = None  # reserved: mission list feature (not used yet)


class DcsBotSettings(_Strict):
    rest_enabled: bool = False
    rest_url: HttpUrl = "http://localhost:9876"
    rest_prefix: Annotated[str, Field(pattern=r"^[A-Za-z0-9/_-]{0,40}$")] = ""
    server_name: Annotated[str | None, Field(max_length=120)] = None
    db_enabled: bool = False


class ServerSettings(_Strict):
    foothold: FootholdSettings = Field(default_factory=FootholdSettings)
    tacview: TacviewSettings = Field(default_factory=TacviewSettings)
    missions: MissionsSettings = Field(default_factory=MissionsSettings)
    dcsbot: DcsBotSettings = Field(default_factory=DcsBotSettings)


def revision(settings: dict, mission_type: str) -> str:
    """Stable hash so the agent can tell whether the settings changed."""
    blob = json.dumps({"s": settings, "m": mission_type}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode()).hexdigest()[:16]


ADDRESS = re.compile(r"^[A-Za-z0-9.\-:\[\]_ ]{1,120}$")
