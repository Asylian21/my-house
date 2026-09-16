# C/B/B: 100 mm C16/20 a 400 mm rebrá na zhutnenej zemine


## Doska 100 mm na zhutnenej zemine

Hlavný model rešpektuje tvoje zadanie: doska aj spodná plocha rebier majú súvislú podporu zhutneným zásypom. Doska preto automaticky nepreklenuje celé vzdialenosti medzi rebrami. Stenu mimo rebra môže podopierať doska spolu so zeminou. Predošlé voľné polia sú už len doplnkovými skúškami straty podpory.

| Vstup | Použitá hodnota a dôkazová úroveň |
| --- | --- |
| Doska a betón | DEKLAROVANÉ: 100 mm, C16/20, spoločná betonáž s rebrami. |
| Štyri rebrá | R7 / R1 / R2 / R4. DEKLAROVANÁ celková výška 400 mm; 300 mm pod doskou. Pracovná šírka 350 mm je PREDPOKLAD. |
| Zásyp | DEKLAROVANÁ miestna zhutnená hlina/piesok. Súvislý kontakt a rovnomerná pružná podpora sú PREDPOKLAD modelu. |
| Tuhosť a výstuž | ks = 5 / 10 / 20 / 50 MN/m³ sú citlivostné hodnoty, nie skúšky. Skúšobná oceľ B500; výstuž stavby zatiaľ CHÝBA. |

Čo sa dá vypočítať hneď: rovnomerné podlahové zaťaženie

Tiaž dosky: 0,10 × 25 = 2,50 kN/m². Pracovný predpoklad ďalších vrstiev 2,00 kN/m² a úžitkového zaťaženia 2,00 kN/m² dá spolu 6,50 kPa v charakteristickom stave. Návrhová kombinácia je 1,35 × 4,50 + 1,50 × 2,00 = 9,075 kPa. Steny sú počítané navyše, jednotlivo.

| ks [MN/m³] | Tlak G + Q [kPa] | Stlačenie pružín w = p/ks [mm] |
| --- | --- | --- |
| 5 | 6,50 | 1,300 |
| 10 | 6,50 | 0,650 |
| 20 | 6,50 | 0,325 |
| 50 | 6,50 | 0,130 |

Tieto posuny sú odpoveď zvolených pružín. Nie sú predpoveďou konečného sadnutia domu. Pri nekonečnej rovnomernej ploche, rovnakom ks a rovnomernom zaťažení vychádza ohyb od tejto zložky nulový. Okraje, steny, prestupy, rozdiely podložia a zmrašťovanie tento ideálny stav menia.

Význam výsledku

Súvislá podpora zeminou umožňuje oveľa priaznivejšie miestne ohybové výsledky, ako dávalo voľné pole. Nasledujúce strany uvádzajú skutočne prepočítané steny a rebrá. 100 mm tým nie je automaticky vylúčených, ale bezpečnosť celého domu ešte nie je preukázaná: skúšobná výstuž, parametre podložia, všetky strešné reakcie a spoj na obvod sa musia uzavrieť.


## Doska pod stenami: miestny ohyb a tlak

Samostatný vnútorný pás šírky 1 m na homogénnej podpore. Zaťaženie steny pôsobí cez jej konečnú šírku. Počítajú sa tiaže z modelu vrátane predpokladaných povrchov, bez dodatočných reakcií strechy a povaly. Nekonečný pás idealizuje oblasť vzdialenú od okrajov a koncov stien; nie je to výpočet všetkých 37 úsekov domu.

| Skúmaná stena | Gk [kN/m] | Šírka stopy [mm] |
| --- | --- | --- |
| H200 pri pracovni | 5,212 | 200* |
| Murovaná priečka | 6,938 | 140 |
| Deliaca stena garáže | 12,975 | 301 |

*Pri H200 je rovnomerná stopa celej skladby idealizáciou; skutočné rozdelenie tiaže muriva a predsadenej konštrukcie treba doriešiť. Ide o vlastné tiaže jednotlivých stien, nie priemer rozpočítaný na podlahu.

Najťažšia stena 12,975 kN/m: nepopraskaná tuhosť

| ks[MN/m³] | MEd+ / MEd-[kNm/m] | pmax G+Q[kPa] | wmax G+Q[mm] |
| --- | --- | --- | --- |
| 5* | 4,515 / -1,064 | 11,99 | 2,399 |
| 10 | 3,701 / -0,893 | 13,02 | 1,302 |
| 20 | 3,019 / -0,748 | 14,23 | 0,711 |
| 50 | 2,284 / -0,591 | 16,17 | 0,323 |

Porovnanie skúšobnej spodnej Ø8/150: slabšia kladná odolnosť MRd+ = 6,551 kNm/m (d = 53 mm); slabšia záporná MRd- = 4,512 kNm/m (d = 39 mm). Najväčšie požiadavky vo všetkých 48 citlivostiach sú 4,515 a 1,064 kNm/m. Tieto miestne ohybové požiadavky sú menšie ako uvedené odolnosti. Výsledok sám nepotvrdzuje trhliny, kotvenie ani realizovateľnosť siete.

*Pri ks = 5 a najťažšej stene je Mser = 3,344 > Mcr = 3,167 kNm/m. Čisto nepopraskaný stav preto nie je konzistentný. Následne sa skúšali nižšie tuhosti; nejde o potvrdenie skutočného priebehu trhlín.

Tá istá stena a ks = 5: vplyv popraskania

| Konštantná tuhosť EI[kNm²] | MEd+[kNm/m] | pmax G+Q[kPa] | wmax G+Q[mm] |
| --- | --- | --- | --- |
| Hrubý prierez / 2383,3 | 4,515 | 11,99 | 2,399 |
| Popraskaný d = 53 / 128,0 | 1,876 | 17,73 | 3,546 |
| Popraskaný d = 39 / 65,2 | 1,502 | 19,69 | 3,939 |
| d = 39, phi = 2,5 / 45,4 | 1,328 | 20,87 | 4,173 |

Nižšie EI zmenší roznesenie sily: ohyb klesne, ale tlak a miestne zatlačenie rastú. Redukované hodnoty sú vypočítané z úplne popraskaného prierezu a použité konštantne na celý pás. Nie sú nelineárnym SLS výpočtom. Pri 48 prípadoch vyšiel maximálny charakteristický tlak 30,51 kPa a najväčší pružný posun 4,17 mm; tieto dve špičky patria rôznym prípadom.

Všetky kontrolované celkové tlaky zostali kladné aj pri kvázistálej kombinácii G + 0,3Q. Zemina sa preto v týchto konkrétnych výpočtoch nenúti prenášať ťah. Skúšobná sieť nie je návrhom výstuže pri rebrách a hornom povrchu. Priehyb a trhliny hotovej dosky sa touto kontrolou neuzatvárajú.


## Štyri rebrá 350 × 400 mm podopreté zeminou

Každé rebro je konečný nosník na súvislej pružnej podpore šírky 350 mm. Konce sú v tomto samostatnom modeli voľné: M = V = 0, bez predpokladaného votknutia alebo nepreukázaného uloženia na obvod. Dĺžky 7,495 a 6,298 m tu označujú dĺžku podopretého rebra, nie voľné rozpätie.

Zahrnutá je vlastná tiaž 0,35 × 0,40 × 25 = 3,50 kN/m a tiaže súosých stenových úsekov, vrátane otvorov podľa vstupu. Pruh 100 mm dosky nad rebrom je započítaný raz. Ďalšia plocha dosky, podlahové vrstvy, úžitkové a bodové zaťaženia, strecha, povala a nadpražia nad rámec opísaných tiaží zatiaľ nie sú zahrnuté.

Výsledky pri predpokladanom ks = 20 MN/m³

| Rebro | max p(Gk)[kPa] | max w(Gk)[mm] | max |MEd|[kNm] | max |VEd|[kN] |
| --- | --- | --- | --- | --- |
| R7 | 26,19 | 1,309 | 3,618 | 3,486 |
| R1 | 44,32 | 2,216 | 9,278 | 8,370 |
| R2 | 44,16 | 2,208 | 11,071 | 9,047 |
| R4 | 47,99 | 2,400 | 4,106 | 7,204 |

Každá bunka je obálka troch tuhostí, nie nevyhnutne jedna spoločná fyzická zostava. p a w patria zahrnutým charakteristickým tiažam Gk; MEd a VEd používajú 1,35Gk. Skúšané EI = 53 386,7 / 7 870,1 / 9 587,3 kNm²: hrubý prierez a dve plne popraskané konštantné tuhosti s phi = 2,5. Ani tu nejde o vyriešenú históriu trhlín.

Citlivosť na ks = 5 až 50 MN/m³ a na tuhosť rebra

| Rebro | Rozsah max w(Gk)[mm] | MEd+ max[kNm] | MEd- min[kNm] |
| --- | --- | --- | --- |
| R7 | 0,526 až 5,230 | 0,878 | -4,569 |
| R1 | 0,884 až 8,757 | 1,961 | -12,063 |
| R2 | 0,821 až 7,966 | 13,898 | -1,747 |
| R4 | 0,925 až 9,827 | 4,520 | -3,871 |

Záporný moment znamená ťah hore. Najmä R1 a R7 preto nemožno schváliť iba porovnaním so spodnými prútmi. Skúšobný prierez s účinnými 3Ø16 na ťahovej strane má MRd = 80,69 kNm; so 4Ø16 102,77 kNm. To je podmienená prierezová odolnosť, nie predpis rovnakej výstuže hore a dole. Skutočná horná výstuž a kotvenie nie sú navrhnuté.

Čo preukazuje tento model rebier

Súvislá zemina prenáša väčšinu zaťaženia priebežne a podstatne znižuje ohyb oproti nosníku nesenému iba na koncoch. Všetkých 48 prípadov má tlakový kontakt. Najvyšší tlak od zahrnutých Gk je 49,14 kPa; najväčší posun pružín 9,83 mm. Únosnosť zeminy a prípustné rozdielne sadanie sa tým ešte nepreukázali.

Zjemnenie siete zo 100 na 50 mm zmenilo sledované extrémy najviac o 0,134 %. Relatívna chyba rovnováhy zvislých síl bola najviac 4.75e-09. Model susednej dosky, rebier a obvodu treba následne spojiť; tieto lokálne posuny nemožno priamo odčítať a označiť za skutočné rozdielne sadanie domu.


## Podložie, obvod a konštrukčný detail

Súvislá podpora musí byť aj pod spodkom rebra

Model počíta s doskou uloženou na zásype a s podopretím rebra na jeho spodnej ploche, 300 mm pod doskou. Pod rebrami sa používa plošná tuhosť násobená šírkou 0,35 m. Skutočný zásyp v tejto úrovni a prirodzená zemina pod ním musia túto podporu vytvoriť. Rovnaké ks pod doskou aj rebrom je citlivostný predpoklad, nie vlastnosť potvrdená stavbou.

Tuhosť ks, únosnosť a sadanie sú tri odlišné kontroly

ks vyjadruje modelovú tuhosť kontaktu, teda vzťah tlaku a posunu. Nie je dovoleným tlakom do zeminy. Vyššie ks spravidla zmenší miestny pokles, ale môže zvýšiť špičku kontaktného tlaku. Návrhovú únosnosť a celkové aj rozdielne sadanie treba overiť pre celý profil zásypu a prirodzenej zeminy. [1, 3]

Zhutnenie je vstup do posúdenia. Percento Proctora, modul zo skúšky doskou Ev2 a ks nie sú zameniteľné veličiny. Geotechnik má podľa materiálu, vlhkosti a hrúbok vrstiev určiť skúšky, preberacie kritériá a parametre pre tento model. Posuny na stranách 1-3 nezahŕňajú následnú konsolidáciu, premočenie alebo objemové zmeny. [1, 3]

Existujúce pásy 380-400 mm zostávajú samostatným základom

Pôvodná statika mala pre 800 mm pás NEd = 68 kN/m. Ak by rovnaká sila pôsobila na 400 mm, samotné N/B dá 170 kPa; na 380 mm 178,9 kPa, ešte bez tiaže pásu. Pôvodných Rd = 150 kPa bolo projektovým predpokladom. Tieto čísla upozorňujú na potrebu nových reakcií a geotechniky; nie sú výpočtom dnešnej únosnosti ani automatickým dôkazom poruchy. Zásyp vnútri automaticky nezväčšuje šírku starého obvodového základu.

Zarážka 150 mm a výstuž

Oznámených 300 mm pri hornom obvode a 150 mm hĺbky neurčuje celý profil spoja. Zarážka sa preto nezapočítala ako hotová kotva ani votknutie. Napríklad základná priama kotevná dĺžka Ø16 pri plnom fyd, C16/20 a dobrej súdržnosti vychádza 892 mm; konečné lbd závisí od napätia a detailu. Spoločná betonáž dosky a rebier nepreukazuje spoj so starým betónom. [2]

Modré obvodové čiary sú deklarované približné osi betónu. Rozdiel voči starým sivým osiam 349-354 mm je koordinačný rozpor modelu, nie zameraná chyba stavby. Pred návrhom spoja treba určiť skutočné líca, výšky a uloženie nového betónu.


## Rozsah výsledku a ďalšie rozhodnutie

| Čo sa teraz prepočítalo | Čo tým ešte nie je potvrdené |
| --- | --- |
| Rovnomerná podlaha na zemi | Podpora pri okrajoch, kútoch, prestupoch a pri rozdieloch ks. |
| Miestny pás pod jednotlivou stenou | Spoločné pôsobenie všetkých stien, dosky, rebier a obvodu; konce a križovania stien. |
| Samostatné rebrá na pružnom podloží | Celý monolitický L-systém, rozdielne sadanie oproti starým pásom a konečný spoj. |
| Priebehy tlaku, posunov a síl | Nameraná únosnosť zásypu, hlbšieho podložia a konečné sadnutie domu. |
| Skúšobné železobetónové prierezy | Skutočná výstuž, trhliny, dotvarovanie, zmrašťovanie, kotvy, kolesá v garáži a nohy zariadení. |

Praktický záver pre 100 mm C16/20

Počítanie so zhutnenou zeminou je oprávnený nosný model a výrazne mení výsledok. Miestne ohybové kontroly uvedené v tejto správe nedávajú dôvod zamietnuť hrúbku 100 mm iba pre veľké rozostupy rebier. Nemáme však uzavretý návrh, ktorý by potvrdil bezpečnosť celého domu. Pred betonážou musí autorizovaný statik uzavrieť výstuž, skutočné zaťaženia a napojenia s geotechnickými parametrami pre túto stavbu.

Nie je potrebné automaticky doplniť rebro pod každú stenu iba preto, že na pôdoryse neleží nad jedným zo štyroch rebier. Rozhodne výsledok dosky so zeminou pri príslušnej stene. Ani tento priaznivejší výpočet zatiaľ nepredpisuje konkrétnu sieť alebo pozdĺžne prúty na nákup.

Predošlé výpočty bez podpory zásypom

Výsledky lokálnych dutín 1-2 m, voľných doskových polí a rebier podopretých iba na koncoch zostávajú v samostatných JSON/MD a v archive/before-ground-support-20260916/. Sú to doplnkové scenáre. Ich nevyhovenie sa nepoužíva ako záver o dnešnom hlavnom modeli s priebežnou podporou.

Metóda, overenie a reprodukcia

Rovnováha prúta: EI d⁴w/dx⁴ + ks b w = qline(x); reakcia p = ks w. Doskový pás je samostatný jednosmerný model šírky 1 m. Konečná šírka steny sa integruje, nenahrádza sa bodovým tlakom pri kontrole jeho špičky. Rebrá majú samostatný konečný prútový model. Súčet týchto lokálnych výpočtov nie je spojeným priestorovým modelom domu.

Nezávislá Fourierova kontrola pásu: 24 kombinácií, 4 096 a 16 384 harmoník; maximálna relatívna odchýlka od uzavretého riešenia je 1.93e-08. Ďalšie kontroly rovnováhy, kontaktu a zjemnenia sú v výsledných JSON. Matematická zhoda overuje algoritmus, nie vstupné vlastnosti stavby.

Reprodukcia v calculations/: ground_support_independent.py, slab_100_ground_support.py, four_rib_ground_support.py, report_100mm.py. Podrobné vstupy a výsledky sú v results/*ground-support*; odolnosti nadväzujú na slab_100_four_ribs.py a four_rib_free_beam_screen.py. C16/20: fcd = 0,85 × 16/1,5 = 9,067 MPa; B500: fyd = 500/1,15 = 434,783 MPa. Krytie 35 mm a národné voľby sú výpočtové predpoklady.

Primárne zdroje a hranice ich použitia

[1] FHWA NHI-05-037 §5.4.6 a §8.3: význam ks a kontrola podložia; mechanický podklad, nie český návrhový predpis. [2] JRC 2014: Eurocode 2, worked examples: RC a geotechnické kontroly. [3] JRC 2013: Eurocode 7: prieskum a sadanie. [4] NPTEL, Beam on Elastic Foundation, kap. 11: rovnice a analytický kontrolný príklad. Overené 16. 9. 2026.

ČSN EN 1992-1-1 ed. 2 (2019) a NA ed. A (2020): overené katalógové údaje ČAS; úplné znenie českých národných príloh nebolo dostupné. Súbor inputs/check-100mm-sources.md uvádza dostupnosť a vydania; inputs/ground-support-sources.md obsahuje podrobné nové zdroje. Správa nepredstiera autorizované normové posúdenie.
