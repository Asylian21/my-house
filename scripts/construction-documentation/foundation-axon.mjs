/** Deterministic axonometry. Proposal geometry is separate from the building model. */
const esc=v=>String(v).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;');
const mid=(a,b)=>(a+b)/2;
const pathPoints=pts=>pts.map(p=>p.map(n=>Number(n.toFixed(3))).join(',')).join(' ');
const number=n=>n.toLocaleString('sk-SK',{maximumFractionDigits:2});

export function deriveFoundationIllustration(d){
  const facade=id=>d.facades.find(f=>f.def.id===id).def;
  const core=d.house.exteriorWall.masonryMm;
  const axis=id=>{const f=facade(id);return f.inner+f.outward*core/2;};
  const wall=id=>{const w=d.walls.find(w=>w.id===id);if(!w)throw new Error(`Missing foundation illustration source ${id}`);return w;};
  const spine=wall('C-GARAGE-SPINE-N').rectMm;
  // Inner-side 300 mm nominal core, consistent with the original plan faces.
  // This is an explicitly proposed axis, never an as-built foundation centre.
  const loggiaAxis=spine.x1-core/2;
  const closedOutline=[
    [facade('W').outer,facade('S').outer],[facade('E').outer,facade('S').outer],
    [facade('E').outer,facade('NN2').outer],[facade('WW').outer,facade('NN2').outer],
    [facade('WW').outer,facade('N').outer],[d.house.porches.gardenLoggia.eastInnerXmm,facade('N').outer],
    [d.house.porches.gardenLoggia.eastInnerXmm,facade('L').outer],[facade('W').outer,facade('L').outer],
  ];
  const castOutline=d.house.footprintMm.map(p=>[p.x,p.y]);
  if(castOutline[0][0]===castOutline.at(-1)[0]&&castOutline[0][1]===castOutline.at(-1)[1])castOutline.pop();
  // Terrace NN.inner is the far edge of the terrace, NOT a masonry inner face.
  // Continue the explicitly proposed 200 + 150 mm inset at the outer terrace end.
  const terraceEndAxis=d.house.porches.wingEnd.frontYmm-d.house.exteriorWall.insulationMm-core/2;
  const perimeterAxis=[
    [axis('W'),axis('S')],[axis('E'),axis('S')],[axis('E'),terraceEndAxis],[axis('WW'),terraceEndAxis],
    [axis('WW'),axis('N')],[axis('W'),axis('N')],
  ];
  const kid=wall('C-KID-ENTRY-WALL').rectMm,kitchen=wall('C-KITCHEN-BEARING-WALL').rectMm;
  const entry=wall('C-ENTRY-OFFICE-EAST').rectMm,ret=wall('C-ENTRY-OFFICE-RETURN').rectMm;
  const partitionWalls=d.acousticWalls.filter(s=>s.assembly.code==='SA30').map(s=>({code:s.mark,wallId:s.wallId,rectMm:wall(s.wallId).rectMm}));
  if(partitionWalls.length!==2)throw new Error('Review SA30 support routes after assembly change');
  const partitionAxis=mid(partitionWalls[0].rectMm.x0,partitionWalls[0].rectMm.x1);
  if(partitionWalls.some(w=>mid(w.rectMm.x0,w.rectMm.x1)!==partitionAxis))throw new Error('SA30 walls no longer share a support axis');
  const ribs=[
    {id:'R1',points:[[mid(kid.x0,kid.x1),axis('S')],[mid(kid.x0,kid.x1),axis('N')]],sourceKind:'MODEL_LOAD_BEARING_WALL',sourceIds:['C-KID-ENTRY-WALL','C-GARDEN-KID-EAST'],note:'Pod dvojicou nosných úsekov pri izbách; spojenie pod chodbou je návrh.'},
    {id:'R2',points:[[axis('WW'),mid(kitchen.y0,kitchen.y1)],[axis('E'),mid(kitchen.y0,kitchen.y1)]],sourceKind:'MODEL_LOAD_BEARING_WALL',sourceIds:['C-KITCHEN-BEARING-WALL','C-KITCHEN-BEARING-WALL-E'],note:'Pod kuchynskou nosnou líniou; západný prenos a podopretie sa musia vypočítať.'},
    {id:'R3',points:[[mid(entry.x0,entry.x1),axis('S')],[mid(entry.x0,entry.x1),mid(ret.y0,ret.y1)],[ret.x0,mid(ret.y0,ret.y1)]],sourceKind:'MODEL_LOAD_BEARING_WALL',sourceIds:['C-ENTRY-OFFICE-EAST','C-ENTRY-OFFICE-RETURN'],note:'Vetva pod vstupným nosným úsekom a jeho návratom; voľný koniec nie je overené uloženie.'},
    {id:'R4',points:[[axis('WW'),axis('NN2')],[axis('E'),axis('NN2')]],sourceKind:'FACADE_BOUNDARY',sourceIds:['NN2'],note:'Vnútorná trasa pod zadnou stenou obývačky medzi domom a zahrnutou krytou terasou, vrátane úseku pod O8.'},
    {id:'R5',points:[[axis('W'),axis('L')],[loggiaAxis,axis('L')]],sourceKind:'FACADE_BOUNDARY',sourceIds:['L'],note:'Vnútorná trasa pod zadnou stenou garáže pri zahrnutej lodžii, vrátane úseku pod D6.'},
    {id:'R6',points:[[loggiaAxis,axis('L')],[loggiaAxis,axis('N')]],sourceKind:'PARTITION_BOUNDARY_COORDINATION',sourceIds:['C-GARAGE-SPINE-N'],note:'Bočný styk lodžie; zdrojová stena je PARTITION, jej nosná funkcia nie je týmto potvrdená.'},
    {id:'R7',points:[[partitionAxis,axis('S')],[partitionAxis,axis('N')]],sourceKind:'OWN_WEIGHT_PARTITION_SUPPORT',sourceIds:partitionWalls.map(w=>w.wallId),loadedIntervalsMm:partitionWalls.map(w=>({code:w.code,from:w.rectMm.y0,to:w.rectMm.y1})),note:'Kandidátny spojitý pás na výpočet pod vlastnou hmotnosťou dvoch SA30. Chodba ostáva voľná; spojenie prechádza iba pod podlahou. Nie je to schválenie zásahu do existujúcej dosky.'},
  ].map(r=>({...r,status:'COORDINATION_ROUTE_PROPOSAL',designWidthMm:null,designReinforcement:null,foundationSupport:null,heightRequestedMm:d.clientBrief.foundations.requestedRibs.heightMm}));
  return {
    status:'COORDINATION_ILLUSTRATION_NOT_FOR_CONSTRUCTION',closedOutline,castOutline,perimeterAxis,
    castExtentEvidence:d.clientBrief.foundations.reportedCastScope,
    perimeterWidthMm:d.clientBrief.foundations.requestedUpperStrip.widthMm,
    upperHeightMm:d.clientBrief.foundations.requestedUpperStrip.heightMm,
    perimeterPlacement:'PROPOSED_FULL_L_AXIS_WITH_350MM_TERRACE_END_INSET',asBuiltOffsetMm:null,
    view:{type:'PARALLEL_OBLIQUE',streetAtBottom:true,garageOnLeft:true,wingOnRight:true,reflected:false},
    ribs,graphicRibWidthMm:300,graphicWidthIsDesign:false,
    lowerStrip:{widthMm:null,bottomElevationMm:null,asBuiltCoordinates:null,reportedDepthBelowLocalGroundMm:d.clientBrief.foundations.reportedExistingLowerStrip.depthBelowLocalGroundMm},
    excavation:{widthMm:null,bottomElevationMm:null,designDepthMm:null},
    slabThicknessMm:null,absoluteElevations:null,
    foundationLoadApproval:false,
    notRoofLoadBearingWalls:['IW-STUDY-NORTH','C-OPEN-HALL-S','C-OPEN-HALL-N'],
    partitionWalls,
    terraces:{wing:{x0:facade('WW').outer,x1:facade('E').outer,y0:facade('NN2').outer,y1:facade('NN').outer},loggia:{x0:facade('W').outer,x1:d.house.porches.gardenLoggia.eastInnerXmm,y0:facade('L').outer,y1:facade('N').outer}},
  };
}

function poly(pts,fill,stroke='#48515a',width=.9,extra=''){
  return `<polygon points="${pathPoints(pts)}" fill="${fill}" stroke="${stroke}" stroke-width="${width}" stroke-linejoin="round" ${extra}/>`;
}
function line(a,b,color='#707982',width=1,extra=''){
  return `<line x1="${a[0]}" y1="${a[1]}" x2="${b[0]}" y2="${b[1]}" stroke="${color}" stroke-width="${width}" ${extra}/>`;
}
function txt(x,y,value,size=17,weight=400,fill='#172a3b',extra=''){
  return `<text x="${x}" y="${y}" font-family="Arial,Helvetica,sans-serif" font-size="${size}" font-weight="${weight}" style="fill:${fill}" ${extra}>${esc(value)}</text>`;
}
function wrap(x,y,value,width,size=16,fill='#45515c',weight=400){
  const words=value.split(/\s+/);let row='',out='',n=0;
  for(const word of words){if((row+' '+word).length*size*.53>width&&row){out+=txt(x,y+n*size*1.42,row,size,weight,fill);n++;row=word;}else row+=(row?' ':'')+word;}
  if(row)out+=txt(x,y+n*size*1.42,row,size,weight,fill);
  return {svg:out,height:(n+1)*size*1.42};
}
function stripRects(points,width,kind,closed=false){
  const result=[],count=closed?points.length:points.length-1;
  for(let i=0;i<count;i++){
    const a=points[i],b=points[(i+1)%points.length],r=width/2;
    result.push({x0:Math.min(a[0],b[0])-r,x1:Math.max(a[0],b[0])+r,y0:Math.min(a[1],b[1])-r,y1:Math.max(a[1],b[1])+r,kind});
  }return result;
}
/** Grid union removes internal solid faces at rib/perimeter intersections. */
function solidFaces(rects,height){
  const split=values=>{const a=[...new Set(values)].sort((x,y)=>x-y),out=[];
    for(let i=0;i<a.length-1;i++){const n=Math.ceil((a[i+1]-a[i])/1200);for(let j=0;j<n;j++)out.push(a[i]+(a[i+1]-a[i])*j/n);}out.push(a.at(-1));return out;};
  const xs=split(rects.flatMap(r=>[r.x0,r.x1])),ys=split(rects.flatMap(r=>[r.y0,r.y1]));
  const cells=new Map();
  for(let i=0;i<xs.length-1;i++)for(let j=0;j<ys.length-1;j++){
    const x=mid(xs[i],xs[i+1]),y=mid(ys[j],ys[j+1]);
    const r=rects.find(r=>x>r.x0&&x<r.x1&&y>r.y0&&y<r.y1);if(r)cells.set(`${i},${j}`,r.kind);
  }
  const faces=[];
  const face=(pts,kind,side)=>faces.push({pts,kind,side,depth:pts.reduce((s,p)=>s+.4*p[0]-p[1]+.8*p[2],0)/pts.length});
  for(const [key,kind] of cells){const [i,j]=key.split(',').map(Number),x0=xs[i],x1=xs[i+1],y0=ys[j],y1=ys[j+1];
    face([[x0,y0,height],[x1,y0,height],[x1,y1,height],[x0,y1,height]],kind,'top');
    if(!cells.has(`${i+1},${j}`))face([[x1,y0,0],[x1,y1,0],[x1,y1,height],[x1,y0,height]],kind,'east');
    if(!cells.has(`${i},${j-1}`))face([[x0,y0,0],[x1,y0,0],[x1,y0,height],[x0,y0,height]],kind,'south');
  }return faces.sort((a,b)=>a.depth-b.depth);
}
export const foundationViewPoint=([x,y,z=0])=>[x+.4*y,-.8*y-z];
function projection(points,box){
  const raw=foundationViewPoint;
  const pp=points.map(raw),minX=Math.min(...pp.map(p=>p[0])),maxX=Math.max(...pp.map(p=>p[0]));
  const minY=Math.min(...pp.map(p=>p[1])),maxY=Math.max(...pp.map(p=>p[1]));
  const s=Math.min(box.width/(maxX-minX),box.height/(maxY-minY));
  const ox=box.x+(box.width-(maxX-minX)*s)/2,oy=box.y+(box.height-(maxY-minY)*s)/2;
  return p=>{const a=raw(p);return [ox+(a[0]-minX)*s,oy+(a[1]-minY)*s];};
}
function palette(color){return color?{blue:'#82b8eb',blueLine:'#286497',green:'#acc58e',greenDark:'#779864',greenLine:'#426a35',red:'#bd3133',ground:'#eee9de',edge:'#5b6268'}:{blue:'#b6b6b6',blueLine:'#222',green:'#e0e0e0',greenDark:'#a1a1a1',greenLine:'#333',red:'#111',ground:'#f0f0f0',edge:'#555'};}
function renderFaces(faces,p,c,prefix){
  return faces.map(f=>{
    const fill=f.kind==='rib'?(f.side==='top'?c.green:f.side==='east'?c.greenDark:c.green):(f.side==='top'?c.blue:f.side==='east'?'#c4c8ca':'#e0e2e3');
    const pts=f.pts.map(p);
    // No stroke between coplanar grid cells; visible edges are drawn separately.
    return poly(pts,fill,fill,.45)+poly(pts,`url(#${prefix}-aggregate)`,'none',0);
  }).join('');
}
function edges(rects,height,p,c){
  // Outline only exposed boundaries from the same grid union, never internal grid seams.
  const faces=solidFaces(rects,height);let out='';
  for(const f of faces.filter(f=>f.side!=='top')){
    const [a,b,tb,ta]=f.pts.map(p);out+=line(ta,tb,c.edge,.8)+line(a,b,c.edge,.65);
  }
  return out;
}
function tag(p,label,c){return `<circle cx="${p[0]}" cy="${p[1]}" r="15" fill="white" stroke="${c}" stroke-width="2"/>`+txt(p[0],p[1]+5,label,13,700,c,'text-anchor="middle"');}
function dim(a,b,offset,label,p,c){
  const aa=p(a),bb=p(b),a2=[aa[0]+offset[0],aa[1]+offset[1]],b2=[bb[0]+offset[0],bb[1]+offset[1]];
  let angle=Math.atan2(b2[1]-a2[1],b2[0]-a2[0])*180/Math.PI;
  if(angle>90)angle-=180;
  if(angle < -90)angle+=180;
  let out=line(aa,a2,c,.7)+line(bb,b2,c,.7)+line(a2,b2,c,1.1);
  for(const pt of[a2,b2])out+=line([pt[0]-3,pt[1]+5],[pt[0]+3,pt[1]-5],c,1.4);
  return out+`<g transform="translate(${mid(a2[0],b2[0])} ${mid(a2[1],b2[1])}) rotate(${angle})">${txt(0,-7,label,15,700,c,'text-anchor="middle" paint-order="stroke" stroke="white" stroke-width="5"')}</g>`;
}

/** Returns a self-contained 1640 x 1030 vector illustration, not an edited bitmap. */
export function foundationAxonSvg(d,color=true){
  const a=d.foundationIllustration??deriveFoundationIllustration(d),c=palette(color),prefix='foundation-axon';
  const perimeter=stripRects(a.perimeterAxis,a.perimeterWidthMm,'perimeter',true);
  const ribs=a.ribs.flatMap(r=>stripRects(r.points,a.graphicRibWidthMm,'rib'));
  const rects=[...perimeter,...ribs],faces=solidFaces(rects,a.upperHeightMm);
  const allPoints=a.castOutline.flatMap(p=>[[...p,-650],[...p,700]]);
  const p=projection(allPoints,{x:60,y:180,width:1030,height:600});
  let out=`<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1640 1030" width="1640" height="1030" role="img" aria-label="C/B/B: priestorový návrh obvodových pásov a trás vnútorných rebier"><defs><pattern id="${prefix}-aggregate" patternUnits="userSpaceOnUse" width="19" height="17"><path d="M3 4l2-1 1 3z M12 11l3 1-2 2z" stroke="#41505a" stroke-opacity=".18" fill="none" stroke-width=".6"/><circle cx="8" cy="7" r=".55" fill="#52606a" fill-opacity=".18"/></pattern><pattern id="${prefix}-soil" patternUnits="userSpaceOnUse" width="17" height="11"><path d="M2 4l4 2m5-4 3 4" stroke="#b0a38b" stroke-width=".65" opacity=".45"/></pattern></defs><rect width="1640" height="1030" fill="white"/>`;
  out+=txt(36,39,'HLAVNÝ NÁVRH C / B / B',16,700,c.blueLine);
  out+=txt(36,85,'Základy domu v priestore',38,700);
  out+=txt(36,116,'Celý obrys vrátane lodžie a krytej terasy · ulica dole, garáž vľavo',20,400,'#52606a');
  out+=txt(1604,41,'ZA-03 · 14. 09. 2026',15,700,'#56616b','text-anchor="end"');
  out+=line([36,140],[1604,140],'#c9d1d7',1);

  // The floor slab and fill are visually removed, with a neutral ground plane only.
  out+=poly(a.castOutline.map(v=>p([...v,-80])),'#faf9f6','#d1cbc0',1);
  let terraceLabels='';
  for(const [name,t] of Object.entries(a.terraces)){
    const pts=[[t.x0,t.y0],[t.x1,t.y0],[t.x1,t.y1],[t.x0,t.y1]];
    out+=poly(pts.map(v=>p([...v,-80])),'#f3f4f4','#91999e',1,'stroke-dasharray="7 5"');
    const center=p([mid(t.x0,t.x1),mid(t.y0,t.y1),-80]);
    terraceLabels+=txt(center[0],center[1]+(name==='loggia'?10:0),name==='wing'?'KRYTÁ TERASA':'LODŽIA',13,700,'#677079','text-anchor="middle" paint-order="stroke" stroke="white" stroke-width="3"');
  }
  // A broken, schematic continuation is NOT a trench or lower foundation solid.
  for(const r of perimeter){const segments=[[[r.x0,r.y0],[r.x1,r.y0]],[[r.x1,r.y0],[r.x1,r.y1]]];
    for(const [v,w] of segments){const aa=p([...v,0]),bb=p([...w,0]),cc=p([...w,-310]),dd=p([...v,-230]);out+=poly([aa,bb,cc,dd],'#eeeeec','#b4b4b1',.6,'stroke-dasharray="4 4"');}
  }
  out+=renderFaces(faces,p,c,prefix)+edges(rects,a.upperHeightMm,p,c);
  out+=terraceLabels;
  // Dashed outlines are the two real loaded wall footprints, not extra ribs or a corridor wall.
  for(const w of a.partitionWalls){
    const r=w.rectMm,z=a.upperHeightMm+25;
    out+=poly([[r.x0,r.y0],[r.x1,r.y0],[r.x1,r.y1],[r.x0,r.y1]].map(v=>p([...v,z])),'none','#222222',1.8,'stroke-dasharray="5 3"');
    const at=p([r.x0,mid(r.y0,r.y1),z]),label=[at[0]-68,at[1]-5];
    out+=line(at,[label[0]+24,label[1]-4],'#222222',1.2)+txt(label[0],label[1],w.code,15,700,'#222222','text-anchor="middle" paint-order="stroke" stroke="white" stroke-width="4"');
  }
  for(const support of d.house.porches.wingEnd.portalFrame.supportsMm){
    const pts=[[support.startXmm,support.startYmm],[support.endXmm,support.startYmm],[support.endXmm,support.endYmm],[support.startXmm,support.endYmm]];
    out+=poly(pts.map(v=>p([...v,60])),'white',c.red,1.5,'stroke-dasharray="5 3"');
  }
  const pier=d.house.porches.gardenLoggia.cornerPier;
  out+=poly([[pier.startXmm,pier.returnStartYmm],[pier.returnEndXmm,pier.returnStartYmm],
    [pier.returnEndXmm,pier.startYmm],[pier.endXmm,pier.startYmm],[pier.endXmm,pier.endYmm],[pier.startXmm,pier.endYmm]]
    .map(v=>p([...v,60])),'white',c.red,1.5,'stroke-dasharray="5 3"');
  for(const r of a.ribs){
    const v=r.points[0],w=r.points[1],at=p([mid(v[0],w[0]),mid(v[1],w[1]),a.upperHeightMm+90]);
    if(r.id==='R5'){const below=[at[0],at[1]+34];out+=line(at,below,c.greenLine,1)+tag(below,r.id,c.greenLine);}
    else if(r.id==='R7'){const beside=[at[0]+45,at[1]+3];out+=line(at,beside,c.greenLine,1)+tag(beside,r.id,c.greenLine);}
    else out+=tag(at,r.id,c.greenLine);
  }
  const joint=a.ribs[1].points.at(-1);
  out+=tag(p([...joint,720]),'J',c.red);
  const blueTag=p([mid(a.perimeterAxis[0][0],a.perimeterAxis[1][0]),a.perimeterAxis[0][1],720]);
  out+=tag(blueTag,'Z1',c.blueLine);
  out+=dim([...a.castOutline[0],0],[...a.castOutline[1],0],[0,48],`${number(d.house.lowerBar.widthMm)} · ULICA / VSTUP`,p,c.red);
  const right0=a.castOutline[1],right1=a.castOutline[2];
  out+=dim([...right0,0],[...right1,0],[43,0],`${number(right1[1]-right0[1])} · vrátane krytej terasy`,p,c.red);
  const load=d.partitionLoads;
  out+=txt(40,822,'R7 · PODOPRETIE VLASTNEJ HMOTNOSTI SA30 NA VÝPOČET',19,700,c.greenLine);
  out+=wrap(40,851,`AK-01 + AK-02: ${number(load.walls[0].unplastered.kgPerM)} kg/m muriva bez omietky, spolu ${number(load.totals.unplasteredKg)} kg. Povrchy a ďalšie vrstvy navyše. Čiarkovane sú označené iba zaťažené úseky; chodba ostáva voľná.`,1010,17).svg;
  out+=wrap(40,923,'Doska vrátane terás je podľa stavebníka vyliata; tu je odkrytá. R7 je návrh na posúdenie existujúcej dosky, nie pokyn na jej rezanie alebo betonáž.',1010,17,'#713e37',700).svg;

  const rx=1152,rw=445;
  out+=txt(rx,181,'ČO V OBRÁZKU VIDÍŠ',18,700);
  const items=[
    ['Z1',c.blueLine,'Obvod vrátane oboch terás','350 × 600 mm podľa zadania. Líca a skutočné rozmery treba zamerať.'],
    ['R',c.greenLine,'R1 až R7 · návrhové trasy','R1–R6 podľa stien a terás. R7 pod vlastnou hmotnosťou SA30. Výška 600 mm; šírka, uloženie a výstuž na výpočet.'],
    ['J',c.red,'Napojenie rebra na obvod','Označené miesto na návrh spojenia. Obrázok nepredpisuje priemery, počty ani kotvenie prútov.'],
  ];
  let iy=221;
  for(const [code,col,title,note] of items){out+=tag([rx+17,iy-5],code,col)+txt(rx+44,iy,title,18,700);const t=wrap(rx+44,iy+25,note,rw-45,16);out+=t.svg;iy+=t.height+62;}
  out+=line([rx,iy-4],[1600,iy-4],'#d4dadd');
  out+=txt(rx,iy+24,'J · PRINCÍP NAPOJENIA',18,700);
  const detailRects=[{x0:0,x1:350,y0:0,y1:2200,kind:'perimeter'},{x0:350,x1:1850,y0:925,y1:1225,kind:'rib'}];
  const dp=projection(detailRects.flatMap(r=>[[r.x0,r.y0],[r.x1,r.y0],[r.x1,r.y1],[r.x0,r.y1]].flatMap(v=>[[...v,0],[...v,600]])),{x:rx+15,y:iy+49,width:390,height:180});
  out+=renderFaces(solidFaces(detailRects,600),dp,c,prefix)+edges(detailRects,600,dp,c);
  const jp=dp([350,1075,600]);out+=`<ellipse cx="${jp[0]}" cy="${jp[1]}" rx="29" ry="24" fill="none" stroke="${c.red}" stroke-width="2" stroke-dasharray="5 3"/>`;
  out+=wrap(rx,iy+254,'Zväčšený princíp bez mierky. Šírka rebra je grafická. Čiarkované obrysy na terasách označujú nadzemné podpery.',rw,15).svg;
  out+=wrap(rx,iy+326,'Spodný pás: podľa stavebníka 600 mm v zemi. Jeho náznak je prerušovaný; šírka a kóty výkopu zostávajú neurčené.',rw,15).svg;
  out+=line([36,987],[1604,987],'#c9d1d7');
  out+=txt(36,1013,'NÁVRH NA KOORDINÁCIU · NEVYDANÉ NA REALIZÁCIU',16,700,c.red);
  out+=txt(1604,1013,'Axonometria bez odmeriavania · súradnice z modelu C/B/B',14,400,'#52606a','text-anchor="end"');
  const svg=out+'</svg>';
  return color?svg:svg.replace(/#[0-9a-fA-F]{6}/g,hex=>{
    const [r,g,b]=[1,3,5].map(i=>parseInt(hex.slice(i,i+2),16));
    const gray=Math.round(.2126*r+.7152*g+.0722*b).toString(16).padStart(2,'0');
    return '#'+gray.repeat(3);
  });
}

export function foundationAxonSheet(d,draw,color){
  const figure=foundationAxonSvg(d,color).replace('width="1640" height="1030"','x="12" y="42" width="817" height="440" preserveAspectRatio="xMidYMid meet"');
  return draw.sheet(d,'D1.1.ZA-03','Základy · priestorový pohľad na pásy a rebrá',figure,
    'Celý L-obrys vrátane lodžie a krytej terasy. R7 dopĺňa kandidátny pás pod vlastnou hmotnosťou SA30; priečky zostávajú nenosné pre strechu a strop. R1–R7 nemajú potvrdené prierezy, uloženie ani výstuž. Podklad a zdroj hmotnosti: ZA-01.',
    'axonometria');
}
