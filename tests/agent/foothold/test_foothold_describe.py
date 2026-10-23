from __future__ import annotations

import pytest
from foothold_samples import IDENTITY_STATS, LEGACY_STATS, full_file, write_saves

from fox3_agent.sources.foothold import describe_structure, parse_lua

SECRETS = ["Mitch", "Tomy10", "APOLLO", "Alpha", "Bravo", "Charlie", "Delta", "Soldier M4", "M-2 Bradley", "SA-6", "F-16C_50", "WPT 8",
           "Intercept Bombers", "Bombers north", "Unknown", "id-aaa", "id-bbb", "dynamictexaco", "texaco", "kutaisicaptured", "NoPos",
           "43.118", "40.572", "43.484", "40.146", "5326", "481.08", "43.29", "12.5", "missioncompleted"]


@pytest.mark.parametrize("stats", [LEGACY_STATS, IDENTITY_STATS])
def test_no_values_names_or_coordinates_leak(tmp_path, stats):
    path = write_saves(tmp_path, full_file(stats, "zonePersistance['future'] = { ['SecretKey']={ ['Tomy10']='Mitch', ['n']=5 } }\n"))
    for out in (describe_structure(path), describe_structure(parse_lua(path.read_text("utf-8")))):
        for secret in SECRETS + ["SecretKey"]:
            assert secret not in out, secret


def test_outline_shows_structure():
    out = describe_structure(parse_lua(full_file(IDENTITY_STATS, "zonePersistance['brandNew'] = { 1, 2 }\n")))
    assert "zones: table x1, size 4..4" in out
    assert "side: int x4" in out and "range 0..2" in out
    assert "playerStatsIdentityVersion: int x1, range 1..1" in out
    assert "brandNew: sequence x1, size 2..2" in out
    assert "latitude: float x" in out and "latitude: float x2, range" not in out  # coordinate ranges are suppressed
    assert "keys redacted: 4 str" in out  # zone names counted, not shown
    assert "Points: int x" in out


def test_parse_error_is_reported_without_content(tmp_path):
    path = write_saves(tmp_path, "zonePersistance = {}\nzonePersistance['SecretName'] = SecretName")
    out = describe_structure(path)
    assert out.startswith("PARSE ERROR") and "SecretName" not in out


def test_missing_file(tmp_path):
    assert describe_structure(tmp_path / "nope.lua").startswith("CANNOT READ FILE")
