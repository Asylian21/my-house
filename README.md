# Dom 6012/26 — digitálne dvojča

Interaktívny technický model parcely a navrhovaného rodinného domu v Březí u Mikulova. Aplikácia používa Babylon.js a drží 3D geometriu, výpočty aj inspector nad jedným typovaným modelom v celočíselných milimetroch.

## Dôkazová hranica

- hranica parcely a výmera 753 m² vychádzajú z aktuálneho ČÚZK/CPX a geometrického plánu,
- situačná revízia C3 a neskoršia detailná revízia D1.1 sú uložené oddelene; ich rozpor sa neskrýva,
- prípojky vody, splaškovej a dažďovej kanalizácie sú projektovaný stav podľa IO 01–03,
- verejný vodovod a splašková stoka pri parcele sú len kontext z verejnej DMVS,
- skutočné geodetické zameranie prípojok nie je dostupné a aplikácia nič z návrhu neoznačuje ako as-built.

Režim **Realita** používa projektové rozmery a materiály D1. Vegetácia, nábytok
a panoramatická atmosféra sú zámerne označené ako ilustračný záhradný koncept.
Lokálne panoramatické pozadie `public/assets/environment/overcast-garden.jpg`,
textúra trávnika `public/assets/textures/lawn-albedo.jpg`, vizualizačný obklad
`public/assets/textures/larch-cladding-v2.jpg`, teplá fasádna omietka
`public/assets/textures/stucco-warm-v1.jpg`, terasové drevo
`public/assets/textures/deck-larch-v1.jpg` a botanické karty
`public/assets/vegetation/ornamental-grass-card.png` a
`public/assets/vegetation/perennial-cluster-card.png` boli pre tento prototyp
vygenerované pomocou OpenAI imagegen. Nereprezentujú skutočný stav parcely, jej
susedov ani konkrétny dodaný výrobok či realizačný výber výsadby.

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
