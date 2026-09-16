# Hlavný vstup D2 — priestorový a výškový podklad

Stav 14. 09. 2026: **COORDINATION_PROPOSAL — priestorový návrh na zakreslenie do doplnkovej dokumentácie, nevydané na realizáciu.** Overené je aktuálne C/B/B. Táto správa nemení dom, jeho pôdorys, kódy otvorov, existujúci prístup, modelové výšky ani UI. Nový stupeň a samostatná podesta zatiaľ nie sú súčasťou 3D. Nové zadanie povaly iba na odkladanie s dreveným stropom patrí nadväzujúcej konštrukčnej koordinácii; nie je podkladom na určenie výšky vstupu.

## Overený vstup a prístup

Hlavný peší vstup je **D2**, identifikátor položky `Výplň otvoru FRONT-ENTRY`, názov „Hlavné vstupné dvere“, miestnosť `ROOM-1-01`. Kód bol overený priamym načítaním aktuálneho `CODED_OPENINGS`, nie odvodený z poradia starej tabuľky. `D1` je garážová brána; `D3 / EAST-03` je bočný vstup technickej miestnosti. [Kódovanie otvorov](</Users/davidzita/www/dom/lib/plan-export.ts:429>), [aktívna fasáda](</Users/davidzita/www/dom/lib/twin-active-house.ts:36>), [zdedený otvor FRONT-ENTRY](</Users/davidzita/www/dom/lib/twin-site.ts:973>), [Babylon — hlavné vstupné dvere](</Users/davidzita/www/dom/lib/babylon-scene.ts:5228>).

Všetky nasledujúce XY sú v zachovanom miestnom rámci domu, v mm. +Y smeruje od ulice do domu.

| Existujúci prvok | Presný modelový údaj |
| --- | --- |
| D2 — stavebný otvor | X 21 540–22 790; šírka 1 250; výška 2 250; parapet 0 |
| Vonkajšie líce južnej fasády / os 1 | Y 3 000 |
| Os otvoru a hlavného prístupu | X 22 165 |
| Najbližšie pôvodné osi | D: X 21 040; E: X 22 711 |
| D2 voči osi D | ľavý okraj +500; stred +1 125; pravý okraj +1 750 |
| Existujúca plocha `SITE-ENTRY` | X 21 415–22 915; Y −3 104–3 000 |
| Šírka / celková dĺžka prístupu | 1 500 / 6 104 |
| Presah šírky prístupu za stavebný otvor | 125 na každej strane |
| Katastrálna uličná hranica | Y 0 |
| Modelový okraj asfaltu | Y −3 104 |
| Súkromná časť prístupu | 1 500 × 3 000 = 4,500 m² |
| Napojenie cez cestnú rezervu | 1 500 × 3 104 = 4,656 m²; nie automaticky súkromný pozemok |

Prístup už má status `DESIGN_PROPOSAL_CENTERED_ON_MAIN_ENTRY`, zdroje `SRC-CLIENT-EXTERIOR-20260821`, `SRC-C3`, `SRC-D11002`. Jeho starší nepravidelný `sourceEnvelopePolygonMm` nie je dnešná hranica dlažby. Rozhoduje `polygonMm` a jeho priamy odber v aktívnom site. [Aktuálna receptúra prístupu](</Users/davidzita/www/dom/lib/twin-site.ts:1598>), [aktívne SITE_SURFACES](</Users/davidzita/www/dom/lib/twin-active-site.ts:81>), [test šírky a osi vstupu](</Users/davidzita/www/dom/tests/twin-site.test.ts:725>), [pôvodné osi](</Users/davidzita/www/dom/lib/plan-export.ts:81>).

Aktívny peší prístup a vjazd sa držia súradníc domu aj po jeho posune; neaplikovať na ne druhý posun 77,913405454 mm. Pevný pozemok a jeho hranice sa transformujú do toho istého rámca. Uličný aj pravý kolmý odstup domu zostávajú **3 000 mm**. Návrhová podesta leží v existujúcom prístupe pred domom a nemení footprint ani tieto referenčné odstupy. Ide o modelové osadenie `CLIENT_REQUESTED_SETBACK`, nie vytýčenie stavby. [Aktívna transformácia](</Users/davidzita/www/dom/lib/twin-house-placement.ts:25>), [prístupy v aktívnom rámci](</Users/davidzita/www/dom/lib/twin-active-site.ts:13>).

## Čo je dnes modelované vo výške

Pri D2 **nie je samostatná podesta ani modelovaný vstupný schod**. Je tu triangulovaná spádovaná plocha s krajnými vrcholmi M −110 mm na Y −3 104 a M −15 mm na Y 3 000. Jej výsledná rovina má sklon 95 / 6 104 = 1,556356 % k ulici. To je vizualizačné spojenie; nie výškopis ani schválený návrh nového vstupu.

Pozor na čítanie kódu: pomocná funkcia `elevationForPoint()` by pri samostatnom bode Y 0 vrátila −30 mm, ale polygon `SITE-ENTRY` taký vrchol nemá. Skutočná triangulovaná plocha má tam interpolovanú výšku **M −61,690695 mm**, na Y 1 500 potom **M −38,345347 mm**. Tieto čísla len opisujú súčasný render a nesmú určiť ΔFFL. [Vrcholová triangulácia](</Users/davidzita/www/dom/lib/babylon-scene.ts:401>), [výšky vstupnej dlažby](</Users/davidzita/www/dom/lib/babylon-scene.ts:3414>), [výslovná interpolácia skutočnej hrany pri Y 0](</Users/davidzita/www/dom/lib/babylon-scene.ts:520>).

Dva existujúce betónové stupne pri Y 22 035–22 795, so šírkou 2 400 mm a hornými modelovými úrovňami +15 / −25 mm, patria **záhradnej krytej terase**, nie D2. Ich komentár „entry steps“ sa nesmie zameniť za hlavný uličný vstup. [Krytá terasa — dva stupne](</Users/davidzita/www/dom/lib/babylon-scene.ts:5850>).

## Dvere a voľný priestor pred nimi

D2 sa v aktuálnom Babylon modeli otvárajú **dovnútra, smerom +Y**, do zádveria. Pánt je pri nižšom X; pevný bočný svetlík je na vyššom X. Hinge pivot je X **21 618**, Y **3 150**; maximálne otvorenie 90°. Nominálny polomer animácie je 900 mm (`round(1250 × 0.72)`), skutočný kváder krídla je široký 894 mm, hrubý 48 mm. Tieto modelové rozmery nie sú výrobné rozmery objednávaných dverí. [Generátor dverí a svetlíka](</Users/davidzita/www/dom/lib/babylon-openings.ts:640>), [pánt a smer otvorenia](</Users/davidzita/www/dom/lib/babylon-openings.ts:685>), [posun rámovej roviny 150 mm](</Users/davidzita/www/dom/lib/babylon-openings.ts:100>).

| Stav modelového krídla | Pôdorysný obal samotného krídla [mm] |
| --- | --- |
| Zatvorené | X 21 621–22 515; Y 3 126–3 174 |
| Otvorené na 90° | X 21 594–21 642; Y 3 153–4 047 |
| Konzervatívny obal pohybu vrátane kľučiek, zaokrúhlený von | X 21 568–22 516; Y 3 100–4 048 |

V read-only NullEngine kontrole sa použil skutočný `buildOpening()` s aktívnym `HOUSE`, registráciou animovaných dverí a všetkými pohyblivými kľučkami. Prechod 0–90° po 1° dal obal X 21 568,251–22 515,292 / Y 3 100,251–4 047,291 mm. Uvedený celočíselný obal má rezervu; smer pohybu potvrdzuje aj explicitný vzorec rotácie. Šírka modelovej priechodovej pomôcky je 894 mm; nejde o potvrdenie normovej ani výrobnej svetlej šírky.

Celá navrhovaná vonkajšia podesta končí pri líci Y 3 000, teda mimo tohto obalu. Čelo stupňa na Y 1 500 je **1 500 mm pred fasádou**, **1 650 mm od osi pántu** a najmenej **1 600 mm od konzervatívneho obalu pohybu**. Schod preto nekoliduje s aktuálne modelovaným otváraním. Nezakresľovať oblúk otvárania na vonkajšiu podestu ani nemenovať stranu dverí iba nejednoznačným „ľavé/pravé“ bez určenia pohľadu.

Rám začína v exteriérovom smere na Y 3 075; medzi fasádou a ním ostáva 75 mm hlboké ostenie. Jeho povrchové napojenie na podestu treba vyriešiť pri prahu, bez plošného rozširovania navrhovanej podesty dovnútra obrysu domu.

## Jednostupňový priestorový návrh

Podesta je navrhnutá v už existujúcej šírke prístupu. Rozmer 1 500 mm je priestorová voľba pre koordináciu, nie tvrdenie o úplnom normovom posúdení či bezbariérovom vstupe. Nemení sa D2, prístupová os, fasáda ani hranice domu.

| Návrhový prvok — status COORDINATION_PROPOSAL | XY / rozmer |
| --- | --- |
| Horná podesta | X 21 415–22 915; Y 1 500–3 000; 1 500 × 1 500 mm, 2,250 m² |
| Jediné čelo stupňa | úsečka (21 415, 1 500) → (22 915, 1 500); šírka 1 500 mm |
| Výška jediného stupňa | h = 150 mm medzi spodným prístupom a hornou hranou podesty na tej istej čiare Y 1 500 |
| Spodný súkromný prístup | X 21 415–22 915; Y 0–1 500; nadväzuje na existujúci koridor k ulici |
| Smer nástupu | od ulice k domu, +Y; 1 výškový stupeň, potom podesta |
| Poloha voči pôvodnej osi 1 | čelo stupňa 1 500 mm pred osou; podesta končí na osi 1 |

**Nekresliť druhý samostatný „nášľap“ 300–380 mm**, ktorý by vytvoril druhú výškovú úroveň. Pri tomto návrhu sa po prekonaní jediného čela stúpa priamo na hornú podestu. Skladba, založenie, hrana stupňa, protišmyk, odvádzanie vody a bočné ukončenia zatiaľ nie sú navrhnuté touto správou.

## Výškový vzťah — podesta nie je ulica R0

R0 je stavebníkom oznámený najvyšší bod ulice pri pracovni s hodnotou 184,200 m. Nie je to úroveň prístupu pod stupňom, vonkajšia podesta ani prah D2. M0 je zachovaná podlaha modelu. Absolútna realizovaná výška podlahy a priame výškové spojenie všetkých týchto bodov nie sú doložené. [Výškový podklad a stav merania](</Users/davidzita/www/dom/docs/construction-height-basis.md:1>).

Nech `d` je rozdiel FFL mínus podesta pri prahu, `s` pozdĺžny sklon podesty smerom von v mm/mm, `L = 1500 mm` hĺbka od fasády po čelo a `h = 150 mm` výška čela. Výšky sa porovnávajú na osi X 22 165; detail 75 mm ostenia sa dopracuje s výrobcom dverí.

```text
FFL − podesta pri dverách = d
FFL − podesta na hornej hrane stupňa = d + s × L
FFL − prístup bezprostredne pod stupňom = d + s × L + h

ΔFFL_mm = (výška prístupu pod stupňom − R0)_mm + d + s × L + h
```

Pre prvé priestorové porovnanie možno použiť **pracovnú alternatívu d = 20 mm a s = 2 % = 0,02**, so spádom od domu. Potom je pokles podesty 30 mm a rozdiel FFL k prístupu pod čelom **20 + 30 + 150 = 200 mm**. V zachovanom modelovom rámci by tieto čisto podmienené povrchové hladiny boli M −20 mm pri dverách, M −50 mm na hornej hrane stupňa a M −200 mm tesne pod stupňom. **Nie sú to prijaté realizačné kóty a nesmú sa predvoliť v modeli ani uložiť ako známe ΔFFL.** Výška R0 sa do nich nedosádza namiesto neznámej miestnej výšky prístupu.

Odporúčanie pre základný dátový záznam a list: h = 150, L = 1500 a XY podesty uviesť ako návrh; `d`, `s`, výšku prístupu voči R0 a ΔFFL ponechať neurčené. Číselný príklad 20 mm / 2 % uviesť iba pri označení „pracovné porovnanie prahového detailu“. Samotný schod 150 mm neurčuje podlahu na R +0,150 ani na 184,350 m.

### Prečo nemožno prevziať prah z 3D

Generátor súčasne kreslí **spodný priečnik zárubne M 0–78 mm** cez svetlú šírku rámu a samostatný **prah M 0–20 mm**. Oba ležia X 21 618–22 712 / Y 3 075–3 225; krídlo začína na M +6 mm. Toto prekrytie je modelová stolárska reprezentácia, nie vyriešený nízky prah. [Spodný rám vo frameRing](</Users/davidzita/www/dom/lib/babylon-openings.ts:176>), [jeho použitie pri dverách](</Users/davidzita/www/dom/lib/babylon-openings.ts:641>), [samostatný prah](</Users/davidzita/www/dom/lib/babylon-openings.ts:682>).

Z uvedeného 20 mm modelového kvádra preto nemožno vyvodiť požadovaný rozdiel hotovej podesty a FFL. Pracovných d = 20 mm je samostatná koordinačná voľba, ktorú treba potvrdiť s prahovým systémom, tesnením, povrchmi a odvodnením. Do uzavretia detailu ponechať rozdiel neurčený. Táto správa neodstraňuje ani neopravuje existujúce rámové objekty.

## Podklad na doplnenie listu

Na existujúci koordinačný list zakresliť pôdorys podesty s pôvodnými súradnicami a osou D2, čelo Y 1 500, šírku/hĺbku 1 500/1 500, h = 150 a schematický vzťah `d + sL + h`. Označiť „návrh, nie stav modelu“. Oblúk D2 viesť dovnútra. R0 zakresliť len ako samostatnú textovú referenciu, kým jeho XY a prevod na FFL nie sú uzavreté. Nepoužiť dva záhradné modelové stupne ako existujúci uličný vstup.

Overenie tejto správy: priame načítanie aktuálnych `CODED_OPENINGS`, `HOUSE`, `SITE_SURFACES`, osí a transformácie cez Vite SSR; skutočný generátor dverí v Babylon NullEngine s kontrolou priebehu otvorenia a kľučiek; kontrola výškovej triangulácie z vrcholov; aritmetika návrhového vzorca. Bola vytvorená iba táto správa, bez zásahu do modelu, exportéra alebo pôvodného pôdorysu.
