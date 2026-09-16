# Pracovňa C/B/B · AlzaErgo Table ET1 NewGen

Používateľ 13. 9. 2026 vybral [čierny stôl ET1 NewGen s čiernou laminovanou doskou 140 × 80 cm](https://www.alza.cz/alzaergo-table-et1-newgen-cerny-deska-14080-cm-lamino-cerna-d13366453.htm), kód BUNAEY0806dq.

- Doska má **1 400 × 800 × 18 mm**. Hrúbku 18 mm uvádza [katalóg Alza pri tomto konkrétnom čiernom balíku](https://www.alza.cz/polohovaci-stoly-a-stanice/praha-7-holesovice/18868000-b0.htm).
- Čierna oceľová podnož má dva motory a dva trojsegmentové zdvíhacie stĺpy. Produkt uvádza rozsah nastavenia 620–1 280 mm. Horná plocha je v modeli vo výške 750 mm; model je zobrazený v tejto pevnej polohe.
- Pôdorys dosky: X **23 542–24 342 mm**, Y **3 704–5 104 mm**. Stôl je otočený na západ: šírka 1 400 mm prebieha v osi Y a hĺbka 800 mm v osi X.
- Zachovaná je os monitora a stoličky Y 4 404 mm, poloha pri západnej stene a výška monitora. Oproti pôvodnej šírke 1 800 mm ustúpili oba konce dosky o 200 mm. Od severného konca po začiatok vyhradeného vstupného pásu ostáva 296 mm; nejde o šírku priechodu miestnosťou.
- Rozmery dosky sú presné podľa katalógu. Rozstup a prierezy podnože, motory, pätky a ovládač sú vizuálne odvodené z fotografie; nejde o výrobný model ani vŕtaciu šablónu.

Rozmery výrobku sú v `lib/twin-office-desk.ts`; osadenie v `OFFICE_FITOUT` v `lib/twin-interior.ts`. Babylon, kolízny obrys, generovaný 2D plán a detail produktu používajú tieto údaje. Historické snímky a základný historický stôl 1 800 × 800 mm zostávajú zachované.

## Lokálne overenie 13. 9. 2026

- 18/18 testov pre stôl, aktuálnu pracovňu a aktívny interiér prešlo (`office-desk`, `office-acoustic-geometry`, `twin-interior-c`). Kontrolujú aj obrys, otváranie dverí, priechod a zhodu generovanej 2D dosky s Babylon geometriou.
- Cielený ESLint, `git diff --check` a produkčné zostavenie prešli. Širší existujúci `babylon-interior.test.ts` naďalej padá na očakávaní pántu `DOOR-102-109` (`-1` oproti aktuálnemu `1`); nejde o zmenu stola.
- V živom WebGL2 náhľade C/B/B má nová doska šírku 1 400 mm, hĺbku 800 mm, hrúbku 18 mm a hornú plochu 750 mm nad podlahou (odchýlka plávajúcej čiarky menšia než 0,00001 mm). Starý importovaný kancelársky stôl sa nevykresľuje.
- [Pôdorys s kótami](../output/playwright/office-desk-2d-top.png), [detail v 3D](../output/playwright/office-desk-3d-detail.png), [produktová referencia](../output/playwright/office-desk-product-reference.png).
- Overené lokálne; bez commitu a publikovania. Čistý náhľad používa port 5173 a samostatnú cache; existujúci server na porte 3000 mal pri 3D zastarané závislosti. Konzola nového náhľadu obsahuje iba existujúce 404 pre `favicon.ico`.
