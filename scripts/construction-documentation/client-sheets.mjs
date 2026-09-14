/** Additional measured brief sheets; deliberately no fabricated structural sizes. */
export function clientFoundationSheet(d,draw){
  const {text,line,rect,poly,paragraph,dimH,dimV,table,sheet}=draw;
  const f=d.clientBrief.foundations;
  let out=text(12,50,'MONOLIT DO ODNÍMATEĽNÉHO DEBNENIA · ZADANIE STAVEBNÍKA',4,'bold');
  out+=paragraph(12,62,'Horný pás 350 × 600 mm je zadaný rozmer. Podľa doplnenia stavebníka je doska vyliata aj s lodžiou a krytou terasou. Líca, výšky a výstuž treba zamerať; nepoužíva sa stratené debnenie.',805,3.3).svg;
  const x=90,y=114,w=f.requestedUpperStrip.widthMm/10,h=f.requestedUpperStrip.heightMm/10;
  out+=text(22,91,'Z1 · HORNÝ OBVODOVÝ MONOLIT · 1 : 10',3.5,'bold');
  out+=rect(x,y,w,h,'heavy','url(#concrete)')+dimH(x,x+w,y-9,y,'350')+dimV(y,y+h,x-14,x,'600');
  out+=line(x-40,y+h,x+w+85,y+h,'datum')+text(x+w+20,y+h-4,'Pracovná škára k staršej betonáži',2.9);
  out+=poly([[x-25,y+h],[x+w+25,y+h],[x+w+25,y+h+24],[x+w+9,y+h+20],[x+w-5,y+h+24],[x-4,y+h+20],[x-25,y+h+24]],'thin','url(#concrete)');
  out+=text(22,220,'Spodný pás: 600 mm v zemi podľa stavebníka.',3);
  out+=text(22,227,'Šírka, spodok a horné líce voči R0 zatiaľ nezamerané.',3);
  out+=text(22,234,'Prerušený obrys spodného pásu neurčuje jeho šírku ani výšku.',2.8,'bold');
  out+=paragraph(167,113,'Líca horného pásu voči nosnému murivu sa určia až po zameraní. Na výkrese preto nie je predpísané centrovanie muriva ani excentricita.',220,3).svg;
  out+=paragraph(167,141,'Zvislé prúty z fotografie: priemer, počet, rozstup, krytie a zakotvenie nie sú doložené. Existujúcu trhlinu skontrolovať na mieste pred nadbetónovaním dotknutého úseku.',220,3).svg;
  out+=text(432,91,'D1 · NOSNÁ DOSKA A INŠTALÁCIE · 1 : 10',3.5,'bold');
  out+=line(460,119,780,119,'heavy')+line(460,134,780,134,'unknown')+line(460,139,780,139,'unknown');
  out+=dimV(119,134,449,460,'150')+dimV(119,139,795,780,'200');
  out+=text(463,112,'Horné líce dosky: kóta voči R0 zatiaľ neurčená',2.9,'bold');
  out+=paragraph(460,154,'150–200 mm je rozsah požiadavky, nie zvolená hrúbka. Obidva dolné obrysy sú alternatívne hranice rozsahu; nejde o dve vrstvy betónu.',337,3).svg;
  out+=paragraph(460,183,'Nad nosnou doskou: vodovod a kanalizácia so spádmi → tepelné a systémové vrstvy → vykurovací poter → povrch. Bez dodatočných vrtov do dosky. Hrúbky, križovania a vývody cez obvod musí uzavrieť nový návrh.',337,3).svg;
  out+=text(12,262,'VNÚTORNÉ REBRÁ A ZÁKLADOVÁ PÔDA',3.7,'bold');
  out+=table(12,272,817,[['Prvok / rozhodnutie',.23],['Záväzné zadanie / nadväznosť',.43],['Čo ešte určuje návrh',.34]],[
    ['R1–R7 · vnútorné trasy','Monolitické, v horných 600 mm podľa stavebníka. Musia mať konkrétnu cestu prenosu zaťaženia do únosného podkladu alebo podpor.','Polohy, šírky, uloženie, výstuž a spoje podľa reakcií stien, stropu a krovu.'],
    ['Zásyp pod doskou','Stavebník požaduje zhutnenú zeminu. Vhodnosť existujúcej zeminy, vlhkosť, hutnenie po vrstvách a výsledná únosnosť nie sú overené.','Geotechnické posúdenie a merateľné podmienky prevzatia podkladu.'],
    ['Betón C16/20','Požadovaný pre pokračovanie; fotografie ani názov triedy nepotvrdzujú dodanú zmes alebo vhodnosť pre všetky prvky.','Doklad o dodávke, expozičné triedy, krytie a statická únosnosť. Sokel posúdiť samostatne.'],
    ['Škáry a monolit','Spodný pás už bol betonovaný. Nová horná časť bude mať pracovnú škáru; monolitický systém neznamená betonáž bez škáry.','Príprava a posúdenie styku, prenos šmyku, zakotvenie a postup betonáže.'],
    ['Ťažké priečky SA30','AK-01/02 zaťažujú dosku aj ako nenosné priečky. Ich vlastná hmotnosť je vyčíslená na ZA-01; kandidátna trasa R7 na ZA-03.','Posúdiť existujúcu dosku a podopretie oboch plášťov. SA30 ani H200 neslúžia ako potvrdené podpery strechy alebo stropu.'],
  ],18).svg;
  out+=text(12,394,'VÝŠKA PODLAHY SA NAVRHNE Z NADVÄZUJÚCICH ÚROVNÍ',3.5,'bold');
  out+=text(12,407,'Všetko v mm: ΔFFL = zE + 600 + j + p',3.4,'bold');
  out+=paragraph(12,417,'zE = zameraný vrch existujúceho spodného pásu nad R0; j = vrch dosky mínus vrch nového pásu; p = úplná podlahová skladba nad doskou.',800,2.9).svg;
  out+=table(12,429,817,[['Možný styk dosky s pásom',.43],['Výšková väzba; styk a únosnosť musí určiť návrh',.57]],[
    ['Horné líca dosky a nového pásu zarovnané','j = 0; hrúbka dosky sa k vrchu pásu znova nepripočíta.'],
    ['Celá doska uložená nad novým pásom','j = hrúbka dosky; 150–200 mm je zatiaľ len požadovaný rozsah.'],
  ],10).svg;
  return sheet(d,'D1.1.ZA-02','Monolitické založenie · rozmery a väzby',out,'Rozmery 350/600/150–200 mm pochádzajú zo zadania stavebníka. Zameranie a statické overenie chýbajú. Nejde o výkres výstuže ani pokyn na pokračovanie betonáže.','1 : 10');
}

export function clientServicesSheet(d,draw){
  const {text,rect,paragraph,table,sheet,planMap,mm}=draw;
  const {svg,u,v}=planMap(d,35,48), excluded=d.clientBrief.services.heatedRoomExclusions;
  let out='<defs><pattern id="heat-area" width="4" height="4" patternUnits="userSpaceOnUse"><rect width="4" height="4" fill="white"/><circle cx="2" cy="2" r=".3" fill="black"/></pattern><pattern id="no-heat" width="3" height="3" patternUnits="userSpaceOnUse"><rect width="3" height="3" fill="#eee"/><path d="M0 0L3 3M3 0L0 3" stroke="black" stroke-width=".1"/></pattern></defs>';
  for(const room of d.rooms)for(const r of room.rectsMm)out+=rect(u(r.x0),v(r.y1),(r.x1-r.x0)/50,(r.y1-r.y0)/50,'hair',excluded.includes(room.number)?'url(#no-heat)':'url(#heat-area)');
  const s=d.showerFootprint;
  out+=rect(u(s.x0),v(s.y1),(s.x1-s.x0)/50,(s.y1-s.y0)/50,'unknown','url(#no-heat)');
  out+=svg;
  out+=text(535,50,'ROZSAH PODLAHOVÉHO VYKUROVANIA',3.7,'bold');
  out+=table(535,60,290,[['Miestnosť',.2],['Rozsah zadania',.8]],d.rooms.map(r=>[r.number,excluded.includes(r.number)?'Bez podlahového vykurovania':r.number==='1.05'?'Áno; okrem sprchovej plochy':'Podlahové vykurovanie']),10).svg;
  out+=rect(535,226,12,7,'thin','url(#heat-area)')+text(553,231,'Priestor s požadovaným vykurovaním',2.7);
  out+=rect(535,238,12,7,'thin','url(#no-heat)')+text(553,243,'Vylúčený priestor / sprcha',2.7);
  out+=paragraph(535,262,`Sprcha z modelu: X ${mm(s.x0)}–${mm(s.x1)}; Y ${mm(s.y0)}–${mm(s.y1)} mm. Slovo „sprcha“ je vyložené ako sprchová plocha; vylúčenie celej kúpeľne 1.05 nebolo zadané.`,290,3).svg;
  out+=paragraph(535,310,'Bodkovaná plocha znamená požadovaný rozsah vykurovania, nie kladačský plán rúrok. Nábytok, steny a zariadenia, tepelné straty, okruhy, rozstupy a regulácia musia vstúpiť do samostatného výpočtu.',290,3).svg;
  out+=paragraph(535,360,'POVALA: potvrdená iba na odkladanie vecí. Drevené stropy a záklop, bez betónovej stropnej dosky a nadbetonávky. Rozsah zahŕňa garáž aj technickú; nad 1.03 zostáva otvorená katedrála. Skladovacie a bodové zaťaženia ešte treba navrhnúť.',290,3.1,'bold').svg;
  out+=text(12,445,'VODA A ODPAD NAD NOSNOU DOSKOU · ŽIADNE DODATOČNÉ VRTY DO DOSKY',3.5,'bold');
  out+=paragraph(12,456,'Výšky trasovania, priemery, spády, izolačné hrúbky, vývody cez obvod a skladby vykurovaných aj nevykurovaných podláh zostávajú súčasťou nového profesijného návrhu.',800,3).svg;
  return sheet(d,'D1.1.TZ-01','Podlahové vykurovanie a rozsah povaly',out,'Pôdorysná geometria bez zmeny. Nové požiadavky stavebníka sú zakreslené k miestnostiam; list nie je výpočtom kúrenia ani statickým návrhom pochôdzneho stropu.');
}
