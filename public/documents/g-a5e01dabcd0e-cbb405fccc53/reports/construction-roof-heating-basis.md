# Strecha, povala a rozsah podlahového kúrenia C/B/B

Podklad k spresnenému zadaniu stavebníka z 14. 9. 2026: falcovaný plech bez presahov, **pochôdzna povala iba na odkladanie, bez bývania, v dome mimo obývačky; drevené stropy bez betónovej stropnej dosky a bez nadbetonávky**. Podlahové kúrenie zostáva všade okrem garáže, technickej miestnosti a sprchy. Pôdorysné líca, osi, otvory a kódy zostávajú záväzné. Tento dokument rozlišuje existujúcu modelovú geometriu od nového realizačného návrhu. Neurčuje dimenzie krovu, drevených stropov, nosnej povaly ani vykurovacích okruhov; číselné návrhové zaťaženie skladovaním nie je zadané.

## Zdroj a spôsob kontroly

Rozmery nižšie sú v spoločnom lokálnom ráme X/Y, výšky Z v mm od podlahy 1. NP ±0,000. Základom sú [aktívny dom](../lib/twin-active-house.ts), [parametre strechy](../lib/twin-roof.ts#L161), [fasády a portál](../lib/twin-site.ts#L850), [aktuálne miestnosti](../lib/twin-interior.ts#L22) a [aktívna dispozícia](../lib/floor-plan-concept.ts). Hlavný výber je [C/B/B](active-design.md).

Audit pred úpravou strechy porovnal SHA-256 siedmich uvedených geometrických a dispozičných zdrojov so snapshotom výkresovej sady. Všetky odtlačky súhlasili. Plochy boli nezávisle prepočítané zo strešných trojuholníkov a obdĺžnikov miestností. Obaly vizualizačných líšt boli navyše overené v Babylon NullEngine; odchýlky pod 0,001 mm vznikajú pri floatových súradniciach renderera.

## Vykonaná aktívna zmena 14. 9. 2026

Po audite bol na výslovný pokyn stavebníka odstránený 50 mm architektonický presah. `ACTIVE_JOINED_ROOF_PARAMETERS.wingEndYmm` teraz preberá `HOUSE.porches.wingEnd.frontYmm`, teda **Y 22 035**. Číslo sa neudržiava na druhom mieste. Tri koncové vrcholy krídla sa posunuli z Y 22 085 na Y 22 035; ich X a Z, všetky ostatné vrcholy, fasády, miestnosti, osi a kódy otvorov zostali rovnaké. Aktívna strecha má **nulový presah geometrickej roviny** na všetkých nominálnych obvodových lícach. Krytá terasa zostáva hlboká 2 500 mm.

Aktuálny vodorovný priemet je **252,965000 m²**, šikmá plocha **299,979126571 m²**. Vnútorný odkvap krídla má dĺžku 10 835 mm a vonkajší 19 035 mm. Ostatné sklony, dĺžky a výšky zostávajú.

Pôvodné hodnoty sú zachované ako `ARCHIVE_JOINED_ROOF_PARAMETERS`, vrátane Y 22 085 a historického `HOUSE.roof.wingEndOverhangMm: 50`. Existujúci príznak `archive` sa odovzdáva z TwinStudio cez BabylonViewport do TwinSceneOptions. Scéna z neho pri prvom použití odvodí a uloží správnu strechu a používa ju pri plášti, ukončeniach, podbití a strešných nadväznostiach. Extraktor pôdorysu používa tie isté metódy bez konštruktora prehliadača; pri chýbajúcom archívnom príznaku dostane aktívnu strechu. Samotný archív teda nepreberá novú nulovú hodnotu. Súbory `versions/v1`, `versions/v2`, pôdorysná geometria a historické snímky neboli upravované.

Existujúce klampiarske a vizualizačné profily nižšie zostávajú oddelenými detailmi; neboli nasilu zmenšené na nulový rozmer. Staré údaje v nasledujúcej auditovej tabuľke sú označené ako stav pred úpravou.

Overenie: 68 testov v súboroch `twin-roof`, `babylon-scene-rendering`, `twin-design-preview`, `twin-active-house-area`, `twin-site`, `plan-documentation` a `active-windows` prešlo. Zahŕňajú pôvodnú a novú plochu, zachovanie celej krytej terasy, stabilitu pôdorysu, presahy 0/50 mm, výber strechy z archívneho príznaku a hranice reálnych mesh-ov vytvorených spoločnou funkciou `createRoofFace` v NullEngine. Skutočné `npm run docs:generate` prešlo s 1 968 komponentmi; generovaný pôdorysný JSON zostal bez zmeny. Integračný test nanovo extrahuje všetky komponenty bez konštruktora prehliadača a kontroluje aj obe hlavy portálu. Cielený ESLint zmenených zdrojových/testových súborov a `git diff --check` prešli. Toto je geometrické a lokálne programové overenie; nový výrobný návrh strechy ani povaly tým nevznikol.

## Strešný obal pred novým pokynom

Spoločná rímsa má Z = 3 125 mm a priesečník strešných rovín v hrebeni Z = 5 560 mm. Rozdiel je 2 435 mm. Parametre určujú štyri spojené roviny, dva hrebene, jedno úžľabie a jedno nárožie; nejde o štyri navzájom sa prekrývajúce celé sedlové strechy.

| Údaj | Hlavný trakt | Krídlo |
| --- | --- | --- |
| Vonkajší rozsah | X 6 440 až 28 040; Y 3 000 až 11 200 | X 21 040 až 28 040; Y 3 000 až 22 085 pred úpravou |
| Os hrebeňa | Y 7 100 | X 24 540 |
| Polovica priečneho rozpätia | 4 100 | 3 500 |
| Sklon z vrcholov | 30,706179687° | 34,826887273° |
| Plná šikmá dĺžka od rímsy po hrebeň | 4 768,566346 | 4 263,710239 |

Výpočet sklonu je atan(2 435 / polovičné rozpätie). Staré popisky `roofPitchDeg: 30`, `wingPitchDeg: 34` a `mainSlopeLengthMm: 4735` v [historickom zázname HOUSE.roof](../lib/twin-site.ts#L913) nie sú presnými hodnotami aktuálnych strešných vrcholov. Nesmú sa používať ako druhá geometrická autorita.

### Všetky obvodové hrany voči fasádam

Hotové vonkajšie modelové líca sú vonkajším povrchom ETICS alebo plného piliera, nie lícom samotného 300 mm muriva. [exteriorWallLayers](../lib/twin-facade.ts#L120) kladie izoláciu od vonkajšieho líca dovnútra; zateplenie sa k týmto súradniciam nepripočítava druhýkrát.

| Rovina / obvodový úsek | Líce fasády | Okraj geometrického plášťa pred úpravou | Vodorovný presah |
| --- | --- | --- | --- |
| Ulica S | Y 3 000; X 6 440 až 28 040 | Y 3 000 | 0 mm |
| Východ E | X 28 040; Y 3 000 až 22 035 | X 28 040 | 0 mm |
| Záhrada N | Y 11 200; X 6 440 až 21 040 | Y 11 200 | 0 mm |
| Západný štít W | X 6 440; Y 3 000 až 11 200 | X 6 440 | 0 mm k nominálnemu lícu |
| Vnútorný odkvap krídla WW | X 21 040; Y 11 200 až 22 035 | X 21 040 | 0 mm |
| Čelný portál krídla NN | Y 22 035; X 21 040 až 28 040 | Y 22 085 | **50 mm** |

Západný omietnutý štít je ako renderovaná plocha posunutý na X 6 432, teda 8 mm pred nominálne líce X 6 440. Samotná geometrická strecha je voči tejto ploche ustúpená o 8 mm; nejde o kladný presah. Zdroj: [buildGables](../lib/babylon-scene.ts#L4502).

Posledných 50 mm strechy bolo v `ACTIVE_JOINED_ROOF_PARAMETERS.wingEndYmm` odvodených ako `origin.y + wingOverallPlanLengthMm + wingEndOverhangMm`. Historická dĺžka krídla 19 085 mm zahŕňa tento presah; dom a podpery končia po 19 035 mm na Y 22 035.

### Vizualizačné lemovanie a odvodnenie

Tieto objekty nie sú nosným strešným obalom. Ich dnešná prítomnosť nepredstavuje vyriešený klampiarsky detail bezpresahovej strechy.

| Existujúci objekt | Skutočný modelový rozsah / presah |
| --- | --- |
| Predný krytý žľab | X 6 380 až 28 100; Y 2 887,5 až 2 992,5; Z 3 020 až 3 125. Pred uličné líce vystupuje 112,5 mm, na koncoch o 60 mm. |
| Záhradný krytý žľab | X 6 380 až 21 100; Y 11 207,5 až 11 312,5; rovnaké Z. Pred líce N vystupuje 112,5 mm. |
| Vnútorný žľab krídla | X 20 927,5 až 21 032,5; Y 11 140 až 22 105. Pred líce WW vystupuje 112,5 mm. |
| Vonkajší žľab krídla | X 28 047,5 až 28 152,5; Y 2 940 až 22 105. Pred líce E vystupuje 112,5 mm. |
| Biele šikmé lišty portálu | Y 22 035 až 22 105: 70 mm pred čelom podpier. Otočený profil výšky 180 mm vystupuje tiež o 51,398896 mm mimo bočné líca X 21 040 / 28 040. Horný obal dosahuje Z 5 779,276526, teda nad geometrický hrebeň. |
| Vrcholová krytka portálu | X 24 440 až 24 640; Y 22 033 až 22 107. Čelný presah 72 mm. Horné Z 5 741,638263. |
| Kovové hrany západného štítu | Rúrový profil polomeru 38 mm; NullEngine potvrdil min. X približne 6 402, teda 38 mm pred nominálne líce a 30 mm pred renderovaný štít X 6 432. Na koncoch zasahuje približne 16,8045 mm v Y mimo odkvapové konce. |
| Dažďové zvody | Vizualizačný Ø 100 mm, os 65 mm pred príslušným lícom, teda vonkajšok 115 mm pred ním. Nie sú odkvapovým presahom strešnej roviny. |

Zdroj žľabov a líšt: [buildRoofEdges](../lib/babylon-scene.ts#L4709), [biely portál](../lib/babylon-scene.ts#L4656), [dažďové zvody](../lib/babylon-scene.ts#L4224). Profil žľabov je v kóde výslovne označený ako vizualizačný. Starý komentár o vonkajšom líci bieleho rámu na Y 22 085 sa rozchádza s aktuálnou hodnotou `rakeFrontFaceYmm: 22105`; platí číselný parameter a odvodená geometria.

Hrebeňové profily, úžľabný a nárožný lem aj vizualizačné falce sú ďalšie objemy nad plášťom. Výšku 5 560 mm preto treba označovať ako výšku priesečníka strešných rovín, nie ako automaticky najvyšší bod všetkých klampiarskych dielov.

### Krytá terasa nie je odkvapový presah

Krytá terasa má čelo podpier Y 22 035 a zapustené zasklenie NN2 na Y 19 535. Rozdiel **2 500 mm je hĺbka krytej časti domu**, nie voľný odkvapový presah za obvodovú hmotu. Jej strechu neskracovať na rovinu zasklenia. Podobne záhradná lodžia má čelo Y 11 200, zadnú stenu Y 9 247 a hĺbku 1 953 mm.

[deriveJoinedRoofRenderPlan](../lib/twin-roof.ts#L403) už pred novým pokynom kreslí kovový plášť iba po Y 22 035. Historický 50 mm pás v architektonickej geometrii vizuálne preberá biely rám. Všeobecný biely podhľad končí na Y 19 535; osobitná drevená podbitka pokrýva Y 19 535 až 22 015, teda 2 480 mm s 20 mm ustúpením od čela. Obklad má v rendereri hrúbku 45 mm kolmo na rovinu a jeho strednica leží 60 mm pod strechou. Tieto hodnoty opisujú model, nie kompletnú skladbu strechy.

Prípustný architektonický opis po odstránení 50 mm je: **falcovaný plech, strešný obal bez odkvapových a štítových presahov za nominálne vonkajšie líca; kryté zapustené terasy zostávajú.** Presahy lemovania, odkvapov a fasádneho ukončenia treba samostatne uzavrieť detailom. Súčasný celý 3D obal vrátane uvedených profilov nemožno opísať ako „žiadny diel nepresahuje fasádu“.

### Plochy a falce

Plochy z presných trojuholníkov pred odstránením 50 mm; bez odpočtu dymovodu, prirážok na drážky, prekrytí, odpadu a samostatných lemovaní:

| Strešná rovina | Vodorovný priemet m² | Šikmá plocha m² |
| --- | ---: | ---: |
| MAIN_FRONT | 81,385000 | 94,656042 |
| MAIN_GARDEN | 67,035000 | 77,966060 |
| WING_INNER | 45,272500 | 55,151092 |
| WING_OUTER | 59,622500 | 72,632304 |
| **Spolu pred zmenou** | **253,315000** | **300,405498** |

Samotný 50 mm pás na celom 7 000 mm štíte predstavuje 0,350000 m² v pôdoryse a 0,426371 m² po sklone. Po jeho odstránení, pri nezmenenom sklone, vychádza 252,965000 m² vodorovne a 299,979127 m² po sklone. Toto nie je objednávkové množstvo plechu.

Modelový raster falcov: hlavný trakt odsadenie 360 mm a rozstup 760 mm v X; krídlo odsadenie 300 mm a rozstup 720 mm v Y. Každý segment je orezaný svojou strešnou rovinou. V 3D ide o rúrovú ilustráciu polomeru 8 mm so zdvihom osi 16 mm nad plášť, nie o výrobný profil drážky. Nový projekt musí určiť materiál a hrúbku plechu, typ drážky, užitočné šírky pásov, pevné a posuvné príponky, dilatáciu, podklad, separáciu, odvetranie, okrajové ukončenia, zaťaženie vetrom, odvodnenie, prepady a prestupy. Existujúci raster nepredpisuje rozstup krokiev ani výslednú výrobnú šírku.

## Skladovacia povala a drevené stropy

Potvrdeným účelom povaly je **odkladanie vecí s pochôdznym prístupom, bez bývania**. Nejde o obytné podkrovie ani zadanie novej izby. Potvrdené sú **drevené stropy bez betónovej stropnej dosky a bez nadbetonávky**. Tieto konštrukčné voľby nemenia pôvodný rozsah povaly, polohy podhľadov ani obal strechy. Zákaz betónovej stropnej dosky sa vzťahuje na strop a povalu; nemení samostatne zadané monolitické založenie a podlahovú dosku na teréne.

Miestnosti 1.01, 1.02, 1.04 až 1.12 a 1.14 majú plochý podhľad v Z 2 600 mm. Miestnosť **1.03 zahŕňa obývačku aj kuchyňu**, má katedrálový podhľad od 2 750 do 4 850 mm; výnimku pre povalu preto treba viazať na jej celú aktuálnu pôdorysnú plochu, nie iba na priestor sedačky. Zdroj: [INTERIOR_ROOMS](../lib/twin-interior.ts#L22), [ceilingElevationMm](../lib/twin-interior-baseline.ts#L1883).

Rozsah skladovacej povaly nad miestnosťami mimo 1.03 zostáva zachovaný a zahŕňa aj garáž 1.12 a technickú 1.07; zadanie ich z povaly nevylučuje. Súčet metadátových obdĺžnikov týchto miestností pred koordinačným orezaním stenami je **129,936635 m²**. Nie je to čistá použiteľná ani nosná plocha povaly: nepozná skutočné obsadenie stenami, úroveň jej podlahy, skladbu, podpery, prístup, prestupy ani pásy s nedostatočnou výškou. Rozsah nad krytými exteriérovými terasami nemožno automaticky pridať k vnútornej pochôdznej povale; zmenil by ich otvorený podhľad.

V aktuálnom modeli nie je navrhnutá nosná podlaha povaly, dimenzovaná drevená stropná sústava, jej únosnosť, prístupový otvor ani schodisko/rebrík. Rozdiel medzi plochým podhľadom Z 2 600 a strešným obalom je pri odkvape 525 mm a pri hrebeni 2 960 mm, ešte pred odpočítaním všetkých skladieb. Nad katedrálou je pri hrebeni rozdiel 710 mm medzi Z 4 850 a Z 5 560. Tieto rezervy nie sú svetlé výšky povaly ani dôkaz, že sa do nich zmestí konkrétny krov alebo drevený strop.

**Návrhové plošné aj sústredené zaťaženie skladovaním zostáva neurčené.** Samotné označenie „odkladanie“ nedáva oprávnenie dosadiť číselnú únosnosť; treba určiť prípustný spôsob a rozsah skladovania. Následný statický a stavebno-fyzikálny návrh musí stanoviť drevenú nosnú sústavu, prierezy a rozstupy, uloženie a kotvenie, pochôdzny záklop a jeho spoje, stabilitu a priehyb, nadväznosť na katedrálu, prístup, požiarne riešenie a vedenie rozvodov. Nosná skladba sa má vyriešiť v potvrdenom drevenom systéme bez betónovej dosky alebo nadbetonávky; chýbajúce dimenzie ani únosnosť táto správa nenahrádza.

## Podlahové kúrenie podľa nového rozsahu

Plochy zahŕňajú revíziu [priečky garáže SP14 zo 16. 9. 2026](construction-garage-partition.md): garáž +0,506345 m² vrátane zarovnania zuba pri regáli. Rozsah podlahového kúrenia zostáva rovnaký, pretože garáž je vylúčená.

Tabuľka používa aritmetický súčet aktuálnych metadátových obdĺžnikov izieb pred koordinačným orezaním stenami. Nejde o čisté použiteľné plochy ani o výkaz vykurovanej podlahy. Známy nesúlad v 1.03: obdĺžnik miestnosti siaha po Y 19 533, ale plná zadná stena začína už na Y 19 035. Časť obdĺžnika sa teda prekrýva s konštrukciou. Hodnotu 50,441838 m² ani súčty z nej nemožno označiť za čistú plochu. Pri grafickom vyznačení rozsahu majú presné steny prekryť plošné šrafy; samotné šrafovanie neopravuje metadátový výkaz.

| Miestnosť | Súčet metadátových obdĺžnikov m² | Súčet po výlukách zadania, pred orezaním stenami m² | Rozhodnutie |
| --- | ---: | ---: | --- |
| 1.01 Zádverie, chodba, vstup | 6,456724 | 6,456724 | zahrnúť |
| 1.02 Spoločná chodba | 16,276116 | 16,276116 | zahrnúť |
| 1.03 Obytný priestor s kuchyňou | 50,441838 | 50,441838 | zahrnúť |
| 1.04 Pracovňa | 12,135290 | 12,135290 | zahrnúť |
| 1.05 Kúpeľňa a práčovňa | 7,214871 | 6,089871 | zahrnúť okrem sprchy 1,125000 m² |
| 1.06 WC | 3,418200 | 3,418200 | zahrnúť |
| 1.07 Technická miestnosť | 7,989019 | 0 | vylúčená |
| 1.08 Dievčenská izba | 15,406584 | 15,406584 | zahrnúť |
| 1.09 Chlapčenská izba | 15,406584 | 15,406584 | zahrnúť |
| 1.10 Spálňa | 11,050400 | 11,050400 | zahrnúť |
| 1.11 Kúpeľňa | 5,297780 | 5,297780 | zahrnúť; obsahuje vaňu, nie ďalšiu modelovanú sprchu |
| 1.12 Garáž | 25,151355 | 0 | vylúčená |
| 1.14 Šatník | 4,195400 | 4,195400 | zahrnúť |
| **Spolu** | **180,440161** | **146,174787** | metadátové obaly pred orezaním stenami a ďalšími prekážkami |

Sprcha v 1.05 sa preberá z `BATHROOM_FITOUT.shower.footprintMm`: **X 26 291 až 27 541; Y 6 652 až 7 552**, rozmery **1 250 × 900 mm**, plocha **1,125000 m²**. Je celá v aktuálnom východnom výklenku 1.05. Vylúčiť celý sprchový obdĺžnik, nielen žľab alebo sklenenú zástenu. Lineárny odtok je X 27 391 až 27 471, Y 6 752 až 7 452; jeho 80 × 700 mm pôdorys nenahrádza rozsah sprchy. Zdroj: [sprchový fitout](../lib/twin-interior-baseline.ts#L1120), zachovaný cez [technical-design](../lib/technical-design.ts#L140) a [aktívny fitout](../lib/twin-interior.ts#L50), [skutočný render sprchovej plochy](../lib/babylon-interior.ts#L2350).

Starý text [HEATING_OPERATION_NOTES](../lib/technical-design.ts#L111) vymenúva iba časť izieb s podlahovkou a hovorí o samotných rebríkoch v kúpeľniach. **Nový pokyn ho v rozsahu podlahového kúrenia nahrádza:** zahŕňa obe kúpeľne mimo sprchy, chodby, zádverie a šatník. Pôvodné rebríky nie sú týmto auditom odstránené. Samostatné teleso v garáži a vykurovanie technickej miestnosti sa týmto zoznamom podlahových okruhov neurčujú.

Hodnota 146,174787 m² je iba súčet metadátových obalov po odčítaní technickej miestnosti, garáže a sprchy, pred koordinačným orezaním stenami. Nie je čistou použiteľnou alebo aktívnou vykurovacou plochou ani výpočtom potrebného výkonu. Návrh musí najprv odrátať konštrukcie a potom vyriešiť pevné skrine, kuchynský ostrov a linku, vaňu, ďalšie zariadenia, odstupy rúrok, dilatácie a tepelné straty po miestnostiach. Chýbajú rozstupy a dĺžky okruhov, rozdeľovače, regulácia, prietoky, tlakové straty, teplotný režim a úplná skladba podlahy. Záväzná požiadavka vedenia vody a odpadu nad nosnou doskou zostáva.
