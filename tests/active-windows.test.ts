import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { Scene } from '@babylonjs/core/scene';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { describe, expect, it } from 'vitest';
import { TwinSceneController } from '../lib/babylon-scene';
import { ARCHITECTURAL_DOOR_INVENTORY, type AnimatedDoorRegistration } from '../lib/babylon-doors';
import { HOUSE } from '../lib/twin-active-house';
import { ACTIVE_CONCEPT, CHILDRENS_BEDROOM_FITOUTS, INTERIOR_ROOMS, INTERIOR_DOORS, KITCHEN_RUN, OFFICE_FITOUT } from '../lib/twin-interior';
import { PLAN_ITEMS } from '../lib/plan-documentation';
import { CODED_OPENINGS, FACADES, facadeChains } from '../lib/plan-export';
import { HOUSE as historicalHouse } from '../lib/twin-site';

describe('C facade revision at the current furniture',()=>{
  it('narrows the screenshot-selected GARDEN-02 to 220 cm in the plan, D5 schedule and dimension chain',()=>{
    const portal=HOUSE.facades.garden.openings.find(o=>o.id==='GARDEN-02')!;
    const original=historicalHouse.facades.garden.openings.find(o=>o.id==='GARDEN-02')!;
    expect(portal).toMatchObject({startXmm:11990,widthMm:2200,heightMm:2400,sillMm:0});
    expect(portal.startXmm+portal.widthMm/2).toBe(original.startXmm+original.widthMm/2);
    expect(original.widthMm).toBe(2500);
    expect(HOUSE.facades.wingWest.opening).toMatchObject({startYmm:11550,widthMm:2250,heightMm:2400});
    expect(PLAN_ITEMS.some(item=>item.id==='Terasové presklenie 2500')).toBe(false);
    const item=PLAN_ITEMS.find(item=>item.id==='Terasové presklenie 2200')!;
    expect(item.roomId).toBe('ROOM-1-10');
    expect(item.opening).toEqual({width:2200,height:2400,sill:0});
    expect(item.rect.x0).toBe(11990);
    expect(item.rect.x1).toBe(14190);
    expect(CODED_OPENINGS.find(o=>o.item.id===item.id)?.code).toBe('D5');
    const facade=FACADES.find(f=>f.def.id==='N')!;
    expect(facade.segments.find(s=>s.item?.id===item.id)).toMatchObject({a:11990,b:14190,kind:'opening'});
    const row=facadeChains(2).find(c=>c.axis==='x'&&c.at===facade.def.outer+700)!;
    const index=row.points.indexOf(11990);
    expect(index).toBeGreaterThanOrEqual(0);
    expect(row.points[index+1]-row.points[index]).toBe(2200);
    expect(row.sub![index].replaceAll('\u00a0',' ')).toBe('2 400 (0)');
  });

  it('centres kitchen and bath openings, preserves the shower opening across H200 revisions and positions office glazing',()=>{
    const east=(id:string)=>HOUSE.facades.east.openings.find(o=>o.id===id)!;
    const front=(id:string)=>HOUSE.facades.front.openings.find(o=>o.id===id)!;
    const kitchen=east('EAST-04');
    expect(kitchen.startYmm-KITCHEN_RUN.rectMm.y1).toBe(KITCHEN_RUN.peninsulaRectMm.y0-kitchen.startYmm-kitchen.widthMm);
    const showerBay=INTERIOR_ROOMS.find(r=>r.number==='1.05')!.rectsMm.find(r=>r.x1===27541)!;
    const shower=east('EAST-02');
    expect(shower.startYmm).toBe(6801.5);
    expect(shower.startYmm-showerBay.y0).toBe(249.5);
    expect(showerBay.y1-shower.startYmm-shower.widthMm).toBe(199.5);
    const bath=front('FRONT-03');
    expect(Math.abs(bath.startXmm+bath.widthMm/2-(ACTIVE_CONCEPT.bathLeft+ACTIVE_CONCEPT.bathRight)/2)).toBeLessThanOrEqual(.5);
    expect(6412-east('EAST-01').startYmm-east('EAST-01').widthMm).toBe(200);
    expect(east('EAST-01').startYmm-OFFICE_FITOUT.cabinet.footprintMm.y1).toBeGreaterThan(200);
    expect(front('FRONT-07').startXmm-OFFICE_FITOUT.desk.footprintMm.x1).toBe(100);
    expect(front('FRONT-07')).toMatchObject({startXmm:24442,widthMm:2000,kind:'fixed',frameWidthMm:35});
  });

  it('builds identical slim double windows in both child rooms and the complete moving terrace portal',()=>{
    const engine=new NullEngine(), scene=new Scene(engine), material=new PBRMaterial('frame',scene);
    const facadeFrame=new PBRMaterial('real-glass-frame',scene);
    // Distinct materials expose accidental routing through the former timber
    // frames, which a single material shared by every stub would conceal.
    const realisticMaterials=new Proxy<Record<string,PBRMaterial>>({glassFrame:facadeFrame},{get:(target,key)=>{
      const name=String(key);
      return target[name]??=new PBRMaterial(`real-${name}`,scene);
    }});
    const doors:AnimatedDoorRegistration[]=[];
    const identity=<T,>(mesh:T)=>mesh;
    // Exercise the same facade dispatch as the browser and the 2D extractor.
    const shell=Object.create(TwinSceneController.prototype);
    Object.assign(shell,{scene,materials:new Proxy({},{get:()=>material}),realisticMaterials,
      register:identity,realisticOnly:identity,castShadow:identity,larchFor:()=>material,
      appearance:identity,doors:{register:(door:AnimatedDoorRegistration)=>doors.push(door)},renderQuality:{anisotropy:1}});
    try{
      shell.buildRealisticHouseShell();
      expect(doors.map(d=>d.id)).not.toContain('GARDEN-03');
      expect(ARCHITECTURAL_DOOR_INVENTORY.map(d=>d.id)).not.toContain('GARDEN-03');
      const facadeIds=['FRONT-ENTRY','EAST-03','LOGGIA-DOOR','GARDEN-02','GARDEN-03','WING-WEST-01'];
      expect(doors.map(({id,kind})=>({id,kind})).sort((a,b)=>a.id.localeCompare(b.id))).toEqual(
        ARCHITECTURAL_DOOR_INVENTORY.filter(d=>facadeIds.includes(d.id)).toSorted((a,b)=>a.id.localeCompare(b.id)),
      );
      const boy=scene.meshes.filter(m=>m.name.includes('GARDEN-03'));
      const girl=scene.meshes.filter(m=>m.name.includes('FRONT-05'));
      const childBars=[...boy,...girl].filter(m=>/(?:stĺpik|priečnik)$/.test(m.name));
      expect(childBars).toHaveLength(26);
      for(const bar of childBars){
        const bounds=bar.getBoundingInfo().boundingBox.extendSize;
        expect((bar.name.endsWith('stĺpik')?bounds.x:bounds.y)*2,bar.name).toBeCloseTo(.045,6);
      }
      for(const parts of [boy,girl]){
        expect(parts.filter(m=>m.name.includes('izolačné dvojsklo'))).toHaveLength(2);
        expect(parts.filter(m=>m.name.endsWith('kľučka'))).toHaveLength(2);
        const head=parts.find(m=>m.name.endsWith('rám horný priečnik'))!;
        head.computeWorldMatrix(true);
        expect(head.getBoundingInfo().boundingBox.maximumWorld.y,head.name).toBeCloseTo(2.4,6);
      }
      expect(scene.meshes.some(m=>/GARDEN-BOY-DESK|Terasové presklenie 800/.test(m.name))).toBe(false);
      const facadeBars=scene.meshes.filter(m=>
        /^(?:Výplň otvoru|Terasové presklenie|Bočná výplň otvoru|Bočné garážové okno|Terasové posuvné presklenie|Lodžia · presklené dvere)/.test(m.name)
        &&/(?:stĺpik|priečnik)$/.test(m.name));
      expect(facadeBars.length).toBeGreaterThan(childBars.length);
      for(const bar of facadeBars)expect(bar.material,bar.name).toBe(facadeFrame);
      expect(scene.meshes.some(m=>/FRONT-GIRL-BED|FRONT-04/.test(m.name))).toBe(false);
      const slim=scene.meshes.filter(m=>m.name.startsWith('Terasové posuvné presklenie 2 250'));
      for(const bar of slim.filter(m=>m.name.endsWith('stĺpik'))){
        expect(bar.getBoundingInfo().boundingBox.extendSize.z*2,bar.name).toBeCloseTo(.035,6);
      }
      const slider=doors.find(d=>d.id==='WING-WEST-01')!;
      const moving=slim.find(m=>m.metadata?.dynamicCameraOccluder)!;
      moving.computeWorldMatrix(true);
      const closed=moving.getAbsolutePosition().clone();
      slider.apply(1,1); moving.computeWorldMatrix(true);
      expect(moving.getAbsolutePosition().subtract(closed).length()).toBeGreaterThan(1);
      slider.apply(0,0); moving.computeWorldMatrix(true);
      expect(moving.getAbsolutePosition().subtract(closed).length()).toBeLessThan(.00001);
      expect(moving.checkCollisions).toBe(true);
      const gardenParts=scene.meshes.filter(m=>m.name.startsWith('Terasové presklenie 2200'));
      expect(gardenParts.length).toBeGreaterThan(10);
      const frameParts=gardenParts.filter(m=>m.name.includes(' · rám '));
      const bounds=frameParts.map(m=>{m.computeWorldMatrix(true);return m.getBoundingInfo().boundingBox;});
      expect(Math.max(...bounds.map(b=>b.maximumWorld.x))-Math.min(...bounds.map(b=>b.minimumWorld.x))).toBeCloseTo(2.2,6);
      expect(Math.max(...bounds.map(b=>b.maximumWorld.y))).toBeCloseTo(2.4,6);
      for(const [index,width] of [[1,1.35],[2,1.65]]){
        const field=scene.meshes.find(m=>m.name===`Modřínové pole záhradnej fasády ${index}`)!;
        expect(field.getBoundingInfo().boundingBox.extendSize.x*2).toBeCloseTo(width,6);
      }
      const gardenSlider=doors.find(d=>d.id==='GARDEN-02')!;
      const gardenLeaf=gardenParts.find(m=>m.metadata?.dynamicCameraOccluder)!;
      gardenLeaf.computeWorldMatrix(true);
      const gardenClosed=gardenLeaf.getAbsolutePosition().clone();
      gardenSlider.apply(1,1);gardenLeaf.computeWorldMatrix(true);
      expect(Math.abs(gardenLeaf.getAbsolutePosition().x-gardenClosed.x)).toBeCloseTo(.997,6);
      gardenSlider.apply(0,0);gardenLeaf.computeWorldMatrix(true);
      expect(gardenLeaf.getAbsolutePosition().subtract(gardenClosed).length()).toBeLessThan(.00001);
      expect(gardenLeaf.checkCollisions).toBe(true);
    }finally{scene.dispose();engine.dispose();}
  });

  it.each([
    ['ROOM-1-09','GARDEN-03','DOOR-102-109'],
    ['ROOM-1-08','FRONT-05','DOOR-102-108'],
  ])('centres the double window opposite the door in %s and keeps both sashes clear of furniture',(roomId,openingId,doorId)=>{
    const windows=PLAN_ITEMS.filter(i=>i.category==='openings'&&i.id.includes(openingId));
    expect(windows).toHaveLength(1);
    expect(windows[0].roomId).toBe(roomId);
    expect(windows[0].opening).toEqual({width:1800,height:1500,sill:900});
    expect(PLAN_ITEMS.some(i=>/GARDEN-BOY-DESK|Terasové presklenie 800/.test(i.id))).toBe(false);
    const opening=[...HOUSE.facades.garden.openings,...HOUSE.facades.front.openings].find(o=>o.id===openingId)!;
    const door=INTERIOR_DOORS.find(d=>d.id===doorId)!;
    const room=INTERIOR_ROOMS.find(r=>r.id===roomId)!.rectsMm[0];
    expect(opening.startXmm+opening.widthMm/2).toBe(door.startMm+door.widthMm/2);
    expect(opening.startXmm-room.x0).toBe(room.x1-opening.startXmm-opening.widthMm);
    const fit=CHILDRENS_BEDROOM_FITOUTS.find(f=>f.roomId===roomId)!;
    // The entire inward sweep stays between bed and desk, including fittings.
    expect(opening.startXmm-30).toBeGreaterThan(fit.bed.footprintMm.x1);
    expect(opening.startXmm+opening.widthMm+30).toBeLessThan(fit.desk.footprintMm.x0);
    const furniture=PLAN_ITEMS.filter(i=>i.id.startsWith(fit.id)).flatMap(i=>i.meshes);
    for(const w of windows.flatMap(i=>i.meshes))for(const f of furniture){
      expect([Math.min(w.rect.x1,f.rect.x1)-Math.max(w.rect.x0,f.rect.x0),Math.min(w.rect.y1,f.rect.y1)-Math.max(w.rect.y0,f.rect.y0),Math.min(w.z1,f.z1)-Math.max(w.z0,f.z0)].every(n=>n>1),w.name+' / '+f.name).toBe(false);
    }
  });
});
