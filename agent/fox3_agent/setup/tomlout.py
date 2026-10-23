"""Minimal TOML writer for the agent config (scalars, lists of scalars, nested tables)."""
from __future__ import annotations

import json
import tomllib
from typing import Any

from ..config import ConfigError, from_mapping


def _scalar(v: Any) -> str:
    if isinstance(v, bool):
        return "true" if v else "false"
    if isinstance(v, (int, float)):
        return repr(v)
    if isinstance(v, str):
        if any(ord(c) < 32 or ord(c) == 127 for c in v):
            raise ValueError("control characters in a config value")
        return json.dumps(v)  # JSON string == TOML basic string
    if isinstance(v, list) and all(not isinstance(i, (dict, list)) for i in v):
        return "[" + ", ".join(_scalar(i) for i in v) + "]"
    raise ValueError(f"unsupported config value type: {type(v).__name__}")


def _key(k: str) -> str:
    return k if k.replace("_", "").replace("-", "").isalnum() else json.dumps(k)


def _table(path: list[str], data: dict[str, Any], out: list[str]) -> None:
    scalars = {k: v for k, v in data.items() if not isinstance(v, dict)}
    if path and (scalars or not data):
        out += ["", "[" + ".".join(_key(p) for p in path) + "]"]
    out += [f"{_key(k)} = {_scalar(v)}" for k, v in scalars.items()]
    for k, v in data.items():
        if isinstance(v, dict):
            _table([*path, k], v, out)


def dumps(raw: dict[str, Any]) -> str:
    out: list[str] = []
    _table([], raw, out)
    return "\n".join(out).lstrip("\n") + "\n"


def with_state_dir(text: str, state_dir: str) -> str:
    """Re-render `text` with `[paths] state_dir` replaced; everything else is preserved. Re-validated with the config rules."""
    raw = tomllib.loads(text)
    raw.setdefault("paths", {})["state_dir"] = state_dir
    new = dumps(raw)
    try:
        from_mapping(tomllib.loads(new))
    except (ConfigError, tomllib.TOMLDecodeError) as exc:
        raise ValueError(str(exc)) from exc
    return new
