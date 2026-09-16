# Doska a rebrá na priebežne podopierajúcom zásype

**Overenie zdrojov: 16. 9. 2026.** Vstup používateľa: 100 mm C16/20, monolitické rebrá celkovej výšky 400 mm, miestna zhutnená hlina/piesok pod doskou **aj po celej dĺžke rebier**. Toto je hlavný model pre ďalšie posúdenie. Predošlé výpočty úplne nepodopretých polí nepredstavujú tento stav.

## 1. Odporúčané stručné vysvetlenie

> Počítame dosku aj rebrá s priebežnou podporou zhutneného zásypu. Zaťaženie preto odovzdávajú do zeminy priebežne; rebrá nemusia automaticky preklenuť celé rozpätia medzi obvodovými pásmi. Pre dosku 100 mm treba vyčísliť miestny ohyb, šmyk, trhliny a rozdielne sadanie pri konkrétnej tuhosti podpory. Údaj „zhutnené“ potvrdzuje zamýšľaný postup, ale neurčuje nameranú tuhosť ani únosnosť. Podmienený výpočet má ukázať, pri akých parametroch podložia a akej výstuži konštrukcia vyhovuje.

Ide o vlastný výklad pre tento dom, nie citáciu normy. Kvalitné priebežné podopretie je reálny nosný mechanizmus; netreba ho nahradiť hypotézou, že zemina chýba.

## 2. Winklerov model: význam a jednotky

[FHWA NHI-05-037, §5.4.6](https://www.fhwa.dot.gov/engineering/geotech/pubs/05037/05c.cfm) vysvetľuje vzťah medzi tlakom a poklesom a upozorňuje, že koeficient reakcie podložia závisí aj od rozmerov a tuhosti dosky/základu. Nie je samostatnou materiálovou konštantou zeminy. Viacvrstvový profil, sezóna a stav podložia ovplyvňujú jeho interpretáciu. Ide o odborný podklad pre mechaniku; jeho dopravné návrhové koeficienty nepreberáme ako české pravidlá rodinného domu.

Vlastný zápis modelu so zvislým posunom w kladným nadol:

- `p = ks · w`, ks v kN/m³, w v m, p v kPa. `1 MN/m³ = 1000 kN/m³ = 0.001 N/mm³`.
- Jednotlivá uzlová pružina pod plochou Ai: `Ki = ks · Ai` v kN/m. Sieťou sa mení Ki, nie automaticky ks.
- Rebro šírky b: `Kline = ks · b` v kN/m². Jeho reakcia na jednotku dĺžky je `r = Kline · w` v kN/m.
- Zemina bez kotvenia neprenáša ťah. Pri počiatočnom úplnom kontakte je jednostranný model `p = ks · max(w,0)`; pri sadnutí podložia wg sa používa relatívny posun `max(w−wg,0)`. Záporné pružinové reakcie v bilaterálnom výpočte znamenajú potrebu kontakt prepočítať.

**Ks, E, Eoed, Ev2 a percentá Proctora sú rozdielne veličiny.** Napríklad Ev2 má jednotku MPa, ks MPa/m a Proctor je pomer suchých objemových hmotností. Kladný výsledok skúšky jedného ukazovateľa nemožno bez zdôvodnenia dosadiť namiesto druhého.

## 3. Rovnice a analytická kontrola programu

Primárny učebný podklad [NPTEL: Beam on Elastic Foundation, kap. 11](https://archive.nptel.ac.in/content/storage2/courses/105106049/lecnotes/mainch11.html), rovnice 11.1, 11.7–11.10 a 11.19–11.25, odvodzuje rovnováhu prútového prvku na pružnej podpore. V jeho zápise je pružinový parameter **líniový**; pri používaní plošného ks treba pridať b.

Pre konštantné EI, vlastná konvencia znamienok:

`EI · w'''' + Kline · w = qline(x)`.

Pre dosku konštantnej tuhosti analogická rovnováha:

`D · ∇⁴w + ks · w = q(x,y)`, `D = Ec h³/[12(1−νc²)]`.

Pri E v kN/m², I v m⁴ a h v m má EI jednotku kNm² a D jednotku kNm. Plošná rovnica nie je náhradou prútovej s dosadením h namiesto I.

Analytický test nekonečného prúta s osamelou silou P:

`β = [Kline/(4EI)]^(1/4)` v 1/m,

`w(x) = Pβ/(2Kline) · exp(−β|x|) · [cos(β|x|)+sin(β|x|)]`,

`|M(0)| = P/(4β)`, `|V(0±)| = P/2`.

Podklad výslovne uvádza zmenu znamienka reakcie ďalej od sily. Preto samotné analytické riešenie osamelej sily na pružinách schopných ťahu nie je automaticky riešením zeminy. Overiť celkový kontakt po pridaní vlastnej tiaže a ostatných zaťažení; podľa potreby jednostranné pružiny. Konce skutočného rebra, uzly a zmena podpory môžu ovplyvniť výsledok, takže nekonečný prút je kontrolný príklad programu.

[PEER 2005/04, Harden, Hutchinson, Martin, Kutter](https://peer.berkeley.edu/publications/2005-04) je primárny experimentálne kalibrovaný výskum nelineárnych Winklerových modelov pre plytké základy na piesku aj íle. Podporuje potrebu modelovať odtrhnutie a trvalé deformácie, ale neposkytuje parametre tejto parcely; seizmické skúšky nepreberáme ako jej statický dôkaz.

### Kontroly numerického modelu — vlastný odporúčaný postup

1. Reakcie zeminy a obvodu musia vyrovnať súčet zaťažení aj momenty. Pri doske/rebre spoločnú kontaktnú plochu, betón a zaťaženie počítať iba raz.
2. Zjemniť sieť a porovnať posuny i rozhodujúce sily. Bodové a líniové zaťaženie nahradiť skutočnou kontaktnou plochou, kde sa kontrolujú lokálne špičky.
3. Pri rovnomernom zaťažení homogénnej podpory a bez obmedzujúcich okrajov musí vyjsť rovnomerný posun `w=q/ks` a nulová krivosť. Tým sa kontroluje program; nie úplný dom.
4. Overiť uvedený analytický príklad osamelej sily; oddelene skúšať tlakový kontakt.
5. Zahrnúť rôznu tuhosť starých pásov a nového zásypu, miestne mäkšiu **stále podopierajúcu** zónu a skutočné napojenie monolitických rebier. Tuhý obvod bez sadania nie je automaticky overený vstup.
6. Pri EC2 kontrole posudzovať oba smery a znamienka ohybu, šmyk/pretlačenie, kotvenie, trhliny a dlhodobú tuhosť. Neprasknutý EcIg nie je konečný SLS model tenkej železobetónovej dosky.

## 4. Užitočný parametrický raster

**Vlastná citlivostná voľba, nie hodnoty namerané na pozemku:** ks=5 / 10 / 20 / 50 MN/m³. Ide o desaťnásobný rozsah na odhalenie citlivosti, zosúladený s aktuálnym výpočtom; jednotlivé hodnoty nepredstavujú triedy zeminy ani doloženú dolnú a hornú hranicu miestnej hliny/piesku. Kým sa ks neurčí pre danú skladbu, nevyhlásiť variant za vyhovujúci iba preto, že vyhovel všetkým štyrom číslam.

Kontrolná aritmetika rovnomerne zaťaženej podpory:

| Tlak / ks [MN/m³] | 5 | 10 | 20 | 50 |
|---|---:|---:|---:|---:|
| 6.5 kPa: w=q/ks [mm] | 1.300 | 0.650 | 0.325 | 0.130 |
| 100 kPa: w=q/ks [mm] | 20.000 | 10.000 | 5.000 | 2.000 |

Tieto posuny sú iba deformáciou zvolenej pružnej podpory. Nezahŕňajú dodatočné sadanie z konsolidácie, premočenia, zmien objemu ani nesprávne zvolenú hĺbku profilu. Pod rebrami môžu byť tlaky omnoho vyššie než 6.5 kPa od podlahy; treba použiť výsledné reakcie od konkrétnych stien a zariadení.

Pridať raster relatívnej tuhosti mäkšej zóny 0.5ks a prípadne 0.2ks pri zachovaní kontaktu, samostatne rôzne tuhosti starého obvodu. Šírky/miesta zón označiť ako predpoklad. Praktickým výsledkom je požadované minimum overiteľnej podpory a prípustná nerovnomernosť, nie iba zelené políčko pri zvolenom ks.

Pre homogénnu tenkú vrstvu v 1D tlaku vyplýva z mechaniky `s=pH/Eoed` a teda `k_1D=Eoed/H`; vrstvy sa skladajú poddajnosťami `1/k_1D=Σ(Hj/Eoed,j)`. Je to obmedzený kontrolný model, **nie všeobecný prevod Eoed na Winklerovo ks celej dosky alebo úzkeho rebra**. Priestorové šírenie napätia a pôvodná zemina sa musia zahrnúť osobitne.

## 5. Čo overiť na zhutnenej miestnej zemine

[FHWA, §8.3 a §8.4](https://www.fhwa.dot.gov/engineering/geotech/pubs/05037/08.cfm) rozlišuje návrhovú požiadavku na tuhosť/pevnosť od preberania podľa hustoty: splnenie hustoty nemusí potvrdiť tuhosť. Uvádza skúšky doskou, penetráciou a vzorky ako spôsoby väzby na návrh. Povrchové zaťažovanie odhalí hrubé slabé miesta, ale samo nezisťuje všetky hlbšie vrstvy.

[JRC Eurocode 7, 2013, kap. 5, PDF str. 59–64](https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/2013_06_WS_GEO.pdf) vysvetľuje cestu od prieskumu, vody, vzoriek a skúšok k odvodeným a charakteristickým parametrom. Príloha A.3.4, PDF str. 124 a nasledujúce, hodnotí sadanie vrstveného podložia. Únosnosť a deformácia sú samostatné kontroly; výsledky tejto príkladovej zeminy nie sú parametrami domu.

Pre tento dom navrhujem zaznamenať:

- druhy a hrúbky zásypu, prítomnosť organiky, vlhkosť a rozdiely medzi krídlami; osobitne úzke miesta pod rebrami a okolím prestupov;
- skúšobné hutnenie, hrúbky jednotlivých vrstiev, stroj, vlhkosť a dosiahnutú suchú hustotu podľa skúšky konkrétneho materiálu;
- statickú zaťažovaciu skúšku s úplnou krivkou tlak–posun, priemerom dosky, cyklami, napäťovým rozsahom a stavom vlhkosti; geotechnik z nej spolu s profilom odvodí parametre pre geometriu dosky a rebier;
- hrúbku a stlačiteľnosť pôvodných vrstiev pod zásypom a pásmi, aktuálnu/možnú hladinu vody; pri jemnozrnnej zemine aj účinok zmien vlhkosti.

[Pospíšil a Horníček, 2025: pôvodná porovnávacia štúdia statických doskových skúšok](https://link.springer.com/article/10.1007/s40515-025-00542-7), časti 2 a 5, dokumentuje rozdielne postupy a moduly pri českých, francúzskych a nemeckých skúškach. Výsledky korelácií závisia od materiálu a platia v skúmanom rozsahu. Vzorec pre Ev2 zahŕňa geometriu skúšobnej dosky a spôsob spracovania krivky; **Ev2 nie je priamo ks**. Ich experiment sa týkal kameniva a stabilizovaných zemín, nie tohto miestneho zásypu.

[FHWA §5.3.3](https://www.fhwa.dot.gov/engineering/geotech/pubs/05037/05a.cfm) vysvetľuje väzbu zmien objemu jemnozrnnej zeminy na jej vlastnosti a vlhkosť. Prítomnosť hliny preto nie je automatický zákaz použitia; rovnako však slovo „zhutnená“ nevylučuje všetky deformácie po premočení. Konkrétne vlastnosti sa majú overiť, nie prisúdiť zo všeobecného názvu.

## 6. Čo zostáva otvorené pre celý dom

1. Skutočné sily zo strechy, povaly, stien, stĺpov a zariadení a ich prenos cez potvrdené štyri rebrá/pásy; nie predchádzajúca neodsúhlasená sieť 17 trás.
2. Únosnosť a sadanie zásypu **aj pôvodnej zeminy**, vrátane zaťaženia od samotného zásypu a rozdielov voči starým pásom. Vysoké ks samo osebe nepreukazuje qRd.
3. Výstuž a krytie 100 mm dosky a 400 mm rebier, skutočné monolitické uzly, pracovné škáry a neurčený profil obvodovej drážky 150 mm.
4. Stav, rozmery a výstuž existujúcich pásov; presná podpora nového obvodu, stabilita a prenos vodorovných síl.
5. Voda, mráz a konkrétne trvanlivostné riešenie C16/20 pre požadovanú životnosť.

Tieto body bránia zatiaľ úplnému potvrdeniu domu. **Neznamenajú**, že priebežná podpora nefunguje alebo že je nutné dokazovať voľné premostenie všetkých pôdorysných polí. České NA ani úplné aktuálne normové texty nie sú touto verejnou rešeršou nahradené. Druhá generácia EC7 sa v tomto výpočte nepoužíva ako už účinný český predpis.
