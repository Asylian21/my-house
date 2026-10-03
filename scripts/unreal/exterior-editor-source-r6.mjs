// Closed source receipt adapters for Editor pilots. CPU validation is not a
// native launch, image review, package, or performance acceptance claim.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence as loadR5,validateProjectClosure} from './exterior-editor-source-r5.mjs';
export {validateProjectClosure};

export const STUDY_SHA='6e73abcdfc5a0d7a712625f0468cf0a58c9e174e329947b4a04f1cfc846d9351';
export const SUPPLEMENT_SHA='b8c08e541138969e7649681034ea3749352054cf5d932de6d0d884f58564affd';
const ORIGINAL_SUPPLEMENT_SHA='f1692dd83cd5caa15800845b5e31a18eeecbf22cc8587f4fc55bcf8a66293b18';
const NATIVE_OWNER='scripts/unreal/exterior-neighbor-finish-native-r3.py';
const NATIVE_HELPER_SHA='5a64d2413944cd009d74f5bba7c99b6be4f7f2a04d23f88396366062ebe856ac';
const ORIGINAL_NATIVE_OWNER='scripts/unreal/exterior-neighbor-finish-native.py';
const DIAGNOSTIC_OWNER='scripts/unreal/exterior-neighbor-finish-diagnostic-r3.py';
const BASE_SHA='1f4fcf02a460153d8e2c691d301c5970bcb6c750439432c8f152b63be835e122';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const previousGuards=[5,4,3].map(v=>fileURLToPath(new URL(`./exterior-editor-source-r${v}.mjs`,import.meta.url)));
const PREFIX='/Game/Brezi/NeighborFinish20261001R18';
const PARTITIONS=['village_0_2_wall','village_0_2_roof','village_0_2_darkroof','neighborhood_0_2_wire',
  'neighborhood_0_2_village_wall','neighborhood_0_2_boundary_post'];
const exec=promisify(execFile),hashLike=v=>typeof v==='string'&&/^[a-f0-9]{64}$/.test(v);
const read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const sha=async p=>{const h=createHash('sha256');for await(const b of createReadStream(p))h.update(b);return h.digest('hex');};
const within=(parent,file)=>file.startsWith(parent+path.sep);
const flags=v=>{for(const key of ['nativeAppearanceAccepted','performanceAccepted','fullPhotorealismAccepted'])assert.equal(v[key],false);};
const packageKey=asset=>{assert(typeof asset==='string'&&asset.startsWith(PREFIX+'/'));return asset.split('.')[0].slice('/Game/'.length);};

export function validateNeighborNativeVersion(report,source,{root}){
  assert.equal(source,path.join(root,'output/unreal/exterior-20261001-r18b'));
  assert.equal(report.schemaVersion,3);assert.equal(report.owner,NATIVE_OWNER);
  assert.equal(report.status,'neighbor-finish-native-overlay-validated');
  assert.equal(report.nativeApplied,true);assert.equal(report.savedReloaded,true);
  assert.equal(report.pipelineFiles[path.join(root,NATIVE_OWNER)],NATIVE_HELPER_SHA);
}

export function validateDiagnosticViews(original,supplement,appended) {
  assert.equal(supplement.schemaVersion,3);assert.equal(supplement.owner,DIAGNOSTIC_OWNER);
  assert.equal(supplement.status,'source-only-neighbor-finish-diagnostic-native-pending');flags(supplement);
  assert.equal(supplement.nativeApplied,false);assert.equal(supplement.sourceStudy.sha256,STUDY_SHA);
  assert.deepEqual(supplement.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});
  assert.deepEqual(supplement.setbacksMm,{street:3000,east:3000});
  assert.deepEqual(supplement.numericalComparisonPolicy,{floatAuditPaths:[
    '$.audit.nearestAuthoredSourceRoadDistanceCm','$.audit.protectedPrivateDistanceCm','$.audit.selectedEyeDistancesCm.BU.3800911'],
    maximumLargerUlpDelta:1,maximumAbsoluteDeltaCm:4e-12,cameraAndAllOtherFieldsExact:true,integerBooleanStringTypesExact:true});
  assert.equal(original.coordinateSystem,'unreal-centimeters');assert(Array.isArray(original.views));
  const {views:oldViews,...oldRoot}=original,{views:newViews,...newRoot}=appended;
  assert.deepEqual(newRoot,oldRoot,'Diagnostic changed original viewpoint root metadata');
  assert.equal(newViews.length,oldViews.length+1);assert.deepEqual(newViews.slice(0,-1),oldViews);
  assert.deepEqual(newViews.at(-1),supplement.view);assert.equal(supplement.view.id,'neighbor-finish-close-r18');
  assert.equal(supplement.view.horizontalFovDegrees,68);assert.equal(new Set(newViews.map(v=>v.id)).size,newViews.length);
  for(const key of ['eyeCm','targetCm'])assert(Array.isArray(supplement.view[key])&&supplement.view[key].length===3&&supplement.view[key].every(Number.isFinite));
  assert(Math.hypot(...supplement.view.targetCm.map((v,i)=>v-supplement.view.eyeCm[i]))>.1);
  assert.equal(supplement.sourceCameraAudit.actualCameraNativeReadback,false);
  assert.equal(supplement.sourceCameraAudit.observedStreetAccessClaimed,false);assert.equal(supplement.sourceCameraAudit.surveyAccuracyClaimed,false);
  assert.deepEqual(supplement.changedCloneContentFiles,['Data/viewpoints.json']);
}

export function validateNeighborContentDelta(before,after,report,{diagnosticBase=false}={}) {
  assert(Object.keys(before).every(key=>Object.hasOwn(after,key)),'Original Content removed');
  const changed=Object.keys(before).filter(key=>before[key].sha256!==after[key].sha256||before[key].bytes!==after[key].bytes).sort();
  assert.deepEqual(changed,diagnosticBase?['Data/viewpoints.json']:['Brezi/Maps/Brezi.umap','Data/viewpoints.json']);
  const added=Object.keys(after).filter(key=>!Object.hasOwn(before,key)).sort();
  if(diagnosticBase){assert.deepEqual(added,[]);return;}
  assert.equal(Object.keys(report.meshes).length,37);assert.equal(Object.keys(report.materials.materials).length,9);
  assert.equal(Object.keys(report.materials.textures).length,3);
  assert.deepEqual(report.importPipelineAssets.map(packageKey).sort(),['Assets','Level','Materials'].map(x=>'Brezi/NeighborFinish20261001R18/Pipeline/'+x));
  const packages=[...Object.values(report.meshes),...Object.values(report.materials.materials).map(v=>v.asset),
    ...Object.values(report.materials.textures).map(v=>v.asset),...report.importPipelineAssets].map(packageKey);
  assert.equal(packages.length,52);assert.equal(new Set(packages).size,52);
  for(const key of added){const ext=path.extname(key);assert(['.uasset','.uexp','.ubulk'].includes(ext)&&packages.includes(key.slice(0,-ext.length)),
    'Unreported new neighbor asset or sidecar');}
  assert.deepEqual(added.filter(x=>x.endsWith('.uasset')).sort(),packages.map(p=>p+'.uasset').sort());
}

export function validateNeighborActorDelta({before,expected,saved,report,base,sourceRows}) {
  assert.equal(Object.keys(before).length,base.finalActorCount);assert.equal(report.componentChanges.length,6);
  assert.deepEqual(report.componentChanges.map(c=>c.sourceMeshId).sort(),[...PARTITIONS].sort());
  const counterfactual=structuredClone(before);
  for(const change of report.componentChanges) {
    const id=change.sourceMeshId;assert.equal(change.actor,base.geometry.actors[id]);assert.equal(change.beforeMesh,base.geometry.meshes[id]);
    const parts=counterfactual[change.actor].components.filter(c=>c.name===change.componentName);assert.equal(parts.length,1);
    const c=parts[0];assert.equal(c.mesh,change.beforeMesh);
    if(id==='village_0_2_darkroof') {
      assert.equal(change.operation,'hide-empty-source-chunk');assert.equal(change.afterMesh,change.beforeMesh);
      assert.deepEqual(change.changedFields,['visible','hiddenInGame','cast_shadow','cast_hidden_shadow']);
      c.visible=false;c.hiddenInGame=true;c.neighborRenderPolicy.cast_shadow=false;c.neighborRenderPolicy.cast_hidden_shadow=false;
    } else {
      assert.equal(change.operation,'replace-with-retained-source-chunk');assert.deepEqual(change.changedFields,['mesh']);
      assert.equal(change.afterMesh,report.meshes['neighbor_r18_retained_'+id]);c.mesh=change.afterMesh;
    }
  }
  const source=sourceRows.filter(r=>!r.sourceMeshId);assert.equal(source.length,32);
  assert.deepEqual(Object.keys(report.addedActors).sort(),source.map(r=>r.id).sort());
  const added=Object.values(report.addedActors);assert.equal(new Set(added).size,32);
  assert.deepEqual(Object.keys(saved).sort(),[...Object.keys(before),...added].sort());
  assert.deepEqual(Object.keys(expected).sort(),Object.keys(before).sort());
  for(const [id,row] of Object.entries(counterfactual)) {
    assert.deepEqual(expected[id],row,'Expected witness changes original policy beyond six owned components');
    assert.deepEqual(saved[id],row,'Saved original scene differs from exact expected original scene');
  }
  for(const row of source) {
    const actor=saved[report.addedActors[row.id]];assert.equal(actor.label,row.id);
    assert.equal(actor.actorTick,false);
    assert.deepEqual(actor.transform,[[0,0,0],[0,0,0,1],[1,1,1]]);
    const components=actor.components.filter(c=>c.mesh===report.meshes[row.id]);assert.equal(components.length,1);
    const c=components[0];assert.deepEqual(c.transform,actor.transform);assert.equal(c.navigation,false);assert.equal(c.collisionProfile,'NoCollision');
    assert(c.collision.includes('NO_COLLISION'));assert.equal(c.visible,true);assert.equal(c.hiddenInGame,false);
    assert.equal(c.componentTick,false);assert.equal(c.overlapEvents,false);assert.equal(c.maxDrawDistanceCm,65000);
    assert.equal(c.neighborRenderPolicy.cast_shadow,row.castShadow);
    const material=report.materials.materials[row.material]?.asset??base.materials.materials[row.material]?.asset;
    assert(material);assert.deepEqual(c.materials,[material]);
  }
}

export async function loadEditorSourceEvidence(source,{root}={}) {
  source=path.resolve(source);root=path.resolve(root);const project=path.join(source,'Project/BreziTwin'),closure=new Set();
  const names=await fs.readdir(source),overlayName='neighbor-finish-overlay-report-r3.json',baseName='editor-diagnostic-baseline-receipt-r2.json';
  const historicalBaseName='editor-diagnostic-baseline-receipt.json';
  const kinds=names.filter(n=>/(?:overlay-report(?:-r\d+)?|diagnostic-baseline-receipt(?:-r\d+)?)\.json$/.test(n)&&n!==historicalBaseName);
  assert(kinds.every(n=>[overlayName,baseName].includes(n)),'Unknown Editor overlay receipt kind');
  assert(kinds.length<=1,'Ambiguous diagnostic/native-overlay receipt');
  if(!kinds.length){assert(!names.includes(historicalBaseName),'Historical R2 supplement baseline is not an active R4 source');
    const e=await loadR5(source,{root});e.additionalClosureFiles.push(...previousGuards);return e;}
  assert.equal(path.dirname(source),path.join(root,'output/unreal'));
  assert(!names.includes('exterior-import-report.json')&&!names.includes('canopy-transmission-native-report.json'),'Typed neighbor source cannot carry a copied exterior/foreign overlay report');
  const diagnosticBase=kinds[0]===baseName,receiptPath=path.join(source,kinds[0]),report=await read(receiptPath);closure.add(receiptPath);
  assert(diagnosticBase||!names.includes(historicalBaseName),'Historical baseline receipt belongs only to the diagnostic baseline');
  assert.equal(report.schemaVersion,diagnosticBase?1:3);flags(report);assert.equal(report.shippingVerified,false);assert.equal(report.packageVerified,false);
  assert.equal(path.resolve(report.project),project);assert.equal(path.resolve(report.output),source);
  if(diagnosticBase){assert.equal(report.schema,'brezi-editor-diagnostic-base-r1');assert.equal(report.owner,'/root');
    assert.equal(report.status,'verified-source-owned-diagnostic-baseline-camera-only');assert.equal(report.nativeApplied,false);
    assert.equal(path.basename(source),'exterior-20261001-r18-close-baseline');
  }else validateNeighborNativeVersion(report,source,{root});
  async function pinned(pin){assert(pin&&path.isAbsolute(pin.path)&&path.resolve(pin.path)===pin.path&&hashLike(pin.sha256)&&Number.isInteger(pin.bytes)&&pin.bytes>=0);
    const stat=await fs.lstat(pin.path);assert(stat.isFile()&&!stat.isSymbolicLink());assert.equal(stat.size,pin.bytes);assert.equal(await sha(pin.path),pin.sha256);closure.add(pin.path);return pin.path;}
  const pj=async pin=>read(await pinned(pin));
  assert.equal(report.baseNativeReport.sha256,BASE_SHA);const base=await pj(report.baseNativeReport);
  assert.equal(base.status,'exterior-import-validated');assert.equal(base.savedReloaded,true);
  assert.deepEqual(base.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});assert.deepEqual(base.setbacksMm,{street:3000,east:3000});
  if(!diagnosticBase){assert.deepEqual(report.activeDesign,base.activeDesign);assert.deepEqual(report.setbacksMm,base.setbacksMm);}
  assert.equal(path.basename(path.dirname(report.baseNativeReport.path)),'exterior-20261001-r16a');
  assert.equal(report.sourceStudy.sha256,STUDY_SHA);const study=await pj(report.sourceStudy);
  assert.equal(study.owner,'scripts/unreal/exterior-neighbor-finish-study.py');assert.equal(study.status,'source-only-neighbor-finish-proposal-native-pending');flags(study);
  for(const [file,h] of Object.entries({...study.inputFiles,...study.payloadFiles})){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  assert.equal(report.diagnosticSupplement.sha256,SUPPLEMENT_SHA);const supplement=await pj(report.diagnosticSupplement);
  for(const [file,h] of Object.entries(supplement.inputFiles)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  assert.equal(supplement.originalR2Supplement.sha256,ORIGINAL_SUPPLEMENT_SHA);
  const originalSupplement=await pj(supplement.originalR2Supplement);
  assert.deepEqual(supplement.view,originalSupplement.view);assert.deepEqual(supplement.sourceCameraAudit,originalSupplement.sourceCameraAudit);
  assert.equal(supplement.appendedViewpoints.sha256,originalSupplement.appendedViewpoints.sha256);
  await pinned(supplement.originalDiagnosticProducer);await pinned(supplement.nativeRuntimeProbe);
  const generatorFile=path.join(root,supplement.owner),generatorStat=await fs.lstat(generatorFile);
  await pinned({path:generatorFile,sha256:supplement.generatorSha256,bytes:generatorStat.size});
  const originalViews=await pj(supplement.originalViewpoints),appendedViews=await pj(supplement.appendedViewpoints);
  validateDiagnosticViews(originalViews,supplement,appendedViews);
  const ownViews=path.join(project,'Content/Data/viewpoints.json');assert.equal(await sha(ownViews),supplement.appendedViewpoints.sha256);closure.add(ownViews);
  const before=await pj(report.baseContentInventory),after=await pj(report.afterContentInventory),protectedProof=await pj(report.protectedProjectProof);
  await pinned(report.projectClone);
  assert.equal(protectedProof.schemaVersion,1);
  if(diagnosticBase)assert([ORIGINAL_NATIVE_OWNER,NATIVE_OWNER].includes(protectedProof.owner));
  else assert.equal(protectedProof.owner,NATIVE_OWNER);
  assert.equal(protectedProof.status,'neighbor-finish-protected-project-byte-validated');assert.equal(protectedProof.originalProjectBytesPreserved,true);
  assert.equal(protectedProof.fileCount,Object.keys(protectedProof.files).length);
  const projectProof={};
  for(const [relative,row] of Object.entries(protectedProof.files)) {
    assert(!path.isAbsolute(relative)&&path.normalize(relative)===relative&&!relative.startsWith('../')&&
      (relative==='BreziTwin.uproject'||/^(Config|Source|Binaries)\//.test(relative)),'Protected proof escapes own project source/binary scope');
    assert.equal(row.source,path.join(base.project,relative));assert.equal(row.destination,path.join(project,relative));
    assert.equal(row.independentInodes,true);assert(hashLike(row.sha256)&&Number.isInteger(row.bytes)&&row.bytes>=0);
    projectProof[relative]={sha256:row.sha256,bytes:row.bytes};
  }
  assert.equal(Object.keys(before).length,Object.keys(base.afterAssetHashes).length);
  for(const [relative,row] of Object.entries(before))assert.equal(row.sha256,base.afterAssetHashes[path.join(base.project,'Content',relative)]);
  assert.equal(before['Data/viewpoints.json'].sha256,supplement.originalViewpoints.sha256);assert.equal(after['Data/viewpoints.json'].sha256,supplement.appendedViewpoints.sha256);
  validateNeighborContentDelta(before,after,report,{diagnosticBase});
  const witness=report.nativeModuleWitness,module=path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib');
  assert.equal(witness.source,path.join(base.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));assert.equal(witness.destination,module);
  assert.equal(witness.sha256,MODULE_SHA);assert.equal(witness.bytes,2818384);assert.equal(witness.independentInodes,true);
  const donor=await fs.stat(witness.source),own=await fs.stat(module);assert(donor.dev!==own.dev||donor.ino!==own.ino);
  assert.equal(own.size,witness.bytes);assert.equal(await sha(module),MODULE_SHA);closure.add(witness.source);closure.add(module);
  let summary={mode:diagnosticBase?'diagnostic-base':'neighbor-finish-overlay',supplementalViews:1,nativeAppearanceAccepted:false,performanceAccepted:false,fullPhotorealismAccepted:false};
  if(!diagnosticBase){
    assert.equal(report.pipelineFiles[path.join(root,NATIVE_OWNER)],NATIVE_HELPER_SHA);
    const protectedBefore=await pj(report.protectedProjectBefore);
    assert.deepEqual(protectedBefore,protectedProof,'Saved protected project proof differs from before receipt');
    const processPath=path.join(source,'neighbor-finish-native-r3.log.json'),processReceiptPath=path.join(source,'neighbor-finish-native-r3-process.json');
    const processReceipt=await read(processReceiptPath),proc=await read(processPath);
    assert.equal(processReceipt.processFile,processPath);assert.equal(processReceipt.processFileSha256,await sha(processPath));
    assert.equal(processReceipt.reportSha256,await sha(receiptPath));assert.equal(processReceipt.logFile,path.join(source,'neighbor-finish-native-r3.log'));
    assert.equal(processReceipt.logSha256,await sha(processReceipt.logFile));
    assert.equal(proc.code,0);assert.equal(proc.signal,null);assert.equal(proc.pid,report.nativeProcessId);assert(Number.isInteger(proc.pid)&&proc.pid>0);
    assert(Number.isFinite(Date.parse(proc.startedAt))&&Date.parse(proc.endedAt)>=Date.parse(proc.startedAt));
    assert.equal(proc.command,'/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd');
    assert.equal(proc.args[0],path.join(project,'BreziTwin.uproject'));assert(proc.args.includes('-nullrhi')&&proc.args.includes('-run=pythonscript'));
    assert(proc.args.includes('-script='+path.join(root,report.owner)));assert(proc.args.includes('-abslog='+processReceipt.logFile));
    for(const file of [processPath,processReceiptPath,processReceipt.logFile])closure.add(file);
    const beforeActors=await pj(report.beforeActorWitness),expectedActors=await pj(report.expectedActorWitness),savedActors=await pj(report.savedActorWitness);
    const originalMaterials=await pj(report.originalMaterialTextureWitness),savedOriginalMaterials=await pj(report.savedOriginalMaterialTextureWitness);
    assert.deepEqual(savedOriginalMaterials,originalMaterials,'Saved original42graphs74textures differ from before witness');
    assert.equal(Object.keys(originalMaterials.graphs).length,42);assert.equal(Object.keys(originalMaterials.textures).length,74);
    assert.equal(base.savedPlantReadback.length,135);assert.equal(base.savedPlantReadback.reduce((n,p)=>n+p.lodTriangles.length,0),405);
    for(const [id,row] of Object.entries(base.materials.materials))assert.deepEqual(originalMaterials.graphs[id],{asset:row.asset,graph:row.graph});
    const geometryPath=Object.keys(study.payloadFiles).find(p=>p.endsWith('/neighbor-finish-geometry.json'));assert(geometryPath);
    const recipesPath=Object.keys(study.payloadFiles).find(p=>p.endsWith('/neighbor-finish-recipes.json'));assert(recipesPath);
    const recipes=await read(recipesPath);assert.equal(report.materials.owner,'scripts/unreal/exterior-neighbor-finish-materials.py');
    assert.deepEqual(Object.keys(report.materials.materials).sort(),Object.keys(recipes).sort());
    for(const [id,row] of Object.entries(report.materials.materials)) {
      assert.deepEqual(row.recipe,recipes[id]);assert.deepEqual(row.shaderCompileErrors,[]);assert.equal(row.nativeAppearanceAccepted,false);
      assert(row.graph.nodes.length>0&&Object.keys(row.graph.roots).length>0);
    }
    const plaster=Object.values(recipes).find(r=>r.kind==='neighbor-plaster-scan');assert(plaster);
    assert.deepEqual(Object.keys(report.materials.textures).sort(),['albedo','normal','roughness']);
    for(const [role,row] of Object.entries(report.materials.textures)) {
      assert.equal(row.sourceSha256,plaster.maps[role].sha256);assert.equal(row.sourceRole,role);
      assert.deepEqual(row.snapshot.pixels,[2048,2048]);assert.equal(row.snapshot.srgb,role==='albedo');
      assert.equal(row.snapshot.flip_green_channel,role==='normal');
    }
    const glass=report.materials.materials.neighbor_window_dielectric;
    assert.equal(glass.proposedGlassOpacity,.08);assert.equal(glass.nativeGlassOpticalValues.opacity,Math.fround(.08));
    assert.equal(glass.nativeGlassOpticalValues.roughness,Math.fround(.12));assert.equal(glass.nativeGlassOpticalValues.metallic,0);
    assert.equal(glass.nativeGlassOpticalValues.indexOfRefraction,1.5);
    assert(glass.graph.flags.refraction_method.replace(/[^a-z]/gi,'').toLowerCase().includes('rmindexofrefraction'));
    assert.deepEqual(glass.graph.roots.REFRACTION[0],'BreziNeighborR18:proposed-glass-ior');
    const geometry=await read(geometryPath),rows=[...geometry.candidateMeshes,...geometry.unchangedRemainderMeshes.filter(r=>r.indices.length).map(r=>({...r,id:'neighbor_r18_retained_'+r.id,sourceMeshId:r.id}))];
    assert.equal(rows.length,37);validateNeighborActorDelta({before:beforeActors,expected:expectedActors,saved:savedActors,report,base,sourceRows:rows});
    const rb=report.savedReadback;assert.equal(rb.meshCount,37);assert.equal(rb.candidateMeshCount,32);assert.equal(rb.candidateTriangles,5095);assert.equal(rb.retainedTriangles,1720);
    assert.equal(rb.allNativeF32PositionUVTopologyOrderVerified,true);assert.equal(rb.nativeWindowOpeningsVerified,35);assert.equal(rb.old919TargetTrianglesRetiredFromRendering,true);
    assert.equal(rb.oldSourceAssetsPreserved,true);assert.equal(rb.allAddedVisualsNoCollision,true);assert.equal(rb.nativeNormalTangentReadbackAvailable,false);assert.equal(rb.nativeAppearanceAccepted,false);
    assert.deepEqual(Object.keys(rb.meshProofs).sort(),rows.map(r=>r.id).sort());
    for(const row of rows){const proof=rb.meshProofs[row.id];assert.equal(proof.sourceMeshId,row.id);assert.equal(proof.triangles,row.indices.length/3);
      for(const key of ['nativeFloat32RepresentationExact','triangleOrderPreserved','positionUVTopologyWindingVerified'])assert.equal(proof[key],true);
      assert.equal(proof.nativeNormalTangentReadbackAvailable,false);assert(hashLike(proof.sourceGeometrySha256)&&hashLike(proof.orderedNativeF32CornersSha256));}
    // Native receipts use Python canonical JSON with float32 values. Decode
    // the frozen source sidecar with the same numerical representation.
    const sourceScript=`import hashlib,json,struct,sys
d=json.load(open(sys.argv[1]));rows=list(d['candidateMeshes'])
for r in d['unchangedRemainderMeshes']:
 if r['indices']: rows.append(dict(r,id='neighbor_r18_retained_'+r['id'],sourceMeshId=r['id']))
f=lambda v:struct.unpack('<f',struct.pack('<f',v))[0]
h=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
out={}
for r in rows:
 p=[[f(f(v/100)*100) for v in q] for q in r['verticesCm']];u=[[f(v) for v in q] for q in r['uvs']];faces=[]
 for j in range(0,len(r['indices']),3):
  face=[tuple(p[i]+u[i]) for i in r['indices'][j:j+3]];faces.append(min(tuple(face[k:]+face[:k]) for k in range(3)))
 out[r['id']]=[h(r),h(faces)]
print(json.dumps(out))`;
    const decoded=await exec('python3',['-c',sourceScript,geometryPath],{timeout:60000,maxBuffer:1024*1024});
    const sourceHashes=JSON.parse(decoded.stdout);
    for(const row of rows){assert.equal(rb.meshProofs[row.id].sourceGeometrySha256,sourceHashes[row.id][0]);
      assert.equal(rb.meshProofs[row.id].orderedNativeF32CornersSha256,sourceHashes[row.id][1]);}
    const script="import hashlib,json,sys;print(json.dumps([hashlib.sha256(json.dumps(json.load(open(p)),sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest() for p in sys.argv[1:]]))";
    const {stdout}=await exec('python3',['-c',script,report.beforeActorWitness.path,report.expectedActorWitness.path,report.savedActorWitness.path],{timeout:60000,maxBuffer:1024*1024});
    const hashes=JSON.parse(stdout);assert.equal(report.beforeActorWitnessSha256,hashes[0]);assert.equal(report.savedActorWitnessSha256,hashes[2]);
    assert.equal(report.afterActorWitnessSha256,hashes[2],'Created full scene differs from actual reloaded scene');
    assert.equal(report.originalMaterialGraphsPreserved,42);assert.equal(report.originalTextureObjectsPreserved,74);assert.equal(report.originalBaselineProjectBytesPreserved,true);
    for(const [file,h] of Object.entries({...report.inputFiles,...report.pipelineFiles})){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
    summary={...summary,nativeProcessId:proc.pid,newMeshes:37,newMaterials:9,newTextures:3,newActors:32,retiredTargetTriangles:919};
  }
  for(const pin of [report.afterContentInventory,report.protectedProjectProof])assert(within(source,pin.path));
  for(const p of previousGuards)closure.add(p);
  return {mode:summary.mode,project,nativeReceiptPath:receiptPath,base,summary,contentInventory:after,projectProof,
    additionalClosureFiles:[...closure],nativeModuleWitness:witness,moduleWitnessSource:report.baseNativeReport,
    receiptSummary:{baseNativeReport:report.baseNativeReport,sourceStudy:report.sourceStudy,diagnosticSupplement:report.diagnosticSupplement,
      sourceOnlyDiagnosticBase:diagnosticBase,savedReloaded:diagnosticBase?false:true,summary}};
}
