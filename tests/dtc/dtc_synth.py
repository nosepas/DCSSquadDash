"""Small synthetic .dtc documents that mimic the structure of the real samples (no personal data), for clean-checkout tests."""
from __future__ import annotations

from typing import Any

from fox3_common import geo
from fox3_dtc.io import write_json

# Syria / Caucasus reference points (lat, lon, alt)
LL = [(36.2, 36.1, 100), (36.5, 36.9, 250.5), (36.9, 37.4, 0), (35.8, 37.0, 1200)]


def _xy(terrain: str, lat: float, lon: float) -> tuple[float, float]:
    x, y = geo.latlon_to_xy(terrain, lat, lon)
    return round(x, 8), round(y, 8)


def f16_stpt(n: int, lat: float, lon: float, alt: float) -> dict[str, Any]:
    x, y = _xy("Syria", lat, lon)
    return {"alt": alt, "altitudeType": 1, "FIX_Time": False, "id": f"STPT{n}", "idOA1": f"OA1{n}", "idOA1_Line": f"OA1{n}Line", "idOA2": f"OA2{n}",
            "idOA2_Line": f"OA2{n}Line", "isOAP_1": False, "isTOSEnabled": True, "note": f"n{n}", "number": n, "R1": True, "routeAltitude": 2000,
            "speed": 790 + n, "TOS": 38565.5 + n, "type": "STPT", "velocityType": 3, "x": x, "y": y}


def f16_geo(n: int, lat: float, lon: float, alt: float, line: int = 1) -> dict[str, Any]:
    x, y = _xy("Syria", lat, lon)
    return {"alt": alt, "id": f"GEO_LINES3{n}", **{f"L{i}": i == line for i in range(1, 5)}, "note": "", "number": n, "x": x, "y": y}


def _comm() -> dict[str, Any]:
    """COMM shaped like the real file: channel keys in string order, integer MHz, modulation 1, mirror flags."""
    def radio(base: int) -> dict[str, Any]:
        return {f"Channel_{n}": {"freq": base + n, "modulation": 1} for n in sorted(range(1, 21), key=str)}
    return {"COMM1": radio(250), "COMM2": radio(120), "mirror_COMM1": True, "mirror_COMM2": False}


def f16() -> dict[str, Any]:
    mpd = {"CMDS": {"a": 1}, "DEST": [], "GEO_LINES": [f16_geo(i + 1, *LL[i]) for i in range(2)], "mirror_DEST": True,
           "NAV_PTS": [f16_stpt(i + 1, *LL[i]) for i in range(3)], "ROE": {"List": []}, "THREAT_PTS": [{"opaque": [1, 2]}],
           "terrain": "Syria", "VIPVRP": {"VIP_Number": 1}}
    return {"data": {"COLR": {"x": 4}, "COMM": _comm(), "ELINT": {}, "MPD": mpd, "name": "", "terrain": "Syria", "type": "F-16C_50"},
            "name": "", "type": "F-16C_50"}


def _f14_pt(lat: float, lon: float, elev: float, name: str | None = None) -> dict[str, Any]:
    x, y = _xy("Caucasus", lat, lon)
    p: dict[str, Any] = {"elev": elev, "lat": lat, "lon": lon}
    if name is not None:
        p.update(name=name, spd=0, tot="")
    return {**p, "x": x, "y": y}


def f14() -> dict[str, Any]:
    cau = [(43.1, 40.5, 197), (42.8, 41.1, 43), (42.9, 41.6, 1043), (43.2, 40.7, 7)]
    slots = [{"additional_points": [], "lines": [], "name": "", "route_as_line": False, "waypoints": []} for _ in range(12)]
    slots[0].update(name="A", waypoints=[_f14_pt(*cau[0], "w1"), _f14_pt(*cau[1], ""), _f14_pt(*cau[2], "w3")])
    slots[1].update(name="B", route_as_line=True, lines=[{"closed": True, "points": [_f14_pt(*c) for c in cau]}])
    slots[2]["additional_points"] = [{"opaque": 1}]
    return {"data": {"CMDS": {"k": 1}, "cartridge_name": "TEST", "JDAM": {}, "NAV": slots, "name": "F-14BU DTC", "TIS": {}, "type": "F-14BU"},
            "name": "", "type": "F-14BU"}


def _ah_pt(num: int, text: str, ident: int, lat: float, lon: float, alt: int) -> dict[str, Any]:
    x, y = _xy("Caucasus", lat, lon)
    return {"alt": alt, "id": ident, "note": "", "num": num, "text": text, "x": x, "y": y}


def _ah_radio(freq: float, mod: int) -> dict[str, Any]:
    return {"Encryption": 0, "Frequency": freq, "Modulation": mod}


def _ah_preset(n: int) -> dict[str, Any]:
    comms = {"FM1": _ah_radio(31.5, 1), "FM2": _ah_radio(31.5, 1), "HF_ALE": 1, "HF_Pre": 1, "HF_Rx": _ah_radio(2, 2),
             "HF_Tx": _ah_radio(2, 2), "UHF": _ah_radio(250 + n, 0), "VHF": _ah_radio(127.5, 0)}
    return {"COMMS": comms, "DoNotUploadTabData": False,
            "InitialMode": {"CallSign": f"PRE {n}", "DLNet": n < 9, "PrimaryFrequency": n if n < 5 else 0, "UnitID": f"PRESET {n}"}}


def _ah_radios() -> dict[str, Any]:
    ini = {k: {"Encryption": 0, "Frequency": f, "Mode": 0, "Modulation": m, "Preset": 1}
           for k, f, m in (("FM1", 31.5, 1), ("FM2", 31.5, 1), ("UHF", 305, 0), ("VHF", 127.5, 0))}
    ini["HF"] = {"Mode": 0, "Preset": 1, "RxEncryption": 0, "RxFrequency": 2, "RxModulation": 2, "TxEncryption": 0,
                "TxFrequency": 2, "TxModulation": 2}
    return {"FM": {"FM1_CUE_Frequency": 30, "FM1_Power": 0}, "IFF": {"Mode3A": {"Code": "0000", "Enable": True}},
            "InitialRadioSettings": ini, "UHF_GuardReceiver": True}


def ah64() -> dict[str, Any]:
    def mission() -> dict[str, Any]:
        grp = {"isEnabled": True, "POINTS": []}
        pts = {"CTRLM": dict(grp, POINTS=[]), "TGT": dict(grp), "WPTHZ": dict(grp)}
        return {"ADF": {"isEnabled": False}, "Areas": [], "Lines": [], "Points": pts,
                "Routes": [{"isEnabled": False, "Name": "ALPHA", "POINTS": [{"opaque": 1}]}], "Zones": {"NFZ": [], "PFZ": []}}
    m1, m2 = mission(), mission()
    m1["Points"]["TGT"]["POINTS"] = [_ah_pt(1, "T01", 12, 43.0, 41.0, 767)]
    m1["Points"]["WPTHZ"]["POINTS"] = [_ah_pt(1, "W01", 1, 43.1, 41.2, 586), _ah_pt(2, "W02", 1, 43.2, 41.5, 709)]
    nav = {"MissionFile": 1, "Mission_1": m1, "Mission_2": m2}
    return {"data": {"IDM": [], "NAV": nav, "name": "", "Presets": {"COMM": [_ah_preset(n) for n in range(1, 11)], "MPS": {"x": 1}},
                     "Radios": _ah_radios(), "Radios_HF": [], "terrain": "Caucasus", "type": "AH-64D_BLK_II"}, "name": "", "type": "AH-64D_BLK_II"}


def synth_raw(aircraft: str) -> bytes:
    return write_json({"F-16C_50": f16, "F-14BU": f14, "AH-64D_BLK_II": ah64}[aircraft]())
