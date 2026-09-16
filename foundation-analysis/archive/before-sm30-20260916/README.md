# Základy a doska C16/20 - C/B/B

**Stav: podmienená výpočtová štúdia na nezávislé odborné preverenie. Žiadny variant nie je pripravený na realizáciu.**

## Najnovšia požiadavka: 100 mm doska + štyri rebrá 400 mm

**Aktuálny výpočet so súvislou podporou zhutneným zásypom:** [report-100mm.pdf](report-100mm.pdf), 5 strán A4, a [report-100mm.md](report-100mm.md). Hlavný model ponecháva zeminu pod doskou aj spodkom rebier. Voľné polia nie sú jeho návrhovým stavom. Stena mimo rebra môže prenášať zaťaženie cez dosku do zeminy; samotný pôdorysný prienik preto nerozhoduje o potrebe nového rebra.

Prepočítaných je 48 lokálnych stenových a 48 rebrových prípadov pri predpokladaných ks = 5 / 10 / 20 / 50 MN/m³ a rôznych tuhostiach betónu. Najvyššie miestne MEd doskového pásu sú +4,515 / -1,064 kNm/m oproti skúšobným odolnostiam +6,551 / -4,512 kNm/m pri Ø8/150. Hodnoty ks ani výstuž nie sú potvrdené na stavbe. Znížené EI sú citlivosti, nie vyriešená história trhlín. R1/R7 vyžadujú kontrolu horného ťahu. Celý spojený dom, všetky reakcie, skutočné podložie, sadanie, kotvenie a konečná výstuž ešte nie sú uzavreté.

Používateľ potvrdil spoločnú betonáž 100 mm dosky a rebier vysokých 400 mm celkom. Zásyp je miestna hlina/piesok, zhutnené. Výstuž nie je určená; údaje 300/150 mm pri obvode ešte neurčujú celý detail. Zdroj: [user-100mm-clarification.md](inputs/user-100mm-clarification.md).

Samostatná reprodukcia aktuálnej kontroly (Python, rovnaké závislosti ako nižšie):

```bash
python3 foundation-analysis/calculations/slab_100_four_ribs.py
python3 foundation-analysis/calculations/four_rib_load_path_audit.py
python3 foundation-analysis/calculations/four_rib_free_beam_screen.py
python3 foundation-analysis/calculations/check_100mm_independent.py
python3 foundation-analysis/calculations/ground_support_independent.py
python3 foundation-analysis/calculations/slab_100_ground_support.py
python3 foundation-analysis/calculations/four_rib_ground_support.py
python3 foundation-analysis/calculations/report_100mm.py
```

Hlavné nové výsledky: `results/slab-100-ground-support.json/.md`, `four-rib-ground-support.json/.md`, `four-rib-ground-support-summary.csv`, `four-rib-ground-support-traces.csv`, `ground-support-independent.json` a `ground-support-cross-check.json`. Generátor aktuálneho reportu: `calculations/report_ground_support.py`, stabilný vstup `report_100mm.py`.

Staršie doplnkové kontroly: `results/slab-100-four-ribs.json/.md`, `four-rib-load-path-audit.json/.md`, `four-rib-wall-coverage.csv`, `four-rib-free-beam-screen.json/.md`, `check-100mm-independent.json`. Predchádzajúci report a generátor sú zachované v `archive/before-ground-support-20260916/`. Nevyhovujúce voľné polia sa nepoužívajú ako dôkaz nevyhovenia dosky na súvislom zásype. Primárne zdroje: [ground-support-sources.md](inputs/ground-support-sources.md) a [check-100mm-sources.md](inputs/check-100mm-sources.md). QA: `results/report-100mm-qa.json`.

Pôvodný porovnávací výstup: [report.pdf](report.pdf), **10 strán A4**, a [report.md](report.md). Týka sa starej podmienenej štúdie 17 trás; nie je výpočtom aktuálnej 100 mm dosky so štyrmi rebrami.

## Aktuálna revízia 16. 9. 2026 - obvodové čiary ako približné osi betónu

Investor novým obrázkom8:56 a následnou odpoveďou potvrdil:

- vyliaty spodný betón je približne vystredený po čiarach obvodu;
- garážový koniec bol oproti situácii20,80m predĺžený o800mm; koordinačná šírka je teda21,60m;
- horná časť a doska ešte nie sú vyliate; dohodnuté zostávajú štyri rebrá R7,R1,R2,R4.

**Aktuálny technický výkres:** [ZK-01/ZK-02/ZK-03 - revízia OSI](drawings/technical/agreed-ribs-technical.pdf), tri listy A3, pôdorys1:100 pri tlači100%. Modré čiary A-D sú nové približné osi spodného betónu v rámci modelu, nie betónové hrany. Kóty do osí rebier sú R7odľavej8 653mm, R1odpravej7 348,5mm, R2oduličnej7 862mm, R4odzadu2 850mm. Presné hrany a súososť vyliateho betónu zostávajú nezamerané. Pracovná šírka350mm nie je staticky potvrdená pre štyri rebrá.

**Predchádzajúce kóty od líc horného350mmobvodu a tabuľka od spodného380/400mm pásu sú prekonané.** Pôvodná os horného obvodu leží približne349-354mm dovnútra od novej interpretácie obvodových čiar. Červené osi a konce rebier sa potichu nemenili; ich napojenia treba zosúladiť. R2 leží338mm pred zalomenímL a nemá týmto vyriešenú ľavú podporu. Staré dĺžky7495/6298mm už nepredstavujú dĺžky medzi novými modrými osami. Prekonaná revízia je v `archive/before-centerline-clarification-20260916/`.

**List ZK-03 - priame kóty k hranám rebier, oprava podľa obrázka 9:41:18:** používateľ požaduje kóty od modrého obvodu po červené rebrá a medzi nimi priamo v pôdoryse. Červené kóty teraz vedú po líca: ľavý obvod → R7 **8 478 mm**, svetlá medzera R7–R1 **5 248,5 mm**, ľavé líce R7 → L-bok **6 122 mm**, pravé líce R1 → premietnutý L-bok **173,5 mm**, pravé líce R1 → pravý obvod **7 173,5 mm**. Vo zvislom smere: spodný obvod → dolné líce R2 **7 687 mm**, svetlá medzera R2–R4 **7 973 mm**, horné líce R4 → zadný obvod **2 675 mm**. Pracovné šírky 350 mm sú zobrazené osobitne; spodný tmavý reťazec zostáva po osiach.

Tieto kóty sú modelové; napojenia ani geodetická poloha nie sú novým zakreslením potvrdené. Predošlý ZK-03 s odstupmi modrá–sivá riešil nesprávne pochopenú požiadavku a je zachovaný v `archive/before-direct-rib-dimensions-20260916/`. Jeho číselné rozdiely zostávajú pomocnými údajmi v JSON/CSV. Zdroj aktuálneho spresnenia: `inputs/client-direct-rib-dimensions-20260916.json`; nové kóty: `drawings/technical/direct-rib-face-dimensions.csv`.

Na druhom liste sú osobitne zdrojové a modelové rozmery: zdrojové19 050/10 840/14 550mm po predĺžení oproti modelovým19 035/10 835/14 600mm. Kótový uzáver pôvodného obrázka má rozdiel50mm vX a10mm vY; hodnoty sa nenormalizujú bez podkladu.

[Prehľadová schéma](drawings/agreed-ribs.svg) je na strane2 [reportu](report.pdf). Nový zdroj je `inputs/client-perimeter-centerlines-20260916.png`; pôvodné označenie4rebier zostáva v `inputs/client-foundation-markup-20260916.png`. Výklad, zdrojové odtlačky a potvrdenie predĺženia sú v `inputs/client-agreed-layout.json`.

Strojové kóty: `results/agreed-ribs-dimensions.json`, `drawings/technical/dimensions.csv`. `drawings/agreed-ribs.csv` uchováva pôvodné modelové osi a konce, nie hotové realizačné dĺžky.

**Výpočty a množstvá MIN/MEDIUM/MAX zostávajú výsledkami pôvodnej štúdie17trás. Neposudzujú štyri rebrá ani novú interpretáciu polohy spodného betónu.** `inputs/geometry.json`, `model-snapshot.json` a pôvodné výpočtové výsledky zostávajú zmrazené pre reprodukciu. Nový stav je zaznamenaný osobitne, aby sa neopravovala geometria bez nového výpočtu a zamerania.

## Čo štúdia preukazuje a čo nie

- MIN: doska 150 mm v obytných častiach, 180 mm v garáži.
- MEDIUM: 180 mm; garáž má hustejšiu sieť Ø10/100.
- MAX: 200 mm; väčšia rezerva pri definovanej lokálnej strate podpory.
- Všetky výpočty používajú C16/20. Ostatné materiálové a súčiniteľové predpoklady sú uvedené v skriptoch, reporte a poznámkach.
- Vytvorená je geometricky súvislá kandidátna sieť 17 nových podporných trás; 37 modelových úsekov muriva je pokrytých bez geometrickej tolerancie. Geometrické prepojenie nie je dôkaz kotvenia alebo nosníkového pôsobenia.
- Existujúce pásy 380-400 mm nemožno pri chýbajúcom zameraní/geotechnike a skutočných reakciách potvrdiť. Samotné zosilnenie dosky tento problém nevyrieši.
- Úplný model skutočnej strechy, stabilita, okraje a škáry dosky, starý/nový betón, zosilnenie obvodu a 100-ročná trvanlivosť nie sú uzavreté. V reporte sú presne oddelené podmienené lokálne výsledky a nepreukázané časti.
- Označenie MIN znamená najnižšiu spotrebu v skúmanej rodine, nie dokázané globálne ekonomické optimum. Celková cena realizovateľného založenia ešte nie je známa.

## Vstupy a stav stavby

`inputs/user-brief.md` je zadanie. Investor v následnej odpovedi potvrdil, že **vyliate sú iba spodné pásy, horné debnenie a doska ešte nie**. Staršie opačné tvrdenie v projektovej dokumentácii je v tejto štúdii výslovne nahradené. Pôvodné dokumenty sa nemenili.

- [source-register.md](inputs/source-register.md): register projektovaných, deklarovaných, predpokladaných a chýbajúcich údajov, súbory a strany.
- [norms-and-ground.md](inputs/norms-and-ground.md): primárne normové zdroje, vydania a obmedzenia prístupu.
- `geometry.json`: modelová geometria; **nie geodetické zameranie**.
- `model-snapshot.json`: zmrazená kópia podkladu pre reprodukciu; staršie údaje o vyliatí a povrchoch v nej neprevažujú nad aktuálnym registrom.
- `supplementary-routes.json`: spojitá kandidátna sieť R8-R17, pokrytie stien, uzly a podmienky výstuže.
- `photos/*.jpg`: prevod troch používateľových HEIC do JPEG pre čítanie; originály v Downloads zostali nezmenené. Fotografie nie sú meradlom.
- `extracted/`: extrahovaný text a kontrolné náhľady pôvodných PDF; obrázky/rozmery boli overované aj vizuálne, OCR môže byť neúplné.

## Reprodukcia zo zmrazených vstupov

Python 3.11+; na PDF sa použije font DejaVu Sans. Generátor hľadá font v lokálnom Codex runtime, inak v `/usr/share/fonts/truetype/dejavu/`.

```bash
cd /Users/davidzita/www/dom
python3 -m venv foundation-analysis/.venv
foundation-analysis/.venv/bin/python -m pip install -r foundation-analysis/requirements.txt
foundation-analysis/.venv/bin/python foundation-analysis/calculations/route_network.py
foundation-analysis/.venv/bin/python foundation-analysis/calculations/slab.py
foundation-analysis/.venv/bin/python foundation-analysis/calculations/foundation.py
foundation-analysis/.venv/bin/python foundation-analysis/calculations/technical_layout.py
foundation-analysis/.venv/bin/python foundation-analysis/calculations/report.py
foundation-analysis/.venv/bin/python foundation-analysis/calculations/verify.py
```

V tomto prostredí bolo použité:

```text
/Users/davidzita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3
```

Chýbajúce `shapely` je lokálne v ignorovanom `.deps/`; skripty ho vedia načítať. Žiadny výpočet nepotrebuje server aplikácie, internet, platené API ani zmenu modelu domu. PDF výstupy v `drawings/` sú samostatné technické obrázky, nie ďalšie strany hlavného reportu.

## Obnova geometrie z novšej dokumentácie

`calculations/extract_geometry.py` znovu načíta `output/pdf/construction-cbb/model-snapshot.json` a uloží aktuálne `inputs/geometry.json`. Toto **mení vstupy štúdie**; na obyčajné zopakovanie výpočtu ho nespúšťať. Po úmyselnej aktualizácii treba skontrolovať register, dispozíciu, zdrojové odtlačky, fotografie a všetky predpoklady, potom obnoviť `model-snapshot.json`, sieť a výpočty. Nové meranie základov nemožno nahradiť exportom architektonického modelu.

## Výstupy a jednotky

- `results/foundation-results.json`: geometria, množstvá, obvodový reakčný obal, sadanie, sokel, vnútorné pásy a bloky. Geometria m; sily kN; RC napätia MPa; doskové momenty kNm/m.
- `results/slab-results.json` a [slab-notes.md](results/slab-notes.md): lokálne medzné stavy, šmyk pohybujúceho sa kolesa, trhliny, priehyb, Navierova kontrola a citlivosť.
- `results/load-envelope.json`: dodatočné veterné, snehové, bodové, PV, vodné a zásypové citlivosti. Nie je to potvrdené zaťaženie pozemku.
- [calculation-method.md](calculations/calculation-method.md): modely, rozsah výsledkov, pracovné škáry a množstvá.
- `drawings/routes.csv`: presné osi a šírky R1-R17, mapované na steny; PDF/SVG majú rovnaký zdroj.
- `results/wall-loads.csv`: vlastné hmotnosti všetkých 37 úsekov, nie plošný priemer priečok.
- `results/cost-model.csv`: množstvá a prázdne sadzby; neobsahuje vymyslenú cenovú ponuku.
- `results/verification.json`: automatické kontroly, nie autorizácia návrhu.

## Kontrola PDF

```bash
mkdir -p foundation-analysis/results/rendered
pdftoppm -scale-to 1400 -png foundation-analysis/report.pdf foundation-analysis/results/rendered/page
```

Po každej obsahovej zmene prezrieť všetkých 10 strán, najmä kóty, popisy trás, rezy, poznámky o nevyhovujúcich stavoch a súlad výstuží. Automatické overenie počíta strany A4, kontroluje súčty, vybrané rovnováhy, geometrické pokrytie a zhodu množstiev. Nenahrádza posúdenie konkrétnou autorizovanou osobou pred stavbou.
