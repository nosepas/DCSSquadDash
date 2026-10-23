"""Read-only HTTP client for the DCSServerBot REST API (plugin `restapi`).

Verified against DCSServerBot v3.0.4.27 (plugins/restapi/commands.py, register_routes):
  * the optional API key is sent in the `X-API-Key` request header (FastAPI APIKeyHeader), compared with `!=`;
    a wrong/missing key gives HTTP 403;
  * the optional `prefix` (config/plugins/restapi.yaml) is prepended to every route; a missing leading '/' is added.

Security: only the calls in ALLOWED_CALLS can ever be sent. The same API can restart servers, load missions or capture
airbases, so the allowlist is enforced in `_request`, before any network activity. The API key is never put in an
exception message or a log line.
"""
from __future__ import annotations

import json
from typing import Any

import httpx

from .errors import RestAuthError, RestForbiddenCall, RestProtocolError, RestUnreachable
from .rest_url import build_url, clean_prefix, parse_base

ALLOWED_CALLS: frozenset[tuple[str, str]] = frozenset({("GET", "/servers"), ("POST", "/getuser")})
API_KEY_HEADER = "X-API-Key"


class RestClient:
    def __init__(self, base_url: str, *, prefix: str = "", api_key: str | None = None, verify: bool | str = True,
                 timeout_s: float = 5.0, max_bytes: int = 2_000_000, transport: httpx.BaseTransport | None = None) -> None:
        self._base, self._prefix = parse_base(base_url), clean_prefix(prefix)
        self._root = f"{self._base.scheme}://{self._base.netloc.decode()}" + (f"/{self._prefix}" if self._prefix else "")
        self._headers = {API_KEY_HEADER: api_key} if api_key else {}
        self._max_bytes = max_bytes
        self._http = httpx.Client(timeout=timeout_s, verify=verify, transport=transport, follow_redirects=False)

    def __repr__(self) -> str:
        return f"RestClient(root={self._root!r})"

    def close(self) -> None:
        self._http.close()

    def get_servers(self) -> list[dict[str, Any]]:
        return self._list(self._request("GET", "/servers"))

    def get_users(self, nick: str) -> list[dict[str, Any]]:
        """POST /getuser (form `nick`). Note: DCSServerBot matches with ILIKE '%nick%' (substring), filter afterwards."""
        return self._list(self._request("POST", "/getuser", data={"nick": nick}))

    @staticmethod
    def _list(body: Any) -> list[dict[str, Any]]:
        if not isinstance(body, list) or not all(isinstance(x, dict) for x in body):
            raise RestProtocolError("unexpected response shape (expected a JSON list of objects)")
        return body

    def _request(self, method: str, path: str, *, data: dict[str, str] | None = None) -> Any:
        if (method, path) not in ALLOWED_CALLS:
            raise RestForbiddenCall(f"REST call {method} {path} is not in the read-only allowlist")
        url = build_url(self._base, self._prefix, path)
        try:
            with self._http.stream(method, url, data=data, headers=self._headers) as resp:
                status = resp.status_code
                raw = self._read_limited(resp) if status == 200 else b""
        except httpx.TimeoutException as exc:
            raise RestUnreachable("DCSServerBot REST request timed out") from exc
        except httpx.HTTPError as exc:
            raise RestUnreachable(f"DCSServerBot REST unreachable ({type(exc).__name__})") from exc
        if status in (401, 403):
            raise RestAuthError(f"DCSServerBot REST rejected the API key (HTTP {status})")
        if status != 200:
            kind = RestUnreachable if status >= 500 else RestProtocolError
            raise kind(f"DCSServerBot REST answered HTTP {status}")
        try:
            return json.loads(raw)
        except ValueError as exc:
            raise RestProtocolError("DCSServerBot REST answered invalid JSON") from exc

    def _read_limited(self, resp: httpx.Response) -> bytes:
        chunks: list[bytes] = []
        size = 0
        for chunk in resp.iter_bytes():
            size += len(chunk)
            if size > self._max_bytes:
                raise RestProtocolError(f"DCSServerBot REST response larger than {self._max_bytes} bytes")
            chunks.append(chunk)
        return b"".join(chunks)
