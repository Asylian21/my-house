# Unreal exteriér a okolie Březí

Záväzná architektúra je [C/B/B](active-design.md), s uličným aj pravým kolmým odstupom 3 000 mm. Exteriérová pipeline mení vizuálne okolie v samostatnom výstupe. Pôvodné stavebné mesh assety, materiálové assety, kolízie, rozmery a transformácie zostávajú overené kontrolnými súčtami a natívnym odtlačkom scény.

## Autorita a stav

Autoritou pre spustenie je `output/unreal/model-refresh-current.json`, nie najvyššie číslo adresára. Nový adresár, úspešný cook ani úspešný test nie sú vizuálnym prijatím. Výstupy R1 až R6 boli technicky overené, ale vizuálne zamietnuté; dôvody a presné SHA256 sú v `output/unreal/exterior-validation-20260926-r1/exterior-rN-rejected-review.json`.

Aktuálna pracovná iterácia je `output/unreal/exterior-20260927-r7`. Nadväzuje na regionálne listnaté koruny, skupiny krov, prirodzenejšie záhonové rastliny a krátky zelený porast R6. R7 pripravuje skorší farebný prechod do ortofota a selektívnu zelenú sezónu celých polí s ochranou ciest a zástavby. Jej prijatie musí byť doložené samostatným review, pôvodnými natívnymi PNG a dokončeným meraním pohybu. Tento dokument sám výstup nepovyšuje na hlavný.

## Dátové podklady

- [Parcely a povrchy](unreal-exterior-context.md): uložený oficiálny ČÚZK WFS, transformácia zhodná s doterajším C3 modelom, geometrické vylúčenie samotnej parcely a pôvodných ciest. Vyznačenie hraníc je vizuálna pomôcka, nie vytýčenie stavby.
- [Ortofoto](unreal-exterior-orthophoto.md): ČÚZK 2024, georeferencované farby vzdialenej krajiny, overený rozsah a maska chýbajúcich snímok. Fotografia obsahuje pôvodné osvetlenie; nejde o neutrálny PBR sken.
- [Terén](unreal-exterior-terrain.md): DMR 5G, zachovaná výška bez zvislého zvýraznenia. Chýbajúce údaje majú výslovne označenú ilustračnú náhradu; pôvodná výška a kolízia stavebného pozemku sa nemení.
- [Vzdialená zástavba](unreal-exterior-buildings.md): oficiálne pôdorysy, odhadnuté výšky a strechy. Nevydávať za zameraný model fasád.
- [Rastliny a materiály](unreal-exterior-assets.md): CC0 zdroje a odvodené modely s tromi LOD. Druhová skladba aj vinohrad sú vizuálnou interpretáciou, nie botanickým súpisom miesta.

## Import do izolovanej kópie

Použiť nový, dosiaľ neimportovaný výstup. Presné frozen vstupy uvádza `exterior-import-report.json`; staré vstupy ani hotové balíky neprepisovať.

```sh
BREZI_MODEL_OUTPUT=output/unreal/exterior-YYYYMMDD-rN \
  BREZI_ARCHVIZ_GAME=1 BREZI_DOUBLE_GLASS=1 \
  BREZI_GAME_CONFIGURATION=Shipping BREZI_DEFAULT_RENDER_PROFILE=cinematic \
  node scripts/unreal/model-refresh.mjs prepare

BREZI_MODEL_OUTPUT=output/unreal/exterior-YYYYMMDD-rN \
  node scripts/unreal/model-refresh.mjs inherit output/unreal/realism-20260926-r5

BREZI_MODEL_OUTPUT=output/unreal/exterior-YYYYMMDD-rN \
  node scripts/unreal/model-refresh.mjs reuse-build output/unreal/realism-20260926-r2
```

`reuse-build` prijíma iba zhodné natívne source/config piny. Pri odlišnom C++ alebo konfigurácii použiť normálny Editor/Game build.

Akcia `exterior` vyžaduje `BREZI_EXTERIOR_CONTEXT` (context-plan.json) a `BREZI_EXTERIOR_ASSETS` (adresár troch manifestov). Voliteľné `BREZI_EXTERIOR_TERRAIN`, `BREZI_EXTERIOR_GARDEN`, `BREZI_EXTERIOR_BUILDINGS` a `BREZI_EXTERIOR_YARD` prijímajú konkrétne immutable JSON plány. `BREZI_EXTERIOR_ORTHO` voliteľne pridáva overený manifest ortofota, iba spolu s jeho zhodným terénom. Balík pri jeho použití obsahuje podpísaný `Contents/Resources/ExteriorDataCredits.json` a výstup samostatný `EXTERIOR-SOURCES.txt`. Všetky vstupy sa pripnú SHA256. Následne spustiť akciu `package` s rovnakým `BREZI_MODEL_OUTPUT`.

`BREZI_EXTERIOR_SEASONAL_FIELDS` pridáva samostatný manifest autorskej zelenej sezóny, pripnutý ku konkrétnemu ortofotu. Mení iba farbu vybraných vnútorných plôch polí; vstupné fotografie, alpha pokrytia a výška terénu ostávajú zachované. Geografická maska sa vzorkuje na explicitnej mip úrovni 0, aby sa farebná úprava nerozlievala na chránené okolie. Zelená sezóna nie je tvrdením o aktuálnej plodine alebo termíne snímkovania.

`BREZI_EXTERIOR_FIELD_MACRO` pripája obmedzený jasový detail odvodený z ortofota k štyrom blízkym materiálom polí. Rozsah 0,75–1,10 nemení farebný charakter PBR podkladu, normály, výšky ani kolízie. Maska chráni cesty, dom, zástavbu a porasty vrátane priestoru pre bilineárne filtrovanie. `BREZI_EXTERIOR_DIAGNOSTIC_VIEWS` voliteľne pripojí overené kamery ku korunám stromov; je naviazaný na presné manifesty kontextu, terénu a stavieb. Statický audit kamery nenahrádza natívny render ani overenie chôdze.

Importer vytvára assety iba pod `/Game/Brezi/Exterior20260926`. Scéna prepne viditeľnosť nahradzovaných pôvodných rastlín a plochej vzdialenej plochy; staré assety zachová. Materiálové väzby mení len na explicitne určených vizuálnych povrchoch zeminy a mulča. Nové prvky nemajú kolízie ani navigačný vplyv.

Po uložení importer scénu zavrie, znova načíta a overí mesh LOD, materiály, presné transformácie všetkých inštancií a pôvodnú architektúru. `exterior-import-process.json` navyše viaže výsledok na konkrétny natívny proces a jeho log. Obnova neúspešného importu je dostupná iba pre ukončený proces, status `failed` a presnú nezmenenú checkpoint inventúru:

```sh
python3 scripts/unreal/exterior-import.py --restore output/unreal/exterior-YYYYMMDD-rN
```

## Vizuálna kontrola

`scripts/unreal/performance-qa.mjs` spúšťa skutočný Shipping proces cez Metal. Exteriérové pohľady sú `street-day`, `terrace-day`, `exterior-garden-day`, `exterior-vineyard-day`, `exterior-parcels-day`, `exterior-site-aerial-day` a `exterior-neighborhood-day`. Statické meranie a orbit sú rozdielne dôkazy. Automatizovaný režim `walk` používa interiérovú trasu; nemožno ho označiť za prechádzku lúkou.

Výstupy zostávajú v `output/unreal/exterior-validation-20260926-r1/qa/`. `runtime.json` obsahuje skutočné rozlíšenie, render profil, kontrakt scény, časovanie a stav popredia. Meranie bez platného popredia sa nemá používať na FPS tvrdenia. Pri interaktívnom aktivovaní okna možno nastaviť `BREZI_QA_WARMUP_FRAMES` v rozsahu 240–3600; nemení počet ani dĺžku meraných snímok. R4 sedem statických behov ani prvý 45-sekundový orbit nemali nepretržité popredie, preto ich agregované FPS nie sú platným výkonnostným porovnaním. PNG sa neupravujú. Galériu zostaví:

```sh
node scripts/unreal/exterior-gallery.mjs output/unreal/exterior-validation-20260926-r1
```

Galéria porovnáva iba rovnakú kameru, profil a rozlíšenie. Prijatie uzná výlučne z explicitného review zviazaného so SHA256 balíka a konkrétnych QA sérií. Lokálny render, technické testy a vizuálne prijatie sú tri odlišné úrovne dôkazu.

R5 má sedem úspešných 1920 × 1080 natívnych záberov s platným popredím (36,65–44,63 ms priemerný interval v režime Cinematic). Tieto statické merania nie sú dôkazom plynulej prechádzky. Vizuálne review stále odmietlo chýbajúce koruny, suchý sezónny podklad, holé plochy pri dome a pravidelné listové poschodia ružovej rastliny. R5 zostáva pracovným výstupom; launcher sa nezmenil.

R6 má sedem úspešných natívnych záberov 1920 × 1080 s platným popredím. Overil zelený porast pri dome, 1 100 explicitných regionálnych umiestnení a novú morfológiu záhonov. Celkový počet stromov nie je počet stromov viditeľných v jednom zábere. Review odmietlo najmä plošné materiály v strednej vzdialenosti a príliš svetlé listy ružovej rastliny. Pohyb ani 4K finálneho kandidáta zatiaľ tieto statické zábery nenahrádzajú.
