"""The API key must only ever reach the configured host, and only the allowlisted paths."""
from __future__ import annotations

import httpx
import pytest

from fox3_agent.config import from_mapping
from fox3_agent.runtime.settings import merge
from fox3_agent.runtime.source_set import LiveSources
from fox3_agent.runtime.state import AgentState
from fox3_agent.sources.dcsbot.errors import ConfigError, RestForbiddenCall
from fox3_agent.sources.dcsbot.rest_client import RestClient

FORBIDDEN = ("/instance/restart", "/mission/upload", "/airbase/capture")


def recorder() -> tuple[list[httpx.Request], httpx.MockTransport]:
    seen: list[httpx.Request] = []

    def handler(req: httpx.Request) -> httpx.Response:
        seen.append(req)
        return httpx.Response(200, json=[])

    return seen, httpx.MockTransport(handler)


@pytest.mark.parametrize("base", [
    "http://127.0.0.1:9876/restart?x=", "http://127.0.0.1:9876/restart?", "http://127.0.0.1:9876#", "http://127.0.0.1:9876/#x",
    "http://user:pw@127.0.0.1:9876", "http://127.0.0.1:9876/instance/restart", "ftp://127.0.0.1", "http://", "attacker.example",
])
def test_hostile_base_urls_are_rejected_before_any_request(base):
    seen, transport = recorder()
    with pytest.raises(ConfigError):
        RestClient(base, api_key="KEY", transport=transport).get_servers()
    assert seen == []


@pytest.mark.parametrize("prefix", ["../x", "a b", "a?b=1", "a#b", "a//b", "x" * 41, "a%2Fb", "a.b", "a\b"])
def test_invalid_prefix_is_rejected(prefix):
    with pytest.raises(ConfigError):
        RestClient("http://127.0.0.1:9876", prefix=prefix, api_key="KEY")


@pytest.mark.parametrize("prefix", ["", "stats", "/stats/", "a/b_c-d"])
def test_every_request_has_exactly_prefix_and_allowed_path(prefix):
    seen, transport = recorder()
    client = RestClient("http://127.0.0.1:9876/", prefix=prefix, api_key="KEY", transport=transport)
    client.get_servers()
    client.get_users("x")
    want = "/" + (prefix.strip("/") + "/" if prefix.strip("/") else "")
    assert [r.url.path for r in seen] == [want + "servers", want + "getuser"]
    assert all(r.url.host == "127.0.0.1" and r.url.port == 9876 and not r.url.query and not r.url.fragment for r in seen)
    assert all(r.headers["X-API-Key"] == "KEY" for r in seen)


@pytest.mark.parametrize("path", FORBIDDEN)
def test_allowlist_cannot_be_bypassed(path):
    seen, transport = recorder()
    client = RestClient("http://127.0.0.1:9876", api_key="KEY", transport=transport)
    for method in ("GET", "POST"):
        with pytest.raises(RestForbiddenCall):
            client._request(method, path)
        with pytest.raises(RestForbiddenCall):
            client._request(method, "/servers/../" + path.lstrip("/"))
    assert seen == []


def _local(**extra):
    return from_mapping({"central": {"url": "https://c.example"}, "sources": {"dcsserverbot": {"api_key_env": "K", **extra}}})


def _remote(url: str) -> dict:
    return {"settings": {"dcsbot": {"rest_enabled": True, "rest_url": url}}}


@pytest.mark.parametrize("url", ["http://attacker.example:9876", "https://evil.test", "http://10.0.0.9:9876", "http://localhost.evil.com",
                                 "http://127.0.0.1@evil.com", "not a url"])
def test_remote_rest_url_with_unlisted_host_is_ignored(url):
    eff = merge(_local(rest_url="http://localhost:9999"), _remote(url))
    assert eff.rest_url_refused and eff.dcsbot["rest_url"] == "http://localhost:9999"
    assert eff.dcsbot["api_key_env"] == "K"


def test_remote_rest_url_loopback_and_allowlisted_accepted():
    assert not merge(_local(), _remote("http://127.0.0.1:9876")).rest_url_refused
    assert merge(_local(), _remote("http://[::1]:9876")).dcsbot["rest_url"] == "http://[::1]:9876"
    cfg = _local(allowed_rest_hosts=["Bot.LAN"])
    assert "allowed_rest_hosts" not in cfg.dcsbot
    eff = merge(cfg, _remote("http://bot.lan:9876"))
    assert not eff.rest_url_refused and eff.dcsbot["rest_url"] == "http://bot.lan:9876"


@pytest.mark.parametrize("bad", ["bot.lan", [1], [""]])
def test_allowed_rest_hosts_type_is_validated(bad):
    with pytest.raises(Exception, match="allowed_rest_hosts"):
        _local(allowed_rest_hosts=bad)


def test_refusal_is_surfaced_and_key_never_sent_to_the_remote_host(tmp_path, monkeypatch):
    monkeypatch.setenv("K", "TOPSECRET")
    live = LiveSources(_local(), AgentState(tmp_path), tmp_path)
    live.apply(_remote("http://attacker.example:9876"))
    warnings = [w for s in live.sources for w in s.warnings()]
    refused = [w for w in warnings if w.code == "DCSBOT_REST_URL_REFUSED"]
    assert len(refused) == 1 and "attacker" not in refused[0].message and "TOPSECRET" not in refused[0].message
    assert live.dcsbot.config.rest_url == "http://localhost:9876"  # the default loopback URL, never the refused one
    live.apply({**_remote("http://127.0.0.1:9876"), "revision": "2"})
    assert not [w for s in live.sources for w in s.warnings() if w.code == "DCSBOT_REST_URL_REFUSED"]
