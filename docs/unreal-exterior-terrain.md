# Meraný vzdialený reliéf Březí

`scripts/unreal/exterior-terrain.py` vytvára vzdialený terén z oficiálnej služby
[ČÚZK DMR 5G ImageServer](https://ags.cuzk.gov.cz/arcgis2/rest/services/dmr5g/ImageServer).
Aktuálny nemenný plán je `output/unreal/exterior-terrain-20260926-r4/terrain-plan.json`.
Zdrojový návrh ostáva C/B/B, oba kolmé odstupy 3 000 mm a dom sa neposúva.

Používa sa 16 × 16 km ohraničený výrez v EPSG:5514 s 257 × 257 bodmi, teda
približne 62 m medzi vzorkami. Výrez je voči národnému bodu pri dome posunutý
o 1 200 m na východnú os a 1 000 m na severnú os, aby overený vzdialený vrchol
neležel na orezanom okraji. Výška je Bpv (EPSG:8357). Služba uvádza pôvodné
letecké laserové skenovanie 2009–2013; tento výrez preto nie je dôkazom
dnešných stavieb či aktuálneho terénu po výstavbe.

## Zdrojové dáta a NoData

`inputs` obsahuje odpoveď metadát služby, surový F32 GeoTIFF a zhodný PNG32
výrez s alfa maskou. Oba exporty majú explicitné
`renderingRule={"rasterFunction":"None"}`, rovnaký rozmer, bbox, EPSG:5514
a bilineárnu interpoláciu. Žiadny hillshade ani farebný obraz sa nečíta
ako výška. Ku každému exportu patrí nemenný receipt s celým dotazom, odpoveďou,
časom získania a SHA-256. Rovnakým spôsobom sa pripína malý 17 × 17 bodov,
2 m raster okolo národného východiska.

Pri prvotnej kontrole TIFF knižnica vracala neplatné hodnoty zo sparse tiles
s offsetom 0. Generátor preto číta skutočné nekomprimované float tiles cez
TIFF offsety a počty bajtov; prázdne tiles nevytvárajú výšku. Alfa 255 zo
zhodného exportu je povinnou ďalšou podmienkou platnej vzorky. Neplatné bunky
sú `null`, nie nulová výška a nie odhadované vrchy. Neočakávaná platná výška
zastaví generovanie namiesto tichého orezania.

Zmrazený výrez má **50 140 platných bodov a 15 909 chýbajúcich bodov**.
Platný rozsah je **165,798–542,150 m Bpv**. Najvyššia vzorka leží približne
9,2 km od scény a zodpovedá vzdialenému pásmu Pálavy; silueta vzniká z DEM.
Botanické pokrytie, stavby ani farba jednotlivých svahov z DEM nevyplývajú.

Právny pôvod: **© ČÚZK, DMR 5G, CC BY 4.0; sampled and transformed for
visualization**, podľa [podmienok ČÚZK](https://cuzk.gov.cz/Predpisy/Podminky-poskytovani-prostor-dat-a-sitovych-sluzeb/Podminky-poskytovani-prostorovych-dat-CUZK.aspx).

## Napojenie na existujúcu scénu

Presná transformácia XY zodpovedá existujúcemu C3 rámcu: projekcia v mm,
zaokrúhlenie a potom klientsky posun; UE X = lokálne X / 10,
UE Y = −lokálne Y / 10. Čerstvá 2 m vzorka pri východisku je
**184,029342651 m Bpv**. Slúži ako relatívna kotva reliéfu, nie výška hotovej
podlahy domu a nie náhrada geodetického bodu.

Meraný mesh nevstupuje do okruhu 300 m. V pásme 300–900 m sa jeho relatívna
výška plynulo pripája k aktuálnemu plochému okoliu. Za 900 m má mierku výšky
1,0. Pri hranici platného pokrytia a na vonkajšom okraji výrezu sa pridáva
samostatne priznané 600 m grafické napojenie na neznáme ploché pozadie.
Surové Bpv hodnoty zostávajú nedotknuté; grafický blend sa uchováva ako
výslovná politika renderu, nie ako meranie terénu.

`context_unresolved_flat_backdrop` dopĺňa iba priestor bez meraného mesh:
chýbajúce bunky vrátane Rakúska, plochu za výrezom až do rámca 60 × 60 km
a blízke napojenie mimo pôvodného DOM_00000. To je **ilustračná rovina
Z = −25 cm**, s `noDataFallback.measured=false`. Pôvodná plocha DOM_00000
má rámec X ±120 m / Y ±100 m; zostáva zachovaná. Väčší rámec katastrálneho
kontextu sa nemusí všade vyplniť WFS parcelami, preto je pod ním fallback.

Pri importe s `BREZI_EXTERIOR_TERRAIN` sa vypína iba vzdialená pôvodná rovina
DOM_02039; keby ostala viditeľná, zakryla by merané údolia pod jej výškou.
Dom, zdrojové cesty, kolízie ani pohyb chodca sa nemenia. Merané chunky aj
fallback majú `NoCollision`. Materiál je `context_distant_terrain` a jeho
svahové normály musia pochádzať zo skutočnej geometrie.

## Reprodukcia a overenie

```sh
python3 -B scripts/unreal/exterior-terrain.py \
  --scene output/unreal/realism-20260926-r5/geometry/scene.json \
  --output output/unreal/exterior-terrain-20260926-r4
python3 -B -m unittest discover -s scripts/unreal -p test_exterior_terrain.py -v
```

Existujúci výstup sa neprepisuje; ďalšie generovanie vyžaduje nový adresár.
Pillow slúži na metadáta a PNG alfa masku, F32 tile decode je explicitný.
`inputFiles` pripína zdrojovú scénu, parser, všetky rastre, metadáta aj receipts.
Zdrojový parser nemá oprávnenie spúšťať Unreal.

Šesť kontrol overuje C3 zaokrúhlenie, pixel-centre georeferenciu, jednotkovú
výšku a blend, presnú zhodu hodnôt a masky so zmrazeným plánom, všetky hashe,
konečnosť súradníc, orientáciu každého trojuholníka, úplné hrany 300 m
vylúčenej oblasti a zachovanie pôvodnej blízkej základne. Technický
`height-overview.png` v R3 zobrazuje rovnaké zdrojové DEM ako R4; je dôkazom
vstupu, nie natívny screenshot. Natívny obraz a výkon overuje až samostatný
import a zachytenie v Unreale.
