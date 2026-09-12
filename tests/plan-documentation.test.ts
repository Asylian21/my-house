import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { extractPlanGeometry, hull, triangleSilhouette } from '../scripts/plan-documentation/extract';
import generated from '../lib/plan-geometry.generated.json';
import { PLAN_ITEMS, PLAN_ITEMS_ALL, PLAN_ITEM_BY_ID, PLAN_ROOMS, PLAN_FULL_BOUNDS, fitPlanRect, planItemsFor, planRoomNotes, searchPlanItems, zoomPlanAt } from '../lib/plan-documentation';
import { BEDROOM_FITOUT, CHILDRENS_BEDROOM_FITOUTS, INTERIOR_DOORS, INTERIOR_RENDER_WALLS, KITCHEN_RUN } from '../lib/twin-interior';
import { LIVING_LAYOUTS, diningTableRectMm } from '../lib/twin-living-layouts';
import { HEATING_LAYOUTS, HEATING_LAYOUT_IDS, normalizeHeatingLayout } from '../lib/technical-design';
import { codedItems, drawnItems } from '../lib/plan-export';
import { HOUSE } from '../lib/twin-site';

describe('Documentation of the active 3D model',()=>{
  it('keeps the empty inside of a bent tube instead of filling its convex hull',()=>{
    const points=[[0,0],[3,0],[3,1],[1,1],[1,3],[0,3]];
    const path=triangleSilhouette(points,[0,1,2,0,3,2,0,3,5,3,4,5]);
    const triangles=path.split('M').filter(Boolean).map(p=>p.replace('Z','').split('L').map(v=>v.split(',').map(Number)));
    const cross=(a:number[],b:number[],p:number[])=>(b[0]-a[0])*(p[1]-a[1])-(b[1]-a[1])*(p[0]-a[0]);
    expect(triangles).toHaveLength(4);
    for(const [a,b,c] of triangles)expect(cross(a,b,c)).toBeGreaterThan(0);
    const covered=(p:number[])=>triangles.some(([a,b,c])=>cross(a,b,p)>=0&&cross(b,c,p)>=0&&cross(c,a,p)>=0);
    expect(covered([.5,2])).toBe(true);
    expect(covered([2,.5])).toBe(true);
    expect(covered([2,1.5])).toBe(false);
    for(const layout of HEATING_LAYOUT_IDS){
      const hose=generated.meshes.find(m=>m.heatingLayout===layout&&m.name.includes('PELLET-FEED-HOSE'))!;
      expect(hose.silhouettePath?.startsWith('M')).toBe(true);
      expect(hose.silhouettePath?.split('Z').length).toBeGreaterThan(20);
    }
  });
  it('is an exact fresh projection of every eligible physical component',()=>{
    const actual=extractPlanGeometry(readFileSync(new URL('../public/assets/archviz/dom-terrace.glb',import.meta.url)));
    expect(generated).toEqual(actual);
    const ids=PLAN_ITEMS_ALL.flatMap(item=>item.meshes.map(mesh=>mesh.id));
    expect(ids).toHaveLength(actual.meshes.length);
    expect(new Set(ids).size).toBe(ids.length);
    expect(new Set(PLAN_ITEMS_ALL.map(item=>item.id)).size).toBe(PLAN_ITEMS_ALL.length);
    for(const item of PLAN_ITEMS_ALL){
      expect([...PLAN_ROOMS.map(r=>r.id),'EXTERIOR']).toContain(item.roomId);
      for(const mesh of item.meshes){
        expect(Object.values(mesh.rect).every(Number.isFinite)).toBe(true);
        expect(mesh.z1).toBeGreaterThanOrEqual(mesh.z0);
        expect(mesh.rect.x1).toBeGreaterThanOrEqual(mesh.rect.x0);
        expect(mesh.rect.y1).toBeGreaterThanOrEqual(mesh.rect.y0);
        expect(mesh.name).not.toMatch(/navigation.guard|collision.proxy|kolízny/i);
      }
    }
  },30000);
  it('documents both living-room layouts side by side and shows exactly one at a time',()=>{
    const A=planItemsFor('A'),B=planItemsFor('B');
    expect(PLAN_ITEMS).toEqual(A);
    const livingA=A.filter(item=>item.layout),livingB=B.filter(item=>item.layout);
    expect(livingA.length).toBeGreaterThanOrEqual(10);
    expect(livingB).toHaveLength(livingA.length);
    expect(A.length).toBe(B.length);
    expect(A.filter(item=>!item.layout)).toEqual(B.filter(item=>!item.layout));
    expect(livingA.every(item=>item.layout==='A'&&item.roomId==='ROOM-1-03')).toBe(true);
    expect(livingB.every(item=>item.layout==='B'&&item.roomId==='ROOM-1-03'&&(item.id.endsWith('-B')||item.id.includes('-B-')))).toBe(true);
    expect(livingA.some(item=>item.id.endsWith('-B'))).toBe(false);
    expect(livingB.reduce((sum,item)=>sum+item.meshes.length,0)).toBe(livingA.reduce((sum,item)=>sum+item.meshes.length,0));
    expect(generated.meshes.filter(m=>'layout' in m).length).toBe(livingA.concat(livingB).reduce((sum,item)=>sum+item.meshes.length,0));
    for(const [suffix,layout] of [['','A'],['-B','B']] as const){
      const spec=LIVING_LAYOUTS[layout];
      expect(PLAN_ITEM_BY_ID.get(`sofa${suffix}`)?.nominal).toEqual({x0:Math.min(spec.fitout.sofa.mainRectMm.x0,spec.fitout.sofa.chaiseRectMm.x0),y0:Math.min(spec.fitout.sofa.mainRectMm.y0,spec.fitout.sofa.chaiseRectMm.y0),x1:Math.max(spec.fitout.sofa.mainRectMm.x1,spec.fitout.sofa.chaiseRectMm.x1),y1:Math.max(spec.fitout.sofa.mainRectMm.y1,spec.fitout.sofa.chaiseRectMm.y1)});
      expect(PLAN_ITEM_BY_ID.get(`LIVING-103-TV-WALL${suffix}`)?.nominal).toEqual(spec.fitout.tvWall.rectMm);
      expect(PLAN_ITEM_BY_ID.get(`dining-table${suffix}`)?.nominal).toEqual(diningTableRectMm(spec.fitout.dining));
      expect(PLAN_ITEM_BY_ID.get(spec.stove.id)?.nominal).toEqual(spec.stove.footprintMm);
      expect(PLAN_ITEM_BY_ID.get(spec.stove.id)?.layout).toBe(layout);
      expect(PLAN_ITEM_BY_ID.get(spec.stove.flue.id)?.layout).toBe(layout);
      // Modelled pieces stay inside their specified envelopes (plus the TV, console and handle protrusions).
      const tv=PLAN_ITEM_BY_ID.get(`LIVING-103-TV-WALL${suffix}`)!;
      expect(Math.max(tv.rect.x1-tv.nominal!.x1,tv.nominal!.x0-tv.rect.x0,tv.rect.y1-tv.nominal!.y1,tv.nominal!.y0-tv.rect.y0)).toBeLessThanOrEqual(120);
      expect(planRoomNotes('ROOM-1-03',layout)).toEqual([...spec.notes]);
      // Six numbered chairs per layout, 1–3 on the kitchen/wall side and 4–6 opposite, each on its data footprint.
      const chairs=planItemsFor(layout).filter(item=>item.id.startsWith('DINING-CHAIR-'));
      expect(chairs.map(item=>item.name).sort()).toEqual([1,2,3,4,5,6].map(n=>`Jedálenská stolička ${n}`));
      for(const chair of spec.fitout.dining.chairs){
        const item=PLAN_ITEM_BY_ID.get(`${chair.id}${suffix}`)!;
        expect(item.layout).toBe(layout);
        expect(Math.abs((item.rect.x0+item.rect.x1)/2-chair.centerMm.x)+Math.abs((item.rect.y0+item.rect.y1)/2-chair.centerMm.y)).toBeLessThan(120);
      }
      expect(PLAN_ITEM_BY_ID.get(`dining-light${suffix}`)?.meshes.filter(m=>/tienidlo/.test(m.name))).toHaveLength(2);
    }
    // Shared kitchen: the peninsula worktop edge is flush with the terrace-door reveal and the
    // east return's upstand stops before window EAST-04 while its worktop continues under the sill.
    const island=PLAN_ITEM_BY_ID.get('kitchen-island')!;
    expect(island.nominal).toEqual(KITCHEN_RUN.peninsulaRectMm);
    expect(island.rect.y1).toBe(HOUSE.facades.wingWest.opening.startYmm+HOUSE.facades.wingWest.opening.widthMm);
    const eastWindow=HOUSE.facades.east.openings.find(o=>o.id==='EAST-04')!;
    const kitchenReturn=PLAN_ITEM_BY_ID.get('kitchen-return')!;
    expect(kitchenReturn.nominal).toEqual(KITCHEN_RUN.eastReturnRectMm);
    expect(kitchenReturn.meshes.find(m=>/obklad pri stene/.test(m.name))?.rect.y1).toBe(eastWindow.startYmm-20);
    expect(kitchenReturn.meshes.find(m=>/kremenná doska/.test(m.name))?.rect.y1).toBeGreaterThanOrEqual(KITCHEN_RUN.eastReturnRectMm.y1);
    expect(searchPlanItems('sedacka','ROOM-1-03','all','B').map(i=>i.id)).toEqual(['sofa-B']);
    expect(searchPlanItems('sedacka','ROOM-1-03','all').map(i=>i.id)).toEqual(['sofa']);
    expect(searchPlanItems('kachle','','equipment','B').map(i=>i.id)).toEqual([LIVING_LAYOUTS.B.stove.id]);
    expect(planRoomNotes('ROOM-1-07')).toBeDefined();
  });
  it('selects technical equipment independently of the living layout, including inventory and exports',()=>{
    for(const living of ['A','B'] as const)for(const heating of HEATING_LAYOUT_IDS){
      const items=planItemsFor(living,heating),h=HEATING_LAYOUTS[heating];
      const equipment=items.filter(i=>i.heatingLayout);
      expect(equipment.length).toBeGreaterThan(8);
      expect(equipment.every(i=>i.heatingLayout===heating&&i.roomId==='ROOM-1-07')).toBe(true);
      expect(items.some(i=>i.layout&&i.layout!==living)).toBe(false);
      expect(searchPlanItems('kotol','ROOM-1-07','all',living,heating).every(i=>!i.heatingLayout||i.heatingLayout===heating)).toBe(true);
      expect(items.find(i=>i.id===`${h.id}-BUFFER-TANK-${h.accumulator.nominalVolumeL}L`)?.product?.dimensions).toContain(String(h.accumulator.outerDiameterMm).replace('1106','1 106'));
      for(const exported of [drawnItems(5,living,heating),codedItems(5,living,heating).map(c=>c.item)]){
        expect(exported.some(i=>i.id===`${h.id}-WOOD-PELLET-BOILER`)).toBe(true);
        expect(exported.some(i=>i.heatingLayout&&i.heatingLayout!==heating)).toBe(false);
      }
      expect(planRoomNotes('ROOM-1-07',living,heating)?.join(' ')).toContain(`Plus ${h.boiler.referenceOutputKw} kW`);
    }
    expect(planItemsFor('B','A').filter(i=>!i.heatingLayout)).toEqual(planItemsFor('B','B').filter(i=>!i.heatingLayout));
    expect(normalizeHeatingLayout('b')).toBe('B');expect(normalizeHeatingLayout('B')).toBe('B');expect(normalizeHeatingLayout('invalid')).toBe('A');
  });
  it('keeps every current interior wall and door, without treating vaulted ceilings as openings',()=>{
    for(const wall of INTERIOR_RENDER_WALLS){
      const mesh=generated.meshes.find(m=>m.name.startsWith(`Vnútorná stena ${wall.id} · `));
      expect(mesh?.rect).toEqual(wall.rectMm);
    }
    for(const door of INTERIOR_DOORS){
      const item=PLAN_ITEM_BY_ID.get(door.label.split(' · ')[0]);
      expect(item?.category,door.id).toBe('openings');
      expect(item?.opening).toEqual({width:door.widthMm,height:door.heightMm,sill:0});
    }
    expect(PLAN_ITEMS.filter(i=>i.category==='openings').some(i=>i.meshes.some(m=>m.name.includes('SDK podhľad')))).toBe(false);
    expect(PLAN_ITEM_BY_ID.get('1.02-Podhľad')?.roomId).toBe('ROOM-1-02');
  });
  it('separates the mattress/frame/rug and individual lamps, cartons and appliances',()=>{
    for(const fit of [BEDROOM_FITOUT,...CHILDRENS_BEDROOM_FITOUTS]){
      const bed=PLAN_ITEM_BY_ID.get(`${fit.id}-BED`);
      expect(bed?.nominal).toEqual(fit.bed.footprintMm);
      expect(bed?.meshes.some(m=>/koberec|koberca/.test(m.name))).toBe(false);
    }
    expect(PLAN_ITEMS.filter(i=>i.id.startsWith('C-BEDROOM-110-LIGHT'))).toHaveLength(3);
    const cartons=PLAN_ITEMS.filter(i=>i.name.startsWith('kartónová krabica'));
    expect(cartons).toHaveLength(4);
    expect(cartons.every(i=>i.rect.x1-i.rect.x0<600)).toBe(true);
    expect(cartons.every(i=>i.meshes.length===2)).toBe(true);
    expect(PLAN_ITEMS.filter(i=>i.name==='Práčka')).toHaveLength(1);
    expect(PLAN_ITEMS.filter(i=>i.name==='Sušička')).toHaveLength(1);
    expect(PLAN_ITEMS.filter(i=>i.id.startsWith('C-BOY-109-rug-play'))).toHaveLength(1);
    expect(PLAN_ITEM_BY_ID.get('kitchen-back')?.nominal?.x0).toBe(KITCHEN_RUN.fridgeUnitRectMm.x1);
  });
  it('includes terrace furniture in its actual coordinate frame and correct parked car direction',()=>{
    const terrace=PLAN_ITEMS.filter(i=>i.roomId==='EXTERIOR');
    expect(terrace).toHaveLength(6);
    expect(terrace.filter(i=>i.name.startsWith('Terasová stolička'))).toHaveLength(2);
    expect(terrace.every(i=>i.rect.y0>11200)).toBe(true);
    const car=PLAN_ITEM_BY_ID.get('vehicle')!;
    const rear=car.meshes.find(m=>m.name==='Superb Combi IV · superb-rear-wordmark')!;
    expect(rear.rect.y1).toBeLessThan(4000);
    expect(car.rect.y1-car.rect.y0).toBeGreaterThan(4800);
  });
  it('finds furniture by room number and Slovak names without accents',()=>{
    expect(searchPlanItems('1.04','', 'all').some(i=>i.name==='Pracovný stôl')).toBe(true);
    expect(searchPlanItems('pracka','', 'all').some(i=>i.name==='Práčka')).toBe(true);
    expect(searchPlanItems('stolicka','EXTERIOR','all')).toHaveLength(2);
    expect(searchPlanItems('zzzz','', 'all')).toHaveLength(0);
  });
  it('documents three purposeful girl-room windows and keeps all physical window parts clear of furniture',()=>{
    const ids=['FRONT-GIRL-BED','FRONT-04','FRONT-05'];
    const windows=PLAN_ITEMS.filter(item=>item.category==='openings'&&ids.some(id=>item.id.includes(id)));
    expect(windows).toHaveLength(3);
    expect(windows.every(item=>item.roomId==='ROOM-1-08'&&item.note&&item.opening)).toBe(true);
    const furniture=PLAN_ITEMS.filter(item=>item.roomId==='ROOM-1-08'&&item.id.startsWith('C-GIRL-108')).flatMap(item=>item.meshes);
    for(const w of windows.flatMap(item=>item.meshes))for(const f of furniture){
      const overlap=[Math.min(w.rect.x1,f.rect.x1)-Math.max(w.rect.x0,f.rect.x0),Math.min(w.rect.y1,f.rect.y1)-Math.max(w.rect.y0,f.rect.y0),Math.min(w.z1,f.z1)-Math.max(w.z0,f.z0)];
      expect(overlap.every(d=>d>1),`${w.name} versus ${f.name}`).toBe(false);
    }
  });
  it('keeps pan/zoom geometry and fitting correct on wide and portrait canvases',()=>{
    for(const aspect of [.5,1,2.5]){
      const view=fitPlanRect(PLAN_FULL_BOUNDS,aspect,500);
      expect(view.width/view.height).toBeCloseTo(aspect);
      expect(view.x).toBeLessThan(PLAN_FULL_BOUNDS.x0);
      expect(view.x+view.width).toBeGreaterThan(PLAN_FULL_BOUNDS.x1);
      expect(view.y).toBeLessThan(-PLAN_FULL_BOUNDS.y1);
      expect(view.y+view.height).toBeGreaterThan(-PLAN_FULL_BOUNDS.y0);
      const anchor={x:view.x+view.width*.23,y:view.y+view.height*.61};
      const zoomed=zoomPlanAt(view,.5,anchor);
      expect((anchor.x-zoomed.x)/zoomed.width).toBeCloseTo(.23);
      expect((anchor.y-zoomed.y)/zoomed.height).toBeCloseTo(.61);
      expect(zoomPlanAt(zoomed,2,anchor)).toEqual(view);
    }
    expect(hull([[0,0],[2,0],[1,1],[2,2],[0,2],[0,0]])).toEqual([[0,0],[2,0],[2,2],[0,2]]);
  });
});
