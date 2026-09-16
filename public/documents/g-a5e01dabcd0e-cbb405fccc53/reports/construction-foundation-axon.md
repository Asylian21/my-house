# Priestorový pohľad na základy C/B/B



Revízia **16. 9. 2026** zužuje iba [vnútornú priečku garáže na SP14, 140 mm](construction-garage-partition.md). R6 aj os B sa ďalej odvodzujú od zachovaného vonkajšieho úseku `C-GARAGE-SPINE-N`, teraz samostatne od Y 8 749 mm. Poloha ani význam navrhovaných základových trás sa nemenia.
Na požiadavku stavebníka z 14.09.2026 je doplnená axonometria podobná dodanej obrazovej ukážke: odkrytý obvod, vnútorné rebrá a zväčšené napojenie. Je to geometricky generovaný vektorový obrázok z aktuálneho pôdorysu, nie obrázok upravený generatívnou AI. Priložená ukážka určuje spôsob zobrazenia, nie konštrukčné rozmery alebo výstuž tohto domu.

Stavebník následne spresnil, že **doska je už vyliata aj pod lodžiou a krytou terasou**. Aktuálna ilustrácia preto zahŕňa celý L-obrys modelu vrátane oboch plôch. Ide o oznámený rozsah (`CLIENT_REPORTED`), nie geodeticky zameranú dosku. Obrázok má **ulicu dole, garáž vľavo a krídlo s obývačkou vpravo**, bez zrkadlenia. Toto spresnenie nemení geometriu domu ani hotový pôdorys C/B/B.

Výstupy v `output/pdf/construction-cbb/`:

- `foundation-axon-color.svg` a `.png`: farebná priestorová ilustrácia.
- `foundation-axon-mono.svg` a `.png`: čiernobiela verzia.
- Nový list **D1.1.ZA-03**, strana 16 celej sady A1; sada má teraz 25 listov.

Generátor je [foundation-axon.mjs](../scripts/construction-documentation/foundation-axon.mjs). Volá sa pri existujúcom exporte výkresov. Vstupné hodnoty, ich stav aj SHA-256 zdrojov sa ukladajú do `model-snapshot.json`. Axonometria sa neoznačuje 1:50: nemá slúžiť na odmeriavanie výkopov. Pôvodný pôdorys, jeho osi a kódy sa nemenia.

## Obvod a jeho dôkazová úroveň

Celý modelový L-obrys `HOUSE.footprintMm`, použitý na zobrazenie oznámeného rozsahu vyliatia (`castOutline`), má rohy v mm:

```text
(6440,3000) → (28040,3000) → (28040,22035) → (21040,22035)
→ (21040,11200) → (6440,11200) → začiatok
```

Celý rozsah má **modelové rozmery 21 600 × 19 035 mm**. Zahŕňa krytú terasu po Y22035 aj lodžiu pri garáži. Uzavretý dom má hĺbku 16 535 mm po fasádu Y19535; táto hranica oddeľuje interiér od terasy a **nie je odstrihnutím rozsahu základov alebo oznámenej dosky**. Pôvodná ustúpená obálka uzavretého domu zostáva v dátach ako `closedOutline`, oddelene od `castOutline`.

Záznam `reportedCastScope` uchováva oznámenie stavebníka. Skutočne zamerané rozmery, hrúbka dosky a geometria už existujúcich rebier zostávajú neurčené (`null`). Modelový obrys sa preto nesmie vydávať za zameranie vyhotovenej konštrukcie.

**Modrý horný pás 350 × 600 mm je zadaný rozmer v navrhovanej polohe po celom L-obvode.** Pri fasádach návrhová strednica vychádza z vnútorných líc pôvodného pôdorysu a polovice nominálneho jadra 300 mm smerom von. Nepreberá 330 mm presah vizualizačného muriva do podláh a necentruje sa pod obálkou ETICS. Na vonkajšom konci krytej terasy je Y21685 výslovne návrhový odstup **200 + 150 mm od Y22035**. Neodvodzuje sa z `NN.inner`, ktoré označuje vzdialenú zadnú hranicu terasy, a nepotvrdzuje tam súvislú fasádnu stenu ani zameraný pás.

```text
(6794,3354) → (27691,3354) → (27691,21685) → (21393,21685)
→ (21393,10849) → (6794,10849) → začiatok
```

Tieto nové strednice nenahrádzajú pôvodné osi A–F / 1–6. Šírka 350 mm sa kreslí ±175 mm. Nie je to tvrdenie, že takto leží už vybetónovaný pás. Vzťah k nemu, šírka spodného pásu, základová škára a absolútne výšky zostávajú neurčené (`null`). Úseky pri zadnej stene obývačky a pri lodžii sa teraz zobrazujú ako vnútorné návrhové trasy R4–R6. Lodžiová bočná stena `C-GARAGE-SPINE-N` má v modeli rolu `PARTITION`; jej zakreslenie v R6 nepotvrdzuje nosnú funkciu.

Prerušovaný sivý pás pod modrou časťou je **grafický náznak pokračovania do neurčenej spodnej konštrukcie**. Jeho vykreslená hĺbka ani šírka sa nesmú použiť na výkop alebo výkaz betónu. Stavebník uviedol existujúci pás 600 mm v zemi; tento údaj sám neurčuje hĺbku nového výkopu, úroveň hornej pracovnej škáry alebo základovej škáry.

## Zelené trasy na výpočet

| Trasa | Navrhovaná strednica v mm | Nadväznosť |
| --- | --- | --- |
| R1 | (20691,5;3354) → (20691,5;10849) | Pod `C-KID-ENTRY-WALL` a `C-GARDEN-KID-EAST`. Spojenie pod chodbou Y6412–7791 je nový návrh, nie existujúca stena. |
| R2 | (21393;10862) → (27691;10862) | Pod `C-KITCHEN-BEARING-WALL` a `…-E`. Nosné úseky X22639–26081 a X26881–27541 zachovávajú D11. Západný úsek po X22639 je nový prenos do zalomenia obvodu; nie podpora pod súvislou západnou stenou. |
| R3 | (23454,5;3354) → (23454,5;5282,5) → (22842;5282,5) | Pod `C-ENTRY-OFFICE-EAST` a `…-RETURN`. Steny majú hrúbku 175 mm; nosná funkcia, vetva a jej voľný koniec vyžadujú výpočet. |
| R4 | (21393;19185) → (27691;19185) | Pod zadnou stenou obývačky `NN2`, na hranici domu a zahrnutej krytej terasy. Súvislá návrhová trasa zahŕňa aj úsek pod O8; nepotvrdzuje existujúci pás. |
| R5 | (6794;8897) → (10993;8897) | Pod zadnou stenou garáže `L` pri zahrnutej lodžii, vrátane úseku pod D6. Napojenie na R6 je návrhový uzol. |
| R6 | (10993;8897) → (10993;10849) | Bočný styk lodžie podľa `C-GARAGE-SPINE-N`. Zdroj má rolu `PARTITION`; ide o koordináciu trasy pod stenou, nie potvrdenie jej nosnej funkcie. |
| R7 | (15093;3354) → (15093;10849) | **Kandidátny spojitý podporný pás na výpočet vlastnej hmotnosti SM30 AK-01/AK-02.** Dve zaťažené časti sú Y3504–6552 a Y7651–10699. Nad úsekom Y6552–7651 zostáva voľná chodba; prípadná kontinuita pásu je iba pod podlahou. |

Výška 600 mm pochádza z požiadavky stavebníka. **Zelená šírka 300 mm je výlučne grafická šírka pre čitateľný objem** (`graphicWidthIsDesign: false`); požadovaná ani staticky navrhnutá šírka rebra nie je týmto vybraná. Každá trasa má `designWidthMm`, `designReinforcement` a `foundationSupport` nastavené na `null`. Žiadna z nich nie je vydaná ako realizovateľný nosník uložený iba v zásype. Návrhové trasy sa musia uzavrieť spolu so sústavou strechy a drevených stropov, reakciami a geotechnickým návrhom.

SM30 je pri R7 zahrnutá svojou vlastnou hmotnosťou a naďalej zostáva nenosnou priečkou `PARTITION`. Strecha ani drevený strop sa na ňu neukladajú. H200 a garážové priečky sa tiež nepremenúvajú na nosné steny; ich vlastná hmotnosť sa musí zahrnúť do návrhu dosky a podopretia. Obrázok nie je výpočet podopretia každej priečky.

## R7 a zaťaženie od SM30

Od 16. 9. 2026 majú AK-01 a AK-02 každá **jednu 300 mm vrstvu klasickej obvodovej tehly**. Účel odhlučnenia zostáva. Obe zaberajú X14943–15243 mm; AK-02 má Y3504–6552 a AK-01 Y7651–10699 mm. Každý úsek je dlhý 3048 mm, modelová výška oboch murovaných telies je Z0–3125 mm.

Os muriva X15093 je zhodná s kandidátnou osou R7. Dva priamo zaťažené úseky majú spolu 6096 mm; návrhová trasa R7 medzi obvodovými osami má 7495 mm. **Chodba Y6552–7651 ostáva voľná v celých 1099 mm.** Prípadná kontinuita pásu cez ňu je iba pod podlahou.

**Hmotnosť novej steny zatiaľ nie je určená.** Konkrétny výrobok obvodovej tehly a malty treba zvoliť a doplniť jeho deklarované údaje. Pôvodný prepočet dvojplášťovej SA30 je neaktuálny a nepoužíva sa v ZA-01, ZA-03 ani strojovom výkaze zaťaženia. Bežné omietky, kúpeľňové povrchy a vybavenie sa doplnia osobitne.

R7 nepotvrdzuje únosnosť dosky, nosnú funkciu stien, prierez, výstuž ani uloženie pásu. Preveriť treba skutočnú pätu muriva, prenos cez existujúcu dosku a cestu síl do základov; modelové Z0 nie je realizačné výškové založenie.

## Terasy a detail J

Červené prerušované obálky sú nadzemné modelové podpery krytej terasy a rohová podpera lodžie. Obe plochy sú zahrnuté do oznámeného rozsahu dosky. **Obálky podpier nie sú pôdorysnými rozmermi ich základov**. Pod 500 mm podperu sa automaticky nekopíruje 350 mm pás; R4 tieto vonkajšie podpery nenahrádza. Typ, rozmer, úroveň a prípadné konštrukčné oddelenie ich založenia zostávajú otvorené aj pri oznámenom spoločnom rozsahu vyliatia.

Krúžok J zvýrazňuje princíp spoja zeleného rebra s modrým obvodom. Nie je to výstužný kôš; nezobrazujú sa vymyslené priemery, strmene ani kotevné dĺžky. Zväčšená ukážka nemá mierku. Spôsob styku a pracovnej škáry musí určiť nový statický návrh.

Doska a zásyp sú v hlavnom pohľade odokryté pre čitateľnosť; nejde o tvrdenie, že oznámená vyliata doska chýba, ani o návrh prázdnej dutiny pod podlahou. Stav skutočnej dosky, jej vzťah k navrhovanému hornému pásu a rebrám treba zamerať a konštrukčne overiť. Rozvody nad nosnou doskou zostávajú podľa [konštrukčného zadania](construction-drawings.md).

Tento list dopĺňa požadovaný spôsob zobrazenia. Nenahrádza pôdorys výkopov, zameranie rozostavaných základov alebo výkres výstuže.

## Aktuálna revízia R7

Zdrojový modul `partition-loads.mjs` číta dve súvislé 300 mm murované telesá a ich skutočnú modelovú výšku. Hmotnosti sú explicitne `null`, so stavom `PRODUCT_SELECTION_REQUIRED`; nie sú nulovým zaťažením. Exportný overovač kontroluje jednu vrstvu na stenu, zachovanú geometriu, kandidátnu os R7 a rolu `PARTITION`. Staré exportné hodnoty SA30 sa nesmú považovať za výsledok pre SM30.
