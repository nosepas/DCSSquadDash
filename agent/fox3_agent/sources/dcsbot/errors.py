"""Error types of the DCSServerBot source. None of their messages may ever contain secrets (API key, DB password)."""
from __future__ import annotations


class DcsBotError(Exception):
    """Base class of every expected failure of this source."""


class ConfigError(DcsBotError, ValueError):
    """Invalid [dcsbot] configuration."""


class RestForbiddenCall(DcsBotError):
    """A REST call outside the read-only allowlist was requested (programming error, never sent)."""


class RestUnreachable(DcsBotError):
    """The DCSServerBot REST service did not answer (connection refused, timeout, 5xx...)."""


class RestAuthError(DcsBotError):
    """The REST service rejected the API key (HTTP 401/403)."""


class RestProtocolError(DcsBotError):
    """The REST service answered something we cannot use (bad JSON, wrong shape, body too large)."""


class DbError(DcsBotError):
    """The DCSServerBot database could not be read."""
