# Štyri rebrá 350 × 400 mm na priebežne podopierajúcej zemine

**Revízia AK-01/AK-02, 16. 9. 2026:** aktuálne je SM30, jedna 300 mm obvodová tehla so zachovaným účelom odhlučnenia. Táto štúdia používa zmrazené pôvodné zaťaženia SA30; výsledky pre stenové zaťaženia a R7 sa nepovažujú za prepočet SM30. Konkrétny výrobok a nový prepočet zostávajú otvorené. Samostatné geometrické kóty a výpočty bez stenového zaťaženia týmto nie sú prerátané. Pozri [záznam revízie](/Users/davidzita/www/dom/foundation-analysis/inputs/wall-revision-sm30-20260916.md).

**Podmienená citlivostná analýza podľa výslovného predpokladu používateľa: rebrá sú priebežne podopreté zhutnenou zeminou. Nie je to voľný nosník nesený iba na koncoch.** Rozsah je vlastná tiaž a priamo súosé modelové steny; chýbajúce ostatné zaťaženia sa nepovažujú za nulové.

## Model

- Konečný Eulerov–Bernoulliho nosník na spojitých Winklerových pružinách: `EI·w⁽⁴⁾ + ks·b·w = q(x)`, tlak `p = ks·w`. Oba konce sú voľné, M = V = 0. Nevytvára sa tak nepreukázaná podpora v dnešnom obvode. Dĺžky 7,495/6,298 m tu znamenajú dĺžku priebežne podopretého pásu, nie voľné rozpätie.
- Pracovný pôdorysný kontakt b = 350 mm po celej dĺžke; rovnaká výška a tuhosť podkladu, bez dutín a vynúteného sadania. Samostatný pás nepreukazuje skutočný spoj s obvodom ani kompatibilitu so susednou doskou.
- Celková výška 400 mm zahŕňa 100 mm dosku. Vlastná tiaž je **3,500 kN/m = 2,625 + 0,875 kN/m**; pruh dosky v šírke rebra je započítaný raz. Širšia neznáma zaťažovacia plocha dosky sa nepriraďuje.
- Presné intervalové tiaže stien sú načítané z predchádzajúceho vstupu; jeho voľné uloženie ani vnútorné sily sa nepreberajú. Pri R4 je zahrnuté predpokladané murivo nad otvorom, nie neznáma vlastná tiaž nadpražia a reakcie strechy.
- Predpokladané **ks = 5 / 10 / 20 / 50 MN/m³** predstavujú citlivosť. Nie sú skúškou miestnej zeminy ani únosnosťou podložia. Hlina/piesok a „zhutnené“ neurčujú ks.
- Pre každé ks sa skúša okamžitá tuhosť neporušeného obdĺžnika a dve konštantné plne popraskané tuhosti s 3Ø16/4Ø16 a predpokladaným dotvarovaním φ = 2,5. Nie je to predikcia trhlín alebo záruka, že tieto hodnoty ohraničia každú odozvu.

| Scenár tuhosti | EI [kNm²] |
|---|---:|
| gross_instantaneous | 53386.7 |
| cracked_sustained_3phi16 | 7870.1 |
| cracked_sustained_4phi16 | 9587.3 |

## Výsledky — obálka tuhostí pri jednotlivých ks

w a p sú pre zahrnuté charakteristické stále tiaže Gk. MEd/VEd sú tieto výsledky násobené 1,35. Záporný M je horný ťah. Rotácia je najväčší miestny sklon, nie posúdenie relatívneho sadania celého domu.

| Rebro | ks [MN/m³] | max w [mm] | max p(Gk) [kPa] | max absolútne MEd [kNm] | max absolútne VEd [kN] | max sklon [mrad] |
|---|---:|---:|---:|---:|---:|---:|
| R7 | 5 | 5.230 | 26.15 | 4.569 | 3.670 | 0.232 |
| R7 | 10 | 2.630 | 26.30 | 4.162 | 3.594 | 0.170 |
| R7 | 20 | 1.309 | 26.19 | 3.618 | 3.486 | 0.126 |
| R7 | 50 | 0.535 | 26.76 | 2.836 | 3.305 | 0.085 |
| R1 | 5 | 8.757 | 43.78 | 12.063 | 9.008 | 0.651 |
| R1 | 10 | 4.448 | 44.48 | 10.870 | 8.741 | 0.459 |
| R1 | 20 | 2.216 | 44.32 | 9.278 | 8.370 | 0.327 |
| R1 | 50 | 0.891 | 44.56 | 7.010 | 7.768 | 0.213 |
| R2 | 5 | 7.966 | 39.83 | 13.898 | 10.500 | 1.886 |
| R2 | 10 | 4.202 | 42.02 | 12.793 | 9.936 | 1.282 |
| R2 | 20 | 2.208 | 44.16 | 11.071 | 9.047 | 0.810 |
| R2 | 50 | 0.930 | 46.50 | 8.009 | 7.425 | 0.397 |
| R4 | 5 | 9.827 | 49.14 | 4.520 | 7.440 | 1.232 |
| R4 | 10 | 4.872 | 48.72 | 4.365 | 7.356 | 0.736 |
| R4 | 20 | 2.400 | 47.99 | 4.106 | 7.204 | 0.464 |
| R4 | 50 | 0.933 | 46.66 | 3.798 | 6.829 | 0.260 |

Každá bunka je obálka troch tuhostí, preto nie celý riadok jednej fyzickej zostavy. Všetkých 48 samostatných prípadov vrátane znamienok M, minima tlaku a integrálu reakcií obsahuje JSON/CSV.

## Porovnanie prierezu bez predpisovania výstuže

Pre identický obdĺžnik z predchádzajúceho prierezového výpočtu: MRd = 80,69 kNm (3Ø16) a 102,77 kNm (4Ø16), VRd,c = 51,29 a 56,46 kN. Platí prijaté C16/20, B500, krytie 35 mm ku strmeňu Ø8 a plné rozvinutie napätia v prútoch. Porovnanie kladného M predpokladá výstuž dole; pre záporný M musí byť rovnaká účinná vrstva hore. Skutočná horná výstuž a kotvenie nie sú určené.

| Rebro | Najväčšie absolútne MEd, všetky prípady [kNm] | Pomer k MRd 3Ø16, len s účinnou výstužou na ťahovej strane | Najväčšie VEd [kN] |
|---|---:|---:|---:|
| R7 | 4.569 | 5.66 % | 3.670 |
| R1 | 12.063 | 14.95 % | 9.008 |
| R2 | 13.898 | 17.22 % | 10.500 |
| R4 | 4.520 | 5.60 % | 7.440 |

**Čítanie výsledku:** táto priebežná podpora podstatne mení vnútorné sily oproti voľnému nosníku. Prípadné vyhovenie týchto čiastkových M/V porovnaní však potvrdzuje iba zvolený obmedzený výpočtový scenár; neschvaľuje rebro, 100 mm dosku ani dom.

## Overenie výpočtu

- Konzistentná spojitá pružinová matica, štandardné kubické nosníkové prvky; hranice zaťažených úsekov sú uzlami siete. Priehyb, tlak a vnútorné sily sa vyhodnocujú aj v analyticky nájdených vnútorných extrémoch.
- Kontrola rovnováhy celkovej zvislej sily a momentu, nulových koncových síl a rezídua lineárnej sústavy.
- Nezávislé presné riešenie pri plnom rovnomernom zaťažení: w = q/(ks·b), nulové M/V a sklon, ľubovoľné EI.
- Sieť do 100 mm oproti sieti do 50 mm: najväčšia relatívna zmena sledovaného extrému **0.13435 %**.
- Najväčšia relatívna chyba rovnováhy sily **4.751e-09**, momentu **4.200e-09**.
- Kontrola kontaktu: všetkých 48 prípadov má iba tlakové reakcie: **áno**. Ide o kontrolu vypočítaného stavu, nie dôkaz fyzického kontaktu na stavbe.

## Rozsah a chýbajúce údaje

**Stena mimo štyroch rebier nie je automaticky bez nosnej cesty.** Pri priebežne podopretej podlahovej doske môže zaťaženie prechádzať zo steny cez dosku do zeminy. Pôdorysný audit 37 stien preto neurčuje povinnosť doplniť rebro pod každú priečku a sám nepreukazuje zlyhanie; príslušnú 100 mm dosku a podložie treba posúdiť pre tieto stenové zaťaženia.

Na konečné posúdenie zostávajú: overené vlastnosti a vrstvy zásypu/základovej zeminy, vlhkosť, organické prímesi, kvalita zhutnenia a dlhodobé/nerovnomerné sadanie; skutočná geometria podpory; reakcie strechy a povaly, užitné a bodové zaťaženia; prenos mimo rebier cez 100 mm dosku; spoje so starým obvodom a L-roh; výstuž na oboch potrebných ťahových stranách a kotvenie; trhliny, zmrašťovanie, prerazenie, prestupy, škáry a trvanlivosť. Stará hodnota Rd = 150 kPa sa nepoužíva ako schválenie vypočítaných tlakov.

Winklerove pružiny nemodelujú vzájomné pôsobenie susedných pásov alebo súvislého objemu zeminy. Výsledné w je deformácia ideálneho pružinového podložia, nie úplná prognóza sadania budovy. Šmykové deformácie nosníka a 2D pôsobenie dosky sa v tomto obmedzenom modeli nezapočítali.

Metodické zdroje: [PyCBA — beam on an elastic Winkler foundation](https://ccaprani.github.io/pycba/notebooks/foundation.html) pre spojitú pružinovú podporu a voľné konce; [JRC — EC2 worked examples](https://eurocodes.jrc.ec.europa.eu/doc/1110_WS_EC2/report/1110_WS_EC2.pdf) pre prierezové vzťahy. Použitie týchto vzťahov nie je normovou autorizáciou konkrétnej stavby.

Reprodukcia:

```text
/Users/davidzita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 foundation-analysis/calculations/four_rib_ground_support.py
```

Výstupy: `four-rib-ground-support.json`, `four-rib-ground-support-summary.csv`, `four-rib-ground-support-traces.csv`. Pôvodné vstupy, staré výsledky a report sa nemenia.
