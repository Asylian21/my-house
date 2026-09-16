# Register vstupov a rozporov — 15. 9. 2026

**OVERENÉ** znamená overený obsah konkrétneho zdroja alebo zhodu geometrie modelu; samo osebe to neznamená zameranie stavby. **DEKLAROVANÉ** znamená údaj investora. **PREDPOKLAD** je vstup podmieneného výpočtu. **CHÝBA** označuje údaj potrebný na uzavretie posúdenia. Čísla strán nižšie sú fyzické stránky PDF, pokiaľ sa neuvádza inak.

## 1. Rozhodujúca hierarchia a aktuálny stav

**Výslovný pokyn počítať so zhutnenou zeminou, 16. 9. 2026:** hlavný výpočet 100 mm dosky a štyroch rebier teraz obsahuje súvislú pružnú podporu zásypom. Hodnoty ks = 5 / 10 / 20 / 50 MN/m³ sú PREDPOKLADY citlivosti, nie OVERENÉ vlastnosti zeminy. Steny sa môžu podopierať doskou so zeminou aj mimo rebier. Staršie voľné polia zostávajú iba doplnkovými scenármi. Aktuálne výsledky: `results/slab-100-ground-support.json`, `results/four-rib-ground-support.json`; metóda a primárne zdroje: `ground-support-sources.md`. Samostatné lokálne modely sa nevydávajú za spojené posúdenie celého domu.

**Nové konštrukčné zadanie 16. 9. 2026:** používateľ potvrdil dosku 100 mm C16/20 betonovanú spolu s rebrami výšky 400 mm celkom (300 mm pod doskou), miestny zhutnený zásyp hlina/piesok a 150 mm zarážku pri hornom obvode s uvedeným rozmerom 300 mm. Výstuž, skúšky zeminy a úplný profil zarážky nie sú určené. Presný záznam: `user-100mm-clarification.md`. Samostatný report-100mm.pdf obsahuje nové podmienené výpočty; nevyhlasuje bezpečnosť domu ani neprenáša výsledky starej 17-trásovej štúdie na štyri rebrá.

**Oprava výkladu požiadavky podľa červených šípok 9:41:18, 16. 9. 2026:** používateľ upresnil, že chce kóty od modrého obvodu k červeným rebrám a medzi rebrami priamo v pôdoryse. Predošlé čítanie výrezu ako požiadavky na odstupy modrá–sivá bolo nesprávne. Aktuálny list ZK-03 používa líca rebier šírky 350 mm: 8 478 / 5 248,5 / 6 122 / 173,5 / 7 173,5 mm v X a 7 687 / 7 973 / 2 675 mm v Y. Kóty k L-boku sú priemety na jeho X-polohu, nie dôkaz napojenia. Modré čiary zostávajú približnými modelovými referenciami. Geometria ani výpočet sa nemenia. Zdroj a odtlačok: `client-direct-rib-dimensions-20260916.json`.

**PREKONANÝ VÝKLAD POŽIADAVKY - výrez 9:26:58, 16. 9. 2026:** požadované sú presné odstupy modrej obvodovej čiary od sivej prerušovanej osi. List ZK-03 uvádza šesť kolmých modelových rozdielov: ľavá 354 mm, uličná 354 mm, pravá 349 mm, zadná za terasou 350 mm, vodorovný návrat pri dvore 351 mm, vnútorný zvislý bok krídla 353 mm. Na priloženom výreze je teda zľava 354 mm a zhora 351 mm. Nejde o nové zameranie betónu ani zmenu polohy rebier. Kópia a SHA-256: `client-line-offset-request-20260916.json`.

**Najnovšie spresnenie - obrázok8:56 a potvrdená odpoveď16.9.2026:** betón vedie približne stredom obvodových čiar; garážový koniec JE predĺžený800mm oproti situácii20,80m. Pre koordináciu sa používa obrys C/B/B21,60m ako približná osová referencia, nie ako vonkajšie líce betónu. Presné osadenie či šírky sa tým nezamerali. Nový zdroj `client-perimeter-centerlines-20260916.png`, odtlačok a potvrdenia v `client-agreed-layout.json`. Staršie kóty z technického doplnenia nižšie sú **PREKONANÉ**.

Zdrojové kóty obrázka20 800/19 050/7 000/10 840/13 750/8 200mm sa pri pravouhlomL neuzatvárajú: rozdielX50mm/Y10mm. Po pripočítaní800mm je celkovášírka21 600 a zdrojový návrat14 550mm; aktuálny model má21 600/19 035/7 000/10 835/14 600/8 200mm. Modelové hodnoty sa nepodsúvajú ako overené zameranie.

Pôvodné osy horného pásu ležia voči takto interpretovaným spodným osiam približne349-354mm dovnútra. Starý predpoklad súososti nemožno prevziať. Červené body sa zachovali ako modelové; konce a podopretie sa musia navrhnúť nanovo. R2Y10862 je338mm prednovýmLrohomY11200. Nie je tým vytvorený preukázaný spoj na obvod. Starý výpočet a jeho `geometry.json` sa nemenili; nová koordinačná geometria je osobitná.

**PREKONANÁ REVÍZIA – technické kóty pred spresnením obvodových čiar, 16. 9. 2026:** používateľ žiada šírky a polohy od krajov. Listy `drawings/technical/agreed-ribs-technical.pdf` určujú presné modelové vzdialenosti od vonkajších líc navrhovaného horného350mmobvodu A-D. Pracovná šírka350mm je prevzatá z výsledkov starej štúdie preR1-R7; nie je novým potvrdením jej dostatočnosti pre štyri rebrá. Polohy dnešných líc a súososť chýbajú. Prepočet od existujúceho pásu380/400mm je uvedený len ako podmienená geometria pri súososti. Tieto líca sa nezamieňajú s obálkou ETICS ani zameranou stavbou. Presné údaje sú v `results/agreed-ribs-dimensions.json`; pôvodné výpočtové vstupy sa nezmenili.

**Doplnenie 16. 9. 2026:** investor označil na obrázku modrou celý už vyliaty spodný L-obvod vrátane lodžie a terasy, červenou štyri dohodnuté budúce rebrá. Zľava doprava ide o R7 a R1; v pravom krídle od ulice dozadu o R2 a R4. Zdroj `client-foundation-markup-20260916.png`, výklad a SHA-256 v `client-agreed-layout.json`. Toto polohové zadanie má prednosť pred staršími kandidátnymi kresbami; nezadáva prierez, výstuž ani spôsob podopretia. R1 a R2 spája približne0,702m obvodového úseku. Rozdiel modelových Y-osí R2 a obvodu13mm sa z ručného obrázka neoveruje. Presné súradnice ostávajú modelové. Výsledky pre17trás sa na štyri dohodnuté rebrá neprenášajú.

1. Najnovšie zadanie investora a následné potvrdenie 15. 9. 2026: **vybetónované sú len spodné obvodové pásy; horné debnenie ani doska NIE SÚ vybetónované.** Spodný betón C16/20, šírka približne 380–400 mm a výška betónu približne 600 mm sú **DEKLAROVANÉ**, nie geodeticky zamerané. Táto informácia výslovne nahrádza staršie tvrdenie o vyliatej doske v `docs/active-design.md` a `docs/construction-foundation-axon.md`. Pôvodné súbory sa nemenili.
2. Rozmer približne 350 mm pri hornom debnení nemá v aktuálnom zadaní overený smer. Staršie `docs/construction-drawings.md` obsahujú zámer 350 × 600 mm. Nový report môže také rozmery **navrhnúť**, nesmie ich označiť za zameraný aktuálny stav.
3. Geometria C/B/B je záväzný **projektový/modelový** stav. Neexistuje použiteľný súbor súradníc všetkých skutočných základových líc, nivelácie, výstuže ani základovej škáry. Žiadny výkres v tejto analýze preto nemôže byť nazvaný zameraním vyhotovenia.
4. História dosky a pôvodné výkresy nie sú dôkazom existujúcich vnútorných pásov. Tie sa vo výpočte musia viesť ako nové alebo osobitne overené.

## 2. Register rozhodujúcich dokumentov

| ID | Súbor a strana | Čo je overené v zdroji | Použitie / dôkazová úroveň |
|---|---|---|---|
| U-01 | Zadanie `pasted-text.txt`, priložené k tejto úlohe; následné potvrdenie investora | C16/20; spodné pásy cca 380–400 × 600 mm; horná časť aj doska ešte nevyliate | DEKLAROVANÉ, aktuálny stav; rozmer350 mm nejednoznačný |
| P-01 | `arch-docs/projektova dokumentace/D_Vykresova dokumentace/D2_Statika/D.2.001-00 - TZ + SV .pdf`, s.3–4 | Pôvodné obvodové pásy800 mm, vnútorné600 mm; výška≥500 mm; základová škára≥1.20 m pod upraveným terénom; patky1100×1600 a1850×1100; doska150 mm | OVERENÉ ako pôvodný projekt; nie skutočné rozmery; projekt vyžaduje prevzatie geotechnikom |
| P-02 | Tá istá statika, s.4 | Vence C25/30XC1, pásy a doska C20/25XC2, prostý betón C16/20X0; pôvodná KARI8/150/150 dole, horná pri pásoch | OVERENÉ pôvodný návrh, **nepreberá sa** do nového C16/20 |
| P-03 | Tá istá statika, s.39–43 | Jediný kontrolný pás: B0.80 m,t0.50 m,D1.20 m; NEd68kN/m, Nser48.57kN/m; nulové M,H; qEd123.47kPa protiRd150kPa; sadanie3.4mm | OVERENÉ výsledky pôvodného modelu; nevzťahujú sa na dnešný0.38–0.40m pás ani sústredené reakcie |
| P-04 | Tá istá statika, s.40–41 | F5 tuhá, φ′21°,c′12kPa,γ20kN/m³,Eoed8.5MPa; Rd210/1.4=150kPa | **PREDPOKLAD pôvodného projektu**, nie výsledok terénnych skúšok domu |
| P-05 | Tá istá statika, s.10–12 | Strešné vrstvy1.18kN/m²; sneh základ1.0kPa; raz37°/μ0.61, potom30°/μ0.80; vietor25m/s | OVERENÉ ako zdroj; vnútorné rozpory nižšie; lokálne účinky aktuálneho L-domu neuzavreté |
| P-06 | `…/D1_ASR/D1.1.001_Pudorys zakladu.pdf`, s.1, D1.1.001,28.4.2026 | Kótovaný obrys pôvodných základov21900×19385; obvod800 mm, vnútorné600 mm, ostrovné patky a prestupy | OVERENÉ pôvodný výkres; líca širokých pätiek sa nemajú zamieňať s21600×19035 obálkou domu |
| P-07 | `…/D1_ASR/D1.1.005_Rez A-A.pdf`, s.1 | Podlaha±0.000, upravený terén−0.150; lokálne základové výšky−1.150/−0.650,−0.900/−0.400; doska−0.400 až−0.250 | OVERENÉ pôvodný rez; nie dnešná nivelácia. Rozpor s min1.20m podU.T. |
| P-08 | `…/D1_ASR/D1.1.007_Skladby konstrukci.pdf`, s.2 | F10 dve vrstvy betónu150+100mmC25/30XC2 s izoláciou medzi; EPS160mm,poter50mm,povrch15mm,vykurovacia doska25mm,kamenivo150mm | OVERENÉ pôvodná skladba; nezhoduje sa so statikou (jedna150mmC20/25) a nepreberá sa ako hotové zadanie |
| P-09 | `…/D1_ASR/D1.1.003_Pudorys stropu a krovu.pdf`, s.1; statika s.4 | Krokvy120/200; pozednice160/160; oceľová hrebeňová väznica2×U240; rámyHEA160; drevené stĺpiky120/120 na trám nad nosnými stenami | OVERENÉ pôvodný systém; dnešné nosné steny a nové nenosnéSA30/H200 nezodpovedajú pôvodnej podporovej schéme |
| P-10 | `…/D1_ASR/D1.1.002_Pudorys 1.NP.pdf`, s.1; `…/D1.1.01_Technicka zprava.pdf` | Pôvodná dispozícia a architektúra pred klientskymi zmenami | OVERENÉ archív, nie záväzná nová dispozícia |
| G-01 | `arch-docs/projektova dokumentace/E_Dokladova cast/Hydrogeologický posudek 2.etapa.pdf`, s.2,5–8 | ENVI-AQUA, máj2025; prieskum z3.5.2022 pre vsakovanie; regionálny profil a voda | OVERENÉ dokument, **nie základový geotechnický prieskum domu** |
| M-01 | `docs/active-design.md`; `lib/floor-plan-concept.ts`; `lib/twin-active-house.ts` | Hlavný model C/B/B, architektonický obrys a nosné/nenosné roly | OVERENÉ model; zachovaný bez zásahu |
| M-02 | `docs/construction-foundation-axon.md`; `output/pdf/construction-cbb/model-snapshot.json` | L-obrys, predbežné osy horného obvodu, kandidátneR1–R7 | OVERENÉ modelové súradnice; prierezy, podopretie a existujúca poloha nie sú overené |
| M-03 | `docs/construction-roof-heating-basis.md`; `docs/construction-structural-basis.md` | Drevený skladovací strop, žiadny betónový strop/nadbetonávka; povala mimo1.03; katedrála; strecha bez architektonického presahu | DEKLAROVANÝ zámer + OVERENÁ geometria. Konečné skladovanie, nosníky, reakcie a kotvenie **CHÝBAJÚ** |
| M-04 | `lib/acoustic-walls.ts`; `docs/acoustic-walls.md`; `docs/office-acoustic-wall-thinner-options.md` | SA30 dva100mmplášte+100mmvata; nové15mmomietky; H200 skladba; výška modelu3.125m | OVERENÉ modelové skladby; výrobky, skutočné výšky a kompletné hmotnosti na stavbe nepotvrdené |
| M-05 | `lib/technical-design.ts`,HEATING_LAYOUTS.B; `lib/twin-living-layouts.ts`,FIREPLACE_STOVE_B; `lib/twin-interior.ts`,KITCHEN_ISLAND | AKU800l,kotol15kW+zásobník180kgpeliet; pozície kachlí a ostrova | OVERENÉ plánované pozície/kapacity; prevádzkové hmotnosti, kotvenie, nohy a tlak do podlahy **CHÝBAJÚ** |
| F-01 až03 | `/Users/davidzita/Downloads/IMG_7530.HEIC`, `IMG_7292.HEIC`, `IMG_7299.HEIC` | Fotografie aktuálne priložené k zadaniu | Vizuálny doklad detailov; bez kalibrovanej mierky nie zameranie. Interpretácia v samostatnom fotozázname analýzy |

## 3. Zistenia z pôvodnej statiky a rozporov

- **Šírka900 mm sa v rozhodujúcom pôvodnom návrhu nepotvrdila.** Pôvodná statika a výkres uvádzajú800mmobvod/600mmvnútri. Pre800mm pôvodný výpočet používa NEd68kN/m a predpoklad Rd150kPa; výsledok so základom a nadložím je123.47kPa (82.31%). Samotné68/0.40=170kPa už prekročí150kPa ešte pred vlastnou tiažou nového základu. To je kontrola pôvodného modelu, nie automatický dôkaz nevyhovenia každého nového návrhu.
- **Hĺbka1.20m** je v s.3 minimálna hĺbka pod konečným terénom a zároveň v s.40 vstup geotechnického modelu. Dokument nepreukazuje, že ju určil prieskum konkrétneho domu. Pôvodný rez pri U.T.−0.150 a škáre−1.150 dáva lokálne1.00m; rozpor nemožno vyriešiť prevzatím jedného čísla.
- **Zaťaženie strechou:** s.10 uvádza1.18kN/m² vrstiev (PV0.25,plech0.05,fólia0.02,laty0.15,izolácia0.13,bednenie0.33,podhľad0.25), s.39 používa3.93kN/m²×4m bez vysvetlenia. Nie je doložený prevod1.18→3.93 ani kompletná stopa všetkých bodových reakcií do základov. Zaťaženie strešných vrstiev musí rozlíšiť plochu po sklone a pôdorysný priemet.
- **Sneh:** s.10 má37° aμ0.61; vlastné posúdenie krokvy na s.10–11 má30° aμ0.80. Oba používajú sk1.0kPa. Aktuálny model má sklony30.70618° a34.82689°; základnú hodnotu a asymetrické/naviate prípady treba uzavrieť podľa aktuálnej českej národnej prílohy a geometrie.
- **Vietor:** s.11 používa vref25m/s,qref0.39kPa,cp+0.40/−0.50,ce1.05,b0.90m →+0.15/−0.18kN/m. Tieto zjednodušené staré koeficienty nie sú kontrolou lokálnych okrajov, úžľabia, otvorenej terasy, vnútorného tlaku ani aktuálnej novej nosnej sústavy. Pôvodný základ bol posúdený sH=0, nemožno z neho odvodiť dnešné kotvenie.
- **Doska a betón:** statika s.4 opisuje150mmKARI8/150 aC20/25XC2; skladbaF10 má150+100mmC25/30XC2. Vstup investoraC16/20 zostáva záväzný nový scenár. Žiadna historická vrstva sa nemá započítať ako existujúca.
- **Murivo:** pôvodná architektúra a rez opisujú500mmPorotherm50T; statika s.4 Porotherm24Profi a veniec300mm; dnešný model používa nominálne300mmobvod+ETICS a upravené vnútorné steny. Vlastnú tiaž je nutné zostaviť z konkrétneho nového výrobku a skutočných otvorov. Renderingové330mmlíce muriva nie je ďalšia normatívna hrúbka jadra.

## 4. Hydrogeologický podklad: čo hovorí a čo nepreukazuje

Hydrogeologický posudok je sken; rozhodujúce strany5–8 boli vizuálne prečítané. Jeho pôvodný účel je odvodnenie a vsakovanie pre rozvojovú lokalituZ7,2.etapu. Dňa3.5.2022 vznikla skúšobná jama3.0×1.0m,hlboká1.9m.

| Hĺbka pod vtedajším terénom | Popis podľa PDF s.6 (tlačená4) |
|---|---|
| 0–1.0m | piesčitá hlina,tmavohnedá/čierna, vo vrchnej vrstve organické zvyšky |
| 1.0–1.2m | ílovitá hlina,sivá až sivožltá |
| 1.2–1.5m | piesok žltosivý až oranžový,zavlhnutý,svalúnmi do10cm |
| 1.5–1.9m | vápenitý piesok,pevný,sivooranžový |

Voda bola narazená v1.50m, ustálená v1.40m. Report s.5 uvádza regionálne kvartérnu vodu1.5–1.9m a zvýšenú mineralizáciu hlbších neogénnych vôd. **Nie je doložené chemické zatriedenie XA ani návrhová maximálna hladina pod týmto domom.**

Mapovo odčítaná poloha sondy je X1202288.20,Y606859.12 v bežnej kladnej konvenciiS-JTSK. Po prehodení a znamienkach do konvencie modelu je sonda približne278.2m od jeho lokálneho georeferencovaného počiatku; ide iba o orientačný prevod, nie vytýčenie sondy. Nemožno ju priradiť priamo pod dom. Profil preto podporuje požiadavku miestnych sond a varuje pred organickou vrchnou zeminou, ale nepotvrdzujeφ′,c′,Eoed,Rd ani mrazuvzdornú hĺbku stavby.

## 5. Aktuálny model a hmotnosti, ktoré sa nesmú stratiť

`geometry.json` reprodukovateľne obsahuje:

- celý L-obrys `(6.440,3.000)–(28.040,3.000)–(28.040,22.035)–(21.040,22.035)–(21.040,11.200)–(6.440,11.200)`, modelovú plochu252.965m²;
- oddelenú uzavretú obálku, ktorá končí pri teraseY19.535 a pri lodžiiY9.247; **nie je to menší rozsah existujúcich zameraných pásov**;
- všetkých37aktuálnych vnútorných úsekov srect/centerline/hrúbkou/modelovou nosnou rolou; označenieLOAD_BEARING je modelový zámer, nie statická certifikácia;
- sedem predchádzajúcich kandidátnych trásR1–R7; ich podopretie a prierezy boli pôvodne neurčené;
- skutočné medzery pri SA30: obidve steny3.048m, celkom6.096m; voľná chodba1.099m. Dve murované osiX14.993 a15.193 treba zaťažiť osobitne;
- SA30 bez vaty/obkladov:2×73+2×0.015×1800=200kg/m²; pri3.125m je6.13125kN/m. Predchádzajúcich4.4758kN/m patrilo len neomietnutému murivu;
- H200 pred roštom,vatou aobkladom:73+54+35=162kg/m²; pri3.125m je4.9663125kN/m a dĺžka4.758m. Hmotnosti omietky a opláštenia sú stále návrhové predpoklady, nie vážená dodávka;
- AKU800 na(25.410,10.123), už voda sama7.848kN; prirátať nádrž,armatúry a skutočné nohy;
- kotol vrátane zásobníka180kgpeliet v obálkeX25.112–26.408,Y7.851–9.039; prevádzková hmotnosť a kontakty neoverené;
- kachleB na(21.853,18.620) s priemerom0.510m; kovový dymovod nesmie automaticky dostať hmotnosť pôvodného murovaného komína;
- kuchynský ostrov2640×920mm a skutočné rozloženie jeho nôh; plná vaňa, práčka/sušička, regály, vozidlo a lokálne stavebné balíky sa majú zahrnúť ako miestne účinky.

**Kontrola aktuálnosti:** kľúčové hashy pôdorysu,aktívneho domu,strechy,interiéru atechnickej miestnosti súhlasia so snapshotom. Štyri pomocné/akustické zdroje sa od exportu zmenili; najnovšie15mmomietkySA30 sa preto preberajú priamo zaktuálneho `lib/acoustic-walls.ts`, nie zo starého hmotnostného riadka snapshotu. Register hashov je vgeometry.json. Výšku3.125m všetkých bežných stien používa analýza ako konzervatívnu modelovú obálku; skutočnú výšku založenia a preklady nad dverami treba uzavrieť.

## 6. Chýbajúce údaje pre definitívny výsledok

1. Zameranie celého obvodu: XY oboch líc, výšky hornej a dolnej hrany, šírky aj lokálne zúženia, výšky konečného terénu; kolmosť a excentricita jadier na skutočných pásoch.
2. Dodacie listy C16/20, vek/betonážny postup, výstuž a kĺbovanie existujúcich úsekov, charakter povrchu a prípadných trhlín; podľa nálezu jadrové skúšky, nie iba sklerometer.
3. Miestny geotechnický profil, únosnosť aj deformácie, pôvodná zemina pod navážkou, hladina a chémia vody, mráz a vlhkostné objemové zmeny.
4. Konečná strešná a drevená stropná sústava s tabuľkou zvislých/vodorovných/vztlakových reakcií vo všetkých podperách; potvrdené skladovacie aj lokálne zaťaženie povaly.
5. Výrobky obvodových a vnútorných stien, povrchy a hmotnosti všetkých ťažkých zariadení vrátane základových plôch nôh.
6. Typ a objem zásypu, pôvodné a cieľové výšky, vhodnosť materiálu, overený technologický postup a preberacie skúšky; chýbajúce výšky nesmú byť vo výkaze nahradené skrytou nulou.
7. Zatriedenie prostredia a preukázateľná ochrana C16/20 pre dlhú životnosť; hydro/radónová kontinuita pod stenami, pri pracovných škárach a prestupoch.
