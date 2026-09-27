# Okolie Březí — katastrálne hranice a krajina

`scripts/unreal/exterior-context.py` pripravuje doplnkovú scénu okolia hlavného
návrhu C/B/B. Hranice parciel získava zo služby
[ČÚZK INSPIRE WFS — Cadastral Parcels](https://services.cuzk.gov.cz/wfs/inspire-cp-wfs.asp).
Podklad zo zadania slúži na interpretáciu polí, nízkych riadkov porastu a
nezastavaných susedných pozemkov. Satelitná snímka sa nepoužíva ako textúra.

Aktuálna geometrická revízia má nemenný vstup a plán v
`output/unreal/exterior-context-20260926-r7`; staršie plány zostávajú zachované.
R6 preberá geometriu a pôvodné polohy R5 bez zmeny a nahrádza iba vizuálne
nevyhovujúce `meadowBasePlacements` hustejším `meadowBladePlacements`.
Samostatný generátor `exterior-meadow-blades.py` nemení pôvodný
`exterior-context.py` ani jeho SHA-256 vo vstupoch predchádzajúcich revízií.
R7 opravuje iba identitu generátora R6: `owner` teraz ukazuje na
`scripts/unreal/exterior-meadow-blades.py`, ktorého hash zodpovedá
`generatorSha256`. Pôvodný zdroj R6 bol pred opravou uložený do
`exterior-context-20260926-r6/inputs/exterior-meadow-blades-r6.py`.
Plán aj receipt R6 ostávajú nezmenené; všetky geometrické a výsadbové polia
R7 sú presne rovnaké ako R6. Štyri regresné testy `test_exterior_meadow_revision.py`
overujú túto zhodu, archivovaný zdroj a natívne rozlíšenie identity generátora.
Spoločné nástroje medzi R6 a R7 zmenili NumPy 2.5.3 na 2.4.6. Presný pôvodný
`numpy/__init__.py` bol preto obnovený z oficiálneho wheel PyPI do
`R6/inputs/runtime-snapshot`; jeho hash sa zhoduje s nemenným receipt R6.
Archivovaný je aj wheel, metadata PyPI a vysvetľujúci receipt. Historický test
R6 overuje tento zdroj, kým test R7 overuje aktuálne prostredie 2.4.6.
Obnovenie nevykonalo inštaláciu ani zmenu živého Python prostredia.
Vstup `inputs/cuzk-parcels.gml`
obsahuje 117 prvkov. `inputs/source-receipt.json` uchováva presný dotaz,
čas získania, čas služby a SHA-256 odpovede. Ďalšie spustenie neobnovuje ani
neprepisuje existujúci podklad; odlišný výstup vyžaduje nový adresár.

Údaje sú poskytované pod licenciou
[CC BY 4.0 podľa podmienok ČÚZK](https://cuzk.gov.cz/Predpisy/Podminky-poskytovani-prostor-dat-a-sitovych-sluzeb/Podminky-poskytovani-prostorovych-dat-CUZK.aspx).
Uvádzanie pôvodu: **© ČÚZK, INSPIRE Cadastral Parcels, CC BY 4.0; získané
26. 9. 2026**. Stav a úpravy sú rozlíšené v pláne: národné súradnice sú
zdrojové údaje; lokálna transformácia, orezanie, povrchové materiály a osadenie
ilustračného porastu sú odvodenou vizualizáciou. Žiadne údaje o vlastníkoch
sa nevyžadujú ani neukladajú.

## Súradnice a ochrana domu

Transformácia používa `cadastralDatumSjtskMm`, `siteAxis`, `housePlacement`
a `sceneCenterMm` z aktuálneho exportu. Najskôr zaokrúhli C3 projekciu na
milimetre a až potom odpočíta klientsky posun domu 77,913405454 mm. Následne
prevedie OBJ súradnice do Unrealu: X/10, −Y/10, Z/10. Zaokrúhlenie už
posunutého počiatku by nezodpovedalo `twin-house-placement.ts`.

Všetkých 13 katastrálnych prstencov prítomných v spoločnom exporte bolo pri
generovaní porovnaných s aktuálnou WFS odpoveďou; zhodujú sa v celočíselných
milimetroch. Zmena ľubovoľného z nich zastaví generovanie. C/B/B a oba odstupy
3 000 mm sú kontrolované samostatne.

Zo všetkých nových povrchov aj z vyznačenia hraníc sa geometricky odčíta celý
pozemok 6012/26 a skutočné projekcie zdrojových trojuholníkov DOM_00002–00008
a DOM_00048–00059. Tým sa zachová existujúca cesta, krajnice, obrubníky
a tri prístupy. Pri cestnej parcele 6012/1 zostávajú tri vnútorné prstence;
cesta sa nevylieva cez bloky stavebných pozemkov.

Nové plochy sú orezané na rámec 360 × 360 m. Časť rámca, kde výrez WFS nemá
úplné pokrytie, zostáva na existujúcom vzdialenom teréne. Pôvodné schematické
kilometrové pokračovania ciest je možné vypnúť iba v novom doplnkovom importe;
zdrojové komunikácie a všetky kolízie zostávajú zachované.

## Vizuálna interpretácia

Plán obsahuje 96 povrchov, spoločnú vrstvu prerušovaných značiek
a tri zdieľané prototypy kolíka, vinohradníckeho stĺpika a drôtu:
100 mesh, 69 092 trojuholníkov. Žiadny mesh neprekračuje 8 338 trojuholníkov.
Okolité stavebné parcely majú 229 jedinečných
úsekov hraníc, naznačených sivobielym pásom širokým 70 mm, s dĺžkou značky
2,8 m a medzerou 1 m. Dvanásť drobných drevených kolíkov je ilustračných;
nejde o tvrdenie, že na mieste existujú alebo že nahrádzajú vytýčenie.

Parcely 6015 a 6034 vytvárajú pásy riadkového porastu pozdĺž polí.
Plán poskytuje 2 824 polôh nízkeho porastu vysokého 1,32–1,48 m. Označenie
`vineyard-row` vyjadruje čítanie riadkov na používateľovej snímke, nie
potvrdený druh rastlín ani zameranie konkrétnych kmeňov. Medzi radmi je 2,4 m,
medzi navrhnutými trsmi 1,1 m s malým nepravidelným rozptylom. Celá koruna
má odstup od hraníc a pôvodných komunikácií. Nepridávajú sa vymyslené domy.

Riadky majú 539 inštancií stĺpika 50 × 50 × 1 600 mm a 1 040 úsekov drôtu
s priemerom 5 mm vo výške 900/1 350 mm. Opory sú od seba najviac 6 m;
prerušenia pri hraniciach a cestách sa nespájajú cez medzery. Aj táto konštrukcia
je ilustračná. Dva malé prototypy používajú HISM skupiny s obmedzenou
vzdialenosťou vykreslenia; drôt nevrhá tieň. Orientácia trojuholníkov zodpovedá
výpočtu normál v existujúcom `rural-import.py`.

Právna cestná parcela už nie je interpretovaná ako celoplošný svetlý asfalt.
GEOS vytvára vnútornú jazdnú plochu a zelené krajnice: pri 6012/1 a 6035/1
odsadí jadro 2,5 m od právneho okraja, pri užšej poľnej ceste 6013/6019 o 0,9 m.
Jadro a krajnice spolu presne vypĺňajú pôvodný polygón vrátane všetkých dier;
šírka jazdnej plochy je vizuálna interpretácia, nie meranie. Materiál poľa 6041
je samostatný `context_arable`, ostatné zelené polia používajú `context_crop`.

Zo starého dvojradového vetrolamu ostávajú v doplnkovom pláne iba štyri
vybrané polohy pre záhradný kontext. Každá koruna s priemerom 3 m sa zmestí
do pásu 6014, pričom stred má aspoň 1,6 m od hraníc tohto pásu aj chránenej
parcely/komunikácií. Navrhnutá výška je 4,2 m. Ide o výsadbový koncept
zachovávajúci vybrané staršie polohy, nie potvrdenie skutočných stromov.
Ďalších 2 996 nepravidelne zoskupených trsov trávy sa nachádza na blízkych
susedných plochách mimo vlastnej parcely a pôvodných povrchov; stred trsu
s polomerom 350 mm má odstup aspoň 450 mm od chránenej geometrie.

Zdrojový terén označený ako DMR 5G je v tomto exporte plochou Z = −20 cm.
Nové polia používajú základ −18,2 cm a drobnú odchýlku ±0,75 cm;
pokračovania komunikácií −11,5 cm. Sú to explicitné grafické predpoklady
v existujúcom rámci, nie výšky z geodetického zamerania alebo nového DMR.

## Súvislá tráva R5

Samostatné pole `meadowBasePlacements` pridáva **24 579** zelených trsov
s výškou 18–25 cm a plným polomerom 22 cm, z toho **2 193** na cestných
krajniciach. Vychádza výhradne z už existujúcich `context_meadow` trojuholníkov
v okruhu 90 m. Pokrýva všetkých 25 dostupných lúčnych plôch; súčet ich výmery
je 12 077 m². Celá koruna ostáva na lúčnom povrchu, stred má aspoň 25 cm
od chránenej parcely a pôvodnej komunikácie. Dom, vlastná parcela, cesty,
riadky vinohradu, opory a všetky predchádzajúce polia plánu zostávajú nezmenené.

Vzorkovanie používa 65 cm mriežku otočenú o 23°, nezávislý rozptyl ±23 cm
a mierne priestorové zvlnenie. Plynulé polia hustoty a výšky majú mierku
5–12 m, aby porast tvoril súvislý základ. Native importer má použiť iba
`grass_bermuda_clump`, bez troch dodatočných pôdopokryvných rastlín na každý
trs. Maximálny culling je 90 m.

`meadow-density-audit.json` a štyri testy v `test_exterior_meadow.py` overujú
všetky koruny a zachovanie pôvodných R4 polí. V 464 päťmetrových dlaždiciach
s aspoň 10 m² použiteľnej lúky nie je žiadna prázdna; najnižšia lokálna hustota
je 1,57 trsu/m². Analýza používa 1 μm presnosť GEOS na odstránenie nulových
vnútorných švov zo zjednotenia plávajúcich trojuholníkov. Zdrojové súradnice
ani mesh sa tým nemenia; rozdiel analyzovanej plochy je 0,00147 m².

Reprodukcia R5 používa rovnaký príkaz nižšie s novým adresárom a argumentom
`--base-plan output/unreal/exterior-context-20260926-r4/context-plan.json`.
Počet tráv a geometrická kontrola ešte nepotvrdzujú natívny vzhľad či výkon.

## Generovanie a overenie

### Husté nízke steblá R6

Natívne zábery R3 odmietli R5: veľké skenované trsy pôsobili ako svetlé
ostrovčeky na hladkom povrchu. R6 používa **382 678** polôh pre pôvodné
`nativeLawnTuft0–3` a `blade_material`; ide o rovnaký typ nízkej geometrie
ako v trávniku pri dome. Neobsahuje už `meadowBasePlacements` ani jeho policy.
Rozmiestnenie pokrýva rovnakých 25 lúčnych plôch s výmerou 12 077 m²,
vrátane **40 490** trsov na krajniciach. Priemer je **31,69 trsu/m²**.

Mriežka má rozstup 17 cm, otočenie 31,7°, nezávislý rozptyl ±6 cm a mierne
priestorové zvlnenie. Plynulé polia obsadenosti 90–98 % a výšky 14–25 cm
nemajú obdĺžnikové hranice zón. Celý polomer každého trsu je 14 cm,
stred ostáva aspoň 16 cm od chránenej parcely a pôvodných komunikácií.
Maximálny dosah vrátane koruny je 90 m; rovnaký limit má vykresľovanie.
Importér musí pri škálovaní dodržať polomer pre **každý LOD** prototypu.
Výška každého koreňa je barycentricky odvodená z pôvodných trojuholníkov
lúky; nemení sa mesh, zdrojový terén ani výška záhrady.

`meadow-blade-audit.json` a päť testov `test_exterior_meadow_blades.py`
overujú všetky polohy, celé koruny, cesty, pôvodnú geometriu, polia plánu
a vstupné hashe. Hustota nepredstavuje meranie nepriehľadného pokrytia listami;
natívny vzhľad, škálovanie LOD a výkon sa musia overiť zvlášť.
Nezávislé zjednotenie trojuholníkov navyše uzatvára numerické švy užšie než
2 μm; rozdiel analyzovanej výmery je iba 0,602 cm². Táto normalizácia slúži
výhradne na kontrolu a nemení žiadny zdrojový vrchol ani výslednú polohu.

```sh
output/unreal/exterior-tools-py312-20260926/bin/python -B scripts/unreal/exterior-meadow-blades.py \
  --base-plan output/unreal/exterior-context-20260926-r5/context-plan.json \
  --output output/unreal/exterior-context-20260926-r6
output/unreal/exterior-tools-py312-20260926/bin/python -B -m unittest discover -s scripts/unreal -p test_exterior_meadow_blades.py -v
```

Výstupný adresár R6 je už použitý; ďalšie generovanie vyžaduje nové meno.
Plán používa kompaktný JSON kvôli počtu polôh. Pôvodné hodnoty geometrie
zostávajú pri dekódovaní presne rovnaké ako R5.

### Pôvodný geometrický kontext

```sh
python3.12 -m venv output/unreal/exterior-tools-py312-20260926
output/unreal/exterior-tools-py312-20260926/bin/python -m pip install shapely==2.1.2
output/unreal/exterior-tools-py312-20260926/bin/python -B scripts/unreal/exterior-context.py \
  --geometry output/unreal/realism-20260926-r5/geometry \
  --output output/unreal/exterior-context-20260926-r4 \
  --reference-image /absolutna/cesta/k/podkladu.png
output/unreal/exterior-tools-py312-20260926/bin/python -B -m unittest discover -s scripts/unreal -p test_exterior_context.py -v
```

Príklad výstupného adresára je už použitý; ďalšia revízia potrebuje nové meno.
Generátor používa Python 3.12, izolovaný Shapely 2.1.2 a existujúci balík
`earcut` v repozitári; závislosti projektu sa nemenia.
Nespúšťa Unreal a nemení zdrojovú scénu.

Prešlo 15 kontrol vrátane zaokrúhlenia transformácie, zachovania vnútorných
prstencov, nemennosti podkladu, orientácie trojuholníkov a prieniku **každého**
nového trojuholníka s chránenou parcelou a pôvodnými povrchmi. Kontrola sa
neobmedzuje na stredy trojuholníkov. Overuje sa aj úplné rozdelenie právnych
cestných polygónov, koruny vinohradu, bezpečnosť celých úsekov drôtu a jeho
normály. `geometry-overview.png` z R3 je skontrolovaný
technický pôdorysný náhľad a nemá sa prezentovať ako natívny render.

`context-plan.json` zahŕňa štyri doplnkové kamery. Natívny import, správne
priradenie materiálov, obrazová kvalita a výkon sa overujú až v samostatnom
novom balíku; geometrický plán sám osebe nie je potvrdením fotorealizmu.
