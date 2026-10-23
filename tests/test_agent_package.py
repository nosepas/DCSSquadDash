"""Personalised agent download: contents, one-time pairing code, access control, rate limit, texts, settings."""
import io
import re
import tomllib
import zipfile

import pytest
from fastapi.testclient import TestClient

from fox3_agent.config import load_config
from fox3_central.app import create_app
from fox3_central.config import Settings
from fox3_central.repositories import servers
from fox3_central.scaffold import central_toml
from fox3_central.services import agent_package
from fox3_central.services.agent_package_texts import LANGUAGES, TEXTS, leeme
from fox3_central.settings_file import SettingsError, from_mapping

EXE = b"MZ-fake-exe" * 100
PAIR = {"agent_name": "x", "agent_version": "1"}


@pytest.fixture
def agent_dir(tmp_path):
    d = tmp_path / "agent"
    d.mkdir()
    (d / "fox3-agent.exe").write_bytes(EXE)
    (d / "fox3-agent.version").write_text("1.2.3\n")
    return d


@pytest.fixture
def pkg_app(db_url, agent_dir):
    return create_app(Settings(db_url=db_url, demo_login=True, web_dir=None, elevation_url="", agent_dir=agent_dir,
                               public_base_url="https://fox3.example.org"))


@pytest.fixture
def admin(pkg_app):
    c = TestClient(pkg_app, base_url="https://testserver", follow_redirects=False)
    assert c.get("/api/v1/auth/demo?admin=true").status_code == 302
    c.headers["X-CSRF-Token"] = c.get("/api/v1/me").json()["csrf_token"]
    return c


@pytest.fixture
def sid(pkg_app):
    with pkg_app.state.ctx.tx() as cn:
        return servers.create(cn, "Escuadron 1", "foothold")["server_id"]


def _get(admin, sid, **params):
    r = admin.post(f"/api/v1/admin/servers/{sid}/agent-package", params=params)
    assert r.status_code == 200, r.text
    return r, zipfile.ZipFile(io.BytesIO(r.content))


def test_status_and_zip_contents(admin, sid):
    assert admin.get("/api/v1/admin/agent-package").json() == {"available": True, "version": "1.2.3", "size_bytes": len(EXE), "reason": None}
    r, z = _get(admin, sid)
    assert r.headers["content-type"] == "application/zip" and r.headers["cache-control"] == "no-store"
    assert r.headers["x-pairing-expires-minutes"] == "15"
    assert r.headers["content-disposition"] == 'attachment; filename="FOX3-Agent-Escuadron-1.zip"'
    assert sorted(z.namelist()) == ["INSTALAR.cmd", "LEEME.txt", "agent.toml", "fox3-agent.exe", "pairing-code.txt"]
    assert z.read("fox3-agent.exe") == EXE
    assert z.read("INSTALAR.cmd") == b'@echo off\r\n"%~dp0fox3-agent.exe" setup --here "%~dp0"\r\necho.\r\npause\r\n'
    assert re.fullmatch(r"[A-Z2-7]{10}\r\n", z.read("pairing-code.txt").decode("ascii"))


def test_windowless_exe_is_included_when_built(admin, sid, agent_dir):
    (agent_dir / "fox3-agentw.exe").write_bytes(b"MZ-windowless")
    _, z = _get(admin, sid)
    assert z.read("fox3-agentw.exe") == b"MZ-windowless"


def test_agent_toml_loads_with_the_real_agent_loader(admin, sid, tmp_path):
    _, z = _get(admin, sid, language="gl")
    (tmp_path / "agent.toml").write_bytes(z.read("agent.toml"))
    assert load_config(tmp_path / "agent.toml").central.url == "https://fox3.example.org"
    assert tomllib.loads(z.read("agent.toml").decode())["ui"] == {"language": "gl"}


def test_pairing_code_works_once_and_each_download_is_new(admin, sid, pkg_app):
    codes = [_get(admin, sid)[1].read("pairing-code.txt").decode().strip() for _ in range(2)]
    assert codes[0] != codes[1]
    c = TestClient(pkg_app)
    assert c.post("/agent/v1/pair", json={"pairing_code": codes[0], **PAIR}).status_code == 200
    assert c.post("/agent/v1/pair", json={"pairing_code": codes[0], **PAIR}).status_code == 400
    assert c.post("/agent/v1/pair", json={"pairing_code": codes[1], **PAIR}).status_code == 200


def test_pairing_code_expires(admin, sid, pkg_app, monkeypatch):
    code = _get(admin, sid)[1].read("pairing-code.txt").decode().strip()
    from fox3_central.services import agents
    monkeypatch.setattr(agents, "now", lambda: "9999-01-01T00:00:00")
    assert TestClient(pkg_app).post("/agent/v1/pair", json={"pairing_code": code, **PAIR}).status_code == 400


def test_language_is_validated_with_spanish_as_default(admin, sid):
    for asked, used in (("ca", "ca"), ("xx", "es"), ("../x", "es"), ("EN", "es")):
        z = _get(admin, sid, language=asked)[1]
        assert tomllib.loads(z.read("agent.toml").decode())["ui"]["language"] == used
    assert _get(admin, sid)[1].read("LEEME.txt").decode("utf-8-sig") == leeme("es", 15)


def test_not_built_unknown_server_and_status(admin, sid, agent_dir):
    assert admin.post("/api/v1/admin/servers/00000000-0000-0000-0000-000000000000/agent-package").status_code == 404
    (agent_dir / "fox3-agent.exe").unlink()
    r = admin.post(f"/api/v1/admin/servers/{sid}/agent-package")
    assert r.status_code == 503 and r.json()["error"]["code"] == "agent_not_built"
    assert admin.get("/api/v1/admin/agent-package").json() == {"available": False, "version": None, "size_bytes": None, "reason": "not_built"}


def test_admin_only_and_csrf(pkg_app, sid, admin):
    url = f"/api/v1/admin/servers/{sid}/agent-package"
    anon = TestClient(pkg_app, base_url="https://testserver")
    assert anon.post(url).status_code == 401 and anon.get("/api/v1/admin/agent-package").status_code == 401
    user = TestClient(pkg_app, base_url="https://testserver", follow_redirects=False)
    user.get("/api/v1/auth/demo")
    user.headers["X-CSRF-Token"] = user.get("/api/v1/me").json()["csrf_token"]
    assert user.post(url).status_code == 403 and user.get("/api/v1/admin/agent-package").status_code == 403
    del admin.headers["X-CSRF-Token"]
    assert admin.post(url).status_code == 403


def test_rate_limit_per_admin(admin, sid):
    for _ in range(10):
        _get(admin, sid)
    assert admin.post(f"/api/v1/admin/servers/{sid}/agent-package").status_code == 429


@pytest.mark.parametrize("name", ["../../x", 'a"b', "line\nbreak\r\nX: y", "Escuadrón ñandú 日本", "   ", "..", "x" * 80])
def test_hostile_server_names_give_safe_file_names(pkg_app, admin, name):
    with pkg_app.state.ctx.tx() as cn:
        sid = servers.create(cn, name, "foothold")["server_id"]
    disposition = _get(admin, sid)[0].headers["content-disposition"]
    assert re.fullmatch(r'attachment; filename="FOX3-Agent-[A-Za-z0-9_-]{1,40}\.zip"', disposition), disposition
    assert agent_package.slug(name) == agent_package.slug(name).strip("-_")


def test_texts_have_the_same_shape_in_every_language():
    assert set(TEXTS) == set(LANGUAGES)
    steps = set()
    for lang in LANGUAGES:
        text = leeme(lang, 15)
        assert not re.search(r"[{}]", text) and "15" in text and "\r\n" in text and "\n" not in text.replace("\r\n", "")
        for must in ("INSTALAR.cmd", "pairing-code.txt", "fox3-agent.exe uninstall", "SmartScreen"):
            assert must in text, (lang, must)
        steps.add(tuple(re.findall(r"^(\d)\. ", text, re.M)))
    assert steps == {("1", "2", "3", "4")}


def test_agent_dir_setting_is_strict_and_written_by_init():
    base = {"server": {"public_base_url": "https://fox3.example.org"}, "database": {"url": "sqlite://"}}
    assert from_mapping({**base, "paths": {"agent_dir": "C:/FOX3/agent"}})[0].agent_dir.name == "agent"
    for bad in ("", "  ", 5, ["x"]):
        with pytest.raises(SettingsError, match="agent_dir"):
            from_mapping({**base, "paths": {"agent_dir": bad}})
    with pytest.raises(SettingsError, match="unknown key"):
        from_mapping({**base, "paths": {"agent_dirr": "x"}})
    text = central_toml("fox3.example.org", 8000, [], "", agent_dir="C:\\ProgramData\\FOX3\\agent")
    assert tomllib.loads(text)["paths"]["agent_dir"] == "C:\\ProgramData\\FOX3\\agent"
    assert "[paths]" not in central_toml("fox3.example.org", 8000, [], "")
    with pytest.raises(ValueError):
        central_toml("fox3.example.org", 8000, [], "", agent_dir="x\ny")
