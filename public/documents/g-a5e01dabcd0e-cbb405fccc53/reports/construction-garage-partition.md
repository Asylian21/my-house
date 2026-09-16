# Garáž / spálňa a šatník: priečka 140 mm

Revízia hlavného návrhu C/B/B podľa červeného označenia stavebníka zo **16. 9. 2026**. Vnútorný úsek medzi garážou 1.12 a šatníkom 1.14 / spálňou 1.10 používa bežnú murovanú priečku **SP14, 140 mm**, rovnakú nominálnu hrúbku ako priečky izieb. Nahrádza tu pôvodných 301 mm modelového muriva, označovaného SP30.

| Údaj | Aktuálny model |
| --- | --- |
| Identifikátor vnútorného úseku | `C-GARAGE-PARTITION` |
| Materiálový kód a rola | SP14, murovaná nenosná priečka (`PARTITION`) |
| Hrúbka a dĺžka | 140 × 3 005 mm |
| Rozsah | X 11 003–11 143 mm; Y 5 744–8 749 mm |
| Zachované líce pri izbách | X 11 143 mm |
| Nové líce pri garáži | X 11 003 mm, posun 161 mm do pôvodnej steny |
| Prírastok podlahového modelu garáže | 161 × 3 005 mm za priečku + 161 × 140 mm za zarovnaný zub = 0,506345 m² |
| Garáž 1.12 | 25,151355 m², v pôdoryse 25,15 m² |
| Súčet podlahových obdĺžnikov domu | 180,378473 m² vrátane garáže |

Spálňa, šatník, ich nábytok aj dvere zostávajú na pôvodných súradniciach. Hlavná zostava nemá dvere medzi garážou a šatníkom. Voliteľný otvor v dispozičnej štúdii používa rovnaké nové líca 11 003–11 143 mm.

Za zadným vnútorným lícom garáže Y 8 749 mm pokračuje zachovaná stena pri **vonkajšej lodžii** `C-GARAGE-SPINE-N`: X 10 842–11 143 mm, Y 8 749–10 699 mm. Jej hrúbka 301 mm, rohové murivo a obvodové zateplenie zostávajú. Os B na X 10 993 mm aj koordinačná trasa základov R6 na X 10 993 mm sa naďalej odvodzujú od tohto vonkajšieho úseku, nie od novej tenšej vnútornej priečky. R6 nemení polohu ani význam.

Hrúbka 140 mm má rovnaký význam ako SP14 v ostatných izbách: nominálna modelová hrúbka priečky; dodatočné povrchové vrstvy sa touto revíziou nepredpisujú. Zmena geometrie neurčuje výrobok, požiarnu odolnosť ani nepriezvučnosť konkrétnej skladby. Nenahrádza existujúci otvorený návrh konštrukcií a oddelenia garáže v [statickom podklade](construction-structural-basis.md).

## Zarovnanie pri regáli a poloha kosačky

Nadväzujúce zadanie stavebníka zo 16. 9. 2026 odstránilo **161 mm zub** na ľavom konci priečneho návratu `C-GARAGE-BAY-RETURN`. Návrat začína na **X 11 003 mm**, presne na líci novej priečky, a zostáva v páse **Y 5 604–5 744 mm**. Uvoľnený pás podlahy garáže je tak súvislý od Y 5 604 po 8 749 mm. Oproti prvému zúženiu priečky pribudlo ďalších **0,022540 m²**.

Regál sa skracuje z **2 000 na 1 839 mm**: pôdorys **X 11 003–12 842 mm, Y 5 104–5 604 mm**, teda **1 839 × 500 mm**, výška 2 100 mm. Jeho ľavá hrana lícuje s priečkou aj návratom; pravá zostáva. Police, stojany, uložené veci a kolízny obal vychádzajú z upraveného rozmeru.

Kosačka je posunutá **o 161 mm doprava k stene**: pôdorys **X 10 503–10 983 mm, Y 6 660–7 360 mm**. Rozmer **480 × 700 mm**, orientácia a poloha pozdĺž steny zostávajú. Pri líci priečky X 11 003 mm zostáva **20 mm medzera**. Rovnakú polohu používa 2D priemet, 3D model aj navigačný obal.

## Zdroj a dokumentácia

Spoločný zdroj je `narrowGaragePartition()` a `GARAGE_PARTITION_MM` v `lib/floor-plan-concept.ts`. Aktívny interiér, Babylon steny a kolízie, podlahy a plochy preberajú rovnaké dáta. Pôdorys, manuál a export označujú vnútorný úsek SP14; vonkajší úsek pri lodžii zostáva SP30.

Obnova prebieha cez `npm run docs:drawings`: merané komponenty 3D, celá farebná a čiernobiela sada A1, rezy, skladby, výkazy, modelový snímok, náhľady a knižnica `/docs`. [Podklad strechy a kúrenia](construction-roof-heating-basis.md) obsahuje novú plochu garáže a súčet plôch. Rozsah podlahového kúrenia sa nemení, garáž z neho zostáva vylúčená. Historické snímky `versions/v1`, `versions/v2` a dispozície A/B/D sa neprepisujú.
