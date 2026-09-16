"""Build the ten-page A4 report and vector figures from calculation JSON."""
import json, math, re, csv, sys, html, base64
from pathlib import Path
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.graphics.shapes import Drawing, Rect, Line, String, PolyLine, Polygon as GPolygon, Circle
from reportlab.graphics import renderPDF, renderSVG
BASE=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(BASE/'.deps'))
from shapely.geometry import shape
FONT=Path('/Users/davidzita/.cache/codex-runtimes/codex-primary-runtime/dependencies/native/poppler/poppler/fonts')
if not (FONT/'DejaVuSans.ttf').exists(): FONT=Path('/usr/share/fonts/truetype/dejavu')
pdfmetrics.registerFont(TTFont('DV',str(FONT/'DejaVuSans.ttf')))
bold=FONT/'DejaVuSans-Bold.ttf'
pdfmetrics.registerFont(TTFont('DVB',str(bold if bold.exists() else FONT/'DejaVuSans.ttf')))
pdfmetrics.registerFontFamily('DV',normal='DV',bold='DVB',italic='DV',boldItalic='DVB')
R=json.loads((BASE/'results/foundation-results.json').read_text()); S=json.loads((BASE/'results/slab-results.json').read_text()); G=json.loads((BASE/'inputs/geometry.json').read_text())
AGREED=json.loads((BASE/'inputs/client-agreed-layout.json').read_text())
DIMENSIONS=json.loads((BASE/'results/agreed-ribs-dimensions.json').read_text())
W,H=A4; M=34; CW=W-2*M
NAVY=colors.HexColor('#18334a'); BLUE=colors.HexColor('#287399'); GREEN=colors.HexColor('#3c7966'); ORANGE=colors.HexColor('#a55c20'); GRAY=colors.HexColor('#7c8389'); LIGHT=colors.HexColor('#edf2f5'); RED=colors.HexColor('#a73932')
sty=ParagraphStyle('body',fontName='DV',fontSize=9.1,leading=12.5,textColor=NAVY,spaceAfter=5)
small=ParagraphStyle('small',parent=sty,fontSize=8.2,leading=10.7)
heading=ParagraphStyle('head',parent=sty,fontName='DVB',fontSize=11.5,leading=15)
c=canvas.Canvas(str(BASE/'report.pdf'),pagesize=A4); c.setTitle('DOM C/B/B - C16/20: výpočtová štúdia základov')
md=['**Revízia AK-01/AK-02, 16. 9. 2026:** aktuálne je SM30, jedna 300 mm obvodová tehla so zachovaným účelom odhlučnenia. Táto štúdia používa zmrazené pôvodné zaťaženia SA30; výsledky pre stenové zaťaženia a R7 sa nepovažujú za prepočet SM30. Konkrétny výrobok a nový prepočet zostávajú otvorené. Samostatné geometrické kóty a výpočty bez stenového zaťaženia týmto nie sú prerátané. Pozri [záznam revízie](/Users/davidzita/www/dom/foundation-analysis/inputs/wall-revision-sm30-20260916.md).\n']; page=0; y=0; qa=[]
def plain(t):return html.unescape(re.sub('<[^>]+>','',t))
def start(title):
 global page,y
 if page:c.showPage()
 page+=1; y=H-M
 c.setFillColor(RED);c.setFont('DV',8)
 c.drawString(M,H-12,'REVÍZIA 16. 9. 2026: AK-01/02 = SM30, jedna 300 mm obvodová tehla.')
 c.drawString(M,H-23,'Staré stenové zaťaženia SA30 neplatia pre SM30; nový výrobok a prepočet čakajú.')
 c.setFillColor(NAVY);c.setFont('DVB',16);c.drawString(M,y-16,title);y-=30
 c.setStrokeColor(BLUE);c.line(M,y,W-M,y);y-=13
 c.setFont('DV',7.5);c.setFillColor(GRAY);c.drawString(M,20,'DOM C/B/B | revízia 16. 9. 2026 | Podmienená štúdia - nie realizačný projekt');c.drawRightString(W-M,20,f'{page}/10')
 if page>=3:
  c.setFont('DV',7);c.setFillColor(RED);c.drawString(M,31,'Pôvodná schéma R1-R17; neoveruje 4 rebrá ani nový výklad osí spodného betónu zo strany 2.')
 md.append('\n## '+title+'\n')
def p(t,style=sty):
 global y
 q=Paragraph(t,style);w,h=q.wrap(CW,1000); y-=h;q.drawOn(c,M,y);y-=6;md.append(plain(t)+'\n');guard()
def h(t):p(t,heading)
def guard():
 if y<35:raise RuntimeError(f'Page {page} content overflow y={y}')
def table(rows,widths=None):
 global y
 widths=widths or [CW/len(rows[0])]*len(rows[0])
 cells=[[Paragraph(str(x),small) for x in row] for row in rows]
 t=Table(cells,colWidths=widths,hAlign='LEFT');t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),LIGHT),('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('LEFTPADDING',(0,0),(-1,-1),5),('RIGHTPADDING',(0,0),(-1,-1),5),('LINEBELOW',(0,0),(-1,0),.7,BLUE),('LINEBELOW',(0,1),(-1,-1),.25,colors.HexColor('#d4dde2'))]))
 _,hh=t.wrap(CW,1000);y-=hh;t.drawOn(c,M,y);y-=8
 md.append('| '+' | '.join(plain(str(z)) for z in rows[0])+' |\n| '+' | '.join('---' for _ in rows[0])+' |\n'+'\n'.join('| '+' | '.join(plain(str(z)) for z in row)+' |' for row in rows[1:])+'\n');guard()
def fig(d,name,height=None):
 global y
 renderSVG.drawToFile(d,str(BASE/'drawings'/f'{name}.svg'))
 renderPDF.drawToFile(d,str(BASE/'drawings'/f'{name}.pdf'))
 scale=min(CW/d.width,(height or d.height)/d.height)
 y-=d.height*scale;c.saveState();c.translate(M,y);c.scale(scale,scale);renderPDF.draw(d,c,0,0);c.restoreState();y-=7
 md.append(f'![{name}](drawings/{name}.svg)\n');guard()
def text(d,x,y,t,size=8.6,color=NAVY,bold=False,anchor='start'):
 d.add(String(x,y,t,fontName='DVB' if bold else 'DV',fontSize=size,fillColor=color,textAnchor=anchor))
def geometry(d,obj,fn,fill=None,stroke=GRAY,width=.7):
 poly=shape(obj)
 for a in ([poly] if poly.geom_type=='Polygon' else poly.geoms):
  d.add(GPolygon([v for xy in a.exterior.coords for v in fn(*xy)],fillColor=fill,strokeColor=stroke,strokeWidth=width))
  for interior in a.interiors:d.add(GPolygon([v for xy in interior.coords for v in fn(*xy)],fillColor=colors.white,strokeColor=stroke,strokeWidth=.3))
def plan(existing=False,variant=None):
 d=Drawing(CW,425);sc=19.6;ox=28;oy=26
 def xy(x,y):return ox+(x-6.2)*sc,oy+(y-2.8)*sc
 # orientation source Y points up = street at bottom, without reflection.
 for w in G['walls']:
  r=w['rect_m'];a,b=xy(r['x0'],r['y0']);d.add(Rect(a,b,(r['x1']-r['x0'])*sc,(r['y1']-r['y0'])*sc,fillColor=colors.HexColor('#e1e5e8'),strokeColor=None))
 geometry(d,R['geometry']['slab'],xy,None,GRAY,.4)
 geometry(d,R['geometry']['old'] if existing else R['geometry']['cap'],xy,colors.HexColor('#bec5ca') if existing else colors.HexColor('#bcd7e8'),GRAY if existing else BLUE,.6)
 if not existing:
  for pad in R['pads']:
   geometry(d,pad['polygon'],xy,colors.HexColor('#f5dfc5'),ORANGE,.7)
   px,py=xy(*pad['center']);text(d,px,py+3,pad['id'],8.5,ORANGE,True,'middle')
  for r in R['routes']:
   pts=[v for q in r['points'] for v in xy(*q)];d.add(PolyLine(pts,strokeColor=GREEN,strokeWidth=r['b']*sc,strokeLineCap=0))
  # Displace labels into small separate zones; leader lines identify exact route.
  occupied=[]
  for r in R['routes']:
   a,b=r['points'][0],r['points'][-1];px,py=xy((a[0]+b[0])/2,(a[1]+b[1])/2)
   tx,ty=px+4,py+5
   for trial in range(30):
    if not any(abs(tx-u)<23 and abs(ty-v)<10 for u,v in occupied):break
    ty+=11 if trial<8 else -15;tx+=4 if trial>8 else 0
   occupied.append((tx,ty));d.add(Line(px,py,tx,ty-1,strokeColor=GREEN,strokeWidth=.45));d.add(Rect(tx-1,ty-2,22,10,fillColor=colors.white,strokeColor=None));text(d,tx,ty,r['id'],8.0,GREEN,True)
  if variant=='MIN':
   # garage boundary only; upper surfaces remain flush
   geometry(d,R['geometry']['garage'],xy,None,ORANGE,1.4)
 # A few spatial anchors in open zones.
 text(d,*xy(8.3,6.8),'GARÁŽ',9,GRAY,True);text(d,*xy(23.6,16),'OBÝVAČKA',9,GRAY,True)
 text(d,*xy(22.8,20.7),'TERASA',8.5,GRAY);text(d,*xy(16.0,12.1),'DVOR',9,GRAY)
 # Dimension strings source model outline and critical main support coordinates.
 a,b=xy(6.44,2.45),xy(28.04,2.45);d.add(Line(*a,*b,strokeColor=NAVY,strokeWidth=.5))
 for xx in [a[0],b[0]]:d.add(Line(xx,a[1]-3,xx,a[1]+3,strokeColor=NAVY,strokeWidth=.5))
 text(d,(a[0]+b[0])/2,a[1]-11,'21 600 - architektonický obrys',8.5,NAVY,False,'middle')
 a,b=xy(28.7,3),xy(28.7,22.035);d.add(Line(*a,*b,strokeColor=NAVY,strokeWidth=.5))
 text(d,a[0]+5,(a[1]+b[1])/2,'19 035',8.2)
 text(d,*xy(13.2,3.05),'ULICA / Y = 3,000 m',8.5,NAVY,True)
 text(d,6,412,'PÔVODNÁ VÝPOČTOVÁ SCHÉMA 17 TRÁS; nie dohoda zo 16. 9.',8.5,RED,True)
 text(d,6,400,'Sivá: existujúci pás (deklarovaný) | modrá: nový obvod | zelená: nové trasy',8.0)
 if existing:
  text(d,65,295,'Existujúce vnútorné základy nie sú doložené.',9.2,RED)
  text(d,65,280,'Spodné pásy: b = 380-400; h betónu ≈ 600.',9.2)
  text(d,65,265,'Osi ani hĺbka škáry pod terénom nie sú zamerané.',9.2)
 return d
def agreed_plan(existing_only=False):
 """User's four red strokes, on model axes; no implied section or support design."""
 d=Drawing(CW,445);sc=19.6;ox=28;oy=26
 blue=colors.HexColor(AGREED['existing_perimeter']['color']);red=colors.HexColor(AGREED['rib_color'])
 def xy(x,y):return ox+(x-6.2)*sc,oy+(y-2.8)*sc
 pts=[v for q in G['outline_m'] for v in xy(*q)]
 d.add(GPolygon(pts,fillColor=colors.HexColor('#f5f7fa'),strokeColor=colors.HexColor('#cad1d9'),strokeWidth=.5))
 for wall in G['walls']:
  r=wall['rect_m'];a,b=xy(r['x0'],r['y0']);d.add(Rect(a,b,(r['x1']-r['x0'])*sc,(r['y1']-r['y0'])*sc,fillColor=colors.HexColor('#cbd1d8'),strokeColor=None))
 # Rear wall of garage is context only, absent from the four red strokes.
 for rib in G['ribs_prior_candidates']:
  if rib['id'] in ['R4','R5','R6']:
   d.add(PolyLine([v for q in rib['points_m'] for v in xy(*q)],strokeColor=colors.HexColor('#cbd1d8'),strokeWidth=3))
 per=AGREED['existing_perimeter']['points_m'];per=per+[per[0]]
 d.add(PolyLine([v for q in per for v in xy(*q)],strokeColor=blue,strokeWidth=6,strokeLineJoin=1))
 oldper=G['perimeter_axis_m']+[G['perimeter_axis_m'][0]]
 d.add(PolyLine([v for q in oldper for v in xy(*q)],strokeColor=GRAY,strokeWidth=.7,strokeDashArray=[3,2]))
 if not existing_only:
  for rib in AGREED['agreed_ribs']:
   d.add(PolyLine([v for q in rib['points_m'] for v in xy(*q)],strokeColor=red,strokeWidth=5,strokeLineCap=0))
   a,b=rib['points_m'];mx,my=(a[0]+b[0])/2,(a[1]+b[1])/2
   if a[0]==b[0]:tx,ty=xy(mx+.30,7.06)
   else:tx,ty=xy(mx,my+.28)
   d.add(Rect(tx-2,ty-2,23,13,fillColor=colors.white,strokeColor=None));text(d,tx,ty,rib['id'],10,red,True)
 for x,y,label in [(8.1,6.6,'GARÁŽ'),(7.8,9.8,'LODŽIA'),(11.65,9.2,'SPÁLŇA'),(16.1,9.2,'DETSKÁ IZBA'),(16.1,5.0,'DETSKÁ IZBA'),(23.4,4.8,'PRACOVŇA'),(24.1,8.55,'TECHNICKÁ'),(23.4,15.8,'OBÝVAČKA'),(23.55,14.95,'A KUCHYŇA'),(23.6,20.45,'TERASA')]:
  text(d,*xy(x,y),label,7.8,GRAY)
 # Legend occupies the clear courtyard, with the same orientation as the markup.
 text(d,42,370,'STAV A DOHODA',11,NAVY,True)
 text(d,42,354,'16. 9. 2026 · C / B / B',9,GRAY)
 d.add(Line(42,326,64,326,strokeColor=blue,strokeWidth=6));text(d,74,323,'Približné osi vyliateho obvodu',9,NAVY,True)
 if not existing_only:
  d.add(Line(42,300,64,300,strokeColor=red,strokeWidth=5));text(d,74,297,'4 dohodnuté nové rebrá',9.5,NAVY,True)
 text(d,42,265,'Horné debnenie a doska ešte nie sú vyliate.',8.7)
 text(d,42,244,'Garážový koniec: potvrdené predĺženie 800 mm.',8.3)
 text(d,42,229,'Sivá prerušovaná: pôvodná os horného pásu.',8.3)
 text(d,42,215,'Modrá a sivá os sa líšia približne o 350 mm.',8.3,RED)
 text(d,42,199,'Červené napojenia treba nanovo zosúladiť.',8.5,RED)
 a,b=xy(6.44,2.40),xy(28.04,2.40);d.add(Line(*a,*b,strokeColor=NAVY,strokeWidth=.5))
 for xx in [a[0],b[0]]:d.add(Line(xx,a[1]-3,xx,a[1]+3,strokeColor=NAVY,strokeWidth=.5))
 text(d,(a[0]+b[0])/2,a[1]-11,'21 600 mm · obrys modelu',8,NAVY,False,'middle')
 a,b=xy(28.7,3),xy(28.7,22.035);d.add(Line(*a,*b,strokeColor=NAVY,strokeWidth=.5))
 text(d,a[0]+4,(a[1]+b[1])/2,'19 035',8)
 text(d,*xy(16.5,3.65),'ULICA / VSTUP',8,NAVY,True)
 text(d,6,430,'VYLIATY OBVOD' if existing_only else 'VYLIATY OBVOD A ŠTYRI DOHODNUTÉ REBRÁ',12,NAVY,True)
 text(d,6,413,'Modrá = približná os spodného betónu, nie jeho vonkajšie líce.',8.5)
 return d
def sections():
 d=Drawing(CW,248)
 # equal scale transverse sections, dimensions in labels
 for x0,title,footw in [(22,'A / OBVOD - MEDIUM',.38),(285,'B / NOSNÉ REBRO - MEDIUM',.65)]:
  text(d,x0,232,title,10,NAVY,True);scale=120;cx=x0+92;base=25
  d.add(Rect(x0,23,235,3,fillColor=colors.HexColor('#baad95'),strokeColor=None))
  d.add(Rect(cx-footw/2*scale,base,footw*scale,.3*scale,fillColor=colors.HexColor('#bec5ca') if x0<100 else colors.HexColor('#bcd7e8'),strokeColor=GRAY))
  if x0<100:d.add(Rect(cx-.38/2*scale,base+.3*scale,.38*scale,.3*scale,fillColor=colors.HexColor('#bec5ca'),strokeColor=GRAY))
  else:d.add(Rect(cx-.35/2*scale,base+.3*scale,.35*scale,.3*scale,fillColor=colors.HexColor('#bcd7e8'),strokeColor=BLUE))
  d.add(Rect(cx-.35/2*scale,base+.6*scale,.35*scale,.6*scale,fillColor=colors.HexColor('#bcd7e8'),strokeColor=BLUE))
  d.add(Rect(cx+.35/2*scale,base+1.02*scale,95,.18*scale,fillColor=colors.HexColor('#bcd7e8'),strokeColor=BLUE))
  d.add(Rect(cx+.35/2*scale,base+.6*scale,95,.42*scale,fillColor=colors.HexColor('#e3d7bd'),strokeColor=GRAY,strokeWidth=.4))
  for dy in [.65,1.13]:
   for dx in [-.11,0,.11]:d.add(Circle(cx+dx*scale,base+dy*scale,2,fillColor=RED,strokeColor=None))
  for dy in [1.07,1.16]:d.add(Line(cx+.18*scale,base+dy*scale,cx+.9*scale,base+dy*scale,strokeColor=RED,strokeWidth=1.4))
  d.add(Rect(cx-.125*scale,base+.65*scale,.25*scale,.50*scale,fillColor=None,strokeColor=RED,strokeWidth=.65))
  if x0>100:
   d.add(Line(cx-(footw/2-.05)*scale,base+.05*scale,cx+(footw/2-.05)*scale,base+.05*scale,strokeColor=RED,strokeWidth=1))
  d.add(Line(cx-.3*scale,base+.6*scale,cx+.3*scale,base+.6*scale,strokeColor=ORANGE,strokeWidth=1,strokeDashArray=[3,2]))
  text(d,x0,10,'380-400 existujúci' if x0<100 else '650 × 300 nový základ',8.5)
  text(d,x0,205,'350 × 600 vrátane dosky; 3Ø14 hore aj dole',8.0)
  text(d,x0,192,'Doska 180; časť pod doskou 420',8.4)
  text(d,x0,179,'Zásyp 420 iba pre referenčné z = 0',8.1)
 text(d,10,1,'z = 0 je horné líce starého pásu; nové horné líce +600. Absolútne výšky CHÝBAJÚ.',8.2,RED)
 return d
def photo():
 global y
 ht=188;y-=ht
 c.saveState();clip=c.beginPath();clip.rect(M,y,CW,ht);c.clipPath(clip,stroke=0,fill=0)
 c.drawImage(str(BASE/'inputs/photos/IMG_7530.jpg'),M,y,width=CW,height=CW*.75,mask='auto');c.restoreState()
 markers=[(1,.48,.51),(2,.20,.36),(3,.66,.36)]
 for n,px,py in markers:
  c.setFillColor(ORANGE);c.circle(M+px*CW,y+py*ht,9,fill=1,stroke=0);c.setFillColor(colors.white);c.setFont('DVB',9);c.drawCentredString(M+px*CW,y+py*ht-3,str(n))
 imgdata=base64.b64encode((BASE/'inputs/photos/IMG_7530.jpg').read_bytes()).decode()
 svg=f'<svg xmlns="http://www.w3.org/2000/svg" width="{CW}" height="{ht}" viewBox="0 0 {CW} {ht}"><image href="data:image/jpeg;base64,{imgdata}" x="0" y="{ht-CW*.75}" width="{CW}" height="{CW*.75}"/>'
 for n,px,py in markers:svg+=f'<circle cx="{px*CW}" cy="{ht-py*ht}" r="9" fill="#a55c20"/><text x="{px*CW}" y="{ht-py*ht+3}" font-family="sans-serif" font-size="9" fill="white" text-anchor="middle">{n}</text>'
 (BASE/'drawings/photo-annotated.svg').write_text(svg+'</svg>')
 y-=15;md.append('![Aktuálny stav s anotáciami](drawings/photo-annotated.svg)\n')
def joint():
 d=Drawing(CW,112)
 text(d,5,100,'J / KANDIDÁT SPOJA - VÝSTUŽ NIE JE SCHVÁLENÁ NA REALIZÁCIU',9,RED,True)
 d.add(Rect(10,8,150,33,fillColor=colors.HexColor('#bec5ca'),strokeColor=GRAY))
 d.add(Rect(20,41,130,36,fillColor=colors.HexColor('#bcd7e8'),strokeColor=BLUE))
 d.add(Line(10,41,160,41,strokeColor=ORANGE,strokeWidth=1.2,strokeDashArray=[4,2]))
 for xx in [45,115]:d.add(Line(xx,19,xx,68,strokeColor=RED,strokeWidth=1.6))
 text(d,165,61,'2 rady Ø10/250; zapustenie300 mm*',8.3)
 text(d,165,46,'Oranžová: zdrsnená pracovná škára',8.3)
 text(d,165,31,'*Len geometrický kandidát; ETA a okrajové',8.3)
 text(d,165,18,'porušenie, šmyk, výstuž a trhliny neoverené.',8.3)
 return d

start('Základy C16/20: rozhodnutie a hranice návrhu')
p('<b>Existujúce pásy zatiaľ nemožno potvrdiť ako dostatočné.</b> Pri šírke 380 mm vychádza v skúmanom zaťažovacom obale tlak až 296 kPa pri excentricite 25 mm; pôvodná statika predpokladala 150 kPa. Hrubšia doska tento nedostatok základovej plochy neodstráni.')
p('<b>Nová revízia 16. 9.: betón vedie približne stredom obvodových čiar; garážový koniec bol predĺžený o800 mm.</b> Do koordinácie sa preberá šírka21 600 mm. Staré kóty od líc horného obvodu sú prekonané. Pôvodná os horného pásu je od takto interpretovaného spodného betónu odsadená asi350 mm; podopretie a napojenia štyroch rebier sa musia zosúladiť. Nasledujúce výpočty pre17trás tento stav neoverujú.')
table([['Variant','Výsledok výpočtu','Stav celého domu'],['MIN','150 mm izby / 180 mm garáž; miestne kontroly vyhovujú podmienene.','NEPREUKÁZANÝ'],['MEDIUM','180 mm všade; menší priehyb a jednoduchšie výškové detaily.','NEPREUKÁZANÝ'],['MAX','200 mm; vyššia rezerva kolesa nad dutinou 1,5 m.','NEPREUKÁZANÝ']],[63,310,CW-373])
p('Hlavné prekážky: skutočné podložie a základová škára, bodové reakcie krovu/povaly, neznáma výstuž a stav starého betónu, pracovné škáry, expozícia a 100-ročná trvanlivosť. Žiadny variant nemá status „pripravené na realizáciu“.')
photo()
p('Foto IMG_7530: <b>1</b> horné debnenie bez preukázanej betonáže; <b>2</b> navŕšená zemina s vegetáciou nie je prevzatý zásyp; <b>3</b> podpery debnenia. Fotografia nemá spoľahlivú mierku. Zvyšné dve fotografie dokladajú skorší otvorený výkop; presnú výstuž ani základovú škáru z nich neurčujem.',small)
p('<b>Potvrdenie investora 15. 9. 2026:</b> vyliate sú iba spodné pásy, horná konštrukcia a doska ešte nie. Starší zápis o vyliatej doske je týmto nahradený. Rozmer „35 cm“ zostáva bez významového potvrdenia; návrhových 350 × 600 mm je predpoklad tejto štúdie.',small)

start('Vyliaty obvod a dohodnuté štyri rebrá')
fig(agreed_plan(),'agreed-ribs',425)
# Separate existing-only drawing uses the same source and the same blue convention.
existing_drawing=agreed_plan(existing_only=True)
renderSVG.drawToFile(existing_drawing,str(BASE/'drawings/existing-state.svg'))
renderPDF.drawToFile(existing_drawing,str(BASE/'drawings/existing-state.pdf'))
rows=[['Rebro / od čiary*','Šírka**','Do bližšieho líca','Do osi','Do ďalšieho líca']]
refs={'A':'ľavý A','B':'uličný B','C':'pravý C','D':'zadný D'}
for r in DIMENSIONS['routes']:
 vals=[r['near_face_distance_mm'],r['axis_distance_from_reference_mm'],r['far_face_distance_mm']]
 rows.append([r['id']+' / '+refs[r['reference']],'350 mm']+[f'{z:g} mm'.replace('.',',') for z in vals])
table(rows,[119,68,116,103,CW-406])
p('<b>*Referencie sú teraz ČIARY:</b> A=X6440, B=Y3000, C=X28040, D=Y22035. Betón je podľa investora približne v ich strede; nejde o presné betónové hrany. <b>**350 mm je pracovná šírka zo štúdie so17trasami, pre4rebrá staticky nepotvrdená.</b> Staré kóty od vonkajších líc horného pásu už neplatia pre túto interpretáciu.',small)
p('<b>ZK-01/ZK-02:</b> drawings/technical/agreed-ribs-technical.pdf, A3, 1:100. Červené osi a konce zostali z modelu; ich napojenia na modrý obvod sú otvorené. OsR2 je338 mm pred L-rohom. Pôvodné osy horného pásu sú od modrých čiar349-354 mm; ich podopretie sa nesmie prevziať bez nového zosúladenia.',small)
p('Zdroj: nový obrázok8:56 a výslovné potvrdenie predĺženia garáže800 mm. Zdrojové19 050/10 840/14 550 sa líšia od modelových19 035/10 835/14 600 mm; rozdiely sú na listeZK-02. Strany3-10 sú pôvodná štúdia, nie výpočet novej interpretácie skutočného obvodu.',small)

start('Zaťaženia, existujúce pásy a sadanie')
p('Nosná cesta skúmaného systému: strecha + drevená skladovacia povala → skutočné nosné steny/prievlaky → obvodový sokel a nové vnútorné základy → rastlá zemina. Doska nesie podlahu a miestne úžitkové zaťaženie. SA30 a H200 nenesú strechu. Jej skutočné bodové reakcie nie sú nahradené plošným priemerom; výpočet nižšie je kontrolný <b>reakčný obal</b>, nie vyriešený globálny model krovu.')
table([['Parameter','Použitý predpoklad'],['Materiál / súčinitele','fck16; fctm1,9; Ecm28 600 MPa; fcd=0,85×16/1,5=9,07 MPa; B500B fyd434,8 MPa. αcc0,85 je konzervatívny predpoklad, nie overený český NDP.'],['Plošné a líniové zaťaženia','Strecha1,40 + drevený strop0,75 kN/m². Sneh0,80 kPa (sk1,0; bez dôkazu závejov). Povala 2,0 a 7,5 kPa - citlivostné prípady, nie odsúhlasené užívanie. Obvod: 300 mm murivo12 kN/m³ + 2×15 mm omietka18 kN/m³; h3,125 m.'],['Obvodový metrový úsek','Tributárna šírka4,10 m; Gk obsahuje aj veniec, nový sokel a starý pás. NEd=1,35Gk+1,50(Qk+sneh), bez zníženia súbehu ψ. B′=B−2e; qEd=NEd/B′.']],[146,CW-146])
rows=[['Povala kPa','NEd kN/m','qEd: e=0 / 25 mm','B nutná pri150 kPa*']]
for q in [2.,7.5]:
 z=[x for x in R['perimeter_load_envelopes'] if x['attic_q_kPa']==q and x['B_m']==.38];a=z[0];b=z[1];rows.append([f'{q:.1f}',f'{a["NEd_kN_m"]:.1f}',f'{a["qEd_kPa"]:.0f} / {b["qEd_kPa"]:.0f} kPa',f'{b["B_required_at_150kPa_m"]*1000:.0f} mm'])
table(rows,[95,100,180,CW-375])
p('*Ide o potrebnú celkovú šírku B pri zachovanom obale síl a e25 mm, nie o dovolenie priliať betón vedľa pásu. Pri rozšírení treba preniesť sily do novej plochy a zohľadniť vlastnú tiaž, podkopanie, pracovné etapy a sadanie. Tieto detaily pri neznámom podloží nie sú navrhnuté na realizáciu.',small)
rows=[['Eoed / vrstva2 m','s pri povale2,0','s pri povale7,5','Rozdielne sadanie']]
for E in [3000,8500,15000]:
 z=[x for x in R['settlement_sensitivity'] if x['Eoed_kPa']==E];rows.append([f'{E/1000:g} MPa',f'{z[0]["settlement_mm"]:.1f} mm',f'{z[1]["settlement_mm"]:.1f} mm','Pri E/2 sa s zdvojnásobí.'])
table(rows,[120,95,95,CW-310])
p('Kontrola s=N<sub>SLS</sub>·ln[(B+H)/B]/Eoed, B0,38 m: približné šírenie 2:1, bez odpočtu odťaženej zeminy; bez konsolidácie, objemových zmien a kolapsu. Projektové kritériá: s≤25 mm a Δs≤8 mm/4 m (1/500). Už Eoed8,5→4,25 MPa poruší diferenčné kritérium. Zásyp vedľa pásu pridáva napätie: široké priťaženie12 kPa na vrstve2 m pri Eoed8,5 MPa dá ďalších2,82 mm; skutočné etapy treba doplniť.',small)
rows=[['Sokel350×600, dutina2 m','MIN','MEDIUM','MAX']]
bs=[next(z for z in R['cap_robustness'] if z['variant']==v and z['span_m']==2) for v in ['MIN','MEDIUM','MAX']]
for label,key,key2 in [('MEd/MRd [kNm]','MEd_kNm','MRd_kNm'),('VEd/VRds [kN]','VEd_kN','VRds_kN_cot1'),('f / limit [mm]','deflection_fully_cracked_phi2_5_mm','deflection_limit_mm'),('w / limit [mm]','wk_characteristic_mm','wk_limit_mm')]:rows.append([label]+[f'{b[key]:.2f}/{b[key2]:.2f}' for b in bs])
table(rows,[191,111,111,CW-413])
p('MIN pri dutine2 m prekročí limit trhliny0,30 mm; MED a MAX týmto testom prejdú. Kontrola horného obvodového nosníka nezapočítava starý betón do ohybu. Neplatí pre celú dĺžku R1 ani automaticky pre užšie rebrá. Pri nosných vnútorných pásoch vychádza max. qEd MIN146,6 / MED136,1 / MAX127,1 kPa proti predpokladu150 kPa; bodové reakcie pri otvoroch zostávajú nepreukázané.',small)
p('Vietor: skúmané čisté tlaky0,8/1,5 kPa dávajú na čelnej ploche21,6×5,56 m vodorovne96/180 kN; výsledný návrhový vztlak strechy po odpočte0,9G je −15/+250 kN. Nejde o normové určenie vetra pre pozemok. Závej1,6 kPa pridá obvodu4,92 kN/m; lokálna PV sústava sa uvažuje osobitne3 kN. Voda0,6 m nad spodkom dosky dáva návrhový vztlak8,83 kPa oproti stabilizujúcemu MED5,85 kPa: <b>nevyhovuje bez ďalšieho opatrenia</b>. Tieto obaly odhaľujú potrebné kontroly; kotvy a stabilita celej stavby nie sú uzavreté.',small)

start('Pôvodná štúdia: množstvá pre 17 trás')
vs=R['variants'];rows=[['Nové práce od dnešného stavu','MIN','MEDIUM','MAX']]
for label,key,fmt in [('Doska izby / garáž [mm]',None,None),('Betón C16/20 celkom [m³]','concrete_m3','.2f'),('z toho doska [m³]','slab_m3','.2f'),('obvod/rebrá pod doskou [m³]','upper_below_slab_m3','.2f'),('nové spodné základy [m³]','new_lower_m3','.2f'),('Oceľ s prirážkami [kg]*','steel_kg_estimate','.0f'),('Debnenie účinných plôch [m²]*','formwork_m2','.1f'),('Nové ryhy, geometrický objem [m³]*','trench_excavation_m3','.1f'),('Zásyp pre referenčné výšky [m³]*','fill_geometric_m3','.1f')]:
 rows.append([label]+([f'{v["slab_m"]*1000:.0f} / {v["garage_slab_m"]*1000:.0f}' for v in vs] if key is None else [format(v[key],fmt) for v in vs]))
table(rows,[246,94,94,CW-434])
p(f'Betón je geometrický súčet bez prekrývania objemov. Nosná plocha dosky je {R["slab_structural_area_m2"]:.2f} m² po vonkajšie líce sokla, nie architektonických 252,965 m² po obálku domu. Zahŕňa lodžiu a terasu; ich povrchové a mrazové riešenie zostáva otvorené. Spoločný obvod má {R["perimeter_length_m"]:.3f} m, vnútorné trasy {R["internal_routes_length_m"]:.3f} m.')
delta1=vs[1]['concrete_m3']-vs[0]['concrete_m3'];delta2=vs[2]['concrete_m3']-vs[1]['concrete_m3'];ds1=vs[1]['steel_kg_estimate']-vs[0]['steel_kg_estimate'];ds2=vs[2]['steel_kg_estimate']-vs[1]['steel_kg_estimate']
p(f'<b>MIN → MEDIUM: +{delta1:.2f} m³ a približne +{ds1:.0f} kg ocele.</b> Jedna hrúbka180 mm odstraňuje výškový prechod garáže; pri dvojmetrovej dutine pod izbami klesá vypočítaný priehyb z {S["sections"]["MIN_RESIDENTIAL"]["cases"][2]["deflection"]["total_mm"]:.2f} na {S["sections"]["MEDIUM_RESIDENTIAL"]["cases"][2]["deflection"]["total_mm"]:.2f} mm. Širšie nové pásy znižujú kontaktné tlaky; existujúci obvod zostáva limitom.')
p(f'<b>MEDIUM → MAX: +{delta2:.2f} m³ a približne +{ds2:.0f} kg ocele.</b> Garáž zvládne skúmanú dutinu1,5 m, ktorú MEDIUM na šmyk nezvládne. Bez požiadavky na tento scenár je prínos podstatne menší než nárast ocele. MAX nie je dokázaná absolútna ekonomická hranica; zmenou technológie alebo podopretia môže vzniknúť lepšie riešenie.')
p('*Oceľ: siete a pozdĺžne prúty +15 % na presahy/odrezky, strmene a miestne prirážky; nejde o dielenský výkaz. Debnenie je hrubý technologický model. Ryhy uvažujú150 mm pracovného priestoru na každú stranu. Odhumusovanie0,20 m pridáva47,74 m³ odťažby a približne rovnakú potrebu náhradného zásypu pred odpočtom prienikov základov; tabuľka zásypu pokrýva iba priestor NAD z=0. Objednávka zásypu musí zahŕňať aj spodnú náhradu. Prekrývajúce výkopy sa nesmú sčítať dvakrát.',small)
p('<b>Cenový model:</b> C = Vbetón·pbetón + Moceľ·poceľ + Adebn·pdebn + Vvýkop·pvýkop + Vzásyp·pzásyp + Vodvoz·podvoz + kotvy + skúšky + práca. Sadzby sú prázdne, pretože porovnateľné miestne ponuky chýbajú. Nové podchytenie obvodu, hydroizolácia, mrazová ochrana, prípojky a konečné kotvy nie sú ocenené ani skryté v betóne.',small)
rows=[['Lokálne bloky (spoločné)','Rozmer X×Y [m]','P obal / qEd*']]
for pad in R['pads']:
 ch=next(z for z in R['pad_checks'] if z['id']==pad['id']);rows.append([pad['id']+' '+{'P1':'AKU800','P2':'kotol','P3':'kachle','P4':'terasa Z','P5':'terasa V','P6':'lodžia L'}[pad['id']],f'{pad["size"][0]:.2f} × {pad["size"][1]:.2f}',f'{pad["Pk"]} kN / {ch["qEd_kPa"]:.0f} kPa'])
table(rows,[222,150,CW-372])
p('*Predpokladané bloky od z−600 po+600 mm, spodná zóna350 mm: Ø12/150 oba smery dole aj hore, plášť Ø10/200 oboma smermi, nad tým všeobecná sieť dosky. Bodový obal zahŕňa tiaž podporovaného zariadenia/piliera aj prípadnú reakciu; sily nie sú dodané výrobcom/krovárom. Tlak predpokladá účinnú celú plochu. P4-P6 sa prekrývajú so starým pásom: bez navrhnutého prenosu do novej plochy NEPREUKÁZANÉ. Najvyšší skríningový šmyk0,289 MPa oproti0,351 MPa nenahrádza úplný dôkaz pretlačenia.',small)

for i,name in enumerate(['MIN','MEDIUM','MAX']):
 v=vs[i];start(f'{name}: pôvodná výpočtová schéma 17 trás')
 fig(plan(variant=name),f'plan-{name.lower()}',390)
 residential='Ø8/150' if name!='MAX' else 'Ø10/150';garage={'MIN':'Ø10/125','MEDIUM':'Ø10/100','MAX':'Ø12/150'}[name];dia=[12,14,16][i]
 table([['Prvok','Navrhnutý prierez / výstuž (podmienene)'],['Doska',f'{int(v["slab_m"]*1000)} mm; garáž {int(v["garage_slab_m"]*1000)} mm. {residential} izby, {garage} garáž - hore aj dole, oba smery. cnom35 mm; Dmax16 mm.'],['Obvod a R1-R7',f'350 × 600 mm vrátane dosky; časť pod doskou {600-int(v["slab_m"]*1000)} mm. 3Ø{dia} hore + 3Ø{dia} dole; strmene Ø8/200, pri uzloch Ø8/100 na600 mm.'],['Doplnkové R8-R17',f'Šírka300 alebo350 mm podľa routes.csv; H600 mm. Rovnaká pozdĺžna výstuž a strmene. Každá trasa má vlastnú súvislú podporu na rastlej zemine.'],['Spodné vnútorné základy',f'R1-R5 nosné trasy: {int(v["major_foot_width_m"]*1000)} × 300 mm; ostatné400 × 300 mm. Ø12/150 dole oba smery; stredný driek300 mm vysoký, šírka podľa rebra; zvislé Ø10/200 na oboch lícach.']],[122,CW-122])
 if name=='MIN':p('MIN je najnižšia spotreba v preskúmanej rodine. Nie je preukázané, že ide o najlacnejší vyhovujúci návrh celej stavby. V garáži sa180 mm zachováva kvôli šmyku; 150 mm s Ø10/125 zlyhalo. Oranžová hranica označuje modelový rozsah garáže; prechod hrúbky smeruje nadol, horné líce je rovné.',small)
 elif name=='MEDIUM':p('Nosné rebrá sa nepovažujú za nosníky preklenujúce celú dĺžku. Prirodzená zemina musí byť prevzatá pod celou trasou. Ak je pod R1 len zásyp a podpery iba na koncoch7,495 m, uvedená výstuž neplatí. SA30 zaťažuje R7 dvoma líniami ±100 mm; vrátane omietok a vaty model6,25 kN/m, priebežná chodba zostáva bez steny.',small)
 else:p('MAX zvyšuje ohybovú rezervu aj hmotnosť konštrukcie. Nespraví zo slabej zeminy únosný podklad. Ani200 mm doska nie je navrhnutá na zmiznutie všetkého zásypu. Vonkajšie časti vyžadujú oddelenie teplotných polí a doriešenie expozície; spoločná kresba neznamená automatický tuhý monolit.',small)
 p('Kóty polohy R1-R7 sú v tabuľke detailov; R8-R17 sledujú presné líniové osi všetkých zvyšných modelových stien v drawings/routes.csv. Každý identifikátor je naviazaný na wall-loads.csv; 37 úsekov je geometricky pokrytých. Polohy nie sú vytyčovacím podkladom bez zamerania starých pásov.',small)

start('Rezy, výstuž a pracovné škáry')
fig(sections(),'sections-medium',245)
table([['Trasa','Súradnice osi X/Y [m], pôvodný modelový rámec'],['R1 / R7','X20,6915 / X15,093; Y3,354 →10,849; dĺžka7,495.'],['R2 / R4','Y10,862 / Y19,185; X21,393 →27,691; dĺžka6,298.'],['R3','(23,4545;3,354)→(23,4545;5,2825)→(22,842;5,2825).'],['R5 / R6','R5: Y8,897; X6,794→10,993. R6: X10,993; Y8,897→10,849.']],[94,CW-94])
fig(joint(),'joint-medium',105)
p('<b>Výstužný detail MEDIUM:</b> cnom50 mm k betónovanému povrchu základov a sokla (pracovný predpoklad), 35 mm v doske. 3Ø14 pri každom hornom a dolnom líci; uzavreté strmene Ø8. Rovné kotevné dĺžky pri plnom fyd a dobrom súdržnom prostredí: Ø10≈558, Ø12≈669, Ø14≈780, Ø16≈892 mm. Návrh vyhradzuje 1000 mm za uzlom; v rohoch použiť L/U prúty, nie koniec rovného prúta na hrane. Presahy pri α6=1,5: približne840/1010/1170/1340 mm; rozmiestniť mimo uzlov. Súdržnosť hornej výstuže a skutočné podmienky betonáže treba overiť; zhoršené podmienky dĺžky zväčšujú.',small)
p('<b>Starý/nový betón:</b> odstrániť laitanciu a uvoľnené časti, zmapovať trhliny, overiť zdravý podklad, očistiť a zdrsniť; vlhkosť podľa technológie. Na preukázanie trenia sa ráta c=0, μ=0,5 iba pri overenom kontakte bez separačnej fólie: HEd≤μNEd,min. Pri zásype600 mm + stavebnom priťažení10 kPa vychádza HEd7,20 kN/m, vlastná tiaž sokla dáva len2,36 kN/m trenia. <b>Bez dočasného zavetrenia alebo schválených spojov nezásypovať jednostranne.</b>',small)
p('Kandidát kotvenia: dve rady dodatočných Ø10/250 s predbežne300 mm zapustením; pri fbd,PIR2,0 MPa je čisto súdržnostný limit18,85 kN/prút. To NIE JE únosnosť kotvy v šmyku ani okrajovom vylomení. Presné ETA, poloha pôvodnej výstuže, okraje, trhliny, rozštiepenie a 100-ročný návrh chýbajú; tento detail ostáva nepreukázaný. Spoje nových pásov sa plánujú mimo uzlov, výstuž priebežná; dodatočné otvory cez rebrá sa nepovoľujú týmto výpočtom.',small)

start('Doska: únosnosť, trhliny a strata podpory')
p('Doska je <b>podlahová doska na podloží</b>; nie základová doska domu ani doska voľne rozpätá cez celé L. Výpočtový stav: lokálna vnútorná nepodopretá ryha široká1,0 m, na oboch stranách spoľahlivé priame podopretie a ≥1,0 m zakotvenej výstuže. Obytné pole: g=25h+2 kPa, q=2 kPa. Garáž: jedno koleso10 kN na200×200 mm, účinok priradený iba200 mm širokému pásu; ďalšie koleso v tej istej ryhe, zdvihák a ťažšie auto nie sú pokryté.')
rows=[['Rozhodujúci prierez / L','MEd/MRd kNm/m','VEd/VRd kN/m','w /0,30 mm','f / L/250 mm']]
for key,L,label in [('MIN_RESIDENTIAL',1,'MIN izba /1,0'),('MEDIUM_RESIDENTIAL',2,'MED izba /2,0*'),('MIN_GARAGE',1,'MIN garáž/1,0'),('MEDIUM_GARAGE',1,'MED garáž/1,0'),('MAX_GARAGE',1.5,'MAX garáž/1,5*')]:
 sec=S['sections'][key];a=next(z for z in sec['cases'] if z['span_m']==L);rows.append([label,f'{a["MEd_kNm_per_m"]:.2f}/{sec["section"]["MRd_kNm_per_m"]:.2f}',f'{a["VEd_kN_per_m"]:.2f}/{sec["section"]["VRdc_kN_per_m"]:.2f}',f'{a["crack_characteristic_conservative"]["wk_mm"]:.3f}',f'{a["deflection"]["total_mm"]:.2f}/{a["deflection_limit_mm"]:.1f}'])
table(rows,[130,113,108,73,CW-424])
p('Využitie garáže L1 m: MIN ohyb63 %, šmyk97 %; MED ohyb52 %, šmyk90 %. *L1,5 a2 m sú testy robustnosti. Šmyková redukcia podľa EC2 6.2.2(6) používa polohu výslednice sily a platí iba pri priamom podopretí a plnom zakotvení; bez nej surový VEd71,89 kN/m prekročí aj MED66,46. Voľné okraje, prestupy a L-roh tento model nepokrýva.',small)
table([['Referenčná možnosť','Záver'],['100 mm, obe siete Ø8/150, c35','Vertikálna vôľa100−2×35−4×8=−2 mm: nemožno zrealizovať. Aj keď ohyb obytného pásu L1 m číselne vyjde, tento detail NEVYHOVUJE. Jedna sieť sa tu nepreukázala ako náhrada.'],['150 mm garáž, Ø10/125','Pri posúvaní kolesa VEd63,88>VRd51,80 kN/m: NEVYHOVUJE. Preto MIN garáž180 mm.'],['180 / 200 mm - robustnosť','MED garáž180 pri L1,5 m: šmyk68,58>66,46, nevyhovuje. MAX200 pri L1,5 m vyhovuje. Pri L2 m zlyhá šmyk73,43>71,16 a wchar0,337>0,30 mm.'],['Strata podpory4 m','Všetky zvolené obytné prierezy zlyhajú najmenej na priehybe. Je to hypotetický extrém, nie povinný návrhový stav.']],[151,CW-151])
p('Vzťahy: M=qL²/8+PL/4; MRd=As·fyd·(d−0,4x), x=As·fyd/(0,8bfcd); VRdc=max[0,12k(100ρfck)<super>1/3</super>; vmin]bd. Priehyb z plne popraskaného prierezu s Eeff=Ecm/(1+φ), φ1,5/2,5/3,5; trhliny wk=sr,max·(εsm−εcm). Výsledky tabuľky používajú prísnejšiu charakteristickú kontrolu trhlín; kvázistála je v JSON. Navierova 2D kontrola dosky1×1 m: M≈3,329 kNm/m oproti konzervatívnemu pásu19,847; 81→161 členov stabilizuje M, integrál zaťaženia má odchýlku0,18 %. Ide o kontrolu miestneho ohybu, nie celého domu.',small)
p('Plné zabránenie zmršťovaniu nevyhovuje automaticky minimálnej výstuži: potrebná klzná vrstva, rozdelenie polí a návrh škár. Uvažovať samostatné polia pri vnútornom rohu L, terase a lodžii; škáry nesmú prerušiť nosné rebrá. Konečné polohy, prenos kolesa cez škáry a teplotno-zmršťovacie účinky zostávajú otvorené.',small)

start('Podmienky dokončenia a kontrolné body')
h('C16/20 a životnosť približne 100 rokov')
p('Český sprievodca ČSN EN206+A2 / ČSN P73 2404 uvádza pre XC2 pri50 rokoch C16/20, w/c≤0,60, cement≥280 kg/m³. Nie je to doklad100-ročnej životnosti. XC3, XC4 a mrazové XF môžu vyžadovať inú špecifikáciu; preto treba C16/20 konštrukčne chrániť a overiť skutočné prostredie. Krytá terasa ani sokel automaticky neznamenajú „bez mrazu“. Hydroizolácia/radón, odvodnenie, nenasýtenie a tepelná ochrana sú súčasťou riešenia. Väčšie krytie výstuže samo nedokazuje100 rokov.',small)
h('Kontrolovaný zásyp a pôvodná zemina')
p('Odstrániť humus, korene, rozmočené a mrazom porušené vrstvy; výkopovú hlinu nepoužiť bez skúšok. Kandidát: doložená čistá dobre zrnená drť0/32 alebo0/63, materiálovo a vodne stabilná. Skúšobný úsek stanoví vlhkosť, počet prejazdov a hrúbku vrstvy; pracovný rozsah150-200 mm sa potvrdí konkrétnou mechanizáciou. Kontrolovať každú vrstvu, okolie potrubí, kúty a pätu rebier. Pôvodných Ev2≥40 MPa a pomer≤2,5 sa nepreberá ako dôkaz sadania. DPr, Ev2 a Eoed sa navzájom neprevádzajú. Preberanie musí potvrdiť model sadania vrátane prirodzenej zeminy; 98 % Proctor neznamená2 % budúceho sadnutia.',small)
table([['Kedy','Čo musí byť splnené'],['Pred zakrytím starých pásov','Zamerať oba líca, základovú škáru, hornú úroveň, terén a trhliny. Sondy pri rohoch, otvoroch a zmenách vrstiev; sken výstuže, dodacie listy, podľa nálezu jadrové skúšky. Overiť vodu, agresivitu a mráz.'],['Pred výkopmi vnútri','Uzavrieť geotechnický profil a reakcie strechy/povaly vrátane bodových a vodorovných síl. Navrhnúť etapy pri starých pásoch; neznížiť ich bočnú alebo spodnú podporu súvislým podkopaním.'],['Pred zásypom','Prevziať prirodzenú škáru každého nového základu. Skontrolovať bloky P1-P6, spoj starého/nového betónu a dočasné zavetrenie. Zdokumentovať skúšobné hutnenie a každú vrstvu.'],['Pred betonážou dosky','Prevziať výstuž, krytie, presahy, pracovné a dilatačné škáry, chráničky a výšky. Voda/odpad nad doskou podľa zadania. Potvrdiť zmesC16/20 vrátane expozície, konzistencie, kameniva a ošetrovania.'],['Po betonáži / pred zaťažením','Ošetrovanie podľa zmesi a počasia; nehutniť ani nezaťažovať čerstvé rebrá. Dokumentovať pevnosť, trhliny a výšky. Dovoliť murivo až po prevzatí a schválenom postupe.']],[118,CW-118])
p('<b>Normový rámec k15. 9. 2026:</b> ČSN EN1990 ed.2:2021; ČSN EN1991-1-1:2004, -1-3 ed.2:2024, -1-4 ed.2:2020 s príslušnými zmenami/NA; ČSN EN1992-1-1 ed.2:2019 a NA ed.A:2020; ČSN EN1997-1:2006; ČSN EN206+A2:2021 a ČSN P73 2404:2021/ed.2:2024. Katalógové vydania overené, celé rozhodujúce české NA a pravidlo100 rokov neboli prístupné. Výpočet preto nepredstiera úplnú normovú autorizáciu.',small)
p('Zdroje a presné URL: inputs/norms-and-ground.md a inputs/source-register.md. Primárne: eurocodes.jrc.ec.europa.eu (EC2 a EC7 príklady), transportbeton.cz (český sprievodca), csnonline.agentura-cas.cz (vydania), hilti.com (HIT-RE500V4, údaje12/2025). <b>Ďalší krok:</b> zameranie + geotechnik + reakcie krovu umožnia rozhodnúť o zachovaní pásov alebo vypočítať najmenšie účinné podchytenie. Konkrétny výsledný návrh musí pred realizáciou nezávisle skontrolovať príslušný autorizovaný odborník.',small)

assert page==10
c.save();(BASE/'report.md').write_text('# Dokončenie základov a dosky C16/20\n\nPodmienená výpočtová štúdia; hlavný PDF report má 10 strán A4.\n'+''.join(md))
# precise route coordinates and wall mapping; no approximate graphical measurement
with (BASE/'drawings/routes.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['id','points_XY_m','upper_width_m','total_upper_height_m','support','source_wall_ids'])
 for r in R['routes']:w.writerow([r['id'],json.dumps(r['points']),r['b'],.6,'continuous new footing on natural soil; not span beam',','.join(r['source_ids'])])
with (BASE/'drawings/agreed-ribs.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['id','model_points_XY_m','model_axis_length_m','status'])
 for r in AGREED['agreed_ribs']:w.writerow([r['id'],json.dumps(r['points_m']),r['length_m'],'MODEL AXES ONLY; endpoints require revision against newly declared perimeter centerlines; not final rib length or support design'])
with (BASE/'results/wall-loads.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['wall','routes','length_m','gk_kN_m','Gk_kN','status'])
 for a in R['wall_loads']:w.writerow([a['wall'],','.join(a['routes']),a['length_m'],a['gk_kN_m'],a['Gk_kN'],a['status']])
(BASE/'results/report-qa.json').write_text(json.dumps({'pages':page,'page_size':'A4','body_font_pt':9.1,'table_font_pt':8.2,'automatic_overflow_check':'passed','visual_review':'PENDING'},indent=2))
with (BASE/'results/cost-model.csv').open('w') as f:
 w=csv.writer(f);w.writerow(['item','unit','MIN_quantity','MEDIUM_quantity','MAX_quantity','unit_price_CZK_blank','scope_note'])
 for label,unit,key in [('New C16/20 concrete','m3','concrete_m3'),('Reinforcement estimated','kg','steel_kg_estimate'),('Formwork estimated','m2','formwork_m2'),('Trench excavation assumption','m3','trench_excavation_m3'),('Fill above old top only','m3','fill_geometric_m3'),('Organic soil stripping 0.2m scenario','m3','stripping_allowance_m3')]:w.writerow([label,unit]+[round(v[key],3) for v in R['variants']]+['','Conditional geometric estimate, not supplier quote'])
 for label in ['Fill replacement below old top after stripping','Spoil disposal loose volume','Geotechnical investigation and lift tests','Concrete testing and crack survey','Post-installed connection design and installation','Old perimeter underpinning if required','Waterproofing radon frost protection and thermal separation','Joint load transfer and sealing','Temporary bracing and trench support','Labour placing vibrating curing']:
  w.writerow([label,'to be measured','','','','','Not zero: scope/quantity/rate unresolved'])
print('Created report.pdf: 10 A4 pages; vectors and matching report.md.')
