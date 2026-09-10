# Březí 6012/26 → Unreal Engine na macOS

Tri výstupy používajú tú istú pracovnú verziu dát: technická 2D dokumentácia,
interaktívna Babylon scéna a samostatný Unreal projekt. Export nemení pôdorys
ani schválenosť zdrojových revízií. Aktívny variant sa číta z `twin-interior.ts`;
fasádne úpravy z `twin-active-house.ts`, parcela a technické prvky z `twin-site.ts`,
doménový katastrálny záznam a provenance z `twin-domain.ts`.

## Kontinuálny režim caustics

Projekt teraz explicitne zapína schválený provider `transport-continuous`.
Jeho zdroje, konfigurácie a engine patch sú kanonické; existujúca overená
aplikácia a natívne dôkazy zostávajú samostatnými výstupmi.
[Aktuálne fázové príkazy](caustics/README.md) používajú izolovaný upravený engine,
nový cook a cooked binding pred podpisom. Staré príkazy `unreal:editor-build`
a `unreal:package` v tomto režime skončia pred natívnym spustením, pretože ich
monolitická cesta ešte neprepája celý overený postup. `unreal:open`, `unreal:qa`
a `unreal:qa-ui` prijímajú explicitné `BREZI_PACKAGE_REPORT` spolu s
`BREZI_PACKAGE_REPORT_SHA256`; bez nich zostáva pôvodný
`output/unreal/package-report.json`. [Presné príkazy pre overenú delivery app](caustics/README.md)
zahŕňajú read-only `package-check` a voliteľné profily `tsr67`/`tsr50` len pre otvorenie.

## Opakovateľný export a pôvodný postup bez kontinuálneho provideru

Export/testy spúšťajte z koreňa po `npm ci`. Natívne kroky v nasledujúcom
staršom postupe platia len pre konfiguráciu bez kontinuálneho provideru;
aktuálny predvolený projekt používa vyššie uvedené fázové príkazy:

```sh
npm run unreal:audit
npm run unreal:export
npm run unreal:vegetation
npm run unreal:test
npm run unreal:editor-build
python3 scripts/unreal/tv-oak/fetch_assets.py
npm run unreal:import
npm run unreal:package
npm run unreal:package-verify
npm run unreal:open
# Po úspešnom package: warmup, 300 meraných snímok a 4K PNG
npm run unreal:qa -- street
npm run unreal:qa -- interior
npm run unreal:qa-ui -- street
# Porovnanie výpočtu histórie TSR pri rovnakom 4K výstupe
npm run unreal:qa -- street --history-100 --profile-gpu
```

`unreal:export` zostaví aktuálnu procedurálnu Babylon scénu bez načítania starého
webového GLB. Existujúci exportér zachytí aj generované objekty a expanduje thin
instances. Blender konvertuje OBJ do glTF 2.0, aplikuje transformácie a znovu
načíta oba GLB. Každý logický objekt musí zachovať identity a svetové bounds
s odchýlkou menšou ako 0,5 mm. Nakoniec prebehne nezávislý Khronos validator,
kontrola hashov, archívnych vrstiev a kontraktu bazéna 6000 × 2700 mm.

Predpoklady: Node z `package.json`, Chromium cez `npx playwright install chromium
--only-shell`, Blender, Unreal Engine 5.8, plný Xcode a Metal Toolchain.
Chýbajúci kompilátor Metal pripraví `xcodebuild -downloadComponent MetalToolchain`.

Premenné: `BLENDER_BIN` určuje binárku Blenderu, `UNREAL_ENGINE_ROOT` adresár
engine (predvolene `/Users/Shared/Epic Games/UE_5.8`), `UNREAL_OUTPUT` adresár
geometrie (predvolene `output/unreal/geometry`). Pracovné dáta sa nepublikujú.
`unreal:import` vytvorí aj natívne PBR materiály z overených lokálnych máp.
Samostatný pass [deck-wood/deck_wood.py](deck-wood/deck_wood.py) upraví zdrojovo
identifikované drevo terasy bez zmeny geometrie. Pri `BREZI_APPLY_MATERIALS=1`
overí vstupy pred zmenou mapy a aplikuje sa po nastavení kolízií chôdze, aby
zachoval aj konečné nastavenie pochôdzneho poklopu.
Pri hodnote `0` sa vynechá spolu s ním. `import-report.json.deckWood` zaznamená
výsledok; vstupné piny a výsledné material/mesh hashe vstúpia do spoločného
záznamu, ktorý balenie overí pred aj po cooku. Úspešný import ešte nepotvrdzuje
vzhľad dreva v natívnom Metal renderi.
Nadväzujúci [fasádny materiál](../../docs/unreal-facade-wood.md) priradí 50 mm
zvislé obloženie presne 12 zdrojovým panelom. Geometriu a UV0 nemení; kontroluje
ich pred aj po priradení a materiály overí po opätovnom otvorení mapy.
Podklady obnoví `python3 scripts/unreal/facade-wood/restore_inputs.py`.
Na rýchlu kontrolu iba geometrie slúži
`BREZI_APPLY_MATERIALS=0 BREZI_APPLY_OPTICS=0 BREZI_APPLY_VEGETATION=0 BREZI_APPLY_WALKING=0 npm run unreal:import`.
Textúrové predpoklady a ich pôvod sú v [materiálovom pláne](../../docs/unreal-material-plan.md).
Tri TV skrinky majú samostatnú [fotografovanú dubovú dyhu](../../docs/unreal-tv-oak.md).
Jej obnovovací príkaz doplní chýbajúce fotografie a presné vstupné záznamy;
odlišné existujúce súbory neprepíše. Import naďalej overuje konkrétnu zdrojovú
geometriu a materiálové priradenia, takže zmena scény vyžaduje nový audit receptu.

`unreal:vegetation` pripraví skenované listy pre existujúci živý plot z lokálnych
CC0 podkladov `scripts/archviz/assets.lock.json` (stiahne ich `npm run archviz:assets`).
Konvertor overí všetkých 153 pôvodných korún a zachová ich priestorový objem.
Natívny import vytvorí osem priestorových skupín s tromi úrovňami detailu;
pôvodné proxy sa skryjú až po úspešnej kontrole. Trávnik ostáva zachovaný.
Nový export zdrojovej scény vyžaduje aj nové `unreal:vegetation`.

Balenie spúšťa aj explicitný UAT krok `-package` pred archiváciou. Kontroluje
payload vo vnútri `.app`, pak/IoStore súbory, pribalené ICU a kamerové dáta,
Retina plist a podpis. Samotný archivačný exit kód nestačí. Príkaz
`unreal:package-verify` iba skontroluje existujúci bundle; nepriraďuje mu aktuálne
zdrojové hashe. Tie sa zaznamenajú až po novom úspešnom `unreal:package`.
Každé QA spustenie ukladá vlastný log, JSON a PNG do `output/unreal/runtime`.
Pri `--profile-gpu` sa profil vyžiada uprostred zahrievacích snímok; uložený
`gpu-profile.log` vznikne len po pozorovanom výstupe profilera. `--history-100`
mení rozlíšenie histórie TSR, výstup a primárny render zostávajú 3840 × 2160
pri 100 %. Kvalitu hrán a pohybu treba porovnať pred zmenou predvoleného profilu.
QA aj balenie odmietnu už spustenú BreziTwin aplikáciu, aby ďalšie okno
neskresľovalo výkon alebo nepoužívalo práve prepisovaný balík.

## Výstupy a presnosť

| Výstup | Obsah |
| --- | --- |
| `output/unreal/geometry/brezi-twin.glb` | Aktívna architektúra, interiér, parcela, bazén, plot a detaily |
| `output/unreal/geometry/brezi-archive.glb` | Základy, schematické siete a pomocné vizuálne plochy |
| `scene.json` | Integer mm, pôvodné parcelné súradnice, revízie, source IDs, skip dôvody a SHA-256 |
| `bridge-report.json` | Konverzia, materiálový inventár, archívne dôvody, roundtrip odchýlky |
| `validation.json` | Úspešný výsledok kontroly aktuálnych bajtov; pri chybe sa starý výsledok odstráni |
| `viewpoints.json` | Kamery a slnko odvodené zo zdrojovej konfigurácie a GPS |
| `walking.json` | Zdrojové rýchlosti/výška očí, identifikované podklady, dvere a výškové korekcie; samo neimplementuje pohyb |
| `output/unreal/environment.json` | Sanitizovaný živý audit Macu a nástrojov |
| `output/unreal/import-report.json` | Skutočný výsledok importu a kontroly v Unreal |
| `output/unreal/package/Mac/` | Zostavená macOS aplikácia po úspešnom cook/package |

Zdrojové integer milimetre zostávajú v manifeste. Vrcholy renderovacích mesh používajú
float32 a toleranciu, preto sa z nich spätne nerobí geodetický zdroj pravdy.
`sourceCommit` je HEAD; `sourceWorktreeStatus` a hashe označujú aj necommitnutý
snapshot. Exportuje sa uložený zdrojový model, nie úpravy v lokálnom browser storage.

```text
OBJ (mm, Z-up RHS):  X=planX−15200, Y=planY−10800, Z=elevation
glTF (m, Y-up RHS):  X=(planX−15200)/1000, Y=elevation/1000, Z=−(planY−10800)/1000
Unreal (cm, Z-up LHS): X=(planX−15200)/10, Y=−(planY−10800)/10, Z=elevation/10
```

Unreal Interchange vykonáva metre → centimetre a výmenu osí raz. Import scale
zostáva 1. Mapa bola overená v lokálnom zdroji UE 5.8.2 (`ConvertVec3` a
`GltfUnitConversionMultiplier`); runtime import má vlastný merací report.
Pre geolokáciu sa používa otočený frame `twin-site.SITE_AXIS`, nikdy starší
nerotovaný lokálny origin z `twin-domain.ts`. National EPSG:5514 ring sa uchováva
bez zmeny. WGS84 aproximácia slúži osvetleniu, nie vytyčovaniu.

## Aktuálna hranica kvality

GLB prenáša geometriu a skalárne PBR hodnoty vrátane emisie. Nie je to finálny
fotorealistický materiálový balík: Babylon procedurálne textúry, refraction,
kaustiky a finálna vegetácia vyžadujú natívne Unreal shadery a vizuálnu iteráciu.
Archívne alebo konfliktné technické podklady nie sú automaticky koordinované
ani potvrdené stavebným úradom. Tieto stavy ostávajú v `scene.json.sources`.

Natívny projekt je v `unreal/BreziTwin`. Jeho shell používa štyri dátové kamerové
presety, filmový prechod, orbit/chôdzu a deň/noc. Jednotlivé štádiá dôkazu sú
oddelené: export, Unreal import, kompilácia, `.app`, Metal render, 4K framebuffer,
výkon a vizuálna kvalita. Samotný úspešný export žiadne neskoršie štádium nepotvrdzuje.

4K profil vypína dynamic resolution a nastavuje screen percentage 100. Fyzické
zobrazenie 3840 × 2160 vyžaduje 4K displej; na menšom monitore možno overiť 4K
render target a screenshot, nie počet fyzicky zobrazených pixelov.

Referencie: [glTF špecifikácia](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html),
[Epic glTF podpora](https://dev.epicgames.com/documentation/unreal-engine/gltf-file-format-support-in-unreal-engine),
[UE 5.8 release notes](https://dev.epicgames.com/documentation/unreal-engine/unreal-engine-5-8-release-notes).
