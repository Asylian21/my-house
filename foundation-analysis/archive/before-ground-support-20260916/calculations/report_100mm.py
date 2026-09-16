"""Build the focused five-page 100 mm / four-rib check from fresh JSON results."""
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
S=json.loads((B/'results/slab-100-four-ribs.json').read_text())
I=json.loads((B/'results/check-100mm-independent.json').read_text())
F=json.loads((B/'results/four-rib-free-beam-screen.json').read_text())
L=json.loads((B/'results/four-rib-load-path-audit.json').read_text())
G=json.loads((B/'inputs/geometry.json').read_text())
A=json.loads((B/'inputs/client-agreed-layout.json').read_text())
FONT=Path('/Users/davidzita/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/fonts')
for name,filename in [('DV','DejaVuSans.ttf'),('DVB','DejaVuSans-Bold.ttf')]:
 p=FONT/filename
 if not p.exists():p=FONT/'DejaVuSans.ttf'
 pdfmetrics.registerFont(TTFont(name,str(p)))
pdfmetrics.registerFontFamily('DV',normal='DV',bold='DVB',italic='DV',boldItalic='DVB')
W,H=A4;M=34;CW=W-2*M
NAVY=colors.HexColor('#18334a');RED=colors.HexColor('#bb3047');BLUE=colors.HexColor('#315de5');GRAY=colors.HexColor('#77818b');LIGHT=colors.HexColor('#eef2f5');ORANGE=colors.HexColor('#c66d14');GREEN=colors.HexColor('#257563')
P=ParagraphStyle('body',fontName='DV',fontSize=9.1,leading=12.5,textColor=NAVY)
SM=ParagraphStyle('small',parent=P,fontSize=8.1,leading=10.8)
HD=ParagraphStyle('head',parent=P,fontName='DVB',fontSize=10.8,leading=14.5)
c=canvas.Canvas(str(B/'report-100mm.pdf'),pagesize=A4);c.setTitle('DOM C/B/B - 100 mm C16/20 a štyri rebrá 400 mm: podmienený výpočet')
page=0;y=0;md=[];bottoms=[]
def plain(t):return html.unescape(re.sub('<[^>]+>','',t))
def start(title):
 global page,y
 if page:bottoms.append(y);c.showPage()
 page+=1;y=H-M
 c.setFillColor(NAVY);c.setFont('DVB',15);c.drawString(M,y-15,title);y-=29
 c.setStrokeColor(BLUE);c.line(M,y,W-M,y);y-=12
 c.setFont('DV',7.5);c.setFillColor(GRAY);c.drawString(M,21,'DOM C/B/B | 16. 9. 2026 | Podmienený výpočet - bez súhlasu na realizáciu');c.drawRightString(W-M,21,f'{page}/5')
 md.append('\n## '+title+'\n')
def guard():
 if y<42:raise RuntimeError(f'Overflow page{page}: y={y}')
def p(text,style=P):
 global y
 q=Paragraph(text,style);_,hh=q.wrap(CW,1000);y-=hh;q.drawOn(c,M,y);y-=7;md.append(plain(text)+'\n');guard()
def head(text):p(text,HD)
def table(rows,widths):
 global y
 cells=[[Paragraph(str(v),SM) for v in row] for row in rows]
 t=Table(cells,colWidths=widths);t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('LINEBELOW',(0,0),(-1,0),.7,NAVY),('LINEBELOW',(0,1),(-1,-1),.25,GRAY)]))
 _,hh=t.wrap(CW,1000);y-=hh;t.drawOn(c,M,y);y-=9
 md.append('| '+' | '.join(plain(str(v)) for v in rows[0])+' |\n| '+' | '.join('---' for _ in rows[0])+' |\n'+'\n'.join('| '+' | '.join(plain(str(v)) for v in row)+' |' for row in rows[1:])+'\n');guard()
def txt(x,y,t,size=9,color=NAVY):c.setFillColor(color);c.setFont('DV',size);c.drawString(x,y,t)
def n(x,k=2):return 'neurčené' if x is None else f'{x:.{k}f}'.replace('.',',')
def case(span,load):return next(v for v in S['meshes']['phi8_s150']['directions']['inner_cross_wire']['cases'] if v['model']=='local_void' and v['span_m']==span and v['load_case']==load)

start('100 mm doska: bezpečnosť domu nie je preukázaná')
p('<b>Záver pre tvoju zostavu:</b> zo zadaných rozmerov a podkladov nemožno potvrdiť, že dom bezpečne unesie 100 mm doska C16/20, štyri rebrá a súčasné obvodové pásy. Výpočet nižšie našiel konkrétne nevyhovujúce porovnávacie prípady a chýbajúce nosné dráhy. Nie je to predpoveď, že dom nevyhnutne spadne, ani plošné odmietnutie každej 100 mm podlahy.')
table([['Vstup','Stav a použitá hodnota'],['Doska / betón','DEKLAROVANÉ: 100 mm; C16/20; spoločná betonáž s rebrami.'],['Rebrá R7, R1, R2, R4','DEKLAROVANÁ výška 400 mm celkom (odpoveď na otázku vrátane dosky): 300 mm pod doskou. Šírka 350 mm je pracovná hodnota z výkresu.'],['Horný obvod a zarážka','DEKLAROVANÝ rozmer 300 mm a hĺbka zarážky 150 mm. Smer rozmerov, celý profil a priebeh prútov CHÝBAJÚ.'],['Zásyp','DEKLAROVANÉ: miestna hlina/piesok, zhutnené. Geotechnické vlastnosti, výška a skúšky CHÝBAJÚ.'],['Výstuž','CHÝBA. Ø6/150, Ø8/150 a Ø8/100 sú iba skúšobné siete; nie realizačný predpis.']],[115,CW-115])
head('Čo vlastný výpočet ukázal')
p('<b>1. Lokálne podopretá podlaha:</b> skúšobná Ø8/150 pri vnútornej dutine 1 m a iba podlahovom zaťažení číselne prejde uvedenými kladnými pásovými kontrolami. Pri dutine 2 m má priehyb <b>13,66 mm proti 8,00 mm</b>. Veľkosť skutočnej straty podpory sa nezistila.')
p('<b>2. Voľné pole medzi rebrami:</b> aj idealizované podopretie po štyroch stranách dá v menšom porovnávacom poli Mx = <b>17,53 kNm/m</b>. Najvyššia odporová hodnota skúšaných sietí v priaznivejšom smere je <b>10,70 kNm/m</b>. Tieto siete nevyhovujú tomuto modelu voľného poľa. Úplný výpadok zásypu sa však neurčuje ako povinný návrhový stav.')
p('<b>3. Steny a základy:</b> štyri rebrá plne geometricky pokrývajú iba 6 z 37 vnútorných modelových stenových úsekov. Medzi ostatnými sú aj nosné steny pri vstupe. Bez výpočtu ich podopretia a skutočných základov nemožno schváliť celý dom.')
head('Rozhodnutie pred betonážou')
p('Túto zostavu zatiaľ <b>nepovažovať za pripravenú na betonáž</b>. Najprv treba uzavrieť podopretie stien, zeminu, osadenie obvodu, skutočnú výstuž a spoj. Autorizovaný statik musí preveriť konkrétnu zostavu na stavbe; nasledujúce reprodukovateľné výpočty sú podkladom pre túto kontrolu.')

start('Doska 100 mm: prierez, lokálne dutiny a rozpätia')
p('PREDPOKLADY: B500; krytie 35 mm; fcd = 0,85 × 16 / 1,5 = 9,067 MPa; fyd = 500 / 1,15 = 434,783 MPa; Ecm = 28 600 MPa. Krytie a národné koeficienty nie sú novým normovým schválením. Gk = 2,5 doska + 2,0 vrstvy; Qk = 2,0 kPa. <b>qEd = 1,35 × 4,5 + 1,5 × 2 = 9,075 kPa.</b>',SM)
rows=[['Skúšobná sieť','As [mm²/m]','d [mm]','MRd [kNm/m]','VRdc [kN/m]']]
for mesh in ['phi6_s150','phi8_s150','phi8_s100']:
 sec=S['meshes'][mesh]['directions']['inner_cross_wire']['section']
 rows.append([mesh.replace('phi','Ø').replace('_s','/'),n(sec['As_mm2_per_m'],1),n(sec['d_mm'],0),n(sec['MRd_strain_compatible_kNm_m'],3),n(sec['VRdc_kN_m'],2)])
table(rows,[115,100,66,122,CW-403])
p('MEd a VEd sú účinky zaťaženia; MRd a VRdc sú odolnosti prierezu. Pre vyhovenie musí byť požiadavka najviac rovná odolnosti. Tabuľka používa slabší smer krížiacich sa drôtov jednej spodnej siete. MRd z rovnováhy a pretvorení nie je povolené zaťaženie celej dosky. Ø8/100 prekračuje prijaté konzervatívne kritérium x/d ≤ 0,45; jeho hodnoty 0,494/0,568 sa vykazujú osobitne. Hranica 0,45 nie je univerzálny zákaz každého prierezu bez redistribúcie.',SM)
head('Lokálna vnútorná dutina: kontrola 1 m pásu, Ø8/150')
p('Jednoduché uloženie na dvoch okrajoch; kladný ohyb. Stena kolmá na pás je v jeho strede, Gk steny = 6,9375 kN/m z predpokladov modelu. MEd = qEd L²/8 + 1,35 Gk,steny L/4. Dutiny 1 / 1,5 / 2 m sú citlivostné scenáre, nie zistené vady.',SM)
rows=[['L / zaťaženie','MEd / MRd<br/>[kNm/m]','wk QP<br/>[mm]','Priehyb / L/250<br/>[mm]','Výsledok iba týchto kontrol']]
for span,load in [(1.,'floor_only'),(1.,'wall_typical_partition'),(1.5,'floor_only'),(1.5,'wall_typical_partition'),(2.,'floor_only'),(2.,'wall_typical_partition')]:
 v=case(span,load);ss=v['sls_phi2p5'];passed=v['positive_bending_and_SLS_conservative_screen_pass']
 rows.append([n(span,1)+' m / '+('podlaha' if load=='floor_only' else '+ priečka'),n(v['MEd_kNm_m'])+' / 6,55',n(ss['crack_QP']['wk_mm'],3),n(ss['deflection_mm'])+' / '+n(ss['limit_L250_mm']), 'číselne áno*' if passed else 'NIE / nepreukázané'])
table(rows,[113,91,68,119,CW-391])
p('*Nie schválenie stavby. Pre podlahu + priečku pri L=1 m je aj konzervatívny šmyk VEd=13,90 &lt; VRdc=27,51 kN/m. SLS: popraskaná tuhosť, dotvarovanie phi=2,5 (citlivosť 1,5 až 3,5), QP=G+0,3Q, limit trhliny 0,30 mm. „Neurčené“ znamená prekročený rozsah lineárneho SLS prediktora; nelineárna odpoveď nebola vypočítaná. Záporný ohyb, prestupy, okraje a zmrašťovanie zostávajú otvorené.',SM)
head('Kontrolný výpočet voľných polí: priaznivé štyri podpory')
rows=[['Hypotetické pole [m]','Mx / My [kNm/m]','Porovnanie so skúšanými sieťami']]
for v in I['two_way_comparisons']:
 rows.append([n(v['a_m'],4)+' × '+n(v['b_m'],3),n(v['ULS']['Mx_kNm_m'])+' / '+n(v['ULS']['My_kNm_m']), 'Mx > najvyššie MRd 10,70; nevyhovuje'])
table(rows,[159,125,CW-284])
p('Navierova pružná doska so štyrmi ideálnymi nepretvárajúcimi sa kĺbovými hranami; iba podlaha, bez stien. P1: svetlá medzera R7-R1 a staré horné obvodové líca. P2: hypotetické 350 mm podpory na modrých osiach. Použitie svetlých rozmerov je priaznivá kontrola, nie stanovenie finálneho účinného rozpätia. Priehyb nepopraskanej dosky sa nepoužíva ako SLS dôkaz.',SM)

start('Nosné dráhy: štyri rebrá nepokrývajú všetky steny')
p('Pôdorys ukazuje modelové steny a štyri dohodnuté rebrá. Oranžová znamená stenu bez úplného pôdorysného pokrytia týmito rebrami; neznamená sama osebe vypočítanú poruchu. Zelená tiež nepotvrdzuje statickú únosnosť podpory.',SM)
# Exact vector plan, fit inside 300pt high box. Street below; long wing on right.
plot_h=284;top=y;bottom=y-plot_h;sc=plot_h/19.035;ox=M+38;oy=bottom
fn=lambda x,z:(ox+(x-6.44)*sc,oy+(z-3)*sc)
wallstatus={w['wall']:w['four_ribs_status'] for w in L['walls']}
per=A['existing_perimeter']['points_m'];c.setStrokeColor(BLUE);c.setLineWidth(1.7)
for a,b in zip(per,per[1:]+per[:1]):c.line(*fn(*a),*fn(*b))
for rib in A['agreed_ribs']:
 a,b=rib['points_m'];c.setStrokeColor(RED);c.setLineWidth(.35*sc);c.line(*fn(*a),*fn(*b));x,z=fn(*a);txt(x+4,z+10,rib['id'],8,RED)
for wall in G['walls']:
 rr=wall['rect_m'];x,z=fn(rr['x0'],rr['y0']);c.setFillColor(GREEN if wallstatus[wall['id']]=='FULL_PLAN_COVERAGE' else ORANGE);c.rect(x,z,(rr['x1']-rr['x0'])*sc,(rr['y1']-rr['y0'])*sc,fill=1,stroke=0)
# Labels in the courtyard and right margin avoid tracing over thin walls.
txt(M+40,top-22,'MODRÁ: deklarovaný obvod',8.2,BLUE)
txt(M+40,top-39,'ČERVENÁ: štyri rebrá',8.2,RED)
txt(M+40,top-56,'ORANŽOVÁ: podopretie treba doriešiť',8.2,ORANGE)
txt(M+40,top-73,'ZELENÁ: úplný pôdorysný prienik',8.2,GREEN)
txt(M+CW-133,top-30,'6 úplne pokrytých',9,GREEN)
txt(M+CW-133,top-47,'10 čiastočne',9,ORANGE)
txt(M+CW-133,top-64,'21 bez prieniku',9,ORANGE)
txt(ox+110,bottom-14,'ULICA / VSTUP',8.5)
y=bottom-27;guard()
md.append('Pôdorysná schéma: 6 úplných, 10 čiastočných a 21 nepokrytých vnútorných stenových úsekov; geometrická kontrola nie je statický dôkaz.\n')
table([['Rozhodujúci úsek','Čo zostáva bez preukázanej podpory'],['Nosné steny pri vstupe / pracovni','C-ENTRY-OFFICE-EAST 1,691 m a RETURN 0,700 m: mimo štyroch rebier; pôvodná línia R3 je vynechaná.'],['H200 pri pracovni','Dĺžka 4,758 m, predpoklad vlastnej tiaže 5,212 kN/m; chýba priebežné rebro.'],['Deliaca stena garáže','Dĺžka 4,855 m, šírka 301 mm; predpoklad 12,975 kN/m. Zadná garážová fasáda na pôvodnom R5 je ďalšia samostatná línia.'],['Ťažké prvky','Nohy AKU800, kotla, kachlí a podpery terasy vyžadujú lokálny výpočet. Obálka zariadenia nie je kontaktná plocha jeho nôh.']],[142,CW-142])
p('Pri pridaní starého horného obvodu zostáva 6 úplne pokrytých, 15 čiastočne a 16 bez pokrytia. Mimo pôdorysu tejto siete leží 44,0075 m z 61,165 m vnútorných stenových osí. Steny môže niesť navrhnutá doska na vhodnom podloží alebo doplnené podpory; ani jedno zatiaľ nie je pre túto zostavu preukázané.',SM)

start('Rebrá 400 mm, spoločná betonáž a 150 mm zarážka')
p('Pre výpočet sa 400 mm chápe ako celková výška vrátane 100 mm dosky, podľa položenej otázky. Všetky skúšobné prúty nižšie sú predpoklady; investor výstuž neurčil. Rozmery samotné nenahrádzajú prenos zaťaženia do zeminy alebo koncových podpier.',SM)
# Cross-section schematic to show declared 100+300=400; no invented joint detail.
base=y-145;c.setFillColor(LIGHT);c.setStrokeColor(NAVY);c.setLineWidth(.8)
c.rect(M+36,base+86,250,30,fill=1,stroke=1);c.rect(M+126,base,70,86,fill=1,stroke=1)
txt(M+305,base+100,'100 mm doska',9);txt(M+305,base+45,'300 mm pod doskou',9);txt(M+305,base+13,'400 mm celkom',10)
txt(M+122,base-15,'350 mm*',9);txt(M+36,base+133,'SCHEMATICKÝ REZ - VÝSTUŽ EŠTE NIE JE NAVRHNUTÁ',8.5)
y=base-30;guard()
head('Nosník iba medzi koncami: ohraničený porovnávací model')
# The independent beam helper below is intentionally a trial, not a reinforcement schedule.
beamrows=[['Skúšobná spodná výstuž','d [mm]','MRd [kNm]','qEd,max pri L=7,495 m [kN/m]']]
beamvals=[]
for count in [3,4]:
 d=400-35-8-8;As=count*math.pi*16**2/4;x=As*(500/1.15)/(.8*350*(.85*16/1.5));MR=As*(500/1.15)*(d-.4*x)/1e6;qm=8*MR/7.495**2
 beamvals.append((count,MR,qm));beamrows.append([f'{count}Ø16 (predpoklad)',n(d,0),n(MR),n(qm)])
table(beamrows,[162,61,97,CW-320])
p('Pravouhlý prierez b/h=350/400 mm; krytie 35 mm, skúšobný strmienok Ø8, B500, jednoduché uloženie, bez priaznivého T-prierezu a bez zemnej podpory. qEd,max = 8 MRd/L² je <b>iba ohybová hranica</b>, nie dovolené zaťaženie hotového rebra. Účinné rozpätie a koncové uloženia sú stále neurčené.',SM)
rows=[['Rebro / L [m]','MEd [kNm]','VEd [kN]','MEd/MRd pri 4Ø16']]
for v in F['cases']:
 rows.append([v['rib']+' / '+n(v['old_model_axis_length_m_assumed_span'],3),n(v['demand']['MEd_kNm']),n(v['demand']['VEd_max_unreduced_kN']),n(100*v['capacity_comparisons'][1]['MEd_over_MRd'],1)+' %'])
table(rows,[131,105,95,CW-331])
p('Zaťaženie: celá tiaž prierezu 0,35 × 0,40 × 25 = 3,50 kN/m + presne integrované tiaže priamo súosých stien podľa úsekov; súčiniteľ 1,35. <b>R1: MEd 114,88 > MRd 102,77 kNm aj pri 4Ø16.</b> V tomto obdĺžnikovom voľnom nosníku nevyhovuje už tento čiastkový súbor síl. Strecha, povala, širšia doska a ďalšie reakcie ešte nie sú zahrnuté. Menší pomer pri ostatných rebrách nie je celkové vyhovenie.',SM)
p('Šmykový príklad R1: VEd=68,64 kN; skúšobné dvojramenné Ø8/200 pri cot(theta)=1 dajú VRds=64,23 kN pre 4Ø16. Tento scenár tiež nevyhovuje. Hustejšie strmene nemenia ohybový deficit. Ak rebro nesie zemina, treba iný model podpory; spolupôsobenie dosky ako T-prierezu môže odolnosť zmeniť, ale nebolo preukázané. Priehyb, trhliny a celý spoj rebier sú otvorené.',SM)
head('150 mm betónovej zarážky nie je údaj o kotvení prútov')
p('Zatiaľ nie je jednoznačné, či 150 mm určuje zvislú drážku, vodorovné uloženie alebo iný profil. Nemožno z toho určiť reakciu, šmyk drážky ani dĺžku kotvy. Spoločné liatie dosky s rebrami nevyrieši automaticky spoj na obvodový alebo starší betón.',SM)
p('Vlastný porovnávací výpočet rovného ťahaného prúta pri plnom fyd a dobrej súdržnosti: fbd = 2,25 × 1,3 / 1,5 = 1,95 MPa; lb,rqd = Ø fyd / (4 fbd). <b>Ø8: 446 mm; Ø12: 669 mm; Ø16: 892 mm.</b> Sú to základné dĺžky pred úpravami detailu, nie predpis konkrétneho kotvenia. Ohyb prúta, zvary, priečna výstuž, krytie a napätie menia posúdenie. [1, 2]',SM)
head('Dve siete a záporný ohyb')
p('Pri dvoch obojsmerných sieťach Ø8 a krytí 35 mm je voľná medzera 100 - 2×35 - 4×8 = <b>-2 mm</b>: tento detail sa nezmestí. Jedna spodná sieť má d=61/53 mm pri kladnom, ale 39/47 mm pri opačnom ohybe. Pri spoločnej betonáži s rebrami treba riešiť aj podporové momenty, trhliny a obmedzenie zmrašťovania; jedna dolná sieť ich sama nepotvrdzuje. [1, 2]',SM)

start('Základy, zemina a podmienky dokončenia posúdenia')
head('Existujúce pásy 380-400 mm nie sú overené 100 mm doskou')
p('Pôvodná statika pre 800 mm pás uvádzala NEd=68 kN/m a referenčné Rd=150 kPa. Iba stará sila, bez tiaže dnešného pásu a nadložia, dá na šírke 400 mm <b>170,0 kPa</b> a na 380 mm <b>178,9 kPa</b>. Obe presahujú pôvodnú referenciu. Toto nie je nový výpočet dnešných reakcií ani dôkaz aktuálnej únosnosti zeminy; ukazuje, prečo nemožno prevziať schválenie pôvodného širšieho pásu.')
p('Model má navyše rozdiel modrých deklarovaných a sivých pôvodných horných osí 349-354 mm. Pri ich doslovnom priradení a šírkach horný 350 / spodný 400 mm by bol prienik iba 21-26 mm. <b>Je to rozpor koordinácie, nie zameraná chyba stavby.</b> Treba ho vyriešiť zameraním líc a rezom spoja; výkres sa zatiaľ nedá použiť ako dôkaz uloženia.')
head('Miestna hlina a piesok: čo musí dodať overenie')
p('Z opisu „zhutnené“ nemožno vypočítať tuhosť ani zostávajúce sadnutie. Potrebné sú zrnitosť a plasticita jemnej zložky, organické prímesi, vlhkosť, výška a hrúbky ukladaných vrstiev, stav prirodzenej zeminy, voda a návrhové hodnoty únosnosti/deformácií. Geotechnik musí určiť vhodnosť materiálu, skúšobný postup a preberacie kritériá pre konkrétny model. Percento Proctora nie je percento zostávajúceho sadania.')
head('Čo je potrebné uzavrieť, aby sa dalo rozhodnúť o 100 mm')
table([['Podklad / krok','Výsledok, ktorý musí byť preukázaný'],['Zameranie a rezy','Šírky a výšky starého i nového betónu; osadenie stien; skutočný profil 300/150 mm; každé uloženie rebra.'],['Nosný systém a zaťaženia','Každá nosná stena, priečka a ťažký prvok má overenú podporu; aktuálne strešné/povalové reakcie, sneh a vietor.'],['Zemina a zásyp','Návrhové parametre a skúšky, celkové i rozdielne sadanie; primeraný scenár straty kontaktu.'],['Výstuž a detaily','Oba smery a znamienka ohybu dosky; pozdĺžne prúty, strmienky, kotvenie, styky a pracovné škáry; garážové kolesá a pretlačenie.']],[127,CW-127])
p('<b>Odporúčanie pri zachovaní C16/20:</b> 100 mm ponechať iba ako skúmaný variant podlahy na overenom podloží, pokiaľ výpočet každej steny a podpery nepreukáže aj jej ďalšiu nosnú úlohu. Pre dnešnú zostavu štyroch rebier zatiaľ neexistuje uzavretý bezpečný realizačný návrh. Zvýšenie hrúbky dosky samo nevyrieši chybné uloženie ani slabé základové podložie.',SM)
head('Zdroje, reprodukcia a rozsah overenia')
p('[1] <link href="https://eurocodes.jrc.ec.europa.eu/sites/default/files/2022-06/EN1992_1_Walraven.pdf" color="#315de5">JRC / Walraven 2008: Eurocode 2</link>, materiál, ohyb, šmyk, kotvenie. [2] <link href="https://eurocodes.jrc.ec.europa.eu/doc/1110_WS_EC2/report/1110_WS_EC2.pdf" color="#315de5">JRC 2014: Design of concrete buildings</link>, SLS a detaily. [3] <link href="https://csnonline.agentura-cas.cz/Detailnormy.aspx?k=507748" color="#315de5">ČAS: ČSN EN 1992-1-1 ed. 2 (2019)</link> a <link href="https://csnonline.agentura-cas.cz/Detailnormy.aspx?k=511214" color="#315de5">NA ed. A (2020)</link>: overené katalógové údaje; plný český NA nebol dostupný. Normové voľby ostávajú označenými predpokladmi. Prístupy 16. 9. 2026.',SM)
p('Reprodukcia: v foundation-analysis/calculations spustiť slab_100_four_ribs.py, four_rib_load_path_audit.py, four_rib_free_beam_screen.py, check_100mm_independent.py a report_100mm.py. Podrobné JSON/MD sú v results/. Overené: rovnováha prierezov a pásov, nezávislá virtuálna práca, zhoda dvoch výpočtov MRd, konvergencia Navierovho radu a nezávislá kontrola 401 harmonikami. Nie sú overené skutočné reakcie stavby, geotechnika ani realizačné detaily. Pôvodné výsledky 17 trás zostávajú historickou štúdiou.',SM)

bottoms.append(y);assert page==5;c.save()
(B/'report-100mm.md').write_text('# C/B/B: 100 mm C16/20 a štyri rebrá 400 mm\n\n'+ '\n'.join(md)+'\n')
qa={'page_count':page,'page_size':'A4','minimum_content_y_points':min(bottoms),'pdf_sha256':hashlib.sha256((B/'report-100mm.pdf').read_bytes()).hexdigest(),'visual_review':'PENDING','whole_building_approval':False,'scope':'100mm slab / four400mm ribs: bounded conditional checks and open load paths'}
(B/'results/report-100mm-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print('Created 5-page report-100mm.pdf; minimum bottom',min(bottoms))
