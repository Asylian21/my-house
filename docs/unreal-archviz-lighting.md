# Osvetlenie interiéru v aktuálnej Unreal prehliadke

`scripts/unreal/archviz_lighting.py` dopĺňa skutočné lokálne svetlá do nového
profilu `archvizGame`. Staršie exporty a balíky zostávajú referenčnými snímkami.
Východiskom je výlučne aktuálne exportovaný C/B/B model a jeho 13 miestností.

Predchádzajúci model refresh vytváral slnko, oblohu a adaptáciu expozície, ale
nepridával interiérové svetlá k modelom svietidiel. Nový doplnok používa
exportované difúzory v pracovni, detských izbách, spálni, kúpeľni a pri jedálni.
Zachováva presnú polohu, rozmery a svetelný tok oboch zdrojových kuchynských
svietidiel. Ich denný stav je pre obývanú prehliadku výslovne zapnutý.

Nepokryté časti pôdorysu dostávajú navrhované stropné plošné svetlá. Polohy
vychádzajú zo skutočných čistých obdĺžnikov miestností a exportovaných SDK
podhľadov. Šikmá výška obývačky sa odvodzuje z exportovaných vzoriek sklonu
závesov kuchynského svietidla. Doplnkové svetlá majú v zázname
`visibleLuminaireMeshAuthored: false`: ide o návrh osvetlenia, ich ďalšie telesá
nie sú doplnené do architektonického modelu.

Každé svetlo je samostatný pohyblivý `RectLight`, svieti nadol, vrhá tiene a má
konečný dosah. Tok je v lúmenoch, teplota 3 000 K, pri existujúcich jedálenských
svietidlách 2 700 K. Slnko, obloha, globálna expozícia, kolízie, zdrojové modely
a materiály sa nemenia. Svietidlá zostávajú zapnuté vo dne aj v noci; vonkajší
cyklus deň/noc sa naďalej riadi existujúcim ovládačom.

Mimo kuchyne je tok rozpočítaný podľa skutočnej podlahovej plochy: chodby a vstup
240 lm/m², mokré a technické miestnosti 400 lm/m², ostatné priestory 350 lm/m².
Tieto čísla predstavujú návrhový príkon svetelného toku na plochu, **nie namerané
luxy**. Model nepoužíva vymyslený IES profil ani údaje výrobcu. Aktuálny zdroj
vytvára 40 svetiel; najväčší individuálny tok je približne 3 622 lm.

Integrácia importu:

```python
from archviz_lighting import apply_archviz_lighting, verify_archviz_lighting
# Po base.lighting(), pred uložením novej mapy:
REPORT["archvizLighting"] = apply_archviz_lighting(scene, actor_system)
# Po opätovnom načítaní uloženej mapy:
REPORT["archvizLighting"] = verify_archviz_lighting(scene, actor_system)
```

Zapínací profil má zvoliť nadradený importér. Pomocník odmieta opakované
vytvorenie duplicitných svetiel. Pri čiastočnom zlyhaní odstráni iba vlastné
práve vytvorené svetlá. Overenie číta späť presnú polohu, smer, orientáciu
obdĺžnika, tok, jednotky, rozmery zdroja, dosah, teplotu, tiene a viditeľnosť.
Obidve fázy patria do overenia nového balíka a pomocník do hashov jeho pipeline.

`scripts/unreal/archviz-room-viewpoints.mjs` vracia 13 pohľadov `room-1-01` až
`room-1-12` a `room-dressing`. Kamera stojí vo výške 1 650 mm na overiteľnej
zdrojovej návštevnej pozícii z walkthrough fixture. Smer pohľadu sa vyberá do
širokého voľného priestoru miestnosti namiesto ponechania príchodového smeru
kamery. Konzervatívne lúče rešpektujú vnútorné nepriehľadné objekty a pôdorys.
Ide o kandidátov na vizuálne overenie; samotné generovanie pohľadu nepotvrdzuje
fyzickú priechodnosť ani úplnosť zariadenia miestnosti.

Pred prijatím výsledku treba v skutočnom Metal runtime prezrieť všetkých 13
pohľadov cez deň, aspoň chodbu, kúpeľňu a kuchyňu v noci a exteriér cez deň.
Kontrolovať čitateľnosť stien a zariadenia, neprepálené povrchy, tiene pri
dverách a výkon. Úspešný CPU plán alebo natívny readback nie je vizuálnym
potvrdením svetelnej kvality ani fotometrickým výpočtom.

Lokálne kontroly:

```sh
python3 tests/unreal-archviz-lighting.test.py
node --test tests/unreal-archviz-room-viewpoints.test.mjs
```

Použité natívne vlastnosti zodpovedajú rozhraniu
[Epic RectLightComponent](https://dev.epicgames.com/documentation/en-us/unreal-engine/python-api/class/RectLightComponent?application_version=5.7)
a lokálnym hlavičkám `RectLightComponent.h` / `LocalLightComponent.h` UE 5.8.
