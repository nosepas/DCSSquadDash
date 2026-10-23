"""Task Scheduler XML for the per-user `FOX3 Agent` task (no administrator rights needed)."""
from __future__ import annotations

import os
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "http://schemas.microsoft.com/windows/2004/02/mit/task"
TASK_NAME = "FOX3 Agent"


def current_user() -> str:
    domain, name = os.environ.get("USERDOMAIN", ""), os.environ.get("USERNAME", "")
    if not name:
        raise ValueError("cannot determine the current Windows user")
    return f"{domain}\\{name}" if domain else name


def _add(parent: ET.Element, tag: str, text: str | None = None) -> ET.Element:
    el = ET.SubElement(parent, f"{{{NS}}}{tag}")
    if text is not None:
        el.text = text
    return el


def build_task_xml(command: str, arguments: str, user: str, description: str = "FOX3 agent for DCS") -> bytes:
    """UTF-16 XML (with BOM). ElementTree escapes every text value, so hostile names cannot break the document."""
    if "\x00" in command + arguments + user:
        raise ValueError("NUL in task field")
    ET.register_namespace("", NS)
    task = ET.Element(f"{{{NS}}}Task", {"version": "1.2"})
    _add(_add(task, "RegistrationInfo"), "Description", description)
    logon = _add(_add(task, "Triggers"), "LogonTrigger")
    _add(logon, "Enabled", "true")
    _add(logon, "UserId", user)
    pr = ET.SubElement(_add(task, "Principals"), f"{{{NS}}}Principal", {"id": "Author"})
    _add(pr, "UserId", user)
    _add(pr, "LogonType", "InteractiveToken")
    _add(pr, "RunLevel", "LeastPrivilege")
    s = _add(task, "Settings")
    for tag, val in (("MultipleInstancesPolicy", "IgnoreNew"), ("DisallowStartIfOnBatteries", "false"),
                     ("StopIfGoingOnBatteries", "false"), ("AllowHardTerminate", "true"), ("StartWhenAvailable", "true"),
                     ("RunOnlyIfNetworkAvailable", "false"), ("AllowStartOnDemand", "true"), ("Enabled", "true"),
                     ("Hidden", "true"), ("ExecutionTimeLimit", "PT0S"), ("Priority", "7")):
        _add(s, tag, val)
    rof = _add(s, "RestartOnFailure")
    _add(rof, "Interval", "PT1M")
    _add(rof, "Count", "999")
    ex = _add(ET.SubElement(task, f"{{{NS}}}Actions", {"Context": "Author"}), "Exec")
    _add(ex, "Command", command)
    _add(ex, "Arguments", arguments)
    return ET.tostring(task, encoding="utf-16", xml_declaration=True)


def agent_task_xml(exe: Path, config: Path, user: str | None = None) -> bytes:
    for p in (exe, config):
        if '"' in str(p):
            raise ValueError("a double quote is not allowed in the install path")
    return build_task_xml(str(exe), f'run --config "{config}"', user or current_user())
