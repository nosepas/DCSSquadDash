import argparse

from conftest import FakeClient, make_args
from fox3_agent.setup.installer import run_setup
from fox3_agent.setup.lifecycle import run_status, run_uninstall


def install(bundle, tmp_path):
    assert run_setup(make_args(bundle, tmp_path), factory=lambda c, k: FakeClient(), prompt=lambda _p: "") == 0


def test_uninstall_only_touches_our_paths(bundle, tmp_path, calls):
    install(bundle, tmp_path)
    other = tmp_path / "other"
    other.mkdir()
    calls.clear()
    assert run_uninstall(argparse.Namespace(install_dir=str(tmp_path / "inst"), keep_data=False, language="en")) == 0
    assert not (tmp_path / "inst").exists() and other.exists() and bundle.exists()
    assert [c[1] for c in calls if c[0] == "schtasks"] == ["/End", "/Delete"]
    assert all(c[0] in ("schtasks", "powershell") for c in calls)


def test_uninstall_keep_data(bundle, tmp_path, calls):
    install(bundle, tmp_path)
    assert run_uninstall(argparse.Namespace(install_dir=str(tmp_path / "inst"), keep_data=True, language="en")) == 0
    assert (tmp_path / "inst" / "agent.toml").exists() and not (tmp_path / "inst" / "fox3-agent.exe").exists()


def test_status_plain_language(bundle, tmp_path, calls, capsys):
    install(bundle, tmp_path)
    capsys.readouterr()
    assert run_status(argparse.Namespace(install_dir=str(tmp_path / "inst"), language="en")) == 0
    out = capsys.readouterr().out
    assert "Installed: yes" in out and "Automatic start: Ready" in out and "Paired with the central server: yes" in out
