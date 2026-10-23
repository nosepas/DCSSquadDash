"""The live set of data sources. Rebuilt in place when the admin changes the settings; never crashes on a bad configuration."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Protocol

from ..config import AgentConfig
from ..sources.base import Message, Source, Warning_
from ..sources.dcsbot import ConfigError, DcsBotConfig, DcsBotSource
from ..sources.foothold import FootholdSource
from ..sources.tacview import TacviewSource
from .settings import Effective, merge
from .state import AgentState

log = logging.getLogger("fox3.agent.sources")


class SourceProvider(Protocol):
    sources: list[Source]
    foothold: FootholdSource | None
    dcsbot: DcsBotSource | None
    mission_type: str

    def apply(self, remote: dict) -> None: ...
    def stop(self) -> None: ...


class StaticSources:
    """Fixed sources (tests, simple setups): settings pushed from central are ignored."""

    def __init__(self, sources: list[Source], foothold=None, dcsbot=None, mission_type: str = "foothold"):
        self.sources, self.foothold, self.dcsbot, self.mission_type = sources, foothold, dcsbot, mission_type

    def apply(self, remote: dict) -> None:
        pass

    def stop(self) -> None:
        pass


class ConfigProblem:
    """Stands in for a source whose configuration is invalid: it reports the problem instead of failing the agent."""

    def __init__(self, name: str, code: str, message: str):
        self.name, self._w = name, Warning_(code, message)

    def poll(self) -> list[Message]:
        return []

    def warnings(self) -> list[Warning_]:
        return [self._w]


class LiveSources:
    def __init__(self, local: AgentConfig, state: AgentState, state_dir: Path | None = None):
        self._local, self._state = local, state
        self._eff: Effective = merge(local, None)
        self.tacview = TacviewSource(lambda: (self._eff.tacview_dir, self._eff.tacview_enabled), state_dir or local.state_dir,
                                 cloud_files=local.tacview.cloud_files)
        self.foothold: FootholdSource | None = None
        self.dcsbot: DcsBotSource | None = None
        self._problems: dict[str, ConfigProblem] = {}
        self._build_foothold()
        self._build_dcsbot()

    @property
    def sources(self) -> list[Source]:
        live = [s for s in (self.foothold, self.dcsbot) if s is not None]
        return [*live, self.tacview, *self._problems.values()]

    def apply(self, remote: dict) -> None:
        new = merge(self._local, remote)
        old, self._eff = self._eff, new
        if (old.foothold_enabled, old.foothold_dir) != (new.foothold_enabled, new.foothold_dir):
            self._build_foothold()
        if (old.dcsbot, old.rest_url_refused) != (new.dcsbot, new.rest_url_refused):
            self._build_dcsbot()
        log.info("settings applied")

    def _build_foothold(self) -> None:
        e = self._eff
        self.foothold = FootholdSource(e.foothold_dir, stale_after_s=self._local.foothold.stale_after_s) \
            if e.foothold_enabled and e.foothold_dir else None
        self._problems.pop("foothold", None)
        if e.foothold_enabled and not e.foothold_dir:
            self._problems["foothold"] = ConfigProblem("foothold", "FOOTHOLD_FOLDER_NOT_SET", "No Foothold saves folder configured")

    def _build_dcsbot(self) -> None:
        keep = self.dcsbot.watermark if self.dcsbot else self._state.load().get("dcsbot_watermark")
        self.dcsbot, raw = None, self._eff.dcsbot
        self._problems.pop("dcsbot", None)
        self._problems.pop("dcsbot_rest", None)
        if self._eff.rest_url_refused:
            log.warning("refused the DCSServerBot REST URL sent by central (host not loopback nor in allowed_rest_hosts)")
            self._problems["dcsbot_rest"] = ConfigProblem(
                "dcsbot_rest", "DCSBOT_REST_URL_REFUSED",
                "The DCSServerBot REST URL set in the admin panel was ignored: its host is not local nor in allowed_rest_hosts")
        if not raw:
            return
        try:
            self.dcsbot = DcsBotSource(DcsBotConfig.from_mapping({"mission_type": self._eff.mission_type, **raw}), watermark=keep)
        except ConfigError as exc:
            log.warning("invalid DCSServerBot configuration: %s", exc)
            self._problems["dcsbot"] = ConfigProblem("dcsbot", "DCSBOT_CONFIG_INVALID", str(exc)[:200])

    @property
    def tacview_folder(self) -> Path | None:
        return self._eff.tacview_dir if self._eff.tacview_enabled else None

    @property
    def mission_type(self) -> str:
        return self._eff.mission_type

    def stop(self) -> None:
        self.tacview.stop()
