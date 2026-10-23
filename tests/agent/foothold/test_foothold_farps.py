from foothold_samples import full_file, write_saves

from fox3_agent.sources.foothold import FootholdSource
from fox3_agent.sources.foothold.farps import parse_farps
from fox3_central.core.validation import Validators

OLD = "FARP COORDINATES\n1;CTLD FARP London;57367.292969;-54940.789062;\n2;CTLD FARP Paris;80000.0;-30000.0;\n"
NEW = "seq;name;x;y;zell;latitude;longitude;\n1;CTLD FARP Baghdad;200000.000000;400.000000;;33.312805;44.361488;\n"


def test_old_layout_has_dcs_coordinates_only():
    assert parse_farps(OLD) == [
        {"name": "CTLD FARP London", "position": {"x": 57367.292969, "y": -54940.789062}},
        {"name": "CTLD FARP Paris", "position": {"x": 80000.0, "y": -30000.0}}]


def test_new_layout_carries_lat_lon_too():
    farp = parse_farps(NEW)[0]
    assert farp["geo"] == {"lat": 33.312805, "lon": 44.361488} and farp["position"] == {"x": 200000.0, "y": 400.0}


def test_bad_rows_are_skipped_not_guessed():
    text = "seq;name;x;y;latitude;longitude\n1;;1;2;;\n2;NoCoords;;;;\n3;BadLat;1;2;99;10\n4;Good;nan;inf;40.5;3.5\n"
    assert parse_farps(text) == [{"name": "BadLat", "position": {"x": 1.0, "y": 2.0}}, {"name": "Good", "geo": {"lat": 40.5, "lon": 3.5}}]
    assert parse_farps("") == [] and parse_farps("garbage") == []


def test_source_sends_farps_and_notices_a_change_in_the_csv_only(tmp_path):
    persistence = write_saves(tmp_path, full_file())
    csv = persistence.with_name(persistence.stem + "_CTLD_FARPS.csv")
    src = FootholdSource(persistence.parent)
    first = src.poll()
    assert "farps" not in first[0].payload  # no csv yet
    csv.write_text(OLD, "utf-8")
    second = src.poll()  # the persistence file did not change, only the FARP list did
    assert [f["name"] for f in second[0].payload["farps"]] == ["CTLD FARP London", "CTLD FARP Paris"]
    assert src.poll() == []  # nothing new
    csv.write_text(OLD + "3;CTLD FARP Rome;1.0;2.0;\n", "utf-8")
    assert len(src.poll()[0].payload["farps"]) == 3
    assert Validators(__import__("pathlib").Path("contracts/schemas")).errors("foothold_state", second[0].payload) == []
