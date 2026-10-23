import sqlite3
import time

import pytest
from dcsbot_fakes import SERVER, UCID1, UCID2, FakeBot
from foothold_samples import IDENTITY_STATS, full_file, write_saves
from tacview_samples import BASIC, acmi, age, write_plain, write_zip

from fox3_agent import cli
from fox3_agent.diagnose.foothold_csv import mask_row, outline_csv
from fox3_agent.diagnose.runner import build_context, run_diagnose
from fox3_agent.diagnose.s_foothold import status_kind
from fox3_agent.diagnose.tacview_stats import collect, looks_ai
from fox3_agent.scaffold import write_agent_toml

# every name that exists in the synthetic fixtures and must never reach the report
SECRET_NAMES = ["Alpha", "Bravo", "Charlie", "Delta", "Mitch", "APOLLO", "Tomy10", "Intercept Bombers", "Bombers north",
                "Viper 1-1", "Apache", "Uzi", "FarpSecretName", "TOPSECRET", "1.2.3.4", "Pilot1", "Pilot2", "Chevy",
                "FOX3 Test", UCID1, UCID2, "SuperSecretApiKey", "SecretDbPass"]
CSV_NEW = "seq;name;x;y;zell;latitude;longitude;\n1;FarpSecretName;-123456.789;234567.5;1.0;43.1234567;40.7654321;\n"


def assert_clean(text: str) -> None:
    for name in SECRET_NAMES:
        assert name not in text, f"{name!r} leaked into the report"


def recordings(tmp_path):
    rec = tmp_path / "tv"
    old = write_plain(rec / "Tacview-old.txt.acmi", BASIC)
    new = write_zip(rec / "Tacview-new.zip.acmi", BASIC)
    wip = write_plain(rec / "Tacview-wip.txt.acmi", BASIC)
    now = time.time()
    age(old, 7000, now)
    age(new, 600, now)
    age(wip, 5, now)
    write_plain(rec / "Tacview-wip.txt.acmi.crdownload", "x")
    return rec


def ctx_for(tmp_path, **kw):
    cfg = write_agent_toml(tmp_path / "cfg", "https://central.example.org")
    ctx = build_context(cfg, kw.pop("saves", None), kw.pop("tv", None), home=tmp_path / "home")
    for k, v in kw.items():
        setattr(ctx, k, v)
    return ctx


# --- Foothold -------------------------------------------------------------------------------------------------------------------
def test_foothold_section_reports_structure_without_names(tmp_path):
    saves = write_saves(tmp_path, full_file(IDENTITY_STATS)).parent
    (saves / "foothold.status").write_text(r"C:\Users\someone\Saved Games\DCS\Missions\Saves\Foothold_Caucasus.lua", "utf-8")
    (saves / "Foothold_Caucasus_CTLD_FARPS.csv").write_text(CSV_NEW, "utf-8")
    text = run_diagnose(ctx_for(tmp_path, saves=saves))
    assert_clean(text)
    assert "Foothold_Caucasus.lua" in text
    assert "absolute (Windows drive path), uses backslashes" in text
    assert "its file name equals the located file: True" in text
    assert "columns / data rows: 7 / 1" in text and "latitude+longitude columns: True" in text
    assert "first row (masked): 1.0;<name>;-123500;234600;1.0;43.1;40.8;" in text
    assert "at_risk derivable: True" in text and "format_notes:" in text
    assert "someone" not in text


def test_foothold_missing_folder_is_flagged_and_report_continues(tmp_path):
    text = run_diagnose(ctx_for(tmp_path, saves=tmp_path / "nope", tv=tmp_path / "nope2"))
    assert "Foothold saves folder does not exist" in text and "## 4. Tacview" in text and "## Unexpected" in text


def test_foothold_garbage_file_reports_parser_failure(tmp_path):
    saves = write_saves(tmp_path, "this is { not lua").parent
    text = run_diagnose(ctx_for(tmp_path, saves=saves))
    assert "our parser cannot read the file" in text and "## What to send" in text


def test_csv_outline_old_layout_and_masking():
    o = outline_csv("FARP COORDINATES\n1;Hidden Name;100.55;-20.0;\n2;Other;1;2;\n")
    assert (o.header, o.rows, o.has_lat_lon) == ("FARP COORDINATES", 2, False)
    assert o.first_row == "1.0;<name>;100.5;-20.0;" or o.first_row == "1.0;<name>;100.6;-20.0;"
    assert "Hidden" not in str(o)
    assert mask_row("a;12345.6;x") == "<name>;12300;<name>"
    assert outline_csv("").rows == 0


def test_csv_header_with_unexpected_content_is_masked():
    o = outline_csv("seq;name;SecretPlayer99;\n1;x;2;\n")
    assert o.header == "<name>;<name>;<name>;"             # contains a digit: not a plain header, only its shape is shown
    assert outline_csv("seq;name;latitude;" + chr(10)).header == "seq;name;latitude;"
    o2 = outline_csv("seq;name;Player 99 secret;\n1;x;2;\n")
    assert "Player" not in (o2.header or "")


@pytest.mark.parametrize("entry, expect", [
    ("Foothold_X.lua", "relative, uses no separators"),
    ("Missions/Saves/Foothold_X.lua", "relative, uses forward slashes"),
    ("D:/DCS/Foothold_X.lua", "absolute (Windows drive path), uses forward slashes"),
    ("//srv/share/x.lua", "absolute (network/UNC)"),
    ("/home/x/y.lua", "absolute (POSIX)"),
])
def test_status_kind_is_generic(entry, expect):
    out = status_kind(entry)
    assert expect in out and "X.lua" not in out and "srv" not in out


# --- Tacview --------------------------------------------------------------------------------------------------------------------
def test_tacview_section_no_pilot_names(tmp_path):
    rec = recordings(tmp_path)
    text = run_diagnose(ctx_for(tmp_path, tv=rec))
    assert_clean(text)
    assert "newest 3 recordings (of 3)" in text and "zip=True" in text
    assert "newest finished recording: Tacview-new.zip.acmi" in text
    assert "objects with a Pilot property: 2" in text
    assert "Color among Pilot objects: {'Blue': 1, 'Red': 1}" in text
    assert "Coalition among Pilot objects: {'Allies': 1, 'Enemies': 1}" in text
    assert "<pilot 1>" in text and "indexer throughput" in text and "MB/s" in text
    assert "Test mission" in text and "2024-05-01T18:00:00Z" in text
    assert "temporary sync/download files ignored: 1" in text


def test_tacview_zip_members_listed(tmp_path):
    rec = tmp_path / "tv"
    p = write_zip(rec / "a.zip.acmi", BASIC, member="inner.txt.acmi")
    age(p, 7000, time.time())
    text = run_diagnose(ctx_for(tmp_path, tv=rec))
    assert "zip members: 1: inner.txt.acmi" in text


def test_tacview_only_fresh_recordings_not_indexed(tmp_path):
    rec = tmp_path / "tv"
    write_plain(rec / "fresh.acmi", BASIC)
    text = run_diagnose(ctx_for(tmp_path, tv=rec))
    assert "newer than the settle time" in text and "objects (distinct ids)" not in text


def test_tacview_stats_counts_and_ai_heuristic(tmp_path):
    body = acmi("#0", "10,T=1|2|3,Type=Air+FixedWing,Pilot=Aerial-1-1,Group=Aerial-1,Color=Red",
                "11,T=1|2|3,Type=Air+Rotary,Pilot=Human Name,Group=Other,Coalition=Enemies",
                "12,T=1|2|3,Type=Ground+Vehicle", "#5", "11,Color=Blue")
    st = collect(write_plain(tmp_path / "x.acmi", body))
    assert (st.objects, st.pilot_objects, st.ai_like) == (3, 2, 1)
    assert st.colors == {"Red": 1, "Blue": 1} and st.coalitions == {"<absent>": 1, "Enemies": 1}
    assert st.all_types["Ground+Vehicle"] == 1
    assert looks_ai("Aerial-3-2", None) and looks_ai("Ground-4", "x") and looks_ai("Same", "Same") and not looks_ai("Viper", "Other")


def test_tacview_missing_folder_with_drive_hint(tmp_path):
    from pathlib import PureWindowsPath

    text = run_diagnose(ctx_for(tmp_path, tv=tmp_path / "Google Drive" / "x"))
    assert "-ServiceUser" in text and str(PureWindowsPath("x")) == "x"


# --- versions / config / pairing ----------------------------------------------------------------------------------------------
def test_versions_config_and_pairing_sections(tmp_path):
    text = run_diagnose(ctx_for(tmp_path))
    assert "fox3-agent: 0.1.0" in text and "central host: https://central.example.org" in text
    assert "paired: no" in text and "dcsserverbot (local file): not configured" in text


def test_missing_config_does_not_stop_the_report(tmp_path):
    text = run_diagnose(build_context(tmp_path / "missing.toml", None, None, home=tmp_path / "home"))
    assert "config not loaded" in text and "## 2. Discover" in text and "## What to send" in text


def test_section_exception_is_contained(tmp_path, monkeypatch):
    def boom(ctx, sec):
        raise RuntimeError(r"failed reading C:\Users\bob\x " + UCID1)

    monkeypatch.setattr("fox3_agent.diagnose.runner.discover", boom)
    text = run_diagnose(ctx_for(tmp_path))
    assert "section failed: RuntimeError" in text and "bob" not in text and UCID1 not in text and "## 3. Foothold" in text


# --- DCSServerBot ---------------------------------------------------------------------------------------------------------------
def bot_ctx(tmp_path, bot, db=False, env=None, sub="cfg"):
    cfg = write_agent_toml(tmp_path / sub, "https://central.example.org", dcsbot_api_key_env="BOT_KEY")
    extra = '\nrest_enabled = true\nrest_url = "http://localhost:9876"\nserver_name = "FOX3 Test"\n'
    if db:
        extra += 'db_enabled = true\ndb_url_env = "BOT_DB"\n'
    cfg.write_text(cfg.read_text("utf-8") + extra, "utf-8")
    ctx = build_context(cfg, None, None, home=tmp_path / "home")
    ctx.environ = {"BOT_KEY": "SuperSecretApiKey", **(env or {})}
    ctx.extras["rest_transport"] = bot.transport()
    return ctx


def test_dcsbot_rest_probe_structure_only(tmp_path):
    bot = FakeBot([SERVER], api_key="SuperSecretApiKey")
    text = run_diagnose(bot_ctx(tmp_path, bot))
    assert_clean(text)
    assert "GET /servers: HTTP 200" in text and "mission.theatre present: True" in text
    assert "exact `side` values seen: {\"'blue'\": 1, \"'RED'\": 1}" in text
    assert "sensitive keys present (values not shown): password, address" in text
    assert "weather keys: clouds_base, pressure" in text
    assert [r.headers.get("X-API-Key") for r in bot.requests] == ["SuperSecretApiKey"]


def test_dcsbot_rest_wrong_key_reported_without_key(tmp_path):
    text = run_diagnose(bot_ctx(tmp_path, FakeBot([SERVER], api_key="other")))
    assert "rejected the credentials" in text and "HTTP 403" in text
    assert_clean(text)


def test_dcsbot_odd_side_values_are_flagged(tmp_path):
    server = {**SERVER, "players": [{"nick": "Pilot1", "side": 7}]}
    text = run_diagnose(bot_ctx(tmp_path, FakeBot([server], api_key="SuperSecretApiKey")))
    assert "outside blue/red/neutral" in text and "Pilot1" not in text


def make_db(path):
    cn = sqlite3.connect(path)
    cn.executescript("""
        CREATE TABLE missions (id INTEGER PRIMARY KEY, server_name TEXT);
        CREATE TABLE players (ucid TEXT, name TEXT, last_seen TEXT);
        CREATE TABLE missionstats (id INTEGER PRIMARY KEY, mission_id INT, event TEXT, init_id TEXT, init_side TEXT, init_type TEXT,
            target_id TEXT, target_side TEXT, target_type TEXT, weapon TEXT, place TEXT, time TEXT);
        INSERT INTO missions VALUES (1, 'FOX3 Test');
        INSERT INTO players VALUES ('aabbccddeeff00112233445566778899', 'Pilot1', '2025-01-01');
    """)
    rows = [(1, "S_EVENT_KILL", UCID1, "2", None), (1, "S_EVENT_KILL", UCID1, "2", None), (1, "S_EVENT_TAKEOFF", UCID2, "1", None),
            (1, "S_EVENT_WEIRD", None, "5", None)]
    for i, (m, ev, uc, side, _) in enumerate(rows, 1):
        cn.execute("INSERT INTO missionstats VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (i, m, ev, uc, side, "F-16C", None, None, None, None, None,
                                                                            "2025-01-01 10:00:00"))
    cn.commit()
    cn.close()


def test_dcsbot_db_probe_schema_and_enumerations_only(tmp_path):
    db = tmp_path / "bot.sqlite"
    make_db(db)
    text = run_diagnose(bot_ctx(tmp_path, FakeBot([SERVER], api_key="SuperSecretApiKey"), db=True, env={"BOT_DB": f"sqlite:///{db.as_posix()}"}))
    assert_clean(text)
    assert "tables found among missionstats/missions/players/statistics: missionstats, missions, players" in text
    assert "rows in missionstats: 4" in text and "max(id): 4" in text
    assert "S_EVENT_KILL': 2" in text and "S_EVENT_WEIRD" in text
    assert "distinct init_side values: {'2': 2, '1': 1, '5': 1}" in text
    assert "init_side values our mapper reads as 'unknown': 5" in text
    assert "missionstats columns: id, mission_id, event" in text


def test_dcsbot_db_missing_env_and_bad_url_are_contained(tmp_path):
    bot = FakeBot([SERVER], api_key="SuperSecretApiKey")
    assert "environment variable 'BOT_DB' is empty" in run_diagnose(bot_ctx(tmp_path, bot, db=True))
    text = run_diagnose(bot_ctx(tmp_path, bot, db=True, sub="cfg2", env={"BOT_DB": "sqlite:////nonexistent_dir_zz/none/x.sqlite"}))
    assert "## Unexpected" in text and "SecretDbPass" not in text


# --- CLI ------------------------------------------------------------------------------------------------------------------------
def test_cli_diagnose_prints_and_writes_file(tmp_path, capsys):
    cfg = write_agent_toml(tmp_path / "cfg", "https://central.example.org")
    out = tmp_path / "report.txt"
    rc = cli.main(["diagnose", "--config", str(cfg), "--home", str(tmp_path / "home"), "--out", str(out)])
    printed = capsys.readouterr().out
    assert rc == 0 and out.read_text("utf-8") in printed and "FOX3 agent diagnose report" in printed
