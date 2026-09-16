# Podklad pre samostatnú kontrolu dosky 100 mm, C16/20

Overenie verejných zdrojov: **16. 9. 2026**. Tento doplnok nemení existujúce výpočty ani výkresy. Vstup používateľa: doska a rebrá majú byť betonované spolu; potvrdená celková výška rebra je 400 mm vrátane dosky 100 mm, teda 300 mm pod doskou. Zásyp je miestna zemina opísaná ako hlina/piesok a zhutnená. To je deklarácia materiálu a postupu, nie meranie tuhosti, únosnosti alebo budúceho sadania. Na obvode používateľ opisuje 300 mm betónu ako horný šalung a drážku/zarážku hlbokú 150 mm; presná orientácia, profil a dĺžka prútov pri tomto detaile zatiaľ nie sú jednoznačné.

## 1. Použitá generácia normy a prístup

- [ČAS: ČSN EN 1992-1-1 ed. 2](https://csnonline.agentura-cas.cz/Detailnormy.aspx?k=507748): vydanie 1. 11. 2019, účinnosť 1. 12. 2019, koniec platnosti 30. 3. 2028; katalóg uvádza Z1.
- [ČAS: NA ed. A](https://csnonline.agentura-cas.cz/Detailnormy.aspx?k=511214): vydanie 1. 11. 2020, účinnosť 1. 12. 2020. Katalóg neobsahuje jej úplné ustanovenia.
- [ČAS: ed. 3](https://csnonline.agentura-cas.cz/Detailnormy.aspx?k=520008): vydanie 1. 10. 2025, účinnosť až 1. 10. 2027. Nemiešať jej pravidlá s nižšie použitou prvou generáciou.

Overené sú **katalógové údaje**, nie celé konsolidované české normy a NA. České národne určené parametre, expozícia, krytie, realizačné tolerancie a 100-ročná životnosť zostávajú na kontrolu. Cnom=35 mm je vstup geometrického testu, nie novo preukázaná česká normová požiadavka.

## 2. Čo je doska na zemi a čo základová doska

[Concrete Society: Ground supported floors](https://www.concrete.org.uk/fingertips/ground-supported-floors/) je verejný odborný podklad vydavateľa príručiek pre podlahy. Vysvetľuje závislosť podlahy na vlastnostiach zeminy a potrebu zabrániť nadmernému sadaniu aj porušeniu ohybom či šmykom. Stránka bola pri prvom otvorení dostupná; opakované otvorenia hlásili timeout. Nie je to česká norma ani kontrola tejto parcely.

**Dôsledok pre tento model — inžiniersky výklad:**

- Podlahová doska prenáša svoje plošné a miestne zaťaženia do podložia. Ak dom nesú samostatné pásy/rebrá, kontrola dosky nepreukazuje bezpečnosť týchto základov.
- Ak cez dosku prechádzajú nosné steny alebo reakcie stĺpov, ktoré nemajú samostatnú podporu, musí sa overiť aj táto cesta síl. Samotný názov „podlahová“ ju z výpočtu nevylúči.
- Pri strate kontaktu je potrebný model premostenia dutiny; pri predpoklade trvalého kontaktu je potrebný dôveryhodný model podložia. Pri betónovaní dosky s rebrami spolu preveriť aj obmedzenie pootočenia, záporný ohyb a zmrašťovanie.
- Monolitické zhotovenie nevytvára automaticky dostatočnú únosnosť zeminy, kotvenie do starého pásu ani dostatočnú ohybovú výstuž.

## 3. Geometria 100 mm: vlastný výpočet

Predpoklady: nominálna hrúbka h=100 mm, krytie c=35 mm, Ø8 v oboch smeroch, prúty v mieste kríženia nad sebou. Krytie sa meria k povrchu najbližšieho prúta.

### Dve obojsmerné siete pri oboch lícach

`voľná medzera = h − 2c − 4φ = 100 − 70 − 32 = −2 mm`.

Takýto konkrétny detail sa nezmestí ani bez medzery na betón. Pri samostatných rovnobežných vrstvách a Dmax=16 mm dá odporúčané pravidlo `s_min=max(φ,20,Dmax+5)=21 mm`; jednoduchá skladba potom potrebuje `35+16+21+16+35=123 mm`. **123 mm nie je univerzálna minimálna hrúbka dosky.** Je výsledkom tejto skladby, bez miestnych presahov a osobitných detailov.

Podklad k rozstupom: [JRC EC2 worked examples, 2014](https://eurocodes.jrc.ec.europa.eu/doc/1110_WS_EC2/report/1110_WS_EC2.pdf), PDF str. 115, čl. 4.1, odkaz na EC2 8.2; [JRC EC8 worked examples](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EC8_Seismic_Design_of_Buildings-Worked_examples.pdf), tlačená str. 198, rozstupy doskových prútov podľa EC2 8.2. Nejde o medzeru medzi dotýkajúcimi sa, navzájom kolmými drôtmi jednej zváranej siete.

### Jedna obojsmerná sieť

| Poloha siete | Osi prútov zospodu [mm] | d pri ťahu dole [mm] | d pri ťahu hore [mm] |
|---|---:|---:|---:|
| Pri spodnom líci, c=35 | 39 / 47 | 61 / 53 | 39 / 47 |
| Sústredená okolo stredu h/2 | 46 / 54 | 54 / 46 | 46 / 54 |
| Pri hornom líci, c=35 | 53 / 61 | 47 / 39 | 53 / 61 |

Pri sieti dole je 53 mm konzervatívne d pre **kladný** ohyb v oboch smeroch. Nemožno ho bez zmeny použiť na záporný ohyb: nepriaznivejší smer má d=39 mm. Pri stredovej sieti je konzervatívne d=46 mm pre oba smery aj znamienka, za predpokladu presnej polohy. Jedna sieť teda má ohybovú odolnosť, ale nie rovnakú ako dvojica sietí pri lícach. Výšku siete treba zabezpečiť dištanciami; pri 100 mm je chyba polohy významná.

## 4. Otvorené výpočtové podklady

[JRC, J. Walraven: Eurocode 2 presentation, 2008](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1992_1_Walraven.pdf), PDF str. 10, 52, 66–72: materiál C16/20 `fck=16`, `fctm=1.9`, `fctk,0.05=1.3 MPa`, `Ecm≈29 GPa`; obdĺžnikový tlakový blok λ=0.8, η=1; šmyk a podmienky redukcie pri zaťažení blízko podpory. Pre vzťah k používať **d v mm**, ako v novšom číselnom príklade JRC 2014 PDF str. 71; stará prezentácia má pri tomto vzťahu chybný text jednotky.

Pracovné vzťahy pre obdĺžnikový pás b, mm/MPa/N:

`fcd=αcc fck/γc; fyd=fyk/γs; As=(πφ²/4)(1000/s)`.

`x=As fyd/(0.8 b fcd); z=d−0.4x; MRd=As fyd z`.

Pred použitím fyd overiť kompatibilitu pretvorení a ťažnosť; hranica x/d=0.45 je samostatná návrhová voľba viazaná na postup analýzy, nie univerzálna hranica platnosti každého železobetónového prierezu. Národné αcc a ďalšie súčinitele neboli z českého NA overené.

Pre nulový osový tlak:

`VRd,c=max[(0.18/γc) k (100ρl fck)^(1/3), 0.035 k^(3/2) √fck] b d`,

`k=min[2,1+√(200/d)]; ρl=min[As/(bd),0.02]`.

[Concrete Centre: Worked Examples to Eurocode 2](https://www.concretecentre.com/TCC/media/TCCMediaLibrary/Events/Online%20course/CCIP_Worked_Examples_EC2.pdf), PDF str. 53–55, dokladá oba členy šmykovej odolnosti a `As,min=max[0.26 fctm/fyk,0.0013] b d`. Je to odborný britský príklad; jeho NA nemožno vydávať za český. Minimálna ohybová výstuž sama nepreukazuje obmedzenie trhlín zo zmrašťovania.

Redukcia príspevku miestneho zaťaženia blízko podpory vyžaduje skutočné priame podopretie a zakotvenie. Nepoužiť ju automaticky pre neoverený zásyp alebo odhadnuté „15 cm uloženie“. Samostatne preveriť pretlačenie, okraje, prestupy, trhliny a priehyb.

[JRC EC2 worked examples, 2014](https://eurocodes.jrc.ec.europa.eu/doc/1110_WS_EC2/report/1110_WS_EC2.pdf), PDF str. 104–111: SLS treba posúdiť cez trhlinovú tuhosť, dotvarovanie a `wk=sr,max(εsm−εcm)`. PDF str. 25–27 opisuje voľbu krytia podľa expozície, životnosti a realizácie; národné pravidlá sa môžu líšiť. Z tohto príkladu nemožno prevziať jeho triedu betónu alebo krytie ako povinné hodnoty pre tento dom.

## 5. Kotvenie a údaj 150 mm

[JRC Walraven, PDF str. 145–146](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1992_1_Walraven.pdf) uvádza `lb,rqd=φσsd/(4fbd)` a `lbd=α1α2α3α4α5 lb,rqd ≥ lb,min`. [Concrete Centre, PDF str. 60–61](https://www.concretecentre.com/TCC/media/TCCMediaLibrary/Events/Online%20course/CCIP_Worked_Examples_EC2.pdf) rozpisuje `fbd=2.25η1η2fctd`, dobré/zhoršené podmienky a návrhové napätie pri začiatku kotvenia. **Tlačený číselný príklad tam miestami obsahuje nezrovnalosti; nižšie sú vlastné prepočty zo vzťahov.**

Pri C16/20, αct=1, γc=1.5, η1=η2=1 a B500, γs=1.15:

`fctd=1.3/1.5=0.8667 MPa; fbd=1.95 MPa; fyd=434.7826 MPa; lb,rqd=55.7414φ`.

| Ø [mm] | lb,rqd pri plnom fyd [mm] | max(0.3lb,rqd,10φ,100) [mm] |
|---:|---:|---:|
| 8 | 446 | 134 |
| 10 | 557 | 167 |
| 12 | 669 | 201 |
| 14 | 780 | 234 |
| 16 | 892 | 268 |

Minimum nie je výsledná požadovaná kotevná dĺžka. [Primárny CEN corrigendum EN 1992-1-1:2004/AC:2010 zverejnený SIA, PDF str. 11, oprava 46](https://cms.sia.ch/en/api/getMedia/492) priamo potvrdzuje nerovnosť `lb,min≥max(0.3lb,rqd;10φ;100 mm)`. Ide o pôvodný opravný dokument EN, nie české konsolidované znenie/NA. Český vysvetľujúci podklad je aj [ČVUT, kotvenie a presahy, str. 1–2](https://people.fsv.cvut.cz/www/holanjak/vyuka/pomucky/vykresy/DCV1_kotveni_a_presahy.pdf).

Vlastný príklad: 150 mm rovného Ø8, pri všetkých α=1 a uvedenej súdržnosti, zodpovedá iba `σsd=4×1.95×150/8=146.25 MPa`, nie plnému fyd. Toto **nie je únosnosť skutočného spoja**: treba zistiť, či 150 mm znamená presah betónu, dĺžku prúta, uloženie, drážku alebo iný rozmer; či prút pokračuje, je ohnutý alebo využíva priečne zvárané prúty; a kde vzniká potrebná ťahová sila. Spoločná betonáž nenahrádza tento detail.

## 6. Čo nemožno tvrdiť

[Svaz výrobců betonu ČR, český sprievodca, PDF str. 2, T2](https://www.transportbeton.cz/uploads/sources/publikace/b4f7788fc9d77f683e02bc6f2e4637f1_pruvodce-betonarskou-normou-csn-en-206-a2-pdf.pdf) pre 50 rokov uvádza C16/20 pre XC1 aj XC2. Preto nie je podložený plošný zákaz C16/20 vo všetkých českých základoch. Tabuľka však nedokazuje 100 rokov ani splnenie expozície mokrej/mrznúcej terasy alebo zasolenej garáže.

Zo zdrojov nevyplýva univerzálna minimálna hrúbka platná pre každú dosku. Pre tento dom musí výsledok jasne rozlišovať: **geometria výstuže**, **odolnosť konkrétneho prierezu**, **správanie dosky na konkrétnom podloží** a **bezpečnosť celého domu vrátane pôvodných pásov**. Posledné dve úrovne nemôže nahradiť samotný vyhovujúci ohyb metrového pásu.
