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
Orbitálny zoom používa exponenciálny model vlastnej implementácie: každá
udalosť kolieska násobí cieľový polomer faktorom `exp(gain · px)`, pričom
touchpad scroll, momentum, fyzické koliesko aj pinch (wheel + ctrl) sú
normalizované na pixle a pinch má päťnásobnú citlivosť. Glide polomeru je
framerate-nezávislý s polčasom 42 ms a vždy dobehne presne do cieľa, takže
reakcia je rovnaká pri každom priblížení aj obnovovacej frekvencii; v režime
Prelet koliesko doluje pozdĺž
pohľadového lúča. K dispozícii je aj samostatný režim **Prelet**: stabilná
world-up kamera s ovládaním WASD, Q/E, Shift/Alt, dotykovým ovládačom a
bezpečným návratom do orbitálnych pohľadov.

Režim **Interiér** (kláves G) je prechádzka domom s postavou z pohľadu
tretej osoby. Postava je textúrovaná rigovaná ženská figúra Mixamo „Michelle“
so svetlou pleťou (`public/assets/avatar/avatar.glb`, zdroj: ukážkové modely
three.js). Svetlý albedo atlas
`public/assets/avatar/michelle-light-diffuse.png` vznikol z pôvodnej 512 px
diffuse mapy cielenou úpravou cez OpenAI imagegen a následným presným
maskovaním iba plôch kože; odev, UV švy, kostra a geometria zostali bez
zmeny. Na kostru sú offline preretargetované Mixamo lokomočné klipy
Idle/Walk/Run z
modelu „Vanguard/Soldier“ (`tools/avatar/retarget.mjs`: zhoda svetových
orientácií kostí oproti obom T-pózam, zarovnanie smeru postáv, preškálovaný
posun bokov). Mixamo assety podliehajú licencii Adobe Mixamo (použitie
v projekte áno, samostatná redistribúcia nie); textúry figúry majú 512 px, čo
je hranica realizmu dostupných voľných rigovaných postáv. Ovládanie: W A S D
chôdza v smere kamery, ťahanie otáča kameru okolo postavy, Shift beh, koliesko
priblíženie, V prepne pohľad z očí a R vystredí kameru alebo vráti zaseknutú
postavu na posledný bezpečný bod; pohyb má krátke zrýchlenie a dobeh
(`WALK_CAMERA` v `lib/twin-viewport-contract.ts`), postava sa otáča do smeru
skutočného posunu a kamera sa po 0,58 s bez ťahania plynulo vracia za postavu.
Päťlúčová vnútorná sonda pred stenou okamžite skráti kamerové rameno bez
straty používateľovho priblíženia; po uvoľnení ho obnoví s polčasom 120 ms.
Pod približne 1 m sa postava schová a pohľad plynulo prejde k výške očí, takže
nezacloní malé WC ani úzku chodbu. Animácie Idle/Walk/Run sa
miešajú podľa rýchlosti a klipy sú časovo škálované, aby nohy nekĺzali.
Staršia verzia režimu bola iba kamera vo výške očí 1,65 m; tá zostáva ako
pohľad z očí (V). Vnútorné
nosné steny, priečky 140 mm, dvere so zárubňami a otvorenými krídlami,
podlahy podľa legendy miestností (keramická dlažba, vinyl, epoxidová stierka),
SDK podhľady 2 600 mm a šikmý podhľad hlavného obytného priestoru
2 750 → 4 850 mm sú odčítané z vektorov výkresu D1.1.002 (`lib/twin-interior.ts`,
hrúbka stien z obrysov 1,44 pt v mierke 1:100). Chodec sa ovláda rovnako ako
prelet (WASD, ťahanie, Shift/Alt), steny ho zastavia cez kolízny elipsoid
s polomermi 0,22 × 0,80 × 0,22 m a pohyb sa delí na najviac 50 mm kroky.
Otvorené interiérové dvere a presklené steny
terás zostávajú priechodné; HUD ponúka priamy vstup do každej z dvanástich
miestností. Plochy 1.01, 1.04 a 1.06–1.12 sedia s legendou na 0,05 m²;
1.02, 1.03 a 1.05 sú v legende merané inak (chodbová chrbtica a kuchynská
nika sa počítajú raz), rozdiel je otvorene vedený v testoch. Kuchynská linka,
kachle pri komíne a soklové lišty sú ilustračný návrh, nie projektová
špecifikácia. Sklo je od tejto revízie skutočne priehľadné (alfa prekrytie s
dielektrickým Fresnelom namiesto lomu IBL panorámy), takže z terasy vidno
interiér a zvnútra terasu.

Revízia stavebníka z 22. 8. 2026 (`SOURCES.clientRevision20260822`) mení tri
veci v obytnom priestore 1.03: kachle s komínom sú menšie a stoja hneď vedľa
dverí na bazénovú terasu opreté o západnú stenu — dymovod vedie do murovaného
piliera 346 × 500 z výkresu D1.1.002, ktorý je teraz komínovým telesom
(`HOUSE.chimneys[0]`, prestup strechou na dvorovej rovine, FV pole preto
posunuté o ďalší stĺpcový krok 1,1 m do záhrady); štítová stena k prístrešku
má podľa referenčnej fotografie stavebníka pri rohovom pilieri 500 mm
murovaný pilier, potom jediné pevné presklenie 2 000 × 2 750 (bez dverí),
nad ním uzavretý pás venca +2,750 → +3,050 cez celú šírku a nad pásom iba
malý pravouhlý trojuholníkový svetlík so spodnou stranou v dĺžke skla, šikmou
stranou pozdĺž podhľadu a zvislou stranou na východnej hrane skla; zvyšných
3 500 je modřínom obložená plná stena a celý zvyšok štítu je modřín zvonku a
omietka zvnútra; kuchyňa
je postavená podľa pôdorysu D1.1.002 — zadná linka 2 900 s drezom a umývačkou,
na jej západnom konci samostatná 600 mm vstavaná chladnička s mrazničkou v
dubovom dekore, biele horné skrinky s LED lištou a tmavý
kremeňový obklad, polostrov 4 750 × 600 s indukčnou doskou, ostrovným
odsávačom, rúrou pod varnou doskou a voľným presahom bez barových stoličiek
(`KITCHEN_RUN`, dubová dyha `oak-veneer`,
kremeň `stone-dark`). Východný koniec polostrova sa v priestore zo snímky
prechádzky zalamuje do krátkeho 994 × 600 mm L-returnu s dvoma dubovými
skrinkami, nadväzujúcou kremennou doskou a nízkym obkladom; končí 156 mm pred
oknom EAST-04 a začína 260 mm za otvorom dverí technickej miestnosti. Technická
miestnosť 1.07 obsahuje vizualizačný návrh vykurovania
(`TECHNICAL_HEATING_FITOUT`): drevosplyňovací kotol 800 × 900 × 1 450 mm v
južnom výklenku a zvislú akumulačnú nádrž s nominálnym objemom 1 000 l,
priemerom 1 000 mm a výškou 2 100 mm v západnom poli. Obe telesá kopírujú
technologické zóny D1.1.002, neblokujú kuchynské dvere ani EAST-03 a zachovávajú
900 mm servisný pás pred kotlom. Výrobca, hydraulika, prívod spaľovacieho
vzduchu, požiarne odstupy a samostatný komín nie sú realizačne potvrdené.
Klientská revízia zároveň posúva priečku medzi 1.06 a 1.07 o 300 mm do
technickej miestnosti: WC má nový čistý rozmer 1 299 × 1 600 mm a geometrickú
plochu približne 2,08 m². `WC_FITOUT` dopĺňa závesnú misu s podomietkovým
modulom, kompaktné 450 mm umývadlo, batériu a zrkadlo; pred misou ostáva 779 mm
a otvorené dverné krídlo je bez kolízie. Akumulačná nádrž je v zmenšenom
západnom poli technickej miestnosti nanovo vycentrovaná.
Klientská kompaktná revízia kúpeľne a práčovne 1.05 ponecháva všetky priečky
aj vysoké okno EAST-02. Pôvodné rozdrobené zariadenie nahrádza 1 400 × 900 mm
walk-in sprcha vo východnom výklenku, plávajúca 1 000 mm umývadlová skrinka
a jediná 650 × 650 mm vetraná veža s práčkou a sušičkou nad sebou
(`BATHROOM_FITOUT`). Otvorené dvere zostávajú bez kolízie, pred spotrebičmi je
900 mm servisný pás a voľný stred má šírku približne 1,5 m. Ide o interiérový
dizajnový koncept; hydroizoláciu, odvetranie a výrobné napojenia musí potvrdiť
profesijný projekt. Okná a dvere sú
stavané ako skutočné výplne
(`lib/babylon-openings.ts`): rám 150 mm za lícom fasády, krídla s vlastným
profilom a kľučkou, izolačné dvojsklo, vnútorný postformingový parapet s
ušami a nosom, exteriérový hliníkový parapet s okapnicou a bočnicami, zdvižno‑
posuvné dvere s pevným a posuvným krídlom na dvoch koľajniciach a vstupné
dvere s bočným svetlíkom. Pevné sklá zastavujú chodca, posuvné a dverné
krídla sú priechodné.

Revízia interiéru stavebníka z 23. 8. 2026 dopĺňa do 1.03 ucelenú obývaciu a
jedálenskú zónu (`LIVING_DINING_FITOUT`). Na západnej stene je za komínovým
pilierom 3,37 m dlhá vstavaná bezúchytková TV zostava v teplej greige, dubovej
dyhe a tmavom kameni, so zapusteným 98-palcovým TV, plávajúcou skrinkou,
soundbarom a nepriamou 2700 K LED. Oproti stojí nízka svetlá modulová
L-sedačka s ležadlom až na plnej časti štítovej steny, na koberci s dvojicou
oválnych stolíkov. Medzi kuchynským polostrovom a sedačkou je kompaktný klasický
dubový stôl 1 400 × 800 so štyrmi zúženými nohami, štyrmi rámovými čalúnenými
stoličkami a jedným centrálnym teplým závesným svietidlom.
Pôdorysné odstupy od krbu, zadného muriva, pevného skla a priechodov sú uzamknuté
kontraktovými testami; finálny protipožiarny odstup a výrobnú skladbu TV steny
musí potvrdiť dodávateľ konkrétnych kachlí a interiéru.

Krytá terasa pod štítom krídla je modelovaná ako súvislý portálový rám P04:
obe biele podpory (rohový pilier 500 × 500 a koniec východnej steny) pokračujú
nad korunou múru šikmou hlavou až k debneniu strechy, biele lemovacie dosky
štítu sedia spodnou hranou presne na rohu koruny a zadnou plochou lícujú s
čelom podpory, oba žľaby krídla končia v líci lemovky a dažďový zvod DS-02
visí na východnom odkvape (x = 28 040) namiesto voľne stojaceho stĺpika v
otvorenom čele terasy, kde žiadny žľab nie je.

Interiérové PBR sady `vinyl-oak`, `tile-porcelain`, `epoxy-grey`, `tile-wall`,
`oak-veneer`, `stone-dark`, `boucle-taupe` a `rug-wool-taupe`
vznikajú rovnakým deterministickým generátorom
(`python3 tools/generate-visual-assets.py interior`; textílie dennej zóny samostatne
cez `python3 tools/generate-visual-assets.py living`).
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
- `lib/babylon-openings.ts` — okná, parapety, posuvné a vstupné dvere,
- `lib/babylon-avatar.ts` — postava prechádzky, jej kolízie, animácie a sledovacia kamera,
- `lib/babylon-scene.ts` — jediná hranica medzi milimetrami domény a metrami Babylon scény,
- `app/twin-studio.tsx` — prístupný DOM prieskumník, inspector a stav pracovného priestoru,
- `app/babylon-viewport.tsx` — client-only životný cyklus WebGL canvasu.

Úpravy základov sú v tejto fáze iba session-only náhľad. Trvalé revízie vyžadujú autorizované úložisko; browser storage nie je zdroj pravdy digitálneho dvojčaťa.
