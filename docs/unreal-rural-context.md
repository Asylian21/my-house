# Unreal — cesta a krajina parcely 6012/26

Revízia `output/unreal/rural-context-20260923-r4` nadväzuje na materiály,
kuchyňu a detailný trávnik profilu z 23. septembra. Zdrojový dom C/B/B,
uličný aj pravý odstup 3 000 mm a katastrálny rámec zostávajú autoritatívne.
Fotografie stavebníka `p1.png`–`p4.png` určujú vzhľad okolia; nejde o
fotogrametriu ani zameranie polohy poklopu, rastlín a medzníkov.

Cesta používa pôvodnú geometriu a oblúk zo spoločného exportu. Materiál
zobrazuje sivé obdĺžnikové betónové tvarovky 200 × 100 mm s 3 mm pieskovými
škárami, väzbou na polovicu a filtrovaným detailom hrán. Obrubníky si
zachovávajú pôvodné nábehy pri vstupoch; cestné mesh a obrubníky dostávajú
Nanite v samostatných vizuálnych kópiách. Pôvodné assety sa neprepisujú.
Za tromi koncovými hranami exportu pokračujú samostatné vizuálne úseky
cesty, obrubníkov a hlinených krajníc po 1 km. Nadväzujú na pôvodné
koncové vrcholy a smer hrán; vzdialený priebeh je scénografické pokračovanie,
nie zameranie okolitých komunikácií. Nepridáva pochôdzne kolízie.
Mikrotextúra pochádza z lokálne overeného CC0 skenu
[Poly Haven Concrete Pavement](https://polyhaven.com/a/concrete_pavement).
Výrez vnútra pôvodných tvaroviek vylučuje druhú, konkurenčnú sieť škár.

Nespevnené pásy vychádzajú z triangulácie existujúcich krajníc vrátane
otvorov pre vjazd a vstupy. Povrch kombinuje suchú zeminu s lokálne
hashovo overeným CC0 skenom [Poly Haven Gravel Floor 02](https://polyhaven.com/a/gravel_floor_02).
Nová burina, suchá tráva a štíhle listnaté stromy sú autorské geometrické
aproximácie s tromi LOD; nie sú skenmi konkrétnych rastlín z fotografií.
Vetrolam tvorí nepravidelná dvojica radov za zadnou hranicou. Široké poľné
pozadie pokračuje na existujúcom vzdialenom teréne.
Štyri pôvodné schematické objemy živého plota nahrádza nepravidelný
listnatý podrast; samotný zadný plot zostáva zachovaný.

Kosený porast zostáva vo dvore pri átriu a bazéne. Vonkajšie pásy parcely
majú surový povrch a riedky porast. Vegetácia používa priestorovo rozdelené
HISM skupiny bez kolízií, navigácie a vlastného ticku. Vzdialenostné culling
limity a skutočný výkon sú uvedené v importnom a vizuálnom protokole;
samotná existencia LOD nepotvrdzuje nezmenené FPS.

Pouličné lampy zostávajú podľa spoločného modelu. Nové vizuálne detaily
obsahujú liatinový poklop s priemerom 600 mm a plastové vytyčovacie značky.
Poloha týchto nových detailov je ilustračná. Slnko používa uhlový priemer
0,75°, Lumen, výšku 48° nad horizontom a zachovaný azimut scény; nejde o presnú rekonštrukciu
času z EXIF fotografií.

## Reprodukcia

Použiť nový izolovaný profil podľa postupu v [materiálovej revízii](unreal-photoreal.md)
a [trávniku dvora](unreal-lawn.md). Po úspešnom kroku `photoreal`:

```sh
python3 -B scripts/unreal/rural-geometry.py --geometry "$BREZI_MODEL_OUTPUT/geometry"
node scripts/unreal/model-refresh.mjs rural
node scripts/unreal/model-refresh.mjs package
node scripts/unreal/rural-capture.mjs street
node scripts/unreal/rural-capture.mjs road-detail
node scripts/unreal/rural-capture.mjs courtyard
```

`BREZI_MODEL_OUTPUT` musí byť exportované do prostredia. Generátor píše
`geometry/rural-context-geometry.json`; natívny krok kontroluje súradnice,
LOD, kolízie, zachovanie zdrojových komponentov a ukladanie/opätovné načítanie
mapy. Neúspešný pokus možno po ukončení engine obnoviť cez
`python3 -B scripts/unreal/rural-import.py --restore "$BREZI_MODEL_OUTPUT"`.
Historické profily a snímky sa neprepisujú.

## Overený výstup

`npm run unreal:open -- street` otvorí aktuálny samostatný balík.
[Galéria šiestich natívnych 4K záberov](../output/unreal/rural-context-20260923-r4/PREZENTACIA.md)
obsahuje celok, ulicu, dlažbu s poklopom, vetrolam, átrium a interiér.
[Vizuálny protokol](../output/unreal/rural-context-20260923-r4/rural-visual-review.json)
viaže snímky, runtime diagnostiku, import a konkrétny balík cez SHA-256.

Prešlo 10 geometrických a integračných testov okolia a 7 testov osadenia
a hlavného variantu. Nový import, cook a podpis balíka prešli; natívna
kontrola po uložení a načítaní potvrdila materiály, Nanite, tri LOD, HISM
transformácie, zachované zdrojové assety, dvere a kolízie. Zdrojová scéna
sa od prijatého profilu trávnika líši iba časom exportu; OBJ je bitovo zhodný.

Okolie má 3 969 inštancií v 321 HISM skupinách. Z pôvodného detailného trávnika
ostáva 40 437 inštancií vo vymedzenom dvore; 57 907 inštancií vonkajších
pásov nahrádza surová zemina a riedky poľný porast. Cestné pokračovania,
obrubníky a všetky nové rastliny sú vizuálne kulisy bez kolízií.

Rovnaká interiérová kamera s rovnakým natívnym 4K nastavením namerala
135,2 ms oproti pôvodným 136,1 ms na snímku (240 intervalov po 360 zahrievacích
snímkach). Toto meranie nezistilo spomalenie v danom zábere; nepotvrdzuje
nezmenené FPS vo všetkých miestnostiach. Približne 7,4 FPS v 4K je prezentačný
režim, nie plynulá prechádzka. Celodomová pohybová skúška sa neopakovala.

Zábery potvrdzujú odstránenie pôvodných schematických objemov živého plota,
useknutých koncov ciest pri parcele a rušivých farebných pásov/škvŕn pozadia.
Stromy zblízka ostávajú rozpoznateľné ako procedurálna geometria a široká
poľná krajina je zjednodušená. Výsledok preto nie je označený ako úplne
fotorealistická ani geodeticky presná rekonštrukcia fotografií.
