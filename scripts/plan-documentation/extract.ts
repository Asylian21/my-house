import { NullEngine } from '@babylonjs/core/Engines/nullEngine';
import { Scene } from '@babylonjs/core/scene';
import { PBRMaterial } from '@babylonjs/core/Materials/PBR/pbrMaterial';
import { Matrix, Quaternion, Vector3 } from '@babylonjs/core/Maths/math.vector';
import { buildInterior } from '../../lib/babylon-interior';
import { SCENE_CENTER_MM } from '../../lib/twin-render-frame';
import { TwinSceneController } from '../../lib/babylon-scene';
import { buildGarageSuperbVehicle } from '../../lib/babylon-garage-vehicle';
import { GARAGE_VEHICLE } from '../../lib/twin-garage';
import type { AbstractMesh } from '@babylonjs/core/Meshes/abstractMesh';
import { CreateCylinder } from '@babylonjs/core/Meshes/Builders/cylinderBuilder.pure';
import { HOUSE } from '../../lib/twin-active-house';
import { Mesh } from '@babylonjs/core/Meshes/mesh';

/** Convex orthographic silhouette. Dimensions retain the unrounded world bounds. */
export function hull(points: number[][]): number[][] {
  const sorted = [...new Map(points.map(p => [p.join(','), p])).values()].sort((a,b) => a[0]-b[0] || a[1]-b[1]);
  if (sorted.length < 3) return sorted;
  const cross = (a:number[], b:number[], c:number[]) => (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]);
  const half = (list:number[][]) => { const out:number[][]=[]; for(const p of list) { while(out.length>1 && cross(out[out.length-2],out[out.length-1],p)<=0) out.pop(); out.push(p); } out.pop(); return out; };
  return [...half(sorted), ...half([...sorted].reverse())];
}

export function extractPlanGeometry(terraceGlb?:Uint8Array) {
  const engine = new NullEngine({renderWidth:128,renderHeight:128,textureSize:128,deterministicLockstep:false,lockstepMaxSteps:1});
  const scene = new Scene(engine);
  scene.useRightHandedSystem=true;
  const material = new PBRMaterial('documentation-context', scene);
  try {
    // Reuse the real facade/porch builders without creating a browser engine or
    // mutating the live model. Material-only hooks do not change geometry.
    const shell = Object.create(TwinSceneController.prototype);
    const identity=(mesh:AbstractMesh)=>mesh;
    Object.assign(shell,{scene,materials:new Proxy({}, {get:()=>material}),realisticMaterials:new Proxy({}, {get:()=>material}),
      register:identity,realisticOnly:identity,castShadow:identity,larchFor:()=>material,
      appearance:(mesh:AbstractMesh,_technical:unknown,realistic:PBRMaterial)=>{mesh.material=realistic;return mesh;},
      doors:{register:()=>{}},renderQuality:{anisotropy:1},garageDoorPanels:[]});
    shell.buildRealisticHouseShell();
    shell.buildInteractiveGarageDoor();
    const shellNames=new Set(scene.meshes);
    shell.buildGardenFurniture();
    // The live ArchViz terrace asset replaces these fallback garden chairs.
    for(const mesh of [...scene.meshes])if(/^(Záhradné kreslo|Operadlo záhradného kresla|Noha kresla)/.test(mesh.name))mesh.dispose();
    buildInterior({scene,anisotropy:1,wall:material,soffit:material,glassFrame:material,chimneyMetal:material,timber:material,
      register:mesh=>mesh, realisticOnly:mesh=>mesh, castShadow:mesh=>mesh});
    const vehicle=buildGarageSuperbVehicle(scene,{register:identity,realisticOnly:identity,castShadow:identity});
    vehicle.root.position.set((GARAGE_VEHICLE.route.parkedMm.x-SCENE_CENTER_MM.x)/1000,-GARAGE_VEHICLE.wheelGroundOffsetM,(SCENE_CENTER_MM.y-GARAGE_VEHICLE.route.parkedMm.y)/1000);
    vehicle.root.rotation.y=Math.PI/2;
    if(terraceGlb){
      // Decode the real static furniture vertices without loading textures.
      // Both glTF and the live scene use the same right-handed Y-up frame.
      const data=new DataView(terraceGlb.buffer,terraceGlb.byteOffset,terraceGlb.byteLength),jsonSize=data.getUint32(12,true);
      const gltf=JSON.parse(new TextDecoder().decode(terraceGlb.subarray(20,20+jsonSize)));
      const binaryStart=28+jsonSize;
      for(const node of gltf.nodes){
        if(node.mesh===undefined)continue;
        const transform=node.matrix?Matrix.FromArray(node.matrix):Matrix.Compose(Vector3.FromArray(node.scale??[1,1,1]),Quaternion.FromArray(node.rotation??[0,0,0,1]),Vector3.FromArray(node.translation??[0,0,0]));
        for(const primitive of gltf.meshes[node.mesh].primitives){
          const accessor=gltf.accessors[primitive.attributes.POSITION],buffer=gltf.bufferViews[accessor.bufferView];
          if(accessor.componentType!==5126||accessor.type!=='VEC3')throw new Error('Unsupported terrace position accessor');
          const offset=binaryStart+(buffer.byteOffset??0)+(accessor.byteOffset??0),stride=buffer.byteStride??12,positions:number[]=[];
          for(let i=0;i<accessor.count;i++){
            const p=Vector3.TransformCoordinates(new Vector3(data.getFloat32(offset+i*stride,true),data.getFloat32(offset+i*stride+4,true),data.getFloat32(offset+i*stride+8,true)),transform);
            positions.push(p.x,p.y,p.z);
          }
          const mesh=new Mesh(node.name.endsWith('_table')?'Terasový stôl z 3D':`Terasová stolička ${node.name.endsWith('01')?'1':'2'}`,scene);
          mesh.setVerticesData('position',positions);mesh.material=material;
        }
      }
    }
    for(const flue of HOUSE.flues){
      const pipe=CreateCylinder(`${flue.id} · zvislý dymovod`,{height:(flue.terminationElevationMm-flue.baseElevationMm)/1000,diameter:flue.outerDiameterMm/1000,tessellation:48},scene);
      pipe.position.set((flue.centerMm.x-SCENE_CENTER_MM.x)/1000,(flue.baseElevationMm+flue.terminationElevationMm)/2000,(SCENE_CENTER_MM.y-flue.centerMm.y)/1000);
    }
    const meshes = scene.meshes.filter(mesh=>mesh.isVisible && mesh.visibility>0 && !mesh.metadata?.walkCollisionOnly && !mesh.metadata?.navigationGuard && mesh.getTotalVertices()>0).map((mesh,index)=>{
      const matrix = mesh.computeWorldMatrix(true);
      const vertices=mesh.getVerticesData('position') ?? [];
      const projected:number[][]=[];
      let x0=Infinity,y0=Infinity,x1=-Infinity,y1=-Infinity,z0=Infinity,z1=-Infinity;
      for(let i=0;i<vertices.length;i+=3) {
        const p=Vector3.TransformCoordinates(new Vector3(vertices[i],vertices[i+1],vertices[i+2]),matrix);
        const x=p.x*1000+SCENE_CENTER_MM.x, y=SCENE_CENTER_MM.y-p.z*1000, z=p.y*1000;
        x0=Math.min(x0,x);x1=Math.max(x1,x);y0=Math.min(y0,y);y1=Math.max(y1,y);z0=Math.min(z0,z);z1=Math.max(z1,z);
        projected.push([Math.round(x),Math.round(-y)]);
      }
      const round=(n:number)=>Math.round(n*100)/100||0;
      const surface=mesh.material as PBRMaterial|null;
      return {id:`mesh-${index}`,name:mesh.name,source:shellNames.has(mesh)?'shell':'interior',rect:{x0:round(x0),y0:round(y0),x1:round(x1),y1:round(y1)},z0:round(z0),z1:round(z1),
        polygon:hull(projected).map(p=>p.join(',')).join(' '),color:surface?.albedoColor?.toHexString() ?? '#c9cbd0'};
    });
    return {revision:1,projection:'World-space orthographic convex silhouettes; measurements in mm; at rest.',meshes};
  } finally { scene.dispose(); engine.dispose(); }
}
