# Výkresová dokumentácia C/B/B



Revízia **16. 9. 2026**: [vnútorná priečka garáže SP14](construction-garage-partition.md) má 140 mm namiesto 301 mm; plocha garáže po zarovnaní zuba pri regáli je 25,151355 m². Regál má 1 839 × 500 mm a kosačka je o 161 mm bližšie k stene, s medzerou 20 mm. Všetky aktuálne listy, farebné aj čiernobiele exporty, výkazy, model a knižnica sa obnovujú z tejto geometrie. Vonkajší úsek pri lodžii a osi základov zostávajú.
Zadanie zo 14.09.2026: pôdorys sa nemení. Nové pohľady, rezy, základové a strešné výkresy, situácia, výpisy a detaily majú vychádzať z aktuálneho modelu. Pôvodná dokumentácia projektanta a statika je podľa následného výslovného zadania stavebníka iba orientačný archív; nový nosný návrh ani skladby sa z nej nepreberajú.

**Stav: rozpracované, nevydané na realizáciu.** Geometrický export nepreukazuje nový statický návrh. Chýbajúcu výstuž, prierezy, založenie, kotvenie, vrstvy a výšky nemožno nahradiť odhadom. Cieľ kompletnej realizačnej dokumentácie nie je splnený.

## Vytvorenie a kontrola

`npm run docs:drawings` obnoví meranú geometriu a vytvorí farebnú aj čiernobielu vektorovú sadu pod `output/pdf/construction-cbb/`. Mierka výkresov je 1:50 na A1 841 × 594 mm; detail vrstiev 1:5 a detail monolitu 1:10 majú vlastnú mierku. Situácia je rozdelená na dva nadväzujúce listy bez zmenšenia. Tlačiť na 100 %, bez prispôsobenia strane.

`node scripts/construction-documentation/verify.mjs` kontroluje kódy, polohy a šírky otvorov, rezové roviny, horný svetlík, skutočnú strechu v reze, výber B/B a pretečenie textov. Vizuálne treba skontrolovať každý list oboch posledných PDF. Záznam `model-snapshot.json` obsahuje odtlačky zdrojov; `drawing-register.json` uvádza stav každého listu. Staré pásy F-01 až F-11 nie sú vstupom nového návrhu.

`python3 scripts/construction-documentation/verify_pdf.py` s knižnicou `pdfplumber` meria skutočný PDF MediaBox a vektorové mierkové úsečky vrátane pôvodného pôdorysu; PDF nemení ani nepreškáluje. Výsledok je v `pdf-verification.json`.

Predchádzajúca kontrola exportu 14.09.2026 sa vzťahovala na pôvodných 22 listov v každej verzii: bez pretečenia textov, vizuálne overená farba aj mono, mierkový úsek 20 mm nameraný ako 19,999927 mm na papieri. Následná revízia podľa údajov o stavbe pridáva ZA-02 a TZ-01, teda 24 listov. Aktuálny výsledok kontroly je uložený v `verification.json` a `pdf-verification.json`; staršie výsledky sa nepovažujú za overenie nového exportu.

Predchádzajúca lokálna kontrola revízie 14.09.2026, exporty 17:17:07 / 17:17:15: všetkých 24 listov oboch PDF vizuálne prezretých, po posledných opravách opätovne prezreté pohľady a SK-01. Bez kolízií či orezu textov. Overené A1 MediaBoxy, 20 mm mierkové úsečky aj označenie detailu 1:10; prešli odtlačky vstupov, ochrana neznámeho ΔFFL pred náhradou nulou, 68 súvisiacich testov, cielený ESLint, `git diff --check` a lokálny build aplikácie. Build má upozornenia nástroja na veľké balíky a duplicitný názov CSS; skončil úspešne. Hlavná/archívna geometria strechy je overená aj v NullEngine. Pôdorysný generovaný JSON s 1 968 komponentmi zostal nezmenený. Nebolo publikované ani potvrdené realizačné vydanie; tieto kontroly nepreukazujú statickú únosnosť alebo vhodnosť existujúcich základov.

Kontrola následnej revízie `CLIENT-CONSTRUCTION-20260914-TIMBER-STORAGE`, exporty 14.09.2026 o 19:24:15 / 19:24:23 CEST: generovanie, kontrola zdrojov a cielený ESLint prešli. Oba PDF majú 24 listov, správny formát A1 a 20 mm mierkové úsečky; automatická kontrola nezistila pretečenie obsahu. Všetkých desať dotknutých strán (1, 11–13, 15–17, 19, 22 a 24) bolo nanovo vykreslených a vizuálne skontrolovaných vo farbe aj čiernobielo, bez kolízií a orezu. Overenie zachovania neznámych absolútnych výšok, skladovacieho účelu povaly, drevených stropov a návrhovej podesty D2 prešlo. Rozlišujú sa oba styky dosky s horným pásom; hrúbka dosky sa nezapočítava dvakrát. Ide o kontrolu dokumentácie a geometrických väzieb, nie o výpočet únosnosti alebo realizačné vydanie. Aplikačný build z predchádzajúcej kontroly sa pri tejto úprave dokumentácie neopakoval.

Existujúci `ExportSheet` sa vykresľuje bezo zmeny geometrie. Samostatne sa pridávajú iba stopy A-A, B-B a C-C. Nové listy importujú rovnaké `GRID_X`, `GRID_Y`, `FACADES` a `CODED_OPENINGS`. O1–O10 a D1–D16 sa neprečíslujú; O11 je doplnený svetlík nad rovinou pôdorysného rezu. Jeho profil pochádza z aktuálneho rendereru, nie z výrobnej šablóny.

Nadväzujúca kontrola doplnila do rezov pôvodné osi, súvislé kótové reťazce líc a hrúbok stien, úplný úsek západnej terasy 3 000 mm, modelované stupne a presné podbitkové polygóny. A-A obsahuje aj rozmery pásu nad presklením 6 000 × 500 × 300 mm s úrovňami +2,750/+3,050. Hlavy podpier a rotované 45 mm podbitkové panely boli porovnané so svetovými vrcholmi skutočnej Babylon scény; najväčšia odchýlka bola menšia než 0,0004 mm. Je to overenie zobrazeného obalu, nie návrh jeho nosnej konštrukcie. DT-01 obsahuje zväčšený pôdorysný detail D1/J1/J2 v 1:5. SK-01 zachováva aj kódy SN30/SN20, SP30/SP20/SP14 a SP10/SP6 z pôvodnej legendy.

**Zistený vnútorný nesúlad modelu:** metadáta obývačky pri reze A-A vedú Y 11 012–19 533 mm (8 521 mm), ale zadná plná stena začína už Y 19 035 mm. Svetlá vzdialenosť skutočných líc je 8 023 mm. Rez kótuje tieto líca; metadáta miestnosti ani hotový pôdorys sa neprepisujú. Pri B-B sa zachováva pôdorysné vnútorné líce X 21 543 mm a svetlá šírka 5 998 mm, nie pomocné líce renderovanej vrstvy X 21 540 mm. Pred realizačným vydaním treba uzavrieť aj túto koordináciu zdrojov.

Modelované stupne majú X 23 340–25 740 mm, dva úseky hĺbky 380 mm od Y 22 035 do 22 795 mm, hrúbku 70 mm a horné úrovne +0,015/−0,025 m. Rozdiel oproti terase +0,020 je iba 5 mm a medzi stupňami 40 mm. Tieto hodnoty sú zakreslené ako existujúca modelová geometria; nie sú vydané ako konečný návrh schodiska a terénu.

### Priestorový pohľad na základy

Následná obrazová požiadavka stavebníka dopĺňa **D1.1.ZA-03: priestorový pohľad na pásy a rebrá**; sada má 25 listov. Farebný a čiernobiely obrázok sa ukladajú aj samostatne ako `foundation-axon-color/mono.svg` a `.png`. Stavebník spresnil, že doska je už vyliata aj pod lodžiou a krytou terasou: ilustrácia preto zahŕňa **celý modelový L-obrys 21 600 × 19 035 mm**. Ide o oznámený rozsah (`CLIENT_REPORTED`), nie zameraný stav; skutočné rozmery, hrúbka dosky a existujúce rebrá zostávajú neurčené. Hĺbka uzavretého domu 16 535 mm neznamená odstrihnutie základov pred terasou. **Ulica je dole, garáž vľavo a krídlo vpravo**, bez zrkadlenia; nové oznámenie nemení geometriu domu ani hotový pôdorys. Modrý horný monolit má zadaných 350 × 600 mm; jeho strednica vrátane zadnej trasy Y21685 je nový návrh. Zelené R1–R3 sledujú nosné úseky izieb, kuchyne a vstupu, R4 zadnú stenu obývačky pri terase, R5 zadnú stenu garáže pri lodžii a R6 jej bočný styk. R6 nepotvrdzuje nosnú funkciu modelovej priečky. R7 dopĺňa kandidátny pás pod vlastnou hmotnosťou SM30 AK-01/02; označené sú iba ich dva skutočné úseky, chodba zostáva voľná. ZA-01 uvádza jednu 300 mm obvodovú tehlu a modelovú výšku 3125 mm; hmotnosť čaká na výber konkrétneho výrobku. Dôvod odhlučnenia zostáva. Pôvodný dvojplášťový prepočet neplatí a únosnosť existujúcej dosky nie je potvrdená. Šírky rebier, výstuž, podopretie a skutočný výkop zostávajú neurčené. [Podklad axonometrie a presné súradnice](construction-foundation-axon.md).

## Záväzné nové požiadavky

- Zachovať obrys, osi, materiálové rozhodnutia a hotový pôdorys C/B/B.
- Voda a odpad sa vedú **nad nosnou doskou** v novej podlahovej skladbe. Žiadne dodatočné vrty do dosky. Nový návrh musí určiť priemery, trasy, spády, križovania, celkovú hrúbku vrstiev a presné vývody cez obvod.
- Nové základy, doska, vence, preklady, krov, oceľové rámy a spoje vyžadujú koordinovaný statický výpočet aktuálneho domu. Geotechnické parametre založenia domu ani nový statický výpočet nie sú doložené.
- H200 a SM30 zostávajú vo zvolenej geometrii. Ich pôvodnú nosnú funkciu, stabilitu, kotvenie a napojenia treba vyriešiť v novom návrhu.
- Kotolňa B má v modeli iba rezervu napojenia dymovodu pod stropom; neexistuje hotový návrh vonkajšej trasy komína.

### Doplnenie stavebníka 14.09.2026: výšky, kúrenie, povala a rozostavané základy

Strojovo čitateľný záznam je v [client-brief.ts](../scripts/construction-documentation/client-brief.ts). Neznáme hodnoty majú `null`; nepoužíva sa náhradná nula ani historická výška 184 m z `HOUSE.datumElevationM`.

- **R0 = 184,200 m**, najvyšší bod ulice pri rohu pracovne, podľa údajov stavebníka získaných od geodeta. Je to spoločná referenčná nula. Bpv, presné XY bodu a nivelácia hotovej podlahy či vybetónovaného pásu ešte nie sú potvrdené.
- **M0 = pôvodná modelová podlaha.** Nové výškové značky majú predponu M. Rozdiel `ΔFFL = M0 − R0` je zatiaľ neurčený; výška nad ulicou je `M + ΔFFL`. Pôvodný pôdorys má vysvetľujúci dodatok bez zmeny geometrie. Z R0 sa bez ďalšieho údaja nerobí hotová podlaha.
- **Podlahové vykurovanie** v miestnostiach mimo garáže 1.12, technickej 1.07 a sprchovej plochy 1.05. Výklad slova „sprcha“ sa týka sprchovej plochy z modelu, nie automaticky celej kúpeľne. TZ-01 vyznačuje rozsah požiadavky; nekreslí vymyslené okruhy ani rozstupy rúrok.
- **Povala iba na odkladanie vecí**, potvrdené následným zadaním. Nad plochými stropmi vrátane garáže a technickej; mimo obývačky s kuchyňou 1.03. **Nosné stropy a záklop drevené, bez betónovej stropnej dosky a nadbetonávky.** Bývanie na povale sa nenavrhuje. Návrh musí ešte určiť plošné aj bodové skladovacie zaťaženia, polohy regálov, prierezy, spoje, prístup a úplnú skladbu; samotné slovo „odkladanie“ nepreukazuje únosnosť.
- **Falcovaný plech bez architektonického presahu.** Aktívna rovina končí na čele terasy Y 22 035; archív si zachováva pôvodné Y 22 085. Hotový pôdorys, otvory a krytá terasa sa nemenia. Žľaby a vizualizačné lišty vyžadujú samostatný finálny detail. Audit: [strecha a kúrenie](construction-roof-heating-basis.md).
- **Monolitické založenie bez strateného debnenia.** Stavebník opisuje spodný vybetónovaný pás 600 mm v zemi; jeho šírka, nivelácia a výstuž nie sú doložené. Horný pás požaduje 350 × 600 mm, vnútorné rebrá v horných 600 mm, zhutnenú zeminu a dosku v rozsahu 150–200 mm. Rozsah hrúbky dosky nie je finálne zvolená hrúbka. Detail ZA-02 kótuje zadaný horný monolit; nevymýšľa spodnú šírku, výstuž ani úroveň dosky.
- **C16/20 je požiadavka, nie schválená špecifikácia všetkých prvkov.** Treba overiť dodací list, expozíciu, krytie a nový statický návrh. Spodný pás a exponovaný sokel sa neposudzujú automaticky rovnako.

Priložené fotografie sú byte-for-byte zachované v `output/research/construction-site-20260914/`, ich SHA-256 sú súčasťou exportu. Na detailnej fotografii vidno trhlinu a nerovnomerný povrch. Fotografia neurčuje príčinu, hĺbku ani závažnosť; dotknutý úsek má pred ďalším zakrytím posúdiť statik na mieste.

[Podklad pre nosnú sústavu](construction-structural-basis.md) obsahuje aktuálne podporové zóny K-01 až K-09 a variant na výpočet a ocenenie: pôdne väzníky nad plochými stropmi a samostatnú katedrálovú sústavu. Uzol L nemá súvislú zadnú podporu, takže bežný priečny väzník sa tam nedá iba opakovať. Vnútorné rebrá potrebujú prenos zaťaženia do overeného podkladu alebo podpor; ich samotná výška 600 mm nestačí. H200 a SM30 sa nezaťažujú ako nosné steny. Prierezy a výstuž zostávajú otvorené do výpočtu sústavy.

### Drevené stropy a aspoň jeden vstupný schod

Následná revízia `CLIENT-CONSTRUCTION-20260914-TIMBER-STORAGE` uzatvára účel povaly a materiál stropov. Požiadavka na drevené stropy nemení predchádzajúce monolitické základy ani prízemnú dosku. Pri pravidelnom trakte sa rozpracuje drevený pôdny väzník; uzol L potrebuje samostatné drevené polia a prenosové prvky. Katedrála zostáva otvorená. Výrobná geometria a prierezy sa neodvodzujú iba z obalu vizualizácie.

Stavebník neurčuje absolútnu výšku podlahy sám; jej návrh je úlohou projektu. Záväzná požiadavka je **aspoň jeden schod pri hlavnom vstupe D2**. Návrh VS1 na SI-01 využíva existujúci prístup SITE-ENTRY: podesta **1 500 × 1 500 mm**, X **21 415–22 915**, Y **1 500–3 000 mm**, jeden návrhový stupeň **150 mm** na čele Y **1 500 mm**. Tieto doplnkové prvky sú označené `COORDINATION_PROPOSAL`; pôvodné otvory, steny, odstupy a 3D sa nemenia. D2 sa otvára dovnútra, čelo stupňa je mimo jeho modelového pohybu.

Výška stupňa je rozdiel medzi miestnym prístupom a vonkajším čelom podesty. **Nie je to ΔFFL voči ulici R0.** Zníženie podesty pri prahu a jej spád zostávajú otvorené. Vzťah k miestnemu prístupu je `FFL − prístup = d + s × L + h`; s je bezrozmerný spád. Iba pracovný príklad d = 20 mm, s = 0,02, L = 1 500 mm a h = 150 mm dáva 200 mm. Nie je to zvolená hotová podlaha ani realizovateľný prahový detail. [Audit a návrh vstupu](construction-entry-basis.md) opisuje aj konflikt modelového spodného rámu 78 mm s prahom 20 mm a potrebu výrobného detailu.

Pre nadväznosť na hotový spodný pás platí v mm **ΔFFL = zE + 600 + j + p**. zE je zamerané horné líce existujúceho pásu voči R0; j je rozdiel horného líca nosnej dosky oproti hornému lícu nového pásu; p je celá podlahová skladba nad doskou. Pri zarovnaných horných lícach j = 0, pri doske úplne nad pásom j = hrúbka dosky. ZA-02 oba prípady rozlišuje. Bez zE, zvoleného styku a p sa hotová podlaha nesmie vymyslieť. Od stavebníka sa teraz žiada zameranie existujúceho pásu, nie vlastné rozhodnutie o FFL.

Podľa štúdie Z7/Z22 sa kontroluje aj najviac trojica stupňov pred domom a podlaha maximálne 500 mm nad upraveným terénom naviazaným na najbližší obrubník. Návrhových 150 mm nie je vydávaných za automaticky schválený normový rozmer alebo dôkaz splnenia celého prístupového detailu.

Kontrola SK-01 zachovala kódy SP10/SP6 a hrúbky 100/60 mm, ale nepreberá chybný príklad „Rigips W112“ zo starej legendy. W112 je systém Knauf; pre tieto nové vrstvy nie je zvolený konkrétny výrobok. Pôvodný pôdorys sa nemenil.

## Územný plán a výšky

Overené 14.09.2026: [platná dokumentácia](https://www.mikulov.cz/obcan/platna-dokumentace-brezi-up) uvádza ÚP po zmene č.3, účinný od 22.05.2026. Mapové priradenie katastrálneho obrysu parcely 6012/26 k oficiálnym výkresom zodpovedá Z.7/SV, urbanistickej zóne C a triede výšky rímsy 4,5 m; ide o interpretáciu mapy, nie rozhodnutie úradu. [Hlavný výkres](https://www.mikulov.cz/data/content_files/832/1b-hlv-1.pdf), [urbanistická kompozícia](https://www.mikulov.cz/data/content_files/832/1f-urbanisticka-kompozice.pdf).

Aktuálny [text ÚP](https://www.mikulov.cz/data/content_files/831/brezi-up-oop-uz.pdf), I.F.3, tlačené strany 34–35: výška rímsy sa posudzuje na uličnej strane od najvyššieho bodu komunikácie pred domom po spodnú úroveň rímsy. Zóna C pre obytné stavby určuje sedlovú strechu 25–40°. Model má odkvapovú hranu roviny M+3,125 a hrebeň rovín M+5,560 m; sklony z vrcholov 30,706180°/34,826887° spĺňajú tento rozsah. **Hrana strešnej roviny nie je overený spodok rímsy.** Pri oznámenom R0 = 184,200 m vychádza podmienený limit spodnej uličnej rímsy **188,700 m**. Hrana roviny je 187,325 + ΔFFL a hrebeň rovín 189,760 + ΔFFL m, pričom ΔFFL zatiaľ nepoznáme. Biely vizualizačný rám portálu siaha nad hrebeň rovín; údaj +5,560 nie je najvyšší bod všetkých renderovaných prvkov. Hodnota 4,5 m nie je limitom hrebeňa. Podrobný [výškový podklad](construction-height-basis.md) rozlišuje tieto veličiny a potrebné potvrdenia.

[Štúdia Z7/Z22 s doplnkom 2026](https://www.mikulov.cz/data/content_files/731/textova-cast-souhlas-obce-stavebni-cara-5m.pdf), PDF strany 2–4: samostatný dom má uličnú čiaru 3 m; dodatok 5 m sa týka radových domov. Treba preveriť aj odstupy medzi obytnými domami, podlahu voči terénu, zastavanosť, zeleň a dve parkovacie miesta. Modelové 3 000 mm k hranici samy nepotvrdzujú vzdialenosť susedného domu.

## Otvorené body pred realizačným vydaním

R01 nový nosný systém; R02 geotechnika a založenie; R03 nová podlaha a rozvody; R04 strecha a veniec; R05 výškopis a osadenie; R06 sokel/ETICS/otvory; R07 akustické napojenia; R08 dymovody a odvodnenie; R09 výrobná špecifikácia okien a dverí. Konkrétne požadované vstupy sú na prvom liste sady. Žiadny list nie je označený za schválený realizačný výkres.

## Kontrola voči úplnému zadaniu

| Požiadavka | Aktuálny dôkaz | Stav pred stavbou |
| --- | --- | --- |
| Všetky strany a zalomené fasády | PO-01 až PO-08, dva doplnkové pohľady vratných líc, pôvodné kódy a kóty | Geometria z modelu; chýba konečný terén, sokel, detaily povrchov a vonkajší dymovod kotolne |
| Dva až tri rezy so stopami | RE-01 až RE-03, spoločné CUTS v pôdoryse aj rezoch | Tri rezy existujú; nové základy, podlahové a strešné vrstvy, nosné prvky a spoje stále chýbajú |
| Pôdorys základov | ZA-01 obsahuje presné nadväzujúce steny a osi, ZA-02 rozmery zadania, ZA-03 priestorové návrhové trasy | Nesplnené: bez nového návrhu založenia a výstuže |
| Pôdorys strechy | ST-01 zo spoločných vrcholov, rovín a hrán strechy | Geometria existuje; krov, kotvenie, skladby a odvodnenie sú otvorené |
| Situácia a odstupy 3 000 mm | SI-01/SI-02 z aktívnej transformácie, UP-01 z oficiálnych podkladov | Modelové odstupy overené; zameranie a výškové osadenie chýbajú |
| Okna a dvere použiteľné pre výrobu | OT-01/OT-02 s kódmi, polohami, otvormi a pohybom krídel | Výpis otvorov existuje; profily, vlastnosti, montážne škáry a výrobná špecifikácia chýbajú |
| Úplné skladby a podstatné detaily | SK-01/DT-01, aktuálne H200/SM30 a J1/J2 | Čiastočné: nové podlahy/strecha, sokel, prahy, nadpražia, nosné a tesniace spoje nie sú uzavreté |
| A1, 1:50, červené kóty, materiálové šrafy, razítko, mono | Dve vektorové PDF, revízia na 25 listov; výsledky aktuálnych kontrol v overovacích JSON | Lokálne detaily 1:5 / 1:10; ZA-03 axonometria bez odmeriavania; stav nevydané na realizáciu |
| Murár, tesár a oknár môžu vymerať a postaviť bez dopytovania | Chýbajúce R01–R09 a neuzavretý nesúlad metadát sú priamo uvedené v sade/zázname | **Nesplnené.** Realizačné vydanie vyžaduje nový koordinovaný odborný návrh, geotechnické parametre a geodetický výškopis |

Chýbajúce geotechnické hodnoty, skutočné výšky komunikácie a pozemku ani nový statický výpočet sa nedajú získať meraním 3D obalu. Staré orientačné podklady sa za ne nepovažujú. Uvedené otvorené časti sú požadovanou zostávajúcou prácou, nie zúžením pôvodného cieľa.
