# Drevo terasy odvodené zo zdrojových dosiek

Fotografovaná textúra [Wood Planks, Poly Haven](https://polyhaven.com/a/wood_planks)
od Amal Kumar, CC0, nahrádza vizuálne opakujúci sa pôvodný materiál na štyroch
terasových meshoch a poklope. Je to návrh povrchovej úpravy; fotografia neurčuje
skutočný druh alebo stav dreva na stavbe. Farebná, normálová a roughness mapa
majú 4096 × 4096 px. Presné zdrojové súbory obnoví
`python3 scripts/unreal/deck-wood/restore_inputs.py`; odlišné lokálne súbory neprepisuje.

[Samostatný materiálový pass](../scripts/unreal/deck-wood/deck_wood.py) používa
264 pôvodných dosiek a jeden pôvodný box poklopu. Nevytvára nové stavebné prvky.
UV1 sa odvodí zo skutočných rozmerov každého povrchu. UV0, vrcholy, trojuholníky,
normály, tangenty a nastavenia zostavenia zostávajú zachované. Dosky majú podľa
zdroja hrúbku 28 mm a šírku najviac 145 mm. Poklop ostáva samostatným boxom
900 × 1100 × 55 mm; jeho kresba neurčuje konštrukciu pod povrchom.

Fotografia pokrýva približne 1500 × 1500 mm. Vybrané tri pásy vynechávajú
fotografované priečne škáry v ploche jednotlivých dosiek. Pozdĺžny výrez
ponecháva 1440 mm; náhodná fáza sa deterministicky odvodzuje z ID a čísla dosky.
Materiál používa derivácie pôvodných súvislých súradníc pre mipmapy aj cez
opakovanie výrezu. Roughness zostáva z fotografie; normálová sila 0,35 je
autorská voľba. UV1 má rovnaké kladné smery ako natívny UV0, takže zachováva
bázu normálovej mapy. Prevod OBJ → glTF obráti V: `(u, 1-v)`.

[Zdrojový plánovač](../scripts/unreal/deck-wood/source_geometry.py) kontroluje
3180 trojuholníkov vrátane orientácie a úplného pokrytia. Takmer spoločné vrcholy
na dvoch terasách rozlišuje podľa celého trojuholníka a UV0. Tolerancia polohy
je 0,002 mm; nezväčšuje sa kvôli nejednoznačnému bodu. Editorový
[UV most](../unreal/BreziTwin/Source/BreziTwin/BreziDeckUVLibrary.cpp) prijme iba
päť konkrétnych zdrojových identít a všetky ich vertex instances. Po štandardnom
rebuild porovná celý pôvodný descriptor a nastavenia kolízie, Nanite aj materiálov.
Cudzie alebo nezhodné existujúce UV1 odmietne. Materiály majú samostatný adresár
podľa receptu, takže nová revízia neprepisuje predchádzajúcu.

Prvý celý import úspešne zapísal a overil UV1, ale následne skončil na obmedzení
menného priestoru hlavného Nanite writeru. Jeho neúspešný záznam zostal zachovaný
v `output/unreal/deck-import-1-report.json`. Deck pass preto nasleduje až po tomto
writeri a sám kontroluje Nanite usage svojich materiálov. Pôvodný `materials.py`
sa nemenil. Poradie zároveň zachová konečné kolízne nastavenie pochôdzneho poklopu.

Pred importom prešiel samostatný natívny proces kontrolou uložených piatich meshov;
geometria a UV0 súhlasili so zdrojom a žiadne vstupné assety ani mapu nezmenil.
25 CPU testov plánovača prešlo; 461 Node, 33 oak a 69 pendant regresných testov
tiež prešlo.

Druhý celý import skončil úspešne, 1878/1878 aktívnych objektov, maximálna
odchýlka bounds 0,0009765625 cm. Zápis UV1 na všetkých piatich meshoch zachoval
pôvodné atribúty aj konfiguráciu. Samostatný
[proces načítania z disku](../output/unreal/deck-readback/20260908T200109Z-efbf5dc3-9602-42a7-8f96-30c6a1b19e73/report.json)
skončil s exit 0: overil každý UV1 float32, pôvodný UV0 a topológiu, celý uložený
descriptor, materiálové grafy, väzby komponentov a kolízne nastavenia.
Všetkých 2272 overovaných súborov zostalo nezmenených. Ide o kontrolu kolíznej
konfigurácie a zdrojovej geometrie; samostatné fyzikálne trojuholníky nemerala.

Pôvodné probe verzie zlyhali na porovnávaní Python tuple s JSON array a následne
na textovom hashi ekvivalentných čísel `0.0`/`0`. Diagnostický záznam potvrdil
rovnaké JSON hodnoty a platný natívny descriptor. Verzia v3 normalizuje iba
JSON reprezentáciu pred hodnotovým porovnaním; nemení toleranciu, geometriu,
materiály ani existujúce reporty. Neúspešné pokusy zostali zachované.

Nová `.app` bola zostavená a zabalená s exit 0 (UAT 102,31 s). Skutočný
[4K záber terasy](../output/unreal/runtime/foreground-terrace-day-5e3155f0-9181-4cb7-9de6-6074cde13603/capture.png)
ukazuje jemnejšiu hnedú kresbu a patinu bez pôvodných veľkých opakovaných uzlov.
Kamerová výška sa líši od staršieho orbit záberu, preto nejde o striktné A/B.
Root skontroloval aj originálny obrázok 3840 × 2160. V jednom stojacom behu
bolo všetkých 300 vzoriek v popredí po 1200 zahrievacích snímkach; render zostal
natívny 4K pri 100 %. Priemer 56,526 ms (17,69 fps), P95 61,431 ms,
GPU priemer 56,144 ms. Proces skončil čisto a balík zostal nezmenený.

Vzhľad je lepší, ale fotorealizmus ani požadovaná plynulosť nie sú potvrdené.
Pozdĺžne opakovanie a veľmi hrubé mipmapy potrebujú hodnotenie pri pohybe.
Najviditeľnejšie zostávajú opakujúce sa drevo fasády, plochý trávnik a príliš
čisté materiálové spoje; [vizuálna recenzia](../output/unreal/deck-material-study/native-visual-review.md).
