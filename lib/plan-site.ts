import { SITE_BOUNDARY } from './plan-export';
import { HOUSE } from './twin-active-house';
import type { Point2Mm as PointMm } from './twin-site';

/** Same local millimetre frame as the floor plan and Babylon model. */
export const PARCEL_BOUNDS = {
  x0: Math.min(...SITE_BOUNDARY.map(p => p.x)) - 1800,
  x1: Math.max(...SITE_BOUNDARY.map(p => p.x)) + 1800,
  y0: Math.min(...SITE_BOUNDARY.map(p => p.y)) - 2000,
  y1: Math.max(...SITE_BOUNDARY.map(p => p.y)) + 1800,
};
export const PARCEL_PATH = `M${SITE_BOUNDARY.map(p => `${p.x},${-p.y}`).join('L')}Z`;
export const PARCEL_AREA_M2 = Math.abs(SITE_BOUNDARY.slice(0,-1).reduce((sum,p,i) => {
  const next=SITE_BOUNDARY[i+1];return sum+p.x*next.y-next.x*p.y;
},0))/2e6;

function project(point:PointMm,a:PointMm,b:PointMm) {
  const dx=b.x-a.x,dy=b.y-a.y;
  const t=Math.max(0,Math.min(1,((point.x-a.x)*dx+(point.y-a.y)*dy)/(dx*dx+dy*dy)));
  return {x:a.x+t*dx,y:a.y+t*dy};
}
/** Nearest house vertex to each main parcel edge; rounded street corner stays in the polygon. */
export const HOUSE_SETBACKS = SITE_BOUNDARY.slice(0,-1).flatMap((a,i) => {
  const b=SITE_BOUNDARY[i+1],length=Math.hypot(b.x-a.x,b.y-a.y);
  if(length<10000)return [];
  const candidates=HOUSE.footprintMm.map(from=>{const to=project(from,a,b);return {from,to,distance:Math.hypot(from.x-to.x,from.y-to.y)};});
  const nearest=candidates.reduce((best,p)=>p.distance<best.distance?p:best);
  const side=Math.abs(b.x-a.x)>Math.abs(b.y-a.y)?(a.y+b.y>20000?'Záhrada':'Ulica'):(a.x+b.x>30000?'Východ':'Západ');
  return [{...nearest,side}];
});
