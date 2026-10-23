import httpx
import pytest

from conftest import SECRET_CODE, SECRET_KEY, FakeClient, http_error, make_args
from fox3_agent.config import load_config
from fox3_agent.credentials import CredentialStore
from fox3_agent.setup import bundle as bd
from fox3_agent.setup.installer import run_setup


def setup(bundle, tmp_path, client, prompt=lambda _p: "", **kw):
    return run_setup(make_args(bundle, tmp_path, **kw), factory=lambda cfg, key: client, prompt=prompt)


def test_full_setup_pairs_installs_and_registers(bundle, tmp_path, calls, capsys):
    c = FakeClient()
    assert setup(bundle, tmp_path, c) == 0
    inst = tmp_path / "inst"
    assert (inst / "fox3-agent.exe").read_bytes() == b"MZ-fake"
    cfg = load_config(inst / "agent.toml")
    assert cfg.state_dir == inst / "state" and cfg.central.url == "https://central.example"
    assert CredentialStore(cfg.state_dir, "X_UNSET_ENV").load().api_key == SECRET_KEY
    assert not (bundle / "pairing-code.txt").exists()
    assert [x[1] for x in calls if x[0] == "schtasks"] == ["/Create", "/Query", "/Run"]
    out = capsys.readouterr().out
    assert SECRET_CODE not in out and SECRET_KEY not in out and "ONLINE" in out and "Windows protected your PC" in out


def test_second_run_does_not_repair(bundle, tmp_path, calls):
    c = FakeClient()
    assert setup(bundle, tmp_path, c) == 0
    (bundle / "pairing-code.txt").write_text("NEWCODE1")
    assert setup(bundle, tmp_path, c) == 0
    assert c.pairs == 1


@pytest.mark.parametrize(("err", "text"), [(http_error(410), "expired, already used or invalid"),
                                          (http_error(401), "expired, already used or invalid"),
                                          (httpx.ConnectError("no"), "Cannot reach")])
def test_pair_failure_keeps_code_and_is_friendly(bundle, tmp_path, calls, capsys, err, text):
    assert setup(bundle, tmp_path, FakeClient(pair_error=err)) == 1
    out = capsys.readouterr().out
    assert text in out and SECRET_CODE not in out
    assert (bundle / "pairing-code.txt").exists() and calls == []


def test_server_error_message(bundle, tmp_path, calls, capsys):
    assert setup(bundle, tmp_path, FakeClient(pair_error=http_error(500))) == 1
    assert "HTTP 500" in capsys.readouterr().out


def test_connectivity_failure_is_reported_not_fatal(bundle, tmp_path, calls, capsys):
    assert setup(bundle, tmp_path, FakeClient(config_error=httpx.ConnectError("x"))) == 0
    assert "FAILED" in capsys.readouterr().out


def test_prompt_used_when_no_code_file(bundle, tmp_path, calls):
    (bundle / "pairing-code.txt").unlink()
    asked = []
    assert setup(bundle, tmp_path, FakeClient(), prompt=lambda p: asked.append(p) or "TYPED-123") == 0
    assert len(asked) == 1


@pytest.mark.parametrize("bad", ["has space", "a\nb", "x" * 33, "ab;rm", "", "ñandú"])
def test_hostile_codes_rejected_before_network(bundle, tmp_path, calls, bad):
    (bundle / "pairing-code.txt").write_text(bad, "utf-8")
    c = FakeClient()
    assert setup(bundle, tmp_path, c, prompt=lambda _p: "bad code!") == 1 and c.pairs == 0


def test_missing_or_bad_toml(bundle, tmp_path, calls, capsys):
    (bundle / "agent.toml").write_text("[central]\nurl = 'ftp://x'\n")
    assert setup(bundle, tmp_path, FakeClient()) == 1
    (bundle / "agent.toml").unlink()
    assert setup(bundle, tmp_path, FakeClient()) == 1
    assert "agent.toml was not found" in capsys.readouterr().out


def test_dry_run_changes_nothing(bundle, tmp_path, calls, capsys):
    c = FakeClient()
    assert setup(bundle, tmp_path, c, dry_run=True) == 0
    assert not (tmp_path / "inst").exists() and calls == [] and c.pairs == 0
    assert (bundle / "pairing-code.txt").exists() and "dry-run" in capsys.readouterr().out


def test_no_start_skips_run(bundle, tmp_path, calls):
    assert setup(bundle, tmp_path, FakeClient(), no_start=True) == 0
    assert "/Run" not in [x[1] for x in calls]


def test_dev_mode_skips_copy_and_task(bundle, tmp_path, calls, monkeypatch, capsys):
    monkeypatch.setattr(bd, "running_exe", lambda: None)
    assert setup(bundle, tmp_path, FakeClient()) == 0
    assert calls == [] and "Development mode" in capsys.readouterr().out


def test_language_from_toml_and_default(bundle):
    p = bundle / "agent.toml"
    assert bd.ui_language(p) == "es"
    p.write_text(p.read_text() + '\n[ui]\nlanguage = "ca"\n')
    assert bd.ui_language(p) == "ca" and bd.ui_language(p, "en") == "en"
    p.write_text(p.read_text().replace('"ca"', '"xx"'))
    assert bd.ui_language(p) == "es"


def test_default_install_dir_must_be_under_profile(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "elsewhere"))
    monkeypatch.setattr(bd.Path, "home", classmethod(lambda cls: tmp_path / "home"))
    with pytest.raises(bd.SetupError):
        bd.resolve_install_dir(None)
    assert bd.resolve_install_dir(str(tmp_path / "x")) == (tmp_path / "x").resolve()
