import test from 'node:test';
import assert from 'node:assert/strict';
import {resolve} from 'node:path';
import {validateDerivedBounds,validateNaniteStudy} from '../scripts/unreal/nanite-study.mjs';

function fixture(count=1){
  const project='/portable/output/unreal/study/Project/BreziTwin';
  const h='a'.repeat(64),next='b'.repeat(64),witness='c'.repeat(64);
  const content={[resolve(project,'Content/Brezi/Maps/Brezi.umap')]:h,
    [resolve(project,'Content/Brezi/Materials/Opaque.uasset')]:h};
  const selected=[],objects=[];
  for(let i=0;i<count;i++){
    const id='DOM_'+String(i).padStart(5,'0'),file='Brezi/Geometry/brezi-twin/StaticMeshes/'+id+'.uasset';
    content[resolve(project,'Content',file)]=h;
    selected.push({sourceId:id,asset:'/Game/Brezi/Geometry/brezi-twin/StaticMeshes/'+id+'.'+id,file,
      triangles:12,naniteEnabledInitially:false,componentDisallowNanite:false,witnessSha256:witness,derivedBoundsBeforeCm:[[1,2,3],[1,1,1]]});
    objects.push({id,group:'Interior',enabled:true,instances:1,triangles:12,metadata:{},materialSlots:['opaque']});
  }
  const source={donor:'/portable/output/unreal/shipping',content};
  const study={schemaVersion:1,status:'nanite-study-validated-unaccepted',owner:'scripts/unreal/nanite-study.py',experimental:true,
    accepted:false,renderedVerified:false,performanceAccepted:false,project,sourceOutput:source.donor,cohortLimit:128,attemptedCohortCount:count,
    savedReloaded:true,protectedContentUnchanged:true,mapUnchanged:true,sourceGeometryMaterialsAndCollisionPreserved:true,
    beforeAssetHashes:{...content},afterAssetHashes:{...content},actorWitnessSha256:witness,savedActorWitnessSha256:witness,
    actorCount:1,selected,savedMeshReadback:selected.map(row=>({sourceId:row.sourceId,naniteEnabled:true,
      beforeWitnessSha256:witness,afterWitnessSha256:witness,derivedBoundsBeforeCm:row.derivedBoundsBeforeCm,
      derivedBoundsAfterCm:row.derivedBoundsBeforeCm,derivedBoundsMaxErrorCm:0}))};
  for(const row of selected)study.afterAssetHashes[resolve(project,'Content',row.file)]=next;
  return {study,source,project,scene:{objects,materials:{opaque:{alpha:1}}},doors:{doors:[]}};
}

test('derived bounds admit one float32 ULP but reject larger movement and enforce the absolute cap',()=>{
  const bounds=x=>[[x,0,0],[1,1,1]];
  assert.equal(validateDerivedBounds(bounds(1209.1000366210938),bounds(1209.10009765625)),.00006103515625);
  assert.equal(validateDerivedBounds(bounds(1),bounds(1+2**-23)),2**-23);
  for(const [old,value] of [[1,1+2**-22],[100000,100000+2**-7],[0,.000001]])
    assert.throws(()=>validateDerivedBounds(bounds(old),bounds(value)),/Derived bounds exceed/);
});

test('bounded asset study accepts exact saved source witnesses and only the selected mesh bytes',()=>{
  for(const count of [1,128]){
    const f=fixture(count);assert.deepEqual(validateNaniteStudy(f),f.study.afterAssetHashes);
  }
});
test('map, materials and unrelated mesh files remain immutable',()=>{
  for(const relative of ['Brezi/Maps/Brezi.umap','Brezi/Materials/Opaque.uasset','Brezi/Geometry/brezi-twin/StaticMeshes/DOM_99999.uasset']){
    const f=fixture(),file=resolve(f.project,'Content',relative);
    f.study.afterAssetHashes[file]='d'.repeat(64);
    assert.throws(()=>validateNaniteStudy(f),/inventory|only every selected/);
  }
});
test('every selected mesh must change and the cohort is unique, present, bounded and exactly namespaced',()=>{
  const mutations=[f=>{f.study.afterAssetHashes={...f.study.beforeAssetHashes};},
    f=>{f.study.selected.push({...f.study.selected[0]});f.study.savedMeshReadback.push({...f.study.savedMeshReadback[0]});},
    f=>{f.study.selected[0].file='../outside.uasset';},f=>{f.study.selected[0].asset='/Game/Other.Mesh';}];
  for(const mutate of mutations){const f=fixture();mutate(f);assert.throws(()=>validateNaniteStudy(f));}
  for(const count of [0,129])assert.throws(()=>validateNaniteStudy(fixture(count)),/bounded study cohort/);
});
test('source contract rejects doors, collision metadata, translucent and non-interior meshes',()=>{
  const mutations=[f=>{f.doors.doors=[{members:[{sourceObjectId:'DOM_00000'}]}];},
    f=>{f.scene.materials.opaque.alpha=.5;},f=>{f.scene.objects[0].group='Vegetation';},
    f=>{f.scene.objects[0].triangles=512;f.study.selected[0].triangles=512;},
    ...['doorMotion','dynamicCameraOccluder','walkSurface','cameraOccluder','babylonCheckCollisions']
      .map(flag=>f=>{f.scene.objects[0].metadata[flag]=true;})];
  for(const mutate of mutations){const f=fixture();mutate(f);assert.throws(()=>validateNaniteStudy(f));}
});
test('fixed door frames, sidelights and stove effects are excluded beyond the moving-door contract',()=>{
  for(const name of ['Dvere · pravá zárubňa','Dveře · klika','EAST-04 · D1.1.002 · parapet','kľučka','DOOR-HANDLE','FIREPLACE-STOVE · LOG-1','FLAME-3']){
    const f=fixture();f.scene.objects[0].name=name;assert.throws(()=>validateNaniteStudy(f),/fixed door part or stove/);
  }
});
test('separate native readback must cover every original witness and prove non-Nanite to Nanite transition',()=>{
  const mutations=[f=>{f.study.savedMeshReadback=[];},f=>{f.study.selected[0].naniteEnabledInitially=true;},
    f=>{f.study.savedMeshReadback[0].naniteEnabled=false;},f=>{f.study.savedMeshReadback[0].sourceId='DOM_99999';},
    f=>{f.study.savedMeshReadback[0].beforeWitnessSha256='f'.repeat(64);},
    f=>{f.study.savedMeshReadback[0].afterWitnessSha256='f'.repeat(64);},
    f=>{f.study.savedActorWitnessSha256='f'.repeat(64);}];
  for(const mutate of mutations){const f=fixture();mutate(f);assert.throws(()=>validateNaniteStudy(f));}
});
test('experimental receipt cannot imply visual acceptance, performance acceptance or promotion',()=>{
  for(const field of ['accepted','renderedVerified','performanceAccepted']){
    const f=fixture();f.study[field]=true;assert.throws(()=>validateNaniteStudy(f));
  }
  for(const field of ['savedReloaded','protectedContentUnchanged','mapUnchanged','sourceGeometryMaterialsAndCollisionPreserved']){
    const f=fixture();f.study[field]=false;assert.throws(()=>validateNaniteStudy(f),/Missing study invariant/);
  }
});
