"""F-16C_50 radios: data.COMM.COMM1 (UHF) / COMM2 (VHF), each with Channel_1..Channel_20 = {freq, modulation}.

Neutral: radios.radios[] = {id, label, kind: "channelised", channels: [{channel, frequency_mhz, extra}], extra}.
Exposed: the frequency in decimal MHz. UNVERIFIED: the sample only has integer MHz and DCS may not accept fractions.
Preserved in `extra`, not for the UI: each channel's `modulation` (value 1 everywhere; meaning unknown) and radio
`mirror` (DCS `mirror_COMM1/2`, meaning unknown). Channels missing from the model are left as in the template.
"""
from __future__ import annotations

import re
from copy import deepcopy
from typing import Any

from . import radio_fields as rf

RADIOS = {"COMM1": "UHF", "COMM2": "VHF"}
MAX_CHANNELS = 20
_CH = {"frequency_mhz": "freq"}


def to_model(template: dict[str, Any]) -> tuple[dict[str, Any] | None, list[str]]:
    comm = template["data"].get("COMM")
    if not isinstance(comm, dict):
        return None, ["data: missing key 'COMM'; radios are not editable"]
    out, warns = [], []
    for rid, band in RADIOS.items():
        src = comm.get(rid)
        if not isinstance(src, dict):
            warns.append(f"COMM: missing radio {rid}")
            continue
        chans = []
        for key, ch in src.items():
            m = re.fullmatch(r"Channel_(\d+)", key)
            if m and isinstance(ch, dict):
                chans.append({"channel": int(m[1]), **rf.read(ch, _CH)})
        radio: dict[str, Any] = {"id": rid, "label": f"{rid} ({band})", "kind": "channelised",
                                 "channels": sorted(chans, key=lambda c: c["channel"])}
        if f"mirror_{rid}" in comm:
            radio["extra"] = {"mirror": comm[f"mirror_{rid}"]}
        out.append(radio)
    return {"radios": out}, warns


def apply(radios: dict[str, Any], out: dict[str, Any]) -> None:
    comm = rf.section(out["data"], "COMM")
    for radio in radios.get("radios", []):
        rid = radio["id"]
        dst = comm.setdefault(rid, {})
        for ch in radio.get("channels", []):
            key = f"Channel_{ch['channel']}"
            if key not in dst:  # new channel: start from a sibling so unknown keys (modulation) get a real default
                sibling = next((v for k, v in dst.items() if k.startswith("Channel_")), {})
                dst[key] = deepcopy(sibling)
            rf.write(dst[key], ch, _CH)
        if "mirror" in (radio.get("extra") or {}):
            rf.put(comm, f"mirror_{rid}", radio["extra"]["mirror"])
