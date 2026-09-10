# Samostatné zdrojové kolízne telesá

`scripts/archviz/scene-export.ts` zachytáva enabled skryté meshe s reálnym `mesh.checkCollisions === true` do oddeleného poľa. Pôvodné poradie a obsah `meshes` pre viditeľný OBJ nemení. Archív, optické dekorácie a proxy s vypnutou kolíziou sa do doplnku nesmú dostať. Aktuálny zdroj obsahuje 57 takýchto telies; počet sa vždy overuje proti presnému zoznamu `scene.skipped`, nie podľa názvu alebo odhadu nábytku.

Export vytvorí vedľa `scene.json`:

- `hidden-collision-source.json`: skutočné source positions, indices, normals, instance/world matrices a metadata.
- `brezi-collision-only.glb`: výhradne trojuholníky vyššie uvedených telies, bez materiálov a bez pripojenia k viditeľnému OBJ.
- `hidden-collision.json`: stabilné identity `COLL_` + prvých 20 hex znakov SHA-256 pôvodného UTF-8 source ID, presné počty a obálky, hash capture/GLB/main OBJ/scene, kontrola Khronos a runtime tags.

Geometria sa transformuje presnými zdrojovými maticami; žiadny fitting boxu, konvexná aproximácia, nová pozícia ani prečíslovanie `DOM_` objektov. GLB používa metre; UE mapuje `[x,y,z]` na `[100*x,100*z,100*y]` cm. Source navigation guards môžu byť zámerne konzervatívne (napríklad vyššie než nábytok); tento doplnok zachováva ich skutočné trojuholníky. Tieto rozmery sa nesmú prezentovať ako merané fyzické rozmery nábytku. Vozidlá a iné dynamické zdrojové telesá zostávajú v zachytenej polohe.

## Natívny import a dôkaz

`scripts/unreal/hidden_collision.py` poskytuje:

1. `verify_inputs(scene_manifest, geometry_dir)` – samostatný vstupný gate pred akoukoľvek zmenou mapy.
2. `apply_hidden_collision_contract(scene_manifest, geometry_dir)` – asset-only Interchange import do `/Game/Brezi/HiddenCollision`, potom vlastné skryté StaticMeshActors. Viditeľnosť, hidden-in-game, tiene, RT a DF vplyv sú vypnuté ešte pred prvým priradením meshu. Používa explicitný profil `BlockAll`, `QueryAndPhysics`, Pawn Block, LOD0 a `CTF_USE_COMPLEX_AS_SIMPLE`; Nanite je vypnutý. Žiadny floor tag ani generovaná jednoduchá kolízia.
3. `verify_hidden_collision_contract(scene_manifest, geometry_dir)` – volá sa po uložení mapy, prechode cez prázdnu mapu a opätovnom načítaní pôvodnej mapy. Číta skutočné komponenty, flags, LOD0 trojuholníky a world bounds bez ďalšieho authoringu.

`UBreziCollisionAudit::ReadLod0Triangles` je malý editor-only readback; mimo vlastného namespace alebo mimo editor buildu vracia prázdny výsledok. Negeneruje ani nemení meshe. Python porovná všetky trojuholníky so source GLB; dovolí iba zmenu poradia indexov/vrcholov, s toleranciou 0,005 cm. Kontrola obálok má toleranciu 0,02 cm a je doplnková – rovnaký box nestačí na úspech.

`import_scene.py` oba kroky zapája, canonical count necháva oddelený a auxiliary asset/pipeline hashes pridáva do `finalAssetHashes`/`pipelineFiles`. Uloženie a opätovné načítanie sa deje pred finálnym import receipt. Výstup `hidden-collision-report.json` má až po úspešnom reread stav `hidden-collision-saved-reloaded-validated`; pri chybe sa prepíše na `failed`. `import-report.json.hiddenCollision` nesie rovnaké údaje. Súhrn obsahuje `objectCount`, `triangleCount`, `maxTriangleErrorCm`, `maxBoundsErrorCm`, každý source ID/component/asset, source hashes a asset hashes.

Natívny runtime načítava samostatný `Content/Data/hidden-collision.json`, kontroluje zhodu scene/OBJ identity a presne jeden neviditeľný blokujúci komponent pre každé `COLL_` ID. `walking.json` naďalej opisuje canonical podlahy, steny a zachytené zatvorené dvere. Package gate musí hashovať všetky tri zdrojové doplnkové súbory, ich Data kópiu, helpery, assety a mapu; UFS musí obsahovať `Data/hidden-collision.json`.

## Overenie a hranice

CPU regresie: `node --test tests/unreal-hidden-collision.test.mjs`. Kontrolujú nepreniknutie do hlavného namespace, stabilitu ID, úplnú Khronos validáciu, transformácie, odmietnutie neprípustných dát a zistenie zmenených trojuholníkov aj pri zachovaní ich počtu a obálky.

Koordinovaný export, regenerácia vegetácie, Editor build a natívny import už prebehli.
`output/unreal/hidden-collision-source-proof.json` potvrdzuje nezmenený hlavný OBJ
aj presne rovnakých 1 895 kanonických záznamov. Natívny import skončil s exit 0,
uložil a znovu otvoril všetkých 57 objektov/684 trojuholníkov. Maximálna odchýlka
trojuholníkov bola 0,000057220459 cm a bounds 0,000087738037 cm.
Podklad: `output/unreal/import-report.json` a `hidden-presentation-material-import-2.log`.

Zabalený runtime následne overil celý kontrakt vrátane 57 pomocných kolízií a reálne
pripravených fyzikálnych triangle mesh dát. Vstup a státie v interiéri prešli s exit 0
a 541 podopretými vzorkami. Podklad:
`output/unreal/runtime/walking-interior-standing-hwrt-5fa57033-fa67-495e-8a5d-79602b6332a8/`.
To nepreukazuje prejdenie všetkých trás, kontakt s každým kusom nábytku, dverovú
animáciu ani vizuálnu kvalitu. Každá takáto oblasť má osobitný natívny test.
