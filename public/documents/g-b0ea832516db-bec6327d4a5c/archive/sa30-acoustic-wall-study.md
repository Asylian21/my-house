# Archív: pôvodná dvojplášťová SA30

**Nahradené 16. 9. 2026. Tento dokument je historický podklad, nie aktuálne zadanie. AK-01 a AK-02 teraz používajú jednu 300 mm obvodovú tehlu SM30; dôvod odhlučnenia zostáva.** [Aktuálne riešenie](acoustic-walls.md). Nižšie je zachované pôvodné znenie a výpočet; jeho 58 dB ani hmotnosti sa na SM30 neprenášajú. Výpočtový modul je v `lib/archive/sa30-acoustic-calculation.ts`.

# Akustické deliace steny SA30 a H200

Revízia podľa zadania stavebníka a označeného pôdorysu z 13. 9. 2026. Platí pre aktívny návrh C/B/B.

| Označenie | Umiestnenie | ID v modeli | Rozsah X | Rozsah Y |
|---|---|---|---|---|
| AK-01 | Spálňa 1.10 / chlapčenská izba 1.09 | C-OPEN-HALL-N | 14 943–15 243 mm | 7 651–10 699 mm |
| AK-02 | Kúpeľňa 1.11 / dievčenská izba 1.08 | C-OPEN-HALL-S | 14 943–15 243 mm | 3 504–6 552 mm |

Líca, dĺžka každého úseku 3 048 mm a otvor chodby 1 099 mm zostávajú zachované. Modelovaná výška stien je 3 125 mm. Konštrukčné napojenia pri fasádach, podlahe, strope a priečkach nie sú týmto geometrickým rozsahom realizačne vyriešené.

| Vrstva od spálne / kúpeľne smerom k detskej izbe | Materiál | Hrúbka |
|---|---|---|
| 1 | Vápenno-cementová omietka do spálne / kúpeľne; výpočtový predpoklad | 15 mm |
| 2 | Leier LeierPLAN 10 P10, brúsená keramická tehla | 100 mm |
| 3 | Mäkká minerálna vata vhodná pre deliace steny; celoplošná výplň bez stlačenia | 100 mm |
| 4 | Leier LeierPLAN 10 P10, brúsená keramická tehla | 100 mm |
| 5 | Vápenno-cementová omietka do detskej izby; výpočtový predpoklad | 15 mm |
| **SA30 s omietkami** | **Dvojplášťová akustická priečka** | **330 mm** |

Stavebník 15. 9. 2026 potvrdil omietku v každej miestnosti. Pre predbežný výpočet sa volí **15 mm VC omietky s návrhovou hustotou 1 800 kg/m³ na každom izbovom líci**, jedna omietka na každý plášť. Omietka sa nepridáva do dutiny; vata zostáva 100 mm. Jadro modelu ostáva **300 mm**, skladba s týmito omietkami má **330 mm**, povrchy uberú 15 mm zo svetlého rozmeru každej susednej izby. Hydroizolácia, lepidlo a obklad kúpeľne sú navyše. Konkrétny výrobok omietky a vaty je ešte potrebné určiť; hrúbka a hustota omietky sú výpočtové predpoklady.

Vybraný výrobok: [LeierPLAN 10 P10 – VASTAP](https://www.vastap.cz/leier-leierplan-10-p10-P/). [Priložený technický list výrobcu](https://www.vastap.cz/files/download/ZSMA4AgCN2EdFPpyhLgdnfRSjO6pOTHy) uvádza rozmer 500 × 100 × 249 mm a použitie pre nenosné priečky. Overené 13. 9. 2026. Logistické údaje predajcu a technického listu sa líšia; nie sú použité na výkaz materiálu.

Pôvodné úseky boli v modeli označené ako nosné 300 mm. Nová skladba je vedená ako **návrh nenosnej priečky**, nie ako overená náhrada nosného muriva. Statik musí posúdiť zmenu nosného systému, podopretie nadväzujúcich konštrukcií, výšku a stabilitu jednotlivých plášťov.

Predbežný **hmotnostný scenár oddelených plášťov dáva 58,43 dB ≈ 58 dB**, postup nižšie. Nejde o výrobcom deklarované alebo namerané Rw celej SA30. Kotvenie, obvodové napojenia a prestupy vrátane rámu WC pri AK-02 vyžadujú konkrétny detail a nesmú vytvoriť tuhé prepojenie plášťov.

Spoločným dátovým zdrojom je `lib/acoustic-walls.ts`. Kliknutie na AK-01 alebo AK-02 otvorí päťvrstvový detail 15 / 100 / 100 / 100 / 15 a výpočet; rovnaká skladba je v manuáli a legende. Pôdorys a 3D naďalej zobrazujú a kótujú tri konštrukčné vrstvy 300 mm jadra. Omietky sú výpočtovým povrchom mimo tohto obalu; nejde o prerátanie modelových svetlých rozmerov na hotové líca.

## Výpočtový detail SA30 · AK-01 a AK-02

Doplnené 15. 9. 2026 po potvrdení omietok: obe steny zdieľajú reprodukovateľný výpočet v `lib/archive/sa30-acoustic-calculation.ts`. Výsledok v detaile je **R′w,model ≈ 58 dB · výpočet**. Zhodné zaokrúhlenie s vtedajším dvojdoskovým H200 vychádzalo z odlišného výpočtu; aktuálna jednovrstvová revízia H200 zo 16. 9. 2026 má predbežné Rw ≈ 56 dB.

[Technický list LeierPLAN 10 N+F, Devecser](https://www.leier.sk/wp-content/uploads/2025/07/Technicky-list-LP10-NF.pdf) uvádza 73 kg/m² neomietnutého muriva. Jedna izbová omietka pridáva 27 kg/m². Použitý porovnávací scenár pre murované plášte vychádza z [Ziegel 2022, s. 34–38, rovnice 4.10 a 4.11](https://ziegel.de/sites/default/files/2022-04/Ziegel-Broschuere_Baulicher_Schallschutz_2022_web_0.pdf#page=36):

```text
m₁ = m₂ = 73 + 0,015 × 1 800 = 100 kg/m²
mΣ = 200 kg/m²
R′w,1 = 28 × log₁₀(200) − 18 = 46,43 dB
ΔRw = 12 dB; K = 0 dB
R′w,model = 46,43 + 12 − 0 = 58,43 dB ≈ 58 dB

f₀ = 160 × √[(0,111 / 0,100) × (1/100 + 1/100)]
f₀ ≈ 23,84 Hz
```

Zdroj pracuje s **R′w domových deliacich stien**, nie s laboratórnym Rw; túto značku zachovávame s dodatkom „model“. Predpokladáme oddelené plášte, vzduchotesné omietky a plnú mäkkú minerálnu výplň typu WTH. Základný prírastok je 12 dB; príplatok 2 dB za širšiu dutinu sa neuplatňuje. **K = 0 je predpoklad scenára**, nie preukázaný nulový bočný prenos v dome. Každý plášť nominálne dosahuje dolnú hranicu 100 kg/m² pri dutine aspoň 50 mm; ľahšia omietka tento predpoklad mení. [Rezonancia podľa s. 57](https://ziegel.de/sites/default/files/2022-04/Ziegel-Broschuere_Baulicher_Schallschutz_2022_web_0.pdf#page=57) je pomocná kontrola.

Použiteľnosť modelu na konkrétne LeierPLAN 10 a napojenia C/B/B nie je potvrdená. Skutočné R′w medzi izbami sa musí vypočítať pre spoločnú dosku, strop, bočné steny a prestupy osobitne. [Hranice postupu na s. 38](https://ziegel.de/sites/default/files/2022-04/Ziegel-Broschuere_Baulicher_Schallschutz_2022_web_0.pdf#page=38) bránia zameniť uvedený scenár s overeným výsledkom realizácie. Nie je to meranie ani deklarácia konkrétnej SA30.

Výrobcom uvedených Rw 35 dB patrí jednej 100 mm murovanej priečke s 15 mm omietkou z oboch strán (celkom 130 mm). Tento údaj nie je vstupom nášho hmotnostného scenára a dve hodnoty sa nesčítavajú.
