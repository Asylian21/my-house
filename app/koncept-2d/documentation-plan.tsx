import { memo, type SVGProps } from 'react';
import { SERVICE_CORE_REVISION, HEATING_LAYOUTS, DEFAULT_HEATING_LAYOUT_ID, type HeatingLayoutId } from '@/lib/technical-design';
import { INTERIOR_DOORS } from '@/lib/twin-interior';
import { HOUSE } from '@/lib/twin-active-house';
import { PLAN_ITEMS, PLAN_ITEMS_ALL, PLAN_ROOMS, exteriorWallLayer, formatMm, numberSk, type PlanCategory, type PlanItem, type PlanMesh, type PlanViewBox } from '@/lib/plan-documentation';
import { DEFAULT_LIVING_LAYOUT_ID, type LivingLayoutId } from '@/lib/twin-living-layouts';
import type { RectMm } from '@/lib/twin-interior';
import { Box, Door } from './plan-svg';

export const ROOM_COLORS=['#e8eef0','#edf0f2','#eee9df','#e6eaef','#e1ecec','#e1ecec','#e7e9ec','#eee9e5','#e7edf1','#ece9e3','#e1ecec','#e8e9eb','#e8e5df'];
const SORTED_PARTS=PLAN_ITEMS_ALL.flatMap(item=>item.meshes.map(mesh=>({mesh,item}))).sort((a,b)=>a.mesh.z0-b.mesh.z0 || a.mesh.z1-b.mesh.z1);
/** A curved tube must keep its concave silhouette, including in thumbnails and exports. */
export function MeshSilhouette({mesh,...props}:{mesh:PlanMesh}&SVGProps<SVGPathElement>){
  return <path {...props} d={mesh.silhouettePath??`M${mesh.polygon.replaceAll(' ','L')}Z`} style={mesh.silhouettePath?{...props.style,stroke:'none'}:props.style} fillRule="nonzero"/>;
}
export function PlanDimensions({rect,unit='mm',size=130,offsetMm}:{rect:RectMm;unit?:'mm'|'cm'|'m';size?:number;offsetMm?:number}) {
  const offset=offsetMm??size*2.4, x=(rect.x0+rect.x1)/2,y=-(rect.y0+rect.y1)/2;
  return <g className="pd-dimensions" fontSize={size} pointerEvents="none" fill="#245ccd" stroke="#245ccd" strokeWidth={1}>
    <path vectorEffect="non-scaling-stroke" fill="none" d={`M${rect.x0},${-rect.y0+offset}H${rect.x1} M${rect.x0},${-rect.y0+offset-size/2}v${size} M${rect.x1},${-rect.y0+offset-size/2}v${size} M${rect.x1+offset},${-rect.y0}V${-rect.y1} M${rect.x1+offset-size/2},${-rect.y0}h${size} M${rect.x1+offset-size/2},${-rect.y1}h${size}`}/>
    <text x={x} y={-rect.y0+offset+size*1.25} textAnchor="middle" stroke="white" strokeWidth={size*.35} paintOrder="stroke fill">{formatMm(rect.x1-rect.x0,unit)}</text>
    <text x={rect.x1+offset+size*1.25} y={y} textAnchor="middle" transform={`rotate(-90 ${rect.x1+offset+size*1.25} ${y})`} stroke="white" strokeWidth={size*.35} paintOrder="stroke fill">{formatMm(rect.y1-rect.y0,unit)}</text>
  </g>;
}

export const PlanGeometry=memo(function PlanGeometry({layers,details,overhead,selectedId,componentId,roomId,labels=true,dimensions=false,unit='mm',clipRect,unitsPerPixel=17,livingLayout=DEFAULT_LIVING_LAYOUT_ID,heatingLayout=DEFAULT_HEATING_LAYOUT_ID}:{layers:Record<PlanCategory,boolean>;details:boolean;overhead:boolean;selectedId:string|null;componentId:string|null;roomId:string;labels?:boolean;dimensions?:boolean;unit?:'mm'|'cm'|'m';clipRect?:RectMm;unitsPerPixel?:number;livingLayout?:LivingLayoutId;heatingLayout?:HeatingLayoutId}) {
  // Paint the model from floor upwards, while keeping high joinery selectable
  // through the inventory. Door symbols carry the architectural swing, not a
  // misleading closed-leaf silhouette. Living-room pieces of the other layout
  // stay out of the drawing entirely.
  const visibleParts=SORTED_PARTS.filter(({item})=>(!item.layout||item.layout===livingLayout)&&(!item.heatingLayout||item.heatingLayout===heatingLayout));
  const polygons=clipRect?visibleParts.filter(({mesh:m})=>m.rect.x0<=clipRect.x1&&m.rect.x1>=clipRect.x0&&m.rect.y0<=clipRect.y1&&m.rect.y1>=clipRect.y0):visibleParts;
  return <>
    <defs>
      <pattern id="pd-grid" width="1000" height="1000" patternUnits="userSpaceOnUse"><path d="M1000 0H0V1000" fill="none" stroke="#ced5de" strokeWidth="8" opacity=".35"/></pattern>
      <pattern id="pd-insulation" width="90" height="90" patternUnits="userSpaceOnUse" patternTransform="rotate(-45)"><rect width="90" height="90" fill="#dde6eb"/><path d="M0 0V90" stroke="#6f8290" strokeWidth="14"/></pattern>
    </defs>
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
      // Exterior walls are drawn in their build-up: dark masonry, light insulation band on the outer face.
      const insulation=item.category==='walls'&&exteriorWallLayer(mesh)==='insulation';
      const fill=insulation?'url(#pd-insulation)':item.category==='walls'?'#414a56':item.category==='openings'?'#adcbdc':item.category==='lighting'?'#edd8a5':mesh.color;
      return <MeshSilhouette key={mesh.id} mesh={mesh} data-item={item.id} data-component={mesh.id} data-layer={item.category==='walls'?exteriorWallLayer(mesh):undefined} className={`pd-part${selected?' is-selected':''}${component?' is-component':''}`} fill={component?'#3974eb':selected?'#b4cdfb':fill} stroke={component?'#1449bd':selected?'#2a65d4':item.category==='walls'?'#343e49':'#63707b'} strokeWidth={component?1.5:selected?1:.45} vectorEffect="non-scaling-stroke" opacity={roomId&&item.roomId!==roomId&&!selected?0.25:overheadMesh&&!component?0.4:1}>
        <title>{`${item.name} · ${mesh.name.split(' · ').slice(-1)[0]}`}</title>
      </MeshSilhouette>;
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
    {[...item.meshes].sort((a,b)=>a.z0-b.z0).map(m=><MeshSilhouette key={m.id} mesh={m} fill={m.id===componentId?'#3e78e9':m.color} opacity={componentId&&m.id!==componentId?0.15:1} stroke="#677486" strokeWidth=".5" vectorEffect="non-scaling-stroke"/>)}
  </svg>;
}

export function TechnicalClearances({heatingLayout=DEFAULT_HEATING_LAYOUT_ID}:{heatingLayout?:HeatingLayoutId}){
  const h=HEATING_LAYOUTS[heatingLayout],b=h.boiler,t=h.accumulator,door=SERVICE_CORE_REVISION.exteriorDoor;
  const zones=[{rect:b.serviceRectMm,color:'#256eaa',label:`Pred kotlom ${numberSk(b.frontServiceClearanceMm)} mm`},
    {rect:t.serviceRectMm,color:'#187c75',label:'Prípojky · 600'},
    {rect:h.storage.frontClearanceRectMm,color:'#93602a',label:'Skriňa · 600'},
    {rect:h.shelving.frontClearanceRectMm,color:'#7b664c',label:'Police · 600'}];
  return <g pointerEvents="none" aria-label={`Obslužné priestory · technická ${heatingLayout}`} className="pd-clearances">
    {zones.map(({rect:r,color,label})=><g key={color}>
      <Box r={r} fill={color} fillOpacity=".08" stroke={color} strokeWidth="1.25" strokeDasharray="6 4" vectorEffect="non-scaling-stroke"/>
      <text x={(r.x0+r.x1)/2} y={-(r.y0+r.y1)/2} fontSize="75" fill={color} stroke="white" strokeWidth="24" paintOrder="stroke" textAnchor="middle">{label}</text>
    </g>)}
    <text x={t.centerMm.x} y={-t.centerMm.y-35} textAnchor="middle" fontSize="90" fill="#187c75" stroke="white" strokeWidth="28" paintOrder="stroke">{numberSk(t.nominalVolumeL)} l · Ø{numberSk(t.outerDiameterMm)}</text>
    <text x={t.centerMm.x} y={-t.centerMm.y+85} textAnchor="middle" fontSize="70" fill="#187c75" stroke="white" strokeWidth="22" paintOrder="stroke">bez izolácie Ø{t.transportDiameterWithoutInsulationMm}</text>
    <text x={HOUSE.facades.east.faceXmm+420} y={-(door.startYmm+door.widthMm/2)+30} textAnchor="middle" fontSize="80" fill="#45596e" stroke="white" strokeWidth="24" paintOrder="stroke">{door.id} · {door.widthMm}</text>
    <text x={(h.boiler.hopper.footprintMm.x0+h.boiler.hopper.footprintMm.x1)/2} y={-h.boiler.hopper.footprintMm.y0-100} textAnchor="middle" fontSize="65" fill="#45596e" stroke="white" strokeWidth="22" paintOrder="stroke">Zásobník · 180 kg</text>
    <text x={b.body.footprintMm.x1+90} y={-b.body.footprintMm.y0+120} fontSize="80" fill="#256eaa" stroke="white" strokeWidth="24" paintOrder="stroke">Čelo kotla →</text>
    <text x={h.flue.centerMm.x} y={-h.flue.centerMm.y+175} textAnchor="middle" fontSize="65" fill="#45596e" stroke="white" strokeWidth="22" paintOrder="stroke">Dymovod ↑</text>
    <text x={h.shelving.footprintMm.x0-40} y={-h.shelving.footprintMm.y1+80} textAnchor="end" fontSize="70" fill="#7b664c" stroke="white" strokeWidth="22" paintOrder="stroke">Regál 750 × 300</text>
  </g>;
}
export function TechnicalLegend({heatingLayout=DEFAULT_HEATING_LAYOUT_ID}:{heatingLayout?:HeatingLayoutId}){
  const h=HEATING_LAYOUTS[heatingLayout],b=h.boiler;
  return <p className="pd-clearance-legend"><span>Modrá: obsluha kotla</span><span>Zelená: prípojky nádrže</span><span>Hnedá: skriňa a police</span><strong style={{color:'#aa6021',flexBasis:'100%'}}>Nádrž vľavo hore, kotol pod ňou, zásobník dole. Dvierka zatvorené, čelo doprava. Pred telesom {numberSk(b.frontServiceClearanceMm)} mm, pred horákom {numberSk(b.clearFloorBeyondBurnerMm)} mm. Návod uvádza vpredu 2 000 mm; odstupy musí vyriešiť dodávateľ.</strong><small>Za telesom je {b.modeledRearClearanceMm} mm k ľavej stene, zvislý dymovod je {numberSk(h.flue.wallClearanceMm)} mm od nej. Rozmerový obal zahŕňa kotol, násypku a podávač so zatvorenými dvierkami. Koleno, podávač a servisné otváranie treba potvrdiť. Napravo zostáva voľná plocha aspoň 1 050 × 1 330 mm, spoločná pre obsluhu a priechod k vonkajším dverám. Servisné plochy ponechať voľné.</small></p>;
}

export function StaticPlan({viewBox,roomId='',labels=true,livingLayout=DEFAULT_LIVING_LAYOUT_ID,heatingLayout=DEFAULT_HEATING_LAYOUT_ID}:{viewBox:PlanViewBox;roomId?:string;labels?:boolean;livingLayout?:LivingLayoutId;heatingLayout?:HeatingLayoutId}) {
  return <svg xmlns="http://www.w3.org/2000/svg" viewBox={`${viewBox.x} ${viewBox.y} ${viewBox.width} ${viewBox.height}`} role="img" aria-label="Pôdorys aktuálneho 3D modelu">
    <PlanGeometry layers={{furniture:true,equipment:true,lighting:false,walls:true,openings:true,finishes:true}} details overhead={false} selectedId={null} componentId={null} roomId={roomId} labels={labels&&roomId!=='ROOM-1-07'} dimensions unitsPerPixel={viewBox.width/600} clipRect={{x0:viewBox.x,x1:viewBox.x+viewBox.width,y0:-viewBox.y-viewBox.height,y1:-viewBox.y}} livingLayout={livingLayout} heatingLayout={heatingLayout}/>
    {roomId==='ROOM-1-07'&&<TechnicalClearances heatingLayout={heatingLayout}/>}
  </svg>;
}
