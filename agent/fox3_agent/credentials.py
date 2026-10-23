"""Storage of the agent API key: environment variable first, else a DPAPI-protected file in the state dir."""
from __future__ import annotations

import json
import logging
import os
from dataclasses import asdict, dataclass
from pathlib import Path

from . import dpapi

log = logging.getLogger("fox3.agent.credentials")
FILE_NAME = "credentials.bin"
TAG_LEGACY, TAG_DPAPI, TAG_PLAIN = b"DPAPI1", b"DPAPI2", b"PLAIN1"  # DPAPI1: machine scope; DPAPI2: 1 scope byte follows
SCOPE_USER, SCOPE_MACHINE = b"U", b"M"


class CredentialError(RuntimeError):
    """The credentials cannot be stored safely."""


@dataclass(frozen=True)
class Credentials:
    agent_id: str
    api_key: str
    server_id: str

    def __repr__(self) -> str:  # never print the key
        return f"Credentials(agent_id={self.agent_id!r}, server_id={self.server_id!r}, api_key=***)"


class CredentialStore:
    def __init__(self, state_dir: Path, env_var: str = "FOX3_AGENT_KEY", machine_scope: bool = False):
        """User scope (default): only the Windows account that paired the agent can decrypt. Machine scope: any account on this PC."""
        self._file, self._env, self._machine = state_dir / FILE_NAME, env_var, machine_scope

    def save(self, creds: Credentials) -> None:
        self._file.parent.mkdir(parents=True, exist_ok=True)
        raw = json.dumps(asdict(creds)).encode()
        if dpapi.AVAILABLE:
            raw = TAG_DPAPI + (SCOPE_MACHINE if self._machine else SCOPE_USER) + dpapi.protect(raw, self._machine)
        elif os.name == "nt":
            raise CredentialError("Windows DPAPI is unavailable: refusing to store the agent key in plain text")
        else:
            log.warning("DPAPI unavailable: credentials are stored unencrypted, protect the folder %s", self._file.parent)
            raw = TAG_PLAIN + raw
        tmp = self._file.with_suffix(".tmp")
        tmp.write_bytes(raw)
        if os.name != "nt":
            tmp.chmod(0o600)
        tmp.replace(self._file)

    def load(self) -> Credentials | None:
        if (key := os.environ.get(self._env)):
            agent_id, _, _ = key.partition(".")
            return Credentials(agent_id=agent_id, api_key=key, server_id="")
        if not self._file.exists():
            return None
        raw = self._file.read_bytes()
        tag, body = raw[:6], raw[6:]
        if tag == TAG_DPAPI and body[:1] in (SCOPE_USER, SCOPE_MACHINE):
            body = dpapi.unprotect(body[1:])  # DPAPI records the scope inside the blob; the marker is informational
        elif tag == TAG_LEGACY:
            body = dpapi.unprotect(body)
        elif tag != TAG_PLAIN:
            raise ValueError("unrecognised credentials file")
        return Credentials(**json.loads(body))
