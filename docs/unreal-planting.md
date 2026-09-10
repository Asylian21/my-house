# Natívne záhony — 2026-09-09

Aktuálna macOS aplikácia používa nový povrch drevnej štiepky na dvoch existujúcich záhonoch. Pôvodná výsadba zostáva aktívna. Prvý autorský model okrasnej trávy technicky prešiel importom, ale bol zamietnutý pri kontrole skutočného 4K obrazu.

## Prijatý povrch

`scripts/unreal/planting-surfaces/` pridáva iba component material overrides pre `DOM_01821` a `DOM_01822`. Zachováva ich pôvodných 5 a 3 trojuholníky, UV, výšku −29 mm, kolízie a pôvodný Interchange materiál `MAT_0091`. Zadný mulčovací pás `DOM_01692`, ktorý zdieľa rovnaký zdrojový materiál, zostáva bez tohto override.

Použitá je [CC0 PBR sada Wood Chips](https://polyhaven.com/a/wood_chips) od eye-candy.xyz / Poly Haven. Tri mapy majú 4096 × 4096 pixelov a fyzickú periódu 2000 mm podľa provider metadata. `inputs.json` obsahuje URL, veľkosti, MD5 a SHA-256; pôvodné API odpovede sú uložené v `inputs/`.

Materiál má osem uzlov a tri texture samples. Albedo je sRGB, roughness lineárna bez remapu a OpenGL normal mapa sa pri importe invertuje v zelenom kanáli raz. Súradnice sa odvodzujú z natívneho world XY / 200 cm; dekódovaný normál sa používa vo world priestore, nezávisle od pôvodnej UV tangent basis. Geometrické výškové nerovnosti ani displacement sa nepridávajú. Ide o vizualizačný výber materiálu, nie o meranie skutočného mulču na parcele.

Native stage overuje presné dve väzby, celý zachovaný stav ostatných aktérov vrátane 33 769 inštancií trávnika a reálne MeshDescription pozície/UV. Materiál a tri textúry sa uložia, uvoľnia z pamäte a opätovne načítajú pred aj po aktivácii. Import a package gate prešli.

## Zamietnutý prototyp tráv

`scripts/unreal/ornamental-grass/inputs/authored-v1/` uchováva deterministický generátor a šesť GLB modelov. Každý má 72 listov a 1584 trojuholníkov, spolu 9504. Zdrojové koreňové polohy a obaly XY boli zachované; výška 75 % pôvodnej karty bola explicitným autorským návrhom. Pri trse 4 sa najnižší rad listov predĺžil o 32 mm do existujúceho podkladu bez posunu kotvy. Nejde o sken ani o overený botanický kultivar.

Všetkých šesť GLB prešlo oficiálnym Khronos validatorom bez chýb a varovaní, opakovaná generácia bola byte-for-byte rovnaká a native import potvrdil trojuholníky, UV, umiestnenie a uložené materiály. Skutočný záber však ukázal príliš úzku základňu, tuhé zalomené listy a zahnuté hranaté špičky. Technická validácia preto neznamená vizuálne prijatie.

Prototyp je predvolene vypnutý. Experimentálny import možno výslovne zapnúť cez `BREZI_APPLY_ORNAMENTAL=1`; bežný import obnovuje a overuje všetkých 18 pôvodných kariet. Opakovaný native import overil starú vrstvu šiestich aktérov pred jej odstránením a potom skutočný uložený stav pôvodných kariet. Zdieľaný `MAT_0004`, krajnicové karty a trvalky sa nemenia.

Zamietnutý obraz a jeho technické dôkazy zostávajú v `output/unreal/runtime/foreground-terrace-day-60c0556a-c06d-45ca-874b-2c5af65bcb64/`. Aktívny obraz má samostatný dôkaz uvedený nižšie.

## Aktuálny balík a overenie

- Aplikácia: `output/unreal/package/Mac/BreziTwin.app`.
- Package receipt SHA-256: `fe1a382d393a8556c3c66f6bb6804ef35eead275075f4680fe43bf6cb5dfed7f`.
- Mapa SHA-256: `be665781eb0ea23418c015e207189500afb75914b301928db551d2c55614b8ba`.
- Bežný BuildCookRun prešiel za 69.74 s so stock ZenLaunch sponsorom; nebol potrebný manuálny zásah.
- Native PID 1838 skončil s kódom 0. Po 1200 zahrievacích snímkach sa meralo 300 snímok; všetky mali aktívnu aplikáciu, okno aj keyboard focus. Render target aj RHI textúra zostali 3840 × 2160, render percentáž 100 %, bez dynamického znižovania rozlíšenia.
- Priemer 53.945 ms, **18.54 fps**; p95 62.531 ms. Jedna vzorka nepreukazuje kauzálny výkonový rozdiel. Požiadavka plynulého 4K a celkového fotorealizmu zostáva nesplnená.
- Všetkých 2456 source/import pinov aj zabalený payload boli overené pred a po behu. Záverečný terasový obraz bol skutočne prezretý; nejde o dôkaz všetkých pohľadov ani o 4K fyzický displej.

Aktuálne dôkazy: `output/unreal/runtime/foreground-terrace-day-11b8503b-59e1-403b-85b4-df9adbe0e23a/`. Celý priebeh, pôvodná záloha a rozhodnutie o prototype: `output/unreal/planting-adoption/` a `output/unreal/planting-iteration.json`.

```sh
node scripts/unreal/planting-surfaces/fetch-assets.mjs
node scripts/unreal/run.mjs import
node scripts/unreal/run.mjs package
node output/unreal/foreground-study/capture-deck-terrace.mjs day
```

Autoritatívne 2D/Babylon zdroje sa nemenili. Oheň sa podľa pokynu používateľa ďalej neladil.
