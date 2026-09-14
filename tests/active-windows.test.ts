import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { Scene } from '@babylonjs/core/scene';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { describe, expect, it } from 'vitest';
import { TwinSceneController } from '../lib/babylon-scene';
import { ARCHITECTURAL_DOOR_INVENTORY, type AnimatedDoorRegistration } from '../lib/babylon-doors';
import { HOUSE } from '../lib/twin-active-house';
import { ACTIVE_CONCEPT, CHILDRENS_BEDROOM_FITOUTS, INTERIOR_ROOMS, INTERIOR_DOORS, KITCHEN_RUN, OFFICE_FITOUT } from '../lib/twin-interior';
import { PLAN_ITEMS } from '../lib/plan-documentation';

describe('C facade revision at the current furniture',()=>{
  it('centres kitchen and bathroom openings and moves both office windows toward the requested walls',()=>{
    const east=(id:string)=>HOUSE.facades.east.openings.find(o=>o.id===id)!;
    const front=(id:string)=>HOUSE.facades.front.openings.find(o=>o.id===id)!;
    const kitchen=east('EAST-04');
    expect(kitchen.startYmm-KITCHEN_RUN.rectMm.y1).toBe(KITCHEN_RUN.peninsulaRectMm.y0-kitchen.startYmm-kitchen.widthMm);
    const showerBay=INTERIOR_ROOMS.find(r=>r.number==='1.05')!.rectsMm.find(r=>r.x1===27541)!;
    const shower=east('EAST-02');
    expect(shower.startYmm-showerBay.y0).toBe(showerBay.y1-shower.startYmm-shower.widthMm);
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
