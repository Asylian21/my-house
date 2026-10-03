// Closed R21 artist-authored foreground adapter. All historical modes delegate
// frozen R6; an actual process0/native saved receipt is required for this mode.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence as loadR6,validateProjectClosure} from './exterior-editor-source-r6.mjs';
export {validateProjectClosure};
const OWNER='scripts/unreal/exterior-canopy-foreground-native-r2.py';
const HELPER_SHA='fb443ef8c180b3774b07b8392e94e2dc9755434760c3855f7795e99bd7ef84ee';
const GUARD_SHA='ecf7c3421f357e2a384e40016bc151c3e141621ee1068c567196bdf53241ac15';
const PLAN_SHA='71bddb13e370b9523558e2a1d4a90c92c9e49c44476a1b4d40ca8f0ec69e1c4a';
const PREFLIGHT_SHA='8242a26748adb538f01b0bd992b2bb23ce88a2ad00121d7f08d019d01a05949f';
const BASE_SHA='1f4fcf02a460153d8e2c691d301c5970bcb6c750439432c8f152b63be835e122';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const R6_SHA='c54122f455541474a964db8e07dd901f03355e6a8b999d04c42b85764f320b09';
const FROZEN_GUARDS={6:R6_SHA,5:'e7392a0f5f365fba88e3d26f8979ff748b4ae8ff28a4c34cd6e3e8d9eb3a0f8b',4:'4469319f624a396e71699587b1436657d442d6dfb4e83b5f290db6459038f105',3:'1fcbd62598fe9f2bd66a64c2b86355fdfdee357d82dd28068d78786b25688c7b'};
const PREFIX='/Game/Brezi/CanopyForeground20261002R21',TAG='BreziCanopyForeground20261002R21';
const MODEL_IDS=['canopy_ecology_grass_0','canopy_ecology_grass_1','canopy_ecology_herb_0','canopy_ecology_herb_1'];
const COUNTS=[213,213,43,43],FLOOR='canopy_foreground_r21_surface';
const read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const hashLike=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const sha=async file=>{const h=createHash('sha256');for await(const b of createReadStream(file))h.update(b);return h.digest('hex');};
const exec=promisify(execFile);
const identity=[[0,0,0],[0,0,0,1],[1,1,1]];
function denied(row){for(const k of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingVerified','packageVerified'])assert.equal(row[k],false,k);}
function ownPackage(asset){assert(typeof asset==='string'&&asset.startsWith(PREFIX+'/')&&!asset.includes('..'));return asset.split('.')[0].slice('/Game/'.length)+'.uasset';}

export function validateForegroundHeader(report,{source,root}){
  assert.equal(source,path.join(root,'output/unreal/exterior-20261002-r21b'));
  assert.equal(report.schemaVersion,2);assert.equal(report.owner,OWNER);assert.equal(report.status,'foreground-native-overlay-validated');denied(report);
  assert.equal(report.output,source);assert.equal(report.project,path.join(source,'Project/BreziTwin'));assert.equal(report.baseline,path.join(root,'output/unreal/exterior-20261001-r16a'));
  for(const k of ['nativeApplied','savedReloaded','allOriginalActorsAndWitnessedPoliciesPreserved','onlyOriginalMapChanged'])assert.equal(report[k],true,k);
  for(const k of ['landUseObserved','measuredElevation','nativeNormalTangentReadbackAvailable'])assert.equal(report[k],false,k);
  assert.equal(report.originalActorCount,5306);assert.equal(report.savedActorCount,5311);assert.equal(report.newContentPackageCount,5);assert.equal(report.newTextureObjects,0);
  assert.equal(report.originalMaterialGraphsPreserved,42);assert.equal(report.originalTextureObjectsPreserved,74);assert.equal(report.originalPlantMeshesPreserved,135);assert.equal(report.originalPlantLODsPreserved,405);
  assert.equal(report.sourceStudy.sha256,PLAN_SHA);assert.equal(report.sourcePreflight.sha256,PREFLIGHT_SHA);assert.equal(report.baseNativeReport.sha256,BASE_SHA);
  assert.deepEqual(report.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});assert.deepEqual(report.setbacksMm,{street:3000,east:3000});
}

export function validateForegroundProcess(proc,report,{project,root,logFile}){
  assert.equal(proc.code,0);assert.equal(proc.signal,null);assert.equal(proc.pid,report.nativeProcessId);assert(Number.isInteger(proc.pid)&&proc.pid>0);
  assert(Number.isFinite(Date.parse(proc.startedAt))&&Date.parse(proc.endedAt)>=Date.parse(proc.startedAt));
  assert.equal(proc.command,'/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd');assert.equal(proc.args[0],path.join(project,'BreziTwin.uproject'));
  for(const arg of ['-nullrhi','-run=pythonscript','-script='+path.join(root,OWNER),'-abslog='+logFile])assert(proc.args.includes(arg));
}

export function validateForegroundContent(before,after,packages){
  assert.equal(Object.keys(before).length,3975);assert.equal(packages.length,5);assert.equal(new Set(packages).size,5);
  assert(packages.every(p=>p.startsWith('Brezi/CanopyForeground20261002R21/')&&p.endsWith('.uasset')&&!p.includes('..')));
  assert.deepEqual(Object.keys(after).sort(),[...Object.keys(before),...packages].sort());
  assert.deepEqual(Object.keys(before).filter(k=>JSON.stringify(before[k])!==JSON.stringify(after[k])).sort(),['Brezi/Maps/Brezi.umap']);
}

export function validateForegroundActors({before,expected,saved,report,groups}){
  assert.equal(Object.keys(before).length,5306);assert.equal(Object.keys(expected).length,5311);assert.equal(Object.keys(saved).length,5311);
  const added=report.addedActors;assert.deepEqual(Object.keys(added).sort(),[FLOOR,...groups.map(g=>g.id)].sort());assert.equal(new Set(Object.values(added)).size,5);
  assert.deepEqual(Object.keys(saved).sort(),[...Object.keys(before),...Object.values(added)].sort());
  for(const [p,row]of Object.entries(before)){assert.deepEqual(expected[p],row,'Counterfactual changed old actor '+p);assert.deepEqual(saved[p],row,'Saved old actor changed '+p);}
  assert.deepEqual(expected,saved,'Actual saved counterfactual differs');
  for(const [id,p]of Object.entries(added)){
    const actor=saved[p],floor=id===FLOOR;assert(actor&&!before[p]);assert.equal(actor.label,id);assert.equal(actor.actorTick,false);assert.equal(actor.hidden,false);assert.deepEqual(actor.transform,identity);
    assert.deepEqual(actor.tags,[TAG,'BreziGenerated',...(!floor?['BreziLawnDetail']:[])].sort());
    assert.equal(actor.class,floor?'/Script/Engine.StaticMeshActor':'/Script/BreziTwin.BreziVegetationPatch');
    const components=actor.components.filter(c=>c.mesh);assert.equal(components.length,1);const c=components[0];assert.deepEqual(c.transform,identity);assert.equal(c.visible,true);assert.equal(c.hiddenInGame,false);
    assert.equal(c.collision,'<CollisionEnabled.NO_COLLISION: 0>');assert.equal(c.collisionProfile,'NoCollision');assert.equal(c.navigation,false);assert.equal(c.componentTick,false);assert.equal(c.overlapEvents,false);
    assert.equal(c.mobility,'<ComponentMobility.STATIC: 0>');assert.equal(c.attachParent,null);assert.deepEqual(c.overrideMaterials,[]);
    assert.equal(c.neighborRenderPolicy.cast_shadow,false);assert.equal(c.neighborRenderPolicy.affect_distance_field_lighting,false);assert.equal(c.neighborRenderPolicy.visible_in_ray_tracing,true);
    if(floor){assert.equal(c.mesh,report.newMesh);assert.deepEqual(c.materials,[report.newMaterial.asset]);assert.equal(c.maxDrawDistanceCm,6000);}
    else{
      const group=groups.find(g=>g.id===id),rb=report.savedReadback.groups.find(g=>g.id===id);assert(group&&rb);assert.equal(actor.detailDensityScaling,true);
      assert.equal(c.class,'/Script/Engine.HierarchicalInstancedStaticMeshComponent');assert.equal(c.mesh,group.nativeMesh);assert.deepEqual(c.materials,group.nativeMaterials);
      assert.equal(c.instanceCount,group.instances.length);assert(hashLike(c.orderedInstanceTransformsSha256)&&hashLike(rb.orderedInstanceTransformsSha256));assert.deepEqual(c.instanceCullCm,[4500,6000]);
      // Full witness uses [translation,quaternion,scale] lists; the native
      // source-loop receipt uses named transform dictionaries. Their hashes
      // cannot be equated. Exact expected/saved full-witness equality above
      // protects the ordered list representation; the frozen executed native
      // loop compares every source root and pins its dictionary representation.
    }
  }
}

// Python canonical float spelling and the frozen source validator reproduce
// actual floor F32 corner hashes and material graph policy independently of
// claims in the native JSON. This runs no Unreal, package writer or renderer.
const canonicalCheck=`import hashlib,importlib.util,json,sys
from pathlib import Path
sys.dont_write_bytecode=True
helper,report_path=sys.argv[1:];s=importlib.util.spec_from_file_location('r8_r21_source_cpu',helper);n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
r=json.load(open(report_path));b=n.guard.load_source();preflight,glb=n.validated_preflight(Path(r['sourcePreflight']['path']),b)
read=lambda key:json.load(open(r[key]['path']))
before,expected,saved=(read(k)for k in ['beforeActorWitness','expectedActorWitness','savedActorWitness']);n.guard.validate_actor_delta(before,expected,saved,list(r['addedActors'].values()))
for key,value in [('beforeActorWitnessSha256',before),('expectedActorWitnessSha256',expected),('savedActorWitnessSha256',saved)]:assert r[key]==n.digest(value)
materials=read('originalMaterialTextureWitness');assert len(materials['graphs'])==42 and len(materials['textures'])==74
assert n.digest(materials)==r['originalMaterialTextureBeforeSha256']==r['originalMaterialTextureSavedSha256']
original=b['inputs']['nativeR16']['materials']['materials']['context_meadow']['graph'];rb=r['savedReadback'];n.guard.validate_graph_copy(original,rb['materialGraph']);n.guard.validate_graph_copy(original,r['newMaterial']['graph'])
assert rb['materialGraph']==r['newMaterial']['graph'] and n.digest(rb['materialGraph'])==rb['materialGraphSha256']==r['newMaterial']['graphSha256']
floor=b['geometry']['mesh'];assert n.digest(floor)==rb['floor']['sourceGeometrySha256'];assert n.digest(n.guard.geometry_corners(floor))==rb['floor']['orderedNativeF32CornersSha256']
assert r['sourceAudit']==b['audit'];assert r['newMaterial']['sourceGraphSha256']==n.guard.SOURCE_GRAPH_SHA
assert r['newMaterial']['originalWorldPositionShaderOffsets']==r['newMaterial']['copiedWorldPositionShaderOffsets']==rb['worldPositionShaderOffsets']
print(json.dumps({'source':b['audit'],'nativeReceiptCanonicalVerified':True,'nativeGeometryWasReadByExecutedFrozenHelper':True,'nativeNormalsTangentsAvailable':False}))`;

export async function loadEditorSourceEvidence(source,{root}={}){
  source=path.resolve(source);root=path.resolve(root);const historicalGuards=[];
  for(const [version,h]of Object.entries(FROZEN_GUARDS)){const file=fileURLToPath(new URL(`./exterior-editor-source-r${version}.mjs`,import.meta.url));assert.equal(await sha(file),h,'Frozen delegated source guard changed');historicalGuards.push(file);}
  const names=await fs.readdir(source),reports=names.filter(n=>/^foreground-overlay-report(?:-r\d+)?\.json$/.test(n));
  if(!reports.length){const evidence=await loadR6(source,{root});evidence.additionalClosureFiles.push(...historicalGuards);return evidence;}
  assert.deepEqual(reports,['foreground-overlay-report-r2.json'],'Only the explicitly reviewed R21 native-r2 version is accepted');
  assert(!names.some(n=>n==='exterior-import-report.json'||n==='canopy-transmission-native-report.json'||(/overlay-report/.test(n)&&n!==reports[0])),'Copied or foreign overlay receipt rejected');
  const project=path.join(source,'Project/BreziTwin'),reportPath=path.join(source,reports[0]),report=await read(reportPath);validateForegroundHeader(report,{source,root});const closure=new Set([reportPath,...historicalGuards]);
  async function pinned(row){assert(row&&path.isAbsolute(row.path)&&path.resolve(row.path)===row.path&&hashLike(row.sha256)&&Number.isInteger(row.bytes)&&row.bytes>=0);const stat=await fs.lstat(row.path);assert(stat.isFile()&&!stat.isSymbolicLink());assert.equal(stat.size,row.bytes);assert.equal(await sha(row.path),row.sha256);closure.add(row.path);return row.path;}
  const pj=async row=>read(await pinned(row));
  const base=await pj(report.baseNativeReport),plan=await pj(report.sourceStudy),preflight=await pj(report.sourcePreflight);assert.equal(base.status,'exterior-import-validated');assert.equal(base.savedReloaded,true);
  assert.equal(plan.owner,'scripts/unreal/exterior-canopy-foreground-study.py');assert.equal(plan.status,'source-only-bounded-artistic-foreground-native-pending');denied(plan);assert.equal(plan.nativeApplied,false);
  assert.equal(preflight.schemaVersion,2);assert.equal(preflight.owner,OWNER);assert.equal(preflight.nativeExecuted,false);assert.equal(preflight.status,'foreground-source-preflight-validated-native-pending');
  for(const row of [...Object.values(plan.inputFiles),plan.geometry,plan.roots,plan.materialRecipe,preflight.sourceGLB,preflight.primaryActorApi])await pinned(row);
  const roots=await pj(plan.roots);assert.equal(roots.groups.length,4);assert.deepEqual(roots.groups.map(g=>g.meshId),MODEL_IDS);assert.deepEqual(roots.groups.map(g=>g.instances.length),COUNTS);
  const before=await pj(report.baseContentInventory),after=await pj(report.afterContentInventory);assert.deepEqual(Object.keys(base.afterAssetHashes).sort(),Object.keys(before).map(k=>path.join(base.project,'Content',k)).sort());
  for(const [relative,row]of Object.entries(before))assert.equal(row.sha256,base.afterAssetHashes[path.join(base.project,'Content',relative)]);
  const packages=[ownPackage(report.newMesh),ownPackage(report.newMaterial.asset),...report.importPipelineAssets.map(ownPackage)];assert.deepEqual(report.importPipelineAssets.map(p=>p.split('.')[0]).sort(),['Assets','Materials','Level'].map(n=>PREFIX+'/Pipeline/'+n).sort());assert.deepEqual([...report.newContentPackages].sort(),[...packages].sort());validateForegroundContent(before,after,packages);
  const proof=await pj(report.protectedProjectProof),protectedBefore=await pj(report.protectedProjectBefore);assert.deepEqual(proof,protectedBefore);assert.equal(proof.owner,OWNER);assert.equal(proof.schemaVersion,1);assert.equal(proof.status,'foreground-protected-project-byte-validated');assert.equal(proof.originalProjectBytesPreserved,true);assert.equal(proof.fileCount,132);assert.equal(Object.keys(proof.files).length,132);
  const projectProof={};for(const [relative,row]of Object.entries(proof.files)){assert(relative==='BreziTwin.uproject'||/^(Config|Source|Binaries)\//.test(relative));assert(!path.isAbsolute(relative)&&path.normalize(relative)===relative&&!relative.includes('..'));assert.equal(row.source,path.join(base.project,relative));assert.equal(row.destination,path.join(project,relative));assert.equal(row.independentInodes,true);projectProof[relative]={sha256:row.sha256,bytes:row.bytes};}
  const clone=await pj(report.projectClone);assert.equal(clone.status,'verified-byte-identical-independent-apfs-r21-project-clone-before-foreground-native');assert.equal(clone.fileCount,4107);assert.equal(clone.nativeExecuted,false);assert.deepEqual(clone.baseNativeReport,report.baseNativeReport);assert.deepEqual(clone.selectedPlan,report.sourceStudy);for(const k of ['byteValidationHelper','baseByteInventoryReferencePlan'])await pinned(clone[k]);
  const module=report.nativeModuleWitness;assert.equal(module.source,path.join(base.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));assert.equal(module.destination,path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));assert.equal(module.sha256,MODULE_SHA);assert.equal(module.bytes,2818384);assert.equal(module.independentInodes,true);await pinned({path:module.destination,sha256:module.sha256,bytes:module.bytes});const donor=await fs.stat(module.source),own=await fs.stat(module.destination);assert(donor.dev!==own.dev||donor.ino!==own.ino);closure.add(module.source);
  const processPath=path.join(source,'foreground-native-r2.log.json'),processReceiptPath=path.join(source,'foreground-native-r2-process.json'),proc=await read(processPath),processReceipt=await read(processReceiptPath);assert.equal(proc.code,0);assert.equal(proc.signal,null);assert.equal(proc.pid,report.nativeProcessId);assert(Number.isInteger(proc.pid)&&proc.pid>0);assert(Number.isFinite(Date.parse(proc.startedAt))&&Date.parse(proc.endedAt)>=Date.parse(proc.startedAt));assert.equal(proc.command,'/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd');assert.equal(proc.args[0],path.join(project,'BreziTwin.uproject'));assert(proc.args.includes('-nullrhi')&&proc.args.includes('-run=pythonscript')&&proc.args.includes('-script='+path.join(root,OWNER)));
  assert.equal(processReceipt.processFile,processPath);assert.equal(processReceipt.processFileSha256,await sha(processPath));assert.equal(processReceipt.reportSha256,await sha(reportPath));assert.equal(processReceipt.logFile,path.join(source,'foreground-native-r2.log'));assert.equal(processReceipt.logSha256,await sha(processReceipt.logFile));validateForegroundProcess(proc,report,{project,root,logFile:processReceipt.logFile});assert.equal(processReceipt.sourcePinsUnchangedAfterNative,true);
  for(const f of [processPath,processReceiptPath,processReceipt.logFile])closure.add(f);
  for(const [file,h]of Object.entries({...report.inputFiles,...report.pipelineFiles, ...processReceipt.sourcePinsBeforeNative})){const stat=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:stat.size});}
  assert.equal(report.pipelineFiles[path.join(root,OWNER)],HELPER_SHA);assert.equal(report.pipelineFiles[path.join(root,'scripts/unreal/exterior-canopy-foreground-guards.py')],GUARD_SHA);
  const beforeActors=await pj(report.beforeActorWitness),expectedActors=await pj(report.expectedActorWitness),savedActors=await pj(report.savedActorWitness);validateForegroundActors({before:beforeActors,expected:expectedActors,saved:savedActors,report,groups:roots.groups});
  const oldMaterials=await pj(report.originalMaterialTextureWitness);assert.equal(Object.keys(oldMaterials.graphs).length,42);assert.equal(Object.keys(oldMaterials.textures).length,74);for(const [id,row]of Object.entries(base.materials.materials))assert.deepEqual(oldMaterials.graphs[id],{asset:row.asset,graph:row.graph});
  const rb=report.savedReadback;assert.equal(rb.savedGroups,4);assert.equal(rb.savedInstances,512);assert.equal(rb.floor.mesh,report.newMesh);assert.equal(rb.floor.triangles,1843);for(const k of ['nativeFloat32RepresentationExact','triangleOrderPreserved','positionUV0UV1TopologyWindingVerified'])assert.equal(rb.floor[k],true);assert.equal(rb.floor.nativeNormalTangentReadbackAvailable,false);assert.equal(rb.allNewVisualsNoCollision,true);assert.equal(rb.runtimeQualityPredicateSourceVerified,true);assert.equal(rb.runtimeQualityLightingDiagnosticReadbackAvailable,false);
  assert.deepEqual(rb.groups.map(g=>g.meshId),MODEL_IDS);assert.deepEqual(rb.groups.map(g=>g.instances),COUNTS);for(const [i,g]of rb.groups.entries()){const sourceGroup=roots.groups[i],model=roots.models[g.meshId];assert.equal(g.id,sourceGroup.id);assert.equal(g.actor,report.addedActors[g.id]);assert.equal(g.nativeMesh,model.nativeMesh);assert.deepEqual(g.materials,model.nativeMaterials);assert.deepEqual(g.lodScreens,model.lodScreens);assert.deepEqual(g.lodTriangles,model.decodedLods.map(v=>v.triangles));assert.equal(g.allOrderedSourceTransformsCompared,true);assert.equal(g.detailDensityScaling,true);assert.equal(g.ownNamespaceVerified,true);assert.equal(g.runtimeQualityClassificationTag,'BreziLawnDetail');assert.equal(g.runtimeQualityPredicateSourceVerified,true);assert.deepEqual(g.cullCm,[4500,6000]);assert.equal(g.translationScaleToleranceCm,.003);assert.equal(g.quaternionTolerance,.00003);assert(hashLike(g.orderedInstanceTransformsSha256));}
  assert.equal(report.newMaterial.newNodes,3);assert.equal(report.newMaterial.originalPBRNodesPreserved,104);assert.equal(report.newMaterial.newTextureObjects,0);assert.deepEqual(report.newMaterial.compileErrors,[]);assert.equal(report.newMaterial.nativeAppearanceAccepted,false);
  const checked=await exec('python3',['-c',canonicalCheck,path.join(root,OWNER),reportPath],{timeout:60000,maxBuffer:1024*1024});const canonical=JSON.parse(checked.stdout);assert.equal(canonical.nativeReceiptCanonicalVerified,true);
  for(const row of [report.baseContentInventory,report.afterContentInventory,report.protectedProjectProof,report.beforeActorWitness,report.expectedActorWitness,report.savedActorWitness,report.originalMaterialTextureWitness])assert(row.path.startsWith(source+path.sep));
  const views=path.join(project,'Content/Data/viewpoints.json');assert.equal(await sha(views),plan.inputFiles.views.sha256);closure.add(views);
  const summary={mode:'canopy-foreground-overlay-r2',nativeProcessId:proc.pid,originalActors:5306,newActors:5,savedActors:5311,newGroups:4,newRoots:512,surfaceTriangles:1843,newPackages:5,newTextures:0,sourceSurfaceAreaM2:plan.audit.surfaceAreaM2,sourceMicroreliefCm:plan.audit.maximumMicroreliefCm,sourceLandUse:'ARTISTIC_UNSURVEYED_CLEARING_TRANSITION',fullWitnessTransformEncoding:'ordered lists',nativeSourceLoopTransformEncoding:'ordered dictionaries',nativeNormalTangentReadbackAvailable:false,nativeAppearanceAccepted:false,fullPhotorealismAccepted:false,performanceAccepted:false};
  return {mode:summary.mode,project,nativeReceiptPath:reportPath,base,summary,contentInventory:after,projectProof,additionalClosureFiles:[...closure],nativeModuleWitness:module,moduleWitnessSource:report.baseNativeReport,receiptSummary:{baseNativeReport:report.baseNativeReport,sourceStudy:report.sourceStudy,sourcePreflight:report.sourcePreflight,savedReloaded:true,savedOriginalMaterialsEvidence:'Actual frozen helper before/after canonical equality plus exact unchanged original serialized packages; no separate saved-material-witness file.',summary}};
}
