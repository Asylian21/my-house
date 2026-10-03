# Dom pre macOS

Aplikácia sa inštaluje ako `/Applications/Dom.app`. Je to samostatný Shipping balík finálnej scény r46a, ktorú používateľ schválil 2. októbra 2026. Obsahuje vlastný runtime; na spustenie nepotrebuje otvorený Unreal Editor.

Zostáva C/B/B a uličný aj pravý kolmý odstup 3 000 mm. Príprava balíka klonuje schválený projekt; konfigurácia, geometria, mapa a materiály zostávajú byte-identické. V izolovanom klone sa zostaví natívny vstup a aktuálna politika vykresľovania s menu. Bežné spustenie používa finálny pohľad, profil **Plný model** a Retina rozlíšenie. Výslovné argumenty pre diagnostiku si zachovávajú svoje správanie.

Plný model ponecháva celú scénu a vegetáciu, dvojité sklo a miestne tiene. Znižuje výpočtovú kvalitu osvetlenia, odrazov a vnútorné rozlíšenie, čo prinieslo namerané zvýšenie FPS. Jemné hrany a odrazy môžu byť mäkšie; profil Fotoreal zostáva dostupný v menu. [Merania a hranice overenia](unreal-performance.md).

Ikona používa natívny render skutočného modelu domu C/B/B: sivé sedlové strechy, presklený štít a záhradnú stranu domu do L. Je uložená v `unreal/BreziTwin/Build/Mac/Resources/Dom.png` a `Dom.icns`. Zodpovedajúci `Assets.xcassets` používa aj budúce generovanie projektu Xcode. Pôvod renderu a nastavenie kamery zaznamenáva `Dom-icon-source.json`.

## Príprava a inštalácia

`npm run unreal:dom:package` používa `package-final-dom.mjs`. Pre opakované balenie urči nový nepoužitý `DOM_APP_OUTPUT`; predchádzajúci výstup sa neprepisuje. Potrebný je lokálny Unreal Engine 5.8. `npm run unreal:dom:install` overí úplný obsah a podpis balíka a presunie ho do `/Applications/Dom.app`. Výmena existujúcej aplikácie cez `--replace` vyžaduje `DOM_NATIVE_REVIEW`, ktorý schvaľuje presný hash nového balíka a mapy po natívnom vizuálnom a výkonovom overení. Predchádzajúca aplikácia zostáva do overenia inštalácie v izolovanom priečinku `installation-rollback`.

Jednorazovú výmenu pôvodnej ikony zaznamenáva `rebrand-dom-app.mjs` v samostatnom výstupe r2. Jej malý záznam zostáva zachovaný; staré generované aplikácie, rollback po úspešne overenej inštalácii a nepotrebné pracovné kópie boli odstránené pri čistení 3. októbra.

Po natívnom overení sa aktuálna inštalácia zapisuje do `output/unreal/dom-app-current.json`. `npm run unreal:open` potom overí a otvorí túto aplikáciu. Výslovné historické premenné `BREZI_MODEL_OUTPUT` alebo `BREZI_PACKAGE_REPORT` obchádzajú nový predvolený vstup.

## Vyhľadávanie v macOS

Spotlight má v zozname vynechaných umiestnení iba generované priečinky projektu `output/unreal` a `unreal/BreziTwin/Binaries`. Zdroje a potrebné vývojové balíky zostávajú zachované. Nainštalovaná `/Applications/Dom.app` zostáva indexovaná.

Staré registrácie `local.brezi.twin` boli cielene odregistrované. Registrácia aktuálnej aplikácie sa zachováva; databáza ostatných aplikácií sa neresetuje.

Šesť nepotrebných starých balíkov bolo pôvodne presunutých do Koša pod `~/.Trash/Dom-old-apps-20261003-r1`. Pri čistení 3. októbra bol odstránený iba tento presne určený projektový priečinok. Potrebné vývojové závislosti finálnej scény, testovacie vzorky, licencie a používané historické vizuálne podklady zostávajú v projekte. Registrácie starých balíkov a testovacích fixture aplikácií boli cielene odregistrované; fixture súbory zostali zachované.

Záznamy pôvodného balenia, natívneho vstupu a renderu domu sú v `output/unreal/dom-app-20261003-r1`; výmena ikony má záznam v `dom-app-20261003-r2`. Aktuálny výkonový balík a jeho zdrojový projekt sú v `output/unreal/dom-app-20261003-performance-r3`. Jeho Shipping zostavenie je čerstvo zostavené a natívne overené; zachované knižnice Editoru pochádzajú zo schváleného autorského projektu. Nové zostavenie Editoru nie je súčasťou výkonového dôkazu.

## Overenie po čistení

Celý aktuálny autorský projekt je v `output/unreal/dom-app-20261003-performance-r3/Project/BreziTwin`. Zachované zostávajú Source, Config, Content, Build, descriptor a potrebné natívne závislosti. Príprava nového izolovaného balíka prešla kontrolou presnej kópie; po všetkých odstráneniach prešiel read-only plán Shipping zostavenia s 39 akciami, 28 kompiláciami a 226 overenými vstupmi. Tento plán znovu nespúšťal natívnu kompiláciu. [Záznam vstupov na opätovné zostavenie](../output/unreal/performance-20261003-r1/storage-audit/read-only-rebuild-preflight-after-all-cleanup-r3-r1.json).

Nainštalovaný balík po čistení dosiahol v r38 **74,26 FPS**, p99 **23,32 ms**, maximum **28,99 ms**, pri 600 plne fokusovaných vzorkách a výstupe 1920 × 1080. Podpis, payload, mapa a aktuálny výber sa nezmenili. Bežný `npm run unreal:open` úspešne spustil aplikáciu cez LaunchServices s predvoleným Plným modelom a r38. Záverečné naviazanie CUA na okno zlyhalo, preto sa nový GUI/Finder ani natívny Close test netvrdí; skoršie vizuálne a ovládacie testy presne toho istého balíka sú zachované v dokumentácii výkonu.

[Výsledok čistenia a záverečné dôkazy](../output/unreal/performance-20261003-r1/storage-audit/cleanup-final-summary.json) · [Merania a pokrytie natívneho UI](unreal-performance.md).
