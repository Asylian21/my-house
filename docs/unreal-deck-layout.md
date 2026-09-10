# Súvislý raster terasových dosiek

Spoločný Babylon/Unreal zdroj opravuje nepravidelné medzery na terase. Opravený samostatný macOS balík `dd6cb6cb…` už prešiel buildom, cook/archive, podpisom, kontrolou vstupu do chôdze a stabilného státia. Dva skutočné 4K zábery pri profiloch 67/100 a 50/100 potvrdzujú uzavretie širokej medzery v popredí. Konkrétne výsledky a hranice overenia pripája [delivery review](../output/unreal/deck-gap-study/delivery-review.json).

## Príčina a oprava

Pôvodné `buildDeckZone` začínalo raster 145 mm doska / 8 mm škára odznova v každom pomocnom obdĺžniku a vynechávalo krátke koncové pásy. Pri bazéne tak vznikli otvorené pásy široké 49 a 37 mm.

[Spoločný plánovač](../lib/deck-boards.ts) používa jeden Y raster pre celú zónu a spája dotýkajúce sa X intervaly pri zhodnom reze. Výsledok preto nezávisí od pomocného rozdelenia pôdorysu. Zachováva hranice terasy, servisný otvor 900 × 1100 mm, hrúbku dosiek 28 mm a hornú plochu +20 mm. Posun rastra volí tak, aby kladné krajné odrezky mali aspoň 40 mm; táto minimálna šírka je navrhnuté konštrukčné pravidlo, nie meranie osadených dosiek.

V skutočnom exportovanom OBJ sa 49 mm otvor uzavrel a z 37 mm otvoru zostala pravidelná 8 mm škára. Zdrojový audit porovnáva všetky trojuholníky s ich normálami a UV0, nezávisle od prečíslovania OBJ indexov:

| Zdrojový objekt | Dosky pred → po | Trojuholníky pred → po |
| --- | ---: | ---: |
| DOM_01708, záhradná terasa | 78 → 78 | 936 → 936 |
| DOM_01713, vstupná terasa | 47 → 35 | 564 → 420 |
| DOM_01719, terasa pri bazéne | 68 → 64 | 816 → 768 |

Ostatných **1 892 objektov** zachovalo rovnaké polohy, topológiu, normály a UV0. Zhodné zostali aj rozmery a ostatné metadáta modelu, materiály, bazén, servisný otvor a bajty samostatného collision GLB. Bočná terasa DOM_01710 a poklop DOM_01779 sa nemenili. Podrobnosti sú v [geometrickej delte](../output/unreal/deck-gap-study/geometry-delta-v2.json).

## Overenie

- Prešlo 328 testov v 33 súboroch, ESLint zmenených TS súborov a produkčný webový build.
- [Nový export](../output/unreal/deck-gap-study/geometry-candidate-v2) má 1 895 objektov a 393 547 trojuholníkov. Khronos validácia oboch GLB skončila bez chýb a upozornení. Blender spätný import celého modelu mal maximálnu odchýlku hraníc 0,008313 mm.
- [Tri samostatné GLB](../output/unreal/deck-gap-study/derived-v2/report.json) zachovávajú pôvodné bajty geometrie, normál, UV0 a indexov a pridávajú fyzické UV1 pre existujúce fotomateriály. Ich prepočet overuje rovnaký geometrický plánovač, bez zmeny starých native guardov.
- Natívny import a uloženie mapy: PID **56728**, exit **0**, všetky vlastnené procesy skončili. Zmenil sa iba klon mapy a pribudol importný pipeline asset s tromi meshmi. Pôvodné materiály a nastavenia Nanite zostali rovnaké. Nové meshe importujú UV v plnej float32 presnosti.
- Nezávislé nové otvorenie projektu: PID **57988**, exit **0**, žiadne zmeny bajtov Content. Pre všetky tri meshe sú overené polohy, cyklické poradie a násobnosť trojuholníkov, UV0 a presné float32 UV1 v MeshDescription. Verejný `ProceduralMeshLibrary` getter overil aj jedinú skutočnú LOD0 sekciu s kompletnou geometriou a UV0. Najväčšia odchýlka polohy je **0,001297 mm**.
- Porovnanie scény zahŕňa 1 968 actorov a všetky instance transformácie. V sledovaných vlastnostiach sa zmenili iba tri odkazy na mesh; materiály, transformácie, viditeľnosť a kolízne nastavenia zostali rovnaké. Rozsah porovnania je uvedený v [natívnom review](../output/unreal/deck-gap-study/native-review.json).

Prvý importný pokus skončil pred zmenou mapy na nesprávne zvolenom LOD getteri. Jeho dva nepoužité assety ostali v pôvodnom pokusnom namespace. Úspešný import používa nový namespace s príponou `_02`; chybný pokus sa nepovažuje za prijatý.

## Zabalená aplikácia a hranice výsledku

Natívne readbacky nepokrývajú UV1 priamo v render bufferi ani topológiu Nanite klastrov. Nové vizuálne zábery overujú viditeľnú opravu pri bazéne; vstupnú terasu DOM_01713 táto kamera nepokrýva.

Samostatný tmavý klin na vzdialenej bočnej terase sa týmto neprehlasuje za opravený. Zníženie `r.Nanite.MaxPixelsPerEdge` z 1 na 0,125 jeho odstránenie nepreukázalo; medzi zábermi sa navyše kamera posunula približne o 1,08 m, takže nejde o presné A/B. Globálne nastavenie Nanite sa preto nemenilo.

Aktuálnu väzbu vytvára [exportér revízie](../scripts/unreal/caustics/export_scene_revision.py). [Generátor identity](../scripts/unreal/caustics/scene_revision.py) odlišuje aktuálnu scénu a walking provenance od historického pôvodu nezmenenej geometrie bazéna. Povinne overuje aj aktuálny hidden-collision manifest a jeho väzbu na rovnakých 57 colliderov, 684 trojuholníkov a 58 natívnych assetov. Jeho C++ header vzniká pred buildom; nový dvojfázový dôkaz transportu svetla sa pripája až po skutočných meraniach. Cook vyžaduje aj tri nové deck balíky v reálnom IoStore obsahu.

Aktuálny Editor build (PID 44865) a Game build (PID 60402) skončili s exit 0 a ukončenými vlastnenými procesmi. Prijaté buildy a zdrojová identita sú uvedené v [aktuálnom pracovnom kontexte](../output/unreal/deck-gap-study/package-context.json). Dve nové transportné fázy (0 a 0,125 s; PID 56149 a 57996) prešli nezmeneným nezávislým validátorom aj spoločným porovnaním. Každá potvrdzuje 45 receiverov a hladinu, spolu 1 076 receiver trojuholníkov. Nasledoval úspešný cook (70923), archive (71649) a finalizácia balíka (72780), všetky exit 0. Nemenné build/package receipty zachovávajú dobový stav pred runtime kontrolami; novšie výsledky pripája delivery review.

Prvý balík `37404fcc…` bol odmietnutý pre starú revíziu v pomocnom manifeste chôdze. Geometria colliderov sa nemenila; oprava spojila aktuálne scene/OBJ hashe s overenými pôvodnými assetmi a vytvorila nový izolovaný projekt aj balík. Staré neúspešné dôkazy zostali zachované.

[Kontrola státia](../output/unreal/deck-gap-study/walking-pool-sp67-5f1adeab-7f7e-4c61-acdb-1f319fa06f4b/result.json), PID 73721 / exit 0, potvrdzuje aktuálnu source/world identitu, úspešný vstup cez floor/capsule queries a 541 uzemnených vzoriek bez chyby výšky očí. Počas 300 meraných snímok bolo okno aktívne v popredí. Ide o vstup a státie; traversal, schody, zatvorené dvere, sliding a pohyb klávesnicou sa týmto behom neprehlasujú za overené.

| Profil, rovnaký pohľad bazéna | Výstup | Priemerný interval | Pozorované FPS |
| --- | --- | ---: | ---: |
| 67 % / TSR história 100 % | 3840 × 2160 | 38,43 ms | 26,0 |
| 50 % / TSR história 100 % | 3840 × 2160 | 27,67 ms | 36,1 |

Ide o samostatné krátke merania 240 snímok po 240 zahrievacích snímkach, vždy 240/240 v popredí. [Záber 67 %](../output/unreal/deck-gap-study/visual-pool-sp67-1952d7ff-9041-43c3-8d8e-925386d1bb41/capture.png) aj [záber 50 %](../output/unreal/deck-gap-study/visual-pool-sp50-f7160518-614e-4b7a-b22a-c91b5a45be91/capture.png) uzatvárajú pôvodnú širokú medzeru. Malý vzdialený klin a krátke tmavé zakončenia škár ostávajú viditeľné. Jitter, expozícia a fáza vody sa môžu líšiť; nejde o presné pixelové A/B, potvrdenie rovnakej ostrosti v pohybe ani prijatie cieľa 45–60 FPS. Interné raster/history textúry tieto behy priamo nemerajú. Numerický transportný dôkaz používa diagnostické 100/200; pri škálovaných profiloch sa numerická energia znova neoverovala.

Historické režimy `inactive/zero/constant` používajú pôvodný diagnostický kontrakt a na novej walking provenance sa odmietnu; aktuálna revízia aktualizuje kontrakty `transport-opaque` a `continuous`. Pôvodné diagnostické dôkazy sa tým neprepisujú.

Pôvodný balík s overeným [ovládaním a ukladaním profilov](unreal-quality-profiles.md) zostáva zachovaný. Nová aplikácia bola následne otvorená s dočasným profilom Plynulosť 50/100; natívne AX a snímka potvrdili zvolený profil a dostupné voľby v Ovládaní. Celkový fotorealizmus a cieľová plynulosť zostávajú otvorené.
