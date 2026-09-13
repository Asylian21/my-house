import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { Scene } from '@babylonjs/core/scene';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { describe, expect, it } from 'vitest';
import { TwinSceneController } from '../lib/babylon-scene';
import { ARCHITECTURAL_DOOR_INVENTORY, type AnimatedDoorRegistration } from '../lib/babylon-doors';
import { HOUSE } from '../lib/twin-active-house';
import { ACTIVE_CONCEPT, CHILDRENS_BEDROOM_FITOUTS, INTERIOR_ROOMS, KITCHEN_RUN, OFFICE_FITOUT } from '../lib/twin-interior';
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
    expect(OFFICE_FITOUT.desk.footprintMm.x1-front('FRONT-07').startXmm).toBe(50);
    expect(front('FRONT-07')).toMatchObject({startXmm:24292,widthMm:2000,kind:'fixed',frameWidthMm:35});
  });

  it('builds one fixed boy-room pane, one square sash, a girl-room double sash and the complete slim moving portal',()=>{
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
      const boy=scene.meshes.filter(m=>m.name.startsWith('Terasové presklenie 800'));
      expect(boy.filter(m=>m.name.includes('izolačné dvojsklo'))).toHaveLength(1);
      expect(boy.some(m=>/krídlo|kľučka|stredový stĺpik/.test(m.name))).toBe(false);
      const square=scene.meshes.filter(m=>m.name.includes('GARDEN-BOY-DESK'));
      expect(square.filter(m=>m.name.includes('izolačné dvojsklo'))).toHaveLength(1);
      const boyBars=[...boy,...square].filter(m=>/(?:stĺpik|priečnik)$/.test(m.name));
      expect(boyBars).toHaveLength(12);
      for(const bar of boyBars){
        const bounds=bar.getBoundingInfo().boundingBox.extendSize;
        expect((bar.name.endsWith('stĺpik')?bounds.x:bounds.y)*2,bar.name).toBeCloseTo(.045,6);
      }
      for(const parts of [boy,square]){
        const head=parts.find(m=>m.name.endsWith('rám horný priečnik'))!;
        head.computeWorldMatrix(true);
        expect(head.getBoundingInfo().boundingBox.maximumWorld.y,head.name).toBeCloseTo(2.4,6);
      }
      const facadeBars=scene.meshes.filter(m=>
        /^(?:Výplň otvoru|Terasové presklenie|Bočná výplň otvoru|Bočné garážové okno|Terasové posuvné presklenie|Lodžia · presklené dvere)/.test(m.name)
        &&/(?:stĺpik|priečnik)$/.test(m.name));
      expect(facadeBars.length).toBeGreaterThan(boyBars.length);
      for(const bar of facadeBars)expect(bar.material,bar.name).toBe(facadeFrame);
      const girl=scene.meshes.filter(m=>m.name.includes('FRONT-05'));
      expect(girl.filter(m=>m.name.includes('izolačné dvojsklo'))).toHaveLength(2);
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

  it('exports both boy-room openings and keeps window parts clear of the moved noticeboard',()=>{
    const windows=PLAN_ITEMS.filter(i=>i.roomId==='ROOM-1-09'&&i.category==='openings'&&i.opening);
    const square=windows.find(i=>i.id.includes('GARDEN-BOY-DESK'))!;
    expect(square.opening).toMatchObject({width:1200,height:1200,sill:1200});
    expect(windows.some(i=>i.name==='Pevný sklenený pás')).toBe(true);
    const opening=HOUSE.facades.garden.openings.find(o=>o.id==='GARDEN-BOY-DESK')!;
    const desk=CHILDRENS_BEDROOM_FITOUTS.find(f=>f.roomId==='ROOM-1-09')!.desk.footprintMm;
    // Conservative envelope of a 90-degree inward swing from the left jamb,
    // including 30 mm beyond the full rough opening for sash fittings.
    expect(opening.startXmm+opening.widthMm+30).toBeLessThan(desk.x0);
    const furniture=PLAN_ITEMS.filter(i=>i.id.startsWith('C-BOY-109')).flatMap(i=>i.meshes);
    for(const w of windows.flatMap(i=>i.meshes))for(const f of furniture){
      expect([Math.min(w.rect.x1,f.rect.x1)-Math.max(w.rect.x0,f.rect.x0),Math.min(w.rect.y1,f.rect.y1)-Math.max(w.rect.y0,f.rect.y0),Math.min(w.z1,f.z1)-Math.max(w.z0,f.z0)].every(n=>n>1),`${w.name} / ${f.name}`).toBe(false);
    }
  });
});
