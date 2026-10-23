import sys

import pytest

from fox3_agent import dpapi
from fox3_agent.config import ConfigError, from_mapping, load_config
from fox3_agent.credentials import Credentials, CredentialStore
from fox3_agent.detect import detect


def test_config_defaults_and_foothold_path(tmp_path):
    cfg = from_mapping({"central": {"url": "https://fox.example.org/"}, "paths": {"foothold_saves": "D:/s"}}, tmp_path)
    assert cfg.central.url == "https://fox.example.org" and cfg.foothold.enabled
    assert str(cfg.foothold.saves_dir).endswith("s") and cfg.queue_path == tmp_path / "state" / "queue.sqlite"


@pytest.mark.parametrize("raw", [
    {}, {"central": {"url": "ftp://x"}}, {"central": {"url": "http://fox.example.org"}},
    {"central": {"url": "https://x.org"}, "mission_type": "other"},
])
def test_config_rejects_bad_values(raw):
    with pytest.raises(ConfigError):
        from_mapping(raw)


def test_plain_http_only_for_localhost_or_explicit_opt_in():
    assert from_mapping({"central": {"url": "http://localhost:8000"}})
    assert from_mapping({"central": {"url": "http://10.0.0.5", "allow_insecure_http": True}})


def test_load_config_reports_unreadable_file(tmp_path):
    with pytest.raises(ConfigError):
        load_config(tmp_path / "missing.toml")


@pytest.mark.skipif(sys.platform != "win32", reason="without DPAPI the credentials file is stored in plain text (and says so)")
def test_credentials_round_trip_and_env_override(tmp_path, monkeypatch):
    store = CredentialStore(tmp_path, env_var="FOX3_TEST_KEY")
    creds = Credentials("aid", "aid.secret", "sid")
    store.save(creds)
    assert store.load() == creds
    assert b"secret" not in (tmp_path / "credentials.bin").read_bytes()  # not readable as plain text
    assert "secret" not in repr(creds)
    monkeypatch.setenv("FOX3_TEST_KEY", "envid.envsecret")
    assert store.load().api_key == "envid.envsecret"


@pytest.mark.skipif(sys.platform != "win32", reason="DPAPI is Windows only")
def test_dpapi_round_trip():
    blob = dpapi.protect(b"hello")
    assert blob != b"hello" and dpapi.unprotect(blob) == b"hello"


def test_detect_finds_foothold_dcsbot_and_tacview(tmp_path):
    saves = tmp_path / "Saved Games" / "DCS.server1" / "Missions" / "Saves"
    saves.mkdir(parents=True)
    (saves / "foothold.status").write_text("x")
    (tmp_path / "DCSServerBot" / "config").mkdir(parents=True)
    (tmp_path / "Documents" / "Tacview").mkdir(parents=True)
    (tmp_path / "Documents" / "Tacview" / "a.acmi").write_text("x")
    d = detect(tmp_path)
    assert d.foothold_saves[0].path == saves and "found" in d.foothold_saves[0].note
    assert d.dcsserverbot[0].note == "has config/" and "1 .acmi" in d.tacview[0].note


def test_detect_on_empty_home_is_empty(tmp_path):
    d = detect(tmp_path)
    assert not (d.saved_games or d.foothold_saves or d.tacview)


def test_example_config_stays_valid():
    """The shipped example must load: config and DCSServerBot options are validated by the real code."""
    from pathlib import Path

    from fox3_agent.sources.dcsbot import DcsBotConfig

    cfg = load_config(Path(__file__).resolve().parents[2] / "contracts" / "config" / "agent.example.toml")
    assert cfg.central.url.startswith("https://") and cfg.foothold.enabled
    DcsBotConfig.from_mapping({"mission_type": cfg.mission_type, **cfg.dcsbot})
