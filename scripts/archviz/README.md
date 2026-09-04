# DOM → Blender Cycles ArchViz

Lokálny pipeline používa skutočne zostavenú Babylon scénu, nie zjednodušený
prepis pôdorysu. Overený runtime: **Blender 5.2.1 LTS, Apple M3, Metal,
24 GB RAM, Node 22**. Webová aplikácia zostáva zdrojom architektonickej geometrie.

## Spustenie

Z koreňa repozitára:

```sh
npm ci
npm run archviz:setup
npm run archviz:preview
npm run archviz:render
npm run archviz:open
```

`setup` pripraví Chromium pre export a 55 overovaných CC0 súborov. Na tomto
Macu je Blender už v `/Applications/Blender.app`. Ak chýba na inom Macu:

```sh
brew install --cask blender
```

Alternatívny Blender nastav cez `BLENDER_BIN=/absolutna/cesta/Blender`.
Adresár výstupov možno zmeniť cez `ARCHVIZ_OUTPUT=/absolutna/cesta`.
Pipeline vždy čaká na dokončenie a pri chybe skončí nenulovým návratovým kódom.
Netreba platené pluginy ani cloudový renderovací účet.

```sh
# Len geometria: OBJ + MTL v mm, JSON s pôvodnými rozmermi a metadátami
npm run archviz:export
# Zostaví aj GLB v metroch a zabalený .blend, bez renderu
npm run archviz:build
# 4K, pohľad z ulice alebo z interiéru
npm run archviz:render -- --camera street
npm run archviz:render -- --camera courtyard
npm run archviz:render -- --camera interior --date-time 2026-09-04T18:00:00+02:00
# CPU fallback, napríklad pri chybe Metal ovládača
npm run archviz:preview -- --device cpu
# Kontroly exportéra a geometrickej mierky po zostavení
npm run archviz:test
node scripts/archviz/validate.mjs
```

Pri zmenách len renderovacieho skriptu nie je nutné znovu exportovať geometriu:

```sh
/Applications/Blender.app/Contents/MacOS/Blender \
  --background --factory-startup --python-exit-code 1 \
  --python scripts/archviz/build.py -- --quality final --camera garden --render
```

## Výstupy

V `output/archviz/` (ignorované Gitom, nepublikované na webe):

| Súbor | Obsah |
| --- | --- |
| `dom-mm.obj`, `dom-mm.mtl` | Geometria, názvy objektov a materiálové sloty, jednotka mm |
| `scene.json` | Pôvodné integer-mm dáta, zdroje, transformácie parcely, názvy, rozmery, SHA-256 |
| `dom.glb` | Prenosná základná geometria v metroch, štandard glTF 2.0 |
| `dom-archviz.blend` | Cycles materiály, kamery, slnko, rastliny a zabalené textúry |
| `garden-final.png` | 3840 × 2160, 16-bit PNG, AgX, adaptívne vzorkovanie a denoise |
| `garden-preview.png` | Rýchlejší 1280 × 720 náhľad |
| `build-report.json` | Zostavenie, zariadenie, geodézia, rozmerová odchýlka |
| `*-report.json` | Záznam vznikne až po úspešnom dokončení renderu |

OBJ zachováva samostatné logické objekty; opakované tenké Babylon inštancie
sa expandujú do pôvodných pomenovaných skupín, aby plot ani živý plot nestratili
diely. Základy sú dostupné v samostatnej skrytej kolekcii. Technické schematické
trasy sietí sú archívny podklad, nie zameraná podzemná geometria. Pomocné
hmotové kvádre, popisy parciel, obloha, kolízne proxy a neaktívny avatar sa
nezaradia do renderu. Presné dôvody sú v `scene.json.skipped`.

### Mierka a orientácia

Zdrojové dáta zostávajú v integer milimetroch. Babylon používa metre, Y hore;
OBJ používa mm, Z hore:

```text
OBJ X = planXmm − 15200
OBJ Y = planYmm − 10800
OBJ Z = výškaMm
Blender: OBJ import scale 0.001, potom aplikovať transformácie objektov
GLB: metre; už neškálovať o 0.001 ani o 1000
```

Blender kontroluje všetky svetové bounding boxy oproti exportu, limit 0,5 mm.
Overený bazén má 6000 × 2700 mm a pôvodnú hladinu −12 mm. Export nemení rozmery
stavby; float32 renderovacie vrcholy majú malú numerickú odchýlku. Optické
vlnky vody, bevel hrán a nové rastliny sú oddelené vizualizačné úpravy.

Geolokácia sa počíta z `twin-site.SUBJECT_PARCEL_SJTSK_ORIGIN_MM` a `SITE_AXIS`,
približne **48.81759° N, 16.55278° E**. Starý lokálny origin z `twin-domain.ts`
sa na umiestnenie renderovacej scény nepoužíva. +Y pôdorysu nie je sever.
Datum transformácia je vhodná pre svetlo, nie na geodetické vytyčovanie.

Predvolený `garden` ukazuje celý dom spoza zadnej hranice. `courtyard` je
bližší záber z dvora pri bazéne; `interior` vychádza z overeného stojaceho
bodu obývacej izby a má voľný výhľad ku kachliam a preskleniu terasy.

## Vzhľad a nastavenia

`config.json` obsahuje kamery, čas s explicitným UTC offsetom, hustotu trávy,
seed, expozíciu a kvalitu. Prednastavenie final: 4K, najviac 256 vzoriek,
adaptívny prah 0,012, odrazy aj refrakcia, AgX. `--samples 128` je rýchlejší
variant; zvýšenie počtu vzoriek pomáha najmä pri skle a vode.

- Omietka, drevo, betón, dlažba a štrk používajú CC0 fotografie a mapy drsnosti
  a výšky v reálnej mierke. Trojplanárne premietanie používa bump z výšky, aby
  nesprávna tangentová báza nedeformovala normály stien.
- Rámy a kovové oplotenie: jemný práškový náter, obrazovková aproximácia
  **RAL 7016**. Presný farebný súlad s fyzickou vzorkou vyžaduje kalibráciu.
- Sklo: IOR 1,52, skutočný prenos svetla. Voda: IOR 1,333, uzavretý optický
  objem, absorpcia a geometrické vlnky. Cycles MNEE je zapnuté na slnku,
  hladine a bazéne; sila viditeľnej kaustiky závisí od uhla a svetla.
- Ulica zachováva dláždený povrch podľa existujúceho projektu. Materiál
  `ARCHVIZ_ASPHALT` je pripravený v `.blend` na priradenie asfaltovej ploche.
- Fyzikálna obloha a slnko používajú geografický sever a výpočet slnečnej
  polohy podľa dátumu. Stav atmosféry a expozícia sú vizualizačné nastavenia,
  nie meranie aktuálneho počasia.
- Interiér osvetľuje Cycles globálne osvetlenie cez skutočné otvory a svietidlá;
  kachle majú žiarivé uhlíky a teplé bodové svetlo. Tráva a rastliny sú
  zdieľaná 3D geometria. Náletové stromy za parcelou sú ilustračné okolie.
- Zjednodušené terasové kreslá vo výslednom renderi nahrádza detailný CC0
  drevený bistro set. Pôvodné objekty zostávajú v presnom geometrickom exporte;
  styling má vlastnú kolekciu. Vzdialený pás stromov je vizualizačné okolie.

## Prechádzka

Otvoriť `npm run archviz:open`. Príkaz nastaví Metal pre aktuálny proces Blenderu
bez prepísania používateľských preferencií. Vo Viewporte vybrať kameru, prípadne Rendered
pre Cycles náhľad. Blender menu **View → Navigation → Walk Navigation**
spustí prechádzku: WASD, myš, Q/E hore/dole; ľavé tlačidlo potvrdí, Esc zruší.
Predvolená klávesová skratka závisí od klávesnice (Shift + grave accent).

Cycles náhľad sa po pohybe postupne dopočíta; na M3 to nie je garantovaná
plynulá herná fotorealistická prechádzka. Material Preview je rýchlejší.
Existujúca webová Babylon prechádzka zostáva dostupná. Samostatná aplikácia
UE5/Lumen vrátane interakcií nie je súčasťou tohto pipeline.

## Overenie a hranice

`archviz:test` overuje prevod osí, inštancie, materiálové sloty, winding,
OBJ syntax a časové/geografické transformácie. `validate.mjs` kontroluje
checksum, pokrytie kategórií, bazén a Blender import; `npm test` overuje
existujúcu aplikáciu. Uložený `.blend` nie je dôkaz dokončeného PNG renderu.

`npm run archviz:validate -- --render` navyše overí 4K PNG, 16-bitovú hĺbku,
SHA-256 a zhodu použitých renderovacích skriptov a konfigurácie.

Pri prvom spustení môže Metal niekoľko minút kompilovať renderovacie kernely.
4K výpočet potom využíva GPU; čas výrazne závisí od uhla, transparentných
listov, odrazov a počtu vzoriek. Výstup sa uloží až po dokončení.

Fotorealizmus sa hodnotí výsledným záberom. Pipeline sám osebe nezaručuje
nerozoznateľnosť od fotografie zo všetkých uhlov: geometrické detaily,
ilustračné okolie a zariadenie zdedili úroveň pôvodného modelu. Finálne zábery
treba posúdiť vizuálne; interiérové svetlo a styling možno doladiť v Blenderi.

## Zdroje a licencia

**Powered by Poly Haven.** Nové fotografie a rastliny sú CC0; konkrétni autori,
URL, veľkosti a kontrolné súčty sú v `assets.lock.json`. Lokálne existujúce
textúry projektu zostávajú pod jeho pôvodnými podmienkami.

- [Poly Haven CC0](https://polyhaven.com/license)
- [Poly Haven API terms](https://github.com/Poly-Haven/Public-API/blob/master/ToS.md)
- [Blender Cycles GPU / Metal](https://docs.blender.org/manual/en/4.5/render/cycles/gpu_rendering.html)
- [NOAA výpočet polohy slnka](https://www.gml.noaa.gov/grad/solcalc/solareqns.PDF)
