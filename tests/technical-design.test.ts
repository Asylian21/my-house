import { describe, expect, it } from 'vitest';
import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { Scene } from '@babylonjs/core/scene';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import { buildOpening, type OpeningBuildContext } from '../lib/babylon-openings';
import { buildInterior } from '../lib/babylon-interior';
import type { AnimatedDoorRegistration } from '../lib/babylon-doors';
import { HOUSE } from '../lib/twin-active-house';
import { SCENE_CENTER_MM } from '../lib/twin-render-frame';
import { INTERIOR_DOORS, INTERIOR_ROOMS, INTERIOR_WALLS, roomAreaM2 } from '../lib/twin-interior';
import { BATHROOM_FITOUT, SERVICE_CORE_REVISION, TECHNICAL_HEATING_FITOUT as heating, WC_FITOUT } from '../lib/technical-design';
import generated from '../lib/plan-geometry.generated.json';
import { contains, floorBoundary, inside, intersects } from './floor-plan-geometry';
import { hull } from '../scripts/plan-documentation/extract';

type Point=[number,number];
const distance=(p:Point,a:Point,b:Point)=>{
  const dx=b[0]-a[0],dy=b[1]-a[1],t=Math.max(0,Math.min(1,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy||1)));
  return Math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy);
};
function discHits(p:Point,r:number,poly:Point[]){
  let inside=false;
  for(let i=0,j=poly.length-1;i<poly.length;j=i++){
    const a=poly[i],b=poly[j];
    if(distance(p,a,b)<r-.5)return true;
    if((a[1]>p[1])!==(b[1]>p[1])&&p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0])inside=!inside;
  }
  return inside;
}
const polygon=(mesh:typeof generated.meshes[number]):Point[]=>mesh.polygon.split(' ').map(pair=>{const [x,y]=pair.split(',').map(Number);return [x,-y];});
function polygonDistance(p:Point,poly:Point[]){
  if(discHits(p,0,poly))return 0;
  return Math.min(...poly.map((v,i)=>distance(p,v,poly[(i+1)%poly.length])));
}
function polysOverlap(a:Point[],b:Point[]){
  for(const p of [a,b])for(let i=0;i<p.length;i++){
    const v=p[i],w=p[(i+1)%p.length],nx=-(w[1]-v[1]),ny=w[0]-v[0];
    const aa=a.map(q=>q[0]*nx+q[1]*ny),bb=b.map(q=>q[0]*nx+q[1]*ny);
    if(Math.min(Math.max(...aa),Math.max(...bb))-Math.max(Math.min(...aa),Math.min(...bb))<=.1*Math.hypot(nx,ny))return false;
  }
  return true;
}

describe('Service core dimensional and access contracts',()=>{
  it('has continuous 600 mm access from the kitchen door to storage, tank connections, boiler and hopper, including linings, nozzles and raised bases',()=>{
    const floors=INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-07')!.rectsMm,edges=floorBoundary([...floors]);
    const obstacles=generated.meshes.filter(m=>(m.name.startsWith('TECHNICAL')||m.name.startsWith('1.07 ·'))&&m.z0<1850&&m.z1>20
      &&(!m.name.includes('BUFFER-TANK')||/hrdlo|teplomer|ciferník/.test(m.name))).map(polygon);
    // 12. 9. 2026: the door sits in the load-bearing kitchen wall (25 881–26 681 × 10 712);
    // 600 mm stay free behind its whole width, then the routes fan out east of the tank.
    const door=INTERIOR_DOORS.find(d=>d.id==='DOOR-103-107')!;
    expect(door.wallSpanMm[0]).toBe(floors[1].y1);
    const entry:Point=[26331,10400];
    expect(entry[0]).toBeGreaterThan(door.startMm);
    expect(entry[0]).toBeLessThan(door.startMm+door.widthMm);
    const routes:Point[][]=[[entry,[26700,10100],[27100,10130]],[entry,[26700,10100],[26460,9812]],[entry,[26700,10100],[27000,9780]],[entry,[26700,10100],[27000,9660],[26500,9320],[26320,8940]]];
    for(const rect of [heating.storage.frontClearanceRectMm,heating.accumulator.serviceRectMm,heating.boiler.serviceRectMm])
      expect(routes.some(route=>route.some(p=>inside(rect,...p))),JSON.stringify(rect)).toBe(true);
    // The whole door width has 600 mm of free technical-room floor behind it: the
    // tank's jacket touches that depth only at the west jamb.
    const approach={x0:door.startMm,y0:door.wallSpanMm[0]-600,x1:door.startMm+door.widthMm,y1:door.wallSpanMm[0]};
    expect(floors.some(r=>contains(r,approach))).toBe(true);
    const tank=heating.accumulator,dx=door.startMm-tank.centerMm.x;
    expect(tank.centerMm.y+Math.sqrt((tank.outerDiameterMm/2)**2-dx**2)).toBeCloseTo(approach.y0,0);
    for(const m of generated.meshes.filter(m=>(m.name.startsWith('TECHNICAL')||m.name.startsWith('1.07 ·'))&&m.z0<2013&&m.z1>20&&!/akumulačná nádrž|veko|obruč|podstavec/.test(m.name)))
      expect(intersects(approach,m.rect),m.name).toBe(false);
    // Distance is 1-Lipschitz: a 0.5 mm margin and samples <=1 mm apart
    // also protect every point between samples, rather than only grid nodes.
    for(const route of routes)for(let i=1;i<route.length;i++){
      const a=route[i-1],b=route[i],steps=Math.ceil(Math.hypot(a[0]-b[0],a[1]-b[1]));
      for(let j=0;j<=steps;j++){
        const p:Point=[a[0]+(b[0]-a[0])*j/steps,a[1]+(b[1]-a[1])*j/steps];
        const clear=Math.min(Math.hypot(p[0]-heating.accumulator.centerMm.x,p[1]-heating.accumulator.centerMm.y)-heating.accumulator.outerDiameterMm/2,
          ...obstacles.map(poly=>polygonDistance(p,poly)),...edges.map(([x0,y0,x1,y1])=>distance(p,[x0,y0],[x1,y1])));
        expect(floors.some(r=>inside(r,...p))&&clear>=300.5,`600 mm route blocked at ${p}; radius clearance ${clear}`).toBe(true);
      }
    }
  });
  it('enlarges the WC without overlapping room floors or reducing full-size laundry appliances',()=>{
    const wc=INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-06')!;
    expect(roomAreaM2(wc)).toBeCloseTo(3.4182,6);
    const tech=INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-07')!;
    // 12. 9. 2026: without the 1 680 × 699 mm protrusion north of the load-bearing kitchen wall.
    expect(roomAreaM2(tech)).toBeCloseTo(7.494857,6);
    const floors=INTERIOR_ROOMS.flatMap(r=>r.rectsMm.map(rect=>({id:r.id,rect})));
    floors.forEach((a,i)=>floors.slice(i+1).forEach(b=>expect(intersects(a.rect,b.rect),`${a.id}/${b.id}`).toBe(false)));
    for(const a of BATHROOM_FITOUT.builtIn.appliances){
      expect(a.footprintMm.x1-a.footprintMm.x0).toBe(600);
      expect(a.footprintMm.y1-a.footprintMm.y0).toBe(600);
      expect(contains(BATHROOM_FITOUT.builtIn.footprintMm,a.footprintMm)).toBe(true);
    }
    const sanitary=generated.meshes.filter(m=>m.name.startsWith(WC_FITOUT.id));
    expect(sanitary.length).toBeGreaterThan(10);
    for(const m of sanitary)expect(intersects(WC_FITOUT.clearFloorRectMm,m.rect),m.name).toBe(false);
  });
  it('keeps the real boiler assembly inside the catalogue envelope and the tank body at its verified size',()=>{
    const boiler=generated.meshes.filter(m=>m.name.startsWith(heating.id)&&!m.name.includes('BUFFER-TANK'));
    expect(boiler.length).toBeGreaterThan(30);
    for(const m of boiler){
      expect(contains(heating.boiler.assemblyFootprintMm,m.rect),m.name).toBe(true);
      expect(m.z1,m.name).toBeLessThanOrEqual(1441.1);
    }
    const west=Math.min(...boiler.map(m=>m.rect.x0))-25253;
    const east=27500-Math.max(...boiler.map(m=>m.rect.x1));
    expect(west).toBe(759);
    expect(east).toBe(250);
    // Explicit client layout revision: reduced gaps must never silently pass as manufacturer-compliant.
    expect(heating.boiler.clearanceStatus).toBe('BELOW_MANUFACTURER_RECOMMENDATION');
    expect(heating.boiler.professionalInstallationReviewRequired).toBe(true);
    expect(east).toBeLessThan(heating.boiler.manufacturerSideAndRearRecommendationMm);
    const body=boiler.find(m=>m.name.endsWith('kombinované teleso drevo alebo pelety'))!;
    const flue=boiler.find(m=>m.name.includes('koncept napojenia dymovodu'))!;
    expect(body.rect.y0-7751).toBe(250);
    expect(flue.rect.y0-7751).toBe(37);
    const tank=generated.meshes.find(m=>m.name.endsWith('akumulačná nádrž 1000 l'))!;
    const zone=heating.accumulator.placementZoneMm;
    expect((tank.rect.x0+tank.rect.x1)/2).toBe((zone.x0+zone.x1)/2);
    expect((tank.rect.y0+tank.rect.y1)/2).toBe((zone.y0+zone.y1)/2);
    expect(tank.rect.x1-tank.rect.x0).toBe(1106);
    expect(tank.rect.y1-tank.rect.y0).toBe(1106);
    expect(generated.meshes.find(m=>m.name.endsWith('horné izolované veko'))!.z1).toBe(1913);
  });
  it('fits three supported pellet sacks and a hanging stick vacuum in the shallow entry cabinet',()=>{
    const parts=generated.meshes.filter(m=>m.name.startsWith(heating.storage.id));
    const panels=parts.filter(m=>m.name.includes('STORAGE-CABINET'));
    const contents=parts.filter(m=>/PELLET-BAG|VACUUM/.test(m.name));
    const bags=contents.filter(m=>m.name.includes('PELLET-BAG'));
    expect(bags).toHaveLength(3);
    for(const bag of bags)expect(panels.some(p=>/polica/.test(p.name)&&Math.abs(p.z1-bag.z0)<.1&&contains(p.rect,bag.rect))).toBe(true);
    for(const m of contents){
      expect(contains(heating.storage.footprintMm,m.rect),m.name).toBe(true);
      for(const panel of panels)if(m.z0<panel.z1-.1&&m.z1>panel.z0+.1)expect(intersects(m.rect,panel.rect),`${m.name}/${panel.name}`).toBe(false);
    }
    const vacuum=contents.filter(m=>m.name.includes('VACUUM'));
    expect(Math.max(...vacuum.map(m=>m.z1))-Math.min(...vacuum.map(m=>m.z0))).toBe(1105);
    for(const p of panels)expect(intersects(p.rect,heating.boiler.serviceRectMm),p.name).toBe(false);
    // 12. 9. 2026: the cabinet backs onto the load-bearing kitchen wall east of the
    // door; the boiler's front strip ends at its front, 1 794 mm from the body.
    const wall=INTERIOR_WALLS.find(w=>w.id==='C-KITCHEN-BEARING-WALL-E')!.rectMm;
    const door=INTERIOR_DOORS.find(d=>d.id==='DOOR-103-107')!;
    expect(heating.storage.footprintMm.y1).toBe(wall.y0);
    expect(heating.storage.footprintMm.x0).toBeGreaterThanOrEqual(wall.x0);
    expect(heating.storage.footprintMm.x1).toBeLessThanOrEqual(wall.x1);
    expect(heating.storage.footprintMm.x0-(door.startMm+door.widthMm)).toBe(79);
    expect(heating.hydraulicReserve.footprintMm).toEqual(heating.storage.footprintMm);
    expect(heating.storage.frontClearanceRectMm).toEqual({...heating.storage.footprintMm,y0:heating.storage.footprintMm.y0-600,y1:heating.storage.footprintMm.y0});
    expect(heating.boiler.serviceRectMm.y1).toBe(heating.storage.footprintMm.y0);
    expect(heating.boiler.serviceRectMm.y1-heating.boiler.body.footprintMm.y1).toBe(heating.boiler.frontServiceClearanceMm);
    expect(heating.boiler.frontServiceClearanceMm).toBe(1794);
    expect(heating.boiler.previousFrontServiceClearanceMm).toBe(2000);
    const tech=INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-07')!.rectsMm;
    // The stacked 25 243–27 510 rectangles share their x range, so corners inside the union suffice.
    for(const r of [heating.storage.footprintMm,heating.storage.frontClearanceRectMm,heating.boiler.serviceRectMm,heating.accumulator.serviceRectMm])
      expect([[r.x0,r.y0],[r.x1,r.y0],[r.x0,r.y1],[r.x1,r.y1]].every(([x,y])=>tech.some(floor=>inside(floor,x,y))),JSON.stringify(r)).toBe(true);
    expect(intersects(heating.storage.frontClearanceRectMm,heating.accumulator.serviceRectMm)).toBe(false);
  });
  it('keeps the moved tank centred in its zone, clear of the WC wall lining and the hopper approach, with its connections facing east',()=>{
    const tank=heating.accumulator,r=tank.outerDiameterMm/2;
    expect(tank.centerMm).toEqual({x:25416.5,y:9812});
    expect(tank.placementZoneMm).toEqual({x0:24831,y0:8922,x1:26002,y1:10702});
    expect(tank.centerMm.x-r).toBe(24863.5);
    // 10 mm lining on the WC wall (24 821) and the hopper's west face (26 012) bound the zone.
    expect(tank.placementZoneMm.x0-INTERIOR_WALLS.find(w=>w.id==='IW-WC-EAST')!.rectMm.x1).toBe(10);
    expect(heating.boiler.hopper.footprintMm.x0-tank.placementZoneMm.x1).toBe(10);
    expect(tank.centerMm.y-r).toBeGreaterThan(heating.boiler.hopper.footprintMm.y1);
    expect(tank.connectionAzimuthDegrees).toBe(0);
    expect(tank.serviceRectMm.x0-(tank.centerMm.x+r+tank.connectionProjectionMm)).toBeCloseTo(10.5,6);
    expect(tank.serviceRectMm.x1-tank.serviceRectMm.x0).toBe(600);
    const body=generated.meshes.find(m=>m.name.endsWith('akumulačná nádrž 1000 l'))!;
    expect(body.rect).toEqual({x0:24863.5,y0:9259,x1:25969.5,y1:10365});
    const nozzles=generated.meshes.filter(m=>/hydraulické hrdlo/.test(m.name));
    expect(nozzles).toHaveLength(4);
    for(const n of nozzles){
      expect(n.rect.x0).toBeGreaterThan(tank.centerMm.x);
      expect(n.rect.x1).toBeCloseTo(tank.centerMm.x+r+tank.connectionProjectionMm,0);
      expect(Math.abs((n.rect.y0+n.rect.y1)/2-tank.centerMm.y)).toBeCloseTo(245,0);
    }
  });
  it('opens the single 900 mm leaf of EAST-03 outward through a collision-free sweep, swings the kitchen door into the kitchen and records that the tank no longer passes',()=>{
    const engine=new NullEngine({renderWidth:128,renderHeight:128,textureSize:128,deterministicLockstep:false,lockstepMaxSteps:1}),scene=new Scene(engine);
    scene.useRightHandedSystem=true;
    const material=new PBRMaterial('transport-test',scene),doors:AnimatedDoorRegistration[]=[];
    const identity:OpeningBuildContext['register']=mesh=>mesh;
    const context:OpeningBuildContext={scene,materials:new Proxy({} as OpeningBuildContext['materials'],{get:()=>material}),register:identity,realisticOnly:identity,castShadow:identity,appearance:mesh=>mesh,registerAnimatedDoor:d=>doors.push(d)};
    try{
      const opening=HOUSE.facades.east.openings.find(o=>o.id==='EAST-03')!;
      // 12. 9. 2026: 900 mm single leaf for the statics of the east facade beside the load-bearing kitchen wall.
      expect(opening).toEqual({id:'EAST-03',startYmm:9300,widthMm:900,heightMm:2250,sillMm:0});
      expect(SERVICE_CORE_REVISION.exteriorDoorRevision).toMatchObject({previousWidthMm:1700,layout:'SINGLE_LEAF_OUTWARD',hinge:'SOUTH_JAMB'});
      expect(INTERIOR_WALLS.find(w=>w.id==='C-KITCHEN-BEARING-WALL-E')!.rectMm.y0-(opening.startYmm+opening.widthMm)).toBe(512);
      buildOpening(context,{name:opening.id,axis:'X',faceMm:HOUSE.facades.east.faceXmm,centerMm:opening.startYmm+opening.widthMm/2,widthMm:opening.widthMm,heightMm:opening.heightMm,sillMm:0,outward:1,wallThicknessMm:530,kind:'door',frameMaterial:material,curtains:false,interaction:{id:opening.id,label:'Technická',layout:SERVICE_CORE_REVISION.exteriorDoorRevision.layout}});
      expect(doors).toHaveLength(1);
      expect(doors[0].passage!.halfClearWidthM*2).toBeCloseTo(heating.accumulator.transport.clearWidthMm/1000,6);
      expect(scene.meshes.some(m=>/svetlík|transportné krídlo/.test(m.name))).toBe(false);
      const leaves=scene.meshes.filter(m=>m.metadata?.dynamicCameraOccluder&&m.name.includes('plné krídlo otvárané von'));
      expect(leaves).toHaveLength(1);
      const shape=(mesh:typeof leaves[number])=>{
        const matrix=mesh.computeWorldMatrix(true),v=mesh.getVerticesData('position')!,points:Point[]=[];let bottom=Infinity,top=-Infinity;
        for(let i=0;i<v.length;i+=3){const p=Vector3.TransformCoordinates(new Vector3(v[i],v[i+1],v[i+2]),matrix);points.push([p.x*1000+SCENE_CENTER_MM.x,SCENE_CENTER_MM.y-p.z*1000]);bottom=Math.min(bottom,p.y*1000);top=Math.max(top,p.y*1000);}
        return {name:mesh.name,polygon:hull(points) as Point[],bottom,top};
      };
      // Closed, the leaf fills the frame between the 78 mm jambs.
      const closed=shape(leaves[0]);
      expect(Math.min(...closed.polygon.map(p=>p[1]))).toBeCloseTo(opening.startYmm+78+3,0);
      expect(Math.max(...closed.polygon.map(p=>p[1]))).toBeCloseTo(opening.startYmm+opening.widthMm-78-3,0);
      const frames=scene.meshes.filter(m=>m.name.includes('zárubňa')).map(shape);
      for(let step=0;step<=180;step++){
        doors[0].apply(step/180,0);
        for(const leaf of leaves.map(shape))for(const frame of frames){
          if(leaf.top>frame.bottom+.1&&leaf.bottom<frame.top-.1)expect(polysOverlap(leaf.polygon,frame.polygon),`${leaf.name}/${frame.name} at ${step/2} degrees`).toBe(false);
        }
      }
      // Open, it stands outside the facade beside the south jamb, leaving the north side of the approach free.
      const open=shape(leaves[0]);
      expect(Math.max(...open.polygon.map(p=>p[0]))).toBeGreaterThan(HOUSE.facades.east.faceXmm+600);
      expect(Math.max(...open.polygon.map(p=>p[1]))).toBeLessThan(opening.startYmm+78+60);
      const exteriorMeshes=[...scene.meshes],interiorDoors:AnimatedDoorRegistration[]=[];
      buildInterior({scene,anisotropy:1,wall:material,soffit:material,glassFrame:material,chimneyMetal:material,timber:material,
        register:identity,realisticOnly:identity,castShadow:identity,registerAnimatedDoor:d=>interiorDoors.push(d)});
      const kitchenDoor=interiorDoors.find(d=>d.id==='DOOR-103-107')!;
      expect(kitchenDoor).toBeDefined();
      const kitchenSpec=INTERIOR_DOORS.find(d=>d.id==='DOOR-103-107')!;
      const kitchenMeshes=scene.meshes.filter(m=>m.name.startsWith(kitchenSpec.label));
      expect(kitchenMeshes.length).toBeGreaterThan(3);
      // The kitchen door swings into the kitchen through its whole arc without touching the
      // kitchen run, the bearing wall pieces or the pellet cabinet, and never enters 1.07.
      const kitchenMoving=scene.meshes.filter(m=>m.metadata?.doorId===kitchenDoor.id);
      const kitchenObstacles=scene.meshes.filter(m=>(m.name.startsWith(kitchenSpec.label)&&!m.metadata?.doorId)||m.name.startsWith('KITCHEN-RUN')||/C-KITCHEN-BEARING-WALL/.test(m.name)||m.name.startsWith(heating.storage.id)).map(shape);
      expect(kitchenMoving.length).toBeGreaterThanOrEqual(3);
      for(let step=0;step<=360;step++){
        kitchenDoor.apply(step/360,0);
        for(const m of kitchenMoving.map(shape)){
          expect(Math.min(...m.polygon.map(p=>p[1])),`${m.name} at ${step/4} degrees enters 1.07`).toBeGreaterThanOrEqual(kitchenSpec.wallSpanMm[0]-.5);
          for(const o of kitchenObstacles)if(m.top>o.bottom+.1&&m.bottom<o.top-.1)expect(polysOverlap(m.polygon,o.polygon),`${m.name}/${o.name} at ${step/4} degrees`).toBe(false);
        }
      }
      kitchenDoor.apply(1,0);
      const wcDoor=interiorDoors.find(d=>d.id==='DOOR-102-106')!;
      expect(wcDoor.kind).toBe('HINGED');
      const wcSpec=INTERIOR_DOORS.find(d=>d.id===wcDoor.id)!;
      const wcMoving=scene.meshes.filter(m=>m.metadata?.doorId===wcDoor.id);
      const wcObstacles=scene.meshes.filter(m=>(m.name.startsWith(wcSpec.label)&&!m.metadata?.doorId)||m.name.startsWith(WC_FITOUT.id)).map(shape);
      expect(wcMoving.length).toBeGreaterThanOrEqual(3);
      for(let step=0;step<=360;step++){
        wcDoor.apply(step/360,0);
        for(const m of wcMoving.map(shape))for(const o of wcObstacles)
          if(m.top>o.bottom+.1&&m.bottom<o.top-.1)expect(polysOverlap(m.polygon,o.polygon),`${m.name}/${o.name} at ${step/4} degrees`).toBe(false);
      }
      // Neither the insulated nor the bare tank passes the 900 mm opening; the model
      // says so instead of drawing a route, and keeps the superseded route for reference.
      const transport=heating.accumulator.transport;
      expect(transport).toMatchObject({openingId:'EAST-03',openingWidthMm:opening.widthMm,clearWidthMm:648,passesInsulated:false,passesWithoutInsulation:false,method:'PLACE_BEFORE_ROOF_OR_SPLIT_TANK'});
      expect(transport.clearWidthMm).toBe(opening.widthMm-2*78-96);
      expect(heating.accumulator.outerDiameterMm).toBeGreaterThan(opening.widthMm);
      expect(heating.accumulator.transportDiameterWithoutInsulationMm).toBeGreaterThan(transport.clearWidthMm);
      expect('transportRouteMm' in heating.accumulator).toBe(false);
      expect(transport.previousRouteMm.at(-1)).toEqual({x:25771.5,y:9812});
      // The frames of the open door and the facade masonry around it would stop even the bare tank on the old route.
      const jambs=[...exteriorMeshes].map(shape).filter(m=>m.top>100.1&&m.bottom<2013&&/zárubňa/.test(m.name));
      const entryPoint:Point=[HOUSE.facades.east.faceXmm-265,opening.startYmm+opening.widthMm/2];
      expect(jambs.some(j=>discHits(entryPoint,heating.accumulator.transportDiameterWithoutInsulationMm/2,j.polygon))).toBe(true);
    }finally{scene.dispose();engine.dispose();}
  },30000);
});
