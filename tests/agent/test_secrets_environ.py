from fox3_agent import secrets_store
from fox3_agent.secrets_store import SecretStore


def test_export_adds_missing_variables_and_keeps_existing_ones(tmp_path, monkeypatch):
    monkeypatch.setattr(secrets_store.dpapi, "AVAILABLE", False)
    store = SecretStore(tmp_path)
    store.set("fox3_dcsbot_api_key", "from-store")
    store.set("fox3_dcsbot_db_url", "sqlite:///x")
    env = {"FOX3_DCSBOT_DB_URL": "already-set"}
    assert store.export_to_environ(env) == ["FOX3_DCSBOT_API_KEY"]
    assert env == {"FOX3_DCSBOT_API_KEY": "from-store", "FOX3_DCSBOT_DB_URL": "already-set"}


def test_export_never_raises_on_a_broken_file(tmp_path):
    (tmp_path / "secrets.bin").write_bytes(b"garbage")
    env: dict[str, str] = {}
    assert SecretStore(tmp_path).export_to_environ(env) == [] and env == {}
