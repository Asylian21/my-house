# Dokumentácia aktuálneho 3D domu

`/koncept-2d?variant=c` je interaktívna dokumentácia aktuálneho modelu. Pôvodný nastaviteľný koncept C zostáva na `/koncept-2d?variant=c&mode=study`; ostatné varianty a historické verzie sa nemenia.

## Zdroj rozmerov

`npm run docs:generate` spúšťa skutočné modelovacie funkcie interiéru, obvodového plášťa, výplní a terasového nábytku v Babylon NullEngine. Auto je v zaparkovanej polohe. Tri doplnkové kusy sedenia sa čítajú priamo z aktuálneho `dom-terrace.glb`. Zdrojový model sa nemení. Generátor sa automaticky spúšťa aj pred `npm run dev` a `npm run build`.

Výsledný `lib/plan-geometry.generated.json` obsahuje fyzické komponenty s transformovanými súradnicami. Hodnoty sa uchovávajú na 0,01 mm, UI ich zaokrúhľuje na 1 mm. Pôdorys používa konvexné priemety jednotlivých dielov: vnútorné dutiny ani výrobný profil nemožno odvodzovať z obalového rozmeru. Výška dielu a jeho horná hrana od podlahy sú rozdielne veličiny. Návrhové rozmery rámov, skríň a liniek pochádzajú z aktívnych dát `twin-interior.ts` a sú označené oddelene od rozsahu celej zostavy.

Dokumentácia pokrýva prízemie, stavebné otvory, obvodové steny a sedenie na terasách. Strešný plášť, parcela, vegetácia, bazén a podzemné siete nie sú obsahom pôdorysu prízemia. Neviditeľné navigačné a kolízne pomôcky sa neexportujú.

## Ovládanie a výstupy

- Ťahanie posúva plátno; koliesko alebo gesto dvoma prstami približuje okolo zvoleného bodu.
- Výber miestnosti ju priblíži. Hľadanie podporuje názvy bez diakritiky aj čísla miestností.
- Kliknutie na prvok otvorí rozmery; zoznam dielov sprístupňuje aj prekryté a veľmi malé súčasti.
- V = výber, H = posun, M = dvojbodové meranie, +/− = zoom, 0 = celý dom, šípky = posun, Escape = zrušenie.
- Manuál má prehľad domu, listy miestností, terasové vybavenie a voliteľnú prílohu všetkých dielov. Tlač používa vlastné statické pohľady nezávislé od aktuálneho zoomu.
- SVG je vektorový pôdorys, CSV je úplný súpis rozmerov a výškového osadenia komponentov.

## Overenie

`tests/plan-documentation.test.ts` porovnáva uložený export s čerstvým výpočtom celého pokrytého modelu. Kontroluje jedinečnosť a úplnosť dielov, súlad stien a dverí, samostatné kusy nábytku, mierku, súradnicový systém a vyhľadávanie. Kontroly stránok sú v `tests/rendered-html.test.mjs`. Celý projekt overuje `npm test`.

## Revízia okien a technickej miestnosti · 7. 9. 2026

Aktívny variant C má tri okná dievčenskej izby: 1 000 × 1 250 mm nad posteľou, pevné 1 600 × 1 950 mm pri hre a 1 050 × 1 600 mm pri stole. Všetky majú nadpražie 2 500 mm. Plocha otvorov je 6,05 m²; nejde o výpočet denného osvetlenia.

Technológia nadväzuje na dohodu zo 16.–17. 2. 2026: DEFRO Firewood Duo Plus 19 kW, násypka 180 kg a DBO-S 1 000 l. Zdrojové odkazy a samostatné označenie overených rozmerov výrobku sú v `lib/technical-design.ts` a v manuáli. Samotné teleso kotla má 538 × 656 mm; celkový katalógový obal zostavy 1 238 × 1 298 × 1 391 mm. Nádrž má Ø1 106 × 1 913 mm s izoláciou, Ø897 mm bez izolácie. Odvodený štvorcový pôdorys násypky a navrhnuté presahy hrdiel nie sú vydávané za samostatne okótované výrobné rozmery.

WC získalo ďalších 370 mm oproti predošlej publikácii: má 1 899 × 1 800 mm medzi priečkami (3,4182 m²; predtým 2,7522 m²). Celkový posun od pôvodného variantu je 600 mm. Misa je na novej osi miestnosti a umývadlo sa presunulo s priečkou. Technická má 8,669177 m² podlahového modelu namiesto 9,335177 m². Plochy sú z obrysov podláh; obklady zmenšujú skutočne voľný priestor. Kúpeľňový návrat ustúpil o 300 mm, práčka a sušička zostávajú 600 × 600 mm. Kuchyňa a vnútorné vstupy zostávajú na mieste.

Zostava kotla je vystredená medzi hotovými bočnými obkladmi: na oboch stranách má 504,5 mm, vzadu 500 mm. Od čela telesa zostáva 2 000 mm obslužný pás. Hrdlá aj teplomer nádrže sú natočené o 30° ku kuchynskému vstupu; hrdlá sú napojené na skutočný kruhový plášť. Regál pri nádrži nahradila plytká skriňa 720 × 261 × 1 750 mm hneď napravo od kuchynských dverí. Tri samostatné police nesú zvislo uložené vrecia peliet, pravý stĺpec je pre nástenný tyčový vysávač. Posuvné roletové čelo udržiava priechod voľný. Nad skriňou je hydraulická rezerva 720 × 261 × 650 mm vo výške 1 850–2 500 mm.

`tests/technical-design.test.ts` overuje 181 polôh oboch transportných krídel, presun nádrže Ø1 106 × 1 913 mm zvislo na 100 mm podvozku, skutočné sanitárne obálky, neprekrývanie podláh a spojitý priechod Ø580 mm ku skrini, nádrži, kotlu aj násypke. Zahŕňa hotové obklady, skutočné otočené obrysy hrdiel a podstavce. Kontroluje tiež symetriu kotla, uloženie vriec na policiach a kolízie obsahu s korpusom. Rozmery konkrétnych prípojok, balení peliet a držiaka vysávača treba potvrdiť pred realizáciou.

Manuál v technickej miestnosti rozlišuje fyzické prvky, obslužné plochy a trasu transportu. Rezerva pre tri modelové 15 kg vrecia a vysávač nemá schválené požiarne oddelenie. Presné osadenie DEFROmat, expanzia, rozvody, vetranie, komín, požiarne riešenie, statika prekladov a denné osvetlenie zostávajú na profesijné dopracovanie. Geometrická kontrola modelu nie je montážne ani realizačné schválenie.
