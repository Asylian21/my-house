# Dom 6012/26 — digitálne dvojča

Interaktívny technický model parcely a navrhovaného rodinného domu v Březí u Mikulova. Aplikácia používa Babylon.js a drží 3D geometriu, výpočty aj inspector nad jedným typovaným modelom v celočíselných milimetroch.

## Dôkazová hranica

- hranica parcely, výmera 753 m² a koridor cestnej parcely 6012/1 s výmerou
  10 647 m² vychádzajú z aktuálnej služby ČÚZK/CP a geometrického plánu,
- zelená cestná rezerva a hrana asfaltu vo vzdialenosti približne 3,104 m od
  parcely sú odvodené z napojení C3 na čelnej aj bočnej vetve; nejde o
  geodetické zameranie skutočných obrubníkov,
- situačná revízia C3 a neskoršia detailná revízia D1.1 sú uložené oddelene; ich rozpor sa neskrýva,
- prípojky vody, splaškovej a dažďovej kanalizácie sú projektovaný stav podľa IO 01–03,
- verejný vodovod a splašková stoka pri parcele sú len kontext z verejnej DMVS,
- skutočné geodetické zameranie prípojok nie je dostupné a aplikácia nič z návrhu neoznačuje ako as-built.

Aktuálna revízia stavebníka z 21. 8. 2026 má pred staršími výkresmi prednosť
v piatich presne ohraničených bodoch: komín pri hlavnom obytnom priestore
zostáva, ale je posunutý o 1 m hlbšie do záhrady, zatiaľ čo druhý komín pri
zóne 1.09 je odstránený; FV pole je na dvorovej rovine krídla posunuté o 2 m
hlbšie do záhrady; bočný spevnený prístup na východnej fasáde je vycentrovaný
na dvere EAST-03; garážová brána s priamym príjazdom je na uličnej fasáde
namiesto prvého garážového okna; súkromnú záhradu uzatvára nový plot podľa
žltého náčrtu s 4,2 m bránou v zelenom otvore pôvodného ľavého zjazdu. Plot je
na úrovni čelnej fasády, takže nezatvára nový priamy príjazd do garáže. Ostatná
geometria D1 zostáva nedotknutá.

Nadväzujúca záhradná revízia zachováva čelné antracitové hliníkové lamely RAL
7016, mení obe bočné hranice na plné nepriehľadné polia a zadnú kovovú líniu na
hustý živý plot. Najnovšia doložená exteriérová revízia požaduje v otvorenom
L-dvore vodnú plochu 5,0 × 3,0 m. Aktuálny modelovaný variant ju po dorovnaní
do vnútorného rohu oboch terás predlžuje na 5,6 × 3,0 m; jeho 6,2 m dlhý lem je
bez medzery napojený na hlavnú aj bočnú terasu a zdieľa s nimi hornú úroveň.
Rozdiel 0,6 m je otvorene vedený ako vizualizačný návrh na potvrdenie. Dažďová
trasa je v modeli predbežne odklonená; najmenší odstup od plášťa potrubia je
približne 0,63 m. Vizualizačná hĺbka vody je navrhnutá na 1,40 m; nie je to
realizačne potvrdená hodnota. Výška 1,6 m, trojdielny teleskopický pojazd, plná skrytá
bránka pri EAST-03, druh živého plota, poloha a technológia bazéna sú
vizualizačný dizajnový návrh. Nie sú schválenou realizačnou špecifikáciou;
materiály, výsadbu, systém a presné geodetické osadenie treba potvrdiť pred
realizáciou.

Režim **Realita** používa projektové rozmery a materiály D1 vrátane oboch
krytých terás odčítaných z vektorov výkresu D1.1.002: zapustenej presklenej
steny pod štítom krídla (TERASA 16,45 m²) a záhradnej lodžie (súčasť TERASY
34,80 m²). Tri drevené terasové zóny (34,80 + 33,10 + 16,45 = 84,35 m²) sa
generujú doska po doske z `TERRACE_ZONES_D1`. Vegetácia, nábytok a
panoramatická atmosféra sú zámerne označené ako ilustračný záhradný koncept.

WebGL výstup používa manuálne riadený Retina framebuffer do 2× DPR, pixelový
rozpočet pre veľké obrazovky, MSAA bez zmäkčujúceho FXAA pri vysokom rozlíšení
(8× MSAA na kompaktných plochách ULTRA vrstvy), plné mipmapy, 16× anizotropné
filtrovanie, stabilizované štvorstupňové kaskádové tiene, plný dielektrický
Fresnel na skle, lom svetla vo vode, ACES tone mapping, jemný HDR bloom iba pre
skutočné odlesky a animovaný filmový grain. Presety Záhrada a Ulica majú
fyzickú výšku kamery 3,05 m a 1,85 m namiesto pôvodného leteckého pohľadu.
Orbitálne ovládanie používa jedinú frame-independent vstupnú cestu Babylonu:
macOS momentum sa už nezdvojuje vlastným glide efektom, zoom smeruje k bodu
pod kurzorom a rotácia, posun aj zoom majú krátku zhodnú zotrvačnosť.
Citlivosť posunu je zámerne tlmená pre touchpad; koliesko aj pinch ostávajú
plynulé a prehliadač ich počas práce s modelom nepreberá. V režime Prelet
koliesko doluje pozdĺž pohľadového lúča. K dispozícii je aj samostatný režim
**Prelet**: stabilná
world-up kamera s ovládaním WASD, Q/E, Shift/Alt, dotykovým ovládačom a
bezpečným návratom do orbitálnych pohľadov.

Režim **Postava** (kláves G) je GTA-style pohyb po interiéri, terase aj
záhrade. Má samostatnú kolíznu kapsulu, viditeľnú low-poly postavu, kameru
za ramenom s kolíziou o steny a režimy za postavou / blízko / z očí (V).
Q prepína rameno, kliknutie zapína voľný pointer-lock rozhľad, Escape najprv
uvoľní kurzor a druhé stlačenie režim ukončí. WASD sa vždy orientuje podľa
kamery, Shift zapína beh a trackpad, koliesko alebo pinch menia iba vzdialenosť
kamery — neposúvajú postavu. Vnútorné
nosné steny, priečky 140 mm, dvere so zárubňami a otvorenými krídlami,
podlahy podľa legendy miestností (keramická dlažba, vinyl, epoxidová stierka),
SDK podhľady 2 600 mm a šikmý podhľad hlavného obytného priestoru
2 750 → 4 850 mm sú odčítané z vektorov výkresu D1.1.002 (`lib/twin-interior.ts`,
hrúbka stien z obrysov 1,44 pt v mierke 1:100). Steny, oplotenie, zatvorené
brány a bazén postavu zastavia; otvorené interiérové dvere a presklené steny
terás zostávajú priechodné. HUD ponúka zbalený vstup do každej z dvanástich
miestností. Plochy 1.01, 1.04 a 1.06–1.12 sedia s legendou na 0,05 m²;
1.02, 1.03 a 1.05 sú v legende merané inak (chodbová chrbtica a kuchynská
nika sa počítajú raz), rozdiel je otvorene vedený v testoch. Kuchynská linka,
kachle pri komíne a soklové lišty sú ilustračný návrh, nie projektová
špecifikácia. Sklo je od tejto revízie skutočne priehľadné (alfa prekrytie s
dielektrickým Fresnelom namiesto lomu IBL panorámy), takže z terasy vidno
interiér a zvnútra terasu.

Krytá terasa pod štítom krídla je modelovaná ako súvislý portálový rám P04:
obe biele podpory (rohový pilier 500 × 500 a koniec východnej steny) pokračujú
nad korunou múru šikmou hlavou až k debneniu strechy, biele lemovacie dosky
štítu sedia spodnou hranou presne na rohu koruny a zadnou plochou lícujú s
čelom podpory, oba žľaby krídla končia v líci lemovky a dažďový zvod DS-02
visí na východnom odkvape (x = 28 040) namiesto voľne stojaceho stĺpika v
otvorenom čele terasy, kde žiadny žľab nie je.

Interiérové PBR sady `vinyl-oak`, `tile-porcelain`, `epoxy-grey` a `tile-wall`
vznikajú rovnakým deterministickým generátorom
(`python3 tools/generate-visual-assets.py interior`).
Textúra trávnika `lawn-albedo.jpg` a botanické karty
`ornamental-grass-card.png` a `perennial-cluster-card.png` boli pre tento
prototyp vygenerované pomocou OpenAI imagegen. Rovnako boli cez vstavaný režim
OpenAI imagegen pre túto revíziu vytvorené `hedge-privet-albedo.png` (bezšvová
fotorealistická báza hustého európskeho vtáčieho zobu, neutrálne mäkké svetlo)
a `pool-water-normal.png` (bezšvová tangent-space normálová mapa jemných
prekrývajúcich sa vĺn pokojného rezidenčného bazéna). PBR sady v
`public/assets/textures` — omietka
(`plaster-white-albedo.jpg`, `plaster-white-normal.jpg`), modřín
(`larch-albedo.jpg`, `larch-normal.jpg`), terasové dosky
(`deck-plank-albedo.jpg`, `deck-plank-normal.jpg`), falcovaný plech
(`metal-anthracite-albedo.jpg`, `metal-anthracite-normal.jpg`), kačírek
(`gravel-albedo.jpg`, `gravel-normal.jpg`), betón (`concrete-albedo.jpg`,
`concrete-normal.jpg`) a normálová mapa trávnika (`lawn-normal.jpg`) sú
procedurálne vygenerované v tomto repozitári (deterministický generátor, žiadne
externé licencie). Aktívne panoramatické pozadie
`suburban-field-01-8k.jpg` má rozlíšenie 8192 × 4096; responzívny variant
`suburban-field-01-4k.jpg` a pamäťovo úsporný IBL variant
`suburban-field-01-2k.jpg` sú odvodené z rovnakého zdroja. Dielo
[Suburban Field 01](https://polyhaven.com/a/suburban_field_01) vytvoril Jacopo
Voltolina a Poly Haven ho publikuje pod licenciou CC0.
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
- `lib/twin-interior.ts` — miestnosti, vnútorné steny a dvere 1.NP odčítané z D1.1.002,
- `lib/twin-viewport-contract.ts` — testovateľná Retina politika, vstupy, pohyb voľnej kamery a chodca,
- `lib/babylon-interior.ts` — stavba interiérového vybavenia zo záznamu miestností,
- `lib/babylon-scene.ts` — jediná hranica medzi milimetrami domény a metrami Babylon scény,
- `app/twin-studio.tsx` — prístupný DOM prieskumník, inspector a stav pracovného priestoru,
- `app/babylon-viewport.tsx` — client-only životný cyklus WebGL canvasu.

Úpravy základov sú v tejto fáze iba session-only náhľad. Trvalé revízie vyžadujú autorizované úložisko; browser storage nie je zdroj pravdy digitálneho dvojčaťa.
