# Steny SM30 a H200 s požiadavkou odhlučnenia

Revízia stavebníka **16. 9. 2026**, hlavný návrh C/B/B: AK-01 a AK-02 sa menia na **samotnú klasickú obvodovú keramickú tehlu hrúbky 300 mm**. Označenie skladby je **SM30**. **Dôvod odhlučnenia medzi susednými miestnosťami zostáva.**

| Označenie | Umiestnenie | ID v modeli | Rozsah X | Rozsah Y |
|---|---|---|---|---|
| AK-01 | Spálňa 1.10 / chlapčenská izba 1.09 | C-OPEN-HALL-N | 14 943–15 243 mm | 7 651–10 699 mm |
| AK-02 | Kúpeľňa 1.11 / dievčenská izba 1.08 | C-OPEN-HALL-S | 14 943–15 243 mm | 3 504–6 552 mm |

Líca, dĺžka každého úseku **3 048 mm**, modelová výška **3 125 mm**, rozmery miestností a voľný otvor chodby **1 099 mm** zostávajú zachované.

| Konštrukčná vrstva | Materiál | Hrúbka |
|---|---|---|
| 1 | Klasická obvodová keramická tehla; rovnaký druh ako obvodové murivo domu | **300 mm** |

Stena nemá minerálnu vatu, vnútornú dutinu ani akustickú predstenu. Predchádzajúca požiadavka bežných omietok v miestnostiach zostáva; omietky, hydroizolácia, lepidlo a kúpeľňový obklad sú dodatočné povrchy mimo 300 mm modelovaného muriva. Starých 330 mm a päťvrstvový detail nie sú označením aktuálnej skladby.

Konkrétny výrobok 300 mm obvodovej tehly zatiaľ v projekte nie je určený. Preto **nepriezvučnosť ani hmotnosť novej steny nie sú doložené**. Pôvodný predbežný výpočet približne 58 dB pre dvojplášťovú SA30 sa na jednovrstvovú SM30 nevzťahuje. Splnenie požiadavky odhlučnenia treba posúdiť podľa vybraného výrobku, povrchov, napojení, prestupov a vedľajších ciest zvuku.

Modelová rola ostáva **PARTITION**. Zámena materiálu sama neurčuje, že stena nesie strechu alebo drevený strop; nosnú sústavu, stabilitu a podopretie posúdi statik. Kandidátna trasa **R7** zostáva pre prenos vlastnej hmotnosti; staré hmotnosti dvoch 100 mm plášťov sú vyradené z aktuálnych výpočtov. [Geometria R7 a stav zaťaženia](construction-foundation-axon.md).

Pri AK-02 sa kotvenie závesného WC a rozvody navrhnú pre konkrétnu 300 mm tehlu. Drážky a prestupy treba koordinovať so stabilitou muriva a odhlučnením; nepreberať detail kotvenia pre starý 100 mm plášť.

Spoločným zdrojom je `lib/acoustic-walls.ts`. Pôdorys, 3D, detail, manuál, legenda, miestnostné poznámky a výkresová dokumentácia používajú jednu 300 mm murovanú vrstvu. Pôvodná skladba a jej výpočet zostávajú iba v [archívnej štúdii SA30](sa30-acoustic-wall-study.md).

## AK-03 · H200 s jednou doskou, revízia 16. 9. 2026

Na žiadosť stavebníka zostáva jedna Silentboard 12,5 mm. Od kúpeľne: 15 mm VC omietka + 100 mm LeierPLAN 10 N+F + 15 mm VC omietka + 45 mm dutina W623 s pružnými Direktschwingabhänger a vatou 40 mm + 12,5 mm Silentboard. Spolu **187,5 mm**; H200 je zachovaný identifikátor. Hydroizolácia, lepidlo a obklad sú navyše.

Prepočet s m₁ = 127 kg/m² a m₂ = 17,5 kg/m² dáva f₀ = 64,07 Hz, ΔRw = 20,77 dB a **Rw,odhad = 55,77 dB ≈ 56 dB**. Oproti R2 ide o pokles 2,15 dB. Požiadavka Rw ≥ 51 dB zostáva cieľom, nie potvrdenou hodnotou. [Reprodukovateľný výpočet a zdroje](office-acoustic-wall-scientific-rationale.md). Nepreberať starších 58 dB do aktívnej skladby.

Stena je **X 22 783–27 541 mm, Y 6 364,5–6 552 mm**, výška 3 125 mm. Kúpeľňové líce je zarovnané s lícom priečky do chodby na Y 6 552 mm. Dvere nemenia polohu: pri pracovni ostáva **42,5 mm**, pri kúpeľni **149,5 mm**; kúpeľňový otvor aj krídlo ostávajú na osi Y 7 101,5 mm. Obložku pracovne zosúladiť s menšou rezervou. Tabuľa a radiátor sledujú stenu, sprcha a okná zostávajú.

[Úplná skladba a realizačné podmienky](office-acoustic-wall-thinner-options.md). Jediné opláštenie, kotvy, stabilita 100 mm muriva, podopretie a napojenia vyžadujú potvrdenie. Princíp J1/J2 sa zachováva s novými rozmermi; neprepojiť plášte tuhým mostom. **SA25-AKU 274 mm** ostáva iba [historickou zálohou](office-acoustic-wall-study.md). Jej údaj 56 dB je podkladom inej zostavy; zhodné zaokrúhlenie nového modelu H200 neznamená zhodnú dôkazovú úroveň. Výpočet H200 sa neprenáša na AK-01/AK-02.

## Odborné zdôvodnenie H200

Napojenie pri dverách je rozpracované v [detaile D1 — pevné ostenie a škáry J1/J2](office-acoustic-wall-junction.md), s výkresom na `/docs/akustika-h200/napojenie`. Pôdorys označuje tento bod ako D1; jeho plná obálka neznamená tvrdé zaliatie pripojovacích škár.

[Odborná technická správa — princíp, metodika, výpočet a literatúra](office-acoustic-wall-scientific-rationale.md) je súčasne dostupná v aplikácii na `/docs/akustika-h200`, z prehľadu dokumentácie a priamo z detailu AK-03. Obsahuje prepočet jednej Silentboard na približne 56 dB, porovnanie so staršou R2 a hranice modelového výsledku. Spoločný obsah je v `lib/h200-research.json`; Markdown sa obnovuje cez `node scripts/plan-documentation/generate-h200-research.mjs`.
