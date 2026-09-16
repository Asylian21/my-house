# Rebrá 350 × 400 mm — samostatný scenár voľného nosníka

**Revízia AK-01/AK-02, 16. 9. 2026:** aktuálne je SM30, jedna 300 mm obvodová tehla so zachovaným účelom odhlučnenia. Táto štúdia používa zmrazené pôvodné zaťaženia SA30; výsledky pre stenové zaťaženia a R7 sa nepovažujú za prepočet SM30. Konkrétny výrobok a nový prepočet zostávajú otvorené. Samostatné geometrické kóty a výpočty bez stenového zaťaženia týmto nie sú prerátané. Pozri [záznam revízie](/Users/davidzita/www/dom/foundation-analysis/inputs/wall-revision-sm30-20260916.md).

**Podmienený kontrolný scenár, nie návrh na realizáciu.** Výška 400 mm zahŕňa 100 mm dosku. Šírka 350 mm ostáva pracovným vstupom. Posudzuje sa iba vlastná tiaž a priamo súosé modelové steny.

## Statický model a vstupy

- Prostý nosník bez priebežného podopretia zeminou; obidva konce sú idealizované kĺby. Skutočné uloženie na dnešnom obvode nie je preukázané.
- Rozpätia 7,495 a 6,298 m sú pôvodné modelové dĺžky, optimistické pracovné náhrady za zatiaľ neznáme účinné rozpätia.
- C16/20; B500; αcc = 0,85; γc = 1,50; γs = 1,15; stála tiaž γG = 1,35. Hodnoty sú prevzaté pracovné predpoklady, nie overenie aktuálnej českej národnej prílohy.
- Krytie 35 mm k vonkajšiemu lícu strmeňa Ø8, spodné prúty Ø16 v jednej vrstve: d = 400 − 35 − 8 − 8 = 349 mm. Krytie/expozícia/detaily nie sú týmto schválené.
- Vlastná tiaž celého prierezu = 0,350 × 0,400 × 25 = **3,500 kN/m**. Obsahuje 300 mm spodnú časť 2,625 kN/m aj pruh 100 mm dosky 0,875 kN/m. Táto časť dosky sa druhýkrát nepripočítava; širšia zaťažovacia plocha dosky sa bez podkladov nepriraďuje.
- Do zaťaženia nevstupuje strecha, strop/povala, sneh, vietor, úžitkové zaťaženie, auto, zariadenia ani nepreukázaný prenos priečnych stien. R4 používa nominálne 300 mm murivo a 30 mm povrchov, vrátane pásu nad zasklením; hmotnosť nadpražia ani jeho reakcie nie sú známe.
- Nezapočítava sa T-prierez, votknutie, klenbové pôsobenie muriva, tlaková výstuž ani starý betón.

## Zaťaženie a ohyb

Intervalové stenové zaťaženia sa integrujú presne; pod dverami a v chodbách sa nevytvára plná stena. Polohy a tiaže každého úseku sú v JSON. Únosnosť obdĺžnika: x = As·fyd/(0,8·b·fcd), z = d − 0,4x, MRd = As·fyd·z. Oceľ v oboch scenároch dosahuje medzu klzu pri prijatom medznom pretvorení betónu.

| Spodná ťahová výstuž | As [mm²] | d [mm] | x/d | MRd [kNm] | VRd,c [kN] |
|---|---:|---:|---:|---:|---:|
| 3Ø16 | 603.19 | 349 | 0.296 | 80.69 | 51.30 |
| 4Ø16 | 804.25 | 349 | 0.395 | 102.77 | 56.46 |

| Rebro | Modelové L [m] | MEd [kNm] | Najväčšie VEd [kN] | MEd/MRd, 3Ø16 | MEd/MRd, 4Ø16 |
|---|---:|---:|---:|---:|---:|
| R7 | 7.495 | 76.26 | 43.44 | 94.5 % | 74.2 % |
| R1 | 7.495 | 114.88 | 68.64 | 142.4 % | 111.8 % |
| R2 | 6.298 | 94.70 | 53.85 | 117.4 % | 92.1 % |
| R4 | 6.298 | 85.97 | 59.20 | 106.5 % | 83.7 % |

**Interpretácia:** pomer nad 100 % nevyhovuje uvedenému obdĺžnikovému nosníkovému scenáru už pri samotnej vlastnej tiaži a zahrnutých stenách. Pomer pod 100 % nepreukazuje celkové vyhovenie — chýbajú ďalšie zaťaženia, podpery, kotvenie a medzné stavy používateľnosti.

## Šmyk — parametrické strmene, bez návrhu rozstupu

VRd,c používa CRd,c = 0,18/γc, k = min(2; 1 + √(200/d)), ρl = As/(b·d), dolnú hranicu vmin = 0,035·k^(3/2)·√fck. Pre zvislé dvojramenné strmene Ø8: VRd,s = Asw/s·z·fyd·cotθ; VRd,max = b·z·0,6(1−fck/250)·fcd/(cotθ + tanθ). Používa sa z ≤ min(0,9d; vypočítané z). Kapacity VRd,c a VRd,s sa nesčítavajú.

| Spodné prúty | Strmene — scenár | cotθ | min(VRd,s; VRd,max) [kN] |
|---|---|---:|---:|
| 3Ø16 | 2 ramená Ø8 / 100 mm | 1.0 | 134.48 |
| 3Ø16 | 2 ramená Ø8 / 100 mm | 2.5 | 189.08 |
| 3Ø16 | 2 ramená Ø8 / 150 mm | 1.0 | 89.66 |
| 3Ø16 | 2 ramená Ø8 / 150 mm | 2.5 | 189.08 |
| 3Ø16 | 2 ramená Ø8 / 200 mm | 1.0 | 67.24 |
| 3Ø16 | 2 ramená Ø8 / 200 mm | 2.5 | 168.10 |
| 4Ø16 | 2 ramená Ø8 / 100 mm | 1.0 | 128.46 |
| 4Ø16 | 2 ramená Ø8 / 100 mm | 2.5 | 180.61 |
| 4Ø16 | 2 ramená Ø8 / 150 mm | 1.0 | 85.64 |
| 4Ø16 | 2 ramená Ø8 / 150 mm | 2.5 | 180.61 |
| 4Ø16 | 2 ramená Ø8 / 200 mm | 1.0 | 64.23 |
| 4Ø16 | 2 ramená Ø8 / 200 mm | 2.5 | 160.58 |

VEd je reakcia pri idealizovanej podpere bez priaznivého zníženia pri priamom uložení. Rozstupy a cotθ sú výslovne scenáre. Neoverujú styk so starým betónom, zarážku, kotevnú dĺžku, torziu, uzly ani únosnosť podpery.

## Ohybový limit rovnomerného čiarového zaťaženia

`qEd,lim = 8·MRd/L²`. Celkové q zahŕňa vlastnú tiaž nosníka. Posledný stĺpec je iba matematický zvyšok pre rovnomerné stále zaťaženie pri γG = 1,35, po odpočítaní 3,5 kN/m vlastnej tiaže. Nie je to dovolené zaťaženie domu ani lokálnej steny.

| L [m] | Spodné prúty | Celkové qEd,lim [kN/m] | Rovnomerné ďalšie Gk nad tiaž nosníka [kN/m] |
|---|---|---:|---:|
| 7.495 | 3Ø16 | 11.49 | 5.01 |
| 7.495 | 4Ø16 | 14.64 | 7.34 |
| 6.298 | 3Ø16 | 16.27 | 8.56 |
| 6.298 | 4Ø16 | 20.73 | 11.85 |

## Čo tento scenár uzatvára

Je to samostatný audit možnosti nosníkového prenosu pri úplnej absencii priebežnej podpory. Nenahrádza model rebier a dosky na zhutnenom podloží. Pre ten treba poznať vlastnosti a sadanie podložia; miestna hlina/piesok a slovné „zhutnené“ neurčujú tuhosť podpory. Priehyb, dotvarovanie a trhliny sa tu neoverili. Výsledky nemožno označiť za schválenie 100 mm dosky alebo celého domu.

Metodický podklad: [JRC — Eurocode 2: Design of Concrete Buildings, Worked examples (2014)](https://eurocodes.jrc.ec.europa.eu/doc/1110_WS_EC2/report/1110_WS_EC2.pdf), kapitoly 3.2.1.2 a 3.2.1.4. Verejný metodický príklad nie je potvrdením dnešnej českej národnej prílohy. Konkrétne dosadené hodnoty a obmedzenia sú vyššie.

Reprodukcia: `python3 foundation-analysis/calculations/four_rib_free_beam_screen.py`. Skript overuje rovnováhu síl a momentov aj známy výsledok rovnomerne zaťaženého prostého nosníka. Použité vstupy s SHA-256 a všetky intervaly sú v `four-rib-free-beam-screen.json`.
