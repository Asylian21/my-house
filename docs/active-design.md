# Hlavný návrh C / B / B — záväzné východisko projektu

Potvrdené stavebníkom 13. 9. 2026: hlavný variant je **C · Výklenok, technická miestnosť B, obývacia zóna B**.

Používateľ následne výslovne určil, že **všetky hlavné a predvolené cesty vedú na C/B/B a ostatné varianty sú dostupné len cez archív**. Tento zápis spresňuje staršie poznámky, v ktorých sa A/B voľby ešte prepínali priamo na hlavných stránkach. Hlavný variant sa mení až novým výslovným zadaním používateľa, nie otvorením inej zostavy na porovnanie.

| Pozícia v C / B / B | Význam | Parameter v URL |
| --- | --- | --- |
| C | Dispozícia C · Výklenok | `variant=c` |
| prvé B | Technická miestnosť B | `heating=b` |
| druhé B | Obývacia zóna B | `living=b` |

Používateľské označenie je **HLAVNÝ NÁVRH C / B / B**. V URL sú hodnoty malé písmená; identifikátory obývačky a technickej miestnosti v modeli sú `B`.

Referenčný pôdorys: <http://localhost:5173/koncept-2d?variant=c&heating=b&living=b>.

Všetky ďalšie úpravy a opravy vychádzajú z C/B/B. Výber musí prechádzať z pôdorysu do 3D aj dokumentácie. Predvolené hodnoty historických geometrických generátorov sa nemenia; hlavné vstupné stránky používajú `ACTIVE_DESIGN`.

## Hlavné vstupy a archív

| Cesta | Záväzné správanie |
| --- | --- |
| `/`, `/docs` | Prehľad a dokumentácia hlavného návrhu; hlavné odkazy vedú na C/B/B. |
| `/podorys`, `/koncept-2d` | Pôdorys C/B/B bez prepínačov alternatív. `site=1` zobrazí parcelu, `view=manual` manuál. |
| `/3d`, `/navrh-3d` | 3D hlavného návrhu C/B/B. |
| `/docs/manual` | Manuál a tlač hlavného návrhu C/B/B. |
| `/docs/model` | Technické podklady a model s výberom C/B/B. |
| `/archiv` | Vstup k alternatívam, dispozičným štúdiám a historickým snímkam. |
| `/archiv/podorys` | Alternatívne zostavy C s prepínačmi A/B; `mode=study` sprístupní zachované dispozičné štúdie. |
| `/archiv/podorys?...&view=manual` | Manuál konkrétnej archívnej zostavy; zachová jej `heating` a `living`. |
| `/archiv/3d` | 3D konkrétnej archívnej zostavy C; zachová jej `heating` a `living`. |
| `/v1`, `/v2`, `/archiv/model` | Zachované historické vstupy, dostupné z archívu. |
| `/koncept-2d-2` | Starý odkaz na experiment E presmeruje do `/archiv/podorys?variant=e&mode=study`. |

Hlavná navigácia **vždy vracia C/B/B**, aj keď je práve otvorená archívna zostava C/A/B. Iba odkazy na ďalšie zobrazenia danej archívnej zostavy zachovávajú C/A/B. Na mobile sú archívny manuál a 3D dostupné v menu „Zobrazenia archívnej zostavy“.

Príklady, ktoré sa pri ďalšej práci nesmú zameniť:

- `/podorys?variant=c&heating=a&living=b` je starý hlavný odkaz: presmeruje na C/B/B.
- `/archiv/podorys?variant=c&heating=a&living=b` je zámerne zvolená archívna zostava C/A/B: zostane C/A/B.
- Hlavný odkaz „3D dom“ z archívu otvorí `/3d?variant=c&heating=b&living=b`. Odkaz „3D archívnej zostavy“ otvorí `/archiv/3d?variant=c&heating=a&living=b`.

## Implementačné oporné body

- [lib/twin-design-selection.ts](../lib/twin-design-selection.ts): `ACTIVE_DESIGN` je B/B, `PREVIEW_DESIGN` je jeho alias. `designHref(path)` aj `designHref(path, design)` vytvárajú hlavný odkaz C/B/B. Alternatívu prenáša iba `designHref(path, design, true)` do archívu.
- [app/active-design-route.ts](../app/active-design-route.ts): `requireActiveDesign()` opravuje historické, neplatné alebo duplicitné variantové parametre hlavných stránok a odstraňuje `mode=study`; zachová ostatné parametre, napríklad `site=1` a `view=manual`.
- [app/project-nav.tsx](../app/project-nav.tsx): hlavné odkazy sa neodvodzujú od práve prezeranej archívnej zostavy.
- [app/koncept-2d/studio.tsx](../app/koncept-2d/studio.tsx) a [documentation-studio.tsx](../app/koncept-2d/documentation-studio.tsx): alternatívy a prepínače povolí iba explicitný režim `archive`; hlavný pohľad zostáva C/B/B.
- `ARCHIVE_DESIGN` a historické normalizátory či geometrické generátory môžu mať predvolenú zostavu A/A. To nemení hlavný návrh a nie je dôvod na návrat hlavných vstupov k A/A.

Po zmene navigácie overiť hlavné vstupy bez parametrov, starý hlavný odkaz s A, alternatívu otvorenú cez archív, jej prechod medzi plánom/manuálom/3D a návrat hlavnou navigáciou na C/B/B. Existujúce kontroly sú v [tests/twin-design-preview.test.ts](../tests/twin-design-preview.test.ts) a [tests/rendered-html.test.mjs](../tests/rendered-html.test.mjs). Stav predchádzajúcich overení je v [zázname navigácie](project-navigation-verification.md); lokálne overenie nie je potvrdením publikovania.

## Zachované geometrické rozhodnutia

Dodatočná pravá priečka pri kuchynskej linke a dverách technickej miestnosti bola 13. 9. 2026 na výslovnú žiadosť stavebníka zrušená kvôli vzhľadu interiéru. Pravý koniec linky zostáva otvorený, koncová skrinka a pracovná doska majú pôvodnú dĺžku. Ľavá priečka pri chodbe zostáva. Túto pravú priečku znovu nepridávať bez nového zadania.

Akustické steny AK-01 (spálňa / chlapčenská izba) a AK-02 (kúpeľňa / dievčenská izba) majú podľa zadania z 13. 9. 2026 skladbu **SA30: LeierPLAN 10 P10 100 mm + minerálna vata 100 mm + LeierPLAN 10 P10 100 mm**. Hrúbka 300 mm bez omietok a obkladov, poloha líc aj priechod chodby zostávajú. Ide o návrh nenosnej priečky s potrebou statického posúdenia pôvodne nosných úsekov. Pozri [skladbu a poznámky SA30](acoustic-walls.md).

Ostatné varianty sa nemažú. Sú dostupné cez `/archiv`; snímky `/v1` a `/v2` zostávajú zachované. Dispozičné štúdie a staršie kombinácie A/B sú historické pracovné alternatívy, nie hlavný návrh.

Hlavné cesty `/koncept-2d`, `/podorys`, `/3d`, `/navrh-3d` a `/docs/manual` sú pevne nastavené na C/B/B. Staré alebo neplatné parametre sa upravia na hlavný návrh, pričom pohľad na parcelu a manuál zostávajú zachované. Hlavná navigácia vždy vedie na C/B/B aj pri prezeraní archívu. Prepínače alternatív sú dostupné iba v `/archiv/podorys`; archívna zostava si zachová výber v manuáli a v `/archiv/3d`.

Sekcie: `/` prehľad projektu, `/docs` dokumentácia, `/3d` dom v 3D, `/podorys` samostatný interiérový plán. Pôvodné adresy zostávajú funkčné.

Hranica parcely 6012/26 sa odvodzuje z nezmeneného katastrálneho polygónu S-JTSK. Aktívny pôdorys aj 3D používajú spoločný `twin-active-site.ts`. Pôvodný lokálny rámec C3 a historické osadenie zostávajú v `twin-site.ts`.

Používateľ potvrdil platnosť C3 a následne požiadal **uličný aj pravý (východný) kolmý odstup presne 3 000 mm**. Revízia `CLIENT-PLACEMENT-20260913` v `twin-house-placement.ts` posúva celý dom o 77,913405454 mm doprava oproti pôvodnému osadeniu; Y sa nemení. Rozmery, dispozícia a vnútorné súradnice domu zostávajú zachované. Pevné prvky pozemku sa zobrazujú v posunutom rámci domu; prístupy a plot sa napájajú na tento rámec. Stav je `CLIENT_REQUESTED_SETBACK`, nie geodetické zameranie stavby. Ostatné odstupy sa naďalej odvodzujú kolmo ku katastrálnym hranám.
