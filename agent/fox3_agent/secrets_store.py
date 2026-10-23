"""Small local secrets (e.g. DCSServerBot API key), encrypted with Windows DPAPI for the CURRENT USER in `<state>/secrets.bin`."""
from __future__ import annotations

import json
import logging
import os
import re
from collections.abc import MutableMapping
from pathlib import Path

from . import dpapi

log = logging.getLogger("fox3.agent.secrets")
FILE_NAME = "secrets.bin"
NAME_RE = re.compile(r"[a-z0-9_]{1,64}")


class SecretError(ValueError):
    pass


class SecretStore:
    def __init__(self, state_dir: Path):
        self._file = state_dir / FILE_NAME

    def _read(self) -> dict[str, str]:
        if not self._file.exists():
            return {}
        raw = self._file.read_bytes()
        tag, body = raw[:6], raw[6:]
        if tag == b"DPAPI1":
            body = dpapi.unprotect(body)
        elif tag != b"PLAIN1":
            raise SecretError("unrecognised secrets file")
        return json.loads(body)

    def _write(self, data: dict[str, str]) -> None:
        raw = json.dumps(data).encode()
        if dpapi.AVAILABLE:
            raw = b"DPAPI1" + dpapi.protect(raw, machine_scope=False)
        else:
            log.warning("DPAPI unavailable: secrets are stored unencrypted")
            raw = b"PLAIN1" + raw
        self._file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self._file.with_suffix(".tmp")
        tmp.write_bytes(raw)
        if os.name != "nt":
            tmp.chmod(0o600)
        tmp.replace(self._file)

    @staticmethod
    def _check(name: str) -> str:
        if not NAME_RE.fullmatch(name):
            raise SecretError("secret names use lowercase letters, digits and _ (max 64)")
        return name

    def get(self, name: str) -> str | None:
        return self._read().get(self._check(name))

    def set(self, name: str, value: str) -> None:
        if not value:
            raise SecretError("empty secret")
        data = self._read()
        data[self._check(name)] = value
        self._write(data)

    def delete(self, name: str) -> bool:
        data = self._read()
        if self._check(name) not in data:
            return False
        del data[name]
        self._write(data)
        return True

    def names(self) -> list[str]:
        return sorted(self._read())

    def export_to_environ(self, environ: MutableMapping[str, str] | None = None) -> list[str]:
        """Makes each stored secret visible as the environment variable NAME.upper() (e.g. `fox3_dcsbot_api_key` -> FOX3_DCSBOT_API_KEY).

        A variable that is already set wins. Returns the variable names that were added. Never raises: a broken secrets file only means
        the sources report their own "key not available" warning.
        """
        env = os.environ if environ is None else environ
        added: list[str] = []
        try:
            data = self._read()
        except (SecretError, ValueError, OSError) as exc:
            log.warning("could not read the stored secrets: %s", exc)
            return added
        for name, value in data.items():
            if not env.get(name.upper()):
                env[name.upper()] = value
                added.append(name.upper())
        return added
