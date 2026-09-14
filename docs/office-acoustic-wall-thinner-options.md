# H200 · Finálna akustická stena medzi pracovňou a sprchou

**Finálne zvolené riešenie stavebníka je hybrid H200: omietnutá tehla LeierPLAN 10 a akustická predstena Knauf W623 s dvojitým opláštením Silentboard. Celá základná skladba má 200 mm a je záväzná pre hlavný návrh C/B/B. Predbežný výpočtový odhad Rw je približne 58 dB; ide o návrhový výpočet, nie o nameraný výsledok presnej kombinácie Leier a Knauf.** Výber H200 je uzavretý. Realizačná príprava zahŕňa technické potvrdenie systému na konkrétnom tehlovom podklade a dopracovanie jeho stykov.

Záloha 12 + 250 + 12 = 274 mm zostáva zachovaná v [pôvodnej štúdii](office-acoustic-wall-study.md) ako historická možnosť. Hrúbka bola odmietnutá ako príliš veľká. H200 šetrí **74 mm, teda približne 27 % hrúbky**, pri porovnaní rovnakých povrchov. Kúpeľňové dvere zachovávajú presnú pozdĺžnu os hlavnej chodby.

[Vizuálne porovnanie hrúbok a jednotlivých vrstiev](../output/research/office-acoustics/thinner-wall-comparison.png) · [Vektorová schéma SVG](../output/research/office-acoustics/thinner-wall-comparison.svg)

Aktuálny implementovaný návrh: [detail H200 na jednej A4 (PDF)](../output/playwright/office-acoustics/h200-wall-detail.pdf) · [záznam lokálneho overenia 2D, 3D a dokumentácie](../output/playwright/office-acoustics/h200-verification.md).

## 1. Skladba H200

Poradie od kúpeľne do pracovne:

| Vrstva | Finálne zvolená skladba | Hrúbka |
|---|---|---:|
| Povrch muriva v kúpeľni | Súvislá vápenno-cementová omietka | 15 mm |
| Murivo | LeierPLAN 10 N+F, Devecser, na systémovej tenkovrstvovej malte | 100 mm |
| Povrch muriva v dutine | Súvislá vápenno-cementová omietka; ponechať aj napriek tomu, že nebude viditeľná | 15 mm |
| Akustická dutina | 45 mm medzi omietkou a vnútorným lícom dosiek; CD 60/27 na presných pružných závesoch Knauf Direktschwingabhänger; minerálna izolácia 40 mm v tejto dutine | 45 mm |
| Vnútorné opláštenie | Knauf Silentboard | 12,5 mm |
| Vonkajšie opláštenie pracovne | Knauf Silentboard, preložené a vytmelené škáry | 12,5 mm |
| **Spolu** | **Základná skladba vrátane oboch omietok a dosiek** | **200 mm** |

**Obe dosky Silentboard zostávajú spolu na strane pracovne.** Tvoria jeden 25 mm doskový plášť oddelený dutinou od omietnutej tehly. Presunutie jednej dosky k murivu by zmenilo hmotnosti plášťov a rezonančné správanie; ďalšia vzduchová medzera by vytvorila tretí samostatný plášť. Výskum NRC dokladá pri takýchto vnútorných doskách možné zhoršenie nízkofrekvenčnej izolácie.[^11] Pre rozdelené dosky preto neplatí nižšie uvedený výpočet zvoleného H200.

Leier pre uvedený omietnutý 100 mm základ uvádza Rw 35 dB a hmotnosť neomietnutého muriva 73 kg/m². Obojstranná omietka 15 mm je súčasťou tohto podkladu.[^1] Zachovanie omietky v dutine zaisťuje aj súvislé uzavretie tehlového podkladu; jej odstránením by sa zmenili vstupy posúdenia.

Hrúbka 45 mm už obsahuje rošt aj minerálnu izoláciu. Tieto položky sa nesčítavajú druhýkrát. Výplň 40 mm zaberá približne 89 % dutiny; požiadavka výpočtového postupu je najmenej 70 % a vhodný odpor proti prúdeniu vzduchu 5–50 kPa·s/m².[^3]

Zverejnený systémový list W61.de, vydanie 11/2023, uvádza pre dvojité opláštenie W623 minimálnu dutinu 45 mm a celkovú predstenu 70 mm. Pri presných pružných závesoch umožňuje výpočtové posúdenie podľa DIN 4109-34.[^2] Staršie podklady obsahujú dutinu 40 mm a predstenu 65 mm. Tie by matematicky umožnili 195 mm, ale bez potvrdenia ich aktuálnej použiteľnosti je vhodné držať **200 mm**.

W623 sa pripevňuje k murivu cez systémové pružné závesy. Pevný priamy záves, bežný uholník ani neurčená podložka nie sú rovnocennou náhradou. Knauf tento princíp opisuje aj na príklade dierovaného keramického muriva.[^3] Rozstup profilov, závesov a kotvy sa vyberú z príslušného riadka systému pre skutočnú hmotnosť opláštenia a konkrétny podklad; hranica výšky predsteny sama nepotvrdzuje stabilitu 100 mm tehlovej priečky.

Dosková predstena je na strane pracovne. Oba plášte sa vedú súvislo po navrhnuté horné napojenie, s utesneným obvodom a preloženými škárami dosiek. Rozvody, radiátor, sprcha ani kotvenie tabule nesmú dodatočne vytvoriť neoverený tuhý most medzi tehlou a doskovým plášťom. Sanitárne potrubia a nosné rámy nie sú zahrnuté v 45 mm akustickej dutine; ich trasy a zaťaženie sa riešia osobitným detailom.

## 2. Konečná hrúbka pri sprche

**200 mm nezahŕňa hydroizoláciu, lepidlo, obklad ani prípadnú celoplošnú finálnu stierku dosiek.** Tieto povrchy zatiaľ nemajú určený konkrétny výrobok a hrúbku. Napríklad celková dodatočná rezerva 15 mm by znamenala hotovú stenu 215 mm; je to priestorový scenár, nie predpis hrúbky hydroizolácie či lepidla.

Aj záložných 274 mm bolo uvedených bez týchto povrchov. Úspora 74 mm preto zostáva pri rovnakej dodatočnej úprave zachovaná. Finálny rozmer sa po výbere obkladu premietne do polohy hotového kúpeľňového líca, sprchového priestoru a montážneho detailu zárubne.

## 3. Predbežné akustické posúdenie

Podklad má výrobcom uvedené Rw 35 dB.[^1] Výpočet doplnenej konštrukcie vychádza z hmotností oboch plášťov a šírky dutiny. Nepripočítava sa katalógové zlepšenie zmerané na inom murive.

Pre návrhovú hmotnosť vápenno-cementovej omietky 1 800 kg/m³:

`m₁ = 73 + 2 × 0,015 × 1 800 = 127 kg/m²`

Pre dve Silentboard dosky sa konzervatívne používa `m₂ = 2 × 17,5 = 35 kg/m²`; ide o plošnú hmotnosť opláštenia použitú v podklade Knauf.[^3] Dutina `d = 0,045 m`.

Metodická príručka nemeckého zväzu výrobcov tehál uvádza pre tieto predsadené vrstvy nasledujúcu závislosť rezonančnej frekvencie a zlepšenia. Upozorňuje tiež na rozdiel medzi koeficientmi 0,08 a 0,111 v starších podkladoch; pre tento návrh sa používa opatrnejší koeficient **0,111**.[^4]

`f₀ = 160 × √[(0,111 / d) × (1/m₁ + 1/m₂)] = 47,97 Hz`

Pri konzervatívnom posúdení s `f₀ = 50 Hz`:

`ΔRw = 74,4 − 20 × log₁₀(50) − 0,5 × 35 = 22,92 dB`

`Rw,odhad = 35 + 22,92 = 57,92 dB ≈ 58 dB`

**Požiadavkou zvoleného H200 je Rw ≥ 51 dB; výpočtový odhad približne 58 dB podporuje tento návrh. Nie je zárukou minimálnej hodnoty realizácie.** Metóda je predikcia idealizovaného plného panelu; realizačné posúdenie potvrdí použiteľnosť na konkrétnej zostave a jej detailoch. Koeficient 0,08 by dal priaznivejší výsledok približne 59,7 dB, ktorý tu nie je použitý ako hlavná hodnota.

Kontrola citlivosti na návrhovú hustotu omietky 1 300 až 1 800 kg/m³ dáva rezonančnú frekvenciu približne 48,66 až 47,97 Hz. V oboch prípadoch ostáva opatrne použitých 50 Hz. Tento jednoduchý výpočet však nekvantifikuje neistotu montáže, škár, rezonancií samotného dutinového muriva ani akustických mostov.

Rw plnej steny je odlišná veličina od stavebného R’w a od hluku počuteľného v pracovni. Projekt musí samostatne riešiť prenos cez podlahu, strop, bočné steny, inštalácie a cestu cez dvere oboch miestností. Nejde o dôvod automaticky odčítať univerzálnych 5 dB; chýbajúce stavebné posúdenie sa tak nenahradí.

## 4. Zachovaná alternatíva H215 bez kotvenia roštu do tehlového líca

Na porovnanie zostáva zachovaná alternatíva so samostatným roštom **215 mm**: rovnaký omietnutý Leier základ 130 mm + 10 mm voľný odstup + CW 50 s minerálnou izoláciou 50 mm + Silentboard 12,5 mm + vonkajšia Diamant 12,5 mm. Táto predstena W626 sa kotví do ohraničujúcich konštrukcií, pričom sa zachová odstup od tehlového líca. Aktuálnou voľbou pre AK-03 je H200.

Systémový list pre túto konfiguráciu obsahuje bytovú výšku predsteny 3,35 m pri rozstupe profilov 625 mm, čo pokrýva modelových 3,125 m.[^2] Stále je potrebné overiť stabilitu muriva, použitie konkrétnej kategórie a napojenia. H215 má o 15 mm väčšiu dutinu a odlišné mechanické spojenie než H200; jeho akustika sa posúdi samostatne. Ani tu sa údaj skúšky iného podkladu neprenáša na Leier automaticky.

## 5. Čisto keramický kandidát približne 22 cm

**Leier Polska MAX 220**, orientovaný na jadro **188 mm**, má v aktuálnej akustickej tabuľke pre nominálnych 19 cm výrobcom publikované **Rw 52 dB**. Tabuľka odkazuje na ITB **02168/15/Z00NA** a požaduje obojstrannú cementovápennú omietku.[^5] Číslo 220 označuje výšku tehly; nie hrúbku steny. DoP potvrdzuje rozmery 188 × 288 × 220 mm a pálenú keramiku.[^6]

S dvomi omietkami po 15 mm by vyšlo 218 mm. **Hrúbka akustických omietok však vo verejnej tabuľke chýba, preto 218 mm zostáva podmieneným rozmerom.** Údaj 10 mm v hornej časti toho istého dokumentu patrí požiarnej klasifikácii; nemožno ho bez ďalšieho prevziať do akustiky. Pri tomto variante treba od výrobcu doplniť skúšané omietky a potvrdiť zhodu dodávaného závodu a triedy s protokolom.

MAX sa murovaním odlišuje od LeierPLAN: výrobca vyžaduje úplné vyplnenie vodorovných aj zvislých maltových škár.[^7] Je to reálna keramická alternatíva s deklaráciou konkrétnej steny, no pred objednaním chýba úplný predpis povrchov a potvrdenie dodávky.

## 6. Vplyv na dvere a dispozíciu

Kúpeľňové líce základnej skladby zostáva na **Y = 6 602 mm**. Pri H200 je líce pracovne na **Y = 6 402 mm**, teda o 74 mm späť do objemu predchádzajúcej hrubšej steny. Kúpeľňový otvor ostáva **Y = 6 701,5 až 7 501,5 mm**, so stredom aj krídlom na osi **Y = 7 101,5 mm**. Stred otvoru aj uzavretého krídla je presne na pozdĺžnej osi hlavnej chodby.

Pracovňový otvor aj vstupné zalomenie sú oproti pôvodnému stavu posunuté o **30 mm k ulici**. Otvor šírky 901 mm má rozsah **Y = 5 421–6 322 mm**. Pri pracovňovom líci steny Y = 6 402 mm tak zostáva **80 mm**. Zalomenie pri zádverí má pracovňové líce Y = 5 370 mm a zachováva 51 mm po začiatok otvoru. Oproti zálohe s posunom 100 mm sa vstup vracia o 70 mm. Šírku obložky, montážne medzery a kotvenie potvrdí dodávateľ dverí; 80 mm je geometrický úsek, nie univerzálne montážne minimum.

Rozmery určujú zhodné osadenie H200 v pôdoryse a 3D hlavného návrhu C/B/B; nepredstavujú zameranie stavby. Pevné kúpeľňové líce Y = 6 602 mm je líce omietky. Dodatočná hydroizolácia a obklad sa od neho doplnia smerom do kúpeľne a zohľadnia v hotových svetlých rozmeroch, sprchovom detaile a zárubni.

## 7. Ostatné preskúmané možnosti

| Smer | Stav podkladu | Význam pre rozhodnutie |
|---|---|---|
| Leiertherm 20 N+F + omietky, približne 230 mm | Web výrobcu uvádza 51 dB, pripojený technický list 44 dB | Pred výberom treba vyriešiť rozdiel verzií a výrobných údajov; 51 dB sa zatiaľ nepotvrdzuje[^8][^9] |
| Leier THERMOPOR 8 P+W + predstena | Keramické 80 mm jadro existuje; pri omietnutí výrobca uvádza Rw 42 dB | Ešte tenší výskumný smer, ale chýbajú presné akustické omietky a treba preveriť stabilitu tenkého jadra[^5] |
| Leier 18 AKU-BET alebo LECA 18 | Vysoké deklarované akustické hodnoty pri 180 mm jadre | Betónové/keramzitobetónové prvky; menili by požiadavku na pálenú tehlu[^10] |
| PhoneStar, Tecsound a podobné tenké prídavné systémy | Nájdené boli odlišné skúšobné podklady | Ich katalógové zlepšenie sa bez výpočtu alebo potvrdenia nepoužije ako hodnota hotového Leier hybridu |

## 8. Realizačné dopracovanie finálne zvoleného H200

Na technické potvrdenie zostavy je pripravená táto špecifikácia:

> Deliaca nenosná stena pracovne a kúpeľne, modelová dĺžka 4 758 mm, výška 3 125 mm. Požadované Rw plného panelu najmenej 51 dB. Základ LeierPLAN 10 N+F Devecser, 100 mm, systémová tenkovrstvová malta, 15 mm súvislá vápenno-cementová omietka na oboch stranách. Na strane pracovne W623, CD 60/27 cez originálne Direktschwingabhänger, dutina 45 mm, minerálna izolácia 40 mm, 2 × Silentboard 12,5 mm. Celok 200 mm pred finálnym obkladom. Predbežný výpočet s m₁ = 127 kg/m², m₂ = 35 kg/m² a f₀ = 50 Hz dáva Rw približne 58 dB. Potvrdiť použiteľnosť výpočtu, kotvy v konkrétnom dutinovom murive, rozstupy, stropný a obvodový styk, utesnenie škár a riešenie prestupov. Prípadné zmeny systému uviesť spolu s výslednou hrúbkou a akustickým podkladom.

Text je technický podklad pre dodávateľa alebo akustika; nebol odoslaný. Realizačná dokumentácia doplní konkrétne kotvy, rozstupy, napojenia, zaťaženie, mokré povrchy a posúdenie celkovej akustiky miestností. **H200 je finálna voľba stavebníka a aktívna skladba AK-03. H215 zostáva porovnávacou alternatívou a 274 mm historickou zálohou.** Rozhodnutie o skladbe sa tým neoznačuje za laboratórnu certifikáciu ani za statické schválenie.

## Zdroje

[^1]: Leier Slovensko, [LeierPLAN 10 N+F — technický list](https://www.leier.sk/wp-content/uploads/2025/07/Technicky-list-LP10-NF.pdf), jedna strana; Rw 35 dB, omietky 15 mm, hmotnosť muriva 73 kg/m².
[^2]: Knauf, [W61.de — Vorsatzschalen, vydanie 11/2023](https://media.knauf.com/a/EDKwYfTuyWRUkKKKihg9E7), najmä systémové varianty W623 a výšky W626. Údaje pre presné systémové komponenty, nie ľubovoľné náhrady.
[^3]: Knauf, [W623 — výpočtové posúdenie a pružné uchytenie](https://trockenbau-unlimited.de/schallschutz/w623-vorsatzschale), požiadavky na výplň a príklad s keramickým podkladom; obsahuje starší rozmer dutiny, ktorý nenahrádza novší systémový list.
[^4]: Bundesverband der Deutschen Ziegelindustrie, [Baulicher Schallschutz mit Ziegeln, 2022](https://ziegel.de/sites/default/files/2022-04/Ziegel-Broschuere_Baulicher_Schallschutz_2022_web_0.pdf), tlačené strany 57 a 62, koeficient rezonančnej frekvencie a výpočet predsadených vrstiev.
[^5]: Leier Polska, [Akustické a požiarne vlastnosti, aktualizácia máj 2025](https://www.leier.pl/wp-content/uploads/2025/06/wlasciwosci-ogniowe-i-dzwiekoizolacyjne-przegrob-z-elementow-murowych-THERMOPOR_od_maj_2025.pdf), samostatná spodná akustická tabuľka.
[^6]: Leier Polska, [MAX 220, klasa 15 — DoP Wola Rzędzińska, 16. 12. 2022](https://www.leier.pl/wp-content/uploads/2023/02/leier_dec_wr_MAX22015_od_20221216.pdf).
[^7]: Leier Polska, [Montáž murovacích prvkov na obyčajnú maltu, máj 2025](https://www.leier.pl/wp-content/uploads/2025/06/instr-obslugi-elementy-murowe-murowane-na-zaprawe-zwykla_maj-2025_pl.pdf).
[^8]: Leier Hungária, [Leiertherm 20 N+F — produktová stránka](https://www.leier.hu/hu/termekek/leiertherm-20-n-f-tegla), hodnota 51 dB pre Mátraderecske, overené 13. 9. 2026.
[^9]: Leier Hungária, [Pripojený technický list Leiertherm 20 N+F](https://www.leier.hu/uploads/files/Leiertherm_20_NF_adatlap.pdf), hodnota 44 dB a odlišné údaje hustoty.
[^10]: Leier Polska, [THERMOPOR 18 AKU-BET](https://www.leier.pl/product/bloczek-thermopor-18-aku-bet/) a [LECA BLOK AKUSTYCZNY 18](https://www.leier.pl/product/leca-blok-akustyczny-18-leier/), materiálové rozlíšenie oproti pálenej keramike.
[^11]: Mahn, Skoda, Cunha / NRC Canada, [The Transmission Loss of Double Stud Walls with Layers of Gypsum Board Installed inside the Wall Cavity](https://nrc-publications.canada.ca/eng/view/object/?id=768bf32f-8313-435f-ab85-8680efba61b2), 8. 9. 2024. Princíp ďalšieho plášťa a rezonancií; experiment inej konštrukcie, nie meranie H200.

## Odborné zdôvodnenie H200

Konkrétny styk pri dverách: [D1 — napojenie H200 na spoločné ostenie](office-acoustic-wall-junction.md), výkres `/docs/akustika-h200/napojenie`. Zachováva 200 mm, dvere na osi a nominálnych 80 mm pri pracovni. Rieši oba kontakty dosiek s masívom, vrátane krátkeho dorovnania ostenia.

[Odborná technická správa — princíp, metodika, výpočet a literatúra](office-acoustic-wall-scientific-rationale.md) je súčasne dostupná v aplikácii na `/docs/akustika-h200`, z prehľadu dokumentácie a priamo z detailu AK-03. Obsahuje dôvody ponechania oboch Silentboard dosiek spolu a rozlíšenie výsledkov [výskumu NRC](https://nrc-publications.canada.ca/eng/view/object/?id=768bf32f-8313-435f-ab85-8680efba61b2) od predbežného výpočtu H200. Spoločný obsah je v `lib/h200-research.json`; Markdown sa obnovuje cez `node scripts/plan-documentation/generate-h200-research.mjs`.
