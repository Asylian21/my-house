import { SITE_BOUNDARY } from '@/lib/plan-export';
import { HOUSE_SETBACKS, PARCEL_PATH, PARCEL_BOUNDS } from '@/lib/plan-site';
import { HOUSE } from '@/lib/twin-active-house';
import { PLAN_ROOMS } from '@/lib/plan-documentation';

export function ParcelGeometry({dimensions=true}:{dimensions?:boolean}) {
  return <g className="parcel-geometry" pointerEvents="none">
    <path d={PARCEL_PATH} fill="#e7efe9" fillOpacity=".62" stroke="#44806b" strokeWidth="2" vectorEffect="non-scaling-stroke"/>
    {SITE_BOUNDARY.slice(0,-1).map((p,i)=><circle key={i} cx={p.x} cy={-p.y} r="70" fill="#fff" stroke="#44806b" strokeWidth="1.5" vectorEffect="non-scaling-stroke"/>)}
    <g fontFamily="Arial, sans-serif" fill="#356955" fontSize="310" textAnchor="middle"><text x="6500" y="-20400" fontWeight="600">PARCELA 6012/26</text><text x="6500" y="-21000">Březí u Mikulova</text><text x="15000" y="1150" letterSpacing="90" fontSize="250">ULICA · PARCELA 6012/1</text></g>
    {dimensions&&HOUSE_SETBACKS.map(({from,to,distance,side})=><g key={side}>
      <path d={`M${from.x},${-from.y}L${to.x},${-to.y}`} fill="none" stroke="#347760" strokeDasharray="5 4" strokeWidth="1" vectorEffect="non-scaling-stroke"/>
      <text x={(from.x+to.x)/2+(side==='Záhrada'?400:0)} y={-(from.y+to.y)/2-150} fontSize="280" textAnchor={side==='Záhrada'?'start':'middle'} fill="#255c48" stroke="white" strokeWidth="95" paintOrder="stroke fill" fontFamily="Arial, sans-serif">{(distance/1000).toLocaleString('sk-SK',{minimumFractionDigits:3,maximumFractionDigits:3})} m</text>
    </g>)}
  </g>;
}
export function SiteDrawing() {
  const b=PARCEL_BOUNDS;
  return <svg viewBox={`${b.x0} ${-b.y1} ${b.x1-b.x0} ${b.y1-b.y0}`} role="img" aria-label="Pôdorys variantu C na parcele 6012/26, uličný aj pravý odstup domu 3 metre">
    <ParcelGeometry/>
    <path d={`M${HOUSE.footprintMm.map(p=>`${p.x},${-p.y}`).join('L')}Z`} fill="#e6eaf0" stroke="#536270" strokeWidth="25"/>
    {PLAN_ROOMS.flatMap(room=>room.rectsMm.map((r,i)=><rect key={`${room.id}-${i}`} x={r.x0} y={-r.y1} width={r.x1-r.x0} height={r.y1-r.y0} fill={room.number==='1.03'?'#dce8f6':'#f8fafc'} stroke="#536270" strokeWidth="15"/>))}
    {PLAN_ROOMS.map(room=><text key={room.id} x={room.standingPointMm.x} y={-room.standingPointMm.y} textAnchor="middle" fontFamily="Arial, sans-serif" fontSize="255" fill="#536270">{room.number}</text>)}
  </svg>;
}
