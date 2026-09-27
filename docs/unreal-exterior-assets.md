# Exteriér Unreal — vegetačné assety R1–R6

Stav knižnice k 27. 9. 2026. Záväzný návrh ostáva [C/B/B](active-design.md), oba odstupy 3 000 mm. Tento dokument opisuje zdroje a reprodukciu vegetácie; nemení osadenie ani stav vizuálneho prijatia.

## R6 — zelená regionálna výsadba

Aktuálny zložený master je `output/unreal/exterior-assets-20260927-r6`: 41 variantov, 123 LOD uzlov, 14 rastlinných receptov. Vznikol cez `scripts/unreal/exterior-assets-merge.py` z knižnice R5 a dvoch samostatných rozšírení. Pôvodné knižnice aj pôvodné mapy zostávajú zachované. Nasledujúce počty opisujú zmrazené vstupy; natívne prijatie určuje samostatné review konkrétneho balíka.

- `exterior-regional-assets-20260927-r4`: tri členité listnaté formy a jeden nízky ker, súvislé vetvenie, fotografické listy [CGBookcase](https://www.cgbookcase.com/textures) pod CC0 a pôvodná kôra Poly Haven. Nové listové mapy majú explicitný natívny stretch na rozmer mocniny dvoch pre správne mipmapy; pôvodné PNG ani modelové UV sa nemenia.
- `exterior-garden-morphology-20260927-r6b`: dve nové ružové kompozície s nerovnakou výškou, ohybom a sklonom výhonkov; pôvodný materiál a UV vrátane opakovania mimo 0–1. Všetkých 12 koreňov výsadby a 10 nezmenených kompozícií zostáva zachovaných.
- `exterior-context-20260927-r8`: 1 100 explicitných stromových/krových umiestnení v skupinách, z toho štyri zachované ilustračné malé stromy; 86 248 nových nízkych trsov na najbližších plochách. Pôvodných 382 678 lúčnych trsov, 2 824 vinohradových miest, parcely a terénne mesh sú zachované.
- `exterior-yard-20260927-r2`: 15 111 krátkych trsov na pôvodnej zemine a krajniciach. Nezávislý audit overil celé koruny, všetky mulče vrátane zapusteného zadného pásu, vstupy, stavbu, terasy a nášľapy. Pôvodná verzia R1 je zamietnutá pre prienik do zadného mulča a nie je vstupom R6.

Nové regionálne modely majú `placementPolicy: explicit-only`: importer používa konkrétny `meshId`, koreň, natočenie a jednotnú mierku vo všetkých osiach. Nezamiešava ich do starej náhodnej voľby rastlín. Pôvodné štyri riedke africké tvary sa v tejto výsadbe nahrádzajú novými regionálnymi korunami; ich zdrojové assety sa nemažú. Druhová identita ani presná poloha jednotlivých stromov sa nevydávajú za terénny súpis.

Kompletný R6 materiálový návrh s ortofotom obsahuje 29 materiálov a 68 textúr. Stromové LOD2 majú hrubšiu vnútornú kresbu; prechod a výkon treba hodnotiť na skutočnom pohybe kamery. Sezónna úprava samotného ortofota je zatiaľ samostatný prototyp a do tohto vstupu R6 nepatrí.

## Historické zmrazené vstupy

Všetky cesty sú relatívne ku koreňu repozitára:

- **R2:** `output/unreal/exterior-assets-20260926-r2/` — 28 variantov, 84 LOD uzlov, 7 GLB, 9 materiálových receptov.
- **Závislosť R1:** `output/unreal/exterior-assets-20260926-r1/` — R2 odtiaľ priamo referencuje `glb/tree_small_02.glb`, `glb/grass_medium_02.glb`, `glb/nettle_plant.glb` a príslušné pôvodné textúry. R2 nie je samostatný adresár na prenos.
- **R3:** `output/unreal/exterior-assets-20260926-r3/` — 35 variantov, 105 LOD uzlov, 10 referencovaných GLB a 12 materiálových receptov. Pridáva 7 okrasných kompozícií v 3 GLB; všetkých 28 geometrických záznamov R2 zachováva. Na prenos treba všetky tri knižnice.
- **Vstupná knižnica R4:** `output/unreal/exterior-assets-20260926-r4/` — `geometry-manifest.json` a `asset-manifest.json` sú bajtovo zhodné s R3; `material-manifest.json` je bajtovo zhodný s odvodeným R4 manifestom nižšie. R4 tým jednoznačne vyberá opravené albedo, stále závisí od súrodeneckých zdrojov R1/R2/R3 a `exterior-alpha-20260926-r4/`.
- **Výsadba R4:** `output/unreal/exterior-garden-20260926-r4/garden-plan.json` a `composition-manifest.json` — 12 explicitných inštancií zo zmrazenej geometrie R3, bez nových GLB. `meshId`, `positionCm`, `yawDeg` a bezrozmerné `scale=[s,s,s]` sú záväzné; `actualHeightCm` a `radiusCm` vychádzajú zo všetkých LOD.
- **Natívna väzba:** `output/unreal/exterior-20260926-r2/exterior-import-report.json`, pole `inputFiles`, obsahuje SHA256 manifestov, GLB a máp použitých importom. `model-package.json` v tom istom adresári je doklad Shipping balíka.

SHA256 R2 manifestov sa zhodujú s `inputFiles` natívneho importu:

```text
geometry-manifest.json  74951f361914e3814c672a42c072df57d411c883185d361fa7e0f80b1e6c1842
material-manifest.json  f635401679f06a7b3be087b14267bfc2e41acc2109838cc2655bac9544d79d59
asset-manifest.json     3008e96a11e3432085722206c13fc10cd8ccd0094bd120278f4364e2b891a730
```

SHA256 zmrazených manifestov R3:

```text
geometry-manifest.json  918d309b517f7d3854c29e990ff471efe226d6ca97f25e326733a254e3db4569
material-manifest.json  1d6bb2f861be451b76394225602adaadb571d3d0c121a99421486c8a93f35bfc
asset-manifest.json     fb2fe91c7960f3f4c8dc99cdee705ba626e23ea0597764f2fa58f57133c1eb9f
```

SHA256 výsadby R4:

```text
garden-plan.json        3be79236ed33683b5b5b8e13e27b10ef353acb2497ebf64f6002cf4c1fd6f821
composition-manifest.json 95bf335a6e49766885267abc0e10482fc18e7665a2e9cbf6afe54062e6eceb5a
```

Presné R1 GLB závislosti použité R2:

```text
tree_small_02.glb   aaa458f840a2ee8deb6e0202bc7f2b8ef3c7e7a3989273ecead0726e7444d93a
grass_medium_02.glb c09551da5f8138fc84fe50a05d6d8d4ce3cd6dd504e32cdc10ba5218b6dd386a
nettle_plant.glb    c10c949f8795e2db600504fc54d0a0fac9b8c5a37c597d5cd23dc5f74cd175cd
```

`asset-manifest.json` v knižniciach uchováva URL, autorov, veľkosti, MD5 a SHA256 pôvodných stiahnutých súborov. `geometry-manifest.json` nesie presné názvy uzlov, poradie materiálov, počty trojuholníkov a natívne hranice. `material-manifest.json` viaže každú mapu na cestu a SHA256. Zmrazené adresáre, manifesty a vstupy balíka **neprepisovať pri ďalšom exporte**.

## Zdroje, licencia a význam modelov

Historické rastlinné modely a textúry v nasledujúcej tabuľke pochádzajú z Poly Haven a sú [CC0](https://polyhaven.com/license). Pri každom zdroji sú lokálne `<asset>/info.json`, `files-api.json`, `<asset>_2k.blend` a `textures/`; podrasť má aj pôvodný FBX. API je `https://api.polyhaven.com/info/<asset>` a `https://api.polyhaven.com/files/<asset>`.

| Zdroj | Knižnica / použitie | Derivácia |
| --- | --- | --- |
| [Tree Small 02](https://polyhaven.com/a/tree_small_02) | R1; 3 stromy | Burkea africana / wild syringa. Rozpočtové LOD z pôvodného LOD1: 224 787 / 94 910 / 29 971 trojuholníkov; tri mierne tvarové obmeny. |
| [Grass Medium 02](https://polyhaven.com/a/grass_medium_02) | R1; 5 tráv | Prevažne suchý vzhľad; zdroj + odvodené LOD 0,55 / 0,25. |
| [Nettle Plant](https://polyhaven.com/a/nettle_plant) | R1; 6 bylín | Pôvodné tri LOD; zdrojové rastliny sú malé, približne 2–22 cm. |
| [Shrub 02](https://polyhaven.com/a/shrub_02) | Iba zachovaný R1 | Riedka úzkolistá bylina. **Vylúčená z R2**: nevhodná ako hustá koruna vinohradu. |
| [Shrub 01](https://polyhaven.com/a/shrub_01) | R2; `vine_broadleaf_a–c` | Sedem zdrojových výhonkov na korunu, 1,40 × 1,05 × 0,85 m; 10 902 / 6 384 / 3 220 trojuholníkov. |
| [Shrub 04](https://polyhaven.com/a/shrub_04) | R2; `shrub_broadleaf_a–c` | Sedem výhonkov na ker, 0,80 × 0,90 × 0,85 m; 21 901 / 10 946 / približne 4 925 trojuholníkov. |
| [Celandine 01](https://polyhaven.com/a/celandine_01) | R2; 5 pôdopokryvných variantov | Pôvodné LOD, výška 12–19 cm. |
| [Grass Bermuda 01](https://polyhaven.com/a/grass_bermuda_01) | R2; 3 trsy | 72 živých zdrojových výhonkov na trs; suché objekty vynechané. Výška 15–18 cm; odvodené LOD 0,65 / 0,35. |
| [Grass Medium 01](https://polyhaven.com/a/grass_medium_01) | R3; `ornamental_grass_a–c` | 64 skutočných vysokých výhonkov vrátane zdrojových klasov a 5 základových trsov. Kompozícia má 85 cm; zdrojové vysoké výhonky 24–32 cm. Nejde o botanicky kalibrovanú výšku. |
| [Shrub 01](https://polyhaven.com/a/shrub_01) | R3; `ornamental_white_a–b` | 7 kvitnúcich výhonkov `g/h/i` a 6 zelených výhonkov; 78 cm. Zachované zdrojové LOD listov a kvetov. |
| [Periwinkle Plant](https://polyhaven.com/a/periwinkle_plant) | R3; `ornamental_pink_a–b` | 15 zdrojových výhonkov, 72 cm, pôvodné LOD1–3. Zostáva viditeľná stonková základňa; nejde o jednoliaty strihaný ker. |

Táto zmes rôznych druhov a biomov je **ilustračná vizuálna výsadba**, nie botanický súpis Březí. `shrub_01` je podľa zdrojových metadát **Ageratina adenophora, nie Vitis vinifera**. Riadky vyjadrujú krajinnú interpretáciu vinohradu; trojuholníky listov neurčujú miestny druh. Africký strom nie je tvrdením o existujúcom strome na parcele. Aj kompozície siedmich výhonkov a zmeny mierky sú autorské úpravy, nie samostatné skeny celých miestnych rastlín.

R3 používa rolu `ornamental`, formu `grass` alebo `flowering` a farbu `white`/`pink`. Zdroj sa volá `grass_medium_01`; samostatný model `grass_tall` sa pri akvizícii nenašiel, vysoké výhonky sú objekty v tomto modeli. Názov Periwinkle sa nezužuje na neoverený konkrétny druh. Nové kompozície obsahujú priestorové listy a stonky, nie tri prekrížené fotografie celej rastliny.

| R3 variant | Trojuholníky LOD0 / LOD1 / LOD2 |
| --- | --- |
| `ornamental_grass_a` | 48 071 / 24 532 / 14 342 |
| `ornamental_grass_b` | 47 614 / 24 619 / 14 406 |
| `ornamental_grass_c` | 49 440 / 24 477 / 14 525 |
| `ornamental_white_a` | 93 067 / 39 347 / 36 095 |
| `ornamental_white_b` | 100 587 / 42 217 / 38 965 |
| `ornamental_pink_a`, `ornamental_pink_b` | každý 48 216 / 22 548 / 11 457 |

## Geometria a materiály

Export vznikol v Blenderi **5.2.1 LTS**, lokálne `/Applications/Blender.app/Contents/MacOS/Blender`. GLB používa metre a Y-up: Blender `[x,y,z]` → glTF `[x,z,-y]` → Unreal `[100*x,-100*y,100*z]`. Node aj mesh majú meno `PH_<variant>_LOD<n>`. Spoločný koreň a orientácia platia pre všetky tri LOD. Pri zdrojových skrytých kolekciách použiť explicitný `rotation_euler` a `scale`; ich cache `matrix_world` predtým vracala nesprávnu identitu.

GLB obsahuje neutrálne materiálové zástupné definície s presnými `ph_*` názvami. Pôvodný komplexný Blender shader sa neprenáša automaticky. UE recept používa UV0, sRGB iba pre albedo, lineárne ostatné mapy a **DirectX normály bez ďalšieho prevrátenia zelenej**. Listy sú masked/two-sided foliage, kôra opaque. `albedoScale`, `specular`, `subsurfaceScale`, `normalStrength` a voliteľná `maps.mask` sú explicitné; UE intenzita presvitania je umelecké nastavenie, nie fyzikálne kalibrovaný prepočet Blender shaderu.

Zdrojové hodnoty sú zaznamenané v R2 `source-material-graphs.json` a `additional-source-material-graphs.json`. Native import zabezpečujú `scripts/unreal/exterior-import.py` a `exterior-materials.py`; aktívna knižnica sa odovzdáva cez `BREZI_EXTERIOR_ASSETS`.

R3 dopĺňa `provider-material-graphs.json`. Kľúče nových materiálov sú `ph_grass_medium_01`, `ph_shrub_01_ornamental` a `ph_periwinkle_plant`; Periwinkle používa zdrojový kanál `opacity` ako alpha. Jeho transmission/backfacing/vertex-color sieť ostáva zdokumentovaná, zjednodušený UE recept ju nereprodukuje presne. R3 kópia receptov kalibruje problémové listy a nové ornamentály na specular 0,12 / subsurfaceScale 0,08, pôvodné provider hodnoty uchováva. R1/R2 sa tým nemenili.

R4 opravuje samotné rozmiestnenie: 4 biele a 2 ružové kvitnúce trsy, 6 tráv, deväť korún v pôvodných záhonoch a tri korene mimo nich na presnom historickom XY. Všetky osi majú rovnakú mierku. Konkrétne veľkosti vyplývajú z priestoru a celej LOD koruny, nie z natiahnutia rastliny do úzkej výšky 110–125 cm. Plán overuje aj všetky nášľapy `DOM_01961–01964`, pool coping a terasy. `underplantingDirection` je iba viditeľne označený kompozičný cieľ; nepredstavuje ďalšie vygenerované alebo schválené inštancie.

## R4 — odstránenie bielych okrajov atlasu

`output/unreal/exterior-alpha-20260926-r4/derived-material-manifest.json` zachováva 12 receptov R3 a nahrádza **päť albedo máp**: `ph_celandine_01`, `ph_grass_bermuda_01`, `ph_grass_medium_01`, `ph_grass_medium_02` a `ph_tree_small_02_leaves`. Nové `*_diff_rgb_dilated.png` sú odvodené RGB8 obrázky; normály, roughness a pôvodné alpha masky zostávajú referencované bez zmeny.

Zdrojové RGBA atlasy mali v čiastočne priesvitných okrajoch takmer biele RGB. Pri `grass_medium_01` meranie lineárneho RGB týchto okrajov vyšlo približne `[0,961; 0,965; 0,811]`. `scripts/unreal/exterior-alpha-dilate.py` nahrádza RGB pri alpha pod 0,99 farbou najbližšieho nepriesvitného pixelu pomocou euklidovskej distance transform. RGB pri alpha ≥0,99 ostáva bajtovo zhodné; pôvodné fotografické zdroje a alpha sa nemenia. Nejde o prefarbenie celej rastliny ani o retuš natívneho záberu.

Nettle, Periwinkle a Shrub 01/04 tento preukázaný biely fringe nemali, preto sa ich albedo nemení. Nastavenie UE `FillZeroAlphaPNGData` rieši pixely s nulovým alpha; samo neopraví kontaminované čiastočne priesvitné okraje.

```text
derived-material-manifest.json 84847d52e9d0206de0ce9b30d9441973dab71fd6bfafca36d7fb1612198ba301
derivation-report.json         e3b54fb69d81cca3d01f0efe768a9d10c4d1b8d79789cf574c9843437206ceeb
exterior-alpha-dilate.py       3d94996dd3415084473d6159b135925edd971acea3f5b6448f759ecb5194d2a9
```

`derivation-report.json` pripína zdrojové mapy a generátor, dokladá zachovanie nepriesvitných pixelov a nezmenené alpha masky. CPU simulácia lineárnych mipov v reporte nie je Unreal DDC, Metal sampling ani dôkaz vizuálneho prijatia. Stav pri derivácii je `derived-rgb-atlases-cpu-validated-awaiting-native`.

Reprodukcia používa Python s NumPy, Pillow a SciPy (zaznamenané NumPy 2.3.5 / SciPy 1.16.2). Spustiť z koreňa repozitára s novým výstupným adresárom; generátor odmieta prepísať existujúce odvodené atlasy:

```sh
python3 scripts/unreal/exterior-alpha-dilate.py \
  --source output/unreal/exterior-assets-20260926-r3/material-manifest.json \
  --output output/unreal/exterior-alpha-reproduction
```

Presný lokálne použitý interpreter bol `/Users/davidzita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B` s `PYTHONPATH=/tmp/dom-exterior-alpha-deps`. Tento dočasný adresár nie je trvalý dependency lock ani súčasť repozitára; pri neskoršej reprodukcii treba obnoviť zaznamenané balíky v samostatnom prostredí.

Pre nový balík treba explicitne použiť odvodený materiálový manifest a znovu overiť jeho natívne `inputFiles`. Samotná existencia derivácie neznamená, že ju používa otvorený Unreal balík.

## Reprodukcia bez zmeny zmrazených vstupov

Exportéry sú zatiaľ v **Git-ignorovanom `output/`** a odvodzujú koreň z vlastnej cesty. R2 navyše očakáva vedľa seba adresár presne pomenovaný `exterior-assets-20260926-r1`. Nie sú to ešte prenosné kanonické CLI nástroje.

1. Skopírovať obe celé knižnice do nového pracovného koreňa; zachovať ich názvy súrodeneckých adresárov. Zdrojové súbory porovnať s uloženým `asset-manifest.json`. Pre presnú reprodukciu použiť uložené zdroje; živé API môže medzitým vrátiť inú revíziu.
2. Pracovné materiálové manifesty majú absolútne cesty: zmeniť iba ich pracovné kópie na nový koreň a znova overiť SHA256 máp. Recepty sú archivované JSON; úplný generátor všetkých deviatich receptov zatiaľ neexistuje.
3. V pracovných kópiách spustiť Blender `--background --python <súbor>` v poradí: **R1 `export-plants.py` → R1 `export-trees.py` → R2 `export-composites.py` → R2 `export-green-grass.py`**. Posledný krok dopĺňa Bermuda trsy. `export-composites.py` resetuje R2 zoznam na zachované R1 role a nové kríky/podsadbu, preto poradie záleží.
4. Spustiť `python3 <pracovné-R2>/verify-glb.py`. Kontroluje GLB a mapové SHA256, uzly, sloty, LOD, UV0, normály, tangenty a natívne hranice. **Zapisuje `asset-validation.json`**, preto ho nepúšťať do zmrazenej knižnice.
5. Náhľady: Blender `preview-runtime.py`, potom `preview-green-grass.py` opravujúci zdrojový render border trávy. Výsledky sú Blender/Cycles, nie Unreal QA. Nové exporty dostať do nového izolovaného Unreal výstupu a znovu overiť import/reload, Shipping a natívne zábery; staré package hashe sa na ne nevzťahujú.

Pre R3 pokračovať iba v novej pracovnej kópii s dostupnými R1/R2 zdrojmi:

1. `acquire.py` overí/doplní Grass Medium 01 a Periwinkle; presnú reprodukciu založiť na archivovaných mapách a modeloch.
2. Blender `--background --python export-ornamentals.py` vytvorí tri nové GLB a aditívny manifest.
3. `python3 orthogonalize-tangents.py` ortogonalizuje tangenty Gram–Schmidtom a upraví hashe iba nových GLB. Zachová handedness, pozície, normály, UV a topológiu; zapisuje `tangent-repair-receipt.json`.
4. `python3 verify-glb.py` a `python3 verify-ornamental-basis.py` zapíšu reporty. Posledný kontroluje 21 nových LOD / 753 623 vertexov; maximálne absolútne `N·T` je pod 4,7e−8. Zriedkavé orientačné výnimky zdrojových plátkov sú spočítané, nie zamaskované.
5. Blender `--background --python preview-ornamentals.py` vytvorí `ornamental_grass-preview.png`, `ornamental_white-preview.png` a `ornamental_pink-preview.png`. Ide o neupravené Blender/Cycles náhľady zdrojového shadera, nie natívny Metal výsledok.

R4 `output/unreal/exterior-garden-20260926-r4/derive-garden.py` používa hashovo pripnutý zdrojový OBJ, R3 manifest, pôvodné card identity a deterministické spoločné rozloženie na 2 cm sieti. Vyžaduje NumPy a Shapely; použitý interpreter je `output/unreal/exterior-tools-py312-20260926/bin/python`. Pri reprodukcii skopírovať skript do nového súrodeneckého výstupu a jeho vstupné cesty explicitne overiť. Existujúci `garden-plan.json` odmietne prepísať. Mierka je bezrozmerná; všetky geometrické odstupy sú centimetre, nie pixely.

Nová online akvizícia používa v R1 `acquire.py` a `acquire-tree.py`, v R2 `acquire.py` a `acquire-grass.py` (Python 3 + curl). Akvizičné skripty obnovujú metadáta/manifesty; R1 stromový skript navyše očakáva existujúci materiálový manifest. Nepredstavujú samostatný čistý build od nuly. Reexport s inou verziou Blenderu nemusí mať totožné GLB bajty, aj keď prejdú geometrické kontroly.

## Navrhované presunutie do kanonických skriptov

Presun sa týmto dokumentom **nevykonal**. Nasledujúce zdroje treba po parametrizácii uchovať v Gite; tabuľka je presný návrh názvov pod `scripts/unreal/exterior-assets/`:

| Existujúci súbor | Navrhovaný kanonický názov |
| --- | --- |
| R1 `acquire.py`, `acquire-tree.py` | `acquire-r1-plants.py`, `acquire-r1-tree.py` |
| R1 `export-plants.py`, `export-trees.py` | `export-r1-plants.py`, `export-r1-trees.py` |
| R2 `acquire.py`, `acquire-grass.py` | `acquire-r2-plants.py`, `acquire-r2-grass.py` |
| R2 `export-composites.py`, `export-green-grass.py` | `export-r2-composites.py`, `export-r2-green-grass.py` |
| R3 `acquire.py`, `export-ornamentals.py` | `acquire-r3-ornamentals.py`, `export-r3-ornamentals.py` |
| R3 `orthogonalize-tangents.py`, `verify-ornamental-basis.py` | `orthogonalize-tangents.py`, `verify-ornamental-basis.py` |
| R3 `inspect-provider-materials.py`, `preview-ornamentals.py` | `inspect-ornamental-materials.py`, `preview-ornamentals.py` |
| Garden R4 `derive-garden.py` | `derive-garden-composition.py` |
| R2 `verify-glb.py` | `verify-glb.py` |
| R2 `inspect-source-materials.py`, `inspect-additional-materials.py` | `inspect-source-materials.py`, `inspect-additional-materials.py` |
| R1 `preview-tree.py`; R2 `preview-runtime.py`, `preview-green-grass.py` | `preview-tree.py`, `preview-runtime.py`, `preview-green-grass.py` |

Pred presunom oddeliť explicitné source/dependency/output korene a cestu validačného reportu, nahradiť pevný súrodenecký R1 adresár argumentom, pridať odmietnutie prepísania zmrazeného výstupu a pripnúť verziu Blenderu. Archivované recepty a zdrojové locky treba preniesť ako verziované vstupy; online akvizícia ich nesmie potichu obnovovať. Zdieľané exportné funkcie oboch R2 skriptov následne zlúčiť bez zmeny výslednej geometrie.

## Dôkaz kvality

`asset-validation.json` R2 prešlo pre 28 variantov / 84 LOD / 9 receptov, R3 pre 35 variantov / 105 LOD / 12 receptov. Natívny import/reload a Shipping sú technické dôkazy; samy nepotvrdzujú vizuálne prijatie. Autoritou pre obrazy a výkon sú konkrétne `qa/**/summary.json`, `runtime.json` a neupravené `capture.png` v `output/unreal/exterior-validation-20260926-r1/`.

Garden R4 `independent-world-audit.json` nezávisle prečítal GLB pozície: 36 world LOD boxov, 288 rohov a 66 párov. Minimálny odstup koreňov je 82,292 cm, celých konzervatívnych korún 2,292 cm, skutočných world boxov 7,397 cm; odstup celej koruny od záhonovej hrany 14,01 cm, nášľapov 14,543 cm a bazéna/terás 56,5 cm. Kolízie: nula. Výšky pri rovnomernej mierke sú 50–75,71 cm; tri korene mimo záhonov majú presné pôvodné XY. Najväčší vedomý presun v existujúcom záhone je 121,696 cm. Celých 12 primárnych inštancií predstavuje 773 990 / 355 480 / 259 580 trojuholníkov pri spoločnom LOD0 / LOD1 / LOD2 pred cullingom; nejde o počet skutočne viditeľných trojuholníkov jedného frame.

`scripts/unreal/exterior-gallery.mjs` číta generické `exterior-r*-rejected-review.json`, viaže ich na SHA256 série a balíka a zobrazuje „zamietnutý pokus“ so skutočnými nálezmi. Samostatné `exterior-r*-review.json` smie vzniknúť až po natívnej vizuálnej kontrole. Úspešný technický import, názov fázy `after` ani `final` nie sú potvrdením fotorealizmu. Ani korektné proporcie R4 a nulové geometrické kolízie samy nedokazujú prijateľný obraz.
