# Vlnenie bazéna — 9. september 2026

Táto iterácia prijíma dvanásť slabších analytických vĺn ako lokálne zlepšenie vzhľadu hladiny po zamietnutí jednoduchého preladenia pôvodných štyroch. Pravidelné rady oválnych odrazov výrazne ustúpili, odraz domu zostáva čitateľný. Prijatý lem bazéna zostáva zachovaný a renderer používa pôvodné nastavenie presnosti normál. Celkový fotorealizmus a plynulý natívny 4K výkon zostávajú otvorené.

Predchádzajúci test `r.GBufferFormat=3` nepriniesol presvedčivú opravu dominantného pravidelného rastra odrazov; predvolený stav `1` bol obnovený a overený v natívnej aplikácii. Táto iterácia preto mení smery, dĺžky a fázy samotných vĺn v `scripts/unreal/optics.py`.

## Prvý štvorvlnový kandidát — zamietnutý

| Režim | Smer v UE XY | Dĺžka | Amplitúda | Fáza v cykloch |
| --- | ---: | ---: | ---: | ---: |
| 1 | 17,3° | 39,7 cm | 0,661667 mm | 0,071 |
| 2 | 61,7° | 17,3 cm | 0,318684 mm | 0,389 |
| 3 | 132,4° | 11,9 cm | 0,194727 mm | 0,823 |
| 4 | 273,8° | 7,6 cm | 0,108571 mm | 0,547 |

Každá amplitúda je prepočítaná pravidlom `A_nová = A_pôvodná × λ_nová / λ_pôvodná`. Zachováva sa tak amplitúda sklonu každého režimu a analytický RMS sklon pri nezávislých rovnomerných fázach: **0,014661265872**, približne 0,840° po arctan. Nie je to tvrdenie o presne rovnakom okamžitom poli normál nad konečným bazénom. Smery menia anizotropiu; normalizácia pridáva malé nelineárne rozdiely. Všetky štyri vlny zostávajú súvislé sínusoidy a kandidát môže pravidelný vzor iba preskupiť. Nejde o nameraný vietor ani hydrodynamickú simuláciu okrajov bazéna.

Počet štyroch kosínusových vetiev sa nemení. Zachovávajú sa centimetrové svetové súradnice, normálové vlnenie bez geometrického displacementu, zdrojová hladina −12 mm, pôdorys 6,0 × 2,7 m, IOR 1,333, roughness, absorpcia, rozptyl, svetlo a expozícia. Z toho sa nedá vyvodiť rovnaký nameraný výkon.

## Natívne overenie

Nový `OpticsWriter.validate_water_normal()` prechádza graf spätne od `MP_NORMAL`. Číta skutočné priestorové koeficienty v cykloch/cm, záporné frekvencie, fázy, vektory sklonu, periódu kosínusov a spojenia. Vyžaduje spoločný čas a absolútnu svetovú pozíciu, svetovú bázu a predvolené výstupné kanály. Interné názvy uzlov nepoužíva. CPU testy pokrývajú pôvodné aj nové parametre, float32, premenovanie uzlov a 16 neplatných hodnôt alebo väzieb.

Úplný import prešiel s exit 0. Samostatné porovnanie potvrdilo rovnaké zdrojové GLB/manifesty, optickú geometriu, 23 priradených mesh objektov, parametre inštancií aj pôvodné polia grafov; v optickom správaní sa mení iba tabuľka vĺn. Optické assety a ich metadata sa regenerujú, preto ich bajtová identita s predchádzajúcim importom nie je očakávaná.

Ďalší samostatný proces Unrealu načítal uložený materiál z disku bez zápisu scény. Potvrdil celý nový 50-uzlový graf normály a zhodu 31 finálnych optických a priradených mesh assetov pred aj po čítaní. Dôkazy sú v `output/unreal/water-wave-study/import-01-comparison.json` a `saved-water-readback-04.json`.

Zdroj prvého kandidáta: SHA `719434ca013efc3cd5f72ace38d06a5965584bd9e3016e3094bbc54768b59b48`. Pôvodný zdroj aj import/package reporty sú zachované v `output/unreal/water-wave-study/before/`.

Jeho BuildCookRun prešiel za 78,44 s. Natívny proces PID 36250 skončil s exit 0, po 1200 zahrievacích a 300 meraných snímkach s plným fokusom a natívnou 4K scénou aj RHI textúrou. Priemer bol 66,984 ms (14,93 fps), P95 77,438 ms. Pôvodný súborový log potvrdil `r.GBufferFormat=1`. V zábere `water-gbuffer-pool-day-f414c4b1-847b-4f65-b339-8fc6d004e94e/capture.png` zostali dominantné pravidelné rady oválnych odrazov. Root aj nezávislý reviewer ho zamietli ako opravu tohto vzoru. Jednotlivé snímky mali rozdielnu fázu vĺn; nejde o presné časovo synchronizované A/B.

## Dvanásťvlnový kandidát

Smery pokrývajú celý kruh pomocou deterministickej golden-angle postupnosti, fázy používajú samostatnú iracionálnu postupnosť a dĺžky dvanásť logaritmických pásiem s malými odchýlkami. Ide o autorské voľby. Úplné presné parametre a výpočty sú v `output/unreal/water-wave-study/twelve-mode-candidate/candidate.json` a `README.md`.

Dĺžky sú 7,688–38,614 cm a frekvencie 2,011–4,506 Hz podľa pôvodného gravitačného vzťahu. Rovnaká energia sklonu je rozdelená medzi dvanásť slabších režimov: RMS zostáva 0,014661265872, analytická RMS výška je 0,508759 mm. Pomer vlastných hodnôt kovariancie sklonu je 1,13187. Zachovanie tejto štatistiky nepreukazuje rovnaké maximum sklonu alebo okamžitý výsledok normalizácie.

Reader teraz akceptuje iba štyri alebo dvanásť vetiev. Šesť CPU testových skupín pokrýva obe schémy, float32 a poškodenie poslednej dvanástej vetvy; nepovolený počet päť odmieta. Úplný import 02 prešiel a samostatný proces následne potvrdil z disku všetkých 138 uzlov normály (159 uzlov celého materiálu), skutočné konštanty a spojenia aj nezmenené finálne optické assety počas čítania. Ostatné optické koeficienty, geometria a priradenia sa zhodujú s baseline. BuildCookRun prešiel za 70,03 s.

Zdroj kandidáta: SHA `a0556f658fda7eb89cb306d966f41fe9c35b85262c69b3e07fda376fb20d0d59`. Dôkazy: `import-02-comparison.json`, `saved-water-readback-12.json`, `package-02-report.json`. Vyšší počet kosínusov môže zvýšiť náklady shaderu; samotný počet vetiev nehovorí o celkovom nameranom výkone.

## Prijatý lokálny výsledok a jeho hranice

Root aj nezávislý vizuálny reviewer prijali dvanásťvlnový výsledok ako zlepšenie statického vzhľadu. Rovnomerné rady oválnych ostrovčekov už nedominujú; obrysy majú rôznorodejšie rozostupy a prepojené tvary. Pásy a jednotlivé ovály stále zostávajú. Porovnávali sa pôvodné 3840 × 2160 PNG s rozdielnou fázou vĺn, zobrazené nástrojom v 2048 × 1152; nejde o synchronizované pixelové A/B ani o prijatie úplného fotorealizmu. Nezávislý záznam: `output/unreal/water-wave-study/native-visual-review.json`.

Natívny proces PID 39812 skončil s exit 0. Po 1200 zahrievacích a 300 meraných snímkach s plným fokusom a priebežne overenou natívnou 4K scénou aj RHI textúrou nameral priemer **68,006 ms (14,70 fps)**, P95 79,222 ms. Renderer zostal pri 100 % scéne, TSR history 200 %, Lumen HW a vypnutom dynamickom rozlíšení; pôvodný súborový log potvrdil `r.GBufferFormat=1`. Jednotlivé behy nepreukazujú kauzálny výkonový rozdiel medzi tabuľkami vĺn. Dôkaz a záber: `output/unreal/runtime/water-gbuffer-pool-day-a5129d5a-68f7-4c36-a6e7-3b7af05b856c/`.

Následný proces PID 40673 skončil s exit 0 a automaticky overil 64 po sebe idúcich párovaných natívnych 4K PNG, kanonický prechod terasy k bazénu pri pevnom simulačnom kroku 30 Hz, účinné AA/expozíciu/jitter, obnovenie hodín a nezmenený balík. Root vizuálne prezrel snímky 000, 032, 052 a 063 bez chýbajúceho vodného materiálu alebo zjavného nového rozpadu v týchto fázach. Záznam nie je meraním reálneho FPS, úplným vizuálnym posúdením všetkých 64 snímok ani plynule prehratou kontrolou animácie. Dôkaz: `output/unreal/runtime/motion-tsr-0629be62-bf65-4441-9874-59f50f7849eb/motion-qa.json`.

Po oboch natívnych behoch nezávislá kontrola potvrdila všetkých 2475 odkazov na vstupné hashe / 2462 rôznych súborov, presné digesty receptov a všetkých 37 súborov balíka. Aktuálny, archivovaný kandidátny a pohybovým testom uložený package receipt sú bajtovo zhodné: SHA `14f8021d9592dd1ac56890bea16ee9abf130813391de8754ce6543c0594ff5e7`. Dôkaz: `output/unreal/water-wave-study/post-motion-revalidation.json`; súhrn prijatého stavu: `progress.json`.

Historické transportné podklady diagnostického caustics pluginu obsahujú pôvodnú tabuľku vĺn a zostávajú zachované. Následná [iterácia väzby kaustík na vodu](unreal-caustics-water-binding.md) už doplnila samostatný aktuálny binding všetkých 12 vĺn a overila dva nové Metal transportné záznamy. Plugin zostáva opt-in bez produkčného svetelného konzumenta. Samotný optický materiál stále negeneruje dynamické kaustiky. Oheň sa v tejto iterácii nemení.
