# Kaustický transport a aktuálna hladina — 9. september 2026

Diagnostický Metal shader teraz používa všetkých 12 režimov uloženého materiálu vody. Parametre už nepočíta z vlastnej štvorvlnovej tabuľky. Aktívne osvetlenie aplikácie sa touto zmenou nemení; atlas zatiaľ nemá produkčného konzumenta. Dva samostatné Editor/Metal procesy už prešli nezávislou kontrolou transportu pri t = 0 a 0,125 s.

## Jediný zdroj optického stavu

`Plugins/BreziCausticsProbe/Tools/water_binding.py` číta autorské hodnoty z AST `scripts/unreal/optics.py` bez importu Unreal modulu. Porovnáva ich s čerstvým readbackom uloženého grafu a presnými bajtmi materiálu. Generuje samostatný `Resources/active-water-binding.json` a C++ header s hashmi. Shader dostáva presné float32 priestorové koeficienty v cykloch/cm, záporné frekvencie, fázy a podpísané vektory sklonu. Číta `View.GameTime`, rovnako ako materiál.

Historický receiver kontrakt, jeho 45 objektov, 1 076 usporiadaných trojuholníkov, 359 BVH uzlov a pravidlá numerickej identity zostávajú nezmenené. Nový checker samostatne overuje všetky ponechané záznamy a trojuholníky proti dnešnému scene/OBJ exportu. Historický hash `optics.py` sa nenahrádza v starom dôkaze; nový optický stav má samostatný explicitný pôvod.

Binding SHA256: `05186c2144e8415f6f6d68043f50d996320130bc717b2ef1b7f0088987a7049d`.
Uložený materiál SHA256: `b9d77656cf5f25cd18170d8008710260c854e7d9ccfea9fa334ed35abfc834bf`.

Natívny modul pred použitím overí bajty bindingu aj `.uasset`. Táto kontrola je určená pre aktuálny Editor diagnostický proces; nie je dôkazom doručenia v cooknutej samostatnej aplikácii. Koeficienty absorpcie/rozptylu sú overené proti zdroju a importnému reportu, bez nového natívneho getteru ich hodnôt.

## Testy a natívny protokol

`node --test tests/unreal-caustics.test.mjs` prešlo vo všetkých 10 skupinách. Nové skupiny obsahujú 12 testov pôvodu/bindingu a 7 numerických testov, bežne aj s `python -O`. Kontrolujú aj vynechanie posledných vĺn, zámenu jednotiek, osí, znamienka frekvencie a periódy. Maximálna odchýlka testovanej CPU float32 normály od nezávislej autorskej double referencie je `4,19×10⁻⁷`; nejde o bitovú zhodu Metal/LWC aritmetiky.

Aktuálny Editor modul sa zostavil s exit 0 za 8,70 s (`output/unreal/caustics-wave-module-build-02.log`). Pomocný skript `scripts/unreal/caustics-qa.mjs` spúšťa jeden proces naraz, kontroluje vstupy pred/po, natívny exit, chyby shaderov, uložený čas a 12-vlnový binding.

Prvý čistý proces PID 51176 vytvoril záznam už počas štartu pred spracovaním `ExecCmds`. Jeho pôvodné dáta a receipt zostávajú zachované v `output/unreal/caustics-wave-runtime/time-0-9be85bd2-1423-443f-9be7-b7bf571c39e5/`. Nie je zaradený do porovnania dvoch fáz. Opravený protokol čaká aspoň na číslo view family 60 a zaznamenáva rozmery toho istého pohľadu; host navyše overuje skutočný čas zo všetkých photon records.

Nezávislý CPU validátor pre nové záznamy vyžaduje explicitný hash aj súbor aktívneho bindingu. Neznámy binding, nesúlad počtu vĺn alebo pokus vynechať metadata neprejde. Historické záznamy naďalej používajú pôvodné štyri vlny a nezmenenú identity policy.

## Výsledok oboch Metal záznamov

Úplné porovnanie s hashmi je v `output/unreal/caustics-wave-runtime/comparison.json`. Oba procesy skončili s exit 0, bez zisteného ensure/fatal/shader error, s rovnakými zaznamenanými vstupmi a rovnakým slnkom. Všetky zaznamenané zdrojové/binary vstupy aj pôvodné capture súbory boli overené po oboch behoch; procesy sú ukončené.

| Veličina | t = 0 s | t = 0,125 s |
| --- | ---: | ---: |
| PID | 52198 | 52861 |
| Lúče | 117 760 | 117 760 |
| Presná zhoda object ID | 117 577 | 117 583 |
| Výslovne uvedené float32 nejednoznačnosti | 183 | 177 |
| Nevysvetlené rozdiely object ID | 0 | 0 |
| Maximálna chyba zhodného zásahu | 1,808 µm | 1,684 µm |
| Najväčšia relatívna chyba toku v atlase | 0,11581 % | 0,11472 % |
| Zásahy dna | 70 540 | 70 560 |

Nejednoznačnosti zostávajú iba podľa pôvodného pravidla pre takmer koplanárne steny/lem; neoznačujú sa za presnú identitu a nepovoľujú zlučovanie prijímačov alebo BRDF. Priestorová kontrola bilineárnych splatov aj nezávislý Snell/Fresnel/Beer výpočet prešli pôvodnými prahmi. Žiadny prah sa nezvyšoval.

Rozdiel máp medzi fázami má normalizovanú L1 približne 0,8692 v každom RGB kanáli. Dokazuje časovo sa meniace rozloženie vypočítaného toku pri rovnakých vstupoch okrem času; nie prirodzenosť pohybu v hotovom renderi. Jednotkový tok nie je kalibráciou lux na RGB radianciu.

Oba capture vznikli pri čísle view family 60 s rozmermi toho istého nezmenšeného pohľadu 3840 × 2160. Neskoršie samostatné diagnostické snímky potvrdzujú natívnu 4K scénu/RHI textúru počas benchmarku. Nejde o odčítanie interného rastra priamo na capture frame ani o výkonový test či overenie samostatnej `.app`.

## Zostávajúce napojenie

Existujúci izolovaný Renderer kandidát už obsahuje zostavený a cooknutý direct-diffuse/SingleLayerWater consumer, ale jeho aktívny provider ešte nebol spustený. Ďalším krokom je preniesť iba provider a startup z `output/unreal/caustics-provider-draft` do nového izolovaného kandidáta s aktuálnym obsahom; starú kompletnú kópiu pluginu neaplikovať cez tento 12-vlnový shader.

Potrebné je skutočné overenie inactive/zero/constant režimov vrátane downstream HDR SceneColor/SLW readbacku. Samotný Prepare readback nepotvrdí odstránenie pôvodného diffuse slnka, jedinú aplikáciu incoming Beer útlmu ani zachovanie osvetlenia mimo dna. [Epic opisuje poradie Single Layer Water po osvetlení scény](https://dev.epicgames.com/documentation/en-us/unreal-engine/single-layer-water-shading-model-in-unreal-engine); násobenie celého výsledného obrazu by tento rozsah neoddelilo.

Viditeľnosť nad vodou pre všetky lúče, konečný slnečný disk, steny/schody ako osvetlené prijímače, refracted specular/GI a plný fotorealizmus zostávajú otvorené. Predošlých šesť opaque TLAS kontrol tieto požiadavky nepokrýva. Aktuálny produkčný balík, geometria 2D/Babylon, renderer nastavenia a oheň sa nemenili.
