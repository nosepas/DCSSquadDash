# PLA — Plataforma web multiservidor DCS (Foothold)

Estat: **pla APROVAT** (2026-10-21). Fase 0 en curs: contractes a `contracts/`.

Decisions finals: nom del projecte/esquadró **FOX3**; llicència **PolyForm Noncommercial 1.0.0** (`LICENSE.md`); Foothold **5.3.5**, DCSServerBot **3.0.4.27** (versions declarades per l'usuari, no verificades contra instal·lacions reals); HTTPS amb nom DNS indicat a l'instal·lador; públic = mapa i missions, la resta privat (login Discord).

## 1. Verificació de la secció 4 contra `samples/`

Executat amb Python + `pyproj` sobre els 4 fitxers reals.

| Afirmació | Resultat |
|---|---|
| `.dtc` = JSON `{"data","name","type"}`, UTF-8 | ✅ (`type`: `F-16C_50`, `F-14BU`, `AH-64D_BLK_II`) |
| F-16C: `data.MPD.NAV_PTS` amb `x,y,alt,id,number,type,TOS,speed,routeAltitude,altitudeType,velocityType,R1..R3,isTOSEnabled,OAP_*` | ✅ És una **llista** (3 punts a la mostra). Claus de `data`: `COLR, COMM, ELINT, MPD, name, terrain, type`. `GEO_LINES`, `THREAT_PTS`, `DEST`, `VIPVRP` són dins `MPD`, no a nivell `data`. `ROE` i `CMDS` **no he comprovat on viuen**. |
| F-16C `terrain` | ✅ `"Syria"`. |
| F-16C `THREAT_PTS` i `DEST` | ⚠️ **Buits a la mostra** → l'estructura d'un punt d'amenaça i d'un destí és **desconeguda**. Cal un fitxer que els tingui. |
| F-14BU: `data.NAV` amb `waypoints (lat,lon,x,y,elev,name,spd,tot)`, `lines (points, closed)`, `additional_points` | ✅ però són **12 rutes**, no 11 (a més `name`, `route_as_line` per ruta). `additional_points` és buit a les dues mostres → estructura no verificada. No hi ha camp `terrain`. Altres claus: `CMDS, JDAM, TIS, cartridge_name`. |
| AH-64D: `NAV.Mission_1.Points.{CTRLM,TGT,WPTHZ}.POINTS[]` (`alt,id,num,text,x,y,note`) | ✅ Hi ha `Mission_1` i `Mission_2`, cada una amb `ADF, Areas, Lines, Points, Routes(10), Zones{NFZ,PFZ}`. `terrain` = `"Caucasus"`. **`Routes` (10), `Zones`, `Areas`, `Lines` són buits a la mostra** → forma interna no verificada. |
| Projecció Caucas | ✅ F-14: error màxim **6·10⁻⁸ m** (lat/lon → x,y) sobre tots els punts de les dues mostres. |
| Projecció Síria | ✅ F-16 STPT1 → 35,950°N 35,403°E, a ~0,1 km de Hmeimim (35,401; 35,949). Coherent, però no hi ha lat/lon al fitxer per demostrar-ho amb exactitud (només plausibilitat). |
| AH-64 Caucas | ✅ Plausible: TGT1 → 43,862°N 42,112°E (Caucas). Tampoc amb lat/lon de referència. |
| `x` = nord, `y` = est | ✅ coherent en els tres avions. |

Conseqüència per al generador DTC: **només el F-14 permet validació numèrica exacta** (té lat/lon). F-16 i AH-64 es validen per ronda (round-trip) i per plausibilitat geogràfica.

Les afirmacions sobre Foothold, DCSServerBot, Tacview/jambon **no s'han pogut verificar** (no tinc fitxers ni internet verificat en aquesta fase). Queden com a tasques de verificació de la Fase 2/3 (secció 8).

## 2. Decisions ja preses (de les teves respostes)

- Idiomes UI: **castellà (per defecte), català, anglès, gallec, euskera**. i18n des del primer dia; català i castellà complets, la resta pot arribar amb cadenes parcials amb *fallback* a castellà.
- Càrrega: ~**20 jugadors simultanis** → arquitectura simple (un procés API, un PostgreSQL). Cap caché distribuïda ni broker.
- Accés per **IP directa**; IP públiques **fixes**.
- Maquinari, versions de DCSServerBot/Foothold i dades de Tacview: **desconegudes** → l'agent les detecta en instal·lar i la Fase 2 comença amb una *fase de descobriment*.

- Entorn de proves: aquest PC té **XAMPP** (Apache + MySQL/MariaDB). La nostra pila és Python + PostgreSQL, així que **XAMPP no és necessari**: la Fase 1 usa SQLite i el servei Python propi. Apache de XAMPP només seria útil com a *reverse proxy* HTTPS de prova (`mod_proxy`); MySQL no s'utilitza. Cal instal·lar Python 3.12 i, per a proves reals, PostgreSQL.
- **Repositori públic a GitHub**. Implicacions: cap secret ni IP/ID de servidor al repo (només `*.example.toml`); `.gitignore` estricte; **llicència a triar** (proposo AGPL-3.0 o MIT; cal decidir-ho i que sigui compatible amb el que reutilitzem — vegeu verificacions de llicències); no es publiquen els `samples/` si contenen dades personals (els teus `.dtc` poden tenir notes/indicatius: revisar abans); escaneig de secrets (gitleaks) com a pre-commit i CI.
- **Accés (decidit)**: **públic** = mapa i missions. **Privat (login Discord)** = tota la resta: portada/KPIs, rànquings, pilots, kills, perfils, Tacview, **generador de DTC** i admin. Tot endpoint privat es protegeix al servidor (no només amagat al front).
- **Llicència (decidit en intenció)**: tu en conserves la propietat intel·lectual; tothom pot usar-lo i modificar-lo, **però no vendre'l**. Això és una llicència *source-available* no comercial, **no és "open source" segons l'OSI** (l'OSI no permet prohibir la venda). Proposo **PolyForm Noncommercial 1.0.0** (text legal estàndard, pensat per a programari) abans que CC BY-NC (pensada per a contingut, no codi). Cal que ho confirmis; si algú aporta codi, convé un acord de cessió (CLA) perquè en mantinguis la propietat. Les dependències (FastAPI, React, Leaflet…) tenen llicències pròpies que es respecten.
- **Versions declarades**: DCSServerBot **3.0.4.27** i Foothold «última versió de Leka» (número exacte desconegut). No he pogut verificar que aquestes versions existeixin ni el seu esquema: es comprovarà contra instal·lacions/fitxers reals a la Fase 2.
- **Nom**: provisional `fox3` (codi de crida «Fox 3»). Es pot canviar en qualsevol moment; el nom s'aïlla en una sola constant de config/i18n i en el nom del paquet, per no ser costós de renomenar. **Pendent: nom de l'esquadró** (afecta repo, instal·ladors i títol de la web).

## 3. Arquitectura

```
[PC servidor DCS] DCS + Foothold + DCSServerBot (+ Tacview, gRPC opc.)
      │  Agent (servei Windows, Python)
      │   lectors: Foothold Lua | DCSServerBot (REST o BD només lectura) | .acmi | gRPC
      └─► HTTPS sortint, clau per agent, cua local (SQLite) amb reintents ─► [Central]
                                              FastAPI + PostgreSQL + frontend (estàtic)
```

- Només connexions **sortints** agent → central. Cap port de DCS/gRPC/BD exposat.
- Central: **Python 3.12 + FastAPI**, PostgreSQL (SQLite només en demo), SQLAlchemy + Alembic. Frontend **React + Vite + TypeScript + Leaflet**, servit com a estàtic pel mateix FastAPI (un sol servei, sense Docker).
- Temps real: **Server-Sent Events** per al front (suficient per a 20 jugadors i més simple que WebSocket); l'agent envia per HTTPS POST amb lots.
- Agent: Python empaquetat amb PyInstaller + servei Windows (via `pywin32` o NSSM — a decidir a la Fase 2). Instal·ladors **Inno Setup**.
- Totes les taules centrals amb `server_id`. Jugador = `ucid` (global); estadístiques per `(ucid, server_id)`.
- El central també pot córrer l'agent del seu propi PC (3r servidor local).

### Estructura del repositori
```
docs/            PLA.md, contractes
contracts/       openapi-public.yaml, openapi-agent.yaml, schemas/*.json
central/         API FastAPI, models, migracions
agent/           lectors, cua, servei
web/             frontend
dtc/             model neutre + serialitzadors + tests (llibreria compartida)
installer/       scripts Inno Setup
samples/         .dtc reals (tests)
tools/           lua de calibratge de projeccions, scripts
```

## 4. Contractes (Fase 0, abans de qualsevol subagent)

Entregables a `contracts/` (els redacto jo després d'aprovar aquest pla):
1. `openapi-public.yaml` — API del frontend.
2. `openapi-agent.yaml` — API d'agents (`/agent/v1/...`, autenticació per clau).
3. `schemas/` JSON Schema: `server_info`, `foothold_state`, `players`, `events`, `tacview_index`, `heartbeat`. Tots amb `schema_version`.
4. Model de dades (DDL). Taules: `servers`, `agents` (clau hash, revocació), `users` (Discord id, rol), `players` (ucid), `player_links` (ucid↔discord, codi, caducitat), `foothold_snapshots`, `zones`, `kills`, `rounds`, `tacview_files`, `tacview_appearances`, `audit_log`.
5. Config d'agent i central (TOML).
6. Model neutre DTC (secció 7).

Regla: **cap subagent modifica un contracte**; ho fa l'orquestrador.

## 5. Seguretat

- Clau per agent: generada al central, mostrada una sola vegada, guardada **com a hash**; revocable des d'admin. Codi d'aparellament d'un sol ús i caducitat curta per a la instal·lació.
- Cap secret al repositori; `.env`/config fora del control de versions.
- BD de DCSServerBot: usuari **només lectura**. gRPC mai exposat.
- OAuth2 Discord amb `state` + PKCE; cookies `HttpOnly`, `SameSite=Lax`, `Secure` quan hi hagi HTTPS; rate limiting (slowapi) al login i a l'API d'agents.
- Admin = llista d'ID de Discord a la config; rols guardats a BD.
- Validació estricta amb Pydantic de tot el que arriba de l'agent (és entrada no fiable si un PC és compromès).

### 5.1 HTTPS sense domini — OPCIONS (decideix tu)

Problema real, no cosmètic: sense HTTPS, la **clau d'agent i les cookies de sessió viatgen en clar**, i Discord **només accepta redirect URI `http://` per a `localhost`**; per a una IP pública cal `https://`. Per tant el **login amb Discord no funcionarà per `http://IP`**.

| Opció | Cost | Pros | Contres |
|---|---|---|---|
| A. DNS dinàmic gratuït (DuckDNS, No-IP…) + Let's Encrypt | 0 € | Funciona amb Discord i navegadors. IP fixa → no cal updater. | Subdomini del proveïdor; cal port 80/443 obert per a la validació (o DNS-01). |
| B. Certificat Let's Encrypt **per a IP** | 0 € | Sense nom. | Suport recent i limitat (certificats curts de ~6 dies, validació HTTP-01 al port 80); **no verificat que el meu client ACME ho suporti a Windows** — caldria provar-ho. |
| C. Domini propi barat (~5–10 €/any) | baix | El més net; es pot fer servir també per a agents. | Cost i gestió d'un DNS. |
| D. Túnel (Cloudflare Tunnel) | 0 € | Cap port obert, HTTPS gratuït. | Requereix domini a Cloudflare; dependència externa. |
| E. HTTP pla per IP (el que prefereixes ara) | 0 € | Cap configuració. | Claus d'agent en clar; **Discord OAuth no funciona**; cookies sense `Secure`. Només acceptable en xarxa de prova. |

**DECISIÓ (usuari): HTTPS amb un nom DNS, proveïdor encara no triat** (No-IP era només un exemple). L'instal·lador del central demana el **nom d'amfitrió (FQDN) en instal·lar**; no és a cap fitxer del repo. Conseqüències:
- Cal que el nom resolgui a la IP pública del central abans de demanar el certificat; l'instal·lador ho comprova.
- Si finalment és No-IP gratuït: cal **confirmar el nom cada 30 dies**. Com que les IP són fixes, no cal client d'actualització d'IP.
- Certificat: validació **HTTP-01** (port 80 obert al PC central) amb un client ACME per a Windows (p. ex. win-acme o Caddy, que gestiona el certificat sol; a triar a la Fase 1). DNS-01 no és viable de manera automàtica amb No-IP gratuït.
- Els agents i el redirect d'OAuth de Discord usaran `https://<nom>.ddns.net` (ports 80/443 oberts al router del PC central).
- La URL base es posa a la config (`public_base_url`); un canvi futur de domini no toca el codi.
- La Fase 1 continua a `localhost`.

L'agent ha d'admetre **certificat fix (pinning)** com a mitigació si algun dia s'usa HTTP o un certificat auto-signat. Es pot migrar a un domini propi (opció C) sense canvis de codi.

## 6. Fases, tasques i repartiment

Cada subagent: worktree propi, encàrrec escrit (objectiu, fitxers permesos, contracte, criteris, proves). Revisió independent abans del merge.

| Fase | Contingut | Mòduls / subagents |
|---|---|---|
| 0 | Pla, contractes, esquelet del repo | Orquestrador |
| 1 | Demo local tot en un: dades d'exemple, agent simulat, Discord a localhost, portada/mapa/perfils | `central-api`, `web-frontend`, `agent-sim`, `installer-demo` |
| 2 | 1 servidor Foothold real. **Primer: descobriment** (veure 8) | `agent-foothold`, `agent-dcsbot`, `central-ingest`, `web-foothold` |
| 3 | Tacview: indexador en flux, cerca, admin | `tacview-indexer`, `central-tacview`, `web-tacview` |
| 4 | 3 servidors, tipus de missió, seccions condicionals | `central-multiserver`, `web-selector` |
| 5 | Generador DTC (F-16C, F-14B, AH-64D; F/A-18C quan hi hagi mostra) | `dtc-core`, `dtc-f16`, `dtc-f14`, `dtc-ah64`, `web-dtc`, `tools-projections` |
| 6 | DCS-gRPC (opc.) | `agent-grpc`, `installer-grpc` |

**Planificació interna:** Fase 5 es pot avançar en paral·lel a la 2 perquè no depèn dels servidors.

## 7. Generador de DTC (disseny)

- **Model neutre**: `Mission{terrain, aircraft, waypoints[], lines[], threats[], zones[]}` amb punts en **lat/lon + alt** (font de veritat). Cada serialitzador converteix a x,y del mapa via `proj/<terrain>.py`.
- **Estratègia segura de serialització**: partir d'una **plantilla base real** (una mostra) i substituir només les seccions que modifiquem (p. ex. `MPD.NAV_PTS`, `GEO_LINES`), preservant tota la resta (`COLR`, `COMM`, …). Evita inventar camps que no entenem (`TOS`, `velocityType`…) — reutilitzem els valors de la mostra com a per defecte.
- **Tests**: round-trip (parse → model → serialitzar → comparar) contra `samples/`; F-14: lat/lon↔x,y a <1 cm; F-16/AH-64: error de round-trip < 1 mm i plausibilitat geogràfica.
- **Mapes**: Caucas i Síria verificats. La resta: script Lua `coord.LLtoLO` en un servidor real (o amb DCS local) per a ≥10 punts per mapa → ajust amb `pyproj` → error esperat <1 m; **cap mapa s'activa sense validar**. Fins aleshores el mapa apareix com a «no calibrat».
- **Elevació**: opcions a avaluar a la Fase 5 (SRTM/Copernicus DEM via servei o tessel·les locals; consulta Lua `land.getHeight`; edició manual). Mai es bloqueja la descàrrega si no hi ha elevació: camp editable.
- **F/A-18C**: mòdul **ocult** fins tenir mostra.
- **UI**: llista de punts editable + arrossegar al mapa + afegir/eliminar/reordenar; descàrrega `.dtc`.
- **Risc conegut**: no puc comprovar que DCS accepti el fitxer; la validació final és la teva importació al joc. Versionarem els esquemes per versió de DCS (la mostra no indica versió).

## 8. Verificacions pendents (no s'assumeixen)

1. **Foothold**: obtenir un `zonePersistance` real i `foothold.status`; mesurar freqüència d'escriptura; documentar variants. → *Fase 2, primer pas.*
2. **DCSServerBot**: versió, si té API REST, esquema de la BD (taules `players`, `statistics`, `missionstats`…). *Cap d'aquests noms està verificat.*
3. **Plugin Tacview de DCSServerBot** i abast.
4. **jambon**: comprovar llicència i si l'ús previst (cerca per `Pilot`) és reutilitzable; si no, indexador propi en streaming.
5. **foothold-sitac (VEAF)**: llicència desconeguda → **només referència**, no copiar codi.
6. **Semàntica dels camps de F-16** (`TOS`, `velocityType`, …) i acceptació de fitxers mínims.
7. **Marianes, Golf Pèrsic, Sinaí, Nevada, Mànega, Atlàntic Sud…**: calibratge.
8. **Estratègia de servei Windows** (`pywin32` vs NSSM) i signatura de l'instal·lador (SmartScreen: avís esperat si no està signat; es documenta).

## 9. Criteris generals d'acceptació

- Cada fase acaba amb una demo executable i un informe «comprovat / no comprovat».
- Tests automàtics obligatoris: contractes (validació d'esquemes), ingest, serialitzadors DTC, indexador Tacview (amb fitxer sintètic i un de gran).
- Rendiment Tacview: lectura en flux, memòria constant; objectiu <60 s per a 500 MB (a mesurar).

## 10. Preguntes obertes per a tu

1. ~~HTTPS~~ **Resolt**: nom DNS + Let's Encrypt; el nom es posa a l'instal·lador (secció 5.1).
2. Pots aportar, quan puguis: un `zonePersistance` real, la versió de Foothold/DCSServerBot, un `.acmi` i un `.dtc` amb **threat points / destins (F-16)** i **rutes/zones (AH-64)** i **additional_points (F-14)** no buits, i el del **F/A-18C**?
3. ~~Resolt~~: públic només mapa i missions; la resta privat. (Text original:) Vols el **pilot invitat** (sense Discord) amb accés de lectura a tot, o tot requereix login? (Assumeixo: lectura pública, login només per a perfil/admin/DTC desat.)
4. ~~Resolt~~: el generador de DTC és privat (login).
5. **Nom de l'esquadró**: pendent (es podrà canviar). **Llicència**: confirma PolyForm Noncommercial 1.0.0.

## 11. Estat Fase 2 (agent + Foothold + DCSServerBot) — actualitzat 2026-10-21

**Verificat (fonts públiques, no amb el teu servidor):**
- DCSServerBot **3.0.4.27 existeix** (llicència MIT). Té el plugin opcional `restapi` (via WebService, port 9876 per defecte) amb clau `X-API-Key` i `prefix` opcional. `GET /servers` dona servidor, missió, jugadors (**sense UCID**) i meteo; `POST /getuser` resol nom→UCID i Discord.
- L'API REST del bot **pot reiniciar servidors, carregar/pujar missions i capturar bases**: l'agent només pot fer `GET /servers` i `POST /getuser` (llista tancada, amb tests) i mai reenvia la contrasenya ni l'adreça del servidor.
- Taula `missionstats` de la BD del bot (esdeveniments amb UCID de l'iniciador/objectiu) → alimenta el registre d'enfrontaments, amb usuari de BD només de lectura.
- Format del fitxer de Foothold (documentació de tercers per a la **3.2.2**): Lua simple amb coordenades lat/lon dins el propi fitxer → el mapa de Foothold **no necessita projecció**. El contracte `foothold_state` s'ha ampliat (`geo`, `accounts`, `ejected_pilots`).
- `foothold-sitac` (VEAF) **no té llicència**: només s'ha llegit com a referència de format; el codi és propi.

**Implementat i provat (206 tests):** parser Lua segur (sense eval), normalitzador, font Foothold (detecció de canvis, fitxer a mig escriure, fitxer vell), font DCSServerBot (REST + BD), agent (cua persistent, avisos al heartbeat, aïllament de fonts que fallen), CLI `discover | pair | check | run`, credencials amb DPAPI, prova extrem a extrem amb el CLI real contra el central.

**NO verificat — cal el teu servidor real:**
1. Que Foothold **5.3.5** escrigui el mateix format (`describe` ho comprova; vegeu `docs/FASE2-PROVES-REALS.md`).
2. El valor real de `side` de `/servers` (la doc diu minúscules; el codi suggereix majúscules: es tracten ambdues).
3. Si l'identificador de `playerStats` de Foothold coincideix amb l'UCID (de moment es resol per nom via `/getuser`).
4. PostgreSQL real (només provat amb SQLite); `psycopg` és opcional (`pip install .[postgres]`).
5. El servei de Windows (`scripts/install-agent.ps1`, amb NSSM) no s'ha provat.
6. `is_hq` no existeix al fitxer conegut: de moment no es mostra cap quarter general (a decidir amb el fitxer real).

**Decisió pendent:** si un agent més nou envia camps que un central més antic no coneix, el central respon 422 i l'agent descarta el missatge (queda reflectit al heartbeat com `CENTRAL_REJECTED_MESSAGES`). Política proposada: desplegar sempre central abans que agents, i pujar `schema_version` per als canvis incompatibles.

## 12. Estat Fase 3 (Tacview) — actualitzat 2026-10-21

**Decisió nova (de l'usuari):** els servidors poden ser en altres PC, i els `.acmi` s'han de poder **obtenir** (no només cercar).
Disseny: relé a demanda, només amb connexions sortints de l'agent. El navegador demana el fitxer → el central avisa l'agent (long poll)
→ l'agent el puja en flux → el central el reenvia al navegador **sense guardar-lo**. Si el servidor és fora de línia, error clar al cap de 30 s.
Si la pujada es talla, la descàrrega s'avorta (mai un fitxer truncat en silenci). Límits: 2 descàrregues per servidor, 8 en total, 4 GB.
Limitació: l'estat del relé és en memòria (un sol procés del central); per escalar a diversos processos caldria un bus compartit.

**Decisió nova (de l'usuari):** tot es configura des del web. Cada servidor té `settings` (Foothold, Tacview, missions, DCSServerBot) i
`address`/`description`; l'agent els rep de `GET /agent/v1/config` i els aplica en viu. L'agent informa de les carpetes que detecta
(suggeriments). **Els secrets (clau de l'API de DCSServerBot, URL de la BD) NO passen pel central**: es queden al PC del servidor.

**Decisió nova (de l'usuari):** el mapa mostra els **avions aliats**. Regla aplicada: cada usuari només veu el seu bàndol (el del seu compte DCS
vinculat i en línia), mai l'enemic; els admins trien bàndol; els anònims no veuen cap avió (el mapa públic només té zones).

**Implementat i provat (303 proves + prova real amb uvicorn):** indexador ACMI en flux (text i zip, ~74 MB/s en una prova sintètica de 100 MB),
cerca per pilot (servidor, fitxer, avió, hora UTC, offset), relé de fitxers, configuració remota amb recàrrega en viu, avions aliats.
Frontend (panell d'admin nou, pàgina Tacview, capa d'avions): en curs amb un subagent.

**NO verificat:** fitxers `.acmi` reals de DCS (només sintètics): bàndols (`Color`/`Coalition`), si els avions d'IA porten `Pilot`, noms dels membres del zip;
rendiment amb 500 MB reals; protecció contra enllaços simbòlics (no es pot provar en aquest Windows); posicions d'avions en directe només existeixen
si Foothold escriu `players` al fitxer (no verificat a la 5.3.5).

**Pendent tècnic:** migracions de base de dades (Alembic): ara es fa `create_all` i un canvi d'esquema obliga a recrear la BD demo;
PostgreSQL real; servei de Windows; instal·lador `.exe`.

## 13. Estat Fase 4 (tres servidors i missions no Foothold) — actualitzat 2026-10-21

**Fet i provat (313 proves de Python, 47 de frontend):**
- Aïllament entre servidors: mapa, rànquing, registre d'enfrontaments, jugadors en línia, avions i índex de Tacview mai es barregen; una clau d'agent només pot escriure al seu servidor.
- Identitat única: un mateix UCID és **un sol jugador** amb estadístiques **separades per servidor**; el vincle Discord↔UCID val a tots els servidors.
- Servidor no Foothold (`generic`): funciona sense dades de campanya (mapa sense zones però amb avions aliats, missions, jugadors, perfil, Tacview); el menú oculta Panell, Objectius, Classificació i Registre de derribos.
- Selector de servidor amb estat en línia; un servidor desactivat desapareix de tot el web.
- Demo amb **tres servidors simulats** (Foothold Caucasus, Foothold Syria, entrenament genèric) i un mateix grup de pilots.

**Errors reals trobats i corregits en aquesta fase:**
1. SQLite donava «database is locked» amb tres agents escrivint alhora (transaccions que llegeixen i després escriuen). Ara les transaccions d'escriptura agafen el bloqueig d'inici (`BEGIN IMMEDIATE`); prova de regressió que falla sense el correctiu.
2. En canviar de servidor el mapa es quedava a la vista del servidor anterior; ara es torna a enquadrar quan canvia el conjunt de zones.
3. Els servidors sense zones no mostraven mapa; ara es frama sobre els avions aliats.

**NO verificat:** el tipus de missió genèrica amb dades reals (només simulat); posicions d'avions en una missió genèrica requereixen DCS-gRPC (Fase 6) o una font equivalent: sense gRPC un servidor genèric no tindrà posicions.

## 14. Estat Fase 5 (generador de DTC) — actualitzat 2026-10-21

**Disseny:** *plantilla + pedaç*. Un `.dtc` té centenars de ajustos que no entenem (colors, ràdios, CMDS, ELINT...). Per això
l'exportació parteix d'una plantilla (el teu fitxer importat o la plantilla integrada de l'avió) i **només substitueix les seccions de
navegació que entenem**; la resta queda tal com la va escriure DCS. Un fitxer importat i exportat sense edicions torna **idèntic byte a byte**
(verificat amb els 4 fitxers reals, també a través de l'API HTTP).

**Mapes (tots els de DCS):** 11 projeccions (Caucas, Síria, Nevada, Golf Pèrsic, Marianes, Sinaí, Malvines, Normandia, Canal de la Mànega,
Alemanya CW, Kola). Font: constants numèriques de pydcs (generades des del propi DCS). Verificació: Caucas **exacta** contra el teu F-14;
Síria **plausible** contra el teu F-16; la resta **comprovades contra posicions reals d'aeroports (<2 km, la majoria <1 km)**.
**Cap s'ha provat dins del joc.** L'API i la web mostren el nivell de confiança de cada mapa.

**Elevació:** Copernicus GLO-90 (90 m) via Open-Meteo (gratuït per a ús no comercial, amb atribució), aproximada i sempre editable;
configurable o desactivable (`FOX3_ELEVATION_URL`). El central només envia coordenades.

**Suportat per avió (editable):** F-16C (steerpoints fins a 25 — d'ençà de la teva descripció, no verificat al joc — i 4 línies geogràfiques),
F-14B (12 rutes amb punts, línies), AH-64D (punts TGT i WPTHZ a les 2 missions). **Es conserva però no s'edita** (estructura desconeguda:
mostres buides): F-16 amenaces i destinacions; F-14 punts addicionals; AH-64 rutes, zones, àrees, línies, ADF, punts CTRLM.
**F/A-18C: desactivat fins que hi hagi un fitxer d'exemple.**

**Regles inferides d'UNA sola mostra per avió (no verificades al joc):** numeració i `id` dels steerpoints/punts nous, ids de línies de l'F-16,
valors per defecte dels punts nous (es copien del primer punt existent de la plantilla). Si DCS els rebutja, caldrà un fitxer real amb més punts.

**Plantilles integrades:** `dtc/fox3_dtc/templates/*.json.gz`, fetes amb `tools/make_templates.py` a partir de les teves mostres, amb la navegació buidada.
Revisades les cadenes: només taules per defecte de DCS (amenaces, unitats). Els números (freqüències) no s'han revisat a mà.

**Pendent verificar (només tu pots):** importar a DCS els fitxers generats (F-16, F-14, AH-64) i dir-me el resultat; provar un mapa que no sigui Caucas/Síria.

### 14.1 Capes de referència del mapa del DTC (afegit a petició de l'usuari)

El mapa de l'editor de DTC mostra, només per orientar-se i **mai exportats al fitxer**: **aeroports** (taula fixa per mapa, 11 mapes),
**línia del front i zones** i **FARPs** (de l'estat actual d'un servidor Foothold que jugui aquell mapa). Un aeroport o un FARP es pot afegir
com a punt amb un clic.
- Aeroports: extrets de les taules de pydcs (vegeu `docs/THIRD-PARTY.md`; **l'usuari ha de confirmar la compatibilitat de llicència**).
- FARPs: l'agent llegeix `<fitxer de persistència>_CTLD_FARPS.csv` (dos formats coneguts per documentació de tercers, **no verificats a
  Foothold 5.3.5**); si el fitxer només porta x/y de DCS, el central els converteix amb la projecció del mapa. Només per a usuaris amb login.
- La llista pública de servidors ara inclou el mapa (`terrain`), que el selector de capes fa servir per escollir el servidor de referència.

## 15. Estat producció: migracions, PostgreSQL i instal·lació — 2026-10-22

- **Migracions (Alembic):** l'esquema és propietat de les migracions (`central/fox3_central/migrations`), no de `create_all`. Una prova comprova que
  les migracions construeixen **exactament** el que descriuen els models, que són reversibles i que una base de dades anterior a les migracions es
  rebutja en lloc de corrompre's. Nova migració: `python tools/make_migration.py "missatge"` (cal revisar-la).
- **PostgreSQL real:** tota la bateria de proves (371) passa sobre **PostgreSQL 16** (cada prova amb una base de dades nova;
  `FOX3_TEST_PG=postgresql+psycopg://usuari@host:port`). Això va destapar i corregir problemes de portabilitat (mides de fitxer de 64 bits, claus de 64 bits).
  Camí de producció provat de punta a punta: `fox3-central check-config / migrate / serve` contra PostgreSQL.
- **Configuració de producció:** `central.toml` estricte (claus desconegudes = error), secrets només en variables d'entorn, https obligatori (http només
  a localhost), el login de demostració no es pot activar des del fitxer. `fox3-central init` genera `central.toml` i el `Caddyfile` sense sobreescriure edicions.
- **HTTPS:** el servidor escolta en local i **Caddy** (proxy) obté i renova el certificat de Let's Encrypt. Un sol procés (estat en memòria: SSE i relé de Tacview).
- **Instal·lador:** `scripts/install-central.ps1` (amb `-DryRun`) i la guia `docs/INSTALACIO-CENTRAL.md`. **No provat en un Windows net**; el certificat
  necessita el teu nom DNS i els ports 80/443 oberts.
- **Pendent:** instal·lador `.exe` gràfic (Inno Setup), servei de l'agent (NSSM) provat en un PC real, còpies de seguretat de PostgreSQL (política per definir).


## 16. Revisió de seguretat independent i distribució de l'agent — 2026-10-22

**Revisió (un revisor independent, que no havia escrit el codi, amb exploits reproduïts):** 1 crítica, 1 alta, 5 mitjanes, 9 baixes. Estat:
- **Corregit i amb prova de regressió:** *CRÍTICA* `/players/online` filtrava els dos bàndols amb posicions a qualsevol usuari (saltava la regla d'avions aliats);
  *ALTA* cossos de petició sense límit (esgotament de memòria anònim): middleware de mida per ruta + límit al Caddy; OAuth sense vincle al navegador
  (login CSRF; migració 0002); limitador de peticions sense límit de memòria i bloquejable amb l'ID d'un agent real; perfils que revelaven servidors desactivats;
  documentació de l'API oberta en producció; descàrregues de Tacview que ocupaven els espais (límit per usuari i temps d'inactivitat);
  taules que creixien sempre (neteja periòdica); comodins `%`/`_` a les cerques; límits del DTC (amplificació de sortida) i pressupost de memòria de la memòria cau de plantilles;
  redirecció oberta després del login i tooltips amb HTML (web); URL de DCSServerBot controlada pel central podia filtrar la clau i saltar la llista tancada (central i agent).
- **Millores a l'agent:** REDoS al lexer de Lua, 401 reintentat sense fi, credencials en text pla a Windows, rutes amb el nom d'usuari enviades al central, càrrega sense temps límit.
- **Pendent / assumit:** vulnerabilitats conegudes d'eines de desenvolupament npm que només es resolen amb salts de versió major (vitest 5, vite 6+, react-router 7): no afecten el servidor en producció, però cal planificar-los;
  fitxer de bloqueig de dependències de Python amb hashes; fixar les accions de CI per SHA; serveis de Windows amb compte virtual i ACL (L4).
- **Vincle Discord ↔ compte DCS (implementat):** amb la lectura de BD de DCSServerBot activada, l'agent llegeix de només lectura les parelles `ucid ↔ discord_id` ja verificades per `/linkme` (`players.discord_id > 0`; -1 vol dir sense vincle; noms de columna a `db_mapping.LINK_COLUMNS`) i només n'envia els canvis (`discord_links`, màx. 500 per missatge, reenviament complet cada 6 h).
  El central les desa com a *reclamacions* (`discord_link_claims`, migració 0003), de confiança només perquè l'agent està autenticat, i crea el `player_links` en iniciar sessió l'usuari (o en arribar les parelles si ja existeix). Mai no es roba un UCID ja vinculat a un altre usuari ni s'aplica si les reclamacions es contradiuen (queda a l'auditoria). Cap codi passa pel xat públic; `/link-codes` continua funcionant. Limitació: si algú es desvincula a DCSServerBot, el vincle ja creat al FOX3 no s'esborra automàticament.
  Revisió independent: una reclamació només es converteix en vincle si un servidor que la fa ha vist realment el UCID (estadístiques o en línia), la creació és atòmica (no sobreescriu), les reclamacions caduquen als 3 dies sense renovar-se, s'esborren en eliminar el servidor i hi ha un màxim de 50.000 per servidor. **Límit conegut:** un agent compromès podria fabricar també les seves estadístiques; la confiança en un agent autenticat no es pot eliminar del tot, només limitar. Entrega: els missatges `discord_links` van a la cua persistent de l'agent, que reintenta davant d'errors de xarxa, 5xx, 429 i 401; només descarta els rebutjats com a invàlids (altres 4xx), que no es poden reintentar. Si una parella es perd, el reenviament complet cada 6 h la recupera. Un administrador pot revisar l'auditoria (`fox3.audit`) per veure quin servidor ha canviat quina reclamació.

**Distribució de l'agent (requisit nou: l'administrador no serà el propietari):** l'agent es compila a un únic `fox3-agent.exe` (PyInstaller, ~15 MB, no cal Python).
Des del panell d'administració del servidor es descarrega un **ZIP personalitzat** (executable, `agent.toml` amb l'URL del central, codi d'aparellament d'un sol ús i 15 minuts,
`INSTALAR.cmd`, `LEEME.txt` en l'idioma de l'administrador). `INSTALAR.cmd` executa `fox3-agent.exe setup`: aparella, copia l'executable a `%LOCALAPPDATA%\FOX3Agent`
i crea una **tasca programada per a l'usuari actual** (no cal ser administrador ni NSSM; Saved Games i Google Drive són per usuari). L'assistent web mostra els passos,
espera que l'agent aparegui en línia i ofereix les carpetes detectades. L'executable **no està signat**: Windows SmartScreen mostrarà un avís («Més informació» → «Executar igualment»).
