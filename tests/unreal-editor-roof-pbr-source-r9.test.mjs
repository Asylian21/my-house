// CPU receipt fixtures; no Unreal/GPU, image review or native proof is produced.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {validateRoofHeader,validateRoofActorDelta,validateRoofContentDelta} from '../scripts/unreal/exterior-editor-source-r9.mjs';
const source='/fixture/output/unreal/exterior-20261002-r23a',project=source+'/Project/BreziTwin';
const header={schema:'brezi-original-roof-pbr-component-overlay-r1',owner:'scripts/unreal/exterior-roof-pbr-native.py',status:'verified-saved-original-roof-pbr-component-overlay',output:source,project,
  nativeAppearanceAccepted:false,performanceAccepted:false,fullPhotorealismAccepted:false,shippingPackageProduced:false,nativeMaterialPackagesIndependentlyReloaded:false,nativeNormalTangentReadbackAvailable:false,
  savedMapUnloadedReloaded:true,nativeApplied:true,originalR18bUnchanged:true,originalContentExceptMapByteIdentical:true,
  baseNativeReport:{sha256:'40ccc7cc686e2beafc05e5248eb8abe371f23bc8ad470c05284d4c442ed950da'},sourceStudy:{sha256:'0370301cb33688419b1940dd7c812f5fbedf8c7590a5df09b3e5e6e1de26000b'},selectedPreflight:{sha256:'987de6ebc672876d3702b15c83ef353559b19c0b510fd4e0456585abcc70d7f9'},
  existingActorCount:5338,existingMaterialGraphsPreserved:51,existingTextureObjectsPreserved:77,geometryChanges:0,originalStaticMeshSlotChanges:0,newImportPipelineAssets:0,
  activeDesign:{variant:'C',heatingLayout:'B',livingLayout:'B'},setbacksMm:{street:3000,east:3000},baselineRecordedPlantLibrary:{masters:135,lods:405,newNativePlantLodReadbackPerformed:false}};
test('CPU typed header rejects native failure, invented savedReloaded substitute and accepted appearance',()=>{
  validateRoofHeader(header,{source,project});
  for(const change of [{status:'failed'},{owner:'scripts/unreal/exterior-neighbor-finish-native-r3.py'},{nativeAppearanceAccepted:true},{nativeMaterialPackagesIndependentlyReloaded:true},{existingMaterialGraphsPreserved:42},{sourceStudy:{sha256:'0'.repeat(64)}},{savedMapUnloadedReloaded:undefined,savedReloaded:true}])assert.throws(()=>validateRoofHeader({...structuredClone(header),...change},{source,project}));
});
test('CPU5338 actor fixture rejects a fifth binding, changed original mesh or changed lighting',()=>{
  const plan=JSON.parse(fs.readFileSync(new URL('../output/unreal/exterior-roof-pbr-20261002-r3-study/roof-pbr-source-plan.json',import.meta.url),'utf8'));
  const before=Object.fromEntries(Array.from({length:5334},(_,i)=>['/fixture/actor'+i,{label:'fixture'+i,lighting:{intensity:1},components:[]}]));
  for(const t of plan.targets)before[t.actor]=structuredClone(t.originalSavedActorWitness);
  const expected=structuredClone(before),material='/Game/Brezi/RoofPbr20261002R23/Materials/M_roof_tiles_original.M_roof_tiles_original',changes=[];
  for(const t of plan.targets){const c=expected[t.actor].components.find(c=>c.name===t.componentName);c.materials=[material];c.overrideMaterials=[material];changes.push({sourceMeshId:t.sourceMeshId,actor:t.actor,componentName:t.componentName,slot:0,mesh:t.mesh,beforeMaterial:t.oldMaterial,afterMaterial:material,changedFields:['materials','overrideMaterials']});}
  validateRoofActorDelta(before,expected,structuredClone(expected),plan.targets,changes);
  const bad=structuredClone(expected);bad['/fixture/actor0'].lighting.intensity=2;assert.throws(()=>validateRoofActorDelta(before,expected,bad,plan.targets,changes));
  const mesh=structuredClone(expected);mesh[plan.targets[0].actor].components[0].mesh='/Game/Changed.Mesh';assert.throws(()=>validateRoofActorDelta(before,mesh,mesh,plan.targets,changes));
  assert.throws(()=>validateRoofActorDelta(before,expected,expected,[...plan.targets,plan.targets[0]],[...changes,changes[0]]));
});
test('CPU4027 Content fixture permits four packages and rejects an extra pipeline or modified old texture',()=>{
  const before=Object.fromEntries(Array.from({length:4026},(_,i)=>['Old/'+i+'.uasset',{sha256:'a'.repeat(64),bytes:1}]));before['Brezi/Maps/Brezi.umap']={sha256:'b'.repeat(64),bytes:1};
  const after=structuredClone(before);after['Brezi/Maps/Brezi.umap']={sha256:'c'.repeat(64),bytes:2};
  const packages=Array.from({length:4},(_,i)=>'/Game/Brezi/RoofPbr20261002R23/Fixture/Asset'+i);
  for(const p of packages)after[p.slice('/Game/'.length)+'.uasset']={sha256:'d'.repeat(64),bytes:1};
  const delta={changedFiles:['Brezi/Maps/Brezi.umap'],newFiles:packages.map(p=>p.slice('/Game/'.length)+'.uasset').sort(),newUassetPackages:4,protectedOriginalFilesByteIdentical:4026};validateRoofContentDelta(before,after,packages,delta);
  const extra=structuredClone(after);extra['Brezi/RoofPbr20261002R23/Pipeline/Extra.uasset']={sha256:'d'.repeat(64),bytes:1};assert.throws(()=>validateRoofContentDelta(before,extra,packages,delta));
  const changed=structuredClone(after);changed['Old/0.uasset'].sha256='e'.repeat(64);assert.throws(()=>validateRoofContentDelta(before,changed,packages,delta));
});
