"""Exceptions of the DTC library."""
from __future__ import annotations


class DtcError(Exception):
    """Raised for unreadable files and invalid models; `errors` holds human-readable messages."""

    def __init__(self, errors: list[str]) -> None:
        super().__init__("; ".join(errors))
        self.errors = errors
