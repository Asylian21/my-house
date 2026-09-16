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
X0,Y0=6794,3354;RIGHT,REAR=27691,21685
REF={'A':6619,'B':3179,'C':27866,'D':21860}
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
 routes.append({'id':r['id'],'points_mm':pts,'vertical':vertical,'width_mm':350,'width_status':'PRELIMINARY_FROM_17_ROUTE_STUDY_NOT_VALIDATED_FOR_FOUR_RIBS','reference':ref,'axis_distance_from_reference_mm':dist,'near_face_distance_mm':dist-175,'far_face_distance_mm':dist+175,'axis_coordinate_mm':pos,'face_coordinates_mm':[pos-175,pos+175],'axis_length_mm':round(r['length_m']*1000,3),'clear_length_between_proposed_350_perimeter_faces_mm':round(r['length_m']*1000-350,3),'existing_400_outer_face_to_axis_if_concentric_mm':axisdist+200,'existing_400_outer_face_to_near_rib_face_if_concentric_mm':axisdist+25,'existing_380_outer_face_to_axis_if_concentric_mm':axisdist+190,'existing_380_outer_face_to_near_rib_face_if_concentric_mm':axisdist+15})
DATA={'units':'mm','design':'C/B/B','scale':'A3 landscape 1:100 at 100 percent','status':'MODEL_COORDINATION_ONLY_NOT_FOR_CONSTRUCTION','reference_faces':REF,'reference_definition':'Outer faces of hypothetical 350 mm upper perimeter centred on model axes; not surveyed existing concrete faces.','rib_width_mm':350,'rib_width_status':routes[0]['width_status'],'rib_half_width_mm':175,'routes':routes,'X_chain_mm':[8474,5598.5,7174.5],'Y_chain_mm':[7683,8323,2675],'outer_upper_perimeter_dimensions_mm':[21247,18681],'field_survey':None,'engineering_check_for_four_ribs':False}
(BASE/'results/agreed-ribs-dimensions.json').write_text(json.dumps(DATA,ensure_ascii=False,indent=2)+'\n')
with (OUT/'dimensions.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['rib','working_width_mm','reference_outer_upper_face','near_face_mm','axis_mm','far_face_mm','axis_length_mm','status'])
 for r in routes:w.writerow([r['id'],350,r['reference'],r['near_face_distance_mm'],r['axis_distance_from_reference_mm'],r['far_face_distance_mm'],r['axis_length_mm'],DATA['status']])

c=canvas.Canvas(str(OUT/'agreed-ribs-technical.pdf'),pagesize=(W,H))
c.setTitle('ZK-01 / ZK-02 - Štyri rebrá: modelové kóty a pracovná šírka')
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
 txt(38,H-79,'KOORDINAČNÝ VÝKRES Z MODELU - PRED VYTÝČENÍM POTVRDIŤ ZAMERANIE A NÁVRH ŠTYROCH REBIER',10,True,RED)
 line(28,47,W-28,47,GRAY)
 txt(28,29,f'{code} | {page}/2 | Modelové rozmery nie sú zameraním vyliateho betónu.',8)
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
 # Exact proposed 350 upper reference faces, distinct from symbolic blue old perimeter.
 if a[0]==b[0]:
  for delta in [-175,175]:line(*xy(a[0]+delta,a[1]),*xy(b[0]+delta,b[1]),GRAY,.65,[3,2])
 else:
  for delta in [-175,175]:line(*xy(a[0],a[1]+delta),*xy(b[0],b[1]+delta),GRAY,.65,[3,2])
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
# Primary dimension chains: outer faces of future 350 perimeter to red centerlines.
for a,b in zip([REF['A'],15093,20691.5,REF['C']],[15093,20691.5,REF['C']]):dh(a,b,Y0,143)
dh(REF['A'],REF['C'],Y0,119,'21 247 - vonkajšie líca horného obvodu 350*')
for a,b in zip([REF['B'],10862,19185,REF['D']],[10862,19185,REF['D']]):dv(a,b,RIGHT,707)
dv(REF['B'],REF['D'],RIGHT,741,'18 681 - vonkajšie líca horného obvodu 350*')
dh(21393,27691,21685,722,'6 298 - medzi osami obvodu')
dv(3354,10849,X0,40,'7 495 - medzi osami obvodu')
tag('A',REF['A'],4300,-17,0);tag('B',12000,REF['B'],0,-17);tag('C',REF['C'],5400,15,0);tag('D',22500,REF['D'],0,-20)
txt(400,93,'ULICA / VSTUP',10,True,NAVY,'center')
# Small explanation in courtyard, without crossing plan lines.
leftx=80;y=681
txt(leftx,y,'REFERENCIE A - D',12,True);y-=17
y=para(leftx,y,370,'A ľavé, B uličné, C pravé a D zadné <b>vonkajšie líce navrhovaného horného obvodu širokého 350 mm</b>. Sivá prerušovaná čiara.',9)
y=para(leftx,y,370,'Modrá značí iba rozsah už vyliateho spodného obvodu. Jeho skutočné hrany nie sú zamerané; šírka modrej čiary nie je kóta.',9)
line(leftx,y-6,leftx+24,y-6,RED,3);txt(leftx+34,y-9,'Červená = nové rebrá, pracovná šírka 350*',9);y-=30
y=para(leftx,y,370,'*350 mm = šírka betónového rebra, nie šírka výkopu ani spodnej pätky. Prevzatá zo staršej štúdie; pre 4 rebrá staticky nepotvrdená.',9,RED)
y=para(leftx,y,370,'Pôdorys kótuje polohu osí voči hranám A-D. Presné vzdialenosti k obom hranám rebra sú v tabuľke vpravo. Líce rebra = os ±175 mm.',9)
txt(leftx,y-5,'Mierka 1 : 100 pri tlači A3 / 100 %',9,True)
line(leftx,y-25,leftx+50*MM,y-25,NAVY,1.3)
for p in [leftx,leftx+50*MM]:line(p,y-29,p,y-21,NAVY,1)
txt(leftx,y-41,'Kontrolná úsečka 50 mm na papieri = 5 000 mm v modeli.',8)
# Right technical panel.
px=791;pw=W-px-28;py=738
txt(px,py,'KÓTY OD OKRAJA PO REBRO',12,True);py-=15
py=para(px,py,pw,'Všetko v mm. Meranie kolmo dovnútra od modelovej vonkajšej hrany A/B/C/D.',9)
rows=[['Rebro / od','Bližšia hrana','Os','Vzdialenejšia hrana']]
for r in routes:rows.append([r['id']+' / '+r['reference'],number(r['near_face_distance_mm']),number(r['axis_distance_from_reference_mm']),number(r['far_face_distance_mm'])])
py=table(px,py,pw,rows,[65,98,83,pw-246])
py=para(px,py,pw,'Príklad R7: od A po prvú hranu 8 299; ďalších 350 tvorí šírka rebra. Jeho os je od A 8 474.',9)
py=para(px,py,pw,'R1 sa meria <b>sprava od C smerom doľava</b>. R4 sa meria <b>zozadu od D smerom k ulici</b>. R2 od B smerom do záhrady.',9)
rows=[['Rebro','Šírka*','Dĺžka medzi osami obvodu']]+[[r['id'],'350',number(r['axis_length_mm'])] for r in routes]
py=table(px,py,pw,rows,[65,75,pw-140])
py=para(px,py,pw,'Dĺžka medzi osami neurčuje kotevnú dĺžku ani koniec výstuže. Svetlé medzery medzi 350mm hornými pásmi: R1/R7 = 7 145; R2/R4 = 5 948.',9)
py=para(px,py,pw,'<b>Detail pri L-rohu:</b> R1 a R2 nie sú jeden uzol. Ich osi sú v X vzdialené 701,5. R2 je v modeli o 13 mm smerom do záhrady oproti osi horného obvodu hlavného traktu; nevyrovnávať ich z obrázka.',9)
py=para(px,py,pw,'<b>Pred betonážou:</b> preniesť model na zameraný obvod a potvrdiť prierezy, podopretie, výstuž a spoje pre zostavu štyroch rebier. Tento list nedokladá ich únosnosť.',9,RED)
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
header('ZK-02','REFERENČNÉ HRANY A KONTROLA KÓT',2)
lx=35;lw=553;rx=619;rw=W-rx-35;yy=735
txt(lx,yy,'1 / ČO JE NAOZAJ OKRAJ A - D',13,True);y=yy-20
y=para(lx,y,lw,'Modelové líca horného 350mm obvodu sú odvodené z jeho osí. Nie sú to hrany fasády s izoláciou a nie sú to zamerané hrany už vyliateho pásu.',10)
y=table(lx,y,lw,[['Referencia','Os horného obvodu','Modelové vonkajšie líce'],['A - ľavá','X = 6 794','X = 6 619'],['B - uličná','Y = 3 354','Y = 3 179'],['C - pravá','X = 27 691','X = 27 866'],['D - zadná','Y = 21 685','Y = 21 860']],[137,185,lw-322])
y=para(lx,y,lw,'Súradnice referencií sú v lokálnom rámci modelu C/B/B. A je 179 mm vpravo od architektonického ľavého obrysu; B 179 mm za uličným obrysom; C 174 mm dovnútra od pravého obrysu; D 175 mm dovnútra od zadného obrysu.',9)
txt(lx,y-6,'2 / AK SA MERIA OD DNEŠNÉHO SPODNÉHO BETÓNU',12,True);y-=24
y=para(lx,y,lw,'Tabuľka nižšie platí <b>iba vtedy, ak je dnešný pás súosý s modelom</b> a má v mieste merania presne uvedenú šírku. Súososť sa nepotvrdila. Pri odchýlke sa kóty prepočítajú podľa zameraného líca.',10,RED)
rows=[['Rebro / smer','Pás 400: do hrany / osi','Pás 380: do hrany / osi']]
for r in routes:rows.append([r['id']+' / '+r['reference'],number(r['existing_400_outer_face_to_near_rib_face_if_concentric_mm'])+' / '+number(r['existing_400_outer_face_to_axis_if_concentric_mm']),number(r['existing_380_outer_face_to_near_rib_face_if_concentric_mm'])+' / '+number(r['existing_380_outer_face_to_axis_if_concentric_mm'])])
y=table(lx,y,lw,rows,[110,222,lw-332])
y=para(lx,y,lw,'Vzťah: vzdialenosť od vonkajšieho líca do osi rebra = vzdialenosť modelových osí + polovica skutočnej šírky referenčného pásu. Do bližšieho líca rebra odpočítať 175 mm. Pri nesúososti pridať zameranú podpísanú korekciu.',9)
y=para(lx,y,lw,'Pri páse 380 mm je jeho vonkajšie líce o 10 mm bližšie k vlastnej osi než pri páse 400 mm. Táto 10mm zmena nie je toleranciou stavby a nevyjadruje neznámu odchýlku polohy celého pásu.',9)
assert y>65,y

txt(rx,yy,'3 / CELÉ REŤAZCE A NEZÁVISLÁ KONTROLA',13,True);y=yy-20
y=para(rx,y,rw,'Vodorovne A → os R7 → os R1 → C:<br/><b>8 474 + 5 598,5 + 7 174,5 = 21 247</b><br/>Zvisle B → os R2 → os R4 → D:<br/><b>7 683 + 8 323 + 2 675 = 18 681</b>',10)
y=table(rx,y,rw,[['Voľná vzdialenosť medzi lícami*','mm'],['Vnútorné ľavé líce obvodu → R7','7 949'],['R7 → R1','5 248,5'],['R1 → vnútorné pravé líce obvodu','6 649,5'],['Vnútorné uličné líce obvodu → R2','7 158'],['R2 → R4','7 973'],['R4 → vnútorné zadné líce obvodu','2 150']],[rw-110,110])
y=para(rx,y,rw,'*Pri všetkých horných obvodových pásoch aj rebrách širokých 350 mm. Reťazce sú geometrické, nepreukazujú podopretie dosky ani realizovateľnosť spojov.',9)
txt(rx,y-4,'4 / PRENOS NA STAVBU',12,True);y-=22
y=para(rx,y,rw,'1. Zamerať skutočné vnútorné a vonkajšie líca vyliatych pásov, rohy, šírky a výšky.<br/>2. Skontrolovať súlad s modelovým rámcom a preniesť referencie A-D; určiť prípadné odchýlky.<br/>3. Po potvrdení 350mm prierezu vytýčiť os každého rebra a obe hrany ±175 mm.<br/>4. Skontrolovať väzbu na steny, pravé uhly a L-roh. Odsúhlasiť nosnú funkciu, podopretie a výstuž pred výkopom či betonážou.',9.7)
y=para(rx,y,rw,'Zdroj kót: inputs/client-agreed-layout.json + geometry.json. Pracovná šírka 350 mm: pôvodná štúdia foundation-results.json, R1-R7. Žiadne nové určenie výšky, spodnej pätky ani výstuže.',9)
y=para(rx,y,rw,'Rámec overenia pred realizáciou: JRC, Implementation of Design during Execution & Service Life (orientačný odborný podklad, nie schválenie tejto stavby).',8)
c.linkURL('https://eurocodes.jrc.ec.europa.eu/publications/implementation-design-during-execution-service-life',(rx,y,rx+rw,y+33),relative=0,thickness=0)
assert y>58,y
c.save()

# Machine-readable arithmetic review for this drawing, separate from engineering checks.
assert sum(DATA['X_chain_mm'])==REF['C']-REF['A']==21247
assert sum(DATA['Y_chain_mm'])==REF['D']-REF['B']==18681
for r in routes:
 assert r['far_face_distance_mm']-r['near_face_distance_mm']==350
 assert r['axis_distance_from_reference_mm']-r['near_face_distance_mm']==175
 assert r['existing_400_outer_face_to_axis_if_concentric_mm']-r['existing_380_outer_face_to_axis_if_concentric_mm']==10
qa={'status':'ARITHMETIC_AND_LAYOUT_NOT_STRUCTURAL_APPROVAL','page_count':2,'page_size':'A3 landscape','scale':'1:100 at actual size','exact_four_routes':[r['id'] for r in routes],'width_mm':350,'width_is_approved':False,'references_surveyed':False,'chains_and_350_widths':'PASS','visual_review':'PENDING','pdf_sha256':hashlib.sha256((OUT/'agreed-ribs-technical.pdf').read_bytes()).hexdigest()}
(BASE/'results/technical-drawing-qa.json').write_text(json.dumps(qa,ensure_ascii=False,indent=2)+'\n')
print('Created 2-page A3 technical drawing; model coordinates and conditional edge offsets verified.')
