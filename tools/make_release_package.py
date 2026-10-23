"""Builds the release package: the tracked source files + the built web interface (web/dist) + the built agent (prebuilt/agent).

    python tools/make_release_package.py --agent-dir <folder with fox3-agent.exe, fox3-agentw.exe, *.sha256, fox3-agent.version> \
        --out FOX3-0.1.0-pilot-windows.zip

`scripts/install-central.ps1` uses web/dist and prebuilt/agent when they exist, so Node.js and PyInstaller are not needed on the central.
Run `npm run build` in web/ first and build the agent with tools/build_agent.py. Writes <out>.sha256 next to the zip.
"""
from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AGENT_FILES = ("fox3-agent.exe", "fox3-agentw.exe", "fox3-agent.exe.sha256", "fox3-agentw.exe.sha256", "fox3-agent.version")


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, check=True, capture_output=True, text=True).stdout
    return [p for p in out.split("\0") if p]


def build(agent_dir: Path, out: Path, prefix: str) -> None:
    web = ROOT / "web" / "dist"
    if not (web / "index.html").is_file():
        raise SystemExit("web/dist is missing: run `npm run build` in web/ first")
    missing = [n for n in AGENT_FILES if not (agent_dir / n).is_file()]
    if missing:
        raise SystemExit(f"missing in --agent-dir: {', '.join(missing)} (build with tools/build_agent.py)")
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        for rel in tracked_files():
            z.write(ROOT / rel, f"{prefix}/{rel}")
        for path in sorted(web.rglob("*")):
            if path.is_file():
                z.write(path, f"{prefix}/web/dist/{path.relative_to(web).as_posix()}")
        for name in AGENT_FILES:
            z.write(agent_dir / name, f"{prefix}/prebuilt/agent/{name}")
    digest = hashlib.sha256(out.read_bytes()).hexdigest()
    Path(f"{out}.sha256").write_text(f"{digest} *{out.name}\n", "utf-8")
    print(f"Wrote {out} ({out.stat().st_size / 1e6:.1f} MB), sha256 {digest}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--agent-dir", type=Path, required=True)
    ap.add_argument("--out", type=Path, required=True)
    ap.add_argument("--prefix", default="FOX3", help="top-level folder inside the zip")
    args = ap.parse_args()
    build(args.agent_dir.resolve(), args.out.resolve(), args.prefix)
    return 0


if __name__ == "__main__":
    sys.exit(main())
