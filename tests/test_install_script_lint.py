"""Static checks of the Windows installer scripts (they cannot be run in CI: they need admin, nssm and caddy)."""
import shutil
import subprocess
from pathlib import Path

import pytest

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
FILES = [SCRIPTS / "install-central.ps1", *sorted((SCRIPTS / "lib").glob("*.ps1"))]
PWSH = shutil.which("powershell") or shutil.which("pwsh")
pytestmark = pytest.mark.skipif(PWSH is None, reason="PowerShell not available")


def _ps(command: str) -> subprocess.CompletedProcess:
    return subprocess.run([PWSH, "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", command],
                          capture_output=True, text=True, timeout=120)


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_parses_without_errors(path):
    r = _ps(f"$e=$null; [void][System.Management.Automation.Language.Parser]::ParseFile('{path}',[ref]$null,[ref]$e); "
            "$e | ForEach-Object { $_.Message }; exit $e.Count")
    assert r.returncode == 0, r.stdout


@pytest.mark.parametrize("path", FILES, ids=lambda p: p.name)
def test_no_control_characters(path):
    """A '\\f' inside a Windows path in a non-raw string once produced a form feed; keep the files clean."""
    bad = [c for c in path.read_text("utf-8") if ord(c) < 32 and c not in "\r\n\t"]
    assert not bad


def test_dry_run_install_shows_hardening_steps_and_no_secrets():
    r = _ps(f"& '{SCRIPTS / 'install-central.ps1'}' -Hostname fox3.example.org -DryRun")
    out = r.stdout
    assert r.returncode == 0, r.stderr
    for needle in ("obj= \"NT SERVICE\\FOX3Central\"", "obj= \"NT SERVICE\\FOX3Caddy\"", "/inheritance:r",
                   "registry ACL", "firewall:", "AppEnvironmentExtra (values hidden)"):
        assert needle in out, needle
    assert "FOX3_DATABASE_URL=" not in out


def test_dry_run_uninstall_keeps_data_unless_purge():
    keep = _ps(f"& '{SCRIPTS / 'install-central.ps1'}' -Uninstall -DryRun").stdout
    purge = _ps(f"& '{SCRIPTS / 'install-central.ps1'}' -Uninstall -PurgeData -DryRun").stdout
    assert "data kept" in keep and "DELETE" not in keep
    assert "DELETE" in purge
