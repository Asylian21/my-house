# 100 mm doska nad štyrmi rebrami – predbežný screening

**Revízia AK-01/AK-02, 16. 9. 2026:** aktuálne je SM30, jedna 300 mm obvodová tehla so zachovaným účelom odhlučnenia. Táto štúdia používa zmrazené pôvodné zaťaženia SA30; výsledky pre stenové zaťaženia a R7 sa nepovažujú za prepočet SM30. Konkrétny výrobok a nový prepočet zostávajú otvorené. Samostatné geometrické kóty a výpočty bez stenového zaťaženia týmto nie sú prerátané. Pozri [záznam revízie](/Users/davidzita/www/dom/foundation-analysis/inputs/wall-revision-sm30-20260916.md).

**Nie je to schválenie statiky domu.** Hrúbka 100 mm, spoločná betonáž dosky/rebier a miestny zhutnený zásyp sú deklarované. Výstuž nie je zadaná; nižšie uvedené siete sú iba skúšobné možnosti.

## Model a zdroje vstupov

C16/20; B500 bez doloženej triedy ťažnosti; b = 1000 mm, h = 100 mm, cnom = 35 mm. fcd = 0,85 × 16/1,5 = 9,067 MPa, fyd = 500/1,15 = 434,783 MPa; Ecm = 28 600 MPa, Es = 200 000 MPa, fctm = 1,9 MPa. Národné parametre sú výslovné predpoklady; české NA ani expozícia/100-ročná trvanlivosť tým nie sú overené.

Stále plošné zaťaženie je 2,5 kPa vlastná doska + 2,0 kPa predpoklad vrstiev; obytné qk = 2,0 kPa. qEd = 1,35 × 4,5 + 1,5 × 2 = **9,075 kPa**. Vrstva 2,0 kPa zachováva porovnateľnosť so starším výpočtom; skutočná skladba chýba.

Rebrá R7, R1, R2, R4: deklarovaná celková výška 400 mm vrátane dosky, teda 300 mm pod doskou; šírka 350 mm je pracovný predpoklad. Ich výstuž, skutočná zemná podpora, reakcie a uloženie nie sú týmto skriptom posúdené. Zarážka 150 mm nie je automaticky preukázané uloženie alebo zakotvenie.

Líniové hmotnosti sú načítané priamo z `results/wall-loads.csv`. Ide o predpoklady výrobku, skladby a výšky pôvodnej štúdie, nie zamerané hmotnosti. Hodnota 4,05 kN/m nemala doložený zdroj a nepoužíva sa. Ťažké nosné steny tu zahŕňajú iba vlastnú hmotnosť, bez strechy a povaly.

| Prípad | Gk steny kN/m | Identifikátor zdroja |
|---|---:|---|
| floor_only | 0.0000 | bez steny |
| wall_H200 | 5.2116 | IW-STUDY-NORTH |
| wall_SA30 | 6.2539 | C-OPEN-HALL-S |
| wall_typical_partition | 6.9375 | IW-BATH-105-SOUTH-E |
| wall_heaviest_selfweight | 12.9750 | C-GARAGE-SPINE-N |

V každom 1 m páse sa stena kolmá na smer premostenia zaťažuje samostatnou silou P = gsteny × 1 m uprostred rozpätia. Nie je rozpočítaná do plošného zaťaženia celého domu. To nie je posúdenie skutočnej polohy každej steny; rovnobežná stena, otvory a bodové reakcie potrebujú iný model.

## Výpočtové vzťahy a obmedzenia

Skúša sa jedna spodná obojsmerná sieť: pri vonkajšom drôte d = h − c − φ/2; pri krížnom vnútornom drôte d = h − c − 3φ/2. Siete sa preto neposudzujú s rovnakou účinnou výškou oboch smerov.

ULS: MEd = qEd L²/8 + Pd L/4. Stena je stála, Pd = 1,35 gsteny. Šmyk má samostatne centrálnu reakciu qL/2 + P/2 a konzervatívnu pohybovú hornú hranicu qL/2 + P, bez redukcie pri podpore. Prierez rieši rovnováhu 0,8 b x fcd = As min[fyd; Es εcu(d−x)/x], εcu = 0,0035; MRd = T(d−0,4x). Oceľ sa bez kontroly kompatibility nepovažuje vždy za vytečenú.

VRdc = max[0,12 k(100ρ fck)^(1/3); 0,035 k^(3/2)√fck] bd, k ≤ 2, ρ ≤ 0,02. Platnosť potrebuje zakotvenú ťahovú výstuž a správne podopretie, ktoré zatiaľ chýbajú. Minimálna ohybová výstuž As,min = max[0,26 fctm/fyk; 0,0013] bd.

**Ťažnosť:** pre tento konzervatívny screening sa požaduje aj x/d ≤ 0,45. Nie je prezentované ako univerzálna hranica každého jednoduchého prierezu bez redistribúcie; EC2 viaže zodpovedajúce obmedzenia na spôsob analýzy, redistribúciu a rotačnú kapacitu. Ø8/100 prekračuje toto prijaté kritérium v oboch smeroch (0,494 / 0,568), preto nie je označená za vyhovujúci návrh ani pri malej MEd. Pomocný MRd pri xlim = 0,45d je iba porovnanie tlakového bloku: nezmení skutočné x/d už navrhnutého množstva ocele.

SLS sa počíta z úplne popraskaného prierezu: n=Es/Ec; x=[√((nAs)²+2bnAsd)−nAs]/b; Icr=bx³/3+nAs(d−x)²; σs=M/[As(d−x/3)]. Trhliny podľa EC2 §7.3.4 s kt=0,4, k1=0,8, k2=0,5, k3=3,4, k4=0,425 a ρeff; limit wk=0,30 mm je porovnávací predpoklad. QP je G+0,3Q, garáž G+0,6P; ψ2 vyžaduje potvrdenie podľa konkrétneho užívania a českej NA.

Dlhodobá časť používa Ec,eff=Ecm/(1+φ), φ=1,5/2,5/3,5; prechodný prírastok krátkodobú tuhosť. δ=5qL⁴/(384EI)+PL³/(48EI), porovnávací limit L/250. Ak elastický prediktor prekročí fy=500 MPa, charakteristický tlak 0,6fck alebo kvázistály tlak 0,45fck, príslušné trhliny/priehyby sa **nevydávajú za platný lineárny výsledok**; v JSON je null a dôvod. Potrebný nelineárny výpočet nie je urobený. Veľká vypočítaná deformácia z neplatného modelu sa teda neprezentuje ako reálna predpoveď.

Zmrašťovanie, teploty, krútenie a záporné ohyby nie sú preukázané. Jedna sieť pri spodku sa nepovažuje za navrhnutú hornú výstuž. Lokálne zásypové dutiny 1 / 1,5 / 2 m sú citlivostné prípady, nie dôkaz ich pravdepodobnosti ani automatická povinnosť pre každý pozemok.

## Prierezy – obe výšky krížiacich sa drôtov

| Sieť / smer | d mm | As mm²/m | MRd kNm/m | x/d | VRdc kN/m | x/d ≤ 0,45 |
|---|---:|---:|---:|---:|---:|---|
| phi6_s150 / vonkajší | 62 | 188.5 | 4.711 | 0.182 | 25.21 | áno |
| phi6_s150 / vnútorný | 56 | 188.5 | 4.219 | 0.202 | 23.56 | áno |
| phi8_s150 / vonkajší | 61 | 335.1 | 7.717 | 0.329 | 30.21 | áno |
| phi8_s150 / vnútorný | 53 | 335.1 | 6.551 | 0.379 | 27.51 | áno |
| phi8_s100 / vonkajší | 61 | 502.7 | 10.697 | 0.494 | 34.59 | NIE |
| phi8_s100 / vnútorný | 53 | 502.7 | 8.949 | 0.568 | 31.49 | NIE |

Dve plné obojsmerné siete hore+dole sa pri cnom=35 mm nezmestia s požadovanou medzerou aspoň 21 mm: Ø6 má medzeru 6 mm, Ø8 zápornú medzeru −2 mm. Jedna spodná sieť sa geometricky zmestí; tým nie sú vyriešené presahy, podložky, tolerancie a krytie v uzloch.

## Lokálna dutina – slabší smer siete

Nižšie sú platné QP trhliny a dlhodobý priehyb pri φ=2,5. „—“ znamená prekročený rozsah lineárneho modelu, nie nulový výsledok. Označenie „číselne áno“ sa týka iba uvedených pozitívnych lokálnych kontrol.

| Sieť | L m | Zaťaženie | MEd kNm/m | wk QP mm | δ mm | Pozitívny screening |
|---|---:|---|---:|---:|---:|---|
| phi6_s150 | 1.0 | floor_only | 1.13 | 0.058 | 1.15 | číselne áno |
| phi6_s150 | 1.0 | wall_typical_partition | 3.48 | 0.217 | 3.21 | číselne áno |
| phi6_s150 | 1.0 | wall_heaviest_selfweight | 5.51 | — | — | NEPREUKÁZANÉ / NIE |
| phi6_s150 | 1.5 | floor_only | 2.55 | 0.131 | 5.82 | číselne áno |
| phi6_s150 | 1.5 | wall_typical_partition | 6.06 | — | — | NEPREUKÁZANÉ / NIE |
| phi6_s150 | 1.5 | wall_heaviest_selfweight | 9.12 | — | — | NEPREUKÁZANÉ / NIE |
| phi6_s150 | 2.0 | floor_only | 4.54 | 0.233 | 18.40 | NEPREUKÁZANÉ / NIE |
| phi6_s150 | 2.0 | wall_typical_partition | 9.22 | — | — | NEPREUKÁZANÉ / NIE |
| phi6_s150 | 2.0 | wall_heaviest_selfweight | 13.30 | — | — | NEPREUKÁZANÉ / NIE |
| phi8_s150 | 1.0 | floor_only | 1.13 | 0.031 | 0.85 | číselne áno |
| phi8_s150 | 1.0 | wall_typical_partition | 3.48 | 0.117 | 2.40 | číselne áno |
| phi8_s150 | 1.0 | wall_heaviest_selfweight | 5.51 | — | — | NEPREUKÁZANÉ / NIE |
| phi8_s150 | 1.5 | floor_only | 2.55 | 0.071 | 4.32 | číselne áno |
| phi8_s150 | 1.5 | wall_typical_partition | 6.06 | — | — | NEPREUKÁZANÉ / NIE |
| phi8_s150 | 1.5 | wall_heaviest_selfweight | 9.12 | — | — | NEPREUKÁZANÉ / NIE |
| phi8_s150 | 2.0 | floor_only | 4.54 | 0.130 | 13.66 | NEPREUKÁZANÉ / NIE |
| phi8_s150 | 2.0 | wall_typical_partition | 9.22 | — | — | NEPREUKÁZANÉ / NIE |
| phi8_s150 | 2.0 | wall_heaviest_selfweight | 13.30 | — | — | NEPREUKÁZANÉ / NIE |
| phi8_s100 | 1.0 | floor_only | 1.13 | 0.018 | 0.65 | NEPREUKÁZANÉ / NIE |
| phi8_s100 | 1.0 | wall_typical_partition | 3.48 | 0.068 | 1.84 | NEPREUKÁZANÉ / NIE |
| phi8_s100 | 1.0 | wall_heaviest_selfweight | 5.51 | 0.140 | 2.88 | NEPREUKÁZANÉ / NIE |
| phi8_s100 | 1.5 | floor_only | 2.55 | 0.041 | 3.30 | NEPREUKÁZANÉ / NIE |
| phi8_s100 | 1.5 | wall_typical_partition | 6.06 | 0.147 | 7.32 | NEPREUKÁZANÉ / NIE |
| phi8_s100 | 1.5 | wall_heaviest_selfweight | 9.12 | — | — | NEPREUKÁZANÉ / NIE |
| phi8_s100 | 2.0 | floor_only | 4.54 | 0.076 | 10.42 | NEPREUKÁZANÉ / NIE |
| phi8_s100 | 2.0 | wall_typical_partition | 9.22 | — | — | NEPREUKÁZANÉ / NIE |
| phi8_s100 | 2.0 | wall_heaviest_selfweight | 13.30 | — | — | NEPREUKÁZANÉ / NIE |

## Výhodne idealizované celé medzery bez zemnej podpory

Pevné nepretvárajúce sa jednoduché podpory na dvoch okrajoch, iba podlahové zaťaženie bez stien. Používa sa už svetlá medzera, bez zväčšenia na účinné rozpätie; je to priaznivý predpoklad. Nie je to automatický návrhový stav straty všetkého zásypu ani dôkaz celého L pôdorysu.

| L m | MEd kNm/m, iba podlaha | Max MRd všetkých skúšaných smerov kNm/m | Záver |
|---|---:|---:|---|
| 5.2485 | 31.248 | 10.697 | nevyhovuje všetkým skúšobným sieťam |
| 6.6500 | 50.165 | 10.697 | nevyhovuje všetkým skúšobným sieťam |
| 7.9730 | 72.111 | 10.697 | nevyhovuje všetkým skúšobným sieťam |

5,2485 m je modelová svetlá medzera R7–R1; 7,973 m modelová R2–R4. Hodnota 6,65 m = 7,00 − 0,35 m je výhodná idealizácia šírky krídla s pracovnými podperami; nie je geodeticky potvrdené voľné rozpätie. Presné napojenia a nosná funkcia rebier ostávajú otvorené.

Doplňujúci garážový prípad (JSON): jedno **predpokladané**, nepotvrdené koleso 10 kN na stope 200 × 200 mm, celá sila iba na 200 mm páse. Pri L=1 m MEd=19,509 kNm/m, nad všetkými skúšanými MRd. Je to konzervatívny test bez priečneho roznosu, nie dôkaz, že každá 100 mm doska na skutočnom podloží pod vozidlom zlyhá. Pretlačenie, okraje a súbeh kolies nie sú týmto testom uzavreté.

## Čo sa nedá schváliť

- Celý dom: strecha, steny, štyri rebrá, obvodový betón a pôvodné pásy nemajú týmto výpočtom potvrdenú nosnú cestu ani únosnosť.
- Jedna spodná sieť: chýba horná výstuž nad rebrami, pri lokálnom zdvihu podložia, zápornom ohybe a obmedzenom zmrašťovaní.
- Miestna hlina/piesok: opis „zhutnené“ neurčuje zrnitosť, vlhkosť, organické prímesi, namŕzavosť, hrúbku vrstiev, modul, sadanie ani budúcu stratu podpory. Výpočet nevyvodzuje sadanie z percent Proctora.
- Pôvodná zemina pod zásypom a pásmi, voda, drenáž, stavebné fázy, trhliny a rozdielne sadanie zostávajú neoverené.
- Krytie 35 mm a C16/20 pre skutočnú expozíciu a životnosť 100 rokov zostávajú podmienene zadanými vstupmi.
- 150 mm zarážka bez rozmerového výkladu, reakcií a výstuže nie je preukázané uloženie, prenesenie šmyku alebo zakotvenie. Orientačné lb,rqd pri dobrých podmienkach vychádza približne 334 mm pre Ø6 a 446 mm pre Ø8; nejde o návrh konkrétneho spoja.

## Overenie a opakovanie

`python3 foundation-analysis/calculations/slab_100_four_ribs.py` vytvorí iba nové JSON/MD súbory. Kontroly: rovnováha prierezu a reakcií; výpočet priehybu nezávislým numerickým integrálom virtuálnej práce; oba smery každej siete; citlivosť dotvarovania. Starý `slab.py` a `slab-results.json` sa nemenia.

Zdroj základných vzťahov: [JRC, Walraven, EN 1992, 2008](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1992_1_Walraven.pdf), časti analýzy/redistribúcie, prierezových pretvorení, šmyku a trhlín; [JRC Worked Examples, kapitola 5](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/Bridge_Design-Eurocodes-Worked_examples.pdf), §7.3.4 trhliny. Sú to verejné podklady k prvogeneračnému EN 1992-1-1; nenahrádzajú plný text rozhodujúcej ČSN a českej NA.
