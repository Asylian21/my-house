# Zvislé drevené obloženie fasády

Natívny import používa fotografický materiál na presne 12 vonkajších paneloch
(10 materiálových slotoch). Zdrojové OBJ trojuholníky, polohy a UV0 sa nemenia.
Stolík DOM_01876/MAT_0111, terasa a interiérový dub sú mimo rozsahu.

Zdrojový návrh `NATURAL_VERTICAL_LARCH`, generátor `gen_larch` a obrazová referencia
podporujú zvislé úzke obloženie. Nové mapovanie používa 50 mm rytmus, fotografickú
kresbu pozdĺž zvislej osi stien a pozdĺž skutočného sklonu oboch podhľadov.
Pri bočnom paneli DOM_00157 ide o vedomú opravu smeru oproti jeho pôvodnej UV0
orientácii. Spoločný svetový počiatok zachováva nadväznosť troch dielov štítu.

Použité sú nezmenené 4K mapy [Poly Haven Hinoki Planks](https://polyhaven.com/a/hinoki_planks),
Charlotte Baglioni, CC0. Overená plocha skenu je približne 1,89 × 1,89 m.
Osem 50 mm fotografických pásov obchádza pôvodné široké škáry skenu; jednotlivé
lamely majú deterministický výber pásu a pozdĺžny posun. Procedurálna škára
1,953125 mm a tmavnutie ×0,42 vychádzajú zo zdrojového generátora. Integrované
pokrytie škáry a explicitné derivácie nezalomených súradníc obmedzujú aliasing.
Drsnosť zostáva fotografická, sila normály 0,35 je autorské nastavenie.

Hinoki je vizuálna náhrada za v návrhu pomenovaný smrekovec. Referenčný obrázok
nie je preukázané meranie realizovanej fasády v Březí. Materiál preto nepredstavuje
kalibrovaný vzor dodávateľa ani dôkaz fotorealizmu.

Implementácia je v `scripts/unreal/facade-wood/`. Import najprv overí presný zdroj,
fotografie a rozsah, potom vytvorí samostatné materiály s podporou Nanite.
Pôvodné polohy, trojuholníky a UV0 číta pred aj po priradení materiálu.
Po opätovnom otvorení mapy kontroluje komponenty, grafy a uložené súbory;
balenie aplikácie vyžaduje tento platný výsledok.

Chýbajúce podklady obnoví `python3 scripts/unreal/facade-wood/restore_inputs.py`.
Skript overuje veľkosť, SHA256 a pri sťahovaní aj oficiálne MD5; existujúce odlišné
súbory neprepisuje. Import zostáva explicitný cez `npm run unreal:import`.

Natívny preflight v samostatnom procese overil všetkých 204 trojuholníkov a UV0
na 12 paneloch. Najväčšia polohová odchýlka bola 0,001167563 mm; žiadny vstup ani
asset sa nezmenil. CPU overenie zahŕňa odmietnutie obráteného poradia, chýbajúcich
trojuholníkov, zmien UV0, nesprávneho rozsahu a numericky odlišných uložených dát.
Porovnanie reportov toleruje iba ekvivalentný JSON zápis čísiel a polí, bez
zaokrúhľovania hodnôt. Aktuálne prešlo 31 testov materiálu a obnovy vstupov.

Finálny import prešiel s 1 878 aktívnymi objektmi, bez chyby hostiteľského procesu.
Metal cook a macOS balenie skončili úspešne; balík z 8. septembra 2026, 20:42 UTC,
má SHA256 reportu `3a5cd70691177ce321ee325a0008e16907ed5c2ea6a80b239065c1a06c40e88c`.
Samostatný čerstvý NullRHI proces PID 31939 znovu načítal všetkých 12 panelov,
10 materiálov a tri mapy. [Readback](../output/unreal/facade-readback/20260908T204534Z-fb35740e-4831-4c5a-aec0-09aa4b5cf613/report.json)
prešiel, všetkých 2 301 sledovaných súborov ostalo nezmenených a proces skončil
s exit 0. Pôvodný úspešný import pred opravou porovnávania JSON je zachovaný
v `output/unreal/facade-import-1-report.json`.

[Skutočný 4K záber novej aplikácie](../output/unreal/runtime/foreground-terrace-day-28608fa6-e1d7-451b-9314-cd1a2d51f4ba/capture.png)
ukazuje zvislé úzke lamely na záhradných poliach, ľavej terase a pravej nike.
Nezávislá obrazová kontrola potvrdila odstránenie pôvodných širokých vodorovných
pásov bez zjavného výpadku materiálu. Viditeľné zostáva opakovanie niektorých
hrčí a pravidelnosť čistých škár. Jeden záber neoveruje zakryté podhľady,
časové filtrovanie pri pohybe ani presnú milimetrovú mierku z obrazu.

Po 1 200 zahrievacích snímkach prešlo 300/300 vzoriek s aktívnou aplikáciou,
oknom aj klávesovým fokusom. Scéna zostala 3840 × 2160 pri 100 %;
priemer 51,288 ms (19,50 fps), P95 56,090 ms, GPU priemer 50,948 ms.
Proces PID 31068 skončil s exit 0 a balík sa nezmenil.
Ide o aktuálne meranie jednej stojacej kamery, nie dôkaz zrýchlenia fasádnym
materiálom ani dosiahnutie požadovanej plynulosti a fotorealizmu.
