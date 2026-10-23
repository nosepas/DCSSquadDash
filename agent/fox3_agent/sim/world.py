"""Simulated DCS/Foothold world that produces payloads matching contracts/schemas."""
from __future__ import annotations

import random
import uuid

from fox3_common import geo

from ..protocol import utc_now
from . import data
from .scenarios import CAUCASUS, Scenario


class SimWorld:
    def __init__(self, seed: int | None = None, scenario: Scenario = CAUCASUS):
        self.rng = random.Random(seed)
        self.sc = scenario
        self.zones = {n: {"coalition": c, "is_hq": hq, "level": self.rng.randint(1, 4)} for n, _, _, c, hq in scenario.zones}
        self.positions = {n: geo.latlon_to_xy(scenario.terrain, la, lo) for n, la, lo, _, _ in scenario.zones}
        self.online: dict[str, dict] = {}
        self.points: dict[str, float] = {u: 0.0 for _, u in data.PILOTS}
        self.mission_started = utc_now()
        self._events: list[dict] = []
        self._join(data.PILOTS[0], "blue")  # the demo user is linked to this pilot, so it is always online and blue
        for _ in range(3):
            self._join()

    # ---- simulation -------------------------------------------------------------------------------------------
    def tick(self) -> None:
        r = self.rng.random()
        if r < 0.25 and len(self.online) < len(data.PILOTS):
            self._join()
        elif r < 0.35 and len(self.online) > 2:
            self._leave()
        for p in self.online.values():
            if self.rng.random() < 0.15:
                p["in_air"] = not p["in_air"]
            self._move(p)
        if self.rng.random() < 0.5 and self.online:
            self._kill()
        if self.rng.random() < 0.12:
            self._capture()

    def _pilot(self, ucid: str) -> tuple[str, str]:
        return next((n, u) for n, u in data.PILOTS if u == ucid)

    def _join(self, pilot: tuple[str, str] | None = None, side: str | None = None) -> None:
        free = [(n, u) for n, u in data.PILOTS if u not in self.online]
        if not free and pilot is None:
            return
        name, ucid = pilot or self.rng.choice(free)
        side = side or self.rng.choice(["blue", "red"])
        home = self.rng.choice([z for z in self.sc.zones if z[3] == side] or list(self.sc.zones) or [("", *self.sc.center, side, False)])
        self.online[ucid] = {"ucid": ucid, "name": name, "coalition": side, "aircraft": self.rng.choice(data.AIRCRAFT[side]),
                             "slot": f"{side}_{self.rng.randint(1, 40)}", "in_air": False, "connected_at": utc_now(),
                             "position": {"lat": home[1], "lon": home[2], "alt_m": 20.0}}
        self._events.append(self._event("connect", self._party(self.online[ucid])))

    def _move(self, p: dict) -> None:
        """Random walk: airborne pilots drift and change altitude, grounded ones stay at their base."""
        pos = p["position"]
        if p["in_air"]:
            pos["lat"] = round(pos["lat"] + self.rng.uniform(-0.04, 0.04), 5)
            pos["lon"] = round(pos["lon"] + self.rng.uniform(-0.05, 0.05), 5)
            pos["alt_m"] = float(min(9000, max(500, pos["alt_m"] + self.rng.uniform(-400, 600))))
        else:
            pos["alt_m"] = 20.0

    def _leave(self) -> None:
        ucid = self.rng.choice([u for u in self.online if u != data.PILOTS[0][1]])
        self._events.append(self._event("disconnect", self._party(self.online.pop(ucid))))

    def _kill(self) -> None:
        killer = self.rng.choice(list(self.online.values()))
        enemies = [p for p in self.online.values() if p["coalition"] != killer["coalition"]]
        if enemies and self.rng.random() < 0.3:
            v = self.rng.choice(enemies)
            target = self._party(v)
        else:
            target = {"name": self.rng.choice(data.AI_TARGETS), "coalition": "red" if killer["coalition"] == "blue" else "blue",
                      "unit_type": None, "is_player": False}
        self.points[killer["ucid"]] += 10 if target["is_player"] else 2
        ev = self._event("kill", self._party(killer), target)
        ev["weapon"] = self.rng.choice(data.WEAPONS)
        self._events.append(ev)

    def _capture(self) -> None:
        border = [(a, b) for a, b in self.sc.connections if self.zones[a]["coalition"] != self.zones[b]["coalition"]]
        if not border:
            return
        a, b = self.rng.choice(border)
        winner_zone, lost = (a, b) if self.rng.random() < 0.5 else (b, a)
        if self.zones[lost]["is_hq"]:
            return
        side = self.zones[winner_zone]["coalition"]
        if side == "neutral":
            return
        self.zones[lost]["coalition"] = side
        pilots = [p for p in self.online.values() if p["coalition"] == side]
        actor = self._party(self.rng.choice(pilots)) if pilots else {"coalition": side, "is_player": False}
        ev = self._event("zone_captured", actor)
        ev["zone"] = lost
        self._events.append(ev)

    # ---- payload builders (one per contract schema) ---------------------------------------------------------------
    def server_info(self) -> dict:
        return {"server_name": self.sc.server_name, "dcs_version": "demo", "terrain": self.sc.terrain, "mission_name": self.sc.mission_name,
                "mission_started_at": self.mission_started, "mission_type": self.sc.mission_type, "max_players": 32,
                "dcsserverbot_version": "demo", "foothold_version": "demo", "agent_version": "0.1.0-sim",
                "capabilities": {"foothold": self.sc.mission_type == "foothold", "tacview": False, "grpc": False,
                                 "dcsbot_rest": False, "dcsbot_db": False},
                "weather": {"temperature_c": 18.0, "qnh_hpa": 1015.0, "wind_dir_deg": 240, "wind_speed_ms": 5.5, "visibility_m": 80000}}

    def foothold_state(self) -> dict:
        def at_risk(name: str) -> bool:
            c = self.zones[name]["coalition"]
            if c == "neutral":
                return False
            neighbours = [b if a == name else a for a, b in self.sc.connections if name in (a, b)]
            return any(self.zones[o]["coalition"] not in (c, "neutral") for o in neighbours)

        zones = []
        for n, z in self.zones.items():
            x, y = self.positions[n]
            zones.append({"name": n, "coalition": z["coalition"], "position": {"x": x, "y": y}, "is_hq": z["is_hq"],
                          "active": True, "at_risk": at_risk(n), "level": z["level"], "upgrades": []})
        stats = [{"name": self._pilot(u)[0], "ucid": u, "points": pts} for u, pts in self.points.items() if pts]
        return {"snapshot_at": utc_now(), "foothold_version": "demo", "mission_name": self.sc.mission_name, "zones": zones,
                "connections": [{"from": a, "to": b} for a, b in self.sc.connections], "missions": [], "player_stats": stats,
                "farps": [{"name": n, "geo": {"lat": la, "lon": lo}} for n, la, lo in self.sc.farps]}

    def players(self) -> dict:
        return {"snapshot_at": utc_now(), "players": list(self.online.values())}

    def tacview_indexes(self) -> list[dict]:
        """Two fictional finished recordings (the files do not exist: downloading them shows the 'agent did not answer' path)."""
        out = []
        for n, day in enumerate(("2026-10-18", "2026-10-19")):
            apps = [{"pilot": name, "aircraft": self.rng.choice(data.AIRCRAFT["blue"]), "coalition": "blue",
                     "first_offset_s": float(self.rng.randint(0, 900)), "last_offset_s": float(self.rng.randint(1800, 7200))}
                    for name, _ in data.PILOTS[: 6 - n]]
            out.append({"index_version": 1, "file": {
                "relative_path": f"Foothold/Tacview-{day.replace('-', '')}-190000-DCS-Foothold.zip.acmi", "size_bytes": 180_000_000 + n,
                "mtime": f"{day}T21:05:00Z", "reference_time": f"{day}T19:00:00Z", "duration_s": 7500.0, "complete": True},
                "appearances": apps})
        return out

    def drain_events(self) -> dict | None:
        evs, self._events = self._events, []
        return {"events": evs} if evs else None

    # ---- helpers ------------------------------------------------------------------------------------------------
    @staticmethod
    def _party(p: dict) -> dict:
        return {"ucid": p["ucid"], "name": p["name"], "coalition": p["coalition"], "unit_type": p.get("aircraft"), "is_player": True}

    @staticmethod
    def _event(kind: str, actor: dict, target: dict | None = None) -> dict:
        e = {"event_id": str(uuid.uuid4()), "type": kind, "time_utc": utc_now(), "actor": actor}
        if target:
            e["target"] = target
        return e
