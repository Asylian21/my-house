# Štyri rebrá a požiadavka na 100 mm dosku — audit nosných ciest

**Revízia AK-01/AK-02, 16. 9. 2026:** aktuálne je SM30, jedna 300 mm obvodová tehla so zachovaným účelom odhlučnenia. Táto štúdia používa zmrazené pôvodné zaťaženia SA30; výsledky pre stenové zaťaženia a R7 sa nepovažujú za prepočet SM30. Konkrétny výrobok a nový prepočet zostávajú otvorené. Samostatné geometrické kóty a výpočty bez stenového zaťaženia týmto nie sú prerátané. Pozri [záznam revízie](/Users/davidzita/www/dom/foundation-analysis/inputs/wall-revision-sm30-20260916.md).

16. 9. 2026. **Kontrola modelovej geometrie a samostatný referenčný prepočet starého zaťaženia; nie realizačný statický návrh ani schválenie 100 mm dosky.**

## Rozhodujúci výsledok

Z dostupných podkladov sa nedá potvrdiť, že 100 mm ŽB doska C16/20 spolu so štyrmi rebrami a existujúcimi pásmi unesie dnešný dom. Chýba uzavretý prenos zaťaženia do základovej zeminy. To samo osebe nie je dôkaz, že každá 100 mm podlahová doska musí zlyhať: doska na spoľahlivom podloží a doska nesúca dom cez voľné rozpätia sú odlišné konštrukcie.

Aktuálne dohodnuté sú polohy **R7, R1, R2, R4**. Pracovná šírka 350 mm je prevzatá zo starej štúdie. Následná odpoveď používateľa udáva celkovú výšku rebier 400 mm vrátane 100 mm dosky. To nemení výsledok nižšie uvedenej pôdorysnej kontroly. Výška, šírka ani trieda betónu nenahrádzajú návrh podopretia, výstuže a detailov spojov.

Výsledky `foundation-results.json` patria k **17 trasám, novým vnútorným základom a samostatným blokom P1–P6**. Neprenášajú sa na aktuálnu štvoricu rebier, na nové osadenie obvodu ani na 100 mm dosku. Počas tohto auditu sa stará geometria, aplikácia, hlavný report ani staré výpočty nemenili.

## 1. Čo geometricky pokrývajú štyri rebrá

Kontrola používa 37 vnútorných stenových obdĺžnikov z `inputs/geometry.json` a presné body štyroch rebier z `inputs/client-agreed-layout.json`. Pôdorysný prienik sa počíta bez prídavnej tolerancie. Za „úplne pokryté“ sa považuje celý uložený obdĺžnik steny, nie iba jej os; neskoršie dodatočné povrchové vrstvy geometrický vstup nerozširuje. Ani úplné pokrytie nie je dôkazom skutočného uloženia alebo únosnosti.

| Pôdorysný kandidát | Úplne pokryté steny | Čiastočne | Bez pokrytia | Os stien mimo kandidáta |
|---|---:|---:|---:|---:|
| Len štyri rebrá, b = 350 mm | 6 | 10 | 21 | 44,1325 m z 61,1650 m |
| Štyri rebrá + pôvodný horný obvod b = 350 mm | 6 | 15 | 16 | 44,0075 m z 61,1650 m |

Úplné pokrytie majú len dva úseky SA30 na R7, dve nosné steny pri izbách na R1 a dva úseky kuchynskej nosnej steny na R2. R4 podopiera zadnú fasádnu líniu NN2, ktorá nie je medzi 37 vnútornými stenami. Čiastočné pokrytie často znamená iba 25 mm konca steny alebo priečne kríženie 350 mm rebrom; nemožno ho považovať za podopretie zvyšnej steny. Napríklad malý `C-WC-DOOR-JAMB` má celú os v prieniku, ale len 54,35 % obdĺžnika — preto nie je vykázaný ako úplne pokrytý.

Podrobná bilancia všetkých 37 úsekov: `four-rib-wall-coverage.csv` a `four-rib-load-path-audit.json`. Súčet predpokladaných vlastných tiaží zo starej štúdie je 166,656 kN pre šesť úplne pokrytých stien a 336,976 kN pre ostatných 31 stien. Druhé číslo je súčet **celých** týchto stien, nie vypočítaná sila do dosky alebo reakcia jednotlivých rebier. Hmotnosti výrobkov a povrchov ostávajú predpokladmi.

### Rozhodujúce chýbajúce línie

| Stena/línia | Modelová poloha a dĺžka | Predpoklad vlastnej tiaže starej štúdie | Pokrytie štyrmi rebrami |
|---|---|---:|---|
| `C-ENTRY-OFFICE-EAST`, model LOAD_BEARING | X = 23,4545 m; Y = 3,504–5,195 m; L = 1,691 m | 8,250 kN/m; celkom 13,951 kN | Žiadne; s pôvodným horným obvodom iba 25 mm začiatku |
| `C-ENTRY-OFFICE-RETURN`, model LOAD_BEARING | Y = 5,2825 m; X = 22,842–23,542 m; L = 0,700 m | 8,250 kN/m; celkom 5,775 kN | Žiadne; obe vstupné nosné steny patrili k vynechanému R3 |
| H200 `IW-STUDY-NORTH`, model PARTITION | Y = 6,502 m; X = 22,783–27,541 m; L = 4,758 m | 5,212 kN/m; celkom 24,797 kN | Žiadne; pri pridaní pôvodného horného obvodu len 25 mm východného konca |
| `C-GARAGE-SPINE-N`, 301 mm, model PARTITION | X = 10,9925 m; Y = 5,844–10,699 m; L = 4,855 m | 12,975 kN/m; celkom 62,994 kN | Žiadne; s pôvodným horným obvodom len 25 mm severného konca |
| Zadná garážová fasáda `L` | Os jadra Y = 8,897 m; X = 6,940–10,640 m; hrubá línia 3,700 m; plné úseky 2,450 m + otvor 1,250 m | Konečné murivo, nadpražie a reakcie strechy chýbajú | Žiadne; samostatná línia pôvodného R5 je vynechaná |
| Kúpeľňové, WC, šatníkové a priečne izbové steny | Pozri CSV, väčšinou šírka 139–144 mm | Stará štúdia približne 6,9–7,09 kN/m | Prevažne bez priebežného rebra; lokálne kríženia nie sú priebežnou podporou |

Modelový štítok LOAD_BEARING je projektový zámer, nie zistená reakcia strechy. PARTITION neznamená zanedbateľnú vlastnú tiaž. Pri H200 sa v predchádzajúcej štúdii použilo 170 kg/m² vrátane predpokladu 8 kg/m² pre doplnky; nie je to vážená dodávka ani potvrdený výrobok.

## 2. Obvod: osy sa po novom výklade neprekrývajú

Modrá čiara je používateľom deklarovaný **približný stred spodného betónu** v súradnicovom rámci modelu. Sivá je pôvodná os navrhovaného horného obvodu. Výpočet geometrického prieniku predpokladá presné osadenie podľa týchto čiar, rovnomerné obdĺžnikové prierezy a spoločnú styčnú výšku. Ide o kontrolu geometrie na priamych úsekoch mimo rohov.

`presah = max(0; B_spodný/2 + b_horný/2 − |rozdiel osí|)`

| Strana | Rozdiel osí | Presah: dolný 400 / horný 350 mm | Presah: dolný 380 / horný 350 mm |
|---|---:|---:|---:|
| Ľavá | 354 mm | 21 mm | 11 mm |
| Uličná | 354 mm | 21 mm | 11 mm |
| Pravá | 349 mm | 26 mm | 16 mm |
| Zadná | 350 mm | 25 mm | 15 mm |
| Vodorovný návrat pri dvore | 351 mm | 24 mm | 14 mm |
| Vnútorná zvislá strana krídla | 353 mm | 22 mm | 12 mm |

To je len 6,0–7,4 % šírky horného 350 mm obvodu pri spodnom 400 mm páse, resp. 3,1–4,6 % pri 380 mm. **Nie je to dovolená styčná plocha ani výpočet kontaktného napätia.** Tieto čísla nemožno použiť ako jednoduchú excentricitu celého domu alebo vložiť bez ďalšieho do vzťahu B − 2e: chýba najprv fyzický model prenosu zo steny/horného pásu na spodný pás.

Pôvodné červené konce sa zachovali. Pri plochých koncoch rebier a idealizovanom spodnom 400 mm obvode nemá žiadne zo štyroch rebier pôdorysný prienik so spodným betónom; najmenšia medzera obálok je 151 mm pre R1/R7 a 149 mm pre R2/R4. Je to ďalší doklad, že kresba nie je detailom uloženia. Pôvodný horný obvod môže rebrá v modeli spájať, ale jeho vlastné uloženie na spodný betón ostáva nevyriešené.

Pri R2 je os Y = 10,862 m, kým L-roh modrého obvodu je Y = 11,200 m; rozdiel 338 mm. Samotné vodorovné predĺženie jeho osi preto netrafí zvislý L-bok začínajúci až v Y = 11,200 m. Žiadna nová poloha, rozšírenie alebo nosný detail sa v audite nevymýšľa.

Následné označenie používateľa „30 cm betón hore ako šalung“ a drážka/zarážka hlboká 150 mm neurčuje jednoznačne smer rozmerov ani výslednú styčnú geometriu. Tabuľka vyššie preto zostáva výslovne scenárom **horného 350 mm** prvku; nevyhlasuje sa za skutočný nový detail.

## 3. Ťažké zariadenia a vonkajšie podpery

Modelové obálky AKU800, kotla, kachlí, paliet/vreciek s peletami a ostrova nepretínajú štyri rebrá. Najmenšie pôdorysné vzdialenosti obálok k rebrám sú: AKU800 85 mm, kotol 1 648 mm, kachle 135 mm, pelety 2 216 mm, ostrov 1 843 mm. Nejde o vzdialenosti skutočných nôh ani o dôkaz potreby konkrétneho typu základu.

- AKU800: samotná voda 7,848 kN; nádrž, príslušenstvo a nohy neznáme.
- Kotol so zásobníkom: v modeli 180 kg peliet; suchá a prevádzková hmotnosť, kontakt a umiestnenie nôh neznáme.
- Kachle/komín a ostrov: konečné hmotnosti a kontaktné plochy neznáme.
- Podpery terasy a L-pilier lodžie: model obsahuje obálky, nie overené reakcie ani pätky. Staré P4–P6 zo 17-trásovej štúdie nie sú automaticky súčasťou štyroch rebier.

Ak budú tieto prvky na 100 mm doske, potrebujú vlastné lokálne posúdenie dosky a podložia alebo konkrétne navrhnutú podporu. Stará štúdia ich z dosky odvádzala do samostatných blokov; tento predpoklad sa nesmie stratiť.

## 4. Samostatný referenčný prepočet pôvodného zaťaženia

Zdroj: pôvodná statika `arch-docs/projektova dokumentace/D_Vykresova dokumentace/D2_Statika/D.2.001-00 - TZ + SV .pdf`, fyzické strany 40–42. Pôvodný príklad mal pás 800 mm, hĺbku 1,20 m, Nser = 48,57 kN/m, NEd = 68,00 kN/m a nulové M/H. Hodnota Rd = 150 kPa bola vstupom pôvodného modelu, nie novým miestnym meraním.

Nasleduje iba delenie **starých** síl šírkou centricky zaťaženého pásu, bez vlastnej tiaže základu a nadložia:

| B | Nser/B | NEd/B | (NEd/B)/150 kPa |
|---|---:|---:|---:|
| 800 mm, pôvodný pás | 60,71 kPa | 85,00 kPa | 56,7 % |
| 400 mm, referenčný scenár | 121,43 kPa | 170,00 kPa | 113,3 % |
| 380 mm, referenčný scenár | 127,82 kPa | 178,95 kPa | 119,3 % |

Pri zachovaní pôvodného NEd je potrebná šírka už iba z 68/150 = **453,3 mm**, stále bez ďalších tiaží a bez excentricity. To vysvetľuje, prečo staré schválenie 800 mm pásu nepotvrdzuje dnešných 380–400 mm. Nie je to nový návrh šírky ani automatický rozsudok nad každým možným upraveným domom.

Pôvodný výsledok qEd = 123,47 kPa na 800 mm zahŕňal tiež vlastnú tiaž pásu a nadložie; výstup uvádza G = 10,87 kN/m a Z = 7,56 kN/m. Hodnotu 123,47 preto **neškálujeme pomerom 800/400** a nepreberáme tieto tiaže do geometricky iného dnešného pásu. Rovnako sa neprenáša pôvodné sadanie 3,4 mm.

## 5. Čo rozhoduje o definitívnom závere pre 100 mm

1. **Skutočná geometria a styky:** obe líca, horná a spodná výška existujúceho betónu, absolútne uloženie muriva, nový horný prierez, význam 300 mm a 150 mm drážky, dĺžky uloženia/kotvenia a riešenie L-rohu.
2. **Nosný systém:** či sú rebrá založené na prirodzenej zemine, na zásype alebo nesené iba koncami; ktoré steny nesie doska; kde ležia zaťaženia strechy, povaly, oceľových rámov a vonkajších podpier. Priamy prenos cez neoverený zásyp nie je automaticky preukázaný základ.
3. **Zemina a zásyp:** miestny geotechnický profil, únosnosť a deformácie pod starými aj novými prvkami, voda, sadanie a nerovnomernosť. Deklarovaná miestna hlina/piesok „zhutnené“ neurčuje zrnitosť, vlhkosť, hrúbky vrstiev, objemovú hmotnosť ani modul podložia.
4. **Zaťaženia:** dnešné murivo a výšky, strešné/stropné reakcie, presné využitie povaly, sneh/vietor v aktuálnej nosnej sústave, zariadenia a vozidlo vrátane kolies/zdviháka.
5. **Doska 100 mm a rebrá:** výstuž, krytie, kamenivo, spoje a presahy, pracovné/dilatačné škáry, prestupy, okraje, trhliny, deformácie, šmyk/prerazenie a uvažovaná strata kontaktu s podložím. Z pevnostnej triedy C16/20 a hrúbky samotnej sa únosnosť zostavy nedá určiť.
6. **Existujúci betón a spoj:** pevnosť/skutočná výstuž, stav styčnej plochy, prípadné kotvy, okrajové vzdialenosti a konkrétny overiteľný prenos síl; predchádzajúci súosý detail je po novom výklade prekonaný.

## Reprodukcia

Skript `calculations/four_rib_load_path_audit.py` číta len vstupy a staré predpoklady tiaží a zapisuje vlastné nové JSON/CSV. Pri tomto audite bol spustený cez:

```text
/Users/davidzita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 foundation-analysis/calculations/four_rib_load_path_audit.py
```

Kontrola: 37 stien, práve R1/R2/R4/R7, pracovná šírka 350 mm; súradnicové prieniky bez dodatočného rozšírenia. SHA-256 použitých vstupov je v novom JSON. **Neboli vykonané sondy, meranie, skúšky betónu/zeminy ani definitívny výpočet stavby.**
