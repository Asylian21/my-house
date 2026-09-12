import { Fragment, type ReactNode, type SVGProps } from 'react';
import { PLAN_ROOMS, numberSk, type PlanItem, type PlanMesh } from '@/lib/plan-documentation';
import { INTERIOR_DOORS, type RectMm } from '@/lib/twin-interior';
import { DEFAULT_LIVING_LAYOUT_ID, LIVING_LAYOUTS, type LivingLayoutId } from '@/lib/twin-living-layouts';
import { AXIS_OFFSET, AXIS_RADIUS, CODED_OPENINGS, CUT_PLANE_MM, DOOR_CHAINS, DOOR_TEXTS, EXPORT_LEVELS, EXPORT_REVISION, FACADES, FOOTPRINT as F, GRID_X, GRID_Y, INTERIOR_WALL_MESHES, ITEM_CODE_LABEL, MATERIAL_LEGEND, OPENING_BY_DOOR, PLAN_EXTENT, POOL, ROOM_KIND_LABEL, SECTION_CHAINS, SHELL_WALL_MESHES, SITE_BOUNDARY, SITE_LABELS, STRUCTURAL_EXTRAS, TERRACES, TERRACE_AREA_M2, clearHeightLabel, codedItems, drawnItems, facadeChains, finishCeiling, finishFloor, finishWalls, fixedSk, innerDims, roomAxes, roomKind, roomLabelPos, roomRectsByArea, shellWallClass, wallClass, type ChainSpec, type CodedItem, type ExportLevel, type ItemCode, type PlanRoom, type RoomKind, type WallClass } from '@/lib/plan-export';
import { Door } from './plan-svg';

/** Paper: A1 landscape in millimetres, plan at 1:50 (prints 1:100 on A3). */
export const SHEET={w:841,h:594,m:8};
export const SCALE=50;
export const PX_PER_MM=7.2;
const S=SCALE;
const T=(paperMm:number)=>paperMm*S;
const FONT='"Helvetica Neue", Helvetica, Arial, sans-serif';
const PLAN_W=(PLAN_EXTENT.x1-PLAN_EXTENT.x0)/S,PLAN_H=(PLAN_EXTENT.y1-PLAN_EXTENT.y0)/S;
const PLAN_BOX={x:SHEET.m,y:SHEET.m,w:PLAN_W,h:PLAN_H};
const STRIP={x:SHEET.m,y:PLAN_BOX.y+PLAN_H+3,w:PLAN_W,h:SHEET.h-SHEET.m-(PLAN_BOX.y+PLAN_H+3)};
const PANEL={x:PLAN_BOX.x+PLAN_W+6,y:SHEET.m,w:SHEET.w-SHEET.m-(PLAN_BOX.x+PLAN_W+6),h:SHEET.h-2*SHEET.m};
const TITLE={x:PLAN_BOX.x+PLAN_W+6,w:SHEET.w-SHEET.m-(PLAN_BOX.x+PLAN_W+6),h:82,y:SHEET.h-SHEET.m-82};
const TABLES={x:PANEL.x,y:PANEL.y,w:PANEL.w,h:TITLE.y-PANEL.y-16};

interface Palette {
  ink:string;muted:string;rule:string;dim:string;roomNo:string;boundary:string;glass:string;hatch:string;board:string;insulation:string;
  room:Record<RoomKind,string>;water:string;deck:string;pill:Record<'O'|'D'|ItemCode,string>;itemStroke:string;accent:string;tableStripe:string;
}
/** Colour sheet: black construction, red dimensions and room numbers, magenta parcel boundary, blue glazing (D1.1.002 convention) plus a faint room wash. */
const COLOR:Palette={ink:'#000',muted:'#555',rule:'#b8b8b8',dim:'#e30613',roomNo:'#e30613',boundary:'#c2129b',glass:'#1d4ed8',hatch:'#000',board:'#e4e4e4',insulation:'#eef1f3',
  room:{living:'#fcf7ee',wet:'#eef5fb',tech:'#f4f0f7',garage:'#f2f3f4',circulation:'#f1f7ef'},water:'#cfe6f5',deck:'#8b7d68',
  pill:{O:'#1d4ed8',D:'#6d28d9',N:'#8a5a19',Z:'#0e7490',L:'#a16207',F:'#4b5563'},itemStroke:'#6b6b6b',accent:'#e30613',tableStripe:'#f5f5f5'};
const MONO:Palette={ink:'#000',muted:'#444',rule:'#999',dim:'#000',roomNo:'#000',boundary:'#000',glass:'#000',hatch:'#000',board:'#e4e4e4',insulation:'#f2f2f2',
  room:{living:'#fff',wet:'#fff',tech:'#fff',garage:'#fff',circulation:'#fff'},water:'#fff',deck:'#777',
  pill:{O:'#000',D:'#000',N:'#000',Z:'#000',L:'#000',F:'#000'},itemStroke:'#555',accent:'#000',tableStripe:'#f0f0f0'};

const textWidth=(text:string,fontSize:number)=>text.length*fontSize*.56;
const halo={stroke:'#fff',paintOrder:'stroke' as const,strokeLinejoin:'round' as const};
const mm=(n:number)=>numberSk(Math.round(n));
const roomTitle=(room:PlanRoom)=>room.name.replace(' · ulica','').replace(' · dvor','').replace(' do dvora','').replace('Spoločná ','').replace(' a práčovňa',' + práčovňa').toUpperCase();

// ------------------------------------------------------------ plan pieces
function Defs({pal}:{pal:Palette}) {
  const hatch=(id:string,period:number,width:number)=><pattern key={id} id={id} width={T(period)} height={T(period)} patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1={0} y1={0} x2={0} y2={T(period)} stroke={pal.hatch} strokeWidth={T(width)}/></pattern>;
  return <defs>
    {hatch('xs-h-exterior',1.5,.16)}{hatch('xs-h-bearing',.9,.14)}{hatch('xs-h-partition',2.4,.1)}
    {/* Contact insulation: fine hatch in the opposite direction on a light ground, distinct from every masonry hatch. */}
    <pattern id="xs-h-insulation" width={T(1)} height={T(1)} patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><rect width={T(1)} height={T(1)} fill={pal.insulation}/><line x1={0} y1={0} x2={0} y2={T(1)} stroke={pal.hatch} strokeWidth={T(.08)}/></pattern>
    <pattern id="xs-deck" width={T(3)} height={T(3)} patternUnits="userSpaceOnUse"><line x1={0} y1={0} x2={T(3)} y2={0} stroke={pal.deck} strokeWidth={T(.07)}/></pattern>
    <clipPath id="xs-plan-clip"><rect x={PLAN_EXTENT.x0} y={-PLAN_EXTENT.y1} width={PLAN_EXTENT.x1-PLAN_EXTENT.x0} height={PLAN_EXTENT.y1-PLAN_EXTENT.y0}/></clipPath>
  </defs>;
}
function Rect({r,...props}:{r:RectMm}&Omit<SVGProps<SVGRectElement>,'r'>) { return <rect x={r.x0} y={-r.y1} width={r.x1-r.x0} height={r.y1-r.y0} {...props}/>; }
function Site({pal,color}:{pal:Palette;color:boolean}) {
  const fs=T(2);
  return <g>
    <polygon points={SITE_BOUNDARY.map(p=>`${p.x},${-p.y}`).join(' ')} fill="none" stroke={pal.boundary} strokeWidth={T(.35)} strokeDasharray={color?undefined:`${T(5)} ${T(1)} ${T(.6)} ${T(1)}`}/>
    {SITE_LABELS.map(l=><text key={l.text+l.x} x={l.x} y={-l.y+fs*.36} fontSize={fs} fill={pal.boundary} textAnchor="middle" letterSpacing={T(.15)} transform={`rotate(${-l.angle} ${l.x} ${-l.y})`}>{l.text}</text>)}
    <text x={9500} y={-20800} fontSize={T(2.6)} letterSpacing={T(.5)} fill={pal.muted} textAnchor="middle">ZÁHRADA</text>
  </g>;
}
function Outdoor({pal}:{pal:Palette}) {
  const fs=T(2.2);
  const deck=(key:string,r:RectMm)=><Fragment key={key}><Rect r={r} fill="#fff"/><Rect r={r} fill="url(#xs-deck)"/><Rect r={r} fill="none" stroke={pal.muted} strokeWidth={T(.12)}/></Fragment>;
  const label=(x:number,y:number,vertical:boolean|undefined,lines:string[])=><g key={`${x}-${y}`} fill={pal.muted} textAnchor="middle" fontSize={fs} letterSpacing={T(.3)} transform={vertical?`rotate(-90 ${x} ${-y})`:undefined} {...halo} strokeWidth={fs*.35}>
    {lines.map((l,i)=><text key={i} x={x} y={-y+(i-(lines.length-1)/2)*fs*1.3+fs*.36}>{l}</text>)}
  </g>;
  const pw=POOL.water,pc=POOL.coping,ps=POOL.shaft;
  return <g>
    {TERRACES.map(t=><g key={t.id}>{t.rects.map((r,i)=>deck(`${t.id}-${i}`,r))}{label(t.label.x,t.label.y,t.vertical,[t.title,t.area])}</g>)}
    {POOL.deck.map((r,i)=>deck(`pool-deck-${i}`,r))}
    <Rect r={pc} fill="none" stroke={pal.muted} strokeWidth={T(.16)}/>
    <Rect r={pw} fill={pal.water} stroke={pal.muted} strokeWidth={T(.12)}/>
    <Rect r={ps} fill="#fff" stroke={pal.muted} strokeWidth={T(.12)} strokeDasharray={`${T(1.2)} ${T(.6)}`}/>
    <text x={(ps.x0+ps.x1)/2} y={-(ps.y0+ps.y1)/2+fs*.3} fontSize={T(1.6)} fill={pal.muted} textAnchor="middle" letterSpacing={T(.2)}>TECHNOLOGICKÁ ŠACHTA</text>
    {label((pw.x0+pw.x1)/2,(pw.y0+pw.y1)/2,false,[POOL.title,POOL.note])}
  </g>;
}
function Rooms({pal}:{pal:Palette}) {
  return <g>{PLAN_ROOMS.map(room=>room.rectsMm.map((r,i)=><Rect key={`${room.id}-${i}`} r={r} fill={pal.room[roomKind(room)]}/>))}</g>;
}
/** Section through the walls: outline, white core, material hatch. Drawing the outlines first and the cores over them hides the seams between the modelled pieces. */
function Walls({pal}:{pal:Palette}) {
  const solids:{key:string;points:string;cls:WallClass}[]=[
    ...SHELL_WALL_MESHES.filter(m=>m.z0<=0).map(m=>({key:m.id,points:m.polygon,cls:shellWallClass(m)})),
    ...INTERIOR_WALL_MESHES.map(({mesh,kind})=>({key:mesh.id,points:mesh.polygon,cls:wallClass(kind,Math.min(mesh.rect.x1-mesh.rect.x0,mesh.rect.y1-mesh.rect.y0))})),
  ];
  const outline=(cls:WallClass)=>cls==='exterior'||cls==='insulation'?T(.7):cls==='bearing'?T(.5):T(.36);
  const fill=(cls:WallClass)=>cls==='board'?pal.board:`url(#xs-h-${cls})`;
  const masonry=solids.filter(s=>s.cls!=='insulation'),insulation=solids.filter(s=>s.cls==='insulation');
  // The insulation layer is outlined thinly and filled last on an opaque ground, so only its boundary with the masonry and the outer face remain visible.
  return <g strokeLinejoin="miter">
    <g fill="none" stroke={pal.ink}>{solids.map(s=><polygon key={s.key} points={s.points} strokeWidth={outline(s.cls)}/>)}</g>
    <g fill="#fff">{solids.map(s=><polygon key={s.key} points={s.points}/>)}</g>
    <g>{masonry.map(s=><polygon key={s.key} points={s.points} fill={fill(s.cls)}/>)}</g>
    <g fill="none" stroke={pal.ink} strokeWidth={T(.2)}>{insulation.map(s=><polygon key={s.key} points={s.points}/>)}</g>
    <g>{insulation.map(s=><polygon key={s.key} points={s.points} fill={fill(s.cls)}/>)}</g>
  </g>;
}

function Pill({x,y,text,color,fontSize=T(1.8),bold=true}:{x:number;y:number;text:string;color:string;fontSize?:number;bold?:boolean}) {
  const w=textWidth(text,fontSize)+fontSize*.9,h=fontSize*1.45;
  return <g transform={`translate(${x} ${y})`}><rect x={-w/2} y={-h/2} width={w} height={h} rx={h/2} fill="#fff" stroke={color} strokeWidth={T(.2)}/><text y={fontSize*.36} fontSize={fontSize} textAnchor="middle" fontWeight={bold?700:500} fill={color}>{text}</text></g>;
}

const GLASS=/dvojsklo|zasklenie|sklo/i,FRAME=/rám |zárubňa|stĺpik|priečnik|koľajnica|prah/i,LEAF=/dverné krídlo|transportné krídlo/;
function swingArc(hinge:[number,number],closedEnd:[number,number],openEnd:[number,number]) {
  const cross=(closedEnd[0]-hinge[0])*(openEnd[1]-hinge[1])-(closedEnd[1]-hinge[1])*(openEnd[0]-hinge[0]);
  const r=Math.hypot(closedEnd[0]-hinge[0],closedEnd[1]-hinge[1]);
  return `M${closedEnd[0]},${closedEnd[1]} A${r},${r} 0 0 ${cross>0?1:0} ${openEnd[0]},${openEnd[1]}`;
}
function ExteriorOpenings({pal}:{pal:Palette}) {
  const nodes:ReactNode[]=[];
  for(const {def,segments} of FACADES)for(const seg of segments){
    if(seg.kind!=='opening'||!seg.item)continue;
    const item=seg.item,opening=item.opening!;
    const across=seg.meshes.length?[Math.min(...seg.meshes.map(m=>def.axis==='x'?m.rect.y0:m.rect.x0)),Math.max(...seg.meshes.map(m=>def.axis==='x'?m.rect.y1:m.rect.x1))]:[Math.min(def.outer,def.inner),Math.max(def.outer,def.inner)];
    const gap:RectMm=def.axis==='x'?{x0:seg.a,x1:seg.b,y0:across[0],y1:across[1]}:{y0:seg.a,y1:seg.b,x0:across[0],x1:across[1]};
    const code=CODED_OPENINGS.find(o=>o.item.id===item.id);
    const kind=code?.kind;
    const glass=item.meshes.filter(m=>GLASS.test(m.name)),frames=item.meshes.filter(m=>FRAME.test(m.name)&&!GLASS.test(m.name));
    const inward=-def.outward;
    const jambs=def.axis==='x'?`M${seg.a},${-gap.y0}V${-gap.y1}M${seg.b},${-gap.y0}V${-gap.y1}`:`M${gap.x0},${-seg.a}H${gap.x1}M${gap.x0},${-seg.b}H${gap.x1}`;
    const parts:ReactNode[]=[<Rect key="gap" r={gap} fill="#fff"/>,<path key="jambs" d={jambs} stroke={pal.ink} strokeWidth={T(.3)} fill="none"/>];
    parts.push(...frames.map(m=><polygon key={m.id} points={m.polygon} fill="#fff" stroke={pal.ink} strokeWidth={T(.1)}/>));
    parts.push(...glass.map(m=><polygon key={m.id} points={m.polygon} fill={pal.glass} stroke={pal.glass} strokeWidth={T(.12)}/>));
    if(kind==='window'&&opening.sill>=1500)parts.push(<Rect key="high" r={gap} fill="none" stroke={pal.ink} strokeWidth={T(.14)} strokeDasharray={`${T(1)} ${T(.6)}`}/>);
    if(kind==='gate'){
      const y=-def.outer;
      parts.push(<line key="gate" x1={seg.a} x2={seg.b} y1={y} y2={y} stroke={pal.ink} strokeWidth={T(.5)}/>);
      parts.push(<line key="gate2" x1={seg.a} x2={seg.b} y1={-(def.inner+inward*300)} y2={-(def.inner+inward*300)} stroke={pal.ink} strokeWidth={T(.16)} strokeDasharray={`${T(1.4)} ${T(.7)}`}/>);
    }
    if(kind==='door'){
      const leaves=item.meshes.filter(m=>LEAF.test(m.name));
      const sidelight=item.meshes.find(m=>/bočný svetlík/.test(m.name));
      const swingOut=/EAST-03/.test(item.id);
      const face=swingOut?def.outer:def.inner,dir=swingOut?def.outward:inward;
      leaves.forEach((leaf,index)=>{
        const [la,lb]=def.axis==='x'?[leaf.rect.x0,leaf.rect.x1]:[leaf.rect.y0,leaf.rect.y1];const L=lb-la;
        let hingeAtLow:boolean;
        if(leaves.length>1)hingeAtLow=index===0;
        else if(sidelight){const s=def.axis==='x'?(sidelight.rect.x0+sidelight.rect.x1)/2:(sidelight.rect.y0+sidelight.rect.y1)/2;hingeAtLow=s>lb;}
        else hingeAtLow=true;
        const h=hingeAtLow?la:lb,free=hingeAtLow?lb:la;
        const P=(alongV:number,acrossV:number):[number,number]=>def.axis==='x'?[alongV,-acrossV]:[acrossV,-alongV];
        const hinge=P(h,face),closed=P(free,face),open=P(h,face+dir*L);
        parts.push(<path key={`leaf-${index}`} d={`M${hinge[0]},${hinge[1]}L${open[0]},${open[1]}`} stroke={pal.ink} strokeWidth={T(.35)} fill="none"/>);
        parts.push(<path key={`arc-${index}`} d={swingArc(hinge,closed,open)} stroke={pal.ink} strokeWidth={T(.12)} fill="none"/>);
      });
    }
    if(kind==='sliding'){
      const mid=(seg.a+seg.b)/2;
      const arrow=def.axis==='x'?`M${mid-350},${-(def.inner+inward*220)}h700 m-160,-110 l160,110 -160,110`:`M${def.inner+inward*220},${-(mid-350)}v-700 m-110,160 l110,-160 110,160`;
      parts.push(<path key="slide" d={arrow} stroke={pal.ink} strokeWidth={T(.14)} fill="none"/>);
    }
    nodes.push(<g key={`${def.id}-${seg.a}`}>{parts}</g>);
  }
  return <g>{nodes}</g>;
}
/** O/D codes of the exterior openings, just outside the facade between the wall and the first dimension row (drawn over the chains). */
function OpeningCodes({pal}:{pal:Palette}) {
  const nodes:ReactNode[]=[];
  for(const {def,segments} of FACADES){
    if(!def.codes)continue;
    for(const seg of segments){
      const code=seg.item&&CODED_OPENINGS.find(o=>o.item.id===seg.item!.id);
      if(!code)continue;
      const at=def.outer+def.outward*400,mid=(seg.a+seg.b)/2;
      const [x,y]=def.axis==='x'?[mid,-at]:[at,-mid];
      nodes.push(<Pill key={code.code} x={x} y={y} text={code.code} color={pal.pill[code.code.startsWith('O')?'O':'D']} fontSize={T(1.7)}/>);
    }
  }
  return <g>{nodes}</g>;
}
function InteriorDoors() {
  return <g className="xs-doors">{INTERIOR_DOORS.map(door=><Door key={door.id} door={door}/>)}</g>;
}
/** Interior door stamp in the wall gap: D-code on one side of the wall axis, "šírka / výška" on the other, both along the wall. */
function DoorCodes({pal}:{pal:Palette}) {
  const fp=T(1.5),ft=T(1.45);
  return <g>{DOOR_TEXTS.map(t=>{
    const code=OPENING_BY_DOOR.get(t.door.id);if(!code)return null;
    const cx=t.x,cy=-t.y;
    return <g key={t.door.id} transform={t.axis==='y'?`rotate(-90 ${cx} ${cy})`:undefined}>
      <Pill x={cx} y={cy-fp*.85} text={code.code} color={pal.pill.D} fontSize={fp}/>
      <text x={cx} y={cy+ft*1.15} fontSize={ft} fill={pal.dim} textAnchor="middle" fontWeight={500} {...halo} strokeWidth={ft*.3}>{t.text}</text>
    </g>;
  })}</g>;
}

/** Stagger rows so that neighbouring labels never overlap: 0 = on the line, 1/2 = alternate outer rows. */
function staggerRows(points:number[],labels:(string|undefined)[],fontSize:number):number[] {
  const rows:number[]=[];
  for(let i=1;i<points.length;i++){
    const len=points[i]-points[i-1],text=labels[i-1];
    const fits=!text||textWidth(text,fontSize)<=len-fontSize*.25;
    rows.push(fits?0:rows[rows.length-1]===1?2:1);
  }
  return rows;
}
function Chain({chain,color,fontSize=T(2.4)}:{chain:ChainSpec;color:string;fontSize?:number}) {
  const {axis,at,points,textSide,ext,sub}=chain;
  const p0=points[0],pn=points[points.length-1],tick=T(.8),gap=fontSize*.35,lw=chain.role==='section'?T(.12):T(.16);
  const line=axis==='x'?`M${p0},${-at}H${pn}`:`M${at},${-p0}V${-pn}`;
  const ticks=points.map(p=>axis==='x'?`M${p-tick},${-at+tick}L${p+tick},${-at-tick}`:`M${at-tick},${-p+tick}L${at+tick},${-p-tick}`).join('');
  const extension=ext===undefined?'':points.map(p=>{const end=at+Math.sign(at-ext)*T(1.2);return axis==='x'?`M${p},${-ext}L${p},${-end}`:`M${ext},${-p}L${end},${-p}`;}).join('');
  const main=points.slice(1).map((p,i)=>p-points[i]<1?undefined:mm(p-points[i]));
  const rows=staggerRows(points,main,fontSize),subFs=fontSize*.86,subRows=sub?staggerRows(points,sub,subFs):[];
  const label=(i:number,text:string,side:1|-1,row:number,fs:number)=>{
    const mid=(points[i]+points[i+1])/2,off=gap+row*fs*1.15;
    if(axis==='x'){
      const y=side===-1?-at-off:-at+off+fs*.72;
      return <text key={`${side}-${i}`} x={mid} y={y} fontSize={fs} textAnchor="middle" fill={color} {...halo} strokeWidth={fs*.3}>{text}</text>;
    }
    const x=side===-1?at-off:at+off+fs*.72;
    return <text key={`${side}-${i}`} x={x} y={-mid} fontSize={fs} textAnchor="middle" fill={color} transform={`rotate(-90 ${x} ${-mid})`} {...halo} strokeWidth={fs*.3}>{text}</text>;
  };
  return <g fill="none" stroke={color} strokeWidth={lw}>
    {extension&&<path d={extension} strokeWidth={T(.1)}/>}
    <path d={line}/><path d={ticks} strokeWidth={T(.22)}/>
    <g stroke="none" fontWeight={500}>
      {main.map((text,i)=>text===undefined?null:label(i,text,textSide,rows[i],fontSize))}
      {sub?.map((text,i)=>text===undefined?null:label(i,text,-textSide as 1|-1,subRows[i],subFs))}
    </g>
  </g>;
}
function InnerDims({pal}:{pal:Palette}) {
  const fs=T(2.1);
  return <g fill={pal.dim} fontSize={fs} textAnchor="middle" fontWeight={500} {...halo} strokeWidth={fs*.3}>
    {PLAN_ROOMS.flatMap(room=>innerDims(room).map((d,i)=><text key={`${room.id}-${i}`} x={d.x} y={-d.y+fs*.36} transform={d.axis==='y'?`rotate(-90 ${d.x} ${-d.y})`:undefined}>{d.text}</text>))}
  </g>;
}
function Grid({pal}:{pal:Palette}) {
  const fs=T(2.8),dash=`${T(3)} ${T(.8)} ${T(.3)} ${T(.8)}`;
  const y0=-(F.y0-AXIS_OFFSET),x0=F.x0-AXIS_OFFSET,x1=F.x1+AXIS_OFFSET;
  const topFor=(at:number)=>at<F.wingX-1?-(F.gardenY+AXIS_OFFSET):-(F.y1+AXIS_OFFSET);
  const leftFor=(at:number)=>at>F.gardenY+1?F.wingX-AXIS_OFFSET:x0;
  const bubble=(key:string,x:number,y:number,label:string)=><g key={key}><circle cx={x} cy={y} r={AXIS_RADIUS} fill="#fff" stroke={pal.ink} strokeWidth={T(.25)}/><text x={x} y={y+fs*.36} fontSize={fs} fontWeight={700} textAnchor="middle" fill={pal.ink}>{label}</text></g>;
  return <g>
    <g stroke={pal.muted} strokeWidth={T(.12)} strokeDasharray={dash} fill="none">
      {GRID_X.map(a=><path key={a.label} d={`M${a.at},${y0-AXIS_RADIUS}V${topFor(a.at)+AXIS_RADIUS}`}/>)}
      {GRID_Y.map(a=><path key={a.label} d={`M${leftFor(a.at)+AXIS_RADIUS},${-a.at}H${x1-AXIS_RADIUS}`}/>)}
    </g>
    {GRID_X.flatMap(a=>[bubble(`${a.label}-b`,a.at,y0,a.label),bubble(`${a.label}-t`,a.at,topFor(a.at),a.label)])}
    {GRID_Y.flatMap(a=>[bubble(`${a.label}-l`,leftFor(a.at),-a.at,a.label),bubble(`${a.label}-r`,x1,-a.at,a.label)])}
  </g>;
}
interface Box { x0:number; y0:number; x1:number; y1:number }
interface LabelLine { text:string; size:number; weight:number; fill:string }
/** Room stamp: red number, purpose, floor area, at L3+ the clear height (SVG coordinates, shared with the pill collision avoidance). */
function roomLabel(room:PlanRoom,level:ExportLevel,pal:Palette):{x:number;lines:LabelLine[];tops:number[];box:Box} {
  const {x,y,narrow}=roomLabelPos(room,level);
  const number=T(narrow?2.7:3.4),name=T(narrow?1.7:2),small=T(1.8);
  const lines:LabelLine[]=[{text:room.number,size:number,weight:700,fill:pal.roomNo},{text:roomTitle(room),size:name,weight:500,fill:pal.ink},{text:`${fixedSk(room.area,2)} m²`,size:name,weight:400,fill:pal.ink}];
  if(level>=3)lines.push({text:`S.V. ${clearHeightLabel(room)}`,size:small,weight:400,fill:pal.ink});
  if(level>=3&&room.number==='1.01')lines.push({text:'±0,000',size:small,weight:500,fill:pal.ink});
  const total=lines.reduce((s,l)=>s+l.size*1.22,0),top=-y-total/2;
  const tops:number[]=[];
  for(let i=0,cursor=top;i<lines.length;i++){cursor+=lines[i].size*1.22;tops.push(cursor-lines[i].size*.22);}
  const half=Math.max(...lines.map(l=>textWidth(l.text,l.size)))/2;
  return {x,lines,tops,box:{x0:x-half,x1:x+half,y0:top,y1:top+total}};
}
function RoomLabels({pal,level}:{pal:Palette;level:ExportLevel}) {
  return <g textAnchor="middle" {...halo}>{PLAN_ROOMS.map(room=>{
    const {x,lines,tops}=roomLabel(room,level,pal);
    return <g key={room.id}>{lines.map((l,i)=><text key={i} x={x} y={tops[i]} fontSize={l.size} fontWeight={l.weight} fill={l.fill} letterSpacing={i===1?l.size*.06:0} strokeWidth={l.size*.3}>{l.text}</text>)}</g>;
  })}</g>;
}
function Items({pal,level,livingLayout}:{pal:Palette;level:ExportLevel;livingLayout:LivingLayoutId}) {
  const items=drawnItems(level,livingLayout);
  const parts=items.flatMap(item=>item.meshes.map(mesh=>({item,mesh}))).filter(({mesh})=>Math.min(mesh.rect.x1-mesh.rect.x0,mesh.rect.y1-mesh.rect.y0)>=35).sort((a,b)=>a.mesh.z0-b.mesh.z0);
  const polygon=(_item:PlanItem,mesh:PlanMesh)=>mesh.z0>=CUT_PLANE_MM
    ?<polygon key={mesh.id} points={mesh.polygon} fill="none" stroke={pal.itemStroke} strokeWidth={T(.1)} strokeDasharray={`${T(.9)} ${T(.5)}`}/>
    :<polygon key={mesh.id} points={mesh.polygon} fill="#fff" fillOpacity={.55} stroke={pal.itemStroke} strokeWidth={T(.1)} strokeLinejoin="round"/>;
  return <g>
    {STRUCTURAL_EXTRAS.flatMap(item=>item.meshes.map(mesh=><polygon key={mesh.id} points={mesh.polygon} fill="none" stroke={pal.ink} strokeWidth={T(.16)}/>))}
    {parts.map(({item,mesh})=>polygon(item,mesh))}
  </g>;
}
function ItemLabels({pal,level,livingLayout}:{pal:Palette;level:ExportLevel;livingLayout:LivingLayoutId}) {
  const fs=T(1.55),h=fs*1.45;
  const placed:Box[]=PLAN_ROOMS.map(room=>roomLabel(room,level,pal).box);
  const collides=(b:Box)=>placed.some(p=>b.x0<p.x1&&b.x1>p.x0&&b.y0<p.y1&&b.y1>p.y0);
  const labels=codedItems(level,livingLayout).filter(c=>c.labeled).sort((a,b)=>(b.width*b.depth)-(a.width*a.depth)).map((c:CodedItem)=>{
    const w=textWidth(c.code,fs)+fs*.9,cx=(c.item.rect.x0+c.item.rect.x1)/2,cy=-(c.item.rect.y0+c.item.rect.y1)/2;
    const tries=[[0,0],[0,-h*1.15],[0,h*1.15],[w*1.05,0],[-w*1.05,0],[w*1.05,-h*1.15],[-w*1.05,h*1.15],[0,-h*2.3],[0,h*2.3]];
    let x=cx,y=cy;
    for(const [dx,dy] of tries){const b={x0:cx+dx-w/2,x1:cx+dx+w/2,y0:cy+dy-h/2,y1:cy+dy+h/2};if(!collides(b)){placed.push(b);x=cx+dx;y=cy+dy;break;}}
    return <Pill key={c.code} x={x} y={y} text={c.code} color={pal.pill[c.letter]} fontSize={fs}/>;
  });
  return <g>{labels}</g>;
}

// ------------------------------------------------------------ paper pieces
interface Column { title:string; width:number; align?:'l'|'r' }
function truncate(text:string,width:number,fontSize:number){const max=Math.floor(width/(fontSize*.5));return text.length<=max?text:`${text.slice(0,Math.max(1,max-1)).trimEnd()}…`;}
function Table({x,y,width,title,columns,rows,fontSize,pitch,pal}:{x:number;y:number;width:number;title:string;columns:Column[];rows:string[][];fontSize:number;pitch:number;pal:Palette}) {
  const sum=columns.reduce((s,c)=>s+c.width,0),scale=width/sum;
  const xs:number[]=[];let cursor=x;for(const c of columns){xs.push(cursor);cursor+=c.width*scale;}
  const headH=pitch*1.35,titleH=fontSize*2.6,top=y+titleH;
  const cell=(c:Column,i:number,text:string,yy:number,bold=false)=><text key={i} x={c.align==='r'?xs[i]+c.width*scale-.7:xs[i]+.7} y={yy} fontSize={fontSize} textAnchor={c.align==='r'?'end':'start'} fontWeight={bold?700:400} fill={pal.ink}>{truncate(text,c.width*scale-1.4,fontSize)}</text>;
  const bodyH=headH+pitch*rows.length;
  return <g fontFamily={FONT}>
    <text x={x} y={y+fontSize*1.6} fontSize={fontSize*1.6} fontWeight={700} fill={pal.ink} letterSpacing={.2}>{title}</text>
    {rows.map((_,ri)=>ri%2===1&&<rect key={`s${ri}`} x={x} y={top+headH+pitch*ri} width={width} height={pitch} fill={pal.tableStripe}/>)}
    <rect x={x} y={top} width={width} height={bodyH} fill="none" stroke={pal.ink} strokeWidth={.3}/>
    <line x1={x} x2={x+width} y1={top+headH} y2={top+headH} stroke={pal.ink} strokeWidth={.3}/>
    {xs.slice(1).map((vx,i)=><line key={i} x1={vx} x2={vx} y1={top} y2={top+bodyH} stroke={pal.rule} strokeWidth={.15}/>)}
    {columns.map((c,i)=>cell(c,i,c.title,top+headH-headH*.35,true))}
    {rows.map((row,ri)=>{const yy=top+headH+pitch*(ri+1);return <g key={ri}>{row.map((v,i)=>cell(columns[i],i,v,yy-pitch*.3))}</g>;})}
  </g>;
}
const tableHeight=(rows:number,fontSize:number,pitch:number)=>fontSize*2.6+pitch*1.35+pitch*rows+3;
function wrap(text:string,width:number,fontSize:number):string[] {
  const max=Math.max(8,Math.floor(width/(fontSize*.5)));const words=text.split(' ');const lines:string[]=[];let line='';
  for(const w of words){if((line+' '+w).trim().length>max&&line){lines.push(line);line=w;}else line=(line+' '+w).trim();}
  if(line)lines.push(line);return lines;
}
function Paragraph({x,y,width,text,fontSize,pal,bold,fill}:{x:number;y:number;width:number;text:string;fontSize:number;pal:Palette;bold?:boolean;fill?:string}) {
  const lines=wrap(text,width,fontSize);
  return <text x={x} y={y} fontSize={fontSize} fill={fill??pal.ink} fontWeight={bold?700:400}>{lines.map((l,i)=><tspan key={i} x={x} dy={i===0?fontSize:fontSize*1.3}>{l}</tspan>)}</text>;
}
const paragraphHeight=(text:string,width:number,fontSize:number)=>wrap(text,width,fontSize).length*fontSize*1.3+fontSize*.4;

/** One legend column: stacks headings, swatch rows and paragraphs. */
function legendColumn(x:number,y:number,width:number,fs:number,pal:Palette) {
  const nodes:ReactNode[]=[];let cy=y;
  const heading=(text:string)=>{nodes.push(<text key={`h${cy}`} x={x} y={cy+fs*1.3} fontSize={fs*1.25} fontWeight={700} fill={pal.ink} letterSpacing={.3}>{text}</text>);cy+=fs*2.2;};
  const para=(text:string)=>{nodes.push(<Paragraph key={`p${cy}`} x={x} y={cy} width={width} text={text} fontSize={fs} pal={pal}/>);cy+=paragraphHeight(text,width,fs);};
  const row=(key:string,swatch:(sx:number,sy:number,w:number,h:number)=>ReactNode,text:string)=>{
    const h=fs*1.25,w=fs*5,lines=wrap(text,width-w-fs,fs);
    nodes.push(<g key={key}>{swatch(x,cy+fs*.1,w,h)}<text x={x+w+fs*.8} y={cy+fs*1.05} fontSize={fs} fill={pal.ink}>{lines.map((l,i)=><tspan key={i} x={x+w+fs*.8} dy={i===0?0:fs*1.25}>{l}</tspan>)}</text></g>);
    cy+=Math.max(fs*1.6,lines.length*fs*1.25+fs*.4);
  };
  const gap=()=>{cy+=fs*.7;};
  return {nodes,heading,para,row,gap,height:()=>cy-y};
}
function PaperPill({x,y,text,color,fs}:{x:number;y:number;text:string;color:string;fs:number}) {
  const w=text.length*fs*.6+fs*.9,h=fs*1.4;
  return <g><rect x={x-w/2} y={y-h/2} width={w} height={h} rx={h/2} fill="#fff" stroke={color} strokeWidth={.25}/><text x={x} y={y+fs*.36} fontSize={fs*.95} textAnchor="middle" fontWeight={700} fill={color}>{text}</text></g>;
}
function chainSwatch(color:string,ticks:number[]) {
  return function ChainSwatch(sx:number,sy:number,w:number,h:number) {
    return <g stroke={color} strokeWidth={.25}><line x1={sx} x2={sx+w} y1={sy+h/2} y2={sy+h/2}/><path d={ticks.map(t=>`M${sx+w*t-.6},${sy+h/2+.6}l1.2,-1.2`).join('')}/></g>;
  };
}
function legendColumns(level:ExportLevel,pal:Palette,color:boolean,fs:number) {
  const pad=STRIP.h*.08,head=fs*2.6;
  const count=4,colW=(STRIP.w-pad*(count+1))/count;
  const cols=Array.from({length:count},(_,i)=>legendColumn(STRIP.x+pad+i*(colW+pad),STRIP.y+pad+head,colW,fs,pal));
  const [c1,c2,c3,c4]=cols;
  c1.heading('KÓTY A OSI');
  c1.row('c1',chainSwatch(pal.dim,[0,.35,1]),'Rady pri fasáde: 1. otvory – šírka nad čiarou, výška (parapet) pod čiarou · 2. líce priľahlých stien · 3. celkový rozmer');
  if(level>=3)c1.row('c2',chainSwatch(pal.dim,[0,.3,.36,.7,1]),'Reťazce cez miestnosti: svetlé šírky a hrúbky stien za sebou · červené čísla pri stenách = svetlé rozmery miestnosti');
  if(level>=3)c1.row('c3',chainSwatch(pal.dim,[0,.4,.6,1]),'Poloha dverí: odstupy stavebného otvoru od stien miestnosti, do ktorej sa krídlo otvára');
  c1.row('ax',(sx,sy,w,h)=><g><circle cx={sx+h/2} cy={sy+h/2} r={h/2} fill="#fff" stroke={pal.ink} strokeWidth={.25}/><text x={sx+h/2} y={sy+h*.72} fontSize={fs*.8} fontWeight={700} textAnchor="middle" fill={pal.ink}>A</text><circle cx={sx+w-h/2} cy={sy+h/2} r={h/2} fill="#fff" stroke={pal.ink} strokeWidth={.25}/><text x={sx+w-h/2} y={sy+h*.72} fontSize={fs*.8} fontWeight={700} textAnchor="middle" fill={pal.ink}>1</text></g>,'Modulové osi: písmená A–F po šírke (↔), čísla 1–6 po hĺbke (↕); „C–D / 1–2“ = pole medzi osami – jednoznačná poloha aj v čiernobielej tlači');
  c1.para('Všetky kóty v mm po líce murovaných konštrukcií (bez omietok a obkladov) podľa 3D modelu; kóty majú prednosť pred odmeriavaním z výkresu.');

  c2.heading('OTVORY');
  c2.row('o',(sx,sy,w,h)=><PaperPill x={sx+w/2} y={sy+h/2} text="O#" color={pal.pill.O} fs={fs}/>,'okno alebo pevné presklenie · rozmery v tabuľke otvorov');
  c2.row('d',(sx,sy,w,h)=><PaperPill x={sx+w/2} y={sy+h/2} text="D#" color={pal.pill.D} fs={fs}/>,'dvere, brána, posuvná stena · oblúk = otváranie krídla, šípka = posun');
  c2.row('glass',(sx,sy,w,h)=><g><rect x={sx} y={sy} width={w} height={h} fill="#fff" stroke={pal.ink} strokeWidth={.15}/><line x1={sx+1} x2={sx+w-1} y1={sy+h/2} y2={sy+h/2} stroke={pal.glass} strokeWidth={.7}/></g>,'zasklenie v otvore · čiarkovaný obrys = parapet nad 1 500 mm');
  if(level>=2)c2.row('dt',(sx,sy,w,h)=><text x={sx+w/2} y={sy+h*.78} fontSize={fs*.95} textAnchor="middle" fill={pal.dim} fontWeight={500}>900 / 2 100</text>,'vnútorné dvere: šírka / výška stavebného otvoru, písané na strane, kam sa krídlo neotvára');
  c2.para('Šírky a výšky sú stavebné otvory (bez rámov). Parapet a nadpražie od čistej podlahy ±0,000 = podlaha 1. NP.');

  c3.heading('MIESTNOSTI');
  c3.row('stamp',(sx,sy,w,h)=><g textAnchor="middle"><text x={sx+w/2} y={sy+h*.55} fontSize={fs*1.1} fontWeight={700} fill={pal.roomNo}>1.03</text><text x={sx+w/2} y={sy+h*1.35} fontSize={fs*.7} fill={pal.ink}>49,91 m²</text></g>,level>=3?'číslo · účel · plocha čistej podlahy · S.V. = svetlá výška':'číslo · účel · plocha čistej podlahy');
  if(color)for(const kind of ['living','wet','circulation','tech','garage'] as RoomKind[])c3.row(kind,(sx,sy,w,h)=><rect x={sx} y={sy} width={w} height={h} fill={pal.room[kind]} stroke={pal.rule} strokeWidth={.15}/>,ROOM_KIND_LABEL[kind]);
  c3.row('deck',(sx,sy,w,h)=><g><rect x={sx} y={sy} width={w} height={h} fill="#fff" stroke={pal.muted} strokeWidth={.15}/><path d={[0.25,0.5,0.75].map(t=>`M${sx},${sy+h*t}H${sx+w}`).join('')} stroke={pal.deck} strokeWidth={.12}/></g>,`drevená terasa 1.13 (${fixedSk(TERRACE_AREA_M2,2)} m²) · bazén a šachta = návrh stavebníka, nie je súčasťou D1`);

  if(level>=4){
    c4.heading(level>=5?'PRVKY INTERIÉRU':'PEVNÉ VYBAVENIE');
    for(const letter of ['N','Z','L','F'] as ItemCode[]){
      if(level<5&&letter!=='N'&&letter!=='Z')continue;
      c4.row(letter,(sx,sy,w,h)=><PaperPill x={sx+w/2} y={sy+h/2} text={`${letter}#`} color={pal.pill[letter]} fs={fs}/>,ITEM_CODE_LABEL[letter]);
    }
    c4.row('over',(sx,sy,w,h)=><rect x={sx} y={sy} width={w} height={h} fill="none" stroke={pal.itemStroke} strokeWidth={.2} strokeDasharray="1 .6"/>,'prvok nad rezovou rovinou 1 200 mm (horné skrinky, svietidlá, dymovod)');
    c4.para('Poloha prvku v súpise = odstup jeho juhozápadného rohu od západnej (Z) a južnej (J) steny miestnosti.');
    c4.gap();
  }
  c4.heading('POZNÁMKY');
  c4.para(`Výkres je exportom aktívneho 3D modelu variantu C (revízia ${EXPORT_REVISION}) v konvenciách D1.1.002. Obvodová stena 500 mm; líce podláh v modeli 499–504 mm od vonkajšieho líca. Nejde o geodetické zameranie: statiku, TZB, komín a požiarne riešenie potvrdí projektant.`);
  return cols;
}
function LegendStrip({level,pal,color}:{level:ExportLevel;pal:Palette;color:boolean}) {
  const pad=STRIP.h*.08;
  let fs=2.3;
  for(let pass=0;pass<4;pass++){
    const tallest=Math.max(...legendColumns(level,pal,color,fs).map(c=>c.height()));
    const available=STRIP.h-pad*2-fs*2.6;
    const next=Math.min(2.6,Math.max(1.5,fs*Math.min(1.4,available/tallest)));
    if(Math.abs(next-fs)<.02)break;
    fs=next;
  }
  const cols=legendColumns(level,pal,color,fs);
  return <g fontFamily={FONT}>
    <rect x={STRIP.x} y={STRIP.y} width={STRIP.w} height={STRIP.h} fill="#fff" stroke={pal.ink} strokeWidth={.35}/>
    <text x={STRIP.x+pad} y={STRIP.y+pad+4.2} fontSize={4.6} fontWeight={800} fill={pal.ink} letterSpacing={.8}>LEGENDA</text>
    <text x={STRIP.x+STRIP.w-pad} y={STRIP.y+pad+4.2} fontSize={2.6} fontWeight={600} fill={pal.muted} textAnchor="end">ÚROVEŇ L{level} · {EXPORT_LEVELS.find(l=>l.level===level)!.title.toUpperCase()} · {color?'FAREBNÁ VERZIA':'ČIERNOBIELA VERZIA'}</text>
    <line x1={STRIP.x+pad} x2={STRIP.x+STRIP.w-pad} y1={STRIP.y+pad+6.2} y2={STRIP.y+pad+6.2} stroke={pal.rule} strokeWidth={.3}/>
    {cols.map((c,i)=><Fragment key={i}>{c.nodes}</Fragment>)}
  </g>;
}

// ------------------------------------------------------------ right panel
interface Block { key:string; height:(fs:number,pitch:number,width:number)=>number; render:(x:number,y:number,width:number,fs:number,pitch:number)=>ReactNode }
const tableBlock=(title:string,columns:Column[],rows:string[][],pal:Palette):Block=>({key:title,height:(fs,pitch)=>tableHeight(rows.length,fs,pitch),render:(x,y,width,fs,pitch)=><Table key={title} x={x} y={y} width={width} title={title} columns={columns} rows={rows} fontSize={fs} pitch={pitch} pal={pal}/>});
function materialBlock(pal:Palette):Block {
  const swatchW=(fs:number)=>fs*8,rowH=(fs:number,width:number,text:string)=>Math.max(fs*3.4,wrap(text,width-swatchW(fs)-fs,fs).length*fs*1.3+fs*1.1);
  return {key:'materials',
    height:(fs,_pitch,width)=>fs*2.6+MATERIAL_LEGEND.reduce((s,e)=>s+rowH(fs,width,`${e.codes} · ${e.text}`),0)+2,
    render:(x,y,width,fs)=>{
      const nodes:ReactNode[]=[];let cy=y+fs*2.6;
      for(const e of MATERIAL_LEGEND){
        const text=`${e.codes} · ${e.text}`,h=rowH(fs,width,text),sw=swatchW(fs),sh=fs*2.4;
        nodes.push(<g key={e.cls}>
          <rect x={x} y={cy+fs*.2} width={sw} height={sh} fill={e.cls==='board'?pal.board:`url(#xs-l-${e.cls})`} stroke={pal.ink} strokeWidth={e.cls==='exterior'?.5:.3}/>
          <Paragraph x={x+sw+fs} y={cy} width={width-sw-fs} text={text} fontSize={fs} pal={pal}/>
        </g>);
        cy+=h;
      }
      return <g key="materials" fontFamily={FONT}><text x={x} y={y+fs*1.6} fontSize={fs*1.6} fontWeight={700} fill={pal.ink} letterSpacing={.2}>LEGENDA MATERIÁLOV</text>{nodes}</g>;
    }};
}
function panelBlocks(level:ExportLevel,pal:Palette,livingLayout:LivingLayoutId):Block[] {
  const blocks:Block[]=[];
  const totalArea=PLAN_ROOMS.reduce((s,r)=>s+r.area,0);
  const footprint=((F.x1-F.x0)*(F.gardenY-F.y0)+(F.x1-F.wingX)*(F.y1-F.gardenY))/1e6;
  const exterior=CODED_OPENINGS.filter(o=>o.facade);
  blocks.push(tableBlock('LEGENDA MIESTNOSTÍ 1. NP',
    [{title:'OZN.',width:7},{title:'ÚČEL MIESTNOSTI',width:30},{title:'PLOCHA m²',width:11,align:'r'},{title:'S.V. mm',width:12,align:'r'},{title:'PODLAHA',width:19},{title:'STENY',width:20},{title:'STROP',width:21},{title:'OSI',width:13}],
    [...PLAN_ROOMS.map(r=>[r.number,roomTitle(r),fixedSk(r.area,2),clearHeightLabel(r),finishFloor(r),finishWalls(r),finishCeiling(r),roomAxes(r)]),
      ['1.13','TERASA (3 ČASTI)',fixedSk(TERRACE_AREA_M2,2),'—','DREVENÁ TERASOVÁ PODL.','—','—','A–D / 4–6'],
      ['Σ',`ČISTÁ PODLAHA ${PLAN_ROOMS.length} MIESTNOSTÍ`,fixedSk(totalArea,2),'','','','','']],pal));
  blocks.push(materialBlock(pal));
  blocks.push(tableBlock('ZÁKLADNÉ ÚDAJE',[{title:'ÚDAJ',width:26},{title:'HODNOTA',width:74}],[
    ['Pôdorys','L · hlavné krídlo ulica–záhrada + krídlo s krytou terasou'],
    ['Vonkajšie rozmery',`${mm(F.x1-F.x0)} × ${mm(F.y1-F.y0)} mm · hlavné krídlo hĺbka ${mm(F.gardenY-F.y0)} · krídlo šírka ${mm(F.x1-F.wingX)}`],
    ['Zastavaná plocha',`${fixedSk(footprint,2)} m² po vonkajšie líce stien`],
    ['Otvory v obvode',`${exterior.filter(o=>o.code.startsWith('O')).length} okien a presklení · ${exterior.filter(o=>o.code.startsWith('D')).length} dverí, brán a posuvných stien · ${CODED_OPENINGS.filter(o=>o.door).length} vnútorných dverí`],
    ['Výšky','±0,000 = čistá podlaha 1. NP · S.V. 2 600 pod SDK podhľadom · obývačka 2 750 pri stene, 4 850 pod hrebeňom'],
  ],pal));
  if(level>=2)blocks.push(tableBlock('TABUĽKA OTVOROV',[{title:'KÓD',width:8},{title:'OTVOR',width:44},{title:'TYP',width:24},{title:'MIEST.',width:9},{title:'ŠÍRKA',width:10,align:'r'},{title:'VÝŠKA',width:10,align:'r'},{title:'PARAPET',width:11,align:'r'},{title:'NADPR.',width:11,align:'r'},{title:'FASÁDA · OSI',width:20}],
    CODED_OPENINGS.map(o=>[o.code,o.item.name,o.label,o.room?.number??'—',mm(o.item.opening!.width),mm(o.item.opening!.height),mm(o.item.opening!.sill),mm(o.item.opening!.sill+o.item.opening!.height),`${o.facade?.id??'int'} · ${roomAxes(o.room??PLAN_ROOMS[0]).split(' / ')[0]}`]),pal));
  if(level>=3)blocks.push(tableBlock('SVETLÉ ROZMERY MIESTNOSTÍ (mm)',[{title:'OZN.',width:8},{title:'OBDĹŽNIKY ČISTEJ PODLAHY · ŠÍRKA × HĹBKA',width:92}],
    PLAN_ROOMS.map(r=>[r.number,roomRectsByArea(r).slice(0,4).map(p=>`${mm(p.x1-p.x0)} × ${mm(p.y1-p.y0)}`).join('  +  ')+(r.rectsMm.length>4?'  + …':'')]),pal));
  if(level>=4){
    const items=codedItems(level,livingLayout);
    blocks.push(tableBlock(`${level>=5?'SÚPIS PRVKOV':'PEVNÉ VYBAVENIE'} · ${items.length} · OBÝVAČKA ${livingLayout}`,[{title:'KÓD',width:8},{title:'PRVOK',width:44},{title:'MIEST.',width:9},{title:'↔',width:10,align:'r'},{title:'↕',width:10,align:'r'},{title:'VÝŠKA',width:10,align:'r'},{title:'OD PODL.',width:11,align:'r'},{title:'OD Z',width:10,align:'r'},{title:'OD J',width:10,align:'r'},{title:'OSI',width:17}],
      items.map(c=>[c.code,c.item.name,c.room?.number??'ext.',mm(c.width),mm(c.depth),mm(c.height),c.mount>0?mm(c.mount):'0',mm(c.fromWest),mm(c.fromSouth),c.cell]),pal));
  }
  return blocks;
}
function Panel({level,pal,livingLayout}:{level:ExportLevel;pal:Palette;livingLayout:LivingLayoutId}) {
  const blocks=panelBlocks(level,pal,livingLayout);
  // Base metrics at scale 1, then a uniform scale so the blocks fill the panel height.
  const baseFs=1.7,basePitch=2.9,gap=3.5;
  const baseHeight=blocks.reduce((s,b)=>s+b.height(baseFs,basePitch,TABLES.w)+gap,0);
  const k=Math.min(1.55,TABLES.h/baseHeight);
  const pitch=k>=1?basePitch:Math.max(1.9,basePitch*k),fs=k>=1?baseFs:Math.min(baseFs,pitch*.62);
  const scale=k>=1?k:1,width=TABLES.w/scale;
  const tops:number[]=[];
  for(let i=0,cy=TABLES.y/scale;i<blocks.length;i++){tops.push(cy);cy+=blocks[i].height(fs,pitch,width)+gap/scale;}
  return <g>
    <defs>
      <pattern id="xs-l-exterior" width={1.5} height={1.5} patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1={0} y1={0} x2={0} y2={1.5} stroke={pal.hatch} strokeWidth={.16}/></pattern>
      <pattern id="xs-l-bearing" width={.9} height={.9} patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1={0} y1={0} x2={0} y2={.9} stroke={pal.hatch} strokeWidth={.14}/></pattern>
      <pattern id="xs-l-partition" width={2.4} height={2.4} patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1={0} y1={0} x2={0} y2={2.4} stroke={pal.hatch} strokeWidth={.1}/></pattern>
      <pattern id="xs-l-insulation" width={1} height={1} patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><rect width={1} height={1} fill={pal.insulation}/><line x1={0} y1={0} x2={0} y2={1} stroke={pal.hatch} strokeWidth={.08}/></pattern>
    </defs>
    <line x1={PANEL.x-3} x2={PANEL.x-3} y1={PANEL.y} y2={PANEL.y+PANEL.h} stroke={pal.rule} strokeWidth={.3}/>
    <g transform={scale===1?undefined:`scale(${scale})`}>{blocks.map((b,i)=>b.render(TABLES.x/scale,tops[i],width,fs,pitch))}</g>
  </g>;
}

function TitleBlock({level,pal,color,livingLayout}:{level:ExportLevel;pal:Palette;color:boolean;livingLayout:LivingLayoutId}) {
  const spec=EXPORT_LEVELS.find(l=>l.level===level)!;
  const living=LIVING_LAYOUTS[livingLayout];
  const {x,y,w,h}=TITLE;
  const date=new Date().toLocaleDateString('sk-SK',{day:'2-digit',month:'2-digit',year:'numeric'});
  const label=(lx:number,ly:number,text:string)=><text x={lx} y={ly} fontSize={2.1} fill={pal.muted} fontStyle="italic">{text}</text>;
  const value=(lx:number,ly:number,text:string,size=2.8,weight=500,anchor:'start'|'end'='start')=><text x={lx} y={ly} fontSize={size} fontWeight={weight} fill={pal.ink} textAnchor={anchor}>{text}</text>;
  const rule=(ly:number,x0=x,x1=x+w,width=.3)=><line x1={x0} x2={x1} y1={ly} y2={ly} stroke={pal.ink} strokeWidth={width}/>;
  const split=x+w*.66;
  const meta:[string,string][]=[['FORMÁT','A1 · 841 × 594 mm'],['DÁTUM',date],['STUPEŇ',`DT · L${level}`],['REVÍZIA',EXPORT_REVISION],['MIERKA','1 : 50'],['VERZIA',color?'farebná':'čiernobiela']];
  const scaleX=x,scaleY=y-9,marks=[0,1,2,3,4,5];
  return <g fontFamily={FONT}>
    <g stroke={pal.ink} strokeWidth={.3} fill="none">
      {marks.map(m=><Fragment key={m}>{m<5&&<rect x={scaleX+m*20} y={scaleY} width={20} height={2.2} fill={m%2?'#fff':pal.ink}/>}<text x={scaleX+m*20} y={scaleY-1.4} fontSize={2.3} textAnchor="middle" fill={pal.ink} stroke="none">{m===0?'0':m===5?'5 m':String(m)}</text></Fragment>)}
      <text x={scaleX+110} y={scaleY+2} fontSize={2.3} fill={pal.ink} stroke="none">1 : 50 (A1) · 1 : 100 (A3)</text>
    </g>
    <g transform={`translate(${x+w-8} ${y-8})`}>
      <circle r={5.5} fill="#fff" stroke={pal.ink} strokeWidth={.45}/>
      <path d="M0,-5.5 L2.6,0 L0,-1.6 L-2.6,0 Z" fill={pal.ink}/>
      <text y={4.2} fontSize={4} fontWeight={700} textAnchor="middle" fill={pal.ink}>S</text>
    </g>
    {rule(y,x,x+w,.9)}
    {value(x,y+4.6,'±0,000 = ČISTÁ PODLAHA 1. NP',2.6,700)}
    {value(x+w,y+4.6,`PÔDORYS 1. NP · L${level}`,2.6,700,'end')}
    {rule(y+6.2)}
    {label(x,y+9.4,'STAVEBNÍK')}{value(x+30,y+9.6,'Dávid Zita, Hana Ivičičová · Drnholec',2.4,500)}
    {label(x,y+13.2,'PODKLAD')}{value(x+30,y+13.4,'D1.1.002 Půdorys 1.NP · DPSZ 04/2026 · Ing. arch. Jiří Bradáč, Ing. arch. Vladimír Muzikář',2.4,500)}
    {label(x,y+17,'VYPRACOVAL')}{value(x+30,y+17.2,`Digitálne dvojča · export z aktívneho 3D modelu variantu C · revízia ${EXPORT_REVISION}`,2.4,500)}
    {rule(y+19.4)}
    {value(x,y+24.2,'PODKLAD PRE REALIZÁCIU · EXPORT Z DIGITÁLNEHO DVOJČAŤA',3.4,500)}
    {rule(y+25.8)}
    {label(x,y+28.6,'NÁZOV A MIESTO STAVBY')}
    {value(x,y+36.2,'NOVOSTAVBA RD BŘEZÍ U MIKULOVA',7,800)}
    {value(x,y+40.6,'PARC. Č. 6012/26, K.Ú. BŘEZÍ U MIKULOVA, 691 81 BŘEZÍ U MIKULOVA',3,500)}
    {rule(y+42.8)}
    {label(x,y+45.6,'OBJEKT')}{value(x,y+50,'RD BŘEZÍ U MIKULOVA · VARIANT C',3.6,600)}
    {label(x,y+54,'ČASŤ')}{value(x,y+58.4,'D1.1 ARCHITEKTONICKO-STAVEBNÉ RIEŠENIE',3.6,600)}
    {label(x,y+62.6,'VÝKRES')}{value(x,y+69.8,'PÔDORYS 1. NP',7,800)}
    {value(x,y+74.6,`ÚROVEŇ L${level} · ${spec.title.toUpperCase()} · ${spec.summary} Obývačka 1.03 vo variante ${living.id}: ${living.label}.`,2.2,400)}
    <line x1={split-3} x2={split-3} y1={y+42.8} y2={y+h} stroke={pal.ink} strokeWidth={.3}/>
    {meta.map(([k,v],i)=><g key={k}>{label(split,y+46+i*3.6,k)}{value(x+w,y+46+i*3.6,v,2.4,500,'end')}</g>)}
    {label(split,y+69,'ČÍSLO PRÍLOHY')}
    {value(x+w,y+76.6,`D1.1.002-C-L${level}`,6.4,800,'end')}
    <g transform={`translate(${split} ${y+70.4})`}><rect width={11} height={7} rx={1} fill={pal.accent}/><text x={5.5} y={5.4} fontSize={5} fontWeight={800} textAnchor="middle" fill="#fff">L{level}</text></g>
    {rule(y+h,x,x+w,.9)}
  </g>;
}

export function ExportSheet({level,color,livingLayout=DEFAULT_LIVING_LAYOUT_ID}:{level:ExportLevel;color:boolean;livingLayout?:LivingLayoutId}) {
  const pal=color?COLOR:MONO;
  const chains=[...facadeChains(level),...(level>=3?SECTION_CHAINS:[]),...(level>=3?DOOR_CHAINS:[])];
  return <svg xmlns="http://www.w3.org/2000/svg" viewBox={`0 0 ${SHEET.w} ${SHEET.h}`} width={SHEET.w*PX_PER_MM} height={SHEET.h*PX_PER_MM} fontFamily={FONT} role="img" aria-label={`Pôdorys 1. NP, úroveň ${level}`}>
    <style>{`.xs-doors .fp-door path{fill:none;stroke:${pal.ink};stroke-width:${T(.3)}}.xs-doors .fp-door path+path{stroke-width:${T(.12)};stroke-dasharray:none}.xs-doors .fp-door-gap{fill:#fff;stroke:none}.xs-doors .fp-sliding path{stroke:${pal.ink}}text{font-family:${FONT}}`}</style>
    <rect width={SHEET.w} height={SHEET.h} fill="#fff"/>
    <rect x={SHEET.m/2} y={SHEET.m/2} width={SHEET.w-SHEET.m} height={SHEET.h-SHEET.m} fill="none" stroke={pal.ink} strokeWidth={.5}/>
    <g transform={`translate(${PLAN_BOX.x-PLAN_EXTENT.x0/S} ${PLAN_BOX.y+PLAN_EXTENT.y1/S}) scale(${1/S})`}>
      <Defs pal={pal}/>
      <g clipPath="url(#xs-plan-clip)">
        <Site pal={pal} color={color}/>
        <Outdoor pal={pal}/>
        <Rooms pal={pal}/>
        <Grid pal={pal}/>
        <Items pal={pal} level={level} livingLayout={livingLayout}/>
        <Walls pal={pal}/>
        <ExteriorOpenings pal={pal}/>
        <InteriorDoors/>
        {chains.map((c,i)=><Chain key={i} chain={c} color={pal.dim} fontSize={c.role==='facade'?T(2.2):T(2)}/>)}
        {level>=3&&<InnerDims pal={pal}/>}
        {level>=2&&<OpeningCodes pal={pal}/>}
        {level>=2&&<DoorCodes pal={pal}/>}
        <RoomLabels pal={pal} level={level}/>
        {level>=4&&<ItemLabels pal={pal} level={level} livingLayout={livingLayout}/>}
      </g>
    </g>
    <LegendStrip level={level} pal={pal} color={color}/>
    <Panel level={level} pal={pal} livingLayout={livingLayout}/>
    <TitleBlock level={level} pal={pal} color={color} livingLayout={livingLayout}/>
  </svg>;
}
