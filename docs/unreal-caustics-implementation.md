# Ohrančený natívny prototyp kaustík — 8. 9. 2026

**Odporúčanie:** najprv samostatne zostaviť a overiť plugin [BreziCausticsProbe](/Users/davidzita/www/dom/output/unreal/caustics-native-draft/BreziCausticsProbe). Návrh obsahuje vykonateľné C++/HLSL zdroje a CPU validátor. C++ ani Metal shader sa ešte nekompilovali. Projekt aplikácie, importer, `materials.py` a `optics.py` sa pri tejto úlohe nemenili; žiadny UE/GPU proces sa nespustil.

## Presný prijímací kontrakt

[receiver-contract.json](/Users/davidzita/www/dom/output/unreal/caustics/receiver-contract.json) prenáša **45 zdrojových objektov, 1 076 nezmenených trojuholníkov a 359 BVH uzlov**. Zahŕňa dno DOM_01720, steny DOM_01721–24, schody DOM_01755–58, tri svetlá, skimmer, dve trysky, odtok a lem. Identita každého trojuholníka zostáva `(objectId, sourceFaceIndex)`, priestor je `[OBJ.x, −OBJ.y, OBJ.z]/1000` v metroch. Rozmery a počty sú overené proti `scene.json` a SHA celého OBJ. Opätovný export scény zmenil iba kolízne metadáta; aktuálny scene SHA začína `97f3af06`, OBJ zostáva `a42e9eb1`.

Hladina zostáva na −0,012 m, horné dno na −1,412 m, pôdorys 6 × 2,7 m. Hĺbka je návrhová. Normály sú zo štyroch presných autorských vĺn `optics.py`; nejde o meranú vodnú hladinu. Koeficienty absorpcie a rozptylu sa prenášajú v 1/m. Rozmer, poloha ani vrcholy architektúry sa neupravujú.

Nový [CPU first-hit test](/Users/davidzita/www/dom/output/unreal/caustics/receiver-report.json) už lúče k stenám a schodom nezahadzuje. Pri t=0, 29 440 vzorkách a zdrojovom slnku dopadá 17 596 lúčov na dno; 846 na štyri schody a 88 na odtok. Žiadny lúč neunikol. Bilancia odrazu + útlmu + prijatého RGB toku má relatívnu chybu <2,4×10⁻¹⁵. Pri t=0,125 s sa rozdelenie zmení. Priemer BVH je 32,53 testov trojuholníka na lúč; to je CPU algoritmický počet, **nie GPU výkon**.

## Zapojenie do UE5.8

Plugin má runtime modul s fázou `PostConfigInit`, ktorá včas registruje global shaders cez `AddShaderSourceDirectoryMapping`. Samotná view extension sa registruje až cez `OnPostEngineInit`: lokálny `SceneViewExtension.cpp:68` vyžaduje existujúci `GEngine`. Tento detail zabraňuje tichému neregistrovaniu extension pri príliš skorom štarte. Modul je predvolene vypnutý. Postup zodpovedá [Epic: shaders in plugins](https://dev.epicgames.com/documentation/en-us/unreal-engine/overview-of-shaders-in-plugins-unreal-engine).

Prototyp generuje mapu v **`PostRenderBasePassDeferred_RenderThread`**. Public hook dostane konkrétny view aj hotový `ViewUniformBuffer`; lokálny `BasePassRendering.cpp:1162` ho volá po base passe. CS priamo číta `View.GameTime`, rovnaký ako `MaterialExpressionTime`, vrátane pause a `r.Test.OverrideTimeMaterialExpressions`. Čítanie iba `ViewFamily.Time` by minulo tento diagnostický override (`SceneView.cpp:2877`). Neskoré miesto je vhodné pre izolovaný výpočet a readback; mapa zatiaľ nemá produkčného konzumenta. Pre neskoršie vzorkovanie v base-pass materiáli ju treba vypočítať pred base passom a explicitne vyriešiť čas i resource dependencies, nie použiť predchádzajúci frame bez synchronizácie normál.

Game thread vyhľadá jediný natívny actor s runtime tagom `BreziSun`, uloží jeho forward smer a lux; render thread nečíta UObject. Výpočet podporuje iba hlavný single-view deferred viewport SM6, nie scene captures/reflections. Normovaný tok je relatívny k jednotkovej kolmej irradiancii; hodnota lux sa iba zaznamená. Nevykonáva sa nezdokumentovaný prevod lux na RGB radianciu.

Passy:

1. `TraceCS`: 512 × 230 lúčov, Snell IOR 1,333, nepolarizovaný Fresnel, najbližší zásah presných source triangles, Beer–Lambertov útlm. Jednorazovo nahraté statické BVH buffery. Každý photon record má 48 B: world hit/status, RGB tok/dĺžka, Fresnel/object index/triangle index/aktuálny shader čas.
2. `SplatVS/PS`: procedurálne dvojice trojuholníkov uložia tok **iba horného dna DOM_01720** do linear RGBA16F mapy 512 × 256. RGB je delené skutočnou plochou texelu. Bilineárne splaty pri kraji normalizujú iba prijatý floor packet; ostatné first-hit pakety sa na dno nepresúvajú. Alpha je diagnostická váha vzoriek.
3. Asynchrónny readback je jednorazový na zvýšenie capture CVAR. Zapisuje celý photon buffer aj atlas vrátane ne-floor príjmov; chyby stacku, uniknuté alebo nahor smerujúce lúče majú samostatný status. Validátor ich v uzavretom dennom teste odmietne. Mapa sa nikam nepripája ako emissive/light function.

RDG deklaruje UAV/SRV a render-target závislosti. Raster používa aditívne blendovanie, bez float atomics. Runtime overí `RenderTarget | TextureBlendable | TextureSample` capabilities pre `PF_FloatRGBA`; lokálny Metal RHI mapuje tento formát na RGBA16Float. Profil má samostatný GPU scope. [Epic: RDG](https://dev.epicgames.com/documentation/en-us/unreal-engine/render-dependency-graph-in-unreal-engine).

## Výkon a energetické hranice

Približné veľkosti bez RHI zarovnania: photon buffer 5,39 MiB, dva súčasne živé floor atlasy 2 MiB, statické source buffery 0,07 MiB. Readback navyše potrebuje približne 6,39 MiB GPU staging pamäte a CPU kópie; ide o diagnostiku, nie bežný runtime. V tejto fáze **neexistuje nameraný čas GPU**, kvalita MSAA splatov ani dôkaz, že pass splní cieľ ≤1 ms pri 4K. Efekt treba porovnať vypnutý/zapnutý, capture vypnutý, v rovnakom pohľade, medián aj p95.

Vstupná slnečná viditeľnosť je stále 1; okolité steny domu, terasa a zeleň netienia lúče pred vstupom do vody. Pod vodou už všetky pool prekážky tienia prvým zásahom. Slnko je kolimované; konečný disk, viacnásobné odrazy a objemovo rozptýlený tok sa nesimulujú. Je to single-refraction aproximácia pevnej strednej hladiny s meniacimi sa normálami. Pre úplný receiver atlas treba pridať chartovanie skutočných stien a schodov, nie preniesť ich tok na floor UV.

Najťažší ďalší krok zostáva osvetlenie: stock view-extension hook automaticky nenahradí priamy slnečný člen konkrétneho povrchu. `ColorScaleBehindWater` sa nemení; emisným pridaním k plnému sun termu by sa energia zdvojila. Light-function cesta potrebuje oddelenie pôvodného slnka pre prijímače a explicitnú normalizáciu gainu do rozsahu masky; legacy sivá maska nedá plný RGB prenos. Pred produkčným bindingom treba samostatný návrh BRDF, pre-exposure, viditeľnosti a priameho svetla. Fotorealizmus sa týmto draftom netvrdí.
