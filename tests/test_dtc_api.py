"""DTC import/export through the API, with the owner's real samples when present (skipped in a clean checkout)."""
import json
from pathlib import Path
from urllib.parse import unquote

import pytest

SAMPLES = Path(__file__).resolve().parents[1] / "samples"
F16 = SAMPLES / "F-16C_50_DTC.dtc"
needs_samples = pytest.mark.skipif(not F16.exists(), reason="sample .dtc not present")


def test_aircraft_table_lists_fa18_as_disabled(user_client):
    table = {a["id"]: a for a in user_client.get("/api/v1/dtc/aircraft").json()}
    assert {"F-16C_50", "F-14BU", "AH-64D_BLK_II"} <= set(table) and table["FA-18C_hornet"]["enabled"] is False
    assert table["F-16C_50"]["unsupported"]  # parts preserved on export but not editable are declared


def test_dtc_endpoints_need_login(client):
    assert client.get("/api/v1/dtc/aircraft").status_code == 401
    assert client.post("/api/v1/dtc/import", content=b"{}").status_code == 401
    assert client.post("/api/v1/dtc/generate", json={"model": {}}).status_code == 401


def test_import_rejects_garbage_and_oversized(user_client):
    assert user_client.post("/api/v1/dtc/import", content=b"not json").status_code == 422
    assert user_client.post("/api/v1/dtc/import", content=b"").status_code == 400
    assert user_client.post("/api/v1/dtc/import", content=b"x" * (8 * 1024 * 1024 + 1)).status_code == 413  # refused by the body limit


def test_generate_rejects_a_model_that_breaks_the_contract(user_client):
    r = user_client.post("/api/v1/dtc/generate", json={"model": {"aircraft": "F-16C_50"}})
    assert r.status_code == 422 and r.json()["error"]["details"]


def test_export_with_the_builtin_template_adds_a_waypoint(user_client):
    model = {"model_version": 1, "terrain": "Syria", "aircraft": "F-16C_50", "name": "Strike 1",
             "waypoints": [{"lat": 35.95, "lon": 35.40, "elevation_m": 28.0, "name": "Hmeimim"}]}
    r = user_client.post("/api/v1/dtc/generate", json={"model": model})
    assert r.status_code == 200 and 'filename="F-16C_50_Strike_1.dtc"' in r.headers["content-disposition"]
    data = json.loads(r.content)
    assert data["type"] == "F-16C_50" and len(data["data"]["MPD"]["NAV_PTS"]) == 1


def test_unsupported_aircraft_and_bad_terrain_give_clear_errors(user_client):
    bad = {"model_version": 1, "terrain": "Atlantis", "aircraft": "F-16C_50", "waypoints": []}
    assert user_client.post("/api/v1/dtc/generate", json={"model": bad}).status_code == 422
    fa18 = {"model_version": 1, "terrain": "Syria", "aircraft": "FA-18C_hornet", "waypoints": []}
    r = user_client.post("/api/v1/dtc/generate", json={"model": fa18})
    assert r.status_code == 422 and "not supported" in json.dumps(r.json()).lower()


def test_unknown_template_id_and_other_users_template(user_client, admin_client):
    model = {"model_version": 1, "terrain": "Syria", "aircraft": "F-16C_50", "waypoints": []}
    assert user_client.post("/api/v1/dtc/generate", json={"model": model, "template_id": "nope"}).status_code == 404


@needs_samples
def test_import_edit_export_round_trip_keeps_everything_else(user_client):
    raw = F16.read_bytes()
    up = user_client.post("/api/v1/dtc/import", content=raw).json()
    assert up["model"]["aircraft"] == "F-16C_50" and up["model"]["terrain"] == "Syria" and up["template_id"]
    same = user_client.post("/api/v1/dtc/generate", json={"model": up["model"], "template_id": up["template_id"]})
    assert same.content == raw  # an unedited export is byte-identical to what DCS wrote
    up["model"]["waypoints"].append({"lat": 36.0, "lon": 36.0, "elevation_m": 100.0})
    edited = user_client.post("/api/v1/dtc/generate", json={"model": up["model"], "template_id": up["template_id"]})
    a, b = json.loads(raw), json.loads(edited.content)
    assert len(b["data"]["MPD"]["NAV_PTS"]) == len(a["data"]["MPD"]["NAV_PTS"]) + 1
    for key in ("COLR", "COMM", "ELINT"):
        assert b["data"][key] == a["data"][key]  # nothing we do not understand was touched
    assert unquote(edited.headers["x-dtc-warnings"]) is not None


@needs_samples
def test_another_user_cannot_use_my_uploaded_template(user_client, admin_client):
    tid = user_client.post("/api/v1/dtc/import", content=F16.read_bytes()).json()["template_id"]
    model = {"model_version": 1, "terrain": "Syria", "aircraft": "F-16C_50", "waypoints": []}
    assert admin_client.post("/api/v1/dtc/generate", json={"model": model, "template_id": tid}).status_code == 404


def test_default_model_has_the_real_default_radios(user_client):
    f16 = user_client.get("/api/v1/dtc/default-model", params={"aircraft": "F-16C_50", "terrain": "Syria"}).json()
    assert f16["aircraft"] == "F-16C_50" and f16["terrain"] == "Syria" and not f16.get("waypoints")
    assert [r["id"] for r in f16["radios"]["radios"]] == ["COMM1", "COMM2"] and len(f16["radios"]["radios"][0]["channels"]) == 20
    ah = user_client.get("/api/v1/dtc/default-model", params={"aircraft": "AH-64D_BLK_II", "terrain": "Caucasus"}).json()
    assert len(ah["radios"]["presets"]) == 10 and "guard_receiver" in ah["radios"]


def test_default_model_refuses_what_is_not_supported(user_client, client):
    assert user_client.get("/api/v1/dtc/default-model", params={"aircraft": "FA-18C_hornet"}).status_code == 422
    assert user_client.get("/api/v1/dtc/default-model", params={"aircraft": "F-16C_50", "terrain": "Atlantis"}).status_code == 422
    assert client.get("/api/v1/dtc/default-model", params={"aircraft": "F-16C_50"}).status_code == 401


def test_radio_edit_goes_through_the_api_and_only_changes_radios(user_client):
    model = user_client.get("/api/v1/dtc/default-model", params={"aircraft": "F-16C_50", "terrain": "Syria"}).json()
    model["radios"]["radios"][0]["channels"][0]["frequency_mhz"] = 251
    model["waypoints"] = [{"lat": 35.95, "lon": 35.40, "elevation_m": 28.0}]
    r = user_client.post("/api/v1/dtc/generate", json={"model": model})
    assert r.status_code == 200
    data = json.loads(r.content)["data"]
    assert data["COMM"]["COMM1"]["Channel_1"]["freq"] == 251 and len(data["MPD"]["NAV_PTS"]) == 1


def test_radios_are_rejected_for_the_f14(user_client):
    model = {"model_version": 1, "terrain": "Caucasus", "aircraft": "F-14BU", "radios": {"radios": []}}
    r = user_client.post("/api/v1/dtc/generate", json={"model": model})
    assert r.status_code == 422 and "radios" in json.dumps(r.json())
