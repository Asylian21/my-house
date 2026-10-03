# Finálny exteriér a vyčistenie projektu

Používateľ 2. októbra 2026 potvrdil spokojnosť s výsledkom. Finálna uložená scéna zostáva C / B / B, s uličným aj pravým kolmým odstupom 3 000 mm.

Spustenie: [Dom.app](/Applications/Dom.app), `npm run unreal:open` alebo [Spustit-finalny-exterier.command](/Users/davidzita/www/dom/Spustit-finalny-exterier.command). Všetky predvolené vstupy otvárajú aktuálnu samostatnú aplikáciu. Obsahuje schválenú scénu r46a a pri bežnom spustení používa profil **Plný model**, Retina rozlíšenie a finálny pohľad z úrovne očí. [Podrobnosti inštalácie](dom-macos-app.md) · [Výkonové merania](unreal-performance.md).

[Finálna galéria](../output/unreal/exterior-validation-20260930-r1/r46a-final-original-pair-gallery-r32-r1.html) obsahuje dve porovnania zo štyroch pôvodných snímok 1920 × 1080. Oba pôvodné natívne procesy skončili úspešne, bez zmeny vstupných súborov. Fototextúra krytiny priniesla viditeľný miestny detail; samostatný prínos úpravy listov nie je z kombinovaného porovnania preukázaný. Následné výkonové merania a vizuálna kontrola profilu Plný model sú zaznamenané osobitne v dokumentácii výkonu.

Pri predchádzajúcom čistení **2. októbra** bolo odstránených 1 294 509 generovaných súborov v 373 určených priečinkoch. Vtedajší nárast voľného miesta približne o 828 GB patrí tomuto staršiemu meraniu. Aktuálne čistenie z 3. októbra má samostatný inventár a výsledok; logické veľkosti APFS kópií sa neprezentujú ako fyzicky uvoľnené miesto.

Zostali zachované zdroje, rozpracované zmeny, aktuálna aplikácia, finálna scéna, jej potrebné závislosti, originálne licencované assety, fotografie, stavebné podklady a `versions/v1`, `versions/v2`. Pri predchádzajúcom čistení 2. októbra sa zhodovalo všetkých 14 256 vtedy potrebných súborov podľa hashov. Pred čistením 3. októbra bol tento pôvodný inventár znovu overený; následne ho nahradil výslovný inventár jedného finálneho projektu. Ten zachováva aktuálne autorské dáta a potrebné pôvodné vstupy a zaznamenáva vyradenie historických pracovných kópií. Menšie pôvodné záznamy a zdrojové skripty ostali dostupné.

[Záznam čistenia z 2. októbra](/Users/davidzita/www/dom/output/unreal/exterior-final-cleanup-20261002-r1/cleanup-final-summary.json) · [Finálny výber scény](/Users/davidzita/www/dom/output/unreal/exterior-final-current.json)

## Dokončené čistenie a výkon z 3. októbra

Tri samostatne kontrolované čistiace behy odstránili **69 817 súborov / 141,42 GB logických dát**, bez zlyhania. Súčet zmien voľného miesta nameraných pri jednotlivých behoch je **108,64 GB**. Čistý nárast od začiatku hlavného čistenia po posledný beh je **106,24 GB**; rozdiel spôsobuje aktivita medzi meraniami. Logické veľkosti kópií a `du` sa pre APFS nepoužívajú ako fyzicky uvoľnené miesto.

Odstránené sú staré generované projekty a balíky, dočasné cache, nepotrebné výstupy kompilácie a testovacie obrázky. Zachovali sa compiler/UHT vstupy na nové zostavenie, všetky používané galérie a podklady, férové výkonové porovnania aj dôkaz pôvodného nočného záseku. Presná QA časť v používateľskom kontajneri odstránila iba uvedené PNG; zvyšných 6 714 súborov zostalo nezmenených. Neskorší samostatný beh vyradil 777 nepotrebných diagnostických kópií v projekte a zachoval 220 používaných záberov. Pôvodné záznamy sa neprepisovali; samostatné záznamy jasne opisujú vyradenie starých plných obrazových sekvencií.

Posledný inventár po odstráneniach overil **9 448 chránených súborov** bez zmeny. Pred záverečnými natívnymi testami mal projekt približne **46,46 GB** alokovaných referencií, QA kontajner **2,30 GB** a Data volume **893,32 GB** voľného miesta. Prvý pôvodný inventár a novšie finálne inventáre majú odlišný rozsah; historické záznamy zostávajú nemenné. Záverečný záznam zachytáva aj následnú povolenú aktualizáciu týchto troch dokumentov.

Plný model ponecháva celú geometriu a materiály. Férové r38 porovnanie zlepšilo **36,72 → 70,54 FPS**; opakovanie skutočnej nainštalovanej aplikácie po čistení nameralo **74,26 FPS**. Posledná overená chôdza vo dne/noci dosiahla približne **46,6 FPS**, bez intervalu nad 50 ms. Menšie hrany a odrazy môžu byť mäkšie než vo Fotoreal; 60 FPS vo všetkých pohľadoch sa netvrdí. Bežný príkaz aplikáciu spustil s finálnymi predvolenými hodnotami; posledné automatické GUI naviazanie CUA sa nepodarilo, preto sa používa oddelený skorší vizuálny dôkaz nezmeneného balíka.

Prešlo 740 Unreal testov, 74 samostatných safety testov čistenia a 23 kontrol výsledného webového HTML. Po všetkých odstráneniach prešiel read-only plán opätovného Shipping zostavenia; natívna kompilácia sa v tomto poslednom kroku znovu nespúšťala. [Výsledok aktuálneho čistenia](../output/unreal/performance-20261003-r1/storage-audit/cleanup-final-summary.json) · [Výkonové merania a hranice overenia](unreal-performance.md) · [Web po čistení](../output/unreal/performance-20261003-r1/post-clean-web-validation.json).
