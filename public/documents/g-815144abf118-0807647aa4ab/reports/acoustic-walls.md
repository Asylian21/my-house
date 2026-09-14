# Akustické deliace steny SA30 a H200

Revízia podľa zadania stavebníka a označeného pôdorysu z 13. 9. 2026. Platí pre aktívny návrh C/B/B.

| Označenie | Umiestnenie | ID v modeli | Rozsah X | Rozsah Y |
|---|---|---|---|---|
| AK-01 | Spálňa 1.10 / chlapčenská izba 1.09 | C-OPEN-HALL-N | 14 943–15 243 mm | 7 651–10 699 mm |
| AK-02 | Kúpeľňa 1.11 / dievčenská izba 1.08 | C-OPEN-HALL-S | 14 943–15 243 mm | 3 504–6 552 mm |

Líca, dĺžka každého úseku 3 048 mm a otvor chodby 1 099 mm zostávajú zachované. Modelovaná výška stien je 3 125 mm. Konštrukčné napojenia pri fasádach, podlahe, strope a priečkach nie sú týmto geometrickým rozsahom realizačne vyriešené.

| Vrstva od spálne / kúpeľne smerom k detskej izbe | Materiál | Hrúbka |
|---|---|---|
| 1 | Leier LeierPLAN 10 P10, brúsená keramická tehla | 100 mm |
| 2 | Minerálna vata; konkrétny výrobok sa doplní v akustickom detaile | 100 mm |
| 3 | Leier LeierPLAN 10 P10, brúsená keramická tehla | 100 mm |
| **SA30** | **Dvojplášťová akustická priečka** | **300 mm** |

300 mm je hrúbka týchto troch vrstiev **bez omietok a obkladov**. Povrchové úpravy nie sú súčasťou tohto súčtu; ich hrúbku a vplyv na konečný svetlý rozmer treba určiť samostatne.

Vybraný výrobok: [LeierPLAN 10 P10 – VASTAP](https://www.vastap.cz/leier-leierplan-10-p10-P/). [Priložený technický list výrobcu](https://www.vastap.cz/files/download/ZSMA4AgCN2EdFPpyhLgdnfRSjO6pOTHy) uvádza rozmer 500 × 100 × 249 mm a použitie pre nenosné priečky. Overené 13. 9. 2026. Logistické údaje predajcu a technického listu sa líšia; nie sú použité na výkaz materiálu.

Pôvodné úseky boli v modeli označené ako nosné 300 mm. Nová skladba je vedená ako **návrh nenosnej priečky**, nie ako overená náhrada nosného muriva. Statik musí posúdiť zmenu nosného systému, podopretie nadväzujúcich konštrukcií, výšku a stabilitu jednotlivých plášťov.

Hodnota Rw celej zostavy 100 / 100 / 100 mm nie je doložená. Údaj pre jednu omietnutú tehlovú priečku nemožno preniesť na túto zostavu ani sčítať. Typ minerálnej vaty, kotvenie a napojenia pri podlahe, strope a bočných stenách, tesnenia a prestupy musí určiť akustický detail. Predísť neovereným tuhým mostom medzi plášťami. Pri AK-02 samostatne vyriešiť rám závesného WC a rozvody, aby nezasiahli do súvislej izolačnej vrstvy.

Spoločným dátovým zdrojom je `lib/acoustic-walls.ts`. Pôdorys rozlišuje keramické plášte diagonálnou šrafou a minerálnu vatu slučkovým symbolom. Kliknutie na AK-01 alebo AK-02 otvorí skladbu s kótami 100 / 100 / 100 a celkovou kótou 300 mm. Manuál obsahuje samostatný list SA30; výkres má zhodné označenia a legendu vo farebnej aj čiernobielej verzii. 3D obsahuje tri skutočné vrstvy každého úseku. Celkový obal stien zostáva základom kótovania miestností.


## AK-03 · pracovňa a sprcha

**Finálne zvolené riešenie stavebníka je H200.** Stena AK-03 medzi pracovňou 1.04 a kúpeľňou s práčovňou 1.05 používa LeierPLAN 10 a akustickú predstenu Knauf W623 na strane pracovne. Toto rozhodnutie platí pre pôdorys, 3D, detail a manuál hlavného návrhu C/B/B.

| Vrstva od kúpeľne smerom k pracovni | Materiál | Hrúbka |
|---|---|---:|
| 1 | Súvislá vápennocementová omietka | 15 mm |
| 2 | LeierPLAN 10 N+F, Devecser, systémová tenkovrstvová malta | 100 mm |
| 3 | Súvislá vápennocementová omietka aj na strane dutiny | 15 mm |
| 4 | Dutina W623; CD 60/27 na pružných závesoch Knauf Direktschwingabhänger, minerálna vlna 40 mm v dutine | 45 mm |
| 5 | Knauf Silentboard | 12,5 mm |
| 6 | Knauf Silentboard, vonkajšia doska pracovne | 12,5 mm |
| **H200** | **Základná skladba vrátane oboch omietok a dosiek** | **200 mm** |

Hydroizolácia, lepidlo, sprchový obklad a prípadná celoplošná finálna stierka sa pripočítajú k 200 mm. Vlna a profil sú vložené v 45 mm dutine; ich hrúbky sa nepripočítavajú druhýkrát. Predstena je na suchej strane pracovne, mokré povrchy na omietnutom murive kúpeľne.

Požiadavka je **Rw ≥ 51 dB**. Predbežný výpočet pre zvolenú skladbu dáva **Rw približne 58 dB**; nejde o nameraný výsledok presnej kombinácie ani o stavebné R’w. Výber H200 je uzavretý. V realizačnom detaile zostáva potvrdenie použiteľnosti systému na konkrétnom dutinovom murive, stability nenosného jadra, kotiev, napojení a utesnenia. Použiť presné pružné závesy a výplň 40 mm s odporom proti prúdeniu 5–50 kPa·s/m²; rozvody ani upevnenia nesmú vytvoriť neoverené tuhé spojenie oboch plášťov.

Základná skladba zaberá **Y = 6 402–6 602 mm**, dĺžka je 4 758 mm a modelová výška 3 125 mm. Kúpeľňové líce zostáva Y = 6 602 mm. Stavebný otvor kúpeľne Y = 6 701,5–7 501,5 mm aj krídlo zachovávajú stred **Y = 7 101,5 mm**, presne na pozdĺžnej osi hlavnej chodby. Vstup pracovne a jeho zalomenie sú oproti pôvodnému stavu posunuté o **30 mm k ulici**. Horný okraj otvoru je Y = 6 322 mm, takže pri stene zostáva **80 mm**; to je geometrický priestor, ktorý sa koordinuje s konkrétnou zárubňou.

Pozri [finálnu skladbu H200, výpočet a vycentrovanie dverí](office-acoustic-wall-thinner-options.md). **SA25-AKU 274 mm** zostáva iba [historickou zálohou](office-acoustic-wall-study.md): 12 + 250 + 12 mm s výrobcom doloženým Rw 56 dB za jeho podmienok. Hodnota 56 dB tejto zálohy sa neprenáša na H200 ani na SA30. AK-03 má vlastný detail, materiálové vrstvy a samostatný list manuálu; pri jeho zobrazení je rozhodujúce označenie H200.

## Odborné zdôvodnenie H200

Napojenie pri dverách je rozpracované v [detaile D1 — pevné ostenie a škáry J1/J2](office-acoustic-wall-junction.md), s výkresom na `/docs/akustika-h200/napojenie`. Pôdorys označuje tento bod ako D1; jeho plná obálka neznamená tvrdé zaliatie pripojovacích škár.

[Odborná technická správa — princíp, metodika, výpočet a literatúra](office-acoustic-wall-scientific-rationale.md) je súčasne dostupná v aplikácii na `/docs/akustika-h200`, z prehľadu dokumentácie a priamo z detailu AK-03. Obsahuje dôvody ponechania oboch Silentboard dosiek spolu a rozlíšenie výsledkov [výskumu NRC](https://nrc-publications.canada.ca/eng/view/object/?id=768bf32f-8313-435f-ab85-8680efba61b2) od predbežného výpočtu H200. Spoločný obsah je v `lib/h200-research.json`; Markdown sa obnovuje cez `node scripts/plan-documentation/generate-h200-research.mjs`.
