import { type RectMm, type InteriorDoor } from '@/lib/twin-interior';
import { rect, type ConceptCabinet } from '@/lib/floor-plan-concept';

const m=(n:number)=>(n/1000).toLocaleString('sk-SK',{minimumFractionDigits:2,maximumFractionDigits:2});
export function Box({r,...props}:{r:RectMm}&Omit<React.SVGProps<SVGRectElement>,'r'>) { return <rect x={r.x0} y={-r.y1} width={r.x1-r.x0} height={r.y1-r.y0} {...props}/>; }
export function Label({x,y,children,...props}:{x:number;y:number;children:React.ReactNode}&React.SVGProps<SVGTextElement>) { return <text x={x} y={-y} textAnchor="middle" {...props}>{children}</text>; }
export function Dimension({x0,x1,y,label}:{x0:number;x1:number;y:number;label?:string}) {return <g className="fp-dimension"><path d={`M${x0},${-y-90}v180 M${x0},${-y}H${x1} M${x1},${-y-90}v180`}/><Label x={(x0+x1)/2} y={y+110}>{label??`${m(x1-x0)} m`}</Label></g>;}
export function VerticalDimension({x,y0,y1,label}:{x:number;y0:number;y1:number;label:string}) {const cy=(y0+y1)/2;return <g className="fp-dimension"><path d={`M${x},${-y0}V${-y1}M${x-70},${-y0}h140M${x-70},${-y1}h140`}/><Label x={x-120} y={cy} transform={`rotate(-90 ${x-120} ${-cy})`}>{label}</Label></g>;}
export function BuiltInCabinet({cabinet}:{cabinet:ConceptCabinet}) {
  const r=cabinet.rectMm, cx=(r.x0+r.x1)/2, cy=(r.y0+r.y1)/2;
  const horizontal=cabinet.facing!=='EAST', sign=cabinet.facing==='NORTH'?1:-1;
  const front=cabinet.facing==='NORTH'?r.y1:r.y0;
  const size=horizontal?`${m(r.x1-r.x0)} × ${m(r.y1-r.y0)}`:`${m(r.y1-r.y0)} × ${m(r.x1-r.x0)}`;
  return <g className="fp-hall-cabinet" data-facing={cabinet.facing}>
    <title>{`${cabinet.label} · ${size} m`}</title>
    <Box r={r} className="fp-wardrobe fp-walkin-cabinet"/>
    <path className="fp-cabinet-front" d={horizontal?`M${r.x0},${-(front-sign*35)}H${r.x1}`:`M${r.x1-35},${-r.y0}V${-r.y1}M${r.x0},${-cy}H${r.x1}`}/>
    {horizontal?<>
      <Label x={cx} y={cy+65} className="fp-cabinet-label">{cabinet.facing==='SOUTH'?'ZÁDVERIE':'CHODBA'}</Label>
      <Label x={cx} y={cy-90} className="fp-cabinet-label">{size}</Label>
      <path className="fp-cabinet-access" d={`M${cx},${-(front+sign*230)}V${-(front+sign*40)}M${cx-60},${-(front+sign*110)}L${cx},${-(front+sign*40)}L${cx+60},${-(front+sign*110)}`}/>
    </>:<Label x={cx} y={cy} transform={`rotate(-90 ${cx} ${-cy})`} className="fp-furniture-label">{size}</Label>}
  </g>;
}
export function Door({door}:{door:InteriorDoor & {leafPlaneMm?:number}}) {
  const d=door, horizontal=d.axis==='X', exactPivot=d.hingeOffsetMm!==undefined;
  const plane=d.leafPlaneMm??(exactPivot?(d.swing<0?d.wallSpanMm[0]:d.wallSpanMm[1])+d.swing*d.hingeOffsetMm!:(d.wallSpanMm[0]+d.wallSpanMm[1])/2);
  const inset=exactPivot&&d.widthMm!==d.leafWidthMm?60:0;
  const hinge=d.startMm+(d.hinge===1?d.widthMm-inset:inset);
  if(d.motion==='POCKET_SLIDING') {
    const storedStart=d.startMm+(d.pocketDirection??1)*(d.pocketTravelMm??d.widthMm);
    return <g className="fp-door fp-sliding" data-pocket-direction={d.pocketDirection??1}><Box r={horizontal?rect(d.startMm,d.wallSpanMm[0],d.startMm+d.widthMm,d.wallSpanMm[1]):rect(d.wallSpanMm[0],d.startMm,d.wallSpanMm[1],d.startMm+d.widthMm)} className="fp-door-gap"/><path d={horizontal?`M${storedStart},${-plane}h${d.leafWidthMm}m${-d.leafWidthMm},35h${d.leafWidthMm}`:`M${plane},${-storedStart}v${-d.leafWidthMm}`}/><title>{d.label}</title></g>;
  }
  const x=horizontal?hinge:plane, y=horizontal?plane:hinge;
  const ex=horizontal?hinge:plane+d.swing*d.leafWidthMm, ey=horizontal?plane+d.swing*d.leafWidthMm:hinge;
  const closedEnd=hinge-d.hinge*d.leafWidthMm;
  const cx=horizontal?closedEnd:plane, cy=horizontal?plane:closedEnd;
  // The leaf (not the rough opening) sets the radius of the quarter-circle.
  const sweep=horizontal?Number(d.hinge===d.swing):Number(d.hinge!==d.swing);
  return <g className="fp-door"><Box r={horizontal?rect(d.startMm,d.wallSpanMm[0],d.startMm+d.widthMm,d.wallSpanMm[1]):rect(d.wallSpanMm[0],d.startMm,d.wallSpanMm[1],d.startMm+d.widthMm)} className="fp-door-gap"/><path d={`M${x},${-y}L${ex},${-ey}`}/><path d={`M${cx},${-cy}A${d.leafWidthMm},${d.leafWidthMm} 0 0 ${sweep} ${ex},${-ey}`} strokeDasharray="55 35"/><title>{d.label}</title></g>;
}
