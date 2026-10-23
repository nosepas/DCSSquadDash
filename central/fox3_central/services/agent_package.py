"""Personalised agent download: the built fox3-agent.exe plus this server's settings and a FRESH one-time pairing code.

The ZIP is assembled in memory; the pairing code is never written to the central's disk.
"""
from __future__ import annotations

import io
import logging
import re
import unicodedata
import zipfile
from pathlib import Path

from fox3_agent import scaffold as agent_scaffold

from ..context import Context
from ..core.errors import AppError, NotFound, RateLimited
from ..repositories import servers
from . import agents as agent_service
from .agent_package_texts import DEFAULT_LANGUAGE, LANGUAGES, leeme

EXE_NAME = "fox3-agent.exe"
WINDOWLESS_NAME = "fox3-agentw.exe"
VERSION_NAME = "fox3-agent.version"
PAIRING_MINUTES = 15
DOWNLOADS_PER_WINDOW, WINDOW_S = 10, 600
INSTALL_CMD = '@echo off\r\n"%~dp0fox3-agent.exe" setup --here "%~dp0"\r\necho.\r\npause\r\n'
audit = logging.getLogger("fox3.audit")


class AgentNotBuilt(AppError):
    status, code = 503, "agent_not_built"


def package_status(ctx: Context) -> dict:
    exe = _exe(ctx)
    if not exe:
        return {"available": False, "version": None, "size_bytes": None, "reason": "not_built"}
    return {"available": True, "version": _version(exe.parent), "size_bytes": exe.stat().st_size, "reason": None}


def slug(name: str) -> str:
    """Safe file-name fragment: ASCII letters, digits, dot, dash, underscore; never empty."""
    ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9_-]+", "-", ascii_name).strip("-_")[:40].strip("-_") or "server"


def agent_toml(central_url: str, language: str) -> str:
    """The agent's own validated generator, minus the state_dir line (the agent then keeps its state next to the file)."""
    text = agent_scaffold.render_agent_toml(central_url, Path("state"))
    text = re.sub(r"\n\[paths\]\nstate_dir = .*\n", "\n", text)
    return f'{text.rstrip()}\n\n[ui]\nlanguage = "{language}"\n'


def build_package(ctx: Context, server_id: str, language: str, admin_id: int) -> tuple[bytes, str]:
    """Returns (zip bytes, download file name). Creates a new pairing code (and a new pending agent) per call."""
    with ctx.engine.connect() as cn:
        server = servers.get(cn, server_id)
    if not server:
        raise NotFound("server not found")
    exe = _exe(ctx)
    if not exe:
        raise AgentNotBuilt("the agent has not been built on this central yet (see docs/ADMINISTRADOR-AGENT.md)")
    if not ctx.limiter.allow(f"agent-package:{admin_id}", DOWNLOADS_PER_WINDOW, WINDOW_S):
        raise RateLimited("too many agent downloads; try again in a few minutes")
    language = language if language in LANGUAGES else DEFAULT_LANGUAGE
    pairing = agent_service.create_pairing_code(ctx, server_id, PAIRING_MINUTES)
    audit.info("agent package downloaded: user=%s server=%s agent=%s language=%s", admin_id, server_id, pairing["agent_id"], language)
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.write(exe, EXE_NAME)
        windowless = exe.with_name(WINDOWLESS_NAME)
        if windowless.is_file():  # the Scheduled Task runs this one (no black console window at logon)
            z.write(windowless, WINDOWLESS_NAME)
        z.writestr("agent.toml", agent_toml(ctx.settings.public_base_url, language))
        z.writestr("pairing-code.txt", pairing["pairing_code"] + "\r\n")
        z.writestr("INSTALAR.cmd", INSTALL_CMD)
        z.writestr("LEEME.txt", leeme(language, PAIRING_MINUTES).encode("utf-8-sig"))
    return buf.getvalue(), f"FOX3-Agent-{slug(server['name'])}.zip"


def _exe(ctx: Context) -> Path | None:
    base = ctx.settings.agent_dir
    exe = base / EXE_NAME if base else None
    return exe if exe and exe.is_file() else None


def _version(folder: Path) -> str | None:
    try:
        return (folder / VERSION_NAME).read_text("utf-8").strip() or None
    except OSError:
        return None
