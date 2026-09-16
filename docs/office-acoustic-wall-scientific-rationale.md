# Akustická priečka H200: revízia s jednou doskou Silentboard

**Projektová technická správa · literárna rešerš a predbežný výpočet**

DOM / AK-03 / H200 / R3 · 16. 9. 2026 · hlavný návrh C/B/B

> Generované z lib/h200-research.json. Úpravy článku robiť v tomto spoločnom zdroji; obnoviť cez node scripts/plan-documentation/generate-h200-research.mjs. Webová verzia: /docs/akustika-h200.

## Abstrakt

Na žiadosť stavebníka zostáva pri pracovni jedna doska Silentboard 12,5 mm. Základná hrúbka AK-03 je 187,5 mm; identifikátor H200 sa zachováva pre nadväznosť dokumentácie. Kúpeľňové líce je zarovnané s lícom priečky do chodby na Y = 6 552 mm. Aktualizovaný model dáva f₀ = 64,07 Hz a Rw,odhad = 55,77 dB, zaokrúhlene 56 dB. Oproti pôvodnému odhadu 57,92 dB ide o pokles 2,15 dB. Požiadavka Rw ≥ 51 dB zostáva cieľom; výpočet nie je skúškou presnej zostavy ani meraním R′w hotových miestností.

Kľúčové slová: stavebná akustika; vzduchová nepriezvučnosť; dvojplášťová stena; rezonancia; LeierPLAN; Silentboard; H200.

## 1. Aktuálne rozhodnutie a rozsah revízie

Revízia R3 nahrádza dvojité opláštenie z R2 jednou doskou. Odoberá sa pôvodná vonkajšia vrstva; pôvodná vnútorná doska sa stáva jediným opláštením pracovne. Nepridáva sa ďalšia dutina ani doska pri murive.

Stavebník výslovne zvolil spoločné líce kúpeľne a chodby, nie spoločnú os stien. H200 preto leží na Y 6 364,5–6 552 mm, chodbová priečka na Y 6 412–6 552 mm. Rozdiel 47,5 mm zostáva iba na strane pracovne a zádveria. H200 je zachovaný identifikátor skladby; neznamená už hrúbku 200 mm.

## 2. Skladba 187,5 mm

Poradie je od kúpeľne do pracovne. Rošt a izolácia sa zmestia do uvedenej dutiny; ich hrúbky sa nepripočítavajú druhýkrát.

| Vrstva | Predpis | Hrúbka |
| --- | --- | --- |
| 1 | Súvislá vápenno-cementová omietka pri kúpeľni | 15 mm |
| 2 | LeierPLAN 10 N+F, Devecser, systémová tenkovrstvová malta | 100 mm |
| 3 | Súvislá vápenno-cementová omietka v dutine | 15 mm |
| 4 | CD 60/27 na Direktschwingabhänger, minerálna vlna 40 mm v dutine | 45 mm |
| 5 | Jedna Knauf Silentboard pri pracovni | 12,5 mm |
| Spolu | Základná skladba | 187,5 mm |

> Hydroizolácia, lepidlo, obklad a prípadná celoplošná stierka sú navyše. Ilustračných 15 mm dodatočných povrchov by znamenalo 202,5 mm; konkrétna povrchová skladba zatiaľ nie je určená.

## 3. Podklady a hranice ich použitia

Leier uvádza pre 100 mm murivo s obojstrannou 15 mm VC omietkou Rw 35 dB a hmotnosť samotného muriva 73 kg/m². [^2]

Knauf na technickom portáli opisuje W623 s jedným alebo dvoma oplášteniami a uvádza príklad jednej Silentboard 12,5 mm s plošnou hmotnosťou približne 17,5 kg/m². Jeho príklad používa iný tehlový základ; výsledné dB z tohto príkladu sa sem neprenášajú. [^4]

Živý systémový list W61_DSS.de je vydanie 09/2026. Presný riadok pre jednu pôvodnú Silentboard, výšku 3 125 mm, rozstupy a kotvy do LeierPLAN 10 musí potvrdiť dodávateľ. Nový výrobok Silentboard 2in1 nie je automatickou náhradou zvolenej dosky. Dutina 45 mm zostáva projektovým rozmerom. [^3]

## 4. Účinok odobratia dosky

Omietnuté murivo tvorí ťažší plášť a jediná doska ľahší pružne oddelený plášť. Dutina a minerálna vlna zostávajú. Zníženie plošnej hmotnosti opláštenia z 35 na 17,5 kg/m² zvyšuje modelovú rezonanciu a znižuje predpovedané zlepšenie nepriezvučnosti.

Predchádzajúca diskusia o rozdelení dvoch dosiek a výskum NRC sa týkali iného zásahu. Odobratím dosky nevzniká tretí plášť. Výsledky NRC sa nepoužívajú ako číselná korekcia tejto revízie. [^1]

## 5. Reprodukovateľný predbežný prepočet

Hustota omietky 1 800 kg/m³ je projektový predpoklad. Model vychádza z metodiky Ziegel 2022, s. 62, rovnice 5.22 a tabuľky 5.9, s koeficientom 0,111. Výsledok závisí od použiteľnosti modelu na konkrétnom dutinovom murive a pružnom kotvení. [^5]

| Scenár | m₂ | f₀ / použité f₀ | Rw,odhad |
| --- | --- | --- | --- |
| Aktuálna jedna doska | 17,5 kg/m² | 64,07 / 64,07 Hz | 55,77 dB |
| Predchádzajúce dve dosky (R2) | 35 kg/m² | 47,97 / 50 Hz | 57,92 dB |
| Rozdiel aktuálna − R2 | −17,5 kg/m² | vyššia rezonancia | −2,15 dB |

```text
m₁ = 73 + 2 × 0,015 × 1 800 = 127 kg/m²
m₂ = 1 × 17,5 = 17,5 kg/m²; d = 0,045 m
f₀ = 160 × √[(0,111 / 0,045) × (1/127 + 1/17,5)] = 64,07495 Hz
ΔRw = 74,4 − 20 × log₁₀(64,07495) − 0,5 × 35 = 20,76623 dB
Rw,odhad = 35 + 20,76623 = 55,76623 dB ≈ 56 dB
```

> R2 použila opatrný projektový limit 50 Hz; pre aktuálnu dosku sa používa vypočítaných 64,07 Hz bez zaokrúhlenia pred výpočtom logaritmu. Pri porovnaní oboch scenárov bez pôvodného limitu by bol rozdiel 2,51 dB. Hodnota 4,77 dB nad cieľom 51 dB je rozdiel modelu a požiadavky, nie overená rezerva na montážne chyby. Výpočet je v lib/h200-acoustic-calculation.ts.

## 6. Citlivosť a prenos na hotové miestnosti

Pri návrhovej hustote omietky 1 300–1 800 kg/m³ vychádza f₀ približne 64,59–64,07 Hz a Rw,odhad približne 55,70–55,77 dB, pri nezmenenom vstupnom Rw základu 35 dB. Ide iba o citlivosť hmotnostného vstupu, nie o interval spoľahlivosti. Iná omietka môže zmeniť aj Rw samotného základu.

Výpočet nezahŕňa všetky rezonancie dutej tehly, tuhosť spojov, netesnosti ani bočný prenos. R′w na stavbe ovplyvňujú podlahy, stropy, bočné steny, prestupy a cesta cez dvere a chodbu. Hluk sprchy alebo potrubí môže obsahovať konštrukčný prenos. Splnenie cieľa preto treba potvrdiť posúdením presnej zostavy a napojení, prípadne meraním.

## 7. Geometria, napojenia a montáž

Stena: X 22 783–27 541 mm, Y 6 364,5–6 552 mm, výška 3 125 mm. Kúpeľňové líce sa posúva o 50 mm k ulici, pracovňové o 37,5 mm k ulici. Kúpeľňa získava 0,2379 m²; pracovňa stráca 0,1762125 m². Sprcha a fasádne okná zostávajú na mieste; tabuľa v pracovni a kúpeľňový radiátor sledujú svoje nové líce.

Dvere pracovne: otvor Y 5 421–6 322 mm; k H200 zostáva 42,5 mm = 37,5 mm pevné dorovnanie + 5 mm spoj J2. Dvere kúpeľne: otvor Y 6 701,5–7 501,5 mm, os Y 7 101,5 mm; k H200 zostáva 149,5 mm. Polohy otvorov ani krídel sa touto revíziou nemenia. Šírku obložky pracovne treba potvrdiť pre 42,5 mm, bez premostenia predsteny.

Vata 40 mm zaberá približne 89 % dutiny; technický podklad požaduje najmenej 70 % a vhodný odpor proti prúdeniu 5–50 kPa·s/m². Zachovať pružné Direktschwingabhänger, vzduchotesné škáry a obvodové podtesnenie. Jedna doska nemá prekrytie škár druhou vrstvou; škáry a podopretie hrán sa vyhotovia podľa potvrdeného jednovrstvového systému. [^4]

J1 pri čele jedinej dosky zostáva 5 mm, s princípom Trenn-Fix a Uniflott. J2 pod jej lícom má 5 mm mäkkého oddelenia s akustickým tmelom, bez tvrdého sadrového alebo maltového mosta. D1 je projektový detail, nie skúška celej steny.

[Detail D1 · H200 pri dverách do chodby](office-acoustic-wall-junction.md). Pevné ostenie, podtesnený obvodový profil a dve nadväzujúce škáry J1/J2. Zväčšený výkres zachytáva aj kontakt krátkeho dorovnania s vonkajšou doskou. Webový výkres: /docs/akustika-h200/napojenie.

## 8. Výsledok revízie

Aktívna AK-03 / H200 má jednu Silentboard, 187,5 mm a kúpeľňové líce zarovnané s chodbou. Predbežný modelový výsledok je približne 56 dB; nameraná hodnota presnej kombinácie Leier a Knauf ani R′w hotových miestností nie sú k dispozícii.

Záloha 274 mm a porovnávané alternatívy zostávajú historickými podkladmi. Hodnoty tejto revízie sa neprenášajú na AK-01/AK-02. Táto správa nahrádza aktívne údaje R2; statické overenie 100 mm muriva, kotvenia a montážnych detailov je samostatnou realizačnou úlohou.

## Použitá literatúra

Odkazy overené pri spracovaní 13.–14. 9. 2026.

[^1]: Mahn, J.; Skoda, S.; Cunha, I. Canadian Acoustics, 52(3), 8. 9. 2024. NRC Canada; recenzovaný článok. [The Transmission Loss of Double Stud Walls with Layers of Gypsum Board Installed inside the Wall Cavity](https://nrc-publications.canada.ca/eng/view/object/?id=768bf32f-8313-435f-ab85-8680efba61b2). [Záznam u vydavateľa](https://jcaa.caa-aca.ca/index.php/jcaa/article/view/3976). Citovaný mechanizmus a číselný výsledok sú zo zverejneného abstraktu NRC. Skúšané oceľové priečky sa od H200 líšia.
[^2]: Leier Slovensko Zverejnený technický list, závod Devecser, jedna strana. [LeierPLAN 10 N+F — technický list](https://www.leier.sk/wp-content/uploads/2025/07/Technicky-list-LP10-NF.pdf). Výrobkový podklad pre základné murivo a obojstranné omietky.
[^3]: Knauf Vydanie 09/2026, živý odkaz overený 16. 9. 2026. [W61_DSS.de — Vorsatzschalen](https://media.knauf.com/a/EDKwYfTuyWRUkKKKihg9E7). Systémový podklad. Konkrétne jedno opláštenie pôvodnou Silentboard a kotvenie na LeierPLAN 10 vyžadujú potvrdenie dodávateľa.
[^4]: Knauf / Trockenbau Unlimited Technický portál výrobcu, výpočtové príklady a pružné uchytenie. [W623 — Vorsatzschale](https://trockenbau-unlimited.de/schallschutz/w623-vorsatzschale). Príklad jednej Silentboard 12,5 mm a hmotnosti 17,5 kg/m²; jeho iný podklad a 40 mm dutina nie sú skúškou tejto 45 mm zostavy.
[^5]: Bundesverband der Deutschen Ziegelindustrie Vydanie 2022; tlačené s. 57 a 61–62. [Baulicher Schallschutz mit Ziegeln](https://ziegel.de/sites/default/files/2022-04/Ziegel-Broschuere_Baulicher_Schallschutz_2022_web_0.pdf). Metodika predikcie predsadených vrstiev a upozornenie na koeficient rezonančnej frekvencie.
