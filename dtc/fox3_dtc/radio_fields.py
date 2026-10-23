"""Helpers to map DCS radio dicts to neutral-model dicts and back, touching only what changed.

`fmap` maps neutral field name -> DCS key. Whatever a DCS dict holds beyond `fmap` travels in the neutral object's `extra`
and is written back as it came, so unknown keys survive. Writing skips values equal to the template's (so `305.0` stays
`305.0` and unedited files stay byte-identical); numbers are written as int when integral, float otherwise.
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any

from .errors import DtcError
from .model import is_number, num


def same(a: Any, b: Any) -> bool:
    return a == b and isinstance(a, bool) == isinstance(b, bool)


def pick(src: dict[str, Any], fmap: dict[str, str]) -> dict[str, Any]:
    """Mapped fields only (deep-copied)."""
    return {mk: deepcopy(src[dk]) for mk, dk in fmap.items() if dk in src}


def rest(src: dict[str, Any], *keys: Any) -> dict[str, Any]:
    """DCS keys of `src` not consumed. Each arg is a field map (its DCS keys are consumed) or a plain collection of DCS keys."""
    used: set[str] = set()
    for k in keys:
        used |= set(k.values()) if isinstance(k, dict) else set(k)
    return {k: deepcopy(v) for k, v in src.items() if k not in used}


def read(src: dict[str, Any], fmap: dict[str, str]) -> dict[str, Any]:
    out = pick(src, fmap)
    extra = rest(src, fmap)
    if extra:
        out["extra"] = extra
    return out


def put(dst: dict[str, Any], key: str, value: Any) -> None:
    if key in dst and same(dst[key], value):
        return
    dst[key] = num(value) if is_number(value) else deepcopy(value)


def write(dst: dict[str, Any], obj: dict[str, Any], fmap: dict[str, str]) -> None:
    """Apply `obj`'s `extra` and mapped fields onto the DCS dict `dst` in place."""
    for key, value in (obj.get("extra") or {}).items():
        put(dst, key, value)
    for mk, dk in fmap.items():
        if mk in obj:
            put(dst, dk, obj[mk])


def section(data: dict[str, Any], *path: str) -> Any:
    """data[path0][path1]... or a DtcError naming the missing part (export needs the template to hold it)."""
    cur: Any = data
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            raise DtcError([f"cannot write radios: the template has no data.{'.'.join(path)}"])
        cur = cur[key]
    return cur
