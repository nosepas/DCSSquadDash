"""Structural limits for imported .dtc JSON (denial-of-service guard); the walk is iterative so hostile nesting cannot recurse.

Measured maxima (depth counts the top-level object as 1) on the real samples in ``samples/`` and the synthetic fixtures:
depth 11 (F-16C), longest key 53, 9_796 nodes (F-16C), longest string 331, 95 keys in one object, 123 items in one list.
The limits below leave a comfortable margin over those values.
"""
from __future__ import annotations

from typing import Any

from .errors import DtcError

MAX_DEPTH = 24
MAX_KEY_LEN = 128
MAX_NODES = 300_000
MAX_STR_LEN = 100_000
MAX_OBJECT_KEYS = 10_000
MAX_LIST_ITEMS = 100_000


def check_limits(root: Any) -> None:
    """Raise DtcError when the parsed JSON exceeds a structural limit."""
    stack: list[tuple[Any, int]] = [(root, 1)]
    nodes = 0
    while stack:
        node, depth = stack.pop()
        nodes += 1
        if nodes > MAX_NODES:
            raise DtcError([f"unsupported .dtc: more than {MAX_NODES} JSON nodes"])
        if depth > MAX_DEPTH:
            raise DtcError([f"unsupported .dtc: nesting deeper than {MAX_DEPTH} levels"])
        if isinstance(node, dict):
            if len(node) > MAX_OBJECT_KEYS:
                raise DtcError([f"unsupported .dtc: an object has more than {MAX_OBJECT_KEYS} keys"])
            for key, value in node.items():
                if len(key) > MAX_KEY_LEN:
                    raise DtcError([f"unsupported .dtc: a key is longer than {MAX_KEY_LEN} characters"])
                stack.append((value, depth + 1))
        elif isinstance(node, list):
            if len(node) > MAX_LIST_ITEMS:
                raise DtcError([f"unsupported .dtc: a list has more than {MAX_LIST_ITEMS} items"])
            stack.extend((item, depth + 1) for item in node)
        elif isinstance(node, str) and len(node) > MAX_STR_LEN:
            raise DtcError([f"unsupported .dtc: a string is longer than {MAX_STR_LEN} characters"])
