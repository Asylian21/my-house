# SA30 · Akustické deliace steny

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
