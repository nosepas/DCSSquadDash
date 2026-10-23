import subprocess
from types import SimpleNamespace

import httpx
import pytest

from fox3_agent.scaffold import render_agent_toml
from fox3_agent.setup import bundle as bd
from fox3_agent.setup import scheduler

SECRET_CODE = "ABCD-1234-SECRETCODE"
SECRET_KEY = "agent1.super-secret-key"


class FakeClient:
    def __init__(self, pair_error: Exception | None = None, config_error: Exception | None = None):
        self.pair_error, self.config_error, self.pairs = pair_error, config_error, 0

    def pair(self, code, name, version):
        self.pairs += 1
        if self.pair_error:
            raise self.pair_error
        return {"agent_id": "agent1", "api_key": SECRET_KEY, "server_id": "s1"}

    def get_config(self):
        if self.config_error:
            raise self.config_error
        return {}

    def close(self):
        pass


def http_error(status: int) -> httpx.HTTPStatusError:
    req = httpx.Request("POST", "https://x/agent/v1/pair")
    return httpx.HTTPStatusError("boom", request=req, response=httpx.Response(status, request=req))


@pytest.fixture(autouse=True)
def windows_user(monkeypatch):
    """The installer builds the task for the current Windows user; CI on Linux has no USERNAME."""
    monkeypatch.setenv("USERNAME", "tester")
    monkeypatch.setenv("USERDOMAIN", "PC")


@pytest.fixture
def calls(monkeypatch):
    log: list[list[str]] = []

    def fake_run(args, **kw):
        log.append(list(args))
        return subprocess.CompletedProcess(args, 0, stdout='"h","\\FOX3 Agent","N/A","Ready","x","y","0"\n', stderr="")

    monkeypatch.setattr(scheduler.subprocess, "run", fake_run)
    return log


@pytest.fixture
def bundle(tmp_path, monkeypatch):
    b = tmp_path / "bundle"
    b.mkdir()
    (b / "agent.toml").write_text(render_agent_toml("https://central.example", b / "state"), "utf-8")
    (b / "pairing-code.txt").write_text(SECRET_CODE + "\n", "utf-8")
    (b / "fox3-agent.exe").write_bytes(b"MZ-fake")
    monkeypatch.setattr(bd, "running_exe", lambda: (b / "fox3-agent.exe").resolve())
    return b


def make_args(bundle, tmp_path, **kw):
    base = dict(here=str(bundle), install_dir=str(tmp_path / "inst"), no_start=False, dry_run=False, language="en")
    return SimpleNamespace(**{**base, **kw})
