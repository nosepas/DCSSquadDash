"""Request body size limits, enforced BEFORE the application parses anything (pure ASGI middleware).

Without this, an anonymous client could make the single central process read and parse arbitrarily large JSON bodies
(memory exhaustion) because FastAPI parses the body before authentication runs.
"""
from __future__ import annotations

import json
import re
from collections.abc import Awaitable, Callable, MutableMapping
from typing import Any

Scope = MutableMapping[str, Any]
Receive = Callable[[], Awaitable[MutableMapping[str, Any]]]
Send = Callable[[MutableMapping[str, Any]], Awaitable[None]]

KB, MB = 1024, 1024 * 1024
DEFAULT_LIMIT = 64 * KB
SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}

# (method, path regex, limit in bytes; None = no limit). First match wins.
RULES: list[tuple[str, re.Pattern[str], int | None]] = [
    ("PUT", re.compile(r"^/agent/v1/file-requests/[^/]+/content$"), None),  # streamed recording: bounded by the transfer broker
    ("POST", re.compile(r"^/api/v1/dtc/import$"), 8 * MB),
    ("POST", re.compile(r"^/api/v1/dtc/generate$"), 2 * MB),
    ("POST", re.compile(r"^/agent/v1/foothold-state$"), 2 * MB),
    ("POST", re.compile(r"^/agent/v1/tacview-index$"), 2 * MB),
    ("POST", re.compile(r"^/agent/v1/events$"), 1 * MB),
    ("POST", re.compile(r"^/agent/v1/players$"), 512 * KB),
    ("POST", re.compile(r"^/agent/v1/discord-links$"), 256 * KB),
]


def limit_for(method: str, path: str) -> int | None:
    for m, rx, limit in RULES:
        if m == method and rx.match(path):
            return limit
    return DEFAULT_LIMIT


async def _reject(send: Send) -> None:
    body = json.dumps({"error": {"code": "payload_too_large", "message": "request body too large"}}).encode()
    await send({"type": "http.response.start", "status": 413, "headers": [(b"content-type", b"application/json"),
                                                                          (b"content-length", str(len(body)).encode())]})
    await send({"type": "http.response.body", "body": body})


class BodyLimitMiddleware:
    def __init__(self, app: Callable[[Scope, Receive, Send], Awaitable[None]]):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http" or scope["method"] in SAFE_METHODS:
            return await self.app(scope, receive, send)
        limit = limit_for(scope["method"], scope["path"])
        if limit is None:
            return await self.app(scope, receive, send)
        declared = dict(scope["headers"]).get(b"content-length", b"")
        if declared.isdigit() and int(declared) > limit:
            return await _reject(send)

        seen, over = 0, False

        async def counted_receive() -> MutableMapping[str, Any]:
            nonlocal seen, over
            msg = await receive()
            if msg["type"] == "http.request":
                seen += len(msg.get("body", b""))
                if seen > limit:  # chunked body larger than allowed: stop feeding the app, answer 413 instead of its response
                    over = True
                    return {"type": "http.request", "body": b"", "more_body": False}
            return msg

        async def guarded_send(msg: MutableMapping[str, Any]) -> None:
            nonlocal over
            if not over:
                return await send(msg)
            if msg["type"] == "http.response.start":
                over = True
                await _reject(send)

        await self.app(scope, counted_receive, guarded_send)
