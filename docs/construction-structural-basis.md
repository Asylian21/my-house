# C/B/B — podklad pre nový návrh nosnej sústavy



Doplnenie **16. 9. 2026**: [označený vnútorný úsek medzi garážou a spálňou/šatníkom](construction-garage-partition.md) je murovaná nenosná priečka **SP14, 140 mm**, X 11 003–11 143 mm, Y 5 744–8 749 mm. Nepridáva sa ako podpera dreveného stropu ani krovu. Vonkajšie pokračovanie pri lodžii `C-GARAGE-SPINE-N` zostáva 301 mm a trasa R6 sa neposúva.
**14. 9. 2026 · NOT_FOR_CONSTRUCTION · technický audit a kandidátna schéma, nie realizačná statika.** Pôdorys, osi, otvory a akustické skladby zostávajú podľa aktuálneho C/B/B. Pôvodná statika je archívny orientačný podklad; jej výstuž, základové šírky ani oceľové profily sa týmto nepreberajú. Rozmery označené ako modelové dokladajú geometriu, nie únosnosť.

## Zadané a zatiaľ neoverené

Stavebník opisuje existujúci spodný betónový pás ako **600 mm v zemi**, so zatiaľ neznámou šírkou. Nad ním požaduje monolitický soklový pás **350 × 600 mm**, vnútorné rebrá v horných 600 mm, zhutnenú zeminu a dosku **150–200 mm**, údajne všetko z betónu „16/20“. Ide o vstupy zadania, nie zameranie ani schválené prierezy. Stratené debnenie sa nepoužije. Voda a kanalizácia majú viesť nad nosnou doskou bez dodatočného vŕtania dosky.

Strecha má byť z falcovaného plechu bez architektonických presahov. **Potvrdené doplnenie stavebníka: povala slúži iba na odkladanie vecí, bez bývania; nosné stropy budú drevené, bez betónovej stropnej dosky aj bez betónovej nadbetonávky.** Pochôdzna podlaha povaly bude nad všetkými miestnosťami s plochým stropom vrátane garáže a technickej miestnosti; nad katedrálou obývačky 1.03 nebude. Otvorené zostáva množstvo a rozmiestnenie skladovaných vecí, prístup a návrhové zaťaženie, nie samotný účel povaly. Betónové základy, prízemná doska na teréne a nový staticky navrhnutý ŽB veniec týmto doplnením nie sú vylúčené.

Referenčná hodnota ulice R0 = 184,200 m je údaj stavebníka; presný bod a výškový systém nie sú doložené. Rozdiel ΔFFL medzi hotovou podlahou a R0 chýba. Stavebník požaduje **aspoň jeden schod do domu**, výšku hotovej podlahy však neurčil. Modelové ±0,000 sa preto nesmie zameniť s ulicou. Zadaný limit uličnej rímsy +4,500 m nad R0 možno skontrolovať až po určení ΔFFL a konštrukčného detailu. Číselný referenčný podklad: [client-brief.ts](../scripts/construction-documentation/client-brief.ts); potvrdenie dreveného stropu, skladovacej povaly a schodu vychádza z následného priameho zadania stavebníka zo 14. 9. 2026.

## Základy, betón a doska

**C16/20 nemožno automaticky zamietnuť ani schváliť pre celú stavbu.** Označuje charakteristickú pevnostnú triedu, nie kompletnú špecifikáciu betónu. Oficiálny český sprievodca k ČSN EN 206+A2 / ČSN P 73 2404, vydanie 2022, uvádza pre XC2 minimum C16/20, pre XC4 a XF1 minimum C25/30. Ide o príklady viazané na prostredie a ďalšie požiadavky, nie schválenie konkrétneho základu. Chránený spodný pás a sokel vystavený striedavému zavlhčeniu či mrazu preto vyžadujú samostatné určenie expozície vrátane prípadnej agresivity zeminy/vody. Dodací list musí potvrdiť skutočne dodaný betón. [SVB ČR: Průvodce betonářskou normou, strany 1–2](https://www.transportbeton.cz/uploads/sources/publikace/b4f7788fc9d77f683e02bc6f2e4637f1_pruvodce-betonarskou-normou-csn-en-206-a2-pdf.pdf).

Návrh založenia potrebuje geotechnický model, návrhové vlastnosti zemín a kontrolu únosnosti **aj sadania**. Zo samotnej hĺbky „600 mm“ nevyplýva založenie pod miestnym účinkom mrazu ani únosná základová škára. Pre C/B/B tu nie je doložený použiteľný geotechnický návrh; historické informácie o vode ho nenahrádzajú. [JRC: Eurocode 7 — Geotechnical Design, kapitoly 3 a 5](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/2013_06_WS_GEO.pdf).

Pred návrhom horného soklového pásu treba zamerať polohu, šírku, hornú a spodnú úroveň existujúceho pásu a preveriť jeho materiál, výstuž a kontakt so zeminou. **Na detailnej fotografii je viditeľná trhlina; fotografia neurčuje jej hĺbku, príčinu ani závažnosť.** Miestna prehliadka má zaznamenať jej polohu, šírku a vývoj a určiť prípadné sondy. Pred zakrytím sa musí uzavrieť posúdenie existujúcej konštrukcie.

Nový horný pás vznikne v inej betonáži. Prenos síl cez pracovnú škáru, nadväznosť výstuže a realizovateľnosť spojenia treba navrhnúť; samotné označenie „monolit“ spojenie nepreukazuje. Šírku 350 mm treba umiestniť voči nosnému jadru muriva a skutočnému spodnému pásu. Nesmie sa automaticky centrovať pod približne 500 mm širokú obálku muriva so zateplením.

**Vnútorné rebro vysoké 600 mm uložené iba v zásype nie je automaticky vnútorným základom.** Pracovné možnosti sú: nosník prenášajúci zaťaženie do overených spodných podpor, alebo prvok založený na podklade, ktorého únosnosť a sadanie sú overené. Reakcie zo strechy, povaly a nosných stien aj vlastná hmotnosť nenosných priečok musia mať súvislú cestu až do základovej pôdy; rozmery a výstuž rebier zatiaľ nie sú určené.

Pri doske sa musí najprv zvoliť **podlaha celoplošne podopretá overeným zásypom**, alebo **nosná doska prenášajúca zaťaženie medzi rebrami**. Rozsah 150–200 mm tento rozdiel nerieši. Návrh zahrnie aj lokálne zaťaženie priečkami, technológiou a vozidlom v garáži, príslušné škáry a hydroizolačnú/radónovú kontinuitu.

„Zhutnená hlina“ nie je preberacia špecifikácia. Treba určiť vhodnosť materiálu, vlhkosť, hrúbku zhutňovaných vrstiev, technológiu a merateľné kritériá prevzatia podložia i zásypu. Čistý kontrolovaný inertný zásyp je príkladom bežného riešenia podlahy na teréne; oficiálne anglické usmernenie požaduje takéto zloženie a zhutnenie. Jeho lokálne rozmerové pravidlá sa na tento český projekt **nepreberajú**. [Approved Document C, bod 4.7](https://assets.publishing.service.gov.uk/government/uploads/system/uploads/attachment_data/file/431943/BR_PDF_AD_C_2013.pdf).

Kanalizácia nad prízemnou doskou vyžaduje koordináciu spádov, križovaní a vývodu cez obvod; hotový návrh musí tieto miesta vyriešiť pred betonážou bez spoliehania sa na neskoršie vŕtanie.

## Výškový reťazec od existujúceho betónu po vstup

Nasleduje geometrický vzťah v mm, **nie zvolené výškové osadenie**. `h0` je zameraná výška horného líca už vybetónovaného spodného pásu nad R0; zatiaľ ju nepoznáme. Údaj „600 mm v zemi“ ju neurčuje.

| Úroveň / veličina | Vzťah voči R0 | Stav |
| --- | --- | --- |
| Horné líce existujúceho spodného pásu | `h0` | Zamerať, nezamieňať s terénom ani s R0. |
| Horné líce nového soklového pásu | `h0 + 600` | Zadaných 600 mm nad existujúcim horným lícom; šírka pásu 350 mm je iná veličina. |
| Hrúbka prízemnej dosky | `t = 150 až 200` | Rozsah požiadavky; návrh vyberie jednu hrúbku. |
| Horné líce prízemnej dosky | `h0 + 600 + j` | `j` je výškový rozdiel horného líca dosky oproti hornému lícu nového pásu, určený detailom styku. |
| Hotová podlaha prízemia | `ΔFFL = h0 + 600 + j + p` | `p` je úplná skladba nad doskou vrátane inštalácií, izolácií, vykurovacej vrstvy a povrchu. |

Ak doska leží celou hrúbkou **nad** horným lícom nového pásu, potom `j = t` a reťazec je `h0 + 600 + (150 až 200) + p`. Ak sú horné líca dosky a pásu zarovnané, `j = 0`: hrúbka dosky smeruje nadol a druhýkrát sa k výške nepripočíta. Ide o dve vysvetlenia geometrie styku, nie výber statického riešenia. Ani `j`, ani `p` sa zatiaľ nepredpisujú.

Jeden vstupný schod prekonáva rozdiel medzi **miestnou vonkajšou podestou/chodníkom a vstupom**. R0 je iný bod pri rohu pracovne na ulici. Výška prístupovej plochy, jej spád, počet a výšky stupňov aj prah sa musia zosúladiť s ΔFFL. Preto „aspoň jeden schod“ neznamená **FFL = R0 + 150 mm** a 150 mm tu nie je zvolená výška stupňa. Najprv treba výškové zameranie existujúceho pásu a vstupu, potom skontrolovať vyššie uvedený reťazec, odvodnenie, kanalizáciu a limit rímsy. Pri zachovaní modelového okraja strechy M+3,125 platí kontrolný vzťah `výška okraja nad R0 = ΔFFL + 3125 mm`; konečný detail určí vzťah tejto roviny k požadovanej rímse.

Takéto výškové schéma a explicitné vstupné podmienky majú byť súčasťou statického podkladu; konečný výpočet musí uviesť použité modely, zaťaženia a ich polohy. [ČKAIT: TS 05 — Statický výpočet, body 5.2–5.6](https://profesis.ckait.cz/dokumenty-ckait/ts-05/).

## Kandidátna ekonomická schéma strechy a stropu

Odporúčaný smer návrhu je **drevená sústava rozdelená podľa geometrie domu**: opakované pôdne väzníky s dolným pásom navrhnutým na skladovaciu podlahu v pravidelnej západnej časti, samostatný drevený trámový strop s osobitným prenosom strešných reakcií v komplikovanom uzle L a samostatná katedrálová sústava nad 1.03. Integrovaný ľahký drevený strop je výrobcom doložený princíp pôdnych väzníkov. Konkrétnu hospodárnosť musí potvrdiť spoločný výpočet a porovnateľná ponuka vrátane montáže, spojov, podlahy, požiarnej a akustickej skladby. [MiTek: Střešní konstrukce](https://www.mitek.cz/konstrukce/stresni-konstrukce/).

**Nosnú časť stropu tvoria drevené prúty/nosníky a staticky navrhnutý drevený záklop alebo dosky na báze dreva.** Podlahová nášľapná vrstva, prípadná suchá roznášacia/akustická vrstva a podhľad sa evidujú osobitne; bez posúdenia sa nezapočítavajú do nosnosti trámov. Ich vlastná hmotnosť však vstupuje do zaťaženia. Žiadna betónová doska ani spriahnutá betónová nadbetonávka sa do stropu nenavrhuje. Spoje, kotvy a podopretie na navrhnutom ŽB venci treba dopracovať. Výrobné podklady drevených I-nosníkov uvádzajú osobitné detaily uloženia, otvorov a prenosu bodových síl; katalógový detail ani orientačná tabuľka samy neurčujú prierez tohto domu. [STEICO: Technická príručka — Nosníky, konštrukčné detaily stropu](https://www.steico.com/fileadmin/user_upload/Czeskie_Media/Products/Materialy_na_bazi_dreva/STEICO_Technicka_prirucka_Nosniky_cz.pdf).

V západnom úseku hlavnej časti **X 6440–21040, Y 3000–11200** možno preveriť opakované priečne väzníky medzi južnou a severnou obvodovou podporou. **8200 mm je vonkajší rozmer modelu, nie návrhové rozpätie medzi uloženiami.** Severná podpora je lokálne otvorená lodžiou a presklením, južná veľkou garážovou bránou: tieto úseky potrebujú samostatne vyriešené preklady alebo prenosové nosníky a podperné reakcie.

V styku krídel **X 21040–28040** nie je na Y 11200 súvislá severná obvodová stena. Rovnaký väzník sa sem nemôže bez preverenia opakovať. Ako prvý variant tu odporúčam preveriť **samostatné drevené stropné polia**, ukladané na obvod a overené nosné úseky K-07 až K-09, s vlastnými prenosovými nosníkmi pri okraji katedrály. Nie každý úsek musí byť využitý; nosná funkcia, smer nosníkov a reakcie sa určia vo výpočte. Porovnať sa môže osobitná sústava pôdnych/prenosových väzníkov, ak poskytne rovnaký skladovací priestor s jednoduchšími spojmi a nižšou celkovou cenou. Strešné podpery sa nesmú voľne položiť na strop bez zahrnutia ich reakcií. Nové stĺpy do chodby ani ukladanie strešných alebo stropných reakcií na akustické priečky sa nenavrhujú; ich vlastná hmotnosť sa posudzuje samostatne.

Nad 1.03 možno porovnať priečne katedrálové rámy a väzníky so zvýšeným dolným pásom, ktoré sa zmestia medzi zachovaný strop a strechu. Model má vonkajšiu šírku krídla 7000 mm, okraj strechy +3125, hrebeň +5560, okraj katedrály +2750 a vrchol +4850 mm voči modelovej podlahe. **Priestor medzi plášťami nie je dostupnou výškou statického prierezu bez odpočítania všetkých skladieb.** Treba vyriešiť vodorovné účinky, stuženie, nadvihnutie vetrom, úžľabie a komín; historické HEA160 ani iné profily nie sú návrhom novej sústavy.

**Zaťaženie odkladacej povaly:** pri potvrdenom skladovaní treba preveriť skladovací prípad **E1**, ktorý EN 1991-1-1 spája s hromadením vecí vrátane prístupových plôch. Kategória H je iba pre údržbu strechy. Kategória A opisuje domáce/obytné používanie; samotná poloha povaly v rodinnom dome nezdôvodňuje automatických 2 kN/m². Citovaný výklad normy rozlišuje `qk` pre celkové účinky a `Qk` pre miestne účinky; pri skladovaní pripúšťa určenie hodnôt podľa konkrétneho použitia a národnej prílohy. **Konečnú kategóriu, hodnoty a kombinácie musí statik výslovne stanoviť podľa použiteľného znenia ČSN a českej národnej prílohy.** Táto správa nevydáva ani obytné zaťaženie, ani všeobecnú tabuľkovú hodnotu skladu za únosnosť povaly. [JRC: EN 1991-1-1 — snímky 19–20, 23, 28 a 32–33](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1991_2_Malakatas.pdf).

Pre konkrétny výpočet treba spísať uvažované veci, maximálne stohovanie, regály a plochy ich nôh, najťažší jednotlivý predmet a prístupové trasy. Nohy regála môžu zaťažovať záklop medzi nosníkmi; ich účinok sa nesmie skryť spriemerovaním hmotnosti na celú povalu. Posúdiť treba záklop, trámy, spoje aj podpory, priehyb, dlhodobé deformácie pri skladovaní a použiteľnosť pri chôdzi. Výsledný návrh má vydať čitateľné dovolené zaťaženia a zóny používania; táto správa ich zatiaľ neurčuje.

Prístupový otvor a priechodné zóny treba koordinovať s diagonálami väzníkov; bežný priehradový väzník s doskami položenými na dolnom páse automaticky nezabezpečí voľnú skladovaciu povalu. Pochôdzna podlaha všade neznamená možnosť stáť vzpriamene pod celou šikminou. Do zaťaženia patria kompletné strešné vrstvy a podklad falcovaného plechu, sneh, vietor a potvrdená technológia/PV. Skladovacie zaťaženie povaly sa pri kombinovaní nesmie zameniť so zaťažením údržby samotného strešného plášťa. Samostatný drevený strop s krovom a pôdne väzníky sa porovnávajú pri rovnakom skladovaní, prístupe a požadovanom rozsahu podlahy; žiadna možnosť tu neobsahuje betónový strop.

## Kandidátne podporové zóny z aktuálneho modelu

Všetko v mm v pôvodnom lokálnom rámci domu. Označenia **K-01 až K-09 sú iba koordinačné identifikátory tejto správy**; nenahrádzajú osi A–F / 1–6 ani materiálové a otvorové kódy. Uvedené obálky sú polohy existujúcich prvkov, nie schválené plochy uloženia či rozmery nových základov.

| Zóna | Presná modelová poloha | Podmienka prenosu zaťaženia |
| --- | --- | --- |
| K-01 · južný obvod S | X 6440–28040; vonkajšie líce Y 3000, vnútorné Y 3504 | Uloženie do jadra; D1 X 6940–10240 a ostatné otvory vyžadujú overený prenos nadpražím. |
| K-02 · severný obvod N | X 6440–21040; vnútorné líce Y 10699, vonkajšie Y 11200 | Otvorená lodžia X 7840–10640 a D5 X 11990–14190 (šírka 2200 mm) prerušujú podporu. |
| K-03 · západný obvod krídla WW | Y 11200–22035; vonkajšie líce X 21040, vnútorné X 21543 | D4 Y 11550–13800, ďalej otvorená strana terasy; nejde o súvislú podpernú čiaru. |
| K-04 · východný obvod E | Y 3000–22035; vnútorné líce X 27541, vonkajšie X 28040 | Reakcie koordinovať s bočnými otvormi a s odlišnou obálkou terasovej podpory K-06. |
| K-05 · ustúpená stena NN2 | Y 19035–19535; západný pilier X 21540–22040, plná stena X 24040–27540 | Medzi nimi O8 šírky 2000; rám okna nenesie strechu. Modelovaný horný pás X 21540–27540, Z 2750–3050 je obálka 6000 × 500 × 300, nie potvrdený ŽB nosník. |
| K-06 · terasový portál | Západ X 21040–21540 / Y 21535–22035; východ X 27540–28040 / Y 19535–22035 | Presné obálky existujúcich podpier; overiť stabilitu, materiál, reakcie a založenie oboch. |
| K-07 · kuchynské nosné úseky | Y 10712–11012; X 22639–26081 a X 26881–27541 | `C-KITCHEN-BEARING-WALL`, `…-E`; zachovať D11 X 26081–26881. Možná podpora uzla L iba po posúdení steny a základu. |
| K-08 · dvojica nosných stien pri izbách | X 20541–20842; Y 3504–6412 a Y 7791–10699 | `C-KID-ENTRY-WALL`, `C-GARDEN-KID-EAST`; oddelené úseky, nespojiť imaginárnou stenou cez chodbu. |
| K-09 · existujúce úseky pri vstupe/pracovni | X 23367–23542 / Y 3504–5195 a X 22842–23542 / Y 5195–5370 | `C-ENTRY-OFFICE-EAST`, `…-RETURN`; model ich označuje nosné, hrúbka je iba 175 mm. Použitie vyžaduje nový výpočet. |

**Vylúčené ako podpory strechy a dreveného stropu:** SM30 AK-01/AK-02, `C-OPEN-HALL-N/S`, X 14943–15243; H200 AK-03, `IW-STUDY-NORTH`, Y 6402–6602. Ich modelové roly zostávajú nenosné `PARTITION`. Toto vylúčenie sa **netýka ich vlastnej hmotnosti ani potreby podopretia**. Pre SM30 sa preto dopĺňa kandidátna trasa R7 nižšie. Hmotnosť H200 a ostatných priečok takisto patrí do návrhu dosky a základov. Ani modelové garážové priečky sa nesmú bez nového rozhodnutia premenovať na nosné steny len podľa hrúbky.

Geometria bola overená živým exportom `drawingSource()` z [source.tsx](../scripts/construction-documentation/source.tsx); autoritatívne polohy sú v [plan-export.ts](../lib/plan-export.ts), [floor-plan-concept.ts](../lib/floor-plan-concept.ts), [twin-active-house.ts](../lib/twin-active-house.ts), [twin-interior.ts](../lib/twin-interior.ts) a [twin-roof.ts](../lib/twin-roof.ts). Nenosnú klasifikáciu akustických priečok dokladajú [active-design.md](active-design.md) a [acoustic-walls.ts](../lib/acoustic-walls.ts).

## SM30 — vlastná hmotnosť a kandidátne podopretie R7

Revízia 16. 9. 2026 nahrádza dvojplášťovú SA30 jedným 300 mm murivom z bežnej obvodovej tehly. Dôvod odhlučnenia zostáva. **R7 je kandidátny spojitý podporný pás na výpočet**, nie potvrdené existujúce rebro. Rola `PARTITION` zostáva; strecha a drevený strop vyžadujú samostatné posúdenie nosnej sústavy.

| Prvok | Modelová geometria v mm |
| --- | --- |
| AK-02 / `C-OPEN-HALL-S` | X14943–15243, Y3504–6552; dĺžka 3048 |
| AK-01 / `C-OPEN-HALL-N` | X14943–15243, Y7651–10699; dĺžka 3048 |
| Jedna murovaná vrstva na každý úsek | X14943–15243, hrúbka 300; os X15093 |
| Výška oboch modelových stien | Z0–3125 |
| Kandidátna os R7 | (15093;3354) → (15093;10849), dĺžka 7495 |
| Voľná chodba medzi stenami | Y6552–7651, šírka 1099 |

Priame zaťaženie sa vyznačuje iba v dvoch úsekoch dlhých 3048 mm; prípadné spojenie R7 cez chodbu je pod podlahou. Os jednej 300 mm murovanej vrstvy je zhodná s kandidátnou osou R7. Modelové Z0 nepredpisuje realizačnú pätu muriva voči podlahovým vrstvám a nosnej doske.

**Hmotnosť muriva a úplné návrhové zaťaženie sú neurčené do výberu konkrétnej 300 mm tehly a malty.** Údaje pôvodných dvoch 100 mm plášťov nie sú vstupom aktuálneho návrhu. Doplniť treba bežné omietky, kúpeľňové povrchy, kotvenie a vybavenie.

Prierez, výstuž a uloženie R7 sa neurčujú. Posúdenie musí vyriešiť prenos cez existujúcu dosku do overeného základu alebo podkladu; strednica nie je dôkazom únosnosti. [Aktuálny podklad axonometrie](construction-foundation-axon.md).

## Otvorené rozhodnutia pred realizačnou statikou

1. Navrhnúť ΔFFL podľa zameraného horného líca existujúceho pásu, styku novej dosky, skladby podlahy a miestnej vstupnej podesty; zahrnúť aspoň jeden schod bez predpokladu +150 mm nad R0. Potvrdiť výškový systém a referenčný bod. Uzavrieť posúdenie trhliny a použiteľnosti existujúceho betónu.
2. Doplniť geotechnický návrh, podmienky mrazu/vody a špecifikáciu zásypu s preberacími skúškami; rozhodnúť, či doska leží na zásype alebo staticky pôsobí medzi podporami. Zahrnúť vlastnú hmotnosť SM30 cez kandidátnu trasu R7 aj hmotnosť H200 a ostatných priečok; určiť skutočnú cestu ich zaťaženia do základov.
3. Účel povaly **iba na odkladanie vecí** a **drevené nosné stropy bez betónovej dosky/nadbetonávky** sú potvrdené. Doplniť množstvo a rozmiestnenie vecí, prístup a priechodné zóny; určiť skladovacie a bodové zaťaženia. Následne spočítať drevenú strechu/strop, reakcie, murivo, preklady, ŽB vence, betónové základy a pracovné škáry ako jednu sústavu.
4. Aktívna strešná rovina už končí na `wingEndYmm = 22035`, zhodne s čelom terasy Y 22035: architektonický presah je **0 mm**. Pôvodných 50 mm zostáva iba v `ARCHIVE_JOINED_ROOF_PARAMETERS`. Finálny odkvapový/štítový detail, lišty, odvodnenie a skladba zostávajú otvorené; samostatná modelová obálka čela portálu zatiaľ siaha po Y 22105 a nie je schváleným klampiarskym detailom. Dopracovaný detail musí zosúladiť tieto vrstvy s požiadavkou nulového architektonického presahu.

Do uzavretia týchto bodov sa nevydáva výstuž, rozstup rebier/väzníkov, veľkosť drevených či oceľových prierezov ani vyhlásenie, že existujúce základy sú vhodné na pokračovanie stavby.
