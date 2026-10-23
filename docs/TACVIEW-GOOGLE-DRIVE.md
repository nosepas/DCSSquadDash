# Gravacions de Tacview en una carpeta de Google Drive

Aquesta guia explica com deixar que les gravacions de Tacview (`.acmi`) visquin en una carpeta compartida de Google Drive i que
l'agent de FOX3 les llegeixi.

> **Estat: NO verificat.** No hem tingut cap PC amb Google Drive per a escriptori per provar-ho. El que va a continuació es basa
> en com funciona Windows i Google Drive segons la seva documentació; les parts que depenen de Drive (lletra d'unitat,
> atributs dels fitxers, retards de sincronització) s'han de comprovar a la teva màquina. Si alguna cosa no quadra, executa
> `fox3-agent diagnose` i envia'ns l'informe.

## Com funciona (en una frase)

L'agent **no parla amb l'API de Google**. Instal·les **Google Drive per a escriptori** al PC del servidor, que fa aparèixer Drive
com una carpeta normal de Windows, i li dius a FOX3 aquesta carpeta des del panell d'administració, com qualsevol altra.

## Pas a pas

1. **Instal·la Google Drive per a escriptori** al PC on corre l'agent i inicia sessió amb el compte que té accés a la carpeta.
2. **Tria Mirall (Mirror) i no Streaming.** Configuració de Drive > Preferències > *Google Drive* > "Mirror files".
   - *Mirall*: els fitxers es baixen de debò al disc. L'agent els llegeix a velocitat de disc i sempre hi són (fiable i ràpid).
   - *Streaming*: els fitxers són "només en línia" i es baixen quan algú els obre. Una gravació pot trigar molt a obrir-se,
     i si es talla la xarxa, falla. Funciona, però no és recomanable.
3. **Fes visible la carpeta compartida.** Una carpeta que han compartit amb tu no surt a "El meu Drive" fins que hi afegeixes
   una drecera: al web de Drive, clic dret a la carpeta > *Organitza* > *Afegeix una drecera* > tria "El meu Drive".
4. **Apunta Tacview a aquesta carpeta** (opció *Directori de gravació* de Tacview), o bé deixa que **un altre PC** hi pugi els
   fitxers. Veuràs la ruta a l'Explorador, per exemple `G:\My Drive\Tacview` (streaming/unitat virtual) o
   `C:\Users\<tu>\Google Drive\Tacview` (segons la versió i el mode).
5. **Al panell d'admin** de FOX3, secció **Tacview**: posa-hi aquesta ruta (o fes clic al suggeriment de "carpetes detectades",
   que marcarà les de Google Drive) i desa.
6. **Instal·la l'agent amb el teu usuari de Windows.** Les unitats de Google Drive són **per sessió d'usuari**: un servei de
   Windows (`LocalSystem`) **no veu la unitat `G:`**. L'agent descarregat des del web (`INSTALAR.cmd`) s'instal·la com a
   **tasca programada de l'usuari que l'executa** i s'engega en iniciar sessió, així que veu les mateixes unitats que tu.
   Fes doble clic a `INSTALAR.cmd` **amb l'usuari que té Google Drive iniciat**. L'agent només funciona mentre aquest usuari
   té la sessió iniciada (Drive per a escriptori també s'engega amb la sessió).
7. **Verifica**: `fox3-agent check --config <agent.toml>` ha de dir `tacview: OK`. Si hi ha avisos, surten amb el seu codi.

## Opcions de l'agent (només locals)

A `agent.toml`, si vols que l'agent **no toqui** els fitxers "només en línia":

```toml
[sources.tacview]
cloud_files = "skip"   # per defecte "read": els indexa d'un en un (llegir-los els baixa abans)
```

Amb `read` apareix l'avís informatiu `TACVIEW_CLOUD_FILES` ("N recordings are online-only; reading them downloads them first").
Les peticions de baixada des del web també funcionen amb aquests fitxers (la lectura provoca la descàrrega), però **la primera
baixada pot trigar** perquè Drive ha de baixar el fitxer abans de lliurar el primer byte; el navegador pot esperar-se més del
normal. Amb Mirror això gairebé no passa.

## Què fa l'agent per no llegir fitxers a mitges

- Només indexa un fitxer quan la seva data de modificació és més antiga que el temps d'espera (`settle`, 120 s) **i** la seva
  mida és **la mateixa en dues observacions seguides** (la segona, uns 3 s després de la primera quan el fitxer és nou; després,
  cada 30 s). Així no llegeix un fitxer que Drive encara està copiant.
- Ignora els noms temporals: `*.tmp`, `*.crdownload`, `*.part`, `*.gdownload` i `.~lock*`.
- Si la carpeta no existeix i sembla de Google Drive (o la lletra d'unitat no està llesta), l'avís `TACVIEW_FOLDER_MISSING`
  afegeix la pista: *el servei s'ha d'executar com l'usuari de Windows que té Drive iniciat: torna a instal·lar l'agent iniciant sessió amb aquest usuari*.

## Límits

- **Quota d'emmagatzematge**: les gravacions són grans; vigila l'espai de Drive i del disc (en mode Mirror ocupen els dos llocs).
- **Permisos**: el compte de Drive ha de tenir com a mínim accés de *lectura* a la carpeta (escriptura si Tacview hi grava).
- **Retard de sincronització**: una gravació apareix a FOX3 uns minuts després d'acabar la partida (Drive + 120 s + dues revisions).
- **Un sol agent per carpeta**: no posis dos agents (de dos servidors) llegint la mateixa carpeta.
- **No editis ni moguis les gravacions mentre s'indexen**; canviar-ne el contingut les tornaria a indexar.
- **Gravacions de diversos servidors a la mateixa carpeta: NO suportat en aquesta fase.** Cada agent indexa dins del seu propi
  servidor; si barreges gravacions de dos servidors en una carpeta, totes acabaran al servidor de l'agent que la llegeix.
- Els contenidors `.7z` no es suporten (només text i `.zip`).

## Si alguna cosa falla

| Símptoma | Causa probable | Què fer |
|---|---|---|
| `TACVIEW_FOLDER_MISSING` amb la pista de Drive | L'agent corre amb un altre usuari o l'usuari no té Drive iniciat | Torna a executar `INSTALAR.cmd` amb l'usuari de Drive; comprova que ha iniciat sessió i que `G:` existeix per a ell |
| Carpeta correcta però `0` gravacions | La carpeta compartida no té la drecera a "El meu Drive" | Pas 3 |
| `TACVIEW_CLOUD_FILES` constant | Mode Streaming (fitxers només en línia) | Passa a Mirror, o `cloud_files = "skip"` |
| Les gravacions triguen a sortir | Drive encara sincronitza, o el fitxer es va modificant | Espera; comprova que la mida no canvia |
| `TACVIEW_FILE_FAILED` en un fitxer | Fitxer incomplet o dany | Torna a copiar-lo; si persisteix, envia `diagnose` |

## Què NO està verificat

- Cap prova amb Google Drive per a escriptori real: ni el mode Mirror ni Streaming, ni les rutes exactes (`G:\My Drive` vs
  carpeta local), ni quins atributs de fitxer (`OFFLINE`, `RECALL_ON_OPEN`, `RECALL_ON_DATA_ACCESS`) posa Drive als fitxers
  "només en línia". La detecció d'aquests atributs es basa en la documentació de Windows i està provada només amb dades simulades.
- Que NSSM concedeixi automàticament el dret "Iniciar sessió com a servei" a l'usuari triat.
- Que les credencials de l'agent (protegides amb DPAPI de màquina) les pugui llegir el servei amb un altre usuari.
- El comportament de la baixada des del web quan Drive triga a baixar un fitxer "només en línia".
