import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from fox3_agent.setup import scheduler
from fox3_agent.setup.taskxml import NS, agent_task_xml, build_task_xml

Q = "{" + NS + "}"


def parse(xml: bytes) -> ET.Element:
    return ET.fromstring(xml.decode("utf-16"))


def test_xml_is_utf16_and_complete():
    xml = agent_task_xml(Path(r"C:\Users\a\FOX3Agent\fox3-agent.exe"), Path(r"C:\Users\a\FOX3Agent\agent.toml"), r"PC\bob")
    assert xml[:2] in (b"\xff\xfe", b"\xfe\xff")
    root = parse(xml)
    assert root.find(f"{Q}Triggers/{Q}LogonTrigger/{Q}UserId").text == r"PC\bob"
    assert root.find(f"{Q}Principals/{Q}Principal/{Q}RunLevel").text == "LeastPrivilege"
    s = root.find(f"{Q}Settings")
    assert s.find(f"{Q}Hidden").text == "true"
    assert s.find(f"{Q}ExecutionTimeLimit").text == "PT0S"
    assert s.find(f"{Q}MultipleInstancesPolicy").text == "IgnoreNew"
    assert s.find(f"{Q}RestartOnFailure/{Q}Interval").text == "PT1M"
    assert s.find(f"{Q}RestartOnFailure/{Q}Count").text == "999"
    ex = root.find(f"{Q}Actions/{Q}Exec")
    assert ex.find(f"{Q}Command").text.endswith("fox3-agent.exe")
    assert ex.find(f"{Q}Arguments").text == r'run --config "C:\Users\a\FOX3Agent\agent.toml"'


def test_hostile_names_are_escaped():
    user = 'EVIL\\<x>&"\'</UserId><Exec>'
    root = parse(build_task_xml("C:\\a&b\\<c>.exe", 'run --config "x"', user))
    assert root.find(f"{Q}Principals/{Q}Principal/{Q}UserId").text == user
    assert len(root.findall(f"{Q}Actions/{Q}Exec")) == 1


def test_quote_in_path_and_nul_rejected():
    with pytest.raises(ValueError):
        agent_task_xml(Path('C:\\a"b\\x.exe'), Path("C:\\c.toml"), "u")
    with pytest.raises(ValueError):
        build_task_xml("a\x00b", "", "u")


def test_schtasks_argument_lists(calls):
    ok, _ = scheduler.create_task(b"<x/>")
    assert ok
    c = calls[0]
    assert c[:4] == ["schtasks", "/Create", "/TN", "FOX3 Agent"] and c[4] == "/XML" and c[6] == "/F"
    assert not Path(c[5]).exists()  # temp file removed
    scheduler.run_task()
    scheduler.end_task()
    scheduler.delete_task()
    assert calls[1:4] == [["schtasks", "/Run", "/TN", "FOX3 Agent"], ["schtasks", "/End", "/TN", "FOX3 Agent"],
                          ["schtasks", "/Delete", "/TN", "FOX3 Agent", "/F"]]
    info = scheduler.query_task()
    assert calls[4] == ["schtasks", "/Query", "/TN", "FOX3 Agent", "/FO", "CSV", "/V", "/NH"]
    assert info.exists and info.status == "Ready" and info.last_result == "0"


def test_kill_targets_exact_path_via_env(calls):
    scheduler.kill_exe(Path(r"C:\x\fox3-agent.exe"))
    assert calls[0][0] == "powershell" and "C:" not in " ".join(calls[0])  # path only travels in the environment
