"""Minimal `server_info` used when no source provides one (e.g. DCSServerBot REST disabled)."""
from __future__ import annotations

from .. import __version__


def minimal_server_info(mission_type: str, foothold: bool, dcsbot_rest: bool, dcsbot_db: bool) -> dict:
    return {
        "mission_type": mission_type, "agent_version": __version__,
        "capabilities": {"foothold": foothold, "tacview": False, "grpc": False, "dcsbot_rest": dcsbot_rest, "dcsbot_db": dcsbot_db},
    }
