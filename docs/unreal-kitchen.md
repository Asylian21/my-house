# Kuchyňa v Unreal — otvorené dvere, revízia R2 z 22. 9. 2026

Aktuálny lokálny balík `output/unreal/kitchen-archviz-20260922-r2` prenáša
rovnakú kuchyňu C/B/B ako web. Horný rad má päť dubových čiel a končí
nad hlavnou linkou: X 22 791–26 001 mm, výška 2 258–2 700 mm. Premostenie
nad technickými dverami a vysoká koncová skriňa nad bočnou doskou boli
odstránené. Pri dverách a okne zostáva voľná stena; plávajúca polica nie
je súčasťou návrhu. Bočná nízka linka má pôvodnú kamennú zástenu.

Viditeľný čierny digestor s oceľovým obvodom a filtrami zostáva pod
hornou nikou vo výške 1 520–1 600 mm. Fotografický dub zachováva metrický
UV priebeh a mierku 1/1,83 bez otočenia o 90°. Archviz vrstva dopĺňa
drsnosť, normály a vnútorné svetlá. Rozmery a vzduchovú trasu opisuje
[detail kuchyne](kitchen-island.md).

## Spustenie a dôkazy

Bežný výber `output/unreal/model-refresh-current.json` ukazuje na R2.
Kuchyňa sa otvorí príkazom:

```sh
npm run unreal:open -- interior
```

- [Čelný pohľad 4K](../output/playwright/kitchen-open-doorway-unreal-4k.png)
  zobrazuje aktuálny balík cez skutočný natívny Metal renderer.
- [Vizuálny review](../output/unreal/kitchen-archviz-20260922-r2/kitchen-visual-review.json)
  viaže manifest, balík, import, materiály, snímku a dodatočnú kontrolu Editor súborov.
- [Natívny capture report](../output/unreal/kitchen-archviz-20260922-r2/qa/kitchen-native-4k-14840a6e-bbbe-41ad-8c44-c8c8b4e69161/qa.json)
  potvrdzuje rozlíšenie 3 840 × 2 160, renderovanie 100 %, TSR históriu 200 %,
  aktuálny zdrojový svet a nezmenený obsah balíka pred aj po zachytení.
- [Spustenie cez bežný príkaz](../output/unreal/kitchen-archviz-20260922-r2/kitchen-handoff.json)
  zaznamenáva aktuálny výber a proces aplikácie.

SHA-256 manifestu je
`60e22aec5eca9ef6d7981d3338743f83574c44661a4200c083015fd0357e88ef`;
reportu balíka
`51050d9aac0536cd4acb369c7ac01476ab04d8446b78d6c3d9bd63e441481b86`.

Import, uloženie a opätovné načítanie overili 2 023 objektov a materiálových
väzieb s maximálnou odchýlkou bounds 0,0098 mm. Nový Metal cook, podpis
aj kontrola obsahu balíka prešli. Pred povýšením boli opätovne prepočítané
hash hodnoty všetkých 60 zdrojových súborov a 2 615 vstupov balíka.

C++ sa pri R2 nemenil: Editor a Game používajú overené zhodné binárne
súbory z R1, bez novej kompilácie. Report rozlišuje nula nových kompilačných
krokov od 37 krokov pôvodného Game buildu. [Dodatočný záznam](../output/unreal/kitchen-archviz-20260922-r2/editor-reuse-equivalence.json)
overuje zhodu Editor knižnice, modulov a receipt súboru v čase po importe
a cooku; ide o následnú kontrolu, nie o dodatočne vytvorené predimportné hash väzby.

Snímka slúži na vizuálne posúdenie, nie ako prísľub interaktívneho výkonu
v 4K. Táto revízia neopakovala celú prehliadku domu ani manuálne WASD
ovládanie. Existujúca postava a herné ovládanie používajú nezmenené zdroje.

Predchádzajúce balíky `kitchen-archviz-20260922` (R1 so súvislým horným
rámom) a `archviz-game-20260922` zostávajú zachované. Predošlý aktuálny
výber je uložený v R2 ako `previous-current-selection.json`.
