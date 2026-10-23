"""The Lua lexer must never backtrack exponentially on hostile, unterminated strings."""
import time

import pytest

from fox3_agent.sources.foothold.lua_errors import LuaParseError
from fox3_agent.sources.foothold.lua_lexer import tokenize

HOSTILE = ["\\z        " * 500, "\\z " * 1700, "a\\z  b\\z   " * 400, "\\\\z    " * 600, "\\z\n\n\n  " * 600]


@pytest.mark.parametrize("quote", ['"', "'"])
@pytest.mark.parametrize("body", HOSTILE)
def test_unterminated_string_fails_fast(quote, body):
    start = time.perf_counter()
    with pytest.raises(LuaParseError):
        tokenize(quote + body)
    assert time.perf_counter() - start < 0.5


@pytest.mark.parametrize("quote", ['"', "'"])
def test_valid_strings_still_decode(quote):
    q = quote
    cases = {
        r"a\nb": "a\nb", r"\65\066": "AB", r"\x41": "A", r"\u{20AC}": "\u20ac", r"x\z   y": "xy",
        r"x\z" + " " * 3000 + "y": "xy", r"\\": "\\", rf"\{q}": q, "a\\\nb": "a\nb", r"\xC3\xA9": "\u00e9",
    }
    for body, expected in cases.items():
        assert tokenize(f"{q}{body}{q}")[0][:2] == ("str", expected), body


def test_valid_after_many_z_segments():
    text = '"' + "\\z      " * 500 + 'end"'
    assert tokenize(text)[0][1] == "end"
