# Oprava tmavého klinu na terase

V novom lokálnom balíku `710a9343…` je tmavý klin vo vzdialenej doske pri bazéne odstránený. Natívna aplikácia použije pri štarte existujúcu úplnú geometriu fallbacku iba pre zdrojový diel `DOM_01710`. Jeho rozmery, UV, materiál, kolízie a mapa sa nemenia; Nanite zostáva zapnutý pre ostatnú scénu.

Zdrojová kontrola nenašla dieru v doske ani čiernu škvrnu v pôvodnej textúre. Dva zábery z rovnakého balíka, kamery a profilu izolovali zmenu renderovacej cesty konkrétneho komponentu. V približne premietnutej vnútornej oblasti dosky (1 899 pixelov) klesol počet tmavých pixelov zo 188 na 0. Výsledok neurčuje, či je príčinou konkrétna chyba tangént, klastrov alebo tieňovania Nanite.

[Implementácia](../unreal/BreziTwin/Source/BreziTwin/BreziPlayerController.cpp) pred zmenou vyžaduje jediný zdrojový tag, tag generovaného modelu, presnú identitu meshu, dostupnú registrovanú komponentu a platnú fallback geometriu. Potom použije verejný setter a overí spätné čítanie. Pri nejednoznačnej identite alebo chýbajúcej geometrii komponent nemení. Nezávisí od poradového názvu aktéra v mape.

Nové Editor aj Game zostavenie, dve natívne fázy numerickej kontroly svetla, cook, archive a kontrola podpisu balíka prešli. [Produkčný záber](../output/unreal/deck-wedge-app/production-image-review.md) zachoval odstránenie klinu aj bez konzolovej výnimky a bez zjavného zhoršenia okolia. [Merania Retina](unreal-retina-output.md) splnili 30 FPS vo všetkých štyroch denných pohľadoch; produkčný štart overil automatické použitie opravy.

Dôkazy: [diagnostický pár](../output/unreal/deck-wedge-study/pair-integrity-review.json), [porovnanie pôvodných snímok](../output/unreal/deck-wedge-study/image-review.json), [zdrojová revízia a balík](../output/unreal/deck-wedge-app/package-context.json), [natívne merania](../output/unreal/deck-wedge-app/motion-overview.json). Kontrola jednej chyby obrazu nie je prijatím celkového fotorealizmu projektu.
