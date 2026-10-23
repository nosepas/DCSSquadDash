"""Error type of the Lua subset parser. Messages never echo file content (it may contain player data)."""
from __future__ import annotations


class LuaParseError(ValueError):
    def __init__(self, line: int, col: int, message: str) -> None:
        super().__init__(f"line {line}, col {col}: {message}")
        self.line = line
        self.col = col
        self.message = message


def error_at(text: str, pos: int, message: str) -> LuaParseError:
    """Build a LuaParseError for the character offset `pos` of `text`."""
    pos = max(0, min(pos, len(text)))
    line = text.count("\n", 0, pos) + 1
    col = pos - text.rfind("\n", 0, pos)
    return LuaParseError(line, col, message)
