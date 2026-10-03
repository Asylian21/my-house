// Closed R23 original-roof-map adapter. Saved native evidence and fresh Editor
// captures remain separate from appearance, performance and Shipping acceptance.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence as loadR8,validateProjectClosure} from './exterior-editor-source-r8.mjs';
export {validateProjectClosure};
const OWNER='scripts/unreal/exterior-roof-pbr-native.py',HELPER_SHA='fe82492d157997a3e65b289297a4ddd6db81653a558350118a13d0c7c5ef648f';
const PLAN_SHA='0370301cb33688419b1940dd7c812f5fbedf8c7590a5df09b3e5e6e1de26000b',PREFLIGHT_SHA='987de6ebc672876d3702b15c83ef353559b19c0b510fd4e0456585abcc70d7f9';
const BASE_SHA='40ccc7cc686e2beafc05e5248eb8abe371f23bc8ad470c05284d4c442ed950da',MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const R8_SHA='b2161432c2980317188c3c9d1bc6b143a94badc1fbaef97130e267677f0e2ca4';
const PREFIX='/Game/Brezi/RoofPbr20261002R23';
const exec=promisify(execFile),read=async p=>JSON.parse(await fs.readFile(p,'utf8'));
const hashLike=h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h);
const sha=async file=>{const h=createHash('sha256');for await(const b of createReadStream(file))h.update(b);return h.digest('hex');};
export function validateRoofHeader(r,{source,project}){
  assert.equal(r.schema,'brezi-original-roof-pbr-component-overlay-r1');assert.equal(r.owner,OWNER);
  assert.equal(r.status,'verified-saved-original-roof-pbr-component-overlay');assert.equal(r.output,source);assert.equal(r.project,project);
  for(const k of ['nativeAppearanceAccepted','performanceAccepted','fullPhotorealismAccepted','shippingPackageProduced','nativeMaterialPackagesIndependentlyReloaded','nativeNormalTangentReadbackAvailable'])assert.equal(r[k],false);
  for(const k of ['savedMapUnloadedReloaded','nativeApplied','originalR18bUnchanged','originalContentExceptMapByteIdentical'])assert.equal(r[k],true);
  assert.equal(r.baseNativeReport.sha256,BASE_SHA);assert.equal(r.sourceStudy.sha256,PLAN_SHA);assert.equal(r.selectedPreflight.sha256,PREFLIGHT_SHA);
  assert.equal(r.existingActorCount,5338);assert.equal(r.existingMaterialGraphsPreserved,51);assert.equal(r.existingTextureObjectsPreserved,77);
  assert.equal(r.geometryChanges,0);assert.equal(r.originalStaticMeshSlotChanges,0);assert.equal(r.newImportPipelineAssets,0);
  assert.deepEqual(r.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});assert.deepEqual(r.setbacksMm,{street:3000,east:3000});
  assert.deepEqual(r.baselineRecordedPlantLibrary,{masters:135,lods:405,newNativePlantLodReadbackPerformed:false});
}
export function validateRoofActorDelta(before,expected,saved,targets,changes){
  assert.equal(Object.keys(before).length,5338);assert.equal(targets.length,4);assert.equal(changes.length,4);
  const result=structuredClone(before),material=PREFIX+'/Materials/M_roof_tiles_original.M_roof_tiles_original';
  assert.equal(new Set(targets.map(t=>t.actor)).size,4);
  for(const [i,t] of targets.entries()){
    assert.equal(t.slot,0);assert.deepEqual(before[t.actor],t.originalSavedActorWitness);
    const parts=result[t.actor].components.filter(c=>c.name===t.componentName&&c.class===t.componentClass);assert.equal(parts.length,1);
    const c=parts[0];assert.equal(c.mesh,t.mesh);assert.deepEqual(c.materials,[t.oldMaterial]);assert.deepEqual(c.overrideMaterials,[]);
    c.materials=[material];c.overrideMaterials=[material];
    assert.deepEqual(changes[i],{sourceMeshId:t.sourceMeshId,actor:t.actor,componentName:t.componentName,slot:0,mesh:t.mesh,beforeMaterial:t.oldMaterial,afterMaterial:material,changedFields:['materials','overrideMaterials']});
  }
  assert.deepEqual(expected,result);assert.deepEqual(saved,result);
}
export function validateRoofContentDelta(before,after,packages,delta){
  assert.equal(Object.keys(before).length,4027);assert.equal(packages.length,4);assert.equal(new Set(packages).size,4);
  assert(packages.every(p=>p.startsWith(PREFIX+'/')&&!p.includes('..')));assert(Object.keys(before).every(k=>Object.hasOwn(after,k)));
  const changed=Object.keys(before).filter(k=>before[k].sha256!==after[k].sha256||before[k].bytes!==after[k].bytes).sort();assert.deepEqual(changed,['Brezi/Maps/Brezi.umap']);
  const added=Object.keys(after).filter(k=>!Object.hasOwn(before,k)).sort(),expected=packages.map(p=>p.slice('/Game/'.length));
  assert(added.every(k=>/\.(uasset|uexp|ubulk)$/.test(k)&&expected.includes(k.replace(/\.[^.]+$/,''))));
  assert.deepEqual(added.filter(k=>k.endsWith('.uasset')).sort(),expected.map(k=>k+'.uasset').sort());
  assert.deepEqual(delta,{changedFiles:changed,newFiles:added,newUassetPackages:4,protectedOriginalFilesByteIdentical:4026});
}
const nativeCheck=`import importlib.util,json,sys
sys.dont_write_bytecode=True
s=importlib.util.spec_from_file_location('r9_frozen_roof_source',sys.argv[1]);n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
r=n.read(sys.argv[2]);b=n.guard.load_source();n.validate_preflight(r['selectedPreflight']['path'],b)
read=lambda key:n.read(r[key]['path'])
before=read('beforeActorWitness');expected,changes=n.guard.expected_witness(before,b['targets']);saved=read('savedActorWitness')
assert before==b['baseSaved'] and read('expectedActorWitness')==expected==saved and changes==r['componentMaterialOverrides']
assert [r[k]for k in ('beforeActorWitnessSha256','expectedActorWitnessSha256','savedActorWitnessSha256')]==[n.digest(v)for v in (before,expected,saved)]
old=read('existingMaterialsBefore');after=read('existingMaterialsSaved');assert old==after and len(old['graphs'])==51 and len(old['textures'])==77
assert r['existingMaterialsBeforeSha256']==r['existingMaterialsSavedSha256']==n.digest(old)
base=n.read(b['base']['baseNativeReport']['path'])
for key,row in base['materials']['materials'].items():assert old['graphs']['original:'+key]['asset']==row['asset'] and old['graphs']['original:'+key]['graph']==row['graph']
for key,row in b['base']['materials']['materials'].items():assert old['graphs']['neighbor:'+key]['asset']==row['asset'] and old['graphs']['neighbor:'+key]['graph']==row['graph']
for family,rows in [('original',base['materials']['textures']),('neighbor',b['base']['materials']['textures'])]:
 for key,row in rows.items():assert old['textures'][family+':'+key]['asset']==row['asset']
mr=r['materialReport'];assert mr['owner']=='scripts/unreal/exterior-roof-pbr-materials.py' and mr['recipe']==b['recipe'] and mr['shaderCompileErrors']==[] and mr['nativeAppearanceAccepted'] is False and mr['asset']==n.guard.MATERIAL
assert set(mr['textures'])=={'albedo','normal','roughness'}
for role,row in mr['textures'].items():
 name='T_R23_RoofTiles_'+role+'_'+b['recipe']['maps'][role]['sha256'][:16]
 assert row['source']==b['recipe']['maps'][role] and row['asset']==n.guard.PREFIX+'/Textures/'+name+'.'+name
 n.materials.verify_texture_snapshot(row['snapshot'],role)
n.materials.verify_graph(mr['graph'],{k:v['asset']for k,v in mr['textures'].items()});assert r['nativeEnumPreflight']==mr['nativeEnumPreflight']
assert r['sourceAudit']==b['audit'] and r['sourceMeasurement']==b['sourceMeasurement']
neighbor=n.module('r9_roof_corner_source','exterior-neighbor-finish-native-r3.py');proofs=[]
for t in b['targets']:
 row=b['sourceRows'][t['sourceMeshId']];corners=neighbor.guard.native_corner_sequence(row)
 proofs.append(dict(sourceMeshId=row['id'],triangles=len(corners),orderedNativeF32CornersSha256=n.digest(corners),sourceGeometrySha256=n.digest(row),nativeFloat32RepresentationExact=True,triangleOrderPreserved=True,positionUVTopologyWindingVerified=True,nativeNormalTangentReadbackAvailable=False))
assert r['actualSavedTargetGeometry']==proofs and sum(p['triangles']for p in proofs)==332
packages=[mr['asset'].split('.')[0]]+[v['asset'].split('.')[0]for v in mr['textures'].values()]
print(json.dumps(dict(packages=packages,completeOriginalActors=5338,savedActors=5338,componentMaterialOverrides=4,unchangedOrderedNativeF32RoofTriangles=332,existingMaterialGraphs=51,existingTextureObjects=77,newMaterialGraphs=1,newTextureObjects=3,sourceMaximumRelativeUVMetricError=b['sourceMeasurement']['maximumRelativeMetricEdgeError'],nativeNormalTangentReadbackAvailable=False,materialPackagesIndependentlyReloaded=False)))`;
export async function loadEditorSourceEvidence(source,{root}={}){
  source=path.resolve(source);root=path.resolve(root);const names=await fs.readdir(source),name='roof-pbr-native-report.json';
  const guardFiles=[8,6,5,4,3].map(n=>fileURLToPath(new URL(`exterior-editor-source-r${n}.mjs`,import.meta.url)));
  assert.equal(await sha(guardFiles[0]),R8_SHA);
  if(!names.includes(name)){const e=await loadR8(source,{root});e.additionalClosureFiles.push(...guardFiles);return e;}
  assert.equal(source,path.join(root,'output/unreal/exterior-20261002-r23a'));
  assert(!names.some(n=>n==='exterior-import-report.json'||/overlay-report|transmission-native-report|visibility-native-report|foreground-overlay-report|curved-grass-native-report/.test(n)),'Roof source cannot contain copied base/foreign native reports');
  const project=path.join(source,'Project/BreziTwin'),receiptPath=path.join(source,name),r=await read(receiptPath),closure=new Set([receiptPath,...guardFiles]);validateRoofHeader(r,{source,project});
  async function pinned(pin){assert(pin&&path.isAbsolute(pin.path)&&path.resolve(pin.path)===pin.path&&hashLike(pin.sha256)&&Number.isInteger(pin.bytes)&&pin.bytes>=0);const s=await fs.lstat(pin.path);assert(s.isFile()&&!s.isSymbolicLink());assert.equal(s.size,pin.bytes);assert.equal(await sha(pin.path),pin.sha256);closure.add(pin.path);return pin.path;}
  const pj=async pin=>read(await pinned(pin));
  const base=await pj(r.baseNativeReport),plan=await pj(r.sourceStudy),preflight=await pj(r.selectedPreflight);
  assert.equal(r.baseNativeReport.path,path.join(root,'output/unreal/exterior-20261001-r18b/neighbor-finish-overlay-report-r3.json'));
  assert.equal(r.sourceStudy.path,path.join(root,'output/unreal/exterior-roof-pbr-20261002-r3-study/roof-pbr-source-plan.json'));
  assert.equal(r.selectedPreflight.path,path.join(root,'output/unreal/exterior-roof-pbr-20261002-r23-preflight-r1/source-preflight.json'));
  assert.equal(r.pipelineFiles[path.join(root,OWNER)],HELPER_SHA);assert.deepEqual(r.pipelineFiles,preflight.pipelineFiles);
  for(const [file,h] of Object.entries({...r.inputFiles,...r.pipelineFiles})){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  for(const key of ['beforeActorWitness','expectedActorWitness','savedActorWitness','existingMaterialsBefore','existingMaterialsSaved'])await pinned(r[key]);
  await pinned(r.projectClone);const beforeContent=await pj(r.baseContentInventory),contentInventory=await pj(r.afterContentInventory),projectProof=await pj(r.protectedProjectProof),baseProof=await pj(r.baseProtectedProjectProof);
  assert.deepEqual(r.baseContentInventory,base.afterContentInventory);assert.deepEqual(r.baseProtectedProjectProof,base.protectedProjectProof);
  assert.equal(Object.keys(contentInventory).length,4031);assert.equal(Object.keys(projectProof).length,132);
  assert.deepEqual(projectProof,Object.fromEntries(Object.entries(baseProof.files).map(([k,v])=>[k,{sha256:v.sha256,bytes:v.bytes}])));
  for(const [relative,row]of Object.entries(projectProof))assert(!path.isAbsolute(relative)&&path.normalize(relative)===relative&&!relative.startsWith('../')&&(relative==='BreziTwin.uproject'||/^(Config|Source|Binaries)\//.test(relative))&&hashLike(row.sha256)&&Number.isInteger(row.bytes));
  const native=JSON.parse((await exec('python3',['-c',nativeCheck,path.join(root,OWNER),receiptPath],{timeout:120000,maxBuffer:1024*1024})).stdout);
  validateRoofContentDelta(beforeContent,contentInventory,native.packages,r.assetDelta);
  const processPath=path.join(source,'roof-pbr-native.log.json'),processReceiptPath=path.join(source,'roof-pbr-native-process.json'),proc=await read(processPath),p=await read(processReceiptPath);
  assert.equal(p.processFile,processPath);assert.equal(p.processFileSha256,await sha(processPath));assert.equal(p.reportSha256,await sha(receiptPath));assert.equal(p.logFile,path.join(source,'roof-pbr-native.log'));assert.equal(p.logSha256,await sha(p.logFile));
  assert.equal(proc.code,0);assert.equal(proc.signal,null);assert.equal(proc.pid,r.nativeProcessId);assert(Number.isInteger(proc.pid)&&proc.pid>0);
  assert(Number.isFinite(Date.parse(proc.startedAt))&&Date.parse(proc.endedAt)>=Date.parse(proc.startedAt));
  assert.equal(proc.command,'/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd');assert.equal(proc.args[0],path.join(project,'BreziTwin.uproject'));
  for(const arg of ['-nullrhi','-run=pythonscript','-script='+path.join(root,OWNER),'-abslog='+p.logFile])assert(proc.args.includes(arg));
  assert.equal(p.sourcePinsUnchangedAfterNative,true);assert.equal(Object.keys(p.sourcePinsBeforeNative).length,99);assert.equal(p.controllerSha256BeforeNative,p.controllerSha256AfterNative);assert.equal(await sha(p.controller),p.controllerSha256BeforeNative);
  for(const[file,h]of Object.entries(p.sourcePinsBeforeNative)){const s=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:s.size});}
  for(const file of [processPath,processReceiptPath,p.logFile,p.controller])closure.add(file);
  const module=path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),w=r.nativeModuleWitness;
  assert.equal(w.source,path.join(base.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));assert.equal(w.destination,module);assert.equal(w.sha256,MODULE_SHA);assert.equal(w.bytes,2818384);assert.equal(w.independentInodes,true);
  const donor=await fs.stat(w.source),own=await fs.stat(module);assert(donor.dev!==own.dev||donor.ino!==own.ino);assert.equal(own.size,w.bytes);assert.equal(await sha(module),MODULE_SHA);closure.add(module);closure.add(w.source);
  const originalBase=await pj(base.baseNativeReport),summary={mode:'original-roof-pbr-component-overlay',nativeProcessId:proc.pid,...native,packages:undefined,contentFiles:4031,protectedProjectFiles:132,sourcePinsUnchangedAfterNative:99,nativeAppearanceAccepted:false,performanceAccepted:false,fullPhotorealismAccepted:false};
  return {mode:summary.mode,project,nativeReceiptPath:receiptPath,base:originalBase,summary,contentInventory,projectProof,additionalClosureFiles:[...closure],nativeModuleWitness:w,moduleWitnessSource:r.sourceStudy,receiptSummary:{baseNativeReport:r.baseNativeReport,sourceStudy:r.sourceStudy,selectedPreflight:r.selectedPreflight,savedMapUnloadedReloaded:true,materialPackagesIndependentlyReloaded:false,summary}};
}
