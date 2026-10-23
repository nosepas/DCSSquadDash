"""Production configuration: strict TOML, secrets only from environment variables, https required."""
from pathlib import Path

import pytest

from fox3_central import cli
from fox3_central.settings_file import SettingsError, from_mapping, load

EXAMPLE = Path(__file__).resolve().parents[1] / "contracts" / "config" / "central.example.toml"


def _cfg(**over):
    cfg = {"server": {"public_base_url": "https://fox3.example.org", "port": 9000}, "database": {"url_env": "T_DB"}}
    cfg.update(over)
    return cfg


@pytest.fixture(autouse=True)
def env(monkeypatch):
    monkeypatch.setenv("T_DB", "postgresql+psycopg://u@h/db")
    monkeypatch.setenv("T_SECRET", "s3cret")


def test_example_file_is_valid_once_its_placeholders_are_filled(monkeypatch):
    monkeypatch.setenv("FOX3_DATABASE_URL", "sqlite:///x.db")
    text = EXAMPLE.read_text("utf-8").replace("https://CHANGE-ME.example.org", "https://fox3.example.org")
    import tomllib
    settings, listen = from_mapping(tomllib.loads(text))
    assert settings.public_base_url == "https://fox3.example.org" and listen == {"bind": "127.0.0.1", "port": 8000}
    assert not settings.demo_login and not settings.discord_enabled


def test_values_and_secrets_come_from_the_right_places():
    settings, listen = from_mapping(_cfg(discord={"client_id": "123", "client_secret_env": "T_SECRET", "admin_ids": [1, "2"]}))
    assert settings.db_url.startswith("postgresql+psycopg") and settings.discord_client_secret == "s3cret"
    assert settings.admin_ids == ["1", "2"] and listen["port"] == 9000 and settings.discord_enabled


@pytest.mark.parametrize("cfg,message", [
    ({"extra": {}}, "unknown section"),
    ({"server": {"public_base_url": "https://x.org", "typo": 1}}, "unknown key"),
    ({"server": {"public_base_url": "http://fox3.example.org"}}, "https"),
    ({"server": {"public_base_url": "nonsense"}}, "full URL"),
    ({"database": {}}, "database"),
    ({"discord": {"client_id": "1", "client_secret_env": "NOT_SET"}}, "empty"),
    ({"database": {"url_env": "NOT_SET_EITHER"}}, "must hold"),
])
def test_bad_configuration_is_refused_with_a_clear_message(cfg, message):
    with pytest.raises(SettingsError, match=message):
        from_mapping(_cfg(**cfg))


def test_plain_http_is_fine_for_localhost_only():
    settings, _ = from_mapping(_cfg(server={"public_base_url": "http://localhost:8000"}))
    assert settings.public_base_url == "http://localhost:8000" and settings.cookie_secure is False


def test_demo_login_can_never_be_switched_on_from_the_file():
    assert from_mapping(_cfg())[0].demo_login is False


def test_cli_reports_errors_without_a_traceback(tmp_path, capsys):
    assert cli.main(["check-config", "--config", str(tmp_path / "missing.toml")]) == 2
    assert "cannot read" in capsys.readouterr().out


def test_cli_migrate_prepares_the_database(tmp_path, capsys, monkeypatch):
    db = f"sqlite:///{(tmp_path / 'c.sqlite').as_posix()}"
    monkeypatch.setenv("T_DB", db)
    cfg = tmp_path / "central.toml"
    cfg.write_text('[server]\npublic_base_url = "https://fox3.example.org"\n[database]\nurl_env = "T_DB"\n', "utf-8")
    assert cli.main(["check-config", "--config", str(cfg)]) == 0 and cli.main(["migrate", "--config", str(cfg)]) == 0
    from sqlalchemy import create_engine, inspect
    assert "servers" in inspect(create_engine(db)).get_table_names()
    assert "up to date" in capsys.readouterr().out
    assert load(cfg)[0].db_url == db


def test_scaffold_writes_files_that_the_real_loader_accepts(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("FOX3_DATABASE_URL", "sqlite:///x.db")
    monkeypatch.setenv("FOX3_DISCORD_CLIENT_SECRET", "s")
    out = tmp_path / "cfg"
    args = ["init", "--hostname", "fox3.example.org", "--out", str(out), "--port", "8100", "--admin-id", "111", "--admin-id", "222",
            "--discord-client-id", "999"]
    assert cli.main(args) == 0
    settings, listen = load(out / "central.toml")
    assert settings.public_base_url == "https://fox3.example.org" and settings.admin_ids == ["111", "222"] and listen["port"] == 8100
    caddy = (out / "Caddyfile").read_text("utf-8")
    assert caddy.startswith("fox3.example.org {") and "reverse_proxy 127.0.0.1:8100" in caddy and "flush_interval -1" in caddy


def test_scaffold_never_overwrites_an_admins_edits(tmp_path):
    (tmp_path / "central.toml").write_text("# my edits", "utf-8")
    assert cli.main(["init", "--hostname", "fox3.example.org", "--out", str(tmp_path)]) == 0
    assert (tmp_path / "central.toml").read_text("utf-8") == "# my edits" and (tmp_path / "Caddyfile").exists()


@pytest.mark.parametrize("bad", [["--hostname", "not a host"], ["--hostname", "a.example.org", "--admin-id", "12x"],
                                 ["--hostname", "a.example.org", "--port", "70000"], ["--hostname", 'a.example.org", x = "']])
def test_scaffold_rejects_hostile_or_malformed_answers(tmp_path, bad, capsys):
    assert cli.main(["init", "--out", str(tmp_path), *bad]) == 2
    assert not (tmp_path / "central.toml").exists()
