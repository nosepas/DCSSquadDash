"""Plain-language LEEME.txt for the personalised agent package, one text per supported language.

Placeholders: {minutes} (pairing code lifetime). Every language must contain the same placeholders (checked by a test).
"""
from __future__ import annotations

LANGUAGES = ("es", "ca", "en", "gl", "eu")
DEFAULT_LANGUAGE = "es"

_LEEME = {
    "es": """FOX3 - Agente para el servidor de DCS
======================================

Qué es esto: un programita que envía a la web de tu escuadrón los datos de este servidor de DCS.
No abre puertos ni toca tu DCS.

Pasos
1. Haz doble clic en INSTALAR.cmd.
2. Si Windows muestra "Windows protegió su PC" (SmartScreen): pulsa "Más información" y despues "Ejecutar de todas formas".
   És normal: el programa todavía no tiene firma digital.
3. Espera a ver el mensaje de que todo ha ido bien y pulsa una tecla para cerrar.
4. En la web: abre este servidor. El agente aparecera EN LINEA. Elige las carpetas detectadas y pulsa Guardar.

Importante
- El código de emparejamiento (pairing-code.txt) caduca a los {minutes} minutos. Si caducó, descarga el paquete de nuevo desde la web.
- No necesitas abrir puertos en el router ni en el cortafuegos.
- El agente se inicia solo cuando este usuario de Windows inicia sesión.
- Para desinstalarlo: fox3-agent.exe uninstall
""",
    "ca": """FOX3 - Agent per al servidor de DCS
===================================

Què és això: un programet que envia a la web del teu esquadró les dades d'aquest servidor de DCS.
No obre ports ni toca el teu DCS.

Passos
1. Fes doble clic a INSTALAR.cmd.
2. Si Windows mostra "Windows ha protegit el teu PC" (SmartScreen): prem "Més informació" i despres "Executa igualment".
   És normal: el programa encara no té signatura digital.
3. Espera el missatge que tot ha anat bé i prem una tecla per tancar.
4. A la web: obre aquest servidor. L'agent apareixerà EN LÍNIA. Tria les carpetes detectades i prem Desa.

Important
- El codi d'aparellament (pairing-code.txt) caduca als {minutes} minuts. Si ha caducat, descarrega el paquet de nou des de la web.
- No cal obrir ports al router ni al tallafocs.
- L'agent s'inicia sol quan aquest usuari de Windows inicia sessió.
- Per desinstal·lar-lo: fox3-agent.exe uninstall
""",
    "en": """FOX3 - Agent for the DCS server
===============================

What is this: a small program that sends this DCS server's data to your squadron's website.
It opens no ports and does not touch your DCS.

Steps
1. Double-click INSTALAR.cmd.
2. If Windows says "Windows protected your PC" (SmartScreen): click "More info", then "Run anyway".
   This is normal: the program is not code-signed yet.
3. Wait for the message that everything went well, then press a key to close.
4. On the website: open this server. The agent will show as ONLINE. Choose the detected folders and press Save.

Important
- The pairing code (pairing-code.txt) expires after {minutes} minutes. If it expired, download the package again from the website.
- You do not need to open any port on the router or the firewall.
- The agent starts by itself when this Windows user logs in.
- To uninstall: fox3-agent.exe uninstall
""",
    "gl": """FOX3 - Axente para o servidor de DCS
=====================================

Que é isto: un programa pequeno que envia a web do teu escuadrón os datos deste servidor de DCS.
Non abre portos nin toca o teu DCS.

Pasos
1. Fai dobre clic en INSTALAR.cmd.
2. Se Windows amosa "Windows protexeu o teu PC" (SmartScreen): preme "Máis información" e despois "Executar de todos os xeitos".
   É normal: o programa aínda non ten sinatura dixital.
3. Agarda a mensaxe de que todo foi ben e preme unha tecla para pechar.
4. Na web: abre este servidor. O axente aparecerá EN LIÑA. Escolle os cartafoles detectados e preme Gardar.

Importante
- O código de emparellamento (pairing-code.txt) caduca aos {minutes} minutos. Se caducou, descarga o paquete de novo desde a web.
- Non fai falta abrir portos no router nin no firewall.
- O axente inicia só cando este usuario de Windows inicia sesión.
- Para desinstalalo: fox3-agent.exe uninstall
""",
    "eu": """FOX3 - DCS zerbitzariaren agentea
=================================

Zer da hau: programa txiki bat, DCS zerbitzari honen datuak zure eskuadroiaren webgunera bidaltzen dituena.
Ez du portuak irekitzen eta ez dio zure DCSri eragiten.

Urratsak
1. Egin klik bikoitza INSTALAR.cmd fitxategian.
2. Windowsek "Windowsek zure PC babestu du" (SmartScreen) erakusten badu: sakatu "Informazio gehiago" eta gero "Exekutatu hala ere".
   Normala da: programak ez du oraindik sinadura digitalik.
3. Itxaron dena ondo joan dela dioen mezura eta sakatu tekla bat ixteko.
4. Webgunean: ireki zerbitzari hau. Agentea ONLINE agertuko da. Aukeratu detektatutako karpetak eta sakatu Gorde.

Garrantzitsua
- Parekatze-kodeak (pairing-code.txt) {minutes} minututan iraungitzen dira. Iraungi bada, deskargatu paketea berriro webgunetik.
- Ez duzu porturik ireki behar routerrean ez suebakian.
- Agentea bere kabuz hasten da Windows erabiltzaile honek saioa hastean.
- Desinstalatzeko: fox3-agent.exe uninstall
""",
}


def leeme(language: str, minutes: int) -> str:
    """The LEEME.txt text with CRLF line endings; unknown languages fall back to the default."""
    text = _LEEME.get(language, _LEEME[DEFAULT_LANGUAGE]).format(minutes=minutes)
    return text.replace("\n", "\r\n")


TEXTS = _LEEME
