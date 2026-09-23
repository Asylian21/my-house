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

Kuchyňa 22. 9. 2026, revízia po vizuálnom pripomienkovaní: dubová nadstavba široká **3 210 mm** vo výške **2 258–2 700 mm** končí zarovno s varnou nikou pred dverami. Predchádzajúce premostenie nad dverami a vysoké ľavé zakončenie boli na požiadavku stavebníka odstránené. Pri okne zostáva nízka bočná linka a nad ňou súvislá svetlá stena. Digestor má viditeľnú 80 mm kazetu, filtre a grafitové čelo; spodná hrana je 1 520 mm a recirkulácia pokračuje cez nadstavbu k výustke vo výške 2 700 mm. Rovnaký model sa používa vo webe aj v Unreale. [Aktuálny detail kuchyne](kitchen-island.md).

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

**Priečka garáž / spálňa a šatník, 16. 9. 2026:** označený vnútorný úsek je bežná murovaná **SP14, 140 mm**, X 11 003–11 143 mm a Y 5 744–8 749 mm. Líce pri izbách zostáva; garáž získava 161 mm a po zarovnaní zuba pri regáli má 25,151355 m². Regál je skrátený na 1 839 × 500 mm, kosačka posunutá o 161 mm k stene s medzerou 20 mm. Vonkajšie pokračovanie pri lodžii, zateplenie a os B/R6 zostávajú. [Rozsah revízie a dokumentácia](construction-garage-partition.md).

**HS portál GARDEN-02 / D5**, označený stavebníkom na obrázku ako „Terasové presklenie 2500“, má od 15. 9. 2026 šírku **2 200 mm** pri zachovaní výšky **2 400 mm** a parapetu **0 mm**. Ide o otvor zo spálne **1.10** do dvora. Os **X 13 090 mm** zostáva; ostenia sú **X 11 990–14 190 mm**, po 150 mm muriva navyše na oboch stranách. Rám, posuvné krídlo, otvor v murive a izolácii, fasádny obklad, pôdorys a výkresy používajú tieto rozmery. [Revízia a rozsah dokumentácie](construction-openings.md). Samostatný portál obývačky WING-WEST-01 zostáva 2 250 × 2 400 mm.

Veľké čelné okno pracovne **FRONT-07** je podľa zadania z 13. 9. 2026 posunuté o **150 mm doprava (na východ), od stola ku skrini**. Otvor je X **24 442–26 442 mm**; rozmery **2 000 × 1 600 mm**, parapet 900 mm a pevné zasklenie s rámom 35 mm zostávajú. Bočné okno EAST-01 nemení polohu. Spoločnú polohu pre pôdorys aj Babylon určuje `ACTIVE_WINDOW_POSITIONS` v `lib/twin-active-house.ts`.

Dodatočná pravá priečka pri kuchynskej linke a dverách technickej miestnosti bola 13. 9. 2026 na výslovnú žiadosť stavebníka zrušená kvôli vzhľadu interiéru. Pravý koniec linky zostáva otvorený. Následnými zadaniami stavebníka z 13.–14. 9. 2026 sa dvere do technickej miestnosti posúvajú o **200 mm doprava (na východ)**, teda pôvodných 150 mm a ďalších 50 mm, otvor je X **26 081–26 881 mm** pri zachovaní šírky 800 mm a krídla 700 mm. Zadná linka sa na pravom konci predlžuje o **200 mm** na X **26 001 mm** vrátane spodných a horných skriniek, pracovnej dosky, obkladu a osvetlenia. Medzera korpusu pred otvorom zostáva 80 mm; táto stavebná úprava nemení obrys ostrovčeka. Následné rozmiestnenie drezu, varenia a rúry je nahradené aktuálnym návrhom v detaile kuchyne. Ľavá priečka pri chodbe zostáva. Pravú priečku znovu nepridávať bez nového zadania.

**AK-01 a AK-02, revízia 16. 9. 2026:** stena spálňa / chlapčenská izba a stena kúpeľňa / dievčenská izba používajú **SM30: jednu vrstvu klasickej obvodovej keramickej tehly 300 mm**, bez vaty, dutiny a akustickej predsteny. **Dôvod odhlučnenia zostáva.** Líca X 14 943–15 243 mm, dĺžka oboch úsekov 3 048 mm a chodba 1 099 mm sa nemenia; bežné omietky a kúpeľňové povrchy sú navyše. [Aktuálna skladba a poznámky](acoustic-walls.md).

Predchádzajúca SA30 100 + 100 + 100 mm, päťvrstvový detail s omietkami a výpočet približne 58 dB sú [archívnou štúdiou](sa30-acoustic-wall-study.md). Na SM30 sa neprenášajú. Konkrétny výrobok obvodovej tehly, jeho hmotnosť a nepriezvučnosť zatiaľ nie sú určené. Rola `PARTITION` zostáva do statického posúdenia; 300 mm tehla sama nepotvrdzuje nosnú funkciu.

Kandidátna podporná trasa **R7** zostáva pod vlastnou hmotnosťou oboch stien. Starý prepočet dvoch 100 mm plášťov neplatí; nový prepočet čaká na výber výrobku. [Geometria, podklady a hranice návrhu R7](construction-foundation-axon.md).

**Aktívne riešenie AK-03 (pracovňa / kúpeľňa so sprchou) je H200, revízia 16. 9. 2026:** na žiadosť stavebníka zostáva iba jedna Silentboard 12,5 mm. Od kúpeľne: 15 mm VC omietka + 100 mm LeierPLAN 10 N+F, Devecser + 15 mm VC omietka + 45 mm dutina W623 na pružných Direktschwingabhänger s vatou 40 mm + 12,5 mm Silentboard. Základ má **187,5 mm**, H200 zostáva identifikátorom. Hydroizolácia, lepidlo, obklad a finálna stierka sú navyše.

Požiadavka je **Rw ≥ 51 dB**, nový predbežný model dáva **Rw ≈ 55,77 dB ≈ 56 dB**, o 2,15 dB menej než starší odhad s dvoma doskami. Nejde o meranie presnej zostavy ani hotového domu. [Aktuálny výpočet a predpoklady](office-acoustic-wall-scientific-rationale.md). Systém jednej dosky, stabilitu muriva, kotvy a napojenia treba technicky potvrdiť.

**Zarovnanie podľa výslovnej voľby stavebníka:** kúpeľňové líce H200 aj líce priečky do chodby je **Y 6 552 mm**. Líce pracovne je **Y 6 364,5 mm**; na tejto strane ostáva rozdiel hrúbok 47,5 mm voči 140 mm priečke. Dvere pracovne zostávajú Y 5 421–6 322 mm, rezerva k stene je **42,5 mm**. Dvere kúpeľne zostávajú Y 6 701,5–7 501,5 mm a na osi Y 7 101,5 mm; rezerva je **149,5 mm**. Obložku pracovne treba zosúladiť s 42,5 mm. Sprcha a okná zostávajú na mieste; tabuľa a radiátor sledujú nové líca. Pracovňa má 12,1352895 m², kúpeľňa 7,214871 m². [Skladba a D1](office-acoustic-wall-thinner-options.md).

Predchádzajúca **SA25-AKU 274 mm** (12 mm omietka + 250 mm Leiertherm 25/30 AKU Mátraderecske + 12 mm omietka) je uchovaná iba ako [historická záloha](office-acoustic-wall-study.md). Jej pracovňové líce Y 6 328 mm, posun vstupu 100 mm a výrobcom doložených Rw 56 dB patria tejto zálohe; nepoužívajú sa pre aktuálne H200.

Ostatné varianty sa nemažú. Sú dostupné cez `/archiv`; snímky `/v1` a `/v2` zostávajú zachované. Dispozičné štúdie a staršie kombinácie A/B sú historické pracovné alternatívy, nie hlavný návrh.

Hlavné cesty `/koncept-2d`, `/podorys`, `/3d`, `/navrh-3d` a `/docs/manual` sú pevne nastavené na C/B/B. Staré alebo neplatné parametre sa upravia na hlavný návrh, pričom pohľad na parcelu a manuál zostávajú zachované. Hlavná navigácia vždy vedie na C/B/B aj pri prezeraní archívu. Prepínače alternatív sú dostupné iba v `/archiv/podorys`; archívna zostava si zachová výber v manuáli a v `/archiv/3d`.

Sekcie: `/` prehľad projektu, `/docs` dokumentácia, `/3d` dom v 3D, `/podorys` samostatný interiérový plán. Pôvodné adresy zostávajú funkčné.

Rozhranie `/docs` bolo 14. 9. 2026 nahradené [knižnicou súborov](document-library.md), napojenou na celú novú výkresovú sadu vrátane R7. Aktuálnosť exportu a jeho stavebná schválenosť sú odlišné údaje; otvorené statické a konštrukčné body zostávajú uvedené pri dokumentoch.

Hranica parcely 6012/26 sa odvodzuje z nezmeneného katastrálneho polygónu S-JTSK. Aktívny pôdorys aj 3D používajú spoločný `twin-active-site.ts`. Pôvodný lokálny rámec C3 a historické osadenie zostávajú v `twin-site.ts`.

Používateľ potvrdil platnosť C3 a následne požiadal **uličný aj pravý (východný) kolmý odstup presne 3 000 mm**. Revízia `CLIENT-PLACEMENT-20260913` v `twin-house-placement.ts` posúva celý dom o 77,913405454 mm doprava oproti pôvodnému osadeniu; Y sa nemení. Rozmery, dispozícia a vnútorné súradnice domu zostávajú zachované. Pevné prvky pozemku sa zobrazujú v posunutom rámci domu; prístupy a plot sa napájajú na tento rámec. Stav je `CLIENT_REQUESTED_SETBACK`, nie geodetické zameranie stavby. Ostatné odstupy sa naďalej odvodzujú kolmo ku katastrálnym hranám.

## Odborné zdôvodnenie H200

Detail pri zárubniach sa riadi [D1 — napojenie H200](office-acoustic-wall-junction.md) na `/docs/akustika-h200/napojenie`: pevné spoločné ostenie, systémové podtesnenie a dve nadväzujúce škáry J1/J2. Polohy dverí zostávajú; obálka H200 má po revízii 187,5 mm a spoločné kúpeľňové/chodbové líce; 5 mm spoje sú dokumentované vo zväčšenom detaile.

[Odborná technická správa — princíp, metodika, výpočet a literatúra](office-acoustic-wall-scientific-rationale.md) je súčasne dostupná v aplikácii na `/docs/akustika-h200`, z prehľadu dokumentácie a priamo z detailu AK-03. Obsahuje nový prepočet jednej Silentboard na približne 56 dB, porovnanie s predchádzajúcou R2 a hranice modelového výsledku. Spoločný obsah je v `lib/h200-research.json`; Markdown sa obnovuje cez `node scripts/plan-documentation/generate-h200-research.mjs`.
