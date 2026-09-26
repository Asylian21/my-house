# Unreal — plynulosť BreziTwin

Pracovná revízia z 23.–24. septembra 2026 rieši cenu Lumenu, doplnkových odrazov
skla a drobnej vegetácie. Hlavný návrh **C/B/B**, geometria domu, osadenie
s uličným aj pravým odstupom 3 000 mm a historické výstupy zostávajú záväzné.

**Finálny Shipping R4 splnil výkonové kritériá na M5 Pro:** platných je
**60/60** hlavných prípadov vrátane chôdze a **8/8** samostatných
softvérových prípadov. Po piatich opravných behoch má všetkých 68 vybraných
prípadov aj použiteľné RHI GPU údaje. Bežné UI prešlo päť štartov a štyri
reštarty s obnovením profilov. Vizuálne prijatie a výber balíka sú opísané nižšie.

Po dokončení týchto kontrol bol **Shipping R4 povýšený** do
`output/unreal/model-refresh-current.json`; pôvodný výber je zachovaný
v `previousSelection`. [Finálny záznam prijatia](../output/unreal/performance-validation-20260924-r1/performance-final-review.json)
viaže balík, merania, 24 vizuálnych párov, UI, testy a ich obmedzenia hashmi.

Hlavné dôkazy sú [finálne merania JSON](../output/unreal/performance-validation-20260924-r1/measurements.json),
[akceptačný prehľad R4](../output/unreal/performance-validation-20260924-r1/acceptance.md)
([JSON](../output/unreal/performance-validation-20260924-r1/acceptance.json)) a
[galéria pred/po](../output/unreal/performance-validation-20260924-r1/comparison.html).
Stav meraní je **passed**. Prehľad obsahuje **249 záznamov**: 174 nezmenených
historických záznamov a 75 nových (68 plánovaných, päť GPU opakovaní a dva
nočné kontrolné zábery). Záznamy neplatného GPU časovania zostávajú dostupné.

## Rozsah profilov

Recept revízie 2 v `BreziRenderQualityPolicy.h` rozširuje profily o šesť
scalability skupín, efektívne nastavenia Lumenu, lokálne tiene, trávu a
doplnkový odraz skla. Nasledujúca tabuľka uvádza **hodnoty v zdrojovom kóde**,
nie všeobecný prísľub výkonu. Finálna Shipping matica vrátane chôdze,
opravných behov a softvérovej série potvrdila odčítané nastavenia a
skutočné rozmery obrazu; jej namerané hranice sú uvedené nižšie.

| Nastavenie | Native | Balanced | Performance / Plynulosť |
| --- | ---: | ---: | ---: |
| Primárne rozlíšenie | 100 % | 67 % | 50 % |
| TSR história | 100 % | 100 % | 100 % |
| `sg.GlobalIlluminationQuality` | 3 | 2 | 2 |
| `sg.ShadowQuality` | 3 | 2 | 1 |
| `sg.ReflectionQuality` | 3 | 2 | 2 |
| `sg.FoliageQuality` | 3 | 2 | 1 |
| `sg.PostProcessQuality` | 3 | 2 | 1 |
| `sg.EffectsQuality` | 3 | 2 | 1 |
| TLV rozmer / blur, odvodené z Effects | 64 / 1 | 48 / 1 | 32 / 0 |
| Lumen Final Gather | 1,0 | 0,75 | 0,5 |
| Lumen Reflection Quality | 1,0 | 0,75 | 0,5 |
| Lumen Scene Lighting Quality | 1,0 | 1,0 | 0,5 |
| Lumen Scene Detail | 1,0 | 1,0 | 0,5 |
| Lumen Scene View / Max Trace Distance | 150 / 150 m | 100 / 100 m | 60 / 60 m |
| `foliage.DensityScale` | 1,0 | 0,65 | 0,35 |
| Preferovaný Lumen tracing | hardvérový, ak ho RHI podporuje | hardvérový, ak ho RHI podporuje | softvérový |
| Doplnkový zadný odraz skla | zapnutý po ustálení | vypnutý | vypnutý |
| Tiene miestnych svietidiel | pôvodné | pôvodné | vypnuté |

Slnko si zachováva tiene. Profil nemení tok, farbu ani polohu svietidiel.
Aktuálne interiérové svietidlá zostávajú podľa existujúceho návrhu zapnuté
cez deň aj v noci; vypnutie ich tieňov v Plynulosti neznižuje ich intenzitu.

Effects už nastavuje `r.TranslucencyLightingVolume.Dim` a
`r.TranslucencyLightingVolume.Blur`; samostatný override nebol pridaný.
Hodnoty 64/1, 48/1 a 32/0 vychádzajú z lokálneho
[UE 5.8 BaseScalability.ini](</Users/Shared/Epic Games/UE_5.8/Engine/Config/BaseScalability.ini:827>).
R1 runtime potvrdil pre Performance rozmer 32 a blur 0. Finálna séria
uchováva odčítané cvary jednotlivých profilov v každom `runtime.json`.

Hodnoty `r.Brezi.Lumen.*` sa uplatňujú na finálne postprocess nastavenia
hlavného pohľadu po zlúčení kamery a objemov. Tak ich neprebije starý
neohraničený PostProcessVolume s Final Gather 4 a Reflection Quality 4.
Scene capture a reflection capture touto úpravou hlavného pohľadu neprechádzajú.
Základ nových importov aj migrácie má kvality 1,0 a obidva dosahy 100 m.

Pomenovaný `-BreziRenderProfile` sa použije aj počas diagnostiky. Taký beh
neukladá QA voľbu do používateľských nastavení. Profil používa prioritu
GameOverride; vyššie priority Code, Console a Commandline zostávajú
nadradené a kód neprepisuje prioritné príznaky. Nie každý `-ini` zápis má
vyššiu prioritu než GameOverride. Bežná
vedomá voľba profilu sa naďalej ukladá.

Pri chýbajúcej uloženej voľbe vyberá samotná runtime politika Balanced
na RHI s podporou hardvérového tracingu a Plynulosť na ostatných. Generátor
`model-refresh prepare` však zatiaľ výslovne zapisuje predvolený
`ProfileV1=performance` a okno 1 920 × 1 080. Skutočný výstup sa musí odčítať
z runtime reportu a PNG; označenie Retina samo neurčuje počet pixelov.

## Sklo a vegetácia

Devätnásť doplnkových sklenených aktérov zostáva v scéne. Native povoľuje
nový capture až po 0,25 s ustálenia kamery/scény. Zmena polohy sa vyhodnocuje
od 0,25 cm a uhla od 0,05°. Spoločný rozpočet je najviac jeden capture za
frame; výber sa posúva medzi pripravenými sklami. Limit šírky je 512 px,
najviac dve ustáľovacie snímky, formát zostáva HDR `PF_FloatRGBA`.

Doplnkový capture nepoužíva Lumen GI ani Lumen odrazy a neuchováva trvalú
renderovú históriu. Počas pohybu sa jeho starý obraz skryje; pôvodné hlavné
sklo zostáva. To môže zmeniť vzhľad zadného odrazu a vyžaduje kontrolu
zvnútra aj zvonka. Periodické prechádzanie všetkých aktérov a materiálov
kvôli podpisu scény nahrádza revízia z udalostí dverí, osvetlenia a profilu.
Budúce procedurálne zmeny materiálov musia revíziu výslovne invalidovať.

[Natívne runtime snímky Native skla zo Shipping R1](../output/unreal/performance-20260923-r1/glass-runtime-review.json)
potvrdzujú 19 nakonfigurovaných aktérov. V statickom interiéri malo päť
aktérov spolu desať kumulatívnych capture operácií, päť viditeľných
ustálených odrazov a žiadnu čakajúcu operáciu. Konečný orbitový snapshot
mal odrazy skryté; jeho 21 kumulatívnych capture operácií zahŕňa aj štart,
zahrievanie a prípadné ustálenie okolo obratu. Nemožno z neho odvodiť
nulu capture operácií počas celého pohybu. Päť alokovaných targetov
512 × 288 spolu hlási 5,625 MiB, čo nie je celková spotreba GPU pamäte.
Hlásený rozpočet jednej capture operácie na frame je politika plánovača,
nie z tohto snapshotu empiricky zmerané maximum. Manuálna interakcia
a vzhľad odrazu pri pohybe zostávajú samostatnou UI kontrolou.

Spoločná politika `performance_scene_policy.py` mení iba vlastné drobné
HISM vrstvy bez kolízií:

| Vrstva | Začiatok / koniec cullingu | Tiene / RT / distance-field príspevok | Hustota podľa profilu |
| --- | --- | --- | --- |
| Aktuálny krátky trávnik | 15 / 25 m | vypnuté | áno |
| Staršia vrstva `BreziLawnDetail` | zachované 6 / 12 m | vypnuté | áno |
| Malé vidiecke skupiny `plants_*` | 60 / 80 m | vypnuté | áno |

Vidiecke `plants_*` už mali tiene vypnuté; nová úprava im pridáva najmä
vylúčenie z RT, škálovanie hustoty a kratší dosah. Stromy, ich koruny,
vysoký podrast vetrolamu a súkromný živý plot touto politikou neprechádzajú.
Žiadna HISM skupina sa nezlučuje. Uložený počet a poradie transformácií
inštancií zostávajú rovnaké; `foliage.DensityScale` mení ich vykresľovanie.
Riedkejšie steblá, slabšie drobné tiene a rozdiel pri vzdialenom poraste
sú kvalitatívne kompromisy viditeľné aj v natívnych statických snímkach.
Pohybové preblikávanie a objavovanie porastu vyžaduje samostatnú kontrolu.

Samostatné [porovnanie runtime R1 a scény R2b](../output/unreal/performance-20260923-r1/scene-stage-evaluation.md)
obsahuje 12 párov Development behov pri Retina výstupe: ulica/terasa,
tri profily a statická kamera/orbit. Nastavenia profilov aj finálneho
postprocessu sa zhodujú; všetky behy mali nepretržité popredie. Priemerný
frame sa zlepšil v 8/12 pároch, GPU priemer v 11/12. Napríklad Balanced
terasa v pokoji klesla z 27,16 na 23,94 ms a p99 z 34,27 na 30,14 ms;
jej orbit sa mierne zhoršil z 24,90 na 25,03 ms. V GPU profiloch klesli
najmä prepass a base pass, kým TLV a TSR zostali podobné. Ide o menší,
nie plošne rovnaký prínos vegetácie. Dve zostavy majú odlišné Development
binárky a koncové orbitové polohy sa líšia o 0,42–1,96 cm; hlavné
zrýchlenie celého Shipping balíka sa preto nepripisuje iba tejto migrácii.

## Izolovaná migrácia a balenie

Finálna [migrácia R2b](../output/unreal/performance-20260923-r2b/performance-scene-summary.json)
má stav `performance-scene-validated`. Pred uložením a po novom načítaní
sa zhoduje chránený záznam **2 735 aktérov**; zo **2 796 Content súborov**
sa zmenila iba mapa. V **316** drobných vegetačných skupinách sa zachovalo
všetkých **44 244** transformácií inštancií a natívne odčítanie potvrdilo
zapnuté škálovanie hustoty vo všetkých 316 skupinách. Mapa po migrácii má
SHA256 `4ede366c45ab9e32663396a61c61b4a849c93889c7726e1e5473ce9ab109bec0`.

Prvý [Shipping balík R1](../output/unreal/performance-shipping-20260923-r1/model-package.json)
zdedil overenú R2b scénu. Jeho receipt má SHA256
`60ee4ec95c7c39d982b0f6c2ddfc312366ad434df7c07e452e811cc49ed3761a`.
Editor aj Game build, Metal cook, obsah a strict kontrola podpisu prešli;
finálny arm64 `.app` používa stabilné meno `BreziTwin.app` a
`CFBundleExecutable=BreziTwin` so zapečateným štartovacím vstupom.
Tento hash viaže historickú meraciu sériu a akceptačný prehľad R1. Staršie R1
Development merania zostávajú nižšie oddelenou históriou.

Oprava ukladania je v novom [Shipping R4](../output/unreal/performance-shipping-20260924-r4/final-package-provenance.json),
receipt SHA256 `825723b7bbff59fcd5c767afad0f7d7c84ba8525fdc3545d6278f4e392d6feb3`,
UUID `E1A19916-74E1-3B1B-9961-BC93602FE49B`. Voči R1 sa mení iba
`BreziRenderQuality.cpp`; Config, vlastné Build vstupy, projektový descriptor
a všetkých 2 796 Content súborov sú totožné. Generované FileOpenOrder a
PackageVersionCounter nie sú súčasťou tejto zhody Build vstupov.
Editor 30 aj Game 39 krokov, cook,
strict podpis a zapečatený štartovací vstup prešli. R4 dostáva vlastnú
meraciu sériu; R1 výsledky sa neprepisujú ani neoznačujú novým hashom.

Editor pri ukončení natívneho testu rozšíril generovaný `DefaultInput.ini`.
Package kontrola túto odchýlku zastavila ešte pred cookom. Zmenený súbor
aj diff sa zachovali a [obnovenie](../output/unreal/performance-shipping-20260924-r4/editor-config-drift/restoration.json)
vrátilo presné pripravené bajty zhodné s kanonickým zdrojom. Pred úspešným
balením sa znovu overilo všetkých 71 vlastných Source/Config/Build pinov,
278 Game zdrojových pinov a celý chránený obsah. Build receipty sa neupravovali.

Posledné tri povinné hostiteľské sady prešli spolu **806 testami**:
`unreal:test` **577 Node + 163 Python = 740**, `unreal:photoreal:test`
**43** a `unreal:lawn:test` **23**; každá skončila s exit 0 po finálnej
R4 meracej sérii a doplnení regresného testu výberu softvérového GPU opakovania.
Dôkazy: [hlavná sada](../output/unreal/performance-validation-20260924-r1/tests/unreal-test-final.log),
[photoreal](../output/unreal/performance-validation-20260924-r1/tests/photoreal-test-final.log),
[lawn](../output/unreal/performance-validation-20260924-r1/tests/lawn-test-final.log).
Tento výsledok nahrádza staršie súčty 770/773/792/805; hostiteľské testy sa
nepoužívajú ako náhrada natívnych meraní alebo vizuálneho prijatia.

Nové kroky `inherit` a `performance-scene` pracujú v novom
`BREZI_MODEL_OUTPUT`. `inherit` overuje existujúci balík a jeho obsah,
potom kopíruje zdrojové `Content` a `geometry`. Pôvodné importné reporty
sú zachovanou históriou; nevydávajú sa za nový import.

`performance-optimize.py` vyžaduje presnú kópiu celého Content, samostatný
zdroj a cieľ, čerstvý report a projekt zodpovedajúci cieľu. Odmieta aktuálne
vybraný alebo už zabalený cieľ. Jediný povolený zmenený súbor v Content je
`Brezi/Maps/Brezi.umap`. Pred úpravou uchová zálohu mapy. Žiadny mesh,
materiál, textúra, kolízny asset ani dátový kontrakt nesmie zmeniť hash.

Natívna kontrola pred úpravou a po uložení/opätovnom načítaní porovnáva
identitu aktérov, transformácie, mesh a materiálové väzby, viditeľnosť,
kolízne nastavenia a usporiadané HISM transformácie. Report obsahuje všetky
vstupné/výstupné hashe, manifest zmien a presnú politiku. Hostiteľský
procesný report sa viaže na PID, čas behu, log a hash natívneho reportu.
Tieto záruky kontrolujú migráciu; samy nepreukazujú FPS ani vizuálnu zhodu.

Príklad prípravy novej iterácie; názov musí byť nepoužitý:

```sh
export BREZI_MODEL_OUTPUT=output/unreal/performance-next
export BREZI_ARCHVIZ_GAME=1
export BREZI_DOUBLE_GLASS=1
export BREZI_GAME_CONFIGURATION=Shipping
node scripts/unreal/model-refresh.mjs prepare
node scripts/unreal/model-refresh.mjs inherit output/unreal/rural-context-20260923-r4
node scripts/unreal/model-refresh.mjs editor-build
node scripts/unreal/model-refresh.mjs performance-scene
node scripts/unreal/model-refresh.mjs game-build
node scripts/unreal/model-refresh.mjs package
```

Táto sekvencia je reprodukčný postup, nie záznam úspešného vykonania.
Príprava vypína historickú kaustiku a nastavuje `r.RayTracing.Culling=3`
v izolovanej konfigurácii. `BREZI_DOUBLE_GLASS=1` ponecháva projektový
global clip plane potrebný pre Native odraz; jeho cena v base pass tým
nie je odstránená. Podporované Game konfigurácie v tomto postupe sú
Development a Shipping. Nainštalovaný engine neposkytuje použiteľnú
Test konfiguráciu; finálna overovaná aplikácia preto používa Shipping.

## Meranie a aktuálne dôkazy

Runner `scripts/unreal/performance-qa.mjs` vytvára pre každý štart nový
sandbox a samostatný adresár s `qa.json`, `runtime.json`, priamym PNG a
dostupnými logmi. Balík a dôkazy sú previazané hashmi. Statický záber meria
300 intervalov po najmenej 240 zahrievacích snímkach; Development môže
počas zahrievania samostatne zachytiť ProfileGPU. GPU profil nie je súčasťou
meraného intervalu. Samostatný Insights beh používa
`-trace=cpu,gpu,frame -notracethreading` a uchová `.utrace`.

Nový `-BreziRealtimeWalk` vyžaduje zdrojovo odvodený a hashom scény viazaný
JSON z `realtime-walk-contract.mjs`. Trasa vedie od aktuálneho vstupu do
obývačky kuchynskou uličkou po prvé zatvorené dvere a vracia sa po rovnakej
trase. Pred zahrievaním overuje podlahu a swept capsule pozdĺž segmentov.
Počas merania používa bežný CharacterMovement bez teleportov, pevného
kroku alebo zmeny času. Zaznamenáva dráhu, dosiahnuté body, celé návraty
a časové vzorky; päť sekúnd bez postupu ukončí beh ako chybný.

Nové pohybové režimy vyžadujú požadované trvanie **aj najmenej 240
intervalov**; pri nedostatku intervalov je limit 180 s. Chôdza navyše
vyžaduje aspoň jeden celý návrat. To je kontrola tejto trasy, nie prijatie
celého domu, ovládania z klávesnice alebo všetkých podláh a priechodov.

Explicitné diagnostické argumenty `-BreziBenchmarkUncapped` a
`-BreziSoftwareLumen` nastavujú VSync/FPS limit na nulu, respektíve
hardvérový Lumen na nulu. Platí to iba pri zapnutej diagnostike, aj
v Shipping bez všeobecných `ExecCmds`, a so zachovaním vyšších priorít.
Runtime zaznamenáva skutočné hodnoty cvarov, šesť finálnych Lumen nastavení,
stav real-time skylight capture, PID a konfiguráciu zostavy.

### Finálna Shipping séria R4

Výsledky sa viažu na receipt `825723b7…d6feb3` a vopred uložený
[akceptačný plán](../output/unreal/performance-validation-20260924-r1/acceptance-plan.json).
Každá hlavná skupina obsahuje osem statických/orbitových prípadov a dve
chôdze deň/noc. Tabuľka uvádza **najnižší priemer FPS jedného behu** a
**najhoršie p99 intervalu snímky** v skupine, nie okamžité minimum FPS.

| Profil | Skutočný výstup | Prípady | Najnižší priemer FPS | Najhoršie p99 ms |
| --- | --- | ---: | ---: | ---: |
| Plynulosť | 1 920 × 1 080 | 10 | **100,91** | **16,50** |
| Plynulosť | 3 840 × 2 160 | 10 | 67,07 | 20,27 |
| Vyvážený | 1 920 × 1 080 | 10 | **65,69** | **20,63** |
| Vyvážený | 3 840 × 2 160 | 10 | 25,37 | 45,24 |
| Native | 1 920 × 1 080 | 10 | 29,29 | 42,56 |
| Native | 3 840 × 2 160 | 10 | 8,98 | 125,45 |
| Vyvážený, softvérový Lumen | 1 920 × 1 080 | 8 | **70,68** | **19,14** |

Retina ciele Plynulosť ≥60 FPS a Vyvážený ≥30 FPS s p99 <33,3 ms prešli.
Prešiel aj samostatný softvérový cieľ ≥30 FPS. Ide o wall-clock interval
aplikácie pri uncapped diagnostike; nie o meranie fyzického zobrazenia panelom.
Všetky behy boli v popredí, s odčítanými profilmi a overenými rozmermi PNG.

V statickom interiéri cez deň sa Plynulosť Retina zmenila z **39,14 na
120,00 FPS**, p99 z **32,97 na 8,52 ms**, pri zhodnej polohe a smere kamery.
Pri chôdzi deň/noc sú pôvodné priemery **17,03/17,16 FPS** a finálne
**100,91/118,92 FPS**; p99 **184,14/204,71 → 16,50/11,36 ms**. Pohybové
trajektórie nie sú úplne spárované a porovnanie zahŕňa Development → Shipping
aj súbor úprav kvality. Tieto údaje nepriraďujú celý prínos jednej zmene.

Päť pôvodných RHI záznamov malo GPU maximum 89 478,48 ms, dlhšie než celý
meraný interval. Ich surové agregáty sa nepoužívajú ako GPU dôkaz; FPS sa
meria osobitným časovačom. [Plán opakovania](../output/unreal/performance-validation-20260924-r1/gpu-recheck-plan.json)
vybral presne tieto prípady podľa chyby časovania. Každý sa zopakoval raz,
bez výberu vyššieho FPS. Napríklad najnižší Balanced Retina priemer sa po
opakovaní mierne znížil. Všetkých päť nových GPU záznamov je použiteľných;
akceptácia uchováva pôvodné aj vybrané dôkazy a odmieta nejednoznačné duplicity.

### Prvá Shipping séria R1 — splnené výkonové kritériá

Séria [`shipping-final-1790199522964`](../output/unreal/performance-20260923-r1/qa/shipping-final-1790199522964/summary.json)
dokončila všetkých **48** kombinácií: ulica, terasa, interiér deň/noc ×
tri profily × 1 920 × 1 080 / 3 840 × 2 160 × statická kamera/orbit.
Odčítanie požadovaných nastavení prešlo vo všetkých prípadoch. Pôvodných
**47/48** behov malo nepretržité popredie; interiér/deň, Balanced, Retina,
statická kamera následne prešiel [foreground opakovaním](../output/unreal/performance-20260923-r1/qa/shipping-recheck-focus-1790202485270/summary.json).

Dva pôvodné uličné Performance orbity (Retina aj 4K) majú v RHI GPU časovači
jednotlivé maximum **89 478,484 ms**, dlhšie než celý meraný frame interval
daného behu. Ich GPU priemery sa nepoužívajú. Oba príslušné prípady
nahradilo [platné GPU opakovanie](../output/unreal/performance-20260923-r1/qa/shipping-recheck-gpu-1790202425814/summary.json):
Retina GPU priemer/max **6,34/10,94 ms**, 4K **12,58/15,34 ms**.
Pôvodné dôkazy zostávajú zachované. Platné wall-frame intervaly a z nich
odvodené FPS sa chybou GPU časovača automaticky nezneplatňujú. Ide o inú kontrolu integrity než
poškodené poradie udalostí Insights opísané nižšie; ani jeden problém sa
nesmie zatajiť alebo nahradiť tvrdením, že každý zaznamenaný GPU čas je správny.

[Akceptačný prehľad](../output/unreal/performance-20260923-r1/acceptance.md)
má stav **passed**, **60/60** platných hlavných prípadov a **8/8**
samostatných softvérových prípadov. Všetkých 68 vybraných behov má
použiteľné RHI GPU agregáty podľa kontrol meracieho reportu; táto základná
kontrola sama nedokazuje presnosť každého timestampu.

Každý riadok tabuľky zahŕňa desať prípadov: osem statických/orbitových
a dve interiérové chôdze. Minimum FPS je **najnižší priemer jedného behu**,
nie najpomalšia jednotlivá snímka; p99 je najvyššie p99 z príslušných behov.

| Profil | Skutočný výstup | Minimum priemerného FPS | Najhoršie p99 | Platné prípady |
| --- | --- | ---: | ---: | ---: |
| Performance | Retina 1 920 × 1 080 | 118,42 | 11,40 ms | 10/10 |
| Performance | 4K 3 840 × 2 160 | 60,80 | 19,86 ms | 10/10 |
| Balanced | Retina 1 920 × 1 080 | 62,92 | 22,61 ms | 10/10 |
| Balanced | 4K 3 840 × 2 160 | 24,65 | 45,11 ms | 10/10 |
| Native | Retina 1 920 × 1 080 | 29,38 | 42,76 ms | 10/10 |
| Native | 4K 3 840 × 2 160 | 8,83 | 123,11 ms | 10/10 |

Native 4K teda **nie je plynulý herný režim**; ani Balanced 4K nedosahuje
30 FPS vo všetkých meraných prípadoch. Ich platné meranie sa nesmie
zameniť za splnenie výkonového prahu stanoveného pre Retina.

Hlavná matica obsahuje všetkých 60 platných prípadov vrátane [12 chôdzí](../output/unreal/performance-20260923-r1/qa/shipping-walk-1790202496748/summary.json)
interiér deň/noc × tri profily × dva výstupy. Každý z desiatich Retina
prípadov Performance musí mať priemer aspoň 60 FPS; Balanced aspoň 30 FPS
a p99 striktne pod 33,3 ms. Native a 4K musia byť platne odmerané, bez
pridaného výkonového prahu. Samostatná séria
[`shipping-software1080`](../output/unreal/performance-20260923-r1/qa/shipping-software1080-1790202920702/summary.json)
má osem platných Balanced prípadov pri 1 920 × 1 080 s HW Lumen 0,
minimum **75,10 FPS** a najhoršie p99 **22,10 ms**; všetky splnili prah
30 FPS. Samotný Performance tiež používa HW Lumen 0 vo všetkých 20
prípadoch. Ani jedna z týchto kontrol na M5 Pro nepreukazuje výkon M1/M2.

`performance-acceptance.mjs` vyberá opravné behy podľa presnej fázy a
hashu balíka, nikdy podľa vyššieho FPS. Duplicitné platné opravné behy sú
nejasný výsledok. Zachováva pôvodné údaje, samostatnú spôsobilosť GPU
časovania a tabuľky mean/p50/p95/p99 pre frame, GPU, Game a Render thread.
Statické rozdiely kamery potláčajú pomer zrýchlenia; koncová poloha kamery
pri pohybe sama nedokazuje zhodu celej trajektórie. Jedenásť fixture testov
analyzátora prešlo; ide o kontrolu výberu a vyhodnotenia dát, nie ďalšie
natívne meranie.

### Pôvodná aplikácia a skoršie R1 merania

Základná séria pôvodnej aplikácie je v
[`performance-20260923-r1/qa/baseline-1790193917881`](../output/unreal/performance-20260923-r1/qa/baseline-1790193917881/summary.json).
Pôvodný renderer stále používa staré postprocess kvality a pôvodný double
glass; pomenované staré profily sa pre meranie dopĺňajú explicitnými
percentami rozlíšenia. Nie sú ekvivalentom nového receptu z tabuľky.

Úvodný [uličný orbitový pokus](../output/unreal/performance-20260923-r1/qa/baseline-1790193917881/street-day-retina-performance-orbit-e4c7212c-6cae-4026-a769-4cc0a90aeb46/runtime.json)
nedosiahol 240 intervalov a má `measurementCompleted=false`. Takéto
neúplné pokusy zostávajú v histórii; ich existencia nie je úspešnou QA.
Porovnávacie tabuľky používajú iba túto presne určenú pôvodnú sériu,
nie skoršie smoke behy. Výnimkou je výslovný pôvodný `baseline-camera-recheck`
pre rozdielnu kameru interiér/noc, Balanced, 4K; nové odčítané eye/forward
sú zhodné a opravný pár bol aj vizuálne prezretý. Chôdza je porovnaná
s [12 platnými baseline-walk behmi](../output/unreal/performance-20260923-r1/qa/baseline-walk-1790203073926/summary.json)
z [instrumentovanej pôvodnej aplikácie](../output/unreal/performance-baseline-instrumented-20260923-r1/baseline-instrumentation.json):
pôvodný renderer a scéna s výmenou štyroch diagnostických/Pawn súborov,
Development receipt SHA256
`0ce20dfe744a69760db5625581db18e8b8b09a443982f06c22622426a173b068`.
Taký pohybový experiment poskytuje kvalifikované časové rozdelenia,
nie dôkaz izolovaného kauzálneho zrýchlenia.

Pri Performance Retina chôdzi sa pôvodný priemer deň/noc **17,03/17,16 FPS**
a p99 **184,14/204,71 ms** zmenili na Shipping R1 **118,42/118,96 FPS**
a p99 **10,99/11,40 ms**. Úplné frame/GPU/Game-thread/Render-thread
rozdelenia všetkých 12 párov sú v akceptačnom prehľade. Porovnanie zahŕňa
Development → Shipping aj viacero renderovacích zmien; nie je testom
jedného cvaru ani úplnej totožnosti prejdenej trajektórie.

R1 na Apple M5 Pro, Metal, Development, **interiér/deň, Performance,
PNG 1 920 × 1 080, primárna mierka 50 %, TSR história 100 %**:

| Režim | Intervaly | Priemerný interval | FPS z priemerného intervalu | p99 |
| --- | ---: | ---: | ---: | ---: |
| Statická kamera | 300 | 9,3066 ms | 107,45 | 12,8523 ms |
| Orbit ±8°, 30,008 s | 3 577 | 8,3892 ms | 119,20 | 10,8091 ms |
| Chôdza, 30,008 s | 3 541 | 8,4745 ms | 118,00 | 11,1257 ms |

Dôkazy: [statický runtime](../output/unreal/performance-20260923-r1/qa/runtime-optimized-smoke-1790197353392/interior-day-retina-performance-static-c6a8953a-b062-4f9d-aa55-ac4a87318a5c/runtime.json),
[orbit](../output/unreal/performance-20260923-r1/qa/runtime-optimized-smoke-1790197353392/interior-day-retina-performance-orbit-c5a22e0a-f0b5-46bd-93eb-50e0044a021f/runtime.json),
[chôdza](../output/unreal/performance-20260923-r1/qa/runtime-optimized-smoke-1790197353392/interior-day-retina-performance-walk-b91496a5-d57d-470a-b9af-3a7f2db9ef63/runtime.json)
a [QA súhrn](../output/unreal/performance-20260923-r1/qa/runtime-optimized-smoke-1790197353392/summary.json).
Všetky tri procesy skončili s exit 0 a aplikácia bola počas všetkých
meraných intervalov v popredí. FPS je výpočet `1000 / meanMs`, nie počet
prezentácií nameraný systémovým compositorom.

Chôdza prešla 25,69 m, dosiahla desať bodov a dva celé návraty. Native
preflight uspel; 3 782 vzoriek očí bolo podopretých podlahou, nepodopretých
bolo 0, najväčšia chyba výšky očí bola 1,07 × 10⁻⁷ cm a zahodený čas
CharacterMovement bol 0 s. Hodnoty podpory zahŕňajú aj zahrievanie. Trasa
neobsahuje priechod celým domom ani otvorenie dverí; pri chôdzi sa vyskytol
aj jednotlivý interval 50,43 ms, ktorý priaznivé p99 nesmie zakryť.

Samostatné vypnutie iba doplnkového skla v **pôvodnom balíku** dokladá
dominantnú príčinu spomalenia pri pohybe: interiérový denný orbit klesol
z 109,7009 ms (9,12 FPS, 60,006 s / 547 intervalov) na 19,4731 ms
(51,35 FPS, 30,008 s / 1 541 intervalov; p99 28,2448 ms).
[Pôvodný orbit](../output/unreal/performance-20260923-r1/qa/baseline-1790193917881/interior-day-retina-performance-orbit-a1701f6f-0f62-49ec-bd01-fdef27252975/runtime.json),
[orbit s vypnutým sklom](../output/unreal/performance-20260923-r1/qa/baseline-glass-off-1790196864404/interior-day-retina-performance-orbit-5bf2f3c7-d621-4cac-befe-7e9362052ce5/runtime.json).
V druhom behu všetkých 19 aktérov hlásilo `enabled=false` a
`captureCount=0`. Dĺžky behov sa líšia; nejde o izolované vysvetlenie
všetkých rozdielov medzi R1 a pôvodným balíkom. Statický glass-off beh
mal priemer 26,29 ms, teda rovnaký veľký prínos v pokoji neukázal.

Tieto skoršie Development výsledky vysvetľujú smer úprav. Nenahrádzajú
vyššie uvedenú hlavnú Shipping maticu ani jej zostávajúce kontroly.

## Natívne vizuálne porovnanie

Finálny **Shipping R4** má novú kontrolu všetkých **24 párov / 48 pôvodných
PNG**, so zhodným eye/forward v každom statickom páre. [Exteriér R4](../output/unreal/performance-validation-20260924-r1/visual-review-exterior.json)
a [interiér R4](../output/unreal/performance-validation-20260924-r1/visual-review-interior.json)
odkazujú na presne vybrané akceptačné zábery vrátane opráv. Všetky 4K
obrázky boli zobrazené v pôvodnom rozlíšení, bez obrazových úprav.

V kontrolovaných pohľadoch sa nepozoroval zjavný výpadok či posun
architektonických prvkov alebo materiálov. Native zostáva vizuálne najbližší
pôvodnej aplikácii. Balanced aj Performance majú redšiu vegetáciu,
jednoduchšie/tmavšie odrazy skla a hrubšie, miestami zúbkované hrany
tieňov pod odkvapom na terase. Plynulosť má najsilnejší úbytok detailov
a v kuchyni najmä v noci svetlejšiu, plochejšiu dosku a drez so slabšími
kontaktnými tieňmi. Statická kontrola potvrdzuje vizuálnu kontinuitu
s týmito kompromismi; nie pixelovú zhodu ani absenciu časových artefaktov.

### Historická obrazová séria R1

Priame neupravené PNG prvej Shipping série R1 boli prezreté v **24 pároch**: štyri scény × tri
profily × dva výstupy. [Exteriérový záznam](../output/unreal/performance-20260923-r1/visual-review-exterior.json)
a [interiérový záznam](../output/unreal/performance-20260923-r1/visual-review-interior.json)
uvádzajú presné cesty, rozsah zobrazenia a jednotlivé pozorovania.
Geometria a usporiadanie zostávajú v kontrolovaných statických záberoch
vizuálne zachované. Native je vzhľadom najbližší pôvodnému balíku;
Balanced zachováva lokálne tiene a väčšiu časť detailov. Performance
má viditeľne redší drobný porast a viac holej pôdy, plochejší trávnik,
slabšie lokálne tiene a jednoduchšie, tmavšie okenné odrazy. V interiéri
je pracovná doska a drez najmä v noci svetlejší a plochejší.

Pôvodný pár interiér/noc, Balanced, 4K má rozdielnu kameru a zostáva takto
označený v histórii. [Opravný beh](../output/unreal/performance-20260923-r1/qa/baseline-camera-recheck-1790202379347/summary.json)
má presne zhodné odčítané eye/forward a jeho priamy obrazový pár prešiel
vizuálnou kontrolou; dodatok interiérového záznamu tak uzatvára všetkých
12 interiérových kombinácií. Samostatná zhoda FOV sa z týchto údajov netvrdí.
Časť 4K PNG bola prezretá v zmenšenom zobrazení nástroja, čo obmedzuje
posúdenie detailov. Statické obrázky nepotvrdzujú absenciu preblikávania,
ghostingu, objavovania trávy ani správne obnovovanie skleneného odrazu
po pohybe, otvorení dverí alebo zmene svetla. Záverečná natívna UI kontrola
uloženia a obnovy používateľského profilu je opísaná nižšie.

### Priechod celým domom a bežné ovládanie

Natívny [kontinuálny priechod Development R2b](../output/unreal/performance-20260923-r2b/qa/walkthrough-a92d0fd2-6a8f-470a-b648-511f1dd01c43/qa.json)
skončil s `continuous-walkthrough-validated`, bez chýb: **13 miestností,
tri terasy, tri exteriérové prístupy, 16 dverí, tri otvorené priechody,
134 krokov a 202,51 m**. Obsahoval 32 otvorení a 16 zatvorení dverí,
teda aj opätovné otvorenie. Po jedinom úvodnom umiestnení pokračoval
natívnym pohybom a hernými vstupmi. Tento test overuje kolízie a trasu;
nemeria FPS ani reakcie operačného systému na držanie klávesov.

[Doplňujúca vizuálna kontrola](../output/unreal/performance-20260923-r1/visual-review-walkthrough.json)
prezrela kúpeľňu, spálňu, chodbu, WC a záhradnú terasu. V zobrazených
častiach nechýbajú hrubé stavebné plochy ani materiály. Kúpeľňové zrkadlo
má výrazné rozmazanie/škvrnitosť a terasa šum na vode a skle; avatar
zakrýva časť spálne a záber WC má obmedzený rozsah. Ide o jednotlivé
Performance snímky, nie o kompletnú fotorealistickú kontrolu každej miestnosti.

Pri bežnom Shipping R1 ovládaní prešlo prepínanie profilov, vstup do
obývačky, prepnutie pohľadu, deň/noc a prechod medzi chôdzou a letom
s výškovými vstupmi E/Q. Uložený Balanced sa obnovil po ukončení a novom
spustení. Návrat na predvolenú Plynulosť však odhalil chybu overenia
uloženia: UE 5.8 zapisuje rozdiel oproti konfigurácii projektu a predvolený
kľúč môže vynechať. Pôvodný [záznam zlyhania](../output/unreal/performance-20260923-r1/performance-ui-8d837bf1-5d11-4e55-9279-25b678dcf7a1/review.json)
zostáva zachovaný; tento kandidát nie je prijatým finálnym balíkom.

Oprava v čerstvom **Shipping R4** číta skutočný uložený delta súbor,
zlúči ho s oddelenou kópiou základných vrstiev a overí hodnotu, ktorú načíta
nasledujúci štart. Nepoužíva aktuálnu pamäťovú hodnotu ako dôkaz uloženia;
zlyhaný alebo zakázaný zápis a starý diskový override zostávajú chybou.
[Natívny UE test](../output/unreal/performance-shipping-20260924-r4/tests/profile-persistence-native-1/verification.json)
prešiel 1/1, bez testových chýb alebo upozornení, proces exit 0.

[Bežné UI R4](../output/unreal/performance-validation-20260924-r1/performance-final-ui-edc1a970-52ba-4d7c-87e0-aede6e976997/review.json)
prešlo **päť štartov a štyri reštarty** v samostatnom používateľskom
priečinku, bez diagnostického zámku: Balanced → reštart → Performance
→ reštart → Native → reštart → Performance → reštart. Každá voľba sa
obnovila v rozhraní. Oba návraty na predvolenú Plynulosť mali správne
vynechaný delta kľúč a normálny stav bez hlásenia chyby. Overený je aj
vstup do obývačky, pohľad z očí, deň/noc a prechod chôdza–prelet–chôdza.
Krátke klávesové vstupy a rozhľad nenahrádzajú meraný prejdený úsek.

V nočnom pohľade zvonka sú okná silno presvetlené aj v Balanced
s vypnutým doplnkovým sklom. Dodatočný Native pár pôvodného balíka
a Shipping R4 pri 1 920 × 1 080 má presne zhodné eye/forward
([záznam a hashe](../output/unreal/performance-validation-20260924-r1/night-street-review.md)): biele okná
bez detailov a silná teplá žiara fasády boli prítomné už v pôvodnej
aplikácii. Rozsah expozície −6 až 14 a bias 0 sa zhodujú; skutočná EV
sa mierne líši. Starý Native používa históriu 200 % a Lumen FG/odrazy 4,
nový 100 % a 1, preto sa netvrdí úplná pixelová zhoda. Ide o pretrvávajúce
obmedzenie osvetlenia, ktoré optimalizácia neodstránila.
Po zmene profilu alebo kamery sa objavuje dočasný šum. Absencia každého
prebliknutia, ghostingu či objavenia porastu sa týmito kontrolami netvrdí.

## ProfileGPU: pôvodný balík a R1

Samostatný ProfileGPU počas zahrievania rovnakého interiérového denného
záberu pri 1 920 × 1 080 a 50 % primárnej mierke ukazuje:

| Udalosť | Pôvodný balík | R1 Performance |
| --- | ---: | ---: |
| Celý profilovaný GPU frame | 19,590 ms | 6,680 ms |
| ShadowDepths | 1,454 ms | 0,578 ms |
| VSM renderovanie Non-Nanite | 0,914 ms | 0,295 ms |
| Jeho rasterizačná podmnožina | 0,758 ms | 0,205 ms |
| VSM renderovanie Nanite | 0,203 ms | 0,191 ms |
| Označovanie VSM stránok | 0,276 ms | 0,093 ms |
| Lumen Scene Lighting | 3,308 ms | 0,359 ms |
| Hlavný Lumen Screen Probe Gather | 5,250 ms | 1,534 ms |
| TLV clear | 2,151 ms, 64³ | 0,006 ms, 32³ |
| TLV osvetlenie/filter | 0,292 ms | 0,051 ms |
| TSR | 1,020 ms | 1,020 ms |
| BasePass | 0,150 ms | 0,150 ms |

Zdroj: [pôvodný ProfileGPU](../output/unreal/performance-20260923-r1/qa/baseline-1790193917881/interior-day-retina-performance-static-9180d3a0-a74a-4231-8360-8caaedfab34d/interior-day-20260923T200852-gpu-profile.log)
a [R1 ProfileGPU](../output/unreal/performance-20260923-r1/qa/runtime-optimized-smoke-1790197353392/interior-day-retina-performance-static-c6a8953a-b062-4f9d-aa55-ac4a87318a5c/interior-day-20260923T210240-gpu-profile.log).
Ide o jeden frame každého behu a o pripísané časy udalostí. Vnorené riadky
sa nesčítavajú; nulový čas Lumen reflection udalosti neznamená neprítomnosť
odrazu. Nezávislý RHI timer za 300 meraných intervalov uvádza GPU priemer
18,82 → 7,36 ms. Naraz sa zmenilo viacero rozpočtov aj HWRT → software
Lumen, preto tabuľka neizoluje jednotlivé úpravy.

Zvyšných 0,295 ms Non-Nanite VSM tvorí približne 4,4 % tohto R1 GPU frame.
Nie je to zaručená úspora ani identifikácia konkrétneho meshu. Nadväzujúci
malý opaque Nanite experiment je opísaný nižšie a má vlastný oddelený
balík. Tento interiérový výsledok sám neodôvodňuje plošnú konverziu geometrie.

V pôvodnom interiéri cez deň pripisuje ProfileGPU udalosti
`ClearTranslucencyLightingVolumeCompute 64` tieto časy:

| Výstup a primárna mierka starého profilu | Pripísaný čas udalosti |
| --- | ---: |
| Retina, 50 % | [2,151 ms](../output/unreal/performance-20260923-r1/qa/baseline-1790193917881/interior-day-retina-performance-static-9180d3a0-a74a-4231-8360-8caaedfab34d/interior-day-20260923T200852-gpu-profile.log) |
| Retina, 67 % | [3,594 ms](../output/unreal/performance-20260923-r1/qa/baseline-1790193917881/interior-day-retina-balanced-static-a22d04c3-4d03-44d6-a8f5-b6a903761546/interior-day-20260923T202245-gpu-profile.log) |
| 4K, 50 % | [7,856 ms](../output/unreal/performance-20260923-r1/qa/baseline-1790193917881/interior-day-4k-performance-static-b16262da-9f6e-4def-97e7-8ad456d00cd8/interior-day-20260923T201530-gpu-profile.log) |
| 4K, 67 % | [13,768 ms](../output/unreal/performance-20260923-r1/qa/baseline-1790193917881/interior-day-4k-balanced-static-1303f35c-a655-43ac-ae7d-a2b9e80e12b0/interior-day-20260923T202947-gpu-profile.log) |

Susedné HWRT udalosti v týchto logoch majú 0 ms. Samotný clear pritom
pracuje s pevnou mriežkou 64³; počet skupín sa odvodzuje z rozmeru objemu,
nie z rozlíšenia obrazu. To dokladá
[TranslucentLighting.cpp](</Users/Shared/Epic Games/UE_5.8/Engine/Source/Runtime/Renderer/Private/TranslucentLighting.cpp:1359>).
Výrazné škálovanie pripísaného času s počtom obrazových pixelov preto
nemožno vydávať za samostatne odstrániteľnú cenu vymazania objemu. Na
lokálnej Metal ceste treba rátať s pripisovaním časov encoderov udalostiam;
vzorky sa viažu k aktívnym breadcrumbs v
[MetalProfiler.h](</Users/Shared/Epic Games/UE_5.8/Engine/Source/Runtime/Apple/MetalRHI/Private/MetalProfiler.h:123>).
Ide o indíciu hrubšieho časového priradenia, nie izolovaný shader benchmark.
Oddelený prínos zmeny TLV musí potvrdiť kontrolovaný nový beh. Úplné
`r.TranslucencyLightingVolume=0` síce preskočí alokáciu a clear, ale vracia
čierne osvetľovacie objemy; bez vizuálneho porovnania sa nepoužilo.
[Implementácia vypnutia](</Users/Shared/Epic Games/UE_5.8/Engine/Source/Runtime/Renderer/Private/TranslucentLighting.cpp:1277>).

`VSM Log Stats And Status` sa podľa zdrojov enginu neodstráni samotným
Shipping buildom. Renderer volá
[`RenderDebugInfo`](</Users/Shared/Epic Games/UE_5.8/Engine/Source/Runtime/Renderer/Private/DeferredShadingRenderer.cpp:4081>)
pri zapnutých VSM a dostupnom pohľade; následný
[`LogStats`](</Users/Shared/Epic Games/UE_5.8/Engine/Source/Runtime/Renderer/Private/VirtualShadowMaps/VirtualShadowMapArray.cpp:3645>)
odosiela aj stavové hlásenia, napríklad pretečenie stránok, keď sú štatistiky
vypnuté. Shipping vypína časť štatistického feedbacku, nie celý tento pass.

V kontrolovaných pôvodných logoch má táto udalosť približne **0–0,083 ms**,
napríklad [0,083 ms pri ulici v 4K](../output/unreal/performance-20260923-r1/qa/baseline-1790193917881/street-day-4k-balanced-static-9d88d2d3-3414-4e49-90a1-9b339ee1964b/street-day-20260923T202546-gpu-profile.log).
Má preto nižšiu prioritu než Lumen a scene captures; starší údaj okolo
1 ms sa neprenáša na túto revíziu. Aktuálny cvar je
`r.Shadow.Virtual.Stats.Visible`; `r.Shadow.Virtual.ShowStats` je od UE 5.7
zastaraný alias podľa
[VirtualShadowMapArray.cpp](</Users/Shared/Epic Games/UE_5.8/Engine/Source/Runtime/Renderer/Private/VirtualShadowMaps/VirtualShadowMapArray.cpp:367>).
V R1 interiéri táto udalosť predstavuje 0,003 ms. Shipping matica meria
celkový frame a RHI GPU timer; táto hodnota z Development ProfileGPU sa
nevydáva za samostatne nameraný Shipping pass.

## Insights: čisté ukončenie a obmedzenie časovej osi

Pôvodný aj R1 attribution beh skončili čisto s exit 0 po nastavení
obidvoch PSO pool cvarov **pred inicializáciou enginu**:

```text
-ini:Engine:[ConsoleVariables]:r.pso.PrecompileThreadPoolSize=0,[ConsoleVariables]:r.pso.PrecompileThreadPoolPercentOfHardwareThreads=0
```

Tieto dva read-only cvary presunú PSO precompile na existujúci task graph;
nevypínajú precaching. Samotné `-notracethreading` predtým nestačilo:
capture bol uložený, ale pôvodný proces zlyhal pri ukončení v PageAllocator.
Nastavenie poolu je workaround samostatných attribution behov, nie zásah
do bežnej aplikácie ani súčasť neinstrumentovaných FPS výsledkov.

[Pôvodná analýza, PID 54796](../output/unreal/performance-20260923-r1/qa/baseline-attribution-taskgraph-1790197487774/interior-day-retina-performance-static-dc915a12-8cb3-44af-83cc-cc55a4ca3d31/insights-analysis/analysis.json)
a [R1 analýza, PID 54960](../output/unreal/performance-20260923-r1/qa/runtime-attribution-1790197531321/interior-day-retina-performance-static-e2c1f9fe-e1d0-4b3d-a0a5-a52ff38cf9b8/insights-analysis/analysis.json)
majú stav `whole-trace-analysis-qualified`. **GPU timeline oboch zostáva
poškodená**: pôvodný záznam hlási 48 006 udalostí s chybou poradia
(`interleaved`) a 8 993 obrátených alebo premiešaných udalostí
(`interleaved and reversed`), R1 28 748 a 7 070; každý má aj jeden vynútene
uzatvorený RHI command list. Čistý exit tento samostatný problém časových
značiek neopravuje. Numerické GPU trvania z týchto `.utrace` sa odmietajú.

Exporty CPU slúžia iba na priradenie práce vláknam a scope udalostiam za
celý trace, vrátane štartu, zahrievania a screenshotu. Nie sú steady-state
FPS ani p99 herného intervalu. GPU export dokladá zaznamenané udalosti,
nie ich spoľahlivé časy. Vyššie uvedené ProfileGPU a RHI timer sú samostatné
zdroje s vlastnými, výslovne uvedenými limitmi.

## Oddelený Nanite experiment R4 — nezaradiť

[Natívny experiment](../output/unreal/performance-nanite-20260923-r4/nanite-study-summary.json)
je zabalený ako `experimental-nanite-packaged-unaccepted`. Z 120 skúšaných
opaque mesh assetov prešlo prísnymi kontrolami **117 mesh assetov** so
spolu **1 884 zdrojovými trojuholníkmi**; tri boli odmietnuté kontrolou
natívnych odvodených bounds. Zachovalo sa 2 735 aktérov aj mapa, zmenilo sa
presne 117 povolených assetov a ďalších 2 679 Content súborov zostalo
identických. Kontrola po uložení a novom načítaní prešla.

Zdrojové pozície, topológia a všetky UV musia zostať presné. Odvodené
bounds povoľujú najviac jednu float32 ULP na súradnicu, s limitom
0,0002 cm; pozorované maximum je 0,00006104 cm. Vybraná skupina nemá herné
kolízie. Surové normály/tangenty a cooked Chaos dáta nie sú týmto Python
záznamom dostupné, takže ich úplná binárna zhoda sa netvrdí.

Experiment používa **rovnaký natívny Shipping build ako kandidát R1**;
jeho samostatný receipt má SHA256
`0802e6f7202df265938cfb3dc5226d153898e01ce37909bf84a55e1807657747`.
[Dokončené A/B vyhodnotenie](../output/unreal/performance-20260923-r1/nanite-evaluation.md)
([JSON](../output/unreal/performance-20260923-r1/nanite-evaluation.json)) vedie
k rozhodnutiu **nezaradiť zmeny do hlavného balíka**. Štyri skúšky
Native interiéru deň (Retina/4K × statická kamera/orbit) ukázali zmenu
priemerného FPS **−0,17 % až +3,57 %**. Retina orbit sa mierne zhoršil;
jediný beh na podmienku bez intervalu spoľahlivosti nedokazuje sústavný
prínos. Dva statické obrazové páry vrátane 4K nemali zjavný posun
kontrolovanej kuchynskej geometrie, no zachovali drobné rozdiely tieňovania
a kresby. Nie je to pixelová zhoda ani vizuálne prijatie celého domu.

Nanite je v oboch
porovnávaných balíkoch globálne zapnutý; globálne `r.Nanite=0` by nebolo
izolovaným porovnaním tejto skupiny. Experiment **nie je súčasťou hlavného
kandidátneho Shipping receptu**, nemá prijatý výkon ani vzhľad a nie je
povýšený do aktuálneho balíka.

## Otvorené body

- [Spustenie po povýšení](../output/unreal/performance-validation-20260924-r1/post-promotion-launch.json):
  `npm run unreal:open` aj pohľad `-- street` skončili s exit 0 a spustili
  správny R4 proces. Záverečné pripojenie CUA k oknu a screenshot však
  opakovane vypršali na časovom limite. Vzorka pôvodného procesu obsahuje
  herný tick a vykresľovanie; sama nepotvrdzuje vizuálny stav ani zamrznutie.
  Posledné otvorené okno preto nemá nový vizuálny dôkaz. Päť skorších
  bežných UI štartov toho istého balíka v izolovanom UserDir prešlo.
  Používateľské nastavenia pri poslednej kontrole neboli resetované.
- GPU časová os Insights je v oboch čistých attribution behoch poškodená;
  kvalifikované CPU exporty sa nesmú prezentovať ako úplné GPU overenie.
- Simulácia softvérového Lumenu na M5 Pro nepreukazuje výkon fyzického
  M1/M2 ani úplnú zhodu ich podporovaných renderovacích funkcií.
- Native 4K zostáva pomalý (najnižší priemer 8,98 FPS); Balanced 4K
  klesá na 25,37 FPS. Úspešné Retina kritériá tieto režimy necertifikujú.
- Dynamické rozlíšenie zostáva vypnuté. Pevné percentá umožňujú porovnať
  recepty; časový cieľ 16,7/33,3 ms zatiaľ dynamicky nepresadzujú.
- Skylight zatiaľ zachováva real-time capture. Súčasný plynulý prechod
  deň/noc ho vyžaduje; jednoduché vypnutie by zmenilo správanie prechodu.
- Oddelený Nanite R4 experiment sa nezaradí. Plošné rozšírenie Nanite a
  zlučovanie HISM nie sú prijaté; Nanite automaticky neznižuje počet RT
  inštancií. Dvere, kolízie, materiály a väzby `DOM_xxxxx` zostávajú chránené.
- Projektové front-layer reflections, SingleLayerWater refraction,
  CustomDepth a cena global clip planes ešte nemajú samostatné merané
  rozhodnutie. Kaustika zostáva mimo bežného balíka.
- Povinné celé sady majú výsledok 806/806. Testy akceptačného analyzátora
  a importu meraní sú už zaradené do `unreal:test`; samostatný natívny
  UE test ukladania profilov sa k tomuto hostiteľskému súčtu nepripočítava.

Technické podklady:
[Epic — Lumen Performance Guide](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-performance-guide-for-unreal-engine),
[Epic — Nanite](https://dev.epicgames.com/documentation/en-us/unreal-engine/nanite-virtualized-geometry-in-unreal-engine).
Rozdelenie hlavného návrhu a historických dôkazov opisujú
[aktívny návrh](active-design.md), [model refresh](unreal-model-refresh.md),
[materiálová revízia](unreal-photoreal.md) a [vidiecke okolie](unreal-rural-context.md).
