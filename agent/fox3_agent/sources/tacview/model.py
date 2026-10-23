"""Result types of the ACMI indexer."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(slots=True)
class Appearance:
    pilot: str
    object_id: str
    aircraft: str | None
    coalition: str
    group: str | None
    first_offset_s: float
    last_offset_s: float


@dataclass
class TacviewIndex:
    reference_time: str | None = None       # normalized UTC "...Z"
    title: str | None = None
    data_source: str | None = None
    duration_s: float | None = None         # largest time mark seen
    appearances: list[Appearance] = field(default_factory=list)
    complete: bool = True                   # False for a truncated / still-being-written file
    malformed_lines: int = 0
    oversized_lines: int = 0
    dropped_objects: int = 0                # pilot objects ignored because max_objects was reached
