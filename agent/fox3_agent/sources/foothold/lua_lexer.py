"""Single-pass tokenizer for the Lua subset written by Foothold (no eval, no external libs)."""
from __future__ import annotations

import math
import re

from .lua_errors import error_at

Token = tuple[str, object, int]  # (kind, value, character offset); kind: name | num | str | op | eof

# String bodies use possessive quantifiers (no backtracking): a hostile unterminated string fails in linear time.
_TOKEN = re.compile(
    r"""
    (?P<ws>\s+)
  | (?P<lcomment>--\[(?P<lc>=*)\[)
  | (?P<comment>--[^\n]*)
  | (?P<lstr>\[(?P<ls>=*)\[)
  | (?P<num>0[xX][0-9a-fA-F]+(?:\.[0-9a-fA-F]*)?(?:[pP][+-]?\d+)?
        |(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?(?:\#[A-Za-z]+)?)
  | (?P<name>[A-Za-z_][A-Za-z0-9_]*)
  | (?P<dq>"(?:[^"\\\n]++|\\z\s*+|\\.)*+")
  | (?P<sq>'(?:[^'\\\n]++|\\z\s*+|\\.)*+')
  | (?P<op>[{}\[\]=,;.\-()])
    """,
    re.VERBOSE | re.DOTALL,
)

_ESC = re.compile(r"\\(?:(\d{1,3})|x([0-9a-fA-F]{2})|u\{([0-9a-fA-F]+)\}|z\s*|(.))", re.DOTALL)
_SIMPLE = {"n": 10, "t": 9, "r": 13, "a": 7, "b": 8, "f": 12, "v": 11, "\n": 10}


def decode_string(body: str) -> str:
    """Resolve Lua escapes. Byte escapes (\\ddd, \\xXX) are assembled as bytes so UTF-8 sequences survive."""
    if "\\" not in body:
        return body
    out = bytearray()
    pos = 0
    for m in _ESC.finditer(body):
        out += body[pos:m.start()].encode("utf-8", "replace")
        pos = m.end()
        dec, hexa, uni, other = m.groups()
        if dec is not None:
            out.append(int(dec) & 0xFF)
        elif hexa is not None:
            out.append(int(hexa, 16))
        elif uni is not None:
            out += chr(min(int(uni, 16), 0x10FFFF)).encode("utf-8", "replace")
        elif other is not None:
            out += bytes([_SIMPLE[other]]) if other in _SIMPLE else other.encode("utf-8", "replace")
    out += body[pos:].encode("utf-8", "replace")
    return out.decode("utf-8", "replace")


def convert_number(text: str) -> int | float:
    if text[:2] in ("0x", "0X"):
        return float.fromhex(text) if ("." in text or "p" in text or "P" in text) else int(text, 16)
    if "#" in text:  # MSVC style: 1.#INF, 1.#QNAN, 1.#IND
        return math.inf if "INF" in text.upper() else math.nan
    if "." in text or "e" in text or "E" in text:
        return float(text)
    return int(text)


def _long_close(text: str, start: int, level: int, what: str) -> int:
    end = text.find("]" + "=" * level + "]", start)
    if end < 0:
        raise error_at(text, start, f"unterminated long {what}")
    return end


def tokenize(text: str) -> list[Token]:
    tokens: list[Token] = []
    append = tokens.append
    match = _TOKEN.match
    pos, size = 0, len(text)
    while pos < size:
        m = match(text, pos)
        if m is None:
            ch = text[pos]
            raise error_at(text, pos, "unterminated string" if ch in "\"'" else f"unexpected character U+{ord(ch):04X}")
        kind = m.lastgroup
        end = m.end()
        if kind == "lcomment":
            level = len(m.group("lc"))
            end = _long_close(text, end, level, "comment") + level + 2
        elif kind == "lstr":
            level = len(m.group("ls"))
            close = _long_close(text, end, level, "string")
            body = text[end:close]
            body = body[2:] if body.startswith("\r\n") else body[1:] if body.startswith("\n") else body
            append(("str", body, pos))
            end = close + level + 2
        elif kind in ("dq", "sq"):
            append(("str", decode_string(text[pos + 1:end - 1]), pos))
        elif kind == "num":
            try:
                append(("num", convert_number(m.group()), pos))
            except (ValueError, OverflowError) as exc:
                raise error_at(text, pos, "malformed number") from exc
        elif kind in ("name", "op"):
            append((kind, m.group(), pos))
        pos = end
    return tokens
