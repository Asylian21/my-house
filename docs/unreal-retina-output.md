# Retina výstup a cieľ 30 FPS

Používateľ 9. 9. 2026 uprednostnil plynulý pohyb aspoň pri 30 FPS a dovolil znížiť výstup pod 4K. Pevných 3840 × 2160 preto už nie je podmienkou bežného zobrazenia. Zdrojová geometria, materiály, svetlá a rozmery modelu sa nemenia.

Po skúške [nového vonkajšieho osvetlenia](unreal-exterior-lighting.md) zostáva bežnou verziou nižšie overený balík `a445eb50…`. Svetelný kandidát `a77f76aa…` sa zostavil a spustil, ale jeho merania stratili aktiváciu okna a nepotvrdzujú výkon. [Opätovné bežné otvorenie overenej verzie](../output/unreal/exterior-lighting-study/retained-delivery-open-review.json) obnovilo Retina 3200 × 1800 a profil Plynulosť; samo osebe nejde o nové meranie FPS.

Aktuálny balík `a445eb50…` zo zdrojov `73dcd03c…` splnil cieľ v **dvoch minútových orbit testoch pri bazéne**, cez deň a v noci, pri **3200 × 1800**, TSR **50 %** a histórii **100 %**. Po 600 zahrievacích snímkach nasledovalo 60 sekúnd pohybu podľa bežného wall-clock času. Všetkých **6420 intervalov** bolo v popredí a v aktívnom okne; žiadny neprekročil 33,33 ms.

| Aktuálny pohľad | Priemer FPS | p99 intervalu | Najpomalšia snímka | Intervaly |
| --- | ---: | ---: | ---: | ---: |
| Bazén cez deň | 42,30 | 25,70 ms | 26,87 ms | 2538 |
| Bazén v noci | 64,69 | 18,66 ms | 20,29 ms | 3882 |

[Nezávislý prehľad dvoch behov](../output/unreal/retina-integration/runtime-review.json) pripína výsledky, pôvodné PNG a zdroje. Zopakoval kontroly pohybu, expozície, focusu, providera, natívneho ukončenia a natívnej politiky opravy terasového klinu; overil 100 súborov bez rozdielov. Nový balík skutočne číta skompilované limity kamery **EV[−6,14], bias0** a pevnú cache **EV6**. QA nemení expozíciu príkazmi SET ani INI override. Denný provider kaustiky bol aktívny bez diagnostických GPU readbackov; v noci správne nevytvoril príspevok pri zachovaní kontroly zdrojov a životného cyklu.

Vizuálne posúdenie pôvodných snímok hlavnou úlohou potvrdilo stabilný denný obraz a lepšiu nočnú čitateľnosť oproti starému limitu EV−4. Nočný bazén však zostáva tmavý a osvetlenie potrebuje ďalšiu prácu. Rozdiely FPS nepredstavujú izolované meranie vplyvu expozície či pixelov. Tieto dva behy neoverujú všetky štyri pohľady nového balíka, klávesnicu, bežné opätovné otvorenie aplikácie, chôdzu ani udalosti prezentácie displeja; fotorealistické dokončenie sa neprehlasuje.

[Krátke natívne overenie ovládania](../output/unreal/retina-integration/keyboard-review.json) potvrdilo výber pohľadov podľa fyzických pozícií horného radu, numerickú jednotku, zachovanie fokusu panela a dokončený prechod deň/noc. Prvý dlhý test zostáva odmietnutý pre časový limit; následný kratší test skončil čisto. Automatizácia neodovzdala požadované modifikátory, preto kombinácie s nimi, opakovanie klávesu a fyzická klávesnica zostávajú neoverené.

[Bežné spustenie aktuálneho balíka](../output/unreal/retina-integration/ordinary-open-review.json) bez parametrov rozlíšenia, profilu alebo diagnostiky obnovilo **Plynulosť 50/100** a **3200 × 1800**. Panel aj strom prístupnosti zobrazili zvolený profil; po zatvorení panela zostala aplikácia pri dennom bazéne. Toto spustenie nie je ďalším meraním výkonu. [Nočný interiér](../output/unreal/retina-integration/interior-night-review.json) prešiel samostatnou statickou kontrolou novej expozície.

## Historické merania balíka 710a9343

Predošlý balík `710a9343…` splnil cieľ v štyroch minútových denných orbit testoch pri **3200 × 1800**, TSR **50 %** a histórii **100 %**. Všetkých **14 606 intervalov** bolo v popredí a kratších než 33,3 ms. Zahŕňa aj [opravu tmavého klinu na terase](unreal-deck-fallback.md).

| Pohľad | Priemer FPS | p99 intervalu | Najpomalšia snímka |
| --- | ---: | ---: | ---: |
| Bazén | 42,27 | 25,69 ms | 26,96 ms |
| Obývačka | 65,98 | 16,85 ms | 18,34 ms |
| Terasa | 66,71 | 16,58 ms | 21,59 ms |
| Ulica | 68,44 | 16,58 ms | 19,57 ms |

[Historický záznam štyroch meraní balíka 710a9343](../output/unreal/deck-wedge-app/motion-overview.json) pripína každý natívny výsledok aj kontrolu automaticky aplikovanej opravy. [Nezávislý audit](../output/unreal/deck-wedge-app/motion-review.json) zopakoval kontroly všetkých štyroch behov a overil zdroje, výsledky aj celý balík bez rozdielov. Ide o kadenciu bežných herných snímok pri pohybe zdrojovej orbit kamery; udalosti prezentácie displeja, celé trasy chôdze a nočný režim sa v tomto meraní neoverovali. Predošlý balík `abde8be8…` a jeho [pôvodné merania](../output/unreal/retina-ax-study/motion-review.json) zostávajú historickým dôkazom.

[Historické bežné spustenie balíka 710a9343](../output/unreal/deck-wedge-app/interactive-review.json) bez parametrov rozlíšenia či profilu obnovilo Plynulosť a výstup 3200 × 1800. Natívny panel aj prístupnosť potvrdili zvolený profil; tento stav číta skutočné hodnoty renderovania. Pri tomto historickom overení zostala aplikácia otvorená pri bazéne; nejde o tvrdenie o aktuálne otvorenom procese ani o bežnom spustení nového balíka.

Následný [nočný orbit pri bazéne](../output/unreal/retina-night-study/retina-pool-night-sp50-motion-74c7027e-0cfd-48d4-a4a4-b24d6f4fb46d/result.json) na tom istom balíku a pri rovnakom Retina profile dosiahol **68,79 FPS**, p99 **16,07 ms**, maximum **20,90 ms**. Všetkých 4 128 intervalov bolo v popredí; žiadny neprekročil 33,3 ms. Natívne komponentové záznamy potvrdili nočné svetlá pred aj po meraní. Denný poskytovateľ kaustiky správne nevytváral nočný príspevok.

[Historická vizuálna kontrola nočného bazéna balíka 710a9343](../output/unreal/retina-night-study/static-image-review.json) neprešla: terasa a fasáda sú príliš tmavé. Pozorovaná expozícia dosiahla EV −4, čo zodpovedá spodnej hranici zdrojového nastavenia. V tejto historickej revízii bola úprava expozície ešte otvorená. Aktuálna revízia vyššie už používa EV[−6,14], ale zvyšné nočné osvetlenie a ďalšie pohľady tým nie sú dokončené.

## Správanie

Bežné macOS spustenie používa rozlíšenie skutočnej kresliacej plochy okna. Vnorený 16:9 viewport zostáva oddelený od UI, ale `FSceneViewport::Paint` teraz riadi jeho veľkosť podľa absolútnych pixelových súradníc Slate. Tie už obsahujú DPI; ďalšie násobenie dvomi by bolo nesprávne. Zmena veľkosti okna nemá opakovať centrovanie ani presúvať klávesnicový fokus.

`-BreziOutput=4k` zostáva explicitnou možnosťou. Pôvodné `-BreziCapture4K` a `-BreziCaptureUI` zachovávajú staré 4K diagnostické kritériá. Nové `-BreziCaptureScene` zachytí bežný snímok v aktuálnom rozlíšení, bez HighResShot a bez resetovania histórie. Nezlučiteľné požiadavky na režim sa odmietnu.

Profilová voľba naďalej riadi interné percentá TSR; rozlíšenie výstupu a interné vzorkovanie sú odlišné. Aktuálne dva merané behy použili Plynulosť 50/100 a veľkosť okna 3200 × 1800. Samostatné bežné spustenie vyššie overilo obnovenie uloženého profilu aj na novom balíku. Vyššie profily zostávajú dostupné v Ovládaní.

V historickom overení balíka predchádzajúceho aktuálnej integrácii natívne UI potvrdilo `saved=1`; ďalší štart bez parametrov rozlíšenia a profilu obnovil `performance` s `origin=1`, skutočných 50/100 a Retina cieľ 3200 × 1800. [Overenie obnovených nastavení](../output/unreal/retina-ax-study/interactive-review.json) obsahuje snapshot štartovacieho logu. Príkaz `scripts/unreal/run.mjs open` teraz rešpektuje uloženú veľkosť namiesto vynucovania 1600 × 900. Historické diagnostické príkazy zostávajú samostatné.

## Natívne overenie

Politika výstupu prešla 50 kontrolami v bežnej aj optimalizovanej C++ konfigurácii. Prvý Retina balík `f12b2ecf…` sa zostavil a spustil. Jeho [statická kontrola](../output/unreal/retina-output-study/retina-pool-sp100-static-1df20215-0444-4055-8907-d9c146aba89b/result.json) namerala zhodný drawable, viewport, render target, RHI a PNG **1600 × 900** pri DPI 2 a 300/300 snímkach v popredí. Beh však **neprešiel**: samostatný AX bootstrap ešte vyžadoval pevné 4K a inicializácia prístupnosti preto vypršala. Jeho časovanie nie je prijatým výsledkom tejto revízie ani dôkazom plynulosti vo veľkom okne.

[Opravná revízia](../output/unreal/retina-ax-study/package-context.json) používa spoločnú kontrolu pripraveného výstupu vrátane aktuálneho RHI a troch stabilných pozorovaní rozmerov. Zachováva natívne okno, vnorený viewport a podmienky pre aktiváciu AX. Deväť súborov implementácie je pripnutých k skutočnému zdrojovému uzáveru. QA má 55 CPU kontrol vrátane odmietnutia pôvodného AX zlyhania. Natívny beh a rozmerové zmeny sa samotnými CPU výsledkami neprehlasujú za overené.

Nový opt-in `-BreziRealtimeOrbit -BreziBenchmarkSeconds=60 -BreziCaptureScene` meria skutočný wall-clock čas pri plynulom pohybe ±8° okolo zdrojového pohľadu. Nemodifikuje engine clock; každý meraný tick odmieta pevný krok, pevnú frekvenciu, benchmark clock a time dilation. Zachováva jeden pohľad, polomer, pitch a FOV. Snímka vzniká až po meraní. Historické screenshotové motion režimy s pevným krokom zostávajú samostatné.

Vyhodnotenie potrebuje skutočný pohyb, celú dobu v popredí, stabilné a zhodné drawable/viewport/RHI rozmery a distribúciu intervalov vrátane p95/p99 a zásekov. Výsledok jedného orbit pohľadu nebude dôkazom celej chôdze, kolízií ani všetkých denného/nočného pohľadov. Predchádzajúcich 26,0/36,1 FPS patrí starému pevnému 4K balíku a krátkym statickým meraniam.
