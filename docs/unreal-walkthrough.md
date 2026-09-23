# Natívna prechádzka domom C/B/B

Táto základná revízia používa aktuálny dom, interiér, okná a kuchyňu z [obnovy modelu](unreal-model-refresh.md). Jej balík `output/unreal/walk-game-20260922` a pôvodné výsledky nižšie zostávajú zachované. Nadväzujúci [Archviz Game](unreal-archviz-game.md) pridáva predvolenú animovanú postavu, kameru so zoomom, viditeľný panel miestností, vnútorné svetlá a podrobnejšie materiály.

## Ovládanie

Bežné spustenie začína v obývačke v režime chôdze. Myš otáča pohľad bez držania tlačidla. WASD alebo šípky pohybujú postavou, Shift zrýchli chôdzu a Q umožní pomalý presný pohyb. Kláves E otvorí alebo zatvorí zamerané dvere. Výzva sa zobrazuje pri zameriavacom bode.

Spustenie cez `npm run unreal:open` vyberá aktuálne overený balík, obraz 1 920 × 1 080 a profil Plynulosť. Kvalitu možno zmeniť v pauze. Citlivosť myši má rozsah 0,25–3×; otáčanie nezávisí od snímkovej frekvencie. Počas načítania skoré Pokračovať počká na pripravenú chôdzu; skoré Esc alebo strata fokusu zachová pauzu.

Esc zastaví pohyb a otvorí pauzu s voľným kurzorom. Tlačidlo Pokračovať obnoví chôdzu a zachytenie myši. Strata fokusu aplikácie takisto zastaví pohyb. Pauza obsahuje pohľady na dom, citlivosť myši, obrazové nastavenia a obmedzenie pohybu. Koliesko slúži na približovanie v prehľadovom pohľade.

## Dvere a kolízie

Export ukladá skutočné transformácie mechaník Babylon: otočné krídla, HS portály, sekcie garážovej brány, spotrebiče a poklop bazénovej šachty. `doors.json` spája ich diely so zdrojovou identitou a zatvoreným geometrickým stavom. Natívny import kontroluje všetky väzby aj po uložení a novom načítaní mapy.

Pri pohybe krídla sa premiestňuje viditeľná geometria aj jej kolízia. Zatvorené dvere blokujú kapsulu; otvorené uvoľnia existujúci stavebný otvor. Animácia kontroluje kontakt s postavou. Nemení sa dispozícia domu ani nepridáva neexistujúce vnútorné spojenie do garáže: tá má vstup z terasy a cez garážovú bránu.

Chôdza používa natívnu kapsulu, podlahové dotazy a zdrojové kolízne meshe. Opätovný vstup do chôdze kontroluje uložený zatvorený stav platne dverí, takže bežné otvorenie dverí nezneplatní pôvod modelu.

## Overovanie

Zdrojová trasa pokrýva 13 miestností, 3 terasy, 3 vonkajšie prístupy a 16 architektonických dverí. Plánovanie podľa zdrojových bounds je len príprava testu. Dôkaz priechodnosti musí vytvoriť samostatná natívna aplikácia súvislým pohybom kapsuly cez celú trasu, ovládaním W/E, meraním opory pod nohami a zatvorených/otvorených dverí.

Reporty presne rozlišujú vykonaný natívny test od syntetického plánovania. Vstup odoslaný do Unreal PlayerInput je test hernej vstupnej cesty; nie je dôkaz fyzickej macOS klávesnice. Režim automatického testu na pozadí nemení systémový fokus ani nezachytáva myš. Bežná aplikácia naďalej pri strate fokusu zastaví pohyb a vyžaduje Pokračovať.

## Výsledok 22. 9. 2026

Samostatná natívna aplikácia dokončila 134 krokov a súvislú trasu 202,49 m z jediného vstupného bodu. Navštívila všetkých 13 miestností, tri terasy a tri vonkajšie prístupy. Všetkých 16 architektonických dverí prešlo cyklom E otvoriť → E zatvoriť → E znovu otvoriť → fyzicky prejsť. Test navyše pri zatvorenom krídle držal W a overil blokovanie kapsuly. Kontroly opory pod nohami, priebežnej polohy, výšky očí a neprenikania do geometrie prešli.

Dôkaz je v `output/unreal/walk-game-20260922/qa/walkthrough-ef826f0a-31e3-4cf0-881c-d4f43a6d0a5a/qa.json`. Report overuje pôvod modelu a aplikácie pred aj po spustení, skutočné stavy dverí, fyzické vzorky pohybu a 19 uložených PNG. Všetky snímky boli vizuálne skontrolované bez zisteného chýbajúceho meshu alebo náhradných šachovnicových materiálov v zábere. Niektoré mieria na blízku stenu alebo zariadenie, preto nepotvrdzujú kompletnú výtvarnú kvalitu každej miestnosti.

Import obsahuje 19 interaktívnych mechaník a 84 pohyblivých dielov. Práčka, sušička a poklop šachty majú overený import a väzby; uvedená súvislá trasa skúša 16 architektonických dverí. Základná sada Unreal má 522 úspešných Node testov a 14 + 33 + 69 Python testov; oprava štartu navyše prešla 318 kontrolami v debug aj optimalizovanom C++ builde.

Samostatný záber kuchyne v režime chôdze prešiel pri 1 920 × 1 080: priemer 11,25 ms (približne 89 FPS), P95 15,28 ms. Ide o 240 ustálených snímok po 240 zahrievacích, nie o benchmark pohybu celým domom. Runtime potvrdil 50 % interné renderovanie a 100 % TSR históriu profilu Plynulosť. Záber potvrdzuje aktuálny ostrovček s drezom, zadnú varnú dosku, vysokú rúru, čelá linky a okno. Dôkaz: `qa/interior-walk-fb7506a7-b0e7-4f6e-9b57-c87c3f5dafed/` v rovnakom výstupnom adresári.

Pauza bola samostatne vizuálne overená v `qa/interior-ui-pause-0f55fcad-2ef6-45be-ba9e-3366b4d01acf/`. Bežné spustenie bez diagnostiky následne vstúpilo do chôdze z overeného bodu obývačky. Pripojenie cez macOS CUA skončilo timeoutom a identifikátor aplikácie je spoločný s historickými balíkmi; systémový vstup klávesnice/myši preto nie je potvrdený týmto automatickým overením.

`model-visual-review.json` v tomto výstupnom adresári spája presný balík, snímky, testy a rozsah pôvodného overenia. Aktuálny výber pre spustenie určuje `output/unreal/model-refresh-current.json`; novšia revízia má vlastný report a nezamieňa svoje výsledky s meraniami tohto základného balíka.

Opakovanie natívneho testu:

```sh
node scripts/unreal/walkthrough-qa.mjs --close-reopen --screenshots
BREZI_MODEL_OUTPUT=output/unreal/walk-game-20260922 node scripts/unreal/model-refresh-qa.mjs interior --walk
```
