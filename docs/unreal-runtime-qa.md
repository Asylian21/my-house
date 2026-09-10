# Natívna macOS validácia

## Aktuálna hranica merania výkonu, 8. september 2026

Balík z **20:42 UTC** so zvislým dreveným obložením prešiel
[novým denným meraním terasy](../output/unreal/runtime/foreground-terrace-day-28608fa6-e1d7-451b-9314-cd1a2d51f4ba/foreground-qa.json).
Po 1 200 zahrievacích snímkach malo všetkých 300 vzoriek aktívnu aplikáciu,
okno aj klávesový fokus. Render bol priebežne 3840 × 2160 pri 100 %.
Priemer **51,288 ms (19,50 fps)**, P95 **56,090 ms**, GPU priemer **50,948 ms**;
exit 0 a nezmenený balík. Je to jedna stojaca kamera, bez kauzálneho tvrdenia
o zrýchlení alebo splnení požadovanej plynulosti. [Overenie fasádneho materiálu](unreal-facade-wood.md)
zahŕňa aj čerstvý readback 12 panelov, 10 materiálov a troch fotografických máp.

[Pokus so softvérovým Lumenom](../output/unreal/software-lumen-assessment/a9a7a4cb-40da-4d96-8761-6d54c266c3bc/README.md)
na predchádzajúcom balíku skončil pri B0 po strate fokusu (129/300 aktívnych
vzoriek). Výkonové porovnanie je neplatné a plánovaná A2 sa nespustila.
Obraz vykazuje výraznú zmenu vzhľadu tienidla a digestora; optická ekvivalencia
nebola preukázaná. Produkčne zostáva hardvérový Lumen, bez určenia víťaza testu.

Balík z **19:50 UTC** s novým drevom terasy prešiel
[denným meraním terasy](../output/unreal/runtime/foreground-terrace-day-5e3155f0-9181-4cb7-9de6-6074cde13603/foreground-qa.json):
1200 zahrievacích snímok, potom 300/300 vzoriek aplikácie aj okna v popredí,
natívny render 3840 × 2160 pri 100 %. Priemer **56,526 ms (17,69 fps)**,
P95 **61,431 ms**, GPU priemer **56,144 ms**. Exit 0, balík pred/po nezmenený.
Ide o jednu stojacu kameru, bez tvrdenia o zrýchlení materiálu alebo požadovanej
plynulosti. Podrobnosti materiálu a uložených UV sú v [zázname dreva terasy](unreal-deck-wood.md).

Následné [A/B/A porovnanie Metal plánovania](../output/unreal/metal-scheduling-audit/aba-result.md)
použilo starší nižšie uvedený balík z 18:56 UTC, 1 200 zahrievacích a 300 meraných
snímok, bez GPU profilera. Všetky tri behy mali 300/300 aktívnych vzoriek
a natívny 4K cieľ. `rhi.Metal.ConcurrentDispatch=1` dosiahol priemery
58,90 a 61,93 ms; prostredný beh s hodnotou `0` mal 64,44 ms.
Vizuálne porovnanie nezistilo zmenu kompozície ani zjavný výpadok materiálov.
Zrýchlenie sa nepotvrdilo a ponechávame hodnotu `1`. Rozdiel medzi oboma
referenciami zároveň bráni presnému tvrdeniu o kauzálnom percentuálnom vplyve.

Balík z **18:56 UTC**, s trávnikom a plynulým prepínaním deň/noc, prešiel
[bežným denným meraním interiéru](../output/unreal/runtime/foreground-interior-day-914e2333-55e7-40a8-acbc-63e1c9abc28f/foreground-qa.json)
bez zapnutého GPU profilera. Po 1 200 zahrievacích snímkach bolo všetkých
300 meraných snímok s aplikáciou, oknom aj klávesovým fokusom v popredí.
Render target zostal 3840 × 2160 pri 100 % rozlíšení. Priemer **62,18 ms
(16,1 fps)**, medián **61,80 ms**, P95 **66,81 ms**. Proces skončil s exit 0
a obsah balíka bol pred/po nezmenený. Toto je jedna stojaca kamera;
požadovanú plynulosť ani výkon pri pohybe tým nepovažujeme za dosiahnuté.

[Samostatný profil toho istého balíka](../output/unreal/runtime/profile-split-encoder-interior-day-b1598c87-8bcf-4964-8fb4-883a245dd01d/foreground-qa.json)
lokalizoval najväčšie skupiny GPU záťaže: TSR **17,671 ms**, Lumen screen
probe gather **17,587 ms**, dve fázy Lumen reflections **6,274 a 2,850 ms**.
Ide o inclusive časy oddelených skupín jednej snímky; nesčítavajú sa znovu
s ich podriadenými eventmi. TSR história mala 7680 × 4320 pri natívnom 4K
vstupe/výstupe. Profilovanie rozdeľuje Metal encodery a ovplyvňuje réžiu;
jeho časy slúžia na lokalizáciu nákladov, nie na produkčný výkon.
Neskorších 300 snímok tohto behu prešlo kontrolou popredia a 4K. Presný
stav fokusu a render targetu profilovanej snímky 300 nebol samostatne meraný.

Neúspešné pokusy zostali zachované: prvý profil mal 0/300 aktívnych snímok,
prvé bežné meranie aktivovalo aplikáciu až počas meraného intervalu.
Predĺžený warmup zmenil iba testovací beh, nie kvalitu ani zdroj aplikácie.

## Skoršie merania

Skorší balík, pred neskoršími úpravami svietidla, kamery a navigácie, prešiel štyrmi
[meraniami v popredí](../output/unreal/foreground-study/current-candidate-aa-comparison.json).
Všetky mali rovnaký balík, dennú stojacu kameru v obývačke, 600 zahrievacích
a 300 meraných snímok, aktívnu aplikáciu aj okno 300/300, natívny 4K cieľ,
HWRT, Lumen, Nanite a virtuálne tiene. Procesy skončili s exit 0.

| Režim v poradí merania | Priemer ms | Medián ms | P95 ms | GPU priemer ms |
| --- | ---: | ---: | ---: | ---: |
| TSR, história 200 % | 71,10 | 62,85 | 137,61 | 63,03 |
| TSR, história 100 % | 63,83 | 62,72 | 71,42 | 63,39 |
| TAA High, história 100 % | 53,00 | 47,12 | 98,84 | 46,81 |
| TSR 200 %, opakovanie | 74,24 | 69,45 | 116,14 | 68,82 |

TAA je v tomto pozorovaní rýchlejšie, no ani jeden režim nedosiahol priemer
alebo medián 33,33 ms. Referenčný medián sa pri opakovaní zmenil a behy
obsahujú veľké špičky. Bez kontrolovanej záťaže a teplotnej stopy nejde
o stabilný percentuálny prísľub zrýchlenia. Produkčné nastavenie zatiaľ
zostáva pôvodné; tieto stojace snímky nerozhodujú o kvalite pohybu.

Samostatný [GPU profil aktuálneho balíka](../output/unreal/runtime/profile-foreground-interior-day-66708e93-be28-49f9-a717-006c44b3aa37/gpu-top-exclusive.json)
zaznamenal 69,479 ms v jednej Graphics snímke. Jeho neskoršie meranie
prešlo 300/300 aktívnymi 4K snímkami, ale aktivita profilovanej snímky 300
nie je týmto neskorším záznamom dokázaná. [Kontrola Metal profilera](../output/unreal/metal-profiler-attribution-review-20260908.md)
ukazuje, že názov prvého clear/indirect-args eventu môže niesť čas celého
encoder bloku. Uvedených 19,417 ms pri `TSR ClearPrevTextures` preto
neinterpretujeme ako izolovanú cenu vymazania textúry.

Skorší [aktívny denný beh](../output/unreal/runtime/foreground-interior-day-32947092-4d7d-43bc-9563-e8e7805842aa/foreground-qa.json)
prešiel: **300/300** vzoriek aplikácie aj okna v popredí, bez zmeny aktivity,
po 600 zahrievacích snímkach. Počiatočná stopa má sampleIndex 0 a hernú snímku
601; posledné stavy sú aktívne. Samostatný render target zostal 3840 × 2160
pri 100 % rozlíšení počas celého merania. Priemer **62,38 ms (~16,0 fps)**,
P95 **67,14 ms**, GPU timer priemer **62,02 ms**. Ide o jednu statickú scénu
s HWRT a kuchynským drevom, ešte s pôvodným shaderom plameňa. Tento výkon
zatiaľ nepovažujeme za požadovanú plynulosť. Stopa vzorkuje konce intervalov;
nepreukazuje stav medzi vzorkami ani prekrytie okna. Native proces skončil
s exit 0 a obsah balíka prešiel kontrolou pred aj po behu.

Predchádzajúce denné a nočné testy fotografovaného kuchynského dreva vykreslili
skutočných 3840 × 2160, ale oba zaznamenali **0/300** vzoriek s aplikáciou
a oknom v popredí. Ich priemery 66,43 a 66,67 ms sú merania renderovania
na pozadí; nemožno ich prezentovať ako potvrdený interaktívny výkon.
Podklady a obrazová kontrola sú v [materiálovom zázname](unreal-furniture-materials.md).

Samostatný hostiteľ `output/unreal/foreground-study/capture.mjs` používa
existujúcu natívnu kontrolu státia a vyžaduje aktívnu aplikáciu aj herné okno
počas všetkých 300 snímok. Prvé dva procesy skončili čisto, ale tento prísnejší
výkonový predpoklad nesplnili: [prvý](../output/unreal/runtime/foreground-interior-day-e08864ea-9475-4723-8a3c-c27c77e67a5e/foreground-qa.json)
mal 220/300 aktívnych vzoriek; [druhý](../output/unreal/runtime/foreground-interior-day-a8c938e5-7404-4041-b89f-45217f4e9f01/foreground-qa.json)
115/300. Titulok presne identifikovaného bežiaceho okna bol aktivovaný cez CUA
bez zmeny kamery. Súhrnné počty neukazujú smer zmeny fokusu, takže príčina
nie je potvrdená. Ani jeden beh sa nepovažuje za úspešné meranie v popredí.

Diagnostický zdroj zaznamenáva počiatočný stav a každú zmenu aktivity
s poradím vzorky, hernou snímkou a monotónnym časom. Nový záznam bol natívne
zostavený a overený vyššie uvedeným behom; pôvodné reporty sa spätne nemenia.

Pracovný záznam z 8. septembra 2026. Výsledky sú lokálne na MacBook Pro M5 Pro
(20 GPU jadier, 48 GB), macOS 26.6.2, UE 5.8.2 a Metal SM6. Nejde o dôkaz
fotorealizmu, potvrdenie stavebným úradom ani publikovanú distribúciu.

## Overené vrstvy

- Export zachováva 1 895 identít: 1 878 aktívnych objektov a 17 archívnych/pomocných.
- Khronos glTF kontrola oboch GLB skončila bez chýb a varovaní.
- Natívny import meria každý objekt; maximálna odchýlka bounds bola
  0,0009765625 cm, teda 0,009765625 mm. Kanonické integer mm zostávajú v sidecare.
- Samostatná `.app` obsahuje runtime knižnice, pak/IoStore, descriptor, ICU aj
  kamerové dáta. Podpis prešiel `codesign --verify --deep --strict`.
- Pri každom nižšie uvedenom meraní bol viewport 3840 × 2160, screen percentage
  aj secondary screen percentage 100 a dynamic resolution vypnuté. Fyzický
  vstavaný displej má 3456 × 2234; meranie UHD render targetu nie je fyzický UHD displej.

## Prvý použiteľný denný profil

Táto séria predchádza oprave textúr strechy/PV, optických shaderov a živého plota.
Každý statický pohľad mal 240 zahrievacích a 300 meraných snímok. Uloženie PNG sa
do časov nezapočítava. Merania nemajú súbežne otvorenú druhú BreziTwin aplikáciu.

| Pohľad | Lumen | Priemer FPS | P95 snímky |
| --- | --- | ---: | ---: |
| Ulica | Software | 20,8 | 48,74 ms |
| Obývačka | Software | 20,6 | 49,35 ms |
| Terasa | Software | 23,1 | 43,84 ms |
| Bazén | Software | 23,7 | 42,81 ms |
| Ulica | Hardware RT | 22,1 | 45,71 ms |
| Obývačka | Hardware RT | 20,3 | 49,87 ms |

Podklad: [baseline-qa.json](../output/unreal/baseline-qa.json). Jednotlivé JSON,
PNG a hashe použitého balíka sú v `output/unreal/runtime/<invocation>/`.
Výkon zatiaľ nespĺňa požadovanú plynulosť. Statické presety nenahrádzajú meranie
chôdze, orbitu, prechodov alebo obnovy po minimalizácii.

## Chyby zachytené skutočným spustením

1. UAT bez `-package` archivoval development executable bez runtime dát,
   hoci vrátil exit 0. Runner už vyžaduje krok package a kontroluje payload.
2. Aktivované RT vyžaduje číselné `r.SkinCache.CompileShaders=1` a nový cook.
3. Python `unreal.Rotator` má pozičné poradie roll/pitch/yaw. Slnko sa ocitlo
   pod horizontom. Importér používa pomenované parametre a meria skutočný vektor.
4. 22 scalar material instances nemalo uložený Nanite usage flag. Explicitné
   override a uloženie odstránili všetky runtime hlášky o náhradnom materiáli.
5. Sandboxed aplikácia nemôže zapisovať do ľubovoľnej pracovnej cesty. QA používa
   vlastný kontajner a potom kopíruje dôkazy do workspace.
6. Jeden náhľad spustený mimo benchmarku skreslil samostatnú sériu. Táto séria
   je vyradená. Runner odmieta QA pri už spustenej BreziTwin.
7. Opakované vymazanie materiálového grafu cez hromadné editorové API nechávalo
   časť uzlov. Voda mala tri výstupy Single Layer Water a Metal použil náhradný
   materiál, hoci UAT vrátil exit 0. Generátory teraz mažú snímku zoznamu uzlov
   jednotlivo. Dva natívne rebuildy zachovali presne jeden vodný výstup a následný
   cielený Mac SM6 cook prešiel bez chýb/varovaní so všetkými 58 master shader maps.
   Samotný tento cielený cook ešte neoveruje vodu vo výslednom obraze.
8. Jedna profilovaná séria dokončila všetkých 300 snímok aj 4K PNG, potom spadla
   pri ukončovaní AX časovača. Je označená `capture-complete-exit-crash` a nie je
   dôkazom bezchybného ukončenia. Oprava zastaví AX cache pred výmenou Slate
   handlera. Nový balík a následné denné HWRT merania už ukončili proces s exit 0.
9. Unicode názov okna spôsobil automatický UTF-16 výstup JSON cez FileHelper.
   Runtime meranie prešlo, hostiteľský parser ho odmietol. Diagnostické JSON
   a GPU logy teraz explicitne používajú UTF-8; nový balík prešiel aj hostiteľským spracovaním.
10. Nenamedované vypnutie kolízií sa po ďalšom editorovom authoringu mohlo obnoviť
    z predvoleného BodySetup. Explicitný profil `NoCollision` a kontrola po všetkých
    authoring krokoch teraz overujú 349 kanonických kolíznych objektov a 12 podpier.
    Samostatných 57 skrytých pôvodných kolíznych mesh objektov sa následne importovalo
    oddelene bez zmeny 1 895 kanonických objektov. Import po uložení a novom otvorení
    mapy overil ich presné trojuholníky, bounds, profily aj neviditeľnosť. Nový zabalený
    runtime potvrdil aj existenciu pripravených fyzikálnych triangle mesh dát.
11. Fixný scene target pôvodne rozťahoval aj macOS okno. Základný GameEngine kopíroval
    jeho veľkosť do systémového rozlíšenia a MoviePlayer každú snímku obnovoval obsah
    okna. Vnútorný scene viewport teraz drží samostatný 3840 × 2160 cieľ v stabilnom
    vonkajšom hostiteľovi; rozhranie sa zmestí do okna a zachováva pomer 16 : 9.
    Pokus `0fa801e1-…` spadol pri AX shutdown a pokus `66a1df14-…` počas merania
    menil veľkosť viewportu. Oba sú vyradené z akceptovaného merania.
12. AX cache mohla dostať oneskorené ParentChanged udalosti po prvom vyčistení.
    Aplikácia teraz zastaví producentov pred odstránením widgetov, spracuje čakajúce
    GT/main-thread udalosti a až potom vyčistí cache. Nasledujúce uličné a interiérové
    merania skončili s exit 0 bez zásahu do systémového VoiceOver nastavenia.

Pri profilovaní bolo potvrdené, že predvolená TSR história 200 používa
7680 × 4320 pri natívnom výstupe 3840 × 2160. Kontrolované porovnanie rovnakého
balíka už prebehlo pri zachovaní plného 4K renderovania. Metal priraďuje GPU čas aj širším
encoderom; názvy lacných `Clear…` listových udalostí preto nemožno interpretovať
ako presnú cenu samostatného kernelu. Rozhodujú širšie skupiny, celá snímka
a meranie jednej zmeny.

## Rovnaký balík: kontrolované porovnanie rendereru

Všetky tri pouličné merania majú identické hashe všetkých 36 súborov balíka,
240 zahrievacích a 300 meraných snímok, aktívne okno a natívny 4K viewport.

| Nastavenie | Priemer snímky | Priemer FPS | P95 snímky |
| --- | ---: | ---: | ---: |
| HWRT inline, TSR história 200 | 46,83 ms | 21,35 | 50,10 ms |
| HWRT inline, TSR história 100 | 43,19 ms | 23,16 | 46,44 ms |
| HWRT ray generation, história 100 | 47,83 ms | 20,91 | 51,05 ms |

Podklad: [controlled-street-renderer-comparison.json](../output/unreal/controlled-street-renderer-comparison.json).
Ray generation bol potvrdený skutočnými GPU udalosťami `HardwareRayTracingRGS`
a `ReflectionHardwareRayTracingRGS`. Bol pomalší; predvolený inline režim zostáva.
História 100 znížila čas snímky asi o 7,8 %. Ide o jednu statickú sériu na konfiguráciu;
variabilita opakovaných behov a kvalita obrazu v pohybe nie sú týmto potvrdené.

## Státie a manuálne ovládanie

Zabalený runtime so všetkými 57 skrytými kolíziami prešiel vstupom do obývačky
a státím cez skutočný CharacterMovement:
541 podopretých vzoriek, žiadna nepodopretá vzorka, žiadny vodorovný posun, oči vo výške
165 cm s nulovou zaznamenanou chybou. Použité boli presné kanonické
podlahy vrátane koplanárnej podpery; geometria domu sa nemenila.
Podklad je v `output/unreal/runtime/walking-interior-standing-hwrt-5fa57033-fa67-495e-8a5d-79602b6332a8/`.
Státie nepreukazuje priechod po trase ani chovanie pri stenách.

Manuálne AX kliknutie na Obývačku zmenilo pohľad, F1 zobrazilo ovládanie a Escape
ho zavrelo. M preplo režim chôdze. Zároveň sa odhalilo orezanie UI, pretože vynútené
4K okno presahovalo vstavaný displej, a prítomnosť skrytých help/error uzlov v AX strome.
Fixný 4K scene target v okne prispôsobenom displeju už prešiel natívnym meraním.
Explicitné odpájanie skrytých podstromov prístupnosti je zostavené; nové manuálne
overenie AX stromu a ovládacích prvkov zostáva samostatným krokom.

Na obrazovke sa zobrazilo aj varovanie o clippingu cache osvetlenia pri expozícii EV 12,3.
Konfigurácia `r.EyeAdaptation.CachedLightingPreExposure=8` rozširuje podporovaný rozsah
cache podľa lokálneho zdroja UE 5.8 na EV −4 až 16. Render thread nového denného
interiérového merania zaznamenal EV 9,909 v podporovanom rozsahu, bez pôvodného
varovania. Toto neoveruje clipping jednotlivých pixelov ani nočný režim.

## Fixné 4K v okne prispôsobenom displeju

Séria `street-day-hwrt-history100-af1c469e-4ec1-4d65-8224-7a25ba8ca819`
prešla nezávislým `presentation-qa.json`: samostatný CPU aj RHI target zostal
3840 × 2160 vo všetkých 300 vzorkách, obe renderovacie percentá 100, dynamické
rozlíšenie vypnuté. Okno bolo 1600 × 900 fyzických obrazových bodov, celkom v pracovnej
ploche displeja; pomer strán zostal 16 : 9. Export scény mal skutočne 3840 × 2160.
Proces skončil s exit 0. Priemer 45,679 ms (21,89 FPS), P95 48,060 ms, TSR história 100.

Interiérové státie vyššie zaznamenalo rovnaké natívne rozmery scény a správne osadenie
okna. Pri predvolenej TSR histórii 200 malo priemer 56,078 ms (17,83 FPS), P95 58,586 ms.
Tieto rozdielne pohľady a nastavenia nie sú kontrolovaným porovnaním výkonu.
Žiadne z týchto meraní ešte nespĺňa cieľ plynulého fotorealistického produktu.

## Pohyb pri stene a zatvorených dverách

`walking-traversal-hwrt-04ad9176-ac63-4c41-bd63-e0c704d6831d` prešiel všetkými
12 prípadmi: šesť zdrojovo odvodených prístupov z oboch strán k DOM_00486,
DOM_00545 a DOM_00553 pri 20 aj 60 Hz simulácie. Skutočný CharacterMovement posunul
postavu o 37,900–37,907 cm a zastavil ju s odstupom stredu kapsuly 22,093–22,100 cm
od nameranej roviny prekážky (polomer kapsuly 22 cm). Žiadny prienik, nepodopretá
vzorka ani zaznamenaná chyba výšky očí. Držanie W trvalo dva simulačné sekundy,
uvoľnenie zastavilo pohyb a Escape obnovil kurzor aj pôvodný fokus vo všetkých prípadoch.
Každá pohybová vzorka mala samostatný 4K CPU/RHI target pri 100/100 percentách.
Proces skončil s exit 0; hashe celého balíka boli rovnaké pred aj po spustení.

Predchádzajúci beh `05f27de5-…` bol správne odmietnutý pre variabilný simulačný čas.
Distribuovaný engine má kompiláciou podmienený FApp fixed-step prepínač; test teraz
používa verejné `UEngine::bUseFixedFrameRate`/`FixedFrameRate`, overuje skutočný delta
čas každého ticku a po skončení obnoví pôvodné nastavenia. Celý úspešný beh trval
74,24 s skutočného času. Simulačných 60 Hz neznamená vykreslených 60 FPS.

## Manuálna macOS relácia po oprave okna

`output/unreal/manual-ui-20260908/manual-qa.json` a priložené PNG/AX texty zachytávajú
aktiváciu presetov, F1/Escape, deň/noc, prepnutie orbit/chôdza, viditeľný posun fokusu
cez Tab, natívny fullscreen a návrat do okna. CmdQ ukončil proces; log dosiahol
`Game engine shut down` a `Exiting` bez assertion/fatal chyby. Skryté help/error
ovládače v zavretom stave nie sú v AX strome. Stále sa odhalilo otvorenie pomoci
odrolované k nastaveniu pohybu a AX fokus zostávajúci na okne napriek modrému
Slate označeniu tlačidla. Tieto opravy vyžadujú ďalší build a opakovanú manuálnu QA.
Veľmi krátke jednotlivé klávesové udalosti nepreukázali súvislý pohyb WASD/šípkami;
číselné skratky ani VoiceOver hlasový výstup sa nepovažujú za overené.

## Zostávajúca akceptácia

Výkonový pokus `--sort-trace-tiles` zachováva množstvo Lumen lúčov a mení iba
ich poradie. Kontrolovaný pár `6d5c767f-…`/`dcda1e51-…` mal rovnaký zabalený
obsah, 300 meraní v popredí a stabilné 4K. CVar 0/1 aj skutočný GPU pass boli
zaznamenané. Priemer 45,673/45,718 ms nepreukázal zrýchlenie; predvolená hodnota
ostáva nezmenená. Celý podklad je `output/unreal/radiance-sort-comparison.json`.

Ďalšie voliteľné experimenty `--taa` alebo `--smaa` vyžadujú `--profile-gpu`
a nekombinujú sa s TSR voľbou `--history-100`. `antialiasing-qa.json` vyžaduje
zhodu požadovaného, zloženého a renderovaného AA režimu aj vykonané GPU passy.
TAA má kvalitu High, históriu 100 a vypnutý upsampling; SMAA je priestorový 1×
režim Ultra bez jitteru. Obe možnosti zachovajú renderovanie 3840 × 2160 pri
100/100 percentách. Ide o porovnávacie režimy, nie zmenu predvolenej kvality;
statický záber nepreukazuje rovnakú ostrosť ani stabilitu pri pohybe.

Dodatočná kontrola startup logov vyššie uvedených behov našla nefatálne
`Ensure condition failed: SlateViewport.IsValid()` pri registrácii vonkajšieho
viewportu. Namerané rozmery, časovanie a fyzikálne výsledky zostávajú platnými
čiastkovými pozorovaniami, ale tieto behy nie sú dôkazom bezchybného štartu.
Nové QA kontroly odmietajú aj handled ensure pri exit 0. Oprava registračného
rozhrania vonkajšieho viewportu vyžaduje nový build a natívne opakovanie.

Toto opakovanie už absolvoval balík z `stove-ax-viewport-package.log`
(UAT 98,89 s, kontrola obsahu/podpisu a zdrojových hashov úspešná).
`walking-interior-standing-hwrt-4b02817e-b9c5-4a5c-ad76-d754169c4637`
prešiel státím aj samostatnou sprísnenou presentation kontrolou bez ensure,
shader fallbacku a fatálnej chyby. Vonkajší viewport má platné rozhranie;
CPU/RHI scéna ostala 3840 × 2160, okno 1600 × 900 bolo celé na displeji.
Priemer 57,286 ms (17,46 FPS), P95 59,656 ms stále nespĺňa cieľ plynulosti.

Relácia `output/unreal/manual-ui-20260908-v2/` preukázala správny natívny AX
fokus na ovládačoch, otvorenie pomoci od nadpisu a návrat fokusu cez Escape.
Prešiel preset bazéna, nočný režim, fullscreen/návrat a CmdQ s exit 0.
Odhalené bolo neposunutie scrollboxu za fokusom pri Tab. Opravu už overila
relácia `output/unreal/manual-ui-20260908-v3/` v balíku z 03:58 UTC: Motion aj
System sa pri výbere posunuli do viditeľnej časti, F1 začalo od nadpisu a Escape
vrátilo natívny fokus na Ovládanie. Objavila sa ďalšia chyba: Tab na poslednom
prvku neuzavrel cyklus späť na Zavrieť. Táto oprava ešte vyžaduje nový build.
CUA Shift+Tab opakovane vybralo ďalší prvok; prijaté modifikátory zatiaľ nie sú
zmerané, preto sa smer neposudzuje ako preukázaná chyba fyzickej klávesnice.
Číselná skratka zostáva nepotvrdená. VoiceOver hlas
ani súvislé fyzické klávesnicové ovládanie sa touto reláciou necertifikujú.
Stock UE TSR tiež loguje varovanie pri čítaní `r.MotionVectorSimulation` na
render threade; nejde o pôvodný viewport ensure a engine sa v tomto kroku nemenil.

## Opakovaný AX startup pád a oprava inicializátora

Balík s aditívnym plameňom a preview Tab opravou znovu spadol pri štarte:
`walking-interior-standing-hwrt-f78ab873-4eb6-4490-b9ad-7d85c8b5ab36`.
[Log](../output/unreal/runtime/walking-interior-standing-hwrt-f78ab873-4eb6-4490-b9ad-7d85c8b5ab36/process.log)
zaznamenal aktiváciu AX po troch stabilných snímkach viewportu a následné
`MacAccessibilityElement.cpp:169` assertion. [Natívny crash report](../output/unreal/runtime/walking-interior-standing-hwrt-f78ab873-4eb6-4490-b9ad-7d85c8b5ab36/native-crash.ips)
ukázal `FMacAccessibilityElement dealloc → _Block_release` na GameThread počas
spracovania Cocoa fronty. Predchádzajúce úspešné štarty preto nepreukázali
odstránenie tejto chyby; samotné oneskorenie bootstrapu neriešilo vlastníctvo objektu.

Lokálny UE inicializátor `initWithId:` zachytával `self` v bloku pre GameThread
prostredníctvom vnoreného bloku pre hlavné vlákno. Po odstránení objektu z cache
mohlo posledné uvoľnenie nastať na GameThread. Oprava v `BreziAXInitializer.mm`
nahrádza iba tento inicializátor v procese aplikácie. Objective-C `+load` ju
inštaluje pred `main` samostatnej aplikácie, čím pokrýva aj poradie inicializácie
pri už zapnutom systémovom VoiceOver; tento systémový stav ešte nebol natívne testovaný.
Kontroluje presnú verziu UE 5.8.2, CL 56702186, signatúru metódy a rozloženie triedy.
Medzi vláknami prechádzajú iba ID, generácia a skopírované hodnoty; aktualizácia
na hlavnom vlákne vyžaduje stále existujúci objekt s rovnakou generáciou.
Roly, skrytie hesla a režim iba na čítanie zostali zachované. Jediný zápis do
interného cached-role ivaru používa verejné Objective-C runtime API, pretože
distribuovaný ApplicationCore nesprístupňuje jeho offset symbol pri Editor linkovaní.
Pôvodný `dealloc` aj súbory enginu zostali nezmenené. Oprava sa počas procesu
neodpája; zmena enginu alebo živé odpojenie modulu vyžadujú novú kontrolu.

Nový zabalený beh `interior-day-hwrt-5f391861-fa5d-4d5d-aea4-683a54b70584`
prešiel s `--hwrt --ax-init-stress`, 240 zahrievacími a 300 meranými snímkami,
samostatnou scénou 3840 × 2160 pri 100/100 percentách a uloženým 4K PNG.
Proces skončil s exit 0 bez assertion, ensure alebo fatálnej chyby; obsah balíka
bol po behu nezmenený. [AX receipt](../output/unreal/runtime/interior-day-hwrt-5f391861-fa5d-4d5d-aea4-683a54b70584/ax-initializer.json)
a [nezávislá kontrola](../output/unreal/runtime/interior-day-hwrt-5f391861-fa5d-4d5d-aea4-683a54b70584/ax-initializer-qa.json)
potvrdili inštaláciu cez `+load`, 49 zaradených inicializácií, jednu aplikovanú
aktualizáciu, 32 odmietnutí chýbajúceho Slate ID, 16 odmietnutí chýbajúcej native
cache položky, 16 odmietnutí starej generácie a jedno odmietnutie pri ukončovaní.
Po vyprázdnení front zostalo `outstanding=0`. Hashe receiptu, runtime JSON,
[procesného logu](../output/unreal/runtime/interior-day-hwrt-5f391861-fa5d-4d5d-aea4-683a54b70584/process.log)
a PNG sa zhodujú s uloženou `invocation.json`.

Voliteľný stress test používa 16 ID, ktorých neprítomnosť overí v Slate aj native
cache. Pre každé vytvorí a odstráni dve položky a odmietne aktualizáciu so starou
generáciou: overené počty sú 16/32/16. Nevynucuje konkrétne časovanie pôvodného
pádu, pretože synchronizované volanie hlavného vlákna môže priebežne spracovať
GameThread frontu. Je dôkazom týchto odmietacích vetiev a skutočného čistého
ukončenia, nie dôkazom odstránenia všetkých možných AX race podmienok. Tento beh
pozoroval fokus okna; ovládanie všetkých tlačidiel, nový obojsmerný Tab cyklus
a hlasový výstup VoiceOver zostávajú samostatnou manuálnou akceptáciou.

## Tenké sklo a namerané AA režimy

Balík z `thin-glass-help-aa-package.log` (03:58:00 UTC, UAT 93,11 s) prešiel
importom, cookom, kontrolou podpisu a obsahu. Dvadsať architektonických skiel
a jedno krbové sklo používajú režim bez posunu vzorky refrakcie (`RM_NONE`).
Ich tvar, odrazy, Fresnel odvodený z IOR 1,52, tint a drsnosť zostali zachované.
Tým sa odstránil veľký obrazovkový posun za sklom, ktorý pri tenkých povrchoch
nezohľadňoval fyzickú hrúbku. Sprchové sklo a bazénový shader sa nemenili.
Nejde o model nameranej skladby izolačného zasklenia.

Skutočný 4K záber `walking-interior-standing-hwrt-7eabe067-…` už nemá predchádzajúce
veľké obdĺžnikové posuny cez terasové presklenie. Státie aj sprísnené štartovacie
kontroly prešli, priemer 56,670 ms, P95 59,327 ms pri predvolenom TSR. Interiér
stále potrebuje vizuálne zlepšenie; zmena optiky sama nepotvrdzuje fotorealizmus.

Nasledujúce uličné merania používajú presne rovnaký zabalený obsah. Každé má
240 zahrievacích a 300 meraných snímok, aktívne okno/fokus vo všetkých vzorkách,
samostatný 3840 × 2160 CPU/RHI target a nastavenia 100/100 bez dynamickej mierky.

| Režim | Priemer snímky | P95 snímky |
| --- | ---: | ---: |
| HWRT inline, TSR história 100 | 45,414 ms | 47,818 ms |
| HWRT inline, TAA High, história 100 | 34,013 ms | 36,407 ms |
| HWRT inline, SMAA Ultra 1× | 33,453 ms | 35,718 ms |

Podklad: [antialiasing-comparison.json](../output/unreal/antialiasing-comparison.json).
TAA aj SMAA prešli zhodou požadovaného, zloženého a skutočne renderovaného režimu;
GPU profil potvrdil TAA Main 3840 × 2160 → 3840 × 2160 a všetky tri SMAA passy.
Jedna profilovaná zahrievacia snímka mala TAA pass 0,831 ms a SMAA skupinu
0,569 ms; nejde o priemer passov z 300 výkonových vzoriek. Toto je jedna statická
séria na režim. Predvolené TSR 4/história 200 zostávajú, kým nebude overená
stabilita hrán a detailov pri pohybe. Žiadny záznam nepreukazuje 60 FPS.

Po každej materiálovej a UI revízii treba nový import/cook a natívny render.
Samostatne zostáva vizuálna kvalita skla, vody a kaustík, vegetácia, kvalita
interiérových detailov, výkon pri pohybe a natívna klávesnicová/VoiceOver QA.
Implementácia chôdze cez CharacterMovement už prešla Editor kompiláciou.
Státie v obývačke a vyššie uvedených 12 priamych prístupov k prekážkam už prešli.
Diagonálne kĺzanie pri stenách, schody, okraje, ostatné trasy a súvislé natívne
klávesnicové ovládanie stále vyžadujú vlastné testy.
Príkaz `npm run unreal:traversal-fixtures` znovu odvodí polohy z aktuálnych trojuholníkov;
`npm run unreal:traversal-qa -- output/unreal/traversal-fixtures/cases.json --hwrt`
spustí samostatný zabalený proces a zachová dôkazy aj pri zlyhaní. Počet simulačných
krokov nie je dôkaz skutočných 20/60 FPS. Otváranie dverí zatiaľ nie je implementované.

### Help navigation and source collision retest

`output/unreal/manual-ui-20260908-v5/manual-qa.json` records the observed packaged
process PID 18022, clean exit 0, unchanged bundle and 22 applied native AX
initializations with zero outstanding work at shutdown. F1 focuses Close;
Tab cycles Close → Motion → System → Close, scrolling each focused control
into view. Targeted Quartz events with the native left-device Shift flag
verify the reverse cycle System → Motion → Close → System. Native key traces,
AX focus and screenshots agree. Escape removes help nodes and restores Controls.
The test does not certify VoiceOver speech or a physical keyboard.

CUA `shift+Tab` and a generic Quartz Shift mask arrived in Slate as `shift=0`.
The installed engine's `FMacApplication::ConditionallyUpdateModifierKeys` reads
left/right device bits, not just the generic modifier. The second targeted
helper supplies the left-device bit and the trace records `shift=1` for all
three reverse transitions. No application input behavior was changed for this
verification.

A preceding cold launch in `manual-ui-20260908-v4` failed before engine logs.
Its observed child PID 17049 crashed in an LLM allocation scope while another
thread cleared LLM tracking state. CUA subsequently showed another instance;
v4 UI images therefore do not prove the failed child's behavior. The v5
launcher waits for positive initialization evidence before attaching CUA.
This preserves test provenance but does not repair the separate cold-start
LLM race. The subsequent public `-LLM` study is recorded below.

`output/unreal/runtime/walking-traversal-hwrt-1f267a2e-1172-4dbb-8370-d38b98f14415/`
passes the stricter packaged traversal gate: all 12 source-derived wall/closed-
door approaches at 20/60 simulation Hz, clean exit and no handled ensure.
This replaces the historical handled-ensure run as current bounded traversal
acceptance. It does not cover every route, diagonal, step/drop or physical
keyboard path, and simulation Hz is not measured display FPS.

### Bounded startup tracker study

`output/unreal/llm-startup-study/runs/2026-09-08T05-26-55.100Z-bdbc76b6-69fd-4d78-8fd4-a2751ff3c603/`
contains five alternating default/`-LLM` pairs from the same frozen TV oak
package. Every process exited 0 after 240 warmup and 240 measured frames; the
native 3840 × 2160 scene and drained AX lifecycle gates passed. A prewarmed
helper targeted each actual PID and process birth identity. All early no-reply
open AppleEvents returned −600; subsequent LaunchServices activation requests
were accepted before initialization was observed in buffered engine output.
This does not establish actual event delivery or overlap with the original race.

The original gate incorrectly searched only stdout for LLM's positive startup
message. Its five failed LLM reports remain untouched. The exact message exists
in all five hash-bound `saved/Logs/BreziTwin.log` files, with final profiler
metadata `llm=1`; default arms finish at `llm=0`.
`output/unreal/llm-startup-study/revalidations/cd8b93ac-bbe8-41cf-aa89-7f165c2f241c/report.json`
revalidates the same original processes, matching log hashes, byte counts,
command lines and isolated user directories, and verifies that the complete
original evidence inventory stayed unchanged. No additional native runs were
performed for this parser correction.

The mean of five per-run game-thread active means increased from 0.8478 to
1.1600 ms: +0.3122 ms, with all paired differences positive. The corresponding
frame interval means were 59.3363 and 60.2678 ms, but paired differences ranged
from −1.083 to +4.432 ms with GPU drift. The frame difference is not isolated
LLM cost. Memory overhead was not measured. Both arms also include
`-DetectHitchesWithLLM`, preserving the engine's hitch detection behavior.

The original crash was not reproduced in either arm. Keeping LLM active avoids
the identified startup tracker-clear path in the inspected engine source; ten
clean launches do not prove elimination of the race or general reliability.
This study used fresh processes with warm caches and does not demonstrate
smooth motion or a performance target.

## Metal profil s rozdelenými compute encodermi, 8. september 2026

[Samostatný diagnostický beh](../output/unreal/runtime/profile-split-encoder-interior-day-a93c3a38-efb6-41fc-878f-05381bb5f8ce/foreground-qa.json)
prešiel s `rhi.Metal.SampleComputeEncoderTimings=1`, exit 0 a neskoršími
300/300 aktívnymi 4K vzorkami. Rozdelenie encoderov mení plánovanie aj náklady;
čas snímky 67,484 ms a neskoršie časové distribúcie nie sú produkčným meraním.
Profilovaná zahrievacia snímka 300 stále nemá spárovaný dôkaz fokusu a cieľa.

Samostatné atribúcie teraz ukazujú `TSR RejectShading` **8,902 ms**, aktualizáciu
TSR histórie 7680 × 4320 **5,228 ms**, Lumen screen tracing **4,332 ms**,
krátkodosahové AO **2,978 ms** a screen-probe HWRT **2,935 ms**.
`TSR ClearPrevTextures` má 0,232 ms, príprava indirect argumentov 0,004–0,005 ms
a vymazania radiance-cache zdrojov po 0,004 ms. To podporuje predchádzajúce
vysvetlenie zdieľanej encoder atribúcie; nejde o izolované ceny shaderov ani
preukázané zrýchlenie. Rodičovské a vnorené GPU riadky nesčítavame.

[Zdrojový rozbor a ďalší malý experiment](../output/unreal/metal-split-profile-review/review.md)
navrhuje iba zmenu poradia existujúcich radiance-cache trace tiles, bez zníženia
rozlíšenia, počtu lúčov alebo kvality histórie. Táto cache skupina mala v profile
iba 0,650 ms; nie je podklad na prísľub významného zrýchlenia. Produkčné
nastavenia sa týmto zápisom nemenia. Predchádzajúce dva split-profile behy
[0/300](../output/unreal/runtime/profile-split-encoder-interior-day-5a7c0616-a7ce-419c-a329-cd7a316cef73/foreground-qa.json)
a [185/300](../output/unreal/runtime/profile-split-encoder-interior-day-2ad3a411-8b0d-4920-a5e7-bdbbcfef38a9/foreground-qa.json)
aktívnych vzoriek zostávajú zachované a vyradené z merania v popredí.


### Clean lens and visible navigation action — 2026-09-08

The packaged process in `output/unreal/manual-ui-20260908-v7/manual-qa.json`
(PID 62948) completed the bounded native UI checks and quit through the app menu
with exit 0, no timeout, no logged runtime assertion/ensure/fatal, unchanged
packaged payload and a drained AX initializer. The navigation button changes its
visible and accessible text when entering; Escape restores the cursor and focus.
Walking enters the source floor DOM_00421 and presents “Začať chôdzu”.
Terrace, pool and street buttons reach distinct settled views. Main Tab wraps
from navigation to night mode; help disables navigation and ignores F2 until
closed. An F2/Right sequence visibly changes the camera. These CUA key events
do not certify a physical keyboard or full walking traversal.

The 3840 × 2160 night PNG in the same directory shows the camera's new zero-bloom
policy removing the large fixture halo. It retains the 800 lm source and existing
exposure. The globe is still bright/clipped. Night-to-day switching briefly
overexposes before adaptation settles; smooth exposure transition remains open.
The initial v7 benchmark finished before native key interaction and reports
0/300 foreground samples, so its timing is not accepted as foreground performance.
AX Raise/press alone did not activate NSApp; a targeted Escape key did.
Immediate AX snapshots may lag the visible bound label because the macOS cache
refresh is asynchronous; settled snapshots showed the expected state.

A follow-up unchanged-package v8 capture (PID 64143, clean menu Quit exit 0)
kept the game window and scene keyboard focus active for all 300 samples.
Scene/RHI textures remained 3840 × 2160 with native render percentages.
Mean frame interval was 69.10 ms (about 14.47 FPS), p95 73.50 ms. The separate
NSApp/workspace foreground conjunction remained false in all samples; its cause
is not isolated, and this does not pass the full foreground acceptance gate.
Evidence: `output/unreal/manual-ui-20260908-v8/benchmark-qa.json`. This timing
is descriptive, not a matched optimization result or a 30/60 FPS acceptance.


### Exposure reset on day/night change

The subsequent bundle (`day-night-camera-cut-package-1.log`, UAT exit 0,
104.39 seconds) adds one public camera-cut notification after the existing
light toggle. This asks UE5.8 eye adaptation to use the new target immediately
and also resets temporal history. It introduces no light/exposure endpoints,
quality changes or animation. Regression checks passed: 439 Node, 33 oak and
69 pendant tests (`day-night-camera-cut-tests-1.log`).

Native process 70290 in `output/unreal/manual-ui-20260908-v9/manual-qa.json`
reached fixed-4K presentation and tested both lighting directions on the terrace.
The first observed CUA snapshot after night-to-day no longer showed the broad
white image. It still showed briefly flat indirect lighting and a grey sky
before the normal day image settled. Asynchronous screenshots do not prove
every transition frame. The change is retained as an exposure-reset correction;
premium transition acceptance remains open. Quit exited 0 without timeout or
logged runtime failure, with unchanged payload and a drained AX lifecycle.

### Rovnaký pohyb kamery s TSR históriou 200/100, 8. september 2026

Hostiteľ `scripts/unreal/motion-qa.mjs` teraz explicitne nastaví históriu 200 pre
`capture tsr` a 100 pre `capture tsr100`. Požiadavku porovnáva s natívnou
hodnotou aj pri opätovnom načítaní uloženého behu. Výnimka z porovnania kvality
platí iba pre dvojicu TSR4/100 ↔ TSR4/200; ostatné nastavenia a pôvod balíka
sa musia zhodovať. Zmenu pokrýva 59 úspešných testov vrátane odmietnutia
nesprávnej histórie a zachovania presných pôvodných príkazov starších záznamov.

Balík s čistou optikou, navigačným tlačidlom a jednorazovým resetom
expozície zachytil obe kompletné sekvencie:

- [TSR 200](../output/unreal/runtime/motion-tsr-ace7feae-5699-43b1-85c0-1f3f26b5c463/motion-qa.json), PID 75511.
- [TSR 100](../output/unreal/runtime/motion-tsr100-627c97ae-e2cc-4465-9799-a12e3631e49e/motion-qa.json), PID 76089.
- [Porovnanie](../output/unreal/runtime/motion-comparison-cbee376f-68e4-42a2-b1d7-4a108ce9d585/comparison.json) a [prehliadač snímok](../output/unreal/runtime/motion-comparison-cbee376f-68e4-42a2-b1d7-4a108ce9d585/index.html).

Oba procesy skončili s exit 0 bez timeoutu, runtime chyby alebo zmeny balíka.
Každý obsahuje 64 po sebe idúcich PNG 3840 × 2160 so spárovanými GT/RT
identitami a rovnakou kanonickou kamerou terasa → bazén. Porovnanie prešlo
bez chýb. Rozdiel expozície bol približne 0,009 EV; čas materiálov zostáva
samostatne zaznamenaný. Voda a pohyblivá zeleň preto nie sú podkladom pre
číselné porovnávanie statických hrán.

Ide o pevný simulačný krok, nie meranie reálnych FPS. Natívna hodnota CVar
a 4K PNG samy nepotvrdzujú vnútorné rozmery textúr histórie. Prvé celé náhľady
neukázali hrubý rozdiel kompozície, ale nepredstavujú úplnú kontrolu ostrosti
a stability pri zobrazení 1:1. Víťaz kvality nie je určený a produkčné TSR
200 zostáva zachované; skoršie meranie interiéru nepreukázalo stabilnú GPU
úsporu pri histórii 100.

### Plynulý prechod deň/noc, 8. september 2026

Nový controller rozloží zmenu svetiel na tri sekundy. Otočenie slnka používa
kvaterniónovú interpoláciu, intenzity logaritmickú interpoláciu a priebeh má
plynulý začiatok aj koniec. Opätovné prepnutie vychádza zo skutočných
rozpracovaných hodnôt. Dočasná rýchlosť adaptácie expozície 12/12 sa po
prechode obnoví. Bežný prechod už nežiada reset histórie; okamžité prepnutie
vrátane Obmedzenia pohybu ho ponecháva. Denný a nočný cieľ zostali rovnaké;
medzistavy sú prezentačná animácia, nie výpočet slnka pre konkrétny čas.

Zostavenie `day-night-transition-package-1.log` skončilo s exit 0 za 119,21 s.
Regresné testy prešli: 461 Node, 33 oak a 69 pendant. Následný natívny proces
98159 prešiel [kontrolou životného cyklu](../output/unreal/runtime/launch-services-terrace-01d739a0-5940-427e-afb9-a6e70dda046f/observer-report.json)
aj [kontrolou skutočných hodnôt prechodu](../output/unreal/day-night-transition-validation/validation.json).
Päť bežných prechodov skončilo po 3,010–3,047 s. Obrátenie smeru nastalo
pri 0,889 s a zapnutie Obmedzenia pohybu počas prechodu pri 1,499 s.
Všetkých sedem obnovení nastavilo presne pôvodnú expozíciu 3/1 a oba
override príznaky na false. Normálne Quit počas ďalšieho prechodu obnovilo
expozíciu a skončilo s natívnym exit 0, bez timeoutu či chyby AX.

Úvodná 4K kontrola s 300 aktívnymi foreground vzorkami predchádzala ručnému
ovládaniu. CUA overilo prepínanie, rolovanie panelu pri Tab, nastavenie podľa
macOS a celú obrazovku. Pokus o video cez macOS obsahoval čierny obraz a
zostáva zachovaný ako neúspešný záznam. Jednotlivé UI snímky a hodnoty kamery
nepotvrdzujú každý vykreslený frame, konvergenciu GI ani konečnú kvalitu
animácie; úplná kontrola pohybu zostáva otvorená.
