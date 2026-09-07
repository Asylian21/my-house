import { memo } from 'react';
import { SERVICE_CORE_REVISION, TECHNICAL_HEATING_FITOUT as HEATING } from '@/lib/technical-design';
import { INTERIOR_DOORS } from '@/lib/twin-interior';
import { PLAN_ITEMS, PLAN_ROOMS, formatMm, numberSk, type PlanCategory, type PlanItem, type PlanViewBox } from '@/lib/plan-documentation';
import type { RectMm } from '@/lib/twin-interior';
import { Box, Door } from './plan-svg';

export const ROOM_COLORS=['#e8eef0','#edf0f2','#eee9df','#e6eaef','#e1ecec','#e1ecec','#e7e9ec','#eee9e5','#e7edf1','#ece9e3','#e1ecec','#e8e9eb','#e8e5df'];
const SORTED_PARTS=PLAN_ITEMS.flatMap(item=>item.meshes.map(mesh=>({mesh,item}))).sort((a,b)=>a.mesh.z0-b.mesh.z0 || a.mesh.z1-b.mesh.z1);
export function PlanDimensions({rect,unit='mm',size=130,offsetMm}:{rect:RectMm;unit?:'mm'|'cm'|'m';size?:number;offsetMm?:number}) {
  const offset=offsetMm??size*2.4, x=(rect.x0+rect.x1)/2,y=-(rect.y0+rect.y1)/2;
  return <g className="pd-dimensions" fontSize={size} pointerEvents="none" fill="#245ccd" stroke="#245ccd" strokeWidth={1}>
    <path vectorEffect="non-scaling-stroke" fill="none" d={`M${rect.x0},${-rect.y0+offset}H${rect.x1} M${rect.x0},${-rect.y0+offset-size/2}v${size} M${rect.x1},${-rect.y0+offset-size/2}v${size} M${rect.x1+offset},${-rect.y0}V${-rect.y1} M${rect.x1+offset-size/2},${-rect.y0}h${size} M${rect.x1+offset-size/2},${-rect.y1}h${size}`}/>
    <text x={x} y={-rect.y0+offset+size*1.25} textAnchor="middle" stroke="white" strokeWidth={size*.35} paintOrder="stroke fill">{formatMm(rect.x1-rect.x0,unit)}</text>
    <text x={rect.x1+offset+size*1.25} y={y} textAnchor="middle" transform={`rotate(-90 ${rect.x1+offset+size*1.25} ${y})`} stroke="white" strokeWidth={size*.35} paintOrder="stroke fill">{formatMm(rect.y1-rect.y0,unit)}</text>
  </g>;
}

export const PlanGeometry=memo(function PlanGeometry({layers,details,overhead,selectedId,componentId,roomId,labels=true,dimensions=false,unit='mm',clipRect,unitsPerPixel=17}:{layers:Record<PlanCategory,boolean>;details:boolean;overhead:boolean;selectedId:string|null;componentId:string|null;roomId:string;labels?:boolean;dimensions?:boolean;unit?:'mm'|'cm'|'m';clipRect?:RectMm;unitsPerPixel?:number}) {
  // Paint the model from floor upwards, while keeping high joinery selectable
  // through the inventory. Door symbols carry the architectural swing, not a
  // misleading closed-leaf silhouette.
  const polygons=clipRect?SORTED_PARTS.filter(({mesh:m})=>m.rect.x0<=clipRect.x1&&m.rect.x1>=clipRect.x0&&m.rect.y0<=clipRect.y1&&m.rect.y1>=clipRect.y0):SORTED_PARTS;
  return <>
    <defs><pattern id="pd-grid" width="1000" height="1000" patternUnits="userSpaceOnUse"><path d="M1000 0H0V1000" fill="none" stroke="#ced5de" strokeWidth="8" opacity=".35"/></pattern></defs>
    <rect x="-100000" y="-100000" width="200000" height="200000" fill="url(#pd-grid)" pointerEvents="none"/>
    <g className="pd-floors">{PLAN_ROOMS.map((room,i)=><g key={room.id} data-room={room.id} opacity={roomId&&room.id!==roomId?0.45:1}>
      {room.rectsMm.map((rect,index)=><Box key={index} r={rect} fill={roomId===room.id?'#e0eaff':ROOM_COLORS[i]} stroke="#c7cdd4" strokeWidth="8"/>)}
    </g>)}</g>
    <g className="pd-model-components">{polygons.map(({item,mesh})=>{
      const selected=item.id===selectedId, component=mesh.id===componentId;
      const physicalCeiling=/podhľad|štít podhľadu|Podkladová|· podlaha/.test(mesh.name);
      const tiny=Math.min(mesh.rect.x1-mesh.rect.x0,mesh.rect.y1-mesh.rect.y0)<35;
      const overheadMesh=mesh.z0>2100;
      if(!selected&&!component&&(!layers[item.category]||physicalCeiling||(!overhead&&overheadMesh)||(!details&&tiny&&item.category!=='walls'&&item.category!=='openings')))return null;
      if(item.category==='openings'&&INTERIOR_DOORS.some(d=>d.label.split(' · ')[0]===item.id)&&!component)return null;
      if(item.category==='walls'&&mesh.z0>1400&&!component)return null;
      const fill=item.category==='walls'?'#414a56':item.category==='openings'?'#adcbdc':item.category==='lighting'?'#edd8a5':mesh.color;
      return <polygon key={mesh.id} points={mesh.polygon} data-item={item.id} data-component={mesh.id} className={`pd-part${selected?' is-selected':''}${component?' is-component':''}`} fill={component?'#3974eb':selected?'#b4cdfb':fill} stroke={component?'#1449bd':selected?'#2a65d4':item.category==='walls'?'#343e49':'#63707b'} strokeWidth={component?1.5:selected?1:.45} vectorEffect="non-scaling-stroke" opacity={roomId&&item.roomId!==roomId&&!selected?0.25:overheadMesh&&!component?0.4:1}>
        <title>{`${item.name} · ${mesh.name.split(' · ').slice(-1)[0]}`}</title>
      </polygon>;
    })}</g>
    {layers.openings&&<g className="pd-doors">{INTERIOR_DOORS.map(door=>{
      const item=PLAN_ITEMS.find(item=>item.id===door.label.split(' · ')[0]);
      return <g key={door.id} data-item={item?.id}><Door door={door}/></g>;
    })}</g>}
    {labels&&<g pointerEvents="none" className="pd-room-labels">{PLAN_ROOMS.filter(room=>!roomId||room.id===roomId).map(room=>{
      // Position inside the largest room rectangle; the kitchen/living area
      // needs its label away from the dining/sofa cluster.
      const r=[...room.rectsMm].sort((a,b)=>(b.x1-b.x0)*(b.y1-b.y0)-(a.x1-a.x0)*(a.y1-a.y0))[0];
      const x=room.standingPointMm.x,y=room.number==='1.03'?-12500:-room.standingPointMm.y;
      const fs=Math.min(300,unitsPerPixel*12),showName=(r.x1-r.x0)/unitsPerPixel>90;
      return <g key={room.id} opacity={roomId&&roomId!==room.id?0.35:1}>
        <text x={x} y={y-fs} fontSize={fs*.85} textAnchor="middle" fill="#657285" stroke="#fafbfc" strokeWidth={fs*.22} paintOrder="stroke">{room.number}</text>
        {showName&&<text x={x} y={y+fs*.35} fontSize={fs} fontWeight="600" textAnchor="middle" fill="#25354a" stroke="#fafbfc" strokeWidth={fs*.25} paintOrder="stroke">{room.name.replace(' · ulica','').replace(' · dvor','').replace(' do dvora','').replace('Spoločná ','')}</text>}
        <text x={x} y={y+(showName?1.6:.4)*fs} fontSize={fs*.85} textAnchor="middle" fill="#5a697a" stroke="#fafbfc" strokeWidth={fs*.22} paintOrder="stroke">{numberSk(room.area,2)} m²</text>
      </g>;
    })}</g>}
    {dimensions&&<>{!roomId&&<PlanDimensions rect={{x0:6440,y0:3000,x1:28040,y1:22035}} unit="m" size={150}/>}{PLAN_ROOMS.filter(r=>r.id===roomId).map(r=><PlanDimensions key={r.id} rect={r.bounds} unit={unit} offsetMm={600}/>)}</>}
    <g pointerEvents="none" fill="#7c889a" fontSize="130" letterSpacing="20" textAnchor="middle"><text x="15350" y="-11800">ZÁHRADA</text><text x="17300" y="-2100">ULICA · VSTUP</text></g>
  </>;
});

export function ItemMiniature({item,componentId}:{item:PlanItem;componentId?:string|null}) {
  const mesh=item.meshes.find(m=>m.id===componentId),r=mesh?.rect??item.rect;
  const pad=Math.max(r.x1-r.x0,r.y1-r.y0)*.16+50;
  return <svg viewBox={`${r.x0-pad} ${-r.y1-pad} ${r.x1-r.x0+pad*2} ${r.y1-r.y0+pad*2}`} aria-label={`Pohľad zhora: ${item.name}`} role="img">
    {[...item.meshes].sort((a,b)=>a.z0-b.z0).map(m=><polygon key={m.id} points={m.polygon} fill={m.id===componentId?'#3e78e9':m.color} opacity={componentId&&m.id!==componentId?0.15:1} stroke="#677486" strokeWidth=".5" vectorEffect="non-scaling-stroke"/>)}
  </svg>;
}

export function TechnicalClearances(){
  const boiler=HEATING.boiler.assemblyFootprintMm,body=HEATING.boiler.body.footprintMm,rearY=body.y0-HEATING.boiler.modeledRearClearanceMm,axisX=(boiler.x0+boiler.x1)/2;
  const zones=[{rect:HEATING.boiler.serviceRectMm,color:'#256eaa',label:'Obsluha kotla · 2 000 mm',vertical:true},
    {rect:HEATING.accumulator.serviceRectMm,color:'#187c75',label:'600',vertical:false},
    {rect:HEATING.storage.frontClearanceRectMm,color:'#93602a',label:'600',vertical:false}];
  return <g pointerEvents="none" aria-label="Obslužné priestory a trasa nádrže" className="pd-clearances">
    {zones.map(({rect:r,color,label,vertical})=><g key={color}>
      <Box r={r} fill={color} fillOpacity=".09" stroke={color} strokeWidth="1.25" strokeDasharray="6 4" vectorEffect="non-scaling-stroke"/>
      <text x={(r.x0+r.x1)/2} y={-(r.y0+r.y1)/2} transform={vertical?`rotate(-90 ${(r.x0+r.x1)/2} ${-(r.y0+r.y1)/2})`:undefined} fontSize="90" fill={color} stroke="white" strokeWidth="28" paintOrder="stroke" textAnchor="middle">{label}</text>
    </g>)}
    <path d="M28800 -10200L26250 -10150L26000 -10100H25500" fill="none" stroke="#187c75" strokeWidth="2" strokeDasharray="5 4" vectorEffect="non-scaling-stroke"/>
    <path d="M25595 -10176L25500 -10100L25595 -10024" fill="none" stroke="#187c75" strokeWidth="2" vectorEffect="non-scaling-stroke"/>
    <text x="28480" y="-10320" textAnchor="middle" fontSize="95" fill="#187c75" stroke="white" strokeWidth="28" paintOrder="stroke">Nádrž Ø 1 106</text>
    <g fill="#45596e" stroke="#45596e" fontSize="72" textAnchor="middle">
      {[[SERVICE_CORE_REVISION.boilerBayWestMm+10,boiler.x0],[boiler.x1,SERVICE_CORE_REVISION.technicalFacadeInsideMm-10]].map(([x0,x1])=><g key={x0}>
        <path d={`M${x0} -8740H${x1}M${x0} -8785v90M${x1} -8785v90`} fill="none" strokeWidth="1" vectorEffect="non-scaling-stroke"/>
        <text x={(x0+x1)/2} y="-8820" stroke="white" strokeWidth="22" paintOrder="stroke">{numberSk(x1-x0,1)}</text>
      </g>)}
      <path d={`M${axisX} ${-rearY}V${-body.y0}M${axisX-45} ${-rearY}h90M${axisX-45} ${-body.y0}h90`} fill="none" strokeWidth="1" vectorEffect="non-scaling-stroke"/>
      <text x={axisX} y={-(rearY+body.y0)/2} stroke="white" strokeWidth="22" paintOrder="stroke">{HEATING.boiler.modeledRearClearanceMm}</text>
    </g>
  </g>;
}

export function TechnicalLegend(){return <p className="pd-clearance-legend"><span>Modrá: obsluha kotla</span><span>Zelená: nádrž a jej presun</span><span>Hnedá: prístup ku skrini</span><small>Prerušované plochy ponechať voľné. Rozmery v mm. Trasa platí s nádržou zvislo na 100 mm podvozku a oboma krídlami dverí otvorenými von; zásobník a prípojky sa montujú až po osadení nádrže.</small></p>;}

export function StaticPlan({viewBox,roomId='',labels=true}:{viewBox:PlanViewBox;roomId?:string;labels?:boolean}) {
  return <svg xmlns="http://www.w3.org/2000/svg" viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.width} ${viewBox.height}`} role="img" aria-label="Pôdorys aktuálneho 3D modelu">
    <PlanGeometry layers={{furniture:true,equipment:true,lighting:false,walls:true,openings:true,finishes:true}} details overhead={false} selectedId={null} componentId={null} roomId={roomId} labels={labels&&roomId!=='ROOM-1-07'} dimensions unitsPerPixel={viewBox.width/600} clipRect={{x0:viewBox.x,x1:viewBox.x+viewBox.width,y0:-viewBox.y-viewBox.height,y1:-viewBox.y}}/>
    {roomId==='ROOM-1-07'&&<TechnicalClearances/>}
  </svg>;
}
