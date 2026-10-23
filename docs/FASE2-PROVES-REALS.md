# Fase 2 — com provar l'agent amb el teu servidor real

Tot el que segueix s'executa al **PC del servidor DCS**. Cap pas modifica Foothold, DCS ni DCSServerBot.

## 1. Descobrir carpetes i enviar-me l'estructura del fitxer de Foothold

```powershell
cd <carpeta del projecte>
$env:PYTHONPATH = "common;central;agent"
python -m fox3_agent.cli discover                      # llista Saved Games, Foothold, DCSServerBot i Tacview
python -m fox3_agent.cli discover --describe "C:\Users\<tu>\Saved Games\DCS.<servidor>\Missions\Saves"
```

La segona ordre imprimeix un **esquema amb els valors esborrats** (sense noms de jugadors, sense coordenades).
Enganxa'm la sortida: és el que em permet verificar el format de Foothold **5.3.5**, que de moment només conec per documentació
de la 3.2.2.

## 2. Preparar DCSServerBot (opcional, recomanat)

L'agent necessita l'API REST de DCSServerBot per a jugadors en línia i meteo:

1. A `config/main.yaml` afegeix `restapi` a `opt_plugins` i reinicia el bot.
2. A `config/plugins/restapi.yaml` posa un `api_key` propi.
3. L'agent **només** fa `GET /servers` i `POST /getuser`. Aquesta API també pot reiniciar servidors i pujar missions: per això
   l'agent té una llista tancada de crides i no pot fer res més. No exposis el port 9876 a Internet.

Per al registre d'enfrontaments en directe, crea a PostgreSQL un usuari **només de lectura** (`SELECT` sobre `missionstats`,
`missions` i `players`) i posa'n la URL en una variable d'entorn (`FOX3_DCSBOT_DB_URL`).

## 3. Instal·lar, aparellar i comprovar (la resta es configura des del web)

La configuració (carpetes de Foothold i Tacview, adreça de DCSServerBot, adreça pública del servidor...) es fa al **panell
d'administració del web**, no al PC del servidor. L'agent la descarrega i l'aplica en viu, sense reiniciar-se. Al PC només
calen l'adreça del central, el **codi d'aparellament** i, si cal, la clau de l'API de DCSServerBot (que **no passa mai pel central**).

**Camí guiat (recomanat)**: al panell d'admin crea el servidor i genera un **codi d'aparellament** (caduca als 15 minuts, un sol
ús). Després, en un PowerShell **com a administrador**:

```powershell
cd <carpeta del projecte>
powershell -ExecutionPolicy Bypass -File scripts\install-agent.ps1 -CentralUrl https://EL-TEU-CENTRAL -DryRun   # només mostra els passos
powershell -ExecutionPolicy Bypass -File scripts\install-agent.ps1 -CentralUrl https://EL-TEU-CENTRAL           # de debò
```

L'script comprova Python 3.12+, crea el `.venv`, et demana (sense eco) el codi i, si vols, la clau de DCSServerBot, escriu
`agent.toml` (`fox3-agent init`), mostra què troba al PC (`discover`), aparella, comprova la connexió i instal·la el servei de
Windows amb NSSM (necessita `nssm.exe` al PATH, https://nssm.cc/download). La clau de DCSServerBot només es guarda a l'entorn del
servei; el codi d'aparellament no es desa enlloc. Si les gravacions de Tacview són en una carpeta de Google Drive, afegeix
`-ServiceUser "PC\elteuusuari"` (camí antic; el paquet descarregat del web ja s'instal·la com a tasca de l'usuari: vegeu `docs/TACVIEW-GOOGLE-DRIVE.md`). **L'script sencer no s'ha provat en un PC real**
(sí les ordres de Python que crida i el `-DryRun`).

**Camí manual** (equivalent):

```powershell
python -m fox3_agent.cli init  --central-url https://EL-TEU-CENTRAL --out C:\FOX3Agent [--dcsbot-api-key-env FOX3_DCSBOT_API_KEY]
python -m fox3_agent.cli pair  --config C:\FOX3Agent\agent.toml --code-stdin     # escriu el codi i Enter (no queda a l'historial)
python -m fox3_agent.cli check --config C:\FOX3Agent\agent.toml                  # prova central + cada font i mostra els avisos
python -m fox3_agent.cli run   --config C:\FOX3Agent\agent.toml                  # executa l'agent (sense servei)
```

Un cop en marxa, torna al panell d'admin: veuràs l'agent en línia i les **carpetes que ha detectat** al PC com a suggeriments;
fes-hi clic per omplir els camps i desa.

## 3b. Informe de diagnòstic (una sola ordre, per enviar-me'l)

```powershell
python -m fox3_agent.cli diagnose --config C:\FOX3Agent\agent.toml --out informe.txt
```

Imprimeix (i desa) un informe **esborrat** (sense noms de jugadors ni de zones, sense claus, ucids ni noms d'usuari de Windows):
versions, resum de configuració, estat de l'aparellament, carpetes detectades, estructura del fitxer de Foothold i del CSV de
FARPs, l'última gravació de Tacview acabada (valors `Color`/`Coalition`, tipus, rendiment) i l'estructura de l'API/BD de
DCSServerBot. Opcions: `--saves-dir`, `--tacview-dir` per forçar carpetes. **Enganxa'm tot l'informe** (llegeix-lo abans per si
hi ha res personal). Això és el que em permet verificar el que encara és suposició: format de Foothold 5.3.5, mapatge de bàndols de
Tacview i noms d'esdeveniments de DCSServerBot.

## Què hauries de veure
- Al mapa: les zones de Foothold amb el bàndol correcte (les coordenades vénen del propi fitxer).
- A la portada: jugadors en línia, estadístiques de Foothold, meteo.
- Si alguna cosa falla, el **heartbeat** porta avisos (`FOOTHOLD_FILE_STALE`, `DCSBOT_AUTH_FAILED`,
  `DCSBOT_UCID_UNRESOLVED`, `CENTRAL_REJECTED_MESSAGES`...). `check` els mostra.
