"""Credential storage: no plaintext on Windows, selectable DPAPI scope, backwards-compatible reading."""
from __future__ import annotations

import json
import sys
from dataclasses import asdict

import pytest

from fox3_agent import credentials, dpapi
from fox3_agent.credentials import SCOPE_MACHINE, SCOPE_USER, TAG_DPAPI, CredentialError, Credentials, CredentialStore

CREDS = Credentials("aid", "aid.secret", "sid")
needs_dpapi = pytest.mark.skipif(sys.platform != "win32", reason="DPAPI is Windows only")


def test_windows_without_dpapi_refuses_plaintext(tmp_path, monkeypatch):
    monkeypatch.setattr(dpapi, "AVAILABLE", False)
    monkeypatch.setattr(credentials.os, "name", "nt")
    with pytest.raises(CredentialError, match="plain text"):
        CredentialStore(tmp_path).save(CREDS)
    assert not (tmp_path / "credentials.bin").exists()


@pytest.mark.skipif(sys.platform == "win32", reason="plaintext fallback is for non-Windows development only")
def test_non_windows_keeps_the_plain_fallback(tmp_path):
    store = CredentialStore(tmp_path)
    store.save(CREDS)
    assert store.load() == CREDS


def fake_dpapi(monkeypatch, calls: list[bool]):
    monkeypatch.setattr(dpapi, "AVAILABLE", True)
    monkeypatch.setattr(dpapi, "protect", lambda data, machine_scope=False: calls.append(machine_scope) or b"ENC" + data[::-1])
    monkeypatch.setattr(dpapi, "unprotect", lambda blob: blob[3:][::-1])


def test_default_is_user_scope_and_marker_is_stored(tmp_path, monkeypatch):
    calls: list[bool] = []
    fake_dpapi(monkeypatch, calls)
    CredentialStore(tmp_path).save(CREDS)
    assert calls == [False]
    assert (tmp_path / "credentials.bin").read_bytes().startswith(TAG_DPAPI + SCOPE_USER)
    assert CredentialStore(tmp_path).load() == CREDS


def test_machine_scope_is_selectable(tmp_path, monkeypatch):
    calls: list[bool] = []
    fake_dpapi(monkeypatch, calls)
    CredentialStore(tmp_path, machine_scope=True).save(CREDS)
    assert calls == [True]
    assert (tmp_path / "credentials.bin").read_bytes().startswith(TAG_DPAPI + SCOPE_MACHINE)
    assert CredentialStore(tmp_path).load() == CREDS  # reading does not depend on the configured scope


def test_old_dpapi1_files_still_load(tmp_path, monkeypatch):
    fake_dpapi(monkeypatch, [])
    (tmp_path / "credentials.bin").write_bytes(b"DPAPI1" + b"ENC" + json.dumps(asdict(CREDS)).encode()[::-1])
    assert CredentialStore(tmp_path).load() == CREDS


@needs_dpapi
@pytest.mark.parametrize("machine", [False, True])
def test_real_dpapi_round_trip_both_scopes(tmp_path, machine):
    store = CredentialStore(tmp_path, machine_scope=machine)
    store.save(CREDS)
    assert store.load() == CREDS and b"secret" not in (tmp_path / "credentials.bin").read_bytes()
