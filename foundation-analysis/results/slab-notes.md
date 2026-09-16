# Výpočtové poznámky – lokálna strata podpory podlahovej dosky

**Revízia AK-01/AK-02, 16. 9. 2026:** aktuálne je SM30, jedna 300 mm obvodová tehla so zachovaným účelom odhlučnenia. Táto štúdia používa zmrazené pôvodné zaťaženia SA30; výsledky pre stenové zaťaženia a R7 sa nepovažujú za prepočet SM30. Konkrétny výrobok a nový prepočet zostávajú otvorené. Samostatné geometrické kóty a výpočty bez stenového zaťaženia týmto nie sú prerátané. Pozri [záznam revízie](/Users/davidzita/www/dom/foundation-analysis/inputs/wall-revision-sm30-20260916.md).

**Stav:** vlastný reprodukovateľný podmienený výpočet lokálnych prierezov; nejde o schválenie celej základovej konštrukcie ani zaručenie životnosti. Skript `python3 foundation-analysis/calculations/slab.py` vytvára `foundation-analysis/results/slab-results.json` iba zo štandardnej knižnice Pythonu. Hodnoty v JSON majú plnú presnosť; nižšie sú zaokrúhlené.

## 1. Model a rozsah jeho platnosti

Doska je podlahová doska podopretá zásypom. Všetky murované priečky, nosné steny a ťažké bodové reakcie musí niesť samostatne navrhnutý pás/rebro/podpera; výsledky **neoprávňujú položiť murovanú stenu do voľného poľa dosky**. Metrový pás nie je náhradou celej budovy tvaru L. Je kontrolou presne definovanej vnútornej dlhej straty podpory: dva rovnobežné okraje s jednoduchým uložením, medzi nimi priečna nepodopretá šírka L. Ignorovaním priečneho spolupôsobenia sa pre tento vnútorný pás získava konzervatívny model. Nepokrýva voľné hrany, bránový prah, pracovné škáry bez prenosu šmyku, prestupy, L-rohy ani stratu podpory priamo pri základe.

- Návrhový scenár: vnútorný nepodopretý pás L = 1,0 m.
- Dodatočné testy robustnosti: L = 1,5 a 2,0 m.
- Hypotetický extrém mimo požadovanej funkcie: L = 4,0 m.
- Výstuž je na oboch lícach v oboch smeroch, v poli priebežná. Okolo vyšetrovaného výpadku podpory musí zostať najmenej 1,0 m podopretého betónu s plne zakotvenou výstužou na oboch stranách. Podpora zeminy a jej deformácia sa overujú osobitne.
- Gk = 25 h + 2 kPa, h v metroch; pridané stále vrstvy 2 kPa sú predpoklad. Obytné pole Qk = 2 kPa. Garáž: samostatné koleso Pk = 10 kN na stope 200 × 200 mm, bez súčasného obytného Qk. Celá sila kolesa ide iba do pásu šírky 200 mm; **nie je rozpočítaná na plochu garáže ani domu**. Na porovnanie sa výsledok uvádza na 1 m šírky (Pk/0,2 = 50 kN/m). Druhé koleso v tom istom nepodopretom páse, zdvihák, dielenský zdvihák vozidla, nákladné vozidlo alebo stĺp sú mimo modelu.

## 2. Materiál, prierez, bezpečnostné súčinitele

C16/20: fck = 16, fctm = 1,9, fctk,0.05 = 1,3 MPa; Ecm = 28 600 MPa. B500: fyk = 500 MPa, Es = 200 000 MPa; γc = 1,50, γs = 1,15; **αcc = 0,85 je konzervatívny predpoklad, nie tvrdenie o obsahu českej národnej prílohy**. fcd = 9,067 MPa, fyd = 434,783 MPa. Použité základné vzťahy sú zo systému EN 1992-1-1:2004 + A1:2014; presné relevantné vydanie ČSN a národné parametre musí uzavrieť hlavný report. Plný text rozhodujúcich českých národných príloh nebol pre tento submodel sprístupnený.

Predbežne cnom = 35 mm a maximálne zrno 16 mm, podkladná ochranná vrstva a ochrana proti zemnej vlhkosti. Vhodnosť C16/20 pre skutočné prostredie a cieľ 100 rokov **nie je týmto výpočtom potvrdená**. Pri dvoch smeroch výstuže na každom líci sa vo všetkých výpočtoch uvažuje menej priaznivá vnútorná vrstva:

- As = π φ² / 4 × 1000/s [mm²/m na jeden smer a jedno líce].
- d = h − cnom − 1,5φ [mm].
- Čistá medzera medzi lícami výstuže = h − 2 cnom − 4φ; požadovaná najmenej max(φ; 20; Dmax + 5) = najmenej 21 mm.
- Hrúbka 100 mm s Ø8/150: medzera −2 mm, preto sa dvojitá obojsmerná výstuž vôbec nezmestí. Tento variant je geometricky nevyhovujúci nezávisle od malej ohybovej požiadavky.
- Presahy a dodatočné prúty sa musia výškovo a pôdorysne vystriedať. Výpočet svetlosti je pre základné pole, nie pre križovanie všetkých presahov.

## 3. Vzťahy ULS a lokálne koleso

Kombinácia 1,35 Gk + 1,50 Qk/Pk. Pre jednoduchý pás:

`MEd = qd L²/8 + Pd L/4`; `Rľ = qd L/2 + Pd (L−xc)/L`; `Rpr = qd L/2 + Pd xc/L`.

V ohybe sa koleso v strede konzervatívne nahrádza bodovou silou. Pre šmyk sa 200 mm dlhá stopa kolesa presúva medzi oboma okrajmi. Skript skúma 10 001 polôh vrátane presnej polohy zlomu redukčnej funkcie; plná rovnováha `Rľ+Rpr=qdL+Pd` sa kontroluje pri každej polohe.

- Pravouhlý tlakový blok: a = As fyd / (b fcd); x = a/0,8; MRd = As fyd (d − a/2). Kontroluje sa x/d ≤ 0,45; tlaková výstuž sa nezapočítava.
- As,min = max(0,26 fctm/fyk; 0,0013) b d.
- ρl = min[As/(b d); 0,02], k = min[1 + √(200/d); 2].
- vRdc = max[(0,18/γc) k (100ρl fck)^(1/3); 0,035 k^(3/2) √fck], VRdc = vRdc b d.

**Dôležité pri kolese:** pretože prevláda sústredené zaťaženie, nepoužíva sa automatická výnimka „stačí šmyk vo vzdialenosti d“. Počíta sa reakcia pri okraji podpory. Len pod podmienkami EN 1992-1-1 §6.2.2(6) – horné zaťaženie, priamy tlakový prenos do spoľahlivej podpory a plne zakotvená ťahová výstuž – sa príspevok blízkeho kolesa redukuje β = max[0,25; min(av/(2d); 1)], kde sa v tomto konzervatívnom modeli av = xc meria k **pôsobisku celej bodovej sily, teda k stredu stopy**. Nepoužíva sa bližší okraj stopy. JRC, snímka 72, potvrdzuje pravidlo β a zakotvenie; jeho schéma má malé zaťažovacie doštičky a kótu medzi blízkymi hranami, preto sama osebe nedokazuje povinnosť merať k osi sily ani prenos tohto detailu na tlak pneumatiky. Tu sa vedome volí konzervatívna rodina bodových síl s av = xc; nejde o tvrdenie, že norma všeobecne zakazuje meranie k blízkej hrane rozdelenej stopy. Maximálna hodnota β(x)R(x) pre pohybujúcu sa bodovú silu zároveň ohraničuje integrál ľubovoľného nezáporného tlaku stopy: vážený priemer nemôže prevýšiť maximum príslušnej vplyvovej čiary. Rozhodujúca poloha pri skúmaných rozpätiach je xc = 2d. Súčasne sa overuje neredukovaný VEd ≤ 0,5 b d ν fcd, ν = 0,6 (1 − fck/250). JSON uchováva aj neredukovanú reakciu a jej porovnanie s VRdc. **Ak nemožno preukázať priamu podporu a zakotvenie, príslušný vyhovujúci šmykový výsledok neplatí.** Reálny kontakt s podložím, účinná šírka reakcie a zemina nie sú vyriešené samotnou formulou β.

Doplňujúce vnútorné pretlačenie pod kolesom: u1 = 800 + 4πd mm vo vzdialenosti 2d, βp = 1,15, VEd zahŕňa 15 kN aj 1,35 Gk na celej ploche vnútri u1; žiadna priaznivá reakcia zásypu sa neodčítava. Kontroluje sa vEd ≤ vRdc a pri stope kolesa vEd,0 ≤ 0,5νfcd. Toto je vnútorný uzatvorený kontrolný obvod; voľný okraj alebo roh potrebuje iné overenie.

## 4. Trhliny a deformácie

Úplne popraskaný obdĺžnikový prierez bez priaznivého účinku tlakovej výstuže:

`n = Es/Ec; x = [√((nAs)² + 2 b n As d) − nAs]/b; Icr = b x³/3 + nAs(d−x)²; σs = M/[As(d−x/3)]`.

Podľa EN 1992-1-1 §7.3.4:

- hceff = min[2,5(h−d); (h−x)/3; h/2], ρeff = As/(b hceff).
- sr,max = 3,4 c + 0,8 × 0,5 × 0,425 φ/ρeff; c sa pre kontrolovaný vnútorný prút berie 35 + φ mm. Platnosť dostatočne hustých prútov s ≤ 5(c+φ/2) sa kontroluje.
- Δε = max[(σs − kt fctm/ρeff (1 + Es/Ecm ρeff))/Es; 0,6 σs/Es], wk = sr,max Δε.
- Kvázistály stav G + 0,3 Q pre bytové zaťaženie, G + 0,6 P pre garáž: kt = 0,4, x s Ec,eff = Ecm/(1+φcreep), φcreep = 2,5. Súčinitele ψ2 sú explicitné predpoklady, ktoré sa ešte zosúladia s českou NA.
- Navyše je samostatne vypočítaná prísnejšia charakteristická kombinácia G+Q/P s krátkodobou prierezovou tuhosťou, ale konzervatívnym kt = 0,4. Limit 0,30 mm sa dobrovoľne požaduje aj pre túto obálku. Nezamieňa sa s normovou kvázistálou kombináciou.
- Doska sa môže predpokladať už popraskaná zmrašťovaním; vypočítaná hodnota je príspevok uvedeného zaťaženia, **nie kompletný výpočet trhlín od zmrašťovania a teploty**.

Priehyb = dlhodobá časť G+ψ2Q/P s Ec,eff + dodatočná prechodná časť (1−ψ2)Q/P s Ecm. Po celej dĺžke sa konzervatívne používa Icr bez tension-stiffening:

`δ = 5 q L⁴/(384 EI) + P L³/(48 EI)`.

Uvažuje sa projektový porovnávací limit L/250 a citlivosť φcreep = 1,5 / 2,5 / 3,5. Tento limit nie je dovolené rozdielne sadanie pod dlažbou alebo stenami. Samotná deformácia podložia sa do neho neskrýva.

## 5. Výsledné porovnávané prierezy

| Označenie | Doska | Výstuž na oboch lícach a v oboch smeroch | d | MRd kNm/m | VRdc kN/m | Oceľ bez presahov kg/m² |
|---|---:|---|---:|---:|---:|---:|
| MIN obytná časť | 150 mm | Ø8/150 | 103 mm | 13,84 | 42,84 | 10,52 |
| MIN garáž | 180 mm | Ø10/125 | 130 mm | 31,40 | 61,70 | 19,73 |
| MEDIUM obytná časť | 180 mm | Ø8/150 | 133 mm | 18,21 | 52,67 | 10,52 |
| MEDIUM garáž | 180 mm | Ø10/100 | 130 mm | 37,96 | 66,46 | 24,66 |
| MAX obytná časť | 200 mm | Ø10/150 | 150 mm | 31,29 | 63,87 | 16,44 |
| MAX garáž | 200 mm | Ø12/150 | 147 mm | 42,26 | 71,16 | 23,68 |

MIN má hrubšiu garáž preto, že 150 mm + Ø10/125 v konzervatívnom 200 mm kolese pri L = 1 m **nevyhovuje šmyku**: VEd = 63,88 > VRdc = 51,80 kN/m, hoci ohyb a trhliny vyhovujú. Tým nie je dokázané, že každý možný 150 mm garážový variant zlyhá; presnejšie 2D pôsobenie alebo iné vystuženie by mohli viesť k inému výsledku. Navrhnutá lokálna zmena hrúbky je v skúmanom súbore jednoduchá a realizovateľná.

| Pole a L | MEd kNm/m | VEd kN/m | wk kvázistála / charakteristická mm | δ φ=2,5 mm | Výsledok skúmaných lokálnych kontrol |
|---|---:|---:|---:|---:|---|
| MIN obytná, 1 m | 1,35 | 5,38 | 0,024 / 0,029 | 0,23 | vyhovuje podmienene |
| MEDIUM obytná, 1 m | 1,47 | 5,89 | 0,022 / 0,027 | 0,14 | vyhovuje podmienene |
| MAX obytná, 1 m | 1,56 | 6,23 | 0,013 / 0,016 | 0,08 | vyhovuje podmienene |
| MIN garáž, 1 m | 19,85 | 59,89 | 0,095 / 0,159 | 0,90 | vyhovuje podmienene; šmyk 97,1 % |
| MEDIUM garáž, 1 m | 19,85 | 59,89 | 0,069 / 0,116 | 0,76 | vyhovuje podmienene; šmyk 90,1 % |
| MAX garáž, 1 m | 19,93 | 57,68 | 0,075 / 0,121 | 0,60 | vyhovuje podmienene |
| MIN garáž, 1,5 m | 30,59 | 68,58 | 0,170 / 0,298 | 3,15 | **nevyhovuje šmyk** |
| MEDIUM garáž, 1,5 m | 30,59 | 68,58 | 0,125 / 0,217 | 2,67 | **nevyhovuje šmyk** |
| MAX garáž, 1,5 m | 30,78 | 67,39 | 0,121 / 0,219 | 2,10 | dodatočný test vyhovuje podmienene |
| MAX garáž, 2 m | 42,23 | 73,43 | 0,200 / 0,337 | 5,19 | **nevyhovuje šmyk** a dodatočný limit charakteristickej trhliny; ohyb takmer bez rezervy |

MEDIUM garáž má oproti MIN hustejšiu výstuž Ø10/100: únosnosť v šmyku +7,7 %, v ohybe +20,9 %, charakteristická trhlina −27,2 % a priehyb −15,1 %. MAX garáž má oproti MEDIUM väčšiu účinnú výšku: šmyková rezerva a priehyb sa zlepšia a prejde aj 1,5 m testom. Má však o 4 % menej ocele v garážovom poli (Ø12/150) a charakteristická trhlina pri 1 m je mierne vyššia 0,121 vs 0,116 mm; nejde o zlepšenie každej jednotlivej metriky.

Všetky tri obytné prierezy prešli aj 2 m vnútorným testom. Pri 4 m MIN/MEDIUM obytné pole zlyhá v ohybe, trhlinách aj deformácii. MAX obytné pole má δ = 20,90 > 16,00 mm; všetky garážové polia pri 4 m zlyhajú vo viacerých kontrolách. To nie je povinná požiadavka na vymiznutie celého zásypu, ale hranica preukázaného správania.

## 6. Nezávislá kontrola a citlivosť numeriky

Skript navyše zostavuje Navierov rad pre pružnú dosku jednoducho podopretú na **všetkých štyroch** hranách obdĺžnika. Nie je to model celého L pôdorysu. D = E h³/[12(1−ν²)], ν = 0,2. Koeficient zaťaženia pre q + stredovú 200 × 200 mm stopu P je:

`qmn = 16q/(mnπ²) + 4P/(ab) sin(mπ/2) sin(nπ/2) sinc(mπ100/a) sinc(nπ100/b)` pre nepárne m,n; `Wmn = qmn/[D((mπ/a)²+(nπ/b)²)²]`.

Krivosti radu dávajú Mx a My. Vykonané sú rady po 21, 41, 81 a 161 módoch v každom smere; posledná zmena stredového Mx je < 0,5 %, integrál Fourierovho zaťaženia sa líši < 1 % od zadanej sily. Tento integrál kontroluje spektrálnu normalizáciu zaťaženia; **nie je plnou nezávislou kontrolou okrajových reakcií a rohových síl dosky**. Presná statická rovnováha reakcií sa samostatne kontroluje pri 1D modeli.

- 1 × 1 m, qd = 8,775 kPa, Pd = 15 kN: Mx = My = 3,329 kNm/m.
- 1 × 4 m, rovnaké zaťaženie: Mx = 4,732, My = 2,935 kNm/m. Konzervatívny 200 mm pás má MEd = 19,847 kNm/m.
- 1 × 6 m, len qd = 10,7625 kPa: Mx = 1,34424 kNm/m, analytický metrový pás qL²/8 = 1,34531; rozdiel približne 0,08 %.

Pružné priehyby Navierovho nepopraskaného modelu sú iba kontrolou riešenia, **nie** hodnotami pre dlhodobé SLS. Nebola urobená úplná obálka pohybujúceho sa kolesa, Wood-Armerovo posúdenie krútenia, šmykových tokov ani nelineárne kontaktné riešenie. Preto tieto malé 2D stredové momenty neoprávňujú automaticky znížiť zvolené garážové vystuženie.

## 7. Detaily, zakotvenie a neuzavreté časti

Pri dobrých podmienkach súdržnosti fbd = 2,25 fctk,0.05/γc = 1,95 MPa; lb,rqd = φ fyd/(4fbd) = 55,74φ: Ø8 približne 446 mm, Ø10 približne 557 mm, Ø12 približne 669 mm. Skript uvádza orientačný presah 1,5 lb,rqd; nie je to univerzálny výkres presahov. Treba overiť skutočné podmienky súdržnosti, percento stykovaných prútov, krytie a obmedzenie štiepenia. Pre analyzovanú vnútornú stratu podpory sa vyžaduje aspoň 1 m priebežnej výstuže za oba okraje. Výstuž sa nemá končiť na hranici predpokladanej straty podpory.

Kontrola úplného axiálneho zabránenia zmrašťovaniu pri fct,eff = 1,9 MPa a orientačnom σs = 300 MPa dáva pre každé líce As,req = fct,eff b h/(2σs): 475 / 570 / 633 mm²/m pri h = 150 / 180 / 200 mm. Obytné výstuže Ø8/150 (335 mm²/m) a Ø10/150 (524 mm²/m) **nepokryjú tento úplne zabrzdený prípad**. Garážová oceľ síce týmto minimálnym silovým skríningom prejde, ale ani tento výsledok sám nepotvrdzuje šírku teplotnej alebo zmrašťovacej trhliny. Návrh preto musí riešiť oddelenie od stien, klznú vrstvu, riadené polia a škáry, ošetrovanie a skoré teploty. Škáry sa nesmú umiestniť tak, aby zrušili nosnú dráhu lokálneho modelu bez náhradného prenosu síl. Bez konkrétneho návrhu týchto detailov nejde o uzavretý dôkaz použiteľnosti celej dosky.

## Zdroje vzťahov

1. [JRC – Walraven, EN 1992, 22. 2. 2008](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1992_1_Walraven.pdf): ohyb, šmyk, zaťaženie blízko podpory (snímka 72), trhliny. Ide o vysvetľujúci primárny materiál európskeho pracovného seminára, nie náhradu českej NA.
2. [JRC – Bridge Design, Worked Examples](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/Bridge_Design-Eurocodes-Worked_examples.pdf), kapitola 5, tlačená strana 106: priamy výpočet trhlín podľa EN 1992-1-1 §7.3.4. Použité sú všeobecné vzťahy; nepoužíva sa mostný limit trhlín ani francúzska kombinácia.
3. [The Concrete Centre – Worked Examples to Eurocode 2](https://www.concretecentre.com/TCC/media/TCCMediaLibrary/Events/Online%20course/CCIP_Worked_Examples_EC2.pdf), časť 3.2.10, tlačená strana 45: minimálna plocha výstuže a detaily. Britské národné voľby sa nevyhlasujú za české.
4. [The Concrete Centre – EC2 Spreadsheet User Guide, Bridges](https://www.concretecentre.com/TCC/media/TCCMediaLibrary/Events/Online%20course/CCIP_EC2_Bridges.pdf), §8.1–8.4: pretlačenie pod kolesom, definícia kontrolných obvodov; použité základné rovnice EN 1992-1-1.
