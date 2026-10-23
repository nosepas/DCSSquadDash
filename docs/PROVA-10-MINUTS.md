# Prova real en 10 minuts

Per comprovar FOX3 amb un servidor DCS de veritat. Cal que la central ja funcioni (`docs/INSTALACIO-CENTRAL.md`) i que
tinguis un compte d'administrador.

## Abans de començar
- El PC del servidor DCS té Windows i accés a Internet (només connexions de sortida cap a la central).
- Foothold 5.3.5 ha desat almenys una partida (existeix el fitxer de desat a la carpeta `Missions\Saves`).
- Opcional: DCSServerBot amb l'API REST activada i un usuari de BD només lectura (`docs/ADMINISTRADOR-AGENT.md`).
- Opcional: Tacview en una carpeta local o en una carpeta de Google Drive (`docs/TACVIEW-GOOGLE-DRIVE.md`).

## Passos
1. **Web → Administració → Servidors →** el teu servidor → **Connectar un agent**. Baixa el ZIP (el codi d'aparellament dura 15 minuts).
2. Al PC del servidor, descomprimeix el ZIP en una carpeta qualsevol i fes doble clic a `INSTALAR.cmd`. Si Windows avisa
   (SmartScreen), tria *Més informació → Executar igualment*: l'executable encara no està signat.
3. Espera que l'assistent web passi a **Connectat**. Si no ho fa, mira el pas «Si alguna cosa falla» d'aquí sota.
4. A **Administració → Servidors →** el teu servidor, revisa les carpetes detectades (desats de Foothold, Tacview) i corregeix-les si cal.

## Què has de veure (marca-ho)
- [ ] La portada mostra el servidor com a **en línia** i la missió actual.
- [ ] El mapa mostra les zones de Foothold amb el bàndol correcte.
- [ ] Amb algú connectat: apareix a «jugadors en línia» i el seu avió al mapa.
- [ ] Després d'una partida: la gravació apareix a la cerca de Tacview i es pot descarregar.
- [ ] Rànquings i fitxa de pilot mostren dades (si DCSServerBot està connectat).
- [ ] Generador de DTC: les marques de mapa (aeroports, FARPs, línia de front) i les ràdios apareixen.

## Si alguna cosa falla
Al PC del servidor, des de la carpeta d'instal·lació (`%LOCALAPPDATA%\FOX3Agent`):

```
fox3-agent.exe status
fox3-agent.exe diagnose --config agent.toml --out informe.txt
```

- `status` diu si la tasca està instal·lada, si l'agent corre i quan la central va acceptar dades per última vegada.
- El registre és a `state\agent.log` (l'agent s'executa sense finestra, així que allà hi ha tots els errors).
- `informe.txt` està esborrat (sense noms de jugadors, claus, ucids ni usuari de Windows): és el que cal enviar per diagnosticar
  coses que encara no s'han pogut verificar contra un servidor real (format de Foothold 5.3.5, colors de Tacview, esdeveniments de DCSServerBot).

## Desinstal·lar
Executa `fox3-agent.exe uninstall` des de la **còpia descarregada** (no des de la carpeta instal·lada: un executable no pot
esborrar-se a si mateix). Amb `--keep-data` es conserven la configuració i la cua.
