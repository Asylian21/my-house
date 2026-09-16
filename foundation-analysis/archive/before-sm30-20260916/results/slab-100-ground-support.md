# 100 mm doska so súvislou podporou zeminy – lokálny výpočet

**Hlavný model ponecháva zeminu pod celou doskou.** Ide o vnútorný metrový pás na homogénnej pružnej podpore, nie o dosku visiacu medzi rebrami. Výsledok je podmienená citlivosť, nie súhlas s betonážou ani preukázanie nosnosti celého domu.

## Vstupy a nosná cesta

C16/20, h=100 mm; skúšobná spodná obojsmerná sieť Ø8/150 B500, cnom=35 mm. Výstuž používateľ nezadal. Stena → lokálny ohyb dosky → súvislá tlaková reakcia zásypu. Rebrá, obvod, ich tuhosť a reakcie strechy sa týmto lokálnym modelom nenahrádzajú.

k_s = **5 / 10 / 20 / 50 MN/m³** sú vedome zvolené citlivostné hodnoty. Nie sú skúškou miestnej hliny/piesku, prevodom z Proctora ani dovolenou únosnosťou zeminy. k_s závisí od rozmeru zaťaženej oblasti, vrstiev a skúšobnej metódy; nijaká z týchto hodnôt sa nepredpisuje realizátorovi ako už dosiahnutý stav.

Plošné Gk=4,5 kPa (doska2,5 + predpoklad vrstiev2,0), Qk=2,0 kPa. Charakteristická kombinácia6,5; kvázistála5,1; ULS9,075 kPa. ψ2=0,3 je výslovný predpoklad. Steny sú stále: SLS1,0Gsteny, ULS1,35Gsteny. Podlahové plošné zaťaženie na nekonečnej homogénnej podpore spôsobí konštantný posun q/k_s, bez lokálneho ohybu. Pri reálnych okrajoch a rozdieloch tuhosti to neplatí.

| Stena z interného modelu | Gk kN/m | Kontaktná šírka m |
|---|---:|---:|
| IW-STUDY-NORTH | 5.211563 | 0.200 |
| IW-BATH-105-SOUTH-E | 6.937500 | 0.140 |
| C-GARAGE-SPINE-N | 12.975000 | 0.301 |

Hmotnosti pochádzajú z `results/wall-loads.csv`, šírky z `inputs/geometry.json`; ide o modelové predpoklady, nie potvrdené zaťaženia z dodacích listov. Šírka H200=200 mm idealizuje celý pás rovnomerne; skutočné rozdelenie hmotnosti muriva/predsadenej konštrukcie treba doplniť. Pri najťažšej stene12,975 kN/m sa nepočíta strecha ani povala.

## Riešenie a kontrola kontaktu

Použité jednotky: m, N. P=gsteny×1 m; šírka metrového pásu b=1 m, k=k_s b. Rovnica EI w⁽⁴⁾ + k w = q(x), β=(k/(4EI))^(1/4). Stena je konečná rovnomerná tlaková stopa šírky a: qsteny=P/a. Analyticky sa integruje Greenova funkcia cez celý tento pás. M=−EI w″, V=dM/dx. Výpočet obsahuje kladné aj záporné momenty.

Jadrové funkcie jednotkovej bodovej sily sú w₁(x)=β/(2k) exp(−β|x|)[cos(β|x|)+sin(β|x|)] a M₁(x)=1/(4β) exp(−β|x|)[cos(β|x|)−sin(β|x|)]. Nejde o rozmazanie steny na celý dom: konečná stopa sa konvoluuje s presnou reakciou podporeného pásu.

Pružiny lineárneho riešenia matematicky vedia prenášať aj ťah. Preto sa výslovne overuje celkový tlak p=qpodlahy+k_s wsteny ≥0. Samotný prírastok od steny môže byť záporný; rozhoduje celkový kontakt vrátane vlastnej tiaže. V uvedených kombináciách vyšiel kontakt všade tlakový. Ak by vyšiel ťah, výsledok by nebol fyzikálne prípustný a bolo by potrebné riešenie s oddeľovaním kontaktu; záporná reakcia by sa neskrývala.

## Tuhosť – štyri odlišné citlivosti

| Označenie | EI kN·m² | Pomer k hrubému prierezu |
|---|---:|---:|
| gross_uncracked | 2383.333 | 1.0000 |
| constant_cracked_positive | 128.021 | 0.0537 |
| constant_cracked_negative | 65.178 | 0.0273 |
| constant_cracked_negative_phi2p5 | 45.409 | 0.0191 |

Hrubý nepopraskaný prierez má Ecm=28 600 MPa a Ig=bh³/12. Znížené tuhosti sa reprodukovateľne odvodia z úplne popraskaného prierezu jednej siete: n=Es/Ec, x=[√((nAs)²+2bnAsd)−nAs]/b, Icr=bx³/3+nAs(d−x)². Použité d=53 mm pre kladný ohyb alebo d=39 mm pre záporný; posledný prípad má Ec=Ecm/(1+2,5).

**Každý znížený EI je konštantná citlivosť pre celý pás.** Nie je to skutočne vyriešené rozdelenie trhlín, nelineárne materiálové správanie alebo nameraná tuhosť dosky. Zmenšenie EI zníži roznesenie sily a momenty, ale zväčší miestny tlak a zatlačenie. Nemožno z neho vybrať iba priaznivý moment a ignorovať zhoršenie kontaktnej deformácie.

## Skutočné účinné výšky jednej spodnej siete

| Drôt | d+ mm | MRd+ kNm/m | d− mm | MRd− kNm/m |
|---|---:|---:|---:|---:|
| outer_bottom_wire | 61 | 7.717 | 39 | 4.512 |
| inner_cross_wire | 53 | 6.551 | 47 | 5.677 |

Pri zápornom ohybe sa tlaková strana otočí; preto má rovnaký drôt d−=h−d+, nie d+=61/53 mm. Sieť umiestnená pri spodku môže ležať v ťahovej oblasti aj pri menšej zápornomomentovej účinnej výške, takže jej vypočítaná záporná kapacita nie je automaticky nulová. Tým sa z nej nestáva navrhnutá horná sieť: chýba preukázanie trhlín pri hornom povrchu, ťažnosti, kotvenia a správania nad rebrami. Pri d−39 mm vychádza x/d≈0,515; rotačná kapacita a spôsob analýzy potrebujú osobitné overenie.

MRd je z kompatibility pretvorení pri εcu=0,0035 a rovnováhe tlakového bloku0,8bx fcd s As min(fyd,Esεs). fcd=9,067 MPa; fyd434,783 MPa. Nejde o úplný návrh podľa českých NA ani trvanlivostný dôkaz C16/20 pri cieľovej životnosti100 rokov.

## Výsledky: nepopraskaná tuhosť

| Stena | k_s MN/m³ | MEd+ / MEd− kNm/m | pmax SLS kPa | max posun SLS mm | minimum tlaku SLS kPa |
|---|---:|---:|---:|---:|---:|
| IW-STUDY-NORTH | 5 | 1.896 / -0.429 | 8.71 | 1.742 | 6.40 |
| IW-STUDY-NORTH | 10 | 1.568 / -0.360 | 9.13 | 0.913 | 6.39 |
| IW-STUDY-NORTH | 20 | 1.293 / -0.302 | 9.62 | 0.481 | 6.37 |
| IW-STUDY-NORTH | 50 | 0.995 / -0.240 | 10.42 | 0.208 | 6.33 |
| IW-BATH-105-SOUTH-E | 5 | 2.591 / -0.571 | 9.45 | 1.890 | 6.37 |
| IW-BATH-105-SOUTH-E | 10 | 2.154 / -0.480 | 10.00 | 1.000 | 6.35 |
| IW-BATH-105-SOUTH-E | 20 | 1.786 / -0.403 | 10.67 | 0.533 | 6.32 |
| IW-BATH-105-SOUTH-E | 50 | 1.389 / -0.320 | 11.73 | 0.235 | 6.27 |
| C-GARAGE-SPINE-N | 5 | 4.515 / -1.064 | 11.99 | 2.399 | 6.26 |
| C-GARAGE-SPINE-N | 10 | 3.701 / -0.893 | 13.02 | 1.302 | 6.22 |
| C-GARAGE-SPINE-N | 20 | 3.019 / -0.748 | 14.23 | 0.711 | 6.17 |
| C-GARAGE-SPINE-N | 50 | 2.284 / -0.591 | 16.17 | 0.323 | 6.08 |

SLS tabulka je charakteristická kombinácia. Kvázistála aj ULS kontaktová odozva je v JSON. Nepopraskaný model sa musí kontrolovať proti Mcr=fctm bh²/6=3,167 kNm/m; prekročenie sa v JSON označuje. Ani nižší moment nepreukazuje, že nevznikli predchádzajúce zmrašťovacie alebo teplotné trhliny.

## Najťažšia stena: vplyv tuhosti pri k_s=5 MN/m³

| EI prípad | MEd+ / MEd− kNm/m | pmax SLS kPa | max posun SLS mm | zatlačenie navyše od steny mm |
|---|---:|---:|---:|---:|
| gross_uncracked | 4.515 / -1.064 | 11.99 | 2.399 | 1.099 |
| constant_cracked_positive | 1.876 / -0.503 | 17.73 | 3.546 | 2.246 |
| constant_cracked_negative | 1.502 / -0.421 | 19.69 | 3.939 | 2.639 |
| constant_cracked_negative_phi2p5 | 1.328 / -0.382 | 20.87 | 4.173 | 2.873 |

## Hranice výsledku

- Počítané posuny sú pružná Winklerova odozva modelovanej podpory na uvedené zaťaženie. Nezahŕňajú vlastné sadanie/navlhnutie/konsolidáciu zásypu, sadanie prirodzenej zeminy, zoschnutie hliny, mráz ani históriu výstavby. Nie sú garantovaným celkovým sadaním domu.
- Rovnaký k_s všade nepreukazuje, že miestna zemina bola rovnomerne zhutnená. Materiál, vrstvy, voda, skutočná skúška a jej interpretácia do modelu chýbajú.
- Pás je dlhý a vnútorný, stena rovnako dlhá v priečnom smere. Hrany dosky, L-rohy, konce stien, dvere, prestupy, susediace steny a rigidné rebrá môžu výsledok zmeniť. Dĺžka5/β v JSON ukazuje vzdialenosť približného doznievania; blízky okraj/podpera porušuje predpoklad nekonečného pásu.
- Tlak zeminy sa vypočítal, ale neporovnával s neznámou návrhovou únosnosťou; k_s sa nesmie zamieňať za túto únosnosť.
- Porovnanie ohybových účinkov s prierezom nezahŕňa horné povrchové trhliny, pracovné škáry, kotvenie, dotvarovanie zeminy, zmršťovanie ani celý systém štyroch rebier. Sústredené reakcie strechy, ťažké zariadenia a kolesá auta nie sú nahradené týmito líniami stien.
- Žiadna zo skúšobných sietí ani k_s nie sú realizačným predpisom.

## Opakovanie a overenie

`python3 foundation-analysis/calculations/slab_100_ground_support.py` vytvorí iba vlastné JSON a MD. Kontrola: nezávislá numerická konvolúcia, integrál dodatočnej reakcie = hmotnosť steny, bodový limit stopy, diferenciálna rovnica, symetria a zjemnenie siete extrémov600→2400 bodov. Staršie výpočty sa nemenia.

Zdroje: [NPTEL/IIT Madras, Beam on Elastic Foundation, kapitola11](https://archive.nptel.ac.in/content/storage2/courses/105106049/lecnotes/mainch11.html) pre rovnicu, základnú funkciu a význam negatívnej kontaktnej reakcie; [University of Florida, kapitola10](https://web.mae.ufl.edu/nkim/egm5533/solution/Chap10Student.pdf) pre odlíšenie k od k_s a vzťah β; [JRC, Walraven EN1992](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1992_1_Walraven.pdf) pre prierezové pretvorenia betónu/ocele. Hodnoty k_s nie sú prevzaté z týchto zdrojov ako vlastnosti tejto stavby.
