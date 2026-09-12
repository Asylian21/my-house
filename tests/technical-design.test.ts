import { describe, expect, it } from 'vitest';
import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { Scene } from '@babylonjs/core/scene';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { Vector3 } from '@babylonjs/core/Maths/math.vector';
import { buildOpening, type OpeningBuildContext } from '../lib/babylon-openings';
import { buildInterior } from '../lib/babylon-interior';
import type { AnimatedDoorRegistration } from '../lib/babylon-doors';
import { HOUSE, SIDE_ENTRY_APPROACH } from '../lib/twin-active-house';
import { SITE_SURFACES } from '../lib/twin-site';
import { SCENE_CENTER_MM } from '../lib/twin-render-frame';
import { INTERIOR_DOORS, INTERIOR_ROOMS, INTERIOR_WALLS, roomAreaM2 } from '../lib/twin-interior';
import { BATHROOM_FITOUT, HEATING_LAYOUT_IDS, HEATING_LAYOUTS, SERVICE_CORE_REVISION, TECHNICAL_HEATING_FITOUT as heating, WC_FITOUT } from '../lib/technical-design';
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
  it.each(HEATING_LAYOUT_IDS)('has continuous 600 mm access in heating variant %s, including linings, nozzles and raised bases',(layout)=>{
    const heating=HEATING_LAYOUTS[layout];
    const technical=INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-07')!.rectsMm;
    const door=INTERIOR_DOORS.find(d=>d.id==='DOOR-103-107')!;
    // Include the doorway and the kitchen approach, then the real 60 mm jambs.
    // This proves entry through the opening, not merely circulation from a point already inside.
    const floors=[...technical,{x0:door.startMm,y0:door.wallSpanMm[0],x1:door.startMm+door.widthMm,y1:11550}];
    const edges=floorBoundary(floors);
    const obstacles=generated.meshes.filter(m=>(!m.heatingLayout||m.heatingLayout===layout)&&((m.name.startsWith('TECHNICAL')||m.name.startsWith('1.07 '))
      &&(!m.name.includes('BUFFER-TANK')||/hrdlo|teplomer|ciferník/.test(m.name))
      ||m.name.startsWith(door.label)&&m.name.includes('zárubňa'))&&m.z0<1850&&m.z1>20).map(polygon);
    expect(door.wallSpanMm[0]).toBe(technical[0].y1);
    const entry:Point=[26281,11100];
    const approach:Point[]=[entry,[26281,10401],[26400,10402],[26720,10385],[26720,10050],[26710,10050]];
    const aroundHopper:Point[]=[...approach,[26720,9500],[26720,9000],[26720,8500],[26720,8195],[26500,8130]];
    const routes:Point[][]=[
      [...aroundHopper,[heating.boiler.hopper.fillingStandingPointMm.x,heating.boiler.hopper.fillingStandingPointMm.y]],
      [[26720,8500],[26900,8100]],
      [[26720,9500],[26560,9950]],
      [[26720,9500],[26320,9460]],
      [[27180,9450],[26720,9450],[26720,10050],[26710,10050]],
    ];
    for(const rect of [heating.storage.frontClearanceRectMm,heating.accumulator.serviceRectMm,heating.boiler.serviceRectMm,heating.shelving.frontClearanceRectMm])
      expect(routes.some(route=>route.some(p=>inside(rect,...p))),JSON.stringify(rect)).toBe(true);
    const spawn=INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-07')!.standingPointMm;
    expect(routes.some(route=>route.some(([x,y])=>x===spawn.x&&y===spawn.y))).toBe(true);
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
    expect(tech.rectsMm).toEqual([{x0:24821,y0:7741,x1:27510,y1:10712}]);
    expect(roomAreaM2(tech)).toBeCloseTo(7.989019,6);
    const bath=INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-05')!;
    expect(roomAreaM2(bath)).toBeCloseTo(6.976971,6);
    const partition=INTERIOR_WALLS.find(w=>w.rectMm.y0===7741&&w.rectMm.x0===SERVICE_CORE_REVISION.bathroomEastMm)!;
    const wcWall=INTERIOR_WALLS.find(w=>w.id==='IW-WC-EAST')!;
    expect([partition.rectMm.x0,partition.rectMm.x1]).toEqual([wcWall.rectMm.x0,wcWall.rectMm.x1]);
    expect(BATHROOM_FITOUT.builtIn.footprintMm.x1-BATHROOM_FITOUT.builtIn.footprintMm.x0).toBe(1899);
    expect(BATHROOM_FITOUT.applianceServiceRectMm.y1-BATHROOM_FITOUT.applianceServiceRectMm.y0).toBe(900);
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
  it.each(HEATING_LAYOUT_IDS)('keeps the real rotated boiler and tank at the verified catalogue sizes in %s',(layout)=>{
    const heating=HEATING_LAYOUTS[layout];
    const boiler=generated.meshes.filter(m=>m.name.startsWith(heating.id)&&!m.name.includes('BUFFER-TANK')&&!m.name.includes('BOILER-FLUE'));
    expect(boiler.length).toBeGreaterThan(30);
    for(const m of boiler){
      expect(contains(heating.boiler.assemblyFootprintMm,m.rect),m.name).toBe(true);
      expect(m.z1,m.name).toBeLessThanOrEqual(1441.1);
    }
    const body=boiler.find(m=>m.name.endsWith('kombinované teleso drevo alebo pelety'))!;
    expect(body.rect).toEqual(heating.boiler.body.footprintMm);
    expect(body.rect.x0-24831).toBe(420);
    expect(heating.boiler.front).toBe('EAST');
    expect(heating.boiler.clearanceStatus).toBe('BELOW_MANUFACTURER_RECOMMENDATION');
    expect(heating.boiler.professionalInstallationReviewRequired).toBe(true);
    expect(heating.boiler.frontServiceClearanceMm).toBe(1593);
    expect(heating.boiler.frontServiceClearanceMm).toBeLessThan(heating.boiler.manufacturerFrontRecommendationMm);
    const tank=generated.meshes.find(m=>m.name.startsWith(heating.id)&&m.name.includes('akumulačná nádrž'))!;
    expect(tank.rect.x1-tank.rect.x0).toBe(layout==='A'?1106:958);
    expect(tank.rect.y1-tank.rect.y0).toBe(layout==='A'?1106:958);
    expect(generated.meshes.find(m=>m.name.startsWith(heating.id)&&m.name.endsWith('horné izolované veko'))!.z1).toBe(layout==='A'?1913:2106);
    expect(heating.boiler.catalogueSizeMm).toEqual({width:layout==='A'?1238:1188,depth:layout==='A'?1298:1296,height:1391});
    const motor=boiler.find(m=>m.name.endsWith('motor s prevodovkou'))!;
    expect(motor.rect.x1).toBe(heating.boiler.assemblyFootprintMm.x1);
    for(const part of boiler.filter(m=>/PELLET-AUGER|PELLET-FEED-HOSE/.test(m.name)))
      expect(polysOverlap(polygon(part),polygon(body)),part.name).toBe(false);

  });
  it.each(HEATING_LAYOUT_IDS)('faces the actual doors east and reserves the illustrated open-door width clear of the room in %s',(layout)=>{
    const h=HEATING_LAYOUTS[layout],b=h.boiler,body=b.body.footprintMm;
    const parts=generated.meshes.filter(m=>m.heatingLayout===layout);
    const doors=parts.filter(m=>m.name.startsWith(h.id)&&/ · (horné prikladacie|stredné spaľovacie|spodné popolníkové) dvierka/.test(m.name));
    expect(doors).toHaveLength(3);
    for(const door of doors){
      expect(door.rect.x0).toBeGreaterThan(body.x1);
      expect(door.rect.y0).toBeGreaterThan(body.y0);
      expect(door.rect.y1).toBeLessThan(body.y1);
    }
    const outlet=parts.find(m=>m.name.includes('výrobné zadné hrdlo'))!;
    expect(outlet.rect.x1).toBe(body.x0);
    expect(b.hopper.footprintMm.y1).toBeLessThan(body.y0);
    expect(b.hopper.footprintMm.y0-7751).toBe(100);
    expect(b.mirrorX).toBe(false);
    expect(b.doorState).toBe('CLOSED');
    const burner=parts.find(m=>m.name.endsWith('automaticky čistený peletový horák'))!;
    expect(burner.rect.y1-burner.rect.y0).toBe(220);
    expect(burner.rect.x1-burner.rect.x0).toBe(350);
    expect(burner.z1-burner.z0).toBe(260);
    expect(burner.rect.x1-body.x1).toBe(429);
    expect(b.burner.shapeBasis).toBe('DRAWING_PROPORTION_ESTIMATE');
    const neck=parts.find(m=>m.name.endsWith('pripojovací krčok zatvorených dvierok'))!;
    const lowerDoor=doors.find(m=>m.name.endsWith('spodné popolníkové dvierka'))!;
    expect(neck.z0).toBeGreaterThan(lowerDoor.z0);
    expect(neck.z1).toBeLessThan(lowerDoor.z1);
    expect(parts.some(m=>m.name.includes('BOILER-BASE')&&m.name.endsWith('horák'))).toBe(false);
    expect(b.doorSideExtensionMm).toBe(b.openDoorEnvelopeWidthMm-b.catalogueSizeMm.width);
    expect(b.doorSideExtensionMm).toBe(layout==='A'?425:378);
    expect(b.modeledSideClearanceMm).toBe(layout==='A'?407:605);
    // Regression: 100 mm beside the SOUTH-facing body cannot fit the illustrated C1 opening.
    expect(b.doorSideExtensionMm).toBeGreaterThan(100);
    expect(b.doorOpeningReserveMm.y0-7751).toBe(layout==='A'?375:422);
    expect(contains({x0:24831,y0:7751,x1:27500,y1:10702},b.doorOpeningReserveMm)).toBe(true);
    for(const item of parts.filter(m=>m.name.includes('BUFFER-TANK')||m.name.startsWith(h.shelving.id)||m.name.startsWith(h.storage.id)))
      expect(polysOverlap([[b.doorOpeningReserveMm.x0,b.doorOpeningReserveMm.y0],[b.doorOpeningReserveMm.x1,b.doorOpeningReserveMm.y0],[b.doorOpeningReserveMm.x1,b.doorOpeningReserveMm.y1],[b.doorOpeningReserveMm.x0,b.doorOpeningReserveMm.y1]],polygon(item)),item.name).toBe(false);
    // Room-space verification does not prove operation with the detachable hose/burner connected.
    expect(b.doorOpeningStatus).toBe('ROOM_ENVELOPE_ONLY_ACCESSORIES_REQUIRE_SERVICE_PROCEDURE');
    expect(b.feeder.installationStatus).toBe('POSITION_LENGTH_AND_INCLINE_REQUIRE_SUPPLIER_CONFIRMATION');
  });
  it.each(HEATING_LAYOUT_IDS)('fits the service cabinet contents and free service zones in %s',(layout)=>{
    const heating=HEATING_LAYOUTS[layout];
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
    const wall=INTERIOR_WALLS.find(w=>w.id==='IW-BATH-105-SOUTH-E')!.rectMm;
    expect(heating.storage.footprintMm.y0-wall.y1).toBe(10);
    expect(heating.storage.front).toBe('WEST');
    expect(heating.storage.footprintMm.x0).toBeGreaterThanOrEqual(wall.x0);
    expect(heating.storage.footprintMm.x1).toBeLessThanOrEqual(wall.x1);
    expect(heating.hydraulicReserve.footprintMm).toEqual(heating.storage.footprintMm);
    expect(heating.storage.frontClearanceRectMm).toEqual({...heating.storage.footprintMm,x0:heating.storage.footprintMm.x0-600,x1:heating.storage.footprintMm.x0});
    // Check the actual rotated tambour face and back, not just the declared orientation.
    const fronts=panels.filter(p=>p.name.includes('roletové čelo'));
    expect(fronts.length).toBeGreaterThan(10);
    for(const front of fronts)expect(front.rect.x0).toBe(heating.storage.footprintMm.x0);
    expect(panels.find(p=>p.name.includes('chrbát'))!.rect.x1).toBe(heating.storage.footprintMm.x1);
    expect(heating.boiler.serviceRectMm.x1).toBe(27500);
    expect(heating.boiler.serviceRectMm.x1-heating.boiler.body.footprintMm.x1).toBe(heating.boiler.frontServiceClearanceMm);
    expect(heating.boiler.serviceRectMm.x1-heating.boiler.burner.footprintMm.x1).toBe(heating.boiler.clearFloorBeyondBurnerMm);
    const tech=INTERIOR_ROOMS.find(r=>r.id==='ROOM-1-07')!.rectsMm;
    // Every service allocation stays in the new rectangular room.
    for(const r of [heating.storage.footprintMm,heating.storage.frontClearanceRectMm,heating.boiler.serviceRectMm,heating.accumulator.serviceRectMm])
      expect([[r.x0,r.y0],[r.x1,r.y0],[r.x0,r.y1],[r.x1,r.y1]].every(([x,y])=>tech.some(floor=>inside(floor,x,y))),JSON.stringify(r)).toBe(true);

  });
  it.each(HEATING_LAYOUT_IDS)('retains the stock outlet, rises beside the west wall and fits five accessible shelves in %s',(layout)=>{
    const h=HEATING_LAYOUTS[layout],parts=generated.meshes.filter(m=>m.heatingLayout===layout);
    const outlet=parts.find(m=>m.name.includes('výrobné zadné hrdlo'))!;
    const rise=parts.find(m=>m.name.includes('BOILER-FLUE'))!;
    expect(outlet.rect.x1-outlet.rect.x0).toBe(139);
    expect(outlet.rect.x1).toBe(h.boiler.body.footprintMm.x0);
    expect(rise.z1).toBe(2600);
    expect(rise.rect.y1-rise.rect.y0).toBe(159);
    expect(rise.rect.x0-24831).toBe(h.flue.wallClearanceMm);
    expect(h.flue.wallClearanceMm).toBeGreaterThanOrEqual(100);
    expect(rise.rect.x1).toBeGreaterThanOrEqual(outlet.rect.x0);
    expect(rise.rect.x0).toBeLessThan(outlet.rect.x0);
    expect(h.flue.fittingSelectionStatus).toBe('COMPACT_ELBOW_REQUIRES_SUPPLIER_CONFIRMATION');
    expect(h.flue.termination).toBe('ROOM_CEILING_CONNECTION_RESERVE');
    expect(h.boiler.hopper.footprintMm.x0).toBe(25181);
    const shelves=parts.filter(m=>m.name.startsWith(h.shelving.id));
    expect(shelves.filter(m=>/ · polica \d$/.test(m.name))).toHaveLength(5);
    const room={x0:24831,y0:7751,x1:27500,y1:10702};
    for(const piece of shelves){
      expect(contains(room,piece.rect),piece.name).toBe(true);
      expect(contains(h.shelving.footprintMm,piece.rect),piece.name).toBe(true);
      expect(intersects(h.boiler.serviceRectMm,piece.rect),piece.name).toBe(false);
      expect(piece.z1).toBeLessThanOrEqual(h.shelving.heightMm);
    }
    expect(h.shelving.footprintMm.y0-(SERVICE_CORE_REVISION.exteriorDoor.startYmm+SERVICE_CORE_REVISION.exteriorDoor.widthMm)).toBe(42);
    expect(h.shelving.footprintMm.x0-h.shelving.frontClearanceRectMm.x0).toBe(600);
  });
  it('connects the relocated door to the existing boundary gate through a splayed approach',()=>{
    const face=HOUSE.facades.east.faceXmm;
    const door=SERVICE_CORE_REVISION.exteriorDoor;
    const houseEdge=SIDE_ENTRY_APPROACH.polygonMm.filter(p=>Math.abs(p.x-face)<=2);
    expect(houseEdge).toHaveLength(2);
    expect(Math.min(...houseEdge.map(p=>p.y))).toBeLessThan(door.startYmm-400);
    expect(Math.max(...houseEdge.map(p=>p.y))).toBeGreaterThan(door.startYmm+door.widthMm+400);
    const gateEnd=(points:readonly {x:number;y:number}[])=>points.filter(p=>p.x>30000);
    expect(gateEnd(SIDE_ENTRY_APPROACH.polygonMm)).toEqual(gateEnd(SITE_SURFACES.sideEntryApproach.polygonMm));
    expect(SIDE_ENTRY_APPROACH.roadReservePolygonMm).toEqual(SITE_SURFACES.sideEntryApproach.roadReservePolygonMm);
    expect(SIDE_ENTRY_APPROACH.areaM2).toBeGreaterThan(10);
  });
  it.each(HEATING_LAYOUT_IDS)('groups tank %s above the boiler along the west wall with fittings clear of equipment',(layout)=>{
    const h=HEATING_LAYOUTS[layout],tank=h.accumulator,r=tank.outerDiameterMm/2;
    expect(tank.centerMm.x-r).toBe(24931);
    expect(tank.centerMm.y+r).toBe(10602);
    expect(tank.centerMm.y-r).toBeGreaterThan(h.boiler.body.footprintMm.y1);
    const parts=generated.meshes.filter(m=>m.name.startsWith(h.id)&&m.name.includes('BUFFER-TANK'));
    const nozzles=parts.filter(m=>/hydraulické hrdlo/.test(m.name));
    expect(nozzles).toHaveLength(4);
    const other=generated.meshes.filter(m=>(m.name.startsWith(h.id)&&!m.name.includes('BUFFER-TANK'))||m.name.startsWith(h.storage.id));
    for(const m of parts){
      expect(contains({x0:24831,y0:7751,x1:27500,y1:10702},m.rect),m.name).toBe(true);
      for(const o of other)if(m.z0<o.z1&&m.z1>o.z0)expect(polysOverlap(polygon(m),polygon(o)),`${m.name}/${o.name}`).toBe(false);
    }
    for(const n of nozzles){
      expect(n.rect.x0).toBeGreaterThan(tank.centerMm.x);
      const angle=tank.connectionAzimuthDegrees*Math.PI/180;
      const local=polygon(n).map(([x,y])=>{const dx=x-tank.centerMm.x,dy=y-tank.centerMm.y;return [Math.cos(angle)*dx+Math.sin(angle)*dy,-Math.sin(angle)*dx+Math.cos(angle)*dy];});
      expect(Math.max(...local.map(p=>p[0]))).toBeCloseTo(r+tank.connectionProjectionMm,-1);
    }
  });
  it('opens the single 900 mm leaf of EAST-03 outward through a collision-free sweep, swings the kitchen door into the kitchen and distinguishes modeled door clearance from bare tank transport',()=>{
    const engine=new NullEngine({renderWidth:128,renderHeight:128,textureSize:128,deterministicLockstep:false,lockstepMaxSteps:1}),scene=new Scene(engine);
    scene.useRightHandedSystem=true;
    const material=new PBRMaterial('transport-test',scene),doors:AnimatedDoorRegistration[]=[];
    const identity=(mesh:Parameters<OpeningBuildContext['register']>[0])=>mesh;
    const context:OpeningBuildContext={scene,materials:new Proxy({} as OpeningBuildContext['materials'],{get:()=>material}),register:identity,realisticOnly:identity,castShadow:identity,appearance:mesh=>mesh,registerAnimatedDoor:d=>doors.push(d)};
    try{
      const opening=HOUSE.facades.east.openings.find(o=>o.id==='EAST-03')!;
      // 12. 9. 2026: 900 mm single leaf for the statics of the east facade beside the load-bearing kitchen wall.
      expect(opening).toEqual({id:'EAST-03',startYmm:9000,widthMm:900,heightMm:2250,sillMm:0});
      expect(SERVICE_CORE_REVISION.exteriorDoorRevision).toMatchObject({previousWidthMm:1700,layout:'SINGLE_LEAF_OUTWARD',hinge:'SOUTH_JAMB'});
      expect(INTERIOR_WALLS.find(w=>w.id==='C-KITCHEN-BEARING-WALL-E')!.rectMm.y0-(opening.startYmm+opening.widthMm)).toBe(812);
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
      // The narrower laundry run must work with real open appliance doors,
      // including handles, the vanity, the new partition and the basin.
      const laundry=BATHROOM_FITOUT.builtIn;
      const vanityEnd=laundry.appliances[0].footprintMm.x0-36;
      for(const m of generated.meshes.filter(m=>m.name.startsWith(BATHROOM_FITOUT.id)&&m.name.includes('BUILT-IN-2616')&&/veľké matne čierne umývadlo|vnútorná čierna misa|veľké bezrámové zrkadlo|nepriame LED/.test(m.name))){
        expect(m.rect.x0,m.name).toBeGreaterThanOrEqual(laundry.footprintMm.x0);
        expect(m.rect.x1,m.name).toBeLessThanOrEqual(vanityEnd);
      }
      for(const appliance of laundry.appliances){
        const motion=interiorDoors.find(d=>d.id===appliance.door.id)!;
        expect(motion).toBeDefined();
        const moving=scene.meshes.filter(m=>m.metadata?.doorId===motion.id);
        const obstacles=scene.meshes.filter(m=>(m.name.startsWith(BATHROOM_FITOUT.id)&&!m.name.includes(` · ${appliance.kind} · `))
          ||m.name.startsWith('Vnútorná stena')).filter(m=>!m.metadata?.walkCollisionOnly).map(shape);
        expect(moving.length).toBeGreaterThanOrEqual(3);
        for(let step=0;step<=180;step++){
          motion.apply(step/180,0);
          for(const m of moving.map(shape))for(const o of obstacles)
            if(m.top>o.bottom+.1&&m.bottom<o.top-.1)expect(polysOverlap(m.polygon,o.polygon),`${m.name}/${o.name} at ${step/2} degrees`).toBe(false);
        }
      }
      // The current frame drawing is narrower than the removable-insulation bodies;
      // a genuinely clear 900 mm opening can pass them, subject to transport tolerances.
      const transport=heating.accumulator.transport;
      expect(transport).toMatchObject({openingId:'EAST-03',openingWidthMm:opening.widthMm,clearWidthMm:648,passesInsulated:false,passesWithoutInsulation:false,method:'REMOVE_INSULATION_VERIFY_CLEAR_OPENING',passesBareThroughTrue900MmClear:true,status:'VERIFY_FINISHED_CLEAR_OPENING'});
      expect(transport.clearWidthMm).toBe(opening.widthMm-2*78-96);
      expect(heating.accumulator.outerDiameterMm).toBeGreaterThan(opening.widthMm);
      expect(heating.accumulator.transportDiameterWithoutInsulationMm).toBeGreaterThan(transport.clearWidthMm);
      expect('transportRouteMm' in heating.accumulator).toBe(false);
      expect(transport.clearanceAtTrue900Mm).toBe(3);
      expect(HEATING_LAYOUTS.B.accumulator.transport.clearanceAtTrue900Mm).toBe(155);
      // The frames of the open door and the facade masonry around it would stop even the bare tank on the old route.
      const jambs=[...exteriorMeshes].map(shape).filter(m=>m.top>100.1&&m.bottom<2013&&/zárubňa/.test(m.name));
      const entryPoint:Point=[HOUSE.facades.east.faceXmm-265,opening.startYmm+opening.widthMm/2];
      expect(jambs.some(j=>discHits(entryPoint,heating.accumulator.transportDiameterWithoutInsulationMm/2,j.polygon))).toBe(true);
    }finally{scene.dispose();engine.dispose();}
  },30000);
});
