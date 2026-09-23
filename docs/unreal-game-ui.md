# Herné rozhranie Unreal — 22. 9. 2026

Natívna prechádzka C / B / B má samostatne prerobené rozhranie v Unreal Slate.
Pri chôdzi zostáva malý identifikačný štítok, vstup do menu, zameriavač a nízky
panel s ikonami. Pokyn na otvorenie dverí sa ukáže pri dostupnej interakcii.
Smerové tlačidlá sa zobrazujú až pri voľnom kurzore.

Tlačidlo **Prelet** v spodnom paneli a **Prelet okolo domu** v pauze
spúšťajú voľné lietanie vonku. Rovnaké prepnutie používa **H**. Pri prechode
z interiéru sa otvorí vonkajší pohľad na dom; z už zvoleného exteriéru
sa zachová poloha kamery. Kamera sa pohybuje nezávisle od bodu otáčania,
bez gravitácie a kolízií postavy. WASD a šípky menia vodorovnú polohu,
E/Q výšku, Shift zrýchľuje a Alt spomaľuje. Koliesko posúva kameru v smere
pohľadu. Počas letu sa tlačidlo zmení na **Prechádzka**, ktorá vráti
používateľa do obývačky s overeným vstupom na podlahu.

Pri voľnom kurzore sú v prelete dostupné aj tlačidlá E/Q na stúpanie
a klesanie. Krátke kliknutie vykoná ohraničený posun, podržanie pokračuje
v pohybe. Esc pohyb pozastaví a otvorí menu; strata aktivity okna urobí
to isté. V/R sú dostupné iba pri chôdzi. Voľba miestnosti obnoví chôdzu,
voľba vonkajšieho pohľadu obnoví otáčanie okolo neho.

Pauza obsahuje tri sekcie: **Miestnosti**, **Atmosféra**, **Ovládanie**.
Miestnosti používajú dvojstĺpcové karty so zrozumiteľnými názvami; výber
hneď obnoví prechádzku v danom priestore. Atmosféra združuje deň/noc a tri
voľby kvality obrazu. Ovládanie spája prehľad klávesov, citlivosť myši
a nastavenie pokojnejšieho pohybu kamery. Tlačidlo Pokračovať zostáva
pevne dostupné aj pri rolovaní obsahu.

Vzhľad používa grafitové povrchy, teplú bielu typografiu, pieskový akcent,
jednotné vektorové ikony a samostatné stavy ukázania myšou, stlačenia,
výberu a klávesnicového fokusu. Interaktívne tlačidlá majú minimálne
44 × 44 natívnych bodov. Text a ikony sa renderujú natívne, bez obrázkových
náhrad ovládacích prvkov. Menšie okno má nižšie záhlavie, rolovateľný obsah
a jeden stĺpec nastavení. Nastavenia macOS Reduce Motion, Increase Contrast
a Reduce Transparency zostávajú rešpektované existujúcou politikou.

## Ovládanie

| Vstup | Správanie |
| --- | --- |
| WASD / šípky | Chôdza alebo vodorovný let |
| H / tlačidlo Prelet | Voľný prelet / návrat do prechádzky |
| Myš | Rozhliadanie v hernom režime |
| Shift / Q | Rýchlejšia / pomalšia chôdza |
| E / Q počas letu | Nahor / nadol |
| Shift / Alt počas letu | Rýchlejší / pomalší let |
| E | Kontextové otvorenie alebo zatvorenie dverí |
| V | Postava / pohľad z očí |
| R | Vycentrovanie kamery |
| Koliesko, gesto dvoch prstov, +/− | Priblíženie kamery |
| N | Deň / noc |
| Esc | Otvoriť pauzu alebo obnoviť prechádzku; v otvorenom výbere miestností najprv zatvoriť výber |
| Tab | Z hry uvoľniť kurzor; v rozhraní prechádzať ovládacími prvkami |
| Shift + Tab | Spätný prechod ovládacími prvkami |
| Enter / medzerník | Aktivácia zameraného tlačidla |

Do herného ovládania sa vracia tlačidlom **Hra** pri voľnom kurzore,
Pokračovať alebo Esc
z pauzy. Klávesnica prechádza iba aktívnou sekciou. Zmena sekcie presunie
fokus na jej záložku a vráti obsah na začiatok. Posuvník citlivosti používa
rovnaký teplý obrys fokusu ako tlačidlá, čitateľnú sivú dráhu a pieskový
jazdec; šípky vľavo/vpravo menia hodnotu priamo po zameraní. Pri klávesnicovom
prechode v krátkom okne sa vycentruje tak, aby zostal viditeľný aj názov a hodnota. Skryté sekcie, herný panel
počas pauzy a nedostupná interakcia s dverami sa vyradia z natívneho
accessibility stromu. Strata aktivity okna zastaví ovládanie prechádzky.

## Zdroj a reprodukcia

- `unreal/BreziTwin/Source/BreziTwin/BreziGameUI.h`: paleta, štýly, ikony, minimálne rozmery a fokus.
- `unreal/BreziTwin/Source/BreziTwin/BreziPlayerController.cpp`: rozloženie a správanie rozhrania.
- `scripts/unreal/model-refresh-qa.mjs`: natívne Metal snímky hry a všetkých sekcií pauzy; voliteľný `menuSection` je povolený iba pri `gameplayUi=pause`.

Pôvodná úprava menila UI zdroje a pomocníka snímok. Prelet dopĺňa samostatný režim natívnej kamery a jeho ovládanie. Importovaná geometria,
kuchyňa, materiály, svetlá, avatar a kolízie pochádzajú zo zachovaného
[archviz základu](unreal-archviz-game.md). Jeho úplná 203 m prehliadka
patrí balíku `33de1932…`; sama osebe sa nepovažuje za nový priechod
pre neskoršie binárne zostavy.

## Predchádzajúci overený balík rozhrania

Balík **643ddbf10e3208e685efaf6ccab8e57d48dd398c8f98fc9b21e8799d44727c5c** bol overený pred doplnením preletu. [Vizuálny review](../output/unreal/archviz-game-20260922/hud-visual-review.json)
viaže presný report balíka, zdroje, snímky a testy; všetkých 37 súborov aplikácie
bolo po overení porovnaných s podpísaným balíkom.

- Natívny Game build: 31/31 krokov; cook, podpis a package gates úspešné.
- Dva testy `Brezi.Controls.Hud` prešli v skutočnom zabalenom engine bez chýb alebo upozornení; ich NullRHI beh je oddelený od vizuálnej kontroly.
- Šesť testov capture argumentov, navigačnej a touchpad politiky prešlo.
- Štyri samostatné Metal behy zachytili hru a každú sekciu menu; všetky capture reporty sú validné a všetky snímky vizuálne skontrolované.
- Natívna interaktívna kontrola v kompaktnom 640-bodovom okne potvrdila prepínanie sekcií, automatické posunutie k posuvníku aj s názvom a hodnotou, zmenu citlivosti 1 → 1,05 šípkou, prepínač pokojnejšej kamery, výber kvality, vstup do pracovne cez Tab/Enter, rýchly výber priestorov a návrat tlačidlom Hra. [Záznam kontroly](../output/unreal/archviz-game-20260922/hud-final-manual.json).

| Stav | Dôkaz |
| --- | --- |
| Herný panel | [Snímka](../output/unreal/archviz-game-20260922/qa/interior-ui-play-0e3d4bf1-6cb7-47e4-a216-b420f98725ed/capture.png) · [natívny report](../output/unreal/archviz-game-20260922/qa/interior-ui-play-0e3d4bf1-6cb7-47e4-a216-b420f98725ed/qa.json) |
| Miestnosti | [Snímka](../output/unreal/archviz-game-20260922/qa/interior-ui-pause-rooms-43583e25-1004-4cc3-a493-163af834547d/capture.png) · [natívny report](../output/unreal/archviz-game-20260922/qa/interior-ui-pause-rooms-43583e25-1004-4cc3-a493-163af834547d/qa.json) |
| Atmosféra | [Snímka](../output/unreal/archviz-game-20260922/qa/interior-ui-pause-atmosphere-b758e9b5-7934-4ecf-9efe-a623aafbd3b4/capture.png) · [natívny report](../output/unreal/archviz-game-20260922/qa/interior-ui-pause-atmosphere-b758e9b5-7934-4ecf-9efe-a623aafbd3b4/qa.json) |
| Ovládanie | [Snímka](../output/unreal/archviz-game-20260922/qa/interior-ui-pause-controls-572c7a31-464f-4e27-8289-d9ee5ecdc29b/capture.png) · [natívny report](../output/unreal/archviz-game-20260922/qa/interior-ui-pause-controls-572c7a31-464f-4e27-8289-d9ee5ecdc29b/qa.json) |

Bežné okno má nastavenia vedľa seba; v kompaktnom okne je časť obsahu
rolovateľná a spodné akcie zostávajú pevné. Automatizované doručenie Shift
modifikátora pri spätnom Tab prechode nebolo spoľahlivo potvrdené; tento
spätný smer je overený v implementácii, nie fyzickým klávesnicovým testom.
Nastavenia prístupnosti macOS sa počas tejto kontroly nemenili.

Predchádzajúce balíky a receipty sú zachované v `package-history` a
`hud-redesign-history`. Vizuálna kontrola sa vzťahuje na uvedené zachytené stavy.

Záverečné menu je otvorené a interaktívne overené v čistom profile pri bežnej
veľkosti okna. Bežné spustenie cez LaunchServices inicializovalo scénu, ale
pripojenie UI automatizácie vypršalo; jeho interakcie v pôvodnom profile
preto neoznačujeme za overené. [Záznam otvorenia](../output/unreal/archviz-game-20260922/hud-ui-handoff.json).


## Aktuálny balík s voľným preletom

Balík **6632907850d19f434cd65ccd43d8fd95dec1791dfe1711ee458d563c724a7584**
je od 22. 9. 2026 nastavený pre `npm run unreal:open`.
[Záznam overenia](../output/unreal/archviz-game-20260922/flight-visual-review.json)
viaže presný balík, sedem zmenených natívnych zdrojov, testy a interaktívnu kontrolu.

- Game build: 31/31 krokov; cook, zabalenie, podpis a porovnanie payloadu prešli.
- Tri skutočné testy zabaleného enginu prešli bez chýb a upozornení:
  `Brezi.Controls.Flight.PawnTransitions` a dve existujúce skúšky `Brezi.Controls.Hud`.
  Tento NullRHI beh overuje správanie; vizuálna kontrola je samostatná.
- Politika letu prešla v debug aj optimalizovanej kompilácii: 20 kontrol vrátane
  výšky, rýchlostí, diagonál, hraníc a posunu kolieskom. Existujúce skúšky
  navigácie, avatara, touchpadu a prechodov kamery prešli.
- V natívnom okne bola overená viditeľnosť tlačidla v menu aj hernom paneli,
  prepnutie H, stúpanie nad strechu cez E, klesanie Q a vodorovný posun cez
  tlačidlá, návrat tlačidlom Prechádzka do obývačky a opätovný vstup do preletu.
  Ovládanie výšky pri chôdzi zmizlo aj z accessibility stromu. Esc otvoril
  menu preletu. [Interaktívny záznam](../output/unreal/archviz-game-20260922/qa/flight-manual-66329078/review.json).

Snímky a stromy natívneho rozhrania sú súčasťou príslušnej konverzácie;
interaktívny záznam obsahuje aj odtlačok uloženého runtime logu. Kontrola
nepredstavuje nové výkonnostné ani svetelné schválenie. Pri vonkajšom pohľade
sa prechodne zobrazilo existujúce hlásenie enginu o limite svetiel VSM.
Pôvodné zdroje a receipty sú zachované v `flight-history`, stará aplikácia
v `package-history`.
