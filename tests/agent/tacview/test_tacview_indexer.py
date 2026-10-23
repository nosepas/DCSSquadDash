import pytest
from tacview_samples import BASIC, HEADER, acmi, write_plain, write_zip

from fox3_agent.sources.tacview import index_file
from fox3_agent.sources.tacview.errors import AcmiCancelledError, AcmiFormatError, AcmiUnsupportedError
from fox3_agent.sources.tacview.props import map_side, split_props


def by_pilot(idx):
    return {a.pilot: a for a in idx.appearances}


def test_basic_index(tmp_path):
    idx = index_file(write_plain(tmp_path / "a.acmi", BASIC))
    assert idx.reference_time == "2024-05-01T18:00:00Z"
    assert (idx.title, idx.data_source) == ("Test mission", "DCS 2.9")
    assert idx.duration_s == 60.25 and idx.complete and idx.malformed_lines == 0
    a = by_pilot(idx)
    assert set(a) == {"Viper 1-1", "Apache"}               # the T-72 has no Pilot
    v = a["Viper 1-1"]
    assert (v.aircraft, v.coalition, v.group, v.object_id) == ("F-16C-52", "blue", "Uzi", "3000100")
    assert (v.first_offset_s, v.last_offset_s) == (0.0, 60.25)
    ap = a["Apache"]
    assert ap.coalition == "red" and ap.last_offset_s == 30.0   # last offset = removal time


def test_zip_equals_plain(tmp_path):
    a = index_file(write_plain(tmp_path / "a.acmi", BASIC))
    b = index_file(write_zip(tmp_path / "b.zip.acmi", BASIC))
    assert a == b


def test_bom_crlf_tolerated(tmp_path):
    text = BASIC.replace("\n", "\r\n")
    p = tmp_path / "a.acmi"
    p.write_bytes(b"\xef\xbb\xbf" + text.encode())
    assert index_file(p).duration_s == 60.25


def test_respawn_same_pilot_separate_appearances(tmp_path):
    t = acmi("#0", "100,Pilot=Joe,Name=A-10C", "#50", "-100", "#80", "200,Pilot=Joe,Name=A-10C", "#120", "200,T=1")
    idx = index_file(write_plain(tmp_path / "a.acmi", t))
    assert [(a.object_id, a.first_offset_s, a.last_offset_s) for a in idx.appearances] == [("100", 0, 50), ("200", 80, 120)]


def test_pilot_defined_on_later_line(tmp_path):
    t = acmi("#0", "100,Name=Su-25T,Type=Air", "#10", "100,Pilot=Late,Color=Red", "#20", "100,T=1")
    a = index_file(write_plain(tmp_path / "a.acmi", t)).appearances[0]
    assert (a.pilot, a.aircraft, a.coalition, a.first_offset_s, a.last_offset_s) == ("Late", None, "red", 10, 20)


def test_pilot_change_on_same_object_opens_new_appearance(tmp_path):
    t = acmi("#0", "100,Pilot=One", "#5", "100,Pilot=Two", "#9", "100,T=1")
    idx = index_file(write_plain(tmp_path / "a.acmi", t))
    assert [(a.pilot, a.first_offset_s) for a in idx.appearances] == [("One", 0), ("Two", 5)]


def test_escaped_comma_in_pilot_and_title(tmp_path):
    t = acmi("#0", r"100,Pilot=Doe\, John,Name=F-14B,Group=Grp", header=HEADER.replace("Test mission", r"A\, B"))
    idx = index_file(write_plain(tmp_path / "a.acmi", t))
    assert idx.appearances[0].pilot == "Doe, John" and idx.appearances[0].group == "Grp"
    assert idx.title == "A, B"


def test_split_props_escapes():
    assert split_props(rb"1,a=x\,y,b=2") == [b"1", rb"a=x\,y", b"b=2"]
    assert split_props(b"1,a=x\\\\,b=2") == [b"1", b"a=x\\\\", b"b=2"]      # escaped backslash then a real comma


def test_odd_values_ignored(tmp_path):
    t = acmi("#0", "100,Pilot=", "101,Pilot=   ", "102,Pilot", "103,Pilot=Ok", "zz,Pilot=BadId")
    idx = index_file(write_plain(tmp_path / "a.acmi", t))
    assert [a.pilot for a in idx.appearances] == ["Ok"]
    assert idx.malformed_lines >= 1


def test_malformed_lines_skipped_and_counted(tmp_path):
    t = acmi("#0", "100,Pilot=A", "#abc", "garbage line", "#nan", "#5", "100,T=1", "\x00\x01,,,,", "#9", "100,T=2")
    idx = index_file(write_plain(tmp_path / "a.acmi", t))
    assert idx.malformed_lines == 3
    assert idx.appearances[0].last_offset_s == 9


def test_truncated_file_partial_index(tmp_path):
    p = write_plain(tmp_path / "a.acmi", BASIC + "#99\n3000100,T=1|2|")
    idx = index_file(p)
    assert idx.complete is False
    assert by_pilot(idx)["Viper 1-1"].last_offset_s == 60.25      # the partial line is not used


def test_zip_damaged_midstream_partial_index(tmp_path):
    big = acmi("#0", "100,Pilot=A", *[x for i in range(1, 3000) for x in (f"#{i}", f"100,T={i}|1|1,Heading={i * 7 % 360}")])
    data = bytearray(write_zip(tmp_path / "a.zip.acmi", big).read_bytes())
    mid = len(data) // 2
    data[mid:mid + 40] = bytes([255]) * 40
    bad = tmp_path / "bad.zip.acmi"
    bad.write_bytes(bytes(data))
    idx = index_file(bad)
    assert idx.complete is False       # usable (possibly empty) partial index, no exception


def test_zip_without_central_directory_fails(tmp_path):
    data = write_zip(tmp_path / "a.zip.acmi", BASIC).read_bytes()
    cut = tmp_path / "cut.zip.acmi"
    cut.write_bytes(data[: len(data) // 2])
    with pytest.raises(AcmiFormatError):
        index_file(cut)


def test_out_of_order_frames(tmp_path):
    t = acmi("#50", "100,Pilot=A", "#10", "100,T=1", "#70", "100,T=2", "#30", "100,T=3")
    a = index_file(write_plain(tmp_path / "a.acmi", t)).appearances[0]
    assert (a.first_offset_s, a.last_offset_s) == (10, 70)


def test_comments_and_events_ignored(tmp_path):
    t = acmi("//comment Pilot=X", "#0", "0,Event=Message|100|Pilot=Hacker", "100,Pilot=Real")
    assert [a.pilot for a in index_file(write_plain(tmp_path / "a.acmi", t)).appearances] == ["Real"]


def test_no_frames_duration_none(tmp_path):
    assert index_file(write_plain(tmp_path / "a.acmi", HEADER)).duration_s is None


def test_not_acmi_rejected(tmp_path):
    with pytest.raises(AcmiFormatError):
        index_file(write_plain(tmp_path / "a.acmi", "hello\nworld\n"))


def test_7z_rejected(tmp_path):
    p = tmp_path / "a.acmi"
    p.write_bytes(bytes([0x37, 0x7A, 0xBC, 0xAF, 0x27, 0x1C]) + b"0" * 40)
    with pytest.raises(AcmiUnsupportedError):
        index_file(p)


def test_max_objects_bound(tmp_path):
    t = acmi("#0", *[f"{i:x},Pilot=P{i}" for i in range(1, 20)])
    idx = index_file(write_plain(tmp_path / "a.acmi", t), max_objects=5)
    assert len(idx.appearances) == 5 and idx.dropped_objects == 14


def test_cancel(tmp_path):
    t = acmi("#0", "100,Pilot=A", *[f"#{i}" for i in range(1, 600)])
    with pytest.raises(AcmiCancelledError):
        index_file(write_plain(tmp_path / "a.acmi", t), cancel=lambda: True)


def test_side_mapping_rule():
    assert map_side("Red", "Allies") == "red"                  # Color wins
    assert map_side("Violet", "Blue") == "blue"                # unmapped colour falls back to Coalition
    assert map_side(None, "Neutral") == "neutral"
    assert map_side(None, "Enemies") == "unknown" and map_side(None, "Allies") == "unknown"
    assert map_side(None, None) == "unknown"
    assert map_side("Green", "Allies", {"allies": "blue"}) == "blue"   # configurable override
