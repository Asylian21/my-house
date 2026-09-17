# Výškový základ dokumentácie C/B/B

Stav k 14. 09. 2026: **podmienený výškový podklad, nevydané na realizáciu**. Tento záznam oddeľuje novú spoločnú referenciu ulice od zachovanej nuly modelu a pôdorysu. Nemení geometriu, osi, otvory, skladby ani osadenie C/B/B v pôdoryse. Pripravuje podmienený návrh vstupu a postup určenia podlahy; konečnú hotovú podlahu ani založenie neurčuje.

## Nový vstup stavebníka

Stavebník určil spoločnú nulu v najvyššom bode ulice pri rohu pracovne a oznámil údaj od geodeta **184,2 m**. Výškový systém Bpv, presné XY/číslo bodu a protokol merania zatiaľ nie sú potvrdené. Výška hotovej podlahy voči tomuto bodu nie je určená. Pre výpočty sa tá istá oznámená hodnota zapisuje ako 184,200 m; tri desatinné miesta neznamenajú doloženú milimetrovú presnosť merania.

Identita bodu ako najvyššieho povrchu komunikácie pred posudzovaným domom je zatiaľ údaj stavebníka. Bod nemožno bez XY zakresliť do ľubovoľného rohu parcely a vydať ako geodeticky vytýčený. Bod na obrubníku, historický terén a povrch vozovky nie sú automaticky tá istá výška.

| Označenie | Význam | Aktuálna hodnota |
| --- | --- | --- |
| R0 | Spoločná referenčná nula na ulici | R = ±0,000; oznámená absolútna výška 184,2 m, systém nepotvrdený |
| M0 | Zachovaná modelová nula; hotová podlaha 1. NP v existujúcom pôdoryse | M = ±0,000; absolútna výška neznáma |
| ΔFFL | Výška hotovej podlahy nad R0; kladná smerom nahor | Neznáma, nesmie sa predvoliť 0 |
| ZM | Súradnica konkrétneho prvku nad M0 | Z existujúceho modelu, v mm |
| ZR | Výška toho istého prvku nad R0 | ZM / 1 000 + ΔFFL, v m |

Výrazy s absolútnou výškou nižšie platia v rovnakom výškovom systéme ako oznámených 184,2 m. Označenie „m Bpv“ je prípustné až po potvrdení systému geodetom. Samotný rozdiel výšok v metroch možno počítať bez premenovania systému.

## Primárne pravidlá a ich referencia

[Aktuálny register Mesta Mikulov](https://www.mikulov.cz/obcan/platna-dokumentace-brezi-up) pri kontrole 14. 09. 2026 uvádza úplné znenie ÚP Březí po zmene č. 3 s účinnosťou od 22. 05. 2026. Predchádzajúce mapové porovnanie parcely 6012/26 určilo Z.7/SV, zónu C a výškovú triedu 4,5 m; ide o interpretáciu oficiálnych máp, nie samostatné rozhodnutie úradu. [Hlavný výkres](https://www.mikulov.cz/data/content_files/832/1b-hlv-1.pdf), [výkres urbanistickej kompozície I.f](https://www.mikulov.cz/data/content_files/832/1f-urbanisticka-kompozice.pdf).

[ÚP, textová časť](https://www.mikulov.cz/data/content_files/831/brezi-up-oop-uz.pdf#page=35), I.F.3, tlačená strana 34 / PDF strana 35, meria prípustnú výšku na uličnej strane od najvyššieho povrchu komunikácie pred domom po spodnú úroveň rímsy. Krátky doslovný úryvok: „po spodní úroveň římsy“. Pre tento výpočet sa používa táto konkrétna textová definícia. Legenda výkresu I.f a všeobecná definícia v texte uvádzajú upravený terén; tento rozdiel formulácií sa nesmie zatajiť pri konečnom posúdení. Zóna C na tlačenej strane 35 stanovuje pre hlavnú obytnú hmotu sedlovú strechu so sklonom 25–40°. **4,5 m nie je limit hrebeňa.**

[Register územných štúdií](https://www.mikulov.cz/obcan/uzemni-studie-brezi) naďalej obsahuje Z7/Z22. [Jej text, PDF strana 2](https://www.mikulov.cz/data/content_files/731/textova-cast-souhlas-obce-stavebni-cara-5m.pdf#page=2), uvádza aj rímsu najviac 4,5 m nad podlahou 1. NP, podlahu najviac 0,5 m nad upraveným terénom a jeho výškovú väzbu na najbližší obrubník. Tieto podmienky treba overiť samostatne; z oznámenej výšky jedného bodu vozovky sa nedá odvodiť výška celého upraveného terénu ani obrubníka. Dodatok na PDF strane 4 mení uličnú čiaru na 5 m iba pre radové domy; nepridáva novú výškovú referenciu.

## Podmienené výškové vzťahy

Ak R0 skutočne zodpovedá posudzovanému najvyššiemu bodu vozovky s výškou 184,200 m, horná prípustná úroveň **spodnej uličnej rímsy** podľa textového kritéria ÚP je:

```text
H_R0 = 184,200 m
H_rímsa,max = H_R0 + 4,500 = 188,700 m
H_FFL = H_R0 + ΔFFL = 184,200 + ΔFFL
H_prvok = H_R0 + ΔFFL + ZM / 1 000
```

188,700 m je podmienený regulačný strop spodnej rímsy. Nie je to výška stropnej konštrukcie, podhľadu ani schválená návrhová kóta rímsy. Nejde ani o automatické oprávnenie zdvihnúť dom až po tento limit.

| Prvok zo zachovaného modelu | ZM nad podlahou | Výška nad R0 | Podmienená absolútna výška |
| --- | --- | --- | --- |
| Hotová podlaha 1. NP | 0 mm | ΔFFL | 184,200 + ΔFFL m |
| Okraj hlavného vonkajšieho strešného obalu | 3 125 mm | 3,125 + ΔFFL m | 187,325 + ΔFFL m |
| Hrebeň modelových strešných rovín | 5 560 mm | 5,560 + ΔFFL m | 189,760 + ΔFFL m |
| Najvyšší vnútorný podhľad obývačky | 4 850 mm | 4,850 + ΔFFL m | 189,050 + ΔFFL m |
| Regulačný strop spodnej uličnej rímsy | 4 500 − 1 000 × ΔFFL mm | +4,500 m | 188,700 m |

ΔFFL je vo všetkých výrazoch v metroch. Skutočné prevýšenie spodnej rímsy nad M0 označme hR. Presná kontrola je `ΔFFL + hR ≤ 4,500 m`. Ak sa rozdiel spodnej rímsy oproti modelovej strešnej hrane označí `δR = hR − 3,125 m`, rovnaká podmienka znie:

```text
ΔFFL + 3,125 + δR ≤ 4,500
ΔFFL ≤ 1,375 − δR
```

Len pri výslovne potvrdenom stotožnení spodnej rímsy s modelovou hranou, teda δR = 0, vychádza z tohto jediného kritéria ΔFFL ≤ 1,375 m a H_FFL ≤ 185,575 m. **Táto podmienka nie je návrhom podlahy ani dôkazom celkového súladu.** Podmienka štúdie pre podlahu zostáva `H_FFL − H_upravený_terén ≤ 0,500 m`; neznáma výška terénu sa nesmie nahradiť 184,200 m.

## Doplnené zadanie: drevené stropy, odkladacia povala a vstup

Stavebník následne potvrdil drevené stropy, povalu iba na odkladanie a požiadavku aspoň jedného schodu do domu. Výšku podlahy má navrhnúť projektant z nameraných podkladov a konštrukčnej skladby; stavebník ju nemusí určovať sám. Odkladacia povala nie je obytné podkrovie, ale jej podlaha, drevené stropy, prístup a únosnosť stále potrebujú návrh pre určený spôsob skladovania. Táto informácia sama neurčuje výšku prízemnej podlahy ani rozmery nosných prvkov.

**Návrhový cieľ pre vstup:** jeden riadny výškový stupeň, prípadne dva rovnaké stupne, ak to vyjde zo základov a terénu. Základný [priestorový návrh D2](/Users/davidzita/www/dom/docs/construction-entry-basis.md) používa nominálne `h = 150 mm` a podestu 1 500 × 1 500 mm v existujúcom koridore `SITE-ENTRY`. Nejde o schválené stavebné kóty ani úplné normové posúdenie. Jeden stupeň znamená jedno prevýšenie priamo na hornú podestu; nepridáva sa k nemu druhý samostatný nášľap. Dva stupne sú prípadná alternatíva s dvoma prevýšeniami a jednou medzistupnicou, ktorej šírka sa ešte musí navrhnúť. Rozmery a poloha podesty musia umožniť bezpečné státie, otvorenie dverí a odvodnenie. Schod sa nemá vytvoriť ako vysoký prah samotných vstupných dverí.

Rozhodnutie o jednom alebo dvoch stupňoch sa uzavrie spolu s výškou podlahy. Prístupový chodník, dolná úroveň schodov, horná podesta, prah a ulica sú samostatné úrovne. R0 pri rohu pracovne sa nesmie automaticky stotožniť so žiadnou z nich. Pred domom sa pri tomto návrhu zostáva v rozsahu najviac troch stupňov podľa [štúdie Z7/Z22, PDF strana 2](https://www.mikulov.cz/data/content_files/731/textova-cast-souhlas-obce-stavebni-cara-5m.pdf#page=2). Podmienený návrh jedného alebo dvoch stupňov sám nepotvrdzuje súlad zvyšku vstupu.

### Overenie aktuálnych predpisov pre schody

[MMR potvrdzuje účinnosť novely 97/2026 od 01. 07. 2026](https://mmr.gov.cz/cs/ministerstvo/stavebni-pravo/pravo-a-legislativa/novy-stavebni-zakon/vyhlasky/novela-vyhlasky-c-146-2024-sb-%2C-o-pozadavcich-na-v). [Vyhlásené znenie novely](https://www.zakonyprolidi.cz/media2/file/2606/File83965.pdf?attachment-filename=Sb_2026_97_PZZ.pdf), čl. I body 38–40 na strane 5 a bod 75 na stranách 10–11, zrušilo pôvodný § 31 ods. 2 a nahradilo prílohu č. 4. Staré číselné minimum nášľapu 300 mm / 275 mm pre RD z tejto prílohy preto nemožno bez určenia právneho režimu citovať ako aktuálnu požiadavku. Pôvodná požiadavka rovnakých návrhových výšok stupňov a v priamom ramene aj šírok ostáva v prečíslovanom § 31 ods. 3. Čl. II na strane 14 však zachováva predchádzajúci režim pri dokumentácii pre povolenie spracovanej pred účinnosťou; jeho uplatnenie na terajšiu zmenu C/B/B sa z existencie archívneho projektu nepredpokladá. PDF je kópia vyhláseného aktu na zrkadle; [primárny záznam e-Sbírky](https://e-sbirka.gov.cz/sb/2026/97/2026-07-01?f=146/2024&zalozka=text) je prepojený aj zo stránky MMR.

[Katalóg Českej agentúry pre štandardizáciu](https://csnonline.agentura-cas.cz/Detailnormy.aspx?k=85172) pri kontrole uvádza ČSN 73 4130:2010 a jej zmeny [Z1 z roku 2018](https://csnonline.agentura-cas.cz/DetailZmeny.aspx?k=504157) a [Z2 z roku 2024](https://csnonline.agentura-cas.cz/DetailZmeny.aspx?k=519683), bez vyplneného ukončenia platnosti. Verejný náhľad neobsahuje úplné rozmerové ustanovenia; [sponzorovaný prístup ČAS](https://sponzorpristup.agentura-cas.cz/) vyžaduje registráciu. Preto sa 150 mm používa ako nominálny návrhový cieľ a nevyhlasuje sa normou predpísaná dvojica 150/300 mm. Pred vydaním detailu sa musí overiť celé príslušné znenie vrátane podesty, napojenia dverí, stupňov a povrchu za mokra. Toto overenie je úlohou návrhu, nie požiadavkou, aby si stavebník zvolil rozmery alebo podlahu sám.

### Rovnica od existujúceho pásu po hotovú podlahu

V tejto konštrukčnej rovnici sú dĺžky a výšky v **milimetroch**, zhodne s klientskym záznamom. Výšky `z` sú rozdiely voči R0; kladné smerom nahor. `ΔFFL_mm = 1 000 × ΔFFL`, kde samotné `ΔFFL` v predchádzajúcej územnej kontrole ostáva v metroch.

| Symbol | Význam | Stav |
| --- | --- | --- |
| zE | Horné líce už existujúceho spodného betónového pásu nad R0 | Zamerať; uvádzaná hĺbka 600 mm pod miestnym terénom túto výšku neurčuje |
| u | Výška požadovaného nového horného pásu od jeho spodku po vrch | 600 mm podľa zadania, staticky nepotvrdené |
| j | Horné líce dosky mínus horné líce nového horného pásu | Určí návrh styku; zatiaľ neznáme |
| tD | Hrúbka nosnej dosky | Požadovaný rozsah 150–200 mm; konkrétna hodnota nevybraná |
| p | Celá skladba od vrchu nosnej dosky po hotový nášľap | Neznáma; musí zahŕňať všetky navrhnuté vrstvy aj priestor potrebný pre rozvody |
| zA | Hotová dolná prístupová plocha pri prvom stupni nad R0 | Navrhnúť z miestneho obrubníka a napojenia chodníka |
| zP | Hotová podesta na hornej hrane posledného stupňa nad R0 | Nie výška pri dverách; treba zohľadniť spád podesty |
| d | Hotová vnútorná podlaha mínus podesta pri dverách | Z detailu vstupu; nepredvoliť nulu |
| L, s | Hĺbka podesty a pozdĺžny sklon smerom von | L = 1 500 mm ako návrh, s v mm/mm zatiaľ neznáme |
| n, h | Počet prevýšení a rovnaká výška jedného stupňa | Návrhový cieľ n = 1 alebo 2, nominálne h = 150 mm |
| v | Súčet výškových prírastkov po povrchu prípadných medzistupníc smerom k domu | Pri jednom stupni v = 0; pri dvoch sa dopočíta z povrchového spádu medzistupnice |
| zT | Posudzovaný upravený terén nad R0 | Viazaný na zameraný najbližší obrubník podľa Z7; neznámy |

Ak spodok nového horného pásu dosadne priamo na horné líce existujúceho pásu, platí:

```text
z_vrch_nového_pásu = zE + u
z_vrch_dosky = zE + u + j
z_spodok_dosky = zE + u + j − tD
ΔFFL_mm = zE + u + j + p
zP = zA + n × h + v
ΔFFL_mm = zP + s × L + d

zE + 600 + j + p = zA + n × h + v + s × L + d
H_FFL [m] = 184,200 + ΔFFL_mm / 1 000

Základný návrh jedného stupňa:
ΔFFL_mm = zE + 600 + j + p = zA + 150 + s × 1 500 + d
```

Ak sa medzi existujúci a nový pás navrhne ďalšia vyrovnávacia vrstva, musí sa jej skutočná hrúbka pridať do rovnice. Pri doske ležiacej celou hrúbkou nad vrchom horného pásu je `j = tD`; vtedy `ΔFFL_mm = zE + 600 + tD + p`. Ak je vrch dosky v rovine vrchu pásu, je `j = 0` a `ΔFFL_mm = zE + 600 + p`. Tieto dva konštrukčné prípady sa nesmú zameniť. Požadované 600 mm vysoké rebrá sa nepripočítavajú ďalšími 600 mm, ak sú súbežnou súčasťou tej istej výškovej zóny.

Požiadavka vedenia vody a odpadu nad nosnou doskou bez dodatočného vŕtania sa musí premietnuť do `p` a do vopred navrhnutého vývodu z domu. Potrebný priestor pre odpad závisí od trasy, priemeru, výškovej polohy vývodu a spádu; nemožno ho nahradiť nulovou alebo svojvoľne tenkou vrstvou. Drevené stropy a spôsob využitia povaly nemenia túto rovnicu.

### Rozhodnutie o návrhu R +0,300 m

**R +0,300 m, teda podmienených 184,500 m, ostáva iba nominálnym porovnávacím scenárom. Neustanovuje sa ako pracovná stavebná nula a neukladá sa namiesto `null`.** Nie je doložené, že sa pod túto výšku zmestí požadovaný horný pás, doska a rozvody nad doskou. Pri `j = tD` by scenár vyžadoval `zE = −300 − tD − p` v mm, čiže pri doske 150 mm `zE = −450 − p` a pri doske 200 mm `zE = −500 − p`. Je to podmienka kompatibility, nie výsledok merania.

Ani dva stupne po 150 mm neurčujú automaticky podlahu R +0,300 m: vyžadujú `ΔFFL_mm = zA + 300 + v + s × L + d`. Pre jeden stupeň je to `ΔFFL_mm = zA + 150 + s × L + d`. Z toho vyplýva, že najprv treba spojiť existujúcu betónovú úroveň s budúcim prístupom, až potom vydať kótu podlahy a stupňov. Ak sa v porovnaní použije d = 20 mm a s = 2 %, pri jednom stupni a L = 1 500 mm vyjde rozdiel podlahy voči prístupu 200 mm; obe tieto doplnkové hodnoty však ostávajú iba podmieneným príkladom z podkladu D2.

Samostatné výškové kontroly sú `ΔFFL_mm − zT ≤ 500 mm` podľa Z7 a `ΔFFL + hR ≤ 4,500 m` podľa uvedeného textového kritéria ÚP, kde `ΔFFL` a `hR` sú naďalej v metroch. Pre scenár R +0,300 m by prvá nerovnosť vyžadovala `zT ≥ −200 mm`; nejde o možnosť ľubovoľne naviezť terén, pretože ostáva jeho väzba na najbližší obrubník. Matematických 1,375 m z kontroly modelovej strešnej hrany preto nie je prípustným návrhovým cieľom zdvihu podlahy.

**Od stavebníka treba iba merateľný existujúci podklad:** výšky horného líca existujúceho betónového pásu v rohoch a stykoch, ktoré zachytia jeho nerovnosti, a horného líca najbližšieho uličného obrubníka pri zamýšľanom vstupe, všetko voči tomu istému označenému bodu R0. Súčasne sa identifikuje tento referenčný bod a jeho výškový systém. Nie je potrebné, aby stavebník sám vybral FFL. Z týchto meraní projektant uzavrie styk pásu a dosky, úplnú podlahovú skladbu, chodník a podestu; následne vypočíta FFL, jeden alebo dva rovnaké stupne a overí obidve územné výškové podmienky. Neznáme návrhové veličiny `j`, `tD`, `p`, `d`, `s` a prípadné `v` sú pracovné úlohy návrhu, nie vymyslené merania.

## Čo presne znamená modelových +3,125 m

`lib/twin-site.ts` definuje `HOUSE.eavesElevationMm = 3125` a `ridgeElevationMm = 5560`; `lib/twin-active-house.ts` ich dedí. `lib/twin-roof.ts` používa tieto čísla priamo ako Z vrcholov spojených strešných rovín. Ide o výšky geometrického obalu. Samostatne určený realizačný detail spodnej uličnej rímsy s materiálovými vrstvami zdroj neposkytuje.

`lib/babylon-scene.ts:buildJoinedRoof()` vytvára vizualizačný spodný povrch 70 mm pod strešnou rovinou; pri odkvape teda M +3,055 m. `buildRoofEdges()` kreslí predný žľabový vizualizačný profil s dolnou úrovňou M +3,020 m a výškou 105 mm, čiže hornou úrovňou M +3,125 m. Funkcia `boxAtPlan()` potvrdzuje, že parameter 3,02 znamená spodok kvádra. Ani −70 mm, ani −105 mm nie je schválená odchýlka δR. Nesmú sa použiť na navýšenie prípustnej podlahy bez návrhu a identifikácie skutočne posudzovanej rímsy.

**Ani +5,560 m nie je výška najvyššieho prvku renderera alebo doložená výška dokončenej strechy.** Kontrola bielych šikmých profilov záhradného portálu P04 odhalila horný vrchol M +5,779277 m, teda 219,277 mm nad hrebeňom modelovej strešnej roviny. Vyplýva z rotovaného 180 mm profilu, jeho predĺženia pri vrchole a zdvihu v `lib/babylon-scene.ts` pri tvorbe bieleho rámu. Výškový prevod tohto konkrétneho modelového vrcholu je podmienene `189,979277 + ΔFFL m`; ide o matematiku vizualizačného prvku, nie realizačnú kótu. Bočná projekcia profilu presahuje príslušnú krajnú líniu o 51,399 mm, jeho čelná rovina je Y 22 105 mm a vrcholový kryt siaha po Y 22 107 mm. Samostatná oprava 50 mm presahu hlavnej strešnej roviny tento dekoratívny profil neodstraňuje. Jeho konečný detail a obálku dokončenej strechy treba uzavrieť osobitne; model obsahuje aj ďalšie prvky nad strechou, napríklad dymovod.

Historická hodnota `HOUSE.datumElevationM = 184` v `lib/twin-site.ts` nie je nový vstup geodeta a neurčuje dnešnú hotovú podlahu. `SOURCES.terrain` v tom istom súbore uvádza 184,087 m Bpv z historického DMR 5G. Modelové hladiny vozovky −0,115 m a trávnika −0,065 m v `lib/twin-viewport-contract.ts` slúžia vizualizácii. Žiadnu z týchto hodnôt nemožno použiť na dopočítanie ΔFFL.

## Audit pred migráciou a pravidlá prevodu

Audit kódu pred prvou migráciou 14. 09. 2026 zistil nižšie uvedený stav. Tabuľka zachováva východisko opravy; súčasný implementovaný stav je zaznamenaný pod ňou.

| Miesto | Správanie pred migráciou | Potrebné rozlíšenie |
| --- | --- | --- |
| `source.tsx:drawingSource()` | Importuje geometriu, vrátane zdedeného `house.datumElevationM`; samostatný nový výškový podklad nemá | Pripojiť osobitné údaje R0 a stav ΔFFL, bez prepisu geometrie |
| `render.mjs:level()` a `spot()` | Formátujú priamo modelové Z; nepoznajú referenciu | Odlišovať modelovú kótu M, spoločnú kótu R a absolútnu výšku |
| `render.mjs:legend()` a `facadeSheet()` | Text ±0,000 = podlaha; výška 3 125 má názov rímsa | Uviesť M0 = podlaha, R0 = ulica; 3 125 pomenovať strešná hrana modelu |
| `render.mjs:sectionSheet()` | Vykresľuje modelové Z, podlahu pri Z = 0 a pri B-B označuje 3 125 ako rímsu | Zachovať polygóny; doplniť prevod a opraviť význam názvu |
| `render.mjs:planningSheet()` / situačné poznámky / R05 | Chýbajúcu referenciu opisujú všeobecne; 3,125 m priamo spájajú s rímsou | Zapracovať nový oznámený bod, neznáme ΔFFL a neznáme hR |
| `app/koncept-2d/export-sheet.tsx` | Pôvodný pôdorys v razítku, legende a miestnosti 1.01 používa ±0,000 = čistá podlaha | Pôvodný list ponechať; na doplnenej vrstve jednoznačne uviesť, že ide o M0 |

Odporúčaný dátový záznam oddelený od modelu má obsahovať `referencePoint` (opis, 184.2 m, `verticalSystem: null`, `xy: null`, údaj stavebníka z 14.09.2026), `floorOffsetFromReferenceMm: null` a `streetCorniceUndersideFromModelZeroMm: null`. `null` znamená chýbajúci vstup. Hodnota nula sa uloží iba po výslovnom určení nulového prevýšenia. Starý `house.datumElevationM` zostane historickým atribútom, z ktorého nový export absolútne výšky nepočíta.

Pri migrácii sa ponechajú všetky modelové súradnice a rozmery. Zmení sa výlučne spôsob označenia a prípadná odvodená premietacia transformácia výšok. Kým ΔFFL chýba, na listoch možno uvádzať `M +3,125; R = ΔFFL +3,125` a samostatný blok R0. Nemožno umiestniť numerickú čiaru R0 do modelového rezu ani regulačnú čiaru 188,700 m bez znalosti ich polohy voči podlahe.

Po určení ΔFFL je prevod `ZR_mm = ZM_mm + floorOffsetFromReferenceMm`; opačný prevod pre zakreslenie referenčnej úrovne je `ZM_mm = ZR_mm − floorOffsetFromReferenceMm`. Ak grafika ostane v modelových súradniciach, R0 sa kreslí na `ZM = −floorOffsetFromReferenceMm` a limit rímsy na `ZM = 4500 − floorOffsetFromReferenceMm`. Absolútne výšky musia na každom liste obsahovať aj identifikáciu potvrdeného výškového systému.

Nepridávať posun plošne do existujúcej funkcie `level()`: používa sa aj pri parapetoch, výrobných tabuľkách a relatívnych modelových detailoch. Šírky, výšky otvorov, parapety nad čistou podlahou, svetlé výšky, hrúbky vrstiev a všetky rozdielové kóty posun nemení. Ak sa zobrazujú dve referencie, každá musí mať M/R označenie; dva neodlíšené symboly ±0,000 na jednom liste sú neprípustne nejasné.

Nový dátový podklad musí vstúpiť do `model-snapshot.json` a zoznamu odtlačkov v `generate.mjs`. Kontrola má overiť nezmenenú pôdorysnú geometriu, rovnaké rozdielové výšky po prevode, neprítomnosť vymyslených čísel pri `null` a správne znamienko posunu. Následne treba vizuálne overiť obe A1 sady vrátane označenia pôvodnej pôdorysnej nuly.

## Stav po zapracovaní referencie do sady

Kontrola exportu 14. 09. 2026, PDF vytvorené o 17:10 CEST: sada má 24 listov vo farebnej aj čiernobielej verzii. `source.tsx` už pripája `CLIENT_BRIEF` a `elevationBasis()` zo súboru `scripts/construction-documentation/client-brief.ts`. Použitý názov údaja je `clientBrief.datum.finishedFloorAboveRoadMm`; v snímke modelu má hodnotu `null`. Odvodené `elevations.floor`, `roofEdge` a `ridgePlane` zachovávajú modelové Z, ale `aboveRoadMm` aj `absoluteM` ostávajú `null`. Číselný `absoluteBaseM` je iba konštantná časť symbolického výrazu s neznámym ΔFFL, nie konečná absolútna výška prvku.

Výškové značky nových pohľadov a rezov používajú prefix M. Razítka vysvetľujú R0, M0 a neznámy rozdiel; pôvodný pôdorys má samostatný dolný doplnok objasňujúci jeho zachované ±0,000. UP-01 uvádza podmienené výrazy a limit spodnej rímsy bez tvrdenia o výškovom súlade. Aktívna geometria strešnej roviny končí na Y 22 035 mm. Historický `house.roof.wingEndOverhangMm = 50` uložený v zdedenom objekte nie je aktívnym koncom tejto roviny; rozhodujú `roof.parameters.wingEndYmm` a `roofParameters.wingEndYmm` s hodnotou 22 035 mm, spolu s novou požiadavkou `clientBrief.roof.architecturalOverhangMm = 0`.

Vizuálne boli samostatne skontrolované PDF strany 1, 2, 17–21 a 24 oboch verzií po renderovaní pomocou `pdftoppm` pri 60 dpi. Nové vysvetlenie nuly, vzorce UP-01, tabuľky a označenia TZ-01 nemali zistené prekrytie alebo orez. Táto čiastková QA nepotvrdzuje stav ostatných strán ani splnenie realizačných požiadaviek. TZ-01 správne odlišuje nevykurovanú garáž 1.12, technickú miestnosť 1.07 a samotnú sprchovú plochu v 1.05; povalu uvádza nad plochými stropmi mimo otvorenej katedrály 1.03.

Pôvodný modelový výškový systém zostal zachovaný. Výškový súlad s ÚP zostáva otvorený do potvrdenia referenčného bodu, určenia ΔFFL, výšky terénu/obrubníka a skutočnej spodnej rímsy. Tento dokument ani podmienené čísla samy neurčujú konečné výškové osadenie.
