# FOX3

A multi-server web platform for **DCS World** squadrons running **Foothold** missions: live tactical map, rankings, pilot profiles,
Tacview search and download, and a **DTC generator** (F-16C, F-14B, AH-64D) with a visual map editor.

> **Status:** working software, tested with simulated data, with synthetic files, on PostgreSQL 16, and against a few real DTC files.
> It has **not yet been run against a live DCS server**. See [What is verified](#what-is-verified-and-what-is-not).
> **License:** [PolyForm Noncommercial 1.0.0](LICENSE.md): free to use and modify, not to sell. Not "open source" in the OSI sense.

## What it does

| Area | Details |
|---|---|
| **Live map** (public) | Foothold zones, supply connections and front line per server; the only public data besides the server and mission list |
| **Private pages** (Discord login) | Overview and KPIs, objectives, rankings, kill feed, pilot search and profiles (one identity per player, separate stats per server), allied aircraft on the map (each user sees only their own coalition), account linking |
| **Several servers** | Servers on different PCs; each runs an *agent* that only makes **outbound** HTTPS connections. Foothold missions and plain missions are both supported |
| **Tacview** | Recordings stay on the DCS PC. Only a small index is sent; search a pilot and get server, file, aircraft, UTC time and offset, or download the file on demand (streamed through the central, never stored). Works with a Google Drive for desktop folder |
| **DTC generator** | Import or create a `.dtc`, edit waypoints, lines and **radios** on a map, with airports, front line and FARPs as reference layers. 11 DCS maps. Unedited files are exported byte-identical |
| **Admin panel** | Everything is configured in the browser: folders, DCSServerBot, Tacview, agents, roles |
| **Languages** | Spanish (default), Catalan, English, Galician, Basque |

## Architecture

```
[DCS server PC]  DCS + Foothold + DCSServerBot + Tacview
        |  fox3-agent  (Windows service, outbound HTTPS only, local queue, applies settings from the admin panel)
        v
[Central PC]  Caddy (HTTPS, Let's Encrypt)  ->  FastAPI  ->  PostgreSQL        React web app
```

* `central/` FastAPI API, services, repositories, Alembic migrations. `agent/` the Windows agent and its data sources
  (Foothold persistence file, DCSServerBot REST/DB, Tacview). `web/` React + TypeScript + Leaflet. `dtc/` the DTC library.
  `common/` shared projections and airfield data. `contracts/` OpenAPI, JSON Schemas and the DDL: the interfaces between the parts.
* Design rules: layered code, small files, PostgreSQL-portable SQL, contract-first, nothing trusted from agents (everything is validated against the schemas).

## Try it in 3 minutes (demo, no DCS needed)

Requires Python 3.12+ and Node.js (only to build the web UI once).

```powershell
powershell -ExecutionPolicy Bypass -File scripts\install-demo.ps1
powershell -ExecutionPolicy Bypass -File scripts\run-demo.ps1
```

Opens http://localhost:8000 with three simulated servers. Use the **Demo pilot** / **Demo admin** buttons to log in.

## Install for real

* **Central** (the web server): [docs/INSTALACIO-CENTRAL.md](docs/INSTALACIO-CENTRAL.md) (Catalan).
* **Agent** (on each DCS server PC): see `scripts/install-agent.ps1` and [docs/FASE2-PROVES-REALS.md](docs/FASE2-PROVES-REALS.md).
* **First real-server test (10 minutes, with checklist)**: [docs/PROVA-10-MINUTS.md](docs/PROVA-10-MINUTS.md).
* **Tacview in Google Drive**: [docs/TACVIEW-GOOGLE-DRIVE.md](docs/TACVIEW-GOOGLE-DRIVE.md).

## Development

```powershell
pip install -e ".[dev,postgres]"
python -m pytest -q                      # SQLite
$env:FOX3_TEST_PG = "postgresql+psycopg://user:pass@localhost:5432"; python -m pytest -q   # same suite on PostgreSQL
python -m ruff check .
cd web; npm ci; npm run lint; npm test; npm run build
python tools/prepublish_check.py         # what would be published + secret/personal-data scan
```

New database migration: `python tools/make_migration.py "message"` and review the generated file.

## What is verified, and what is not

**Verified:** the full automated suite (Python and web) on SQLite and on PostgreSQL 16; the production start-up path
(`fox3-central migrate/serve`); DTC import/export round trip, byte-identical on real F-16, F-14 and AH-64 files; the Caucasus
projection against a real file and the other 10 maps against real airport positions; the agent, relay and settings end to end over real HTTP.

**Not verified yet:** behaviour against a live DCS/Foothold 5.3.5/DCSServerBot 3.0.4.27 server; importing generated DTCs inside DCS;
real Tacview recordings; the Windows installers on a clean PC; Google Drive for desktop. These are documented as pending in
[docs/PLA.md](docs/PLA.md). Do not rely on this for anything critical before running them.

## Documentation

[docs/PLA.md](docs/PLA.md) is the architecture, decisions and status log (Catalan). Third-party data and services: [docs/THIRD-PARTY.md](docs/THIRD-PARTY.md).
Security policy: [SECURITY.md](SECURITY.md). Contributing: [CONTRIBUTING.md](CONTRIBUTING.md).
