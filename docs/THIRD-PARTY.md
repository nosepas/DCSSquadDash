# Third-party data, services and references

FOX3 itself is released under the [PolyForm Noncommercial License 1.0.0](../LICENSE.md). This file lists what it uses from others.

## Data included in the repository
| What | Where | Source | License / note |
|---|---|---|---|
| Map projection constants (11 DCS maps) | `common/fox3_common/geo.py` | Numeric constants exported from DCS by the **pydcs** project (`dcs/terrain/*/projection.py`) | pydcs is LGPL-3.0. Only numeric constants (facts) are used; checked independently against real airport coordinates (`tests/test_projections.py`). |
| Airfield names and positions (11 maps) | `common/fox3_common/data/airfields.json.gz`, built by `tools/make_airfields.py` | Airport tables of **pydcs** (DCS's own x/y coordinates), converted to lat/lon | pydcs is LGPL-3.0. Only names, positions and a civil flag are extracted. **Owner to confirm this is acceptable for the repository's license.** |
| DTC templates | `dtc/fox3_dtc/templates/*.json.gz` | Made by `tools/make_templates.py` from DCS-written `.dtc` files supplied by the owner, with the mission-specific navigation emptied | Contains DCS default tables (threats, unit names). Reviewed for personal text, not for numeric values. |

## Services used at run time (outbound from the central server)
| Service | Used for | Terms |
|---|---|---|
| Open-Meteo Elevation API (Copernicus DEM GLO-90) | Approximate ground elevation of DTC points. Only coordinates are sent. | Free for non-commercial use, attribution required (shown in the DTC page). Disable with `FOX3_ELEVATION_URL=`. |
| Esri "World Dark Gray Base" tiles | Basemap in the browser | Esri's terms apply; for production use a provider or tile server you have rights to (`VITE_TILE_URL`). |
| Discord OAuth2 | Login | Discord's developer terms. |

## Projects consulted as references (no code copied)
| Project | License | How it was used |
|---|---|---|
| DCSServerBot (Special-K) | MIT | The agent calls its optional REST API (`GET /servers`, `POST /getuser`) and reads its `missionstats` table read-only. |
| jambon (b1naryth1ef) | MIT | Reference for the ACMI line format; the indexer is an independent implementation. |
| foothold-sitac (VEAF) | **none stated** | Read only to learn the persistence file format; **no code was reused**. |
| Tacview ACMI documentation | public docs | File format facts. |

## Python and JavaScript dependencies
Declared in `pyproject.toml` and `web/package.json` with their own licenses (FastAPI, SQLAlchemy, httpx, pyproj, jsonschema, React, Leaflet, i18next, Vite...). Review them with a license scanner before distributing binaries.
