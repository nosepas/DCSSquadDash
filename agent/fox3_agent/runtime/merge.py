"""Cross-source enrichment: player names -> UCIDs, Foothold positions -> online players."""
from __future__ import annotations

from collections.abc import Callable


def attach_positions(players_payload: dict, positions: list[dict]) -> dict:
    """Add `position` to online players whose name matches a Foothold player entry (matched by exact name)."""
    by_name = {p["name"]: p for p in positions if p.get("name")}
    for player in players_payload["players"]:
        pos = by_name.get(player["name"])
        if pos and pos.get("lat") is not None and pos.get("lon") is not None:
            player["position"] = {"lat": pos["lat"], "lon": pos["lon"], **({"alt_m": pos["alt_m"]} if "alt_m" in pos else {})}
    return players_payload


def resolve_stat_ucids(state_payload: dict, resolver: Callable[[str], str | None]) -> dict:
    """Fill `ucid` of Foothold player stats that are keyed by name only. Unresolved entries stay as they are."""
    for stat in state_payload.get("player_stats", []):
        if not stat.get("ucid") and stat.get("name"):
            stat["ucid"] = resolver(stat["name"])
    return state_payload
