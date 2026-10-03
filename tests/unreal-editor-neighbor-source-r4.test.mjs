// Synthetic CPU receipts using frozen source records. No Unreal or GPU is
// launched; these fixtures are not actual R18 saved/native appearance evidence.
import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {validateDiagnosticViews,validateNeighborContentDelta,validateNeighborActorDelta}
  from '../scripts/unreal/exterior-editor-source-r4.mjs';
const root=fileURLToPath(new URL('../',import.meta.url));
const read=async p=>JSON.parse(await fs.readFile(path.resolve(root,p),'utf8'));
const study='output/unreal/exterior-neighbor-finish-20261001-r18-study';
const geometry=await read(study+'/neighbor-finish-geometry.json');
const recipes=await read(study+'/neighbor-finish-recipes.json');
const baseNative=await read('output/unreal/exterior-20261001-r16a/exterior-import-report.json');
const supplement=await read('output/unreal/exterior-neighbor-finish-20261001-r3-supplement/neighbor-finish-diagnostic-supplement.json');
const originalViews=await read(supplement.originalViewpoints.path),appendedViews=await read(supplement.appendedViewpoints.path);
const prefix='/Game/Brezi/NeighborFinish20261001R18';
const sourceRows=[...geometry.candidateMeshes,...geometry.unchangedRemainderMeshes.filter(r=>r.indices.length).map(r=>({...r,
  id:'neighbor_r18_retained_'+r.id,sourceMeshId:r.id}))];
const identity=[[0,0,0],[0,0,0,1],[1,1,1]],fakeRow={sha256:'a'.repeat(64),bytes:10};
function fixture(){
  const report={meshes:Object.fromEntries(sourceRows.map(r=>[r.id,`${prefix}/Geometry/${r.id}.${r.id}`])),
    materials:{materials:Object.fromEntries(Object.keys(recipes).map(id=>[id,{asset:`${prefix}/Materials/M_${id}.M_${id}`}]))},
    importPipelineAssets:['Assets','Materials','Level'].map(id=>`${prefix}/Pipeline/${id}.${id}`),addedActors:{},componentChanges:[]};
  report.materials.textures=Object.fromEntries(['albedo','normal','roughness'].map(id=>[id,{asset:`${prefix}/Textures/T_${id}.T_${id}`}])) ;
  const before={},expected={},saved={},base={...baseNative,finalActorCount:6};
  for(const partition of geometry.sourceTrianglePartitions){
    const id=partition.sourceMeshId,actor=base.geometry.actors[id];
    before[actor]={label:id,transform:identity,components:[{name:'StaticMeshComponent0',mesh:base.geometry.meshes[id],
      visible:true,hiddenInGame:false,neighborRenderPolicy:{cast_shadow:true,cast_hidden_shadow:true},navigation:false,
      collision:'<CollisionEnabled.NO_COLLISION: 0>',collisionProfile:'NoCollision',overrideMaterials:[],
      preservedControl:'untouched'}]};
    const dark=id==='village_0_2_darkroof';report.componentChanges.push({sourceMeshId:id,actor,componentName:'StaticMeshComponent0',
      beforeMesh:base.geometry.meshes[id],afterMesh:dark?base.geometry.meshes[id]:report.meshes['neighbor_r18_retained_'+id],
      operation:dark?'hide-empty-source-chunk':'replace-with-retained-source-chunk',
      changedFields:dark?['visible','hiddenInGame','cast_shadow','cast_hidden_shadow']:['mesh']});
    expected[actor]=structuredClone(before[actor]);const c=expected[actor].components[0];
    if(dark){c.visible=false;c.hiddenInGame=true;c.neighborRenderPolicy.cast_shadow=false;c.neighborRenderPolicy.cast_hidden_shadow=false;}
    else c.mesh=report.componentChanges.at(-1).afterMesh;
    saved[actor]=structuredClone(expected[actor]);
  }
  for(const row of geometry.candidateMeshes){
    const actor='/synthetic/owned/'+row.id;report.addedActors[row.id]=actor;
    saved[actor]={label:row.id,actorTick:false,transform:identity,components:[{name:'StaticMeshComponent0',mesh:report.meshes[row.id],transform:identity,
      materials:[report.materials.materials[row.material]?.asset??base.materials.materials[row.material].asset],
      navigation:false,collision:'<CollisionEnabled.NO_COLLISION: 0>',collisionProfile:'NoCollision',visible:true,hiddenInGame:false,
      componentTick:false,overlapEvents:false,maxDrawDistanceCm:65000,neighborRenderPolicy:{cast_shadow:row.castShadow}}]};
  }
  return {before,expected,saved,report,base,sourceRows};
}
function contentFixture(report){
  const before={'Brezi/Maps/Brezi.umap':fakeRow,'Data/viewpoints.json':fakeRow,'Brezi/protected.uasset':fakeRow};
  const after={...before,'Brezi/Maps/Brezi.umap':{...fakeRow,sha256:'b'.repeat(64)},'Data/viewpoints.json':{...fakeRow,sha256:'c'.repeat(64)}};
  for(const asset of [...Object.values(report.meshes),...Object.values(report.materials.materials).map(v=>v.asset),
    ...Object.values(report.materials.textures).map(v=>v.asset),...report.importPipelineAssets])after[asset.split('.')[0].slice('/Game/'.length)+'.uasset']=fakeRow;
  return {before,after};
}

test('CPU diagnostic manifest preserves every old camera/root field and adds only the typed source view',()=>{
  validateDiagnosticViews(originalViews,supplement,appendedViews);
  const changed=structuredClone(appendedViews);changed.views[0].eyeCm[0]+=1;
  assert.throws(()=>validateDiagnosticViews(originalViews,supplement,changed));
  assert.throws(()=>validateDiagnosticViews(originalViews,{...supplement,sourceCameraAudit:{...supplement.sourceCameraAudit,actualCameraNativeReadback:true}},appendedViews));
  assert.throws(()=>validateDiagnosticViews(originalViews,{...supplement,schemaVersion:1,owner:'scripts/unreal/exterior-neighbor-finish-diagnostic.py'},appendedViews));
  assert.throws(()=>validateDiagnosticViews(originalViews,{...supplement,numericalComparisonPolicy:{...supplement.numericalComparisonPolicy,maximumAbsoluteDeltaCm:.01}},appendedViews));
});
test('CPU overlay Content permits exactly52 known packages and rejects foreign same-namespace assets',()=>{
  const f=fixture(),c=contentFixture(f.report);validateNeighborContentDelta(c.before,c.after,f.report);
  assert.throws(()=>validateNeighborContentDelta(c.before,{...c.after,'Brezi/NeighborFinish20261001R18/unreported.uasset':fakeRow},f.report));
  assert.throws(()=>validateNeighborContentDelta(c.before,{...c.after,'Brezi/protected.uasset':{...fakeRow,bytes:11}},f.report));
  const baselineAfter={...c.before,'Data/viewpoints.json':{...fakeRow,bytes:12}};
  validateNeighborContentDelta(c.before,baselineAfter,{}, {diagnosticBase:true});
  assert.throws(()=>validateNeighborContentDelta(c.before,{...baselineAfter,'Brezi/Maps/Brezi.umap':{...fakeRow,bytes:13}},{},{diagnosticBase:true}));
});
test('CPU actor counterfactual rejects overwritten original controls and collidable new windows',()=>{
  const f=fixture();validateNeighborActorDelta(f);
  const original=Object.keys(f.before)[0],changed=structuredClone(f.saved);changed[original].components[0].preservedControl='changed';
  assert.throws(()=>validateNeighborActorDelta({...f,saved:changed}));
  const unsafe=structuredClone(f.saved),window=geometry.candidateMeshes.find(r=>r.role==='window_glass');
  unsafe[f.report.addedActors[window.id]].components[0].navigation=true;
  assert.throws(()=>validateNeighborActorDelta({...f,saved:unsafe}));
  const swapped=structuredClone(f.report);swapped.componentChanges[0].actor=swapped.componentChanges[1].actor;
  assert.throws(()=>validateNeighborActorDelta({...f,report:swapped}));
});
