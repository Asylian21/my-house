# 4K výstup s nižším interným rozlíšením — 9. september 2026

Táto historická štúdia skúšala na explicitnú požiadavku používateľa TSR rekonštrukciu pri zachovaní výstupu 3840 × 2160 na balíku `73b9d1d887f1bda6b3991c27773deac7df5d1c00335952ff00a70ccabd686a6f`. Pôvodný požadovaný 100 % interný render už nebol podmienkou týchto profilov. Geometria, materiály, rozmery okna a podpísaný balík sa počas porovnania nemenili. Uvedené FPS a motion výsledky sa neprenášajú na novší UI balík.

Aktuálne tri natívne voľby, predvolené Vyvážené 67/100, uloženie a dočasný CLI profil sú opísané v [profiloch kvality natívnej aplikácie](unreal-quality-profiles.md), vrátane skutočného v2 UI overenia a zostávajúcich kontrol.

## Skutočné meranie pri bazéne

| Interné rozlíšenie | TSR história | Priemer snímky | Pozorovaný výkon | P95 |
| --- | --- | ---: | ---: | ---: |
| 100 % | 200 % | 65,492 ms | 15,27 FPS | 66,465 ms |
| 67 % | 100 % | 41,177 ms | 24,29 FPS | 42,095 ms |
| 50 % | 100 % | 29,222 ms | 34,22 FPS | 30,084 ms |

Každý prijatý beh mal 600 zahrievacích a 300 meraných snímok, všetkých 300 s aktívnou aplikáciou aj oknom. Počas merania nebežal GPU profil ani diagnostické GPU readbacky kaustík. Lumen HWRT, Nanite, VSM a TSR zostali zapnuté; poskytovateľ kaustík vytvoril 843 snímok v každom behu. Pred aj po meraní bol overený celý nezmenený balík. Ide o pozorovaný wall-clock výkon vrátane čakaní/VSync, nie o dôkaz všeobecných 45–60 FPS alebo opakovaný teplotne kontrolovaný benchmark.

Dva behy 100 % / história 100 % stratili popredie a zostávajú vyradené. Samostatná úspora 5–10 ms zo zmeny histórie preto nie je týmto porovnaním preukázaná. Kompletné výsledky, pôvodné PNG, hashe a vyradené behy sú v [summary.json](../output/unreal/caustics-delivery/upscale-study/summary.json).

Samostatné skutočné GPU profily zaznamenali:

- 67 %: `TemporalSuperResolution … 2573x1448 -> 3840x2160`, `TSR UpdateHistory … 3840x2160`.
- 50 %: `TemporalSuperResolution … 1920x1080 -> 3840x2160`, `TSR UpdateHistory … 3840x2160`.

To dokladá rozmery týchto TSR priechodov v profilovanej snímke. Časy z profilov nepoužívame ako čistý výkon a zdieľané Metal encoder časy nepripisujeme jednotlivým clear shaderom. Výstup sa zachováva podľa [dokumentácie Epic k TSR](https://dev.epicgames.com/documentation/unreal-engine/temporal-super-resolution-in-unreal-engine); priechody po TSR sa už neškálujú primárnym Screen Percentage, takže celkový výkon nerastie automaticky štvornásobne pri 50 %.

## Pohyb a kvalita

Oba profily dokončili 64 pôvodných 4K PNG na rovnakej kamerovej trase terasa → bazén; samostatné validácie zdroja, kamery, hodín a výstupu prešli. PID 55294 zachytil 67 %, PID 61187 zachytil 50 %. Simulácia pri snímaní používa 30 Hz a PNG readbacky; tieto behy nemerajú FPS.

Pôvodný Node vstup prvého behu skončil 13 na cyklickom importe následného validátora, až po korektnom ukončení natívnej aplikácie s exit 0. Existujúce snímky prešli samostatnou kontrolou cez externý ESM vstup. Nový `motion/invoke.mjs` odstránil cyklus v spúšťaní; pôvodné zmrazené súbory ani dôkazy sa nemenili.

Striktný párový validátor odmietol zhodu subpixelového jitteru medzi 67 % a 50 %. Jednotlivé záznamy sú platné; nevydávame ich za experiment s identickým jitterom. Root prezrel pôvodné statické 4K výstupy všetkých troch nastavení a snímku 25 oboch pohybových záznamov. Hlavné hrany a členenie ostávajú čitateľné, jemná kresba dreva je pri 50 % mäkšia. To nie je potvrdenie úplne neviditeľného rozdielu ani celého pohybu bez artefaktov.

Nezávislý reviewer prezrel snímky 24, 25, 52 a 63 oboch profilov: 67 % uprednostnil pre architektonické detaily, 50 % zostáva použiteľnou výkonovou voľbou s mierne mäkšími tenkými hranami a drevom. Všetkých 64 póz/FOV sa zhoduje; jitter sa líši. Fáza materiálov sa líšila o 0,354 s a expozícia o 0,0018–0,0046 EV, preto nejde o úplne identické časové podmienky. Podrobnosti: [motionvisual.json](../output/unreal/caustics-delivery/upscale-study/motionvisual.json).

Aplikácia bola následne skutočne otvorená cez maintained CLI v profile `tsr50` (PID 72302). Jej log potvrdil 50 % / históriu 100 % a inicializovaný engine; zostala spustená na používateľovo vyskúšanie. Tento interaktívny beh nemá samostatné meranie FPS.

## Spustenie

Maintained CLI teraz prijíma konkrétny delivery report a jeho SHA. Profily sú explicitné voľby pre `open`; predvolené nastavenia existujúceho balíka ostali zachované. Presné príkazy sú v [návode CLI](../scripts/unreal/caustics/README.md). `BREZI_RENDER_PROFILE=tsr67` používa 67 % / históriu 100 %, `tsr50` používa 50 % / históriu 100 %. Bežná QA cesta s pôvodnou podmienkou 100 % odmieta škálovaný profil pred natívnym spustením.

Overenie integrácie: 49 súvisiacich Node testov, kontrola skutočného delivery balíka (45 súborov), pôvodného balíka (37 súborov), vstupného bodu a podpisov prešli. Samotný automatický build → cook → binding → seal zostáva samostatnou nedokončenou prácou.

Voľba kvality je už integrovaná do natívneho UI; samostatný [aktuálny záznam overenia](unreal-quality-profiles.md) dokladá v2 kliknutia, uloženie a relaunch. Vyhodnotenie ďalších pohľadov, fotorealizmus, finálny UX a cieľová plynulosť celej aplikácie zostávajú otvorené. Oheň v tejto iterácii nemeníme.
