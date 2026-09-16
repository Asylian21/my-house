# Revízia AK-01 a AK-02 na SM30

Dátum: 16. 9. 2026. Zdroj: výslovné zadanie stavebníka v úlohe úpravy AK-01/AK-02.

- Aktuálna konštrukcia: jedna 300 mm vrstva klasickej obvodovej tehly, bez vaty, dutiny a akustickej predsteny. Bežné povrchy sú navyše. Dôvod odhlučnenia zostáva.
- Líca X14943–15243 mm, úseky Y3504–6552 a Y7651–10699 mm, modelová výška 3125 mm a chodba 1099 mm zostávajú. Jedna os muriva je X15093 mm.
- Konkrétna tehla, malta a hmotnosť novej steny nie sú určené. Stará tiaž dvojplášťovej SA30 ani akustický výpočet približne 58 dB sa neprenášajú.
- Zmrazené `inputs/geometry.json`, `inputs/model-snapshot.json` a číselné výsledky ostávajú historickým reprodukovateľným scenárom. Nevykonal sa nový návrh základov ani potvrdenie únosnosti pre SM30.
- Aktuálne správy PDF aj Markdown majú označenie tejto obmedzenej platnosti. Pôvodné PDF sú uchované v `archive/before-sm30-20260916`.
- Po výbere výrobku treba doplniť tiaž muriva, malty, povrchov a vybavenia a prepočítať nadväzujúce prípady dosky a R7. Obnova extrakcie geometrie nesmie znovu priradiť SA30 iba podľa ID steny.

[Spoločná aktuálna dokumentácia stien](../../docs/acoustic-walls.md).
