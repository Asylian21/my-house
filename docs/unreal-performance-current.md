# Výkon aktuálnej dvanásťvlnovej scény — 9. september 2026

Aktuálny balík zostáva `14f8021d9592dd1ac56890bea16ee9abf130813391de8754ce6543c0594ff5e7`. Predchádzajúca iterácia bola pokrok: zmenila zdroj vody, overila uložený natívny graf, zostavila aplikáciu a prijala lokálne zlepšenie obrazu. Táto iterácia skúma výkon bez zmeny geometrie, materiálov alebo ohňa.

## Aktuálny profil

Proces 42521 skončil s exit 0. Profil `output/unreal/runtime/profile-split-encoder-terrace-day-143069c0-bfd6-4174-8cfe-ecf7b1b39e0c/` prešiel kontrolou balíka a neskorších 300 aktívnych natívnych 4K vzoriek. Rozdelenie Metal compute encoderov ovplyvňuje plánovanie; profil nie je produkčným meraním výkonu. Fokus a rozmery cieľa samotnej profilovanej snímky 600 nemajú samostatnú párovanú kontrolu.

| Samostatne priradená skupina | Čas v profilovanej snímke |
| --- | ---: |
| TSR RejectShading, Wave32 / 16 bit | 7,027 ms |
| TSR UpdateHistory, 7680 × 4320 | 3,872 ms |
| Ray tracing priesvitného svetelného objemu | 2,863 ms |
| Projekcia virtuálneho tieňa slnka | 2,391 ms |
| Lumen TraceScreen | 2,374 ms |
| BasePassParallel | 2,047 ms |

Nesčítavajú sa vnorené a rodičovské udalosti. Profil nepotvrdil samostatnú duplicitnú scénu; skryté kolízie nevstupujú do tieňov ani ray tracingu a vegetácia už používa dávky inštancií. Existujúce Wave32 a 16-bit cesty sú aktívne. Podrobnosti a presné zdrojové odkazy: `output/unreal/performance-next-study/twelve-wave-current-cost-review.md`.

## Energetický režim Macu

Mac bol na adaptéri, batéria 100 %, oba režimy Automaticky. `pmset` nehlásil zaznamenané teplotné ani výkonové varovanie; to nie je úplná telemetria teploty alebo taktov. Adaptér hlásil 94 W. Apple uvádza podporu vysokého výkonu pre M5 Pro a pre 14-palcový model odporúča 96 W adaptér pri nabíjaní: [Apple Support](https://support.apple.com/en-ie/101613).

Výber Vysoký výkon pre adaptér v Nastaveniach systému vyvolal požiadavku PowerPreferences na Touch ID alebo heslo. Zmena sa neuplatnila: `pmset` zostal na `powermode 0` a System Information hlásilo `HighPowerMode: No`. Požiadavka bola zrušená a UI znovu zobrazilo Automaticky pre batériu aj adaptér.

Prvý automatický beh 43630 prešiel s exit 0 (76,139 ms). Druhý beh 44024, nesprávne pomenovaný v pracovnom logu ako high-b1, tiež prešiel (73,142 ms), ale stále používal Automaticky. **Neexistuje platný High-vs-Automatic výsledok ani preukázané zrýchlenie.** Oba pôvodné záznamy zostávajú zachované a druhý je explicitne vyradený z tohto porovnania v `output/unreal/power-mode-study/status.json`. Netreba opakovať tento pokus bez skutočne potvrdenej zmeny režimu.

## Samostatná cesta osvetlenia priesvitných materiálov

`r.Lumen.TranslucencyVolume.TraceFromVolume=0` je odlišné od plošného vypnutia `Enable`. Zachováva interpoláciu radiance cache, filtre, históriu aj produkciu odrazov, ale vynechá lokálne trasovanie z objemu. Mení tiež parameter začiatku lúčov samostatnej cache; výsledné osvetlenie preto nemusí byť zhodné. Ide o kandidáta na vizuálny a výkonový test, nie o dokázané odstránenie nepotrebnej práce.

Scéna má aj 26 záclon, hadicu a hladinu drezu s pôvodnými Blend materiálmi a nenulovou zdrojovou farbou. Nemožno ju posudzovať ako súbor výhradne čírych skiel s nulovým difúznym príspevkom. Účinné parametre a odstránenie lookupov kompilátorom zatiaľ nie sú úplne preukázané.

## Výsledok natívneho porovnania — kandidát neprijatý

| Interiér, deň, rovnaký balík | Pôvodné trasovanie | Interpolácia cache |
| --- | ---: | ---: |
| TraceFromVolume | 1 | 0 |
| PID / exit | 46622 / 0 | 46952 / 0 |
| Priemer snímky | 67,901 ms | 69,332 ms |
| P95 snímky | 84,877 ms | 80,376 ms |
| Priemer GPU podľa RHI | 67,209 ms | 68,627 ms |

Oba platné behy prešli 1200 zahrievacími a 300 meranými snímkami, pričom všetkých 300 malo aktívnu aplikáciu aj okno a natívne 4K ciele. Trojica `Enable=1`, `RadianceCache=1`, `TraceFromVolume=1/0` bola prečítaná z pôvodných natívnych súborových logov s `LastSetBy: Console`. Zhodujú sa zdroje, balík, helper, zaznamenané nastavenia kvality aj poloha kamery v režime chôdze. Rozdiel zaznamenanej expozície bol −0,02273 EV; fázy materiálov nie sú synchronizované.

Root prezrel oba pôvodné 4K PNG cez nástrojové zobrazenie 2048 × 1152 a nevidel výrazný rozdiel celého záberu. Nezávislý reviewer tiež nevidel veľkú regresiu, ale záclony v alternatíve pôsobia mierne sivšie a menej teplo; úplnú zhodu osvetlenia nepotvrdzuje. Samostatný záznam s hashmi obrázkov: `output/unreal/tlv-trace-study/visual-review.json`. Toto nepokrýva všetky priehľadné materiály, pohyb alebo detail 1:1. **Jediná platná dvojica nepreukázala praktický výkonový zisk, preto sa kandidát neprijíma.** Nejde o dôkaz kauzálneho spomalenia vo všeobecnosti; P95 a priemer sa menili rôznym smerom a teplotný či časový drift nie je eliminovaný. Produkčný zdroj, konfigurácia aj obsah `.app` zostali nezmenené. Ďalšie rovnaké behy bez nového podkladu nie sú naplánované.

Zachované sú aj dva odmietnuté pokusy: prvý mal 0/300 aktívnych snímok; druhý mal 300/300 aktívnych snímok, ale počas aktivácie sa prepol na orbit. Do porovnania nevstupujú. Následné platné behy aktivoval jediný Escape počas warmup; podľa zdroja controlleru nemení pohľad ani režim chôdze. Všetky štyri natívne procesy skončili s exit 0. Podrobnosti: `output/unreal/tlv-trace-study/comparison.json` a `excluded-runs.json`.
