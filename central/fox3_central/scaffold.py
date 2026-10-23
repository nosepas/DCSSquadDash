"""Generates the production configuration files (central.toml and the Caddyfile) from the installer's answers."""
from __future__ import annotations

import json
import re
from pathlib import Path

HOSTNAME = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9.-]*[A-Za-z0-9])?\.[A-Za-z]{2,}$")


def _q(value: str) -> str:
    return json.dumps(value)  # a JSON string is a valid TOML basic string


def central_toml(hostname: str, port: int, admin_ids: list[str], discord_client_id: str, agent_dir: str = "") -> str:
    if not HOSTNAME.match(hostname):
        raise ValueError(f"not a valid DNS name: {hostname!r}")
    if not 1 <= port <= 65535:
        raise ValueError("port out of range")
    if not all(i.isdigit() for i in admin_ids) or (discord_client_id and not discord_client_id.isdigit()):
        raise ValueError("Discord ids are numeric")
    if any(c in agent_dir for c in "\r\n"):
        raise ValueError("agent_dir must be a single-line path")
    ids = ", ".join(_q(i) for i in admin_ids)
    return (f'[server]\nbind = "127.0.0.1"\nport = {port}\npublic_base_url = {_q("https://" + hostname)}\n\n'
            f'[database]\nurl_env = "FOX3_DATABASE_URL"\n\n'
            f'[discord]\nclient_id = {_q(discord_client_id)}\nclient_secret_env = "FOX3_DISCORD_CLIENT_SECRET"\nadmin_ids = [{ids}]\n'
            + (f'\n[paths]\nagent_dir = {_q(agent_dir)}\n' if agent_dir else ''))


def caddyfile(hostname: str, port: int) -> str:
    if not HOSTNAME.match(hostname):
        raise ValueError(f"not a valid DNS name: {hostname!r}")
    proxy = f"reverse_proxy 127.0.0.1:{port} {{\n            flush_interval -1\n        }}"
    return (f"{hostname} {{\n    encode zstd gzip\n"
            f"    # recordings streamed by an agent can be large: no body limit on that one route\n"
            f"    handle /agent/v1/file-requests/*/content {{\n        {proxy}\n    }}\n"
            f"    handle {{\n        request_body {{\n            max_size 10MB\n        }}\n        {proxy}\n    }}\n}}\n")


def write_missing(out: Path, files: dict[str, str]) -> list[str]:
    """Write each file unless it already exists (an admin's edits are never overwritten). Returns the names written."""
    out.mkdir(parents=True, exist_ok=True)
    written = []
    for name, text in files.items():
        target = out / name
        if not target.exists():
            target.write_text(text, "utf-8")
            written.append(name)
    return written
