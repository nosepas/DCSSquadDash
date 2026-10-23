"""Common interface of every data source the agent can read (Foothold file, DCSServerBot, Tacview, gRPC...).

A source is polled by the agent runtime. It keeps its own incremental state (file mtime, DB watermark...) and returns
only what changed, as messages whose payloads follow contracts/schemas/<kind>.json.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class Message:
    kind: str       # one of fox3_agent.protocol.PATHS (server_info, foothold_state, players, events, ...)
    payload: dict   # validated by central against contracts/schemas/<kind>.json


@dataclass(frozen=True)
class Warning_:
    code: str       # stable id, e.g. FOOTHOLD_FILE_MISSING, DCSBOT_UNREACHABLE (goes into heartbeat.warnings)
    message: str


class Source(Protocol):
    name: str

    def poll(self) -> list[Message]:
        """Return the messages for what changed since the last poll ([] if nothing).

        Must not raise for expected conditions (file missing, service down, malformed data): report them via
        `warnings()` and return []. Unexpected programming errors may propagate.
        """

    def warnings(self) -> list[Warning_]:
        """Current problems of this source (empty when healthy). Re-evaluated on every poll."""
