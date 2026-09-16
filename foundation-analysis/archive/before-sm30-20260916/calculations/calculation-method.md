# Výpočtové modely a vedomé medze

## 1. Východiská

Geometria je v metroch v lokálnom rámci projektu. Horné líce existujúceho pásu je pracovné z=0. Spodok existujúceho pásu z=-0,600 a nové horné líce z=+0,600 sú modelové predpoklady, nie absolútne úrovne voči ulici. Nový vnútorný základ má spodných300 mm, driek300 mm a horné rebro600 mm vrátane dosky. Bloky P1-P6 majú modelovo súvislý prierez až k podložiu, celkom1200 mm; spodná posudzovaná zóna350 mm je vnútri tohto objemu, nepripočítava sa.

Základová škára pod konečným terénom nie je odvodená zo600 mm výšky betónu. Rozhodnutie zmeniť hĺbku vyžaduje geotechniku a prepočet množstiev. Všetky rovnobežné steny SA30 nesú vlastnú tiaž; nemajú priradenú strechu.

## 2. Reakčný obal nie je vyriešená strecha

Pre typický obvodový pás sa skúma tributárna šírka4,10 m, polovica modelového vonkajšieho priečneho rozmeru8,20 m. Zaťaženie strechy1,40 kPa je zaokrúhlená hodnota pôvodných1,18 kPa prepočítaných na vodorovný priemet; skutočná skladba, krokvy, prievlaky a reakcie chýbajú. Drevený strop0,75 kPa a povala2,0/7,5 kPa sú predpoklady. Súbeh oboch premenných v plnej hodnote je konzervatívny oproti znižovaniu ψ, ale nepokrýva ľubovoľnú bodovú reakciu.

ULS: NEd=1,35Gk+1,5(Qk+Sk). SLS charakteristický: Gk+Qk+Sk. Podložie: B'=B−2e, qEd=NEd/B'. Maximálny lineárny tlak SLS=qSLS×(1+6e/B); lineárny plný kontakt predpokladá |e|≤B/6. Všetky skúmané e0/25/50 mm túto nerovnosť spĺňajú, ale vodorovné reakcie skutočného krovu môžu excentricitu zmeniť.

Jednotlivé obaly sa **nesčítavajú ako celá budova**: bez rozdelenia skutočných reakcií by sa strecha započítala opakovane. Preto tu nie je predstieraná globálna rovnováha kompletného domu. Rovnováhy miestnych nosníkov a doskových modelov sú overené. Otvory garáže, úžľabie a stĺpy môžu vyvolať vyššie lokálne tlaky než líniový obal; `load-envelope.json` uvádza prírastky pre30/60/100 kN pri rôznych neprerukázaných prenosových dĺžkach.

Vietor0,8 a1,5 kPa, dvojnásobný sneh1,6 kPa, lokálna PV3 kN a voda0/0,3/0,6 m sú **citlivosti**, nie normové určenie návrhových účinkov. Všetky musia byť nahradené reálnymi údajmi. Zaťaženie pilierov pri P4-P6 v obale60 kN musí obsahovať aj vlastnú tiaž piliera, nie iba strešnú reakciu.

## 3. Vnútorné trasy a bloky

R1-R5: potenciálne nosné steny, konzervatívna dodatočná tributárna šírka3,5 m pre strechu/povalu. R6-R17: vlastná hmotnosť priečok, bez strechy. Rozmery pozri `routes.csv`. Každý pás je uložený súvislo na prevzatej prirodzenej zemine. Žiadny nie je navrhnutý ako7,5 m voľne rozpätý nosník v zásype. Poloha R13 má lokálny70 mm prechod v uzle; nejde o70 mm ohyb hlavného výstužného prúta.

Vlastné hmotnosti: bežné neoverené murivo12 kN/m³, omietky2×15 mm pri18 kN/m³, výška3,125 m. SA30:146 kg/m² murivo+54 omietka+4 vata. H200:73+54+35+8 kg/m² vrátane predpokladaných dosiek, kovov a vaty. Hmotnosti neobsahujú neznámy obklad a zavesené ťažké zariadenia; následné zaťaženie sa musí doplniť. Krátke nadpražné obálky sa konzervatívne rátajú na plnú výšku, preto nejde o presný výkaz tehál.

Kontrola podložia nových nosných pásov pri Rd150 kPa má nízku rezervu MIN. Geotechnik musí určiť únosnosť **aj sadanie**; samotné dosiahnutie150 kPa nestačí. Pri zdvojenom zaťažení alebo excentricite sa výsledky zmenia.

P1-P3: plné zemou podopreté bloky pod zásobníkom vody, kotlom a kachľami; P4-P6: geometrické kandidáty pod podperami terasy/lodžie. Aktuálne rozmery a stredy sú v JSON. Modelový bodový obal20/20/10/60/60/60 kN nie je dodaná reakcia. U P5 sa rešpektuje dlhý modelový pilier500×2500 mm; P6 obopína L-obálku lodžiového piliera. Plochy prekrývajúce starý betón nesmú dostať status účinného spoločného základu bez overenia spoja.

Skríning pretlačenia používa kompletný uzavretý obvod vo vzdialenosti d=294 mm od predpokladanej200 mm štvorcovej plochy, β1,15, plnú silu bez odpočtu reakcie zeminy. Je to úmyselne konzervatívny miestny skríning, **nie uzavreté posúdenie pätky podľa EC2**. Pôvodný skúšobný300 mm spodný prierez P5 mierne prekročil skríning; finálny používa350 mm spodnú zónu v rovnakom1200 mm plnom bloku. Konečné pretlačenie vyžaduje skutočnú kontaktnú plochu, excentricity, účinné obvody a rozdelenie reakcie zeminy.

## 4. RC výpočty

fcd=0,85×16/1,5=9,0667 MPa; fyd=500/1,15=434,783 MPa. Zvolená αcc je konzervatívny predpoklad pri neprečítanom rozhodujúcom českom NDP. Výpočet odolnosti bežného prierezu: x=As fyd/(0,8 b fcd), z=d−0,4x, MRd=As fyd z. Šmyk: VRdc=max[0,12 k(100ρfck)^(1/3);0,035 k^(3/2)√fck]bd. Strmene: VRds=(Asw/s)z fyd cotθ, cotθ=1; VRdmax=0,5b z νfcd, ν=0,6(1−fck/250). Nepripočítava sa VRdc kVRds.

Sokel má výpočet pozitívneho ohybu pri1 a2 m lokálnej strate podpory. Horná výstuž má rovnaké množstvo pre opačné zakrivenie, ale celkové nerovnomerné sadanie nie je vyriešené. Priehyb je z plne popraskaného jednostranne vystuženého prierezu, zanedbanie tlakovej výstuže je konzervatívne. Celé charakteristické zaťaženie sa pre sokel konzervatívne považuje za dlhodobé priφ2,5. MIN pri2 m zlyhá na kritériu trhliny; nie je to návrhová porucha1 m.

Doska: presný opis v `results/slab-notes.md`. Pri kolesovom šmyku sa používa konzervatívna obálka pohybujúcej sa bodovej sily, av=xc; nejde o tvrdenie, že norma bez výnimky predpisuje vzdialenosť k stredu stopy. Redukcia blízko podpory vyžaduje priamu podporu a plné zakotvenie. Bez týchto podmienok nie je odolnosť potvrdená. Navierova plošná kontrola je nezávislá kontrola ohybu pre presne definovanú jednoducho podopretú obdĺžnikovú oblasť, nie náhrada chýbajúceho globálneho modelu L.

## 5. Sadanie, zásyp a pracovné škáry

s=N_SLS ln[(B+H)/B]/Eoed, H2 m. Ide o jednoduchý2:1 roznos pod dlhým pásom; vplyv susedných pásov, vrstvenie, výkop, konsolidácia, navlhnutie a objemové zmeny sa nezamieňajú za vyriešený priestorový geotechnický model. Citlivosť Eoed3/8,5/15 MPa nie je prieskum. Hodnota8,5 MPa pochádza z neovereného predpokladu pôvodnej statiky. Pri plošnom priťažení zásypom sa osobitne pridáva horný odhad qH/Eoed; skutočná časová postupnosť môže mať iné účinky.

Projektové kritériá s25 mm a rotácia1/500 sú skríningové, treba ich zosúladiť s murivom, podlahami, potrubiami a celou stavbou. Žiadna hodnota DPr ani Ev2 sa automaticky nepremieňa na sadanie. Skúšobné hutnenie musí určiť materiál, vlhkosť, počet prejazdov,150-200 mm vrstvy a kontrolu aj pri obvode/rozvodoch. Preberanie je založené na geotechnickom modeli s daným limitom sadania, nie iba na jednom čísle z doskovej skúšky.

Rozhranie starý/nový betón: výpočet bez kohézie c=0, podmienene μ0,5 a bez ťahu. Predpoklad kontaktu je nutné overiť odstránením všetkých fólií a nesúdržných vrstiev na pracovnej ploche. Tlak hutnenia sa nenahrádza statickým zemným tlakom; výpočet K0=0,5,γ20 kN/m³ a prirážka10 kPa je len stavebný obal. Dočasné vystuženie/zavetrenie musí byť navrhnuté zvlášť.

Pracovný kandidát dodatočnej výstuže2radyØ10/250, embed300 mm nemá potvrdenú únosnosť kotvy. π·10·300·2/1000=18,85 kN je iba súdržnostný člen; okrajové vylomenie, rozštiepenie a šmyk vyžadujú ETA a skutočný starý betón. Nezamieňať tento výsledok za monolitické spolupôsobenie. Vodorovné pracovné škáry v nových vnútorných základoch vyžadujú priebežné zvislé prúty, zdrsnenie a overenie etapových síl.

## 6. Množstvá

Objemy sa počítajú geometrickými zjednoteniami v samostatných výškových vrstvách: spodný základ−0,6..−0,3; driek−0,3..0; horné rebrá0..0,6−h; doska0,6−h..0,6. Bloky mimo doskového polygonu majú plnú výšku, nie omylom zníženú o hrúbku neexistujúcej dosky. Prekrytia nových objemov so starým pásom sa odpočítavajú. MIN garáž má180 mm s rovným horným lícom. Tým sa zamedzí dvojitému započítaniu dosky, rebier, uzlov a blokov.

Oceľ je odhad zo sietí, 6pozdĺžnych prútov, strmienkov, základových sietí, zvislých prútov a osobitnej výstuže blokov.15 % pokrýva odrezky/presahy,80 kg ďalšie zhustenie uzlov; nie je to tvarový výkaz. Dĺžky priečnych spojov, hákov a jednotlivých uzlov sa zatiaľ nepredstierajú. MIN→MED→MAX je kvantifikovaný materiálový rozdiel, nie cenová ponuka.

Tabuľkový zásyp je objem medzi z0 a spodným lícom dosky mimo betónu. Odhumusovanie0,20 m je osobitný modelový objem47,744 m³; jeho náhradu pod z0 treba pripočítať po odpočte základov a zistení pôvodných výšok. Pri výkope nesčítať tú istú zeminu dvakrát. Sypký objem, odvoz, skládka, voda, paženie, podchytenie, hydroizolácia a protimrazové riešenie potrebujú vlastné výmery.
