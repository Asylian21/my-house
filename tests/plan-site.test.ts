import { describe, expect, it } from 'vitest';
import { HOUSE_SETBACKS, PARCEL_AREA_M2, PARCEL_BOUNDS } from '../lib/plan-site';
import { SITE_BOUNDARY } from '../lib/plan-export';
import { fitPlanRect } from '../lib/plan-documentation';
import { ACTIVE_DESIGN, designFromSearch, designHref } from '../lib/twin-design-selection';

describe('canonical project and full cadastral plan',()=>{
  it('keeps every cadastral vertex visible on portrait and landscape canvases',()=>{
    for(const aspect of [.5,1,1.5,2.5]){
      const view=fitPlanRect(PARCEL_BOUNDS,aspect,0);
      for(const p of SITE_BOUNDARY){
        expect(p.x).toBeGreaterThan(view.x);expect(p.x).toBeLessThan(view.x+view.width);
        expect(-p.y).toBeGreaterThan(view.y);expect(-p.y).toBeLessThan(view.y+view.height);
      }
    }
    expect(PARCEL_AREA_M2).toBeCloseTo(752.5083,3);
  });
  it('keeps the requested street and right setbacks at exactly three metres',()=>{
    const distances=Object.fromEntries(HOUSE_SETBACKS.map(s=>[s.side,s.distance]));
    expect(distances.Ulica).toBe(3000);
    expect(distances.Záhrada).toBeGreaterThan(2052.91);
    expect(distances.Východ).toBeCloseTo(3000,8);
    expect(distances.Západ).toBeGreaterThan(6556.88);
    for(const {from,to,distance} of HOUSE_SETBACKS)expect(Math.hypot(from.x-to.x,from.y-to.y)).toBeCloseTo(distance,8);
  });
  it('uses C/B/B at current entry points and preserves archived selections across section URLs',()=>{
    expect(designFromSearch(new URLSearchParams(),ACTIVE_DESIGN)).toEqual({livingLayout:'B',heatingLayout:'B'});
    for(const livingLayout of ['A','B'] as const)for(const heatingLayout of ['A','B'] as const){
      for(const route of ['/podorys','/3d','/docs/manual'] as const){
        const design={livingLayout,heatingLayout},url=new URL(designHref(route,design),'http://localhost');
        expect(url.searchParams.get('variant')).toBe('c');
        expect(designFromSearch(url.searchParams,ACTIVE_DESIGN)).toEqual(design);
      }
    }
  });
});
