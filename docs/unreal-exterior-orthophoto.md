# Ortofoto okolitého terénu C/B/B

Zmrazený podklad je v `output/unreal/exterior-ortho-20260926-r1/`. Jeho [manifest](../output/unreal/exterior-ortho-20260926-r1/orthophoto-manifest.json) má stav `SOURCE_GEOGRAPHY_LICENSE_AND_UV_VALIDATED_NOT_NATIVE_INTEGRATED`: potvrdzuje pôvod, licenciu a súradnicové mapovanie, nie prijatie natívneho materiálu ani fotorealistický výsledok. Zostavy R4 a pôvodné vstupné PNG sa nemenia.

## Zdroj, rok a licencia

Zdrojom je **Ortofoto České republiky**, ČÚZK / Zeměměřický úřad, získané jednorazovým exportom [oficiálnej služby ORTOFOTO](https://ags.cuzk.gov.cz/arcgis1/rest/services/ORTOFOTO/MapServer). PNG boli stiahnuté 26. 9. 2026 UTC, no **rok aktuálnosti zdrojových dát je 2024**. Rok stiahnutia sa nesmie použiť ako rok ortofota.

Uložené dotazy na [oficiálnu vrstvu aktuálnosti ortofota](https://ags.cuzk.gov.cz/arcgis/rest/services/Metadata/MapServer/12) vracajú rok `ROK_AKTUALIZACE=2024`: jeden záznam pri parcele a 51 záznamov pre celý 16 km výrez. Dôkazy sú v `inputs/currency-site.json` a `inputs/currency-far16km.json` spolu s URL, časom získania a SHA256 v sprievodných potvrdeniach. `DATUM_AKTUALIZACE` sa nepovažuje za potvrdený presný deň leteckého snímkovania.

[Podmienky priestorových dát ČÚZK](https://www.cuzk.gov.cz/Predpisy/Podminky-poskytovani-prostor-dat-a-sitovych-sluzeb/Podminky-poskytovani-prostorovych-dat-CUZK.aspx) uvádzajú ortofoto medzi otvorenými dátami pod licenciou [Creative Commons CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Pri výstupoch zachovať pôvod, metadáta, odkaz na licenciu a informáciu o úpravách. [Podmienky sieťovej služby](https://www.cuzk.gov.cz/Predpisy/Podminky-poskytovani-prostor-dat-a-sitovych-sluzeb/Podminky-poskytovani-sitovych-sluzeb-CUZK.aspx) dopĺňajú označenie poskytovateľa **ČÚZK – on-line**. Uložený export nie je živá mapová služba.

Viditeľná atribúcia pre zábery používajúce podklad:

> Ortofoto ČR: ČÚZK, 2024 · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/). Zdroj: ČÚZK – on-line, jednorazový export. Úpravy pre vizualizáciu: výrez, prevzorkovanie a mapovanie na DMR.

Takéto označenie neprenáša licenciu ortofota na celý projekt ani nevyjadruje schválenie vizualizácie poskytovateľom. Galéria označuje tento podklad ako ortofoto pre R5; staršie exteriérové pokusy R1–R4 ho nepoužívajú. Prítomnosť v konkrétnom balíku musí potvrdiť jeho import a natívna evidencia.

## Zmrazené súbory

Oba obrazy sú 4096 × 4096, RGBA8, sRGB, v EPSG:5514. Far atlas pokrýva 16 × 16 km a detail 2 × 2 km; ide o veľkosť exportu, nie deklaráciu pôvodného rozlíšenia snímkovania.

| Podklad | Súbor v `inputs/` | Meter na pixel exportu | Pokrytie s alpha 255 |
| --- | --- | ---: | ---: |
| `far16km` | `ortho-dmr-16km.png` | 3,90625 | 75,5684 % |
| `detail2km` | `ortho-site-2km.png` | 0,48828125 | 96,8575 % |

SHA256:

```text
orthophoto-manifest.json
c1ef77591421edc7bebb7d63a0a831eec81e0907c46a0dd04c2c76dbb5e7e71c

inputs/ortho-dmr-16km.png
df4282d278b527d6bd5927ea388f0fc1e882f8e1c4a2f791e6b1193e112227e7

inputs/ortho-site-2km.png
55e805d0924123166f3ff0361e8f2feb970726f5bbe9adb45e9d05759b41f2e5
```

Kontrola 27. 9. 2026: **36/36 položiek `inputFiles` zodpovedá SHA256**, rovnako kontrolné súčty vrstiev, world files, potvrdení poskytovateľa a metadát aktuálnosti. `finalize-manifest.py` vytvoril finálny manifest; opakované spustenie nie je obnovovací postup, pretože zmrazené súbory zapisuje výhradne ako nové (`xb`).

## Transformácia a použitie materiálom

Poskytovateľ exportoval a prevzorkoval požadované výrezy do EPSG:5514 a 4096 × 4096. Lokálne PNG sú uložené bez zmeny pixelov. Doplnené `.pgw` súbory určujú polohu stredov pixelov; manifest obsahuje presné hranice v metroch a afinné matice `worldCmToUvRows` pre natívny materiál.

Vstupom matice je `AbsoluteWorldPosition.XY` v **globálnych centimetroch Unrealu**:

```text
U = rowU.x * worldXcm + rowU.y * worldYcm + rowU.z
V = rowV.x * worldXcm + rowV.y * worldYcm + rowV.z
```

UV má počiatok vľavo hore a V rastie nadol. Súradnice sa nesmú znova previesť na metre, lokálnu polohu aktéra, ani prehodiť osi. Matice vychádzajú zo spoločného rámca C3, stredu scény `(15200, 10800)` mm a aktívneho posunu domu `CLIENT-PLACEMENT-20260913`. Zachovávajú C/B/B a oba požadované odstupy 3 000 mm; nejde o nové geodetické zameranie.

Existujúca kalibrácia porovnala 290 bodov na každej vrstve. Najväčšia odchýlka po zaokrúhlení súradníc C3 je 0,000179 pixelu pre 16 km a 0,001380 pixelu pre 2 km atlas. Ide o zhodu výpočtu, nie o presnosť ortofota alebo umiestnenia domu v teréne.

Alpha je **pokrytie poskytovateľa**, nie priesvitnosť zeminy ani lístia. Alpha 0 označuje chýbajúce dáta; čierne RGB v týchto pixeloch sa nesmie zobraziť ako čierny terén. Materiál musí pred použitím farby vyžadovať UV v rozsahu 0–1 a vzorkovanú alpha aspoň 0,99. Samotný Clamp nestačí: mimo hranice by predlžoval krajné pixely. Filtrované okraje a mipmapy vyžadujú kontrolu v natívnom obraze.

Navrhnuté použitie je makrofarba vzdialenej zeminy cez `BaseColor`: bez ortofota do 300 m od počiatku scény, plynulý nábeh 300–900 m, plný makropríspevok ďalej. Detail 2 km je voliteľný, s prechodom do 16 km atlasu pri okraji. Ponechať geometriu, normály a drsnosť DMR; nevytvárať výšky z fotografie, emissive terén ani fotografické nebo. Dom, strechy, bazén a blízka záhrada používajú vlastnú 3D geometriu a materiály.

Zdroj obsahuje pôvodné tiene a zachytené strechy. Nadväzujúci import musí osobitne zaznamenať miešanie farieb, tlmenie sýtosti a prípadné prekrytie modelovanými budovami. Chýbajúce pokrytie ostáva samostatne označeným kontextom; ortofoto nemení dôkazovú úroveň nameraného DMR ani odvodeného terénu.

## Galéria a hranica prijatia

`scripts/unreal/exterior-gallery.mjs` uvádza atribúciu vo viditeľnej päte, mimo zbaleného zoznamu dokladov. Po uložení novej natívnej série obnoviť galériu:

```sh
node scripts/unreal/exterior-gallery.mjs output/unreal/exterior-validation-20260926-r1
```

Tento krok nemení pôvodné PNG, výber revízií ani pravidlá vizuálneho prijatia. Zdrojový manifest zostáva dôkazom podkladov; prijatie konkrétneho balíka vyžaduje samostatné natívne snímky, posúdenie zarovnania, pokrytia a svetla a meranie výkonu. Dokončený export ortofota sa nesmie zamieňať s potvrdenou fotorealistikou alebo plynulosťou pohybu.
