import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { Texture } from '@babylonjs/core/Materials/Textures/texture';
import { Color3 } from '@babylonjs/core/Maths/math.color';
import { Vector3, Vector4 } from '@babylonjs/core/Maths/math.vector';
import { CreateBox } from '@babylonjs/core/Meshes/Builders/boxBuilder.pure';
import { CreateCylinder } from '@babylonjs/core/Meshes/Builders/cylinderBuilder.pure';
import { CreateTube } from '@babylonjs/core/Meshes/Builders/tubeBuilder.pure';
import { Mesh } from '@babylonjs/core/Meshes/mesh';
import type { InteriorBuildContext, InteriorMaterials } from './babylon-interior';
import { KITCHEN_DESIGN as d, KITCHEN_ISLAND as island, KITCHEN_RUN as k, type RectMm } from './twin-interior';
import { HOUSE } from './twin-active-house';
import { sceneXM as xM, sceneZM as zM } from './twin-render-frame';
import { KITCHEN_TASK_LIGHT } from './twin-interior-lighting';
import { createKitchenTaskLight, registerKitchenLightEmitter } from './babylon-interior-lighting';
import { buildKitchenPendant } from './babylon-kitchen-pendant';

type Finish = (mesh:Mesh, material:PBRMaterial, options?:{
  collide?:boolean; shadow?:boolean; pickable?:boolean; cameraOccluder?:boolean;
})=>Mesh;
const rect=(x0:number,y0:number,x1:number,y1:number):RectMm=>({x0,y0,x1,y1});

/** C/B/B kitchen: a quiet cooking niche, two appliance towers and a working island.
 * Names are revision-specific so archived GLB joinery cannot cover the new fitout.
 */
export function buildKitchenDesign(context:InteriorBuildContext, materials:InteriorMaterials, finish:Finish){
  const scene=context.scene;
  function material(name:string,color:string,roughness:number,texture?:string){
    const m=new PBRMaterial(`Kitchen 2026 · ${name}`,scene);
    m.albedoColor=Color3.FromHexString(color).toLinearSpace();m.roughness=roughness;m.metallic=0;
    if(texture){
      m.albedoTexture=new Texture(`/assets/textures/${texture}.jpg`,scene,false,false);
      m.albedoTexture.gammaSpace=true;
      (m.albedoTexture as Texture).anisotropicFilteringLevel=context.anisotropy;
    }
    return m;
  }
  const oak=material('prírodný dub','#e5d8c7',.72,'living-natural-oak-albedo');
  (oak.albedoTexture as Texture).wAng=Math.PI/2;
  const stone=material('čierny kameň · saténový povrch','#777875',.42,'stone-dark-albedo');
  stone.environmentIntensity=.5;
  const shadow=material('zapustené profily','#36332d',.64);
  const metal=material('kartáčovaná oceľ','#adb1ae',.38);metal.metallic=.9;
  const glass=material('spotrebiče grafit','#16191a',.2);glass.clearCoat.isEnabled=true;
  glass.environmentIntensity=.3;
  const emitter=material('pracovné svetlo','#fff2d8',.65);
  function rawBox(name:string,r:RectMm,bottom:number,height:number){
    const w=(r.x1-r.x0)/1000,depth=(r.y1-r.y0)/1000,h=height/1000;
    const faceUV=[w,w,depth,depth,w,w].map((a,i)=>new Vector4(0,0,a,i<4?h:depth));
    const mesh=CreateBox(`KITCHEN-RUN · ${name}`,{width:w,depth,height:h,faceUV},scene);
    mesh.position.set(xM((r.x0+r.x1)/2),(bottom+height/2)/1000,zM((r.y0+r.y1)/2));
    return mesh;
  }
  function box(name:string,r:RectMm,bottom:number,height:number,m:PBRMaterial,collide=false){
    return finish(rawBox(name,r,bottom,height),m,{collide,shadow:true,pickable:true});
  }
  // Four pieces merged into one real opening. The sink is recessed into it;
  // neither the stone nor the cabinet volume plugs the bowl with a solid slab.
  function perforated(name:string,r:RectMm,hole:RectMm,bottom:number,height:number,m:PBRMaterial){
    const pieces=[rect(r.x0,r.y0,hole.x0,r.y1),rect(hole.x1,r.y0,r.x1,r.y1),
      rect(hole.x0,r.y0,hole.x1,hole.y0),rect(hole.x0,hole.y1,hole.x1,r.y1)]
      .map(p=>rawBox(name,p,bottom,height));
    const mesh=Mesh.MergeMeshes(pieces,true,true)!;mesh.name=`KITCHEN-RUN · ${name}`;
    mesh.metadata={planProjection:'TRIANGLE_SILHOUETTE'};
    return finish(mesh,m,{shadow:true,pickable:true});
  }
  function guard(name:string,r:RectMm){
    const mesh=box(name,r,-2000,6000,shadow,true);mesh.isVisible=false;
    mesh.metadata={...mesh.metadata,walkCollisionOnly:true,revisionSourceId:d.id};
  }
  function front(name:string,x0:number,x1:number,y:number,facing:1|-1,drawers:boolean,m:PBRMaterial){
    box(name,rect(x0+2,y-10,x1-2,y+10),120,740,m);
    // Recessed finger rail and two deep drawer divisions; no projecting handles.
    for(const z of drawers?[370,620,850]:[850]){
      box(`${name} · zapustený úchop ${z}`,rect(x0+4,y+facing*11-2,x1-4,y+facing*11+2),z,7,shadow);
    }
  }
  const run=k.rectMm,back=d.backWorktopRectMm;
  // One 2250 mm datum ties the oak appliance pair to the shallow cooking niche.
  for(const [tag,r] of [['FRIDGE-600',k.fridgeUnitRectMm],['OVEN-TOWER',d.ovenTowerRectMm]] as const){
    box(`${tag} · dubový blok 2026`,rect(r.x0, r.y0,r.x1,r.y1-12),100,2150,oak,true);
    box(`${tag} · zapustený sokel 2026`,rect(r.x0+25,r.y0+25,r.x1-25,r.y1-55),0,100,shadow);
    box(`${tag} · horná ventilačná medzera`,rect(r.x0+25,r.y0+35,r.x1-25,r.y1-45),2245,5,shadow);
    box(`${tag} · čelná škára 2026`,rect(r.x1-3,r.y1-11,r.x1,r.y1+2),120,2125,shadow);
  }
  const f=k.fridgeUnitRectMm;
  box('FRIDGE-600 · delenie mrazničky 2026',rect(f.x0+3,f.y1-11,f.x1-3,f.y1+2),720,4,shadow);
  box('FRIDGE-600 · zvislý zapustený profil 2026',rect(f.x1-24,f.y1-13,f.x1-12,f.y1+2),980,830,shadow);
  box('FRIDGE-600 · vetranie sokla 2026',rect(f.x0+60,f.y1-52,f.x1-60,f.y1-48),32,35,shadow);
  const oven=d.ovenTowerRectMm;
  box('OVEN-TOWER · horné dvierka 2026',rect(oven.x0+3,oven.y1-10,oven.x1-3,oven.y1+2),1460,787,oak);
  box('OVEN-TOWER · deliaca škára nad rúrou',rect(oven.x0+3,oven.y1,oven.x1-3,oven.y1+3),1452,5,shadow);
  for(const z of [360,610,827])box('OVEN-TOWER · spodná zásuvka',rect(oven.x0+3,oven.y1,oven.x1-3,oven.y1+3),z,5,shadow);
  const ovenFront=rect(k.ovenCenterXmm-d.oven.widthMm/2,oven.y1-4,k.ovenCenterXmm+d.oven.widthMm/2,oven.y1+12);
  box('OVEN-ELEVATED · rúra so zasúvacím krídlom',ovenFront,d.oven.bottomMm,d.oven.heightMm,glass);
  box('OVEN-ELEVATED · kontrolný displej',rect(ovenFront.x0+220,oven.y1+13,ovenFront.x1-220,oven.y1+15),1365,35,materials.blackGlass);
  box('OVEN-ELEVATED · madlo rúry 2026',rect(ovenFront.x0+55,oven.y1+20,ovenFront.x1-55,oven.y1+38),1320,18,metal);
  box('OVEN-ELEVATED · vnútorné sklo 2026',rect(ovenFront.x0+42,oven.y1+13,ovenFront.x1-42,oven.y1+15),900,370,materials.blackGlass);
  box('nika · spodné korpusy 2026',rect(back.x0,run.y0,run.x1,run.y1-12),100,750,oak,true);
  box('nika · sokel 2026',rect(back.x0+30,run.y0,run.x1-30,run.y1-60),0,100,shadow);
  for(let i=0;i<d.backModules.length-1;i++)front(`nika · zásuvky ${i+1}`,d.backModules[i],d.backModules[i+1],run.y1-3,1,true,oak);
  box('nika · tieňová škára pod kameňom',rect(back.x0+4,run.y0+4,run.x1-4,run.y1-8),860,20,shadow);
  box('nika · minerálna pracovná doska',back,880,20,stone);
  box('nika · súvislý minerálny obklad',rect(back.x0,run.y0,run.x1,run.y0+12),900,700,stone);
  finish(rawBox('horné skrinky · matná nika 2026',rect(back.x0,run.y0,run.x1,run.y0+k.upperCabinets.depthMm),1600,650),oak,
    {shadow:true,pickable:true,cameraOccluder:true});
  for(const x of d.backModules.slice(1,-1))box('horné skrinky · modulová škára 2026',rect(x-2,run.y0+k.upperCabinets.depthMm-1,x+2,run.y0+k.upperCabinets.depthMm+2),1603,644,shadow);
  // The 880 mm canopy sits inside the 990 mm centre module. Recirculation
  // returns at the cabinet top, not into a sealed cupboard or the cathedral.
  const hoodY=(d.hobRectMm.y0+d.hobRectMm.y1)/2,hoodHalfDepth=d.hood.depthMm/2;
  box('odsávač · integrovaná spodná kazeta',rect(k.extractorCenterXmm-440,hoodY-hoodHalfDepth,k.extractorCenterXmm+440,hoodY+hoodHalfDepth),1600,18,metal);
  box('odsávač · filtre',rect(k.extractorCenterXmm-390,hoodY-hoodHalfDepth+20,k.extractorCenterXmm+390,hoodY+hoodHalfDepth-23),1598,2,shadow);
  box('odsávač · horná vratná mriežka',rect(k.extractorCenterXmm-300,run.y0+60,k.extractorCenterXmm+300,run.y0+270),2250,3,shadow);
  // Store the hidden appliance envelope for fit/coordination, not plan clutter.
  const hoodEnvelope=rawBox('odsávač · servisná obálka',rect(k.extractorCenterXmm-440,hoodY-hoodHalfDepth,k.extractorCenterXmm+440,hoodY+hoodHalfDepth),1600,350);
  hoodEnvelope.isVisible=false;hoodEnvelope.isPickable=false;
  hoodEnvelope.metadata={coordinationOnly:true,ductDiameterMm:150,ventilation:d.hood.ventilation};
  box('varná doska · indukcia 800',d.hobRectMm,900,5,glass);
  for(const dx of [-230,230])for(const dy of [-110,110]){
    const cx=k.hobCenterXmm+dx,cy=(d.hobRectMm.y0+d.hobRectMm.y1)/2+dy;
    box('varná doska · označenie zóny',rect(cx-10,cy-1,cx+10,cy+1),905,1,metal);
    box('varná doska · označenie zóny',rect(cx-1,cy-10,cx+1,cy+10),905,1,metal);
  }
  const led=KITCHEN_TASK_LIGHT.geometry,p=led.bodyCenterPlanMm,sz=led.dimensionsMm;
  const ledMesh=box('LED lišta pod skrinkami',rect(p[0]-sz[0]/2,p[1]-sz[1]/2,p[0]+sz[0]/2,p[1]+sz[1]/2),p[2]-sz[2]/2,sz[2],emitter);
  ledMesh.metadata={interiorLightId:KITCHEN_TASK_LIGHT.id};
  createKitchenTaskLight(scene);registerKitchenLightEmitter(scene,KITCHEN_TASK_LIGHT.id,emitter);
  buildKitchenPendant({scene,finish:(mesh,m)=>finish(mesh,m,{shadow:true})});

  // Full-depth island with a true undermount sink and closed living-side storage.
  const pen=k.peninsulaRectMm,top=island.worktopRectMm,sink=d.sinkBowlRectMm;
  const body=rect(pen.x0,pen.y0,pen.x1,d.livingStorageRectMm.y1);
  box('ostrovček · zapustený sokel 2026',rect(body.x0+65,body.y0+65,body.x1-65,body.y1-65),0,100,shadow);
  box('ostrovček · dubový základ 2026',body,100,550,oak,true);
  perforated('ostrovček · korpus okolo výrezu',body,sink,650,210,oak);
  perforated('ostrovček · tieňová škára pod kameňom',rect(body.x0+5,body.y0+5,body.x1-5,body.y1-5),sink,860,20,shadow);
  const topMesh=perforated('pracovná doska ostrovčeka · minerálny povrch',top,sink,880,20,stone);
  topMesh.metadata={...topMesh.metadata,revisionSourceId:d.id};
  for(const [index,cabinet] of d.islandModules.entries()){
    const tag=cabinet.kind==='dishwasher'?'DISHWASHER':'ostrovček';
    const label=cabinet.kind==='dishwasher'?'umývačka':cabinet.kind==='sink-waste'?'drezová skrinka s triedením odpadu':'zásuvková skrinka';
    front(`${tag} · ${label} ${index+1}`,cabinet.x0,cabinet.x1,pen.y0+3,-1,cabinet.kind==='drawers',oak);
  }
  // Three broad, flush fronts give the living-room elevation a calm rhythm.
  const storage=d.livingStorageRectMm;
  for(let i=0;i<3;i++){
    const x0=storage.x0+i*(storage.x1-storage.x0)/3,x1=storage.x0+(i+1)*(storage.x1-storage.x0)/3;
    front(`ostrovček · plytké úložisko ${i+1}`,x0,x1,storage.y1-3,1,false,oak);
  }
  guard('navigačný obrys ostrovčeka',top);
  // Steel basin: bottom, four walls and a visible drain, 200 mm below the top.
  box('drez · zapustené dno 600',sink,700,3,metal);
  for(const r of [rect(sink.x0-2,sink.y0,sink.x0+2,sink.y1),rect(sink.x1-2,sink.y0,sink.x1+2,sink.y1),
    rect(sink.x0,sink.y0-2,sink.x1,sink.y0+2),rect(sink.x0,sink.y1-2,sink.x1,sink.y1+2)])box('drez · nerezová stena',r,700,198,metal);
  const drain=CreateCylinder('KITCHEN-RUN · drez · sitko',{diameter:.07,height:.003,tessellation:32},scene);
  drain.position.set(xM(k.sinkCenterXmm),.705,zM((sink.y0+sink.y1)/2));finish(drain,shadow);
  const tapY=sink.y1+75,tapX=k.sinkCenterXmm;
  const path=[new Vector3(xM(tapX),.9,zM(tapY)),new Vector3(xM(tapX),1.18,zM(tapY)),
    new Vector3(xM(tapX),1.22,zM(tapY-35)),new Vector3(xM(tapX),1.22,zM(tapY-180)),new Vector3(xM(tapX),1.18,zM(tapY-215))];
  const tap=CreateTube('KITCHEN-RUN · batéria · subtilná oceľ',{path,radius:.012,tessellation:16,cap:Mesh.CAP_ALL},scene);finish(tap,metal,{shadow:true});
  box('batéria · páčka',rect(tapX+22,tapY-5,tapX+30,tapY+5),920,85,metal);

  // Full right-hand sideboard: identical thin stone, quiet fronts, daylight worktop.
  const r=d.eastStorageRectMm,rt=island.eastReturnWorktopRectMm;
  box('L-RETURN-EAST · dubové korpusy 2026',r,100,760,oak,true);
  box('L-RETURN-EAST · sokel 2026',rect(r.x0+65,r.y0+40,r.x1,rt.y1-60),0,100,shadow);
  box('L-RETURN-EAST · tieňová škára pod kameňom',rect(r.x0+4,r.y0+4,r.x1-4,r.y1-4),860,20,shadow);
  box('L-RETURN-EAST · minerálna doska pri okne',rt,880,20,stone);
  const eastWindow=HOUSE.facades.east.openings.find(o=>o.id==='EAST-04')!;
  box('L-RETURN-EAST · obklad pri stene 2026',rect(r.x1-12,r.y0+10,r.x1,eastWindow.startYmm-20),900,180,stone);
  const frontLength=rt.y1-20-r.y0;
  for(let i=0;i<3;i++){
    const y0=r.y0+i*frontLength/3,y1=r.y0+(i+1)*frontLength/3;
    box(`L-RETURN-EAST · dvierka ${i+1}`,rect(r.x0-2,y0+2,r.x0+18,y1-2),120,740,oak);
    box(`L-RETURN-EAST · zapustený profil ${i+1}`,rect(r.x0-4,y0+4,r.x0,y1-4),850,7,shadow);
  }
  guard('L-RETURN-EAST · hladký navigačný obrys',rt);
}
