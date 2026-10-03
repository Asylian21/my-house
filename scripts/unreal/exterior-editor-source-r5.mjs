// Closed R19 Editor source adapter. Receipt/CPU validation is separate from
// native capture, appearance, performance, and Shipping acceptance.
import assert from 'node:assert/strict';
import fs from 'node:fs/promises';
import {createReadStream} from 'node:fs';
import path from 'node:path';
import {createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {fileURLToPath} from 'node:url';
import {loadEditorSourceEvidence as loadR4,validateProjectClosure} from './exterior-editor-source-r4.mjs';
export {validateProjectClosure};
const OWNER='scripts/unreal/exterior-meadow-visibility-native.py';
const SCHEMA='brezi-meadow-ecology-visibility-component-overlay-r1';
const PLAN_SHA='b4f06196396acf60a12a32e0fb73e3a679fd9abf2f1761da812ab81fd3b07d08';
const HELPER_SHA='e82b54b06e139634bc8a9f592f931bff3855e254976a6902b233d23a312e28c2';
const BASE_SHA='1f4fcf02a460153d8e2c691d301c5970bcb6c750439432c8f152b63be835e122';
const EVIDENCE_SHA='2f9032afd061b5681844911959fb9247af8a1197a2c8cded78f1ee5cdbcd0ccb';
const GENERIC_SHA='10cc942f098e130f8f22f0acb9948f4381bdc0226d5db2af17a4665fd701bc6b';
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const ECOLOGY_IDS=[...['litter','twig','herb'].flatMap(f=>[0,1,2].map(i=>`canopy_ecology_${f}_${i}`)),
  'canopy_ecology_grass_0','canopy_ecology_grass_1'];
const read=async file=>JSON.parse(await fs.readFile(file,'utf8'));
const hashLike=h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h);
const sha=async file=>{const h=createHash('sha256');for await(const b of createReadStream(file))h.update(b);return h.digest('hex');};
const exec=promisify(execFile);
function falseFlags(row){for(const k of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingPackageProduced'])assert.equal(row[k],false);}

export function canonicalVisibilityTargets(base){
  assert.equal(base.status,'exterior-import-validated');assert.equal(base.savedReloaded,true);
  assert.deepEqual(base.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});assert.deepEqual(base.setbacksMm,{street:3000,east:3000});
  assert.equal(Object.keys(base.materials.materials).length,42);assert.equal(Object.keys(base.materials.textures).length,74);
  assert.equal(base.savedPlantReadback.length,135);assert.equal(base.savedPlantReadback.reduce((n,p)=>n+p.lodTriangles.length,0),405);
  const prototypes=base.nativeMeadow.prototypes;
  assert.deepEqual(Object.keys(prototypes).sort(),[0,1,2,3].map(i=>'LawnTuft'+i));
  for(const p of Object.values(prototypes)){assert.deepEqual(p.lodScreens,[1,.02500000037252903,.007000000216066837]);assert.deepEqual(p.lodProofs.map(r=>r.triangles),[256,64,24]);}
  const meadowMeshes=new Map(Object.entries(prototypes).map(([id,p])=>[p.mesh,id])),groups=base.geometry.groups;
  const meadow=Object.keys(groups).filter(id=>meadowMeshes.has(groups[id].mesh)).sort(),ecology=base.canopyEcology;
  assert.equal(meadow.length,471);assert.equal(meadow.reduce((n,id)=>n+groups[id].instances,0),477117);
  assert.equal(ecology.regionId,'village_nearest_grove');assert.equal(ecology.groupIds.length,130);assert.equal(new Set(ecology.groupIds).size,130);
  assert.deepEqual(ecology.savedReadback,{status:'verified-saved-grove-groups',groups:130,instances:24773,
    allNewVisualsNoCollision:true,orderedNativeTransformsVerifiedAfterReload:true});
  const ecologyIds=new Set(ecology.groupIds);assert(meadow.every(id=>!ecologyIds.has(id)));
  const ecologyMeshes=new Map(base.savedPlantReadback.filter(p=>ECOLOGY_IDS.includes(p.id)).map(p=>[p.mesh,p.id]));
  assert.deepEqual([...ecologyMeshes.values()].sort(),[...ECOLOGY_IDS].sort());
  assert(ecology.groupIds.every(id=>Object.hasOwn(groups,id)));assert.equal(ecology.groupIds.reduce((n,id)=>n+groups[id].instances,0),24773);
  const targets=[...meadow,...ecology.groupIds].sort().map(id=>{
    const row=groups[id];assert.equal(row.qualityDetail,true);assert(Number.isInteger(row.cullStartCm)&&Number.isInteger(row.cullEndCm));
    const local=meadowMeshes.has(row.mesh),masterId=local?meadowMeshes.get(row.mesh):ecologyMeshes.get(row.mesh);assert(masterId);
    const family=local?'meadow':masterId.split('_')[2],end=local?9000:{litter:8000,twig:10000,herb:12000,grass:10000}[family];
    assert.deepEqual([row.cullStartCm,row.cullEndCm],[Math.trunc(.8*end),end]);
    return {groupId:id,scope:local?'local-meadow':'grove-ecology',family,masterId,baseGroup:structuredClone(row),proposedCullCm:[18000,24000]};
  });
  assert.equal(targets.length,601);assert.equal(new Set(targets.map(t=>t.groupId)).size,601);
  return targets;
}

export function validateVisibilityWitness({before,saved,targets,deltas}){
  const expected=structuredClone(before),observed=[],used=new Set();
  for(const target of targets){
    const row=target.baseGroup,actor=expected[row.actor];assert(actor);assert.equal(actor.detailDensityScaling,true);
    const matches=actor.components.filter(c=>c.class.includes('HierarchicalInstancedStaticMeshComponent')&&c.mesh===row.mesh&&c.instanceCount===row.instances);
    assert.equal(matches.length,1);const c=matches[0];assert(!used.has(c.path));used.add(c.path);
    assert.equal(c.orderedInstanceTransformsSha256,row.transformsSha256);assert.deepEqual(c.instanceCullCm,[row.cullStartCm,row.cullEndCm]);
    assert.deepEqual(target.proposedCullCm,[18000,24000]);
    observed.push({groupId:target.groupId,scope:target.scope,family:target.family,actor:row.actor,component:c.path,
      beforeCullCm:structuredClone(c.instanceCullCm),afterCullCm:[18000,24000],instances:row.instances});
    c.instanceCullCm=[18000,24000];
  }
  assert.deepEqual(deltas,observed,'Cull receipts differ from actual before witness and selected source');
  assert.deepEqual(saved,expected,'Saved full scene differs beyond selected distance pairs');return expected;
}

export async function loadEditorSourceEvidence(source,{root}={}){
  source=path.resolve(source);root=path.resolve(root);const names=await fs.readdir(source),name='meadow-visibility-native-report.json';
  const guardFiles=['exterior-editor-source-r4.mjs','exterior-editor-source-r3.mjs'].map(n=>fileURLToPath(new URL(n,import.meta.url)));
  if(!names.includes(name)){const e=await loadR4(source,{root});e.additionalClosureFiles.push(...guardFiles);return e;}
  assert.equal(source,path.join(root,'output/unreal/exterior-20261001-r19a'));
  assert(!names.some(n=>n==='exterior-import-report.json'||n==='canopy-transmission-native-report.json'||/overlay-report|diagnostic-baseline-receipt/.test(n)),
    'R19 cannot carry copied base or foreign overlay receipts');
  const project=path.join(source,'Project/BreziTwin'),receiptPath=path.join(source,name),report=await read(receiptPath),closure=new Set([receiptPath,...guardFiles]);
  assert.equal(report.schema,SCHEMA);assert.equal(report.owner,OWNER);assert.equal(report.status,'verified-saved-meadow-ecology-visibility-component-overlay');falseFlags(report);
  assert.equal(report.output,source);assert.equal(report.project,project);assert.equal(report.savedMapUnloadedReloaded,true);
  for(const k of ['originalR16Unchanged','originalContentExceptMapByteIdentical'])assert.equal(report[k],true);
  assert.equal(report.nearSourceEmptyForegroundFixed,false);
  async function pinned(pin){assert(pin&&path.isAbsolute(pin.path)&&path.resolve(pin.path)===pin.path&&hashLike(pin.sha256)&&Number.isInteger(pin.bytes)&&pin.bytes>=0);
    const stat=await fs.lstat(pin.path);assert(stat.isFile()&&!stat.isSymbolicLink());assert.equal(stat.size,pin.bytes);assert.equal(await sha(pin.path),pin.sha256);closure.add(pin.path);return pin.path;}
  const pj=async pin=>read(await pinned(pin));
  async function pinsIn(value){if(!value||typeof value!=='object')return;if(Object.hasOwn(value,'path')&&Object.hasOwn(value,'sha256')&&Object.hasOwn(value,'bytes')){await pinned(value);return;}
    for(const child of Object.values(value))await pinsIn(child);}
  assert.equal(report.baseNativeReport.sha256,BASE_SHA);const base=await pj(report.baseNativeReport);
  assert.equal(report.baseNativeReport.path,path.join(root,'output/unreal/exterior-20261001-r16a/exterior-import-report.json'));
  assert.equal(report.selectedPlan.sha256,PLAN_SHA);const plan=await pj(report.selectedPlan);
  assert.equal(plan.schema,SCHEMA);assert.equal(plan.schemaVersion,1);assert.equal(plan.owner,'scripts/unreal/exterior-meadow-visibility-study.py');
  assert.equal(plan.status,'source-only-meadow-ecology-visibility-native-trial-pending');falseFlags(plan);assert.equal(plan.nativeExecuted,false);
  assert.deepEqual(plan.activeDesign,base.activeDesign);assert.deepEqual(plan.setbacksMm,base.setbacksMm);assert.deepEqual(plan.baseNativeReport,report.baseNativeReport);
  const targets=canonicalVisibilityTargets(base);assert.deepEqual(plan.targets,targets);assert.equal(base.finalActorCount,5306);
  assert.deepEqual(report.actualAudit,plan.audit);assert.deepEqual(report.scopes,plan.scopes);
  assert.deepEqual(plan.audit,{targetGroups:601,targetInstances:501890,meadowGroups:471,meadowInstances:477117,ecologyGroups:130,ecologyInstances:24773,
    allExteriorGroups:1980,allExteriorInstances:632026,allLevelActors:5306,materialGraphs:42,textureObjects:74,plantStaticMeshes:135,plantLods:405,
    newAssets:0,geometryChanges:0,materialChanges:0,transformChanges:0});
  assert.equal(report.effectiveCullOverrideGroups,601);assert.equal(report.effectiveCullOverrideInstances,501890);
  assert.equal(plan.newSourceFiles.nativeHelper.live.sha256,HELPER_SHA);assert.equal(plan.newSourceFiles.nativeHelper.live.path,path.join(root,OWNER));
  assert.equal(report.reusedBaseEvidencePlan.sha256,EVIDENCE_SHA);assert.equal(report.immutableGenericHelper.sha256,GENERIC_SHA);
  assert.deepEqual(report.reusedBaseEvidencePlan,plan.reusedBaseEvidencePlan);assert.deepEqual(report.immutableGenericHelper,plan.immutableGenericHelper);
  const evidence=await pj(report.reusedBaseEvidencePlan);assert.deepEqual(report.frozenPipeline,evidence.frozenPipeline);assert.deepEqual(report.consumedSourceSnapshot,evidence.consumedSourceSnapshot);
  await pinsIn(plan);await pinsIn(evidence);await pinsIn(report.newSourceFiles);await pinsIn(report.engineEvidence);
  const beforeContent=await pj(report.baseContentInventory),contentInventory=await pj(report.afterContentInventory),projectProof=await pj(report.baseProjectProof);
  assert.equal(Object.keys(projectProof).length,132);assert.deepEqual(report.baseContentInventory,evidence.baseContentInventory);assert.deepEqual(report.baseProjectProof,evidence.baseProjectProof);
  for(const [relative,row] of Object.entries(projectProof))assert(!path.isAbsolute(relative)&&path.normalize(relative)===relative&&!relative.startsWith('../')&&
    (relative==='BreziTwin.uproject'||/^(Config|Source|Binaries)\//.test(relative))&&hashLike(row.sha256)&&Number.isInteger(row.bytes));
  assert.equal(Object.keys(beforeContent).length,3975);assert.deepEqual(Object.keys(contentInventory).sort(),Object.keys(beforeContent).sort());
  for(const [relative,row] of Object.entries(beforeContent))assert.equal(row.sha256,base.afterAssetHashes[path.join(base.project,'Content',relative)]);
  const changed=Object.keys(beforeContent).filter(k=>beforeContent[k].sha256!==contentInventory[k].sha256||beforeContent[k].bytes!==contentInventory[k].bytes).sort();
  assert.deepEqual(changed,['Brezi/Maps/Brezi.umap']);assert.deepEqual(report.assetDelta,{changedFiles:changed,newFiles:[],removedFiles:[],protectedFilesByteIdentical:3974});
  for(const g of [report.baseGeometryReadback,report.savedGeometryReadback])assert.deepEqual(g,{meshCount:547,groupCount:1980,instanceCount:632026,allNewVisualsNoCollision:true});
  const before=await pj(report.witnessBefore),saved=await pj(report.witnessAfter);assert.equal(Object.keys(before).length,5306);
  validateVisibilityWitness({before,saved,targets,deltas:report.componentCullOverrides});
  const materials=await pj(report.originalMaterialsBefore);assert.equal(Object.keys(materials.graphs).length,42);assert.equal(Object.keys(materials.textures).length,74);
  for(const [id,row] of Object.entries(base.materials.materials)){
    assert.equal(materials.graphs[id].asset,row.asset);assert.equal(materials.graphs[id].graphSha256,row.graphSha256);}
  for(const [id,row] of Object.entries(base.materials.textures))assert.equal(materials.textures[id].asset,row.asset);
  const digestScript=`import hashlib,json,sys
r=json.load(open(sys.argv[1]));b=json.load(open(r['witnessBefore']['path']));a=json.load(open(r['witnessAfter']['path']));m=json.load(open(r['originalMaterialsBefore']['path']))
h=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
before=h(b)
for d in r['componentCullOverrides']:
 c=[c for c in b[d['actor']]['components'] if c['path']==d['component']];assert len(c)==1;c[0]['instanceCullCm']=d['afterCullCm']
print(json.dumps([before,h(b),h(a),h(m)]))`;
  const digests=JSON.parse((await exec('python3',['-c',digestScript,receiptPath],{timeout:60000,maxBuffer:1024*1024})).stdout);
  assert.deepEqual([report.beforeActorWitnessSha256,report.expectedActorWitnessSha256,report.savedActorWitnessSha256,report.originalMaterialsWitnessSha256],digests);
  assert.equal(digests[1],digests[2]);
  const processPath=path.join(source,'meadow-visibility-native.log.json'),processReceiptPath=path.join(source,'meadow-visibility-native-process.json');
  const proc=await read(processPath),processReceipt=await read(processReceiptPath);
  assert.equal(processReceipt.processFile,processPath);assert.equal(processReceipt.processFileSha256,await sha(processPath));
  assert.equal(processReceipt.reportSha256,await sha(receiptPath));assert.equal(processReceipt.logFile,path.join(source,'meadow-visibility-native.log'));
  assert.equal(processReceipt.logSha256,await sha(processReceipt.logFile));assert.equal(proc.code,0);assert.equal(proc.signal,null);assert.equal(proc.pid,report.nativeProcessId);
  assert(Number.isInteger(proc.pid)&&proc.pid>0);assert(Number.isFinite(Date.parse(proc.startedAt))&&Date.parse(proc.endedAt)>=Date.parse(proc.startedAt));
  assert.equal(proc.command,'/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd');assert.equal(proc.args[0],path.join(project,'BreziTwin.uproject'));
  for(const arg of ['-nullrhi','-run=pythonscript','-script='+path.join(root,OWNER),'-abslog='+processReceipt.logFile])assert(proc.args.includes(arg));
  assert.equal(processReceipt.sourcePinsUnchangedAfterNative,true);assert.equal(Object.keys(processReceipt.sourcePinsBeforeNative).length,29);
  assert.equal(processReceipt.controllerSha256BeforeNative,processReceipt.controllerSha256AfterNative);
  for(const [file,h] of Object.entries(processReceipt.sourcePinsBeforeNative)){const stat=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:stat.size});}
  for(const file of [processPath,processReceiptPath,processReceipt.logFile])closure.add(file);
  const module=path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),witness=report.nativeModuleWitness;
  assert.equal(witness.source,path.join(base.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));assert.equal(witness.destination,module);
  assert.equal(witness.sha256,MODULE_SHA);assert.equal(witness.bytes,2818384);assert.equal(witness.independentInodes,true);
  const donor=await fs.stat(witness.source),own=await fs.stat(module);assert(donor.dev!==own.dev||donor.ino!==own.ino);assert.equal(own.size,witness.bytes);
  assert.equal(await sha(module),MODULE_SHA);closure.add(module);closure.add(witness.source);
  const summary={mode:'meadow-ecology-visibility-overlay',nativeProcessId:proc.pid,targetGroups:601,targetInstances:501890,
    meadowGroups:471,meadowInstances:477117,ecologyGroups:130,ecologyInstances:24773,newAssets:0,sourcePinsUnchangedAfterNative:29,
    nativeAppearanceAccepted:false,performanceAccepted:false,fullPhotorealismAccepted:false};
  return {mode:summary.mode,project,nativeReceiptPath:receiptPath,base,summary,contentInventory,projectProof,additionalClosureFiles:[...closure],
    nativeModuleWitness:witness,moduleWitnessSource:report.baseNativeReport,receiptSummary:{baseNativeReport:report.baseNativeReport,selectedPlan:report.selectedPlan,
      savedMapUnloadedReloaded:true,materialPackagesIndependentlyReloaded:false,summary}};
}
