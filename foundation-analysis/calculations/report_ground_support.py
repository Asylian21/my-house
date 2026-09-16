"""Current five-page report: continuous compacted-fill support is the main model."""
import json, math, re, html, hashlib
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle

B=Path(__file__).resolve().parents[1]
def read(path):return json.loads((B/path).read_text())
U=read('results/ground-support-independent.json')
S=read('results/slab-100-ground-support.json')
R=read('results/four-rib-ground-support.json')
OLD=read('results/slab-100-four-ribs.json')
FONT=Path('/Users/davidzita/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/fonts')
for name,filename in [('DV','DejaVuSans.ttf'),('DVB','DejaVuSans-Bold.ttf')]:
    path=FONT/filename
    if not path.exists():path=FONT/'DejaVuSans.ttf'
    pdfmetrics.registerFont(TTFont(name,str(path)))
pdfmetrics.registerFontFamily('DV',normal='DV',bold='DVB',italic='DV',boldItalic='DVB')
W,H=A4;M=34;CW=W-2*M
NAVY=colors.HexColor('#18334a');RED=colors.HexColor('#bb3047');BLUE=colors.HexColor('#315de5');GRAY=colors.HexColor('#77818b');LIGHT=colors.HexColor('#eef2f5');SOIL=colors.HexColor('#e9e0ca');GREEN=colors.HexColor('#257563')
P=ParagraphStyle('body',fontName='DV',fontSize=9.1,leading=12.5,textColor=NAVY)
SM=ParagraphStyle('small',parent=P,fontSize=8.1,leading=10.8)
HD=ParagraphStyle('head',parent=P,fontName='DVB',fontSize=10.8,leading=14.5)
c=canvas.Canvas(str(B/'report-100mm.pdf'),pagesize=A4)
c.setTitle('DOM C/B/B - doska 100 mm a rebrá 400 mm na zhutnenej zemine')
page=0;y=0;md=['**Revízia AK-01/AK-02, 16. 9. 2026:** aktuálne je SM30, jedna 300 mm obvodová tehla so zachovaným účelom odhlučnenia. Táto štúdia používa zmrazené pôvodné zaťaženia SA30; výsledky pre stenové zaťaženia a R7 sa nepovažujú za prepočet SM30. Konkrétny výrobok a nový prepočet zostávajú otvorené. Samostatné geometrické kóty a výpočty bez stenového zaťaženia týmto nie sú prerátané. Pozri [záznam revízie](/Users/davidzita/www/dom/foundation-analysis/inputs/wall-revision-sm30-20260916.md).\n'];bottoms=[]
def plain(t):return html.unescape(re.sub('<[^>]+>','',t))
def start(title):
    global page,y
    if page:bottoms.append(y);c.showPage()
    page+=1;y=H-M
    c.setFillColor(RED);c.setFont('DV',8)
    c.drawString(M,H-12,'REVÍZIA 16. 9. 2026: AK-01/02 = SM30, jedna 300 mm obvodová tehla.')
    c.drawString(M,H-23,'Staré stenové zaťaženia SA30 neplatia pre SM30; nový výrobok a prepočet čakajú.')
    c.setFillColor(NAVY);c.setFont('DVB',15);c.drawString(M,y-15,title);y-=29
    c.setStrokeColor(BLUE);c.line(M,y,W-M,y);y-=12
    c.setFont('DV',7.5);c.setFillColor(GRAY)
    c.drawString(M,21,'DOM C/B/B | 16. 9. 2026 | Podmienená analýza - nie realizačný výkres')
    c.drawRightString(W-M,21,f'{page}/5');md.append('\n## '+title+'\n')
def guard():
    if y<42:raise RuntimeError(f'Overflow page {page}: y={y}')
def p(text,style=P):
    global y
    q=Paragraph(text,style);_,hh=q.wrap(CW,1000);y-=hh;q.drawOn(c,M,y);y-=7
    md.append(plain(text)+'\n');guard()
def head(text):p(text,HD)
def table(rows,widths):
    global y
    cells=[[Paragraph(str(v),SM) for v in row] for row in rows]
    t=Table(cells,colWidths=widths)
    t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('LINEBELOW',(0,0),(-1,0),.7,NAVY),('LINEBELOW',(0,1),(-1,-1),.25,GRAY)]))
    _,hh=t.wrap(CW,1000);y-=hh;t.drawOn(c,M,y);y-=9
    md.append('| '+' | '.join(plain(str(v)) for v in rows[0])+' |\n| '+' | '.join('---' for _ in rows[0])+' |\n'+'\n'.join('| '+' | '.join(plain(str(v)) for v in row)+' |' for row in rows[1:])+'\n');guard()
def txt(x,z,t,size=9,color=NAVY):c.setFillColor(color);c.setFont('DV',size);c.drawString(x,z,t)
def n(x,k=2):return 'neurčené' if x is None else f'{x:.{k}f}'.replace('.',',')

start('Doska 100 mm na zhutnenej zemine')
p('<b>Hlavný model rešpektuje tvoje zadanie:</b> doska aj spodná plocha rebier majú súvislú podporu zhutneným zásypom. Doska preto automaticky nepreklenuje celé vzdialenosti medzi rebrami. Stenu mimo rebra môže podopierať doska spolu so zeminou. Predošlé voľné polia sú už len doplnkovými skúškami straty podpory.')
table([['Vstup','Použitá hodnota a dôkazová úroveň'],['Doska a betón','DEKLAROVANÉ: 100 mm, C16/20, spoločná betonáž s rebrami.'],['Štyri rebrá','R7 / R1 / R2 / R4. DEKLAROVANÁ celková výška 400 mm; 300 mm pod doskou. Pracovná šírka 350 mm je PREDPOKLAD.'],['Zásyp','DEKLAROVANÁ miestna zhutnená hlina/piesok. Súvislý kontakt a rovnomerná pružná podpora sú PREDPOKLAD modelu.'],['Tuhosť a výstuž','ks = 5 / 10 / 20 / 50 MN/m³ sú citlivostné hodnoty, nie skúšky. Skúšobná oceľ B500; výstuž stavby zatiaľ CHÝBA.']],[106,CW-106])
head('Čo sa dá vypočítať hneď: rovnomerné podlahové zaťaženie')
p('Tiaž dosky: 0,10 × 25 = <b>2,50 kN/m²</b>. Pracovný predpoklad ďalších vrstiev 2,00 kN/m² a úžitkového zaťaženia 2,00 kN/m² dá spolu <b>6,50 kPa</b> v charakteristickom stave. Návrhová kombinácia je 1,35 × 4,50 + 1,50 × 2,00 = <b>9,075 kPa</b>. Steny sú počítané navyše, jednotlivo.')
table([['ks [MN/m³]','Tlak G + Q [kPa]','Stlačenie pružín w = p/ks [mm]']]+[[n(v['ks_MN_m3'],0),'6,50',n(v['characteristic_spring_compression_mm'],3)] for v in U['uniform_floor']],[109,150,CW-259])
p('Tieto posuny sú odpoveď zvolených pružín. <b>Nie sú predpoveďou konečného sadnutia domu.</b> Pri nekonečnej rovnomernej ploche, rovnakom ks a rovnomernom zaťažení vychádza ohyb od tejto zložky nulový. Okraje, steny, prestupy, rozdiely podložia a zmrašťovanie tento ideálny stav menia.',SM)
head('Význam výsledku')
p('Súvislá podpora zeminou umožňuje oveľa priaznivejšie miestne ohybové výsledky, ako dávalo voľné pole. Nasledujúce strany uvádzajú skutočne prepočítané steny a rebrá. <b>100 mm tým nie je automaticky vylúčených, ale bezpečnosť celého domu ešte nie je preukázaná:</b> skúšobná výstuž, parametre podložia, všetky strešné reakcie a spoj na obvod sa musia uzavrieť.')

start('Doska pod stenami: miestny ohyb a tlak')
p('Samostatný vnútorný pás šírky 1 m na homogénnej podpore. Zaťaženie steny pôsobí cez jej konečnú šírku. Počítajú sa tiaže z modelu vrátane predpokladaných povrchov, bez dodatočných reakcií strechy a povaly. Nekonečný pás idealizuje oblasť vzdialenú od okrajov a koncov stien; nie je to výpočet všetkých 37 úsekov domu.',SM)
table([['Skúmaná stena','Gk [kN/m]','Šírka stopy [mm]'],['H200 pri pracovni','5,212','200*'],['Murovaná priečka','6,938','140'],['Deliaca stena garáže','12,975','301']],[244,126,CW-370])
p('*Pri H200 je rovnomerná stopa celej skladby idealizáciou; skutočné rozdelenie tiaže muriva a predsadenej konštrukcie treba doriešiť. Ide o vlastné tiaže jednotlivých stien, nie priemer rozpočítaný na podlahu.',SM)
head('Najťažšia stena 12,975 kN/m: nepopraskaná tuhosť')
heavy=[v for v in S['cases'] if v['wall_id']=='C-GARAGE-SPINE-N' and v['stiffness_id']=='gross_uncracked']
rows=[['ks<br/>[MN/m³]','MEd+ / MEd-<br/>[kNm/m]','pmax G+Q<br/>[kPa]','wmax G+Q<br/>[mm]']]
for v in heavy:
    q=v['ground_response']['characteristic']
    rows.append([n(v['ks_MN_per_m3'],0)+('*' if not v['gross_uncracked_load_stress_consistent'] else ''),n(v['M_positive_ULS_kNm_m'],3)+' / '+n(v['M_negative_ULS_kNm_m'],3),n(q['ground_pressure_max_kPa'],2),n(q['displacement_max_mm'],3)])
table(rows,[89,160,140,CW-389])
pos=S['section_capacities']['inner_cross_wire']['positive']['MRd_kNm_per_m']
neg=S['section_capacities']['outer_bottom_wire']['negative']['MRd_kNm_per_m']
p('<b>Porovnanie skúšobnej spodnej Ø8/150:</b> slabšia kladná odolnosť MRd+ = '+n(pos,3)+' kNm/m (d = 53 mm); slabšia záporná MRd- = '+n(neg,3)+' kNm/m (d = 39 mm). Najväčšie požiadavky vo všetkých 48 citlivostiach sú <b>4,515 a 1,064 kNm/m</b>. Tieto miestne ohybové požiadavky sú menšie ako uvedené odolnosti. Výsledok sám nepotvrdzuje trhliny, kotvenie ani realizovateľnosť siete.',SM)
p('*Pri ks = 5 a najťažšej stene je Mser = 3,344 > Mcr = 3,167 kNm/m. Čisto nepopraskaný stav preto nie je konzistentný. Následne sa skúšali nižšie tuhosti; nejde o potvrdenie skutočného priebehu trhlín.',SM)
head('Tá istá stena a ks = 5: vplyv popraskania')
reduced=[v for v in S['cases'] if v['wall_id']=='C-GARAGE-SPINE-N' and v['ks_MN_per_m3']==5]
names={'gross_uncracked':'Hrubý prierez','constant_cracked_positive':'Popraskaný d = 53','constant_cracked_negative':'Popraskaný d = 39','constant_cracked_negative_phi2p5':'d = 39, phi = 2,5'}
rows=[['Konštantná tuhosť EI<br/>[kNm²]','MEd+<br/>[kNm/m]','pmax G+Q<br/>[kPa]','wmax G+Q<br/>[mm]']]
for v in reduced:
    q=v['ground_response']['characteristic']
    rows.append([names[v['stiffness_id']]+' / '+n(v['EI_Nm2']/1000,1),n(v['M_positive_ULS_kNm_m'],3),n(q['ground_pressure_max_kPa']),n(q['displacement_max_mm'],3)])
table(rows,[222,90,106,CW-418])
p('Nižšie EI zmenší roznesenie sily: ohyb klesne, ale tlak a miestne zatlačenie rastú. Redukované hodnoty sú vypočítané z úplne popraskaného prierezu a použité konštantne na celý pás. <b>Nie sú nelineárnym SLS výpočtom.</b> Pri 48 prípadoch vyšiel maximálny charakteristický tlak 30,51 kPa a najväčší pružný posun 4,17 mm; tieto dve špičky patria rôznym prípadom.',SM)
p('Všetky kontrolované celkové tlaky zostali kladné aj pri kvázistálej kombinácii G + 0,3Q. Zemina sa preto v týchto konkrétnych výpočtoch nenúti prenášať ťah. Skúšobná sieť nie je návrhom výstuže pri rebrách a hornom povrchu. Priehyb a trhliny hotovej dosky sa touto kontrolou neuzatvárajú.',SM)

start('Štyri rebrá 350 × 400 mm podopreté zeminou')
p('Každé rebro je konečný nosník na súvislej pružnej podpore šírky 350 mm. Konce sú v tomto samostatnom modeli voľné: M = V = 0, bez predpokladaného votknutia alebo nepreukázaného uloženia na obvod. Dĺžky 7,495 a 6,298 m tu označujú dĺžku podopretého rebra, nie voľné rozpätie.')
p('Zahrnutá je vlastná tiaž 0,35 × 0,40 × 25 = <b>3,50 kN/m</b> a tiaže súosých stenových úsekov, vrátane otvorov podľa vstupu. Pruh 100 mm dosky nad rebrom je započítaný raz. Ďalšia plocha dosky, podlahové vrstvy, úžitkové a bodové zaťaženia, strecha, povala a nadpražia nad rámec opísaných tiaží zatiaľ nie sú zahrnuté.',SM)
head('Výsledky pri predpokladanom ks = 20 MN/m³')
rows=[['Rebro','max p(Gk)<br/>[kPa]','max w(Gk)<br/>[mm]','max |MEd|<br/>[kNm]','max |VEd|<br/>[kN]']]
for rib in ['R7','R1','R2','R4']:
    vv=[v for v in R['cases'] if v['rib']==rib and v['ks_MN_m3_assumed']==20]
    rows.append([rib,n(max(v['pressure_max_Gk_kPa'] for v in vv)),n(max(v['w_max_mm'] for v in vv),3),n(max(max(v['M_sagging_Ed_kNm'],abs(v['M_hogging_Ed_kNm'])) for v in vv),3),n(max(v['V_abs_Ed_kN'] for v in vv),3)])
table(rows,[65,124,114,117,CW-420])
p('Každá bunka je obálka troch tuhostí, nie nevyhnutne jedna spoločná fyzická zostava. p a w patria zahrnutým charakteristickým tiažam Gk; MEd a VEd používajú 1,35Gk. Skúšané EI = 53 386,7 / 7 870,1 / 9 587,3 kNm²: hrubý prierez a dve plne popraskané konštantné tuhosti s phi = 2,5. Ani tu nejde o vyriešenú históriu trhlín.',SM)
head('Citlivosť na ks = 5 až 50 MN/m³ a na tuhosť rebra')
rows=[['Rebro','Rozsah max w(Gk)<br/>[mm]','MEd+ max<br/>[kNm]','MEd- min<br/>[kNm]']]
for rib in ['R7','R1','R2','R4']:
    vv=[v for v in R['cases'] if v['rib']==rib]
    rows.append([rib,n(min(v['w_max_mm'] for v in vv),3)+' až '+n(max(v['w_max_mm'] for v in vv),3),n(max(v['M_sagging_Ed_kNm'] for v in vv),3),n(min(v['M_hogging_Ed_kNm'] for v in vv),3)])
table(rows,[65,205,127,CW-397])
p('<b>Záporný moment znamená ťah hore.</b> Najmä R1 a R7 preto nemožno schváliť iba porovnaním so spodnými prútmi. Skúšobný prierez s účinnými 3Ø16 na ťahovej strane má MRd = 80,69 kNm; so 4Ø16 102,77 kNm. To je podmienená prierezová odolnosť, nie predpis rovnakej výstuže hore a dole. Skutočná horná výstuž a kotvenie nie sú navrhnuté.',SM)
head('Čo preukazuje tento model rebier')
p('Súvislá zemina prenáša väčšinu zaťaženia priebežne a podstatne znižuje ohyb oproti nosníku nesenému iba na koncoch. Všetkých 48 prípadov má tlakový kontakt. Najvyšší tlak od zahrnutých Gk je 49,14 kPa; najväčší posun pružín 9,83 mm. Únosnosť zeminy a prípustné rozdielne sadanie sa tým ešte nepreukázali.')
p('Zjemnenie siete zo 100 na 50 mm zmenilo sledované extrémy najviac o '+n(100*R['validation']['max_coarse_to_fine_relative_change'],3)+' %. Relatívna chyba rovnováhy zvislých síl bola najviac '+f"{R['validation']['max_force_equilibrium_relative_error']:.2e}"+'. Model susednej dosky, rebier a obvodu treba následne spojiť; tieto lokálne posuny nemožno priamo odčítať a označiť za skutočné rozdielne sadanie domu.',SM)

def ground_and_details_page():
    global y
    start('Podložie, obvod a konštrukčný detail')
    head('Súvislá podpora musí byť aj pod spodkom rebra')
    p('Model počíta s doskou uloženou na zásype a s podopretím rebra na jeho spodnej ploche, 300 mm pod doskou. Pod rebrami sa používa plošná tuhosť násobená šírkou 0,35 m. Skutočný zásyp v tejto úrovni a prirodzená zemina pod ním musia túto podporu vytvoriť. Rovnaké ks pod doskou aj rebrom je citlivostný predpoklad, nie vlastnosť potvrdená stavbou.')
    top=y;base=top-132
    c.setFillColor(SOIL);c.rect(M+28,base,255,90,fill=1,stroke=0)
    c.setFillColor(LIGHT);c.setStrokeColor(NAVY);c.setLineWidth(.8)
    path=c.beginPath();path.moveTo(M+28,base+115);path.lineTo(M+283,base+115);path.lineTo(M+283,base+90);path.lineTo(M+193,base+90);path.lineTo(M+193,base+18);path.lineTo(M+118,base+18);path.lineTo(M+118,base+90);path.lineTo(M+28,base+90);path.close();c.drawPath(path,fill=1,stroke=1)
    for x,z in [(M+63,base+88),(M+95,base+88),(M+228,base+88),(M+258,base+88),(M+136,base+16),(M+176,base+16)]:
        c.setStrokeColor(GREEN);c.line(x,z-15,x,z);c.line(x,z,x-3,z-5);c.line(x,z,x+3,z-5)
    txt(M+305,base+101,'100 mm doska',9)
    txt(M+305,base+62,'300 mm pod doskou',9)
    txt(M+305,base+39,'400 mm celkom',10)
    txt(M+305,base+15,'Zelené: reakcie zeminy',8,GREEN)
    txt(M+31,base-14,'Schéma podpory; výstuž a obvodový spoj nie sú vykreslené.',8)
    y=base-31;guard()
    head('Tuhosť ks, únosnosť a sadanie sú tri odlišné kontroly')
    p('ks vyjadruje modelovú tuhosť kontaktu, teda vzťah tlaku a posunu. Nie je dovoleným tlakom do zeminy. Vyššie ks spravidla zmenší miestny pokles, ale môže zvýšiť špičku kontaktného tlaku. Návrhovú únosnosť a celkové aj rozdielne sadanie treba overiť pre celý profil zásypu a prirodzenej zeminy. [1, 3]',SM)
    p('Zhutnenie je vstup do posúdenia. Percento Proctora, modul zo skúšky doskou Ev2 a ks nie sú zameniteľné veličiny. Geotechnik má podľa materiálu, vlhkosti a hrúbok vrstiev určiť skúšky, preberacie kritériá a parametre pre tento model. Posuny na stranách 1-3 nezahŕňajú následnú konsolidáciu, premočenie alebo objemové zmeny. [1, 3]',SM)
    head('Existujúce pásy 380-400 mm zostávajú samostatným základom')
    p('Pôvodná statika mala pre 800 mm pás NEd = 68 kN/m. Ak by rovnaká sila pôsobila na 400 mm, samotné N/B dá 170 kPa; na 380 mm 178,9 kPa, ešte bez tiaže pásu. Pôvodných Rd = 150 kPa bolo projektovým predpokladom. Tieto čísla upozorňujú na potrebu nových reakcií a geotechniky; nie sú výpočtom dnešnej únosnosti ani automatickým dôkazom poruchy. Zásyp vnútri automaticky nezväčšuje šírku starého obvodového základu.',SM)
    head('Zarážka 150 mm a výstuž')
    p('Oznámených 300 mm pri hornom obvode a 150 mm hĺbky neurčuje celý profil spoja. Zarážka sa preto nezapočítala ako hotová kotva ani votknutie. Napríklad základná priama kotevná dĺžka Ø16 pri plnom fyd, C16/20 a dobrej súdržnosti vychádza 892 mm; konečné lbd závisí od napätia a detailu. Spoločná betonáž dosky a rebier nepreukazuje spoj so starým betónom. [2]',SM)
    p('Modré obvodové čiary sú deklarované približné osi betónu. Rozdiel voči starým sivým osiam 349-354 mm je koordinačný rozpor modelu, nie zameraná chyba stavby. Pred návrhom spoja treba určiť skutočné líca, výšky a uloženie nového betónu.',SM)

def scope_and_sources_page():
    start('Rozsah výsledku a ďalšie rozhodnutie')
    table([['Čo sa teraz prepočítalo','Čo tým ešte nie je potvrdené'],['Rovnomerná podlaha na zemi','Podpora pri okrajoch, kútoch, prestupoch a pri rozdieloch ks.'],['Miestny pás pod jednotlivou stenou','Spoločné pôsobenie všetkých stien, dosky, rebier a obvodu; konce a križovania stien.'],['Samostatné rebrá na pružnom podloží','Celý monolitický L-systém, rozdielne sadanie oproti starým pásom a konečný spoj.'],['Priebehy tlaku, posunov a síl','Nameraná únosnosť zásypu, hlbšieho podložia a konečné sadnutie domu.'],['Skúšobné železobetónové prierezy','Skutočná výstuž, trhliny, dotvarovanie, zmrašťovanie, kotvy, kolesá v garáži a nohy zariadení.']],[206,CW-206])
    head('Praktický záver pre 100 mm C16/20')
    p('<b>Počítanie so zhutnenou zeminou je oprávnený nosný model a výrazne mení výsledok.</b> Miestne ohybové kontroly uvedené v tejto správe nedávajú dôvod zamietnuť hrúbku 100 mm iba pre veľké rozostupy rebier. Nemáme však uzavretý návrh, ktorý by potvrdil bezpečnosť celého domu. Pred betonážou musí autorizovaný statik uzavrieť výstuž, skutočné zaťaženia a napojenia s geotechnickými parametrami pre túto stavbu.')
    p('Nie je potrebné automaticky doplniť rebro pod každú stenu iba preto, že na pôdoryse neleží nad jedným zo štyroch rebier. Rozhodne výsledok dosky so zeminou pri príslušnej stene. Ani tento priaznivejší výpočet zatiaľ nepredpisuje konkrétnu sieť alebo pozdĺžne prúty na nákup.',SM)
    head('Predošlé výpočty bez podpory zásypom')
    p('Výsledky lokálnych dutín 1-2 m, voľných doskových polí a rebier podopretých iba na koncoch zostávajú v samostatných JSON/MD a v archive/before-ground-support-20260916/. Sú to doplnkové scenáre. Ich nevyhovenie sa nepoužíva ako záver o dnešnom hlavnom modeli s priebežnou podporou.',SM)
    head('Metóda, overenie a reprodukcia')
    p('Rovnováha prúta: EI d⁴w/dx⁴ + ks b w = qline(x); reakcia p = ks w. Doskový pás je samostatný jednosmerný model šírky 1 m. Konečná šírka steny sa integruje, nenahrádza sa bodovým tlakom pri kontrole jeho špičky. Rebrá majú samostatný konečný prútový model. Súčet týchto lokálnych výpočtov nie je spojeným priestorovým modelom domu.',SM)
    p('Nezávislá Fourierova kontrola pásu: 24 kombinácií, 4 096 a 16 384 harmoník; maximálna relatívna odchýlka od uzavretého riešenia je '+f"{U['maximum_relative_error']:.2e}"+'. Ďalšie kontroly rovnováhy, kontaktu a zjemnenia sú v výsledných JSON. Matematická zhoda overuje algoritmus, nie vstupné vlastnosti stavby.',SM)
    p('Reprodukcia v calculations/: ground_support_independent.py, slab_100_ground_support.py, four_rib_ground_support.py, report_100mm.py. Podrobné vstupy a výsledky sú v results/*ground-support*; odolnosti nadväzujú na slab_100_four_ribs.py a four_rib_free_beam_screen.py. C16/20: fcd = 0,85 × 16/1,5 = 9,067 MPa; B500: fyd = 500/1,15 = 434,783 MPa. Krytie 35 mm a národné voľby sú výpočtové predpoklady.',SM)
    head('Primárne zdroje a hranice ich použitia')
    p('[1] <link href="https://www.fhwa.dot.gov/engineering/geotech/pubs/05037/05c.cfm" color="#315de5">FHWA NHI-05-037 §5.4.6</link> a <link href="https://www.fhwa.dot.gov/engineering/geotech/pubs/05037/08.cfm" color="#315de5">§8.3</link>: význam ks a kontrola podložia; mechanický podklad, nie český návrhový predpis. [2] <link href="https://eurocodes.jrc.ec.europa.eu/doc/1110_WS_EC2/report/1110_WS_EC2.pdf" color="#315de5">JRC 2014: Eurocode 2, worked examples</link>: RC a geotechnické kontroly. [3] <link href="https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/2013_06_WS_GEO.pdf" color="#315de5">JRC 2013: Eurocode 7</link>: prieskum a sadanie. [4] <link href="https://archive.nptel.ac.in/content/storage2/courses/105106049/lecnotes/mainch11.html" color="#315de5">NPTEL, Beam on Elastic Foundation, kap. 11</link>: rovnice a analytický kontrolný príklad. Overené 16. 9. 2026.',SM)
    p('ČSN EN 1992-1-1 ed. 2 (2019) a NA ed. A (2020): overené katalógové údaje ČAS; úplné znenie českých národných príloh nebolo dostupné. Súbor inputs/check-100mm-sources.md uvádza dostupnosť a vydania; inputs/ground-support-sources.md obsahuje podrobné nové zdroje. Správa nepredstiera autorizované normové posúdenie.',SM)

def finish():
    bottoms.append(y);assert page==5;c.save()
    (B/'report-100mm.md').write_text('# C/B/B: 100 mm C16/20 a 400 mm rebrá na zhutnenej zemine\n\n'+'\n'.join(md)+'\n')
    qa={'page_count':page,'page_size':'A4','minimum_content_y_points':min(bottoms),'pdf_sha256':hashlib.sha256((B/'report-100mm.pdf').read_bytes()).hexdigest(),'visual_review':'PENDING','whole_building_approval':False,'main_model':'continuous compacted-fill support; void/free-span results are supplementary only'}
    (B/'results/report-100mm-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
    print('Created 5-page ground-supported report; minimum content bottom',min(bottoms))

ground_and_details_page()
scope_and_sources_page()
finish()
