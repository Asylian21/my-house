# Unreal — materiály a modelové detaily C/B/B, 23. 9. 2026

Samostatný profil `output/unreal/photoreal-20260923-r3` vychádza z aktuálneho
hlavného návrhu C/B/B vrátane otvoreného zakončenia kuchyne z 22. septembra.
Predchádzajúce aplikácie, geometria a historické varianty zostávajú zachované.
Osadenie domu ani projektové rozmery sa týmto materiálovým návrhom nemenia.

Aktuálny balík otvorí `npm run unreal:open -- terrace`; na tento materiálový základ
nadväzuje [samostatná revízia trávnika dvora](unreal-lawn.md).
[Galéria deviatich natívnych 4K záberov](../output/unreal/photoreal-20260923-r3/PREZENTACIA.md)
obsahuje terasu, oba pohľady obývačky, detaily a kontrolné porovnania skla.

## Povrchy a detaily

- Fasáda, drevené podbitie a terasa: fotografické CC0 sady Hinoki Planks a
  Wood Planks, osem máp 4096 × 4096 (Albedo, Normal, Roughness, AO). Spoločný
  teplý prírodný tón, fyzická mierka, smer vlákien podľa dielu a deterministické
  striedanie výrezov. Druh dreviny je vizuálny návrh; nie je to identifikácia
  konkrétneho smrekovcového výrobku. Biele podhľady sa nepremaľujú na drevo.
- Dosky terasy si zachovávajú šírku **145 mm** a skutočné **8 mm medzery**.
  Kontrola všetkých 2 976 trojuholníkov dokladá, že náhodná fáza kresby
  nepreskočí uprostred dosky. Fasádne škáry sú materiálový detail na pôvodnom
  modeli; terasové škáry sú existujúca geometria.
- Antracitový plech: nepriehľadný dielektrický lak, roughness 0,33–0,42,
  jemná filtrovaná mikroštruktúra, skutočne zaoblené lišty/falce a ohýbané
  hrebene. Odtieň je návrhová aproximácia RAL 7016, nie meraná vzorka laku.
- Čalúnenie: fotografická jemná tkaná štruktúra Rough Linen, roughness a AO, fyzická plocha
  vzorky 27,071 × 27,13 cm a Cloth fuzz. Originály 4096 × 4105 sa v engine
  zostavia na 4096 × 4096 s mipmapami; shader zachováva fyzický pomer strán.
  Jemná farebná variácia rešpektuje existujúci svetlý poťah.
- Kamenné dosky: jemný matný odlesk a zachované pórové normály. Dubová dyha
  používa overený predchádzajúci 4K materiál; nábytkové hrany dostávajú bevel.
- Sklo: Thin Translucent, IOR 1,52 odvodený do Fresnel specular, jemne neutrálne
  zelená transmisia. Vonkajšia orientácia potláča duplicitné rubové plochy
  štítového skla. Predný odraz Lumen dopĺňa na 19 architektonických plochách
  samostatný obraz zadného rozhrania. Kamera sa zrkadlí na zadnej ploche
  pôvodnej 24 mm obálky; lineárny HDR obraz sa projektívne premieta na sklo
  s váhou `F × (1−F)² × tint^(2/NoV)`. Posuvné krídla odovzdávajú svoj
  aktuálny transform aj doplnkovému odrazu. Je to rovinná aproximácia prvého
  spätného odrazu, bez Snellovho bočného posunu a ďalších vnútorných odrazov;
  nejde o optický výpočet konkrétnej skladby izolačného skla. Sprchové sklo,
  voda v dreze ani sklo pece nedostávajú tento doplnok.
- Bazén: pôvodný mliečny alpha-blend nahrádza SingleLayerWater s IOR 1,333,
  hĺbkovou absorpciou, slabým rozptylom a 12 jemnými normálovými vlnkami.
  Hladina, rozmery a kolízie bazéna sa nemenia; táto verzia nepridáva kaustiky.

235 vizuálnych dielov zahŕňa 93 nábytkových bevelov, 27 čalúnených prvkov,
112 kovových detailov, 2 ohýbané hrebene a jeden mäkký bevel. Majú spolu
415 092 trojuholníkov. Prehnutie vankúšov je najviac 3,871 mm, rozšírenie
obálky pri šve najviac 0,845 mm. Pôvodné zdrojové mesh a ich pôvodný stav kolízií zostávajú zachované;
nové vizuálne diely nemajú kolíziu. Skryté
pôvodné plochy neprispievajú tieňmi ani nepriamym osvetlením.

## Svetlo a kamera

Lumen používa vyššiu kvalitu Final Gather a odrazov, detailnejšiu scénu a
predné odrazy transparentných plôch. Polohy a intenzita slnka aj polohy
svietidiel zostávajú odvodené z existujúcej scény. Zväčšenie slnečného
zdroja na 0,75° zjemňuje tieň. Nejde o fotometrické meranie stavby.
Navrhované doplnkové stropné svetlá obývačky majú 4 000 K a 70 % pôvodného
toku, čím sa potláča plošný jantárový nádych. Skutočné modelované kuchynské
a jedálenské svietidlá si zachovávajú pôvodné teploty a tok.

Zostáva filmický ACES transform Unreal Engine s neutrálnym vyvážením
5 500 K. Bloom, lens flare, chromatická aberácia, zrno, motion blur a
vignetácia sú vypnuté. Histogramová expozícia používa kamerový rozsah
EV100 −6 až 14 pre deň/noc. Prezentačné zábery sa zachytávajú po ustálení;
hlavná terasa, obývačka a kuchyňa majú vodorovnú kameru bez rollu,
teda zvislice zostávajú rovnobežné. Detail sedačky môže mať zámerný náklon.

## Reprodukcia a dôkazy

Hotové natívne zábery možno zopakovať bez úpravy balíka:

```sh
BREZI_MODEL_OUTPUT=output/unreal/photoreal-20260923-r3 node scripts/unreal/photoreal-capture.mjs terrace
BREZI_MODEL_OUTPUT=output/unreal/photoreal-20260923-r3 node scripts/unreal/photoreal-capture.mjs living
```

Novú iteráciu vytvorte v **novom prázdnom profile**. Nasledujúca cesta je príklad,
nie príkaz na prepísanie overeného výstupu. Dvojitý odraz vyžaduje nový natívny
helper a projektové global clip planes; engine samotný sa neupravuje.

```sh
export BREZI_MODEL_OUTPUT=output/unreal/photoreal-next
export BREZI_ARCHVIZ_GAME=1
export BREZI_DOUBLE_GLASS=1
npm run unreal:model -- prepare
npm run unreal:model -- export
npm run unreal:model -- editor-build
npm run unreal:model -- game-build
npm run unreal:model -- import
npm run unreal:model -- archviz
python3 scripts/unreal/photoreal-exterior-fetch.py
python3 scripts/unreal/fetch-photoreal-interior.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python scripts/unreal/photoreal-geometry.py -- --geometry "$BREZI_MODEL_OUTPUT/geometry" --output "$BREZI_MODEL_OUTPUT/photoreal-geometry"
npm run unreal:model -- photoreal
npm run unreal:model -- package
node scripts/unreal/photoreal-capture.mjs terrace
node scripts/unreal/photoreal-capture.mjs living
```

Materiálový krok vyžaduje čistý, už overený archviz profil. Nedá sa opakovať
na hotovom enhancement profile. Zachytený neúspešný pokus možno po skončení
natívneho procesu obnoviť cez
`python3 -B scripts/unreal/photoreal-import.py --restore <output>`.
Obnova porovná všetky aktuálne balíky s chybovým stavom, obnoví iba mapu
a odstráni iba nové vlastné assety. Staré pokusy zostávajú v histórii.

[Importný report](../output/unreal/photoreal-20260923-r3/photoreal-import-report.json)
dokladá úspešné uloženie/opätovné otvorenie 140 exteriérových a 85
interiérových väzieb, 235 vizuálnych dielov a 19 doplnkových odrazov. Pôvodné natívne assety zostali
byte-identické. Najväčšia chyba hraníc nových dielov pri natívnom načítaní
bola **0,00061 mm**; to je kontrola prevodu, nie geodetická presnosť.

[Balík](../output/unreal/photoreal-20260923-r3/model-package.json) má nový cook
a samostatnú aplikáciu. R3 má nový natívny Editor aj Game build
(38 vykonaných Game akcií), nové materiály a nový cook. Historické R1/R2
aplikácie zostávajú zachované.
Úspešný import ani cook sám nepotvrdzuje výtvarné prijatie alebo FPS.

Pôvodná regresná sada prešla: 540 Node a 141 Python testov. Nových 42 CPU
kontrol (`npm run unreal:photoreal:test`) prešlo a pokrýva mierku a orientáciu dreva, topológiu skla, materiálové
väzby, obálky detailov a bezpečnú obnovu po chybe.

Deväť skutočných Metal záberov má 3 840 × 2 160 pixelov, primárne rozlíšenie
100 % a TSR history 200 %. [Vizuálny protokol](../output/unreal/photoreal-20260923-r3/photoreal-visual-review.json)
spája každý obraz s hashom aplikácie a runtime kontrolou scény. Detail sedáka
ukazuje šev približne z 1,59 m; fasádny detail približne z 1,6 m. Jemnú tkaninu
treba posudzovať pri plnom rozlíšení, pretože zmenšenie náhľadu ju potláča.
Celodomová prechádzka nebola v tejto materiálovej revízii opakovaná.

R3 samostatne porovnáva druhý odraz zvonka aj zvnútra s prepínačom
`r.Brezi.DoubleGlass 0/1` pri totožnej kamere. Nejde o konštantný posun jednej
textúry: zrkadlená kamera sníma skutočnú scénu a projekcia závisí od hĺbky.
Jemný odraz protiľahlého okna a interiérových závesov sa objaví iba v zapnutom
porovnaní. Rozdielové obrazy sú diagnostické pomôcky; prezentačné PNG zostávajú
priame renderové výstupy bez retuše.

Doplnok používa 1 024 px HDR cieľ na viditeľnú plochu, po 16 ustáľovacích
snímkach ho pozastaví a obnoví pri zmene kamery alebo sledovaných transformov,
viditeľnosti, materiálov a farby/intenzity svetiel. Procedurálne zmeny parametrov
vyžadujú aktualizáciu `SceneRevision`. Skryté ciele
uvoľní po piatich sekundách. Testovaný je statický prezentačný režim;
plynulosť počas chôdze s aktívnymi viacerými scene captures sa tým nepotvrdzuje.
Priamy A/B test zachováva histogramovú expozíciu, takže drobné plošné rozdiely
jasu a pohyb vodných vlniek nie sú dôkazom druhého odrazu; rozhodujúce sú
samostatné odrazené kontúry na skle a runtime kontrola vrstvy.

V kontrolnom detaile skla zvonka zostáva pri ľavom okraji lokálny svetlý
zubatý pás viditeľný pri zapnutom aj vypnutom doplnku. Nie je dôkazom chyby
zadného odrazu, ale tento detail nemožno označiť za úplne bez artefaktov.

Zdroje: [Hinoki Planks](https://polyhaven.com/a/hinoki_planks),
[Wood Planks](https://polyhaven.com/a/wood_planks),
[Rough Linen](https://polyhaven.com/a/rough_linen),
[licencia CC0](https://polyhaven.com/license),
[Epic — Lumen](https://dev.epicgames.com/documentation/unreal-engine/lumen-global-illumination-and-reflections-in-unreal-engine),
[Epic — filmický tonemapper](https://dev.epicgames.com/documentation/unreal-engine/color-grading-and-the-filmic-tonemapper-in-unreal-engine).
