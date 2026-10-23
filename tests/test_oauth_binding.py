"""Login CSRF (found by the security review): a callback link must only work in the browser that started the login."""
import httpx
import pytest
from fastapi.testclient import TestClient

from fox3_central.app import create_app
from fox3_central.config import Settings
from fox3_central.services import auth as auth_service


@pytest.fixture
def discord_app(tmp_path, monkeypatch):
    app = create_app(Settings(db_url=f"sqlite:///{(tmp_path / 'o.sqlite').as_posix()}", demo_login=False, web_dir=None, elevation_url="",
                              public_base_url="https://fox3.example.org", discord_client_id="123", discord_client_secret="s"))

    def fake_discord(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/oauth2/token"):
            return httpx.Response(200, json={"access_token": "tok"})
        return httpx.Response(200, json={"id": "777", "username": "attacker", "global_name": "attacker"})

    real_client = httpx.Client  # captured first: the patch below replaces httpx.Client for the whole process
    monkeypatch.setattr(auth_service.httpx, "Client", lambda timeout=10: real_client(transport=httpx.MockTransport(fake_discord)))
    return app


def _start(client: TestClient) -> str:
    r = client.get("/api/v1/auth/discord/login", follow_redirects=False)
    assert r.status_code == 302
    return httpx.URL(r.headers["location"]).params["state"]


def test_login_works_in_the_browser_that_started_it(discord_app):
    browser = TestClient(discord_app, base_url="https://fox3.example.org")
    state = _start(browser)
    cookie = [c for c in browser.cookies.jar if c.name == "fox3_oauth"][0]
    assert cookie.secure and cookie.path == "/api/v1/auth/discord"
    assert browser.get(f"/api/v1/auth/discord/callback?code=x&state={state}", follow_redirects=False).status_code == 302
    assert browser.get("/api/v1/me").json()["name"] == "attacker"


def test_a_victim_cannot_be_logged_in_with_the_attackers_callback(discord_app):
    attacker = TestClient(discord_app, base_url="https://fox3.example.org")
    state = _start(attacker)  # the attacker starts a login and does NOT follow the callback; they send the link to the victim
    victim = TestClient(discord_app, base_url="https://fox3.example.org")
    r = victim.get(f"/api/v1/auth/discord/callback?code=attackers-code&state={state}", follow_redirects=False)
    assert r.status_code == 400
    assert victim.get("/api/v1/me").status_code == 401


def test_a_forged_nonce_and_a_replayed_state_are_refused(discord_app):
    browser = TestClient(discord_app, base_url="https://fox3.example.org")
    state = _start(browser)
    browser.cookies.clear()  # drop the real cookie, then plant a forged one
    browser.cookies.set("fox3_oauth", "forged", domain="fox3.example.org", path="/api/v1/auth/discord")
    assert browser.get(f"/api/v1/auth/discord/callback?code=x&state={state}", follow_redirects=False).status_code == 400
    state2 = _start(browser)
    assert browser.get(f"/api/v1/auth/discord/callback?code=x&state={state2}", follow_redirects=False).status_code == 302
    assert browser.get(f"/api/v1/auth/discord/callback?code=x&state={state2}", follow_redirects=False).status_code == 400  # single use
