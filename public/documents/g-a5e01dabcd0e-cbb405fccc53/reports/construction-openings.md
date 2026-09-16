# HS portál GARDEN-02 / D5 — revízia 15. 9. 2026

Hlavný návrh **C/B/B**. Stavebník označil v pôdoryse prvok „Terasové presklenie 2500“ a požiadal zúženie z 250 na 220 cm. Obrázok identifikuje **GARDEN-02 / D5 pri spálni 1.10**, hoci v prvom slovnom zadaní bola uvedená obývačka.

| Veličina | Aktuálna hodnota |
| --- | --- |
| Stavebný otvor — šírka × výška | **2 200 × 2 400 mm** |
| Parapet od podlahy | **0 mm** |
| Os otvoru | **X 13 090 mm**, zachovaná |
| Ostenia | **X 11 990–14 190 mm** |
| Vonkajšie líce fasády | **Y 11 200 mm** |
| Zúženie | **150 mm z každej strany** |
| Otváranie | Zdvižno-posuvné, zachované |
| Názov v interaktívnom pôdoryse | **Terasové presklenie 2200** |

Jednotný zdroj je `ACTIVE_GARDEN_PORTAL` v [aktívnom dome](../lib/twin-active-house.ts). Rozmery preberá Babylon pre otvor v murive a izolácii, rám, sklá, posuv a kolízie. Priľahlé smrekovcové polia sa odvodzujú od nových ostení. Z namodelovaných dielov sa obnovuje pôdorysná geometria, detail prvku, kóty, súpis komponentov, SVG/CSV/PNG a tlačený manuál.

Výkresová sada preberá rovnaký otvor **D5** do pôdorysu, severného pohľadu, výpisu otvorov a príslušných rezov. Knižnica `/docs` obsahuje obnovené farebné aj čiernobiele PDF, náhľady a modelový JSON. [Statický podklad K-02](construction-structural-basis.md) uvádza nové ostenia.

Samostatný posuvný portál obývačky **WING-WEST-01** má naďalej 2 250 × 2 400 mm. Historické podklady a snímky `versions/v1`, `versions/v2` uchovávajú pôvodný stav.
