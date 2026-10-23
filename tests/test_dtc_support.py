import httpx

from fox3_central.services.elevation import BATCH, ElevationClient


def _client(handler, **kw):
    return ElevationClient("http://dem.test/elevation", transport=httpx.MockTransport(handler), **kw)


def _dem(request: httpx.Request) -> httpx.Response:
    lats = [float(v) for v in request.url.params["latitude"].split(",")]
    return httpx.Response(200, json={"elevation": [round(la * 10, 1) for la in lats]})


def test_terrains_list_every_map_with_its_confidence(user_client):
    maps = {t["id"]: t["calibration"] for t in user_client.get("/api/v1/dtc/terrains").json()}
    assert len(maps) == 11 and maps["Caucasus"] == "exact" and maps["Syria"] == "plausible" and maps["Nevada"] == "airports"


def test_elevation_uses_the_service_batches_and_caches():
    calls = []

    def handler(request):
        calls.append(request)
        return _dem(request)

    c = _client(handler)
    pts = [(40.0 + i / 1000, 3.0) for i in range(BATCH + 5)]
    assert c.lookup(pts)[0] == 400.0 and len(calls) == 2  # more than one batch of 100
    assert c.lookup(pts[:3]) == [400.0, 400.0, 400.0] and len(calls) == 2  # answered from the cache


def test_elevation_failure_gives_none_instead_of_an_error():
    assert _client(lambda r: httpx.Response(500)).lookup([(1.0, 2.0)]) == [None]
    assert _client(lambda r: httpx.Response(200, json={"oops": 1})).lookup([(1.0, 2.0)]) == [None]
    assert ElevationClient("").lookup([(1.0, 2.0)]) == [None]


def test_elevation_endpoint(app, user_client, client):
    app.state.ctx.elevation = _client(_dem)
    r = user_client.post("/api/v1/dtc/elevation", json={"points": [{"lat": 43.5, "lon": 41.0}, {"lat": 42.0, "lon": 41.0}]}).json()
    assert r["elevations"] == [435.0, 420.0] and r["enabled"] is True and "Copernicus" in r["attribution"]
    assert client.post("/api/v1/dtc/elevation", json={"points": [{"lat": 1, "lon": 1}]}).status_code == 401


def test_elevation_endpoint_validates_and_rate_limits(app, user_client):
    app.state.ctx.elevation = _client(_dem)
    assert user_client.post("/api/v1/dtc/elevation", json={"points": [{"lat": 99, "lon": 1}]}).status_code == 422
    assert user_client.post("/api/v1/dtc/elevation", json={"points": []}).status_code == 422
    codes = [user_client.post("/api/v1/dtc/elevation", json={"points": [{"lat": 1, "lon": 1}]}).status_code for _ in range(61)]
    assert codes[-1] == 429


def test_disabled_service_says_so(user_client):
    r = user_client.post("/api/v1/dtc/elevation", json={"points": [{"lat": 1, "lon": 1}]}).json()
    assert r == {**r, "enabled": False, "elevations": [None]}


def test_airfields_cover_every_map_and_sit_where_they_should(user_client):
    from fox3_common import geo
    for terrain in geo.PARAMS:
        found = user_client.get("/api/v1/dtc/airfields", params={"terrain": terrain}).json()
        assert len(found) >= 5 and all({"name", "lat", "lon", "civil"} <= set(a) for a in found), terrain
    batumi = next(a for a in user_client.get("/api/v1/dtc/airfields", params={"terrain": "Caucasus"}).json() if a["name"] == "Batumi")
    assert abs(batumi["lat"] - 41.61) < 0.01 and abs(batumi["lon"] - 41.60) < 0.01  # the real Batumi airport


def test_airfields_unknown_map_and_login(user_client, client):
    assert user_client.get("/api/v1/dtc/airfields", params={"terrain": "Atlantis"}).status_code == 404
    assert client.get("/api/v1/dtc/airfields", params={"terrain": "Syria"}).status_code == 401
