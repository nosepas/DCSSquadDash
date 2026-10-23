"""Redaction helpers: everything the diagnose report prints goes through here, so it is safe to paste in a chat."""
from __future__ import annotations

import contextlib
import getpass
import re
from pathlib import Path

_USER_PATH = re.compile(r"(?i)([\\/](?:users|home)[\\/]+)(?!<user>)[^\\/\r\n\"'<>|*?:]+")
_URL_CREDS = re.compile(r"(?i)\b([a-z][a-z0-9+.-]*://)[^/\s@]+@")
_EMAIL = re.compile(r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+")
_UUID = re.compile(r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b")
_UCID = re.compile(r"\b[0-9a-fA-F]{32}\b")
_HEX_ID = re.compile(r"\b[0-9a-fA-F]{16,}\b")
_SECRET = re.compile(r"(?i)\b(bearer\s+|api[_-]?key\s*[=:]\s*|password\s*[=:]\s*|x-api-key\s*[=:]\s*)\S+")
MAX_ERROR = 160


def redact_text(text: str, extra_names: tuple[str, ...] = ()) -> str:
    """Remove user names in paths, credentials in URLs, e-mails, ucids and long hexadecimal identifiers."""
    text = _URL_CREDS.sub(r"\1<redacted>@", text)
    text = _SECRET.sub(r"\1<redacted>", text)
    text = _USER_PATH.sub(r"\1<user>", text)
    text = _EMAIL.sub("<email>", text)
    text = _UCID.sub("<ucid>", text)
    text = _UUID.sub("<id>", text)
    text = _HEX_ID.sub("<hex-id>", text)
    for name in extra_names:
        if len(name) >= 3:
            text = re.sub(rf"(?i)(?<![A-Za-z0-9]){re.escape(name)}(?![A-Za-z0-9])", "<user>", text)
    return text


def local_user_names() -> tuple[str, ...]:
    """The current Windows/OS user name(s), to be masked wherever they appear."""
    names = {Path.home().name}
    with contextlib.suppress(Exception):    # getpass can fail in odd service contexts; redaction is best effort
        names.add(getpass.getuser())
    return tuple(sorted(n for n in names if n))


def safe_error(exc: BaseException) -> str:
    """`ExceptionType: short redacted message` (OS errors give only the system text, never the file name)."""
    detail = exc.strerror if isinstance(exc, OSError) and exc.strerror else str(exc)
    first = detail.splitlines()[0] if detail else ""
    return redact_text(f"{type(exc).__name__}: {first}"[:MAX_ERROR], local_user_names())
