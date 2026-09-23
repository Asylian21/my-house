# Unreal Archviz Game — overený archviz základ, 22. 9. 2026

Profil `output/unreal/archviz-game-20260922` obsahuje aktuálny hlavný návrh
**C / B / B**, natívne materiálové detaily, vnútorné svetlá a import pôvodnej
postavy Michelle. Finálny lokálny balík je zostavený a podpísaný; prešiel
natívnou prehliadkou všetkých 13 miestností a 16 architektonických dverí,
kontrolou kamery a animovanej postavy a vytvorením 19 regionálnych snímok.
Rozhodujúci [archivovaný report balíka](../output/unreal/archviz-game-20260922/hud-redesign-history/2026-09-22T09-55-59-319322Z-8b28c1ab/model-package.json)
má SHA-256 `33de1932772d750bfca47444cbe1bca25af83258cf1637ad5dce240c50c3938b`
a čas vytvorenia **22. 9. 2026, 09:02:23 UTC**.
Tento dokument oddeľuje jeho dôkazy od starších balíkov a uvádza hranice
overenia. Následnú úpravu menu, ovládacích prvkov a aktuálny balík pre
`npm run unreal:open` opisuje [herné rozhranie](unreal-game-ui.md).
Nižšie uvedené runtime dôkazy patria tomuto archviz základu.

Záväzný návrh a pravidlá archívu sú v [active-design.md](active-design.md).
Nový profil zachováva osadenie 3 000 mm od ulice aj pravej kolmej hranice.
Predchádzajúce výstupy `model-refresh-20260922`, `walk-game-20260922`
a historické materiálové štúdie zostávajú oddelené.

## Čo je implementované

[Základný importér](../scripts/unreal/model-refresh-import.py) najskôr vytvorí
a overí aktuálnu geometriu, zdrojové PBR materiály, chôdzu, pomocné kolízie
a pohyblivé dvere. [Samostatný archviz importér](../scripts/unreal/archviz-import.py)
pracuje až s týmto úspešným uloženým základom. Neimportuje stavebnú geometriu
znova a neprepisuje `model-refresh-import-report.json`.

### Povrchy

[Materiálová vrstva](../scripts/unreal/archviz-materials.py) vyberá materiály
podľa aktuálnych zdrojových názvov a rodín textúr, nie podľa historických
čísel objektov. Zachováva pôvodný farebný základ, zdrojové UV, priehľadnosť,
masky a emisné uzly. Dopĺňa normálu, variáciu drsnosti a pri fotografických
mapách obmedzenú sivú moduláciu pôvodnej farby.

| Povrch | Počet materiálov | Doplnok |
| --- | ---: | --- |
| Dubové čelá, nábytok a podlaha | 7 | Fotografická kresba a póry, drsnosť; pri podlahe zostáva pôvodná normála spojov |
| Omietka a podhľady | 4 | Jemná fotografická štruktúra a drsnosť |
| Betón a dlažba exteriéru | 3 | Fotografický povrch a drsnosť |
| Keramická dlažba a obklad | 2 | Projektová normála v pôvodných UV vrátane škár |
| Kameň a pracovné dosky | 4 | Projektová normála a jemná drsnosť bez prefarbenia |
| Epoxid | 1 | Jemná projektová normála |
| Kartáčované kovy | 5 | Procedurálna mikroštruktúra a drsnosť |
| Lakované profily, dvere a ďalšie povrchy | 9 | Tlmená mikroštruktúra a drsnosť |

Fotografická projekcia používa lokálne súradnice objektu v centimetroch:
perióda dubu je približne **183 cm**, omietky **100 cm**, betónu **180 cm**.
Textúra preto zostáva pripojená aj k pohyblivému objektu. Procedurálny detail
sa filtruje podľa derivácií obrazu. Nevzniká displacement ani nová geometria.
Sivá modulácia sa normalizuje voči priemeru vstupnej mapy a násobok farby je obmedzený
na 0,72–1,28. Importované OpenGL normály majú pre Unreal obrátený zelený kanál.

Pri 28 materiáloch s normálou vo svetových súradniciach sa výsledok prevodu
z lokálneho priestoru výslovne násobí `TwoSidedSign`. Unreal tento krok pre
vlastnú svetovú normálu nerobí automaticky. Zdrojové štítové steny obsahujú
koplanárne trojuholníky s opačným poradím vrcholov; bez opravy môže vybraná
zadná strana dostať normálu smerujúcu dovnútra a nesprávne osvetlenie.
Sedem materiálov s tangentovou normálou používa existujúcu korekciu enginu
a ďalšie znamienko sa k nim nepridáva. Oprava nemení žiadny pôvodný uzol,
farbu, emisiu, UV ani geometriu.

[Vstupný manifest](../scripts/unreal/archviz-material-inputs.json) obsahuje
zdroje, autorov, rozmery, fyzické periódy a SHA-256 všetkých 17 lokálnych máp;
aktuálny výber vytvoril 14 natívnych detailových textúr. Fotografické mapy sú
existujúce lokálne **CC0** zdroje Poly Haven:

- [Oak Veneer 01](https://polyhaven.com/a/oak_veneer_01), Jenelle van Heerden.
- [White Plaster 02](https://polyhaven.com/a/white_plaster_02), Rob Tuytel.
- [Concrete Pavement](https://polyhaven.com/a/concrete_pavement), Charlotte Baglioni.

Ostatné použité normály pochádzajú z projektového generátora
[generate-visual-assets.py](../tools/generate-visual-assets.py).
Skeny sú ilustračným výberom povrchov, nie meraním konkrétne objednaného výrobku.
Sklo zachováva zdrojový odtieň, alfu a drsnosť; optická kalibrácia ani historická
vodná kaustika nie sú výsledkom tejto vrstvy.

### Svetlá

[Vnútorné osvetlenie](../scripts/unreal/archviz_lighting.py) vytvorilo
**40 pohyblivých RectLight svetiel v 13 miestnostiach**. Polohy vychádzajú
z aktuálnych difúzorov, kuchynských svietidiel a výšok či sklonov podhľadov.
Každé svetlo má konečný dosah a tiene. Svetlá zostávajú zapnuté počas dennej
aj nočnej obývanej prehliadky.

Exportované kuchynské svetelné toky zostávajú zachované; doplnkové svietidlá
majú návrhový tok podľa plochy miestnosti. Nejde o doložené luxy ani dodávateľskú
fotometriu. Vrstva nemení existujúce slnko, oblohu, expozíciu ani zdrojové
emisné materiály. Denné aj nočné Metal snímky finálneho balíka a podmienky
ich merania sú uvedené v runtime dôkazoch nižšie.

### Postava, kamera a ovládanie

[Import Michelle](../scripts/unreal/archviz-avatar.py) používa existujúci webový
GLB a svetlú difúznu textúru. Zachováva 65 kostí a tri zdrojové animácie:
Idle, Walk, Run. Natívny BlendSpace1D používa vzorky rýchlosti 0, 115 a 240 cm/s.
Vizuálna postava sa normalizuje na 170 cm; jej mesh nemá vlastné kolízie.
Fyzická chôdza naďalej používa existujúcu kapsulu a kontrakt domu.

[Kamera postavy](../unreal/BreziTwin/Source/BreziTwin/BreziPawnAvatar.cpp)
oddeľuje prezentačnú kameru od fyzického oka `ArchitectureCamera`.
Výber dverí používa fyzické oko, takže odsunutá kamera nemení dosah interakcie.
Predvolený odstup kamery je 260 cm, maximum 450 cm. Guľový sweep s polomerom
17 cm kontroluje prekážky; priblíženie pri prekážke má okamžitú prednosť pred
vyhladzovaním a pred zásahom ponecháva 9 cm rezervu.

Aktuálna oprava vynecháva z tohto kamerového dotazu iba zdrojové skryté
navigačné proxy: actor aj komponent musia mať `BreziHiddenCollision`, byť
skryté a mať navzájom zhodné značky zdrojového objektu `COLL_` aj zdrojovej
identity. Komponent s `BreziWalkSurface` sa nevynechá. Ich samostatný kontrakt,
hranice a kolízie overuje
[WalkingContract](../unreal/BreziTwin/Source/BreziTwin/BreziWalkingContract.cpp).
Filter sa pridáva iba do parametrov kamerového sweepu; nemení kolízne profily
ani blokovanie chôdze. Viditeľné steny, nábytok a pohyblivé dvere naďalej
kameru blokujú. Tým sa odstraňuje pritláčanie kamery k postave navigačným
obalom, ktorý môže siahať vyššie než skutočný viditeľný nábytok.

[Politika viditeľnosti](../unreal/BreziTwin/Source/BreziTwin/BreziAvatarPolicy.h)
má hysteréziu: už viditeľná postava sa začne skrývať pri odstupe najviac
120 cm; skrytá sa znova zobrazí od 145 cm. Celý prechod je nastavený na 0,15 s a skončí
presne plnou nepriehľadnosťou alebo skrytím. Nevytvára trvalý čiastočne
maskovaný stav medzi týmito vzdialenosťami. Pri odstupe najviac 55 cm sa telo
skryje okamžite; režim obmedzeného pohybu prechod nesimuluje. Ustálenie
viditeľnosti, zmenu kostrovej pózy a kolízny limit kamery kontroloval úspešný
natívny prezentačný test počas finálnej prehliadky.

Aktuálne väzby v [ovládači](../unreal/BreziTwin/Source/BreziTwin/BreziPlayerController.cpp)
zahŕňajú WASD/šípky, interakciu **E**, prepnutie osoby **V**, vycentrovanie
**R**, zoom kolieskom a tlačidlami **+/−**, deň/noc **N**, uvoľnenie vstupu
**Esc**, kurzor HUD **Tab** a pomoc **F1**. HUD obsahuje ovládanie kamery,
pohybu a výber miestností. Zoom spracúva aj zlomkové hodnoty kolieska,
macOS scroll a magnify gestá. Samotná existencia týchto väzieb nie je dôkazom
úspešného fyzického ovládania touchpadom ani prístupnosti HUD.

HUD teraz používa `SDPIScaler`, ktorý vyrovnáva hernú DPI krivku podľa
natívnej mierky okna. Cieľom je veľkosť textu a ovládacích prvkov v natívnych
bodoch aj v 1080p Retina okne. Táto korekcia nemení 3D render target ani
percento renderovania. Ručný beh overil skutočný fokus a aktiváciu ovládacích
prvkov v testovanom okne; rozsah tohto overenia je uvedený samostatne nižšie.

## Reprodukovateľný postup

Príkazy sa spúšťajú z koreňa repozitára. `prepare` vyžaduje nový nepoužitý
výstupný adresár; nižšie uvedený názov je príklad pre ďalší samostatný beh.
Vyžaduje sa lokálny Unreal 5.8, aktuálny Xcode/Metal toolchain a dostupné
textúry uvedené vo vstupnom manifeste.

```sh
export BREZI_MODEL_OUTPUT="$PWD/output/unreal/archviz-game-20260922-next"
export BREZI_ARCHVIZ_GAME=1
export UNREAL_ENGINE_ROOT="/Users/Shared/Epic Games/UE_5.8"

npm run unreal:model -- prepare
npm run unreal:model -- export
npm run unreal:model -- editor-build
npm run unreal:model -- import
npm run unreal:model -- archviz
npm run unreal:model -- game-build
npm run unreal:model -- package
npm run unreal:model -- open interior
```

`archvizGame: true` sa zapíše do `profile.json` pri príprave. Tento profil
zahŕňa adresár avatara do cooku. Základný import aj archviz fáza majú vlastný
log procesu, časové údaje a SHA väzbu na výsledný report. Natívna archviz fáza
beží cez Python commandlet s `BREZI_ARCHVIZ_OUTPUT` nastaveným runnerom.
Príkaz `materials` slúži staršej obmedzenej obnove zdrojových materiálov;
nie je náhradou archviz fázy s novými textúrami a postavou.

Package gate overuje pôvodný zdrojový report aj nový archviz report. Hash mapy
a natívnych assetov berie z posledného úspešného archviz importu; pôvodné
materiálové balíky preto neoveruje proti ich už nahradeným hashom. Zostávajú
pripnuté všetky zdroje, pomocné skripty, vstupné mapy a samostatné reporty.
Runner nastavuje `DOTNET_SYSTEM_NET_SOCKETS_INLINE_COMPLETIONS=1` iba procesu
UAT pri stagingu Zen dát; nemení inštalovaný engine.

### Bezpečný opakovaný pokus po chybe importu

Pred úpravou vzniká `archviz-checkpoint/`: kópia pôvodného reportu, zálohy
mapy a vybraných materiálových balíkov, kompletné pôvodné hashe a zoznam
povolených zmien. Pri zachytenej chybe sa uloží presný chybný stav disku.
Obnova je prípustná iba pre stav `failed-recoverable` a po skončení zaznamenaného
natívneho procesu. Kontroluje, či od chyby nikto nezmenil balíky ani zdroje.

```sh
python3 -B scripts/unreal/archviz-import.py --restore "$BREZI_MODEL_OUTPUT"
npm run unreal:model -- archviz
```

Obnova vráti iba zálohovanú mapu a vybrané materiály. Odstráni nové natívne
assetové súbory iba z vopred vyhradených priečinkov `Avatar/Michelle`
a `Archviz/Textures`. Geometrické balíky musia zostať byte-identické.
Stav `failed-protected-drift`, neskoršia cudzia zmena súborov alebo nezachytené
prerušenie bez úplného chybového checkpointu sa automaticky neobnovujú.
Po úspešnom importe zostávajú skripty a vstupy pripnuté; ich ďalšia úprava
vyžaduje nový platný importný dôkaz.

### Jednorazová oprava normál už úspešne importovaného profilu

[Normal refresh](../scripts/unreal/archviz-normal-refresh.py) rieši iba prechod
z predchádzajúceho úspešného archviz importu bez `TwoSidedSign`. Nový import
cez aktuálny materiálový helper už vytvára správny graf priamo.
Migračný príkaz vyžaduje presne overenú kópiu predchádzajúceho úspešného
reportu, procesovej väzby, pomocných reportov a všetkých pôvodných helperov
v `normal-refresh-history/before-two-sided-fix/`.

```sh
npm run unreal:model -- normal-refresh
```

Pred zápisom porovná všetky prijaté assety a mapu, zdroje aj reporty s ich
hashmi. Jedinou povolenou zmenou pôvodného helpera je explicitná nová verzia
materiálového receptu, pričom jeho pôvodné overené bajty zostávajú v archíve.
Presný pôvodný validátor najskôr overí prijaté grafy. Následne pribudnú iba
dva uzly pri 28 výstupoch normály. Ich balíky sa samostatne zálohujú.
Mapa sa vôbec neukladá; všetky ostatné balíky vrátane avatara a svetiel
musia zostať byte-identické.

Nový `archviz-normal-refresh-report.json` a nástupnícky
`archviz-import-report.json` odkazujú na SHA pôvodného reportu. Procesová väzba
sa po úspešnom skončení presmeruje na `normal-refresh.log.json`.
Pri zachytenej chybe a až po skončení procesu môže
`python3 -B scripts/unreal/archviz-normal-refresh.py --restore-failed "$BREZI_MODEL_OUTPUT"`
obnoviť presne zálohované prijaté materiály a reporty. Nevracia celý projekt
do predchádzajúceho geometrického importu.

## Dôkaz importu assetov

Úspešný tretí pokus prebehol **22. 9. 2026, 07:53:51–07:54:17 UTC**, exit 0.
Predchádzajúce dva pokusy odhalili natívne API rozdiely pri načítaní funkcie
časového maskovania avatara a zápise materiálu SkeletalMesh. Oba sa obnovili
cez uvedený checkpoint bez opätovného importu stavebnej geometrie.

| Overenie | Zaznamenaný výsledok |
| --- | --- |
| Aktívny návrh | C / B / B |
| Geometria a materiálové väzby po opätovnom otvorení mapy | 1 990 objektov a 1 990 väzieb |
| Najväčšia odchýlka uložených hraníc | 0,0009765625 cm |
| Materiálová vrstva | 35 materiálov, 14 nových detailových textúr; grafy a konvencia normál overené |
| Vnútorné svetlá | 40 svetiel, 13 miestností; polohy a vlastnosti overené |
| Avatar | 65 kostí v zdroji, 3 klipy; uložený materiál, kostra, vzorky blendspace a normála overené |
| Zmenené pôvodné balíky | Presne 35 vybraných materiálov a mapa |
| Chránené geometrické balíky | Byte-identické |
| Pôvodný importný report | Byte-identický s checkpointom |
| Výsledné natívne assetové súbory | 2 349, mapa evidovaná samostatne |
| Natívny Game build | `model-game-build-validated`, všetky plánované akcie vykonané |

Táto tabuľka dokladá importnú vrstvu. Nasledujúce opravy normál, kamery a HUD
sú zahrnuté vo finálnom balíku `33de1932…`; jeho build, package gate
a runtime výsledky sú evidované samostatne.

Podklady: [archviz import](../output/unreal/archviz-game-20260922/archviz-import-report.json),
[záznam procesu](../output/unreal/archviz-game-20260922/archviz-import.log.json),
[materiály](../output/unreal/archviz-game-20260922/archviz-materials-report.json),
[svetlá](../output/unreal/archviz-game-20260922/archviz-lighting-report.json),
[avatar](../output/unreal/archviz-game-20260922/avatar-import-report.json),
[Game build archviz základu](../output/unreal/archviz-game-20260922/hud-redesign-history/2026-09-22T09-55-59-319322Z-8b28c1ab/model-game-build.json).

[Natívna oprava normál](../output/unreal/archviz-game-20260922/archviz-normal-refresh-report.json)
prebehla **22. 9. 2026, 08:42:00–08:42:30 UTC**, exit 0.
Po opätovnom otvorení mapy bolo explicitne overených všetkých **28 zapojení
svetová normála × TwoSidedSign** a sedem nezmenených tangentových materiálov.
Zmenilo sa presne 28 materiálových balíkov; **2 322 chránených balíkových
súborov vrátane mapy zostalo byte-identických**. Všetkých 1 990 objektov
a väzieb opäť prešlo pôvodnou geometrickou kontrolou s rovnakou maximálnou
odchýlkou 0,0009765625 cm. Časy a úspešný proces sú v
[normal-refresh.log.json](../output/unreal/archviz-game-20260922/normal-refresh.log.json).
Uložený graf a geometria sú tým overené; render po oprave pochádza z nového
cooku a je zachovaný v snímkach finálneho balíka.

Sedem testov materiálových receptov, vstupných hashov a zapojenia znamienka
a šesť testov obnovy
checkpointu prešlo. Obnova má testy aj pre cudziu zmenu geometrie, cudzie nové
balíky, súbežnú zmenu po chybe a stále bežiaci natívny proces. Svetelný kontrakt
má deväť zdrojových testov. Dva testy chránia inventár a nedotknuté balíky
pri oprave normál; tri ďalšie používajú aktuálne zdrojové štíty a dokazujú
zhodu opravených normál a svetelného kosínu z oboch strán. Tieto matematické
testy nevykonávajú GPU shader ani neposudzujú výsledný jas obrazu.
Relevantné príkazy:

```sh
python3 -B scripts/unreal/test_archviz_materials.py
python3 -B scripts/unreal/test_archviz_import.py
python3 -B scripts/unreal/test_archviz_normal_refresh.py
python3 -B tests/unreal-archviz-lighting.test.py
node --test tests/unreal-world-normal-facing.test.mjs
node --test tests/unreal-avatar-policy.test.mjs tests/unreal-touchpad-policy.test.mjs tests/unreal-archviz-room-viewpoints.test.mjs
npm run unreal:test
```

Jednotkové testy politík kamery a gest overujú výpočty. Nenahrádzajú vstup
zo skutočného touchpadu ani meranie natívneho renderu. Uvedenie celého
`unreal:test` je reprodukčný príkaz; tento záznam netvrdí nový kompletný beh
celej sady.

## Ručné ovládanie posledného testovaného HUD

Na balíku s reportom SHA-256
`8e184f31f499dd9e5ca7a6bdef3d89ccbc0873c90f3602ee53a256fc90711f33`
prešlo ovládanie cez CUA v bežnej hernej aplikácii s novým používateľským
adresárom. Po aktivovaní okna **Tab** presunul fokus na skutočné tlačidlo HUD,
**Enter** otvoril zoznam so 17 položkami a klik na miestnosť **1.02** presunul
hráča do nej v režime chôdze. **E** zmenilo ponuku dverí z otvorenia na
zatvorenie, **N** preplo deň/noc a po výbere miestnosti **1.03** kláves **V**
zobrazil pohľad z očí. [Záznam spustenia](../output/unreal/archviz-game-20260922/manual-ui-final-launch.json)
identifikuje balík, binárny súbor a začiatok ručného behu 22. 9. o 08:53:57 UTC.

Na tom istom binárnom súbore uspeli aj natívne testy
`Brezi.Controls.Hud.DestinationAction` a `Brezi.Controls.Hud.MouseTransition`;
[proces skončil s exit 0](../output/unreal/archviz-game-20260922/native-hud-tests-process.json).
Bežali s `-nullrhi`, preto zaznamenaný timeout inicializácie grafického okna
nie je výsledkom týchto funkčných testov a beh nedokazuje vykreslenie HUD.
Následná úprava odstránila iba nepodporovaný znak `▾` z textu tlačidla
„Miestnosť / pohľad“. Finálny balík `33de1932…` obsahuje túto typografickú
zmenu; oproti ručne testovanému balíku nemení funkciu ovládania. Jeho úplná
prehliadka a merania sú uvedené nižšie. Fyzické scroll/pinch gestá touchpadu
a širšia kontrola prístupnosti týmto ručným behom potvrdené nie sú.

## Runtime dôkazy finálneho balíka

Nasledujúce behy používajú presne report balíka `33de1932…` uvedený v úvode.
Package gate overil arm64 aplikáciu aj podpis `deep-strict-valid`; kontrola
pred a po každom behu potvrdila nezmenený obsah balíka.

### Súvislá prehliadka a postava

[Natívny záznam](../output/unreal/archviz-game-20260922/qa/walkthrough-dfe3a8d4-acf2-4c6f-bd50-0513336a9462/runtime.json)
z behu **09:03:15–09:10:36 UTC** skončil s exit 0 a stavom
`passed-continuous-walkthrough`. Prešiel **134 krokov, 202,701571 m,
13 miestností, 3 terasy, 3 vonkajšie prístupy a 16 architektonických dverí**.
Obsahuje 32 otvorení a 16 zatvorení cez herný vstup E, skúšku blokovania
zatvorenými dverami a opätovný priechod po otvorení. Regionálne snímky
zahŕňajú všetkých 19 cieľových oblastí; všetkých 19 PNG 1920 × 1080 bolo
dekódovaných a porovnaných s uloženými hashmi.

Pôvodný [hostiteľský QA report](../output/unreal/archviz-game-20260922/qa/walkthrough-dfe3a8d4-acf2-4c6f-bd50-0513336a9462/qa.json)
zostáva nezmenený so stavom `failed`: pri `LOGGIA-DOOR` odmietol jednu
vzorku, v ktorej W nebolo stlačené. Samostatná
[kontrola držaného vstupu](../output/unreal/archviz-game-20260922/qa/walkthrough-dfe3a8d4-acf2-4c6f-bd50-0513336a9462/qa-held-input-review.json)
prehodnotila tie isté natívne údaje, nie nový beh aplikácie. Vyžaduje aspoň
tri skutočne stlačené vzorky W, ich súčet aspoň 1,45 s a presnú zhodu počtu
s natívnym záznamom. Loggia mala **53 držaných vzoriek spolu 1,514854 s**;
jedna nedržaná vzorka 0,040535 s sa do trvania nepočíta a jej príčina nie je
zo záznamu určená. Všetky kontroly fyzických a zdrojových prekážok, vstupov,
pokrytia a interakcie E zostali zachované. Výsledok tejto samostatnej kontroly
je `continuous-walkthrough-validated`, bez chýb; jej 29 regresných testov
prešlo. Report pripína pôvodný neúspešný report, runtime, balík aj všetky PNG.

Súčasná natívna kontrola prezentácie prešla s **15 659 vzorkami**. Pozorovala
65 kostí, 5 655 zmien pokojovej pózy a 10 002 zmien pózy pri chôdzi.
V 6 646 vzorkách mala kamera prekážku; najväčšie prekročenie nezávisle
overeného kolízneho limitu aj odchýlka aktívnej kamery boli 0 cm.
Overila aj 57 vynechaných skrytých navigačných komponentov a ustálenie
viditeľnosti postavy. Syntetické magnify, scroll a wheel udalosti prešli cez
vlastný herný viewport, zmenili odstup kamery a nepohli kapsulou.
Toto je dôkaz natívnej animácie, kamery a spracovania udalostí; nenahrádza
fyzické gesto prstami na touchpade. Dĺžka celej prehliadky ani počet týchto
vzoriek nie sú benchmark FPS.

### Denné, nočné a HUD snímky a výkon

Štyri samostatné Metal behy medzi **09:19–09:21 UTC** skončili so stavom
`standalone-capture-validated`, bez chýb. Každý zaznamenal 240 zahrievacích
a 240 meraných snímok. Používali TSR TemporalUpscale,
`r.ScreenPercentage=50`, vypnuté dynamické rozlíšenie a zapnutý VSync.
Rozmery nižšie sú skutočné výstupné RHI render targety; nejde o tvrdenie
renderovania scény pri 100 % interného rozlíšenia.

| Pohľad a report | Výstup | Priemer / P50 / P95 snímky | Priemer GPU RHI | Aplikácia v popredí |
| --- | --- | --- | --- | --- |
| [Interiér cez deň](../output/unreal/archviz-game-20260922/qa/interior-walk-a3dcff49-abc7-4732-9d28-7cbc2a0cec79/qa.json) | 1920 × 1080 | 93,75 / 77,17 / 181,01 ms | 19,29 ms | 0 / 240 |
| [Miestnosť 1.02 v noci](../output/unreal/archviz-game-20260922/qa/room-1-02-night-walk-87adc706-fcac-4366-af1f-745da3c42705/qa.json) | 1920 × 1080 | 53,47 / 49,06 / 83,11 ms | 17,38 ms | 173 / 240 |
| [Miestnosť 1.06 v noci](../output/unreal/archviz-game-20260922/qa/room-1-06-night-walk-d9047fef-bbaf-44ec-9c6d-f678aab01263/qa.json) | 1920 × 1080 | 48,12 / 47,72 / 56,49 ms | 18,10 ms | 240 / 240 |
| [Interiér s ponukou pozastavenia](../output/unreal/archviz-game-20260922/qa/interior-ui-pause-40f2d782-7ea1-4c61-8c1e-48eb0a8d8868/qa.json) | 3840 × 2160 | 54,13 / 53,57 / 61,90 ms | 50,67 ms | 240 / 240 |

Prvé tri pohľady majú stojacu kameru v režime chôdze. Pri ponuke pozastavenia
patrí fokus HUD, preto scéna správne zaznamenala 0 vzoriek klávesového fokusu;
aplikácia aj okno zostali aktívne počas všetkých 240 vzoriek.
Denné a prvé nočné meranie nemali stabilné popredie. Na počítači zároveň
prebiehala ďalšia práca; tieto údaje neurčujú príčinu rozdielu medzi časom
snímky a GPU a nedokazujú regresiu GPU. Ani behy v popredí nedokladajú
stabilných 30 alebo 60 fps. Merania zostávajú uvedené v skutočných podmienkach,
bez nahradenia lepším výsledkom zo staršieho balíka.

Každý report odkazuje na vlastné `capture.png` a `runtime.json`; zachované
denné a nočné rendery umožňujú skontrolovať opravené materiály a osvetlenie.
Úspešná validácia snímky znamená platný natívny výstup a jeho pôvod, nie
automatické umelecké prijatie všetkých povrchov alebo plynulosti.

## Staršie runtime dôkazy pred poslednou opravou

Nasledujúce behy patria prvému balíku s reportom SHA-256
`fbc9941f624f12cc0fa5cf712a58769282bdb44afcaccd5c34ffa4f1f308dd1c`.
Sú zachovanou referenciou. Nepotvrdzujú poslednú opravu kamerového filtra,
stabilného skrývania postavy, natívneho DPI HUD ani znamienka svetových normál.

- [Súvislá prehliadka 08:05 UTC](../output/unreal/archviz-game-20260922/qa/walkthrough-104df14c-44b5-4091-a233-9a6323cf73db/qa.json)
  prešla 202,57 m, 13 miestností, 3 terasy a 3 vonkajšie prístupy. Záznam
  obsahuje 32 otvorení a 16 zatvorení pre 16 architektonických dverí.
  Vstup išiel cez herný automatizačný mechanizmus. Kontrola postavy a kamery
  pozorovala zmeny kostrovej pózy a syntetické scroll/magnify udalosti cez
  viewport; fyzický macOS touchpad a OS klávesnica overené neboli.
- [Denné meranie 07:57 UTC](../output/unreal/archviz-game-20260922/qa/interior-walk-f7d30fcd-8473-4ced-8bed-37b21b4ea20a/runtime.json)
  malo 240 zahrievacích a 240 meraných snímok, všetky v popredí s aktívnym
  oknom a fokusom scény. Priemer bol 24,49 ms, P50 24,34 ms a P95 27,14 ms.
  Výstup bol 1920 × 1080, s `r.ScreenPercentage=50` a TSR TemporalUpscale.
  Ide o stojacu kameru v režime chôdze, nie o dôkaz plynulého prechádzania
  ani renderovania celého obrazu pri 100 %. Toto meranie sa neprenáša
  na finálny balík.

Experimenty s vyššou kvalitou svetla a tieňov zostávajú experimentmi; nemajú
zastúpiť meranie finálneho profilu pri stabilnom fokuse. Finálny vzhľad sa
nepovažuje za prijatý iba na základe úspešného záznamu PNG alebo číselného
testu pohybu.

## Hranice overenia a odovzdanie

- Natívny import, cook, podpísaný balík, súvislá chôdza a prezentačné kontroly
  sú doložené vyššie. Výtvarné prijatie každého materiálu, realistický kontakt
  chodidiel a svetelné parametre skutočných výrobkov z týchto testov nevyplývajú.
- Syntetický zoom prešiel natívnym viewportom; jemný scroll a pinch fyzickými
  prstami, ich prirodzený smer a celý cyklus straty/návratu fokusu zostávajú
  samostatným praktickým overením. Ručne overené klávesy, kliky a HUD sú
  doložené aj pre finálny balík `33de1932…` v zázname nižšie.
- Čitateľnosť a prístupnosť pri ďalších veľkostiach okna, mierkach, režime
  obmedzeného pohybu a asistívnych technológiách nemajú úplné pokrytie.
  Prehliadka 16 architektonických dverí sa nerozširuje na funkčný test práčky,
  sušičky alebo bazénového poklopu.
- Stabilných 60 fps sa netvrdí. Zostáva samostatné meranie pri pohybe,
  stabilnom popredí a známej súbežnej záťaži; štyri aktuálne merania vyššie
  sú platným záznamom ich podmienok, nie prijatím výkonu.
- Balík bol nastavený ako aktuálny v `output/unreal/model-refresh-current.json`;
  `npm run unreal:open` ho otvorí s predvolenou postavou a herným ovládaním.
  Predchádzajúci výber je zachovaný v `previous-current-selection.json`.

Finálny [záznam prijatia](../output/unreal/archviz-game-20260922/model-visual-review.json)
pripína celý balík, súvislú prehliadku, vizuálnu kontrolu 19 záberov a štyri
samostatné snímky. Natívne testy `DestinationAction` a `MouseTransition`
[prešli aj v tomto balíku](../output/unreal/archviz-game-20260922/qa/native-hud-tests-33de1932/validation.json).
`npm run unreal:test` prešiel: 537 Node testov a 140 Python testov, bez chýb.

[Bežné spustenie finálneho balíka](../output/unreal/archviz-game-20260922/manual-ui-33de-review.json)
potvrdilo postavu a čitateľný panel, pauzu a návrat, otvorenie výberu miestností,
klávesový výber 1.02, presun do chodby, otvorenie dverí cez E a deň/noc cez N.
Strom prístupnosti niekedy zaostával za viditeľným menu; následne zobrazil
všetkých 17 položiek aj správny fokus. Neskorší náhľad okna bol orezaný na
pravom okraji displeja, preto jeho vizuálny rozsah netreba zamieňať s úplnými
natívnymi PNG. Materiály a nočné svetlá boli posúdené na úplných snímkach.

Importné príznaky `nativeRenderedVerified`, `nativeVisualVerified`
a `nativeLocomotionVerified` zostávajú v pôvodných importných reportoch
nepravdivé zámerne: importná vrstva netvrdí runtime dôkaz. Novšie spustenia
sú doložené samostatnými, konkrétnemu balíku priradenými reportmi vyššie.
