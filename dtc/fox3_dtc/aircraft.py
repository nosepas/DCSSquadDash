"""Aircraft support table: what each module can edit, what exists but is not modelled, and known limits."""
from __future__ import annotations

from dataclasses import dataclass, field

from fox3_common import geo


@dataclass(frozen=True)
class AircraftInfo:
    id: str
    label: str
    enabled: bool
    supports: tuple[str, ...] = ()
    unsupported: tuple[str, ...] = ()
    limits: dict[str, int | None] = field(default_factory=dict)
    notes: tuple[str, ...] = ()


def terrains() -> dict[str, str | None]:
    """Allowed terrains (every calibrated map in fox3_common.geo.PARAMS) -> calibration level (exact|plausible|airports)."""
    return {t: geo.calibration(t) for t in geo.PARAMS}


AIRCRAFT: dict[str, AircraftInfo] = {
    "F-16C_50": AircraftInfo(
        "F-16C_50", "F-16C Block 50", True,
        supports=("waypoints", "lines", "radios"),
        unsupported=("threat_points", "destinations"),
        limits={"waypoints": 25, "lines": 4, "radio_channels": 20},
        notes=("Steerpoint limit 25 is from the owner's description, not verified in game.",
               "Lines: GEO_LINES entries carry flags L1..L4; each model line = one flag. Per-line point limit unknown, not enforced.",
               "THREAT_PTS and DEST are empty in the sample: preserved untouched, not editable.",
               "radios.radios[] = COMM1 (UHF) / COMM2 (VHF), channels 1-20 {channel, frequency_mhz} (decimal MHz).",
               "Fractional MHz (e.g. 251.075) is NOT confirmed to be accepted by DCS: the sample only has integers.",
               "Channel modulation (always 1 in the sample) and mirror_COMM1/2 are preserved in `extra`, meaning unknown.",
               "Band ranges are warnings only (commonly documented, not verified in game)."),
    ),
    "F-14BU": AircraftInfo(
        "F-14BU", "F-14B Upgrade", True,
        supports=("routes", "lines"),
        unsupported=("additional_points", "radios"),
        limits={"routes": 12, "waypoints_per_route": None},
        notes=("The file has no terrain: the user must choose it (lat/lon and x/y are both stored).",
               "additional_points are empty in the samples: preserved untouched, not editable.",
               "Radios: the F-14BU .dtc holds no radio data (keys: CMDS, JDAM, NAV, TIS, ...); a model with `radios` is rejected."),
    ),
    "AH-64D_BLK_II": AircraftInfo(
        "AH-64D_BLK_II", "AH-64D Apache Longbow Block II", True,
        supports=("waypoints", "radios"),
        unsupported=("routes", "zones", "areas", "lines", "adf", "iff", "hf_ale", "fm_cue"),
        limits={"waypoints": None, "presets": 10},
        notes=("Waypoints are grouped by kind (CTRLM/TGT/WPTHZ) and mission (1/2); limits unknown, not enforced.",
               "No sample has CTRLM points: adding CTRLM points needs a .dtc that already contains one.",
               "Routes, Zones, Areas, Lines are empty in the sample: preserved untouched, not editable.",
               "radios = {presets[10], initial, guard_receiver}. Preset: {index, call_sign, unit_id, primary_frequency, dl_net, radios}.",
               "Preset radios (FM1, FM2, UHF, VHF, HF_RX, HF_TX): {frequency_mhz, modulation, encryption}, frequencies in decimal MHz.",
               "initial: FM1/FM2/UHF/VHF {+mode, preset}, HF {mode, preset, rx, tx}. Modulation is the raw DCS code "
               "(UHF/VHF 0, FM 1, HF 2 seen; HF meaning unverified).",
               "Preserved untouched, not editable: HF_ALE/HF_Pre (preset extra), Radios.IFF, Radios.FM (CUE frequencies/power), Radios_HF."),
    ),
    "FA-18C_hornet": AircraftInfo("FA-18C_hornet", "F/A-18C Hornet", False, notes=("Reserved: no sample file exists, schema not known.",)),
}
