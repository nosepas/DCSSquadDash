"""`fox3-agent init`: write a minimal, validated `agent.toml`. Pure functions, no network, no secrets.

Almost every setting comes from the central admin panel; the file only needs the central URL, where to keep the state
and (optionally) the NAME of the environment variable that holds the DCSServerBot API key. The key itself is never written.
"""
from __future__ import annotations

import json
import tomllib
from pathlib import Path
from urllib.parse import urlparse

from .config import ConfigError, from_mapping
from .sources.dcsbot.config import ENV_NAME

FILE_NAME = "agent.toml"


class ScaffoldError(ValueError):
    """Hostile or malformed input, or a file that must not be overwritten."""


def _quoted(value: str, what: str) -> str:
    if any(ord(c) < 32 or ord(c) == 127 for c in value):
        raise ScaffoldError(f"{what} contains control characters")
    return json.dumps(value)  # JSON string syntax is a valid TOML basic string


def render_agent_toml(central_url: str, state_dir: Path, dcsbot_api_key_env: str | None = None) -> str:
    """Text of a valid agent.toml, checked with the same rules as `config.load_config`."""
    url = central_url.strip()
    try:
        parsed = urlparse(url)
    except ValueError as exc:
        raise ScaffoldError("central URL is not a valid URL") from exc
    if any(c.isspace() for c in url) or parsed.username or parsed.password or parsed.query or parsed.fragment:
        raise ScaffoldError("central URL must not contain spaces, credentials, a query or a fragment")
    if dcsbot_api_key_env is not None and not ENV_NAME.fullmatch(dcsbot_api_key_env):
        raise ScaffoldError("the DCSServerBot key option takes the NAME of an environment variable (e.g. FOX3_DCSBOT_API_KEY), not the key")
    lines = [
        "# FOX3 agent configuration written by `fox3-agent init`. Everything else is set in the web admin panel.",
        "[central]",
        f"url = {_quoted(url, 'central URL')}",
        "",
        "[paths]",
        f"state_dir = {_quoted(str(state_dir), 'state dir')}",
    ]
    if dcsbot_api_key_env:
        lines += ["", "[sources.dcsserverbot]", f"api_key_env = {_quoted(dcsbot_api_key_env, 'variable name')}"]
    text = "\n".join(lines) + "\n"
    try:
        from_mapping(tomllib.loads(text))
    except (ConfigError, tomllib.TOMLDecodeError) as exc:
        raise ScaffoldError(str(exc)) from exc
    return text


def write_agent_toml(out_dir: Path, central_url: str, state_dir: Path | None = None, dcsbot_api_key_env: str | None = None) -> Path:
    """Create `out_dir/agent.toml`; never overwrites an existing file."""
    text = render_agent_toml(central_url, state_dir or out_dir / "state", dcsbot_api_key_env)
    target = out_dir / FILE_NAME
    out_dir.mkdir(parents=True, exist_ok=True)
    try:
        with target.open("x", encoding="utf-8", newline="\n") as f:  # "x": atomic refusal if it exists
            f.write(text)
    except FileExistsError as exc:
        raise ScaffoldError(f"{target} already exists; it was left untouched (delete it first to start over)") from exc
    return target
