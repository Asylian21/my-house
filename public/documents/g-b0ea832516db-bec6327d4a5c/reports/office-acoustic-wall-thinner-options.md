# H200 · Aktuálna akustická stena s jednou doskou Silentboard

**Revízia 16. 9. 2026:** stavebník odobral jednu dosku a potvrdil zarovnanie kúpeľňového líca s lícom priečky do chodby. AK-03 má **187,5 mm**, jednu Silentboard 12,5 mm a predbežný výpočet **Rw ≈ 55,77 dB ≈ 56 dB**. Identifikátor **H200** zostáva kvôli nadväznosti dokumentácie; už neoznačuje hrúbku 200 mm. Toto zadanie nahrádza skoršiu voľbu dvojitého opláštenia.

Podrobný prepočet a jeho hranice: [odborná správa R3](office-acoustic-wall-scientific-rationale.md), [webová správa](/docs/akustika-h200). Napojenie: [detail D1 / R2](office-acoustic-wall-junction.md). Staršie lokálne obrázky, PDF H200 200 mm a záznamy overenia z 13.–14. 9. 2026 sú historické; nepreukazujú túto revíziu. Aktuálny export je v [knižnici dokumentácie](/docs).

## 1. Aktívna skladba

Poradie od kúpeľne do pracovne:

| Vrstva | Predpis | Hrúbka |
|---|---|---:|
| Kúpeľňová omietka | Súvislá vápenno-cementová omietka | 15 mm |
| Murivo | LeierPLAN 10 N+F, Devecser, systémová tenkovrstvová malta | 100 mm |
| Omietka v dutine | Súvislá vápenno-cementová omietka | 15 mm |
| Dutina | CD 60/27 na Direktschwingabhänger, vata 40 mm v tejto dutine | 45 mm |
| Jediné opláštenie pracovne | Knauf Silentboard so systémovým utesnením škár | 12,5 mm |
| **Spolu** | **Vrátane oboch omietok a jednej dosky** | **187,5 mm** |

Minerálna vlna a rošt sú zahrnuté v 45 mm dutine. Hydroizolácia, lepidlo, obklad a prípadná celoplošná stierka sú navyše. Napríklad 15 mm dodatočných povrchov znamená hotovú hrúbku 202,5 mm; nejde o predpis konkrétneho obkladu. Oproti historickej zálohe 274 mm je základná skladba tenšia o 86,5 mm (31,6 %), oproti H200 R2 o 12,5 mm.

Obe 15 mm omietky zostávajú. Leier pre taký základ uvádza Rw 35 dB a murivo 73 kg/m².[^1] W623 sa v technickom podklade opisuje aj s jedným opláštením a príkladom jednej Silentboard 17,5 kg/m².[^3] Presné komponenty, rozstupy a kotvy pre výšku 3 125 mm a LeierPLAN 10 potvrdí dodávateľ; nový Silentboard 2in1 sa automaticky nezamieňa za pôvodnú dosku.[^2]

## 2. Akustický prepočet

Výpočet používa rovnaký základ a 45 mm dutinu ako R2, mení plošnú hmotnosť doskového plášťa na polovicu. Implementácia: `lib/h200-acoustic-calculation.ts`. Hustota omietky 1 800 kg/m³ je návrhový predpoklad.

```text
m₁ = 73 + 2 × 0,015 × 1 800 = 127 kg/m²
m₂ = 1 × 17,5 = 17,5 kg/m²
d = 0,045 m
f₀ = 160 × √[(0,111 / d) × (1/m₁ + 1/m₂)] = 64,07495 Hz
ΔRw = 74,4 − 20 × log₁₀(64,07495) − 0,5 × 35 = 20,76623 dB
Rw,odhad = 35 + 20,76623 = 55,76623 dB ≈ 56 dB
```

Rovnica je z metodiky Ziegel 2022, tlačená s. 62.[^4] Oproti pôvodnému odhadu R2 57,92 dB (dve dosky, opatrne použité f₀ = 50 Hz) je pokles **2,15 dB**. Pri priamom porovnaní nezaokrúhlených rezonancií oboch scenárov je pokles 2,51 dB. Cieľ **Rw ≥ 51 dB** zostáva; jeho splnenie nie je týmto modelom certifikované.

Citlivosť na hustotu omietky 1 300–1 800 kg/m³ dáva približne f₀ 64,59–64,07 Hz a Rw 55,70–55,77 dB, ak sa ponechá Rw základu 35 dB. Nie je to interval spoľahlivosti; zmena omietky môže zmeniť aj nepriezvučnosť podkladu. Model nezahŕňa všetky rezonancie dutinovej tehly, kotvy, škáry, netesnosti a bočné cesty zvuku. Výsledné R′w hotových miestností vyžaduje samostatné posúdenie napojení a prípadne meranie.

## 3. Zarovnanie, dvere a realizácia

H200 má rozsah **X 22 783–27 541 mm, Y 6 364,5–6 552 mm**. Kúpeľňové líce aj líce priečky do chodby ležia na **Y 6 552 mm**. Oproti R2 sa kúpeľňové líce posunulo o 50 mm a pracovňové o 37,5 mm k ulici. Rozdiel hrúbok oproti 140 mm chodbovej priečke je na strane pracovne/zádveria 47,5 mm. Nejde o osové vycentrovanie.

Dvere zostávajú: pracovňa Y 5 421–6 322 mm, kúpeľňa Y 6 701,5–7 501,5 mm, os kúpeľňového otvoru aj krídla Y 7 101,5 mm. Pri pracovni zostáva **42,5 mm**, pri kúpeľni **149,5 mm**. D1 rozdeľuje pracovňové napojenie na 37,5 mm pevné dorovnanie a 5 mm J2. Obložku pracovne treba zvoliť pre túto menšiu rezervu a nesmie premostiť akustickú škáru. Modelová 10 mm obložka geometricky prejde; nejde o univerzálny montážny rozmer reálneho dverného systému.

Pracovňa má 12,1352895 m², kúpeľňa 7,214871 m². Sprcha a fasádne okná zostávajú, tabuľa a radiátor sledujú nové líca. Kúpeľňové líce je základné omietnuté líce; obklad sa pripočíta do kúpeľne.

Použiť originálne pružné Direktschwingabhänger, vhodné podtesnenie a minerálnu vlnu 40 mm. Tá vypĺňa 89 % dutiny; podklad uvádza najmenej 70 % a odpor proti prúdeniu 5–50 kPa·s/m².[^3] Jedna doska nemá prekrytie škár druhou vrstvou: škáry, hrany, podopretie a tmelenie treba vyhotoviť podľa potvrdenej jednovrstvovej konfigurácie. Zachovať J1 a mäkký J2 bez tvrdých mostov. Stabilita 100 mm muriva, jeho podopretie, kotvy, prestupy a finálne mokré povrchy zostávajú na realizačné dopracovanie. Žiadne údaje tejto steny sa neprenášajú na AK-01/AK-02.

## Historické porovnania

Nasledujúce alternatívy sú zachovanou rešeršou z 13. 9. 2026, nie aktuálnou skladbou. Odkazy a výrobkové údaje tejto historickej časti sa pri revízii jednej dosky znovu neoverovali.

## 4. Zachovaná alternatíva H215 bez kotvenia roštu do tehlového líca

Na porovnanie zostáva zachovaná alternatíva so samostatným roštom **215 mm**: rovnaký omietnutý Leier základ 130 mm + 10 mm voľný odstup + CW 50 s minerálnou izoláciou 50 mm + Silentboard 12,5 mm + vonkajšia Diamant 12,5 mm. Táto predstena W626 sa kotví do ohraničujúcich konštrukcií, pričom sa zachová odstup od tehlového líca. Aktuálnou voľbou pre AK-03 je H200.

Systémový list pre túto konfiguráciu obsahuje bytovú výšku predsteny 3,35 m pri rozstupe profilov 625 mm, čo pokrýva modelových 3,125 m.[^2] Stále je potrebné overiť stabilitu muriva, použitie konkrétnej kategórie a napojenia. H215 má oproti aktuálnej H200 o 15 mm väčšiu dutinu, dvojité opláštenie a odlišné mechanické spojenie; jeho akustika sa posúdi samostatne. Ani tu sa údaj skúšky iného podkladu neprenáša na Leier automaticky.

## 5. Čisto keramický kandidát približne 22 cm

**Leier Polska MAX 220**, orientovaný na jadro **188 mm**, má v aktuálnej akustickej tabuľke pre nominálnych 19 cm výrobcom publikované **Rw 52 dB**. Tabuľka odkazuje na ITB **02168/15/Z00NA** a požaduje obojstrannú cementovápennú omietku.[^5] Číslo 220 označuje výšku tehly; nie hrúbku steny. DoP potvrdzuje rozmery 188 × 288 × 220 mm a pálenú keramiku.[^6]

S dvomi omietkami po 15 mm by vyšlo 218 mm. **Hrúbka akustických omietok však vo verejnej tabuľke chýba, preto 218 mm zostáva podmieneným rozmerom.** Údaj 10 mm v hornej časti toho istého dokumentu patrí požiarnej klasifikácii; nemožno ho bez ďalšieho prevziať do akustiky. Pri tomto variante treba od výrobcu doplniť skúšané omietky a potvrdiť zhodu dodávaného závodu a triedy s protokolom.

MAX sa murovaním odlišuje od LeierPLAN: výrobca vyžaduje úplné vyplnenie vodorovných aj zvislých maltových škár.[^7] Je to reálna keramická alternatíva s deklaráciou konkrétnej steny, no pred objednaním chýba úplný predpis povrchov a potvrdenie dodávky.

## 7. Ostatné preskúmané možnosti

| Smer | Stav podkladu | Význam pre rozhodnutie |
|---|---|---|
| Leiertherm 20 N+F + omietky, približne 230 mm | Web výrobcu uvádza 51 dB, pripojený technický list 44 dB | Pred výberom treba vyriešiť rozdiel verzií a výrobných údajov; 51 dB sa zatiaľ nepotvrdzuje[^8][^9] |
| Leier THERMOPOR 8 P+W + predstena | Keramické 80 mm jadro existuje; pri omietnutí výrobca uvádza Rw 42 dB | Ešte tenší výskumný smer, ale chýbajú presné akustické omietky a treba preveriť stabilitu tenkého jadra[^5] |
| Leier 18 AKU-BET alebo LECA 18 | Vysoké deklarované akustické hodnoty pri 180 mm jadre | Betónové/keramzitobetónové prvky; menili by požiadavku na pálenú tehlu[^10] |
| PhoneStar, Tecsound a podobné tenké prídavné systémy | Nájdené boli odlišné skúšobné podklady | Ich katalógové zlepšenie sa bez výpočtu alebo potvrdenia nepoužije ako hodnota hotového Leier hybridu |

## Zdroje

[^1]: Leier Slovensko, [LeierPLAN 10 N+F — technický list](https://www.leier.sk/wp-content/uploads/2025/07/Technicky-list-LP10-NF.pdf), jedna strana; Rw 35 dB, omietky 15 mm, hmotnosť muriva 73 kg/m².
[^2]: Knauf, [W61_DSS.de — Vorsatzschalen, živé vydanie 09/2026](https://media.knauf.com/a/EDKwYfTuyWRUkKKKihg9E7), najmä systémové varianty W623 a výšky W626. Údaje pre presné systémové komponenty, nie ľubovoľné náhrady.
[^3]: Knauf, [W623 — výpočtové posúdenie a pružné uchytenie](https://trockenbau-unlimited.de/schallschutz/w623-vorsatzschale), požiadavky na výplň a príklad s keramickým podkladom; obsahuje starší rozmer dutiny, ktorý nenahrádza novší systémový list.
[^4]: Bundesverband der Deutschen Ziegelindustrie, [Baulicher Schallschutz mit Ziegeln, 2022](https://ziegel.de/sites/default/files/2022-04/Ziegel-Broschuere_Baulicher_Schallschutz_2022_web_0.pdf), tlačené strany 57 a 62, koeficient rezonančnej frekvencie a výpočet predsadených vrstiev.
[^5]: Leier Polska, [Akustické a požiarne vlastnosti, aktualizácia máj 2025](https://www.leier.pl/wp-content/uploads/2025/06/wlasciwosci-ogniowe-i-dzwiekoizolacyjne-przegrob-z-elementow-murowych-THERMOPOR_od_maj_2025.pdf), samostatná spodná akustická tabuľka.
[^6]: Leier Polska, [MAX 220, klasa 15 — DoP Wola Rzędzińska, 16. 12. 2022](https://www.leier.pl/wp-content/uploads/2023/02/leier_dec_wr_MAX22015_od_20221216.pdf).
[^7]: Leier Polska, [Montáž murovacích prvkov na obyčajnú maltu, máj 2025](https://www.leier.pl/wp-content/uploads/2025/06/instr-obslugi-elementy-murowe-murowane-na-zaprawe-zwykla_maj-2025_pl.pdf).
[^8]: Leier Hungária, [Leiertherm 20 N+F — produktová stránka](https://www.leier.hu/hu/termekek/leiertherm-20-n-f-tegla), hodnota 51 dB pre Mátraderecske, overené 13. 9. 2026.
[^9]: Leier Hungária, [Pripojený technický list Leiertherm 20 N+F](https://www.leier.hu/uploads/files/Leiertherm_20_NF_adatlap.pdf), hodnota 44 dB a odlišné údaje hustoty.
[^10]: Leier Polska, [THERMOPOR 18 AKU-BET](https://www.leier.pl/product/bloczek-thermopor-18-aku-bet/) a [LECA BLOK AKUSTYCZNY 18](https://www.leier.pl/product/leca-blok-akustyczny-18-leier/), materiálové rozlíšenie oproti pálenej keramike.
[^11]: Mahn, Skoda, Cunha / NRC Canada, [The Transmission Loss of Double Stud Walls with Layers of Gypsum Board Installed inside the Wall Cavity](https://nrc-publications.canada.ca/eng/view/object/?id=768bf32f-8313-435f-ab85-8680efba61b2), 8. 9. 2024. Princíp ďalšieho plášťa a rezonancií; experiment inej konštrukcie, nie meranie H200.
