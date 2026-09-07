import { describe, expect, it } from 'vitest';
import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { Scene } from '@babylonjs/core/scene';
import { createConcept, DEFAULT_NESTED_CONCEPT, rect } from '../lib/floor-plan-concept';
import * as baseline from '../lib/twin-interior-baseline';
import { HOUSE as originalHouse } from '../lib/twin-site';
import { HOUSE } from '../lib/twin-active-house';
import { ACTIVE_CONCEPT, BEDROOM_FITOUT, CHILDRENS_BEDROOM_FITOUTS, ENTRY_FITOUT, ENSUITE_BATHROOM_FITOUT, GARAGE_FITOUT, HALLWAY_BUILT_IN_WARDROBES, INTERIOR_ROOMS, INTERIOR_WALLS, INTERIOR_RENDER_WALLS, INTERIOR_DOORS, OFFICE_FITOUT, roomAt, roomAreaM2, type RectMm } from '../lib/twin-interior';
import { buildInterior } from '../lib/babylon-interior';
import type { AnimatedDoorRegistration } from '../lib/babylon-doors';
import { sceneXM, sceneZM, SCENE_CENTER_MM } from '../lib/twin-render-frame';
import { contains, intersects, opening, openLeaf, swingHits, walkingPath } from './floor-plan-geometry';

const furniture:{id:string;room:string;rect:RectMm}[]=[
  {id:'primary-bed',room:'ROOM-1-10',rect:BEDROOM_FITOUT.bed.footprintMm},
  ...BEDROOM_FITOUT.bedsideRectsMm.map((r,i)=>({id:`bedside-${i}`,room:'ROOM-1-10',rect:r})),
  ...HALLWAY_BUILT_IN_WARDROBES.map(w=>({id:w.id,room:w.roomId,rect:w.footprintMm})),
  {id:'entry-bench',room:'ROOM-1-01',rect:ENTRY_FITOUT.bench.footprintMm},
  ...[ENSUITE_BATHROOM_FITOUT.bathtub,ENSUITE_BATHROOM_FITOUT.toilet,ENSUITE_BATHROOM_FITOUT.vanity].map((f,i)=>({id:`bath-${i}`,room:'ROOM-1-11',rect:f.footprintMm})),
  ...[GARAGE_FITOUT.utilitySink,GARAGE_FITOUT.storageRack,GARAGE_FITOUT.mower].map((f,i)=>({id:`garage-${i}`,room:'ROOM-1-12',rect:f.footprintMm})),
  ...[OFFICE_FITOUT.desk,OFFICE_FITOUT.chair,OFFICE_FITOUT.cabinet].map((f,i)=>({id:`office-${i}`,room:'ROOM-1-04',rect:f.footprintMm})),
  ...CHILDRENS_BEDROOM_FITOUTS.flatMap(f=>[f.bed,f.wardrobe,f.desk,f.chair].map((piece,i)=>({id:`${f.id}-${i}`,room:f.roomId,rect:piece.footprintMm}))),
  ...CHILDRENS_BEDROOM_FITOUTS.flatMap(f=>[f.readingRectMm,f.toyStorageRectMm,f.bookcaseRectMm].map((r,i)=>({id:`${f.id}-play-storage-${i}`,room:f.roomId,rect:r}))),
];

describe('active 3D house matches the approved default C plan',()=>{
  it('uses identical walls, room polygons and door openings without modifying the baseline studies',()=>{
    const c=createConcept(DEFAULT_NESTED_CONCEPT);
    expect(INTERIOR_WALLS).toEqual(c.walls);
    expect(INTERIOR_ROOMS.map(r=>r.rectsMm)).toEqual(c.rooms.map(r=>r.rectsMm));
    expect(INTERIOR_DOORS.map(d=>({...d,label:undefined}))).toEqual(c.doors.map(d=>({...d,label:undefined})));
    expect(baseline.INTERIOR_ROOMS.find(r=>r.number==='1.08')!.name).toBe('Spálňa');
    expect(INTERIOR_ROOMS).toHaveLength(13);
    expect(roomAreaM2(INTERIOR_ROOMS.find(r=>r.number==='1.04')!)).toBeCloseTo(12.337492,6);
    expect(INTERIOR_DOORS.some(d=>d.id==='DOOR-102-112'||d.id==='DOOR-108-111')).toBe(false);
    for(const id of ['ROOM-1-03']){
      expect(INTERIOR_ROOMS.find(r=>r.id===id)!.rectsMm).toEqual(baseline.INTERIOR_ROOMS.find(r=>r.id===id)!.rectsMm);
    }
  });
  it('meshes wall corners only once while retaining every boundary',()=>{
    INTERIOR_RENDER_WALLS.forEach((a,i)=>INTERIOR_RENDER_WALLS.slice(i+1).forEach(b=>expect(intersects(a.rectMm,b.rectMm),`${a.id} / ${b.id}`).toBe(false)));
    for(const wall of INTERIOR_WALLS){
      for(let x=wall.rectMm.x0+1;x<wall.rectMm.x1;x+=50)for(let y=wall.rectMm.y0+1;y<wall.rectMm.y1;y+=50){
        expect(INTERIOR_RENDER_WALLS.some(w=>x>=w.rectMm.x0&&x<=w.rectMm.x1&&y>=w.rectMm.y0&&y<=w.rectMm.y1),wall.id).toBe(true);
      }
    }
  });
  it('preserves the envelope, roof and recess and places both small windows in their new rooms',()=>{
    for(const key of ['footprintMm','roof','porches','lowerBar','wing'] as const) expect(HOUSE[key]).toEqual(originalHouse[key]);
    const garage=HOUSE.facades.front.openings.find(o=>o.id==='FRONT-02')!;
    const bath=HOUSE.facades.front.openings.find(o=>o.id==='FRONT-03')!;
    expect([garage.startXmm,bath.startXmm]).toEqual([10942,13368]);
    expect(garage.startXmm+garage.widthMm).toBeLessThan(ACTIVE_CONCEPT.garageBay!.x1);
    expect(bath.startXmm).toBeGreaterThan(ACTIVE_CONCEPT.bathLeft);
    expect(bath.startXmm+bath.widthMm).toBeLessThan(ACTIVE_CONCEPT.bathRight);
  });
  it('keeps furniture in its actual rooms, clear of walls, door swings and other furniture',()=>{
    for(const item of furniture){
      const room=INTERIOR_ROOMS.find(r=>r.id===item.room)!;
      expect(room.rectsMm.some(r=>contains(r,item.rect)),`${item.id} inside ${item.room}`).toBe(true);
      expect(INTERIOR_WALLS.filter(w=>intersects(w.rectMm,item.rect)).map(w=>w.id),`${item.id} walls`).toEqual([]);
      for(const d of INTERIOR_DOORS.filter(d=>d.motion!=='POCKET_SLIDING')) expect(swingHits(d,item.rect),`${item.id} door ${d.id}`).toBe(false);
    }
    furniture.forEach((a,i)=>furniture.slice(i+1).forEach(b=>expect(intersects(a.rect,b.rect),`${a.id} / ${b.id}`).toBe(false)));
    for(const room of INTERIOR_ROOMS){
      expect(roomAt(room.standingPointMm)?.id,room.id).toBe(room.id);
      for(const f of furniture.filter(f=>f.room===room.id)){
        const p=room.standingPointMm;
        expect(intersects(f.rect,rect(p.x-220,p.y-220,p.x+220,p.y+220)),`${room.id} spawn versus ${f.id}`).toBe(false);
      }
    }
  });
  it('fits storage against the dressing-room wall without narrowing either end-of-hall doorway',()=>{
    const cabinet=HALLWAY_BUILT_IN_WARDROBES.find(w=>w.id==='C-HALL-END-CABINET')!;
    const wall=INTERIOR_WALLS.find(w=>w.id==='C-CLOSET-EAST')!.rectMm;
    expect(cabinet.footprintMm).toEqual(rect(13483,5744,14003,7601));
    expect(cabinet.footprintMm.x0).toBe(wall.x1);
    expect(cabinet.frontClearanceRectMm).toEqual(rect(14003,5744,15003,7601));
    expect(cabinet).toMatchObject({roomId:'ROOM-1-02',facing:'EAST',doorCount:2,heightMm:2550});
    for(const id of ['C-HALL-BATH','C-PRIVATE-BED']){
      const door=INTERIOR_DOORS.find(d=>d.id===id)!;
      expect(cabinet.footprintMm.x1).toBe(door.startMm);
      expect(swingHits(door,cabinet.footprintMm)).toBe(false);
      expect(contains(cabinet.frontClearanceRectMm,rect(door.startMm,6560,door.startMm+door.widthMm,7601))).toBe(true);
    }
  });
  it('provides 440mm walking paths between entrance, office, bath, bedroom and closet',()=>{
    const floors=INTERIOR_ROOMS.flatMap(r=>[...r.rectsMm]);
    const obstacles=[...furniture.map(f=>f.rect),...INTERIOR_DOORS.filter(d=>d.motion!=='POCKET_SLIDING').map(openLeaf)];
    const openFloors=[...floors,...INTERIOR_DOORS.map(opening)];
    const entry:[number,number]=[22100,4550];
    for(const goal of [[25100,5800],[13800,4800],[14200,9400],[12250,6500]] as [number,number][]){
      expect(walkingPath(openFloors,obstacles,entry,goal),`entry to ${goal}`).toBe(true);
    }
    // A visit to the shared bathroom must never cross the parents' sleeping room.
    const withoutBedroom=INTERIOR_ROOMS.filter(r=>r.id!=='ROOM-1-10').flatMap(r=>[...r.rectsMm]);
    expect(walkingPath([...withoutBedroom,...INTERIOR_DOORS.filter(d=>d.toRoomId!=='ROOM-1-10').map(opening)],obstacles,entry,[13800,4800])).toBe(true);
  });
  it('fits full-size beds, preschool furniture and daylight with unobstructed play and entry',()=>{
    for(const f of CHILDRENS_BEDROOM_FITOUTS){
      expect(f.childAgeRange).toEqual([3,7]);
      expect(f.bed.mattressWidthMm).toBe(1400);
      expect(f.bed.mattressLengthMm).toBe(2000);
      expect(f.bed.mattressFootprintMm.x1-f.bed.mattressFootprintMm.x0).toBe(1400);
      expect(f.bed.mattressFootprintMm.y1-f.bed.mattressFootprintMm.y0).toBe(2000);
      expect(f.bed.mattressTopElevationMm).toBe(460);
      expect(f.bed.headboardTopElevationMm).toBe(1050);
      expect(f.windowClearanceRectMm.x0-f.bed.footprintMm.x1).toBeGreaterThanOrEqual(200);
      expect(f.chair.wheelCount).toBe(0);
      expect(f.desk.topElevationMm).toBe(540);
      const play=f.clearPlayRectMm;
      expect((play.x1-play.x0)*(play.y1-play.y0)/1e6).toBeGreaterThan(3.7);
      for(const item of furniture.filter(item=>item.room===f.roomId)){
        expect(intersects(play,item.rect),`${item.id} in play zone`).toBe(false);
        expect(intersects(f.windowClearanceRectMm,item.rect),`${item.id} in glazing approach`).toBe(false);
      }
      const floors=INTERIOR_ROOMS.flatMap(r=>[...r.rectsMm]);
      expect(walkingPath([...floors,...INTERIOR_DOORS.map(opening)],
        [...furniture.map(item=>item.rect),...INTERIOR_DOORS.filter(d=>d.motion!=='POCKET_SLIDING').map(openLeaf)],
        [17800,7100],f.roomId==='ROOM-1-09'?[17800,9200]:[17800,4850]),f.roomId).toBe(true);
    }
    expect(INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-09')!.name).toContain('Chlapčenská');
    expect(INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-08')!.name).toContain('Dievčenská');
    expect(HOUSE.facades.garden.openings.find(o=>o.id==='GARDEN-03')).toMatchObject({startXmm:16900,widthMm:2200,sillMm:0});
    const windows=HOUSE.facades.front.openings.filter(o=>['FRONT-GIRL-BED','FRONT-04','FRONT-05'].includes(o.id));
    expect(windows).toHaveLength(3);
    expect(windows.map(w=>[w.startXmm,w.widthMm,w.sillMm,w.heightMm])).toEqual([[15450,1000,1250,1250],[17100,1600,550,1950],[19450,1050,900,1600]]);
    expect(windows.every(w=>w.sillMm+w.heightMm===2500)).toBe(true);
    expect(windows.reduce((sum,w)=>sum+w.widthMm*w.heightMm/1e6,0)).toBeCloseTo(6.05,6);
    expect(windows[1]).toMatchObject({kind:'fixed',frameWidthMm:45});
    for(let i=1;i<windows.length;i++)expect(windows[i].startXmm-windows[i-1].startXmm-windows[i-1].widthMm).toBeGreaterThanOrEqual(650);
    const girl=CHILDRENS_BEDROOM_FITOUTS.find(f=>f.roomId==='ROOM-1-08')!;
    expect(windows[0].sillMm-girl.bed.headboardTopElevationMm).toBe(200);
    expect(windows[2].sillMm-girl.desk.topElevationMm).toBe(360);
    expect(girl.pinboard.facing).toBe('WEST');
  });
  it('renders moved accessories, lights and collision guards in the same room, with clear 80/90cm doors',()=>{
    const engine=new NullEngine({renderWidth:256,renderHeight:256,textureSize:256,deterministicLockstep:false,lockstepMaxSteps:4});
    const scene=new Scene(engine), doors:AnimatedDoorRegistration[]=[];
    const mat=(n:string)=>new PBRMaterial(n,scene);
    try {
      buildInterior({scene,anisotropy:1,wall:mat('wall'),soffit:mat('soffit'),glassFrame:mat('frame'),chimneyMetal:mat('metal'),timber:mat('timber'),register:()=>{},realisticOnly:()=>{},castShadow:()=>{},registerAnimatedDoor:d=>doors.push(d)});
      // The door linings project 12 mm into the alcove. Include their actual
      // meshes, since floor-plan door swings alone cannot catch this overlap.
      const endCabinet=scene.meshes.filter(m=>m.name.startsWith('C-HALL-END-CABINET')&&!m.metadata?.walkCollisionOnly);
      for(const id of ['C-HALL-BATH','C-PRIVATE-BED']){
        const door=INTERIOR_DOORS.find(d=>d.id===id)!;
        const jamb=scene.meshes.find(m=>m.name===`${door.label} · ľavá zárubňa`)!;
        jamb.computeWorldMatrix(true);
        for(const mesh of endCabinet){
          mesh.computeWorldMatrix(true);
          expect(mesh.intersectsMesh(jamb,false),`${mesh.name} clears ${id} lining`).toBe(false);
        }
      }
      const groups=[BEDROOM_FITOUT,ENTRY_FITOUT,ENSUITE_BATHROOM_FITOUT,GARAGE_FITOUT,OFFICE_FITOUT,...CHILDRENS_BEDROOM_FITOUTS,...HALLWAY_BUILT_IN_WARDROBES];
      for(const group of groups){
        const room=INTERIOR_ROOMS.find(r=>r.id===group.roomId)!;
        for(const mesh of scene.meshes.filter(m=>m.name.startsWith(group.id))){
          mesh.computeWorldMatrix(true);
          const b=mesh.getBoundingInfo().boundingBox;
          const x=b.centerWorld.x*1000+SCENE_CENTER_MM.x, y=SCENE_CENTER_MM.y-b.centerWorld.z*1000;
          expect(room.rectsMm.some(r=>x>=r.x0-10&&x<=r.x1+10&&y>=r.y0-10&&y<=r.y1+10),mesh.name).toBe(true);
        }
      }
      for(const id of ['C-HALL-BATH','C-PRIVATE-BED','C-BED-CLOSET','DOOR-101-102']){
        const spec=INTERIOR_DOORS.find(d=>d.id===id)!,registration=doors.find(d=>d.id===id)!;
        expect(registration.passage!.halfClearWidthM*2).toBeCloseTo(spec.widthMm/1000,6);
        const leaf=scene.meshes.find(m=>m.metadata?.doorId===id&&m.name.includes('animované krídlo'))!;
        registration.apply(0,0);leaf.computeWorldMatrix(true);
        const b=leaf.getBoundingInfo().boundingBox;
        expect(b.minimumWorld.x).toBeCloseTo(sceneXM(spec.startMm),5);
        expect(b.maximumWorld.x).toBeCloseTo(sceneXM(spec.startMm+spec.widthMm),5);
        registration.apply(1,0);leaf.computeWorldMatrix(true);
        expect(leaf.checkCollisions).toBe(true);
        if(spec.motion==='POCKET_SLIDING') expect(Math.abs(leaf.getBoundingInfo().boundingBox.centerWorld.z-sceneZM((spec.wallSpanMm[0]+spec.wallSpanMm[1])/2))).toBeLessThan(.001);
      }
      expect(scene.meshes.some(m=>m.name.startsWith(baseline.BEDROOM_FITOUT.id))).toBe(false);
    } finally {scene.dispose();engine.dispose();}
  });
});
