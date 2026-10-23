import argparse
import re
import tomllib

import pytest

from fox3_agent import dpapi
from fox3_agent.secrets_store import SecretError, SecretStore
from fox3_agent.setup import commands
from fox3_agent.setup.messages import LANGUAGES, MESSAGES, tr
from fox3_agent.setup.tomlout import with_state_dir


def test_with_state_dir_preserves_everything_else():
    src = ('[central]\nurl = "https://c.example"\nca_file = "C:\\\\ca.pem"\nverify_tls = true\n\n'
           '[paths]\nstate_dir = "old"\n\n[ui]\nlanguage = "eu"\n\n[sources.tacview]\ncloud_files = "skip"\n')
    new = tomllib.loads(with_state_dir(src, 'C:\\Users\\a "b"\\state'))
    assert new["paths"]["state_dir"] == 'C:\\Users\\a "b"\\state'
    assert new["central"] == {"url": "https://c.example", "ca_file": "C:\\ca.pem", "verify_tls": True}
    assert new["ui"] == {"language": "eu"} and new["sources"]["tacview"] == {"cloud_files": "skip"}


def test_with_state_dir_rejects_control_chars_and_invalid():
    with pytest.raises(ValueError):
        with_state_dir('[central]\nurl = "https://c.example"\n', "a\nb")
    with pytest.raises(ValueError):
        with_state_dir('[central]\nurl = "ftp://c"\n', "x")


def test_message_parity_and_formatting():
    base = set(MESSAGES["en"])
    names = {k: sorted(re.findall(r"\{(\w+)\}", v)) for k, v in MESSAGES["en"].items()}
    for lang in LANGUAGES:
        assert set(MESSAGES[lang]) == base, lang
        for k, v in MESSAGES[lang].items():
            assert v.strip() and sorted(re.findall(r"\{(\w+)\}", v)) == names[k], (lang, k)
    assert "ONLINE" in tr("xx", "summary", path="p")  # unknown language falls back


def test_secret_round_trip_and_not_plaintext(tmp_path):
    s = SecretStore(tmp_path / "st")
    s.set("dcsbot_api_key", "p4ss-W0rd-XYZ")
    s.set("dcsbot_db_url", "postgres://u:pw@h/db")
    assert s.get("dcsbot_api_key") == "p4ss-W0rd-XYZ" and s.names() == ["dcsbot_api_key", "dcsbot_db_url"]
    raw = (tmp_path / "st" / "secrets.bin").read_bytes()
    if dpapi.AVAILABLE:
        assert b"p4ss-W0rd-XYZ" not in raw and raw.startswith(b"DPAPI1")
    assert s.delete("dcsbot_api_key") and not s.delete("dcsbot_api_key")
    assert s.names() == ["dcsbot_db_url"] and not list((tmp_path / "st").glob("*.tmp"))


def test_secret_bad_names(tmp_path):
    s = SecretStore(tmp_path)
    for bad in ("", "UP", "a b", "../x", "x" * 65):
        with pytest.raises(SecretError):
            s.set(bad, "v")
    with pytest.raises(SecretError):
        s.set("ok", "")


def test_secret_cli_hidden_prompt_never_prints(tmp_path, capsys):
    cfg = tmp_path / "agent.toml"
    cfg.write_text(f'[central]\nurl = "https://c.example"\n[paths]\nstate_dir = {str(tmp_path / "st")!r}\n')
    asked = []
    a = argparse.Namespace(action="set", name="dcsbot_api_key", config=str(cfg), language="en")
    assert commands.run_secret(a, prompt=lambda p: asked.append(p) or "TOPSECRET") == 0
    assert asked and "TOPSECRET" not in capsys.readouterr().out
    a.action = "list"
    assert commands.run_secret(a) == 0
    out = capsys.readouterr().out
    assert "dcsbot_api_key" in out and "TOPSECRET" not in out
    a.action = "delete"
    assert commands.run_secret(a) == 0 and commands.run_secret(a) == 1
