# Bazénové kaustiky: overenie a realizovateľný návrh, 8. 9. 2026

Odporúčanie: samostatný RDG výpočet dopredného toku lúčov zo súčasných vĺn do HDR mapy osvetlenia prijímajúcich povrchov. Samotný vzor má fyzikálne odvodenú polohu a energiu. Jeho vloženie do osvetlenia UE vyžaduje oddelený natívny experiment; emisná animácia ani `ColorScaleBehindWater` tento krok nenahrádzajú. Žiadny Unreal proces, shader build ani GPU test sa počas tohto výskumu nespustil. `optics.py` zostal nezmenený.

## Čo skutočne máme

[optics.py](/Users/davidzita/www/dom/scripts/unreal/optics.py:41) používa štyri analytické sínusové vlny: dĺžky 360/190/110/70 mm, amplitúdy 0,60/0,35/0,18/0,10 mm, frekvenciu `sqrt(g/(2πλ))`, smer a fázu zo `WAVES`. Sú to autorské parametre, nie meranie vody. Menia iba normálu; geometria hladiny sa nehýbe. Ten istý čas, svetové súradnice, fázy a normály musí používať budúci výpočet kaustík. Duplicitná nezávislá animácia by časom stratila súlad.

Zdrojový bazén má hladinu `DOM_01725` pri −12 mm, dno `DOM_01720`/`real-pool-tile` s hornou plochou pri −1412 mm a štyri steny `DOM_01721` až `DOM_01724`. Rozmer 6000 × 2700 mm a **navrhovaná**, nie zameraná hĺbka 1400 mm sú overené v [scene.json](/Users/davidzita/www/dom/output/unreal/geometry/scene.json) a [buildGardenPool](/Users/davidzita/www/dom/lib/babylon-scene.ts:5916). Podvodné schody a odtok tiež treba pri finálnom ray teste zohľadniť; AABB stien nenahrádza všetky zdrojové trojuholníky.

[viewpoints.json](/Users/davidzita/www/dom/output/unreal/geometry/viewpoints.json) obsahuje lokalitu 48,8175859646° N, 16,5527842348° E a čas **2026-09-04 16:30 +02:00**. Native light-forward, teda smer pohybu slnečného lúča, je približne `[0.7560316, 0.4519543, −0.4734486]`. Nepoužiť jeho opačné znamienko. Intenzita 80 000 lx je autorský vstup expozície, nie lokálne meranie. Polohu a orientáciu čítať zo sidecaru, nenapočítavať z iného začiatku súradníc.

## Lokálny renderer a jeho hranice

`SingleLayerWaterShading.ush:170–238` násobí už osvetlenú `BehindWaterSceneLuminance` hodnotou `ColorScaleBehindWater`. Nevytvára svetelný prenos na povrch dna. Toto explicitne potvrdzuje aj [Epic: Single Layer Water](https://dev.epicgames.com/documentation/en-us/unreal-engine/single-layer-water-shading-model-in-unreal-engine). Zachovať aktuálnu hodnotu `[1,1,1]`.

Legacy light function zapisuje masku osvetlenia cez `LightFunctionPixelShader.usf:62–81`; jej bežný render target je `PF_B8G8R8A8` (`LightRendering.cpp:1897`). Rozsah masky je 0–1: sám nedokáže zosilniť pôvodné slnko v miestach sústredenia toku. Navyše používa sivú intenzitu. Atlas v `LightFunctionAtlas.cpp:704` používa `PF_R8` alebo `PF_R8G8B8A8`, tiež nie HDR. Jeho materiál nesmie závisieť od hĺbky, GBufferu alebo svetovej pozície. [Epic: Light Functions](https://dev.epicgames.com/documentation/en-us/unreal-engine/using-light-functions-in-unreal-engine).

**Rozpor dokumentácie a lokálneho UE5.8:** stránka Epic stále uvádza vylúčenie Directional Lights z atlasu. Lokálny `AllocateAtlasSlots():381` ich však uprednostňuje a `CanLightUsesAtlasForUnbatchedLight():1372` preveruje kompatibilitu materiálu bez takéhoto zákazu. Funkčnosť directional atlasu preto nemožno označiť za overenú ani všeobecne zakázanú bez natívneho testu. Naše world-space mapovanie aj tak nesplní uvedenú atlasovú podmienku.

Metal má explicitné mapovanie `PF_FloatRGBA → RGBA16Float` a `PF_R16F → R16Float` (`MetalRHI.cpp:979–1000`); typed UAV load/store sa zapína podľa úrovne podpory zariadenia (`:1063–1075`). To dokladá dostupnú implementačnú cestu, **nie** odmeraný čas ani záruku ľubovoľných float atomic operácií. Preferovať rasterizačné aditívne splaty/trojuholníky; nepridávať závislosť od float atomics. Runtime musí overiť formátové capabilities. Všetky uvedené súbory ležia pod `/Users/Shared/Epic Games/UE_5.8/Engine`; ich SHA-256 sú v CPU reporte.

## Výpočet prvého lomu

V SI jednotkách, so svetovým Z nahor a dopadajúcim normalizovaným smerom `I`:

```text
h(p,t) = Σ a sin(2π(d·p/λ − f t + phase))
N = normalize(−∂h/∂x, −∂h/∂y, 1)
eta = 1 / 1.333;  c = −dot(I,N)
T = eta I + (eta c − sqrt(1 − eta²(1−c²))) N
q(p) = p + ((zFloor−zWater)/Tz) Txy
J = ∂q/∂p
```

Snellov smer a presný Fresnelov podiel nepolarizovaného svetla vychádzajú zo štandardnej geometrickej optiky. Pri prenose paketov výkonu nepridávať bezdôvodne ďalší faktor `eta²`: Jacobian už zohľadňuje zmenu plošnej hustoty; pravidlá škálovania radiancie sú iná veličina. [PBRT: Specular Reflection and Transmission](https://www.pbr-book.org/4ed/Reflection_Models/Specular_Reflection_and_Transmission).

Paket cez horizontálnu bunku `dA` nesie relatívny tok `Eperp × max(−Iz,0) × dA × (1−F) × visibility`. Na prvom prijatom povrchu sa priamy tok zmenší o `exp(−(absorption+scattering) × pathLength)`; rozptýlenú energiu tento prvý odhad ďalej nesleduje. Použiť koeficienty z `optics.py`, so správnymi jednotkami 1/m. Normálový model s pevným začiatkom lúča na −12 mm je **aproximácia plochej strednej hladiny s meniacou sa normálou**, nie úplná simulácia premiestnenej hladiny. Pri neskoršom optickom modeli skutočnej výšky `h` treba upraviť začiatok lúča aj projekčný člen toku; nemožno potichu meniť kanonickú geometriu.

Jacobian je vhodný na odhad veľkosti splatu a adaptívne delenie. `1/abs(det J)` platí po vetvách mapovania, treba sčítať všetky príchody. Inverzný shader s jediným Newtonovým koreňom nie je všeobecne správny. Dopredná rasterizácia všetkých lomom deformovaných buniek zvláda prekrytie vetiev aditívne; pri záhybe bunku rozdeliť, nezamlčať ho clampom. HDR akumuláciu deliť skutočnou plochou texelu, nie priemerom hotového obrázka. Lúče dopadajúce najprv na stenu, schod alebo odtok sa nesmú presunúť na dno.

## Porovnanie integrácií

| Cesta | Čo poskytne | Obmedzenie / rozhodnutie |
|---|---|---|
| Dopredná photon-density/HDR RT + receiver lighting | Mapa polohy, toku a zmeny v čase odvodená zo Snella; prijímajúce povrchy môžu mať vlastný atlas | Odporúčaná základňa. Vyžaduje source ray intersections, slnečnú viditeľnosť a explicitné vloženie do priameho osvetlenia. |
| Jednokoreňový inverse Jacobian na dne | Lacný lokálny odhad pri bijektívnom mapovaní | Súčasné vlny už majú záhyby; stráca ďalšie príchody. Samostatne nepoužiť. |
| Light function | Pohybujúca sa maska skutočného svetla, prijímaná geometriou | Na pôvodnom slnku iba zoslabuje. Zisk nad 1 vyžaduje oddelený normalizovaný pool light, odstránenie pôvodného priameho slnka na prijímači a explicitnú energetickú kalibráciu. Žiadne globálne zvýšenie slnka. |
| Emisný vstup konkrétneho dna | Vzor je na dne aj pre podvodnú kameru | Je to aproximácia zobrazenia vypočítaného toku. Pridaním k existujúcemu slnku vzniká dvojnásobná energia; nerieši správne tiene, BRDF ani Lumen feedback. Označiť diagnosticky, nie ako hotový prenos svetla. |

Možný stock-engine experiment používa vyhradený lighting channel iba pre pôvodné opaque dno a normalizovanú light function `G/M` s pool-only intenzitou násobenou `M`; shader musí reportovať prekročenie `M`, nie potichu rezať vrcholy. Najprv treba overiť mobilitu prijímača, oddelenie pôvodného slnka, uhlový kosínus a tiene. Sivý legacy variant neposkytne celý RGB prenos. Lighting channels sa týkajú priameho dynamického osvetlenia opaque povrchov, neoddelia automaticky GI ani všetky materiály. [Epic: Lighting Channels](https://dev.epicgames.com/documentation/unreal-engine/using-lighting-channels-in-unreal-engine). Čistejšie dlhodobé riešenie je vlastný receiver direct-light pass, ktorý nahradí iba zodpovedajúci priamy člen.

## Konkrétny postup a rozpočet na overenie

1. Exportovať spoločné vlnové parametre, aktuálny čas, sun-forward, fyzické hodnoty a source IDs s hashmi. Pridať GPU RDG pass cez vlastný runtime modul; dostupný hook je `FSceneViewExtensionBase::PreRenderViewFamily_RenderThread`, `SceneViewExtension.h:175`. Zdieľaný output musí byť explicitne synchronizovaný a pripojený ako shader resource. [Epic: RDG](https://dev.epicgames.com/documentation/en-us/unreal-engine/render-dependency-graph-in-unreal-engine).
2. Generovať nezávislú optickú vzorkovaciu mriežku, nie nový architektonický mesh. Prvé meranie: 768 × 384 vzoriek na apertúre; približne 590 tisíc dopredných trojuholníkov, najviac 7,82 mm rozstup v dlhej osi. HDR mapa 512 × 256, dve RGBA16F textúry približne **2 MiB**. Voliteľný 32-bajtový záznam na vzorku pridá 9 MiB; indexy možno odvodiť z vertex ID. Pamäťový cieľ simulácie je ≤16 MiB vrátane visibility, bez zdieľaných scénových akceleračných štruktúr; samostatný nový BVH by bolo nutné započítať navyše. To je rozlíšenie simulácie; viewport ostáva natívny 4K.
3. Zahrnúť slnečnú viditeľnosť na vodnej apertúre a prvý zásah zdrojovej geometrie po lome. Pri statickom slnku/scéne možno cacheovať vstupnú visibility mapu, pri zmene času alebo pohybe objektov ju invalidovať. Dno riešiť prvé; steny a schody pridať cez receiver atlas. Vypínať pri slnku pod horizontom a pri nepotrebnom prijímači.
4. Konečnú šírku ostrých kaustík odvodiť z uhlového rozsahu slnka, nie z pohybujúcej sa noise mapy. Engine constructor má `LightSourceAngle=0.5357°` (`DirectionalLightComponent.cpp:1050`), ale native binding má čítať aktuálnu hodnotu komponentu. Začať integrovaným splatom; viac smerových vzoriek je ďalšia položka rozpočtu. Žiadny neodôvodnený boost amplitúdy vĺn alebo časové posúvanie bitmapy.
5. **Cieľ rozpočtu, nie nameraný výsledok:** najviac 1,0 ms dodatočného GPU času pri blízkom 4K pohľade, z toho orientačne 0,5 ms tvorba mapy, 0,2 ms filter/resolve, 0,3 ms aplikácia a amortizovaná visibility. CPU runtime cieľ ≤0,2 ms/frame, žiadny synchronný GPU readback. Overiť medián aj p95 v rovnakých 4K pohľadoch s efektom vypnutým/zapnutým. Pri prekročení najprv zmerať jednotlivé RDG passy; žiadny predpoklad, že uvedená mriežka tento cieľ splní. Zníženie časovej frekvencie nesmie rozísť normály s mapou kaustík.

## CPU dôkaz a jeho presný rozsah

Spustenie: `python3 output/unreal/caustics-sanity.py`. [Prototyp](/Users/davidzita/www/dom/output/unreal/caustics-sanity.py), [report](/Users/davidzita/www/dom/output/unreal/caustics-sanity/report.json) a dva CSV sú iba matematické diagnostiky. Neobsahujú render aplikácie ani hotovú textúru určenú na nasadenie.

- Plochá hladina: uhol lomu 41,3595°, dráha vo vode 1,86523 m, presun na dne `[1,05789, 0,63241]` m, Fresnelov odraz 0,067673; `det J=1`.
- Zdrojové vlny pri `t=0`: **37,055 %** vzoriek zasiahne stenu skôr než dno. Minimálny skúmaný determinant **−0,003447**, teda mapovanie má záhyb; nejde len o pohyb pravidelnej textúry.
- Rezíduum Snellovho zákona ≤3,34×10⁻¹⁶. Chyba súčtu energie uloženej do mapy voči prijatým paketom <3×10⁻¹⁴. Štvornásobné zahustenie vzoriek zmenilo integrovaný zelený tok dna o približne **0,00437 %**.
- Viditeľnosť slnka je v experimente všade 1; dom, terasa a schody netienia. Lúče k stenám sa iba počítajú. Slnko je kolimované, konečný disk a viacnásobný prenos sa nesimulujú. Výsledná maximálna hustota závisí od konečného rozlíšenia splatov; nie je to garantovaný fyzikálny horný limit.
- Overené sú normálny dopad, IOR=1 bez ohybu, plochý Jacobian, Snell, zachovanie uloženej energie, zmena v čase a konvergencia integrovaného toku. **Metal shader, fyzikálna presnosť celej scény, vizuálny fotorealizmus a GPU rozpočet zostávajú neoverené.**
