from __future__ import annotations

import math
import time

import pytest

from fox3_agent.sources.foothold import LuaParseError, parse_lua


def one(expr: str):
    return parse_lua(f"zonePersistance = {{}}\nzonePersistance['v'] = {expr}")["v"]


@pytest.mark.parametrize(("expr", "expected"), [
    ("5", 5), ("-5", -5), ("1.5", 1.5), ("-2.5e2", -250.0), ("1E3", 1000.0), ("0x1F", 31), ("0x1p4", 16.0), (".5", 0.5),
    ("true", True), ("false", False), ("'a\\tb'", "a\tb"), ('"q\\"q"', 'q"q'), ("'it\\'s'", "it's"), ("'a\\\\b'", "a\\b"),
    ("'\\65\\066'", "AB"), ("'\\x41'", "A"), ("'\\195\\169'", "é"), ("'café ✈'", "café ✈"),
    ("'a\\z   \n   b'", "ab"), ("[[long\nstring]]", "long\nstring"), ("[==[a]]b]==]", "a]]b"), ("[[\nskip first]]", "skip first"),
    ("'\\u{e9}'", "é"), ("'esc\\\nnl'", "esc\nnl"),
])
def test_scalars(expr, expected):
    assert one(expr) == expected


def test_non_finite_numbers():
    assert one("1e309") == math.inf and one("-1e309") == -math.inf
    assert one("inf") == math.inf and one("-inf") == -math.inf
    assert math.isnan(one("nan")) and math.isnan(one("-nan")) and math.isnan(one("-nan(ind)"))
    assert one("1.#INF") == math.inf and math.isnan(one("-1.#IND"))


def test_nil_removes_key():
    out = parse_lua("zonePersistance = {}\nzonePersistance['a'] = 1\nzonePersistance['a'] = nil\nzonePersistance['b'] = { x = nil, y = 1 }")
    assert out == {"b": {"y": 1}}


def test_tables_and_sequences():
    assert one("{ }") == {}
    assert one("{ 1, 2, 3, }") == [1, 2, 3]
    assert one("{ [1]=10, [2]=20 }") == [10, 20]
    assert one("{ [2]=20 }") == {2: 20}
    assert one("{ [1]=1, [3]=3 }") == {1: 1, 3: 3}
    assert one("{ 'a'; 'b'; x = 1; }") == {1: "a", 2: "b", "x": 1}
    assert one("{ [1.0]='f' }") == ["f"]
    assert one("{ ['a b']={ ['c']={ 1,{ } } } }") == {"a b": {"c": [1, {}]}}


def test_comments_and_statement_separators():
    src = """-- header
zonePersistance = {} --[[ block
comment ]] ; zonePersistance['a'] = 1 --[==[ x ]] still ]==] zonePersistance["b"] = "two"; ;
zonePersistance.c = { 3 } -- trailing"""
    assert parse_lua(src) == {"a": 1, "b": "two", "c": [3]}


def test_dash_dash_bracket_without_long_form_is_line_comment():
    assert parse_lua("zonePersistance = {} --[ not long\nzonePersistance.a = 1") == {"a": 1}


def test_accepts_bytes_and_bom():
    assert parse_lua("﻿zonePersistance = {}\nzonePersistance.a='café'".encode()) == {"a": "café"}


def test_empty_input_gives_empty_dict():
    assert parse_lua("") == {}
    assert parse_lua("zonePersistance = {}") == {}


@pytest.mark.parametrize("src", [
    "zonePersistance = {}\nzonePersistance['a'] = {",
    "zonePersistance = {}\nzonePersistance['a'] = { 1 2 }",
    "zonePersistance = {}\nzonePersistance['a'] =",
    "zonePersistance = {}\nzonePersistance['a'] = 'unterminated",
    "zonePersistance = {}\nzonePersistance['a'] = 'line\nbreak'",
    "zonePersistance = {}\nzonePersistance['a'] = [[never closed",
    "zonePersistance = {}\n--[[ never closed",
    "zonePersistance = {}\nzonePersistance['a'] = foo",
    "zonePersistance = {}\nzonePersistance['a'] = 1 + 2",
    "zonePersistance = {}\nzonePersistance['a'] = function() end",
    "zonePersistance = {}\nzonePersistance['a'] = os.execute('x')",
    "zonePersistance = {}\nzonePersistance['a'] = { [nil]=1 }",
    "zonePersistance = {}\nzonePersistance['a'] = { [{}]=1 }",
    "zonePersistance = {}\nzonePersistance['a'] = -'x'",
    "zonePersistance = {}\nzonePersistance['a']['b'] = 1",
    "zonePersistance = {}\nother = 1",
    "zonePersistance = 5",
    "zonePersistance = {}\nzonePersistance['a'] = 1 @",
    "zonePersistance = {}\nzonePersistance['a'] = 0xZZ",
    "zonePersistance = {}\nzonePersistance['a' = 1",
])
def test_malformed_input_raises_clear_error(src):
    with pytest.raises(LuaParseError) as info:
        parse_lua(src)
    assert info.value.line >= 1 and info.value.col >= 1 and info.value.message


def test_error_position():
    with pytest.raises(LuaParseError) as info:
        parse_lua("zonePersistance = {}\n\nzonePersistance['a'] = { 1 2 }")
    assert (info.value.line, info.value.col) == (3, 28)


def test_error_message_does_not_echo_content():
    with pytest.raises(LuaParseError) as info:
        parse_lua("zonePersistance = {}\nzonePersistance['SecretName'] = SecretName")
    assert "SecretName" not in str(info.value)


def test_depth_limit():
    ok = "{" * 64 + "}" * 64
    assert one(ok) is not None
    with pytest.raises(LuaParseError, match="deeper"):
        one("{" * 65 + "}" * 65)
    with pytest.raises(LuaParseError, match="deeper"):
        parse_lua("zonePersistance = {}\nzonePersistance.a = " + "{" * 11 + "}" * 11, max_depth=10)


def test_deep_nesting_does_not_blow_the_stack():
    with pytest.raises(LuaParseError):
        one("{" * 100000)


def test_size_limit():
    with pytest.raises(LuaParseError, match="limit"):
        parse_lua("zonePersistance = {}" + " " * 100, max_bytes=50)
    with pytest.raises(LuaParseError, match="limit"):
        parse_lua(b"x" * 100, max_bytes=50)


def test_parses_five_megabytes_quickly():
    unit = ("['u%d']={ ['side']=2,['level']=1,['lat_long']={ ['longitude']=40.5,['latitude']=43.1,['altitude']=0 },"
            "['remainingUnits']={ [1]={ [1]='Soldier M4 GRG',[2]='M-2 Bradley' } } },\n")
    body = "".join(unit % i for i in range(int(5_000_000 / len(unit)) + 1))
    src = "zonePersistance = {}\nzonePersistance['zones'] = {\n" + body + "}\n"
    assert len(src) >= 5_000_000
    start = time.perf_counter()
    out = parse_lua(src)
    assert time.perf_counter() - start < 15
    assert len(out["zones"]) > 20000
