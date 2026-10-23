# Contributing

Thanks for your interest. FOX3 is published under the [PolyForm Noncommercial License 1.0.0](LICENSE.md).

## Ownership of contributions

The project owner keeps the intellectual property of FOX3. By submitting a contribution (pull request, patch, issue text containing
code) you confirm that you wrote it or have the right to submit it, and you **grant the project owner a perpetual, irrevocable,
worldwide, royalty-free license to use, modify, sublicense and relicense it** as part of FOX3. If you cannot agree to this, please
do not submit code (bug reports are always welcome).

## How to work

1. Open an issue first for anything bigger than a small fix.
2. Keep the engineering rules the project follows: layered code (`api` -> `services` -> `repositories` -> `db`), **small files
   (about 150 lines)**, full type hints, no dialect-specific SQL (the suite runs on SQLite *and* PostgreSQL), contracts first
   (`contracts/` is the interface between the parts: change it deliberately), and tests for every behaviour you add.
3. Before opening a pull request:
   ```powershell
   python -m ruff check .
   python -m pytest -q
   cd web; npm run lint; npm test; npm run build
   python tools/prepublish_check.py
   ```
4. Never commit real DCS files, recordings, logs, screenshots with personal data, or any secret. `samples/` is git-ignored on purpose.
5. Anything not verified against real DCS/Foothold/DCSServerBot behaviour must be described as such in code comments and docs.

## Dependency locks

Python dependencies are hash-pinned in `requirements/` (`central.txt` runtime + postgres, `agent-build.txt` agent + PyInstaller,
`dev.txt` tests/lint + postgres). They are universal (all platforms) and resolved for Python 3.12, so one file serves CI (3.12/3.13)
and newer local interpreters. Install with `pip install --require-hashes -r requirements/dev.txt` then `pip install --no-deps -e .`.
After changing dependencies in `pyproject.toml` (or to upgrade), regenerate with `pip install uv` in a throw-away venv and
`python tools/lock_requirements.py [--upgrade]`. GitHub Actions in CI are pinned to full commit SHAs; Dependabot updates them.

## Security issues

See [SECURITY.md](SECURITY.md): report them privately.
