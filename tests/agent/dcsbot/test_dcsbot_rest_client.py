from __future__ import annotations

import httpx
import pytest
from dcsbot_fakes import FakeBot

from fox3_agent.sources.dcsbot.errors import RestAuthError, RestForbiddenCall, RestProtocolError, RestUnreachable
from fox3_agent.sources.dcsbot.rest_client import RestClient


def client(bot: FakeBot, **kw) -> RestClient:
    return RestClient("http://bot:9876", transport=bot.transport(), **kw)


def test_api_key_is_sent_in_x_api_key_header_and_prefix_applied():
    bot = FakeBot(api_key="s3cret")
    assert client(bot, api_key="s3cret", prefix="stats").get_servers()[0]["name"] == "FOX3 Test"
    req = bot.requests[0]
    assert req.headers["X-API-Key"] == "s3cret" and str(req.url) == "http://bot:9876/stats/servers"


def test_no_key_header_when_not_configured():
    bot = FakeBot()
    client(bot).get_servers()
    assert "x-api-key" not in bot.requests[0].headers


def test_getuser_is_a_form_post():
    bot = FakeBot()
    assert client(bot).get_users("Pilot1")[0]["nick"] == "Pilot1"
    req = bot.requests[0]
    assert req.method == "POST" and req.headers["content-type"] == "application/x-www-form-urlencoded"


@pytest.mark.parametrize("status", [401, 403])
def test_auth_failure_never_leaks_key(status):
    bot = FakeBot()
    bot.fail_with = lambda r: httpx.Response(status)
    c = client(bot, api_key="s3cret-key-123")
    with pytest.raises(RestAuthError) as exc:
        c.get_servers()
    assert "s3cret-key-123" not in str(exc.value) and "s3cret-key-123" not in repr(c)


def test_timeout_and_connection_errors_are_unreachable():
    def boom(request):
        raise httpx.ConnectTimeout("t", request=request)
    with pytest.raises(RestUnreachable):
        RestClient("http://x", transport=httpx.MockTransport(boom)).get_servers()

    def refused(request):
        raise httpx.ConnectError("refused", request=request)
    with pytest.raises(RestUnreachable):
        RestClient("http://x", transport=httpx.MockTransport(refused)).get_servers()


def test_non_200_and_bad_payloads():
    bot = FakeBot()
    bot.fail_with = lambda r: httpx.Response(500)
    with pytest.raises(RestUnreachable):
        client(bot).get_servers()
    bot.fail_with = lambda r: httpx.Response(404)
    with pytest.raises(RestProtocolError):
        client(bot).get_servers()
    bot.fail_with = lambda r: httpx.Response(200, content=b"<html>")
    with pytest.raises(RestProtocolError):
        client(bot).get_servers()
    bot.fail_with = lambda r: httpx.Response(200, json={"not": "a list"})
    with pytest.raises(RestProtocolError):
        client(bot).get_servers()


def test_oversize_body_rejected():
    bot = FakeBot()
    bot.fail_with = lambda r: httpx.Response(200, content=b"[" + b"{}," * 5000 + b"{}]")
    with pytest.raises(RestProtocolError, match="larger"):
        client(bot, max_bytes=1000).get_servers()


@pytest.mark.parametrize("method,path", [("POST", "/instance/restart"), ("POST", "/airbase/capture"), ("GET", "/airbases"),
                                         ("POST", "/mission/upload"), ("POST", "/servers"), ("GET", "/getuser"),
                                         ("GET", "/servers/../instance/stop")])
def test_allowlist_blocks_everything_else_before_network(method, path):
    bot = FakeBot()
    c = client(bot)
    with pytest.raises(RestForbiddenCall):
        c._request(method, path)
    assert bot.requests == []


def test_client_exposes_only_read_methods():
    public = {n for n in dir(RestClient) if not n.startswith("_")}
    assert public == {"close", "get_servers", "get_users"}


def test_redirects_not_followed():
    bot = FakeBot()
    bot.fail_with = lambda r: httpx.Response(302, headers={"location": "http://evil/instance/stop"})
    with pytest.raises(RestProtocolError):
        client(bot).get_servers()
    assert len(bot.requests) == 1
