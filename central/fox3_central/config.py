"""Central settings, read from FOX3_* environment variables."""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]


def _bool(name: str, default: bool = False) -> bool:
    return os.environ.get(name, "1" if default else "0").lower() in ("1", "true", "yes")


@dataclass
class Settings:
    db_url: str = field(default_factory=lambda: os.environ.get("FOX3_DB_URL", "sqlite:///./fox3-demo.db"))
    public_base_url: str = field(default_factory=lambda: os.environ.get("FOX3_PUBLIC_BASE_URL", "http://localhost:8000").rstrip("/"))
    demo_login: bool = field(default_factory=lambda: _bool("FOX3_DEMO_LOGIN"))
    discord_client_id: str = field(default_factory=lambda: os.environ.get("FOX3_DISCORD_CLIENT_ID", ""))
    discord_client_secret: str = field(default_factory=lambda: os.environ.get("FOX3_DISCORD_CLIENT_SECRET", ""))
    admin_ids: list[str] = field(default_factory=lambda: [s for s in os.environ.get("FOX3_ADMIN_IDS", "").split(",") if s.strip()])
    contracts_dir: Path = field(default_factory=lambda: Path(os.environ.get("FOX3_CONTRACTS_DIR", REPO_ROOT / "contracts")))
    web_dir: Path | None = field(default_factory=lambda: Path(p) if (p := os.environ.get("FOX3_WEB_DIR")) else (REPO_ROOT / "web" / "dist"))
    # Folder holding the built agent (fox3-agent.exe, fox3-agent.version) that admins download as a personalised package.
    agent_dir: Path | None = field(default_factory=lambda: Path(p) if (p := os.environ.get("FOX3_AGENT_DIR")) else (REPO_ROOT / "dist" / "agent"))
    session_ttl_hours: int = 168
    max_raw_bytes: int = 262144
    online_timeout_s: int = 90
    # Ground elevation for the DTC generator (Copernicus GLO-90 through Open-Meteo, free for non-commercial use, attribution required).
    # Set FOX3_ELEVATION_URL to an empty string to disable; the user then types elevations by hand.
    elevation_url: str = field(default_factory=lambda: os.environ.get("FOX3_ELEVATION_URL", "https://api.open-meteo.com/v1/elevation"))

    @property
    def cookie_secure(self) -> bool:
        return self.public_base_url.startswith("https://")

    @property
    def discord_enabled(self) -> bool:
        return bool(self.discord_client_id and self.discord_client_secret)
