# Dom 6012/26 — digitálne dvojča

Interaktívny technický model parcely a navrhovaného rodinného domu v Březí u Mikulova. Aplikácia používa Babylon.js a drží 3D geometriu, výpočty aj inspector nad jedným typovaným modelom v celočíselných milimetroch.

Historické verzie sú dostupné na `/v1` a `/v2`. Vetva `v2` uchováva celý
repozitár zo 7. 9. 2026 na commite `0bcbb57774fd551137c2b596a899a0432b148f28`.
Trasa `/v2` používa samostatný zdroj v `versions/v2/` a súbory v
`public/v2-assets/`; zahŕňa aj `/v2/koncept-2d` so všetkými variantmi.
Ďalší vývoj patrí do `main`. Historické kópie a ich assety zostávajú nemenné;
obnoviť presnú kópiu umožňuje `node scripts/snapshot-v2.mjs`.

Lokálny **Blender Cycles ArchViz** pipeline exportuje celý model do OBJ/GLB,
zostaví scénu s PBR materiálmi a umožní 4K rendery. Spustenie:
`npm run archviz:setup`, `npm run archviz:preview`, `npm run archviz:render`.
Podrobnosti, ovládanie prechádzky a výstupy sú v [návode ArchViz](scripts/archviz/README.md).

Samostatná macOS vetva v Unreal Engine používa ten istý zdroj geometrie:
[Unreal export, audit a build](scripts/unreal/README.md). `npm run unreal:export`
vytvorí GLB aktívnej scény a oddelený technický archív s kontrolou rozmerov,
revízií a pôvodu dát. Natívny projekt žije v `unreal/BreziTwin`.

Publikovaná 4K vizualizácia je dostupná tlačidlom **4K** v ovládaní modelu
a priamo na `/archviz/garden-4k.jpg`. Web používa JPEG kópiu finálneho renderu;
pôvodný 16-bitový PNG a Blender scéna zostávajú v lokálnom `output/archviz/`.

Režim **Realita** načítava aj interaktívnu podobu tejto Blender scény:
textúrovaný dom, celý existujúci interiér, záhradný nábytok a skenovanú vegetáciu.
Zachováva otáčanie, prelet, chôdzu, kolízie a všetky pôvodné dvere a mechanizmy.
Deväť GLB balíkov má spolu približne 39 MiB; obloha `sky.hdr` používa HDR z uloženého Blender
sveta. Postup obnovy assetov a ich pôvod sú v [návode webového exportu](scripts/archviz/web/README.md).

Obývačka má samostatnú teplú paletu ecru, piesku, dubu, kašmíru a terakoty,
aplikovanú na pôvodný aj importovaný interiér podľa identifikátorov `LIVING-103-`.
Auto je vlastná webová modelácia Superbu Combi IV podľa referenčných pohľadov
a [oficiálneho technického listu](https://cdn.skoda-storyboard.com/2024/03/TD-Superb-en_87b42ad4.pdf),
nie importovaný model výrobcu. Plynulá karoséria používa monotónne kubické krivky;
sklá, maska a svetlá sú orezané podľa jej skutočných trojuholníkov.
`node tools/superb-geometry-check.mjs` kontroluje odstupy panelov, plynulosť profilu,
umiestnenie podbehov a animačné aj kolízne rozhrania.
Pri chybe načítania zostáva funkčný pôvodný model s možnosťou opakovania.
Web dodáva osvetlenie v reálnom čase; Cycles globálne osvetlenie nie je zapečené.

## Dôkazová hranica

- hranica parcely, výmera 753 m² a koridor cestnej parcely 6012/1 s výmerou
  10 647 m² vychádzajú z aktuálnej služby ČÚZK/CP a geometrického plánu,
- nespevnená cestná rezerva a hrana vozovky vo vzdialenosti približne 3,104 m
  od parcely sú odvodené z napojení C3 na čelnej aj bočnej vetve; vzhľad
  hlinenej krajnice, obrubníka a dlažby potvrdzuje fotografia z 25. 8. 2026,
  nejde však o geodetické zameranie skutočných obrubníkov,
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

Fotografická revízia ulice z 25. 8. 2026 mení zelený trávnik v cestnej rezerve
na nepravidelnú hlinenú krajnicu s riedkou náletovou vegetáciou, zosvetľuje
sivú blokovú dlažbu, zachováva zvýšený prefabrikovaný obrubník bez chodníka a
dopĺňa štíhle sivé stožiare verejného osvetlenia. Presný rozstup stožiarov a
geodetická poloha obrubníka zostávajú otvorene označené ako ilustračné.

Revízia z 25. 8. 2026 dopĺňa na západný bočný štít garáže zo strany označenej
na referenčnej snímke okno `WEST-GARAGE-01`. Má rovnaký otvor 1 250 × 750 mm,
parapet 1 750 mm aj antracitové rámovanie ako zostávajúce garážové okno
`FRONT-02` a je vycentrované v hlavnom vnútornom poli garáže 1.12.

Najnovšia interiérová revízia z 24. 8. 2026 prepisuje iba podobu hlavného
komína: murovaný pilier pri 1.03 už v aktívnom modeli nie je. Nahrádza ho
štíhla matne čierna trubka vedená priamo z osi valcových krbových kachlí cez
šikmý podhľad a dvorovú rovinu strechy (`FIREPLACE_STOVE`, `HOUSE.flues[0]`).
Polohová korekcia z 25. 8. 2026 posúva celú os kachlí a rúry o 200 mm smerom
k TV zostave; medzi telesom krbu a TV stenou zostáva 650 mm.

Nadväzujúca záhradná revízia zachováva čelné antracitové hliníkové lamely RAL
7016, mení obe bočné hranice na plné nepriehľadné polia a zadnú kovovú líniu na
hustý živý plot. Klientska revízia z 29. 8. 2026 mení bazén v otvorenom L-dvore
na mierne dlhšiu a užšiu vodnú plochu 6,0 × 2,7 m. Svetlý 300 mm lem je bez
medzery napojený na hlavnú aj bočnú terasu a zdieľa s nimi hornú úroveň.
Na západnej strane vedie smerom do záhrady nový 1 m široký pozdĺžny pás;
zadný pás bezprostredne za bazénom zostáva široký 2 m. Spolu majú hrubú plochu
18,50 m² a čistú plochu 17,51 m² po odpočítaní poklopu. Kolidujúce kríky,
okrasné trávy a mulčovaný záhon okolo bazéna sú
odstránené; zadný živý plot na hranici parcely zostáva. Dažďová trasa je
predbežne vedená južne od rohovej šachty; dažďová nádrž aj vsakovací objekt
sú posunuté iba o nevyhnutných 600/600 mm hlbšie do záhrady. Najmenší
modelovaný odstup bazéna od plášťa potrubia zostáva približne 0,69 m a šachta
má od potrubia 0,13 m. Vizualizačná hĺbka vody je
navrhnutá na 1,40 m; nie je to realizačne potvrdená hodnota. Výška 1,6 m,
trojdielny teleskopický pojazd, plná skrytá
bránka pri EAST-03, druh živého plota, poloha a technológia bazéna sú
vizualizačný dizajnový návrh. Nie sú schválenou realizačnou špecifikáciou;
materiály, výsadbu, systém a presné geodetické osadenie treba potvrdiť pred
realizáciou.

Režim **Realita** používa projektové rozmery a materiály D1 vrátane oboch
krytých terás odčítaných z vektorov výkresu D1.1.002: zapustenej presklenej
steny pod štítom krídla (TERASA 16,45 m²) a záhradnej lodžie (pôvodne súčasť
TERASY 34,80 m²). Aktívna revízia predlžuje garáž 1.12 o 1 000 mm do lodžie,
preto má záhradná zóna 30,60 m² a súčet terás klesá z pôvodných 84,35 m² na
80,15 m². Pôvodné drevené zóny sa generujú doska po doske z
`TERRACE_ZONES_D1`; nová bazénová plocha je samostatná klientská revízia
`POOL_SURROUND_DECK`, takže historický súčet D1 nemení.
Vegetácia, nábytok a
panoramatická atmosféra sú zámerne označené ako ilustračný záhradný koncept.

WebGL výstup pre detailnú Blender scénu používa framebuffer do 1,5× DPR
(1,25× na dotykových zariadeniach) s rozpočtom 2,2 milióna pixelov, 2× MSAA
podľa podpory zariadenia, plné mipmapy, 8× anizotropné
filtrovanie, stabilizované štvorstupňové kaskádové tiene, plný dielektrický
Fresnel na skle, lom svetla vo vode, ACES tone mapping, jemný HDR bloom iba pre
skutočné odlesky, PBR specular anti-aliasing a časovo stabilný obraz bez
animovaného filmového grainu. Presety Záhrada a Ulica majú
fyzickú výšku kamery 3,05 m a 1,90 m namiesto pôvodného leteckého pohľadu;
uličný preset stojí priamo na vozovke a mieri mierne nadol, aby bola dlažba
viditeľná v spodnej tretine záberu.
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
tretej osoby. V rozbaľovacom paneli sa dá počas hry prepínať medzi troma
rigovanými postavami bez zmeny pozície, kamery alebo kolízií; voľba zostáva
uložená iba lokálne v prehliadači. Pôvodná postava je ženská figúra Mixamo
„Michelle“ so svetlou pleťou (`public/assets/avatar/avatar.glb`, zdroj:
ukážkové modely three.js). Svetlý albedo atlas
`public/assets/avatar/michelle-light-diffuse.png` vznikol z pôvodnej 512 px
diffuse mapy cielenou úpravou cez OpenAI imagegen a následným presným
maskovaním iba plôch kože; odev, UV švy, kostra a geometria zostali bez
zmeny. Na kostru sú offline preretargetované Mixamo lokomočné klipy
Idle/Walk/Run z
modelu „Vanguard/Soldier“ (`tools/avatar/retarget.mjs`: zhoda svetových
orientácií kostí oproti obom T-pózam, zarovnanie smeru postáv, preškálovaný
posun bokov). Druhá voľba **Vanguard** používa pôvodný rig aj vlastné textúry
tohto modelu (`public/assets/avatar/vanguard.glb`; SHA-256
`dfb230fc1f942f259dd00281a1186953ad602fc5d69067ce63e24b2aa439736b`).
Mixamo assety podliehajú licencii Adobe Mixamo (použitie v projekte áno,
samostatná redistribúcia nie); tento Sites projekt zostáva owner-only.
Tretia voľba **Robo** je `public/assets/avatar/robot-expressive.glb`, model
RobotExpressive od Tomása Laulhé, upravený Donom McCurdym a vydaný ako
[CC0 1.0](https://github.com/mrdoob/three.js/tree/21585c3021567e7284f1c881b392208a11264a63/examples/models/gltf/RobotExpressive)
(pripnutý upstream commit `21585c3`, SHA-256
`047f5e5fb3bb6d378bd1df16ca6137f2a596c99b3a1b5690b4020c05aaf6f319`).
Ovládanie: W A S D
chôdza v smere kamery, ťahanie otáča kameru okolo postavy, Shift beh, koliesko
priblíženie, E alebo dotyk na kontextovú výzvu ovláda blízke dvere, dvierka
práčky a sušičky, poklop bazénovej šachty aj riadený zostup po rebríku,
V prepne pohľad z očí a R vystredí kameru alebo vráti zaseknutú postavu na
posledný bezpečný bod; pohyb má krátke zrýchlenie a dobeh
(`WALK_CAMERA` v `lib/twin-viewport-contract.ts`), postava sa otáča do smeru
skutočného posunu a kamera sa po 0,58 s bez ťahania plynulo vracia za postavu.
Päťlúčová vnútorná sonda pred stenou okamžite skráti kamerové rameno bez
straty používateľovho priblíženia; po uvoľnení ho obnoví s polčasom 120 ms.
Pod približne 1 m sa postava schová a pohľad plynulo prejde k výške očí, takže
nezacloní malé WC ani úzku chodbu. Animácie Idle/Walk/Run sa
miešajú podľa rýchlosti a klipy sú časovo škálované, aby nohy nekĺzali.
Staršia verzia režimu bola iba kamera vo výške očí 1,65 m; tá zostáva ako
pohľad z očí (V). Vnútorné
nosné steny, priečky 140 mm, 11 interiérových dverí so zárubňami, kľučkami a
animovanými kolíznymi krídlami,
podlahy podľa legendy miestností (keramická dlažba, vinyl, epoxidová stierka),
SDK podhľady 2 600 mm a šikmý podhľad hlavného obytného priestoru
2 750 → 4 850 mm sú odčítané z vektorov výkresu D1.1.002 (`lib/twin-interior.ts`,
hrúbka stien z obrysov 1,44 pt v mierke 1:100). Chodec sa ovláda rovnako ako
prelet (WASD, ťahanie, Shift/Alt), steny ho zastavia cez kolízny elipsoid
s polomermi 0,22 × 0,80 × 0,22 m a pohyb sa delí na najviac 50 mm kroky.
Spoločný kontrolér pokrýva presne 22 interakcií: 18 architektonických dverových
systémov, dvoje dvierka spotrebičov, pochôdzny poklop šachty a obojsmerný
riadený prechod po rebríku.
Zatvorené krídlo chodca zastaví, po animovanom otvorení uvoľní reálny priechod.
Krídlo, ktoré sa otvára na chodca, ho po milimetroch odsúva pred svojou plochou
(`actorDisplacement` v `lib/babylon-doors.ts`), takže dvere sa dajú otvoriť aj
tesne pred nimi; pohyb sa pozastaví s výzvou „Ustúpte z dráhy dverí“ iba vtedy,
keď postavu nemá kam odsunúť (stena, nábytok). Pri približovaní k otvoru sa
smer chôdze jemne stáča na os priechodu a takmer zamietnutý krok sa skúsi
vychýliť o ±30°/±60°, aby zárubňa ani roh skrine nezastavili chodca
(`lib/twin-walk-assist.ts`). V interiéri sa k obrazu pripája SSAO2 a na
tieri ULTRA aj odrazy v obrazovom priestore (`INTERIOR_RENDER_QUALITY`);
stack sa zapína s hysterézou podľa vnútorného blendu, pri trvalom zaťažení
sa odľahčuje a exteriér zostáva bez skrínových efektov. HUD ponúka priamy vstup do každej z dvanástich
miestností. Plochy 1.01, 1.04 a 1.06–1.12 sedia s legendou na 0,05 m²;
1.02, 1.03 a 1.05 sú v legende merané inak (chodbová chrbtica a kuchynská
nika sa počítajú raz), rozdiel je otvorene vedený v testoch. Kuchynská linka,
valcové krbové kachle so zvislým dymovodom a soklové lišty sú ilustračný návrh, nie projektová
špecifikácia. Sklo je od tejto revízie skutočne priehľadné (alfa prekrytie s
dielektrickým Fresnelom namiesto lomu IBL panorámy), takže z terasy vidno
interiér a zvnútra terasu.

Na vonkajšom juhozápadnom okraji zadného pásu, v záhradnom rohu smerom od domu,
je pod drevenou terasou kompaktná železobetónová technologická šachta
`POOL_TECHNOLOGY_SHAFT` s pôdorysom 3 100 × 1 700 mm, podlahou na −2,200 m,
svetlou výškou 2,080 m a pochôdznym poklopom 900 × 1 100 mm. Po otvorení poklopu sa dá
v režime Prechádzka cez E alebo dotyk bezpečne zostúpiť po sedempriečkovom
nerezovom rebríku a rovnakým spôsobom sa vrátiť na terasu. Vnútri je
vymodelovaná piesková filtrácia Ø 620 mm, predfilter, 0,75 kW obehové čerpadlo,
tlakové potrubia, podlahová vpusť, servisné svietidlo a IP65 rozvádzač s ôsmimi
ističmi. Rozmery, hydroizolácia, vetranie, odvodnenie, elektrická ochrana,
pospájanie aj napojenie bazénovej technológie sú klientskym vizualizačným
návrhom a vyžadujú realizačnú koordináciu ZTI, elektro a statiky.

Revízia stavebníka z 22. 8. 2026 (`SOURCES.clientRevision20260822`) mení tri
veci v obytnom priestore 1.03: kachle s komínom sú menšie a stoja hneď vedľa
dverí na bazénovú terasu opreté o západnú stenu — dymovod vedie do murovaného
piliera 346 × 500 z výkresu D1.1.002, ktorý bol komínovým telesom v historickej
revízii (tento pilier neskôr ruší `SOURCES.clientFireplaceRevision20260824`;
prestup strechou na dvorovej rovine zostáva a FV pole je preto
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
kremeňový obklad, pôvodne 4 750 × 600 polostrov skrátený pri západnom konci
o presný 600 mm modul oproti chladničke na výsledných 4 150 × 600, s indukčnou
doskou, ostrovným odsávačom, rúrou pod varnou doskou a voľným presahom bez
barových stoličiek
(`KITCHEN_RUN`, dubová dyha `oak-veneer`,
kremeň `stone-dark`). Varná doska, rúra a odsávač zostávajú na spoločnej osi,
ktorá je po skrátení 699 mm od nového kraja; západný priechod sa rozšíril
o 600 mm približne na 1 848 mm. Východný koniec polostrova sa v priestore zo
snímky prechádzky zalamuje do krátkeho 994 × 600 mm L-returnu s dvoma dubovými
skrinkami, nadväzujúcou kremennou doskou a nízkym obkladom; končí 156 mm pred
oknom EAST-04 a začína 260 mm za otvorom dverí technickej miestnosti. Technická
miestnosť 1.07 obsahuje vizualizačný návrh vykurovania
(`TECHNICAL_HEATING_FITOUT`): kombinovanú zostavu typu DEFRO Firewood Duo
15 kW pre alternatívne režimy kusové drevo alebo pelety, s uzavretou obálkou
1 188 × 1 224 × 1 391 mm. Sivé viacdverové teleso dopĺňa samostatná približne
180 kg násypka, šnekový podávač, pružná jantárová hadica, predný peletový horák
a horný farebný regulátor. V západnom poli zostáva zvislá akumulačná nádrž
s nominálnym objemom 1 000 l, priemerom 1 000 mm a výškou 2 100 mm. Zostava
fyzicky vojde do južného výklenku, neblokuje kuchynské dvere ani EAST-03
a pred čelom zachováva 2 000 mm čistú servisnú hĺbku. Vizualizovaných 405 mm
po bokoch a 50 mm vzadu je menej než 500 mm odporúčanie referenčného výrobcu;
konkrétny výkon, hydrauliku, prívod spaľovacieho vzduchu, požiarne odstupy
a komín preto musí potvrdiť profesijný projekt.
Klientská revízia zároveň posúva priečku medzi 1.06 a 1.07 o 300 mm do
technickej miestnosti: WC má nový čistý rozmer 1 299 × 1 600 mm a geometrickú
plochu približne 2,08 m². `WC_FITOUT` dopĺňa závesnú misu s podomietkovým
modulom, kompaktné 450 mm umývadlo, batériu a zrkadlo; pred misou ostáva 779 mm
a plne otvorené dverné krídlo má overenú voľnú dráhu. Akumulačná nádrž je v zmenšenom
západnom poli technickej miestnosti nanovo vycentrovaná.
Finálna klientská revízia kúpeľne a práčovne 1.05 zachováva posunutú severnú
priečku aj vysoké okno EAST-02. Na konci východného výklenku je 1 250 × 900 mm walk-in
sprcha. Celý 2 616 mm široký zadný výrez tvorí jedna 650 mm hlboká vstavaná
zostava (`BATHROOM_FITOUT`): veľké 1 330 × 450 mm matne čierne umývadlo a jedna
600 mm vetraná veža s práčkou dole a sušičkou hore. Obe kruhové dvierka sa
samostatne otvárajú cez E, dotykovú výzvu alebo priamy klik. Na voľnej južnej
stene je matne čierny rebríkový radiátor 600 × 1 500 mm. Pred zostavou ostáva
súvislý pás 2 616 × 669 mm a pred vežou 900 mm servisná hĺbka; plne otvorené
vstupné dvere, radiátor, sprcha ani vysoké okno nie sú v kolízii. Ide o
interiérový dizajnový koncept; hydroizoláciu, odvetranie a
výrobné napojenia musí potvrdiť profesijný projekt. Okná a dvere sú
stavané ako skutočné výplne
(`lib/babylon-openings.ts`): rám 150 mm za lícom fasády, krídla s vlastným
profilom a kľučkou, izolačné dvojsklo, vnútorný postformingový parapet s
ušami a nosom, exteriérový hliníkový parapet s okapnicou a bočnicami, zdvižno‑
posuvné dvere s pevným a posuvným krídlom na dvoch koľajniciach a vstupné
dvere s bočným svetlíkom. Pevné sklá zastavujú chodca, posuvné a dverné
krídla majú vlastnú kolíziu a priechod uvoľnia až po otvorení.

Revízia interiéru stavebníka z 23. 8. 2026 dopĺňa do 1.03 ucelenú obývaciu a
jedálenskú zónu (`LIVING_DINING_FITOUT`). Na západnej stene je za valcovými
krbovými kachľami 3,37 m dlhá vstavaná bezúchytková TV zostava v teplej greige, dubovej
dyhe a tmavom kameni, so zapusteným 98-palcovým TV, plávajúcou skrinkou,
soundbarom a nepriamou 2700 K LED. Oproti stojí nízka svetlá modulová
L-sedačka s ležadlom až na plnej časti štítovej steny, na koberci s dvojicou
oválnych stolíkov. Medzi kuchynským polostrovom a sedačkou je kompaktný klasický
dubový stôl 1 400 × 800 so štyrmi zúženými nohami, štyrmi rámovými čalúnenými
stoličkami a jedným centrálnym teplým závesným svietidlom.
Pôdorysné odstupy od krbu, zadného muriva, pevného skla a priechodov sú uzamknuté
kontraktovými testami; finálny protipožiarny odstup a výrobnú skladbu TV steny
musí potvrdiť dodávateľ konkrétnych kachlí a interiéru.

Pracovňa 1.04 je v klientskej revízii z 29. 8. 2026 preskladaná ako
minimalistický pracovný kokpit (`OFFICE_FITOUT`). Greige bezúchytková skriňa
s integrovanou bielo-čiernou tlačiarňou sa presúva z priečky pri zádverí na
presne protiľahlú východnú stenu. Zachováva hĺbku 538 mm a výšku 2 550 mm,
ale skracuje sa z 1 697 na 1 461 mm, aby pred oknom EAST-01 zostal 60 mm
odstup od stavebného otvoru a 20 mm od presahu parapetu. Na pôvodnej strane
skrine je pozdĺž steny subtílny dubový stôl 1 800 × 800 mm; používateľ aj
čierne ergonomické kreslo smerujú k západnej stene a prehnutý 40-palcový
ultrawide monitor 21 : 9 má obrazovku otočenú do miestnosti. Medzi obrysom
kresla a novou skriňou ostáva 1 091 mm, po započítaní 220 mm kolízneho
polomeru chodca z každej strany 651 mm. Veľké južné okno FRONT-07 zostáva v
pôvodnom stavebnom otvore 2 000 × 1 600 mm ako jedna pevná neotváravá tabuľa
bez stredového stĺpika, krídel a kľučiek, s ultra-tenkým 35 mm pohľadovým
rámom. Bezrámová 1 700 mm široká tabuľa na fixky zostáva na voľnej severnej
stene; voľný vstupný pás 1 538 × 1 012 mm rešpektuje celý oblúk dverí.

Výrez na východnej stene zádveria 1.01 vypĺňa samostatná vstavaná zostava
`ENTRY_FITOUT`: celovýšková 950 mm skriňa na kabáty, dvojzásuvkový botník,
660 mm čalúnená lavica, dubový panel s tromi háčikmi a horná skriňa s nepriamym
2700 K svetlom. Pred zostavou ostáva komunikačný pás 1 746 × 1 697 mm; zostava
je mimo 900 mm oblúka vstupného krídla, bočného svetlíka aj dverí do chodby.
Obe riešenia sú interiérové dizajnové koncepty; ergonómiu, elektroinštaláciu,
kotvenie a výrobnú skladbu musí potvrdiť dodávateľ interiéru.

Dve niky chodby 1.02 vyznačené stavebníkom vypĺňajú samostatné celovýškové
drevené vstavané skrine (`HALLWAY_BUILT_IN_WARDROBES`). Dlhá zostava pri izbe
1.09 má presný pôdorys 601 × 2 797 mm a štyri koplanárne posuvné čelá; kratšia
zostava medzi spálňou 1.08 a kúpeľňou 1.11 má 601 × 859 mm a dve čelá. Obe sú
vysoké 2 550 mm, používajú bezúchytkové zrkadlovo radené dubové dyhy, zapustený
dymový sokel, 8 mm tieňové škáry a integrované 2 700 K svetlo. Čelá lícujú s
hranou pôvodných ník, takže pred nimi zostáva celý 1 096 / 999 mm široký
komunikačný pás; koplanárne posúvanie nevytvára ďalší dverný oblúk v chodbe.
Geometrické testy zachovávajú všetky interiérové dvere aj priechod postavy s
polomerom 220 mm.

Miestnosti 1.09 a 1.10 sú zariadené ako dve zladené, ale nezameniteľné detské
izby (`CHILDRENS_BEDROOM_FITOUTS`). Každá má matrac 1 200 × 2 100 mm na
plávajúcej úložnej posteli, trojdielnu 600 mm hlbokú vstavanú skriňu, pracovný
stôl 1 600 × 600 mm a výškovo nastaviteľnú ergonomickú stoličku s piatimi
kolieskami. Izba 1.09 kombinuje tlmenú šalviu, hlinený akcent, dubové lamely a
svetelný kruh; izba 1.10 používa hlbokú modrú, pieskový textil a horizontálnu
svetelnú stuhu. V oboch ostáva veľká voľná herná plocha, celé otvorené dverné
krídlo a minimálne 899 mm hlboký prístup k 2 000 / 2 500 mm záhradnému
preskleniu. Pôdorysné kolízie a priechod postavy s polomerom 220 mm overujú
kontraktové testy.

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
externé licencie). Predchádzajúce panoramatické pozadie
`suburban-field-01-8k.jpg` má rozlíšenie 8192 × 4096; responzívny variant
`suburban-field-01-4k.jpg` a pamäťovo úsporný IBL variant
`suburban-field-01-2k.jpg` sú odvodené z rovnakého zdroja. Dielo
[Suburban Field 01](https://polyhaven.com/a/suburban_field_01) vytvoril Jacopo
Voltolina a Poly Haven ho publikuje pod licenciou CC0.
Aktívny interaktívny pohľad používa fyzikálnu oblohu z Blenderu; pôvodné
panorámy zostávajú v archíve assetov. Pôvod skenovaných rastlín a nábytku
je uvedený v `public/assets/archviz/credits.json`.
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
- `lib/twin-viewport-contract.ts` — testovateľná Retina politika, vstupy, pohyb voľnej kamery a chodca, interiérový post-FX kontrakt,
- `lib/twin-walk-assist.ts` — čisté pomocníky chôdze: nálievka priechodu dverami a vychýlenie zablokovaného kroku,
- `lib/babylon-interior.ts` — stavba interiérového vybavenia zo záznamu miestností,
- `lib/babylon-openings.ts` — okná, parapety, posuvné a vstupné dvere,
- `lib/babylon-doors.ts` — inventár 20 interaktívnych dverí/dvierok, 3D cielenie, stavový automat a bezpečnostné obálky pohybu,
- `lib/babylon-avatar.ts` — postava prechádzky, jej kolízie, animácie a sledovacia kamera,
- `lib/babylon-scene.ts` — jediná hranica medzi milimetrami domény a metrami Babylon scény,
- `app/twin-studio.tsx` — prístupný DOM prieskumník, inspector a stav pracovného priestoru,
- `app/babylon-viewport.tsx` — client-only životný cyklus WebGL canvasu.

Úpravy základov sú v tejto fáze iba session-only náhľad. Trvalé revízie vyžadujú autorizované úložisko; browser storage nie je zdroj pravdy digitálneho dvojčaťa.
