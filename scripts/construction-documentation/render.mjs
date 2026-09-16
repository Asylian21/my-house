/** Vector drawing sheets. All drawing coordinates are PAPER mm, at fixed 1:50. */
import { clientFoundationSheet,clientServicesSheet } from './client-sheets.mjs';
import { foundationAxonSheet } from './foundation-axon.mjs';
export const PAPER={width:841,height:594,scale:50};
export const CUTS=[
  {id:'A-A',axis:'y',at:24540,from:2000,to:23035,title:'Pozdĺžny rez krídlom',why:'Pracovňa, H200, kúpeľňa, WC, nosná stena kuchyne, hrebeň obývačky a krytá terasa.'},
  {id:'B-B',axis:'x',at:18620,from:17040,to:30040,title:'Priečny rez katedrálovým stropom',why:'Obývačka 1.03, skutočný profil podhľadu, dymovod B a celá západná terasa.'},
  {id:'C-C',axis:'x',at:5000,from:5440,to:29040,title:'Priečny rez hlavným traktom',why:'Tretí rez je potrebný pre garáž, nočné krídlo, rozdielne podlahy a nosné línie.'},
];
export const GAPS=[
  {id:'R01',title:'Nový nosný systém',need:'Výpočet aktuálneho C/B/B, zaťaženie a reakcie, základy, doska, preklady, vence, oceľové rámy, krov a všetky spoje. Staré D1/D2 sú podľa stavebníka iba archív.',sheets:'ZA, RE, DT'},
  {id:'R02',title:'Monolit a založenie',need:'Podľa stavebníka je doska vyliata aj s lodžiou a krytou terasou. Horný pás zadaný 350 × 600 mm. Zamerať skutočný rozsah, výšky, hrúbku a výstuž; uzavrieť podopretie a nové rebrá.',sheets:'ZA, RE'},
  {id:'R03',title:'Nová podlaha s rozvodmi',need:'Rozvody vody a odpadu nad nosnou doskou; žiadne dodatočné vrty do dosky. Určiť horné líce dosky, kompletnú skladbu, priemery, spády, križovania a vývod cez obvod.',sheets:'RE, SK, ZTI'},
  {id:'R04',title:'Drevený strop a skladovacia povala',need:'Povala iba na odkladanie, mimo obývačky. Drevené stropy bez betónovej dosky/nadbetonávky. Určiť skladovacie a bodové zaťaženia, prierezy a spoje; krov s falcovaným plechom bez presahov.',sheets:'ST, RE, DT'},
  {id:'R05',title:'Spoločná nula a vstup',need:'R0 = 184,200 m pri ulici. Podlahu navrhne projekt podľa nivelácie hotového pásu a terénu; aspoň jeden vstupný stupeň. Návrh podesty pri D2 na SI-01. Potvrdiť Bpv a bod XY.',sheets:'SI, PO, RE'},
  {id:'R06',title:'Sokel, ETICS, otvory',need:'Nové detaily hydroizolácie a sokla, založenia ETICS, parapetov, prahov, nadpraží a napojenia tesniacich vrstiev. Výpis otvorov nie je výrobný rozmer rámu.',sheets:'PO, OT, DT'},
  {id:'R07',title:'Akustické priečky',need:'Vlastná hmotnosť AK-01/02/03 a jej prenos do základov, stabilita muriva a predsteny, kotvy a obvodové spoje. SM30 zaťažuje dosku aj ako nenosná priečka. Strecha a strop potrebujú samostatné nosné riešenie.',sheets:'ZA, RE, SK, DT'},
  {id:'R08',title:'Dymovody a odvodnenie',need:'Systémový návrh a odstupy dymovodu obývačky; kotolňa B končí v modeli rezervou pod stropom, vonkajšia trasa nie je určená. Návrh žľabov, zvodov a dažďovej kanalizácie.',sheets:'ST, PO, RE'},
  {id:'R09',title:'Dodávateľský výpis otvorov',need:'Profily, zasklenie, bezpečnostné/tepelné/akustické vlastnosti, montážne škáry, kovanie a prahy. Trojuholníkový svetlík doplnený O11 bez prečíslovania O1-O10/D1-D16.',sheets:'OT'},
];
const esc=v=>String(v??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const mm=n=>Number(n.toFixed(3)).toLocaleString('sk-SK',{maximumFractionDigits:3});
const level=n=>`M${n>=0?'+':''}${(n/1000).toFixed(3).replace('.',',')}`;
const join=a=>a.filter(Boolean).join('');
const line=(x1,y1,x2,y2,cls='thin',extra='')=>`<line x1="${x1}" y1="${y1}" x2="${x2}" y2="${y2}" class="${cls}" ${extra}/>`;
const rect=(x,y,w,h,cls='thin',fill='none')=>`<rect x="${x}" y="${y}" width="${Math.max(0,w)}" height="${Math.max(0,h)}" class="${cls}" fill="${fill}"/>`;
const poly=(pts,cls='thin',fill='none')=>`<polygon points="${pts.map(p=>p.join(',')).join(' ')}" class="${cls}" fill="${fill}"/>`;
const text=(x,y,t,size=2.8,cls='',anchor='start')=>`<text x="${x}" y="${y}" font-size="${size}" class="${cls}" text-anchor="${anchor}">${esc(t)}</text>`;
const circle=(x,y,r,t)=>`<circle cx="${x}" cy="${y}" r="${r}" fill="white" class="thin"/>${text(x,y+1,t,2.8,'bold','middle')}`;
function paragraph(x,y,str,width,size=3,cls=''){
  const words=String(str).split(/\s+/),rows=[];let row='';
  for(const word of words){if((row+' '+word).length*size*.54>width&&row){rows.push(row);row=word;}else row+=(row?' ':'')+word;}
  if(row)rows.push(row);
  return {svg:rows.map((r,i)=>text(x,y+i*size*1.5,r,size,cls)).join(''),height:rows.length*size*1.5};
}
function dimH(a,b,y,origin,label=mm(Math.abs(b-a)*50)){
  if(a>b)[a,b]=[b,a];
  return line(a,origin,a,y+2,'extension')+line(b,origin,b,y+2,'extension')+line(a,y,b,y,'dim')+line(a-1,y+1,a+1,y-1,'dim')+line(b-1,y+1,b+1,y-1,'dim')+text((a+b)/2,y-1.6,label,2.6,'dim halo','middle');
}
function dimV(a,b,x,origin,label=mm(Math.abs(b-a)*50)){
  if(a>b)[a,b]=[b,a];
  return line(origin,a,x+2,a,'extension')+line(origin,b,x+2,b,'extension')+line(x,a,x,b,'dim')+line(x-1,a+1,x+1,a-1,'dim')+line(x-1,b+1,x+1,b-1,'dim')+`<g transform="translate(${x-1.7} ${(a+b)/2}) rotate(-90)">${text(0,0,label,2.6,'dim halo','middle')}</g>`;
}
function spot(x,y,z,label='',side=1){
  return poly([[x,y],[x+side*2,y-2],[x+side*4,y]],'dim','white')+line(x,y,x+side*23,y,'dim')+text(x+side*5,y-1.5,`${level(z)}${label?' '+label:''}`,2.7,'dim halo',side===1?'start':'end');
}
function table(x,y,width,columns,rows,rowHeight=10){
  const widths=columns.map(c=>c[1]*width),heads=columns.map(c=>c[0]);let xx=x;
  let s=rect(x,y,width,10,'thin','#efefef');
  heads.forEach((h,i)=>{s+=text(xx+2,y+6,h,2.7,'bold');xx+=widths[i];});
  let yy=y+10;
  for(const row of rows){
    const cells=row.map((v,i)=>paragraph(0,0,v,widths[i]-4,2.6));
    const h=Math.max(rowHeight,...cells.map(c=>c.height+4));
    s+=rect(x,yy,width,h,'rule','white');xx=x;
    row.forEach((v,i)=>{s+=paragraph(xx+2,yy+4.5,v,widths[i]-4,2.6).svg;xx+=widths[i];});yy+=h;
  }
  xx=x;for(const w of widths){s+=line(xx,y,xx,yy,'rule');xx+=w;}s+=line(xx,y,xx,yy,'rule');
  return {svg:s,bottom:yy};
}
function titleBlock(d,number,title,notes,scale='1 : 50'){
  let s=line(12,513,829,513,'heavy')+text(12,523,'NOVOSTAVBA RD BŘEZÍ U MIKULOVA',6,'bold')+text(12,531,'PARCELA 6012/26 · HLAVNÝ NÁVRH C / B / B',3.6,'bold');
  s+=text(12,541,title,5,'bold')+text(12,550,'R0 = 184,200 m · M0 = PODLAHA MODELU · ΔFFL = M0 − R0 ZATIAĽ NEURČENÉ',2.6);
  s+=paragraph(12,559,notes,475,2.8).svg;
  s+=line(500,513,500,581,'thin')+text(509,522,'STAV',2.5,'muted')+text(509,530,'NEVYDANÉ NA REALIZÁCIU',4.8,'bold')+text(509,538,'Chýbajúci návrh sa nesmie nahradiť mierkou výkresu.',2.8);
  s+=text(509,549,'VYPRACOVAL: digitálne dvojča · bez autorizačnej pečiatky',2.8)+text(509,557,`DÁTUM ${d.provenance.date}   FORMÁT A1 841 × 594 mm   MIERKA ${scale}`,2.8);
  s+=text(509,565,`ZDROJ ${d.provenance.gitHead.slice(0,12)} · úplné odtlačky v model-snapshot.json`,2.4);
  s+=text(829,578,number,6,'bold','end');
  return s;
}
function calibration(scale){
  if(scale==='axonometria')return text(12,492,'KONTROLA TLAČE 100 % · úsečka 20 mm na papieri',2.7)+line(12,498,32,498,'heavy')+line(12,495,12,501,'thin')+line(32,495,32,501,'thin')+text(39,499,'Axonometria bez mierky; z obrázka neodmeriavať rozmery.',2.7);
  const numeric=Number(scale.match(/^1 : (\d+)$/)?.[1]??50);return text(12,492,`KONTROLA TLAČE 100 % · ${mm(numeric*20)} mm = 20 mm na papieri`,2.7)+line(12,498,32,498,'heavy')+line(12,495,12,501,'thin')+line(32,495,32,501,'thin')+text(39,499,`1 : ${numeric} · vypnúť „prispôsobiť strane“`,2.7);
}
function legend(x=600,y=380){
  return text(x,y,'ZNAČKY A MATERIÁLY',3.4,'bold')+join([
    ['murivo','Murivo / keramické prvky'],['insulation','ETICS / minerálna vlna'],['concrete','Betón – len ak je určený návrhom'],['timber','Drevený obklad'],
  ].map(([id,t],i)=>rect(x,y+5+i*8,10,5,'thin',`url(#${id})`)+text(x+14,y+9+i*8,t,2.7)))+text(x,y+45,'Čiarkovane: prerušené / neurčené konštrukcie.',2.7)+text(x,y+52,'M = výška k podlahe modelu. Dĺžky v mm.',2.7)+text(x,y+58,'K ulici R0: z = M + ΔFFL. ΔFFL neurčené.',2.7);
}
function sheet(d,id,title,body,notes='',scale='1 : 50'){
  return {id,title,status:'NOT_FOR_CONSTRUCTION',scale,svg:`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 841 594" width="841mm" height="594mm" role="img" aria-label="${esc(id+' '+title)}"><defs>
    <pattern id="murivo" width="1.5" height="1.5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="1.5" height="1.5" fill="white"/><path d="M0 0V1.5" stroke="black" stroke-width=".16"/></pattern>
    <pattern id="bearing" width=".9" height=".9" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width=".9" height=".9" fill="white"/><path d="M0 0V.9" stroke="black" stroke-width=".14"/></pattern>
    <pattern id="insulation" width="1" height="1" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><rect width="1" height="1" fill="#fafafa"/><path d="M0 0V1" stroke="black" stroke-width=".08"/></pattern>
    <pattern id="concrete" width="3" height="3" patternUnits="userSpaceOnUse"><rect width="3" height="3" fill="white"/><path d="M.4 .4L1 .3L.8 1Z M2 2L2.6 2.2L2.5 2.7Z" fill="none" stroke="black" stroke-width=".1"/></pattern>
    <pattern id="timber" width="2.4" height="5" patternUnits="userSpaceOnUse"><rect width="2.4" height="5" fill="white"/><path d="M0 0V5" stroke="black" stroke-width=".1"/></pattern>
  </defs><rect width="841" height="594" fill="white"/>${rect(5,5,831,584,'thin')}${text(12,19,id,3.6,'bold')}${text(12,30,title,6,'bold')}${text(829,19,`C / B / B · ${d.provenance.date.split('-').reverse().join('. ')} `,3,'','end')}${line(12,36,829,36,'thin')}${body}${calibration(scale)}${titleBlock(d,id,title,notes,scale)}</svg>`};
}
export function sectionRoof(d,cut){
  const segments=[];
  for(const face of d.roof.faces){const vertices=face.vertexIndices.map(i=>d.roof.vertices[i]),cross=[];
    for(let i=0;i<vertices.length;i++){const a=vertices[i],b=vertices[(i+1)%vertices.length],ac=cut.axis==='x'?a.yMm:a.xMm,bc=cut.axis==='x'?b.yMm:b.xMm;
      if(ac===bc){if(Math.abs(ac-cut.at)<1e-7)cross.push(a,b);continue;}
      const t=(cut.at-ac)/(bc-ac);if(t>=0&&t<=1)cross.push({xMm:a.xMm+t*(b.xMm-a.xMm),yMm:a.yMm+t*(b.yMm-a.yMm),elevationMm:a.elevationMm+t*(b.elevationMm-a.elevationMm)});
    }
    const vals=cross.map(p=>[cut.axis==='x'?p.xMm:p.yMm,p.elevationMm]).sort((a,b)=>a[0]-b[0]);
    if(vals.length>=2&&vals.at(-1)[0]-vals[0][0]>.001)segments.push({face:face.id,a:vals[0],b:vals.at(-1)});
  }return segments;
}
export function openingRows(d){
  return d.openings.map(o=>{const f=d.facades.find(f=>f.def.id===o.facade?.id),s=f?.segments.find(s=>s.item?.id===o.item.id),door=o.door;
    return {code:o.code,id:door?.id??o.item.id,facade:f?.def.id??'interiér',axis:f?.def.axis??door?.axis?.toLowerCase(),plane:f?.def.outer??(door.wallSpanMm[0]+door.wallSpanMm[1])/2,start:s?.a??door.startMm,end:s?.b??door.startMm+door.widthMm,
      width:o.item.opening.width,height:o.item.opening.height,sill:o.item.opening.sill,clearWidth:o.item.opening.clearWidth??null,leaf:door?.leafWidthMm??null,kind:o.item.id.includes('FRONT-07')?'fixed':o.kind,room:o.room?.number??'',door,item:o.item};});
}
function openingDrawing(row,u,v,axis,scale=50){
  const a=row.start,b=row.end,s=row.sill,h=row.height,x=Math.min(u(a),u(b)),y=v(s+h),w=(b-a)/scale;
  let out=rect(x,y,w,h/scale,'medium','white');
  const meshes=row.item.meshes.filter(m=>/rám|priečnik|stĺpik|koľajnica|prah|panel|dverné krídlo/i.test(m.name)&&!/sklo|rukoväť|kľučka/.test(m.name));
  for(const m of meshes){const p=axis==='x'?m.rect.x0:m.rect.y0,q=axis==='x'?m.rect.x1:m.rect.y1;
    if(p<a-1||q>b+1||m.z0<s-1||m.z1>s+h+1)continue;
    out+=rect(Math.min(u(p),u(q)),v(m.z1),(q-p)/scale,(m.z1-m.z0)/scale,'thin','#eee');
  }
  out+=text((u(a)+u(b))/2,v(s+h/2)+1,row.code,3,'bold halo','middle');
  return out;
}
function facadeSheet(d,f,index){
  const def=f.def,reverse=['N','W','WW','NN','NN2','L'].includes(def.id),length=(def.to-def.from)/50;
  const left=52,base=235,u=a=>left+(reverse?def.to-a:a-def.from)/50,v=z=>base-z/50;
  let out=text(12,47,`ROVINA ${def.axis==='x'?'Y':'X'} = ${mm(def.outer)} mm · čítanie ${reverse?'klesajúcich':'rastúcich'} súradníc ${def.axis.toUpperCase()}`,3);
  const roofFaces=d.roof.faces.filter(face=>def.id==='S'?['MAIN_FRONT','WING_OUTER'].includes(face.id):def.id==='E'?face.id==='WING_OUTER':def.id==='N'?face.id==='MAIN_GARDEN':def.id==='WW'?face.id==='WING_INNER':false);
  out+=`<defs><clipPath id="facade-roof-${def.id}"><rect x="${left}" y="60" width="${length}" height="190"/></clipPath></defs><g clip-path="url(#facade-roof-${def.id})">`;
  for(const face of roofFaces){const pts=face.vertexIndices.map(i=>d.roof.vertices[i]);out+=poly(pts.map(p=>[u(def.axis==='x'?p.xMm:p.yMm),v(p.elevationMm)]),'thin','#f6f6f6');
    for(const seam of d.roof.seamSegments.filter(s=>s.faceId===face.id))out+=line(u(def.axis==='x'?seam.start.xMm:seam.start.yMm),v(seam.start.elevationMm),u(def.axis==='x'?seam.end.xMm:seam.end.yMm),v(seam.end.elevationMm),'hair');
  }
  out+='</g>';
  // Plane-local wall spans and real over-opening headers.
  for(const seg of f.segments){if(seg.kind==='open')continue;
    const h=def.id==='L'?d.house.porches.gardenLoggia.soffitElevationMm:def.id==='NN2'?d.house.porches.wingEnd.ringBeam.bottomMm:d.house.eavesElevationMm;
    out+=rect(Math.min(u(seg.a),u(seg.b)),v(h),(seg.b-seg.a)/50,h/50,'',def.id==='NN2'?'url(#timber)':'white');
  }
  const top=def.id==='L'?d.house.porches.gardenLoggia.soffitElevationMm:def.id==='NN2'?d.house.porches.wingEnd.ringBeam.bottomMm:d.house.eavesElevationMm;
  if(def.id!=='NN')out+=line(left,v(top),left+length,v(top),'medium');
  out+=line(left,v(0),left,v(top),'medium')+line(left+length,v(0),left+length,v(top),'medium');
  for(const seg of f.segments.filter(s=>s.kind==='open'))out+=line(u(seg.a),v(0),u(seg.a),v(top),'medium')+line(u(seg.b),v(0),u(seg.b),v(top),'medium');
  const larch=def.id==='N'?[[10640,11840],[14340,15840]]:def.id==='L'?[[d.house.porches.gardenLoggia.backLarch.startXmm,d.house.porches.gardenLoggia.backLarch.endXmm]]:[];
  for(const [a,b] of larch)out+=rect(Math.min(u(a),u(b)),v(2750),(b-a)/50,2750/50,'thin','url(#timber)');
  for(const seg of f.segments.filter(s=>s.kind==='open')){
    const headers=d.shellMeshes.filter(m=>def.prefix&&m.name.startsWith(def.prefix)&&m.z0>0&&(def.axis==='x'?m.rect.x0<=seg.a+1&&m.rect.x1>=seg.b-1:m.rect.y0<=seg.a+1&&m.rect.y1>=seg.b-1));
    for(const h of headers)out+=rect(Math.min(u(seg.a),u(seg.b)),v(h.z1),(seg.b-seg.a)/50,(h.z1-h.z0)/50,'medium','white');
  }
  if(def.id==='W'){const p=d.roofParameters;out+=poly([[u(p.frontEaveYmm),v(p.eavesElevationMm)],[u(p.mainRidgeYmm),v(p.ridgeElevationMm)],[u(p.gardenEaveYmm),v(p.eavesElevationMm)]],'medium','white');}
  if(def.id==='NN'){
    const p=d.roofParameters;out+=line(u(p.wingInnerEaveXmm),v(p.eavesElevationMm),u(p.wingRidgeXmm),v(p.ridgeElevationMm),'heavy')+line(u(p.wingRidgeXmm),v(p.ridgeElevationMm),u(p.maxXmm),v(p.eavesElevationMm),'heavy');
    out+=text(left+length/2,v(1800),'OTVORENÝ PORTÁL · presklenie 2 500 mm za rovinou',2.8,'halo','middle');
    for(const h of d.porchEnvelope.supportHeads)out+=poly(h.polygonXZMm.map(([x,z])=>[u(x),v(z)]),'medium','white');
  }
  const openings=openingRows(d).filter(o=>o.facade===def.id);
  for(const o of openings)out+=openingDrawing(o,u,v,def.axis);
  if(def.id==='NN2'){
    const p=d.house.porches.wingEnd,g=p.gableWindow,top=d.triangle.vertices[2][1];
    out+=rect(Math.min(u(p.ringBeam.spanStartXmm),u(p.ringBeam.spanEndXmm)),v(p.ringBeam.topMm),(p.ringBeam.spanEndXmm-p.ringBeam.spanStartXmm)/50,(p.ringBeam.topMm-p.ringBeam.bottomMm)/50,'medium','url(#timber)');
    for(const profile of d.porchExteriorProfiles)out+=poly(profile.map(([x,z])=>[u(x),v(z)]),'thin','url(#timber)');
    out+=poly(d.triangle.vertices.map(([x,z])=>[u(x),v(z)]),'medium','white');
    out+=text(u(g.endXmm-450),v(g.bottomMm+350),'O11',3,'bold halo','middle');
    out+=text(350,130,'O11 · svetlík nad rovinou pôdorysu',3.2,'bold')+text(350,138,`X ${mm(g.startXmm)}–${mm(g.endXmm)} · spodná hrana ${level(g.bottomMm)}`,3)+text(350,146,`vrchol ${level(top)} · presný model ${mm(top)} mm`,3);
  }
  // Datum only. Do not substitute a render lawn height for surveyed terrain.
  out+=line(left-8,base,left+length+8,base,'datum');
  const pts=[...new Set(f.segments.flatMap(s=>[s.a,s.b]))].sort((a,b)=>a-b);
  for(let i=1;i<pts.length;i++)out+=dimH(u(pts[i-1]),u(pts[i]),base+22,base);
  out+=dimH(left,left+length,base+35,base,mm(def.to-def.from));
  const axes=(def.axis==='x'?d.gridX:d.gridY).filter(a=>a.at>=def.from&&a.at<=def.to);
  for(const a of axes)out+=line(u(a.at),base+40,u(a.at),base+54,'axis')+circle(u(a.at),base+58,3.4,a.label);
  out+=spot(left-15,v(0),0,'',-1);
  if(def.id==='L')out+=spot(left+length+2,v(top),top,'podhľad lodžie');
  else if(def.id==='NN2')out+=spot(left+length+2,v(d.house.ridgeElevationMm-d.house.porches.wingEnd.ceilingClearanceMm),d.house.ridgeElevationMm-d.house.porches.wingEnd.ceilingClearanceMm,'horný obklad');
  else out+=spot(left+length+2,v(3125),3125,'hrana strechy')+spot(left+length+2,v(5560),5560,'hrebeň rovín');
  const flue=d.living.stove;
  if(['S','E','N','WW'].includes(def.id)){
    const a=def.axis==='x'?flue.centerMm.x:flue.centerMm.y;
    if(a>=def.from&&a<=def.to){const visibleBase=['S','E','N'].includes(def.id)?d.house.ridgeElevationMm:d.livingFlueRoofMm;
      out+=rect(u(a)-flue.flue.outerDiameterMm/100,v(flue.flue.terminationElevationMm),flue.flue.outerDiameterMm/50,(flue.flue.terminationElevationMm-visibleBase)/50,'thin','white');out+=spot(u(a)+3,v(flue.flue.terminationElevationMm),flue.flue.terminationElevationMm,'dymovod B');}
  }
  let terrace=terraceIntervals(d,def.axis,def.outer).map(([a,b])=>[Math.max(a,def.from),Math.min(b,def.to)]).filter(([a,b])=>b>a);
  if(def.id==='W')terrace=terrace.flatMap(([a,b])=>f.segments.filter(s=>s.kind==='open').map(s=>[Math.max(a,s.a),Math.min(b,s.b)]).filter(([lo,hi])=>hi>lo));
  for(const [a,b] of terrace)out+=line(u(a),v(d.deck.topMm),u(b),v(d.deck.topMm),'medium');
  if(terrace.length)out+=text(left+length+5,v(d.deck.topMm)+12,`terasa ${level(d.deck.topMm)} · modelová hladina`,2.7);
  if(def.id==='NN'){
    for(const step of [...d.exteriorSteps].sort((a,b)=>a.rect.y0-b.rect.y0))out+=rect(Math.min(u(step.rect.x0),u(step.rect.x1)),v(step.z1),(step.rect.x1-step.rect.x0)/50,(step.z1-step.z0)/50,'thin','white');
    out+=stepsDetail(d,592,178);
  }
  if(['L','NN2'].includes(def.id)){
    const porch=def.id==='NN2',from=porch?d.house.porches.wingEnd.glazingFaceYmm:d.house.porches.gardenLoggia.backFaceYmm,to=porch?d.house.porches.wingEnd.frontYmm:d.footprint.gardenY;
    const x=420,z=235,h=porch?d.house.eavesElevationMm:d.house.porches.gardenLoggia.soffitElevationMm,w=(to-from)/50;
    out+=text(x,155,porch?'VRATNÉ LÍCE KRYTEJ TERASY':'BOČNÉ LÍCE LODŽIE',3.2,'bold')+text(x,163,`X ${mm(porch?d.house.porches.wingEnd.eastWallInnerXmm:d.house.porches.gardenLoggia.eastInnerXmm)} · Y ${mm(from)}–${mm(to)}`,2.8);
    out+=rect(x,z-h/50,w,h/50,'medium','white')+dimH(x,x+w,z+16,z,mm(to-from))+dimV(z-h/50,z,x+w+15,x+w,mm(h));
    if(porch)for(const part of d.porchEnvelope.supportHeads){const heights=profileHeights(part.polygonXZMm,d.house.porches.wingEnd.eastWallInnerXmm);if(heights.length){const high=Math.max(...heights);out+=rect(x+(part.startYmm-from)/50,z-high/50,(part.endYmm-part.startYmm)/50,(high-Math.min(...heights))/50,'medium','white')+spot(x+w+22,z-high/50,high,'hlava podpory')+text(x+w+28,z-high/50+6,`${mm(high)} mm · model`,2.5);}}
  }
  out+=text(12,325,'VYTYČOVACIE ÚDAJE OTVOROV TEJTO ROVINY',3.5,'bold');
  out+=table(12,333,545,[['Kód / identifikátor',.32],['Od / do [mm]',.27],['Š × V [mm]',.21],['Parapet / nadpražie',.20]],openings.map(o=>[o.code+' / '+o.id,`${o.axis.toUpperCase()} ${mm(o.start)} / ${mm(o.end)}`,`${mm(o.width)} × ${mm(o.height)}`,`${mm(o.sill)} / ${mm(o.sill+o.height)}`])).svg;
  out+=legend(592,338);
  out+=paragraph(592,407,'Obvodový plášť SO30 + TI20: nosné murivo 300 mm a ETICS 200 mm. Voľné piliere SO50: 500 mm plné murivo. Skladby a detaily DT/SK.',222,3).svg;
  if(def.id==='L')out+=paragraph(592,448,`Bočná stena lodžie: X ${mm(d.house.porches.gardenLoggia.eastInnerXmm)}, Y ${mm(def.outer)}–${mm(d.footprint.gardenY)}; bez otvorov.`,222,3).svg;
  // Draw after dimension extensions so the datum explanation remains readable.
  out+=text(left,base+8,'M0 · podlaha modelu; R0 = 184,200 m ulica; ΔFFL zatiaľ neurčené',2.8,'halo');
  return sheet(d,`D1.1.PO-${String(index+1).padStart(2,'0')}`,def.name,out,'Presná modelová projekcia. R05/R06: chýba skutočný terén, sokel, finálne povrchy a realizačné detaily. Rozmery otvorov sú modelové stavebné otvory; výrobný rozmer určí dodávateľ.');
}
function planMap(d,x=22,y=48){
  const f=d.footprint;const u=a=>x+(a-f.x0)/50,v=a=>y+(f.y1-a)/50;
  let svg='';
  for(const m of d.shellMeshes.filter(m=>m.z0<=0&&m.z1>1200)){
    const pts=m.polygon.split(' ').map(p=>p.split(',').map(Number)).map(([a,b])=>[u(a),v(-b)]);
    svg+=poly(pts,'thin',m.name.includes('izolácia')?'url(#insulation)':'url(#murivo)');
  }
  for(const {mesh:m} of d.interiorMeshes){const r=m.rect;svg+=rect(u(r.x0),v(r.y1),(r.x1-r.x0)/50,(r.y1-r.y0)/50,'thin',m.name.includes('WOOL')||m.name.includes('CAVITY')?'url(#insulation)':'url(#murivo)');}
  for(const r of d.rooms){const p=r.standingPointMm;svg+=text(u(p.x),v(p.y),r.number,2.7,'bold halo','middle');}
  return {svg,u,v};
}
function tracePlan(d,svg){
  const ext=d.planExtent,tx=x=>8+(x-ext.x0)/50,ty=y=>8+(ext.y1-y)/50;
  const traces=CUTS.map(c=>{const ax=c.axis==='x'?tx(c.from):tx(c.at),ay=c.axis==='x'?ty(c.at):ty(c.from),bx=c.axis==='x'?tx(c.to):tx(c.at),by=c.axis==='x'?ty(c.at):ty(c.to);
    const arrow=(x,y)=>c.axis==='x'?poly([[x,y-5],[x+2,y],[x-2,y]],'thin','black'):poly([[x-5,y],[x,y-2],[x,y+2]],'thin','black');
    return line(ax,ay,bx,by,'cutline')+text(ax+4,ay-3,c.id,3.8,'bold halo')+text(bx+4,by-3,c.id,3.8,'bold halo')+arrow(ax,ay)+arrow(bx,by);}).join('');
  // Embed the existing SVG untouched. Only an independent trace overlay is added.
  const base=svg.replace(/width="[^"]+"/,'width="841mm"').replace(/height="[^"]+"/,'height="594mm"');
  return {id:'D1.1.002-C-RE',title:'Existujúci pôdorys · stopy rezov',status:'NOT_FOR_CONSTRUCTION',scale:'1 : 50',svg:base.replace('</svg>',`${traces}<rect x="8" y="574" width="810" height="12" fill="white"/>${text(12,579,'PÔVODNÉ ±0,000 TOHTO LISTU = M0 PODLAHY; R0 ULICE = 184,200 m; ROZDIEL ΔFFL ZATIAĽ NEURČENÝ.',2.7,'bold')}${text(12,584,'DOPLNENÉ STOPY A-A, B-B, C-C · geometria a kódy bez zmeny · nové konštrukcie NEVYDANÉ NA REALIZÁCIU',2.7,'bold')}</svg>`)};
}
const crosses=(r,axis,at,inclusive=false)=>axis==='x'?(inclusive?r.y0<=at&&r.y1>=at:r.y0<at&&r.y1>at):(inclusive?r.x0<=at&&r.x1>=at:r.x0<at&&r.x1>at);
const along=(r,axis)=>axis==='x'?[r.x0,r.x1]:[r.y0,r.y1];
export function profileHeights(polygon,x){
  const values=[];
  for(let i=0;i<polygon.length;i++){const a=polygon[i],b=polygon[(i+1)%polygon.length];if(a[0]===b[0]){if(Math.abs(x-a[0])<1e-7)values.push(a[1],b[1]);continue;}const t=(x-a[0])/(b[0]-a[0]);if(t>=0&&t<=1)values.push(a[1]+t*(b[1]-a[1]));}
  return [...new Set(values)];
}
export function sectionPorchEnvelope(d,cut){
  const parts=[...d.porchEnvelope.supportHeads,...d.porchEnvelope.soffitPanels,...d.porchExteriorProfiles.map((polygonXZMm,i)=>({id:`PORCH-GABLE-${i+1}`,kind:'LARCH_GABLE',polygonXZMm,startYmm:d.house.porches.wingEnd.gablePlaneYmm,endYmm:d.house.porches.wingEnd.gablePlaneYmm+56}))];
  return parts.flatMap(part=>{
    if(cut.axis==='x')return cut.at>=part.startYmm&&cut.at<=part.endYmm?[{...part,points:part.polygonXZMm}]:[];
    const heights=profileHeights(part.polygonXZMm,cut.at);
    return heights.length?[{...part,points:[[part.startYmm,Math.min(...heights)],[part.endYmm,Math.min(...heights)],[part.endYmm,Math.max(...heights)],[part.startYmm,Math.max(...heights)]]}]:[];
  });
}
function mergeSpans(intervals){const merged=[];for(const p of [...intervals].sort((a,b)=>a[0]-b[0])){if(merged.length&&p[0]<=merged.at(-1)[1])merged.at(-1)[1]=Math.max(p[1],merged.at(-1)[1]);else merged.push([...p]);}return merged;}
export function terraceIntervals(d,axis,at){return mergeSpans(d.terraces.flatMap(t=>t.rects).filter(r=>crosses(r,axis,at,true)).map(r=>along(r,axis)));}
export function sectionWallSlices(d,cut){
  const result=[];
  for(const m of [...d.shellMeshes,...d.interiorMeshes.map(m=>m.mesh)]){
    if(!crosses(m.rect,cut.axis,cut.at)||m.z1<=0||/hlava|obklad/.test(m.name))continue;
    let [a,b]=along(m.rect,cut.axis);if(b-a>1000)continue;
    for(const f of d.facades.filter(f=>f.def.axis!==cut.axis&&cut.at>f.def.from&&cut.at<f.def.to)){
      const lo=Math.min(f.def.outer,f.def.inner),hi=Math.max(f.def.outer,f.def.inner);
      if(a<hi&&b>lo){a=Math.max(a,lo);b=Math.min(b,hi);}
    }
    if(b>a)result.push({m,a,b});
  }
  return result;
}
export function sectionRoomSpans(d,cut,room){
  let spans=mergeSpans(room.rectsMm.filter(r=>crosses(r,cut.axis,cut.at)).map(r=>along(r,cut.axis)));
  for(const {a,b} of sectionWallSlices(d,cut).filter(({m})=>m.z0<=0&&m.z1>0)){
    spans=spans.flatMap(([lo,hi])=>b<=lo||a>=hi?[[lo,hi]]:[[lo,Math.max(lo,a)],[Math.min(hi,b),hi]].filter(([p,q])=>q>p));
  }
  return spans;
}
export function sectionDimensionPoints(d,cut){
  const spans=[...d.walls.filter(w=>crosses(w.rectMm,cut.axis,cut.at)).map(w=>along(w.rectMm,cut.axis)).filter(([a,b])=>b-a<=1000),...d.facades.filter(f=>f.def.axis!==cut.axis&&cut.at>f.def.from&&cut.at<f.def.to&&f.segments.some(s=>s.kind!=='open'&&cut.at>s.a&&cut.at<s.b)).map(f=>[Math.min(f.def.outer,f.def.inner),Math.max(f.def.outer,f.def.inner)])];
  return [...new Set([...mergeSpans(spans).flat(),...terraceIntervals(d,cut.axis,cut.at).flat()])].filter(p=>p>=cut.from&&p<=cut.to).sort((a,b)=>a-b);
}
function stepsDetail(d,x,y){
  const steps=[...d.exteriorSteps].sort((a,b)=>a.rect.y0-b.rect.y0),origin=steps[0].rect.y0,u=a=>x+8+(a-origin)/5,v=z=>y+23-z/5;
  let out=text(x,y,'MODELOVÉ STUPNE TERASY · PROFIL 1 : 5',3.1,'bold');
  for(const s of steps){out+=rect(u(s.rect.y0),v(s.z1),(s.rect.y1-s.rect.y0)/5,(s.z1-s.z0)/5,'thin','#eee')+dimH(u(s.rect.y0),u(s.rect.y1),y+50,v(s.z0),mm(s.rect.y1-s.rect.y0));}
  out+=dimH(u(steps[0].rect.y0),u(steps.at(-1).rect.y1),y+61,y+50,mm(steps.at(-1).rect.y1-steps[0].rect.y0));
  out+=table(x,y+69,232,[['Stupeň',.22],['Horné / dolné Z',.48],['Hrúbka',.30]],steps.map((s,i)=>[String(i+1),`${level(s.z1)} / ${level(s.z0)}`,`${mm(s.z1-s.z0)} mm`]),9).svg;
  out+=paragraph(x,y+103,'Úrovne modelu; nie hotový návrh schodiska. Terén, založenie a napojenie sú otvorené.',232,2.5).svg;
  return out;
}
export function sectionGarageGable(d,cut){
  if(cut.axis!=='x')return null;
  const g=d.garageGable;
  if(g.planeMm<cut.from||g.planeMm>cut.to)return null;
  for(let i=1;i<g.vertices.length;i++){
    const a=g.vertices[i-1],b=g.vertices[i];
    if(cut.at>=a[0]&&cut.at<=b[0])return {at:g.planeMm,bottom:g.vertices[0][1],top:a[1]+(b[1]-a[1])*(cut.at-a[0])/(b[0]-a[0])};
  }
  return null;
}
function sectionSheet(d,cut,index){
  const start=cut.from,end=cut.to,u=x=>40+(x-start)/50,v=z=>220-z/50;
  let out=text(12,48,`${cut.axis==='x'?'Y':'X'} = ${mm(cut.at)} mm · stopa na D1.1.002-C-RE · ${cut.why}`,3);
  const roof=sectionRoof(d,cut);
  for(const s of roof)out+=line(u(s.a[0]),v(s.a[1]),u(s.b[0]),v(s.b[1]),'heavy');
  const cross=r=>cut.axis==='x'?r.y0<cut.at&&r.y1>cut.at:r.x0<cut.at&&r.x1>cut.at;
  const bounds=r=>cut.axis==='x'?[r.x0,r.x1]:[r.y0,r.y1];
  // Intersect exact model wall rectangles. No fabricated beam or footing geometry.
  for(const {m,a,b} of sectionWallSlices(d,cut)){
    out+=rect(u(a),v(m.z1),(b-a)/50,(m.z1-Math.max(0,m.z0))/50,'medium',/izolácia|WOOL|CAVITY/.test(m.name)?'url(#insulation)':/SILENTBOARD/.test(m.name)?'#ddd':/PLASTER/.test(m.name)?'#f3f3f3':'url(#murivo)');
  }
  for(const m of d.upperMeshes.filter(m=>cross(m.rect))){const [a,b]=bounds(m.rect);if(b-a>1000)continue;out+=rect(u(a),v(m.z1),(b-a)/50,(m.z1-m.z0)/50,'thin',/obklad/.test(m.name)?'url(#timber)':'#eee');}
  for(const p of sectionPorchEnvelope(d,cut))out+=poly(p.points.map(([a,z])=>[u(a),v(z)]),'thin',p.kind.startsWith('LARCH')?'url(#timber)':'#eee');
  const garageGable=sectionGarageGable(d,cut);
  if(garageGable)out+=line(u(garageGable.at),v(garageGable.bottom),u(garageGable.at),v(garageGable.top),'medium')+text(u(garageGable.at)+5,v(garageGable.top)+11,'Obal garážového štítu · skladba R04',2.5,'halo');
  for(const room of d.rooms){
    for(const [a,b] of sectionRoomSpans(d,cut,room)){out+=line(u(a),v(0),u(b),v(0),'heavy');
    if(room.ceiling==='FLAT')out+=line(u(a),v(room.clearHeightMm),u(b),v(room.clearHeightMm),'medium');
    else {
      const get=x=>4850-2100*Math.min(1,Math.abs(x-24540)/(24540-21543));
      const points=cut.axis==='x'?[a,...(a<24540&&b>24540?[24540]:[]),b].map(x=>[u(x),v(Math.round(get(x)))]) : [[u(a),v(Math.round(get(cut.at)))],[u(b),v(Math.round(get(cut.at)))]];
      out+=`<polyline points="${points.map(p=>p.join(',')).join(' ')}" class="medium" fill="none"/>`;
    }
    out+=text(u((a+b)/2),v(1450),room.number,3,'bold halo','middle');
    out+=dimH(u(a),u(b),v(0)+18,v(0),mm(b-a));
    if(b-a>1200){const right=room.ceiling!=='FLAT'&&cut.axis==='x';out+=dimV(v(0),v(room.ceiling==='FLAT'?room.clearHeightMm:cut.axis==='y'?4850:room.clearHeightMm),right?u(b)-8:u(a)+8,right?u(b):u(a));}
  }}
  for(const o of openingRows(d).filter(o=>o.facade!=='interiér')){
    if(o.axis===cut.axis)continue;if(cut.at<o.start||cut.at>o.end)continue;
    const f=d.facades.find(f=>f.def.id===o.facade).def;
    if(f.outer<start||f.outer>end)continue;
    const left=f.outer<(start+end)/2,labelX=u(f.outer)+(left?-5:5),anchor=left?'end':'start';
    out+=line(u(f.outer),v(o.sill),u(f.outer),v(o.sill+o.height),'medium')+text(labelX,v(o.sill+o.height/2),o.code,2.8,'bold halo',anchor)+text(labelX,v(o.sill+o.height/2)+5,`${level(o.sill)} / ${level(o.sill+o.height)}`,2.5,'dim halo',anchor);
  }
  if(cut.id==='B-B'){const stove=d.living.stove;out+=rect(u(stove.centerMm.x)-stove.flue.outerDiameterMm/100,v(stove.flue.terminationElevationMm),stove.flue.outerDiameterMm/50,(stove.flue.terminationElevationMm-stove.flue.startElevationMm)/50,'thin','white')+spot(u(stove.centerMm.x)+5,v(stove.flue.terminationElevationMm),stove.flue.terminationElevationMm,'dymovod B');}
  const top=Math.max(...roof.flatMap(s=>[s.a[1],s.b[1]]));
  out+=spot(17,v(0),0)+spot(40+(end-start)/50+3,v(top),top,'strecha v reze');
  if(cut.id==='B-B')out+=spot(u(d.roofParameters.wingRidgeXmm)+3,v(4850),4850,'podhľad')+spot(u(d.footprint.x1)+3,v(d.house.eavesElevationMm),d.house.eavesElevationMm,'hrana strechy');
  for(const [a,b] of terraceIntervals(d,cut.axis,cut.at).map(([a,b])=>[Math.max(a,start),Math.min(b,end)]).filter(([a,b])=>b>a))out+=rect(u(a),v(d.deck.topMm),(b-a)/50,d.deck.thicknessMm/50,'thin','url(#timber)')+dimH(u(a),u(b),v(0)+18,v(0),mm(b-a))+text(u(a)+2,v(d.deck.topMm)-3,`Terasa ${level(d.deck.topMm)}`,2.6,'halo');
  for(const step of d.exteriorSteps.filter(m=>cross(m.rect))){const [a,b]=bounds(step.rect);out+=rect(u(a),v(step.z1),(b-a)/50,(step.z1-step.z0)/50,'thin','#eee');}
  const refs=sectionDimensionPoints(d,cut);
  for(let i=1;i<refs.length;i++){const a=u(refs[i-1]),b=u(refs[i]),label=mm(refs[i]-refs[i-1]),yy=v(0)+35;out+=dimH(a,b,yy,v(0),b-a<9?'':label);if(b-a<9)out+=`<g transform="translate(${(a+b)/2+1} ${yy-2}) rotate(-90)">${text(0,0,label,2.3,'dim halo')}</g>`;}
  for(const a of (cut.axis==='x'?d.gridX:d.gridY).filter(a=>a.at>=start&&a.at<=end))out+=line(u(a.at),v(0)+40,u(a.at),v(0)+53,'axis')+circle(u(a.at),v(0)+58,3.4,a.label);
  if(refs.length>1)out+=dimH(u(refs[0]),u(refs.at(-1)),v(0)+68,v(0)+62,mm(refs.at(-1)-refs[0]));
  if(cut.id==='A-A'){
    out+=stepsDetail(d,592,230);
    const band=d.upperMeshes.find(m=>/pás venca/.test(m.name)&&!/obklad/.test(m.name));
    out+=dimV(v(band.z1),v(band.z0),u(band.rect.y1)+12,u(band.rect.y1),mm(band.z1-band.z0));
    out+=text(592,76,'PÁS NAD PRESKLENÍM · OBAL Z MODELU',3.2,'bold');
    out+=table(592,83,232,[['Rozmer / úroveň',.44],['Hodnota',.56]],[['Dĺžka × hĺbka × výška',`${mm(band.rect.x1-band.rect.x0)} × ${mm(band.rect.y1-band.rect.y0)} × ${mm(band.z1-band.z0)} mm`],['Spodok / vrch',`${level(band.z0)} / ${level(band.z1)}`],['Rozsah v reze',`Y ${mm(band.rect.y0)}–${mm(band.rect.y1)}`]],12).svg;
    out+=paragraph(592,143,'R04: nový nosný materiál, výstuž a kotvenie. Vonkajší plášť pásu je drevený obklad; šrafa nepredpisuje betón.',232,2.7).svg;
  }
  out+=line(u(start),v(0)+75,u(end),v(0)+75,'unknown')+text(u(start),v(0)+85,'POD NOSNOU DOSKOU SA NIČ NEPREBERÁ Z ARCHÍVNEJ STATIKY.',3.2,'bold');
  out+=paragraph(u(start),v(0)+95,'Nové zadanie: horný monolit 350 × 600 mm, vnútorné rebrá a doska 150–200 mm; detail ZA-02. Nivelácia, výstuž a nosná skladba zatiaľ neurčené. R0 = 184,200 m na ulici; všetky výšky M sú k pôvodnej podlahe modelu.',Math.min(520,(end-start)/50),3.1).svg;
  out+=text(12,358,'KOORDINÁCIA NOVÝCH KONŠTRUKCIÍ',3.6,'bold');
  out+=table(12,367,550,[['Prvok',.26],['Záväzný geometrický podklad / chýbajúci návrh',.74]],[[ 'Podlaha M0','Vodovod a kanalizácia nad nosnou doskou. Podlahové vykurovanie mimo garáže, technickej a sprchy; TZ-01. Bez dodatočných vrtov do dosky.'],['Drevený strop a povala','Povala iba na odkladanie, bez betónovej stropnej dosky/nadbetonávky. Skladovacie a bodové zaťaženia musí určiť výpočet. Katedrála 1.03 zostáva otvorená, svetlé výšky 2 750 / 4 850 mm.'],['Nosné línie a základy','Nový monolitický návrh podľa ZA-02, geotechniky a reakcií nosnej sústavy. Výstuž, rebrá a pracovné škáry sa nepreberajú zo starého projektu.']]).svg;
  out+=legend(600,370);
  return sheet(d,`D1.1.RE-${String(index+1).padStart(2,'0')}`,`${cut.id} · ${cut.title}`,out,'Rozmery nadzemnej architektonickej geometrie z modelu. Základy, nosná skladba podlahy a strechy, vence a krov zostávajú otvorené R01-R04; list nie je realizačný rez.');
}
function roofSheet(d){
  const map=planMap(d,30,48),{u,v}=map;let out=map.svg;
  for(const face of d.roof.faces){const pts=face.vertexIndices.map(i=>d.roof.vertices[i]);out+=poly(pts.map(p=>[u(p.xMm),v(p.yMm)]),'medium','#f8f8f8');}
  for(const s of d.roof.seamSegments)out+=line(u(s.start.xMm),v(s.start.yMm),u(s.end.xMm),v(s.end.yMm),'hair');
  for(const l of [...d.roof.ridges,d.roof.valley,d.roof.hip,...d.roof.gutters]){const a=d.roof.vertices[l.startVertexIndex],b=d.roof.vertices[l.endVertexIndex];out+=line(u(a.xMm),v(a.yMm),u(b.xMm),v(b.yMm),l.kind==='RIDGE'?'heavy':'medium');}
  d.roof.vertices.forEach((p,i)=>out+=circle(u(p.xMm),v(p.yMm),3,String(i+1)));
  const flue=d.living.stove;out+=circle(u(flue.centerMm.x),v(flue.centerMm.y),3,'K1');
  const f=d.footprint,p=d.roofParameters;
  out+=dimH(u(f.x0),u(f.x1),v(f.y0)+18,v(f.y0),mm(f.x1-f.x0));
  out+=dimV(v(p.wingEndYmm),v(f.y0),u(f.x1)+17,u(f.x1),mm(p.wingEndYmm-f.y0));
  out+=table(530,52,295,[['Bod',.09],['X [mm]',.25],['Y [mm]',.25],['Z [mm]',.25],['Ref.',.16]],d.roof.vertices.map((p,i)=>[String(i+1),mm(p.xMm),mm(p.yMm),mm(p.elevationMm),'ST'])).svg;
  out+=text(530,173,'GEOMETRIA STRECHY Z MODELOVÝCH VRCHOLOV',3.3,'bold');
  out+=paragraph(530,183,`Hlavný trakt: atan((${p.ridgeElevationMm} − ${p.eavesElevationMm}) / ${(p.mainRidgeYmm-p.frontEaveYmm)}) = ${(Math.atan((p.ridgeElevationMm-p.eavesElevationMm)/(p.mainRidgeYmm-p.frontEaveYmm))*180/Math.PI).toFixed(6)}°. Krídlo: ${(Math.atan((p.ridgeElevationMm-p.eavesElevationMm)/(p.wingRidgeXmm-p.wingInnerEaveXmm))*180/Math.PI).toFixed(6)}°. Pôvodné štítky 30°/34° nie sú presným sklonom tejto geometrie. Obal sa nemení.`,287,3).svg;
  out+=paragraph(530,227,`K1: ${flue.flue.id}; X ${mm(flue.centerMm.x)}, Y ${mm(flue.centerMm.y)}, Ø ${flue.flue.outerDiameterMm} mm, ukončenie ${level(flue.flue.terminationElevationMm)}. Kotolňa B zatiaľ nemá modelovanú vonkajšiu trasu dymovodu.`,287,3).svg;
  out+=paragraph(530,267,'Falcové línie zobrazujú existujúci modelový raster krytiny. Nie sú rozmiestnením krokiev. Úžľabie, nárožie, hrebeň a odkvapné hrany sú z tej istej geometrie ako 3D.',287,3).svg;
  out+=paragraph(530,309,'Nové zadanie: falcovaný plech, nulový architektonický presah. Krytá terasa je zapustená hmota, nie presah. Koncová rovina strechy sa viaže na líce čela terasy; lemovanie a žľab potrebujú finálny detail.',287,3).svg;
  out+=paragraph(530,360,'Povala iba na odkladanie vecí. Drevené pôdne väzníky v pravidelnom trakte, samostatné drevené polia pri uzle L a osobitná katedrála. Bez betónového stropu a nadbetonávky. Prierezy, skladovacie zaťaženie, spoje a kotvenie vyžadujú výpočet.',287,3).svg;
  return sheet(d,'D1.1.ST-01','Pôdorys strechy',out,'Geometrické vrcholy, hrany a presahy z lib/twin-roof.ts. Návrh krovu a strešného plášťa je samostatná otvorená časť R04. Čísla bodov sú doplnkové, existujúce osi zostávajú.');
}
function foundationSheet(d){
  const {svg,u,v}=planMap(d,35,48);let out=svg;
  for(const a of d.gridX)out+=line(u(a.at),v(d.footprint.y0)+20,u(a.at),v(d.footprint.y1),'axis')+circle(u(a.at),v(d.footprint.y0)+24,3,a.label);
  for(const a of d.gridY)out+=line(u(d.footprint.x0)-8,v(a.at),u(d.footprint.x1),v(a.at),'axis')+circle(u(d.footprint.x0)-12,v(a.at),3,a.label);
  const r7=d.foundationIllustration.ribs.find(r=>r.id==='R7');
  const [a,b]=r7.points;
  out+=line(u(a[0]),v(a[1]),u(b[0]),v(b[1]),'unknown');
  out+=circle(u(a[0]),v((a[1]+b[1])/2),4,'R7');
  for(const w of d.partitionLoads.walls){
    const r=w.rectMm;
    out+=rect(u(r.x0),v(r.y1),(r.x1-r.x0)/50,(r.y1-r.y0)/50,'heavy');
    out+=text(u(r.x0)-4,v((r.y0+r.y1)/2),w.code,3,'bold halo','end');
  }
  out+=table(540,55,275,[['Línia',.22],['Súradnica [mm]',.33],['Význam',.45]],[...d.gridX.map(a=>[a.label,mm(a.at),'X / pôvodná os']),...d.gridY.map(a=>[a.label,mm(a.at),'Y / pôvodná os'])]).svg;
  out+=text(540,222,'SM30 · VLASTNÁ HMOTNOSŤ ZAŤAŽUJÚCA DOSKU',3.4,'bold');
  out+=table(540,231,275,[['Stena',.15],['L [mm]',.17],['H [mm]',.18],['kg/m',.23],['kg spolu',.27]],d.partitionLoads.walls.map(w=>[w.code,mm(w.lengthMm),mm(w.heightMm),'neurčené','neurčené']),12).svg;
  const load=d.partitionLoads;
  out+=paragraph(540,280,'Jedna vrstva obvodovej tehly 300 mm. Konkrétny výrobok a hmotnosť neurčené; doplniť maltu, omietky, obklady a vybavenie. Starý prepočet dvojplášťovej steny neplatí.',275,3).svg;
  out+=text(540,313,'SM30 · výber tehly a nový prepočet vlastnej tiaže zostávajú otvorené',2.8);
  out+=paragraph(540,329,`R7: kandidátna os X ${mm(a[0])}; Y ${mm(a[1])}–${mm(b[1])}. Dva zaťažené úseky po ${mm(load.walls[0].lengthMm)} mm, voľná chodba 1 099 mm. Os jedného 300 mm muriva leží na R7. Prípadný spojitý pás prechádza iba pod podlahou.`,275,3.1,'bold').svg;
  out+=paragraph(540,374,'SM30 ostáva nenosná pre strechu a strop. Návrh musí overiť prenos jej hmotnosti cez existujúcu dosku, uloženie pásu a podložie. R7 nemá určený prierez ani výstuž a nie je pokynom na zásah do vyliatej dosky.',275,3.1).svg;
  out+=paragraph(540,424,'Horný monolit 350 × 600 mm a doska 150–200 mm sú požiadavky stavebníka, nie výsledok výpočtu. Rozmery a väzby: ZA-02; priestorový pohľad: ZA-03.',275,3).svg;
  return sheet(d,'D1.1.ZA-01','Základy · nosné línie a ťažké priečky',out,'NEHOTOVÝ LIST. Hmotnosť SM30 čaká na výber výrobku. Základy, existujúca doska, podložie a konečné zaťaženia vyžadujú nový statický návrh.');
}
function siteSheets(d){
  const points=d.siteBoundary,minX=Math.min(...points.map(p=>p.x)),maxY=Math.max(...points.map(p=>p.y));
  return [0,1].map(index=>{
    const topY=index===0?21000:maxY+400;
    const u=x=>28+(x-minX)/50,v=y=>48+(topY-y)/50;
    let drawing=poly(points.map(p=>[u(p.x),v(p.y)]),'boundary');
    drawing+=poly(d.house.footprintMm.map(p=>[u(p.x),v(p.y)]),'heavy','#fafafa');
    if(index===0){const r=d.entryProposal.landingRectMm;
      drawing+=rect(u(r.x0),v(r.y1),(r.x1-r.x0)/50,(r.y1-r.y0)/50,'unknown','white');
      drawing+=line(u(r.x0),v(r.y0),u(r.x1),v(r.y0),'heavy')+text(u((r.x0+r.x1)/2),v((r.y0+r.y1)/2),'VS1',2.8,'bold halo','middle');
      drawing+=dimH(u(r.x0),u(r.x1),v(r.y0)+10,v(r.y0),mm(r.x1-r.x0));
      drawing+=dimV(v(r.y1),v(r.y0),u(r.x1)+9,u(r.x1),mm(r.y1-r.y0));
    }
    for(const t of d.terraces)for(const r of t.rects)drawing+=rect(u(r.x0),v(r.y1),(r.x1-r.x0)/50,(r.y1-r.y0)/50,'thin','url(#timber)');
    for(const s of d.exteriorSteps)drawing+=rect(u(s.rect.x0),v(s.rect.y1),(s.rect.x1-s.rect.x0)/50,(s.rect.y1-s.rect.y0)/50,'thin','#eee');
    if(index===1){const steps=[...d.exteriorSteps].sort((a,b)=>a.rect.y0-b.rect.y0),first=steps[0].rect,last=steps.at(-1).rect;
      drawing+=dimH(u(first.x0),u(first.x1),v(last.y1)-7,v(last.y1),mm(first.x1-first.x0));
      for(const {rect:r} of steps)drawing+=dimV(v(r.y1),v(r.y0),u(r.x0)-9,u(r.x0),mm(r.y1-r.y0));
      drawing+=dimV(v(last.y1),v(first.y0),u(first.x0)-21,u(first.x0)-15,mm(last.y1-first.y0));
      drawing+=line(u((first.x0+first.x1)/2),v(first.y0)+3,u((first.x0+first.x1)/2),v(last.y1)-3,'axis');
    }
    const h=d.house.footprintMm;
    h.slice(0,-1).forEach((p,i)=>drawing+=circle(u(p.x),v(p.y),3,`H${i+1}`));
    if(index===0)drawing+=dimV(v(0),v(h[0].y),u(16000),u(h[0].x),'3 000');
    const edges=points.slice(0,-1).map((p,i)=>[p,points[i+1]]).filter(([a,b])=>Math.abs(b.y-a.y)>10000).sort((a,b)=>b[0].x+b[1].x-a[0].x-a[1].x);
    const [a,b]=edges[0],dx=b.x-a.x,dy=b.y-a.y,len=dx*dx+dy*dy;
    const nearest=h.slice(0,-1).map(p=>{const t=((p.x-a.x)*dx+(p.y-a.y)*dy)/len,q={x:a.x+t*dx,y:a.y+t*dy};return {p,q,d:Math.hypot(q.x-p.x,q.y-p.y)};}).sort((a,b)=>a.d-b.d)[0];
    if(index===1)drawing+=line(u(nearest.p.x),v(nearest.p.y),u(nearest.q.x),v(nearest.q.y),'dim')+text((u(nearest.p.x)+u(nearest.q.x))/2,v(nearest.p.y)-5,mm(nearest.d),3,'dim halo','middle');
    const clipHeight=index===0?428:Math.min(210,(topY-17500)/50);
    let out=`<defs><clipPath id="site-${index}"><rect x="12" y="48" width="685" height="${clipHeight}"/></clipPath></defs><g clip-path="url(#site-${index})">${drawing}</g>`;
    out+=text(12,45,index===0?'ULIČNÁ ČASŤ · nadväzuje SI-02 · prekrytie Y 17 500–21 000 mm':'ZÁHRADNÁ ČASŤ · nadväzuje SI-01 · prekrytie Y 17 500–21 000 mm',2.7,'bold');
    out+=paragraph(706,58,'PARCELA 6012/26. Uličný aj pravý KOLMÝ odstup 3 000 mm. Jediný súradnicový rámec C/B/B.',119,3.2,'bold').svg;
    out+=paragraph(706,116,'Katastrálna hranica a požadované osadenie nie sú geodetické vytýčenie. Pred stavbou overiť hranice a výškopis.',119,3).svg;
    if(index===0){const r=d.entryProposal.landingRectMm;
      out+=text(706,192,'VS1 · NÁVRH VSTUPU',3.2,'bold');
      out+=paragraph(706,202,`Pri D2: podesta ${mm(r.x1-r.x0)} × ${mm(r.y1-r.y0)} mm v existujúcom prístupe. Čelo Y ${mm(r.y0)}; dvere sa otvárajú dovnútra.`,119,3).svg;
      out+=paragraph(706,253,'Jeden stupeň h = 150 mm je návrhový cieľ. Výšky podesty a prístupu, spád a prah sú otvorené; výšková väzba ZA-02. Nejde o zameraný ani realizačný stav.',119,3,'bold').svg;
      out+=paragraph(706,323,'Schod je pred podestou. Jeho výška sa meria od miestneho prístupu; neznamená podlahu 150 mm nad ulicou R0.',119,3).svg;
    }
    if(index===1){
      out+=table(12,260,450,[['Bod',.14],['X [mm]',.28],['Y [mm]',.28],['Prvok',.30]],h.slice(0,-1).map((p,i)=>[`H${i+1}`,mm(p.x),mm(p.y),'vonkajšie líce'])).svg;
      out+=paragraph(490,268,`Počiatok lokálneho rámca S-JTSK [mm]: X ${mm(d.originSjtsk.x)}, Y ${mm(d.originSjtsk.y)}. Posun oproti C3: ${mm(d.placement.translationMm.x)} mm v X.`,325,3).svg;
      out+=paragraph(490,305,'R0 = 184,200 m: najvyšší bod ulice pri pracovni podľa stavebníka. Spodná uličná rímsa má podmienený limit 188,700 m. Presné XY bodu, Bpv a rozdiel ΔFFL podlahy k R0 treba potvrdiť; bod sa preto neumiestňuje odhadom.',325,3).svg;
      out+=paragraph(490,362,'Štúdia Z7/Z22: pre samostatný dom uličná čiara 3 m. Overiť 7 m medzi obytnými domami, plochy zelene, spevnenie a dve parkovacie miesta. Podrobné zdroje a otvorené kontroly: UP-01.',325,3).svg;
      out+=paragraph(12,370,'Voda a odpad sa vedú nad nosnou doskou. Vývody a ich úrovne cez obvodovú konštrukciu musia byť určené v novom návrhu; žiadne dodatočné vŕtanie dosky.',440,3.2).svg;
      const first=d.exteriorSteps[0].rect;
      out+=paragraph(12,411,`Vytyčenie stupňov: spoločná os X ${mm((first.x0+first.x1)/2)} mm; prvé čelo Y ${mm(first.y0)} mm = os 6. Krajné líca X ${mm(first.x0)} / ${mm(first.x1)} mm. Odstupy od vonkajších líc krídla: ${mm(first.x0-d.footprint.wingX)} mm / ${mm(d.footprint.x1-first.x1)} mm.`,440,3).svg;
    }
    return sheet(d,`C.SI-0${index+1}`,'Situácia osadenia · '+(index===0?'ulica':'záhrada'),out,'Rozdelenie na dva nadväzujúce listy zachováva 1:50. Hranice a výškové osadenie treba geodeticky overiť. R05 zostáva otvorený.');
  });
}
function planningSheet(d){
  let out=text(12,50,'PARCELA 6012/26 · PRIRADENIE DO Z.7 / SV / ZÓNA C',4,'bold');
  out+=paragraph(12,63,'Priradenie je interpretácia oficiálnej mapy podľa zhodného katastrálneho obrysu. ÚP po zmene č. 3 je účinný od 22.05.2026. Výšková kontrola používa aktuálne pravidlá, nie staré projektové kóty.',806,3.2).svg;
  out+=table(12,90,817,[['Požiadavka',.30],['Údaj / zdroj',.42],['Stav C/B/B',.28]],[
    ['Rímsa najviac 4,5 m','ÚP I.F.3, tlačená str.34: od najvyššej vozovky po spodnú uličnú rímsu. Pri oznámenom R0 = 184,200 m vychádza limit 188,700 m.','M+3,125 je hrana strešnej roviny, nie overený spodok rímsy. ΔFFL a finálny detail chýbajú.'],
    ['Sedlová strecha 25–40°','ÚP I.F.3, str.35, zóna C. Modelový obal je záväzný; sklon sa počíta z vrcholov.','30,706180° / 34,826887°: v rozsahu.'],
    ['Uličná čiara 3 m','Štúdia Z7/Z22, PDF str.2, samostatné domy. Doplnok 2026 o 5 m sa týka radových domov.','Uličný odstup 3 000 mm; hlavný trakt a hrebeň rovnobežne s ulicou.'],
    ['Odstupy','Štúdia Z7/Z22: k hranici min.2 m, pri obytných miestnostiach medzi domami min.7 m.','Pravá hranica 3 000 mm. Skutočný odstup susedného domu treba preveriť.'],
    ['Podlaha, terén a vstup','Štúdia: podlaha max.0,5 m nad upraveným terénom s väzbou na obrubník; pred domom max.3 stupne. Rímsa max.4,5 m nad podlahou.','Stavebník chce aspoň jeden stupeň; návrhový cieľ 1 × 150 mm pred podestou. Nivelácia pásu, terénu a prahový detail chýbajú.'],
    ['Zastavanosť, zeleň, parkovanie','ÚP KZP0,7 vrátane spevnených plôch. Štúdia: budovy max.50 %, zeleň min.30 %, dve parkovacie miesta.','Vyžaduje výkaz zjednotených plôch a overenie státí podľa konečnej situácie.'],
  ],20).svg;
  out+=text(12,349,'OFICIÁLNE PODKLADY · OVERENÉ 14.09.2026',3.6,'bold');
  const links=[['ÚP po zmene č.3 · I.F.3 str.34–35','https://www.mikulov.cz/data/content_files/831/brezi-up-oop-uz.pdf'],['Hlavný výkres I.b','https://www.mikulov.cz/data/content_files/832/1b-hlv-1.pdf'],['Urbanistická kompozícia I.f · výška4,5m','https://www.mikulov.cz/data/content_files/832/1f-urbanisticka-kompozice.pdf'],['Štúdia Z7/Z22 + doplnok2026 · PDF2–4','https://www.mikulov.cz/data/content_files/731/textova-cast-souhlas-obce-stavebni-cara-5m.pdf']];
  links.forEach(([label,url],i)=>out+=`<a href="${url}">${text(12,362+i*17,label,3,'bold')}${text(12,368+i*17,url,2.7)}</a>`);
  out+=table(468,349,356,[['Vzťah k R0 = 184,200 m',.50],['Výška [m]',.50]],[
    ['Hotová podlaha M0','184,200 + ΔFFL'],['Hrana strešných rovín','187,325 + ΔFFL'],['Hrebeň strešných rovín','189,760 + ΔFFL'],['Limit spodnej uličnej rímsy','188,700 (podmienené R0)'],
  ],12).svg;
  out+=paragraph(468,417,'ΔFFL = rozdiel podlahy k ulici v metroch, zatiaľ neurčený. Bpv a XY bodu treba potvrdiť. Vizualizačný biely portál siaha nad strešnú rovinu; finálny obal a spodok rímsy určí detail.',356,2.8).svg;
  return sheet(d,'C.UP-01','Kontrola územného plánu',out,'Nejde o potvrdenie stavebného úradu. Všetky nesplnené alebo neoverené položky zostávajú otvorené do získania konkrétnych podkladov.','tabuľka');
}
function openingSheets(d){
  const rows=openingRows(d),exterior=rows.filter(o=>o.facade!=='interiér'),interior=rows.filter(o=>o.facade==='interiér');
  return [exterior,interior].map((items,i)=>{
    let out=text(12,49,'O1-O10 / D1-D16 PREVZATÉ BEZ PREČÍSLOVANIA · ROZMERY V MM · 1 KS KAŽDÉHO KÓDU',3.5,'bold');
    const cols=[['Kód / zdrojové ID',.24],['Rovina / súradnica',.17],['Od → do',.15],['Š × V / parapet',.16],['Krídlo / priechod',.13],['Druh / miestnosť',.15]];
    const kinds={window:'okno',fixed:'pevné zasklenie',gate:'sekčná brána',door:'dvere',sliding:'posuvné',pocket:'do puzdra',interior:'otočné'};
    const motion=o=>!o.door?'':o.door.motion==='POCKET_SLIDING'?`; posun ${o.door.pocketDirection===1?'+':'−'}${o.axis.toUpperCase()} ${mm(o.door.pocketTravelMm??o.door.leafWidthMm)} mm`:`; pánt ${o.door.hinge===1?'vyššia':'nižšia'} súradnica; smer ${o.door.swing===1?'+':'−'}${o.axis==='x'?'Y':'X'}`;
    const rr=items.map(o=>[`${o.code} / ${o.id}`,`${o.facade} · ${o.axis==='x'?'Y':'X'} ${mm(o.plane)}`,`${o.axis.toUpperCase()} ${mm(o.start)} → ${mm(o.end)}`,`${mm(o.width)} × ${mm(o.height)} / ${mm(o.sill)}`,`${o.leaf??'neurčené'} / ${o.clearWidth??'neurčené'}`,`${kinds[o.kind]??o.kind} / ${o.room}${motion(o)}`]);
    if(i===0){const g=d.triangle.vertices;rr.push(['O11 / svetlík nad O8',`NN2 · Y ${mm(d.house.porches.wingEnd.glazingFaceYmm)}`,`X ${mm(g[0][0])} → ${mm(g[1][0])}`,`${mm(g[1][0]-g[0][0])} × ${mm(g[2][1]-g[0][1])} / ${mm(g[0][1])}`,'pevné / neprechodné','trojuholník / 1.03']);}
    const t=table(12,59,817,cols,rr,14);out+=t.svg;
    out+=paragraph(12,t.bottom+13,'Uvedené rozmery patria otvorom v modeli. Výrobný rozmer rámu, montážna škára, profily, prah, zasklenie, kovanie a požadované vlastnosti zatiaľ nie sú špecifikované. Údaje označené „neurčené“ nemožno odvodiť od oka.',800,3.2,'bold').svg;
    if(i===0)out+=paragraph(12,t.bottom+40,'O11 je doplnený kód svetlíka nad rovinou pôdorysného rezu. Trojuholník nie je obdĺžnik: vrcholy X/Z [mm] (22040;3050), (24040;3050), (24040;4469,649650). Rozmer z geometrie rendereru; výrobná šablóna a osadenie sa musia dopracovať.',800,3).svg;
    else out+=paragraph(12,t.bottom+40,'Orientácia krídel sa preberá z existujúceho pôdorysu; osi, otvory aj kódy sú zachované. Dodávateľ má potvrdiť zárubne, svetlú priechodnosť, výšku prahu a montážne tolerancie, najmä pri H200 a akustických priečkach.',800,3).svg;
    return sheet(d,`D1.1.OT-0${i+1}`,i===0?'Výpis okien a vonkajších dverí':'Výpis vnútorných dverí',out,'R09: modelový výpis je koordinovaný s pôdorysom, výrobná špecifikácia nie je uzavretá. O11 pridáva chýbajúci horný svetlík.','tabuľka');
  });
}
function assemblySheet(d){
  let out=text(12,49,'AKTÍVNE SKLADBY STIEN · STARÉ PODLAHY A STRECHA SA NEPREBERAJÚ',3.5,'bold');
  out+=table(12,60,817,[['Kód',.10],['Aktuálna geometria / skladba',.56],['Stav pre realizáciu',.34]],[
    ['SO30 + TI20','Nosné murivo 300 + vonkajšie kontaktné zateplenie 200 = 500 mm nominálne. Pôdorysné líca miestností zostávajú; lokálne odstupy líc modelu 499–504 mm sa neprepisujú.','Určiť výrobok, omietky a finálne líca, statiku a systémové napojenia.'],
    ['SO50','Voľné piliere / steny krytých terás: plné murivo 500 mm bez ETICS.','Overiť únosnosť, stabilitu, založenie, povrchy.'],
    ...d.materials.filter(m=>['bearing','partition','board'].includes(m.cls)).map(m=>[m.codes,m.text.replace(', napr. Rigips W112','')+(m.codes.includes('SP14')?' Garáž / spálňa a šatník: SP14, 140 mm; vonkajší úsek pri lodžii zostáva SP30.':''),'Kódy a nominálne hrúbky z hotového pôdorysu. Nový výrobok, úplné vrstvy, kotvenie a nosnú funkciu uzavrieť v R01/R04/R07.']),
    ...d.acousticAssemblies.map(a=>[a.code,a.layers.map(l=>`${l.name} ${mm(l.thicknessMm)} mm`).join(' + ')+` = ${a.totalMm} mm. ${a.finishNote}`,a.structuralNote]),
    ['PODLAHY','M0 = pôvodná podlaha, ΔFFL k ulici R0 neznáme. Voda a odpad nad doskou; kúrenie mimo garáže, technickej a sprchy; TZ-01.','Určiť hrúbky, spády, izolácie, vykurovací poter a povrchy. Bez vrtov do dosky.'],
    ['STRECHA / POVALA','Falcovaný plech, bez architektonických presahov. Roviny M+3,125 / M+5,560; povala iba na odkladanie mimo katedrály 1.03.','Drevený nosný strop a záklop; bez betónovej stropnej dosky/nadbetonávky. Určiť skladovacie a bodové zaťaženia, prierezy, spoje, vrstvy a parotesnosť.'],
    ['ZÁKLADY / DOSKA','Monolitický horný pás 350 × 600 mm; vnútorné rebrá; požadovaná doska 150–200 mm. Podľa zadania, nie zamerania. ZA-02.','Overiť zeminu, už realizovaný pás, C16/20 a jeho expozíciu; navrhnúť rozmery, výstuž a škáry.'],
  ],15).svg;
  out+=paragraph(12,433,'H200: požiadavka Rw ≥ 51 dB. Predbežný výpočet z podkladov nie je meranie ani potvrdenie konkrétnej realizácie. SM30: 300 mm obvodová tehla, dôvod odhlučnenia zostáva; Rw nedoložené. Akustika aj kotvenie sa musia posúdiť pre nové nosné riešenie.',805,3.2).svg;
  return sheet(d,'D1.1.SK-01','Skladby konštrukcií · register',out,'Zachované sú rozhodnuté materiály a líca. Chýbajúce nové konštrukcie sú explicitne otvorené; staré rozporné skladby a statika sa nepoužívajú.','tabuľka');
}
export function acousticJunction(d){
  const wall=d.walls.find(w=>w.id==='IW-STUDY-NORTH').rectMm;
  const pier=d.walls.find(w=>w.id==='IW-SPINE-EAST-1').rectMm;
  const nib=d.walls.find(w=>w.id==='C-OFFICE-NORTH-JAMB').rectMm;
  const stub=d.walls.find(w=>w.id==='C-ENTRY-HALL-JAMB').rectMm;
  const assembly=d.acousticAssemblies.find(a=>a.code==='H200');
  const u=x=>25+(x-stub.x0)/5,v=y=>358+(pier.y1-y)/5,endX=wall.x0+400;
  const draw=(r,fill,cls='thin')=>rect(u(r.x0),v(r.y1),(r.x1-r.x0)/5,(r.y1-r.y0)/5,cls,fill);
  let out=text(12,337,`D1 · ${d.h200Junction.code} · PRI ZÁRUBNIACH · 1 : 5`,3.5,'bold');
  for(const r of [pier,nib,stub])out+=draw(r,'url(#murivo)');
  let at=wall.y0;
  for(const l of assembly.layers){const r={x0:l.material==='gypsum-board'?d.h200Joints.J1.x1:wall.x0,x1:endX,y0:at,y1:at+l.thicknessMm};out+=draw(r,l.material==='masonry'?'url(#murivo)':l.material==='mineral-wool'?'url(#insulation)':'#eee');at+=l.thicknessMm;}
  for(const r of Object.values(d.h200Joints))out+=draw(r,'white','dim');
  out+=text(u(wall.x0)+22,v(pier.y1)-4,'KÚPEĽŇA 1.05 · D9',2.7,'bold');
  out+=text(u(wall.x0)+22,v(pier.y0)+8,'PRACOVŇA 1.04 · D8',2.7,'bold');
  out+=text(12,v(stub.y1)-5,'CHODBA',2.5);
  out+=dimV(v(wall.y1),v(pier.y1),u(endX)+10,u(endX),mm(pier.y1-wall.y1));
  out+=dimV(v(wall.y0),v(wall.y1),u(endX)+10,u(endX),mm(wall.y1-wall.y0));
  out+=dimV(v(pier.y0),v(wall.y0),u(endX)+10,u(endX),mm(wall.y0-pier.y0));
  const j1=d.h200Joints.J1,j2=d.h200Joints.J2;
  out+=dimH(u(j1.x0),u(j1.x1),v(j1.y1)-10,v(j1.y1),`J1 · ${mm(j1.x1-j1.x0)}`);
  out+=dimV(v(j2.y0),v(j2.y1),u(j2.x1)+15,u(j2.x1),`J2 · ${mm(j2.y1-j2.y0)}`);
  out+=text(u(nib.x0)+2,v(nib.y0)-4,`${mm(j2.y0-nib.y0)} + ${mm(j2.y1-j2.y0)}`,2.5,'halo');
  out+=table(205,346,620,[['Spoj / súradnice [mm]',.37],['Predpis existujúceho detailu',.63]],[
    ['J1 · X '+mm(j1.x0)+'–'+mm(j1.x1)+' / Y '+mm(j1.y0)+'–'+mm(j1.y1),'Čelo jedinej dosky: 5 mm, Trenn-Fix + Uniflott podľa princípu W623-B2.'],
    ['J2 · X '+mm(j2.x0)+'–'+mm(j2.x1)+' / Y '+mm(j2.y0)+'–'+mm(j2.y1),'5 mm mäkké oddelenie pri líci vonkajšej dosky. Pružný akustický tmel na vhodnej podkladovej vrstve; bez sadry alebo malty.'],
  ],13).svg;
  out+=paragraph(205,399,d.h200Junction.modelNote,616,2.7).svg;
  out+=paragraph(205,429,'Obvodový UD, podtesnenie a mechanické kotvy nie sú v tejto schéme určené. R07: dopracovať kotvy, závesy, stabilitu muriva, spoje pri podlahe a strope a hydroizoláciu sprchy. J2 je projektový detail, nie skúšaný katalógový spoj.',616,2.7,'bold').svg;
  return out;
}
function acousticSheet(d){
  let out=text(12,49,'AK-01 / AK-02 / AK-03 · GEOMETRIA VRSTIEV A NAPOJENÍ',3.5,'bold');
  let y=68;
  for(const a of d.acousticAssemblies){out+=text(12,y,a.code+' · '+a.name,4.2,'bold');let x=25;
    for(const l of a.layers){const w=l.thicknessMm/5;out+=rect(x,y+8,w,55,'medium',l.material==='mineral-wool'?'url(#insulation)':l.material==='masonry'?'url(#murivo)':'#eee');if(l.material!=='gypsum-board')out+=dimH(x,x+w,y+75,y+64,mm(l.thicknessMm));x+=w;}
    const gypsumTotal=a.layers.filter(l=>l.material==='gypsum-board').reduce((sum,l)=>sum+l.thicknessMm,0);
    if(gypsumTotal)out+=dimH(25,25+gypsumTotal/5,y+75,y+64,mm(gypsumTotal));
    out+=dimH(25,x,y+87,y+64,mm(a.totalMm));
    out+=table(150,y+4,675,[['Vrstva',.78],['Hrúbka [mm]',.22]],a.layers.map(l=>[l.name,mm(l.thicknessMm)]),9).svg;
    if(a.code==='SM30')out+=paragraph(150,y+32,'AK-01 / AK-02: dôvod odhlučnenia zostáva. Jedna 300 mm obvodová tehla, bez vaty a predsteny; bežné povrchy navyše. Výrobok, hmotnosť a nepriezvučnosť treba doplniť.',650,3.2).svg;
    y+=130;
  }
  out+=acousticJunction(d);
  return sheet(d,'D1.1.DT-01','Akustické steny H200 / SM30',out,'Vrstvy z lib/acoustic-walls.ts. J1/J2 z lib/h200-junction.json. Detail vrstiev 1:5; realizačné kotvenie a nosné napojenia vyžadujú nový návrh.','1 : 5');
}
function indexSheet(d,register){
  let out=text(12,50,'VÝKRESOVÁ SADA · REGISTER VYDANIA',4.4,'bold');
  out+=paragraph(12,62,'Táto sada zachováva hotový pôdorys C/B/B a oddeľuje presnú modelovú geometriu od konštrukcií, ktoré treba nanovo navrhnúť. Požadovaná realizačná úplnosť zatiaľ nie je dosiahnutá.',800,3.5,'bold').svg;
  out+=table(12,84,380,[['List',.34],['Obsah',.66]],register.map(s=>[s.id,s.title]),10).svg;
  let y=91;
  for(const g of GAPS){out+=text(420,y,`${g.id} · ${g.title}`,3.3,'bold');const p=paragraph(420,y+6,g.need,403,2.8);out+=p.svg;y+=p.height+15;}
  out+=text(12,467,'PODMIENKA VYDANIA: uzavreté R01-R09 + koordinácia všetkých profesií + kontrola všetkých listov.',3.2,'bold');
  return sheet(d,'D1.1.000-C','Register výkresov a otvorených bodov',out,'Požiadavka stavebníka 14.09.2026: nový projekt od začiatku; pôvodná statika orientačná. Pôdorys a hlavný návrh C/B/B bez zmeny.','register');
}
export function renderDrawingSet(d,originalSvg,color){
  const draw={text,line,rect,poly,paragraph,dimH,dimV,table,sheet,planMap,mm};
  const pages=[tracePlan(d,originalSvg),...d.facades.map((f,i)=>facadeSheet(d,f,i)),...CUTS.map((c,i)=>sectionSheet(d,c,i)),foundationSheet(d),clientFoundationSheet(d,draw),foundationAxonSheet(d,draw,color),roofSheet(d),...siteSheets(d),planningSheet(d),...openingSheets(d),assemblySheet(d),acousticSheet(d),clientServicesSheet(d,draw)];
  pages.unshift(indexSheet(d,pages));
  const register=pages.map(p=>({id:p.id,title:p.title,status:p.status,scale:p.scale}));
  const css=`@page{size:841mm 594mm;margin:0}*{box-sizing:border-box}html,body{margin:0;padding:0;background:#bbb;font-family:Arial,Helvetica,sans-serif}.page{width:841mm;height:594mm;overflow:hidden;break-after:page;page-break-after:always;background:white;margin:0}.page:last-child{break-after:auto;page-break-after:auto}.page>svg{display:block;width:841mm;height:594mm}svg text{font-family:Arial,Helvetica,sans-serif;fill:black}.bold{font-weight:700}.muted{fill:#555}.thin{stroke:black;stroke-width:.18}.medium{stroke:black;stroke-width:.35}.heavy{stroke:black;stroke-width:.65}.hair{stroke:#888;stroke-width:.10}.rule{stroke:#aaa;stroke-width:.13}.dim{stroke:${color?'#e30613':'black'};stroke-width:.18}.dim.halo{stroke:white;stroke-width:1.2;paint-order:stroke}.dim text,text.dim{fill:${color?'#e30613':'black'};stroke:none}.extension{stroke:${color?'#e30613':'black'};stroke-width:.1}.axis{stroke:#555;stroke-width:.13;stroke-dasharray:5 1 1 1}.datum{stroke:#555;stroke-width:.2;stroke-dasharray:6 1 1 1}.unknown{stroke:black;stroke-width:.5;stroke-dasharray:4 2}.boundary{stroke:${color?'#c2129b':'black'};stroke-width:.4;stroke-dasharray:5 1 1 1}.cutline{stroke:black;stroke-width:.5;stroke-dasharray:8 1.5 1 1.5}.halo{paint-order:stroke;stroke:white;stroke-width:1.4;stroke-linejoin:round}svg{print-color-adjust:exact;-webkit-print-color-adjust:exact}@media screen{.page{margin:12px auto;box-shadow:0 2px 10px #666}}`;
  const html=`<!doctype html><html lang="sk"><head><meta charset="utf-8"><title>DOM C/B/B · výkresová sada A1</title><style>${css}</style></head><body>${pages.map(p=>`<section class="page" data-sheet="${p.id}">${p.svg}</section>`).join('')}</body></html>`;
  return {html,register};
}
