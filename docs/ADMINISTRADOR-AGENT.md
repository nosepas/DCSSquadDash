# Guia de l'administrador: instal·lar l'agent al servidor de DCS

Aquesta guia és per a qui administra l'esquadró. No cal saber d'informàtica ni tocar cap fitxer de configuració.

## Què és l'agent?

L'agent és un programa petit (uns 15 MB) que s'instal·la a l'ordinador on corre el teu servidor de DCS. Envia a la web de FOX3
les dades del servidor (jugadors, missió, Foothold, gravacions de Tacview...). Només **envia** dades cap a la web: no obre cap
port, no canvia res del teu DCS i no necessita permisos d'administrador de Windows.

## Instal·lació en 5 passos

1. **Descarrega el paquet des de la web.** Entra a l'administració de FOX3, obre el servidor i prem el botó de descarregar l'agent.
   Tria l'idioma de les instruccions. Et baixarà un fitxer `FOX3-Agent-<nom del servidor>.zip`.
2. **Copia'l a l'ordinador del servidor de DCS** (amb un USB, per l'escriptori remot, per Discord...) i descomprimeix-lo en una carpeta
   (clic dret > Extreure-ho tot). No el posis dins del ZIP: cal descomprimir-lo.
3. **Fes doble clic a `INSTALAR.cmd`.** S'obrirà una finestra negra amb missatges. Si Windows et fa una pregunta, mira l'apartat
   «Windows diu que no el coneix» més avall.
4. **Espera** que la finestra digui que tot ha anat bé i prem una tecla per tancar-la. L'agent ja està instal·lat i funcionant.
5. **Torna a la web**, obre el servidor: l'agent apareixerà **EN LÍNIA**. Tria les carpetes que ha detectat (Foothold, Tacview...)
   i prem **Desa**.

## Windows diu «Windows ha protegit el teu PC»

És normal. Aquest missatge (SmartScreen) surt amb qualsevol programa que encara no té signatura digital, i l'agent encara no en té.
Prem **Més informació** i després **Executa igualment**. El programa surt de la teva pròpia web de FOX3.

## El codi ha caducat

El paquet porta un codi d'un sol ús que **caduca als 15 minuts** i només serveix una vegada. Si has trigat més, o l'instal·lació
diu que el codi no és vàlid, no passa res: **descarrega el paquet de nou** des de la web (cada descàrrega porta un codi nou) i torna
a fer doble clic a `INSTALAR.cmd`.

## Com sé que funciona?

- A la web, dins del servidor, l'agent surt **EN LÍNIA** (es posa en verd uns segons després d'instal·lar).
- A l'ordinador del servidor, obre una finestra d'ordres a la carpeta on has descomprimit el paquet i escriu `fox3-agent.exe status`:
  diu si la tasca està instal·lada, si l'agent corre i quan la central va acceptar dades per última vegada.
- L'agent s'executa **sense finestra**. Si cal veure què fa, el registre és `agent.log` dins la carpeta `state` de l'agent (`%LOCALAPPDATA%\FOX3Agent\state`).

## Actualitzar l'agent

1. Primer s'actualitza el servidor central (el propietari de FOX3 ho fa i torna a construir l'agent).
2. Després descarrega un paquet nou des de la web i torna a executar `INSTALAR.cmd` a l'ordinador del servidor.

Sempre en aquest ordre: central primer, agent després.

## Desinstal·lar

Obre una finestra d'ordres a la carpeta **on has descomprimit el paquet** (no a la carpeta instal·lada: un executable no es pot
esborrar a si mateix) i escriu `fox3-agent.exe uninstall`. Treu la tasca programada i els fitxers instal·lats; amb `--keep-data`
es conserven la configuració i la cua.
A la web pots també revocar l'agent des de la llista d'agents del servidor.

## Guardar la clau de DCSServerBot sense variables d'entorn

Si no vols configurar variables d'entorn de Windows, desa la clau xifrada (només l'usuari de Windows que executa l'agent la pot llegir):

```
fox3-agent.exe secret set fox3_dcsbot_api_key
fox3-agent.exe secret set fox3_dcsbot_db_url
fox3-agent.exe secret list
```

El nom del secret és el de la variable d'entorn en minúscules (`FOX3_DCSBOT_API_KEY` -> `fox3_dcsbot_api_key`; és el nom que apareix a `api_key_env` de l'`agent.toml`). Una variable d'entorn
ja definida té prioritat. Els secrets mai viatgen a la central ni es mostren a la web.

## Cua local quan la central no respon

Si la central no es pot assolir (o la clau s'ha revocat), l'agent guarda els missatges en una cua local (`state/queue.sqlite`) per no perdre res. La cua té un límit
(per defecte 50.000 missatges o 200 MB; es pot canviar a `agent.toml` amb `[queue]`, `max_messages` i `max_mb`). Si s'omple, s'esborren primer els missatges més
antics que després queden substituïts per d'altres (estat del servidor, jugadors, estat de Foothold); els esdeveniments, els vincles de Discord i l'índex de Tacview
es conserven el màxim temps possible. L'agent ho avisa al registre i a la web amb l'avís `OUTBOX_OVERFLOW`.

## Preguntes freqüents

**Cal obrir ports al router o al tallafocs?** No. L'agent només fa connexions de sortida cap a la web de FOX3.

**Calen permisos d'administrador a Windows?** No. S'instal·la només per a l'usuari de Windows que fa doble clic a `INSTALAR.cmd`.

**Funciona si no hi ha ningú amb la sessió iniciada?** No. L'agent s'inicia quan aquest usuari de Windows **inicia sessió**.
L'ordinador del servidor de DCS hauria de tenir l'inici de sessió automàtic, o bé el servidor de DCS hauria de córrer amb el mateix
usuari. Si es reinicia l'ordinador i ningú entra a Windows, l'agent no arrencarà fins que algú hi entri.

**Puc instal·lar-lo en un altre ordinador o usuari?** Sí, però cal descarregar un paquet nou per a cada instal·lació (el codi és d'un sol ús).

**Quantes descàrregues puc fer?** Fins a 10 cada 10 minuts. Cada descàrrega crea un agent pendent nou; els que no s'usen no fan cap mal.

## Si alguna cosa falla

| Què veus | Què fer |
|---|---|
| El botó diu que l'agent no està construït | El propietari de FOX3 ha de construir-lo (`python tools/build_agent.py`, o tornar a executar l'instal·lador de la central). |
| «Codi no vàlid, usat o caducat» | Descarrega el paquet de nou i torna-ho a provar (passos 1-4). |
| L'agent no surt EN LÍNIA | Espera un minut. Comprova que l'ordinador té internet i que l'usuari de Windows té la sessió iniciada. Prova `fox3-agent.exe status`. |
| No surten carpetes detectades | Comprova que el servidor de DCS ha arrencat almenys una vegada. Si encara no, escriu les carpetes a mà a la web. |
| L'antivirus bloqueja el programa | Afegeix-hi una excepció per a la carpeta de l'agent; el programa encara no té signatura digital. |
| Res del que s'ha dit funciona | Executa `fox3-agent.exe diagnose` i envia l'informe al propietari de FOX3. |
