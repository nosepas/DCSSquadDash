# Instal·lació del central (producció)

El central és el PC que té la web, la base de dades i l'adreça pública. Els servidors DCS només s'hi connecten (l'agent fa
connexions sortints). **Estat:** les peces estan provades (configuració, migracions sobre PostgreSQL 16, servidor); l'instal·lador
sencer (inclosos els comptes de servei i els permisos) encara no s'ha executat en un Windows net.

**Paquet de la release (recomanat):** a la pàgina de *Releases* de GitHub baixa `FOX3-<versió>-windows.zip` i comprova el seu `.sha256`
(`Get-FileHash fitxer.zip -Algorithm SHA256`). Ja porta la web i l'agent compilats (`prebuilt/agent`, `web/dist`), de manera que
**no cal Node.js ni PyInstaller**; l'instal·lador els fa servir tal com són. Els executables no estan signats: Windows SmartScreen
avisarà. Si prefereixes compilar-ho tot tu mateix, usa el codi font de la release i el procés de sota.

## 1. Què necessites
| Cosa | Per a què | On |
|---|---|---|
| Python 3.12+ | executar FOX3 | python.org (marca «Add to PATH») |
| Node.js LTS | construir la web (una vegada) | nodejs.org |
| PostgreSQL 15+ | base de dades | postgresql.org |
| `caddy.exe` | HTTPS automàtic (Let's Encrypt) | caddyserver.com/download |
| `nssm.exe` | executar-ho com a serveis de Windows | nssm.cc |
| Un nom DNS | l'adreça pública (No-IP, DuckDNS, un domini propi...) | el teu proveïdor |

## 2. Preparar PostgreSQL
Crea una base de dades buida i un usuari (a `psql`, com a administrador):
```sql
CREATE USER fox3 WITH PASSWORD 'posa-una-clau-llarga';
CREATE DATABASE fox3 OWNER fox3 ENCODING 'UTF8';
```
La URL serà `postgresql+psycopg://fox3:LA_CLAU@localhost:5432/fox3`. L'esquema el crea FOX3 sol (migracions).

## 3. Crear l'aplicació de Discord
1. Entra a <https://discord.com/developers/applications> → **New Application** (nom: FOX3).
2. Al menú **OAuth2**: copia el **Client ID** i genera el **Client Secret** (només es mostra una vegada).
3. A **OAuth2 → Redirects** afegeix `https://EL-TEU-NOM-DNS/api/v1/auth/discord/callback` (el mateix nom que posaràs a l'instal·lador).
4. El teu **ID de Discord**: Discord → Configuració → Avançat → activa «Mode desenvolupador», clic dret al teu nom → **Copiar ID d'usuari**.
   Aquest ID serà d'administrador.

## 4. Xarxa
- El nom DNS ha d'apuntar a la IP pública d'aquest PC.
- Al router: reenvia els ports **TCP 80 i 443** cap a aquest PC (el 80 només serveix per validar el certificat).
- Cap altre port s'ha d'obrir. Els agents dels servidors DCS no necessiten res obert.

## 5. Instal·lar
PowerShell **com a administrador**, a la carpeta del projecte:
```powershell
powershell -ExecutionPolicy Bypass -File scripts\install-central.ps1 -Hostname EL-TEU-NOM-DNS `
    -AdminDiscordIds EL_TEU_ID -DiscordClientId EL_CLIENT_ID -DryRun      # primer, per veure què farà
powershell -ExecutionPolicy Bypass -File scripts\install-central.ps1 -Hostname EL-TEU-NOM-DNS `
    -AdminDiscordIds EL_TEU_ID -DiscordClientId EL_CLIENT_ID              # de debò
```
Et demanarà (sense mostrar-ho) la URL de PostgreSQL i el Client Secret de Discord. **No es guarden en cap fitxer**: queden a la
configuració dels serveis de Windows. L'instal·lador crea `C:\ProgramData\FOX3\central.toml` i `Caddyfile` (si ja existeixen no els sobreescriu).

Es pot tornar a executar sense risc: els serveis que ja existeixen s'actualitzen (`nssm set`), no es dupliquen. Si deixes buida la URL
de PostgreSQL en una reexecució, es conserven els secrets actuals (i no es fa `migrate`).

Ordres útils (després d'activar `.venv`): `fox3-central check-config --config C:\ProgramData\FOX3\central.toml`,
`fox3-central migrate --config ...`, `fox3-central serve --config ...`.

## 5b. Seguretat dels serveis
- **Comptes:** `FOX3Central` i `FOX3Caddy` NO s'executen com a `LocalSystem`, sinó amb comptes de servei virtuals
  `NT SERVICE\FOX3Central` i `NT SERVICE\FOX3Caddy` (sense contrasenya, sense perfil, només amb els permisos que els donem). Si un
  servei és compromès, l'atacant no és SYSTEM.
- **Carpeta `C:\ProgramData\FOX3`:** es talla l'herència; només Administradors i SYSTEM hi tenen control total (els usuaris normals
  ja no la poden llegir). Cada servei només rep el mínim:

  | Ruta | `FOX3Central` | `FOX3Caddy` |
  |---|---|---|
  | `central.toml`, carpeta `agent\`, carpeta del projecte (`.venv`, `web\dist`) | lectura | - |
  | `Caddyfile`, `caddy.exe` | - | lectura |
  | `logs\central\` | modificar (el seu registre) | - |
  | `logs\caddy\`, `caddy\` (certificats i clau del compte ACME) | - | modificar |

  El central no escriu enlloc més: la base de dades és PostgreSQL i l'agent ja ve construït. Caddy desa els certificats a
  `caddy\data` perquè l'instal·lador defineix `XDG_DATA_HOME` i `XDG_CONFIG_HOME` al seu servei.
- **Secrets:** la URL de PostgreSQL i el secret de Discord són a la clau de registre
  `HKLM\SYSTEM\CurrentControlSet\Services\FOX3Central\Parameters`. Per defecte és llegible per usuaris normals; l'instal·lador la
  restringeix a SYSTEM, Administradors i al propi compte del servei.
- **Límit honest:** qualsevol **administrador local** (i SYSTEM) pot llegir aquests secrets (registre, memòria o variables d'entorn
  del procés). Windows no ho pot evitar. Per això: no donis administrador local a qui no ho hagi de ser, i fes servir a PostgreSQL un
  usuari amb permisos només sobre la base de dades `fox3` i una contrasenya única.
- **Python i Caddy:** han d'estar en una ubicació llegible pels comptes de servei (p. ex. `C:\Program Files`). Una instal·lació «només
  per a mi» dins `C:\Users\...` no funciona; l'instal·lador avisa.
- **Tallafoc:** les regles dels ports 80 i 443 queden limitades al programa `caddy.exe`.

## 5c. Desinstal·lar
```powershell
powershell -ExecutionPolicy Bypass -File scripts\install-central.ps1 -Uninstall -DryRun      # primer, per veure-ho
powershell -ExecutionPolicy Bypass -File scripts\install-central.ps1 -Uninstall               # elimina els serveis i les regles de tallafoc
powershell -ExecutionPolicy Bypass -File scripts\install-central.ps1 -Uninstall -PurgeData   # a més esborra C:\ProgramData\FOX3
```
Sense `-PurgeData` es conserven configuració, registres i certificats. La base de dades PostgreSQL no es toca mai.

## 6. Primer accés
Obre `https://EL-TEU-NOM-DNS`, entra amb Discord (si el teu ID és a la llista d'administradors tindràs el panell **Administració**), crea
els servidors i genera els codis d'aparellament dels agents (vegeu `docs/FASE2-PROVES-REALS.md`).

## 7. Actualitzar
Atura els serveis, `git pull`, `pip install ".[postgres]"` (a `.venv`), reconstrueix la web si ha canviat, `fox3-central migrate`, arrenca els serveis.
**Actualitza sempre el central abans que els agents** (un agent més nou pot enviar camps que un central més antic no coneix).

## Si alguna cosa falla
- Web sense carregar: mira el DNS, el reenviament 80/443 i `C:\ProgramData\FOX3\logs\caddy\caddy.log` (el central: `logs\central\central.log`).
- Error de Discord «redirect_uri»: la URL de retorn del pas 3 ha de ser idèntica.
- «database was created before migrations existed»: només passa amb bases de dades de proves antigues; usa una base buida.
- Un sol procés: no posis més d'un `worker` (les actualitzacions en directe i la descàrrega de Tacview guarden estat en memòria).
