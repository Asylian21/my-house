# Výkon Unreal verzie DOM

Stav k 3. 10. 2026: finálny Shipping r3 je nainštalovaný ako `/Applications/Dom.app` a natívne overený. Plný profil má overených päť statických pohľadov a orbit; r3 prešiel fokusovaným r38, chôdzou vo dne/noci a bežným menu pri 1920 × 1080 aj 960 × 540.

## Zachovaný návrh a prostredie

Merané na Apple M5 Pro s 48 GiB zdieľanej pamäte, macOS 27.0, Unreal Engine 5.8.2, Metal SM6. Výstupné zábery majú 1920 × 1080 pixelov. FPS sú nezastropované intervaly medzi hernými tickmi v aktívnej natívnej aplikácii; nemerajú fyzické zobrazovanie snímok na displeji.

Zostáva **C/B/B**, uličný aj pravý kolmý odstup **3 000 mm**. Prijatá mapa má SHA-256 `2a5a6573c092bd4185ef583d35a44deaa0b5ecd00cb560d872444de4ed2e87ca`. Zostavenie vzniklo v samostatnej kópii prijatej scény; mapa, authored Content a Config sa nezmenili. Zmenili sa iba vstup aplikácie, politika kvality a jej UI. [Finálny balík r3](../output/unreal/dom-app-20261003-performance-r3/dom-package.json), [nezávislá kontrola zdrojov a testov](../output/unreal/performance-20261003-r1/independent-source-and-test-review.json).

## Plný model a Fotoreal

Predvolený **Plný model** zachováva celú scénu, geometriu, materiály, hustotu vegetácie 1, doplnkové dvojité sklo a lokálne svetlá. V meraných pohľadoch zostalo rovnakých 963 spravovaných skupín s 609 473 inštanciami. Odstránilo sa vynucovanie tieňov, ray tracingu a distance-field osvetlenia na každom drobnom vegetačnom detaile; obnovujú sa jeho pôvodné autorské príznaky.

Profil používa TSR 67 %, limit 900 interných riadkov, nezmenšený výstup a históriu 100 %. Kvalita GI/tieňov/odrazov/vegetácie/postprocesu/efektov je 2/3/2/3/2/2. Lumen má Final Gather 1, odrazy 0,75, scene lighting/detail 1 a dosah 150 m; odrazy sa počítajú s downsample 2. Hardvérový Lumen zostáva preferovaný na podporovanom RHI. [Presný kontrakt](../output/unreal/performance-20261003-r1/final-full-render-recipe.json).

**Fotoreal** zostáva voliteľný pre vyššiu kvalitu obrazu. Plný profil má viac jemného šumu a mäkšie malé hrany či odlesky. Doplnkové sklo zostáva, ale jeho Lumen front-layer gate sa pri kvalite odrazov 2 vypína; identická kvalita odrazov s Fotoreal sa netvrdí. Automatická expozícia a fáza vody/oblakov nie sú medzi zábermi uzamknuté. Pri prvom pokuse sa objavili hrubé zuby v tieni pod strechou a parapetom pri bazéne; kvalita tieňov 3 ich podstatne odstránila. [Pôvodné porovnanie](../output/unreal/performance-20261003-r1/full-realtime-static-visual-review.json), [kontrola opravy tieňov](../output/unreal/performance-20261003-r1/full-shadow3-visual-review.json).

## Natívne statické merania

| Pohľad | Pôvodný Fotoreal FPS | Pôvodný p99 ms | Nový Plný model FPS | Nový p99 ms |
| --- | ---: | ---: | ---: | ---: |
| Okolie r38 | 36,72 | 33,35 | 70,54 | 19,86 |
| Ulica | 27,72 | 43,09 | 42,65 | 29,79 |
| Kuchyňa deň | 19,44 | 59,59 | 50,61 | 26,07 |
| Kuchyňa noc | 20,59 | 57,40 | 50,68 | 26,14 |
| Bazén deň | 28,13 | 43,86 | 59,06 | 21,43 |

Nový profil má v každom uvedenom behu 600/600 vzoriek s aktívnou aplikáciou, oknom aj fokusom scény. Vo všetkých piatich statických behoch spolu bolo 0/3 000 intervalov nad 33,33 ms. p99 hodnotí pomalší koniec distribúcie, nie iba priemer. **60 FPS vo všetkých pohľadoch nie je dokázaných**; ulica a kuchyňa zostávajú približne 43–51 FPS.

R38 je priamo z finálneho r3. Ostatné štyri pohľady boli merané v r1; všetkých 63 buildových pinov autorských zdrojov sa medzi r1, r2 a r3 zhoduje okrem rozloženia UI v `BreziPlayerController.cpp`. Renderer, diagnostika, startup aj pohyb zostali rovnaké. [Porovnanie zdrojov a finálny r38](../output/unreal/performance-20261003-r1/r3-independent-review.json).

Pôvodná ulica a kuchyňa majú 300 plne fokusovaných vzoriek; nový profil 600 po dlhšom warmupe. R38 používa nový 600-snímkový referenčný beh so zatvoreným menu. Staré r38 malo otvorené menu a nulový fokus scény; jeho FPS slúži iba na diagnostiku a z porovnania sa vylučuje. Bazén používa samostatné fokusované opakovanie na oboch stranách. Pôvodný aj prvý kandidátsky bazén bez aktívnej aplikácie boli odmietnuté pre výkonové tvrdenia. Ide o jednotlivé behy a rovnaké kamery, nie o test každého miesta ani dlhodobé thermal meranie.

Dôkazy:

- [Staré r38 — iba diagnostika, menu otvorené](../output/unreal/performance-20261003-r1/baseline-1791015409723-9b98bc15-d4a5-41be-a4ab-2ac86168dc74/summary.json).
- [Férové r38 — 600 vzoriek, zatvorené menu](../output/unreal/performance-20261003-r1/cinematic-r38-focused-reference-1791039047798-52c08cd5-3a1b-4ce1-bd24-6ad980300942/summary.json).
- [Pôvodná ulica a kuchyňa](../output/unreal/performance-20261003-r1/cinematic-matrix-1791015818941-f9cadb24-2f21-416e-acdb-11b4a873e971/summary.json).
- [Fokusovaný pôvodný bazén](../output/unreal/performance-20261003-r1/cinematic-pool-reference-1791016690852-14f10826-b126-4e5e-bbd3-da65f3ba68ce/summary.json).
- [Finálny r3 r38 — fokusované opakovanie](../output/unreal/dom-app-20261003-performance-r3/native-performance-qa/candidate-full-r38-focused-1791039402905-be296966-b18c-45ee-8238-171a661e064b/summary.json).
- [R1 ulica a kuchyňa](../output/unreal/dom-app-20261003-performance-r1/native-performance-qa/candidate-full-static-1791017269374-7b25e92f-300d-47e0-bef4-09deaa174d64/summary.json); pôvodný nefokusovaný bazén v tomto súhrne sa nepoužíva.
- [Fokusované opakovanie nového bazéna](../output/unreal/dom-app-20261003-performance-r1/native-performance-qa/candidate-full-pool-focused-1791017861621-a7959b3f-2d05-4935-9c14-7ceeb8dfad2d/summary.json).

Päť originálnych záberov skutočne zostaveného Shipping balíka bolo nezávisle porovnaných s pôvodnou verziou. Kamery, denný/nočný režim, identita scény, výstupné pixely aj počty spravovaných vegetačných inštancií sa zhodujú; nový runtime zároveň potvrdzuje celý kontrakt profilu. [Finálna statická vizuálna kontrola](../output/unreal/performance-20261003-r1/candidate-full-static-independent-review.json).

Samostatný 20-sekundový orbit ulice meral 880 fokusovaných snímok v bežnom čase: **44,00 FPS, p99 29,95 ms, maximum 33,78 ms**. Jeden interval prekročil 33,33 ms, žiadny 50 ms. Kamera sa pohybovala v 877 vzorkách, čas enginu nebol zrýchlený ani spomalený. Tento beh overuje výkon pri pohybe kamery, nie všetky ručné gestá alebo chôdzu. [Natívny orbit](../output/unreal/dom-app-20261003-performance-r1/native-performance-qa/candidate-full-orbit-clean-focus-1791018238411-19aae210-6959-4e66-a294-78b4a152dd44/summary.json).

Natívna chôdza cez zdrojovo overenú uličku kuchyne/obývacej zóny trvala 45 s vo dne aj v noci, približne 39 m a štyri obojsmerné kolá v každom behu. Reálny CharacterMovement používal kolízie, bez teleportov či zmeny času počas merania; world contract nemal chyby. [Chôdza deň/noc](../output/unreal/dom-app-20261003-performance-r1/native-performance-qa/candidate-full-walk-1791018514188-db018bba-f0d6-4d94-91ba-25c6cdb56cf3/summary.json).

| Chôdza | FPS | p99 ms | Maximum ms | Intervaly nad 50 ms |
| --- | ---: | ---: | ---: | ---: |
| Deň, 2 112 fokusovaných vzoriek | 46,93 | 33,25 | 37,57 | 0 |
| Noc, 2 111 fokusovaných vzoriek | 46,90 | 33,81 | 184,95 | 1 |

V nočnej chôdzi r1 zostal jeden výraznejší zásek. Dve čisté 45-sekundové opakovania r2 mali **46,75 / 46,62 FPS**, p99 **33,53 / 33,84 ms**, maximum **47,22 / 41,47 ms** a žiadny interval nad 50 ms; všetkých 2 104 / 2 098 vzoriek malo plný fokus. Zásek sa nezopakoval, jeho príčina však nie je dokázaná. [Prvé čisté opakovanie](../output/unreal/dom-app-20261003-performance-r2/native-performance-qa/candidate-full-walk-1791037242900-6826bf1f-b047-483c-9663-dad9946dc2bb/summary.json), [druhé opakovanie](../output/unreal/dom-app-20261003-performance-r2/native-performance-qa/candidate-full-night-walk-repeat-1791037493525-7a6b9755-9872-4d79-a75d-41c0bcb34de7/summary.json), [analýza záseku r1](../output/unreal/performance-20261003-r1/night-walk-hitch-analysis.json).

Finálny r3 zopakoval tú istú 45-sekundovú trasu cez kuchyňu/obývaciu zónu. Oba behy mali štyri obojsmerné kolá, približne 39 m, reálne kolízie, nezmenený čas, žiadne teleporty ani chyby world contractu. [Finálna chôdza r3](../output/unreal/dom-app-20261003-performance-r3/native-performance-qa/candidate-full-walk-1791039470544-4360254b-6dc7-4ef9-b037-47f7a74dfd03/summary.json).

| Finálna chôdza r3 | FPS | p99 ms | Maximum ms | Intervaly nad 50 ms |
| --- | ---: | ---: | ---: | ---: |
| Deň, 2 096 fokusovaných vzoriek | 46,57 | 33,28 | 39,95 | 0 |
| Noc, 2 100 fokusovaných vzoriek | 46,66 | 33,66 | 40,89 | 0 |

Nulové sekanie v celom projekte ani úplný prejazd každou miestnosťou sa týmto testom netvrdí. R3 potvrdil bežné menu pri **1920 × 1080 aj 960 × 540**: predvolený Plný model, Fotoreal → Plný model a noc → deň. Karty v štandardnom okne tvoria dva stĺpce. V malom okne bolo všetkých päť kariet čitateľných a dosiahnuteľných cez forward Tab, fungoval návrat na začiatok posúvania aj Prelet a Pokračovať. Prelet sa presunul do scrollovateľnej časti, aby zostalo viac miesta pre obsah. Reverse Shift+Tab sa pre nespoľahlivé odovzdanie modifikátora cez CUA netvrdí. [Bežné štandardné UI](../output/unreal/dom-app-20261003-performance-r3/native-performance-qa/candidate-menu-standard-1791039671368-a2a98ae7-9e8b-4e7c-a249-716187bca848/manual-ui-observations.json), [bežné kompaktné UI](../output/unreal/dom-app-20261003-performance-r3/native-performance-qa/candidate-menu-compact-1791039756721-42c4ad4c-7968-4ba3-905c-5aee07f029ff/manual-ui-observations.json), [nezávislá kontrola zdrojov a originálnych PNG](../output/unreal/performance-20261003-r1/r3-independent-review.json).

## Nainštalovaná aplikácia

Samostatný r38 beh skutočného `/Applications/Dom.app` nameral **70,3496 FPS, p99 20,029 ms, maximum 22,644 ms**, so všetkými 600 vzorkami fokusovanými. Podpis prešiel deep/strict kontrolou; payload a executable sa zhodovali s r3 pred aj po meraní. Runtime potvrdil nezmenenú mapu a celý Full kontrakt. [Fokusované meranie po inštalácii](../output/unreal/dom-app-20261003-performance-r3/native-performance-qa/installed-full-r38-1791040430513-76cf8a96-171e-4412-b419-600e0bb17c92/summary.json), [natívny installed review](../output/unreal/dom-app-20261003-performance-r3/native-performance-qa/installed-native-review.json).

Priame spustenie nainštalovaného executable **bez argumentov a bez fresh UserDir** otvorilo predvolené okolie r38, malo vybraný Plný model a funkčné dvojstĺpcové menu aj Pokračovať; natívne zatvorenie skončilo exit 0. Prvý pokus cez LaunchServices/CUA sa nepodarilo naviazať na UI a zostáva vylúčený. Úspešný priamy beh nie je dôkazom Finder doubleclick testu. [Pozorovania skutočného noargs behu](../output/unreal/dom-app-20261003-performance-r3/native-performance-qa/installed-default-smoke/observations.json).

Po dokončení všetkých troch čistení sa samostatné meranie nainštalovanej aplikácie zopakovalo: **74,2574 FPS, p99 23,3177 ms, maximum 28,9876 ms**, opäť 600/600 vzoriek s aktívnou aplikáciou, oknom aj fokusom scény. Presný Full kontrakt, mapa, 35 súborov payloadu, podpis aj aktuálne selektory sa pred a po teste zhodovali. Je to samostatné opakovanie: priemer FPS bol vyšší, p99 pomalší než v predchádzajúcom installed behu. Z tejto variability sa nevyvodzuje, že čistenie disku zvýšilo FPS. [Meranie po čistení](../output/unreal/dom-app-20261003-performance-r3/post-clean-native-qa/post-clean-full-r38-1791047831793-58875935-00c4-4944-9813-40085a9a3ef2/summary.json).

Skutočný `npm run unreal:open` v čistom prostredí následne skončil exit 0 a cez LaunchServices spustil `/Applications/Dom.app` s predvoleným Full/r38, bez explicitných viewer argumentov a bez fresh UserDir. CUA sa na jeho GUI nepodarilo spoľahlivo naviazať ani pri nezávislom pokuse; nové vizuálne overenie menu, natívne Close ani Finder doubleclick po čistení sa preto netvrdia. Predchádzajúce ručne overené menu a noargs UI toho istého payloadu zostávajú samostatným doplnkovým dôkazom. Všetkých 35 payload hashov, podpis, mapa a selektory zostali presné aj po pokuse s openerom; procesy boli ukončené. [Konsolidovaný post-clean native review](../output/unreal/dom-app-20261003-performance-r3/post-clean-native-qa/post-clean-native-review.json).

## Dokončené čistenie

Zostal jeden aktívny finálny Unreal projekt [Shipping r3](../output/unreal/dom-app-20261003-performance-r3/Project/BreziTwin) a nainštalovaný `/Applications/Dom.app`. Odstránili sa inventarizované staré pracovné kópie projektov, nadbytočné build/cache výstupy, presne určené staré aplikácie v koši a nepotrebné diagnostické PNG. Aktuálny Content, Config, Source, buildové vstupy, Shipping aj Editor binárne súbory sa zachovali. Autorské podklady, licencované fotografie, zdrojová geometria, archívne webové návrhy a snímky `versions/v1` a `versions/v2` zostali zachované.

| Dokončený priechod | Odstránené súbory | Logická veľkosť, GB | Pozorovaný prírastok voľného miesta, GB |
| --- | ---: | ---: | ---: |
| [Historické projekty a generované výstupy](../output/unreal/performance-20261003-r1/storage-audit/cleanup-execute-final-r3-r1.json) | 67 039 | 121,093 | 88,623 |
| [Presné QA PNG duplikáty a historické snímky](../output/unreal/performance-20261003-r1/storage-audit/qa-png-cleanup-execute-r3-r1.json) | 2 001 | 15,281 | 14,977 |
| [Nepoužívané historické repo PNG](../output/unreal/performance-20261003-r1/storage-audit/repository-png-cleanup-execute-r3-r1.json) | 777 | 5,044 | 5,044 |

Spolu sa odstránilo **69 817 súborov / 141 418 459 390 logických bajtov** bez zlyhaní. Súčet pozorovaných prírastkov voľného miesta jednotlivých priechodov je **108 644 638 720 bajtov**; celkový čistý prírastok za obdobie je **106 241 101 824 bajtov**, pretože medzi priechodmi prebiehala ďalšia práca. APFS klony zdieľajú bloky, takže logické veľkosti ani `du` nemožno sčítať ako fyzicky ušetrené miesto.

Posledný priechod overil nezmenených **9 448 ochranných pinov** a **3 371 susedných súborov**. Pri PNG čisteniach sa nemenili pôvodné reporty ani zostávajúce QA JSON/log/bin/utrace súbory. V preverovanej množine 997 repo diagnostických obrázkov zostalo 220 snímok potrebných pre aktuálne dôkazy, priame čítače, galérie alebo porovnania. V QA zostalo 169 pôvodných PNG vrátane celej potrebnej 64-snímkovej continuous-motion sekvencie; pôvodný 185 ms zásek, férové referencie, finálne zábery a prijatý pár r46a majú zachované dôkazy. Historické plné projekty a nepotrebné obrazy sa už nedajú opätovne prehrať z pôvodných ciest. Neskoršie odstránenie presných 777 diagnostických mirrorov je zaznamenané [samostatným retirement sidecarom](../output/unreal/performance-20261003-r1/storage-audit/repository-png-later-retirement-proof-r3-r1.json); staré receipts sa spätne neprepisovali.

Po čistení read-only Shipping preflight overil **39 akcií, 28 kompilácií a 226 vstupných pinov**. `nativeExecuted=false`: ide o kontrolu zachovaného rebuild grafu, nie o novú natívnu kompiláciu ani cook. [Preflight po všetkých priechodoch](../output/unreal/performance-20261003-r1/storage-audit/read-only-rebuild-preflight-after-all-cleanup-r3-r1.json).

Záverečné meranie pred natívnym smoke testom uviedlo približne **46,46 GB alokovaných referencií projektu**, **2,30 GB QA sandboxu** a **893,32 GB voľného miesta** na Data volume. Hodnoty `du` zahŕňajú zdieľané APFS bloky; nie sú ďalšou sumou fyzických úspor. [Záverečné du/df meranie](../output/unreal/performance-20261003-r1/storage-audit/whole-project-top-dirs-after-all-cleanup-r3-r1.json).

## Testy a hranice overenia

`npm run unreal:test`: **577/577 JavaScript + 163/163 Python = 740 testov**, bez zlyhaní. Politika profilu v rámci tejto sady overila 176 podmienok v debug aj optimalizovanom zostavení; tieto podmienky sa nepripočítavajú druhýkrát k počtu testov. Samostatne prešlo 30 testov meracieho harnessu a 11 testov vstupu aplikácie. Čistenie má **74 izolovaných safety testov: 27 hlavného helpera + 24 QA PNG + 23 repo PNG**, vrátane odmietnutia cudzích ciest, driftu hashov a zachovania rebuild vstupov. Tieto testy pracovali v dočasných fixtures. [Úplný log Unreal sady](../output/unreal/performance-20261003-r1/unreal-tests.log), [natívny startup fixture r3](../output/unreal/dom-app-20261003-performance-r3/startup-default-fixture/receipt.json), [hlavné safety testy](../scripts/unreal/test_cleanup_generated.py), [24 QA safety testov](../output/unreal/performance-20261003-r1/storage-audit/qa-png-executor-safety-tests-r2.json), [23 repo safety testov](../output/unreal/performance-20261003-r1/storage-audit/repository-png-executor-safety-tests-r2.json).

Web sa po odstránení regenerovateľných dist/Vite výstupov úspešne zostavil a prešlo **23/23 rendered HTML kontrol**, vrátane C/B/B trás, presných zachovaných snímok/assets v1/v2 a odkazov výkresov a manuálu. Ide o lokálne overenie; nasadenie neprebehlo. [Post-clean web validácia](../output/unreal/performance-20261003-r1/post-clean-web-validation.json).

Statické PNG nepotvrdzujú ghosting, shimmer ani fyzické zobrazovanie pri pohybe. Niektoré RHI GPU časovače r2 a nočnej chôdze r3 vrátili nemožný outlier 89 478,48 ms; tieto GPU distribúcie sú označené ako nespoľahlivé a nepoužívajú sa na závery o GPU náklade. Fokusované wall-clock intervaly zostávajú samostatným platným meraním. Chýbajúci voliteľný riadok o inicializácii enginu v Shipping logu nie je sám osebe zlyhanie runtime: natívny report zachytáva PID, Shipping build, Metal RHI, reálne nastavenia a podpis/hash konkrétneho balíka.
