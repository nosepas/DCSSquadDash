"""Errors of the Tacview source. All derive from AcmiError so callers can catch one type."""
from __future__ import annotations


class AcmiError(Exception):
    """The file cannot be indexed (reported as TACVIEW_FILE_FAILED)."""


class AcmiUnsupportedError(AcmiError):
    """Container not supported, e.g. 7z (reported as TACVIEW_FORMAT_UNSUPPORTED)."""


class AcmiLimitError(AcmiError):
    """A safety limit (zip bomb guard) was exceeded."""


class AcmiFormatError(AcmiError):
    """The content is not a text ACMI recording."""


class AcmiCancelledError(AcmiError):
    """Indexing was cancelled (agent shutting down or folder changed)."""
