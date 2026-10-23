import pytest
from dcsbot_fakes import SERVER, Clock, FakeBot

from fox3_agent.sources.dcsbot import ConfigError, DcsBotConfig, DcsBotSource


def test_api_key_field_still_works():
    assert DcsBotConfig.from_mapping({"api_key": "k"}).resolved_api_key({}) == "k"


def test_api_key_env_resolved_from_environment_and_not_in_repr():
    cfg = DcsBotConfig.from_mapping({"api_key_env": "MY_KEY"})
    assert cfg.resolved_api_key({"MY_KEY": "secret"}) == "secret" and cfg.resolved_api_key({}) is None
    assert "secret" not in repr(cfg)


@pytest.mark.parametrize("bad", ["", "has space", "1X", "k=v", "a" * 70, 5])
def test_api_key_env_must_be_a_variable_name(bad):
    with pytest.raises(ConfigError):
        DcsBotConfig.from_mapping({"api_key_env": bad})


def test_both_forms_are_rejected():
    with pytest.raises(ConfigError, match="either"):
        DcsBotConfig.from_mapping({"api_key": "k", "api_key_env": "X"})


def test_source_sends_key_from_env(monkeypatch):
    monkeypatch.setenv("FOX3_TEST_BOT_KEY", "from-env")
    bot = FakeBot([SERVER], api_key="from-env")
    cfg = DcsBotConfig.from_mapping({"rest_enabled": True, "api_key_env": "FOX3_TEST_BOT_KEY", "server_name": "FOX3 Test"})
    src = DcsBotSource(cfg, clock=Clock(), transport=bot.transport())
    assert any(m.kind == "server_info" for m in src.poll()) and src.warnings() == []


def test_missing_env_value_gives_actionable_auth_warning(monkeypatch):
    monkeypatch.delenv("FOX3_TEST_BOT_KEY", raising=False)
    bot = FakeBot([SERVER], api_key="needed")
    cfg = DcsBotConfig.from_mapping({"rest_enabled": True, "api_key_env": "FOX3_TEST_BOT_KEY", "server_name": "FOX3 Test"})
    src = DcsBotSource(cfg, clock=Clock(), transport=bot.transport())
    assert src.poll() == []
    (w,) = src.warnings()
    assert w.code == "DCSBOT_AUTH_FAILED" and "FOX3_TEST_BOT_KEY" in w.message
