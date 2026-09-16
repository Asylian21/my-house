"""Dimensioned coordination drawings. No structural release or as-built inference."""
import json, csv, hashlib
from decimal import Decimal as D
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A3, landscape
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.styles import ParagraphStyle
from reportlab.platypus import Paragraph, Table, TableStyle

BASE=Path(__file__).resolve().parents[1]
A=json.loads((BASE/'inputs/client-agreed-layout.json').read_text())
G=json.loads((BASE/'inputs/geometry.json').read_text())
OUT=BASE/'drawings/technical';OUT.mkdir(exist_ok=True)
FONT=Path('/Users/davidzita/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/fonts')
for name,fn in [('DV','DejaVuSans.ttf'),('DVB','DejaVuSans-Bold.ttf')]:
 p=FONT/fn
 if not p.exists():p=FONT/'DejaVuSans.ttf'
 pdfmetrics.registerFont(TTFont(name,str(p)))
pdfmetrics.registerFontFamily('DV',normal='DV',bold='DVB',italic='DV',boldItalic='DVB')
NAVY=colors.HexColor('#173047'); BLUE=colors.HexColor('#315de5');RED=colors.HexColor('#ce3451');GRAY=colors.HexColor('#808a95');LIGHT=colors.HexColor('#edf2f6');PALE=colors.HexColor('#fae5e9')
W,H=landscape(A3);MM=72/25.4;SC=MM/100
X0,Y0=6440,3000;RIGHT,REAR=28040,22035
REF={'A':X0,'B':Y0,'C':RIGHT,'D':REAR}
def number(v):
 s=f'{v:,.1f}' if float(v)%1 else f'{v:,.0f}'
 return s.replace(',',' ').replace('.',',')
routes=[]
refs={'R7':('A',1),'R1':('C',-1),'R2':('B',1),'R4':('D',-1)}
for r in A['agreed_ribs']:
 pts=[[float(D(str(q))*1000) for q in p] for p in r['points_m']]
 vertical=pts[0][0]==pts[1][0];pos=pts[0][0 if vertical else 1];ref,direction=refs[r['id']]
 dist=abs(pos-REF[ref]);axis_ref={'A':X0,'B':Y0,'C':RIGHT,'D':REAR}[ref]
 axisdist=abs(pos-axis_ref)
 routes.append({'id':r['id'],'points_mm':pts,'vertical':vertical,'width_mm':350,'width_status':'PRELIMINARY_FROM_17_ROUTE_STUDY_NOT_VALIDATED_FOR_FOUR_RIBS','reference':ref,'axis_distance_from_reference_mm':dist,'near_face_distance_mm':dist-175,'far_face_distance_mm':dist+175,'axis_coordinate_mm':pos,'face_coordinates_mm':[pos-175,pos+175],'prior_drawn_route_length_mm':round(r['length_m']*1000,3),'final_rib_length_mm':None,'support_detail_status':'UNRESOLVED_AFTER_PERIMETER_CENTERLINE_CLARIFICATION'})
DATA={'units':'mm','design':'C/B/B','scale':'A3 landscape 1:100 at 100 percent','status':'APPROX_PERIMETER_CENTERLINES_MODEL_COORDINATION_NOT_FOR_SETTING_OUT','reference_lines':REF,'reference_definition':'CBB perimeter lines used as approximate centers of existing concrete per client; garage extension800mm confirmed. These are not concrete edges or surveyed exact axes.','rib_width_mm':350,'rib_width_status':routes[0]['width_status'],'rib_half_width_mm':175,'routes':routes,'X_chain_mm':[8653,5598.5,7348.5],'Y_chain_mm':[7862,8323,2850],'perimeter_line_dimensions_mm':[21600,19035],'field_survey':None,'engineering_check_for_four_ribs':False,'old_face_offsets_status':'SUPERSEDED_DO_NOT_USE','source_clarification':A['client_centerline_clarification']}
newpts=[[int(D(str(v))*1000) for v in p] for p in A['existing_perimeter']['points_m']]
oldpts=[[int(D(str(v))*1000) for v in p] for p in G['perimeter_axis_m']]
offsets=[]
for label,point,axis,direction in [('Zľava - garážový bok',0,0,'doprava'),('Zdola - uličná strana',0,1,'nahor / do záhrady'),('Sprava - dlhá vonkajšia strana',1,0,'doľava'),('Zhora - zadná strana terasy',2,1,'nadol / k ulici'),('Zhora pri dvore - vodorovný úsek na fotke',4,1,'nadol / k ulici'),('Zľava pri dvore - vnútorná zvislá krídla',3,0,'doprava')]:
 offsets.append({'side':label,'blue_coordinate_mm':newpts[point][axis],'gray_coordinate_mm':oldpts[point][axis],'coordinate_axis':'X' if axis==0 else 'Y','offset_mm':abs(newpts[point][axis]-oldpts[point][axis]),'direction_from_blue_to_gray':direction})
DATA['blue_to_gray_line_offsets']=offsets
byid={r['id']:r for r in routes}
r7a,r7b=byid['R7']['face_coordinates_mm'];r1a,r1b=byid['R1']['face_coordinates_mm']
r2a,r2b=byid['R2']['face_coordinates_mm'];r4a,r4b=byid['R4']['face_coordinates_mm']
face_dims=[
 ('A po ľavú hranu R7','X',REF['A'],r7a),
 ('Svetlá medzera R7 - R1','X',r7b,r1a),
 ('Ľavá hrana R7 po modrý L-bok','X',r7a,21040),
 ('Pravá hrana R1 po premietnutý L-bok','X',r1b,21040),
 ('Pravá hrana R1 po C','X',r1b,REF['C']),
 ('B po dolnú hranu R2','Y',REF['B'],r2a),
 ('Svetlá medzera R2 - R4','Y',r2b,r4a),
 ('Horná hrana R4 po D','Y',r4b,REF['D']),
]
DATA['direct_face_dimensions']=[{'label':label,'coordinate_axis':axis,'from_mm':a,'to_mm':b,'distance_mm':b-a} for label,axis,a,b in face_dims]
DATA['face_X_chain_mm']=[r7a-X0,350,r1a-r7b,350,RIGHT-r1b]
DATA['face_Y_chain_mm']=[r2a-Y0,350,r4a-r2b,350,REAR-r4b]
with (OUT/'direct-rib-face-dimensions.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['label','axis','from_mm','to_mm','distance_mm'])
 for label,axis,a,b in face_dims:w.writerow([label,axis,a,b,b-a])
(BASE/'results/agreed-ribs-dimensions.json').write_text(json.dumps(DATA,ensure_ascii=False,indent=2)+'\n')
with (OUT/'perimeter-line-offsets.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['side','axis','blue_line_mm','gray_axis_mm','offset_mm','direction'])
 for a in offsets:w.writerow([a['side'],a['coordinate_axis'],a['blue_coordinate_mm'],a['gray_coordinate_mm'],a['offset_mm'],a['direction_from_blue_to_gray']])
with (OUT/'dimensions.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['rib','working_width_mm','reference_approx_centerline','near_face_mm','axis_mm','far_face_mm','final_rib_length_mm','status'])
 for r in routes:w.writerow([r['id'],350,r['reference'],r['near_face_distance_mm'],r['axis_distance_from_reference_mm'],r['far_face_distance_mm'],'UNRESOLVED',DATA['status']])

c=canvas.Canvas(str(OUT/'agreed-ribs-technical.pdf'),pagesize=(W,H))
c.setTitle('ZK-01 / ZK-02 / ZK-03 - Rebrá, obvod a priame kóty k hranám')
def txt(x,y,t,size=9,bold=False,color=NAVY,anchor='left'):
 c.setFillColor(color);c.setFont('DVB' if bold else 'DV',size)
 getattr(c,{'left':'drawString','center':'drawCentredString','right':'drawRightString'}[anchor])(x,y,t)
def para(x,y,w,t,size=9,color=NAVY):
 st=ParagraphStyle('p',fontName='DV',fontSize=size,leading=size*1.38,textColor=color)
 p=Paragraph(t,st);_,h=p.wrap(w,1000);p.drawOn(c,x,y-h);return y-h-8
def table(x,y,width,rows,widths):
 st=ParagraphStyle('cell',fontName='DV',fontSize=8.4,leading=11.4,textColor=NAVY)
 cells=[[Paragraph(str(v),st) for v in row] for row in rows]
 t=Table(cells,colWidths=widths)
 t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('VALIGN',(0,0),(-1,-1),'TOP'),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('TOPPADDING',(0,0),(-1,-1),5),('BOTTOMPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,0),.7,NAVY),('LINEBELOW',(0,1),(-1,-1),.3,colors.HexColor('#cbd4dd'))]))
 _,h=t.wrap(width,1000);t.drawOn(c,x,y-h);return y-h-12
def line(x1,y1,x2,y2,color=NAVY,width=.5,dash=None):
 c.setStrokeColor(color);c.setLineWidth(width);c.setDash(dash or []);c.line(x1,y1,x2,y2);c.setDash([])
def header(code,title,page):
 txt(28,H-36,title,19,True);txt(28,H-55,'C / B / B | 16. 9. 2026 | všetky kóty v mm | pracovná šírka rebier 350*',10)
 c.setFillColor(PALE);c.rect(28,H-86,W-56,22,fill=1,stroke=0)
 txt(38,H-79,'NOVÁ REFERENCIA: OBVODOVÉ ČIARY = PRIBLIŽNÉ STREDY BETÓNU; STARÉ KÓTY OD LÍC A-D SÚ PREKONANÉ',10,True,RED)
 line(28,47,W-28,47,GRAY)
 txt(28,29,f'{code} | revízia OSI | {page}/3 | Koordinačné kóty - nie podklad na vytýčenie.',8)
 txt(W-28,29,'Šírka 350* je pracovný prierez zo štúdie so 17 trasami.',8,False,RED,'right')
def xy(x,y):return 67+(x-X0)*SC,180+(y-Y0)*SC
def dh(x1,x2,source_y,dim_y,label=None):
 a,b=xy(x1,source_y),xy(x2,source_y)
 for x,y in (a,b):line(x,y,x,dim_y+4,GRAY,.35);line(x-2.5,dim_y-2.5,x+2.5,dim_y+2.5,NAVY,.65)
 line(a[0],dim_y,b[0],dim_y)
 txt((a[0]+b[0])/2,dim_y+4,label or number(x2-x1),8.5,False,NAVY,'center')
def dv(y1,y2,source_x,dim_x,label=None):
 a,b=xy(source_x,y1),xy(source_x,y2)
 for x,y in (a,b):line(x,y,dim_x+4,y,GRAY,.35);line(dim_x-2.5,y-2.5,dim_x+2.5,y+2.5,NAVY,.65)
 line(dim_x,a[1],dim_x,b[1])
 c.saveState();c.translate(dim_x-4,(a[1]+b[1])/2);c.rotate(90);txt(0,0,label or number(y2-y1),8.5,False,NAVY,'center');c.restoreState()
def tag(label,x,y,dx=0,dy=0):
 sx,sy=xy(x,y);px,py=sx+dx,sy+dy
 line(sx,sy,px,py,NAVY,.6)
 c.setFillColor(colors.white);c.setStrokeColor(NAVY);c.circle(px,py,10,fill=1,stroke=1);txt(px,py-3,label,9,True,NAVY,'center')

header('ZK-01','ŠTYRI REBRÁ - TECHNICKÝ PÔDORYS',1)
# Plan at exact 1:100: blue is merely extent of declared old perimeter, not an assumed 400 mm face.
for wall in G['walls']:
 r=wall['rect_m'];x,y=xy(r['x0']*1000,r['y0']*1000);c.setFillColor(colors.HexColor('#e4e8ec'));c.rect(x,y,(r['x1']-r['x0'])*1000*SC,(r['y1']-r['y0'])*1000*SC,stroke=0,fill=1)
per=[[q*1000 for q in p] for p in A['existing_perimeter']['points_m']];per+=[per[0]]
for a,b in zip(per,per[1:]):
 p,q=xy(*a),xy(*b);line(*p,*q,BLUE,3.2)
oldper=[[q*1000 for q in p] for p in G['perimeter_axis_m']];oldper+=[oldper[0]]
for a,b in zip(oldper,oldper[1:]):line(*xy(*a),*xy(*b),GRAY,.6,[4,2])
for r in routes:
 a,b=r['points_mm'];pos=r['axis_coordinate_mm']
 if r['vertical']:x,y=xy(pos-175,a[1]);ww,hh=350*SC,(b[1]-a[1])*SC
 else:x,y=xy(a[0],pos-175);ww,hh=(b[0]-a[0])*SC,350*SC
 c.setFillColor(PALE);c.setStrokeColor(RED);c.setLineWidth(.85);c.rect(x,y,ww,hh,fill=1,stroke=1)
 line(*xy(*a),*xy(*b),RED,.45,[5,2,1,2])
 if r['vertical']:
  tx,ty=xy(pos+300,4300);txt(tx,ty,r['id'],11,True,RED);txt(tx,ty-13,'b = 350*',8.5,False,RED)
 else:
  tx,ty=xy(24400,pos+360);txt(tx,ty,r['id']+' / b = 350*',10,True,RED,'center')
for x,y,t in [(8200,6400,'GARÁŽ'),(12000,9200,'SPÁLŇA'),(16500,9250,'DETSKÁ IZBA'),(16500,5400,'DETSKÁ IZBA'),(24100,5300,'PRACOVŇA'),(24700,8500,'TECHNICKÁ'),(23100,15200,'OBÝVAČKA / KUCHYŇA'),(23700,20400,'TERASA')]:txt(*xy(x,y),t,8,color=GRAY)
# Primary dimensions now use the client's approximate concrete CENTER lines, not faces.
for a,b in zip([REF['A'],15093,20691.5,REF['C']],[15093,20691.5,REF['C']]):dh(a,b,Y0,143)
dh(REF['A'],REF['C'],Y0,119,'21 600 - obvodové čiary po predĺžení garáže o 800')
for a,b in zip([REF['B'],10862,19185,REF['D']],[10862,19185,REF['D']]):dv(a,b,RIGHT,707)
dv(REF['B'],REF['D'],RIGHT,741,'19 035 model / 19 050 zdrojový obrázok')
dh(21040,28040,22035,742,'7 000 - medzi obvodovými čiarami')
dv(3000,11200,X0,40,'8 200 - medzi obvodovými čiarami')
tag('A',REF['A'],4300,-17,0);tag('B',12000,REF['B'],0,-17);tag('C',REF['C'],5400,15,0);tag('D',22500,REF['D'],0,-20)
txt(400,93,'ULICA / VSTUP',10,True,NAVY,'center')
# Small explanation in courtyard, without crossing plan lines.
leftx=80;y=710
txt(leftx,y,'A - D TERAZ OZNAČUJÚ ČIARY, NIE HRANY',11,True);y-=17
y=para(leftx,y,370,'A ľavá, B uličná, C pravá a D zadná <b>obvodová čiara</b>. Podľa investora je betón približne vystredený na týchto čiarach. Garážový koniec bol predĺžený o 800 mm.',9)
y=para(leftx,y,370,'Modrá = nová deklarovaná referencia v rámci modelu C/B/B. Sivá prerušovaná = pôvodná os horného obvodu zo štúdie; s modrou sa nezhoduje.',9)
line(leftx,y-6,leftx+24,y-6,RED,3);txt(leftx+34,y-9,'Červená = nové rebrá, pracovná šírka 350*',9);y-=30
y=para(leftx,y,370,'*350 mm = šírka betónového rebra, nie šírka výkopu ani spodnej pätky. Prevzatá zo staršej štúdie; pre 4 rebrá staticky nepotvrdená.',9,RED)
y=para(leftx,y,370,'Červené polohy rebier zostali z modelu; ich napojenia na novú modrú referenciu sú neuzavreté. Kóty vpravo sú od čiar A-D, nie od okraja vyliateho betónu.',9)
txt(leftx,y-5,'Mierka 1 : 100 pri tlači A3 / 100 %',9,True)
line(leftx,y-25,leftx+50*MM,y-25,NAVY,1.3)
for p in [leftx,leftx+50*MM]:line(p,y-29,p,y-21,NAVY,1)
txt(leftx,y-41,'Kontrolná úsečka 50 mm na papieri = 5 000 mm v modeli.',8)
txt(leftx,y-58,'PRIAME KÓTY K HRANÁM A MEDZI REBRAMI: LIST ZK-03',9,True,RED)
# Right technical panel.
px=791;pw=W-px-28;py=738
txt(px,py,'KÓTY OD OBVODOVEJ ČIARY',12,True);py-=15
py=para(px,py,pw,'Všetko v mm. Kolmo dovnútra od čiary A/B/C/D po modelové rebro. Nejde o zamerané kóty od betónových hrán.',9)
rows=[['Rebro / čiara','Bližšia hrana','Os','Vzdialenejšia hrana']]
for r in routes:rows.append([r['id']+' / '+r['reference'],number(r['near_face_distance_mm']),number(r['axis_distance_from_reference_mm']),number(r['far_face_distance_mm'])])
py=table(px,py,pw,rows,[65,98,83,pw-246])
py=para(px,py,pw,'Príklad R7: od čiary A po prvú modelovú hranu 8 478; ďalších 350 tvorí pracovná šírka rebra. Jeho os je od A 8 653.',9)
py=para(px,py,pw,'R1 sa meria <b>sprava od C smerom doľava</b>. R4 sa meria <b>zozadu od D smerom k ulici</b>. R2 od B smerom do záhrady.',9)
rows=[['Rebro','Šírka*','Stav napojenia']]+[[r['id'],'350','Vyžaduje nové zosúladenie s obvodom.'] for r in routes]
py=table(px,py,pw,rows,[65,75,pw-140])
py=para(px,py,pw,'Zobrazené konce červených úsekov sú pôvodné modelové body, nie nové betonážne dĺžky. Medzery pri modrom obvode sú priznaný nesúlad podkladov, nie navrhnuté pracovné škáry.',9)
py=para(px,py,pw,'<b>L-roh:</b> R2 má os Y10 862, modré zalomenie Y11 200: rozdiel338 mm. Ľavý koniec R2 preto nemá preukázané napojenie na nový modrý obvod. Nespojiť ho v kresbe bez návrhu detailu.',9)
py=para(px,py,pw,'<b>Nosná geometria zostáva otvorená:</b> sivé osi horného obvodu sú od modrých čiar odsadené približne349-354 mm. Treba zosúladiť skutočný pás, horný betón a steny; jednoduchá zmena kót sama prenos síl nevyrieši.',9,RED)
assert py>58,py
txt(px,205,'PÔDORYSNÝ DETAIL ŠÍRKY / 1 : 10',10,True)
sx=px+120;sw=350*MM/10;sy=125
c.setFillColor(PALE);c.setStrokeColor(RED);c.setLineWidth(.8);c.rect(sx,sy,sw,40,fill=1,stroke=1)
line(sx+sw/2,sy-8,sx+sw/2,sy+48,RED,.55,[4,2,1,2])
for xp in [sx,sx+sw]:
 line(xp,sy+40,xp,183,GRAY,.4);line(xp-2,180-2,xp+2,180+2,NAVY,.6)
line(sx,180,sx+sw,180);txt(sx+sw/2,184,'350*',9,True,RED,'center')
for a,b in [(sx,sx+sw/2),(sx+sw/2,sx+sw)]:
 line(a,sy,a,106,GRAY,.4);line(b,sy,b,106,GRAY,.4);line(a,109,b,109)
 for xx in [a,b]:line(xx-2,107,xx+2,111,NAVY,.6)
 txt((a+b)/2,96,'175',8.5,False,NAVY,'center')
txt(sx+sw/2,78,'os rebra',8,False,RED,'center')
c.showPage()
header('ZK-02','POTVRDENÝ VÝKLAD OBVODU A ROZDIELY',2)
lx=35;lw=553;rx=619;rw=W-rx-35;yy=735
txt(lx,yy,'1 / AKTUÁLNE POTVRDENIE INVESTORA',13,True);y=yy-20
y=para(lx,y,lw,'Betón je približne vystredený po čiarach obvodu na novom obrázku. Investor výslovne potvrdil predĺženie garážového konca o 800 mm: 20 800 + 800 = <b>21 600 mm</b>. Ide o deklarovaný stav; presné líca a polohy zatiaľ nie sú zamerané.',10)
y=table(lx,y,lw,[['Referencia','Koordinačná čiara v C/B/B','Význam'],['A - ľavá','X = 6 440','Približná os betónu'],['B - uličná','Y = 3 000','Približná os betónu'],['C - pravá','X = 28 040','Približná os betónu'],['D - zadná','Y = 22 035','Približná os betónu']],[137,185,lw-322])
y=para(lx,y,lw,'Súradnice používajú rámec hlavného pôdorysu. Ich priradenie ku skutočným pásom zostáva koordinačné, nie geodeticky potvrdené. A-D už neoznačujú staré vonkajšie líca horného 350mm obvodu.',9)
txt(lx,y-6,'2 / ČIARA A SKUTOČNÝ OKRAJ BETÓNU',12,True);y-=24
y=para(lx,y,lw,'Pri presne vystredenom 400mm páse ležia hrany 200 mm od jeho osi; pri 380mm páse 190 mm. Používateľ však uviedol „približne v strede“, preto <b>presný posun k skutočnému okraju nie je určený</b>. Starú tabuľku od betónových líc nemožno použiť.',10,RED)
y=para(lx,y,lw,'Kóty listu 1 sú vzdialenosti modelových osí a líc rebier od referenčných čiar. Nehovoria, kde presne leží zameraná hrana betónu. Šírka 350 mm je stále iba pracovný návrh zo staršej štúdie.',9)
y=para(lx,y,lw,'Pôvodné listy sú uložené v archive/before-centerline-clarification-20260916. Táto revízia ich nahrádza; pôvodný výpočet sa nemení na posúdenie novej nosnej geometrie.',9)
assert y>65,y

txt(rx,yy,'3 / ZDROJOVÉ KÓTY A MODEL',13,True);y=yy-20
y=table(rx,y,rw,[['Strana L-obvodu','Obrázok + predĺženie','Model C/B/B'],['Celková šírka','20 800 + 800','21 600'],['Celková hĺbka','19 050','19 035'],['Šírka pravého krídla','7 000','7 000'],['Vnútorná dĺžka krídla','10 840','10 835'],['Návrat od garáže po L-roh','13 750 + 800 = 14 550','14 600'],['Ľavý bok pri garáži','8 200','8 200']],[210,185,rw-395])
y=para(rx,y,rw,'Rozmery z obrázka sa pri pravouhlom L neuzatvárajú: 7 000 + 13 750 = 20 750, rozdiel 50 mm oproti 20 800; 8 200 + 10 840 = 19 040, rozdiel 10 mm oproti 19 050. Neopravujú sa potichu. Modelové kóty sú od zdrojových oddelené.',9)
y=para(rx,y,rw,'Koordinačné reťazce: <b>8 653 + 5 598,5 + 7 348,5 = 21 600</b>; <b>7 862 + 8 323 + 2 850 = 19 035</b>. Potvrdenie 800mm predĺženia rieši šírku, nie presnú polohu všetkých hrán.',9)
txt(rx,y-4,'4 / ČO TREBA ZOSÚLADIŤ',12,True);y-=22
y=para(rx,y,rw,'Pôvodné osi horného obvodu sú voči novým modrým čiaram odsadené dovnútra 349-354 mm. Pôvodný predpoklad súosého spodného a horného pásu preto nemožno prevziať. Treba zamerať priečne polohy betónu a stien a upraviť ich podopretie aj napojenie rebier.',9.7)
y=para(rx,y,rw,'Os R2 leží 338 mm pred zalomením L. Ani priame predĺženie jeho ľavého konca po X21 040 samo nezabezpečí napojenie na zvislý obvod, ktorý začína až na Y11 200. Tento detail zostáva otvorený.',9.7,RED)
y=para(rx,y,rw,'Zdroj: inputs/client-agreed-layout.json, nový obrázok a potvrdenie predĺženia garáže. Model: geometry.json. Pracovná šírka 350 mm: staršia štúdia R1-R7. Výška, pätky a výstuž sa tu nanovo neurčujú.',9)
assert y>58,y
c.showPage()
header('ZK-03','PRIAME KÓTY K HRANÁM REBIER',3)
# Draw the unchanged model with light context and direct face-to-face dimensions.
for wall in G['walls']:
 r=wall['rect_m'];x,y=xy(r['x0']*1000,r['y0']*1000)
 c.setFillColor(colors.HexColor('#f0f2f4'));c.rect(x,y,(r['x1']-r['x0'])*1000*SC,(r['y1']-r['y0'])*1000*SC,stroke=0,fill=1)
for a,b in zip(per,per[1:]):line(*xy(*a),*xy(*b),BLUE,3.2)
for a,b in zip(oldper,oldper[1:]):line(*xy(*a),*xy(*b),GRAY,.45,[4,2])
for r in routes:
 a,b=r['points_mm'];pos=r['axis_coordinate_mm']
 if r['vertical']:x,y=xy(pos-175,a[1]);ww,hh=350*SC,(b[1]-a[1])*SC
 else:x,y=xy(a[0],pos-175);ww,hh=(b[0]-a[0])*SC,350*SC
 c.setFillColor(PALE);c.setStrokeColor(RED);c.setLineWidth(.85);c.rect(x,y,ww,hh,fill=1,stroke=1)
 line(*xy(*a),*xy(*b),RED,.45,[5,2,1,2])
 if r['vertical']:
  tx,ty=xy(pos+300,4200);txt(tx,ty,r['id'],11,True,RED);txt(tx,ty-13,'b = 350*',8.5,False,RED)
 else:
  tx,ty=xy(22400,pos+440);txt(tx,ty,r['id']+' / b = 350*',9.5,True,RED)
for x,y,t in [(8200,5700,'GARÁŽ'),(11600,8800,'SPÁLŇA'),(16500,9200,'DETSKÁ IZBA'),(16500,5400,'DETSKÁ IZBA'),(23000,5100,'PRACOVŇA'),(24200,8500,'TECHNICKÁ'),(22100,15100,'OBÝVAČKA'),(23100,20500,'TERASA')]:txt(*xy(x,y),t,8,color=GRAY)

def label_box(x,y,label,rotation=0,size=10):
 c.saveState();c.translate(x,y);c.rotate(rotation)
 w=pdfmetrics.stringWidth(label,'DVB',size)+10
 c.setFillColor(colors.white);c.rect(-w/2,-3,w,size+5,stroke=0,fill=1)
 txt(0,0,label,size,True,RED,'center');c.restoreState()
def direct_h(a,b,y,label=None,ext=None,label_dx=0,label_dy=7):
 x1,yy=xy(a,y);x2,_=xy(b,y)
 if ext:
  for xx,from_y in [(x1,ext[0]),(x2,ext[1])]:line(xx,xy(0,from_y)[1],xx,yy+4,RED,.4)
 line(x1,yy,x2,yy,RED,.8)
 for xx in [x1,x2]:line(xx-2.4,yy-2.4,xx+2.4,yy+2.4,RED,.85)
 label_box((x1+x2)/2+label_dx,yy+label_dy,label or number(b-a))
def direct_v(a,b,x,source_x=None):
 xx,y1=xy(x,a);_,y2=xy(x,b)
 if source_x:
  sx=xy(source_x,0)[0]
  for yy in [y1,y2]:line(sx,yy,xx-4,yy,RED,.4)
 line(xx,y1,xx,y2,RED,.8)
 for yy in [y1,y2]:line(xx-2.4,yy-2.4,xx+2.4,yy+2.4,RED,.85)
 label_box(xx-7,(y1+y2)/2,number(b-a),90)
# Main arrows match the user's 9:41 markup: obvod -> face, clear gap, and L reference.
direct_h(X0,r7a,10100)
direct_h(r7b,r1a,7450)
direct_h(r1b,RIGHT,6200)
direct_h(r7a,21040,12300,ext=(10849,12300))
# Short offset to the projected L-bok has an explicit leader; it is not a support joint.
direct_h(r1b,21040,11550,label=' ',ext=(10849,11550))
px0,py0=xy((r1b+21040)/2,11550)
line(px0,py0,px0-28,py0+58,RED,.6)
label_box(px0-61,py0+60,'173,5')
# Right-hand wing: lower face, clear span between ribs, and upper face to rear line.
direct_v(Y0,r2a,29200,27691)
direct_v(r2b,r4a,29200,27691)
direct_v(r4b,REAR,29200,27691)
# Axis chain remains a separate, muted check so it cannot be read as clear width.
for a,b in zip([X0,15093,20691.5,RIGHT],[15093,20691.5,RIGHT]):dh(a,b,Y0,144)
dh(X0,RIGHT,Y0,119,'21 600 - celková šírka medzi modrými čiarami')
txt(370,94,'SPODNÝ REŤAZEC JE PO OSIACH REBIER',9,True,NAVY,'center')
tag('A',X0,4300,-17,0);tag('B',12000,Y0,0,-17);tag('C',RIGHT,4800,16,0);tag('D',22500,REAR,0,15)
txt(80,709,'KÓTY PODĽA TVOJICH ČERVENÝCH ŠÍPOK',11,True)
y=para(80,688,365,'Červené kóty vedú <b>po hrany rebier</b>. Medzi rebrami je uvedená <b>čistá medzera</b>. Modrá čiara zostáva referenciou obvodu.',10)
line(80,y-6,104,y-6,RED,1);txt(114,y-9,'Kóty k hranám / medzi hranami',9.5);y-=29
line(80,y-6,104,y-6,BLUE,3);txt(114,y-9,'Modrá obvodová referencia',9.5);y-=29
y=para(80,y,365,'Horná kóta <b>6 122</b> ide od ľavej hrany R7 po zvislú modrú čiaru L. Kóta <b>173,5</b> udáva vodorovný rozdiel od pravej hrany R1 po tú istú čiaru premietnutú nadol.',9.5)
y=para(80,y,365,'Červené rebrá sa neposúvali. Šírka každého je pracovných <b>350 mm*</b>. Os leží 175 mm od hrany.',9.5)
assert y>510,y
# Compact face-dimension table, grouped by direction.
tx=785;tw=W-tx-28;ty=738
txt(tx,ty,'ODKIAĽ - KAM / VŠETKO V mm',12,True);ty-=20
rows=[['Kóta po hrany','Vzdialenosť']]+[[label,number(b-a)] for label,axis,a,b in face_dims]
ty=table(tx,ty,tw,rows,[tw-80,80])
ty=para(tx,ty,tw,'<b>Rozdiel oproti osiam:</b> medzi R7 a R1 je po osiach 5 598,5 mm, ale medzi hranami 5 248,5 mm. Rozdiel 350 mm tvorí polovica šírky každého rebra.',9.3)
ty=para(tx,ty,tw,'<b>Kontrola šírky:</b><br/>8 478 + 350 + 5 248,5 + 350 + 7 173,5 = 21 600.<br/><b>Kontrola hĺbky:</b><br/>7 687 + 350 + 7 973 + 350 + 2 675 = 19 035.',9.3)
ty=para(tx,ty,tw,'<b>Rozsah kót:</b> ide o presné rozdiely modelových línií a hrán navrhovaných rebier. Modrá čiara nie je zameraná hrana vyliateho betónu.',9.3)
ty=para(tx,ty,tw,'*Šírka 350 mm nie je staticky potvrdená pre túto štvoricu. Kóty 6 122 a 173,5 sú vodorovné priemety k L-boku; nepreukazujú napojenie ani podopretie. Detaily napojenia zostávajú podľa listov ZK-01 a ZK-02 otvorené.',9.3,RED)
ty=para(tx,ty,tw,'Zdroj spresnenia: označený výrez investora 16. 9. 2026 o 9:41:18. Mierka 1 : 100 pri tlači A3 na 100 %. Sivá pôvodná os je len pomocná.',8.5)
assert ty>76,ty
c.save()

# Machine-readable arithmetic review for this drawing, separate from engineering checks.
assert sum(DATA['face_X_chain_mm'])==21600
assert sum(DATA['face_Y_chain_mm'])==19035
assert [b-a for _,_,a,b in face_dims]==[8478,5248.5,6122,173.5,7173.5,7687,7973,2675]
assert sum(DATA['X_chain_mm'])==REF['C']-REF['A']==21600
assert sum(DATA['Y_chain_mm'])==REF['D']-REF['B']==19035
for r in routes:
 assert r['far_face_distance_mm']-r['near_face_distance_mm']==350
 assert r['axis_distance_from_reference_mm']-r['near_face_distance_mm']==175
assert [r['offset_mm'] for r in offsets]==[354,354,349,350,351,353]
qa={'status':'ARITHMETIC_AND_LAYOUT_NOT_STRUCTURAL_APPROVAL','page_count':3,'page_size':'A3 landscape','scale':'1:100 at actual size','exact_four_routes':[r['id'] for r in routes],'width_mm':350,'width_is_approved':False,'references_surveyed':False,'chains_and_350_widths':'PASS','six_perimeter_line_offsets':'PASS','eight_direct_face_dimensions':'PASS','visual_review':'PENDING','pdf_sha256':hashlib.sha256((OUT/'agreed-ribs-technical.pdf').read_bytes()).hexdigest()}
(BASE/'results/technical-drawing-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print('Created 3-page A3 revision with ZK03: direct dimensions to rib faces and between ribs.')
