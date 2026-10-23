import io
import tomllib

import pytest

from fox3_agent import cli
from fox3_agent.config import ConfigError, from_mapping, load_config
from fox3_agent.scaffold import ScaffoldError, render_agent_toml, write_agent_toml
from fox3_agent.sources.dcsbot import DcsBotConfig


def test_written_file_loads_with_load_config(tmp_path):
    path = write_agent_toml(tmp_path / "cfg", "https://fox3.example.org/", dcsbot_api_key_env="FOX3_DCSBOT_API_KEY")
    cfg = load_config(path)
    assert cfg.central.url == "https://fox3.example.org"
    assert cfg.state_dir == tmp_path / "cfg" / "state"
    assert DcsBotConfig.from_mapping(cfg.dcsbot).api_key_env == "FOX3_DCSBOT_API_KEY"


def test_minimal_file_without_dcsbot_and_custom_state_dir(tmp_path):
    path = write_agent_toml(tmp_path, "http://localhost:8000", state_dir=tmp_path / "my state")
    cfg = load_config(path)
    assert cfg.dcsbot is None and cfg.state_dir == tmp_path / "my state"


def test_windows_paths_survive_toml_escaping():
    text = render_agent_toml("https://x.example.org", __import__("pathlib").PureWindowsPath("C:/ProgramData/FOX3Agent/state"))
    assert tomllib.loads(text)["paths"]["state_dir"] == r"C:\ProgramData\FOX3Agent\state"


def test_never_overwrites(tmp_path):
    write_agent_toml(tmp_path, "https://x.example.org")
    (tmp_path / "agent.toml").write_text("# mine", "utf-8")
    with pytest.raises(ScaffoldError, match="already exists"):
        write_agent_toml(tmp_path, "https://other.example.org")
    assert (tmp_path / "agent.toml").read_text("utf-8") == "# mine"


@pytest.mark.parametrize("url", [
    "", "ftp://x.org", "http://fox3.example.org", "https://user:pw@x.example.org", "https://x.example.org/?a=1",
    'https://x.example.org"\n[evil]', "https://x.example.org/ a", "javascript:alert(1)", "https://x.example.org#frag",
])
def test_hostile_central_urls_refused(tmp_path, url):
    with pytest.raises((ScaffoldError, ConfigError)):
        write_agent_toml(tmp_path, url)
    assert not (tmp_path / "agent.toml").exists()


@pytest.mark.parametrize("name", ["", "1ABC", "has space", 'X"\n[evil]', "sk-secretvalue!", "A" * 80, "a=b"])
def test_env_name_must_be_a_name_not_a_secret(tmp_path, name):
    with pytest.raises(ScaffoldError):
        write_agent_toml(tmp_path, "https://x.example.org", dcsbot_api_key_env=name)


def test_control_characters_in_state_dir_refused(tmp_path):
    with pytest.raises(ScaffoldError):
        render_agent_toml("https://x.example.org", tmp_path / "a\nb")


def test_cli_init_and_second_run_refuses(tmp_path, capsys):
    args = ["init", "--central-url", "https://x.example.org", "--out", str(tmp_path)]
    assert cli.main(args) == 0 and (tmp_path / "agent.toml").exists()
    assert cli.main(args) == 1
    assert "already exists" in capsys.readouterr().out


def test_cli_init_rejects_bad_url(tmp_path, capsys):
    assert cli.main(["init", "--central-url", "http://evil.example.org", "--out", str(tmp_path)]) == 1
    assert not (tmp_path / "agent.toml").exists()


def test_pair_reads_code_from_stdin_and_never_prints_it(tmp_path, monkeypatch, capsys):
    path = write_agent_toml(tmp_path, "https://x.example.org")
    seen = {}

    def fake_pair(self, code, name, version):
        seen["code"] = code
        return {"agent_id": "aid", "api_key": "aid.secret", "server_id": "sid"}

    monkeypatch.setattr(cli.CentralClient, "pair", fake_pair)
    monkeypatch.setattr("sys.stdin", io.StringIO("ABCD-1234\n"))
    assert cli.main(["pair", "--config", str(path), "--code-stdin"]) == 0
    assert seen["code"] == "ABCD-1234"
    out = capsys.readouterr().out
    assert "ABCD-1234" not in out and "aid.secret" not in out


def test_pair_requires_a_code_source(tmp_path):
    with pytest.raises(SystemExit):
        cli.main(["pair", "--config", str(tmp_path / "agent.toml")])


def test_from_mapping_accepts_rendered_text():
    assert from_mapping(tomllib.loads(render_agent_toml("https://x.example.org", __import__("pathlib").Path("s"))))
