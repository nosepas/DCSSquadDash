"""HTTP client for the central agent API (outbound only)."""
from __future__ import annotations

import enum

import httpx


class Outcome(enum.Enum):
    OK = "ok"
    RETRY = "retry"  # network error, 5xx or 429: keep the message and try again later
    AUTH = "auth"    # 401: the agent key was rejected (revoked?): keep the message, back off hard, tell the operator
    DROP = "drop"    # other 4xx: the message is invalid, retrying cannot help


# Idle timeouts only (no total deadline: big recordings must finish), but a stalled source must not hold a worker forever.
UPLOAD_TIMEOUT = httpx.Timeout(connect=10.0, read=120.0, write=120.0, pool=10.0)


class CentralClient:
    def __init__(self, base_url: str, api_key: str | None = None, verify: bool | str = True, timeout: float = 10.0,
                 http: httpx.Client | None = None):
        """`http` lets tests inject a client already bound to the agent API (e.g. a TestClient)."""
        self._http = http or httpx.Client(base_url=f"{base_url.rstrip('/')}/agent/v1", verify=verify, timeout=timeout,
                                          headers={"Authorization": f"Bearer {api_key}"} if api_key else {})

    def pair(self, code: str, agent_name: str, agent_version: str) -> dict:
        r = self._http.post("/pair", json={"pairing_code": code, "agent_name": agent_name, "agent_version": agent_version})
        r.raise_for_status()
        return r.json()

    def get_config(self) -> dict:
        r = self._http.get("/config")
        r.raise_for_status()
        return r.json()

    def file_requests(self, wait_s: float = 25.0) -> list[dict]:
        """Long poll: recordings the browser users are waiting for."""
        r = self._http.get("/file-requests", params={"wait": wait_s}, timeout=wait_s + 10)
        r.raise_for_status()
        return r.json()

    def upload_file(self, request_id: str, chunks, size: int) -> None:
        """Stream a file to central (never loaded in memory). `chunks` yields bytes."""
        r = self._http.put(f"/file-requests/{request_id}/content", content=chunks, headers={"X-File-Size": str(size)}, timeout=UPLOAD_TIMEOUT)
        r.raise_for_status()

    def fail_request(self, request_id: str, reason: str) -> None:
        self._http.post(f"/file-requests/{request_id}/fail", json={"reason": reason}).raise_for_status()

    def send(self, path: str, body: dict) -> Outcome:
        try:
            r = self._http.post(path, json=body)
        except httpx.TransportError:
            return Outcome.RETRY
        if r.is_success:
            return Outcome.OK
        if r.status_code == 401:
            return Outcome.AUTH
        return Outcome.RETRY if r.status_code >= 500 or r.status_code == 429 else Outcome.DROP

    def close(self) -> None:
        self._http.close()
