# R25: jeden pôvodný trs Fern02 vo vlastnej záhrade

Tento samostatný pokus vychádza zo skutočne uloženej spoločnej scény R22c R3
(`realism-integration-native-report-r3.json`, proces 50344, exit 0). Vstupný
plán paprade zostáva pôvodným nemenným zdrojovým plánom; jeho historický stav
„native base pending“ sa neprepisuje. Nový preflight viaže neskorší uložený základ.

Mení sa iba jednočlenná komponenta `Instances` aktora
`BreziVegetationPatch_1428`, skupina
`EX_ornamental_0_-1_garden_feather_r3_b_18000`. Pôvodné natívne XYZ a natočenie
sa kopírujú priamo z natívneho Transform. Mení sa model, materiál a rovnomerná
mierka. Pred zmenou sa na komponente bez modelu a vlastníka odmeria skutočná
serializácia jedného člena; jej Transform a uložená FMatrix sa potom porovnajú
bitovo presne pred aj po uložení a opätovnom načítaní mapy.

Pôvodný model Fern02 b má1 660 vrcholov a 2 384 trojuholníkov. Export zachová
originálne bajty POSITION/NORMAL/UV0/indexov. Poskytovateľ nemá TANGENT ani
reťazec LOD: tri pilotné LOD sú zámerne totožné. Ich skutočné natívne rohy,
UV0, poradie, orientácia, prahy zobrazenia a nastavenia zostavenia sa overujú.
Výpočet tangentov z pôvodných UV je požiadavka; numerický natívny readback
normál/tangentov nie je dostupný a ostáva nepotvrdený.

Rovnomernú mierku obmedzuje pôvodná koruna 54.488 cm a nezmenený záhon
DOM_01966. Výsledná zdrojová výška je 35.273 cm oproti pôvodným 120 cm.
Nejde o rovnocennú výškovú náhradu ani o ekologické odporúčanie. Plná koruna
a každý natívny F32 vrchol musia zostať v pôvodnom záhone. Limit 0.002 cm sa
používa iba na obal zdroj/natívny float; bitové porovnanie Transform/FMatrix
nemá všeobecnú toleranciu.

Jeden nový provisional TwoSidedFoliage graf používa štyri nezmenené publikované
mapy Poly Haven (CC0): RGB albedo, GL normal s explicitným preklopením zelenej,
ARM.G roughness/ARM.B×0 metallic a samostatnú 16-bitovú alfa masku cez
normalizované R s prahom0.5. Pôvodný glTF nemá occlusionTexture, preto AO
koreň nie je zapojený. Hodnota subsurface 0.08 je výtvarná voľba. Pôvodná
16-bitová PNG presnosť nepreukazuje natívny pixelový ani GPU formát.

Celý pôvodný svedok 5 346 aktorov povoľuje len túto jedinú zmenu. Počet 2 312
HISM / 676 944 členov, ostatné rastliny, hustota, cully 14 400 / 18 000, svetlá,
kolízie, kamery, C/B/B a odstupy 3 000 mm ostávajú presné. V pôvodných 4 049
Content súboroch sa mení iba vlastná mapa. Pribudne presne 9 balíkov:
1 mesh, 1 graf, 4 textúry a 3 vlastné importné pipeline. Pôvodných 56 grafov
a 84 textúr sa overuje pred aj po opätovnom načítaní. Zdrojový R22 projekt
a 132 chránených súborov sa zachovajú. Každý súbor kandidáta má nezávislý inode.

Nové CPU testy sú zdrojové a konštruované receipt fixture kontroly. Nepridávajú
natívny ani vizuálny dôkaz. Referenčný host je systémový Python 3.9.6. Bundled
Python 3.12.14 odmietol starý nemenný R22 grass guard na odvodenom
`cameraDistanceCm` ešte pred ktorýmkoľvek R25 testom; tento neúspešný log sa
zachováva samostatne. Natívny root pokus používa UE runtime, ktorý skutočný
R22 import už overil. Žiadny starý guard ani jeho numerická politika sa nemení.

Root spúšťa UnrealEditor-Cmd s `-run=pythonscript`, `-nullrhi` a novým helperom
`exterior-garden-fern-native-r25.py`. Vyžadované premenné:
`BREZI_FERN_OUTPUT`, `BREZI_FERN_PREFLIGHT`, `BREZI_FERN_PREFLIGHT_SHA256`.
Vlastný report je `garden-fern-native-report.json`; úspešný stav je
`verified-saved-original-fern-single-own-garden-root`. Spustenie, uloženie,
realistickosť vzhľadu, výkon a Shipping zostávajú samostatné dôkazové vrstvy.
