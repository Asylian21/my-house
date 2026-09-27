# Regionálna zeleň — samostatný kontext R8 pre native R6

Generátor `scripts/unreal/exterior-regional-vegetation.py` vychádza zo zmrazeného
`output/unreal/exterior-context-20260926-r7/context-plan.json`. Nový výstup je
`output/unreal/exterior-context-20260927-r8/context-plan.json`. Nemení historické
výstupy, návrh C/B/B, oba odstupy 3 000 mm ani geometriu domu a parciel.

Kontext pridáva **1 100** explicitných rastlinných inštancií: 406 širokých
listnatých tvarov, 346 štíhlych listnatých tvarov, 214 ovocných tvarov a 134 krov.
Z toho 1 096 rastlín patrí do 15 skupín korún odčítaných z ortofota ČÚZK z roku
2024. Najbližšie dve skupiny pri dedine obsahujú 102 stromov. Súvislé západné
háje a pásy pri poliach ostávajú v oblastiach viditeľných na snímke; otvorené
polia sa nemenia na les.

Štyri staré ilustratívne korene pri záhrade ostávajú na rovnakých XY. Nahrádza
ich mladý štíhly strom vysoký 3,28–3,31 m, zmenšený výhradne izotropne. Celá
obálka všetkých LOD má polomer najviac 150 cm a odstup aspoň 20 cm od celého
pozemku domu, ciest a stavebných pôdorysov. Tieto štyri výsadby sú návrhový
koncept; nepochádzajú z inventarizácie stromov na fotografii.

Ostatné nové koruny majú aspoň 75 cm rezervu od chránených plôch a 10 cm od
ručne odčítanej hranice korunovej skupiny. Konzervatívny kruh zahŕňa všetkých
osem rohov bounding boxu každého LOD pri ľubovoľnom natočení. Každá koruna
prechádza aj 25-bodovou kontrolou zdrojových pixelov: úplné platné pokrytie,
zelený stred a minimálne 56 % zelených vzoriek. Ide o kontrolu medzier v ručne
zvolenej oblasti, nie o automatické určenie druhu alebo jednotlivého stromu.

Nový `meadowUnderstoryPlacements` pridáva **86 248** krátkych trsov na presné
pôvodné plochy `context_fallow` a `context_crop` do vzdialenosti 75 m. Výška
vo vnútri kolíše približne 7–11 cm a cez posledných 15 m aj pri vonkajších
okrajoch postupne klesá na 2 cm. Rozostup 24 cm má otočený raster, jitter a
pomalú priestorovú variáciu. Kruhová obálka 14 cm zostáva v povolenom zjednotení
plôch a stred má od domu/prístupov/ciest aspoň 30 cm. Susedné oprávnené parcely
môžu mať súvislý podrast cez svoju vnútornú hranicu; katastrálna geometria a
vyznačenie hraníc zostávajú bez zmien.

Pôvodných **382 678** trsov lúky, **2 824** vinohradníckych položiek, všetkých
100 mesh objektov kontextu, treláže a ostatné zdrojové polia sú zachované.
Z každého zachovaného poľa je uložený hash. Každý nový koreň má výšku odvodenú
barycentricky zo skutočného vykresľovaného trojuholníka kontextu alebo DMR R4.
Nemeraný rovný podklad zostáva výslovne nemeraný.

Zdrojové koruny: **ČÚZK, 2024 · Ortofoto ČR · CC BY 4.0**, jednorazový export
ČÚZK – on-line. Polygóny skupín, jednotlivé pozície, výšky, druhový vzhľad a
sezónny podrast sú vizuálne interpretácie. Presnosť katastrálnych hraníc sa na
tieto výsadby neprenáša. Nové modely sú explicit-only zo samostatného balíka
`exterior-regional-assets-20260927-r4`; ich licencia a odvodenie sú v jeho
manifeste.

Overenie: `test_exterior_regional_vegetation.py` kontroluje zdrojové hashe,
zachovanie geometrie, každú transformovanú LOD obálku, odstupy korún, vzorky
ortofota, výšky koreňov, rozstupy aj celú doménu krátkeho podrastu. Tieto
statické testy nepotvrdzujú native vzhľad alebo výkon. Native import,
ukladanie/opätovné načítanie, pohybové zábery a výkon má samostatnú QA.
