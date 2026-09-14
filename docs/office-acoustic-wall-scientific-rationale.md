# Akustická priečka H200: odborné zdôvodnenie skladby a poradia dosiek

**Projektová technická správa · literárna rešerš a predbežný výpočet**

DOM / AK-03 / H200 / R2 · 14. 9. 2026 · hlavný návrh C/B/B

> Generované z lib/h200-research.json. Úpravy článku robiť v tomto spoločnom zdroji; obnoviť cez node scripts/plan-documentation/generate-h200-research.mjs. Webová verzia: /docs/akustika-h200.

## Abstrakt

Správa zdôvodňuje výber 200 mm hybridnej priečky medzi pracovňou a sprchou v hlavnom návrhu C/B/B. Zostava kombinuje obojstranne omietnuté 100 mm keramické murivo LeierPLAN 10, 45 mm akustickú dutinu a dve dosky Silentboard 12,5 mm na strane pracovne. Posudzuje hypotézu, že rozdelenie dosiek na obe strany vaty zlepší nepriezvučnosť. Výpočtový model a systémové podklady podporujú zachovanie oboch dosiek spolu. Odhad Rw ≈ 58 dB je projektovou prognózou pri určených predpokladoch; nie je výsledkom skúšky presnej kombinácie Leier a Knauf. Požiadavka Rw ≥ 51 dB zostáva realizačným cieľom. Výber H200 stavebníkom je uzavretý.

Kľúčové slová: stavebná akustika; vzduchová nepriezvučnosť; dvojplášťová stena; rezonancia; LeierPLAN; Silentboard; H200.

## 1. Výskumná otázka a návrhové obmedzenia

Cieľom je zachovať pálenú tehlu Leier a navrhnúť tenšiu stenu než odmietnutých 274 mm pri požiadavke Rw aspoň 51 dB. Súčasne musí zostať stred otvoru aj zatvoreného krídla dverí sprchy presne na pozdĺžnej osi hlavnej chodby. Hrúbka sa posudzuje vrátane základných omietok a dosiek; dodatočné mokré povrchy sa vykazujú osobitne.

Posudzovaná otázka znie: je pri rovnakom množstve dosiek a priestore výhodnejšie ponechať dve dosky na oddelenom plášti, alebo jednu presunúť k murivu? Kritériom je akustické správanie celej konštrukcie, jej realizovateľnosť a súlad s použitým systémovým podkladom. Počet materiálových rozhraní sám osebe nie je kritériom výsledného Rw.

## 2. Predmet posúdenia: zvolená H200

Poradie v tabuľke je od sprchy smerom do pracovne. Minerálna vlna aj profil sú súčasťou 45 mm dutiny a nepripočítavajú sa znova. Povrchová úprava sprchy sa nanáša na omietnuté murivo. Obe dosky sú na suchej strane pracovne. [^2][^3]

| Vrstva od sprchy | Predpis | Hrúbka |
| --- | --- | --- |
| 1 | Súvislá vápenno-cementová omietka | 15 mm |
| 2 | LeierPLAN 10 N+F, Devecser; systémová tenkovrstvová malta | 100 mm |
| 3 | Súvislá vápenno-cementová omietka aj v dutine | 15 mm |
| 4 | W623; CD 60/27 na Direktschwingabhänger, minerálna vlna 40 mm v dutine | 45 mm |
| 5 | Knauf Silentboard, vnútorná vrstva opláštenia | 12,5 mm |
| 6 | Knauf Silentboard, vonkajšia vrstva pracovne | 12,5 mm |
| Spolu | Základná skladba vrátane omietok a dosiek | 200 mm |

> Hydroizolácia, lepidlo, obklad a prípadná celoplošná finálna stierka sú navyše. Pri dodatočných povrchoch spolu 15 mm by hotová stena mala 215 mm; je to rozmerový scenár, nie určenie konkrétneho obkladového systému.

## 3. Metodika a úroveň dôkazov

Správa spája výrobkové údaje, publikovanú výpočtovú metodiku a výskum mechanizmu ďalšieho plášťa. Nie je protokolom vlastného laboratórneho experimentu, recenzovanou publikáciou ani systematickou rešeršou celej literatúry. Údaje výrobcu jednej súčasti sa neoznačujú ako skúška celej H200.

Pri NRC sa citujú bibliografické údaje a výsledky zverejnené v abstrakte archívu a zázname vydavateľa. Článok je vedený ako recenzovaný výskum. Naše projektové aplikácie, predpoklady a výpočty sú v tejto správe oddelené od jeho výsledkov. [^1]

| Podklad | Čo dokladá | Hranica použitia |
| --- | --- | --- |
| Leier LP10 [^2] | Rw 35 dB pri dvoch 15 mm omietkach; murivo 73 kg/m² | Samostatný omietnutý tehlový základ |
| Knauf W623 [^3][^4] | Dvojité opláštenie, minimálnu dutinu a systém pružného uchytenia | Presné komponenty a podmienky systému |
| Ziegel 2022 [^5] | Metódu predikcie rezonancie a prínosu predsteny | Aplikáciu na konkrétny podklad treba potvrdiť |
| NRC / Canadian Acoustics [^1] | Riziko rezonancií po pridaní vnútorného plášťa | Skúmané oceľové priečky, nie H200 |
| Model DOM | Hrúbku, polohu, vrstvy, os dverí a geometrické kolízie | Geometrické overenie nie je akustická skúška |

## 4. Fyzikálny princíp zvolenej steny

Dopadajúci zvuk rozkmitáva konštrukciu. V zjednodušenom modeli H200 tvorí omietnutá tehla jeden hmotný plášť a dve susediace dosky druhý, pružne oddelený plášť. Vzduch v dutine prenáša dynamické pôsobenie medzi nimi; minerálna vlna tlmí pohyb vzduchu v dutine. Dve dosky vedľa seba sa tu posudzujú spoločnou plošnou hmotnosťou, bez samostatnej vzduchovej dutiny medzi nimi. [^4][^5]

Účinok závisí od hmotností, hĺbky dutiny, jej tlmenia, mechanických spojov a vzduchotesnosti. V okolí rezonančnej frekvencie môže izolácia klesať. Tuhý most, netesná škára alebo nevhodný prestup môže výsledok zhoršiť aj pri správnom súčte hrúbok. Preto H200 používa systémové pružné závesy a súvislú omietku na oboch stranách tehly. [^3][^4]

## 5. Význam a hranice výsledkov NRC

Mahn, Skoda a Cunha publikovali v roku 2024 štúdiu The Transmission Loss of Double Stud Walls with Layers of Gypsum Board Installed inside the Wall Cavity v Canadian Acoustics, 52(3). Skúmali dvojité oceľové priečky s vnútornými sadrokartónovými doskami medzi radmi profilov. Vložené dosky vytvorili tretí plášť. [^1]

Abstrakt NRC uvádza zhoršenie prenosového útlmu v nízkych frekvenciách, súvisiace s dvoma rezonanciami približne v pásme 80 Hz. Pre skúšané steny bol pokles 14–17 dB v opisovanej oblasti pod 200 Hz. Toto číslo nie je pokles celkového Rw nášho H200 a od hodnoty 58 dB sa neodčítava. [^1]

Projektová interpretácia: ďalší vnútorný plášť nemusí byť akustickým prínosom. Výsledok podporuje opatrnosť pri zmene počtu dutín; neurčuje presnú hodnotu H200. Rozdielne murivo, profily, spoje, rozmery a dosky bránia priamemu preneseniu nameranej straty na túto zostavu.

## 6. Porovnanie troch usporiadaní dosiek

Variant A je vybrané H200: obe dosky pri pracovni a jedna 45 mm dutina. Variant B presúva jednu dosku celoplošne a tuho k omietnutému murivu, bez novej vzduchovej medzery. V idealizácii tak presunie hmotnosť k ťažšiemu základu a oddelené opláštenie odľahčí. Variant C by dosku od muriva oddelil ďalšou medzerou; vznikli by tri kmitajúce plášte a dve dutiny.

Porovnanie A/B nižšie používa rovnakú pôvodnú dutinu 45 mm a hmotnosť jednej dosky 17,5 kg/m². Zjednodušenie B predpokladá úplné spojenie dosky s tehlovým základom. Doska prilepená iba na terče túto podmienku automaticky nespĺňa. [^4][^5]

| Usporiadanie | m₁ | m₂ | Modelová f₀ |
| --- | --- | --- | --- |
| A · obe dosky spolu pri pracovni | 127 kg/m² | 35 kg/m² | 47,97 Hz |
| B · jedna tuho pri murive, druhá pri pracovni | 144,5 kg/m² | 17,5 kg/m² | 63,60 Hz |
| C · ďalšia oddelená doska a druhá dutina | Trojplášťový model | Dvojplášťový vzorec nestačí | Tu neurčená |

> Vyššia modelová rezonancia B je dôvodom nepovažovať presun dosky za automatické zlepšenie. Tabuľka nepočíta nové Rw variantu B: zmenila by sa aj nepriezvučnosť základného plášťa. Pre C sa nevydáva číselná predikcia. Zostáva zvolený variant A.

## 7. Reprodukovateľný predbežný výpočet H200

Vstupom je výrobcom uvedené Rw základného omietnutého muriva 35 dB a plošná hmotnosť neomietnutého muriva 73 kg/m². Hustota omietky 1 800 kg/m³ je návrhový predpoklad tejto správy. Pre dve dosky sa používa 2 × 17,5 kg/m² z technického príkladu Knauf; dutina d = 0,045 m. [^2][^4]

Použitý model pre predsadené vrstvy je uvedený v metodike Ziegel 2022. Pre koeficient rezonančnej frekvencie sa používa 0,111; príručka upozorňuje na rozdiel oproti starším podkladom s 0,08. Predikcia je podmienená použiteľnosťou modelu na konkrétny tehlový základ a pružne uchytený systém. [^3][^5]

```text
m₁ = 73 + 2 × 0,015 × 1 800 = 127 kg/m²
m₂ = 2 × 17,5 = 35 kg/m²
f₀ = 160 × √[(0,111 / d) × (1/m₁ + 1/m₂)] = 47,97 Hz
Pre ďalší odhad sa opatrne použije f₀ = 50 Hz.
ΔRw = 74,4 − 20 × log₁₀(50) − 0,5 × 35 = 22,92 dB
Rw,odhad = 35 + 22,92 = 57,92 dB ≈ 58 dB
```

> Požiadavka Rw ≥ 51 dB a výpočtový odhad ≈ 58 dB sú dve odlišné informácie. Ich rozdiel nie je overenou rezervou na ľubovoľné montážne chyby. Nepripočítava sa univerzálny katalógový zisk nameraný na inom murive.

## 8. Citlivosť, neistota a prenos na stavbu

Zmena návrhovej hustoty omietky z 1 800 na 1 300 kg/m³ mení modelovú rezonančnú frekvenciu približne z 47,97 na 48,66 Hz. V oboch prípadoch zostáva použitá hodnota 50 Hz. Ide o kontrolu jedného vstupu, nie úplný interval neistoty. Model nezahŕňa všetky rezonancie dutinovej tehly, tuhosť kotiev, chyby montáže ani vedľajší prenos.

Rw je jednočíselné hodnotenie vzduchovej nepriezvučnosti konštrukcie. Stavebné R’w a výsledok medzi miestnosťami ovplyvňujú aj bočné steny, strop, podlaha, prestupy a cesta cez dvere a chodbu. Hluk sprchy, potrubí alebo spotrebičov môže zahŕňať aj konštrukčný prenos. Samotné splnenie Rw plnej steny preto nepredstavuje dôkaz výsledného komfortu v pracovni.

Technické dopracovanie musí potvrdiť vhodnosť systému pre konkrétne dutinové murivo, hustoty a súvislosť omietok, kotvy, rozstupy, tesnenie a obvodové napojenia. Výška predsteny nenahrádza posúdenie stability 100 mm muriva. Tieto požiadavky nemenia voľbu H200; určujú podmienky jej realizácie.

## 9. Väzba na návrh a kontrolné body

Modelová stena má rozsah X 22 783–27 541 mm, Y 6 402–6 602 mm a výšku 3 125 mm. Otvor kúpeľne šírky 800 mm leží na Y 6 701,5–7 501,5 mm; jeho stred aj stred 700 mm krídla sú Y 7 101,5 mm. Dvere pracovne sú posunuté o 30 mm k ulici, otvor končí na Y 6 322 mm a pri H200 zostáva 80 mm ostenia.

Zachovať jednu dutinu a obe dosky spolu, preložené škáry a ich systémové vytmelenie. Vata 40 mm v dutine 45 mm vypĺňa približne 89 % jej hĺbky; použitá metodika požaduje vhodnú výplň najmenej 70 % a odpor proti prúdeniu 5–50 kPa·s/m². Nepoužiť pevný záves namiesto Direktschwingabhänger. [^3][^4]

Rozvody, rám sanity, sprcha, radiátor ani kotvenie tabule nesmú vytvoriť neoverené tuhé prepojenie oboch plášťov. Finálne mokré povrchy sa pripočítajú smerom do kúpeľne a zosúladia so sprchou a zárubňou. Geometrické testy dverí a 3D vrstiev overujú digitálny návrh, nie meranie stavby.

[Detail D1 · H200 pri dverách do chodby](office-acoustic-wall-junction.md). Pevné ostenie, podtesnený obvodový profil a dve nadväzujúce škáry J1/J2. Zväčšený výkres zachytáva aj kontakt krátkeho dorovnania s vonkajšou doskou. Webový výkres: /docs/akustika-h200/napojenie.

## 10. Záver a záznam rozhodnutia

Pre AK-03 sa zachováva finálne zvolené H200 s dvomi susediacimi Silentboard doskami pri pracovni. Jeho základná hrúbka je 200 mm, požiadavka Rw ≥ 51 dB a predbežná výpočtová prognóza približne 58 dB. Zachovanie poradia vychádza zo systémovej konfigurácie a z rozdelenia hmotností; výskum NRC poskytuje podporný dôkaz rizika ďalšieho samostatného plášťa.

Rozdelenie dosiek nemá pre náš návrh doložený prínos a vyžadovalo by nové posúdenie. Záloha 274 mm ostáva historickou možnosťou, H215 porovnávanou alternatívou. Žiadna hodnota výpočtu H200 ani výsledok NRC sa neprenáša na samostatné steny AK-01 a AK-02 so skladbou SA30.

Správa zaznamenáva rozhodnutie a jeho overiteľné podklady. Pred realizáciou sa doplní odborné potvrdenie akustického návrhu a konštrukčných detailov. Po zhotovení môže požadované stavebné vlastnosti preukázať príslušné meranie; toto meranie zatiaľ nebolo vykonané.

## Použitá literatúra

Odkazy overené pri spracovaní 13.–14. 9. 2026.

[^1]: Mahn, J.; Skoda, S.; Cunha, I. Canadian Acoustics, 52(3), 8. 9. 2024. NRC Canada; recenzovaný článok. [The Transmission Loss of Double Stud Walls with Layers of Gypsum Board Installed inside the Wall Cavity](https://nrc-publications.canada.ca/eng/view/object/?id=768bf32f-8313-435f-ab85-8680efba61b2). [Záznam u vydavateľa](https://jcaa.caa-aca.ca/index.php/jcaa/article/view/3976). Citovaný mechanizmus a číselný výsledok sú zo zverejneného abstraktu NRC. Skúšané oceľové priečky sa od H200 líšia.
[^2]: Leier Slovensko Zverejnený technický list, závod Devecser, jedna strana. [LeierPLAN 10 N+F — technický list](https://www.leier.sk/wp-content/uploads/2025/07/Technicky-list-LP10-NF.pdf). Výrobkový podklad pre základné murivo a obojstranné omietky.
[^3]: Knauf Vydanie 11/2023; W623, najmä s. 7 a zásady opláštenia s. 32. [W61.de — Vorsatzschalen](https://media.knauf.com/a/EDKwYfTuyWRUkKKKihg9E7). Podmienky systémovej predsteny; nejde o skúšku kombinácie s LeierPLAN 10. Pôvodná rešerš pracovala s vydaním 11/2023. Živý odkaz výrobcu pri kontrole 14. 9. 2026 poskytuje W61_DSS.de 09/2026; v tomto novom vydaní bol overený detail W623-B2 na s. 19 a obvodové pripojenie na s. 31. Zmena vydania sama nemení vybrané dosky ani výpočtové vstupy H200.
[^4]: Knauf / Trockenbau Unlimited Technický portál výrobcu, výpočtové príklady a pružné uchytenie. [W623 — Vorsatzschale](https://trockenbau-unlimited.de/schallschutz/w623-vorsatzschale). Starší príklad so 40 mm dutinou nenahrádza novší minimálny rozmer 45 mm podľa [^3].
[^5]: Bundesverband der Deutschen Ziegelindustrie Vydanie 2022; tlačené s. 57 a 61–62. [Baulicher Schallschutz mit Ziegeln](https://ziegel.de/sites/default/files/2022-04/Ziegel-Broschuere_Baulicher_Schallschutz_2022_web_0.pdf). Metodika predikcie predsadených vrstiev a upozornenie na koeficient rezonančnej frekvencie.
