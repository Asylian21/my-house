# Fasádna omietka — 9. september 2026

Kandidát silnejšej omietky bol zamietnutý po dvoch natívnych 4K záberoch: pod pravým odkvapom sa opakovalo slabé hranaté tieňovanie. Jeho príčina zatiaľ nie je preukázaná. Predvolený import preto obnovuje pôvodný materiál s váhou normály 0,2; kandidát 0,5 zostáva dostupný iba cez explicitné `BREZI_APPLY_FACADE_PLASTER=1`.

Experiment mení iba účinok existujúcej normálovej mapy na 66 dieloch vonkajšej omietky `MAT_0010 / real-wall`: váha medzi pôvodnou normálou povrchu a mapou sa mení z 0,2 na 0,5. Ide o autorskú úpravu vizualizácie, nie o meranie povrchu realizovaného domu.

Zostávajú rovnaké tri pôvodné 2K mapy [White Plaster 02](https://polyhaven.com/a/white_plaster_02) od Roba Tuytela / Poly Haven, farebná zmes 85 % konštanty a 15 % fotografie, fotografická roughness aj svetová perióda 1 m. Úplná fotografia nebola použitá ako nové albedo, pretože by výrazne zmenila sivobéžový odtieň a stopy hladidla. Vstupné fotografie ani spoločný `materials.py` sa nemenia. Interiérové materiály a podhľady zostávajú mimo rozsahu.

`scripts/unreal/facade-plaster/plaster.py` duplikuje pôvodný materiál do samostatného adresára podľa SHA receptu. Natívne číta celý graf: 16 uzlov, tri texture objects, prepojenia, parametre a Nanite usage. Porovnanie povoľuje jediný rozdiel v `MP_NORMAL → Normalize → LinearInterpolate.const_alpha`. Tri texture objects neznamenajú tri shader samples: svetové mapovanie používa projekcie viacerých osí.

Zdrojových 817 trojuholníkov, ich poradie, UV0 a geometria sa overujú voči pôvodnému OBJ. Menia sa iba component material overrides. Celý zvyšok mapy vrátane 33 769 trávnych inštancií sa porovnáva pred a po úprave. Nový materiál sa uloží, uvoľní z pamäte a načíta z disku pred aktiváciou aj po nej. Pôvodné mesh a material assety sa neprepisujú.

Prvý import prešiel s natívnym exit 0 za 54,54 s. Samostatný package gate potvrdil skutočný uložený výsledok a prvý BuildCookRun prešiel za 77,66 s. Pôvodné dôkazy zostávajú v `output/unreal/facade-plaster-study/import-01-*` a `package-01-*`. Integrácia následne zladila voliteľný pass s ostatnými povrchovými vrstvami: používa sa v úplnom importe materiálov a vegetácie; pri čiastkovom importe sa nevyžaduje chýbajúca trávna vrstva. Opakovaný úplný import overuje aj už aktívne vlastné overrides pred obnovením mapy.

Prvý opakovaný import skončil pred aktiváciou na kontrole grafu. Samostatné natívne čítanie preukázalo, že sa líšili len interné názvy všetkých 16 uzlov: Unreal ich pri obnovení zdrojového materiálu znovu prideľuje. Kontrola teraz odvodzuje stabilnú identitu z materiálových výstupov a pomenovaných vstupných prepojení. Zachováva typy, všetky hodnoty, výstupné kanály, zdieľanie a počet uzlov; odmieta cykly aj odpojené uzly. Deväť CPU testov vrátane skutočného natívneho výpisu a negatívnych kontrol prešlo.

Opravený import 03 aj následný opakovaný import 04 skončili s exit 0. Import 04 pred odstránením starej mapy skutočne overil 66 aktívnych vlastných overrides a po regenerácii znovu uložil a načítal všetkých 66 nových väzieb. Neúspešný import 02 a jeho diagnostický výpis zostávajú zachované; pred aktiváciou overil nezmenený zdrojový stav.

Aktuálny recept: `0dd12e535755865d2f19d9c15c0182397f9811b03782b8189499589df0d81b37`.

## Výkonový podklad tejto iterácie

Profil aktuálnej terasy pred materiálovou zmenou potvrdil dominantný podiel TSR a Lumen. Konkrétne vykázal TSR RejectShading 7,017 ms, UpdateHistory 3,877 ms a translucent-volume ray tracing 2,911 ms; BasePass 1,499 ms. Ide o jeden profilovaný snímok s delenými compute encodermi, ktoré ovplyvňujú výkon. Tieto čísla nie sú produkčné fps ani dôkaz zrýchlenia.

Pôvodný hostiteľský report nesprávne očakával interiérový pohľad a 600 zahrievacích snímok. Natívny proces skončil správne a zaznamenal terasu s 1200 snímkami. Opravený helper teraz prijíma explicitný pohľad a počet warmup snímok, zachováva interiérový default a prešiel šiestimi regresnými testami. Samostatná validácia ponecháva pôvodné dáta aj failed report nedotknuté: `output/unreal/performance-next-study/terrace-profile-75cc-revalidation/validation.json`. Rozlíšenie a kvalitatívne nastavenia aplikácie sa nemenili.

## Aktuálny vizuálny výsledok

Finálny balík kandidáta prešiel BuildCookRun za 64,50 s. Dve nezávislé spustenia skončili s natívnym exit 0, po 1200 zahrievacích a 300 meraných snímkach; aplikácia, okno aj klávesový fokus zostali aktívne vo všetkých 300 vzorkách. Scéna aj jej RHI textúra mali počas merania 3840 × 2160 pixelov pri 100 % render scale bez dynamického rozlíšenia. To nepreukazuje fyzický 4K displej ani 4K backbuffer okna.

| Záber kandidáta | Priemerný interval | Odvodené fps | P95 |
| --- | ---: | ---: | ---: |
| `foreground-terrace-day-be2c8e02-c661-426f-aaa6-80c457e2ca7b` | 53,115 ms | 18,83 | 55,047 ms |
| `foreground-terrace-day-348c866c-5015-478f-a373-c3b3d696de5d` | 51,562 ms | 19,39 | 53,256 ms |

V oboch origináloch sa opakujú slabé obdĺžnikové škvrny približne v oblasti x = 3380–3670, y = 730–810. V predchádzajúcom zábere `foreground-terrace-day-11b8503b-59e1-403b-85b4-df9adbe0e23a` nie sú zreteľné. Silnejší reliéf je viditeľný najmä pri pravom ostení, ale široký pohľad neprináša presvedčivé zlepšenie. Tieto merania nepreukazujú zrýchlenie, plynulý 4K pohyb ani fotorealizmus.

Obnova používa rovnaký generátor zdroja. Pred odstránením starej mapy kontroluje presných 66 vlastných overrides. Po novom importe kontroluje pôvodné prázdne overrides, zdrojový graf s váhou 0,2, geometriu aj UV, ochranné hashe a 33 769 trávnych inštancií. Uloží a opätovne načíta mapu a porovná celý stav. Package gate vyžaduje tieto dôkazy aj pri vypnutom experimente; samotný prepínač nie je dôkazom obnovy.

Import 05 obnovil všetkých 66 pôvodných väzieb a skončil s exit 0 za 52,38 s. Jeho skutočný natívny report prešiel package gate aj ôsmimi negatívnymi kontrolami vrátane cudzieho override, váhy 0,5, chýbajúceho reloadu, zmenenej geometrie a neúplných hashov. Package 03 prešiel za 67,34 s. Predchádzajúci balík kandidáta zostáva zachovaný v package-history; aktuálna aplikácia je `output/unreal/package/Mac/BreziTwin.app`.

Obnovený balík bol následne skutočne spustený v samostatnom procese PID 17341 a skončil s exit 0. Záber `foreground-terrace-day-70ce5064-412e-4d99-90d3-fa15f9403a93/capture.png` bol skontrolovaný v pôvodnom rozlíšení 3840 × 2160. V sledovanej oblasti horného pravého pásu už opakované obdĺžnikové škvrny nevidno. Ide o prijatie lokálnej obnovy; presná príčina artefaktu kandidáta zostáva neurčená.

Meranie obnovenej aplikácie: 1200 warmup a 300 meraných snímok, 300/300 vzoriek vo foregrounde s aktívnym oknom aj fokusom, priemer 53,405 ms (**18,72 fps**), P95 61,982 ms. Scéna aj RHI textúra zostali natívne 4K. Všetkých 2459 odkazov na vstupné hashe (2447 rôznych súborov) aj obsah `.app` sa zhodovali pred aj po spustení. Výkonový cieľ a celkový fotorealizmus zostávajú nesplnené. Oheň sa v tejto iterácii nemenil.
