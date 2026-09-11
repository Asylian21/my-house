/**
 * Data behind the printable PNG sheet of /koncept-2d?variant=c.
 *
 * Everything is derived from the active 3D model: exterior faces from HOUSE,
 * interior walls and doors from the active concept, wall and opening solids
 * from the generated projection. Sizes are plan millimetres; the sheet itself
 * is laid out in paper millimetres at 1:50 (A1 landscape).
 */
import { PLAN_ITEMS, PLAN_ITEM_BY_ID, PLAN_ROOMS, numberSk, type PlanItem, type PlanMesh } from './plan-documentation';
import { ACTIVE_LAYOUT_ID, INTERIOR_DOORS, INTERIOR_WALLS, type InteriorDoor, type RectMm } from './twin-interior';
import { HOUSE } from './twin-active-house';
import { CADASTRAL_PARCELS, GARDEN_POOL, POOL_SURROUND_DECK, POOL_TECHNOLOGY_SHAFT, TERRACE_ZONES_D1, sjtskToLocalMm, terraceZoneDesignAreaM2 } from './twin-site';

export type ExportLevel=1|2|3|4|5;
export type PlanRoom=(typeof PLAN_ROOMS)[number];
export interface ExportLevelSpec { level:ExportLevel; title:string; summary:string }
export const EXPORT_LEVELS:readonly ExportLevelSpec[]=[
  {level:1,title:'Obrys a miestnosti',summary:'Obvod domu, celkové rozmery, modulové osi, čísla a plochy miestností.'},
  {level:2,title:'Konštrukcia a otvory',summary:'Typy stien, kóty fasád s otvormi, kódy okien a dverí a ich tabuľka.'},
  {level:3,title:'Vnútorné rozmery',summary:'Svetlé rozmery miestností, hrúbky stien, polohy dverí, tabuľka miestností.'},
  {level:4,title:'Pevné vybavenie',summary:'Vstavané skrine, kuchyňa, sanita a kotolňa s rozmermi a polohou od stien.'},
  {level:5,title:'Kompletný interiér',summary:'Všetok nábytok, svietidlá, koberce, terasy a auto s úplným súpisom.'},
];
export const EXPORT_REVISION=ACTIVE_LAYOUT_ID;

/** Outer faces of the L-shaped footprint. */
const O=HOUSE.originMm;
export const FOOTPRINT={
  x0:O.x, x1:O.x+HOUSE.lowerBar.widthMm, y0:O.y, gardenY:O.y+HOUSE.lowerBar.depthMm,
  wingX:O.x+HOUSE.wing.xMm, y1:O.y+HOUSE.wing.yMm+HOUSE.wing.depthMm,
} as const;
const F=FOOTPRINT;
export const CHAIN_STEP=700;
export const AXIS_OFFSET=2800;
export const AXIS_RADIUS=200;
const mmText=(n:number)=>numberSk(Math.round(n));
/** Fixed decimals in Slovak notation (areas 30,60 m², lengths 6,0 m). */
export const fixedSk=(n:number,digits:number)=>n.toLocaleString('sk-SK',{minimumFractionDigits:digits,maximumFractionDigits:digits});

// ---------------------------------------------------------------- site
export interface PointMm { x:number; y:number }
/** Subject parcel 6012/26 in the plan frame (street edge is y = 0). */
export const SITE_BOUNDARY:PointMm[]=CADASTRAL_PARCELS.find(p=>p.isSubject)!.sjtskRingMm.map(sjtskToLocalMm);
const siteBox={x0:Math.min(...SITE_BOUNDARY.map(p=>p.x)),x1:Math.max(...SITE_BOUNDARY.map(p=>p.x)),y0:Math.min(...SITE_BOUNDARY.map(p=>p.y)),y1:Math.max(...SITE_BOUNDARY.map(p=>p.y))};
/** Plan rectangle covered by the drawing: chains and axis bubbles, the street edge and the east/north parcel boundary. */
export const PLAN_EXTENT:RectMm={x0:F.x0-4000,y0:-700,x1:siteBox.x1+213,y1:F.y1+AXIS_OFFSET+AXIS_RADIUS};
/** Text along a boundary; `angle` is the plan-space counter-clockwise rotation in degrees. */
export interface SiteLabel { text:string; x:number; y:number; angle:number }
const northEdge=[...SITE_BOUNDARY].sort((a,b)=>b.y-a.y).slice(0,2).sort((a,b)=>a.x-b.x);
const northAt=(x:number)=>northEdge[0].y+(northEdge[1].y-northEdge[0].y)*(x-northEdge[0].x)/(northEdge[1].x-northEdge[0].x);
const northAngle=Math.atan2(northEdge[1].y-northEdge[0].y,northEdge[1].x-northEdge[0].x)*180/Math.PI;
export const SITE_LABELS:SiteLabel[]=[
  {text:'HRANICA POZEMKU STAVEBNÍKA · PARC. Č. 6012/26',x:12000,y:northAt(12000)-380,angle:northAngle},
  {text:'SUSEDNÝ POZEMOK PARC. Č. 6014',x:12000,y:northAt(12000)+300,angle:northAngle},
  {text:'HRANICA POZEMKU STAVEBNÍKA',x:siteBox.x1-330,y:14000,angle:90},
  {text:'KOMUNIKÁCIA · PARC. Č. 6012/1',x:(F.x0+F.x1)/2,y:-330,angle:0},
];

// ---------------------------------------------------------------- outdoor zones
export interface OutdoorZone { id:string; title:string; area:string; rects:RectMm[]; covered:boolean; label:PointMm; vertical?:boolean }
const zoneLabel:Record<string,{label:PointMm;vertical?:boolean}>={'TERR-D1-GARDEN':{label:{x:12240,y:12150}},'TERR-D1-WING':{label:{x:19540,y:16600},vertical:true},'TERR-D1-PORCH':{label:{x:24540,y:20785}}};
/** Timber terraces of D1.1.002 (1.13) with the active areas. */
export const TERRACES:OutdoorZone[]=TERRACE_ZONES_D1.map(zone=>({id:zone.id,title:zone.covered?'KRYTÁ TERASA':'TERASA',area:`${fixedSk(terraceZoneDesignAreaM2(zone),2)} m²`,rects:[...zone.rectsMm],covered:zone.covered,...zoneLabel[zone.id]}));
export const TERRACE_AREA_M2=TERRACE_ZONES_D1.reduce((s,z)=>s+terraceZoneDesignAreaM2(z),0);
const bounds=(points:readonly PointMm[]):RectMm=>({x0:Math.min(...points.map(p=>p.x)),x1:Math.max(...points.map(p=>p.x)),y0:Math.min(...points.map(p=>p.y)),y1:Math.max(...points.map(p=>p.y))});
/** Client pool proposal in the open corner of the L (drawn for orientation, flagged as a proposal). */
export const POOL={
  water:bounds(GARDEN_POOL.waterFootprintMm),coping:bounds(GARDEN_POOL.copingFootprintMm),deck:[...POOL_SURROUND_DECK.rectsMm] as RectMm[],
  shaft:{...POOL_TECHNOLOGY_SHAFT.outerFootprintMm} as RectMm,
  title:`BAZÉN ${fixedSk(GARDEN_POOL.waterLengthMm/1000,1)} × ${fixedSk(GARDEN_POOL.waterWidthMm/1000,1)} m`,note:'návrh stavebníka · koordinovať s projektantom',
};

const wallById=(id:string)=>INTERIOR_WALLS.find(w=>w.id===id)!.rectMm;
const axisX=(id:string)=>{const r=wallById(id);return Math.round((r.x0+r.x1)/2);};
const axisY=(id:string)=>{const r=wallById(id);return Math.round((r.y0+r.y1)/2);};
export interface GridAxis { label:string; at:number }
/** Letters run along the width (X), numbers along the depth (Y). */
export const GRID_X:readonly GridAxis[]=[{label:'A',at:F.x0},{label:'B',at:axisX('C-GARAGE-SPINE-N')},{label:'C',at:axisX('C-OPEN-HALL-S')},{label:'D',at:F.wingX},{label:'E',at:axisX('IW-SPINE-EAST-2')},{label:'F',at:F.x1}];
export const GRID_Y:readonly GridAxis[]=[{label:'1',at:F.y0},{label:'2',at:axisY('B-STREET-KID-TOP')},{label:'3',at:axisY('B-GARDEN-KID-SOUTH-W')},{label:'4',at:F.gardenY},{label:'5',at:HOUSE.porches.wingEnd.glazingFaceYmm},{label:'6',at:F.y1}];
function axisRef(axes:readonly GridAxis[],c:number){
  const on=axes.find(a=>Math.abs(a.at-c)<=300);if(on)return on.label;
  for(let i=0;i<axes.length-1;i++)if(c>=axes[i].at&&c<axes[i+1].at)return `${axes[i].label}–${axes[i+1].label}`;
  return c<axes[0].at?`<${axes[0].label}`:`>${axes[axes.length-1].label}`;
}
export const gridCell=(r:RectMm)=>`${axisRef(GRID_X,(r.x0+r.x1)/2)} / ${axisRef(GRID_Y,(r.y0+r.y1)/2)}`;

// ---------------------------------------------------------------- walls
export type WallKind='exterior'|'bearing'|'partition';
export interface WallType { code:string; kind:WallKind; nominal:number; label:string }
const WALL_TYPE_LIST:WallType[]=[
  {code:'SO50',kind:'exterior',nominal:500,label:'Obvodová stena'},
  {code:'SN30',kind:'bearing',nominal:300,label:'Nosná vnútorná stena'},
  {code:'SN20',kind:'bearing',nominal:200,label:'Nosná vnútorná stena'},
  {code:'SP30',kind:'partition',nominal:300,label:'Deliaca stena garáže'},
  {code:'SP20',kind:'partition',nominal:200,label:'Priečka (vrátane puzdra posuvných dverí)'},
  {code:'SP16',kind:'partition',nominal:160,label:'Priečka'},
  {code:'SP14',kind:'partition',nominal:140,label:'Priečka'},
  {code:'SP10',kind:'partition',nominal:100,label:'Priečka'},
  {code:'SP6',kind:'partition',nominal:60,label:'Dorovnávacia priečka (zárubňa)'},
];
export function wallType(kind:WallKind,thickness:number):WallType {
  const candidates=WALL_TYPE_LIST.filter(t=>t.kind===kind);
  return candidates.reduce((best,t)=>Math.abs(t.nominal-thickness)<Math.abs(best.nominal-thickness)?t:best,candidates[0]);
}
/** Hatch class of the section: masonry envelope, masonry bearing walls, masonry partitions, plasterboard. */
export type WallClass='exterior'|'bearing'|'partition'|'board';
export const wallClass=(kind:WallKind,thickness:number):WallClass=>kind==='exterior'?'exterior':kind==='bearing'?'bearing':thickness>120?'partition':'board';
export interface WallSolid {
  id:string; rect:RectMm; kind:WallKind; thickness:number; type:WallType;
  /** Exterior bands are trimmed by the room floors, which carry the documented inner faces. */
  snap:boolean; mesh?:PlanMesh;
}
const thicknessOf=(r:RectMm)=>Math.min(r.x1-r.x0,r.y1-r.y0);
const wallItems=PLAN_ITEMS.filter(item=>item.category==='walls');
export const SHELL_WALL_MESHES:PlanMesh[]=wallItems.flatMap(item=>item.meshes).filter(m=>m.source==='shell'&&!/obklad|hlava podpory/.test(m.name));
export const INTERIOR_WALL_MESHES:{mesh:PlanMesh;kind:WallKind}[]=wallItems.flatMap(item=>item.meshes.filter(m=>m.source==='interior'&&m.z0<=0).map(mesh=>({mesh,kind:(item.id==='Vnútorná stena'?'exterior':item.name.startsWith('Nosná')?'bearing':'partition') as WallKind})));

// ---------------------------------------------------------------- facades
export type SegmentKind='wall'|'opening'|'open';
export interface FacadeSegment { a:number; b:number; kind:SegmentKind; item?:PlanItem; meshes:PlanMesh[] }
export interface FacadeDef {
  id:string; name:string; axis:'x'|'y'; outer:number; inner:number; from:number; to:number;
  /** Direction from the wall toward the chain rows, in plan axis sense. */
  outward:1|-1; prefix?:string; manual?:FacadeSegment[]; rows:('openings'|'walls'|'overall')[]; codes:boolean;
}
const along=(axis:'x'|'y',r:RectMm):[number,number]=>axis==='x'?[r.x0,r.x1]:[r.y0,r.y1];
const across=(axis:'x'|'y',r:RectMm):[number,number]=>axis==='x'?[r.y0,r.y1]:[r.x0,r.x1];
const OPENING_ITEMS=PLAN_ITEMS.filter(item=>item.category==='openings'&&item.opening&&!INTERIOR_DOORS.some(d=>d.label.split(' · ')[0]===item.id));
function openingAt(def:Pick<FacadeDef,'axis'|'outer'>,a:number,b:number):PlanItem|undefined {
  return OPENING_ITEMS.find(item=>{
    const [p,q]=along(def.axis,item.rect),[c0,c1]=across(def.axis,item.rect);
    const overlap=Math.min(q,b)-Math.max(p,a);
    return overlap>=(b-a)*.5&&c0<=def.outer+700&&c1>=def.outer-700;
  });
}
const porch=HOUSE.porches.wingEnd;
const manualSegment=(a:number,b:number,kind:SegmentKind,item?:PlanItem):FacadeSegment=>({a,b,kind,item,meshes:[]});
export const FACADE_DEFS:FacadeDef[]=[
  {id:'S',name:'Južná (uličná) fasáda',prefix:'Južná fasáda',axis:'x',outer:F.y0,inner:F.y0+504,from:F.x0,to:F.x1,outward:-1,rows:['openings','walls','overall'],codes:true},
  {id:'E',name:'Východná fasáda',prefix:'Východná fasáda',axis:'y',outer:F.x1,inner:F.x1-499,from:F.y0,to:F.y1,outward:1,rows:['openings','walls','overall'],codes:true},
  {id:'N',name:'Záhradná (severná) fasáda',prefix:'Záhradná fasáda',axis:'x',outer:F.gardenY,inner:F.gardenY-501,from:F.x0,to:F.wingX,outward:1,rows:['openings','walls','overall'],codes:true},
  {id:'W',name:'Západný štít garáže',prefix:'Garážový štít',axis:'y',outer:F.x0,inner:F.x0+504,from:F.y0,to:F.gardenY,outward:-1,rows:['openings','walls','overall'],codes:true},
  {id:'WW',name:'Západná stena krídla',prefix:'Západná stena krídla',axis:'y',outer:F.wingX,inner:F.wingX+503,from:F.gardenY,to:F.y1,outward:-1,rows:['openings','walls','overall'],codes:true},
  {id:'NN',name:'Štít krídla · portál krytej terasy',axis:'x',outer:F.y1,inner:porch.glazingFaceYmm,from:F.wingX,to:F.x1,outward:1,rows:['openings','walls','overall'],codes:false,
    manual:[manualSegment(porch.portalFrame.supportsMm[0].startXmm,porch.portalFrame.supportsMm[0].endXmm,'wall'),manualSegment(porch.portalFrame.supportsMm[0].endXmm,porch.portalFrame.supportsMm[1].startXmm,'open'),manualSegment(porch.portalFrame.supportsMm[1].startXmm,porch.portalFrame.supportsMm[1].endXmm,'wall')]},
  {id:'NN2',name:'Krytá terasa · zasklená stena',axis:'x',outer:porch.glazingFaceYmm,inner:porch.glazingFaceYmm-500,from:porch.westPier.startXmm,to:porch.eastWallInnerXmm,outward:1,rows:['openings'],codes:true,
    manual:[manualSegment(porch.westPier.startXmm,porch.westPier.endXmm,'wall'),manualSegment(porch.glazing.startXmm,porch.glazing.startXmm+porch.glazing.widthMm,'opening',PLAN_ITEM_BY_ID.get('Krytá terasa-glazing')),manualSegment(porch.backWall.startXmm,porch.backWall.endXmm,'wall')]},
  {id:'L',name:'Lodžia · zadná stena garáže',prefix:'Lodžia · zadná stena',axis:'x',outer:HOUSE.porches.gardenLoggia.backFaceYmm,inner:HOUSE.porches.gardenLoggia.backFaceYmm-500,from:F.x0+500,to:HOUSE.porches.gardenLoggia.eastInnerXmm,outward:1,rows:['openings'],codes:true},
];
export function facadeSegments(def:FacadeDef):FacadeSegment[] {
  if(def.manual)return def.manual;
  const spans=new Map<string,{a:number;b:number;solid:boolean;parapet:boolean;meshes:PlanMesh[]}>();
  for(const m of SHELL_WALL_MESHES){
    if(!m.name.startsWith(def.prefix!))continue;
    const [a,b]=along(def.axis,m.rect);const key=`${a}:${b}`;
    const span=spans.get(key)??{a,b,solid:false,parapet:false,meshes:[]};
    if(m.z0<=0){if(m.z1>=2700)span.solid=true;else span.parapet=true;}
    span.meshes.push(m);spans.set(key,span);
  }
  const list=[...spans.values()].filter(s=>s.b>def.from&&s.a<def.to).sort((p,q)=>p.a-q.a);
  const out:FacadeSegment[]=[];let cursor=def.from;
  for(const s of list){
    if(s.a>cursor+1)out.push({a:cursor,b:s.a,kind:'open',meshes:[]});
    const item=s.solid?undefined:openingAt(def,s.a,s.b);
    out.push({a:s.a,b:s.b,kind:s.solid?'wall':item||s.parapet?'opening':'open',item,meshes:s.meshes});
    cursor=s.b;
  }
  if(cursor<def.to-1)out.push({a:cursor,b:def.to,kind:'open',meshes:[]});
  return out;
}
export const FACADES=FACADE_DEFS.map(def=>({def,segments:facadeSegments(def)}));

// Exterior bands (600 deep, trimmed by floors when sectioned), porch and
// loggia walls as modelled, interior walls as modelled.
const bandFor=(def:FacadeDef,seg:FacadeSegment):RectMm=>{
  const inwardEnd=def.outer-def.outward*600;
  const lo=Math.min(def.outer,inwardEnd),hi=Math.max(def.outer,inwardEnd);
  return def.axis==='x'?{x0:seg.a,x1:seg.b,y0:lo,y1:hi}:{y0:seg.a,y1:seg.b,x0:lo,x1:hi};
};
const exteriorType=WALL_TYPE_LIST[0];
export const WALL_SOLIDS:WallSolid[]=[
  ...FACADES.filter(({def})=>def.prefix&&def.id!=='L').flatMap(({def,segments})=>segments.filter(s=>s.kind!=='open').map((s,i)=>({id:`${def.id}-${i}`,rect:bandFor(def,s),kind:'exterior' as const,thickness:500,type:exteriorType,snap:true}))),
  ...SHELL_WALL_MESHES.filter(m=>m.z0<=0&&/^Lodžia · (zadná stena \d|východná bočná stena)$|^Krytá terasa · (murovaný pilier pri rohu|plná zadná stena)$/.test(m.name)).map(m=>({id:m.name,rect:m.rect,kind:'exterior' as const,thickness:/bočná/.test(m.name)?m.rect.x1-m.rect.x0:m.rect.y1-m.rect.y0,type:exteriorType,snap:false,mesh:m})),
  // The porch glazing closes the living room like the pier and the back wall do.
  {id:'porch-glazing',rect:{x0:porch.glazing.startXmm,x1:porch.glazing.startXmm+porch.glazing.widthMm,y0:porch.glazingFaceYmm-500,y1:porch.glazingFaceYmm},kind:'exterior',thickness:500,type:exteriorType,snap:false},
  ...INTERIOR_WALL_MESHES.map(({mesh,kind})=>{const t=thicknessOf(mesh.rect);return {id:mesh.name,rect:mesh.rect,kind,thickness:t,type:wallType(kind,t),snap:kind==='exterior',mesh};}),
];
/** Wall types present in the model with the thickness range actually modelled. */
export const WALL_TYPES_USED=WALL_TYPE_LIST.map(type=>{
  const thicknesses=WALL_SOLIDS.filter(s=>s.type===type&&s.mesh&&s.kind!=='exterior').map(s=>Math.round(s.thickness));
  if(type.kind==='exterior')return {type,range:'500 · líce podláh v modeli 499–504 · bočná stena lodžie 400'};
  if(!thicknesses.length)return null;
  const min=Math.min(...thicknesses),max=Math.max(...thicknesses);
  return {type,range:min===max?`${min}`:`${min}–${max}`};
}).filter((t):t is {type:WallType;range:string}=>t!==null);
export interface MaterialLegendEntry { cls:WallClass; codes:string; text:string }
/** Material legend in the wording of D1.1.002, restricted to the wall types the model contains. */
export const MATERIAL_LEGEND:MaterialLegendEntry[]=(()=>{
  const used=(cls:WallClass)=>WALL_TYPES_USED.map(u=>u.type).filter(t=>wallClass(t.kind,t.nominal)===cls);
  const codes=(cls:WallClass)=>used(cls).map(t=>t.code).join(', ');
  const nominal=(cls:WallClass)=>[...new Set(used(cls).map(t=>t.nominal))].sort((a,b)=>b-a).map(String).join(' / ');
  const out:MaterialLegendEntry[]=[
    {cls:'exterior',codes:codes('exterior'),text:`Nosné obvodové murivo z keramických tvaroviek hr. ${nominal('exterior')} mm s výplňou z minerálnej izolácie, na systémovú murovaciu maltu`},
    {cls:'bearing',codes:codes('bearing'),text:`Nosné vnútorné murivo z keramických tvaroviek hr. ${nominal('bearing')} mm, na systémovú murovaciu maltu`},
    {cls:'partition',codes:codes('partition'),text:`Nenosné priečkové murivo z keramických tvaroviek hr. ${nominal('partition')} mm, na systémovú murovaciu maltu (vrátane puzdra posuvných dverí)`},
    {cls:'board',codes:codes('board'),text:`Sadrokartónové systémové priečky a predsteny hr. ${nominal('board')} mm, napr. Rigips W112, s výplňou z minerálnej vlny`},
  ];
  return out.filter(e=>e.codes.length>0);
})();

// ---------------------------------------------------------------- chains
export interface ChainSpec {
  axis:'x'|'y'; at:number; points:number[]; solid?:boolean[]; ext?:number; textSide:1|-1; role:'facade'|'section'|'door';
  /** Second text row on the far side of the line, per segment: opening height (sill) as in D1.1.002. */
  sub?:(string|undefined)[];
}
export interface SectionLine { axis:'x'|'y'; at:number; from:number; to:number }
/** Interior dimension lines: wall faces cut by a straight line through the rooms. */
export const SECTION_LINES:SectionLine[]=[
  {axis:'x',at:4200,from:F.x0,to:F.x1},
  {axis:'x',at:7550,from:F.x0,to:F.x1},
  {axis:'x',at:8500,from:F.x0,to:F.x1},
  {axis:'x',at:9000,from:21543,to:F.x1},
  {axis:'x',at:15000,from:F.wingX,to:F.x1},
  {axis:'y',at:10500,from:F.y0,to:F.gardenY},
  {axis:'y',at:12800,from:F.y0,to:F.gardenY},
  {axis:'y',at:16800,from:F.y0,to:F.gardenY},
  {axis:'y',at:22600,from:F.y0,to:F.y1},
  {axis:'y',at:25500,from:F.y0,to:F.y1},
];
const ROOM_RECTS=PLAN_ROOMS.flatMap(room=>room.rectsMm.map(rect=>({room,rect})));
export function sectionChain(line:SectionLine):ChainSpec {
  const {axis,at,from,to}=line;
  const hits=(r:RectMm)=>{const [c0,c1]=across(axis,r);return c0<at&&c1>at;};
  const intervals:[number,number][]=[];
  for(const s of WALL_SOLIDS){
    if(!hits(s.rect))continue;
    const [p,q]=along(axis,s.rect);let parts:[number,number][]=[[Math.max(p,from),Math.min(q,to)]];
    if(s.snap)for(const {rect} of ROOM_RECTS){
      if(!hits(rect))continue;const [ra,rb]=along(axis,rect);
      parts=parts.flatMap(([a,b])=>{if(rb<=a||ra>=b)return [[a,b]] as [number,number][];const out:[number,number][]=[];if(ra>a)out.push([a,ra]);if(rb<b)out.push([rb,b]);return out;});
    }
    intervals.push(...parts.filter(([a,b])=>b-a>=1));
  }
  intervals.sort((p,q)=>p[0]-q[0]);
  const merged:[number,number][]=[];
  for(const iv of intervals){const last=merged[merged.length-1];if(last&&iv[0]<=last[1]+15)last[1]=Math.max(last[1],iv[1]);else merged.push([iv[0],iv[1]]);}
  const points=[from],solid:boolean[]=[];let cursor=from;
  for(const [a,b] of merged){if(a>cursor+15){points.push(a);solid.push(false);}points.push(b);solid.push(true);cursor=b;}
  if(to>cursor+15){points.push(to);solid.push(false);}
  return {axis,at,points,solid,textSide:-1,role:'section'};
}
export const SECTION_CHAINS=SECTION_LINES.map(sectionChain);

/** Facade rows: 1 openings, 2 abutting wall faces, 3 overall. */
export function facadeRowPoints(def:FacadeDef,segments:FacadeSegment[],row:'openings'|'walls'|'overall'):number[] {
  if(row==='overall')return [def.from,def.to];
  if(row==='openings')return [...new Set(segments.flatMap(s=>[s.a,s.b]))].sort((a,b)=>a-b);
  // Perpendicular walls meeting the inner face: modelled interior walls, the
  // exact porch/loggia walls and the inner faces of the facades at both ends.
  const intervals:[number,number][]=[];
  for(const s of WALL_SOLIDS){
    if(s.snap)continue;
    const [c0,c1]=across(def.axis,s.rect),[p,q]=along(def.axis,s.rect);
    if(!(c0<=def.inner+20&&c1>=def.inner-20)||q-p>600)continue;
    const a=Math.max(p,def.from),b=Math.min(q,def.to);if(b-a<1)continue;
    intervals.push([a,b]);
  }
  intervals.sort((p,q)=>p[0]-q[0]);
  const merged:[number,number][]=[];
  for(const iv of intervals){const last=merged[merged.length-1];if(last&&iv[0]<=last[1]+250)last[1]=Math.max(last[1],iv[1]);else merged.push([iv[0],iv[1]]);}
  const pts=new Set<number>([def.from,def.to]);
  for(const [a,b] of merged){pts.add(a);pts.add(b);}
  for(const other of FACADE_DEFS){
    if(other.axis===def.axis)continue;
    if(Math.abs(other.outer-def.from)<=20||Math.abs(other.outer-def.to)<=20)pts.add(other.inner);
  }
  return [...pts].filter(p=>p>=def.from&&p<=def.to).sort((a,b)=>a-b).filter((p,i,arr)=>i===0||p-arr[i-1]>15);
}
/** "výška (parapet)" of an opening, the second dimension row of the openings chain. */
export const openingSub=(item:PlanItem)=>`${mmText(item.opening!.height)} (${mmText(item.opening!.sill)})`;
export function facadeChains(level:ExportLevel):ChainSpec[] {
  const chains:ChainSpec[]=[];
  for(const {def,segments} of FACADES){
    const rows=def.rows.filter(row=>row==='overall'?level>=1:row==='openings'?level>=2:level>=3);
    rows.forEach((row,index)=>{
      const points=facadeRowPoints(def,segments,row);
      if(points.length<2)return;
      const sub=row==='openings'?points.slice(1).map((b,i)=>{
        const seg=segments.find(s=>s.kind==='opening'&&s.item&&Math.abs(s.a-points[i])<=1&&Math.abs(s.b-b)<=1);
        return seg?openingSub(seg.item!):undefined;
      }):undefined;
      // Text above / left of the line, the second row (height and sill) below / right of it.
      chains.push({axis:def.axis,at:def.outer+def.outward*CHAIN_STEP*(index+1),points,ext:row==='walls'?def.inner:def.outer,textSide:-1,role:'facade',sub});
    });
  }
  return chains;
}

/** Door chains run this far inside the room the leaf swings into; inner dimension texts sit closer to the wall. */
export const DOOR_CHAIN_OFFSET=650;
export const INNER_DIM_OFFSET=300;
/** Door positions measured inside the room the leaf swings into. */
export function doorChains():ChainSpec[] {
  const groups=new Map<string,ChainSpec&{ends:[number,number]}>();
  for(const door of INTERIOR_DOORS){
    const [w0,w1]=door.wallSpanMm,start=door.startMm,end=door.startMm+door.widthMm;
    const pick=(side:1|-1)=>ROOM_RECTS.find(({rect})=>{
      const [face,lo,hi]=door.axis==='X'?[side===1?rect.y0:rect.y1,rect.x0,rect.x1]:[side===1?rect.x0:rect.x1,rect.y0,rect.y1];
      return Math.abs(face-(side===1?w1:w0))<=5&&lo<=start+5&&hi>=end-5;
    });
    const side:1|-1=pick(door.swing)?door.swing:pick(-door.swing as 1|-1)?(-door.swing as 1|-1):door.swing;
    const found=pick(side);if(!found)continue;
    const rect=found.rect,face=side===1?w1:w0,at=face+side*DOOR_CHAIN_OFFSET;
    const ends:[number,number]=door.axis==='X'?[rect.x0,rect.x1]:[rect.y0,rect.y1];
    const key=`${door.axis}:${face}:${ends.join(':')}`;
    const group=groups.get(key)??{axis:door.axis==='X'?'x':'y',at,points:[...ends],ends,ext:face,textSide:-1 as const,role:'door' as const};
    group.points.push(start,end);groups.set(key,group);
  }
  return [...groups.values()].map(g=>({...g,points:[...new Set(g.points)].sort((a,b)=>a-b)}));
}
export const DOOR_CHAINS=doorChains();

/** "šírka / výška" of an interior door, written in the opening together with its D-code (centre of the wall gap). */
export interface DoorText { door:InteriorDoor; axis:'x'|'y'; x:number; y:number; text:string }
export const DOOR_TEXTS:DoorText[]=INTERIOR_DOORS.map(door=>{
  const opening=PLAN_ITEM_BY_ID.get(door.label.split(' · ')[0])?.opening;
  const [w0,w1]=door.wallSpanMm,plane=(w0+w1)/2,mid=door.startMm+door.widthMm/2;
  return {door,axis:door.axis==='X'?'x':'y',x:door.axis==='X'?mid:plane,y:door.axis==='X'?plane:mid,text:`${mmText(opening?.width??door.widthMm)} / ${mmText(opening?.height??2100)}`};
});

// ---------------------------------------------------------------- inner dimensions
export interface InnerDim { axis:'x'|'y'; x:number; y:number; text:string; len:number }
/** Plan millimetres per character of the 2,2 mm inner-dimension type at 1:50. */
const CHAR_MM=62,TEXT_H=120;
interface TextBox { x0:number; x1:number; y0:number; y1:number }
const textBox=(axis:'x'|'y',x:number,y:number,len:number):TextBox=>axis==='x'?{x0:x-len/2,x1:x+len/2,y0:y-TEXT_H/2,y1:y+TEXT_H/2}:{x0:x-TEXT_H/2,x1:x+TEXT_H/2,y0:y-len/2,y1:y+len/2};
const overlaps=(a:TextBox,b:TextBox,pad:number)=>a.x0<b.x1+pad&&a.x1>b.x0-pad&&a.y0<b.y1+pad&&a.y1>b.y0-pad;
/** Door code + dimension block straddles the wall: about 210 mm across, text length along. */
const DOOR_TEXT_BOXES=DOOR_TEXTS.map(t=>{const b=textBox(t.axis,t.x,t.y,t.text.length*CHAR_MM*.7);return t.axis==='x'?{...b,y0:t.y-110,y1:t.y+110}:{...b,x0:t.x-110,x1:t.x+110};});
function innerDimFree(box:TextBox):boolean {
  for(const line of SECTION_LINES){
    const lineBox:TextBox=line.axis==='x'?{x0:line.from,x1:line.to,y0:line.at-260,y1:line.at+60}:{x0:line.at-60,x1:line.at+260,y0:line.from,y1:line.to};
    if(overlaps(box,lineBox,40))return false;
  }
  return !DOOR_TEXT_BOXES.some(b=>overlaps(box,b,80));
}
/** A section chain already dimensions the rectangle in this direction when it runs right through it. */
const sectionCovers=(r:RectMm,axis:'x'|'y')=>SECTION_LINES.some(line=>line.axis===axis&&(axis==='x'
  ?line.at>r.y0&&line.at<r.y1&&line.from<=r.x0+5&&line.to>=r.x1-5
  :line.at>r.x0&&line.at<r.x1&&line.from<=r.y0+5&&line.to>=r.y1-5));
/** Clear room dimensions written along the inner wall faces (D1.1.002 convention) wherever no section chain already gives them; up to two floor rectangles per room. */
export function innerDims(room:PlanRoom):InnerDim[] {
  const out:InnerDim[]=[];
  const rects=roomRectsByArea(room).filter(r=>r.x1-r.x0>=900&&r.y1-r.y0>=900).slice(0,2);
  rects.forEach((r,index)=>{
    const w=r.x1-r.x0,d=r.y1-r.y0;
    if(index>0&&w*d<1.5e6)return;
    const cx=(r.x0+r.x1)/2,cy=(r.y0+r.y1)/2;
    const place=(axis:'x'|'y',text:string,positions:number[],alongs:number[])=>{
      const len=text.length*CHAR_MM;
      let best:InnerDim|undefined;
      for(const pos of positions)for(const along of alongs){
        const [x,y]=axis==='x'?[along,pos]:[pos,along];
        const dim={axis,x,y,text,len};
        if(!best)best=dim;
        if(innerDimFree(textBox(axis,x,y,len))){out.push(dim);return;}
      }
      if(best)out.push(best);
    };
    if(!sectionCovers(r,'x'))place('x',mmText(w),[r.y1-INNER_DIM_OFFSET,r.y0+INNER_DIM_OFFSET],[cx,cx-w/4,cx+w/4]);
    if(!sectionCovers(r,'y'))place('y',mmText(d),[r.x0+INNER_DIM_OFFSET,r.x1-INNER_DIM_OFFSET],[cy,cy-d/4,cy+d/4]);
  });
  return out;
}

// ---------------------------------------------------------------- openings
export type OpeningKind='window'|'fixed'|'door'|'sliding'|'gate'|'interior'|'pocket';
export interface CodedOpening { code:string; item:PlanItem; kind:OpeningKind; label:string; facade?:FacadeDef; door?:InteriorDoor; room:PlanRoom|undefined }
const OPENING_KIND_LABEL:Record<OpeningKind,string>={window:'okno',fixed:'pevné presklenie',door:'dvere',sliding:'posuvné presklenie',gate:'sekčná brána',interior:'vnútorné dvere',pocket:'posuvné dvere do puzdra'};
function exteriorKind(item:PlanItem):OpeningKind {
  if(item.id==='GARAGE-DOOR')return 'gate';
  if(/posuvn|Terasové presklenie/.test(item.name+item.id))return 'sliding';
  if(item.opening!.sill>0)return 'window';
  if(/glazing|pevné/.test(item.id+item.name)||/FRONT-04|FRONT-07/.test(item.id))return 'fixed';
  return 'door';
}
/** Clockwise walk around the house: street front, east side, porch, wing, garden, west, loggia. */
const FACADE_ORDER:[string,boolean][]=[['S',false],['E',false],['NN2',true],['WW',true],['N',true],['W',true],['L',false]];
export const CODED_OPENINGS:CodedOpening[]=(()=>{
  const list:CodedOpening[]=[];let o=0,d=0;
  const seen=new Set<string>();
  for(const [id,reverse] of FACADE_ORDER){
    const facade=FACADES.find(f=>f.def.id===id);if(!facade)continue;
    const segments=reverse?[...facade.segments].reverse():facade.segments;
    for(const seg of segments){
      if(!seg.item||seen.has(seg.item.id))continue;seen.add(seg.item.id);
      const kind=exteriorKind(seg.item);
      const isWindow=kind==='window'||kind==='fixed';
      const code=isWindow?`O${++o}`:`D${++d}`;
      list.push({code,item:seg.item,kind,label:OPENING_KIND_LABEL[kind],facade:facade.def,room:PLAN_ROOMS.find(r=>r.id===seg.item!.roomId)});
    }
  }
  for(const item of OPENING_ITEMS){
    if(seen.has(item.id)||item.opening!.height<=0)continue;
    seen.add(item.id);const kind=exteriorKind(item);const isWindow=kind==='window'||kind==='fixed';
    list.push({code:isWindow?`O${++o}`:`D${++d}`,item,kind,label:OPENING_KIND_LABEL[kind],room:PLAN_ROOMS.find(r=>r.id===item.roomId)});
  }
  const doors=[...INTERIOR_DOORS].sort((a,b)=>(PLAN_ROOMS.findIndex(r=>r.id===a.toRoomId)-PLAN_ROOMS.findIndex(r=>r.id===b.toRoomId))||a.startMm-b.startMm);
  for(const door of doors){
    const item=PLAN_ITEM_BY_ID.get(door.label.split(' · ')[0]);if(!item)continue;
    const kind:OpeningKind=door.motion==='POCKET_SLIDING'?'pocket':'interior';
    list.push({code:`D${++d}`,item,kind,label:OPENING_KIND_LABEL[kind],door,room:PLAN_ROOMS.find(r=>r.id===door.toRoomId)});
  }
  return list;
})();
export const OPENING_BY_ITEM=new Map(CODED_OPENINGS.map(o=>[o.item.id,o]));
export const OPENING_BY_DOOR=new Map(CODED_OPENINGS.filter(o=>o.door).map(o=>[o.door!.id,o]));

// ---------------------------------------------------------------- items
export type ItemCode='N'|'Z'|'L'|'F';
export const ITEM_CODE_LABEL:Record<ItemCode,string>={N:'Nábytok',Z:'Zariadenie · sanita · technika',L:'Svietidlá',F:'Podlahové a stenové prvky'};
export interface CodedItem {
  code:string; letter:ItemCode; item:PlanItem; level:4|5; labeled:boolean; room:PlanRoom|undefined;
  fromWest:number; fromSouth:number; width:number; depth:number; height:number; mount:number; cell:string;
}
/** Not drawn at all: floors, ceilings, skirtings, tiling, soffits and claddings have no plan footprint of their own. */
export const HIDDEN_ITEM=/Podkladová|-Podlaha$|-Podhľad$|Soklové|Obklad stien|podbitka|pás venca|štít nad vencom|svetlík|Lodžia · podhľad|obklad|Modřínové pole|Smrekovcové pole/i;
/** Exterior steps belong to the building and appear on every level. */
export const ALWAYS_DRAWN=/betónový stupeň/;
/** Drawn (when their level applies) but neither coded nor listed: loose contents and sub-parts. */
const CLUTTER=/kartónová|plastový box|plechovka|kufrík|vedro|hadica|LONG-TOOL|PELLET-BAG|SAFETY-GROUP|FEED-HOSE|AUGER|BURNER|BOILER-BASE|DRAWING|-ART$|WINDOW$|betónový stupeň/;
/** Listed but without a plan label: stacked, overhead or wall-mounted parts. */
const TABLE_ONLY=/DRYER|kitchen-oven|kitchen-extractor|kitchen-upper|OVERHEAD|HYDRAULIC-RESERVE|-lamp$|-board$|MIRROR|HOOKS|PEGBOARD|GARAGE-SHELF|VACUUM|LIGHT1|LIGHT2|kitchen-sink/;
const FIXED_FURNITURE=/CABINET|DRESSING|kitchen-|WARDROBE|TV-WALL|ENTRY-BENCH/;
const LOOSE_EQUIPMENT=/MOWER|vehicle|kartónová|plastový box|plechovka|kufrík|vedro|hadica|LONG-TOOL/;
export const isFixedItem=(item:PlanItem)=>(item.category==='equipment'&&!LOOSE_EQUIPMENT.test(item.id))||(item.category==='furniture'&&FIXED_FURNITURE.test(item.id));
const roomOrder=(roomId:string)=>{const i=PLAN_ROOMS.findIndex(r=>r.id===roomId);return i<0?99:i;};
const isPlanItem=(item:PlanItem)=>item.category!=='walls'&&item.category!=='openings'&&!HIDDEN_ITEM.test(item.id)&&!HIDDEN_ITEM.test(item.name)&&!ALWAYS_DRAWN.test(item.id);
export const CODED_ITEMS:CodedItem[]=(()=>{
  const counters:Record<ItemCode,number>={N:0,Z:0,L:0,F:0};
  const items=PLAN_ITEMS.filter(item=>isPlanItem(item)&&!CLUTTER.test(item.id))
    .sort((a,b)=>roomOrder(a.roomId)-roomOrder(b.roomId)||a.rect.x0-b.rect.x0||b.rect.y1-a.rect.y1);
  return items.map(item=>{
    const letter:ItemCode=item.category==='furniture'?'N':item.category==='equipment'?'Z':item.category==='lighting'?'L':'F';
    const room=PLAN_ROOMS.find(r=>r.id===item.roomId);
    const origin=room?room.bounds:{x0:F.x0,y0:F.y0};
    return {code:`${letter}${++counters[letter]}`,letter,item,level:isFixedItem(item)?4:5,labeled:!TABLE_ONLY.test(item.id),room,
      fromWest:Math.round(item.rect.x0-origin.x0),fromSouth:Math.round(item.rect.y0-origin.y0),
      width:Math.round(item.rect.x1-item.rect.x0),depth:Math.round(item.rect.y1-item.rect.y0),height:Math.round(item.z1-item.z0),mount:Math.round(item.z0),cell:gridCell(item.rect)};
  });
})();
export const drawnItems=(level:ExportLevel)=>level<4?[]:PLAN_ITEMS.filter(item=>isPlanItem(item)&&(level>=5||isFixedItem(item)));
export const STRUCTURAL_EXTRAS=PLAN_ITEMS.filter(item=>ALWAYS_DRAWN.test(item.id));
/** Parts above the conventional 1,2 m cut are drawn dashed. */
export const CUT_PLANE_MM=1200;
export const codedItems=(level:ExportLevel)=>CODED_ITEMS.filter(c=>c.level<=level);

// ---------------------------------------------------------------- rooms
export type RoomKind='living'|'wet'|'tech'|'garage'|'circulation';
export const ROOM_KIND_LABEL:Record<RoomKind,string>={living:'Obytné miestnosti',wet:'Hygienické zázemie',tech:'Technická miestnosť',garage:'Garáž',circulation:'Komunikácie a šatník'};
export function roomKind(room:PlanRoom):RoomKind {
  if(room.number==='1.12')return 'garage';
  if(room.number==='1.07')return 'tech';
  if(room.wetRoom||room.floor==='TILE')return 'wet';
  if(['1.01','1.02','1.14'].includes(room.number))return 'circulation';
  return 'living';
}
export const floorLabel=(room:PlanRoom)=>room.floor==='VINYL'?'vinyl':room.floor==='TILE'?'dlažba':'epoxid';
/** Clear height under the ridge of the vaulted living room (D1.1.002: 4850/2750). */
export const RIDGE_CLEAR_MM=4850;
export const ceilingLabel=(room:PlanRoom)=>room.ceiling==='VAULTED_TO_RIDGE'?`šikmý do ${mmText(RIDGE_CLEAR_MM)}`:'rovný';
/** Surface finishes in the wording of the D1.1.002 room legend. */
export const finishFloor=(room:PlanRoom)=>room.floor==='VINYL'?'VINYL':room.floor==='TILE'?'KERAMICKÁ DLAŽBA':'EPOXIDOVÁ STIERKA';
export const finishWalls=(room:PlanRoom)=>room.wetRoom?'KER. OBKLAD v. 2 100':'VÁPENOCEM. OMIETKA';
export const finishCeiling=(room:PlanRoom)=>room.ceiling==='VAULTED_TO_RIDGE'?'SDK PODHĽAD · ŠIKMÝ':room.wetRoom?'SDK PODHĽAD · VLHKÉ PR.':'SDK PODHĽAD';
export const clearHeightLabel=(room:PlanRoom)=>room.ceiling==='VAULTED_TO_RIDGE'?`${mmText(RIDGE_CLEAR_MM)} / ${mmText(room.clearHeightMm)}`:mmText(room.clearHeightMm);
export const roomAxes=(room:PlanRoom)=>gridCell(room.bounds);
/** Floor rectangles trimmed by exact exterior walls that the model draws over the floor (porch wall over 1.03). */
export function clearRects(room:PlanRoom):RectMm[] {
  const walls=WALL_SOLIDS.filter(s=>s.kind==='exterior'&&!s.snap);
  return room.rectsMm.map(rect=>{
    let r={...rect};
    for(const side of ['y1','y0','x1','x0'] as const){
      const overlapping=walls.filter(w=>w.rect.x0<r.x1&&w.rect.x1>r.x0&&w.rect.y0<r.y1&&w.rect.y1>r.y0);
      const onEdge=overlapping.filter(w=>side==='y1'?w.rect.y1>=r.y1-10:side==='y0'?w.rect.y0<=r.y0+10:side==='x1'?w.rect.x1>=r.x1-10:w.rect.x0<=r.x0+10);
      const vertical=side==='y1'||side==='y0';
      const covered=onEdge.reduce((s,w)=>s+(vertical?Math.min(w.rect.x1,r.x1)-Math.max(w.rect.x0,r.x0):Math.min(w.rect.y1,r.y1)-Math.max(w.rect.y0,r.y0)),0);
      const span=vertical?r.x1-r.x0:r.y1-r.y0;
      if(covered<span*.9)continue;
      if(side==='y1')r={...r,y1:Math.min(...onEdge.map(w=>w.rect.y0))};
      else if(side==='y0')r={...r,y0:Math.max(...onEdge.map(w=>w.rect.y1))};
      else if(side==='x1')r={...r,x1:Math.min(...onEdge.map(w=>w.rect.x0))};
      else r={...r,x0:Math.max(...onEdge.map(w=>w.rect.x1))};
    }
    return r;
  });
}
/** Largest floor rectangles first; the sheet lists up to three per room. */
export const roomRectsByArea=(room:PlanRoom)=>clearRects(room).sort((a,b)=>(b.x1-b.x0)*(b.y1-b.y0)-(a.x1-a.x0)*(a.y1-a.y0));
/** Label anchors chosen to stay clear of section lines, door chains and fixed furniture. */
export interface RoomLabelPos { x:number; y:number; narrow?:boolean; furnished?:{x:number;y:number} }
export const ROOM_LABEL_POS:Record<string,RoomLabelPos>={
  '1.01':{x:21740,y:5150,narrow:true},
  '1.02':{x:22050,y:9800,narrow:true},
  '1.03':{x:24542,y:16200,furnished:{x:26350,y:13840}},
  '1.04':{x:24500,y:5800},
  '1.05':{x:24000,y:8050},
  '1.06':{x:23950,y:9900,narrow:true},
  '1.07':{x:26670,y:10150,narrow:true},
  '1.08':{x:17800,y:5300},
  '1.09':{x:17800,y:9200},
  '1.10':{x:14200,y:9400},
  '1.11':{x:13800,y:4680},
  '1.12':{x:8700,y:6400},
  '1.14':{x:12100,y:6500,narrow:true},
};
export function roomLabelPos(room:PlanRoom,level:ExportLevel):{x:number;y:number;narrow:boolean} {
  const pos=ROOM_LABEL_POS[room.number];
  if(!pos)return {x:room.standingPointMm.x,y:room.standingPointMm.y,narrow:false};
  const anchor=level>=4&&pos.furnished?pos.furnished:pos;
  return {x:anchor.x,y:anchor.y,narrow:pos.narrow??false};
}
