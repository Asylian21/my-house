# Projekt DOM

Profesionálny senior prístup; dokončiť a vizuálne overiť požadované úpravy.

## Hlavný návrh

Záväzné východisko pre všetku ďalšiu prácu je **variant C, heating=b, living=b (C/B/B)**, potvrdené používateľom 13. 9. 2026.
Označenie v rozhraní: **HLAVNÝ NÁVRH C / B / B**. Poradie znamená **dispozícia / technická miestnosť / obývacia zóna**.
Referenčná adresa: `http://localhost:5173/koncept-2d?variant=c&heating=b&living=b`.
Pred ďalšou prácou si prečítať [docs/active-design.md](docs/active-design.md). Tento dokument obsahuje záväzné rozdelenie hlavných a archívnych ciest; staršie záznamy o prepínaní A/B na hlavných stránkach opisujú už nahradené správanie.

### Záväzné pravidlá navigácie

- `/`, `/docs`, `/podorys`, `/koncept-2d`, `/3d`, `/navrh-3d`, `/docs/manual` a `/docs/model` vychádzajú z C/B/B. Hlavné odkazy vytvárať cez `designHref()` a `ACTIVE_DESIGN` v `lib/twin-design-selection.ts`.
- Hlavný pôdorys, 3D ani manuál nesmú ponúkať prepínače alternatív. Iný variant neobnovovať zo starých parametrov, úložiska prehliadača ani poslednej návštevy archívu.
- Alternatívy sa otvárajú cez `/archiv`. Ich plán a štúdie sú v `/archiv/podorys`, manuál pridáva `view=manual`, 3D zostavy C sú v `/archiv/3d`. Len archívne odkazy používajú `designHref(path, design, true)` a zachovávajú alternatívny výber.
- Hlavná navigácia vracia C/B/B aj z archívnej zostavy. Staré alebo neplatné variantové parametre na hlavných cestách upravuje `requireActiveDesign()` v `app/active-design-route.ts`; zachovať pritom požadovaný pohľad na parcelu alebo manuál.
- Historické predvolené hodnoty A v geometrických generátoroch nie sú rozhodnutím o hlavnom návrhu. Nemeňte ich plošne; hlavným vstupom odovzdávajte `ACTIVE_DESIGN` explicitne.
- Hlavný variant meniť až podľa nového výslovného zadania používateľa. Samotné otvorenie či porovnávanie archívnej zostavy toto rozhodnutie nemení.

Osadenie podľa následnej požiadavky: **uličný aj pravý kolmý odstup 3 000 mm**. Aktívna transformácia je v `lib/twin-house-placement.ts`, napojenia pozemku v `lib/twin-active-site.ts`. Pri ďalších úpravách zachovať tieto odstupy a spoločný rámec 2D/3D.

Staršie varianty zachovať v archíve, nemažte ich ani neprepisujte historické snímky `versions/v1`, `versions/v2`. V hlavných odkazoch a vstupných stránkach vždy používať spoločný `ACTIVE_DESIGN` (C/B/B). Alternatívy aj ich prepínače sú dostupné iba pod `/archiv`; výber alternatívy zachovať medzi archívnym pôdorysom, manuálom a 3D. Hlavná navigácia aj zo staršej zostavy vracia na C/B/B.

Zachovať existujúce rozpracované zmeny. Skutočnú geodetickú presnosť osadenia domu netvrdiť bez podkladu; katastrálne hranice a odvodená poloha domu majú odlišnú dôkazovú úroveň.
