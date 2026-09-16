# Akustická stena medzi pracovňou a sprchou — záloha 274 mm

**Stav rozhodnutia: historická záložná možnosť.** Stavebník 13. 9. 2026 odmietol hrúbku 274 mm ako príliš veľkú a požiadal toto riešenie zachovať iba pre prípadný návrat. Následne výslovne zvolil **H200 ako finálnu skladbu AK-03** so zachovanou tehlou Leier a požadovaným Rw najmenej 51 dB. Nasledujúci text uchováva technický podklad a geometriu pôvodnej 274 mm zálohy; jeho posun vstupu 100 mm, plochy miestností a Rw 56 dB nepatria aktuálnemu H200.

Aktuálna dokumentácia po revízii 16. 9. 2026: [H200 — 187,5 mm hybrid s jednou Silentboard, výpočet a zarovnanie líca](office-acoustic-wall-thinner-options.md). H200 má líca Y = 6 364,5 a 6 552 mm; kúpeľňové líce nadväzuje na líce chodbovej priečky. Pri pracovňovom otvore zostáva úsek 42,5 mm. Os kúpeľňového otvoru aj krídla Y = 7 101,5 mm zostáva zachovaná. Údaj Rw približne 55,77 dB (zaokrúhlene 56 dB) pre H200 je predbežný výpočet, nie meranie presnej zostavy.

Záloha pre stenu **AK-03** medzi pracovňou 1.04 a kúpeľňou s práčovňou 1.05 používa akustické murivo **Leiertherm 25/30 AKU z výrobne Mátraderecske**, orientované na hrúbku 250 mm. S predpísanými omietkami má skladba **274 mm** a výrobcom doložené **Rw = 56 dB** pri dodržaní uvedeného vyhotovenia.[^1][^2]

Dvere kúpeľne sú vycentrované na pozdĺžnu os hlavnej chodby. Aby hrubšia stena zachovala priestor pri zárubni pracovne, jej vstup aj zalomenie pri zádverí sa posúvajú o **100 mm smerom k ulici**. Kúpeľňové líce steny, sprcha a fasádne okná zostávajú na pôvodných miestach. Pracovňa má po úprave **12,01 m²**, kúpeľňa **6,98 m²**.

Toto je geometrické riešenie záložnej skladby. Doložený akustický parameter výrobku sa odlišuje od budúceho merania v dome; údaje o dverách sú presné v modeli, pričom konkrétnu zárubňu treba dopracovať s dodávateľom.

## 1. Zadanie a hranice riešenia

Zadanie spája tri podmienky: zachovať tehlu Leier, dosiahnuť najmenej Rw 51 dB a umiestniť vstup do kúpeľne presne do osi centrálnej chodby. Sledovaná stena je vodorovný úsek dlhý 4 758 mm. Na kúpeľňovej strane nadväzuje sprcha a radiátor, na pracovňovej strane vstup a tabuľa. Preto nestačí porovnať iba celkové hrúbky materiálov.

Rozhodujúci je súčasne priestor pre dverný otvor, obložku, napojenie priečky a vybavenie. Záložná štúdia vychádzala z hlavného návrhu C/B/B a jeho osadenia domu. Pri vzniku tejto záložnej štúdie mali AK-01 a AK-02 skladbu SA30. Od 16. 9. 2026 ju nahrádza jedna 300 mm obvodová tehla SM30 so zachovaným účelom odhlučnenia; aktuálny stav je v [prehľade stien](acoustic-walls.md). Hodnota 56 dB záložného muriva sa na ne neprenáša.

Vybraný výrobok patrí do akustického radu **Leiertherm AKU**. Nie je to bežná LeierPLAN 25 ani spojené priečkovky LeierPLAN 10. Zmena produktového radu je vecnou súčasťou rozhodnutia: zachováva výrobcu a pálenú tehlu, ale poskytuje doložený výsledok celého muriva s povrchmi.

## 2. Presná os chodby a kúpeľňových dverí

Vnútorný model používa lokálne súradnice v milimetroch. Hlavná chodba vedie v smere **X**; jej pozdĺžna os preto má konštantnú súradnicu **Y**. Vycentrovanie neznamená posun dverí do polovice dĺžky domu, ale zosúladenie ich stredu s priamym pohľadom pozdĺž chodby.

Svetlé okraje jej hlavného vodorovného úseku sú Y = 6 552 a Y = 7 651 mm. Šírka je **1 099 mm** a os vychádza:

`Y_os = (6 552 + 7 651) / 2 = 7 101,5 mm`

Kúpeľňové dvere zachovávajú modelový stavebný otvor 800 mm a krídlo 700 mm. Otvor preto siaha od **Y = 6 701,5 do 7 501,5 mm**. Na oboch stranách jeho priemetu do chodby zostáva presne **149,5 mm**. Oproti predchádzajúcej polohe sa posúva o **48,5 mm smerom do záhrady**.

Model tiež mení odsadenie krídla v otvore na symetrických 50 mm. Uzavreté krídlo tak zaberá Y = 6 751,5 až 7 451,5 mm a jeho stred je opäť 7 101,5 mm. Toto rozlíšenie je podstatné: vycentrovaný stavebný otvor by pri nesymetrickom osadení ešte nezaručil vizuálne vycentrované dvere.

Výška otvoru zostáva 2 100 mm. Údaj „700 mm“ označuje modelové krídlo, nie dodávateľom overenú výslednú priechodnú šírku. Tá závisí od rámu, kovania a otvorenia. Pri realizácii sa má zo spoločnej osi vytýčiť konkrétny dodávateľský otvor; polmilimetrová súradnica vyjadruje presnú symetriu modelu, nie požadovanú stavebnú toleranciu.

## 3. Osadenie hrubšej steny v záložnom návrhu

Kúpeľňové líce je pevne na **Y = 6 602 mm**. Nová 274 mm skladba teda zaberá Y = 6 328 až 6 602 mm. Jej vrstvy v poradí od pracovne sú:

| Vrstva | Hrúbka | Rozsah Y v modeli |
|---|---:|---:|
| Vápennocementová omietka pracovne | 12 mm | 6 328–6 340 mm |
| Akustické murivo Leiertherm AKU | 250 mm | 6 340–6 590 mm |
| Vápennocementová omietka kúpeľne | 12 mm | 6 590–6 602 mm |

Pôvodná 140 mm stena mala pracovňové líce na Y = 6 462 mm. Zhrubnutie zaberá **134 mm smerom do pracovne**. Pôvodný otvor do pracovne končil na Y = 6 352 mm, takže nová stena by doň bez ďalšej úpravy zasiahla o 24 mm.

Posun pracovňových dverí o 100 mm rieši túto kolíziu. Ich 901 mm otvor sa mení z rozsahu 5 451–6 352 mm na **5 351–6 252 mm**. Medzi koncom otvoru a hotovým lícom akustickej steny zostáva **76 mm**. Na kúpeľňovej strane je medzi stenou a začiatkom nového otvoru **99,5 mm**.

Spolu so vstupom sa posúva aj 175 mm zalomenie pri zádverí: jeho pracovňové líce sa mení z Y = 5 400 na **5 300 mm**. Od neho po začiatok otvoru zostáva 51 mm. Zachováva sa tak pôvodná väzba dverí na dolný roh; neposúva sa iba krídlo do nezmeneného muriva.

Rozmery 76, 99,5 a 51 mm sú **geometricky dostupné úseky**, nie potvrdené univerzálne montážne minimá. Pred objednaním sa musia porovnať s vonkajším rozmerom obložky, potrebnou montážnou medzerou a detailom kotvenia. Širšia obložka môže vyžadovať lokálnu úpravu; nesmie sa vyriešiť svojvoľným zmenšením predpísaného akustického muriva.

## 4. Vplyv na miestnosti a vybavenie

| Priestor | Pred úpravou | Po úprave | Rozdiel |
|---|---:|---:|---:|
| Pracovňa 1.04 | 12,572442 m² | 12,012776 m² | −0,559666 m² |
| Kúpeľňa a práčovňa 1.05 | 6,976971 m² | 6,976971 m² | 0 m² |
| Zádverie 1.01 | 6,478564 m² | 6,405764 m² | −0,072800 m² |

Ide o výpočty z pôdorysných obdĺžnikov záložného návrhu 274 mm, nie o zameranie dokončenej stavby ani o aktuálne plochy H200. Viac desatinných miest umožňuje skontrolovať historický rozdiel; zaokrúhlené hodnoty zálohy sú 12,01, 6,98 a 6,41 m². Finálny obklad kúpeľne by tieto plochy ešte lokálne ovplyvnil.

Pracovňa stráca pri severnej stene pás 134 mm. Posun zalomenia jej zároveň pridáva časť priestoru pri vstupe; preto čistý rozdiel nemožno počítať iba ako dĺžka celej steny krát jej zhrubnutie. Stôl, kreslo a skriňa sa zachovávajú, tabuľa sa premiestňuje na nové líce steny. Modelový vstupný pás pri tabuli sa prispôsobuje menšej hĺbke miestnosti.

Sprcha zostáva v pôdoryse **1 250 × 900 mm**, s modelovaným vstupom 600 mm. Jej sklo a odtok nemenia polohu. Aktívne bočné okno pracovne EAST-01 zostáva v rozsahu Y = 5 212–6 212 mm; okno sprchy EAST-02 v rozsahu Y = 6 801,5–7 401,5 mm. Tieto hodnoty patria aktuálnemu návrhu, nie staršiemu základnému výkresu.

## 5. Historické porovnanie uvažovaných skladieb

Táto tabuľka zachováva stav pôvodnej rešerše. Následné výpočtové rozpracovanie a finálny výber H200 sú v [aktuálnom dokumente](office-acoustic-wall-thinner-options.md).

| Možnosť | Hrúbka pred obkladom | Doloženie požiadavky pre konkrétny celok | Vyhodnotenie |
|---|---:|---|---|
| LeierPLAN 100 + vlna 100 + LeierPLAN 100 | 300 mm jadro; pri 15 mm vonkajších omietkach 330 mm | Presný skúšaný celok nenájdený | Väčší zásah do vstupu; číslo Rw sa nedá garantovať |
| LeierPLAN 100 + vlna 50 + LeierPLAN 100 | 250 mm jadro; s uvedenými vonkajšími omietkami 280 mm | Presný skúšaný celok nenájdený | Priestorovo blízke, ale bez dôkazu požadovaných 51 dB |
| LeierPLAN 100 + nezávislá predstena | Približne 205–233 mm vrátane uvažovaných omietok, podľa systému a odstupu | Výsledky iných referenčných murív | Tenký kandidát, vyžaduje individuálne potvrdenie |
| Leiertherm AKU Mátraderecske, 250 mm | **274 mm** | **Rw 56 dB pre určené vyhotovenie** | **Záložná možnosť; hrúbka odmietnutá** |
| Leiertherm AKU Mátraderecske, 300 mm | 324 mm s predpísanými omietkami | Výrobcom uvádzaných 59 dB | Väčšia priestorová a hmotnostná záťaž |
| Celosadrokartónová systémová priečka | Podľa konkrétneho systému | Vyžadovala by výber príslušnej skúšanej skladby | Vylúčená požiadavkou zachovať tehlu |

Hrúbky dvojplášťových možností sú porovnávacie súčty, nie definitívny realizačný detail. Ich povrchy v dutine, väzby a napojenia nie sú overené. Samotná LeierPLAN 10 má Rw 35 dB **s 15 mm vápennocementovou omietkou na každej strane**; ide o údaj jednotlivého omietnutého plášťa.[^4]

Pri zachovaní záložného posunu pracovňových dverí o 100 mm by celkových 330 mm ponechalo pri ich hornom okraji len 20 mm. Na obnovenie rovnakého 76 mm úseku ako pri posudzovanej 274 mm zálohe by sa vstup musel posunúť o ďalších 56 mm. Stena 300 mm teda nie je principiálne nemožná, ale vyžaduje väčšiu dispozičnú zmenu a nevyrieši chýbajúci dôkaz pre kombináciu dvoch LeierPLAN plášťov.

## 6. Prečo sa nedajú sčítať decibely tehly a predsteny

Vlna sa v sadrokartónovej predstene ukladá medzi profily. Jej hrúbka sa nepripočítava druhýkrát k hĺbke toho istého roštu. Dve dosky po 12,5 mm predstavujú 25 mm opláštenia; „50 mm vaty a 50 mm sadrokartónu“ preto treba previesť na presný systémový rez.

Rigips napríklad uvádza Habito H na R-CW 50 s predstenou 77,5 mm a zlepšenie až 19 dB na referenčnej PTH 11,5 AKU profi. Súčet s obojstranne omietnutým 100 mm jadrom vychádza geometricky 207,5 mm, ale výsledok skúšky inej tehly tým nevznikne. Pri výške modelu 3 125 mm tiež nemožno automaticky použiť rozstup profilov z variantu limitovaného na 3 000 mm.[^5]

Podobne Knauf publikuje pri W626 zlepšenie ΔRw 23 dB pre dvojité opláštenie Diamant a 25 dB pre Silentboard; základom je však **pórobetón 175 mm s Rw 38 dB**. Výrobca vysvetľuje závislosť výsledku od pôvodnej steny.[^6] Výpočet „35 + 23 = 58 dB“ pre LeierPLAN 10 by bol nepodloženou deklaráciou. Následne zvolené H200 používa iný podklad: individuálny predbežný výpočet z Rw základnej Leier steny, hmotností plášťov a dutiny. Aktuálnych približne 55,77 dB pri jednej doske nevzniká pripočítaním uvedeného katalógového zlepšenia.

## 7. Akustika celej miestnosti

**Rw** charakterizuje nepriezvučnosť posudzovanej konštrukcie. **R'w** opisuje výsledok zabudovania so zvukom prenášaným aj bočnými cestami. Záleží na nadväzujúcich stenách, podlahe, strope, prestupoch a netesnostiach. Nie je správne zvoliť univerzálne odpočítanie napríklad 5 dB a vyhlásiť tým výsledok hotového domu.[^7]

Pre pracovňu existuje aj cesta sprcha → kúpeľňové dvere → chodba → pracovňové dvere. Obchádza plnú stenu AK-03. Jej účinok nemožno určiť sčítaním údajov dvoch dverí. Ak je cieľom vysoké súkromie celej miestnosti, treba koordinovať kompletné dvere, obvodové tesnenia, spodný uzáver a vetranie. Výrobcovia ponúkajú akustické dverové zostavy; vybrať sa má konkrétne vyhotovenie so zodpovedajúcou zárubňou.[^8]

Tesnenie zároveň nesmie znemožniť navrhnutý prívod vzduchu do kúpeľne. Voľná podrezaná medzera alebo bežná mriežka nie sú automaticky rovnocenné akusticky uzavretému vstupu. Podhľadová dutina, súvislá plávajúca podlaha alebo netesný prestup môžu znehodnotiť aj kvalitnú stenu. Ich detaily sa posudzujú spolu s konštrukciou, nie až po jej dokončení.[^9]

## 8. Realizačný princíp pri sprche

Pre deklarovaných Rw 56 dB sa musia dodržať **12 mm ložné aj styčné maltové škáry, obojstranná 12 mm vápenno-cementová omietka a objemová hmotnosť malty aj omietky najmenej 1 800 kg/m³** podľa technického listu konkrétneho výrobku.[^1] Vybrané murivo sa zhotovuje na túto maltu, nie na penu LeierFIX. Spoje musia vytvoriť súvislý podklad pre omietky. Slovenská príručka osobitne rieši napojenie AKU muriva na LeierPLAN: výškový modul tvorí 238 mm tehla a 12 mm ložná škára; pripojovacie pásy sa koordinujú so škárami nadväzujúceho muriva.[^3]

V modeli zálohy bolo 274 mm ukončených omietkou. Na sprchovej strane by sa následne určila hydroizolácia, lepidlo a obklad. Tieto vrstvy potrebujú vlastnú rezervu. Obklad sa bez potvrdenia nenahradí za predpísanú akustickú omietku. Pri doskovom plášti na mokrej strane by sa navyše overili dosky vhodné do vlhkého prostredia: priame ostrekovanie vyžaduje ochranu hydroizoláciou, samotná keramika nestačí.[^10] Zvolené H200 má doskovú predstenu na suchej strane pracovne.

Batéria, odtok, potrubie, radiátor aj práčka môžu prenášať mechanické vibrácie. Preto sa rozvody a objímky navrhujú s vhodným oddelením od stavby a s utesnenými prestupmi. Geberit napríklad požaduje súvislé oddelenie potrubia vrátane upevnení; prerušená izolácia alebo zatuhnutý kontakt môže ochranu poškodiť.[^11] Výška Rw plnej steny sama nepreukazuje tichosť sanitárnej inštalácie.[^12]

## 9. Dôkazy, výrobné varianty a rozpory

Hlavným podkladom je konkrétny HU technický list s uvedením meranej hodnoty a jeho aktuálne DoP. Pôvodný úplný skúšobný protokol HU sa verejne nepodarilo nájsť; doloženie preto označujeme ako **údaj výrobcu**, nie ako nezávislé meranie nášho návrhu.

Slovenská produktová stránka uvádza 56 dB, ale zároveň odkazuje na poľské dokumenty.[^13] Poľský výrobok Thermopor 25/30 AKU 238 z Markowicze má v DoP 55 dB pri 250 mm; túto hodnotu potvrdzuje poľská tabuľka z roku 2025 s odkazom na skúšku Applied Precision A10-1/11.[^14][^15] Ide o rozlíšiteľnú alternatívu, nie o oprávnenie zamieňať závody.

Všeobecný slovenský katalóg 08/2025 má pri riadku 25/30 AKU 238 vytlačených **49 dB**. Overili sme to aj vizuálne. Riadok opakuje tepelné hodnoty predchádzajúcej obyčajnej tehly, čo vzbudzuje podozrenie na chybu tabuľky; výrobcom potvrdená oprava však chýba.[^16] Preto sa špecifikácia viaže na presný produkt Mátraderecske a jeho dokumenty. Pri nákupe nestačí objednať „akustickú Leier 25“.

## 10. Hmotnosť a otvorené realizačné položky

Modelová plocha plnej steny je **4,758 × 3,125 = 14,86875 m²**. Pri 352 kg/m² zodpovedá vlastná hmotnosť približne **5,23 t**, teda približne **51,3 kN**, bez dodatočného obkladu. Na bežný meter vychádza približne 1,10 t. Je to aritmetický podklad pre statické zaťaženie, nie schválenie založenia alebo únosnosti.

Pred realizačným uzavretím treba dopracovať:

1. Dodávku presného výrobku a zodpovedajúceho aktuálneho DoP, maltu a omietku s požadovanými vlastnosťami.
2. Únosnosť podkladu, stabilitu pri výške 3 125 mm a horné i bočné napojenie. Pôvodná stena bola vedená ako nosná; označenie novej deliacej steny v modeli tento problém nevyrieši.
3. Výrobný výkres oboch zárubní, ich vonkajšie rozmery a využiteľnosť uvedených úsekov muriva. Zachovať spoločnú os pri prepočte na skutočný dodávateľský otvor.
4. Hrúbku mokrých povrchov, kotvenie sprchy a radiátora, trasy rozvodov, prestupy, vetranie a požadované vlastnosti dverí.

Geometria tejto záložnej štúdie poskytuje konkrétne, vzájomne koordinované porovnanie. Jej súradnice a plochy vychádzali zo spoločných dát pôdorysu a 3D modelu v čase návrhu 274 mm; aktuálny hlavný model používa H200. Akustický výpočet celej budovy, statické posúdenie a montážne potvrdenie zárubní sú odlišné druhy overenia.

## Pramene a pôvod údajov

Všetky externé pramene nižšie sú dokumenty alebo stránky výrobcov, overené 13. 9. 2026. Súradnice, plochy a dispozičné porovnania sú zachované vlastné výpočty nad vtedajšími `lib/floor-plan-concept.ts`, `lib/twin-interior.ts`, `lib/acoustic-walls.ts` a `lib/twin-active-house.ts` pri návrhu 274 mm. Výpočty hmotnosti používajú uvedenú modelovú plochu, plošnú hmotnosť a gravitačné zrýchlenie 9,80665 m/s². Historický stav pre porovnanie plôch je stav projektu pred úpravou na 274 mm; tieto plochy neprepisujú aktuálne hodnoty H200.

[^1]: Leier HU: [Leiertherm 25/30 AKU, technický list Mátraderecske](https://www.leier.hu/uploads/files/Leiertherm_25_30_AKU_adatlap.pdf), 1 strana. Presná skladba, povrchy, hustoty a akustika.
[^2]: Leier HU: [DoP LE MD771-1-11-05](https://www.leier.hu/uploads/files/LE_MD771-1-11-05-6a0321081319c.pdf), 12. 5. 2026. Identifikácia výrobku a deklarované vlastnosti.
[^3]: Leier SK: [Montážna príručka 08/2025](https://www.leier.sk/wp-content/uploads/2025/08/leier-montazna-prirucka-0825.pdf), tlačené strany 86–87 a 123. Oba výrobné varianty a napojenie AKU/PLAN.
[^4]: Leier SK: [Technický list LeierPLAN 10 N+F](https://www.leier.sk/wp-content/uploads/2025/07/Technicky-list-LP10-NF.pdf). Samostatná priečkovka a podmienky jej akustického údaja.
[^5]: Rigips: [Předsazené a šachtové stěny, 2/2025](https://api.profikalkulator.rigips.cz/file-access/f/88/e2/88e2aba49963e1dc7335520f9f52da86-7657.pdf?1738741318=), strany 21 a 23. Systémy, referenčné steny a výšky.
[^6]: Knauf: [Zvuková izolace – předsazené stěny](https://local.knauf.cz/file/4487-predsazene-steny.pdf), strany 10–11. Referenčný pórobetón a ΔRw.
[^7]: Rigips: [Výpočet stavební neprůzvučnosti](https://www.rigips.cz/akusticka-aplikace/nepruzvucnost/). Vplyv zabudovania a bočných ciest.
[^8]: SAPELI: [Protihlukové dveře](https://www.sapeli.cz/protihlukove-dvere). Dvere ako kompletná akustická zostava.
[^9]: Rigips: [Detaily předsazených stěn](https://www.rigips.cz/clanky/detaily-predsazenych-sten/). Napojenia a obmedzenie bočného prenosu.
[^10]: Rigips: [Desky vhodné do vlhkého a mokrého prostředí](https://www.rigips.cz/pro-odborniky/desky-vhodne-do-vlhkeho-a-mokreho-prostredi/). Vlhkosť a ochrana ostrekovaných povrchov.
[^11]: Geberit: [Mapress Therm, technické informácie](https://www.geberit.cz/_assets/local-media/geberit-mapress-therm-technicke-informace.pdf), 04/2026, strana 23. Oddelenie potrubia a upevnení.
[^12]: Geberit SK: [Akustická izolácia sanitárnych inštalácií](https://www.geberit.sk/know-how/kompetencie/akusticka-izolacia/).
[^13]: Leier SK: [Leiertherm 25/30 AKU 238, produktová stránka](https://www.leier.sk/produkty/tehly-a-preklady/tehla/leiertherm-25-30-aku-238/).
[^14]: Leier Polska: [Thermopor 25/30 AKU 238, DoP v slovenčine](https://www.leier.sk/wp-content/uploads/2022/04/lt-25_30-aku238-pl.pdf), 1. 4. 2022, Markowicze.
[^15]: Leier Polska: [Tabuľka požiarnych a akustických vlastností](https://www.leier.pl/wp-content/uploads/2025/06/wlasciwosci-ogniowe-i-dzwiekoizolacyjne-przegrob-z-elementow-murowych-THERMOPOR_od_maj_2025.pdf), 05/2025.
[^16]: Leier SK: [Katalóg tehál a prekladov 08/2025](https://www.leier.sk/wp-content/uploads/2025/08/leier-tehla-preklady-katalog-0825.pdf), PDF strana 7. Zaznamenaný rozporný riadok 49 dB.
