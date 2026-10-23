"""Structure checks that feed ImportResult.warnings (unexpected keys / lengths in the parts we touch)."""
from __future__ import annotations

from typing import Any


def check_keys(items: list[Any], where: str, expected: set[str] | None = None) -> list[str]:
    """Warn when entries are not dicts or their key sets differ from `expected` (default: the first entry's keys)."""
    warnings: list[str] = []
    ref = expected if expected is not None else (set(items[0]) if items and isinstance(items[0], dict) else set())
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            warnings.append(f"{where}[{i}] is not an object")
            continue
        missing, extra = ref - set(item), set(item) - ref
        if missing:
            warnings.append(f"{where}[{i}] lacks keys {sorted(missing)}")
        if extra:
            warnings.append(f"{where}[{i}] has unknown keys {sorted(extra)}")
    return warnings


def need(container: Any, key: str, where: str) -> list[str]:
    """Warning list (empty when `container` is a dict holding `key`)."""
    if isinstance(container, dict) and key in container:
        return []
    return [f"{where}: missing key {key!r}"]
