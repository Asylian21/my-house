# Priestorový pohľad na základy C/B/B

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
| R7 | (15093;3354) → (15093;10849) | **Kandidátny spojitý podporný pás na výpočet vlastnej hmotnosti SA30 AK-01/AK-02.** Dve zaťažené časti sú Y3504–6552 a Y7651–10699. Nad úsekom Y6552–7651 zostáva voľná chodba; prípadná kontinuita pásu je iba pod podlahou. |

Výška 600 mm pochádza z požiadavky stavebníka. **Zelená šírka 300 mm je výlučne grafická šírka pre čitateľný objem** (`graphicWidthIsDesign: false`); požadovaná ani staticky navrhnutá šírka rebra nie je týmto vybraná. Každá trasa má `designWidthMm`, `designReinforcement` a `foundationSupport` nastavené na `null`. Žiadna z nich nie je vydaná ako realizovateľný nosník uložený iba v zásype. Návrhové trasy sa musia uzavrieť spolu so sústavou strechy a drevených stropov, reakciami a geotechnickým návrhom.

SA30 je pri R7 zahrnutá svojou vlastnou hmotnosťou a naďalej zostáva nenosnou priečkou `PARTITION`. Strecha ani drevený strop sa na ňu neukladajú. H200 a garážové priečky sa tiež nepremenúvajú na nosné steny; ich vlastná hmotnosť sa musí zahrnúť do návrhu dosky a podopretia. Obrázok nie je výpočet podopretia každej priečky.

## R7 a zaťaženie od SA30

Pripomienka stavebníka dopĺňa chýbajúcu trasu podopretia ťažkých akustických priečok. `AK-02 / C-OPEN-HALL-S` má Y3504–6552 a `AK-01 / C-OPEN-HALL-N` Y7651–10699. Každá je dlhá **3048 mm**; obidve majú X14943–15243. Skladba v [acoustic-walls.ts](/Users/davidzita/www/dom/lib/acoustic-walls.ts:11) je západný murovaný plášť X14943–15043, vata X15043–15143 a východný murovaný plášť X15143–15243. Nie je to plná murovaná stena hrúbky 300 mm.

Všetkých šesť skutočných modelových komponentov má **Z0–3125 mm**, zhodne s [generátorom stien](/Users/davidzita/www/dom/lib/babylon-interior.ts:777). Svetlá výška miestností sa tu nepoužíva namiesto výšky muriva. Osi murovaných plášťov X14993 a X15193 ležia **±100 mm od kandidátnej osi R7 X15093**. Pás medzi obvodovými osami má návrhovú dĺžku 7495 mm, ale priame zaťaženie priečkami sa vyznačí iba v dvoch skutočných úsekoch, spolu 6096 mm. **Chodba medzi nimi ostáva voľná v celých 1099 mm.** Do chodby sa nepridáva stena, stĺp ani zvýšený betónový prah.

Hmotnostný podklad je [technický list výrobcu LeierPLAN 10 N+F, strana 1](https://www.leier.sk/wp-content/uploads/2025/07/Technicky-list-LP10-NF.pdf). Uvádza pre jeden 100 mm plášť murivo bez omietky 73 kg/m². Pri modelovej výške 3,125 m sa pre dva plášte počíta:

| Hmotnostná veličina | Prepočet | Výsledok |
| --- | --- | --- |
| Dva plášte muriva bez omietky | 2 × 73 | 146 kg/m² steny |
| Hmotnosť na meter priečky | 146 × 3,125 | 456,25 kg/m |
| Jeden úsek AK-01 alebo AK-02 | 456,25 × 3,048 | 1390,65 kg |
| Oba úseky spolu | 2 × 1390,65 | **2781,30 kg** |

Ide o vypočítanú hmotnosť muriva bez omietok podľa technického údaja, nie zameranú hmotnosť stavby ani konečné návrhové zaťaženie `q`. Doplniť treba vatu, omietky, obklady, kotvené vybavenie a skutočné výškové založenie plášťov; modelové Z0 samo neurčuje realizačnú pätu muriva voči nosnej doske. Pri výpočte sa overí konkrétny dodaný výrobok a spôsob murovania.

Obidva plášte treba posúdiť ako dve zaťažovacie línie. Rozdielne povrchy alebo vybavenie môžu zmeniť ich pomer; výslednica sa nesmie bez preverenia umiestniť do stredu R7. Šírka, výstuž, spôsob uloženia pásu, prenos cez dosku a nadväznosť na existujúce základy zostávajú otvorené. Spoločná kandidátna trasa sama nepotvrdzuje vyhovujúci akustický detail ani neoprávňuje vytvoriť neoverené tuhé mosty medzi plášťami.

## Terasy a detail J

Červené prerušované obálky sú nadzemné modelové podpery krytej terasy a rohová podpera lodžie. Obe plochy sú zahrnuté do oznámeného rozsahu dosky. **Obálky podpier nie sú pôdorysnými rozmermi ich základov**. Pod 500 mm podperu sa automaticky nekopíruje 350 mm pás; R4 tieto vonkajšie podpery nenahrádza. Typ, rozmer, úroveň a prípadné konštrukčné oddelenie ich založenia zostávajú otvorené aj pri oznámenom spoločnom rozsahu vyliatia.

Krúžok J zvýrazňuje princíp spoja zeleného rebra s modrým obvodom. Nie je to výstužný kôš; nezobrazujú sa vymyslené priemery, strmene ani kotevné dĺžky. Zväčšená ukážka nemá mierku. Spôsob styku a pracovnej škáry musí určiť nový statický návrh.

Doska a zásyp sú v hlavnom pohľade odokryté pre čitateľnosť; nejde o tvrdenie, že oznámená vyliata doska chýba, ani o návrh prázdnej dutiny pod podlahou. Stav skutočnej dosky, jej vzťah k navrhovanému hornému pásu a rebrám treba zamerať a konštrukčne overiť. Rozvody nad nosnou doskou zostávajú podľa [konštrukčného zadania](construction-drawings.md).

Tento list dopĺňa požadovaný spôsob zobrazenia. Nenahrádza pôdorys výkopov, zameranie rozostavaných základov alebo výkres výstuže.

## Aktuálna revízia R7 — overenie exportu

Finálne PDF z 14.09.2026 o **21:42:36 / 21:42:56 CEST** majú po 25 listov. Geometria SA30, kandidátna os R7, dva zaťažené úseky a prepočet hmotnosti sú overené proti exportovanému modelu. Nový modul `partition-loads.mjs` číta výšku priamo zo štyroch murovaných modelových plášťov; oddelene uchováva čisté tehly a výrobcom deklarované murivo bez omietky. Súčet aj prepočet na meter sú reprodukovateľné. Chýbajúce doplnkové hmotnosti, konečné návrhové zaťaženie, prierez, výstuž a podopretie zostávajú neurčené.

Prešli odtlačky zdrojov, geometrické a výpočtové invarianty, kontrola neprepisovania roly `PARTITION`, orientácia celého L-obrysu a kontrola pretečenia všetkých 25 strán. Fyzické formáty A1 a 20 mm kalibračné úsečky sú overené na oboch PDF. Cielený ESLint a `git diff --check` prešli.

ZA-01, ZA-02 a ZA-03 boli nanovo vykreslené z oboch PDF a vizuálne skontrolované v celku aj detaile. Tabuľka uvádza 456,25 kg/m, 1390,65 kg na stenu a 2781,3 kg spolu. Popis R7 je posunutý mimo chodby s odkazovou čiarou; oba skutočné zaťažené úseky sú oddelené a medzera je viditeľná. Pravá legenda a spodné texty sú bez kolízií. Samostatné PNG majú 3280 × 2060 px; v každom pixeli mono verzie platí R = G = B. Pôdorys ani aplikačný 3D model sa týmto doplnením nemenili; build aplikácie sa neopakoval. Tieto kontroly **nie sú statickým posúdením ani potvrdením dostatočnosti R1–R7**.

## Predchádzajúce overenie celého L-obrysu s R1–R6

Revízia `CLIENT-CONSTRUCTION-20260914-FULL-CAST-FOOTPRINT`, PDF z 14.09.2026 o 20:45:57 a 20:46:15 CEST: oba súbory majú 25 listov. Prešli odtlačky zdrojov, geometrické kontroly celého obrysu a trás R1–R6, orientácia ulice a ochrana neznámych údajov. R6 zostáva koordináciou pod modelovou priečkou, nie premenovaním priečky na nosnú stenu. Automatická kontrola nenašla pretečenie obsahu; fyzické A1 rozmery a 20 mm kontrolné úsečky sú overené na všetkých listoch. Cielený ESLint a `git diff --check` prešli.

Vtedajší ZA-03 bol nanovo vykreslený z oboch PDF a vizuálne prezretý v celku aj detaile. LODŽIA bola plne čitateľná; R5 a R6 ju neprekrývali. Orientácia, celý obvod, všetkých šesť trás a detail J boli bez kolízií a orezu. Overené boli aj oba PNG 3280 × 2060 px a upravené popisy registra/ZA-02. V každom pixeli samostatného mono PNG platilo R = G = B. Pôdorys ani aplikačný 3D model sa nemenili; build aplikácie sa pri tejto úprave dokumentácie neopakoval. Kontroly nie sú statickým posúdením a nepokrývajú neskoršie doplnenie R7.

## Predchádzajúce overenie exportu

Nasledujúci záznam sa týka **predchádzajúcej verzie s ustúpeným obvodom a trasami R1–R3**. Jeho výsledky nepokrývajú následný celý L-obrys, opravenú orientáciu ani trasy R4–R7.

Predchádzajúce PDF z 14.09.2026 o 20:07:15 a 20:07:32 CEST mali po 25 listov. Generovanie, odtlačky vstupov, geometrické kontroly a ochrana neznámych hodnôt prešli; automatická kontrola nezistila pretečenie obsahu. Overené boli fyzické formáty A1 a 20 mm kontrolné úsečky na všetkých listoch. Cielený ESLint a `git diff --check` prešli.

Vtedajší list ZA-03 bol z farebného aj čiernobieleho PDF nanovo vykreslený a vizuálne prezretý. Skontrolované boli aj samostatné PNG 3280 × 2060 px, register a upravený popis ZA-02. Bez kolízií alebo orezania; detail J a popisy kót boli čitateľné. Každý pixel samostatného mono PNG mal R = G = B. Žiadne z týchto overení nie je statickým výpočtom. Aplikačný model sa touto ilustráciou nemenil a jeho build sa neopakoval.
