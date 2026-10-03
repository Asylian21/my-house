# Exteriér Unreal — vegetácia a okolité parcely

## 1. 10. 2026 — R16a: súvislý porast okolitých parciel

Samostatný uložený projekt R16a odstraňuje opakované pôdne prekryvy zo 65 nezastavaných parciel a zachováva sedem obrábaných parciel. Obnovuje **39 834 pôvodných trsov v 164 skupinách**; výška ďalších **219 807 trsov** sa riadi jedným priestorovým poľom a existujúcimi okrajmi ciest. Pôvodné polohy, natočenia a poradie trsov zostávajú zachované. Starých 259 skúšobných skupín je vyradených; celok má **1 980 skupín a 632 026 inštancií**, o 649 menej než R15a. Plnšie koruny R15a, pôvodná architektúra, kolízie, C/B/B a oba odstupy 3 000 mm zostávajú zachované.

Skutočný Unreal import **PID 1073 skončil s exit 0**; projekt bol uložený a znovu načítaný. Natívne overenie porovnalo všetkých **477 117 pôvodných a obnovených lúčnych transformácií**, s nulovou polohovou odchýlkou a odchýlkami mierky a orientácie v presnosti Float32. Zachovaných 11 pôdnych častí obsahuje 2 801 obrábaných trojuholníkov; pôvodné materiálové väzby 65 plôch sú overené. Následný Node kontrolér skončil s exit 1, pretože nesprávne porovnával novšie korunové ID R15a so staršími R14a. Pôvodný neúspešný host záznam sa zachováva; nejde o neúspešné uloženie scény v Unreale.

Všetkých **584 pinov pred importom** zostalo nezmenených pri ukončení pôvodného kontroléra. Nezávislá snímka 601 spotrebovaných zdrojov a skutočných dôkazov je v `exterior-20261001-r16a/source-freeze/consumed-native-r1/snapshot.json`. Následná oprava R2 mení jednu host väzbu na nový presný kontrolný modul; pôvodný modul a neúspešný záznam sú zachované. **592 aktuálnych pinov** zostalo nezmenených pri balení a Shipping QA. Import hlásil nedostatok miesta pre časť Zen cache; neskoršie byte-identické nezávislé APFS kópie 2 983 chránených pracovných súborov nemenili natívne assety ani historické výsledky.

**Štyri skutočné párované Editor PNG R15a/R16a a dva nové Shipping PNG boli obrazovo posúdené.** Opakované hnedé ovály a svetlé lemy zmizli; porast medzi parcelami je súvislejší. Jednotný jemný koberec, vyhladená zeleň v diaľke, hranica vykresľovania trávy a jednoduché susedné domy zostávajú viditeľné. Porovnanie rovnakých kamier je v `exterior-validation-20260930-r1/r16a-comparison.html`; jeho ovládanie a pôvodné obrázky boli overené v prehliadači. Editor-game Development poskytuje samostatný obrazový dôkaz, nie Shipping dôkaz. **R16a nie je prijatá ako fotorealistický celok; aktívny výber zostáva R5.**

Shipping balík má **37 súborov / 2 614 978 506 bajtov**, platný podpis a pôvodnú overenú Shipping kódovú sekciu. Prešlo **62 čerstvých Node testov a 12 Python kontrol**; 31 kontrol nezávislého natívneho auditu, 19 kontrol balíka vykonaných hlavným agentom a 43 kontrol nezávislého Shipping obrazového reťazca. Dva Shipping zábery majú Metal SM6, Cinematic, 1 920 × 1 080, 2 400 zahrievacích a 300 meraných snímok. Parcely majú fokus aplikácie/okna/viewportu 300/300/300; háj 0/0/300, preto jeho časovanie nemožno hodnotiť. Oba detektory GUI vstupu zostávajú neúspešné aj pri úspešných natívnych procesoch a skutočných PNG. Celkový výkon, noc, chôdza a živé UI nie sú prijaté. Záznam je v `exterior-r16a-rejected-review.json`; dodatok spotrebovaných zdrojov a obrazového QA v `exterior-20261001-r16a/source-freeze/post-host-and-qa-r2/snapshot.json`. Tento dodatok nekopíruje celý projekt ani balík. Nové pokusy R17/R18 nie sú súčasťou R16a.

## 1. 10. 2026 — R15a: plnšie koruny stromov

Samostatná Shipping R15a má **135 rastlinných modelov, 405 LOD, 42 materiálov a 74 textúr**. Deväť nových korunových modelov zachováva pôvodné vetvy aj pôvodné vrcholové atribúty a pridáva prepojené jemné výhonky s listami do vnútra a stredu korún. Listová hmota zostáva zachovaná aj vo vzdialenejších LOD. Menia sa modelové väzby 23 skupín hája; všetkých **78 stromových osadení**, ich polohy, natočenia, mierky a vzdialenosti vykresľovania sú presné voči R14a. Pôvodných 126 natívnych modelových záznamov, všetky materiálové grafy, textúry aj ďalších 2 052 skupín sú nezmenené. Celok má 2 075 skupín a 632 675 inštancií. Dom, kolízie, C/B/B a oba odstupy 3 000 mm sú zachované.

**Všetky tri pôvodné nové Metal PNG a tri čerstvé párované R14a PNG boli skutočne posúdené.** Blízke aj vzdialené koruny sú viditeľne plnšie, s menšími priesvitnými medzerami. Tmavé plocho čitateľné stredy, podobné siluety, opakovaný slamový lesný podklad, hladké okolité plochy a jednoduché susedné budovy však zostávajú. **R15a nie je prijatá ako fotorealistický celok; aktívny výber zostáva R5.** Zdrojové alfa projekcie troch reprezentatívnych modelov merajú približne 52,4–59,5 % prekrytie oproti 37,4–43,9 % pôvodných korún. Ide o obmedzené zdrojové projekcie, nie meranie natívneho celoplošného krytia alebo dynamickej stability LOD.

Import, uloženie, nové načítanie a Shipping balík prešli. **49 čerstvých Node testov** a šesť samostatných zdrojových adversariálnych prípadov prešlo. Log piatich nových Node testov je zachovaný; 44 regresných testov má pozorovaný návrat TAP a exit 0 bez samostatne uloženého stdout logu. Testové hashe sú zachytené po vykonaní. **366 vstupných pinov kontroléra** bolo pripnutých pred importom a opätovne overených po importe, balení a audite. Nezávislý audit skutočného importu má 36 úspešných kontrol, opravený audit zostavy a párovaných záberov R2 má 48. Prvý audit zostavy nesprávne vyžadoval rovnakú nameranú pre-exposure; jeho tri neúspešné kontroly a pôvodné hodnotenie sú zachované. R2 rozlišuje presné nastavenia od nameranej reakcie automatickej expozície.

Nové zábery sú v `exterior-validation-20260930-r1/qa/after-exterior-r15a-canopy-artifacts-1790881037878/`, čerstvá referencia v `qa/after-exterior-r14a-canopy-baseline-artifacts-1790879031034/`. Všetkých šesť prípadov má skutočný Shipping/Metal SM6, PNG 1 920 × 1 080, Cinematic, 2 400 zahrievacích a 300 meraných snímok, s aplikáciou, oknom aj viewport fokusom **300/300**. Pri rovnakých nastaveniach sa nameraná expozícia mení o −0,231 / −0,130 / −0,026 EV; nejde o porovnanie pri pevnej expozícii. Zdrojové FOV je rovnaké, runtime FOV sa nezaznamenáva. Všetkých šesť GUI entry detektorov zlyhalo samostatne; skutočné PID, konfigurácie a obrazové artefakty sú overené oddelene.

Čas snímky pre blízke koruny, podklad a vzdialené koruny stúpol z **28,07 / 22,68 / 27,68 ms na 32,79 / 24,59 / 31,79 ms**, približne o 16,8 / 8,4 / 14,8 %. Ide o jeden statický foreground prípad na kameru a verziu, nie opakovaný izolovaný benchmark alebo prijatie celkového výkonu. Jedna GPU vzorka pôvodného blízkeho záberu má extrémnu hodnotu 89 478,484 ms; pôvodné dáta sú zachované a priemer GPU sa nepoužíva ako dôkaz zrýchlenia. Blízky/stredný/vzdialený zdrojový trojuholníkový rozpočet korún stúpol približne 1,94 / 2,66 / 3,36-násobne; nejde o runtime výber GPU LOD. Noc, chôdza, záhrada, ulica a pohyb LOD nemajú nové prijatie.

Záverečný opravený verdikt je v `exterior-validation-20260930-r1/exterior-r15a-rejected-review-r2.json`. Nezávislá kópia spotrebovaných zdrojov a šiestich pôvodných obrazových sád je v `exterior-20261001-r15a/source-freeze/snapshot.json`: **644 súborov, 3,68 GB logických dát**, overené hashe a odlišné inode bez hardlinkov. Opravený audit a hodnotenie má samostatný `source-freeze/supplement-r2/snapshot.json`; pôvodná snímka sa nemenila. Toto je scoped snímka zdrojov a dôkazov, nie kópia celého projektu alebo balíka.

Nasledujúca samostatná **zdrojová** štúdia `exterior-meadow-continuous-20261001-r1-study/` odstraňuje opakované pôdne prekryvy na 65 nezastavaných parcelách, zachováva sedem obrábaných parciel, obnovuje 39 834 pôvodných koreňov trávy a mení iba výšku ďalších 219 807 trsov podľa jedného priestorového poľa. Návrh vyraďuje staré dva skúšobné vrstvy porastu; čistý počet by klesol o 649 inštancií. **Do R15a táto štúdia nie je zapojená; natívny výsledok a výkon zostávajú neoverené.**

## 1. 10. 2026 — R14a: nízky porast na okolitých parcelách

Samostatná Shipping R14a pridáva **33 483 nízkych trsov v 101 skupinách** do dvoch autorských skúšobných oblastí pri parcelách a pohľade na stromy. Šesť nových modelov má 18 LOD; celý import má **126 modelov, 378 LOD, 42 materiálov a 74 textúr**. Pôvodných 120 modelových záznamov, všetky materiálové grafy a textúrové záznamy zostávajú presné voči R13a. Všetkých 1 974 pôvodných skupín zachováva transformácie, počet, model, vzdialenosti aj detailné pravidlá. Tri automaticky vytvorené názvy kontextových aktorov sa posunuli o 101; osadenie sa nemení. Uložený celok má 2 075 skupín a 632 675 inštancií. Dom, kolízie, C/B/B a oba odstupy 3 000 mm zostávajú zachované.

**Oba nové a oba presne párované pôvodné R13a Metal PNG boli skutočne posúdené.** Na parcelách pribudla viditeľná vrstva drobných listov a tmavší kontakt so zemou. Veľké holé pôdne tvary, hladké lemy a jednotná vyššia tráva však zostávajú. Pri stromoch sa mení najmä popredie v dolných rohoch; koruny a väčšina vzdialeného povrchu sú nezmenené. **R14a nie je prijatá ako fotorealistický výsledok; aktívny výber ostáva R5.** Zdrojové alfa pokrytie približne 11–30 % je projekcia štyroch obmedzených okien, nie dôkaz celkového natívneho krytia. Nové osadenie bolo overené zo všetkých 18 dekódovaných modelov proti povrchom a úplným odstupovým maskám.

Import, uloženie, opätovné načítanie a balenie prešli. **44 čerstvých Node testov** prešlo; ďalších šesť nezmenených stdlib testov má overené pôvodné logy, helper aj vstupné hashe. Testové hashe sú zachytené po vykonaní. Všetkých **328 vstupných pinov kontroléra** bolo pripnutých pred importom a znovu overených po importe aj balení. Nezávislé audity skutočného importu a zostavy majú 29 a 34 úspešných kontrol; nejde o ďalšie unit testy. Prvý audit zostavy s nesprávnym očakávaním rovnakého celého podpísaného executable je zachovaný. Opravený R2 overuje zhodnú pôvodnú Shipping binárku, skutočný strojový kód, reuse doklady aj 37 súborov zostavy.

Nové zábery v `qa/after-exterior-r14a-infill-artifacts-1790876678131/` a baseline v `qa/after-exterior-r13a-infill-baseline-artifacts-1790875683494/` majú 1 920 × 1 080, Cinematic, 2 400 zahrievacích a 300 meraných snímok. Všetky štyri prípady majú aplikáciu, okno a viewport fokus **300/300**. Dva nové statické prípady samy nepotvrdzujú celkový výkon, pohyb LOD, noc ani živé UI. GUI entry detektory zlyhali samostatne; skutočné PID, konfigurácia, ukončenie a zábery sú overené oddelene. Všetkých 101 nových skupín má v Cinematic overené detailné osvetlenie, tiene a ray tracing; pôvodných 789 runtime riadkov je presných, spolu 890.

Presný verdikt je v `exterior-r14a-rejected-review.json`, audity v `meadow-infill-native-r14a-audit-r1.json` a `meadow-infill-package-qa-r14a-audit-r2.json`. Nezávislá scoped kópia zdrojov, testov, kontrolérov, dokladov a štyroch pôvodných obrazových artefaktov je v `exterior-20261001-r14a/source-freeze/snapshot.json`; nejde o kópiu celého projektu alebo balíka. Galéria umožňuje vybrať rovnakú R13a kameru cez „Porovnať s“, bez zmeny stavu prijatia.

Nová samostatná zdrojová diagnostika korún v `exterior-canopy-diagnostic-20261001-r1b/` meria listové prekrytie troch reprezentatívnych korún z pôvodných GLB a alfa máp: približne **37,5–43,9 % v LOD0 a 31,7–37,0 % v LOD1**. Ide o výpočet bez natívneho osvetlenia, mipov alebo TAA. Výpočet podľa kamery a lokálneho UE vzorca naznačuje LOD1 pre väčšinu stromov, ale runtime priamy výber GPU LOD nezaznamenáva. Ďalší návrh musí riešiť plnšie nepravidelné výhonky aj zachovanie listovej hmoty v diaľke; samotný posun LOD prahu vnútornú riedkosť neodstráni.

## 1. 10. 2026 — R13a: fotografický povrch trávnika

Samostatná Shipping R13a pridáva **20 fotografických masterov** k pôvodným 100: spolu **120 masterov, 360 LOD, 42 materiálov a 74 textúr**. Všetkých **102 011 osadení v 40 skupinách** zachováva pôvodné polohy, orientácie, mierky a pravidlá vykresľovania. Nové modely menia iba UV0 a zdrojové tangenty; pôvodné polohy vrcholov, normály, COLOR0, UV1, indexy a hranice modelov zostávajú presne zachované. Natívny importer ponecháva normály, tangenty prepočítava. Recept používa skutočné fotografické albedo, normálu, drsnosť a alfa mapu `grass_medium_02`, bez ďalších textúr. Pôvodných 41 uložených materiálových záznamov aj všetkých 74 textúrových záznamov sa zhoduje s R12c. Dom, záhony, okolie, kolízie, C/B/B a oba odstupy 3 000 mm zostávajú zachované.

**Všetky štyri pôvodné Metal PNG boli posúdené a nezávisle porovnané s rovnakými kamerami R11.** Záhrada a detail trávnika majú olivové až slamové odtiene a jemné pozdĺžne znaky. Široké ploché krížené listy a jednotný vláknitý koberec stále dominujú; zmena materiálu neodstránila obmedzenie geometrie. V troch statických pohľadoch sa neobjavili zjavné nové veľké holé alfa ostrovy, ale natívne celoplošné pokrytie nebolo merané. Ulica je prakticky nezmenená. Samostatný prínos normál, presvitania alebo mipov nie je z kombinovanej zmeny izolovaný. **R13a sa neprijíma ako fotorealistický výsledok; aktívny výber zostáva R5.**

Zdrojové overenie obsahuje **93 jedinečných úspešných testov: 48 materiálových, 31 Node a 14 importového helpera**. Dodatočná kontrola skutočného materiálového buildera cez zdrojový Unreal shim sa nepočíta ako ďalší unit test. Hashy testovacích súborov sú výslovne zachytené až po vykonaní; 304 skutočne spotrebovaných natívnych zdrojov bolo pripnutých pred importom a znovu overených po importe a balení. Zdrojová alfa kontrola štyroch pevných 1 m² vzoriek meria **75,154–78,456 %**, s nezmenenými kritériami dvoch okrajových vzoriek. UV hranica bola posunutá o jeden pôvodný pixel dovnútra; niektoré hraničné vrcholy majú alfu pod cutoff. Ide o obmedzené zdrojové vzorkovanie, nie dôkaz globálneho natívneho krytia.

Skutočný import, uloženie, nové načítanie, Shipping balík a štyri natívne zábery sú overené samostatne. Zábery v `qa/after-exterior-r13a-photo-artifacts-1790862600569/` majú 1 920 × 1 080, Cinematic, 2 400 zahrievacích a 300 meraných snímok. Záhrada má aplikáciu aj okno aktívne pri **0/300**, preto je jej časovanie neplatné. Detail, hrana trávnika a ulica majú **300/300**; tieto tri prípady samy nepotvrdzujú celkový výkon. Noc, chôdza ani živé UI nie sú v R13a prijaté.

Presný výsledok je v `exterior-validation-20260930-r1/exterior-r13a-rejected-review.json`, zdrojový súhrn v `source-validation-r13a-r1.json`, natívne audity v `photographic-lawn-import-r13a-audit-r1.json` a `photographic-lawn-package-qa-r13a-audit-r1.json`. Nezávislá kópia spotrebovaných zdrojov, testov, kontrolérov, štúdie UV a štyroch pôvodných obrazových artefaktov je v `exterior-20261001-r13a/source-freeze/snapshot.json`, s overenými hashmi a odlišnými inode bez hardlinkov. Tento záznam **nie je kópiou celého natívneho projektu alebo balíka**; tie zostávajú v samostatnom pôvodnom adresári R13a. Galéria obsahuje 74 pôvodných natívnych záberov. Ďalšia zmena musí riešiť najmä tvar a pestrosť rastlín.

## 1. 10. 2026 — R12c: plynulejšie povrchy susedných parciel

Samostatná Shipping R12c upravuje iba materiálové väzby **65 pôvodných lúčnych a neobrábaných plôch** a pridáva **7 000 drobných trsov v 158 skupinách** pri vonkajších okrajoch pôdnych plôch. Spoločný povrch používa autorské spojité pole podmienok pôdy, takže hranica katastrálnej parcely sama neurčuje zmenu farby. Pole je ilustračný materiálový podklad, nie meranie skutočného využitia pozemku. Pôvodné geometrie, 47 203 odstránených osadení, súkromná parcela, architektúra, C/B/B aj oba odstupy 3 000 mm zostávajú zachované. Natívna zostava má **100 masterov, 300 LOD, 41 materiálov a 74 textúr**; pôvodných 40 materiálových grafov a 73 textúr je nezmenených.

**Všetkých päť skutočných Metal PNG bolo posúdených aj nezávisle porovnaných s rovnakými staršími kamerami.** V pohľade na háj zmizol veľký obdĺžnikový farebný zlom v pravom popredí. Na parcelách sú ostatné zmeny jemné; široké holé pôdne tvary, hladké zelené lemy a jednotná ihličkovitá tráva zostávajú viditeľné. Nadhľad, ulica a záhrada sa výrazne nezmenili. Papierové steblá, opakované listy a kvety, čisté stavebné povrchy a ploché ortofoto stále bránia realizmu. **R12c nie je prijatá ako výsledok na nerozoznanie od reality; aktívny výber zostáva R5.**

Zdrojový súhrn `exterior-validation-20260930-r1/source-validation-r12c-r2.json` obsahuje **279 úspešných kontrol: 111 čerstvých a 168 prevzatých po potvrdení nezmenených závislostí**, s 1 387 pripnutými identitami a 7 329 kontrolami uzavretia dôkazov. Desať kontrol natívneho vstupného helpera má 31 zdrojových hashov zachytených a opätovne overených až po vykonaní; súhrn tento rozdiel výslovne uvádza. Skutočný import, uloženie, opätovné načítanie, Shipping balík a päť obrazových artefaktov majú samostatné audity. Nové osadenia majú po opätovnom načítaní nulovú polohovú odchýlku; uložené mierky a orientácie sú overené s presnosťou exportovaného Float32. Zdrojové a MeshDescription počty trojuholníkov 65 plôch sú 3 671, renderovací počet 3 613 je rovnaký ako v pôvodnej natívnej R11; tri už existujúce rozdiely počítadiel nemenia geometriu.

Päť denných statických záberov je v `qa/after-exterior-r12c-transition-artifacts-1790855241114/`: susedstvo, parcely, háj, ulica a záhrada, vždy 1 920 × 1 080, Cinematic, 2 400 zahrievacích a 300 meraných snímok. Len háj a záhrada majú aplikáciu aj okno aktívne pri 300/300; susedstvo, parcely a ulica majú 0/300 a ich časovanie sa neprijíma ani neporovnáva. Obrazové artefakty sú platné. Celkový výkon, noc, chôdza a živé UI neboli prijaté.

Záverečný záznam je v `exterior-validation-20260930-r1/exterior-r12c-rejected-review.json`. Celý projekt, balík, päť záberov, aktuálne vstupy a oddelené historické dôkazy sú zachované v `exterior-20261001-r12c/source-freeze/snapshot.json`: **18 016 nezávislých APFS kópií, 28,75 GB logických dát**, všetky s overenými hashmi a odlišnými inode, bez hardlinkov. Kópie oddeľujú 8 209 historických identít a 59 identít neúspešných natívnych pokusov od aktuálnych zdrojov. Oba neúspešné importy R12/R12b aj opravy nezávislého auditu zostali zachované; úspešný R12c sa z nich nepovažuje za prevzatý natívny dôkaz. Galéria `exterior-validation-20260930-r1/index.html` obsahuje všetkých 70 pôvodných záberov bez vynechania.

Samostatná štúdia `exterior-lawn-tapered-photo-uv-20261001-r1-study` skúša fotografické žilky a škvrny na štyroch pôvodných steblách bez zmeny 20 vrcholov, 12 trojuholníkov, polôh, normál, farieb ani UV1. Mení iba UV0 a správne prepočítané tangenty. CPU porovnanie ukazuje väčší detail, ale plochý hranatý tvar zostáva. Štúdia je mimo balíka R12c a nepotvrdzuje natívny vzhľad ani pokrytie či výkon celého trávnika.

## 1. 10. 2026 — R11: nové steblá a členitejšie záhonové rastliny

Samostatná Shipping R11 obsahuje **100 masterov a 300 LOD**, zachováva **40 materiálov a 73 textúr**. Dvadsať trávnikových modelov má postupne zúžené steblá s jednou špičkou. Štyri nové rastlinné modely nahrádzajú štyri hlavné biele rastliny a 420 nízkych trsov; všetkých 473 pôvodných osadení záhrady a 102 011 osadení trávnika zostáva nezmenených. Pôvodných 76 ostatných masterov, architektúra, kolízie, C/B/B a oba odstupy 3 000 mm sú zachované.

**Všetky štyri pôvodné Metal PNG boli posúdené a porovnané s rovnakými pohľadmi R10.** Biele rastliny majú menej nápadnej žltozelenej masy a nízky porast členitejšie tvary. Trávnik má dlhšie špičky, ale zblízka stále pripomína husté ploché pásy s príliš rovnomernou odozvou. Opakované vrstvy listov, pravidelné drobné kvety a rovná hrana trávnika zostávajú viditeľné. Uličný pohľad je prakticky nezmenený. **R11 nie je prijatá ako fotorealistický výsledok; aktívny výber zostáva R5.**

Zdrojové overenie má **230 kontrol: 45 čerstvých a 185 výsledkov nezmenených zdrojov po overení hashov**. Devätnásť Node testov má kontrolné súčty zachytené až po spustení; súhrn toto obmedzenie výslovne uvádza. Nové importové, balíkové a štvorpohľadové audity potvrdzujú skutočné uložené modely a artefakty. Zábery majú 1 920 × 1 080, Cinematic, 2 400 zahrievacích a 300 meraných snímok; pri všetkých štyroch sú aplikácia, okno aj klávesnicové zameranie 300/300. Toto nie je celkové výkonnostné ani interaktívne overenie aplikácie. Háj, susedstvo, nadhľad, noc a chôdza neboli v R11 nanovo zachytené.

Výsledok je v `exterior-validation-20260930-r1/exterior-r11-rejected-review.json`, zdrojový súhrn v `source-validation-r11-r2.json` a pôvodné obrázky v `qa/after-exterior-r11-shape-artifacts-1790847691627/`. Pred ďalšou zmenou sa celý projekt, balík, zdroje a štyri zábery zapečatili v `exterior-20261001-r11/source-freeze/snapshot.json`: **9 532 nezávislých APFS kópií, 22,22 GB logických dát**, s overenými hashmi a odlišnými inode, bez hardlinkov. Z toho 4 289 historických identít R10 je oddelených od aktuálnych zdrojov. Nasledujúca štúdia plynulých povrchov a nízkeho porastu na susedných parcelách sa v R11 ešte nenachádza.

## 1. 10. 2026 — R10 posúdená v deviatich natívnych pohľadoch

Samostatná Shipping R10 prešla skutočným importom, uložením, novým načítaním a balením: **96 masterov, 288 LOD, 40 materiálov a 73 textúr**. Päť ďalších presne overených albedov má opravený výklad sRGB; pôvodné fotografie, alfa, ostatné materiálové odozvy a geometria sa nemenia. Šesť uložených natívnych textúr vrátane predchádzajúcej opravy lesného podkladu má potvrdený správny výklad; ostatných 67 zostáva nezmenených.

**Všetkých deväť skutočných Metal PNG bolo posúdených, R10 zostáva vizuálne zamietnutá.** Pôda má prirodzenejšiu tmavohnedú farbu, ale tá zvýrazňuje ostré, pravidelné materiálové hrany a medzery v poraste na susedných parcelách. Papierové steblá, svetlé hlavné kríky, opakované rozety, tlačený lesný podklad a ploché ortofoto stále bránia plnému realizmu. Hlavné svetlé kríky a nízke rozety používajú iné materiály než päť nových farebných opráv; zmenou preto nevznikla zásadná úprava ich vzhľadu. **Aktívny výber ostáva R5; cieľ úplnej realistickosti zelene pokračuje.**

Zdrojové overenie má **200 kontrol: 63 čerstvých a 137 výsledkov nezmenených zdrojov po overení hashov**, so 637 jedinečnými závislosťami. Aktuálny súhrn `exterior-validation-20260930-r1/source-validation-r10-r2.json` opravuje iba dátumové označenie kandidáta v pôvodnom r1; pôvodný doklad zostáva zachovaný a kontroly sa nepočítajú druhýkrát. Deväť záberov má PNG 1 920 × 1 080, Cinematic, 2 400 zahrievacích a 300 meraných snímok. Osem má aplikáciu aj okno v popredí pri 300/300; ulica má 0/300 a jej časovanie je neplatné. Súbor sa neprijíma ako celkové výkonnostné overenie a unfocused R9a sa nepoužíva na porovnanie FPS.

Presný výsledok je v `exterior-validation-20260930-r1/exterior-r10-rejected-review.json`, vrátane samostatných importových a natívnych auditov a dvoch nezávislých vizuálnych hodnotení. Pred ďalšou zmenou sa celý zdroj, projekt, balík, deväť záberov a pripnuté dôkazy zapečatili v `exterior-20261001-r10/source-freeze/snapshot.json`: **5 200 nezávislých APFS kópií, 17,61 GB logických dát**, s overenými hashmi a rozdielnymi inode, bez hardlinkov.

Nová samostatná štúdia `exterior-lawn-tapered-20261001-r2-study` má dlhé špičky stebiel, maximum šírky v 36–45 % dĺžky a nezmenených 102 011 koreňov, 40 skupín aj trojuholníkový rozpočet. Sedem čerstvých kontrol prešlo. Z dekódovaných trojuholníkov merané štyri 1 m² vzorky dosahujú **75,18–78,48 % pokrytie**; aj dve hraničné vzorky splnili svoje pôvodné ciele. Najnižšia vnútorná vzorka má rezervu iba 0,18 percentuálneho bodu. Nejde o meranie celej parcely, natívny render ani prijatie výkonu; tvar sa musí overiť v ďalšom samostatnom balíku.

## 1. 10. 2026 — natívny R9a posúdený, realizmus stále nedosiahnutý

Shipping R9a má 102 011 trsov so vzpriamenými, zakrivenými steblami a deväť korunových modelov so súvislým vetvením. Natívny import, uloženie, opätovné načítanie a balenie prešli; 96 rastlinných masterov, 288 LOD, 40 materiálov a 73 deduplikovaných textúr sú overené v skutočnom balíku. Presné osadenie 78 stromov, pôvodná architektúra, terén, C/B/B a oba odstupy 3 000 mm zostávajú zachované.

**Všetkých šesť skutočných Metal PNG bolo posúdených aj nezávisle porovnaných s R8.** Vzpriamený trávnik odstránil vodorovné odstrižky a hladké ostrovy v popredí; koruny už nemajú nápadné holé horné výhonky a oddelené poschodia. Lesný podklad má po oprave výkladu farieb teplejšiu farbu. Trávnik však zblízka stále pripomína ostré papierové listy s jednotnou hustotou; podsadba opakuje rozety, kry sú príliš svetlé a okolité povrchy majú ploché materiálové hranice. **Úroveň na nerozoznanie od reality sa neprijíma; aktívny balík ostáva R5.**

Zdrojové overenie má **217 kontrol: 181 čerstvých a 36 nezmenených výsledkov po kontrole hashov**, s 522 overenými závislosťami. Každý záber má PNG 1 920 × 1 080, Cinematic, 2 400 zahrievacích a 300 meraných snímok. Pri všetkých šiestich bola aplikácia mimo popredia (0/300), preto sa časy nepoužívajú ako platné výkonnostné porovnanie. Doklady sú v `exterior-validation-20260930-r1/source-validation-r9-r1.json`, `greenery-upright-package-qa-r9a-audit-r1.json` a `exterior-r9a-rejected-review.json`. Celý zdroj, projekt, balík a šesť záberov sú zachované v `exterior-20260930-r9a/source-freeze/snapshot.json`: **5 081 súborov** s nezávislými APFS kópiami a overenými hashmi.

Samostatná natívna Metal diagnostika potvrdila nesprávny výklad farieb konkrétnej 16-bitovej textúry lesného podkladu. Pri 12 vzorkách vybraných zo zdroja pred meraním zodpovedá explicitný výklad sRGB pôvodným dátam s maximálnou chybou 0,01141 v lineárnom RGB. Dôkaz je v `exterior-texture-encoding-probe-analysis-20260930-r2/diagnostic.json`; fotografia, R8 aj jeho balík ostali nezmenené. Oprava pre R9 sa týka iba overeného albeda `forest_leaves_04`. Táto diagnostika sama nepotvrdzuje fotorealistický vzhľad celej scény.

Prvý R9 prešiel natívnym importom, uložením a opätovným načítaním, ale následná Node kontrola nesprávne očakávala starý typ korún. Podmienka je opravená a overená aj proti skutočnému novému výsledku; dokončená R9a vznikla z pôvodného Shipping donora. Pokus R9 vrátane 4 253 pripnutých súborov ostáva zachovaný v `exterior-20260930-r9/source-freeze/snapshot.json`.

Samostatná GPU diagnostika 1. 10. potvrdila rovnakú chybu aj pre päť presných albedov: `farm_soil`, `nettle`, `tree_small_02_trunk`, `shrub_04` a `periwinkle`. Pri 56 oblastiach vybraných zo zdroja pred GPU meraním znížil explicitný výklad sRGB maximálnu lineárnu RGB chybu z 0,2658–0,2997 na 0,00275–0,00624. Alfa sa nezmenila pri všetkých 116 vzorkách. Jeden ostrý bod žihľavy má už v pôvodnom importe chybu alfy 0,005875; táto chyba sa opravou RGB nemení. Samostatné masky neboli GPU vzorkované. Dôkaz a nezmenené zdroje sú v `exterior-texture-encoding-context-analysis-20261001-r1/diagnostic.json`. Následný natívny R10 výsledok je uvedený vyššie; kauzálna oprava zdrojových farieb sama nepotvrdzuje realistický vzhľad.

Nová geometrická štúdia `exterior-lawn-tapered-20261001-r1-study` porovnáva postupne zúžené steblá a skutočný V profil s pôvodným tvarom. Sedem kontrol dekódovaného GLB prešlo. Pri rovnakej hustote však oba nové tvary dosahujú iba 57,6–61,1 % pokrytie, pod 75 % cieľom; zdvojnásobenie počtu trojuholníkov pri V profile tento problém nerieši. Zostávajú samostatnou štúdiou s výslovne neúspešným vnútorným pokrytím a nezapájajú sa do R10. Ďalší návrh musí riešiť prirodzený tvar aj súvislosť porastu.

## 30. 9. 2026 — natívny R8 zamietnutý, pokračuje vývoj zelene

Shipping kandidát `output/unreal/exterior-20260930-r8/` prešiel importom, uložením, opätovným načítaním a balením: **96 rastlinných masterov, 288 LOD, 40 materiálov a 73 deduplikovaných textúr**. Jemnejší trávnik má 69 876 osadení v 40 skupinách; háj zachováva všetkých 78 stromov a pridáva 24 773 ekologických detailov v 130 skupinách. Nový fotografický podklad tvorí 53 plôch s jemným reliéfom. Pridané kužeľové koreňové nábehy sa odstránili. C/B/B, oba odstupy 3 000 mm, pôvodná architektúra, materiálové assety a kolízie sú zachované.

**Všetkých šesť skutočných Metal PNG bolo vizuálne posúdených a R8 je zamietnutý.** Užšie steblá pomohli siluete, ale tráva stále vyzerá ako vodorovne prekrížené odstrižky nad hladkými zelenými miestami. Pri terase zostáva svetlý odkrytý pás. Lesný podklad má viac detailu, no natívne pôsobí príliš bledo; opakované malé hromádky listov a valcový kontakt kmeňov zostávajú nápadné. Koruny stále majú holé rovné horné výhonky a oddelené poschodia. Aktívny vizuálne prijatý balík ostáva **R5**; úroveň „na nerozoznanie od reality“ dosiahnutá nie je.

Zdrojové overenie má **161 kontrol: 131 čerstvých a 30 nezmenených výsledkov po kontrole hashov**. Dôkazy sú v `exterior-validation-20260930-r1/source-validation-r8-r2.json`, `greenery-fine-import-r8-audit-r1.json` a `exterior-r8-rejected-review.json`. Každý záber má PNG 1 920 × 1 080, Cinematic, 2 400 zahrievacích a 300 meraných snímok. Len detail trávnika a vzdialené koruny majú aplikáciu aj okno v popredí pri 300/300 snímkach; ostatné štyri majú aplikáciu v popredí pri 0/300. Výkon celého súboru sa preto neprijíma. Galéria obsahuje aj zamietnuté pokusy. Celý pripnutý strom R8 je zachovaný v `exterior-20260930-r8/source-freeze/`: **4 522 súborov** s overenými kópiami a hashmi v `snapshot.json`.

Pri uzavretí R8 ešte príčina bledého obrazu potvrdená nebola; následná diagnostika a ďalší vývoj sú uvedené vyššie. Zmrazený R8 sa nemení.

## 30. 9. 2026 — natívny R7 zamietnutý, aktívny zostáva R5

Samostatný Shipping balík `output/unreal/exterior-20260930-r7/` prešiel skutočným natívnym importom, uložením, novým načítaním a balením. Obsahuje **96 rastlinných masterov, 288 LOD uzlov, 39 materiálov a 70 skutočne deduplikovaných textúr**. Finálne priestorové kvety zachováva a pridáva trávnik `exterior-lawn-natural-20260930-r3d`, deväť korunových variantov `exterior-canopy-masters-20260930-r1d` a podrast `exterior-canopy-ecology-20260930-r3`. Pôvodná architektúra, materiálové assety, kolízie, C/B/B a oba odstupy 3 000 mm sú zachované. **R7 je po posúdení všetkých šiestich natívnych záberov vizuálne zamietnutý. Aktívny výber zostáva R5.**

Trávnik má **52 013 priestorových trsov v 40 skupinách** na rovnakej presnej kosenej ploche 143,599 m². Každý trs ponecháva všetkých 36 ohnutých listov v každom LOD. Geometrické vzorkovanie štyroch 1 m² plôch v kroku 0,25 mm meria 79,96–82,22 % pokrytie, najvzdialenejší LOD 79,76–82,02 %; zamietnutý R6a dosahoval 14,60–21,59 %, respektíve 6,75–10,30 %. Natívny obraz potvrdzuje opravu veľkých medzier R6a, ale trávnik zblízka pôsobí ako rovnomerný limetkový koberec širokých zrezaných prúžkov. Pri terase a mulči zostáva hladký pás podkladu. Háj zachováva všetkých 78 koreňov, natočení, jednotných mierok a pôvodných výškových a radiálnych limitov; 24 851 ekologických detailov je v 166 skupinách. Rozvetvenie korún sa zlepšilo, ale bledý rovný povrch s oddelenými podobnými hromádkami listov a opakovanými kužeľovými koreňovými nábehmi stále pôsobí synteticky. Úroveň „na nerozoznanie od reality“ prijatá nie je.

Šesť skutočných Shipping/Metal záberov má rozlíšenie PNG 1 920 × 1 080 a profil Cinematic s plnou hustotou vegetácie. Každý meral 300 snímok po 2 400 zahrievacích snímkach; aplikácia, herné okno aj fokus scény boli aktívne pri **300 z 300 snímok vo všetkých šiestich prípadoch**. Časové hodnoty sú oprávnené na porovnávanie, ale kandidát nemá úplné vizuálne ani výkonnostné prijatie. Tieto rozmery PNG samy nedokazujú interné rozlíšenie všetkých rasterizačných a AA priechodov; živá interaktívna kontrola sa tým nedokladá.

Zdrojové overenie má **114 kontrol: 102 čerstvých a 12 výsledkov nezmenených zdrojov po kontrole ich hashov**. Doklad `exterior-validation-20260930-r1/source-validation-r7-r2.json` zachováva pôvodný 108-kontrolový doklad. Nezávislý importový, balíkový a striktne foreground natívny audit je v `greenery-foreground-qa-r7-audit-r1.json`; zamietnutie viazané na presný hash balíka a šesť snímok je v `exterior-r7-rejected-review.json`. Pred ďalšou iteráciou sa celý pripnutý vstupný strom a zdroje kontroly skopírovali do `exterior-20260930-r7/source-freeze/`: **4 372 súborov**, vrátane 164 zdieľaných zdrojov a assetov, s úplným zoznamom hashov v `snapshot.json`. Galéria `exterior-validation-20260930-r1/index.html` obsahuje **40 pôvodných natívnych záberov** a označuje R7 ako zamietnutý pokus. Nasledujúci kandidát musí upraviť tvar a materiálovú odozvu stebiel, krytie pri hranách a lesný podklad; zmrazený R7 sa nemení.

## 30. 9. 2026 — trávnik a koruny, pokračovanie

Aktívny vizuálne prijatý balík zostáva **R5**. Nový Shipping kandidát `output/unreal/exterior-20260930-r6a/` prešiel natívnym importom, uložením, novým načítaním a balením: 70 rastlinných masterov, 210 LOD uzlov, 36 materiálov a 70 textúr. Zachoval architektúru, pôvodné materiálové assety, kolízie, C/B/B a oba odstupy 3 000 mm. Zdrojové pokrytie tejto revízie je 77 kontrol: 71 v dotknutých sadách, šesť nezmenených geometrických výsledkov prevzatých po overení všetkých pripnutých hashov. Doklad je `output/unreal/exterior-validation-20260930-r1/source-validation-r6a.json`; 116 pripnutých zdrojových súborov je zachovaných v `exterior-20260930-r6a/source-freeze/`.

R6a používa priestorové ružové rastliny `exterior-garden-flower-masters-20260930-r1c` a nový trávnik `exterior-lawn-natural-20260930-r2b`: 9 234 trsov v 38 skupinách na presnej kosenej ploche 143,599 m². Zúženie je potrebné, pretože prvá celoplošná štúdia by prekrývala existujúce lúčne trávy, byliny a kry. Štyri pôvodné trávnikové skupiny sa iba skryjú a vyradia z prepínania detailného osvetlenia; ich 40 437 zachovaných inštancií, všetky transformácie, mesh, materiál a kolízie sa overujú proti doloženému vidieckemu zúženiu pôvodnej 98 344-inštančnej výsadby.

**R6a je vizuálne zamietnutý.** Tri skutočné Metal PNG ukazujú príliš riedky trávnik s hladkými zelenými medzerami, tmavými oddelenými trsmi a pravidelným malým porastom pri hrane. Priestorové ružové kvety majú lepšiu morfológiu a ich zdroj sa zachováva. Hodnotenie je `exterior-validation-20260930-r1/exterior-r6a-rejected-review.json`; galéria obsahuje aj zamietnuté pokusy. Mac bol pri týchto snímkach uzamknutý: aplikácia bola v popredí pri 0 z 300 meraných snímok v každom prípade, preto výkon nie je prijatý ani porovnávaný a živá UI kontrola sa nedokončila. Nová verzia sa nevybrala do `model-refresh-current.json`.

Samostatný zdroj pre háj je pripravený v `exterior-canopy-ecology-20260930-r3`: 17 masterov, 51 LOD uzlov a 24 851 drobných geometrických detailov — koreňové nábehy, zvlnené opadané listy, vetvičky, nízke rastliny a krátke trávy. Šesť nezávislých zdrojových testov overilo celé koruny a odstupy od súkromného pozemku, ciest, budov a obrábanej pôdy. Všetkých 78 koreňov stromov a pôvodný výslovne odvodený terén zostáva zachovaných. Tento zdroj ešte **nie je natívne importovaný ani vizuálne prijatý**. Nasleduje hustejší súvislý kosený trávnik a členitejšie koruny hája; cieľ úplnej realistickosti zelene zostáva otvorený.

## 30. 9. 2026 — nové záhradné rastliny a susedné parcely

Zmrazený vstup pre nový natívny kandidát je `output/unreal/exterior-assets-20260930-r3/`: **48 rastlinných variantov, 144 LOD uzlov**. Zachováva knižnicu R6 a pridáva sedem variantov skutočnej priestorovej geometrie v `output/unreal/exterior-garden-masters-20260930-r3/`: tri okrasné trávy s objemovými semenami a jemnými klasmi, dve fialové trvalky s priestorovými listami a dve nízke listové ružice. Nové GLB majú vertex colour, spojité rámy ohnutých stebiel a overené normály, tangenty a orientáciu všetkých trojuholníkov. Fotografie dodávajú farbu jednotlivých listov a stebiel; nové hlavy rastlín sú priestorová geometria.

Záväzný plán je `output/unreal/exterior-garden-masters-20260930-r3/garden-plan.json`. V pôvodných mulčových záhonoch obsahuje **461 detailových inštancií** a nahrádza **šesť hlavných tráv** novými priestorovými trsmi. Zachováva všetkých 12 pôvodných hlavných koreňov; mierka každej rastliny je jednotná vo všetkých osiach. Zdrojový plán detailových skupín je `output/unreal/exterior-garden-drifts-20260930-r1/garden-plan.json`. Ide o autorský návrh výsadby, nie súpis existujúcich rastlín. C/B/B a oba odstupy 3 000 mm zostávajú záväzné.

Okolie používa `output/unreal/exterior-context-20260930-r3/neighborhood-details.json`: detaily 281 budov podľa prevzatých oficiálnych pôdorysných stôp, 573 pôdnych plôch na 72 parcelách, okná, vstupy, odkvapy, zvody, komíny a štrk na cestách. Podoby fasád a tieto drobné prvky sú ilustračné odhady. Plán pripína indexy 47 203 odstránených nízkych rastlín, ktorých celé zaznamenané koruny by zasahovali do nových pôdnych plôch.

Kompletný materiálový vstup s pôvodným ortofotom a field macro, bez sezónnej náhrady farieb polí, obsahuje **34 materiálov a 70 textúr**. `context_soil_exposure` používa farm_soil, tmavší zemitý odtieň a scale 0,30; UV0.x nesie geometrické krytie od 0 na okraji po 1 vo vnútri. Natívny `ComponentMask` kombinuje túto hodnotu s viacmierkovým šumom pôdy a vzdialenosťou kamery, potom ju odovzdáva vstavanému `DitherTemporalAA` do opacity mask. PBR mapy a normály zostávajú mapované v svetových súradniciach; nové pôdne kúsky plynulo zanikajú medzi 40 a 100 m. Funkčný asset, jeho hash, grafové väzby a uložené materiálové nastavenia sa pripínajú a overujú. Orná pôda má albedo scale 0,35, záhradná pôda 0,65. Mulč používa nezmenené mapy wood_chips s tmavšou autorskou albedo scale 0,62 a tint `[0.94,0.98,1]`. Zelené pixely pôvodnej kvitnúcej kompozície majú autorskú kalibráciu jasu 0,60 a saturácie 0,88; zdrojové fotografie sa neprepisujú. Tri nové autorské rastlinné materiály sú opaque TwoSidedFoliage s vertex colour a obmedzeným presvitaním; fotografické steblá sú opaque a obojstranné.

Pri nadhľade prechádzajú štyri poľné materiály a `context_track` medzi 50 a 150 m na farbu pôvodného geografického ortofota. Vzdialený terén a jeho výslovne označená výšková náhrada používajú rovnaký prechod RGB podľa kamery; pôvodný radiálny prechod 180–360 m zostáva iba pri blízkej PBR odozve normál a drsnosti. Toto je výslovná autorská úprava receptu, pôvodný manifest ortofota a jeho pixely sa nemenia. Samostatná ochranná maska `scripts/unreal/exterior-ortho-projection-mask.py` zachováva dom, vlastnú parcelu a skutočnú autorskú geometriu súkromného pozemku; oficiálne stopy okolitých budov majú rezervu 150 cm. Okraje masky používajú plynulý 300 cm prechod a rezervu pre bilineárne vzorkovanie. Tmavé pixely, cesty, koruny stromov ani hranice polí nevytvárajú diery v fotografii. Pôvodná alfa pokrytia poskytovateľa sa vyhodnocuje samostatne. Stará field macro maska zostáva len jemnou skalárnou korekciou blízkych poľných povrchov. Ortofoto z roku 2024 obsahuje pôvodné osvetlenie a tiene; nepredstavuje aktuálny terénny súpis.

Import v predvolenom fotografickom pohľade skrýva čiary `context_parcel_line`; zdrojová parcelná geometria ostáva zachovaná. Pre nový import s geodetickou grafickou vrstvou nastaviť `BREZI_EXTERIOR_SURVEY_OVERLAY=1`. Toto nastavenie nemení dôkazovú úroveň polohy domu ani hraníc.

**Stav: R5 je natívne overený a prijatý ako výrazné vizuálne zlepšenie exteriéru. Úroveň „na nerozoznanie od reality“ zatiaľ prijatá nie je.** Balík je v `output/unreal/exterior-20260930-r5/package/Mac/BreziTwin.app`; presné hodnotenie a kontrolné súčty sú v `output/unreal/exterior-validation-20260930-r1/exterior-r5-review.json`, galéria v rovnakom adresári v `index.html`. Staršie kandidáty R1–R4 majú samostatné zamietnutia a zostávajú zachované.

Import, uloženie a nové načítanie overili zachovanie pôvodnej architektúry, materiálových assetov, kolízií, transformácií, C/B/B a oboch odstupov 3 000 mm. Zdrojové pokrytie R5 je **79 úspešných kontrol**: 53 kontrol dotknutých vstupov bolo spustených znovu, 26 geometrických výsledkov sa prevzalo až po zhode nezmenených zdrojových a testových hashov. Shipping balík prešiel ôsmimi natívnymi prípadmi na Apple M5 Pro cez Metal; pri všetkých meraných snímkach boli aplikácia aj herné okno aktívne.

| Natívny prípad | Profil a výstup | Priemer snímky | FPS z priemeru | P95 |
| --- | --- | ---: | ---: | ---: |
| Okolie | Balanced, 1920 × 1080 | 15,64 ms | 63,9 | 20,88 ms |
| Záhrada | Balanced, 1920 × 1080 | 19,10 ms | 52,3 | 24,53 ms |
| Ulica | Balanced, 1920 × 1080 | 17,60 ms | 56,8 | 22,64 ms |
| Parcely | Balanced, 1920 × 1080 | 24,68 ms | 40,5 | 30,02 ms |
| Nadhľad | Balanced, 1920 × 1080 | 15,45 ms | 64,7 | 20,71 ms |
| Detail záhrady | Cinematic, 3840 × 2160 | 41,21 ms | 24,3 | 46,77 ms |
| Terasa v noci | Cinematic, 3840 × 2160 | 35,75 ms | 28,0 | 41,75 ms |
| Pohyb pri záhone | Cinematic, 1920 × 1080 | 38,20 ms | 26,2 | 43,18 ms |

Statické prípady merajú po 300 snímok po zahriatí; pohyb meria 1 178 snímok počas 45,00 s. Ide o pohyb zdrojovej kamery ±8°, nie úplný oblet, chôdzu ani nové overenie kolízií. FPS vyjadruje tieto konkrétne prípady s vypnutým VSync a limitom FPS. Renderovací recept nastavuje `r.ScreenPercentage.MaxResolution` na 900 riadkov v Balanced a 1 080 v Cinematic; používa TSR. V oboch 4K prípadoch natívny doklad pozoruje render target a RHI textúru 3840 × 2160 počas celého merania. Skutočné rozmery interných rasterizačných a AA priechodov neboli profilované; samotné nastavenie limitu ani označenie TemporalUpscale nedokazuje znížené interné rozlíšenie. Dôkaz pochádza z macOS na tomto zariadení, nie z Windows alebo inej GPU. Shipping má vypnutý bežný log: detektor inicializácie v poli `entry` preto neprešiel; natívne PID, konfiguráciu, dokončené meranie a skutočný obraz overujú samostatné runtime doklady.

Vizuálne sa prijíma vrstvená priestorová výsadba, tmavší mulč, členitejšia pôda a spojité fotografické okolie bez zelených pásov pri spojení s vzdialeným terénom. Zostávajú viditeľné limity: pravidelný ihličkovitý trávnik, niektoré príliš svetlé zelené listy, ostré hrany záhonov, veľmi čisté stavebné povrchy, preexponované nočné svetlá a tiene už obsiahnuté v ortofote. Okolité fasády sú stále ilustračné. Tieto limity bránia prijatiu úplného fotorealizmu.

Reprodukcia z koreňa repozitára používa Python 3.12.9 a Shapely 2.1.2 v existujúcom prostredí. Všetky výstupy musia byť nové; zmrazené adresáre sa neprepisujú. Prvé dva kroky vytvoria detailový plán a nové GLB, tretí zloží master, potom sa vytvorí okolie a ochranná maska:

```sh
exterior_python=output/unreal/exterior-tools-py312-20260926/bin/python

$exterior_python -B scripts/unreal/exterior-garden-drifts.py \
  --base-plan output/unreal/exterior-garden-morphology-20260927-r6b/garden-plan.json \
  --assets output/unreal/exterior-assets-20260927-r6/geometry-manifest.json \
  --geometry output/unreal/realism-20260926-r5/geometry \
  --output output/unreal/exterior-garden-drifts-reproduction

$exterior_python -B scripts/unreal/exterior-garden-masters.py \
  --base-garden output/unreal/exterior-garden-drifts-reproduction/garden-plan.json \
  --library output/unreal/exterior-assets-20260927-r6 \
  --output output/unreal/exterior-garden-masters-reproduction

$exterior_python -B scripts/unreal/exterior-assets-merge.py \
  --base output/unreal/exterior-assets-20260927-r6 \
  --extension output/unreal/exterior-garden-masters-reproduction \
  --output output/unreal/exterior-assets-reproduction

$exterior_python -B scripts/unreal/exterior-neighborhood.py \
  --context output/unreal/exterior-context-20260927-r8/context-plan.json \
  --buildings output/unreal/exterior-buildings-20260926-r2/building-plan.json \
  --scene output/unreal/realism-20260926-r5/geometry/scene.json \
  --output output/unreal/exterior-neighborhood-reproduction

$exterior_python -B scripts/unreal/exterior-ortho-projection-mask.py \
  --context output/unreal/exterior-context-20260927-r8/context-plan.json \
  --buildings output/unreal/exterior-buildings-20260926-r2/building-plan.json \
  --scene output/unreal/realism-20260926-r5/geometry/scene.json \
  --ortho output/unreal/exterior-ortho-20260927-r2/orthophoto-manifest.json \
  --output output/unreal/exterior-ortho-projection-reproduction
```

Natívny importer vyberá tieto vstupy cez `BREZI_EXTERIOR_ASSETS`, `BREZI_EXTERIOR_GARDEN`, `BREZI_EXTERIOR_NEIGHBORHOOD` a `BREZI_EXTERIOR_ORTHO_PROJECTION`. Pre natívny R5 zodpovedajú uvedenému master adresáru, finálnemu `garden-plan.json`, `neighborhood-details.json` a `output/unreal/exterior-ortho-projection-20260930-r2/ortho-projection-manifest.json`. Presný výber ostatných prevzatých vstupov je v `output/unreal/exterior-validation-20260930-r1/native-inputs-r5.json`. Reprodukcia vytvára nové cesty a hashe; následný import a prijatie preto potrebuje vlastný nový výstup a dôkazy.

Stav knižnice k 27. 9. 2026. Záväzný návrh ostáva [C/B/B](active-design.md), oba odstupy 3 000 mm. Tento dokument opisuje zdroje a reprodukciu vegetácie; nemení osadenie ani stav vizuálneho prijatia.

## Knižničná revízia R6 z 27. 9. 2026 — zelená regionálna výsadba

Aktuálny zložený master je `output/unreal/exterior-assets-20260927-r6`: 41 variantov, 123 LOD uzlov, 14 rastlinných receptov. Vznikol cez `scripts/unreal/exterior-assets-merge.py` z knižnice R5 a dvoch samostatných rozšírení. Pôvodné knižnice aj pôvodné mapy zostávajú zachované. Nasledujúce počty opisujú zmrazené vstupy; natívne prijatie určuje samostatné review konkrétneho balíka.

- `exterior-regional-assets-20260927-r4`: tri členité listnaté formy a jeden nízky ker, súvislé vetvenie, fotografické listy [CGBookcase](https://www.cgbookcase.com/textures) pod CC0 a pôvodná kôra Poly Haven. Nové listové mapy majú explicitný natívny stretch na rozmer mocniny dvoch pre správne mipmapy; pôvodné PNG ani modelové UV sa nemenia.
- `exterior-garden-morphology-20260927-r6b`: dve nové ružové kompozície s nerovnakou výškou, ohybom a sklonom výhonkov; pôvodný materiál a UV vrátane opakovania mimo 0–1. Všetkých 12 koreňov výsadby a 10 nezmenených kompozícií zostáva zachovaných.
- `exterior-context-20260927-r8`: 1 100 explicitných stromových/krových umiestnení v skupinách, z toho štyri zachované ilustračné malé stromy; 86 248 nových nízkych trsov na najbližších plochách. Pôvodných 382 678 lúčnych trsov, 2 824 vinohradových miest, parcely a terénne mesh sú zachované.
- `exterior-yard-20260927-r2`: 15 111 krátkych trsov na pôvodnej zemine a krajniciach. Nezávislý audit overil celé koruny, všetky mulče vrátane zapusteného zadného pásu, vstupy, stavbu, terasy a nášľapy. Pôvodná verzia R1 je zamietnutá pre prienik do zadného mulča a nie je vstupom R6.

Nové regionálne modely majú `placementPolicy: explicit-only`: importer používa konkrétny `meshId`, koreň, natočenie a jednotnú mierku vo všetkých osiach. Nezamiešava ich do starej náhodnej voľby rastlín. Pôvodné štyri riedke africké tvary sa v tejto výsadbe nahrádzajú novými regionálnymi korunami; ich zdrojové assety sa nemažú. Druhová identita ani presná poloha jednotlivých stromov sa nevydávajú za terénny súpis.

Kompletný R6 materiálový návrh s ortofotom obsahuje 29 materiálov a 68 textúr. Stromové LOD2 majú hrubšiu vnútornú kresbu; prechod a výkon treba hodnotiť na skutočnom pohybe kamery. Sezónna úprava samotného ortofota je zatiaľ samostatný prototyp a do tohto vstupu R6 nepatrí.

## Historické zmrazené vstupy

Všetky cesty sú relatívne ku koreňu repozitára:

- **R2:** `output/unreal/exterior-assets-20260926-r2/` — 28 variantov, 84 LOD uzlov, 7 GLB, 9 materiálových receptov.
- **Závislosť R1:** `output/unreal/exterior-assets-20260926-r1/` — R2 odtiaľ priamo referencuje `glb/tree_small_02.glb`, `glb/grass_medium_02.glb`, `glb/nettle_plant.glb` a príslušné pôvodné textúry. R2 nie je samostatný adresár na prenos.
- **R3:** `output/unreal/exterior-assets-20260926-r3/` — 35 variantov, 105 LOD uzlov, 10 referencovaných GLB a 12 materiálových receptov. Pridáva 7 okrasných kompozícií v 3 GLB; všetkých 28 geometrických záznamov R2 zachováva. Na prenos treba všetky tri knižnice.
- **Vstupná knižnica R4:** `output/unreal/exterior-assets-20260926-r4/` — `geometry-manifest.json` a `asset-manifest.json` sú bajtovo zhodné s R3; `material-manifest.json` je bajtovo zhodný s odvodeným R4 manifestom nižšie. R4 tým jednoznačne vyberá opravené albedo, stále závisí od súrodeneckých zdrojov R1/R2/R3 a `exterior-alpha-20260926-r4/`.
- **Výsadba R4:** `output/unreal/exterior-garden-20260926-r4/garden-plan.json` a `composition-manifest.json` — 12 explicitných inštancií zo zmrazenej geometrie R3, bez nových GLB. `meshId`, `positionCm`, `yawDeg` a bezrozmerné `scale=[s,s,s]` sú záväzné; `actualHeightCm` a `radiusCm` vychádzajú zo všetkých LOD.
- **Natívna väzba:** `output/unreal/exterior-20260926-r2/exterior-import-report.json`, pole `inputFiles`, obsahuje SHA256 manifestov, GLB a máp použitých importom. `model-package.json` v tom istom adresári je doklad Shipping balíka.

SHA256 R2 manifestov sa zhodujú s `inputFiles` natívneho importu:

```text
geometry-manifest.json  74951f361914e3814c672a42c072df57d411c883185d361fa7e0f80b1e6c1842
material-manifest.json  f635401679f06a7b3be087b14267bfc2e41acc2109838cc2655bac9544d79d59
asset-manifest.json     3008e96a11e3432085722206c13fc10cd8ccd0094bd120278f4364e2b891a730
```

SHA256 zmrazených manifestov R3:

```text
geometry-manifest.json  918d309b517f7d3854c29e990ff471efe226d6ca97f25e326733a254e3db4569
material-manifest.json  1d6bb2f861be451b76394225602adaadb571d3d0c121a99421486c8a93f35bfc
asset-manifest.json     fb2fe91c7960f3f4c8dc99cdee705ba626e23ea0597764f2fa58f57133c1eb9f
```

SHA256 výsadby R4:

```text
garden-plan.json        3be79236ed33683b5b5b8e13e27b10ef353acb2497ebf64f6002cf4c1fd6f821
composition-manifest.json 95bf335a6e49766885267abc0e10482fc18e7665a2e9cbf6afe54062e6eceb5a
```

Presné R1 GLB závislosti použité R2:

```text
tree_small_02.glb   aaa458f840a2ee8deb6e0202bc7f2b8ef3c7e7a3989273ecead0726e7444d93a
grass_medium_02.glb c09551da5f8138fc84fe50a05d6d8d4ce3cd6dd504e32cdc10ba5218b6dd386a
nettle_plant.glb    c10c949f8795e2db600504fc54d0a0fac9b8c5a37c597d5cd23dc5f74cd175cd
```

`asset-manifest.json` v knižniciach uchováva URL, autorov, veľkosti, MD5 a SHA256 pôvodných stiahnutých súborov. `geometry-manifest.json` nesie presné názvy uzlov, poradie materiálov, počty trojuholníkov a natívne hranice. `material-manifest.json` viaže každú mapu na cestu a SHA256. Zmrazené adresáre, manifesty a vstupy balíka **neprepisovať pri ďalšom exporte**.

## Zdroje, licencia a význam modelov

Historické rastlinné modely a textúry v nasledujúcej tabuľke pochádzajú z Poly Haven a sú [CC0](https://polyhaven.com/license). Pri každom zdroji sú lokálne `<asset>/info.json`, `files-api.json`, `<asset>_2k.blend` a `textures/`; podrasť má aj pôvodný FBX. API je `https://api.polyhaven.com/info/<asset>` a `https://api.polyhaven.com/files/<asset>`.

| Zdroj | Knižnica / použitie | Derivácia |
| --- | --- | --- |
| [Tree Small 02](https://polyhaven.com/a/tree_small_02) | R1; 3 stromy | Burkea africana / wild syringa. Rozpočtové LOD z pôvodného LOD1: 224 787 / 94 910 / 29 971 trojuholníkov; tri mierne tvarové obmeny. |
| [Grass Medium 02](https://polyhaven.com/a/grass_medium_02) | R1; 5 tráv | Prevažne suchý vzhľad; zdroj + odvodené LOD 0,55 / 0,25. |
| [Nettle Plant](https://polyhaven.com/a/nettle_plant) | R1; 6 bylín | Pôvodné tri LOD; zdrojové rastliny sú malé, približne 2–22 cm. |
| [Shrub 02](https://polyhaven.com/a/shrub_02) | Iba zachovaný R1 | Riedka úzkolistá bylina. **Vylúčená z R2**: nevhodná ako hustá koruna vinohradu. |
| [Shrub 01](https://polyhaven.com/a/shrub_01) | R2; `vine_broadleaf_a–c` | Sedem zdrojových výhonkov na korunu, 1,40 × 1,05 × 0,85 m; 10 902 / 6 384 / 3 220 trojuholníkov. |
| [Shrub 04](https://polyhaven.com/a/shrub_04) | R2; `shrub_broadleaf_a–c` | Sedem výhonkov na ker, 0,80 × 0,90 × 0,85 m; 21 901 / 10 946 / približne 4 925 trojuholníkov. |
| [Celandine 01](https://polyhaven.com/a/celandine_01) | R2; 5 pôdopokryvných variantov | Pôvodné LOD, výška 12–19 cm. |
| [Grass Bermuda 01](https://polyhaven.com/a/grass_bermuda_01) | R2; 3 trsy | 72 živých zdrojových výhonkov na trs; suché objekty vynechané. Výška 15–18 cm; odvodené LOD 0,65 / 0,35. |
| [Grass Medium 01](https://polyhaven.com/a/grass_medium_01) | R3; `ornamental_grass_a–c` | 64 skutočných vysokých výhonkov vrátane zdrojových klasov a 5 základových trsov. Kompozícia má 85 cm; zdrojové vysoké výhonky 24–32 cm. Nejde o botanicky kalibrovanú výšku. |
| [Shrub 01](https://polyhaven.com/a/shrub_01) | R3; `ornamental_white_a–b` | 7 kvitnúcich výhonkov `g/h/i` a 6 zelených výhonkov; 78 cm. Zachované zdrojové LOD listov a kvetov. |
| [Periwinkle Plant](https://polyhaven.com/a/periwinkle_plant) | R3; `ornamental_pink_a–b` | 15 zdrojových výhonkov, 72 cm, pôvodné LOD1–3. Zostáva viditeľná stonková základňa; nejde o jednoliaty strihaný ker. |

Táto zmes rôznych druhov a biomov je **ilustračná vizuálna výsadba**, nie botanický súpis Březí. `shrub_01` je podľa zdrojových metadát **Ageratina adenophora, nie Vitis vinifera**. Riadky vyjadrujú krajinnú interpretáciu vinohradu; trojuholníky listov neurčujú miestny druh. Africký strom nie je tvrdením o existujúcom strome na parcele. Aj kompozície siedmich výhonkov a zmeny mierky sú autorské úpravy, nie samostatné skeny celých miestnych rastlín.

R3 používa rolu `ornamental`, formu `grass` alebo `flowering` a farbu `white`/`pink`. Zdroj sa volá `grass_medium_01`; samostatný model `grass_tall` sa pri akvizícii nenašiel, vysoké výhonky sú objekty v tomto modeli. Názov Periwinkle sa nezužuje na neoverený konkrétny druh. Nové kompozície obsahujú priestorové listy a stonky, nie tri prekrížené fotografie celej rastliny.

| R3 variant | Trojuholníky LOD0 / LOD1 / LOD2 |
| --- | --- |
| `ornamental_grass_a` | 48 071 / 24 532 / 14 342 |
| `ornamental_grass_b` | 47 614 / 24 619 / 14 406 |
| `ornamental_grass_c` | 49 440 / 24 477 / 14 525 |
| `ornamental_white_a` | 93 067 / 39 347 / 36 095 |
| `ornamental_white_b` | 100 587 / 42 217 / 38 965 |
| `ornamental_pink_a`, `ornamental_pink_b` | každý 48 216 / 22 548 / 11 457 |

## Geometria a materiály

Export vznikol v Blenderi **5.2.1 LTS**, lokálne `/Applications/Blender.app/Contents/MacOS/Blender`. GLB používa metre a Y-up: Blender `[x,y,z]` → glTF `[x,z,-y]` → Unreal `[100*x,-100*y,100*z]`. Node aj mesh majú meno `PH_<variant>_LOD<n>`. Spoločný koreň a orientácia platia pre všetky tri LOD. Pri zdrojových skrytých kolekciách použiť explicitný `rotation_euler` a `scale`; ich cache `matrix_world` predtým vracala nesprávnu identitu.

GLB obsahuje neutrálne materiálové zástupné definície s presnými `ph_*` názvami. Pôvodný komplexný Blender shader sa neprenáša automaticky. UE recept používa UV0, sRGB iba pre albedo, lineárne ostatné mapy a **DirectX normály bez ďalšieho prevrátenia zelenej**. Listy sú masked/two-sided foliage, kôra opaque. `albedoScale`, `specular`, `subsurfaceScale`, `normalStrength` a voliteľná `maps.mask` sú explicitné; UE intenzita presvitania je umelecké nastavenie, nie fyzikálne kalibrovaný prepočet Blender shaderu.

Zdrojové hodnoty sú zaznamenané v R2 `source-material-graphs.json` a `additional-source-material-graphs.json`. Native import zabezpečujú `scripts/unreal/exterior-import.py` a `exterior-materials.py`; aktívna knižnica sa odovzdáva cez `BREZI_EXTERIOR_ASSETS`.

R3 dopĺňa `provider-material-graphs.json`. Kľúče nových materiálov sú `ph_grass_medium_01`, `ph_shrub_01_ornamental` a `ph_periwinkle_plant`; Periwinkle používa zdrojový kanál `opacity` ako alpha. Jeho transmission/backfacing/vertex-color sieť ostáva zdokumentovaná, zjednodušený UE recept ju nereprodukuje presne. R3 kópia receptov kalibruje problémové listy a nové ornamentály na specular 0,12 / subsurfaceScale 0,08, pôvodné provider hodnoty uchováva. R1/R2 sa tým nemenili.

R4 opravuje samotné rozmiestnenie: 4 biele a 2 ružové kvitnúce trsy, 6 tráv, deväť korún v pôvodných záhonoch a tri korene mimo nich na presnom historickom XY. Všetky osi majú rovnakú mierku. Konkrétne veľkosti vyplývajú z priestoru a celej LOD koruny, nie z natiahnutia rastliny do úzkej výšky 110–125 cm. Plán overuje aj všetky nášľapy `DOM_01961–01964`, pool coping a terasy. `underplantingDirection` je iba viditeľne označený kompozičný cieľ; nepredstavuje ďalšie vygenerované alebo schválené inštancie.

## R4 — odstránenie bielych okrajov atlasu

`output/unreal/exterior-alpha-20260926-r4/derived-material-manifest.json` zachováva 12 receptov R3 a nahrádza **päť albedo máp**: `ph_celandine_01`, `ph_grass_bermuda_01`, `ph_grass_medium_01`, `ph_grass_medium_02` a `ph_tree_small_02_leaves`. Nové `*_diff_rgb_dilated.png` sú odvodené RGB8 obrázky; normály, roughness a pôvodné alpha masky zostávajú referencované bez zmeny.

Zdrojové RGBA atlasy mali v čiastočne priesvitných okrajoch takmer biele RGB. Pri `grass_medium_01` meranie lineárneho RGB týchto okrajov vyšlo približne `[0,961; 0,965; 0,811]`. `scripts/unreal/exterior-alpha-dilate.py` nahrádza RGB pri alpha pod 0,99 farbou najbližšieho nepriesvitného pixelu pomocou euklidovskej distance transform. RGB pri alpha ≥0,99 ostáva bajtovo zhodné; pôvodné fotografické zdroje a alpha sa nemenia. Nejde o prefarbenie celej rastliny ani o retuš natívneho záberu.

Nettle, Periwinkle a Shrub 01/04 tento preukázaný biely fringe nemali, preto sa ich albedo nemení. Nastavenie UE `FillZeroAlphaPNGData` rieši pixely s nulovým alpha; samo neopraví kontaminované čiastočne priesvitné okraje.

```text
derived-material-manifest.json 84847d52e9d0206de0ce9b30d9441973dab71fd6bfafca36d7fb1612198ba301
derivation-report.json         e3b54fb69d81cca3d01f0efe768a9d10c4d1b8d79789cf574c9843437206ceeb
exterior-alpha-dilate.py       3d94996dd3415084473d6159b135925edd971acea3f5b6448f759ecb5194d2a9
```

`derivation-report.json` pripína zdrojové mapy a generátor, dokladá zachovanie nepriesvitných pixelov a nezmenené alpha masky. CPU simulácia lineárnych mipov v reporte nie je Unreal DDC, Metal sampling ani dôkaz vizuálneho prijatia. Stav pri derivácii je `derived-rgb-atlases-cpu-validated-awaiting-native`.

Reprodukcia používa Python s NumPy, Pillow a SciPy (zaznamenané NumPy 2.3.5 / SciPy 1.16.2). Spustiť z koreňa repozitára s novým výstupným adresárom; generátor odmieta prepísať existujúce odvodené atlasy:

```sh
python3 scripts/unreal/exterior-alpha-dilate.py \
  --source output/unreal/exterior-assets-20260926-r3/material-manifest.json \
  --output output/unreal/exterior-alpha-reproduction
```

Presný lokálne použitý interpreter bol `/Users/davidzita/.cache/codex-runtimes/codex-primary-runtime/dependencies/python/bin/python3 -B` s `PYTHONPATH=/tmp/dom-exterior-alpha-deps`. Tento dočasný adresár nie je trvalý dependency lock ani súčasť repozitára; pri neskoršej reprodukcii treba obnoviť zaznamenané balíky v samostatnom prostredí.

Pre nový balík treba explicitne použiť odvodený materiálový manifest a znovu overiť jeho natívne `inputFiles`. Samotná existencia derivácie neznamená, že ju používa otvorený Unreal balík.

## Reprodukcia bez zmeny zmrazených vstupov

Exportéry sú zatiaľ v **Git-ignorovanom `output/`** a odvodzujú koreň z vlastnej cesty. R2 navyše očakáva vedľa seba adresár presne pomenovaný `exterior-assets-20260926-r1`. Nie sú to ešte prenosné kanonické CLI nástroje.

1. Skopírovať obe celé knižnice do nového pracovného koreňa; zachovať ich názvy súrodeneckých adresárov. Zdrojové súbory porovnať s uloženým `asset-manifest.json`. Pre presnú reprodukciu použiť uložené zdroje; živé API môže medzitým vrátiť inú revíziu.
2. Pracovné materiálové manifesty majú absolútne cesty: zmeniť iba ich pracovné kópie na nový koreň a znova overiť SHA256 máp. Recepty sú archivované JSON; úplný generátor všetkých deviatich receptov zatiaľ neexistuje.
3. V pracovných kópiách spustiť Blender `--background --python <súbor>` v poradí: **R1 `export-plants.py` → R1 `export-trees.py` → R2 `export-composites.py` → R2 `export-green-grass.py`**. Posledný krok dopĺňa Bermuda trsy. `export-composites.py` resetuje R2 zoznam na zachované R1 role a nové kríky/podsadbu, preto poradie záleží.
4. Spustiť `python3 <pracovné-R2>/verify-glb.py`. Kontroluje GLB a mapové SHA256, uzly, sloty, LOD, UV0, normály, tangenty a natívne hranice. **Zapisuje `asset-validation.json`**, preto ho nepúšťať do zmrazenej knižnice.
5. Náhľady: Blender `preview-runtime.py`, potom `preview-green-grass.py` opravujúci zdrojový render border trávy. Výsledky sú Blender/Cycles, nie Unreal QA. Nové exporty dostať do nového izolovaného Unreal výstupu a znovu overiť import/reload, Shipping a natívne zábery; staré package hashe sa na ne nevzťahujú.

Pre R3 pokračovať iba v novej pracovnej kópii s dostupnými R1/R2 zdrojmi:

1. `acquire.py` overí/doplní Grass Medium 01 a Periwinkle; presnú reprodukciu založiť na archivovaných mapách a modeloch.
2. Blender `--background --python export-ornamentals.py` vytvorí tri nové GLB a aditívny manifest.
3. `python3 orthogonalize-tangents.py` ortogonalizuje tangenty Gram–Schmidtom a upraví hashe iba nových GLB. Zachová handedness, pozície, normály, UV a topológiu; zapisuje `tangent-repair-receipt.json`.
4. `python3 verify-glb.py` a `python3 verify-ornamental-basis.py` zapíšu reporty. Posledný kontroluje 21 nových LOD / 753 623 vertexov; maximálne absolútne `N·T` je pod 4,7e−8. Zriedkavé orientačné výnimky zdrojových plátkov sú spočítané, nie zamaskované.
5. Blender `--background --python preview-ornamentals.py` vytvorí `ornamental_grass-preview.png`, `ornamental_white-preview.png` a `ornamental_pink-preview.png`. Ide o neupravené Blender/Cycles náhľady zdrojového shadera, nie natívny Metal výsledok.

R4 `output/unreal/exterior-garden-20260926-r4/derive-garden.py` používa hashovo pripnutý zdrojový OBJ, R3 manifest, pôvodné card identity a deterministické spoločné rozloženie na 2 cm sieti. Vyžaduje NumPy a Shapely; použitý interpreter je `output/unreal/exterior-tools-py312-20260926/bin/python`. Pri reprodukcii skopírovať skript do nového súrodeneckého výstupu a jeho vstupné cesty explicitne overiť. Existujúci `garden-plan.json` odmietne prepísať. Mierka je bezrozmerná; všetky geometrické odstupy sú centimetre, nie pixely.

Nová online akvizícia používa v R1 `acquire.py` a `acquire-tree.py`, v R2 `acquire.py` a `acquire-grass.py` (Python 3 + curl). Akvizičné skripty obnovujú metadáta/manifesty; R1 stromový skript navyše očakáva existujúci materiálový manifest. Nepredstavujú samostatný čistý build od nuly. Reexport s inou verziou Blenderu nemusí mať totožné GLB bajty, aj keď prejdú geometrické kontroly.

## Navrhované presunutie do kanonických skriptov

Presun sa týmto dokumentom **nevykonal**. Nasledujúce zdroje treba po parametrizácii uchovať v Gite; tabuľka je presný návrh názvov pod `scripts/unreal/exterior-assets/`:

| Existujúci súbor | Navrhovaný kanonický názov |
| --- | --- |
| R1 `acquire.py`, `acquire-tree.py` | `acquire-r1-plants.py`, `acquire-r1-tree.py` |
| R1 `export-plants.py`, `export-trees.py` | `export-r1-plants.py`, `export-r1-trees.py` |
| R2 `acquire.py`, `acquire-grass.py` | `acquire-r2-plants.py`, `acquire-r2-grass.py` |
| R2 `export-composites.py`, `export-green-grass.py` | `export-r2-composites.py`, `export-r2-green-grass.py` |
| R3 `acquire.py`, `export-ornamentals.py` | `acquire-r3-ornamentals.py`, `export-r3-ornamentals.py` |
| R3 `orthogonalize-tangents.py`, `verify-ornamental-basis.py` | `orthogonalize-tangents.py`, `verify-ornamental-basis.py` |
| R3 `inspect-provider-materials.py`, `preview-ornamentals.py` | `inspect-ornamental-materials.py`, `preview-ornamentals.py` |
| Garden R4 `derive-garden.py` | `derive-garden-composition.py` |
| R2 `verify-glb.py` | `verify-glb.py` |
| R2 `inspect-source-materials.py`, `inspect-additional-materials.py` | `inspect-source-materials.py`, `inspect-additional-materials.py` |
| R1 `preview-tree.py`; R2 `preview-runtime.py`, `preview-green-grass.py` | `preview-tree.py`, `preview-runtime.py`, `preview-green-grass.py` |

Pred presunom oddeliť explicitné source/dependency/output korene a cestu validačného reportu, nahradiť pevný súrodenecký R1 adresár argumentom, pridať odmietnutie prepísania zmrazeného výstupu a pripnúť verziu Blenderu. Archivované recepty a zdrojové locky treba preniesť ako verziované vstupy; online akvizícia ich nesmie potichu obnovovať. Zdieľané exportné funkcie oboch R2 skriptov následne zlúčiť bez zmeny výslednej geometrie.

## Dôkaz kvality

`asset-validation.json` R2 prešlo pre 28 variantov / 84 LOD / 9 receptov, R3 pre 35 variantov / 105 LOD / 12 receptov. Natívny import/reload a Shipping sú technické dôkazy; samy nepotvrdzujú vizuálne prijatie. Autoritou pre obrazy a výkon sú konkrétne `qa/**/summary.json`, `runtime.json` a neupravené `capture.png` v `output/unreal/exterior-validation-20260926-r1/`.

Garden R4 `independent-world-audit.json` nezávisle prečítal GLB pozície: 36 world LOD boxov, 288 rohov a 66 párov. Minimálny odstup koreňov je 82,292 cm, celých konzervatívnych korún 2,292 cm, skutočných world boxov 7,397 cm; odstup celej koruny od záhonovej hrany 14,01 cm, nášľapov 14,543 cm a bazéna/terás 56,5 cm. Kolízie: nula. Výšky pri rovnomernej mierke sú 50–75,71 cm; tri korene mimo záhonov majú presné pôvodné XY. Najväčší vedomý presun v existujúcom záhone je 121,696 cm. Celých 12 primárnych inštancií predstavuje 773 990 / 355 480 / 259 580 trojuholníkov pri spoločnom LOD0 / LOD1 / LOD2 pred cullingom; nejde o počet skutočne viditeľných trojuholníkov jedného frame.

`scripts/unreal/exterior-gallery.mjs` číta generické `exterior-r*-rejected-review.json`, viaže ich na SHA256 série a balíka a zobrazuje „zamietnutý pokus“ so skutočnými nálezmi. Samostatné `exterior-r*-review.json` smie vzniknúť až po natívnej vizuálnej kontrole. Úspešný technický import, názov fázy `after` ani `final` nie sú potvrdením fotorealizmu. Ani korektné proporcie R4 a nulové geometrické kolízie samy nedokazujú prijateľný obraz.
