"""Pre-publication check: lists exactly what git would publish and scans it for secrets and personal data.

It works on a throw-away COPY of the tree (so it never touches your repository or creates a .git folder here),
respecting .gitignore. Usage: python tools/prepublish_check.py
Exit code 1 when something suspicious is found.
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKIP_DIRS = {"node_modules", ".venv", "__pycache__", ".git", ".pytest_cache", ".ruff_cache"}
BIG = 1_000_000

# (name, regex, allow-list of harmless matches)
PATTERNS = [
    ("private key", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----"), ()),
    ("secret-looking assignment", re.compile(r"""(?i)\b(client_secret|api[_-]?key|password|passwd|secret|token)\b\s*[:=]\s*["'][^"'\s]{8,}["']"""),
     ("CHANGE-ME", "example", "placeholder", "xxxx", "s3cret", "TOPSECRET", "hunter2", "not-a-secret", "test", "dummy", "secret-key",
      "something-else")),
    ("Windows user path", re.compile(r"[A-Za-z]:[\\/]Users[\\/](?!USER\b|x\b|<|\{|%|Public|Default|All Users)[^\\/\s\"'<>]+", re.I), ()),
    ("e-mail address", re.compile(r"[\w.+-]+@(?!example\.|users\.noreply\.github\.com)[\w-]+\.[\w.]+"), ("noreply@anthropic.com",)),
    ("long numeric id (Discord/Steam-like)", re.compile(r"\b\d{17,19}\b"), ("123456789012345678", "111222333444555666", "999999999999999999")),
    ("public IPv4", re.compile(r"\b(?!10\.|127\.|192\.168\.|172\.(?:1[6-9]|2\d|3[01])\.|0\.|203\.0\.113\.|198\.51\.100\.|192\.0\.2\.|255\.)"
                                r"(?:\d{1,3}\.){3}\d{1,3}\b"), ("3.0.4.27", "1.2.3.4", "1.9.0.0")),
]
TEXT_SUFFIXES = {".py", ".ts", ".tsx", ".js", ".json", ".md", ".toml", ".yaml", ".yml", ".ps1", ".sql", ".css", ".html", ".txt",
                 ".cfg", ".ini", ".mako"}


def stage(copy: Path) -> list[Path]:
    shutil.copytree(ROOT, copy, ignore=lambda _d, names: [n for n in names if n in SKIP_DIRS])
    git = ["git", "-c", "user.name=check", "-c", "user.email=check@example.invalid"]
    subprocess.run([*git, "init", "-q"], cwd=copy, check=True)
    out = subprocess.run([*git, "ls-files", "-o", "--exclude-standard"], cwd=copy, check=True, capture_output=True, text=True).stdout
    return [copy / line for line in out.splitlines() if line]


def scan(files: list[Path], base: Path) -> list[str]:
    findings: list[str] = []
    for f in files:
        rel = f.relative_to(base).as_posix()
        if f.stat().st_size > BIG:
            findings.append(f"LARGE FILE ({f.stat().st_size // 1024} KB): {rel}")
        if f.suffix.lower() not in TEXT_SUFFIXES:
            if f.suffix.lower() in {".png", ".jpg", ".jpeg", ".gif", ".acmi", ".dtc", ".sqlite", ".db", ".log", ".zip", ".pem", ".key", ".pfx"}:
                findings.append(f"NON-SOURCE FILE: {rel}")
            continue
        text = f.read_text("utf-8", errors="replace")
        for n, line in enumerate(text.splitlines(), 1):
            for name, rx, allow in PATTERNS:
                m = rx.search(line)
                if m and not any(a.lower() in line.lower() for a in allow):
                    findings.append(f"{name}: {rel}:{n}: {line.strip()[:110]}")
    return findings


def main() -> int:
    with tempfile.TemporaryDirectory() as tmp:
        copy = Path(tmp) / "tree"
        files = stage(copy)
        total = sum(f.stat().st_size for f in files)
        print(f"{len(files)} files would be published ({total // 1024} KB). Top-level layout:")
        tops = sorted({f.relative_to(copy).parts[0] for f in files})
        print("  " + ", ".join(tops))
        findings = scan(files, copy)
    if findings:
        print(f"\n{len(findings)} thing(s) to review:")
        print("\n".join(f"  - {x}" for x in findings[:200]))
        return 1
    print("\nNothing suspicious found (this is a heuristic scan, not a guarantee).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
