# Natívny povrch strechy — 2026-09-09

Štyri existujúce plochy `DOM_01483–01486 / MAT_0087` používajú hladký antracitový náter. Natívny materiál odstránil pôvodný 15 cm procedurálny albedo/normal vzor. Geometria, UV, falce aj zdieľaný `MAT_0014` zostali bez úprav. Porovnanie importov našlo jedinú zmenu z 57 vytvorených materiálových receptov.

Výkres `arch-docs/projektova dokumentace/D_Vykresova dokumentace/D1_ASR/D1.1.006_Pohledy.pdf`, legenda **5**, predpisuje plechovú krytinu RAL 7016. `D1.1.01_Technicka zprava.pdf`, fyzické strany 2 a 4, uvádza falcovanú krytinu a tento odtieň. Dokumentácia neurčuje BRDF ani lesk: roughness 0.52 je zachovaná autorská hodnota, metallic 0 modeluje nepriehľadný pigmentovaný povlak. Lineárna farba vychádza z existujúcej obrazovkovej aproximácie sRGB (56,62,66), nie z meranej RAL vzorky.

Natívny readback potvrdil tri konštantné uzly, nulový počet texture samples, Opaque / Default Lit / Nanite a presné priradenie štyroch mesh slotov. Hlavné zdroje 2D a Babylon modelu sa nemenili. Plný import znova overil nábytok, svietidlo, LawnGround a 33 769 inštancií LawnDetail.

## Reprodukcia a životnosť Zen

```sh
node scripts/unreal/run.mjs package
node output/unreal/foreground-study/capture-deck-terrace.mjs day
```

Packager teraz pred UAT spustí stock `ZenLaunch` s projektom a sponsor PID celého Node procesu. Tým služba zostane dostupná aj po ukončení cook commandletu, počas stagingu. Natívne overenie bežného príkazu prešlo bez ručného spustenia služby. Výstup je `output/unreal/package/Mac/BreziTwin.app`.

Pôvodný zaseknutý pokus je zachovaný v `output/unreal/roof-surface-adoption/zen-stall/`: Zen mal iba cook PID ako sponsora a skončil pred stagingom. Manuálne obnovenie služby poskytlo HTTP 200 pre oplog, ale starý UAT request sa neobnovil. Tento pokus nie je úspešný build.

## Overenie aktuálneho balíka

- Package receipt SHA-256: `523f3de32d2510509bee9c4ac0742d642032d2c48dfcef698f98b06f337f755d`.
- Natívny beh PID 84680 skončil s kódom 0; po 1 200 zahrievacích snímkach sa meralo 300 snímok. Všetky mali aktívnu aplikáciu, okno aj keyboard focus a natívny render 3840 × 2160.
- Priemer 50.877 ms, približne **19.66 fps**; p95 51.830 ms. Ide o jednu vzorku, nie o preukázaný kauzálny výkonový zisk ani splnenie požiadavky plynulého 4K.
- Všetkých 2 430 zdrojových/importných pinov a zabalený payload boli overené pred aj po behu.
- Dôkazy a obrázok: `output/unreal/runtime/foreground-terrace-day-eeef9842-2ba1-485d-b300-3598be05b2da/`.

`r.TSR.Support.LensDistortion=0` je ponechané pre aktuálne architektonické kamery. Natívna render percentáž 100 %, TSR history 200, Lumen, Nanite a virtuálne tiene sa tým nemenia. Diagnostické shader dump prepínače z experimentu boli odstránené. B0 preukázal 12 backend kompilácií UpdateHistory a odlišný environment key; spoločné cook porovnanie zostáva neúplné, pretože A1 nevytvoril CSV. Pôvodné zlyhania hostov sa zachovali v `output/unreal/tsr-lens-experiment/`.

Vizuálna kontrola potvrdila odstránenie zrnitého povrchu a zachovanie čitateľných falcov. Celkový fotorealizmus zostáva nedosiahnutý; trávnik a ornamentálna výsadba sú stále nápadne syntetické. Oheň sa podľa pokynu používateľa ďalej neladil.

## Zachovaná história adopcie

`output/unreal/roof-surface-adoption/before/` obsahuje pôvodné Content, skripty a receipty. Pred zmenou spoločného writeru prešli verejné restore funkcie FurnitureOak a Pendant pod pôvodnými pinmi. Nový immutable furniture snapshot mení iba pin writeru; historický snapshot zostáva zachovaný. Opravený package gate vyžaduje nový `roof-surface-transfer-v3` podklad. Existujúcich 20 testov gate a kontrola skutočného import receipt prešli.
