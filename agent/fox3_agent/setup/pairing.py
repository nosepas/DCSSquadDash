"""Pairing and connectivity check with friendly, specific errors. The code and the key are never printed."""
from __future__ import annotations

import os
import platform
from collections.abc import Callable

import httpx

from .. import __version__
from ..client import CentralClient
from ..config import AgentConfig
from ..credentials import Credentials, CredentialStore
from .bundle import SetupError

ClientFactory = Callable[[AgentConfig, str | None], CentralClient]


def default_client(cfg: AgentConfig, api_key: str | None = None) -> CentralClient:
    return CentralClient(cfg.central.url, api_key, verify=cfg.central.ca_file or cfg.central.verify_tls)


def computer_name() -> str:
    return (os.environ.get("COMPUTERNAME") or platform.node() or "fox3-agent")[:64]


def is_paired(cfg: AgentConfig) -> bool:
    try:
        return CredentialStore(cfg.state_dir, cfg.central.api_key_env).load() is not None
    except (OSError, ValueError):
        return False


def pair(cfg: AgentConfig, code: str, factory: ClientFactory = default_client) -> None:
    client = factory(cfg, None)
    try:
        r = client.pair(code, computer_name(), __version__)
        creds = Credentials(r["agent_id"], r["api_key"], r["server_id"])
    except httpx.HTTPStatusError as e:
        if e.response.status_code in (400, 401, 403, 404, 409, 410, 422):
            raise SetupError("pair_rejected") from None
        raise SetupError("pair_error", detail=f"HTTP {e.response.status_code}") from None
    except httpx.TransportError:
        raise SetupError("pair_unreachable", url=cfg.central.url) from None
    except (KeyError, ValueError, TypeError):
        raise SetupError("pair_error", detail="unexpected answer") from None
    finally:
        client.close()
    CredentialStore(cfg.state_dir, cfg.central.api_key_env).save(creds)


def check_connection(cfg: AgentConfig, factory: ClientFactory = default_client) -> bool:
    creds = CredentialStore(cfg.state_dir, cfg.central.api_key_env).load()
    if creds is None:
        return False
    client = factory(cfg, creds.api_key)
    try:
        client.get_config()
        return True
    except (httpx.HTTPError, ValueError):
        return False
    finally:
        client.close()
