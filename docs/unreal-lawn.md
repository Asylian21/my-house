# Unreal — krátky trávnik okolo dvora

Samostatná revízia `output/unreal/lawn-archviz-20260923-r3` nadväzuje na
schválený materiálový profil R3. Zachováva jeho dom, kuchyňu, sklo, vodu a
svetlo. Architektonický OBJ, zdrojové objekty a materiály sú zhodné s R3;
nové materiály sa priraďujú na komponent a steblá sú samostatná vizuálna vrstva.

Podklad používa ambientCG Grass004 v rozlíšení 4 096 × 4 096: farbu,
normály a roughness. Kresba je výtvarne zmenšená na 90 cm z dodávateľom uvádzanej mierky 1,4 m. Tri posunuté výrezy
potláčajú opakovanie, spoločné variácie vo svetových súradniciach spájajú
podklad so steblami. Tóny sú tlmenejšie zelené a olivové, so slabou stopou
kosenia. Grass004 je procedurálny CC0 materiál, nie sken tejto záhrady.

Priestorový porast tvorí **98 344 prekrývajúcich sa skupín**, z toho **7 545 menších pri hranách**.
Štyri geometrické varianty majú po 64 krátkych listov rozložených
po kruhovej ploche: 32 zakrivených listov vo výške 32–45 mm a 32 nižších
vyklonených listov vo výške 16–27 mm. Nominálna hustota vnútri plochy je
približne 17 778 stebiel/m². Samostatné stabilné UV1 semienka mierne menia
farbu každého listu; UV0 zachováva smer od koreňa po špičku.
Materiál TwoSidedFoliage má jemnú priesvitnosť a tmavší koreň. Ide o skutočné
polygóny; priehľadné krížené obrazové karty sa nepoužívajú.

Pôvodný trávnik má väčší obrys než skutočne voľná plocha. Distribúcia preto
odčíta dom, všetky terasy, celý obrys bazénovej terasy, bazén, poklop,
chodníky, nášľapy, štrkové pásy a záhony. Kontroluje obálku celého trsu
vrátane všetkých úrovní detailu s rezervou 1 mm. Odhad pokrytej voľnej
plochy je 345,10 m²; nejde o geodetické zameranie.

Korene zostávajú na pôvodnej výške −65 mm. Najvyššia špička je približne
4 cm pod hornou plochou dosiek. Podklad zostáva viditeľný a zachováva
pôvodnú pochôdznu kolíziu. Nové trsy nemajú kolíziu ani vplyv na navigáciu.

Štyri HISM komponenty používajú tri úrovne detailu: 256 / 64 / 24
trojuholníkov na trs, s prahmi veľkosti na obrazovke 1 / 0,025 / 0,007.
Detailné kamery zo vzdialenosti približne 1,6–1,9 m slúžia na posúdenie
stebiel a napojenia na terasu. Hranica vykresľovania je 40 m; porast nemá
animovaný vietor ani plynulé zmiznutie pri tejto vzdialenosti.

## Napojenie na terasu

Nový blízky pohľad odhalil opakované tmavé trojuholníky na koncoch dosiek
už v prijatom R3. Porovnanie z rovnakej kamery ich odstránilo pri vypnutí
tieňov aj pri vypnutí Nanite. Revízia preto používa existujúcu plnú rasterovú
geometriu len na troch komponentoch drevených terás, ktoré predtým používali
Nanite. Štvrtá terasa ju používala už predtým. Zdrojové mesh assety, materiály,
rozmery, kolízie a globálne nastavenie Nanite zostávajú zachované. Natívne
zábery finálneho balíka potvrdili lokálnu opravu so zapnutými tieňmi a
globálnym Nanite.

## Reprodukcia

Pre novú iteráciu použite nový izolovaný profil podľa
[materiálového postupu](unreal-photoreal.md). Pred jeho krokom `photoreal`
pripravte trávnik a zapnite jeho import:

```sh
python3 -B scripts/unreal/lawn-geometry.py --geometry "$BREZI_MODEL_OUTPUT/geometry" --output "$BREZI_MODEL_OUTPUT/lawn-geometry"
BREZI_PHOTOREAL_LAWN=1 npm run unreal:model -- photoreal
npm run unreal:model -- package
node scripts/unreal/photoreal-capture.mjs terrace
node scripts/unreal/photoreal-capture.mjs grass-detail
node scripts/unreal/photoreal-capture.mjs grass-edge
node scripts/unreal/photoreal-capture.mjs courtyard
```

`BREZI_MODEL_OUTPUT` musí byť exportované do prostredia. Úspešný materiálový
profil sa neprepisuje; pre ďalšiu iteráciu sa používa nový adresár.
`npm run unreal:lawn:test` kontroluje materiálové vstupy a geometrické
výluky. Import následne overuje natívne pozície, UV, topológiu, všetky
inštancie, materiály a zachovanie pôvodných komponentov po uložení a
opätovnom načítaní mapy.

Zdroje: [ambientCG Grass004](https://ambientcg.com/view?id=Grass004),
[licencia CC0](https://docs.ambientcg.com/license/).

## Overený výstup

Aktuálny balík otvorí `npm run unreal:open -- terrace`.
[Štyri priame 4K zábery](../output/unreal/lawn-archviz-20260923-r3/PREZENTACIA.md)
ukazujú celkový dvor, terasu, okraj a detail stebiel zo vzdialenosti približne
1,6–1,9 m. Nižšia vrstva vyplnila viditeľné medzery medzi skupinami,
farby jednotlivých listov sa jemne líšia a kontakt s terasou zostáva čitateľný.

[Vizuálny protokol](../output/unreal/lawn-archviz-20260923-r3/lawn-visual-review.json)
spája PNG, runtime diagnostiku a presný hash aplikácie. Import po skutočnom
uložení a načítaní overil všetky inštancie, dva UV kanály a tri úrovne detailu;
pôvodné natívne assety zostali nezmenené. Prešlo 23 cielených kontrol trávnika
a opravy dosiek plus 42 kontrol materiálového profilu.

Profil používa overené nezmenené natívne binárky z materiálového R3 a nový
import, cook a samostatný balík. Štyri statické 4K merania mali priemer
90,8–114,8 ms na snímku; nejde o potvrdenie plynulosti prechádzky v 4K.
Celodomová pohybová skúška sa v tejto revízii neopakovala. Vlastný trávnik,
okolie a cudzie parcely zostávajú oddelené; nový porast je len na vlastnej
voľnej ploche určenej zdrojovým modelom.
