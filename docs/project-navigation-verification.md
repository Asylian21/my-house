# Hlavný návrh C/B/B a navigácia projektu

Lokálne overenie 13. 9. 2026. Referencia používateľa: `/koncept-2d?variant=c&heating=b&living=b`.

## Platné pravidlo po následnom spresnení používateľa

**Hlavné cesty sú pevne C/B/B; ostatné varianty aj ich prepínače sú dostupné cez archív.** Záväzný opis je v [active-design.md](active-design.md). Staršie záznamy nižšie o prepínaní A/B na hlavných stránkach opisujú pôvodný stav pred týmto spresnením a nie sú návodom na ďalší vývoj.

Pri poslednej úprave navigácie z 13. 9. 2026 boli oddelené `/archiv/podorys` a `/archiv/3d`. Archívny manuál používa `/archiv/podorys` s `view=manual`. Hlavná navigácia vracia C/B/B; vnútorné odkazy archívnej zostavy zachovávajú jej voľby. Staré alebo neplatné variantové parametre hlavných vstupov presmerujú na C/B/B so zachovaním pohľadu na parcelu či manuál.

Overenie tejto úpravy: produkčné zostavenie, cielený ESLint, `git diff --check` a 3/3 testy `twin-design-preview` prešli. Renderované HTML: 19/20; všetky kontroly smerovania aj hashové kontroly v1/v2 prešli, zostal starší nesúlad očakávanej plochy 6,19 m². Desktop a mobil 390 × 844: hlavný návrh bez prepínačov, archív C/A/B → manuál → 3D a návrat na C/B/B overené skutočnými kliknutiami. Mobilné odkazy archívu sú v jednom menu, aby sa neorezával manuál. Podrobnosti a log sú v `output/qa/main-design-c-b-b/`. Toto je záznam lokálneho overenia; bez commitu, pushu a publikovania.

## Výsledok

- Rozhodnutie C/B/B je zapísané v AGENTS.md, docs/active-design.md, spoločnom ACTIVE_DESIGN a používateľom vyžiadanej pamäťovej poznámke.
- `/` prehľad, `/docs` dokumentácia, `/docs/manual` manuál a tlač, `/docs/model` technické podklady v modeli, `/3d` prehliadka, `/podorys` interiérový plán a parcela, `/archiv` história.
- Hlavné vstupy používajú C/B/B. Explicitné A/B voľby sa po následnom spresnení prenášajú už iba medzi archívnym pôdorysom, archívnym manuálom a archívnym 3D. Pôvodné hlavné adresy otvárajú C/B/B.
- Snímky v1/v2 zostali nezmenené, čo potvrdzujú existujúce hashové testy. Zachované sú aj pôvodné štúdie a pôvodný vstup do modelu na `/archiv/model`.

## Parcela

Použitý celý katastrálny polygón parcely 6012/26 zo SITE_BOUNDARY so spoločnou transformáciou S-JTSK do lokálnych mm. Zahrnutá je ľavá hranica aj zaoblený uličný roh.

Pri prvom overení (pred následnou korekciou stavebníka) boli kolmé odstupy: ulica 3 000 mm, pravá/východná 3 077,913 mm, zadná/záhrada 2 052,911 mm, ľavá/západná 6 556,879 mm. Tieto hodnoty sú zachovaným záznamom pôvodného osadenia.

### Následná korekcia pravého odstupu, 13. 9. 2026

Stavebník požiadal pravý odstup presne 3 m. Aktívny model má teraz **uličný aj pravý kolmý odstup 3 000 mm**. Celý dom je oproti pôvodnému rámcu C3 posunutý o 77,913405454 mm doprava, bez zmeny rozmerov alebo dispozície. Výsledné zaokrúhlené odstupy: záhrada 2,056 m, západ 6,635 m.

`twin-house-placement.ts` počíta posun podľa šikmej východnej hrany. `twin-active-site.ts` zachováva národný katastrálny polygón a prevádza pozemok, cestu a hraničné prvky do rámca presunutého domu. Spoločný rámec používajú 2D aj Babylon. Plot si zachováva 100 mm odsadenie, bočný prístup sa prispôsobí hranici a čelné napojenia domu sa zachovajú. Export uvádza nový národný počiatok aj pôvodný katastrálny datum. Revízia je požiadavkou stavebníka, nie geodetickým zameraním stavby.

Cielená geometrická sada po korekcii: 52/52 testov. Produkčný build, 3 cielené kontroly renderovaného HTML (navigácia/osadenie, C/B/B v 3D a hash archívu v2), ESLint a `git diff --check` prešli. Globálny TypeScript naďalej obsahuje historické chyby mimo tejto korekcie; nové moduly osadenia vo výstupe nemajú chybu.

Prehliadač po obnove dev servera: pôdorys C/B/B na 1440 × 1000 aj 390 × 844 zobrazuje dve kóty 3,000 m, bez vodorovného pretekania. `/3d?variant=c&heating=b&living=b` načítal WebGL scénu, prepnutie na Dom a záhrada funguje, konzola nemá chyby ani varovania. Podklady: `setback-3m-desktop.png`, `setback-3m-mobile.png`, `setback-3m-babylon.png` v `output/playwright/project-navigation-2026-09-13/`. Ide o lokálnu úpravu, bez commitu alebo nasadenia.

## Kontroly pôvodnej úpravy navigácie

Nasleduje zachovaný historický záznam pred presunutím všetkých alternatív pod archív. Najmä vtedajšie prepínanie A/B na hlavných stránkach bolo nahradené platným pravidlom vyššie.

- Produkčný build prešiel.
- Cielený ESLint upravených komponentov, navigácie, novej geometrie a testov prešiel. `git diff --check` prešiel.
- Nová geometria a zachovanie návrhu: 6/6 cielených testov v plan-site a twin-design-preview, vrátane porovnania B/B s reálnou Babylon geometriou.
- Celá pôvodná unit sada: 402/403. Zostáva nesúvisiace zlyhanie testu závesu DOOR-102-109 v rozpracovanej úprave dverí (očakáva hinge -1, model má +1).
- Renderované HTML: 18/19. Nové sekcie, C/B/B, archivácia, parcela a pôvodné uložené verzie prešli. Existujúci test historických rozmerov C očakáva 6,19/12,34 m², aktuálna rozpracovaná geometria má iné hodnoty. Túto geometriu táto úloha nemenila.
- Globálny TypeScript má existujúce chyby Babylon/Cloudflare/historických súborov. Nové súbory a upravené vstupy tejto úlohy nemajú v jeho výstupe chybu.
- Desktop 1440 × 1000/1050 a mobil 390 × 844: vizuálna kontrola, bez vodorovného pretekania.
- Skutočné kliknutia: prehľad → dokumentácia → manuál → pôdorys; oba rozmery zostavy sa zachovajú. Zmena technickej miestnosti zachová priblíženie na miestnosť. Voľba obývačky A zostane A aj po obnovení. Prepnutie parcely mení URL; globálny odkaz Pôdorys parcelu odstráni a upraví rozsah.
- Dom na parcele: celý polygón je viditeľný na mobile a desktope. Stiahnutý SVG je validné XML, má celý rozsah `-2746 -26297 35733 28297` a obsahuje západný aj oblý roh.
- `/3d` načítal skutočnú WebGL scénu C/B/B. `/docs/model` ostáva v technickom režime, zachováva prieskumník a zdroje; po načítaní bez chýb konzoly.
- Po zostavení obnovený dev server na http://localhost:5173/; odklikané prechody fungujú aj bez úplného obnovenia stránky.

Vizuálne podklady sú lokálne v `output/playwright/project-navigation-2026-09-13/`. Overenie je lokálne; bez commitu, pushu a verejného nasadenia.
