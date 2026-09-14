# Hlavný návrh C / B / B — záväzné východisko projektu

Potvrdené stavebníkom 13. 9. 2026: hlavný variant je **C · Výklenok, technická miestnosť B, obývacia zóna B**.

Používateľ následne výslovne určil, že **všetky hlavné a predvolené cesty vedú na C/B/B a ostatné varianty sú dostupné len cez archív**. Tento zápis spresňuje staršie poznámky, v ktorých sa A/B voľby ešte prepínali priamo na hlavných stránkach. Hlavný variant sa mení až novým výslovným zadaním používateľa, nie otvorením inej zostavy na porovnanie.

| Pozícia v C / B / B | Význam | Parameter v URL |
| --- | --- | --- |
| C | Dispozícia C · Výklenok | `variant=c` |
| prvé B | Technická miestnosť B | `heating=b` |
| druhé B | Obývacia zóna B | `living=b` |

Používateľské označenie je **HLAVNÝ NÁVRH C / B / B**. V URL sú hodnoty malé písmená; identifikátory obývačky a technickej miestnosti v modeli sú `B`.

Referenčný pôdorys: <http://localhost:5173/koncept-2d?variant=c&heating=b&living=b>.

Konštrukčné zadanie doplnené 14. 9. 2026: povala bude slúžiť iba na odkladanie vecí, mimo otvorenej katedrály obývačky 1.03. Nosné stropy budú drevené, bez betónovej stropnej dosky a betónovej nadbetonávky. Monolitické základy a prízemná doska zostávajú predmetom predchádzajúceho zadania. Používateľ žiada aspoň jeden schod pri vstupe; výšku hotovej podlahy má určiť nový návrh podľa zameraných základov a terénu. Uličný referenčný bod R0 je oznámených 184,200 m, nejde automaticky o hotovú podlahu. Podrobnosti a stav návrhu sú vo [výkresovej dokumentácii](construction-drawings.md); tieto požiadavky sa nesmú zameniť s už overenými realizačnými prierezmi a výškami.

Následné spresnenie základov: podľa stavebníka je doska vyliata **aj s lodžiou a krytou terasou**. Priestorový pohľad preto zahŕňa celý L-obrys vrátane oboch plôch; hranica uzavretého interiéru ho nesmie skrátiť. Zobrazenie má ulicu dole, garáž vľavo a dlhé krídlo vpravo. Oznámený rozsah nenahrádza zameranie skutočných líc, hrúbky alebo výstuže. Nové vnútorné trasy R4–R6 a ich stav opisuje [priestorový podklad základov](construction-foundation-axon.md).

Spresnenie kuchyne 14. 9. 2026: [samostatný ostrovček](kitchen-island.md) s hotovou doskou 2 640 × 920 mm končí pravou hranou presne na úrovni pracovnej dosky linky oproti. Pravá linka pri stene zostáva v pôvodnej plnej dĺžke až po zadnú hranu ostrovčeka smerom k obývačke; medzi nimi je priechod 900 mm. Odstup 800 mm od sedačky B zostáva. Nadväzujúci architektonický návrh presúva drez s umývačkou na ostrovček a indukciu s integrovaným odsávačom do niky pri stene. Rúra so zasúvacími dvierkami je vo vysokej skrini vedľa chladničky; ostrovček má uzavreté plytké úložisko zo strany obývačky. Najnovšie spresnenie presúva umývačku do krajného východného modulu ostrovčeka smerom k malému oknu, s jednou zásuvkovou skrinkou medzi umývačkou a drezom. Čierne pracovné dosky a dubové čelá všetkých skriniek vracajú pôvodný materiálový charakter. Materiály a svetlo opisuje rovnaký detail kuchyne.

Všetky ďalšie úpravy a opravy vychádzajú z C/B/B. Výber musí prechádzať z pôdorysu do 3D aj dokumentácie. Predvolené hodnoty historických geometrických generátorov sa nemenia; hlavné vstupné stránky používajú `ACTIVE_DESIGN`.

## Hlavné vstupy a archív

| Cesta | Záväzné správanie |
| --- | --- |
| `/` | Prehľad hlavného návrhu; hlavné odkazy vedú na C/B/B. |
| `/docs` | Knižnica novej dokumentácie C/B/B: zložky, vyhľadávanie, náhľady a sťahovanie výkresov a správ; zachováva stav koordinácie a archívu. |
| `/podorys`, `/koncept-2d` | Pôdorys C/B/B bez prepínačov alternatív. `site=1` zobrazí parcelu, `view=manual` manuál. |
| `/3d`, `/navrh-3d` | 3D hlavného návrhu C/B/B. |
| `/docs/manual` | Manuál a tlač hlavného návrhu C/B/B. |
| `/docs/model` | Technické podklady a model s výberom C/B/B. |
| `/archiv` | Vstup k alternatívam, dispozičným štúdiám a historickým snímkam. |
| `/archiv/podorys` | Alternatívne zostavy C s prepínačmi A/B; `mode=study` sprístupní zachované dispozičné štúdie. |
| `/archiv/podorys?...&view=manual` | Manuál konkrétnej archívnej zostavy; zachová jej `heating` a `living`. |
| `/archiv/3d` | 3D konkrétnej archívnej zostavy C; zachová jej `heating` a `living`. |
| `/v1`, `/v2`, `/archiv/model` | Zachované historické vstupy, dostupné z archívu. |
| `/koncept-2d-2` | Starý odkaz na experiment E presmeruje do `/archiv/podorys?variant=e&mode=study`. |

Hlavná navigácia **vždy vracia C/B/B**, aj keď je práve otvorená archívna zostava C/A/B. Iba odkazy na ďalšie zobrazenia danej archívnej zostavy zachovávajú C/A/B. Na mobile sú archívny manuál a 3D dostupné v menu „Zobrazenia archívnej zostavy“.

Príklady, ktoré sa pri ďalšej práci nesmú zameniť:

- `/podorys?variant=c&heating=a&living=b` je starý hlavný odkaz: presmeruje na C/B/B.
- `/archiv/podorys?variant=c&heating=a&living=b` je zámerne zvolená archívna zostava C/A/B: zostane C/A/B.
- Hlavný odkaz „3D dom“ z archívu otvorí `/3d?variant=c&heating=b&living=b`. Odkaz „3D archívnej zostavy“ otvorí `/archiv/3d?variant=c&heating=a&living=b`.

## Implementačné oporné body

- [lib/twin-design-selection.ts](../lib/twin-design-selection.ts): `ACTIVE_DESIGN` je B/B, `PREVIEW_DESIGN` je jeho alias. `designHref(path)` aj `designHref(path, design)` vytvárajú hlavný odkaz C/B/B. Alternatívu prenáša iba `designHref(path, design, true)` do archívu.
- [app/active-design-route.ts](../app/active-design-route.ts): `requireActiveDesign()` opravuje historické, neplatné alebo duplicitné variantové parametre hlavných stránok a odstraňuje `mode=study`; zachová ostatné parametre, napríklad `site=1` a `view=manual`.
- [app/project-nav.tsx](../app/project-nav.tsx): hlavné odkazy sa neodvodzujú od práve prezeranej archívnej zostavy.
- [app/koncept-2d/studio.tsx](../app/koncept-2d/studio.tsx) a [documentation-studio.tsx](../app/koncept-2d/documentation-studio.tsx): alternatívy a prepínače povolí iba explicitný režim `archive`; hlavný pohľad zostáva C/B/B.
- `ARCHIVE_DESIGN` a historické normalizátory či geometrické generátory môžu mať predvolenú zostavu A/A. To nemení hlavný návrh a nie je dôvod na návrat hlavných vstupov k A/A.

Po zmene navigácie overiť hlavné vstupy bez parametrov, starý hlavný odkaz s A, alternatívu otvorenú cez archív, jej prechod medzi plánom/manuálom/3D a návrat hlavnou navigáciou na C/B/B. Existujúce kontroly sú v [tests/twin-design-preview.test.ts](../tests/twin-design-preview.test.ts) a [tests/rendered-html.test.mjs](../tests/rendered-html.test.mjs). Stav predchádzajúcich overení je v [zázname navigácie](project-navigation-verification.md); lokálne overenie nie je potvrdením publikovania.

## Zachované geometrické rozhodnutia

Veľké čelné okno pracovne **FRONT-07** je podľa zadania z 13. 9. 2026 posunuté o **150 mm doprava (na východ), od stola ku skrini**. Otvor je X **24 442–26 442 mm**; rozmery **2 000 × 1 600 mm**, parapet 900 mm a pevné zasklenie s rámom 35 mm zostávajú. Bočné okno EAST-01 nemení polohu. Spoločnú polohu pre pôdorys aj Babylon určuje `ACTIVE_WINDOW_POSITIONS` v `lib/twin-active-house.ts`.

Dodatočná pravá priečka pri kuchynskej linke a dverách technickej miestnosti bola 13. 9. 2026 na výslovnú žiadosť stavebníka zrušená kvôli vzhľadu interiéru. Pravý koniec linky zostáva otvorený. Následnými zadaniami stavebníka z 13.–14. 9. 2026 sa dvere do technickej miestnosti posúvajú o **200 mm doprava (na východ)**, teda pôvodných 150 mm a ďalších 50 mm, otvor je X **26 081–26 881 mm** pri zachovaní šírky 800 mm a krídla 700 mm. Zadná linka sa na pravom konci predlžuje o **200 mm** na X **26 001 mm** vrátane spodných a horných skriniek, pracovnej dosky, obkladu a osvetlenia. Medzera korpusu pred otvorom zostáva 80 mm; táto stavebná úprava nemení obrys ostrovčeka. Následné rozmiestnenie drezu, varenia a rúry je nahradené aktuálnym návrhom v detaile kuchyne. Ľavá priečka pri chodbe zostáva. Pravú priečku znovu nepridávať bez nového zadania.

Akustické steny AK-01 (spálňa / chlapčenská izba) a AK-02 (kúpeľňa / dievčenská izba) majú podľa zadania z 13. 9. 2026 skladbu **SA30: LeierPLAN 10 P10 100 mm + minerálna vata 100 mm + LeierPLAN 10 P10 100 mm**. Hrúbka 300 mm bez omietok a obkladov, poloha líc aj priechod chodby zostávajú. Ide o návrh nenosnej priečky s potrebou statického posúdenia pôvodne nosných úsekov. Pozri [skladbu a poznámky SA30](acoustic-walls.md).

Ich nenosná rola nevylučuje vlastnú hmotnosť zo zaťaženia dosky. Doplnenie z 14. 9. 2026 vyčísľuje oba plášte pri modelovej výške 3125 mm a pridáva **kandidátnu podpornú trasu R7**, nie schválený prierez alebo zásah do už vyliatej dosky. SA30 sa nemení na podperu dreveného stropu alebo krovu. [Geometria, hmotnosť a hranice návrhu R7](construction-foundation-axon.md).

**Finálne zvolené riešenie stavebníka pre AK-03 (pracovňa / kúpeľňa so sprchou) je H200:** od kúpeľne 15 mm VC omietka + 100 mm LeierPLAN 10 N+F, Devecser + 15 mm VC omietka + 45 mm dutina W623 na pružných závesoch Knauf Direktschwingabhänger s 40 mm minerálnou vlnou + 2 × 12,5 mm Silentboard na strane pracovne, spolu **200 mm**. Dutina zahŕňa profil CD 60/27 aj izoláciu. Hydroizolácia, lepidlo, obklad a prípadná finálna stierka sú dodatočné povrchy. Zvolená skladba je záväzná pre hlavný pôdorys, 3D, detail a manuál.

Požiadavka H200 je **Rw ≥ 51 dB**, predbežný výpočet dáva **Rw približne 58 dB**. Ide o výpočtový údaj, nie o meranie presnej zostavy alebo hodnotu R’w dokončenej stavby. Výber skladby je uzavretý; realizačná príprava zahŕňa technické potvrdenie systému na konkrétnom dutinovom murive, stability 100 mm jadra, kotiev, napojení a prestupov. Zachovať obe 15 mm omietky aj presné pružné závesy. Pozri [finálne H200, zdroje a výpočet](office-acoustic-wall-thinner-options.md).

Geometria H200: kúpeľňové líce **Y 6 602 mm**, pracovňové líce **Y 6 402 mm**. Otvor kúpeľne 800 mm aj krídlo 700 mm sú presne na osi X hlavnej chodby, **Y 7 101,5 mm**; otvor Y 6 701,5–7 501,5 mm. Dvere pracovne aj jej vstupný roh sú oproti pôvodnému stavu posunuté o **30 mm k ulici**, čo oproti zálohe s posunom 100 mm znamená návrat o 70 mm. Pracovňový otvor je Y 5 421–6 322 mm a pri stene zostáva 80 mm; na kúpeľňovej strane 99,5 mm. Ide o dostupné modelové úseky pre koordináciu zárubní. Sprcha a aktívne okná zostávajú zachované.

Predchádzajúca **SA25-AKU 274 mm** (12 mm omietka + 250 mm Leiertherm 25/30 AKU Mátraderecske + 12 mm omietka) je uchovaná iba ako [historická záloha](office-acoustic-wall-study.md). Jej pracovňové líce Y 6 328 mm, posun vstupu 100 mm a výrobcom doložených Rw 56 dB patria tejto zálohe; nepoužívajú sa pre aktuálne H200.

Ostatné varianty sa nemažú. Sú dostupné cez `/archiv`; snímky `/v1` a `/v2` zostávajú zachované. Dispozičné štúdie a staršie kombinácie A/B sú historické pracovné alternatívy, nie hlavný návrh.

Hlavné cesty `/koncept-2d`, `/podorys`, `/3d`, `/navrh-3d` a `/docs/manual` sú pevne nastavené na C/B/B. Staré alebo neplatné parametre sa upravia na hlavný návrh, pričom pohľad na parcelu a manuál zostávajú zachované. Hlavná navigácia vždy vedie na C/B/B aj pri prezeraní archívu. Prepínače alternatív sú dostupné iba v `/archiv/podorys`; archívna zostava si zachová výber v manuáli a v `/archiv/3d`.

Sekcie: `/` prehľad projektu, `/docs` dokumentácia, `/3d` dom v 3D, `/podorys` samostatný interiérový plán. Pôvodné adresy zostávajú funkčné.

Rozhranie `/docs` bolo 14. 9. 2026 nahradené [knižnicou súborov](document-library.md), napojenou na celú novú výkresovú sadu vrátane R7. Aktuálnosť exportu a jeho stavebná schválenosť sú odlišné údaje; otvorené statické a konštrukčné body zostávajú uvedené pri dokumentoch.

Hranica parcely 6012/26 sa odvodzuje z nezmeneného katastrálneho polygónu S-JTSK. Aktívny pôdorys aj 3D používajú spoločný `twin-active-site.ts`. Pôvodný lokálny rámec C3 a historické osadenie zostávajú v `twin-site.ts`.

Používateľ potvrdil platnosť C3 a následne požiadal **uličný aj pravý (východný) kolmý odstup presne 3 000 mm**. Revízia `CLIENT-PLACEMENT-20260913` v `twin-house-placement.ts` posúva celý dom o 77,913405454 mm doprava oproti pôvodnému osadeniu; Y sa nemení. Rozmery, dispozícia a vnútorné súradnice domu zostávajú zachované. Pevné prvky pozemku sa zobrazujú v posunutom rámci domu; prístupy a plot sa napájajú na tento rámec. Stav je `CLIENT_REQUESTED_SETBACK`, nie geodetické zameranie stavby. Ostatné odstupy sa naďalej odvodzujú kolmo ku katastrálnym hranám.

## Odborné zdôvodnenie H200

Detail pri zárubniach sa riadi [D1 — napojenie H200](office-acoustic-wall-junction.md) na `/docs/akustika-h200/napojenie`: pevné spoločné ostenie, systémové podtesnenie a dve nadväzujúce škáry J1/J2. Polohy dverí a obálka H200 zostávajú; 5 mm spoje sú dokumentované vo zväčšenom detaile.

[Odborná technická správa — princíp, metodika, výpočet a literatúra](office-acoustic-wall-scientific-rationale.md) je súčasne dostupná v aplikácii na `/docs/akustika-h200`, z prehľadu dokumentácie a priamo z detailu AK-03. Obsahuje dôvody ponechania oboch Silentboard dosiek spolu a rozlíšenie výsledkov [výskumu NRC](https://nrc-publications.canada.ca/eng/view/object/?id=768bf32f-8313-435f-ab85-8680efba61b2) od predbežného výpočtu H200. Spoločný obsah je v `lib/h200-research.json`; Markdown sa obnovuje cez `node scripts/plan-documentation/generate-h200-research.mjs`.
