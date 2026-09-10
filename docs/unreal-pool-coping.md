# Lem bazéna — 9. september 2026

Táto iterácia pridáva jemnú minerálnu kresbu na 28 existujúcich porcelánových dosiek lemu bazéna. Materiál je prijatý ako lokálne zlepšenie po blízkom aj celkovom natívnom 4K zábere; zdrojový model ani rozmery dosiek sa nemenia.

Rozsah je presne `DOM_01726` až `DOM_01753`, spolu 336 zdrojových trojuholníkov. Pôvodný materiál `MAT_0102 / real-stone` používa aj štvorica nášľapných dosiek `DOM_01817` až `DOM_01820`; tá zostáva mimo úpravy. Dosky lemu majú hrúbku 55 mm, rovné hrany bez geometrického zaoblenia a približne 8 mm škáry medzi dielmi radov. Nový materiál nepridáva ďalšie namaľované škáry ani displacement.

Použité sú pôvodné 4096 × 4096 mapy Color, NormalGL a Roughness z [ambientCG Granite002A](https://ambientcg.com/a/Granite002A), publikované pod [CC0](https://docs.ambientcg.com/license/). Ide o procedurálny vzor, nie o sken alebo doložený výrobok pre tento dom. Poskytovateľ neuvádza fyzické rozmery: opakovanie po 500 mm, kamenný vzhľad porcelánu, farebné stlmenie aj matný remap sú výslovne autorské rozhodnutia.

Vstupné JPG sú skopírované bez úpravy pixelov. Import preklopí zelený kanál OpenGL normály presne raz. Pôvodná roughness mapa má priemer 0,02273521 a leštený vzhľad; shader ju remapuje okolo zdrojovej hodnoty 0,9. Farebná kresba má váhu 35 %, normálový detail 25 %. Farebná konštanta vychádza zo sRGB interpretácie zdrojového odtieňa `#d6d2c6`; nejde o preukázanú opravu farebnej chyby pôvodného materiálu ani o meranú BRDF.

Každá z troch máp má jeden texture sample. Shader zvolí znamienkovú projekciu podľa jednej zo šiestich rovných stien zdrojových boxov, so spoločnou svetovou mierkou pre horné aj bočné plochy. Pôvodné UV0 sa nemenia. Skript kontroluje zhodu zdrojovej geometrie a UV po importe, povolené väzby materiálu aj zachovanie ostatnej scény vrátane 33 769 trávnych inštancií. Vlastný materiál a tri textúry sa ukladajú do adresára podľa hashu receptu a pred aktiváciou aj po nej sa uvoľnia z pamäte a opäť načítajú. Overenie grafu samo osebe nepreukazuje vizuálnu kvalitu ani rezidentné mip úrovne počas renderovania.

Predvolený úplný import používa novú vrstvu; `BREZI_APPLY_POOL_COPING=0` ponechá po importe pôvodné väzby a overí ich uloženie a načítanie. `restore_pool_coping` umožňuje obnoviť vlastné aktívne overrides. Cudzie alebo nezodpovedajúce overrides sa odmietnu pred prepisovaním mapy.

## Podklad pred úpravou

Záber `output/unreal/runtime/foreground-pool-day-56fd5946-0276-4ef6-a73d-3bfa3c0ae6b4/capture.png` vznikol zo samostatnej aplikácie, PID 20198, exit 0. Po 1200 zahrievacích snímkach nasledovalo 300 meraných snímok; aplikácia a okno zostali aktívne vo všetkých vzorkách. Scéna aj jej RHI textúra mali natívnych 3840 × 2160 pixelov. To nedokazuje fyzický 4K displej ani 4K backbuffer okna.

Priemerný interval bol 68,801 ms, teda 14,53 fps; P95 78,702 ms. Je to jedno meranie blízkeho pohľadu na bazén, nie dôkaz plynulého 4K výkonu. Originálny 4K PNG bol prezretý cez nástrojový náhľad; zobrazenie v konverzácii ho zmenšilo na 2048 × 1152. Zhodovalo sa všetkých 2459 odkazov na vstupné hashe, teda 2447 rôznych súborov, aj obsah aplikácie.

Recept a pôvod máp: `scripts/unreal/pool-coping/inputs.json`. Priebežné dôkazy: `output/unreal/pool-coping-study/`. Oheň sa v tejto iterácii nemení.

## Natívne overenie kandidáta

Prešlo 11 Python testov, 29 testov kontroly materiálového reportu a 14 existujúcich testov balenia. Úplný import skončil s exit 0. Jeho skutočný report potvrdil obe uloženia a načítania mapy, neprítomnosť štyroch vlastných assetov v pamäti pred reloadom, zhodu uloženého grafu a ochranu 2077 existujúcich assetov. Následný BuildCookRun prešiel za 80,18 s.

Aktuálny recept: `632a5aba14ddad1711fb55568707b82458f7fab1ef43af169ed80c803c126cac`. Report importu je zachovaný ako `output/unreal/pool-coping-study/import-01-report.json`, report balenia ako `package-01-report.json`. Samostatná aplikácia: `output/unreal/package/Mac/BreziTwin.app`.

Prvý natívny záber kandidáta `foreground-pool-day-4c3a823c-56c1-4c48-b649-6b96300d1440` prešiel s exit 0 (PID 26441). Po 1200 zahrievacích a 300 meraných snímkach mal priemerný interval 68,991 ms, teda **14,49 fps**, P95 79,231 ms. Všetkých 300 vzoriek malo aktívnu aplikáciu a okno, scéna aj RHI textúra zostali natívne 4K. Porovnanie jedného merania pred a po nepreukazuje zmenu výkonu. Po skončení procesu sa zhodovalo všetkých 2475 odkazov na vstupné hashe, teda 2462 rôznych súborov; obsah `.app` overil helper pred spustením aj po skončení.

V porovnaných náhľadoch originálnych 4K PNG je jemná minerálna kresba viditeľná najmä na blízkom ľavom a pravom páse. Lem zostáva svetlý a matný, so zachovaným delením dosiek. Nezávislá kontrola odporučila materiál ponechať bez ďalšieho zosilnenia.

Celkový záber terasy `foreground-terrace-day-6b15ffce-1a50-4e78-879b-9db229eeb31f` tiež prešiel s exit 0 (PID 27591), 1200 zahrievacími a 300 meranými snímkami, plným fokusom a natívnou 4K scénou aj RHI textúrou. Priemer bol 53,316 ms (**18,76 fps**), P95 61,560 ms. Lem ostáva z diaľky nenápadný; v náhľade nevidno nové výrazné opakovanie textúry alebo lesklé fľaky. Zdrojová omietka zostáva vizuálne zhodná s obnoveným stavom bez predchádzajúcich horných pravých obdĺžnikových škvŕn. Znovu sa zhodovala celá vstupná hashová uzávierka aj obsah aplikácie.

Prijatie sa týka iba povrchu lemu v týchto statických pohľadoch. Ostré hrany dosiek, celková fotorealistická kvalita, správanie v pohybe a plynulý 4K výkon zostávajú otvorené.

Samostatný diagnostický beh rovnakého balíka `water-gbuffer-pool-day-f71348ad-a6f6-4547-8d67-e9f7978b4f4a` skončil s exit 0 a znovu overil natívny 4K bazén (14,91 fps, P95 75,499 ms). Iba čítal `r.GBufferFormat`; natívny súborový log potvrdil hodnotu `1`, `LastSetBy: Constructor`. Štandardný stdout obsahoval len ozvenu príkazu, preto dôkaz používa pôvodný súborový log. Toto nie je priama kontrola GPU formátu ani zmena vody; podklad pre ďalšiu iteráciu je v `output/unreal/water-precision-study/query-01-verification.json`.

Nasledujúci test vyššej presnosti bol zamietnutý a pôvodná konfigurácia obnovená. Aktuálna aplikácia zachováva tento prijatý lem; všetky natívne zdrojové súbory a vstupy importu sú zhodné s balíkom tejto materiálovej iterácie. Nové natívne overenie obnovy dosiahlo 14,85 fps pri bazéne, potvrdilo nastavenie `1` a skončilo s exit 0. Aktuálny receipt a záber uvádza [záznam presnosti vody](unreal-water-normal-precision.md).
