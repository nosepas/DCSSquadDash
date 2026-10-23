"""Warnings travel to central in the heartbeat: they must not reveal the Windows user name."""
from __future__ import annotations

from fox3_agent.sources.foothold import FootholdSource


def test_missing_folder_warning_hides_the_user_name():
    src = FootholdSource(r"C:\Users\alice\Saved Games\DCS.server\Missions\Saves")
    assert src.poll() == []
    [warning] = src.warnings()
    assert warning.code == "FOOTHOLD_FOLDER_MISSING"
    assert "alice" not in warning.message and "<user>" in warning.message and "Saves" in warning.message
