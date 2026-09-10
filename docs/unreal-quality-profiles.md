# Profily kvality natívnej aplikácie

Aktuálna [Retina revízia](unreal-retina-output.md) `abde8be8…` dosiahla v štyroch minútových denných orbit testoch **40,7–62,2 FPS** pri 3200 × 1800 a Plynulosti 50/100. Nastavenie profilu aj veľkosť okna boli uložené a obnovené pri bežnom štarte. Nižšie zostávajú historické dôkazy pôvodných profilov a pevných 4K balíkov.

Stav k 9. 9. 2026: **ovládanie a ukladanie profilov vo v2 sú natívne overené** v dokončenom balíku `3c71cc63…`. Čerstvé spustenie použilo Vyvážené 67/100; všetky tri voľby cez AX aj klávesnicu sa uložili s `saved=1` a relaunch obnovil Plynulosť 50/100. Dočasný pomenovaný profil nezmenil uloženú preferenciu; až vedomé kliknutie na už vybrané Vyvážené ju prepísalo. **Overené sú aj viditeľný raw QA lock, zachovanie preferencie v diagnostike a samostatné 4K výstupy pri 100/200 aj 50/100.** Priebežný stav a odkazy na balíky sú v [quality-ui-current.json](../output/unreal/quality-ui-current.json).

## Voľby v Ovládaní

Následná revízia terasy už používa nový balík `dd6cb6cb…`. Jej [samostatné delivery review](../output/unreal/deck-gap-study/delivery-review.json) potvrdzuje 4K výstup pri 67/100 aj 50/100, kontrolu státia a otvorené editovateľné menu s profilom Plynulosť. Krátke merania pri bazéne zaznamenali 26,0 a 36,1 FPS, vždy 240 snímok v popredí. Historické dôkazy všetkých kliknutí, klávesnice a perzistencie nižšie naďalej patria balíku v2; na novú revíziu sa nevydávajú za zopakované testy.

Panel **Ovládanie** (`F1`) obsahuje pod nadpisom sekciu **KVALITA OBRAZU** s tromi zvislými voľbami:

| Viditeľný názov | Krátky popis | Interné ScreenPercentage | TSR History.ScreenPercentage | Natívny názov profilu |
| --- | --- | ---: | ---: | --- |
| Natívny detail | Najjemnejšie detaily | 100 | 200 | `native` |
| Vyvážené | Rovnováha detailov a plynulosti | 67 | 100 | `balanced` |
| Plynulosť | Nižšie vnútorné rozlíšenie | 50 | 100 | `performance` |

V historických balíkoch v2 a revízie terasy zostával výstupný scene target **3840 × 2160** vo všetkých profiloch. Nová [Retina revízia](unreal-retina-output.md) oddeľuje profil TSR od veľkosti výstupu: bežný výstup sa prispôsobuje kresliacej ploche okna, explicitná voľba 4K zostáva dostupná. Vyvážené a Plynulosť používajú nižšie interné vzorkovanie. Percentá samy osebe nie sú meraním rozmerov interných render/history textúr ani dôkazom natívneho 100 % renderovania.

Voľba mení iba dve uvedené CVars. Pred zmenou musí byť aktívne TSR (`r.AntiAliasingMethod=4`), vypnutá dynamická rezolúcia a sekundárne percento 100. Inak sa voľba viditeľne zablokuje. Svetlá, HW Lumen, Nanite, VSM, materiály, geometria a kamera sa touto funkciou nemenia. Názvy profilov nesľubujú konkrétne FPS.

Zaškrtnutie sa odvodzuje zo skutočných hodnôt rendereru vrátane uvedených podmienok, nie iba z posledného kliknutia. Skupina povoľuje jednu voľbu; aj kliknutie na už zvolený profil je vedomou voľbou, ktorú možno uložiť. Názov a aktuálny stav sú dostupné cez AX. Poradie `Tab` je Zavrieť → tri profily → Obmedziť pohyb → nastavenie macOS. `Escape` vracia fokus na tlačidlo Ovládanie. Zmena profilu neprestavuje celý panel ani nemení pohľad kamery.

## Predvolené a uložené nastavenie

Pri bežnom prvom spustení bez platnej uloženej voľby alebo explicitného parametra sa použije **Vyvážené 67/100**. Predvolená hodnota sa sama neukladá. Platná predchádzajúca vedomá voľba má pri ďalšom bežnom spustení prednosť.

Až úspešná používateľská voľba zapisuje `ProfileV1=native|balanced|performance` do vlastnej sekcie `[Brezi.RenderQuality]` v `GGameUserSettingsIni` daného používateľa/UserDir. Po `Flush` sa výsledok nezávisle číta zo skutočného súboru. Pri chybe zápisu UI oznámi, že voľba platí pre reláciu a uloženie sa nepodarilo. Zdrojové INI projektu sa nemenia.

Natívny argument `-BreziRenderProfile=native|balanced|performance` vyberá **dočasný počiatočný profil**. Neprepíše uloženú preferenciu. Používateľ môže následne zvoliť ľubovoľný profil v paneli; táto vedomá voľba sa už uloží, aj keď zodpovedá práve aktívnemu dočasnému profilu. Neplatný pomenovaný profil sa viditeľne odmietne.

Raw renderer argumenty (`ExecCmds`, relevantné `-ini` alebo iné explicitné CVar argumenty) a existujúce QA/diagnostické režimy majú prednosť pred uloženou aj predvolenou voľbou. Profilový kód vtedy nič neaplikuje ani neukladá a panel vysvetlí dočasné uzamknutie. Tým ostávajú zachované študijné hodnoty aj pôvodný QA základ 100/200 z konfigurácie balíka. Kontrola argumentov prebehne už pred prvým vykonaním deferred `ExecCmds`; samotná aktuálna CVar priorita v `BeginPlay` by nestačila. Bežné používateľské voľby používajú `ECVF_SetByGameOverride`, pod prioritou CLI/konzoly.

Samotný `-BreziTraceControlKeys` profil neuzamyká. Je určený aj na natívne manuálne overenie: stručný `BreziRenderQuality` záznam obsahuje požiadavku, pôvod, skutočné percentá pred/po, prioritu a výsledok uloženia, najviac 24 udalostí. Na skúšku editovateľného menu sa nemajú pridávať benchmark/capture QA argumenty, ktoré ho zámerne uzamknú.

## Udržiavaný príkazový riadok

Nasledujúci vzor vyžaduje **skutočný dokončený package report a jeho overený SHA-256**. Zástupné hodnoty nahraďte cestou a hashom konkrétneho overeného balíka; výsledky nižšie sa vzťahujú na uvedený v2 balík.

```sh
cd /Users/davidzita/www/dom
PACKAGE_REPORT=/absolute/path/to/validated/package.json
PACKAGE_REPORT_SHA256=REPLACE_WITH_THE_VALIDATED_64_CHARACTER_SHA256

# Len overenie vybraného balíka, receiptov, payloadu, entry a podpisu; bez spustenia app.
BREZI_PACKAGE_REPORT="$PACKAGE_REPORT" BREZI_PACKAGE_REPORT_SHA256="$PACKAGE_REPORT_SHA256" \
  node scripts/unreal/run.mjs package-check

# Bez explicitného profilu: nový podporovaný balík obnoví uloženú voľbu alebo použije 67/100.
env -u BREZI_RENDER_PROFILE BREZI_PACKAGE_REPORT="$PACKAGE_REPORT" BREZI_PACKAGE_REPORT_SHA256="$PACKAGE_REPORT_SHA256" \
  npm run unreal:open -- pool

# Dočasný profil pre toto spustenie; v novom podporovanom balíku zostáva menu editovateľné.
BREZI_PACKAGE_REPORT="$PACKAGE_REPORT" BREZI_PACKAGE_REPORT_SHA256="$PACKAGE_REPORT_SHA256" \
  BREZI_RENDER_PROFILE=tsr67 npm run unreal:open -- pool
```

Udržiavané názvy prostredia sú `native`, `tsr67`, `tsr50`. Pri balíku s overeným `renderProfileInterface.schemaVersion=1` ich resolver preloží na `-BreziRenderProfile=native`, `balanced`, `performance`. Nezadaná premenná neposiela žiadny profilový argument. Schopnosť musí byť doložená source closure so štyrmi konkrétnymi súbormi: policy header, implementácia profilov a Controller `.h/.cpp`.

Starší balík bez tejto schopnosti naďalej používa pôvodný raw `ExecCmds` pre `tsr67`/`tsr50`; nový native parameter sa doň neposiela. Bez explicitnej cesty a SHA zostáva pôvodný legacy package report. `unreal:qa` a `unreal:qa-ui` neprijímajú škálovaný `BREZI_RENDER_PROFILE`, pretože ich existujúce vyhodnotenie vyžaduje 100 %. Škálované merania a motion skúšky používajú svoje samostatné overenia.

## Natívne dôkazy a rozsah overenia

[Overený v2 package report](../output/unreal/caustics-active-study/candidate/UE_5.8/.brezi-managed/quality-ui-v2-a039cb4c3cc34241ac1c3e3f2cde35e9/runs/reviews/package.json) má SHA-256 `3c71cc632c87279cd54a7793407675329c4f73566c25614d978423a7bab0f5e8`. [Záverečné review](../output/unreal/native-quality-profiles/actual-ui-v2-7bed3f8992e942c080e3cf6937e5d5f1/review.json) potvrdzuje všetky uvedené assertions. [UI relácia](../output/unreal/native-quality-profiles/actual-ui-v2-7bed3f8992e942c080e3cf6937e5d5f1/session.json) viaže skutočné behy na tento balík a rovnaký UserDir:

- [Čerstvé spustenie](../output/unreal/native-quality-profiles/actual-ui-v2-7bed3f8992e942c080e3cf6937e5d5f1/fresh/result.json), PID **93426 / exit 0**: predvolené 67/100; všetky tri AX a klávesnicové voľby dosiahli presné percentá so **`saved=1`**. Zachované sú AX stavy vrátane [klávesnicovej voľby](../output/unreal/native-quality-profiles/actual-ui-v2-7bed3f8992e942c080e3cf6937e5d5f1/fresh/ax-keyboard-performance.txt) a [skutočný uložený INI](../output/unreal/native-quality-profiles/actual-ui-v2-7bed3f8992e942c080e3cf6937e5d5f1/fresh/GameUserSettings-after.ini).
- [Obnovenie uloženej voľby](../output/unreal/native-quality-profiles/actual-ui-v2-7bed3f8992e942c080e3cf6937e5d5f1/saved/result.json), PID **96332 / exit 0**: `origin=1` obnovilo **50/100**; [AX stav](../output/unreal/native-quality-profiles/actual-ui-v2-7bed3f8992e942c080e3cf6937e5d5f1/saved/ax-restored.txt) potvrdil vybranú Plynulosť.
- [Pomenovaný dočasný profil](../output/unreal/native-quality-profiles/actual-ui-v2-7bed3f8992e942c080e3cf6937e5d5f1/named/result.json), PID **97512 / exit 0**: `-BreziRenderProfile=balanced` použil **67/100**, pričom [INI pred kliknutím](../output/unreal/native-quality-profiles/actual-ui-v2-7bed3f8992e942c080e3cf6937e5d5f1/named/GameUserSettings-before-click.ini) stále obsahoval `performance`. Vedomé kliknutie na už vybrané Vyvážené skončilo **`saved=1`** a [INI po kliknutí](../output/unreal/native-quality-profiles/actual-ui-v2-7bed3f8992e942c080e3cf6937e5d5f1/named/GameUserSettings-after-click.ini) obsahoval `balanced`.

Samostatné kontroly uzamknutia a výstupu sú tiež dokončené:

- [Raw renderer override](../output/unreal/native-quality-profiles/actual-ui-v2-7bed3f8992e942c080e3cf6937e5d5f1/raw/result.json), PID **98921 / exit 0**: [AX strom](../output/unreal/native-quality-profiles/actual-ui-v2-7bed3f8992e942c080e3cf6937e5d5f1/raw/ax-locked.txt) má všetky tri profilové voľby zablokované a uvádza dôvod. Fyzicky uložené `balanced` sa nezmenilo.
- [Natívny QA beh](../output/unreal/native-quality-profiles/actual-ui-v2-7bed3f8992e942c080e3cf6937e5d5f1/qa/result.json), PID **962 / exit 0**: diagnostika ignorovala uložené Vyvážené a zachovala **100/200**. [PNG](../output/unreal/native-quality-profiles/actual-ui-v2-7bed3f8992e942c080e3cf6937e5d5f1/qa/capture.png) má **3840 × 2160**; [runtime](../output/unreal/native-quality-profiles/actual-ui-v2-7bed3f8992e942c080e3cf6937e5d5f1/qa/runtime.json) potvrdzuje stabilný samostatný 4K RHI target počas 240 sledovaných snímok. Prešiel udržiavaný `inspectPresentation`.
- [Škálovaný QA beh](../output/unreal/native-quality-profiles/actual-ui-v2-7bed3f8992e942c080e3cf6937e5d5f1/qa50/result.json), PID **2240 / exit 0**: skutočné hodnoty **50/100**, [PNG](../output/unreal/native-quality-profiles/actual-ui-v2-7bed3f8992e942c080e3cf6937e5d5f1/qa50/capture.png) **3840 × 2160** a [runtime](../output/unreal/native-quality-profiles/actual-ui-v2-7bed3f8992e942c080e3cf6937e5d5f1/qa50/runtime.json) so stabilným 4K RHI targetom počas 240 sledovaných snímok. Samostatná validácia rešpektuje rekonštruovaný 4K výstup; neprehlasuje ho za 100 % interný render ani za úspech pôvodného native-sampling kritéria.

Oba QA zábery majú rovnakú klientsku veľkosť okna **1600 × 900**. Profil bol v diagnostike uzamknutý, bez ukladania a bez zmeny preferencie. Všetkých šesť behov skončilo s exit 0 a zachovalo balík. Tieto dôkazy potvrdzujú UI, perzistenciu, izoláciu QA a rozmery výstupu; **nepredstavujú nové meranie FPS, fyzický 4K monitor ani úplnú časovú obrazovú zhodu profilov**.

[Samostatné policy kontroly](../output/unreal/native-quality-profiles/source-check-14b441efc64347e987647bd3c7fd6ed3/report.json) zachytávajú 56 úspešných C++ kontrol v bežnom aj optimalizovanom `-O2 -DNDEBUG` režime: presné profily, prioritu, QA/CLI izoláciu a model uloženia. Skutočné diskové ukladanie a UI potvrdzujú až uvedené v2 behy.

História v1 ostáva zachovaná: [build a package kontext](../output/unreal/caustics-active-study/candidate/UE_5.8/.brezi-managed/quality-ui-ee5fbe36e6dd4d77b7e30a7b3355b536/session-context.json) obsahuje Editor **11800**, Game **34195**, cook **45734** a archive **46819**, všetky exit 0/drained; balík `27f34890…` mal 45 súborov. [UI review v1](../output/unreal/native-quality-profiles/actual-ui-eb68f5a4626147ad89ab8941950b5370/review.json) doložilo kliknutia a obnovenie 50/100 (PID **52134**, **59802**, oba exit 0), ale aj nesprávne hlásenie chyby uloženia. [Minimálna oprava](../output/unreal/native-quality-profiles/persistence-fix01/report.json) používa skutočný `FConfigBranch::IniPath` namiesto cache kľúča `GGameUserSettingsIni`; jej správne potvrdenie je už overené vo v2. Pôvodné dôkazy sa neprepisovali.

[Predchádzajúca upscaling štúdia](../output/unreal/caustics-delivery/upscale-study/summary.json) patrí staršiemu balíku so SHA začínajúcim `73b9d1d8`. Obsahuje konkrétne runtime merania, vyradené focus-failed behy a 64-snímkové motion artefakty. Nie je novým meraním tejto UI implementácie ani všeobecným prísľubom výkonu. Tento dokument nepreberá čísla FPS do novej akceptácie.

Vlastník implementácie: [BreziRenderQualityPolicy.h](../unreal/BreziTwin/Source/BreziTwin/BreziRenderQualityPolicy.h), [BreziRenderQuality.cpp](../unreal/BreziTwin/Source/BreziTwin/BreziRenderQuality.cpp) a [BreziPlayerController.cpp](../unreal/BreziTwin/Source/BreziTwin/BreziPlayerController.cpp). Uvedené overenia profilového UI sú dokončené v rozsahu záverečného review. Tento dokument nevydáva staršie FPS za výkon v2 ani nepotvrdzuje celkový fotorealizmus a cieľovú plynulosť aplikácie.
