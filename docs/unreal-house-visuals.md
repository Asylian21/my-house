# Dom: exteriér a interiér

Aktuálna priorita používateľa je dom, predovšetkým exteriér, a tiež interiér. Cieľom bežného zobrazenia je Retina a aspoň 30 FPS. Pevný 4K výstup už nie je podmienkou. Ďalšie vizuálne ladenie bazéna a ohňa je odložené.

Aktuálna dodaná verzia má report `6d9ee5fe…`; zjednocuje náter strešných drážok a zjemňuje kresbu kuchynských a TV skriniek. Zachováva širší uličný pohľad a predchádzajúce úpravy jedálne a závesov. Merania starších verzií `91481d18…` a `e80edced…` zostávajú historickým záznamom.

## Prvá úprava domu

- **26 záclon:** pôvodné ploché kvádre nahrádzajú statické záhyby látky. Zachovávajú názvy, umiestnenie, šírku a výšku otvorov; obálka záhybov má hĺbku 40,7 mm a látka hrúbku 0,7 mm. Ide o navrhnutý detail, nie zameranú látku alebo fyzikálnu simuláciu.
- **Televízor v obývačke:** vypnutá obrazovka používa existujúce neemitujúce čierne sklo. Deväť kancelárskych monitorov zostáva nezmenených.

Spoločný export obsahuje 1 895 objektov, 2 238 inštancií a 402 947 trojuholníkov. Prírastok 9 400 trojuholníkov je približne 2,4 %. Kontrola glTF a spätné načítanie v Blenderi prešli. Porovnanie dekódovanej geometrie potvrdilo, že všetkých 1 869 objektov mimo záclon zachovalo geometriu, UV a normály. Katalóg materiálov zostal totožný; televízor zmenil iba priradenie materiálu a exportnú skupinu.

## Stav overenia prvého balíka e80

Spoločné zdrojové testy a export sú overené. Unreal importoval 26 modelov a priradil televízoru existujúce čierne sklo. Samostatný nový proces potom načítal uloženú scénu a potvrdil rovnakú geometriu, UV, materiály a povolené zmeny medzi 1 968 aktérmi. Maximálna odchýlka pozícií a UV pri porovnaní natívnych renderovacích dát s odvodeným glTF bola nulová; normály sa líšili najviac o 0,0000154 v jednej zložke.

Nová samostatná macOS aplikácia je zostavená a podpísaná. Natívne zábery potvrdili viditeľné záhyby v interiéri aj cez okná a odstránenie modrého svietenia vypnutého televízora. Ulica a terasa nevykazujú zjavne posunutý alebo chýbajúci prvok domu. Ide o prijatie týchto konkrétnych úprav; celkový fotorealizmus ešte nie je dosiahnutý. Okná majú miestami výrazné sivé pásy a drevo pôsobí príliš pravidelne a kontrastne.

Štyri samostatné minútové testy pohybu kamery prešli pri výstupe **3 200 × 1 800**, `r.ScreenPercentage=50` a `r.TSR.History.ScreenPercentage=100`:

| Pohľad | Priemerné FPS | 99. percentil intervalu | Najdlhší interval |
| --- | ---: | ---: | ---: |
| Ulica, deň | 73,25 | 15,36 ms | 17,84 ms |
| Terasa, deň | 65,00 | 17,56 ms | 20,23 ms |
| Interiér, deň | 63,98 | 17,38 ms | 18,97 ms |
| Interiér, noc | 67,60 | 16,14 ms | 17,38 ms |

Všetkých 16 191 meraných intervalov bolo v popredí a pod 33,333 ms. Meria sa skutočný čas pri pohybe orbitovej kamery ±8°; nejde o meranie všetkých trás chôdze alebo udalostí fyzického displeja. Rozmery výstupu potvrdzuje vykresľovací cieľ aj dekódovaný PNG. Rozmery interných TSR bufferov sa samostatne nepozorovali.

Bežné spustenie bez parametrov veľkosti alebo kvality obnovilo Retina výstup 3 200 × 1 800 a profil **Plynulosť**, potvrdený natívnym panelom Ovládanie. Aplikácia zostala otvorená na širšom pohľade z ulice.

Pohľad z ulice má pripravený návrh širšej kompozície. Zdrojový preset orezáva oba konce fasády. Interaktívne oddialenie troma stlačeniami Page Down už v aplikácii ukázalo celé priečelie; tento obraz bol posúdený cez CUA. Preset zatiaľ zostal nezmenený. Samostatný vypočítaný návrh inej polohy kamery so zvýraznením západného boku ešte nemá natívne obrazové porovnanie.

Podklady: `output/unreal/house-visual-study/geometry-delta.json`, `derived/report.json`, `native-context.json`, `package-context.json`, `runtime-review.json`, `ordinary-open-review.json` a tri vizuálne recenzie. Prijatie tejto iterácie zaznamenáva `delivery-review.json`.

Balík aplikácie má SHA-256 reportu `e80edcede5a428afa153787b6b45f03f8db3ac623fca30674574c9b2011eb599`. Spúšťač vyžaduje explicitný report a jeho hash; starý predvolený `output/unreal/package-report.json` zostáva historický. Presnú aktuálnu cestu uchováva `output/unreal/quality-ui-current.json`.

## Širší pohľad a drevo jedálne — 10. september 2026

Uličný preset v spoločnom `scripts/archviz/config.json` má oči vo výške 1,8 m a polohu `[-10.01, -21.90, 1.8]` m, v Unreal súradniciach `[-1001, 2190, 180]` cm. Celá strecha, garáž, vstup aj obidva konce domu sa zmestia do obrazu bez ručného zoomu. Cieľ kamery, objektív, ostatné presety a slnko zostali rovnaké. Nový export zachoval totožné OBJ, MTL, glTF a kolíznu geometriu; mení sa kamera a časové údaje exportu.

Doska jedálenského stola a štyri horné priečky stoličiek používajú jeden upravený materiál s pokojnejšou farbou a kontrastom kresby. Fotografická textúra dubu si zachováva mierku 1,83 m, drsnosť, normálovú mapu a spôsob mapovania. Ide o autorskú úpravu vzhľadu. Zachované sú tvarované závesy a vypnutá čierna TV z prvého balíka.

Diagnostika skla bola ukončená obnovením pôvodného materiálu. Nový natívny proces potvrdil zhodu všetkých 20 kontrolovaných presklení aj päť nových priradení dreva. Pomocný diagnostický materiál je uchovaný mimo produkčného obsahu. Výpočet odrazených lúčov v zdrojovej geometrii ukazuje pásy cesty a terénu a následné minutie konečného okraja terénu; nepotvrdzuje konkrétne GPU zásahy ani ich farbu. Zjednodušené okolie, horizont a výrazná kresba väčších skriniek zostávajú obmedzením realizmu.

Nové zostavy Editor aj Game, balenie, kontrola obsahu a podpisu prešli. Štyri samostatné 60-sekundové testy pohybu **nového balíka** namerali skutočný výstup **3 200 × 1 800**, `r.ScreenPercentage=50` a `r.TSR.History.ScreenPercentage=100`:

| Pohľad | Priemerné FPS | 99. percentil intervalu | Najdlhší interval |
| --- | ---: | ---: | ---: |
| Ulica, deň | 70,75 | 17,12 ms | 21,22 ms |
| Terasa, deň | 66,19 | 16,75 ms | 18,83 ms |
| Interiér, deň | 63,08 | 17,58 ms | 18,95 ms |
| Interiér, noc | 65,33 | 16,89 ms | 17,84 ms |

Všetkých **15 923 intervalov** bolo v popredí a pod 33,333 ms. Zábery po meraní boli vizuálne posúdené; ide o štyri snímky, nie kontrolu videa alebo každej snímky pohybu. Bežné spustenie bez parametrov rozlíšenia či kvality obnovilo Retina a natívny panel potvrdil profil **Plynulosť**. Aplikácia zostala otvorená na celom uličnom priečelí. Celkový fotorealizmus ešte nie je dosiahnutý.

[Merania a ich rozsah](/Users/davidzita/www/dom/output/unreal/house-surface-study/runtime-review.md) · [Natívne vizuálne overenie](/Users/davidzita/www/dom/output/unreal/house-surface-study/packaged-visual-review.json) · [Bežné otvorenie](/Users/davidzita/www/dom/output/unreal/house-surface-study/ordinary-open-review.json) · [Aktuálny kontext a cesta aplikácie](/Users/davidzita/www/dom/output/unreal/house-surface-study/package-context.json).

SHA-256 aktuálneho reportu balíka: `91481d18d8b23924bd7a7707f73a4def9189425f4f96dbb3edb062f61d762dc0`. Spúšťač naďalej vyžaduje explicitný report a hash.


## Náter strechy a drevo skriniek — 10. september 2026

Sto stojatých strešných drážok používa rovnaký existujúci náter ako plechové roviny. Zmena zachovala čitateľné odlesky; vizuálny rozdiel je jemný. Sedem dielov kuchynských a TV skriniek používa dva spoločné upravené dubové materiály so slabším kontrastom kresby. Pôvodných 19 uzlov materiálu, mierka 1,83 m, normálová mapa a drsnosť zostali zachované. Je to autorská úprava povrchu, nie meranie konkrétneho výrobku.

Nový proces načítal uložený projekt a potvrdil presne 107 zmien priradenia materiálu medzi 178 kontrolovanými objektmi. Geometria, kamery a ostatný obsah sa nezmenili. Porovnanie prostredia pokrýva dostupné načítané hodnoty; jeden nepodporovaný getter atmosféry je výslovne uvedený v dôkaze.

Samostatná skúška rozšírenia plochého okolia na 1 km × 1 km zmenšila čierny horizont, ale vytvorila príliš svetlé pozadie a neodstránila pásy v oknách. Zostala mimo dodaného balíka. Bazén ani oheň sa vizuálne neladili.

Editor, Game, kontrola zabaleného obsahu a podpisu prešli. Štyri nové minútové testy bežného pohybu orbitovej kamery namerali Retina **3 200 × 1 800**, `r.ScreenPercentage=50` a `r.TSR.History.ScreenPercentage=100`:

| Pohľad | Priemerné FPS | 99. percentil intervalu | Najdlhší interval |
| --- | ---: | ---: | ---: |
| Ulica, deň | 67,92 | 17,68 ms | 19,42 ms |
| Terasa, deň | 66,33 | 17,84 ms | 24,40 ms |
| Interiér, deň | 63,80 | 17,59 ms | 19,13 ms |
| Interiér, noc | 65,26 | 16,72 ms | 17,82 ms |

Všetkých **15 800 intervalov** bolo v popredí a pod 33,333 ms. Výsledok platí pre tieto štyri 60-sekundové pohyby, nie pre všetky trasy chôdze alebo fyzické prezentačné udalosti displeja. Štyri následné natívne snímky boli posúdené; nešlo o kontrolu videa. Bežné otvorenie obnovilo Retina aj profil **Plynulosť** a aplikácia zostala otvorená na celom priečelí. Fotorealizmus ako celok ešte nie je dosiahnutý; zostávajú zjednodušené okolie, pásy v skle, opakovanie dreva a miestami hrany tenkých strešných prvkov.

[Merania](/Users/davidzita/www/dom/output/unreal/house-envelope-study/runtime-review.md) · [Vizuálne overenie](/Users/davidzita/www/dom/output/unreal/house-envelope-study/packaged-visual-review.json) · [Bežné otvorenie](/Users/davidzita/www/dom/output/unreal/house-envelope-study/ordinary-open-review.json) · [Dodanie a presná cesta aplikácie](/Users/davidzita/www/dom/output/unreal/house-envelope-study/delivery-review.json).

SHA-256 aktuálneho reportu: `6d9ee5fec9e0620f477b09a3368c3ee8763f66e8afdbf135ffe858bd8ce278d7`. Spúšťač používa explicitný report a hash; historický predvolený report sa nemení.
