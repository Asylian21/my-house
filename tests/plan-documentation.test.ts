import { readFileSync } from 'node:fs';
import { describe, expect, it } from 'vitest';
import { extractPlanGeometry, hull } from '../scripts/plan-documentation/extract';
import generated from '../lib/plan-geometry.generated.json';
import { PLAN_ITEMS, PLAN_ITEM_BY_ID, PLAN_ROOMS, PLAN_FULL_BOUNDS, fitPlanRect, searchPlanItems, zoomPlanAt } from '../lib/plan-documentation';
import { BEDROOM_FITOUT, CHILDRENS_BEDROOM_FITOUTS, INTERIOR_DOORS, INTERIOR_RENDER_WALLS, KITCHEN_RUN } from '../lib/twin-interior';

describe('Documentation of the active 3D model',()=>{
  it('is an exact fresh projection of every eligible physical component',()=>{
    const actual=extractPlanGeometry(readFileSync(new URL('../public/assets/archviz/dom-terrace.glb',import.meta.url)));
    expect(generated).toEqual(actual);
    const ids=PLAN_ITEMS.flatMap(item=>item.meshes.map(mesh=>mesh.id));
    expect(ids).toHaveLength(actual.meshes.length);
    expect(new Set(ids).size).toBe(ids.length);
    expect(new Set(PLAN_ITEMS.map(item=>item.id)).size).toBe(PLAN_ITEMS.length);
    for(const item of PLAN_ITEMS){
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
