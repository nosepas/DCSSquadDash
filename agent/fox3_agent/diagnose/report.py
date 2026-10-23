"""Report builder: titled sections, each produced best-effort (a failing section prints its reason, the rest continues)."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from .redact import local_user_names, redact_text, safe_error


@dataclass
class Section:
    title: str
    lines: list[str] = field(default_factory=list)
    unexpected: list[str] = field(default_factory=list)

    def line(self, text: str = "") -> None:
        self.lines.append(text)

    def kv(self, key: str, value: object) -> None:
        self.lines.append(f"  {key}: {value}")

    def flag(self, text: str) -> None:
        """Something that looked unexpected: shown in the section and again in the final list."""
        self.unexpected.append(f"{self.title}: {text}")
        self.lines.append(f"  ! {text}")


class Report:
    def __init__(self) -> None:
        self.sections: list[Section] = []

    def run(self, title: str, build: Callable[[Section], None]) -> None:
        sec = Section(title)
        try:
            build(sec)
        except Exception as exc:  # noqa: BLE001 - section boundary: one broken probe must not stop the report
            sec.flag(f"section failed: {safe_error(exc)}")
        self.sections.append(sec)

    def render(self, footer: list[str]) -> str:
        out: list[str] = ["FOX3 agent diagnose report", "=" * 26]
        for sec in self.sections:
            out += ["", f"## {sec.title}", *sec.lines]
        flagged = [u for s in self.sections for u in s.unexpected]
        out += ["", "## Unexpected", *(f"- {u}" for u in flagged or ["nothing looked unexpected"]), "", *footer]
        return redact_text("\n".join(out), local_user_names()) + "\n"
