# Unreal — fotorealistická revízia C/B/B

Revízia z 26. septembra 2026 vzniká v samostatných profiloch
`output/unreal/realism-20260926-r2` (svetlo a povrchy) a
`output/unreal/realism-20260926-r3` (drez, batéria a čalúnenie),
na ktoré nadväzuje `output/unreal/realism-20260926-r4`
(spotrebiče, lampa a rohy výrezu pracovnej dosky) a R5
(tvary čalúnenia a smer drevenej kresby jedálenského nábytku).
Vychádza z overeného balíka Shipping R4;
historický balík, pôvodné materiálové assety aj geometria zostávajú zachované.
Hlavný návrh je C/B/B, uličný a pravý kolmý odstup 3 000 mm.

## Čo sa mení

- **Fotoreal** je samostatná voľba kvality: 100 % vstupné rozlíšenie,
  200 % TSR história, podrobnejšie nepriame osvetlenie a odrazy Lumen.
  Kosená tráva a detailný porast znovu prispievajú tieňmi a ray tracingom.
  Ostatné profily si zachovávajú svoje rozpočty; pri prepnutí sa obnovia
  pôvodné príznaky vegetácie.
- **Dub** používa spoločné fyzicky škálované súradnice pre farebnú,
  normálovú a drsnostnú mapu. Kresba je pokojnejšia a jednotlivé panely
  majú odlišný výrez. Odtieň je výtvarný návrh, nie meranie konkrétnej dyhy.
- **Omietka** má čistý minerálny základ s jemnou mikroštruktúrou.
  Odstránená je široká zvislá kresba pochádzajúca z pôvodnej textúry.
- **Farebné priestory** sa opravujú iba pri presne doložených pôvodných
  sRGB konštantách. Čierne sklo, lakované kovy a keramika už nepoužívajú
  sRGB hodnoty ako lineárnu odrazivosť.
  Napríklad `#0c0e10` má lineárne RGB približne
  `[0.00368, 0.00439, 0.00518]`, nie `[0.04706, 0.05490, 0.06275]`.
  Už správne prevedené kuchynské farby sa druhýkrát nedekódujú.
- **Strop** prestáva byť umelým plošným zdrojom svetla. Skutočné
  svietidlá zostávajú; osvetlenie stropu vzniká dopadom a odrazom svetla.
- **Obloha** dostáva priestorové oblaky napojené na existujúce slnko,
  atmosféru a SkyLight. Jemný vzdialený opar začína 60 m od kamery.
  Oblačnosť je výtvarný meteorologický scenár, nie rekonštrukcia počasia.
- **Drez a batéria** dostávajú zaoblené rohy, súvislú vaňu, jemné sitko,
  dutý hladký výtok a pripojenú páčku. Štyri nové vizuálne meshes majú spolu
  33 248 trojuholníkov. Pôvodných osem komponentov zostáva kolíznym podkladom;
  náhrada sa zmestí do pôvodného spoločného obrysu. Nejde o výrobné CAD dáta.
- **Čalúnenie** používa správne lineárne farby v aktívnom materiálovom
  atribúte; zachováva tkaninu, normálovú mapu, drsnosť a existujúci cloth model.
- **Detaily miestností** dopĺňajú zaoblené rámy, šošovky a ovládacie prvky
  práčky a sušičky, fyzickú podporu tienidla detskej lampy a štyri rohy dosky
  okolo zaobleného drezu. Osemnásť vizuálnych dielov má 36 176 trojuholníkov.
  Šesť pohyblivých dielov sleduje pôvodné dvierka. Nejde o značkové výrobné
  modely; sklá spotrebičov naďalej používajú pôvodný nepriehľadný materiál.
- **Nábytok R5** mení tvar dvadsiatich už existujúcich čalúnených dielov
  na mierne vyklenuté plochy s čistejšími rohmi a jemným lemom. Porovnanie
  vychádza zo skutočných PH vizuálnych meshes, ktoré už mali zaoblenie.
  Náhrady majú 76 800 namiesto 264 960 trojuholníkov; menší počet sám osebe
  nedokazuje lepší výkon. Jedenásť dielov stola a stoličiek dostáva pozdĺžny
  smer dubovej kresby cez dva materiálové klony. Fyzická mierka 183 cm,
  farebné a drsnostné hodnoty aj vzorkovanie textúr sa zachovávajú.

## Reprodukcia

Vždy použiť nový prázdny výstup. Natívne fázy spúšťať postupne.

```sh
export BREZI_MODEL_OUTPUT=output/unreal/realism-next
export BREZI_ARCHVIZ_GAME=1
export BREZI_DOUBLE_GLASS=1
export BREZI_GAME_CONFIGURATION=Shipping
export BREZI_DEFAULT_RENDER_PROFILE=cinematic
node scripts/unreal/model-refresh.mjs prepare
node scripts/unreal/model-refresh.mjs inherit output/unreal/performance-shipping-20260924-r4
node scripts/unreal/model-refresh.mjs editor-build
node scripts/unreal/model-refresh.mjs game-build
node scripts/unreal/model-refresh.mjs realism
node scripts/unreal/model-refresh.mjs package
```

Nasledujúce revízie vždy pripravujú nový výstup, preberajú obsah
predchádzajúcej revízie a používajú overený runtime z R2. Príklad R5:

```sh
export BREZI_MODEL_OUTPUT=output/unreal/realism-furniture-next
node scripts/unreal/model-refresh.mjs prepare
node scripts/unreal/model-refresh.mjs inherit output/unreal/realism-20260926-r4
node scripts/unreal/model-refresh.mjs reuse-build output/unreal/realism-20260926-r2
node scripts/unreal/model-refresh.mjs realism-furniture output/unreal/realism-upholstery-study-20260926-r3
node scripts/unreal/model-refresh.mjs package
```

R3 používa fázu `realism-fixtures` a geometriu
`output/unreal/realism-fixtures-20260926-r2`; R4 používa
`realism-room-details` a `output/unreal/realism-room-details-20260926-r3`.
Manifesty overujú zdrojové hashe. Zmena už pripnutého skriptu vyžaduje
nový výstup a nové overenie; historické dôkazy sa neprepisujú.

Import povoľuje zmenu uloženej mapy a nové assety výhradne pod
`/Game/Brezi/Realism`. Overuje pôvodné geometrické transformácie,
kolízie, inštancie, nedotknuté pôvodné assety a explicitný zoznam
materiálových väzieb. Po uložení mapu opätovne načíta. Tento krok
nepotvrdzuje kvalitu obrazu ani výkon.

## Natívne overenie

Východiskové meranie aktuálneho Shipping R4: tri statické Metal zábery,
3 840 × 2 160, profil Native, 100 % vstupné rozlíšenie, 100 % TSR história,
240 zahrievacích a 300 meraných snímok. Všetkých 300 snímok každého behu
malo aplikáciu aj herné okno aktívne.

| Záber | Pôvodný priemer | Pôvodná P95 |
| --- | ---: | ---: |
| Ulica | 51,50 ms / 19,4 FPS | 52,67 ms |
| Terasa | 56,71 ms / 17,6 FPS | 57,60 ms |
| Kuchyňa | 108,21 ms / 9,2 FPS | 109,41 ms |

R2 prešlo ďalšími šiestimi párovými 4K behmi a ôsmimi pohľadmi pri
1 920 × 1 080. Každý beh mal 240 zahrievacích a 300 meraných snímok
v aktívnom hernom okne. Režim Fotoreal má vyšší renderovací rozpočet;
samotná jeho implementácia nie je prísľubom plynulého 4K.

| Záber R2 | 4K Native | 4K Fotoreal | 1080p Fotoreal |
| --- | ---: | ---: | ---: |
| Ulica | 61,68 ms | 87,55 ms | 31,85 ms |
| Terasa | 66,03 ms | 94,40 ms | 34,63 ms |
| Kuchyňa | 131,93 ms | 172,21 ms | 51,94 ms |
| Kuchyňa v noci | — | — | 51,61 ms |
| Obývačka | — | — | 46,04 ms |
| Bazén | — | — | 34,06 ms |
| Kúpeľňa | — | — | 45,00 ms |
| Detská izba | — | — | 38,90 ms |

Natívne snímky bez retuše a párové merania sú v
`output/unreal/realism-validation-20260926-r1/porovnanie.html`.
Rozhranie má posuvník pred/po a umožňuje porovnávať aj rovnaký profil Native.

Natívny Editor aj Shipping Game build prešli. Import po uložení a načítaní
overil 635 materiálových väzieb, 12 nových materiálov a jeden materiál
oblakov. Pôvodných 2 735 aktérov zostalo zachovaných; pribudli dva aktéry
atmosféry. Cook, samostatný Shipping balík a podpis prešli.
Prvé tri 4K porovnania potvrdili odstránenie pásov na fasáde, prirodzenejšiu
oblohu, pokojnejší dub a tmavé odrazivé sklo rúry. Ďalších osem záberov
pokrýva širšiu obývačku, bazén, kúpeľňu, detskú izbu a nočnú kuchyňu.
Terasové čalúnenie dostalo korekciu až v R3.

R3 natívny import po opätovnom načítaní overil 17 väzieb čalúnenia,
dva nové materiály a štyri nové meshes. Všetky pôvodné assety okrem mapy
sú nezmenené; 2 737 aktérov sa rozšírilo na 2 742 vrátane importného koreňa.
Maximálna odchýlka kontrolovaných hraníc importu bola 0,00062 mm.
Build, cook a podpis R3 prešli. Dva ďalšie 4K zábery potvrdili novú
geometriu a čalúnenie; kuchyňa mala 175,02 ms a terasa 94,53 ms na snímku.
Vizuálna kontrola odkryla malé rohové medzery medzi pôvodným štvorcovým
výrezom dosky a zaobleným drezom; R4 ich uzatvára štyrmi dielmi dosky.

Dve 45-sekundové prechádzky v R3 pri 1 920 × 1 080 prešli štyrmi okruhmi
po rovnakej trase bez teleportov. Vyvážené: 2 628 snímok, 17,13 ms / 58,4 FPS,
P95 22,13 ms. Fotoreal: 953 snímok, 47,22 ms / 21,2 FPS, P95 57,25 ms.
Všetky merané snímky mali aktívnu aplikáciu aj herné okno. Toto je dôkaz
výkonu a pohybu, nie video dokazujúce neprítomnosť časového mihotania.
Priamo v natívnom rozhraní bolo overené prepnutie Fotoreal → Natívny detail
→ Vyvážené → Fotoreal. Výber bol po návrate do menu zachovaný.

R4 import prešiel uložením a opätovným načítaním: 2 742 pôvodných aktérov
zostalo zachovaných, pribudlo 19 vrátane importného koreňa. Vzniklo 37 nových
assetov; z pôvodných sa zmenila iba mapa. Kolízie, transformácie a pôvodné
materiálové väzby zostali zachované. Šesť pripojených dielov prešlo natívnou
kontrolou polohy pri zatvorení, polootvorení aj otvorení; kontrola nakoniec
obnovila presný pôvodný stav.

Prvý pokus R4 správne zastavila kontrola viditeľnosti: UE 5.8 považuje
`HiddenInGame` komponent za neviditeľný aj pre existujúci systém dvierok.
Neúspešný pokus sa obnovil zo samostatného checkpointu a jeho dôkazy zostali
uložené. Opravené pohyblivé komponenty preto zachovávajú viditeľnosť pre
interakciu a vypínajú iba pôvodný hlavný/hĺbkový render a príspevok k svetlu.
Nové diely majú vlastné vykresľovanie. Opravený import prešiel bez chýb;
35 Node a 17 Python kontrol dotknutých importných fáz prešlo.

R4 Shipping cook a podpis prešli. Šesť ďalších priamych Metal záberov
prešlo aj nezávislou vizuálnou kontrolou. Všetky merané snímky mali aktívnu
aplikáciu aj herné okno. Výsledky profilu Fotoreal:

| Záber R4 | 1080p | 4K |
| --- | ---: | ---: |
| Kuchyňa | 59,46 ms / 16,8 FPS | 180,55 ms / 5,5 FPS |
| Kúpeľňa | 45,41 ms / 22,0 FPS | 147,60 ms / 6,8 FPS |
| Detská izba | 39,60 ms / 25,3 FPS | 123,09 ms / 8,1 FPS |

R4 zopakovalo 45-sekundovú prechádzku v profile Vyvážené: 2 515 snímok,
17,90 ms / 55,9 FPS, P95 23,06 ms. Priamo v balíku bolo cez bežné ovládanie
overené otvorenie sušičky, pohyb nového rámu a následný návrat do zatvorenej
polohy. Natívny import samostatne overuje pohyb všetkých šiestich dielov
práčky aj sušičky; ručná UI skúška pokrýva sušičku.

Po prijatí R4 bol výber pre `npm run unreal:open` nastavený na `realism-20260926-r4`.
Úplný záznam má 28 natívnych behov vrátane východiskových meraní a starších
revízií; sedem z nich bežalo na finálnom R4. Záznam a hashe sú v
`output/unreal/realism-validation-20260926-r1/realism-r4-review.json`.
Pôvodný výber aj historický balík zostali zachované.

R5 natívny import a Shipping balík prešli; 2 761 pôvodných aktérov sa
rozšírilo na 2 782, pribudlo 46 assetov a z pôvodných sa zmenila iba mapa.
Všetkých dvadsať čalúnených dielov zachovalo aktuálne PH materiály.
Na stole a priečkach sa overilo jedenásť presných materiálových väzieb,
zvyšných 99 väzieb pôvodného dubového materiálu zostalo zachovaných.
Dotknuté testy: 42 Node a 41 Python, všetky úspešné.

Priame párové zábery obývačky z R4 a R5 majú rovnaký profil Fotoreal,
kameru a rozlíšenie. Nezávislá kontrola prijala pozdĺžnu kresbu dreva,
čistejšie rohy čalúnenia a jemné lemy. Zmena expozície medzi pármi bola
len 0,0108 EV pri 1080p a 0,0061 EV pri 4K. Priemer sa zmenil z 47,99 na
53,91 ms pri 1080p a zo 150,81 na 155,48 ms pri 4K; zlepšenie výkonu
sa preto netvrdí. Prechádzka R5 v profile Vyvážené: 2 442 snímok za 45 s,
18,43 ms / 54,3 FPS, P95 23,83 ms, aktívna aplikácia aj okno.

R5 nahradilo R4 v aktuálnom výbere pre `npm run unreal:open`.
`realism-r5-review.json` v validačnom výstupe obsahuje 33 behov vrátane
predchádzajúcich revízií; tri z nich sú z R5. História výberov zostáva
vnorená v `model-refresh-current.json`.

R6 doplnilo dutú komoru kachlí, dve polená, uhlíky a animované plamene
z atlasu 6 × 6. Päť vizuálnych meshes má 2 010 trojuholníkov; pôvodné
kolízie, rozmery, sklo aj svetlá sa zachovali. Import prešiel opätovným
načítaním, 48 Node a 59 Python kontrolami, cookom a podpisom. Pribudlo
16 assetov a šesť aktérov vrátane importného koreňa; pôvodných 2 903
assetov okrem mapy zostalo nezmenených.

**R6 nebolo vizuálne prijaté ani vybrané na bežné spúšťanie.** Štyri
natívne denné/nočné zábery ukázali, že plamene sú takmer neviditeľné.
Kontrola materiálových väzieb, atlasu a priechodnosti pohľadu vylúčila
zjavné zakrytie stredu ohniska. Emisia 3 bola príliš slabá pri nameranej
predexpozícii približne 0,00134 cez deň a 0,01068 v noci. Skúšobný Blender
render používal inú expozíciu a nepotvrdzoval natívny jas. Dôkazy zostávajú
v `realism-r6-rejected-review.json`; R7 pripravuje samostatnú kalibráciu
materiálu bez zmeny geometrie alebo osvetlenia miestnosti.

## Ďalší vizuálny krok

Pretrváva jednoduchá geometria závesov a časti rekvizít, výrazný kontrast
dreva, kužeľové náhrady plameňov v aktuálnom R5 a štylizované stromy.
Náhrada ohniska zatiaľ nie je vydaná.
Profesionálny stromový balík European Black Alder bol nájdený na oficiálnom
Fab, ale jeho získanie čaká na prihlásenie používateľa do Epic Launcher.
Balík zatiaľ nebol získaný, importovaný ani otestovaný. Procedurálna stromová
štúdia nepriniesla dostatočné vizuálne zlepšenie a zostala mimo aplikácie.

Celkový cieľ nerozoznateľnosti od fotografie sa týmto záznamom neoznačuje
za dosiahnutý.

Technické podklady: [Epic — volumetrické oblaky](https://dev.epicgames.com/documentation/unreal-engine/volumetric-cloud-component-in-unreal-engine),
[SkyLight a oblačnosť](https://dev.epicgames.com/documentation/unreal-engine/sky-lights-in-unreal-engine),
[Lumen](https://dev.epicgames.com/documentation/unreal-engine/lumen-global-illumination-and-reflections-in-unreal-engine).
