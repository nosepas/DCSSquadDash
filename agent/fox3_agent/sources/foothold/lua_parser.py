"""Safe parser for the Lua subset of Foothold persistence files: assignments to `zonePersistance` only."""
from __future__ import annotations

import math

from .lua_errors import LuaParseError, error_at
from .lua_lexer import Token, tokenize
from .lua_values import KEYWORDS as _KEYWORDS
from .lua_values import is_number as _is_number
from .lua_values import sequence_or_table as _seq

DEFAULT_MAX_BYTES = 64 * 1024 * 1024
DEFAULT_MAX_DEPTH = 64
ROOT = "zonePersistance"
class _Parser:
    def __init__(self, text: str, max_depth: int) -> None:
        self.text = text
        self.max_depth = max_depth
        self.toks: list[Token] = [*tokenize(text), ("eof", None, len(text))]
        self.i = 0

    def fail(self, pos: int, message: str) -> LuaParseError:
        return error_at(self.text, pos, message)

    def is_op(self, ops: str, offset: int = 0) -> bool:
        kind, val, _ = self.toks[min(self.i + offset, len(self.toks) - 1)]
        return kind == "op" and val in ops

    def expect(self, op: str) -> None:
        kind, val, pos = self.toks[self.i]
        if not (kind == "op" and val == op):
            raise self.fail(pos, f"expected '{op}'")
        self.i += 1

    def run(self) -> dict:
        result: dict = {}
        while self.toks[self.i][0] != "eof":
            if self.is_op(";"):
                self.i += 1
            else:
                result = self.statement(result)
        return result

    def statement(self, result: dict) -> dict:
        kind, val, pos = self.toks[self.i]
        if kind != "name" or val != ROOT:
            raise self.fail(pos, f"expected an assignment to {ROOT}")
        self.i += 1
        path: list[object] = []
        while True:
            if self.is_op("."):
                self.i += 1
                kind, val, pos = self.toks[self.i]
                if kind != "name":
                    raise self.fail(pos, "expected a field name after '.'")
                path.append(val)
                self.i += 1
            elif self.is_op("["):
                self.i += 1
                path.append(self.key(0))
                self.expect("]")
            else:
                break
        self.expect("=")
        value_pos = self.toks[self.i][2]
        value = self.value(0)
        if not path:
            if not isinstance(value, dict):
                raise self.fail(value_pos, f"{ROOT} must be assigned a table")
            return value
        target = result
        for key in path[:-1]:
            target = target.get(key)
            if not isinstance(target, dict):
                raise self.fail(value_pos, "assignment into a missing or non-table path")
        if value is None:
            target.pop(path[-1], None)
        else:
            target[path[-1]] = value
        return result

    def key(self, depth: int) -> object:
        pos = self.toks[self.i][2]
        key = self.value(depth)
        if isinstance(key, float):
            if math.isnan(key):
                raise self.fail(pos, "NaN table key")
            if key.is_integer():
                key = int(key)
        if not isinstance(key, (str, int, float, bool)):
            raise self.fail(pos, "unsupported table key")
        return key

    def value(self, depth: int) -> object:
        kind, val, pos = self.toks[self.i]
        self.i += 1
        if kind in ("str", "num"):
            return val
        if kind == "name" and val in _KEYWORDS:
            if val == "nan" and self.is_op("(") and self.toks[self.i + 1][0] == "name" and self.is_op(")", 2):
                self.i += 3  # `nan(ind)` as printed by some C runtimes
            return _KEYWORDS[val]
        if kind == "op" and val == "{":
            return self.table(depth + 1, pos)
        if kind == "op" and val == "-":
            inner = self.value(depth)
            if not _is_number(inner):
                raise self.fail(pos, "'-' must be followed by a number")
            return -inner
        raise self.fail(pos, "unexpected end of input" if kind == "eof" else "unsupported expression")

    def table(self, depth: int, pos: int) -> dict | list:
        if depth > self.max_depth:
            raise self.fail(pos, f"tables nested deeper than {self.max_depth}")
        items: dict = {}
        n = 0
        while True:
            kind, val, _ = self.toks[self.i]
            if kind == "op" and val == "}":
                self.i += 1
                return _seq(items)
            if kind == "op" and val in ",;":
                self.i += 1
                continue
            if kind == "op" and val == "[":
                self.i += 1
                k = self.key(depth)
                self.expect("]")
                self.expect("=")
            elif kind == "name" and self.is_op("=", 1):
                k = val
                self.i += 2
            else:
                n += 1
                k = n
            v = self.value(depth)
            if v is None:
                items.pop(k, None)
            else:
                items[k] = v
            if not (self.is_op(",;") or self.is_op("}")):
                raise self.fail(self.toks[self.i][2], "expected ',' or '}' in table")


def parse_lua(source: str | bytes, *, max_bytes: int = DEFAULT_MAX_BYTES, max_depth: int = DEFAULT_MAX_DEPTH) -> dict:
    """Parse the text of a Foothold persistence file into plain dicts/lists/scalars (never evaluates anything).

    Lua tables become dicts, or lists when their keys are exactly 1..n. Raises LuaParseError on any problem.
    """
    if len(source) > max_bytes:
        raise LuaParseError(1, 1, f"input larger than the {max_bytes} byte limit")
    text = source.decode("utf-8-sig", "replace") if isinstance(source, bytes) else source.lstrip("﻿")
    return _Parser(text, max_depth).run()
