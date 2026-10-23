"""Small SQL text helpers shared by repositories."""
from __future__ import annotations

ESCAPE = "\\"


def like_contains(term: str) -> str:
    """Pattern for `LIKE ... ESCAPE '\\'` matching `term` as a literal substring (%, _ and the escape char lose their meaning)."""
    esc = term.lower().replace(ESCAPE, ESCAPE * 2).replace("%", ESCAPE + "%").replace("_", ESCAPE + "_")
    return f"%{esc}%"
