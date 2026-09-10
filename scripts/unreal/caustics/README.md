# Kontinuálna caustics pipeline — kanonické zdroje

Schválený plugin, projektové konfigurácie, súhrnný engine patch a fázové pomocné skripty sú teraz v repozitári. Samotné kopírovanie zdrojov nie je nový build ani nové natívne overenie. Existujúca delivery aplikácia a jej motion dôkaz zostávajú v pôvodných výstupných priečinkoch.

Predvolený projekt má `Mode=transport-continuous`. `npm run unreal:editor-build` a `npm run unreal:package` preto končia pred natívnym spustením: stará cesta nezostavuje reťazec source/build/cook/IoStore/cooked-binding. Ani správny upravený engine tento guard neobíde. Príkazy `unreal:open`, `unreal:qa` a `unreal:qa-ui` podporujú explicitný delivery report a jeho SHA-256. Bez tohto výberu naďalej používajú pôvodný `output/unreal/package-report.json`; nikdy ho neprepíšu ani automaticky nezamenia.

Overenie a spustenie už existujúcej delivery aplikácie na tomto Macu:

```sh
cd /Users/davidzita/www/dom
BREZI_DELIVERY_REPORT=/Users/davidzita/www/dom/output/unreal/caustics-delivery/reviews/package.json
BREZI_DELIVERY_SHA=73b9d1d887f1bda6b3991c27773deac7df5d1c00335952ff00a70ccabd686a6f

# Iba čítanie reportov, celého payloadu, startup entry a codesign --verify; aplikáciu nespustí.
BREZI_PACKAGE_REPORT="$BREZI_DELIVERY_REPORT" BREZI_PACKAGE_REPORT_SHA256="$BREZI_DELIVERY_SHA" \
  node scripts/unreal/run.mjs package-check

# Bežná aplikácia, pohľad na bazén; render defaults ostávajú v balíku.
BREZI_PACKAGE_REPORT="$BREZI_DELIVERY_REPORT" BREZI_PACKAGE_REPORT_SHA256="$BREZI_DELIVERY_SHA" \
  npm run unreal:open -- pool

# Existujúce samostatné QA: 240 warmup + 300 meraných snímok, následný 4K screenshot a exit.
BREZI_PACKAGE_REPORT="$BREZI_DELIVERY_REPORT" BREZI_PACKAGE_REPORT_SHA256="$BREZI_DELIVERY_SHA" \
  npm run unreal:qa -- pool
```

Report musí mať platné väzby na sedem pripnutých build/cook/source/seal receiptov, zapečatený cooked binding a celý nemenný obsah `.app`. Resolver navyše overuje aktuálny podpis a pôvodný vstupný bod aplikácie. Existujúce compiled source/helper hashe zostávajú historickým pôvodom buildu; spustenie hotového archívu ich neporovnáva s neskôr upravenými pracovnými zdrojmi ani s prepísaným Xcode build outputom. Nevykonáva nový cook ani nové fyzikálne/visual overenie. QA zachová presné pôvodné bajty reportu v `package.json` a cestu, SHA a receipt väzby v `package-selection.json`; po natívnom procese znovu kontroluje reporty, celý payload, entry a podpis.

Voliteľné experimentálne profily pre **bežné otvorenie** majú uzavreté názvy `native` (predvolené nastavenia balíka), `tsr67` a `tsr50`:

```sh
BREZI_PACKAGE_REPORT="$BREZI_DELIVERY_REPORT" BREZI_PACKAGE_REPORT_SHA256="$BREZI_DELIVERY_SHA" \
  BREZI_RENDER_PROFILE=tsr67 npm run unreal:open -- pool
# Rovnaký príkaz s BREZI_RENDER_PROFILE=tsr50 používa 50 % interné rozlíšenie.
```

Oba experimentálne profily vyberajú TSR, vypnú dynamic resolution, nastavia `r.ScreenPercentage` na 67 alebo 50 a TSR history na 100 jediným `ExecCmds`. Ponechávajú pevný výstupný scene target 3840×2160 a monitoru prispôsobené UI; interné vzorkovanie je nižšie. Nemenia HW Lumen, Nanite, VSM, materiály ani uložené konfigurácie. Samotné otvorenie nepotvrdzuje kvalitu pohybu ani výkon. `unreal:qa`/`qa-ui` so škálovaným profilom skončí pred spustením, pretože ich existujúce pravidlá vyžadujú natívnych 100 %. Súčasnú aplikáciu treba zavrieť pred ďalším otvorením alebo QA.

Na tomto Macu sú explicitné existujúce cesty:

```sh
cd /Users/davidzita/www/dom
BREZI_ENGINE=/Users/davidzita/www/dom/output/unreal/caustics-active-study/candidate/UE_5.8
BREZI_PROJECT="$BREZI_ENGINE/.brezi-managed/active/Project/BreziTwin"
BREZI_RUNS="$BREZI_ENGINE/.brezi-managed/promotion-$(date +%Y%m%dT%H%M%S)"
BREZI_TOOLS=/Users/davidzita/www/dom/output/unreal/caustics-delivery/promotion-adoption/current-toolchain.json
BREZI_TOOLS_SHA=416937267f772e65d0fef17fc63e39fc034a5ebc66d0c443d2629aba71ad0660
BREZI_PHASE_ARGS=(--engine "$BREZI_ENGINE" --project "$BREZI_PROJECT" --run-root "$BREZI_RUNS" --toolchain-pins "$BREZI_TOOLS" --toolchain-sha256 "$BREZI_TOOLS_SHA")

python3 -B scripts/unreal/engine-overlays/ue-5.8.2-floor-caustics/verify_engine.py --engine "$BREZI_ENGINE" --state result
python3 -B scripts/unreal/caustics/phase_runner.py source "${BREZI_PHASE_ARGS[@]}" \
  --engine-manifest scripts/unreal/engine-overlays/ue-5.8.2-floor-caustics/manifest.json --output "$BREZI_RUNS/source.json"
python3 -B scripts/unreal/caustics/phase_runner.py plan editor-graph --attempt promoted "${BREZI_PHASE_ARGS[@]}" \
  --source-closure "$BREZI_RUNS/source.json" --output "$BREZI_RUNS/editor-graph-plan.json"
BREZI_PLAN_SHA=$(python3 -c 'import hashlib,sys;print(hashlib.sha256(open(sys.argv[1],"rb").read()).hexdigest())' "$BREZI_RUNS/editor-graph-plan.json")
python3 -B scripts/unreal/caustics/phase_runner.py run --plan "$BREZI_RUNS/editor-graph-plan.json" --sha256 "$BREZI_PLAN_SHA" --check
```

Posledný príkaz je iba preflight; nezačne UBT. Rovnaký `run` bez `--check` vykoná konkrétny plán. Pred ďalším samostatným `editor-build` plánom treba skutočný graph review vedľa jeho `actions.json`; obdobne nasledujú `game-graph`, `game-build` a `accept_build.py editor|game`. Už up-to-date prázdny graf sa nesmie vydávať za nový dôkaz kompilácie provideru: nové API/build overenie potrebuje skutočné relevantné compile actions alebo samostatne schválené opätovné použitie predchádzajúceho buildu. Runner takéto opätovné použitie automaticky nevymýšľa.

`cook` a `archive` plán prijímajú `--accepted-editor`, `--accepted-game`; archive aj `--cook-receipt`. Pred cookom použite `cook_binding.py before` s novým plánovaným cook outputom a explicitným historickým Editor pair receiptom. Po archive nasleduje skutočný IoStore listing, `cook_binding.py seal`, potom `finalize_package.mjs`. Nový `cooked-runtime-binding.json` sa vkladá do app až počas pečatenia; nikdy nie do kanonického plugin Resources.

Presná gramatika a požadované receipt polia sú v [phased-runner.md](phased-runner.md). Vyššie uvedený toolchain receipt pripína aktuálne lokálne súbory; nie je prenosný bootstrap nového engine. Upravené managed UBT/AT assemblies, ich vytvorenie, nezávislý graph audit, história pôvodných raw dôkazov a automatické zapojenie všetkých fáz do `scripts/unreal/run.mjs` ešte vyžadujú dokončenie. Existujúce import/material/source gates sa nesmú pri tomto zapojení obísť.
