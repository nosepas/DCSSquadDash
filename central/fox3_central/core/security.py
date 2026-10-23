"""Hashing and random-token helpers."""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets


def sha256(value: str) -> str:
    return hashlib.sha256(value.encode()).hexdigest()


def token(nbytes: int = 32) -> str:
    return secrets.token_urlsafe(nbytes)


def short_code(nbytes: int = 8) -> str:
    """Human-typeable code (base32, no padding), e.g. for pairing and Discord<->UCID linking."""
    return base64.b32encode(os.urandom(nbytes)).decode().rstrip("=")[:10]


def safe_equal(a: str, b: str) -> bool:
    return hmac.compare_digest(a.encode(), b.encode())
