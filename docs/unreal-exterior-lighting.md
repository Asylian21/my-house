# Vonkajšie osvetlenie Březí 6012/26

Svetelný návrh používa presne dve existujúce svietidlá štítu a tri podvodné svietidlá. Ich geometria je spoločná pre webový model a export do Unreal Engine. Polohy sú v lokálnych osiach pôdorysu; Z je výška v milimetroch.

Výkon, teplota svetla, vyžarovacie uhly a dosah sú autorský návrh pre vizualizáciu. Nejde o údaje výrobcu, elektroprojekt ani potvrdený stav realizácie. Zdrojom je `lib/twin-exterior-lighting.ts`; základná geometria domu a bazéna vychádza z aktívneho domu a `twin-site.ts`.

| Svietidlo | Stred telesa X / Y / Z [mm] | Menovitý vstup [lm] | Teplota [K] | Vonkajší polovičný uhol | Smer |
| --- | --- | ---: | ---: | ---: | --- |
| EXT-TERRACE-WALL-01 | 22600 / 19610 / 3935 | 300 | 2700 | 40° | Nadol |
| EXT-TERRACE-WALL-02 | 26400 / 19610 / 3935 | 300 | 2700 | 40° | Nadol |
| EXT-POOL-WALL-01 | 13590 / 16092 / -652 | 400 | 4000 | 55° | Dovnútra bazéna |
| EXT-POOL-WALL-02 | 14740 / 16092 / -652 | 400 | 4000 | 55° | Dovnútra bazéna |
| EXT-POOL-WALL-03 | 15890 / 16092 / -652 | 400 | 4000 | 55° | Dovnútra bazéna |

Natívne svetlá používajú inverzný kvadratický útlm, lumeny a tiene. Svetelný zdroj je umiestnený tesne pred existujúcim telesom s rezervou pre polomer zdroja; nemení sa tým geometrická poloha svietidla. Denný stav má nulový výkon, nočný stav menovitý výkon. Prechod používa rovnakú trojsekundovú animáciu ako slnko a obloha.

Bežné bodové osvetlenie pod hladinou nepotvrdzuje fyzikálne správny prenos každého podvodného lúča, rozptyl ani podvodné kaustiky. Vizuálny výsledok a náklady na GPU sa posudzujú samostatne v natívnom obraze.

Stav k 9. 9. 2026: nový natívny kandidát `a77f76aa…` je zostavený, zapečatený a päťkrát zachytený. Export zachoval geometriu OBJ, materiálový MTL a kolíznu geometriu bajtovo zhodné s poslednou dodanou verziou. Všetky štyri pohybové a jeden statický beh však stratili fokus; nové FPS ani plynulosť preto nie sú prijaté. Posledný predvolený dodaný balík s platným výkonnostným overením zostáva `a445eb50…`.

Runtime zábery majú výstup 3200×1800 pri SP50 a TSR history 100. Dve 60-sekundové merania mali 2084/3879 a 2041/3524 vzoriek v popredí; dve nové 24-sekundové merania mali 975/1539 a 497/1417. Statická terasa mala 294/300. Procesy skončili čisto, ale tieto pomery nevyhovujú nezmenenej požiadavke na fokus počas všetkých meraných intervalov. Diagnostické časy sa nesmú prezentovať ako platné FPS. Skrátenie bolo zvolené pred novými zábermi; pôvodné zlyhania zostali zachované.

Skutočné čítanie piatich svetelných komponentov potvrdilo zdrojové dáta a nočný koncový stav na hernom vlákne. Nepotvrdzuje fyzikálny svetelný tok ani podvodný transport. Autentické nočné zábery zlepšili čitateľnosť terasy a fasády, ale takmer súvislý žiarivo biely lem a prevažne čierna voda vyžadujú ďalšiu prácu. Fotorealizmus nie je prijatý.

Podrobný [runtime review](../output/unreal/exterior-lighting-study/runtime-review.md) obsahuje všetkých päť odmietnutých behov; [JSON dôkazy](../output/unreal/exterior-lighting-study/runtime-review.json) obsahujú presné cesty, počty, časy, obmedzenia a overené SHA256. Táto dokumentácia nemení globálne ukazovatele balíka.
