"""Request-URL construction for the REST client: the path is built from components, never by string concatenation."""
from __future__ import annotations

import re

import httpx

from .errors import ConfigError, RestForbiddenCall

PREFIX_RE = re.compile(r"[A-Za-z0-9/_-]{0,40}")


def clean_prefix(prefix: str) -> str:
    """Validated prefix without surrounding slashes ('' for none)."""
    if not PREFIX_RE.fullmatch(prefix) or "//" in prefix:
        raise ConfigError("rest_prefix may only contain letters, digits, '/', '_' and '-' (max 40 characters)")
    return prefix.strip("/")


def parse_base(base_url: str) -> httpx.URL:
    """The configured base URL: scheme://host[:port] only. Userinfo, query, fragment and any path are rejected."""
    try:
        url = httpx.URL(base_url)
    except httpx.InvalidURL as exc:
        raise ConfigError("rest_url is not a valid URL") from exc
    if url.scheme not in ("http", "https") or not url.host:
        raise ConfigError("rest_url must be a full http(s) URL")
    if url.userinfo or url.query or url.fragment or "?" in base_url or "#" in base_url or url.path not in ("", "/"):
        raise ConfigError("rest_url must be only scheme://host:port (no credentials, path, query or fragment; use rest_prefix)")
    return url


def build_url(base: httpx.URL, prefix: str, path: str) -> httpx.URL:
    """URL whose path is exactly /<prefix>/<path>; verified against the base before it is used."""
    expected = "/" + "/".join(p for p in (prefix, path.strip("/")) if p)
    url = base.copy_with(path=expected, query=None, fragment=None, userinfo=b"")
    if ((url.scheme, url.host, url.port) != (base.scheme, base.host, base.port) or url.path != expected
            or url.query or url.fragment or url.userinfo):
        raise RestForbiddenCall("REST request URL does not match the configured base")
    return url
