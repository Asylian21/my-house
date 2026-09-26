# Aktuálny model domu v Unreal

Revízia 22. septembra 2026 prenáša hlavný návrh C/B/B zo spoločnej Babylon scény. Export teraz odovzdáva `ACTIVE_DESIGN` výslovne; historické predvolené hodnoty rendererov A/A sa nemenia.

Model zahŕňa kuchynský ostrovček 2 640 × 920 mm s drezom a umývačkou vo východnom module, varnú dosku v zadnej nike, rúru vo vysokej skrini, dubové čelá a čierne dosky. Súčasťou rovnakého exportu sú aktuálne vnútorné steny, zariadenie, HS portál GARDEN-02 široký 2 200 mm a pevné okno pracovne FRONT-07. Osadenie zostáva C/B/B s požadovanými odstupmi 3 000 mm.

Nový profil `model-refresh` vytvára samostatný projekt a balík. Staré experimentálne materiálové recepty obsahujú ID a hashe staršej geometrie; nový import ich nepriraďuje novým objektom. Vytvára materiály zo súčasných farieb, drsnosti, metalickosti, priehľadnosti a lokálnych albedo textúr. Historické balíky, upravený engine a ich dôkazy zostávajú zachované. Tento profil nezahŕňa historický experimentálny provider kaustík bazéna ani jeho fotografické materiálové recepty.

Nadväzujúcu revíziu z 23.–24. 9. 2026, izolovanú migráciu R2b, Shipping balík a aktuálne výkonové merania opisuje [Plynulosť BreziTwin](unreal-performance.md). Nižšie uvedené dátované overenia naďalej opisujú pôvodný model-refresh balík.

## Obnovenie modelu

Pri novej revízii nastavte nový adresár `BREZI_MODEL_OUTPUT`; import zámerne vyžaduje prázdny projekt a neprepisuje starú scénu.

```sh
export BREZI_MODEL_OUTPUT=output/unreal/model-refresh-20260922
node scripts/unreal/model-refresh.mjs prepare
node scripts/unreal/model-refresh.mjs export
node scripts/unreal/model-refresh.mjs editor-build
node scripts/unreal/model-refresh.mjs import
node scripts/unreal/model-refresh.mjs game-build
node scripts/unreal/model-refresh.mjs package
node scripts/unreal/model-refresh-qa.mjs interior
node scripts/unreal/model-refresh.mjs open interior
```

Pred balením sa overujú hashe importovanej scény, uložených assetov, kolízií, materiálov a generátorov. Balenie uchováva vlastný report a overuje obsah aplikácie aj podpis. Pôvodné kontinuálne caustics kontroly sa nemenia.

Príkaz `materials` dokáže aktualizovať iba materiálové grafy už overeného modelu. Pred úpravou kontroluje vlastníctvo, starý report a všetky súbory; po úprave overuje, že žiadny mesh, textúra ani kolízny asset nezmenil obsah. Kuchynský dub používa otočenie 90° zo zdrojového modelu. Fotovoltika a procedurálna dlažba majú uvedenú reprezentatívnu farbu zdroja; kresba článkov a jednotlivých dlaždíc zatiaľ nie je rekonštruovaná.

Na tomto Macu vnorený Xcode krok v UBT zlyhával napriek úspešnej kompilácii a linkovaniu. `game-build` preto vykoná overený exportovaný graf natívnych príkazov a iba jeho Xcode finalizáciu spustí samostatne s čistým pracovným adresárom. Report obsahuje výsledok každej fázy a hashe finálnych produktov vrátane spustiteľného súboru v `.app`. Platný nezmenený build sa pri opakovaní použije znova.

Kamerový pohľad **Kuchyňa** používa voľný vstupný bod odvodený z aktuálnej sedačky B, rovnako ako Babylon. Starý pohľad sa po premiestnení sedačky nachádzal nad jej sedákom. Nový pohľad mieri na zadnú kuchynskú linku.

## Pôvodné overenie modelu a nadväzujúca prechádzka

- **M / Chôdza:** po úspešnej kontrole podlahy a voľného priestoru okamžite funguje WASD.
- **Esc:** vráti kurzor a zastaví pohyb kamery.
- **F2:** prepne zachytenie myši; uvoľnenie pravého tlačidla už nezruší tento režim.
- Koliesko približuje plynulo; nastavenie obmedzenia pohybu zachová okamžitý prechod.

Toto je rozsah pôvodného balíka `model-refresh-20260922`, ktorý zachovával statické dvere. Nadväzujúcu implementáciu klasického herného ovládania, interaktívnych dverí a overenia všetkých miestností opisuje [Unreal prechádzka](unreal-walkthrough.md). Predvolenú postavu, zoom, panel miestností, svetlá a podrobnejšie materiály opisuje [Archviz Game](unreal-archviz-game.md). Overená geometria neznamená overený výkon ani finálny fotorealizmus.

Výstupy aktuálnej revízie sú v `output/unreal/model-refresh-20260922`: `model-refresh-report.json` overuje rozmery zdrojového modelu, `model-refresh-import-report.json` skutočný natívny import a opätovné načítanie. Natívne snímky, balík a ich výsledky sa evidujú samostatne.

## Overenie 22. 9. 2026

- Natívny import: 1 990 objektov a rovnaký počet väzieb materiálov; maximálna odchýlka uložených bounds 0,0098 mm. Uloženie, nové načítanie a kolízne kontroly prešli.
- Game build, Metal cook, obsah samostatnej aplikácie a podpis prešli. Prvé nekuchané editorové zobrazenie ukázalo sivé náhradné materiály; výsledná samostatná aplikácia ich v kontrolovaných pohľadoch nemá.
- Štyri samostatné spustenia skončili s exit 0: kuchyňa, ulica, terasa a kuchyňa v režime chôdze. Každé má PNG, runtime report a väzbu na presný balík v `output/unreal/model-refresh-20260922/qa/`.
- Pri 1 920 × 1 080: kuchyňa 17,17 ms priemer / 17,60 ms P95, ulica 14,00 / 14,38 ms, terasa 15,96 / 16,44 ms. Spätná kontrola runtime reportov potvrdila 100 % renderovanie a 200 % TSR históriu: diagnostický režim ignoroval pomenovaný parameter Výkon. Meranie zahŕňa 240 ustálených snímok po 240 zahrievacích; nejde o benchmark pohybu celým domom ani natívneho 4K.
- Vstup do chôdze prešiel testom podlahy a kapsuly. Automatizovaná interakcia cez macOS accessibility dvakrát skončila timeoutom, preto ručný WASD pohyb a vizuálna plynulosť zoomu zatiaľ nie sú natívne potvrdené. Politika zachytenia vstupu a časovo nezávislý zoom prešli C++ testami.

`model-visual-review.json` zaznamenáva rozsah vizuálnej kontroly a zostávajúce obmedzenia tohto balíka. `output/unreal/model-refresh-current.json` vyberá aktuálne skontrolovaný balík pre `npm run unreal:open`. Výslovný výber historického balíka cez pôvodné premenné prostredia zostáva dostupný.
