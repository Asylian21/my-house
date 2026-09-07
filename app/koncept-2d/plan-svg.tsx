import { type RectMm, type InteriorDoor } from '@/lib/twin-interior';
import { rect } from '@/lib/floor-plan-concept';

const m=(n:number)=>(n/1000).toLocaleString('sk-SK',{minimumFractionDigits:2,maximumFractionDigits:2});
export function Box({r,...props}:{r:RectMm}&Omit<React.SVGProps<SVGRectElement>,'r'>) { return <rect x={r.x0} y={-r.y1} width={r.x1-r.x0} height={r.y1-r.y0} {...props}/>; }
export function Label({x,y,children,...props}:{x:number;y:number;children:React.ReactNode}&React.SVGProps<SVGTextElement>) { return <text x={x} y={-y} textAnchor="middle" {...props}>{children}</text>; }
export function Dimension({x0,x1,y,label}:{x0:number;x1:number;y:number;label?:string}) {return <g className="fp-dimension"><path d={`M${x0},${-y-90}v180 M${x0},${-y}H${x1} M${x1},${-y-90}v180`}/><Label x={(x0+x1)/2} y={y+110}>{label??`${m(x1-x0)} m`}</Label></g>;}
export function VerticalDimension({x,y0,y1,label}:{x:number;y0:number;y1:number;label:string}) {const cy=(y0+y1)/2;return <g className="fp-dimension"><path d={`M${x},${-y0}V${-y1}M${x-70},${-y0}h140M${x-70},${-y1}h140`}/><Label x={x-120} y={cy} transform={`rotate(-90 ${x-120} ${-cy})`}>{label}</Label></g>;}
export function Door({door}:{door:InteriorDoor & {leafPlaneMm?:number}}) {
  const d=door, horizontal=d.axis==='X', plane=d.leafPlaneMm??(d.wallSpanMm[0]+d.wallSpanMm[1])/2;
  const hinge=d.startMm+(d.hinge===1?d.widthMm:0), end=d.startMm+(d.hinge===-1?d.widthMm:0);
  if(d.motion==='POCKET_SLIDING') return <g className="fp-door fp-sliding"><Box r={horizontal?rect(d.startMm,d.wallSpanMm[0],d.startMm+d.widthMm,d.wallSpanMm[1]):rect(d.wallSpanMm[0],d.startMm,d.wallSpanMm[1],d.startMm+d.widthMm)} className="fp-door-gap"/><path d={horizontal?`M${d.startMm+d.widthMm},${-plane}h${d.widthMm}m${-d.widthMm},35h${d.widthMm}`:`M${plane},${-d.startMm-d.widthMm}v${-d.widthMm}`}/><title>{d.label}</title></g>;
  const x=horizontal?hinge:plane, y=horizontal?plane:hinge;
  const ex=horizontal?hinge:plane+d.swing*d.leafWidthMm, ey=horizontal?plane+d.swing*d.leafWidthMm:hinge;
  const cx=horizontal?end:plane, cy=horizontal?plane:end;
  return <g className="fp-door"><Box r={horizontal?rect(d.startMm,d.wallSpanMm[0],d.startMm+d.widthMm,d.wallSpanMm[1]):rect(d.wallSpanMm[0],d.startMm,d.wallSpanMm[1],d.startMm+d.widthMm)} className="fp-door-gap"/><path d={`M${x},${-y}L${ex},${-ey}`}/><path d={`M${cx},${-cy}Q${horizontal?end:ex},${-(horizontal?ey:end)} ${ex},${-ey}`} strokeDasharray="55 35"/><title>{d.label}</title></g>;
}
