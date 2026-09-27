# Overená obec v okolí — pôdorysy a odhadované objemy

`scripts/unreal/exterior-buildings.py` vytvára nízkopolygónový vzdialený kontext
podľa oficiálnych 2D pôdorysov [ČÚZK INSPIRE Buildings WFS](https://services.cuzk.gov.cz/wfs/inspire-bu-wfs.asp).
Pôvodný výstup R1 zostáva zmrazený. Aktuálna revízia striech je
`output/unreal/exterior-buildings-20260926-r2/building-plan.json`, odvodená
samostatným `scripts/unreal/exterior-building-roofs.py`.

**Pôdorysy pochádzajú z úradného zdroja; výšky, strechy a farby sú odhadované.**
Nie je to zameraný 3D model obce. Zdroj deklaruje horizontálnu odhadovanú
presnosť 1,5 m. Milimetrová transformácia do spoločného rámca nezvyšuje
presnosť zdroja.

## Čo poskytol živý zdroj

Výrez 2 × 2 km v EPSG:5514 okolo národného východiska scény vrátil
26. 9. 2026 celkovo 710 prvkov Building: 708 polygonových pôdorysov
a dva bodové prvky. Ďalších 681 BuildingPart sú bodové reprezentácie častí
budov; negenerujú sa z nich ďalšie stavby. Všetky výšky, elevácie a počty
podlaží sú v tomto výreze `nil` s dôvodom `Unpopulated`.

Služba aj význam polygonových a bodových reprezentácií sú popísané v
[technickej dokumentácii ČÚZK](https://services.cuzk.gov.cz/doc/inspire-bu-data.pdf).
Plné GML odpovede a receipts s dotazom, časom služby a SHA-256 zostávajú v
`output/unreal/exterior-building-audit-20260926-r1/inputs`. Nad nimi vznikol
`building-footprints.json`; ten je v následnom pláne pripnutý hashom.

V okruhu 100 m nie je žiadny polygonový footprint. Do 180 m sú tri,
do 300 m 35, do 500 m 196 a do 1 km 651. Najbližší začína 159,28 m od
scény. Žiadny nepretína overené rozvojové parcely 6012/* alebo 6035/*.
Pôdorysy na okraji 1 km zostávajú celé; polygón sa neodrezáva v strede budovy.

Pôvod údajov: **© ČÚZK, INSPIRE Buildings, CC BY 4.0; získané 26. 9. 2026,
transformované do lokálneho rámca a doplnené odhadovanými objemami.**
[Licenčné podmienky ČÚZK](https://cuzk.gov.cz/Predpisy/Podminky-poskytovani-prostor-dat-a-sitovych-sluzeb/Podminky-poskytovani-prostorovych-dat-CUZK.aspx).

## Pôvodné grafické objemy R1 a napojenie

Plán zachováva všetkých 651 zdrojových polygonov vrátane vnútorných dier.
Fasády sledujú pôvodný obvod. Výška steny je deterministický autorský odhad
2,8–3,3 m; nízka valbová strecha má odhadovaný vzostup 1,4–1,75 m.
132 jednoduchých obdĺžnikových pôdorysov má pozdĺžny hrebeň, 110 ďalších
konvexných pôdorysov nízku ihlanovú strechu a 409 členitých pôdorysov
výslovne označený plochý fallback. Tento fallback nie je tvrdením o skutočnom
tvare strechy. Odhadovaná pálená a sivá krytina ani omietka nie sú skenmi
konkrétnych miestnych stavieb.

Výška každého bodu základov sa počíta barycentrickou interpoláciou priamo
zo skutočných trojuholníkov `exterior-terrain-20260926-r4`. Zohľadňuje teda
aj tamojšie grafické napojenie a označené ploché pozadie. Obvody majú vzorky
v intervale najviac 2,5 m; spodok fasády je zapustený 8 cm, aby nevznikali
medzery pri zmene sklonu hrubšieho výškového rastra. Odkvap je nad najvyššou
vzorkou daného obvodu plus odhadovaná výška steny.

Výsledok má **237 mesh v 88 bunkách po 100 m a 35 152 trojuholníkov**.
Všetky sú vizuálne, bez kolízií. Nepridávajú sa cesty. Používajú materiály
`context_village_wall`, `context_village_roof` a `context_village_darkroof`.
Importer má rešpektovať `castShadow=true` a `maxDrawDistanceCm=125000`,
aby pohľad z okolia domu obsiahol aj vzdialený okraj kilometrového výrezu.

## Generovanie a overenie

### Strechy členitých pôdorysov R2

Natívna kontrola R3 ukázala, že 409 plochých fallback striech R1 pôsobí
ako jednoduché krabice. R2 nahrádza iba tieto strechy nízkym odhadom podľa
vzdialenosti od obvodu. Pôdorysy, fasádne mesh, všetkých 15 523 výškových
vzoriek základov, odkvapy, materiálové kľúče a nastavenie vykresľovania
zostávajú presne rovnaké. Geometria ostatných 242 striech ostáva identická.

Vnútorné body v 2 m rastri a v pôvodných trojuholníkoch vytvoria Delaunayovu
trianguláciu, orezanú presne na pôdorys vrátane nádvorí. Výška vrcholu nad
odkvapom je `min(150 cm, 0,65 × vzdialenosť od hranice)`. Na obvode aj
okrajoch vnútorných dier je preto nulová. Nad členitými krídlami vzniknú
nízke valbám podobné plochy s obmedzeným vzostupom. Táto formulácia
**nie je meraním ani rekonštrukciou skutočných striech**; WFS stále nemá
žiadne vyplnené výškové údaje. Farebnosť rieši samostatný natívny materiál.

R2 má **89 591 trojuholníkov**, rovnakých 237 mesh a 88 buniek po 100 m.
Najväčší mesh má 2 020 trojuholníkov. Päť nezávislých testov overuje
nemenné pôdorysy, fasády, základy a 242 jednoduchých striech; ďalej pokrytie
členitých pôdorysov bez presahov či prekrývania, zachovanie vnútorných dier,
normály smerujúce nahor, odhadovanú výškovú funkciu a vstupné hashe.

```sh
output/unreal/exterior-tools-py312-20260926/bin/python -B scripts/unreal/exterior-building-roofs.py \
  --base-plan output/unreal/exterior-buildings-20260926-r1/building-plan.json \
  --output output/unreal/exterior-buildings-20260926-r2
output/unreal/exterior-tools-py312-20260926/bin/python -B -m unittest discover \
  -s scripts/unreal -p test_exterior_building_roofs.py -v
```

R2 nemení zmrazený generátor R1. Natívny vzhľad a výkon sa overujú osobitne.

### Generovanie pôvodného R1

```sh
output/unreal/exterior-tools-py312-20260926/bin/python -B scripts/unreal/exterior-buildings.py \
  --footprints output/unreal/exterior-building-audit-20260926-r1/building-footprints.json \
  --terrain output/unreal/exterior-terrain-20260926-r4/terrain-plan.json \
  --context output/unreal/exterior-context-20260926-r5/context-plan.json \
  --scene output/unreal/realism-20260926-r5/geometry/scene.json \
  --output output/unreal/exterior-buildings-20260926-r1
output/unreal/exterior-tools-py312-20260926/bin/python -B -m unittest discover \
  -s scripts/unreal -p test_exterior_buildings.py -v
```

Existujúci výstup sa neprepisuje; ďalšia revízia potrebuje nový adresár.
Päť testov prešlo: presná zhoda pôdorysov, vylúčenie bodových prvkov,
nezasiahnutie architektúry, pripnuté zdroje, geometra na pôdorysoch,
orientácia striech, výšky základov a známy analytický sklon testovacieho terénu.
`massing-overview.png` je skontrolovaná technická projekcia mesh, nie natívny
render. Natívny vzhľad, uloženie scény a výkon zostávajú samostatným overením.

Oficiálny DMP 1G ImageServer síce poskytuje F32 povrch vrátane stavieb,
ale uvádza pôvod skenovania 2009–2013. Táto revízia ho nepoužíva ako zdroj
aktuálnych výšok budov; dostupnosť služby sa nesmie zamieňať s overením
konkrétnych dnešných striech.
