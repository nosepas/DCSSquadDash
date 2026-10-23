"""Hostile-template suite: structural limits on import and the output cap of the writer (DoS guard)."""
import json
import time
import tracemalloc

import pytest
from dtc_cases import CASES, F14_TERRAIN, load

from fox3_dtc import DtcError, export_dtc, import_dtc
from fox3_dtc.io import read_json, write_json


def _nest(depth: int, key: str = "k") -> bytes:
    return (f'{{"{key}":' * depth + "1" + "}" * depth).encode()


def _dumps(obj) -> bytes:
    return json.dumps(obj).encode()


HOSTILE = {
    "deep_100": _nest(100),
    "deep_600": _nest(600),
    "deep_25": _nest(24),
    "deep_amplifier": _nest(300, "x" * 100),
    "deep_parser_bomb": b"[" * 200_000 + b"]" * 200_000,
    "huge_key": _dumps({"k" * 129: 1}),
    "wide_object": _dumps({str(i): 0 for i in range(10_001)}),
    "wide_list": _dumps({"a": [0] * 100_001}),
    "huge_string": _dumps({"a": "s" * 100_001}),
    "many_nodes": _dumps({"a": [[0] * 1000] * 400}),
}


@pytest.mark.parametrize("name", list(HOSTILE))
def test_hostile_template_is_rejected_quickly(name):
    raw = HOSTILE[name]
    if name == "deep_parser_bomb":
        raw = b'{"a":' + raw + b"}"
    tracemalloc.start()
    t0 = time.perf_counter()
    with pytest.raises(DtcError):
        read_json(raw)
    with pytest.raises(DtcError):
        import_dtc(raw)
    elapsed, peak = time.perf_counter() - t0, tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    assert elapsed < 1.0
    assert peak < 200 * 1024 * 1024


def test_limit_boundaries_are_accepted():
    assert read_json(_nest(23)) is not None
    assert read_json(_dumps({"k" * 128: "s" * 100_000, "l": [0] * 100_000}))
    assert len(read_json(_dumps({str(i): 0 for i in range(10_000)}))) == 10_000


def test_writer_aborts_on_output_amplification():
    data: dict = {}
    node = data
    for _ in range(400):  # would amplify to ~ depth^2 x key length spaces
        node["k" * 1000] = {}
        node = node["k" * 1000]
    t0 = time.perf_counter()
    with pytest.raises(DtcError):
        write_json(data)
    assert time.perf_counter() - t0 < 1.0


def test_writer_converts_recursion_error():
    data: dict = {}
    node = data
    for _ in range(5000):
        node["k"] = {}
        node = node["k"]
    with pytest.raises(DtcError):
        write_json(data)


@pytest.mark.parametrize("case", CASES)
def test_real_and_synthetic_files_still_import_export_byte_identical(case):
    aircraft, raw = load(case)
    res = import_dtc(raw)
    if aircraft == "F-14BU":
        res.model["terrain"] = F14_TERRAIN
    assert export_dtc(res.model, res.template) == raw
    assert write_json(read_json(raw)) == raw
