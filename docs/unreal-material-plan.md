# Březí 6012/26: materiálový plán pre Unreal

Lokálny audit 2026-09-08. Tento súbor je plán nasledujúcej shader iterácie; nepotvrdzuje dokončený Unreal materiál, fotorealizmus ani 4K výkon. Materiálové názvy sú overené v aktuálnom `output/unreal/geometry/scene.json` s layoutom `C-2026-09-07`. Mapy nižšie fyzicky existujú; SHA-256 bol vypočítaný z aktuálnych bajtov. Pri všetkých uvedených Poly Haven mapách sa navyše overila zhoda MD5 s `scripts/archviz/assets.lock.json`.

Všetky textové cesty sú relatívne ku koreňu repozitára. Pôvodný lock je prenosný; `output/archviz/assets/manifest.json` obsahuje historické `/tmp/dom-archviz-assets/...` cesty a nie je vhodný ako importný manifest pre tento Mac. Pri natívnom balení sa musia zvolené mapy importovať do Unreal Content a zahrnúť do cooku; aplikácia sa nesmie spoliehať na pracovný `output/` adresár.

## Výber materiálov a mierka

| Zdrojové materiálové názvy | Konkrétny vstup / pravidlo | Mierka a existujúca receptúra | Stav / hranica použitia |
| --- | --- | --- | --- |
| `real-wall`, `real-soffit`, `real-interior-wall`, `real-interior-plaster`, `real-interior-ceiling` | `output/archviz/assets/white_plaster_02/white_plaster_02_{diff,rough,nor_gl,disp}_2k.jpg` | Jeden opakovací celok **1 m**; Cycles world-position box mapping, blend 0.18. Základná farba je 85 % lineárneho `(0.82,0.80,0.75)` + 15 % skenu. Výška bump 1 mm, strength 0.45 (`materials.py:121–128,146–208`). | Poly Haven CC0, Rob Tuytel. Ide o vybraný sken omietky; nie odmeraný materiál konkrétnej fasády. `nor_gl` existuje, Cycles v tomto recepte používa displacement ako bump. |
| `real-deck`, `real-timber`, `real-timber-dark`, `real-larch-*`, `TERR-*` | `output/archviz/assets/hinoki_planks/hinoki_planks_{diff,rough,nor_gl,disp}_2k.jpg` | Celok **1.89 m**. Pri `real-larch-*:<width>x<height>` sú UV škály `width/1.89`, `height/1.89`, otočenie 90°. Ostatné povrchy world-position box mapping; Cycles bump 7 mm / strength 0.45 (`materials.py:133–175,199–208`). | Poly Haven CC0, Charlotte Baglioni. Hinoki je existujúca umelecká náhrada, nie dôkaz modřínovej dreviny alebo zmeranej patiny. Nepridávať vymyslenú históriu zvetrania. |
| Skutočné dosky `TERR-*` v aktuálnej geometrii | Rovnaká drevená sada; zachovať individuálne UV / orientáciu každej dosky | Geometria už obsahuje dosky **145 mm**, medzery **8 mm**, hrúbku **28 mm**, povrch **+20 mm** (`babylon-scene.ts:5808–5830`). | Textúra nesmie pridávať ďalšie veľké škáry, ktoré predstierajú inú šírku dosiek. 1.89 m je perioda skenu, nie rozmer jednej dosky. |
| `real-road`, `real-paving`, `real-paving-entry`, `real-concrete` | `output/archviz/assets/concrete_pavement/concrete_pavement_{diff,rough,nor_gl,disp}_2k.jpg` | Celok **1.8 m**, existujúce box mapping / bump 7 mm / strength 0.45. | Poly Haven CC0, Charlotte Baglioni. Aktívny web `real-road` je **dlažba**: DynamicTexture `street-grey-block-paver-albedo`. `materials.py:141–143` ju úmyselne zachováva ako dlažbu. |
| `archviz-asphalt` (pripravená receptúra, v aktuálnom scalar GLB nemá priradený objekt) | `output/archviz/assets/asphalt_02/asphalt_02_{diff,rough,nor_gl,disp}_2k.jpg` | Celok **3 m**, rovnaký box mapping / existujúci bump 7 mm / strength 0.45 (`materials.py:144–145,146–208`). | Poly Haven CC0; autor je v tabuľke proveniencie. Zdroj asfaltu je pripravený. Priradenie na cestnú plochu musí zodpovedať konkrétnej fotoreferencii; aktuálnu dlažbu nemožno v tichosti označiť za asfalt. |
| `Living warm sofa \| real-interior-upholstery` | `public/assets/textures/living-boucle-ecru-albedo.jpg` + `public/assets/textures/boucle-taupe-normal.jpg` | **Zachovať pôvodné UV**; scalar roughness **0.99**, metal 0, albedo multiplier `(0.69,0.72,0.72)`, normal strength 0.16, sheen 0.15 / sheen roughness 1 (`babylon-living-palette.ts:7–8,48–65,86–94`). | Existujúca lokálna procedurálna tkanina a odvodená farebná varianta; nejde o sken látky. Recept nemá zmeraný fyzický rozmer tkania. |
| `Living warm fabric \| real-interior-upholstery`, `real-interior-upholstery` | Teplá varianta: `living-boucle-ecru-albedo.jpg`; pôvodná: `boucle-taupe-albedo.jpg`; spoločná `boucle-taupe-normal.jpg` v `public/assets/textures/` | Teplá varianta roughness **0.92**, albedo multiplier `(1,0.9,0.74)`; pôvodná roughness 0.9 / bump 0.48. UV sa kopírujú z originálu. | Rozlíšiť pohovku od ostatného čalúnenia. `web/export_web.py:125–126` má len **fallback** normal box periodu 0.35 m pre textílie bez normal mapy; nie je to zmeraný rozmer existujúcej pohovky. |
| `Living warm rug \| real-interior-rug` | `public/assets/textures/living-wool-sand-albedo.jpg` + `rug-wool-taupe-normal.jpg` | Zachovať UV, roughness **0.98**, tint `(1,0.9,0.74)`; pôvodný `real-interior-rug` má roughness 0.97 / bump 0.42. | Lokálna procedurálna textília; samostatná skenovaná roughness mapa neexistuje. |
| `Living warm cabinet \| real-interior-living-cabinet`, `Living warm oak \| real-interior-kitchen-front` | `public/assets/textures/living-natural-oak-albedo.jpg` + existujúca `oak-veneer-normal.jpg` | UV prevzaté z originálu; roughness **0.74 / 0.68**; clearcoat vypnutý (`babylon-living-palette.ts:9–11,62–72`). | Lokálne generované drevo, farebná úprava zachováva pôvodnú kresbu. Mapa nepreukazuje konkrétnu výrobnú dyhu. |
| `Living warm stone \| real-interior-media-stone`, `Living warm stone \| real-interior-worktop` | `public/assets/textures/living-warm-stone-albedo.jpg` + existujúca `stone-dark-normal.jpg` | UV prevzaté z originálu, roughness **0.72**, tint `(1,0.96,0.87)`. | Lokálna procedurálna textúra / farebná varianta. Párovanie normal mapy zachováva jej existujúcu kresbu; nesmie sa tvrdiť odmeraný vápenec. |
| `real-glass-frame`, `real-fence-metal`, `real-roof-edge` | Natívny scalar materiál + voliteľne `public/assets/textures/metal-anthracite-normal.jpg` | Cycles recept: sRGB **(56,62,66)** (`#383E42`) prevedené do linear; roughness **0.34**, metallic **0.08**, coat **0.25**, procedurálny bump **0.08 mm**. Web explicitný normal fallback: box perioda **0.15 m**, strength **0.08** (`materials.py:223–245`, `web/export_web.py:121–122`). | Obrazovková aproximácia RAL 7016, nie meraná vzorka. Normal je lokálne generovaný. Farebnú mapu `metal-anthracite-albedo.jpg` netreba násobiť do už zvolenej RAL farby. |
| `real-glass-frame-wood` | **Samostatné rozhodnutie o finálnom povrchu** | Aktívny Babylon zdroj má hnedé drevo `#77522c`, roughness 0.5. Starší `materials.py:223–225` tento názov zahŕňa do RAL override. | Konflikt medzi existujúcimi vizuálnymi receptami; nepreberať RAL override slepo na drevenú povrchovú úpravu. Zdrojová geometria ani názov sa kvôli shaderu nemenia. |
| `real-interior-fireplace` | Matná čierna scalar úprava podľa aktuálneho zdroja | Aktuálny capture: farba zodpovedá `#1D2022`, roughness **0.48**, metallic **0.2**. | Nezamieňať so sklenenými dvierkami alebo žeravými uhlíkmi. Nemáme samostatný zmeraný sken dymoviny. |
| `real-glass`, `real-bathroom-shower-glass`, `real-interior-fireplace-glass` | Natívny transmission shader; žiadny obrázok alpha sa v zdroji nenachádza | Cycles recept IOR **1.52**, transmission 1, roughness **0.025** (`materials.py:259–268`). Aktívny Babylon má vlastné rozdielne tint/alpha hodnoty. | Scalar alpha z GLB nie je náhrada optickej hrúbky a lomu. Zasklenie, sprcha a krbové dvierka vyžadujú oddelené inštancie; čierne nepriehľadné spotrebičové sklo nie je v tomto zozname. |
| `real-pool-water` | Natívny water shader; pozri hranicu nižšie | Cycles IOR **1.333**, roughness **0.035**, bump 3 mm / strength 0.3. Zdrojová hladina **−12 mm**, plocha **6000 × 2700 mm**. | **Dynamické kaustiky, refrakcia, absorbujúci objem a Mac runtime overenie zostávajú pending.** |

Uvedené číselné bump/sheen hodnoty sú existujúce vizuálne recepty, nie fyzikálne meranie materiálu na dome. Albedo je sRGB; roughness, masky, height a normal sú dátové mapy. Názov `nor_gl` deklaruje zdrojovú konvenciu mapy: pri natívnom importovaní overiť znamienko tangentovej Y zložky na orientovanom testovacom povrchu, aby sa reliéf neobrátil. Nenastavovať sRGB na normály alebo roughness.

## Rastliny a alfa kanály

| Materiál / geometria | Existujúce mapy | Prenos a pôvod |
| --- | --- | --- |
| `real-plant-grass` | `public/assets/vegetation/ornamental-grass-card.png`, **768 × 702, RGBA, alpha 0–253** | Preniesť embedded alpha do opacity mask, cutoff **0.28**, two-sided; zachovať UV konkrétnej karty (`babylon-scene.ts:2680–2703`). README označuje mapu ako starší **imagegen prototyp**, nie reálnu fotoreferenciu. Netvoriť novú mapu ani ju premenovať na sken. |
| `real-plant-perennial` | `public/assets/vegetation/perennial-cluster-card.png`, **1024 × 682, RGBA, alpha 0–255** | Rovnaký cutoff **0.28** / two-sided. Starší imagegen prototyp. Bez prenesenia alpha sa exportované roviny javia ako plné obdĺžniky. |
| `real-hedge-dark`, `real-hedge-mid`, `real-hedge-light` | `public/assets/textures/hedge-privet-albedo.png`, **1254 × 1254, RGB, bez alpha** | Je to bezšvový farebný povrch prototypového živého plota, nie cutout list. Nevymýšľať chýbajúcu alpha masku. Zdroj UV scale: `(1.7+index×0.13,1.35+index×0.11)`, offsets `(index×0.217,index×0.137)`; nie fyzická perióda v metroch. README uvádza imagegen. |
| `ArchViz \| Living hedge leaves` a geometria `shrub_02` | `output/archviz/assets/shrub_02/textures/shrub_02_{diff_1k.jpg,alpha_1k.png,mask_1k.png,rough_1k.exr,nor_gl_1k.exr}` | Overený CC0 model/mapy Rico Cilliers. Zachovať **UV skenovaného modelu**. Alpha riadi listový cutout, samostatná `mask` odlišuje listy a drevo; nemožno ju zameniť za alpha. Cycles tint `(0.45,0.85,0.30)`, roughness floor 0.55, normal strength 0.5. Použiť ako skenovanú náhradu spolu so zodpovedajúcou geometriou, nie nalepiť náhodnú atlasovú UV na pôvodný živý plot. |
| `ArchViz \| Dry living grass blades` a `grass_bermuda_01` | `output/archviz/assets/grass_bermuda_01/textures/grass_bermuda_01_{diff_1k.jpg,alpha_1k.png,rough_1k.exr,nor_gl_1k.exr}` | CC0 Rico Cilliers; zachovať modelové UV a blade geometry. Cycles používa diff+alpha, roughness scalar 0.95, tint `(0.70,0.85,0.55)`; normal/roughness súbory existujú, ale nie sú v tomto existujúcom shaderi zapojené. |
| `tree_small_02*` | `output/archviz/assets/tree_small_02/textures/tree_small_02_leaves_{diff,alpha,nor_gl,rough}_1k.png` a samostatné branch/body mapy | CC0 Rico Cilliers. Leaf alpha a branch/body normal sa priraďujú zodpovedajúcim skenovaným material slotom; ponechať modelové UV. Škálovanie rastliny nemení deklaráciu, že nejde o zameraný inventár zelene na parcele. |

Aktuálny `scripts/archviz/scene-export.ts` zbiera scalar alpha a názov albedo textúry, **nie** embedded obrázok, cutoff, `useAlphaFromAlbedoTexture`, obojstrannosť ani UV transformácie textúry. Nový scalar GLB preto tento vizuálny kontrakt sám nenesie. Potrebný je natívny material mapping alebo explicitný rozšírený capture; UV geometrie nestačia na rekonštrukciu runtime scale/offset textúry. Žiadna dynamicky generovaná alpha mapa rastlín nebola v audite identifikovaná: dve karty ju už majú v PNG, skenované rastliny ju majú osobitne a privet ju nemá.

`street-grey-block-paver-albedo` a príslušný normal sú **DynamicTexture** generované v `babylon-scene.ts:1454–1552`; nejde o súbor v `public/`. Ich prenos vyžaduje capture/bake existujúceho deterministického výstupu alebo explicitnú natívnu náhradu. Nie sú to alpha textúry.

## Voda, obloha a historické GLB

`public/assets/textures/pool-water-normal.png` je existujúci **1254 × 1254 RGB** imagegen prototyp bez alpha. Babylon ho animuje posunom UV **+0.0065/s, −0.0042/s**, scale **2.35 × 1.65**, normal level **0.42** (`babylon-scene.ts:1561–1574,2608–2613`). Táto normála nepreukazuje fyzikálne kaustiky. Preferovaná natívna iterácia má oddeliť fyzickú hladinu/objem a výpočet vĺn; neprepíše presnú bazénovú geometriu.

`public/assets/archviz/sky.hdr` je existujúci lineárny **2048 × 1024** render fyzikálnej oblohy z Blenderu, nie fotografia lokality. Podľa `environment-manifest.json` je world-strength 0.23 už započítaný a disk slnka vypnutý; priamy sun light je oddelený. Dátum oblohy je **2026-09-04T16:30:00+02:00**. Nesmie sa zamieňať za dynamickú oblohu každého dňa/nočného režimu. `sky.jpg` je AgX display obraz tej istej oblohy, nie lineárny HDR vstup.

Súbory `public/assets/archviz/dom-*.glb` obsahujú historické vložené mapy pripravené cez `web/prepare_textures.py` (väčšina do 1K, roughness do 512 px) a samostatne upravenú geometriu. Pre novú 4K aplikáciu preferovať pôvodné overené 2K mapy v `output/archviz/assets`; samotný 4K framebuffer neznamená, že vzdialenostná ostrosť 2K/1K textúry je overená. Textúry historického GLB možno auditovať, ale geometriu domu z neho nevracať do aktuálneho Variant C.

## Proveniencia a licencie

- **Poly Haven:** lokálne zaznamenaná licencia **CC0-1.0**, `https://polyhaven.com/license`, konkrétne stránky/autori a originálne download MD5 v `scripts/archviz/assets.lock.json`. Toto je audit lokálneho locku, nie nové právne overenie webu. Záznam `public/assets/archviz/credits.json` sa nevzťahuje automaticky na všetky doplnkové projektové textúry.
- **Lokálne procedurálne mapy:** `tools/generate-visual-assets.py`, deterministic seed/recept; README:350–369 deklaruje lokálny vznik bez externých zdrojov. Neoznačovať ich ako Poly Haven CC0 ani ako fotografované vzorky.
- **Teplé interiérové varianty:** `scripts/archviz/web/prepare_living_palette.py` upravuje farbu pôvodných procedurálnych máp; nejde o nový sken alebo imagegen v tejto iterácii.
- **Staršie imagegen mapy:** explicitne označené vyššie podľa README:355–360. Tento audit nevygeneroval žiadne nové obrázky a nedáva im dodatočnú externú licenciu.
- **RAL 7016, sklo a voda:** scalar/procedurálne shader recepty; nemajú separátnu fotografovanú PBR sadu v audítovanom locku.

| Poly Haven sada | Autor podľa locku | Lokálne zaznamenaný zdroj |
| --- | --- | --- |
| `white_plaster_02` | Rob Tuytel | https://polyhaven.com/a/white_plaster_02 |
| `hinoki_planks` | Charlotte Baglioni | https://polyhaven.com/a/hinoki_planks |
| `asphalt_02` | Rob Tuytel | https://polyhaven.com/a/asphalt_02 |
| `concrete_pavement` | Charlotte Baglioni | https://polyhaven.com/a/concrete_pavement |
| `shrub_02` | Rico Cilliers | https://polyhaven.com/a/shrub_02 |
| `grass_bermuda_01` | Rico Cilliers | https://polyhaven.com/a/grass_bermuda_01 |
| `tree_small_02` | Rico Cilliers | https://polyhaven.com/a/tree_small_02 |

## Kontrolné súčty použitých vstupov

SHA-256 nižšie overuje konkrétne lokálne bajty; nesvedčí o autorstve ani o fyzikálnej správnosti. Poly Haven MD5 zároveň zodpovedá locku. Rozmery v pixeloch boli pre JPG/PNG načítané z obrázka; pri EXR je uvedený iba typ, bez predstierania dekódovania. `PH` = CC0 podľa locku; `P` = lokálny procedurálny projektový asset; `G` = existujúci imagegen prototyp; `B` = lokálny Blender render.

| Cesta od koreňa repozitára | Pôvod | Rozlíšenie / kanály | SHA-256 |
| --- | --- | --- | --- |
| `output/archviz/assets/white_plaster_02/white_plaster_02_diff_2k.jpg` | PH | 2048×2048 RGB | `0ca5245ba70777d3e41ff4566c9f8d363855461891802c55cb7dc0f6f85f084e` |
| `output/archviz/assets/white_plaster_02/white_plaster_02_rough_2k.jpg` | PH | 2048×2048 L | `a3dc1911f6e25d88fdb0031fe0cfb602eec5496084c508774c60691bed087417` |
| `output/archviz/assets/white_plaster_02/white_plaster_02_nor_gl_2k.jpg` | PH | 2048×2048 RGB | `083579b03a8f31ec1886512e5972f3b893610bf26a2098f97910e0f46745cdc9` |
| `output/archviz/assets/white_plaster_02/white_plaster_02_disp_2k.jpg` | PH | 2048×2048 L | `7a477010377e267bbf3c650037f0659c9b5b0c7860f8056e0145600145ef66fc` |
| `output/archviz/assets/hinoki_planks/hinoki_planks_diff_2k.jpg` | PH | 2048×2048 RGB | `e21f0bd9a5fb1ecaf1d363a8a6e0fb36f4dfb2c43dda7be3a6c2a4cb5ccda587` |
| `output/archviz/assets/hinoki_planks/hinoki_planks_rough_2k.jpg` | PH | 2048×2048 L | `cbbb654e748c6c28c45d6dc9d41e04da5e161a81ce2f146fd6c7f2d7acca8e97` |
| `output/archviz/assets/hinoki_planks/hinoki_planks_nor_gl_2k.jpg` | PH | 2048×2048 RGB | `d068ba2c76222280bd54b12dd9bfae7e768ed1c353c184b04826ea844e553762` |
| `output/archviz/assets/hinoki_planks/hinoki_planks_disp_2k.jpg` | PH | 2048×2048 L | `dc6ccab40cfd74461bd203d63f49ed605b0aa604a14c2666bc3634a45fd8fa7c` |
| `output/archviz/assets/asphalt_02/asphalt_02_diff_2k.jpg` | PH | 2048×2048 RGB | `28f5ba8690553f192c0e5e1a5ff40f34765b4b93f4cc7059b1a3e9c795b6c28c` |
| `output/archviz/assets/asphalt_02/asphalt_02_rough_2k.jpg` | PH | 2048×2048 L | `b9a516b61b7040a9245ac206642d5f767ad9589a0169c4a1668221429e8a998c` |
| `output/archviz/assets/asphalt_02/asphalt_02_nor_gl_2k.jpg` | PH | 2048×2048 RGB | `ffe49db71a0fd34c1e259625df66a302a237597d6ef655307987ec4e45bc6f21` |
| `output/archviz/assets/asphalt_02/asphalt_02_disp_2k.jpg` | PH | 2048×2048 L | `943f254ed5e1504131547b35afe3798771cdda33842b7fdc6c0288b8312a44b0` |
| `output/archviz/assets/concrete_pavement/concrete_pavement_diff_2k.jpg` | PH | 2048×2048 RGB | `e5a1cecfe7765cc0b24a6ab0abf492bd21c9e7af64e97fc46ef6021d0645fbd3` |
| `output/archviz/assets/concrete_pavement/concrete_pavement_rough_2k.jpg` | PH | 2048×2048 RGB | `e97b7d190dcda5a842813502505bf3d1b2348b4cad57b1d51d1bcc694a92d137` |
| `output/archviz/assets/concrete_pavement/concrete_pavement_nor_gl_2k.jpg` | PH | 2048×2048 RGB | `72def937e418ccc9d7736c9b1f51ae22a127fa2a53a54f4d1fe4d3cf828b781c` |
| `output/archviz/assets/concrete_pavement/concrete_pavement_disp_2k.jpg` | PH | 2048×2048 L | `ab724fbe03ae03af5565bedf9fc299612e4cd086fffa6a2828488b78f4e0062a` |
| `output/archviz/assets/shrub_02/textures/shrub_02_rough_1k.exr` | PH | EXR | `a9f6cda20dc287fb27ab5c9a399284ae02e8abf032ad324f3083ebcf7f1987a5` |
| `output/archviz/assets/shrub_02/textures/shrub_02_alpha_1k.png` | PH | 1024×1024 I;16 | `5c2c31bac311051db77443e1780078403c2df0a832c40fe6ed7bcd982695cdf0` |
| `output/archviz/assets/shrub_02/textures/shrub_02_diff_1k.jpg` | PH | 1024×1024 RGB | `9956eff294034d70516d867e9668428a23d782feb3d4c34061dce5e44bacd5a8` |
| `output/archviz/assets/shrub_02/textures/shrub_02_mask_1k.png` | PH | 1024×1024 RGB | `5079f3b1136b10f715934f401c7f75b3fa015e24c92680f8758e09f8f0cdf7e2` |
| `output/archviz/assets/shrub_02/textures/shrub_02_nor_gl_1k.exr` | PH | EXR | `e7a55808cea62a123f3f27a92d83a0d55aaadfe64bc7f75853f8f49f37fd63c9` |
| `output/archviz/assets/grass_bermuda_01/textures/grass_bermuda_01_alpha_1k.png` | PH | 1024×1024 I;16 | `e58b3052aad2f107cdd763e437f80ed8fb5a31bcc43b44023f7f767cb3d9888e` |
| `output/archviz/assets/grass_bermuda_01/textures/grass_bermuda_01_diff_1k.jpg` | PH | 1024×1024 RGB | `ef202eeb8f8fb3312446009acecc87e5679a7d612e4dee859d8a849e00af5fcb` |
| `output/archviz/assets/grass_bermuda_01/textures/grass_bermuda_01_nor_gl_1k.exr` | PH | EXR | `7aab2717abf1395f618639038c873901ef56ccddaceb785120d3c92bf25efe85` |
| `output/archviz/assets/grass_bermuda_01/textures/grass_bermuda_01_rough_1k.exr` | PH | EXR | `d2f7d214ed82da77531027b8f865613d41d0b92582e5054a79fc025970e34cf8` |
| `output/archviz/assets/tree_small_02/textures/tree_small_02_branch_diff_1k.png` | PH | 1024×1024 RGBA | `a93ce54213c4a98cd01cb5c5f7ab46b77defcd66e1dd082e6912f6e60632e630` |
| `output/archviz/assets/tree_small_02/textures/tree_small_02_branch_nor_gl_1k.png` | PH | 1024×1024 RGBA | `0338a1400391893fdf6c6cbd1c22a573d6ab2300ad771d4916184bf206e1a671` |
| `output/archviz/assets/tree_small_02/textures/tree_small_02_branch_rough_1k.png` | PH | 1024×1024 RGBA | `f285a54d141f30e39c7741e84a813c5cbccd9e9ee397af687176213f77d3e9a5` |
| `output/archviz/assets/tree_small_02/textures/tree_small_02_diff_1k.jpg` | PH | 1024×1024 RGB | `4e0093f407b3a1120a36de49a48ebe5a465a9a9b77e361c7a3e66866e115e404` |
| `output/archviz/assets/tree_small_02/textures/tree_small_02_leaves_alpha_1k.png` | PH | 1024×1024 I;16 | `4f143e2dda8a6a572f427ac378b92255d21761e4611de0d26e21816c01aa533b` |
| `output/archviz/assets/tree_small_02/textures/tree_small_02_leaves_diff_1k.png` | PH | 1024×1024 RGBA | `d3fc48522c76aa1f91076c6b86f302669822ebe4e2acabd67d42c4d57eaa5ba0` |
| `output/archviz/assets/tree_small_02/textures/tree_small_02_leaves_nor_gl_1k.png` | PH | 1024×1024 RGB | `fa4ad390f2e68b745db8f568cad64c3272696c5e01312ae564795e37724d79b8` |
| `output/archviz/assets/tree_small_02/textures/tree_small_02_leaves_rough_1k.png` | PH | 1024×1024 I;16 | `f005213467e38bcb355b00c9a6eb9896b8d810ee885d5c7fa308d9f3326ef602` |
| `output/archviz/assets/tree_small_02/textures/tree_small_02_nor_gl_1k.exr` | PH | EXR | `cf999e30663267b55b6fab43ca97c1e96176bdc67268e6c25854d53f15267d64` |
| `output/archviz/assets/tree_small_02/textures/tree_small_02_rough_1k.exr` | PH | EXR | `1ed5ad24397c065beb2b2d3521470730f24e957cbd5fb323ad3f9b6d267b4585` |
| `public/assets/textures/living-boucle-ecru-albedo.jpg` | P | 1024×1024 RGB | `b62ea6969ab726b9cf86ddf119ea312f15d04425245d9a5a089dc0ef27017408` |
| `public/assets/textures/boucle-taupe-albedo.jpg` | P | 1024×1024 RGB | `3e44df64378075b07b7308cda9b6cde1c31faa95f95a8a673fbfdd35cb3cf4f9` |
| `public/assets/textures/boucle-taupe-normal.jpg` | P | 1024×1024 RGB | `330091afdd0a396040098f7b81f3200eabfa3c26e97b90b79e1d371854b33379` |
| `public/assets/textures/living-wool-sand-albedo.jpg` | P | 1024×1024 RGB | `2de75244e7d43729e5d6754742f4fdda25d6edc8ce03e7824c2adb14e85b4ea4` |
| `public/assets/textures/rug-wool-taupe-normal.jpg` | P | 1024×1024 RGB | `cc1725cd1bdc07caf776af8cef446115c5a5f9a0b225622fd4e61597c679d89a` |
| `public/assets/textures/living-natural-oak-albedo.jpg` | P | 1024×1024 RGB | `3a4b4434352fddb00bc338cf55128ea3c9f33d2fb98384bf2d3471575636bd52` |
| `public/assets/textures/oak-veneer-normal.jpg` | P | 1024×1024 RGB | `9b052b993e0d54780092b153597b72f09c3b3c05f8cc3420942e3beae1fc26ae` |
| `public/assets/textures/living-warm-stone-albedo.jpg` | P | 1024×1024 RGB | `eabe7b05be4ea951fa865caffe04a10e5f379245d29502bec3a5fbf797c80d9e` |
| `public/assets/textures/stone-dark-normal.jpg` | P | 1024×1024 RGB | `2b132bf3cc6175f40a2906871600b4f812740c196f4952f7912b7fe8d00762a0` |
| `public/assets/textures/metal-anthracite-normal.jpg` | P | 512×512 RGB | `db78996dc2e382a7ebdb1ad2ba967214e39501632e70b5b451b61449289cf470` |
| `public/assets/textures/hedge-privet-albedo.png` | G | 1254×1254 RGB | `292f8afb1f30d4dd49def0e20292d3b9d5a0d430b266e6b6ae556771b340eadf` |
| `public/assets/textures/pool-water-normal.png` | G | 1254×1254 RGB | `d5ed33734eaef8123d2d68ba1d2b4dd19a3851eade7b5c0d36c33e3cef997e4a` |
| `public/assets/vegetation/ornamental-grass-card.png` | G | 768×702 RGBA | `0f603d68be529b3adcb37815704822abe8c68de5adadfb045732ecebaeb5daec` |
| `public/assets/vegetation/perennial-cluster-card.png` | G | 1024×682 RGBA | `09c5b97195f823daa9cf9c4a36c6471e2e4c43804621532f66fd54fa60b9dbde` |
| `public/assets/archviz/sky.hdr` | B | HDR | `7f1e6856111a9cd7af6e9fc63bcc37a6434b549f1ce0e2023cfb3e1917997f2f` |
| `public/assets/archviz/sky.jpg` | B | 2048×1024 RGB | `43c197c6e5391f7d660557137309f943d71aced83d936d26d6a9410440865ab9` |

## Uzavretie ďalšej natívnej iterácie

Za implementované považovať iba material sloty s natívnym importom, overeným source-name mapovaním, korektným sRGB/data nastavením a vizuálnou skúškou na orientovanom povrchu. Samostatne overiť leaf cutout z oboch strán, detail čalúnenia zblízka, jednotnú mierku dosiek, transparentnosť skla a priechod svetla do interiéru. Prítomnosť súborov, Khronos validácia alebo glTF roundtrip samy tento výsledok nepotvrdzujú. Native water kaustiky a fyzikálna vernosť svetla zostávajú otvorené.

## Natívny autor materiálov

`scripts/unreal/materials.py` implementuje explicitný prvý PBR priechod cez
`apply_materials(scene_manifest, mesh_assets_by_id, output_dir)`. Importér ho volá
iba pri `BREZI_APPLY_MATERIALS=1`, po kontrole skutočných UE rozmerov. Materiály a
textúry vznikajú iba v `/Game/Brezi/MaterialsGenerated`; opakovaný beh overuje
vlastníctvo assetov a aktualizuje sloty podľa identifikátora `MAT_####`, nie podľa
predpokladaného poradia. Zdrojová geometria ostáva zachovaná.

Omietka, drevo a dlažba používajú vstavané `WorldAlignedTexture` a
`WorldAlignedNormal` s fyzickou periódou prevedenou z metrov do UE centimetrov.
Normály sú tlmené na 0.2 pre omietku a 0.55 pre ostatné foto sady; nie je pridaný
geometrický displacement. Interiérové projektové mapy zachovávajú UV0, scalar
roughness a tint aktívnej revízie, s tlmením normal 0.35 a osobitne 0.16 pre
pohovku. Tento prvý graf ešte neprenáša všetky sheen/clearcoat atribúty pôvodného
shaderu. RAL override sa týka iba kovových rámov, plota a strešného lemovania.
Názov `real-glass-frame-wood` ostáva bez override.

Dve existujúce botanické PNG karty sa pripájajú ako masked/two-sided s cutoff
0.28. Sklo, voda, kaustiky, neprenesené materiály a objemové rozptyľovanie listov
zostávajú samostatnými otvorenými krokmi. Nevznikla nová rastlina ani nový bitmapový
obrázok.

Autor kontroluje Poly Haven download MD5, pevne uložené audit SHA-256 projektových
máp, úspech material API spojení, návratové chyby recompile a uloženie assetov.
`output/unreal/materials-report.json` má explicitný `pending`/`failed`/
`materials-authored` stav, source/writer hash, zoznam textúr, priradení a skutočné
hashy uložených `.uasset` a prípadných `.uexp`/`.ubulk` súborov. Pole
`nativeAuthoredSha256` viaže tieto vstupy a výstupy. Úspech commandletu nie je
vizuálne potvrdenie Metal renderu: `renderedMetalVerified` zostáva false až do
samostatného natívneho obrazového testu.

Overené v UE 5.8 commandlete s NullRHI dňa 2026-09-08: **42 vytvorených grafov,
25 importovaných textúr a 740 priradených mesh materiálov**. Finálny úplný import
`BREZI_APPLY_MATERIALS=1 npm run unreal:import` skončil exit 0; znovu zmeral všetkých
**1 878** aktívnych objektov s maximálnou odchýlkou **0.009765625 mm**. Native
material recompile API nevrátilo žiadne chyby. Po ukončení sa nezávisle zhodovalo
všetkých **807** zaznamenaných hashov uložených súborov (67 generated assets a
740 upravených mesh assets). Toto potvrdzuje commandlet/asset fázu; Metal render,
4K výkon, optické sklo, voda a kaustiky tým stále nie sú overené.

Receipts: `output/unreal/materials-report.json`, `output/unreal/import-report.json`;
log: `output/unreal/materials-import.log`. Výsledný `nativeAuthoredSha256` tejto
iterácie je `f3ec25a20e992178dc99da45eaf831cd36bfb22159ce3bc74bc9311366b73d90`.

## Revízia podľa zadania 8. 9. 2026 a druhý natívny probe

Nasledujúce dve rozhodnutia nahrádzajú pôvodné odporúčanie zachovať dlažbu ulice
a hnedé okenné rámy. Sú explicitnými `nativeDesignOverrides` podľa nového zadania;
historický zdrojový záznam ani kanonická geometria sa nemenia:

- Iba `real-road` používa overenú `asphalt_02` s periodou 3 m. Historický
  `SRC-CLIENT-STREET-PHOTO-20260825` naďalej eviduje sivú betónovú blokovú dlažbu.
  `real-paving`, `real-paving-entry` a `real-concrete` zostávajú pri betóne/dlažbe.
- Iba okenný slot `real-glass-frame-wood` dostáva rovnakú aproximáciu RAL 7016
  ako ostatné kovové rámy. Terasy, obklad a drevený nábytok sa tým nemenia.

Prvý denný Metal obraz odhalil bielu strechu: `real-roof` mal správnu statickú
textúru v zdroji, ale predchádzajúci natívny priechod ju neprenášal. Teraz má
presný source-name/path selector pre `metal-anthracite-albedo.jpg` a existujúci
normal, s jemnou 0.15 m svetovou periódou a zachovanou zdrojovou roughness 0.52.
Rovnaký audit obnovil pomenované epoxy, tile, wall-tile, dark-worktop, dve
artwork textúry, štrkové pásy a krajnicu. Všetky nové statické vstupy majú pevné
SHA-256 piny v `scripts/unreal/materials.py`; žiadny biely source material so
statickou textúrou neostáva bez explicitnej receptúry.

`real-solar` prenáša existujúci `photovoltaic-cell-grid` ako natívny procedurálny
UV shader: zdrojové 1024 × 640, 10 × 6 buniek, 7 px medzery, 2 px obrysy a dve
3 px zbernice, rovnaké gradientové sRGB farby s výstupným prevodom do linear.
Okraje používajú derivatívové vyhladenie. Clearcoat 0.9 / roughness 0.07 ide cez
`MakeMaterialAttributes`, pretože UE 5.8 skrýva `MP_CustomData0/1` z Python enumu.

Samostatný `scripts/unreal/optics.py` má API
`apply_optics(scene_manifest, mesh_assets_by_id, output_dir)`. Vlastní iba
`/Game/Brezi/OpticsGenerated`, pripája dva master grafy a štyri inštancie podľa
source-slot metadát. ThinTranslucent sklo používa IOR 1.52 a fyzikálny Fresnel;
SingleLayerWater IOR 1.333, absorption/scattering a štyri analytické animované
normálové vlny. Hodnoty 1/m sa v grafe násobia 0.01 na natívne **1/cm**. Optický
objem vychádza zo scene depth k existujúcemu dnu; nevzniká nový mesh. Hladina
−12 mm a footprint 6000 × 2700 mm sa kontrolujú pred priradením, mesh bounds,
počty vrcholov a trojuholníkov aj po ňom. `DOM_00887` zostáva pôvodnou tenkou
vrstvou vody v dreze, hoci zdieľa shader meno `real-bathroom-shower-glass`.

Oddelený NullRHI probe **materials → optics → Nanite usage** skončil exit 0:
55 grafov, 40 textúr, 856 priradení mesh materiálov; optics 2 master grafy,
4 inštancie a 23 mesh objektov; 97 Nanite objektov s 29 použitými materiálmi.
Znova sa zmeralo všetkých 1878 objektov, maximálna odchýlka 0.009765625 mm.
Nezávisle sa zhodovalo 1002 aktuálnych uložených súborových hashov.
`import-report.json` probe nemenil; trvalý import/cook musí root vykonať osobitne.

Dôkazy: `output/unreal/optical-material-probe/probe-report.json` a
`output/unreal/optical-material-probe-engine.log`. **Toto je natívne overenie
grafov, parametrov, geometrie a uložených assetov s NullRHI. Nový Metal obraz,
PV vzhľad, optika a výkon ešte týmto probe overené nie sú.** Dynamické kaustiky
sa nevytvárajú; `ColorScaleBehindWater` zostáva presne 1. Tinty, voda a vlny sú
počiatočné vizuálne receptúry, nie odmerané výrobky alebo vzorky vody.

### Samostatná úprava varných zón a jemného dreveného povrchu

Zdroj `lib/babylon-interior.ts` opisuje varnú dosku ako čierne sklo so štyrmi
prstencovými značkami, ale značky exportuje ako plné 200 × 200 × 2 mm valce.
Iba `DOM_00667`–`DOM_00670` dostávajú variant
`/Game/Brezi/MaterialsGenerated/M_MAT_0041_CooktopRing`. Pred vytvorením grafu sa
kontroluje každé ID, meno/sourceId `KITCHEN-RUN · varná zóna`, slot `MAT_0041`
`real-interior-steel`, 128 trojuholníkov a rozmery s toleranciou 0.01 mm.
Digestor a všetky ostatné objekty so spoločným oceľovým slotom zostávajú pri
pôvodnom materiáli. Identita slotu zostáva v metadátach aj pri opakovanom importe.

Maska počíta radiálnu vzdialenosť svetovej XY pozície od stredu bounds objektu
v natívnych centimetroch. Stred prstenca je 98 mm od stredu platne, šírka 2 mm,
takže pôvodná vonkajšia stena valca pri polomere 100 mm zmizne spolu s plným
vnútrom. Ide o sivú neemitujúcu potlač s roughness 0.45 a metallic 0; šírka ani
farba nie sú odmeraný výrobok. Mesh, jeho kolízia a bounds sa tým nemenia.
Priradenie je zaznamenané ako explicitný objektový `nativeDesignOverride`.

Presne šesť interiérových slotov si ponecháva pôvodné albedo, farebný násobok,
roughness, metallic a UV0; pridáva sa iba jemná normála a variácia drsnosti:

| Source slot | Source name | Smer vlákien v UV0 |
| --- | --- | --- |
| MAT_0031 | real-interior-vinyl-oak | U, pozdĺž podlahových dosiek |
| MAT_0039 | real-interior-kitchen-front | V, výška čelných plôch |
| MAT_0064 | real-hallway-wardrobe-smoked-oak | V |
| MAT_0065 | real-hallway-wardrobe-warm-oak | V |
| MAT_0078 | Living warm cabinet &#124; real-interior-living-cabinet | V |
| MAT_0080 | Living warm oak &#124; real-interior-kitchen-front | V |

Existujúca `oak-veneer-normal.jpg` je takmer plochá. Nový jemný detail je preto
priznanou procedurálnou aproximáciou povrchu, nie zosilneným údajným skenom.
Používa 180 a 317 cyklov na jednotku pôvodného UV, nízku smerovú deformáciu,
pridaný normálový sklon najviac 0.018 (približne 1.03° na plochej normále)
a zmenu roughness najviac ±0.018. Derivácie utlmia detail pri nedostatočnom
rozlíšení. UV škála zostáva autorovaná po jednotlivých plochách `texturedBox`;
nevydávame spoločnú fyzickú veľkosť pórov za odmeranú hodnotu. Bočné a horné
plochy preberajú pôvodný UV chart, bez tvrdenia o rekonštruovanom stolárskom
reze. Terasa a obklad zostávajú pri overenej Hinoki receptúre; rámy pri RAL.

Všetky existujúce textúry naďalej prechádzajú pôvodnými SHA-256/MD5 pinmi.
`output/unreal/material-detail-qa.py` overuje presný rozsah, odmietnutie zmeneného
zdroja, centimetrové rozmery masky, hranice jemného detailu, zdrojové hashy a
opakované priradenie štyroch platní bez zmeny spoločnej ocele. Sedem CPU testov
prešlo; výsledok `material-detail-qa.json` obsahuje SHA skriptu aj scene.
Tento priechod ešte nemá natívne spustenie, Metal cook ani vizuálne overenie.
Vodné/sklenené grafy a opravené mazanie ich uzlov sa nemenili.
