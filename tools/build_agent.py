"""Build the Windows agent executable with PyInstaller.

    python tools/build_agent.py [--out dist/agent]

Writes fox3-agent.exe, fox3-agent.version and fox3-agent.exe.sha256 into the output folder. The central offers that folder
for download (central.toml: [paths] agent_dir). Needs PyInstaller: pip install ".[build]"
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STUB = "from fox3_agent.cli import main\nraise SystemExit(main())\n"
EXCLUDES = ("fox3_agent.sim", "pyproj", "tkinter")


def pyinstaller_command(stub: Path, work: Path, dist: Path, name: str = "fox3-agent", windowed: bool = False) -> list[str]:
    cmd = [sys.executable, "-m", "PyInstaller", "--onefile", "--name", name, "--noconfirm", "--clean",
           "--paths", str(ROOT / "agent"), "--paths", str(ROOT / "common"), "--collect-submodules", "fox3_agent"]
    if windowed:
        cmd.append("--noconsole")
    for mod in EXCLUDES:
        cmd += ["--exclude-module", mod]
    return cmd + ["--distpath", str(dist), "--workpath", str(work / "build"), "--specpath", str(work), str(stub)]


def build(out: Path) -> Path:
    if importlib.util.find_spec("PyInstaller") is None:
        raise SystemExit('PyInstaller is not installed. Run:  pip install ".[build]"')
    sys.path[:0] = [str(ROOT / "agent"), str(ROOT / "common")]
    from fox3_agent import __version__

    out.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="fox3-agent-build-") as tmp:
        work = Path(tmp)
        stub = work / "agent_entry.py"
        stub.write_text(STUB, "utf-8")
        suffix = ".exe" if sys.platform == "win32" else ""
        for name, windowed in (("fox3-agent", False), ("fox3-agentw", True)):  # console build + windowless build for the Scheduled Task
            subprocess.run(pyinstaller_command(stub, work, work / "dist", name, windowed), check=True, cwd=work)
            shutil.copyfile(work / "dist" / (name + suffix), out / f"{name}.exe")
            digest = hashlib.sha256((out / f"{name}.exe").read_bytes()).hexdigest()
            (out / f"{name}.exe.sha256").write_text(f"{digest} *{name}.exe\n", "utf-8")
    exe = out / "fox3-agent.exe"
    (out / "fox3-agent.version").write_text(__version__ + "\n", "utf-8")
    print(f"Built {exe} and fox3-agentw.exe ({exe.stat().st_size / 1_000_000:.1f} MB each), version {__version__}; checksums in *.sha256")
    return exe


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", type=Path, default=ROOT / "dist" / "agent", help="output folder (default: dist/agent)")
    build(ap.parse_args().out.resolve())
    return 0


if __name__ == "__main__":
    sys.exit(main())
