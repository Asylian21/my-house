# Dom 6012/26 — digitálne dvojča

Interaktívny technický model parcely a navrhovaného rodinného domu v Březí u Mikulova. Aplikácia používa Babylon.js a drží 3D geometriu, výpočty aj inspector nad jedným typovaným modelom v celočíselných milimetroch.

## Dôkazová hranica

- hranica parcely a výmera 753 m² vychádzajú z aktuálneho ČÚZK/CPX a geometrického plánu,
- situačná revízia C3 a neskoršia detailná revízia D1.1 sú uložené oddelene; ich rozpor sa neskrýva,
- prípojky vody, splaškovej a dažďovej kanalizácie sú projektovaný stav podľa IO 01–03,
- verejný vodovod a splašková stoka pri parcele sú len kontext z verejnej DMVS,
- skutočné geodetické zameranie prípojok nie je dostupné a aplikácia nič z návrhu neoznačuje ako as-built.

Aktuálna revízia stavebníka z 21. 8. 2026 má pred staršími výkresmi prednosť
v troch presne ohraničených bodoch: komín nad hlavným obytným/kuchynským
priestorom zostáva a odstránený je druhý komín pri zóne 1.09, FV pole je na
dvorovej rovine krídla nad kuchyňou posunuté bližšie k bočnej terase a mimo
ponechaného komína a garážová brána s priamym príjazdom je na uličnej fasáde
namiesto prvého garážového okna. Ostatná geometria D1 zostáva nedotknutá.

Režim **Realita** používa projektové rozmery a materiály D1 vrátane oboch
krytých terás odčítaných z vektorov výkresu D1.1.002: zapustenej presklenej
steny pod štítom krídla (TERASA 16,45 m²) a záhradnej lodžie (súčasť TERASY
34,80 m²). Tri drevené terasové zóny (34,80 + 33,10 + 16,45 = 84,35 m²) sa
generujú doska po doske z `TERRACE_ZONES_D1`. Vegetácia, nábytok a
panoramatická atmosféra sú zámerne označené ako ilustračný záhradný koncept.

Lokálne panoramatické pozadie `overcast-garden.jpg`, textúra trávnika
`lawn-albedo.jpg` a botanické karty `ornamental-grass-card.png`
a `perennial-cluster-card.png` boli pre tento prototyp vygenerované pomocou
OpenAI imagegen. PBR sady v `public/assets/textures` — omietka
(`plaster-white-albedo.jpg`, `plaster-white-normal.jpg`), modřín
(`larch-albedo.jpg`, `larch-normal.jpg`), terasové dosky
(`deck-plank-albedo.jpg`, `deck-plank-normal.jpg`), falcovaný plech
(`metal-anthracite-albedo.jpg`, `metal-anthracite-normal.jpg`), kačírek
(`gravel-albedo.jpg`, `gravel-normal.jpg`), betón (`concrete-albedo.jpg`,
`concrete-normal.jpg`) a normálová mapa trávnika (`lawn-normal.jpg`) — spolu s
IBL oblohou `sky-partly-cloudy.jpg` sú procedurálne vygenerované v tomto
repozitári (deterministický generátor, žiadne externé licencie).
Nereprezentujú skutočný stav parcely, jej susedov ani konkrétny dodaný výrobok
či realizačný výber výsadby.

Zdrojové PDF a presné projektové podklady zostávajú lokálne v `arch-docs/`; tento adresár je zámerne ignorovaný Gitom a nič z neho sa nekopíruje do `public/`.

## Spustenie

Vyžaduje Node.js 22.13 alebo novší.

```bash
npm install
npm run dev
```

Kompletný lokálny gate:

```bash
npm test
```

Gate zahŕňa ESLint, doménové testy, produkčný build a kontrolu serverom vyrenderovaného HTML shellu.

## Architektúra

- `lib/twin-domain.ts` — engine-free doména, presný lokálny S-JTSK rám, proveniencia a nemenná história úprav,
- `lib/twin-site.ts` — projektové revízie, vrstvy, zdroje a parametrické základy,
- `lib/twin-facade.ts` — čisté delenie fasádneho plášťa okolo zdrojovaných otvorov,
- `lib/babylon-scene.ts` — jediná hranica medzi milimetrami domény a metrami Babylon scény,
- `app/twin-studio.tsx` — prístupný DOM prieskumník, inspector a stav pracovného priestoru,
- `app/babylon-viewport.tsx` — client-only životný cyklus WebGL canvasu.

Úpravy základov sú v tejto fáze iba session-only náhľad. Trvalé revízie vyžadujú autorizované úložisko; browser storage nie je zdroj pravdy digitálneho dvojčaťa.
