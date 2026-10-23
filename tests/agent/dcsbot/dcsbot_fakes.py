"""Shared helpers for the dcsbot tests (no network, no real DCSServerBot)."""
from __future__ import annotations

import copy
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx

from fox3_central.core.validation import Validators

SCHEMAS = Path(__file__).resolve().parents[3] / "contracts" / "schemas"
VALIDATORS = Validators(SCHEMAS)

SERVER = {
    "name": "FOX3 Test", "description": "d", "status": "running", "address": "1.2.3.4:10308", "password": "TOPSECRET",
    "restart_time": "2025-08-07T12:00:00", "max_players": 32, "extensions": [{"name": "SRS", "value": "1.2.3.4:5002"}],
    "mission": {"name": "Foothold Syria", "uptime": 3600, "date_time": "2025-08-07 12:00:00", "theatre": "Syria",
                "blue_slots": 20, "red_slots": 20, "restart_time": 1691424000},
    "players": [{"nick": "Pilot1", "side": "blue", "unit_type": "FA-18C_hornet", "callsign": "Chevy 1-1", "radios": [127500000]},
                {"nick": "Pilot2", "side": "RED", "unit_type": "", "callsign": "x", "radios": []}],
    "weather": {"temperature": 15.5, "pressure": 760.0, "wind_speed": 10, "wind_direction": 270, "visibility": 9999,
                "clouds_base": 8000},
}
UCID1 = "aabbccddeeff00112233445566778899"
UCID2 = "11112222333344445555666677778888"
USERS = {"Pilot1": [{"ucid": UCID1, "nick": "Pilot1", "current_server": "FOX3 Test"},
                    {"ucid": "ffffffffffffffffffffffffffffffff", "nick": "Pilot10", "current_server": None}],
         "Pilot2": [{"ucid": UCID2, "nick": "pilot2", "current_server": None}]}
T0 = datetime(2026, 1, 1, 12, 0, 0, tzinfo=UTC)


class Clock:
    def __init__(self) -> None:
        self.now = T0

    def __call__(self) -> datetime:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += timedelta(seconds=seconds)


class FakeBot:
    """Behaves like the DCSServerBot REST service and records every request."""

    def __init__(self, servers: list[dict] | None = None, api_key: str | None = None) -> None:
        self.servers = copy.deepcopy(servers if servers is not None else [SERVER])
        self.api_key = api_key
        self.requests: list[httpx.Request] = []
        self.fail_with: Callable[[httpx.Request], httpx.Response] | None = None

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.fail_with:
            return self.fail_with(request)
        if self.api_key and request.headers.get("X-API-Key") != self.api_key:
            return httpx.Response(403, json={"detail": "Invalid API Key"})
        if request.method == "GET" and request.url.path.endswith("/servers"):
            return httpx.Response(200, json=self.servers)
        if request.method == "POST" and request.url.path.endswith("/getuser"):
            nick = httpx.QueryParams(request.content.decode())["nick"]
            return httpx.Response(200, json=USERS.get(nick, []))
        return httpx.Response(404)

    def transport(self) -> httpx.MockTransport:
        return httpx.MockTransport(self)
