// Closed R20 original-shape Editor adapter. CPU/source and saved native receipts
// remain distinct from fresh rendering, realism, performance and Shipping.
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
const OWNER='scripts/unreal/exterior-curved-grass-native-r4.py';
const ORIGINAL_HELPER_SHA='e7b0158a78055b08836ccbedb62dc244717a3fedbe3c9cc7b9a8e513b5173f99';
const REPAIR_SCHEMA='brezi-original-curved-grass-exact-native-transform-repair-r4';
const REPAIR_SHA='0a29b1f8ea02626da5893e837ac643007c809df604b374de15cb571182735c89';
const CAMERA_SHA='22c420e0720a3c7824ef9d900d48407c43fc2f3a00e7289b60eea29d57d9cb29';
const STAGING_HELPER_SHA='64d492b16e6b6966a481d997ca0d6f2b79a8044ca166a9ad619ed1acbfeb8238';
const LEGACY_BASELINE_STAGE_SHA='e8028d31e82c9a8e7bfce324b2ea4e9fd8910703db90ca5cfe76880ad8e01015';
const LEGACY_BASELINE_RECEIPT_SHA='0ea7f3ed1b34642e1b9a9a751d33a8151d7c6c405f25f50d85916c0805d692cb';
const SCHEMA='brezi-original-curved-grass-root-replacement-r1';
const PLAN_SHA='f43f3d224c9d43d70091a910e5618052fa942bb593ac55d3cc900eace8a8aa68';
const HELPER_SHA='83e9d741a7d43345698f7064d6a63236afbad37222a926c265dd86a9692c7b1c';
const BASE_SHA='1f4fcf02a460153d8e2c691d301c5970bcb6c750439432c8f152b63be835e122';
const EVIDENCE_SHA='2f9032afd061b5681844911959fb9247af8a1197a2c8cded78f1ee5cdbcd0ccb';
const GENERIC_SHA='10cc942f098e130f8f22f0acb9948f4381bdc0226d5db2af17a4665fd701bc6b';
const NATIVE_INPUT_PIN_COUNT=119; // Actual R4 terminal controller, PID44361/code0.
const MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574';
const PREFIX='/Game/Brezi/CurvedGrass20261001R20';
const read=async file=>JSON.parse(await fs.readFile(file,'utf8'));
const hashLike=h=>typeof h==='string'&&/^[a-f0-9]{64}$/.test(h);
const sha=async file=>{const h=createHash('sha256');for await(const b of createReadStream(file))h.update(b);return h.digest('hex');};
const exec=promisify(execFile);
function falseFlags(row){for(const k of ['nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingPackageProduced'])assert.equal(row[k],false);}
export function validateCurvedGrassHeader(report,{source,project}){
  assert.equal(report.schema,SCHEMA);assert.equal(report.owner,OWNER);
  assert.equal(report.repairSchema,REPAIR_SCHEMA);assert.equal(report.repairSupplement.sha256,REPAIR_SHA);
  assert.equal(report.status,'verified-saved-original-curved-grass-root-replacement');falseFlags(report);
  assert.equal(report.output,source);assert.equal(report.project,project);
  for(const key of ['savedMapUnloadedReloaded','originalR16Unchanged','originalContentExceptMapByteIdentical','all64StoredMatrixAndRecoveredTransformExactMeasuredBeforeSaveAndAfterReload'])assert.equal(report[key],true);
  for(const key of ['nearSourceEmptyForegroundFixed','nativeMaterialPackagesIndependentlyReloaded','nativeMeshPackagesIndependentlyReloaded'])assert.equal(report[key],false);
  assert.equal(report.selectedPlan.sha256,PLAN_SHA);assert.equal(report.baseNativeReport.sha256,BASE_SHA);
}
export function retainedSwapIndices(count,removed){
  assert(Number.isInteger(count)&&count>0);assert.equal(new Set(removed).size,removed.length);
  assert(removed.every(i=>Number.isInteger(i)&&i>=0&&i<count));
  const indices=Array.from({length:count},(_,i)=>i);
  for(const i of [...removed].sort((a,b)=>b-a)){indices[i]=indices.at(-1);indices.pop();}
  assert.deepEqual([...indices].sort((a,b)=>a-b),Array.from({length:count},(_,i)=>i).filter(i=>!removed.includes(i)));
  return indices;
}
export function validateCurvedGrassAssetDelta(before,after,packages,delta){
  assert.equal(Object.keys(before).length,3975);assert.equal(packages.length,11);assert.equal(new Set(packages).size,11);
  assert(packages.every(p=>p.startsWith(PREFIX+'/')&&!p.includes('..')));
  assert(Object.keys(before).every(k=>Object.hasOwn(after,k)));
  const changed=Object.keys(before).filter(k=>before[k].sha256!==after[k].sha256||before[k].bytes!==after[k].bytes).sort();
  assert.deepEqual(changed,['Brezi/Maps/Brezi.umap']);
  const added=Object.keys(after).filter(k=>!Object.hasOwn(before,k)).sort(),expected=packages.map(p=>p.slice('/Game/'.length));
  for(const key of added){assert(/\.(uasset|uexp|ubulk)$/.test(key));assert(expected.includes(key.replace(/\.[^.]+$/,'')));}
  assert.deepEqual(added.filter(p=>p.endsWith('.uasset')).sort(),expected.map(p=>p+'.uasset').sort());
  assert.deepEqual(delta,{changedFiles:changed,newFiles:added,removedFiles:[],newUassetPackages:11,protectedOriginalFilesByteIdentical:3974});
}

// Python preserves the canonical spelling of native 1.0/int/exponent values.
// This validates source geometry independently of claimed native status, then
// reconstructs the complete saved counterfactual from actual serialized values.
const nativeCheck=`import copy,hashlib,importlib.util,json,math,sys
from pathlib import Path
sys.dont_write_bytecode=True
helper,report_path=sys.argv[1:]
s=importlib.util.spec_from_file_location('r7_source_only_r20',helper);n=importlib.util.module_from_spec(s);s.loader.exec_module(n)
r=json.load(open(report_path));p=Path(r['selectedPlan']['path']);plan=json.load(open(p))
repair=n.module('r7_enum_repair_cpu','exterior-curved-grass-repair-r4.py');supplement=repair.validated_supplement()
assert r['repairSchema']=='brezi-original-curved-grass-exact-native-transform-repair-r4' and r['repairSupplement']==n.pin(repair.OUTPUT/'curved-grass-repair-supplement.json')
assert r['repairSourceFiles']==supplement['newSourceFiles'] and r['numericalComparisonPolicy']==n.guard.policy()
assert r['transformComparisonPolicy']==n.transform_guard.policy() and r['faithfulTransformProbe']==n.pin(n.transform_guard.PROBE)
assert r['all64StoredMatrixAndRecoveredTransformExactMeasuredBeforeSaveAndAfterReload'] is True
base,_,_,_,rows,selected,recipe=n.validate_plan(plan,p)
probe,transform_lookup=n.transform_guard.validated_probe(selected,rows)
h=lambda x:hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
read=lambda pin:json.load(open(pin['path']))
before=read(r['witnessBefore']);saved=read(r['witnessAfter']);members=read(r['originalMembersBefore']);materials=read(r['originalMaterialsBefore'])
assert len(before)==5306 and len(saved)==5309
assert set(members)=={x['groupId'] for x in selected} and len(members)==4
expected=copy.deepcopy(before);changes=[]
for group in sorted(members):
 g=base['geometry']['groups'][group];values=members[group];assert len(values)==g['instances'] and h(values)==g['transformsSha256']
 removed=sorted(x['instanceIndex'] for x in selected if x['groupId']==group);assert len(set(removed))==len(removed)
 order=list(range(len(values)))
 for index in reversed(removed):order[index]=order[-1];order.pop()
 assert set(order)==set(range(len(values)))-set(removed)
 a=expected[g['actor']];candidates=[c for c in a['components'] if c.get('mesh')==g['mesh']]
 assert len(candidates)==1;c=candidates[0]
 assert c['instanceCount']==len(values) and c['orderedInstanceTransformsSha256']==h(values) and c['instanceCullCm']==[7200,9000] and a['detailDensityScaling'] is True
 c['instanceCount']=len(order);c['orderedInstanceTransformsSha256']=h([values[i] for i in order])
 changes.append(dict(groupId=group,actor=g['actor'],component=c['path'],removedOriginalIndices=removed,originalInstances=len(values),retainedOriginalIndicesInNativeOrder=order,retainedInstances=len(order),originalTransformsSha256=h(values),retainedTransformsSha256=c['orderedInstanceTransformsSha256']))
assert changes==r['originalMemberChanges']
assert sum(len(x['removedOriginalIndices']) for x in changes)==64
mr=r['materialReport'];assert mr['owner']=='scripts/unreal/exterior-curved-grass-materials-r3.py' and mr['recipe']==recipe and mr['nativeAppearanceAccepted'] is False and mr['shaderCompileErrors']==[]
material='/Game/Brezi/CurvedGrass20261001R20/Materials/M_ph_original_grass_medium_01_r20.M_ph_original_grass_medium_01_r20';assert mr['asset']==material
assert set(mr['textures'])=={'albedo','normal','arm','alpha'}
for role,tex in mr['textures'].items():
 assert tex['source']==recipe['maps'][role] and tex['role']==role
 name='T_R20_PhGrass_'+role+'_'+tex['source']['sha256'][:16]
 assert tex['asset']=='/Game/Brezi/CurvedGrass20261001R20/Textures/'+name+'.'+name
 assert tex['snapshot']['pixels']==[2048,2048]
 assert tex['snapshot']['srgb']==(role=='albedo') and tex['snapshot']['flip_green_channel']==(role=='normal')
 token=lambda v:v.split('.')[1].split(':')[0].replace('_','').upper()
 assert token(tex['snapshot']['compression_settings'])==('TCNORMALMAP' if role=='normal' else 'TCMASKS' if role in ('arm','alpha') else 'TCDEFAULT')
 assert token(tex['snapshot']['sourceEncoding'])==('TSESRGB' if role=='albedo' else 'TSENONE')
 assert tex['snapshot']['do_scale_mips_for_alpha_coverage']==(role=='alpha') and tex['snapshot']['alphaCoverageThresholds']==([.5,0.,0.,0.] if role=='alpha' else [0.,0.,0.,0.])
n.maps.check_graph(mr['graph'],{k:v['asset'] for k,v in mr['textures'].items()})
assert_enum={'TextureCompressionSettings':['TCDefault','TCNormalmap','TCMasks'],'TextureSourceEncoding':['TSESRGB','TSENONE'],'MaterialShadingModel':['TWOSIDEDFOLIAGE'],'MaterialUsage':['INSTANCEDSTATICMESHES'],'MaterialSamplerType':['SAMPLERTYPECOLOR','SAMPLERTYPENORMAL','SAMPLERTYPEMASKS'],'TextureAddress':['TA_WRAP'],'TextureMipGenSettings':['TMGS_FROM_TEXTURE_GROUP'],'TexturePowerOfTwoSetting':['NONE'],'BlendMode':['BLEND_MASKED'],'MaterialProperty':['MP_BASE_COLOR','MP_NORMAL','MP_OPACITY_MASK','MP_AMBIENT_OCCLUSION','MP_ROUGHNESS','MP_METALLIC','MP_SUBSURFACE_COLOR','MP_SPECULAR']}
assert set(mr['nativeEnumPreflight'])==set(assert_enum)
for group,tokens in assert_enum.items():
 assert set(mr['nativeEnumPreflight'][group])==set(tokens)
 for key in tokens:
  value=mr['nativeEnumPreflight'][group][key].split('.')[1].split(':')[0].replace('_','').upper()
  prefix={'MaterialShadingModel':'MSM','MaterialUsage':'MATUSAGE'}.get(group,'')
  if prefix and value.startswith(prefix):value=value[len(prefix):]
  assert value==key.replace('_','').upper()
assert len(materials['graphs'])==42 and len(materials['textures'])==74
for k,x in base['materials']['materials'].items():assert materials['graphs'][k]['asset']==x['asset'] and materials['graphs'][k]['graphSha256']==x['graphSha256'] and h(x['graph'])==x['graphSha256']
for k,x in base['materials']['textures'].items():assert materials['textures'][k]['asset']==x['asset']
roots=r['sourceRootPlacementReadback'];assert len(roots)==64
newgroups=r['newGroups'];assert set(newgroups)=={'EX_curved_grass_r20_'+k for k in n.guard.MASTERS}
assert sum(g['instances'] for g in newgroups.values())==64
expected_root_order=[x for kind in n.guard.MASTERS for x in selected if x['kind']==kind]
root_values={}
for source,proof in zip(expected_root_order,roots):
 original=members[source['groupId']][source['instanceIndex']];actual=proof['savedNativeValue']
 assert proof['groupId']==source['groupId'] and proof['originalIndex']==source['instanceIndex'] and proof['newMasterId']==source['newMasterId'] and proof['originalNativeValue']==original
 assert actual[0]==original[0] and proof['nativeRootXYZExact'] is True and proof['nativeInputRotationCopiedExactly'] is True
 reference=transform_lookup[(source['groupId'],source['instanceIndex'])]
 row=next(v for v in rows if v['id']==source['newMasterId'])
 matrix=proof['actualStoredDoubleMatrix']
 n.transform_guard.exact_numeric(actual,reference['recoveredNativeValue'],'Actual saved64 recovered Transform differs from faithful native measurement')
 n.transform_guard.exact_numeric(matrix,reference['actualStoredMatrixFullVertexFootprint']['actualNativeStoredDoubleMatrix'],'Actual saved64 stored FMatrix differs from faithful native measurement')
 assert proof['recoveredTransformExactMeasuredBinary64'] is True and proof['storedMatrixExactMeasuredBinary64'] is True
 assert proof['referenceProbe']==n.pin(n.transform_guard.PROBE) and proof['referenceOriginalIndex']==source['instanceIndex']
 assert proof['authoredHeightCm']==source['authoredHeightCm']
 assert proof['decodedQuaternionMaximumComponentRoundoff']==reference['rotation']['maximumSignEquivalentComponentDifference']
 assert proof['decodedRotationAngleDegrees']==reference['rotation']['relativeRotationAngleDegrees']
 assert proof['maximumUniformScaleComponentDifference']==reference['maximumScaleComponentDifference']
 # Derived statistics are read from the measured native probe. No exact libm
 # recomputation gate is introduced for CPU-only radius metadata.
 for key,value in {'decodedAllVertexRadiusCm':reference['decodedAllVertexRadiusCm'],
     'actualStoredMatrixAllVertexRadiusCm':reference['actualStoredMatrixFullVertexFootprint']['allVertexRadiusCm'],
     'decodedHeightCm':reference['decodedHeightCm'],'heightDifferenceCm':reference['heightDifferenceCm']}.items():
  assert type(proof[key]) is float and math.isfinite(proof[key]) and proof[key]==value
 assert proof['decodedAllVertexRadiusCm']<=14. and proof['actualStoredMatrixAllVertexRadiusCm']<=14.
 n.transform_guard.verify_root(source,original,actual,row,matrix,reference)
 root_values[(source['groupId'],source['instanceIndex'])]=actual
proofs=r['newMasterProofs'];assert len(proofs)==3
meshes={}
for row,proof in zip(rows,proofs):
 mesh='/Game/Brezi/CurvedGrass20261001R20/Geometry/StaticMeshes/'+row['id']+'_LOD0.'+row['id']+'_LOD0';meshes[row['id']]=mesh
 cyclic=lambda face:min(tuple(face[i:]+face[:i]) for i in range(3))
 faces=[cyclic([tuple(row['expectedNativeVerticesCm'][i]+row['uv0'][i]) for i in row['indices'][start:start+3]]) for start in range(0,len(row['indices']),3)]
 assert proof==dict(id=row['id'],mesh=mesh,lodProofs=[dict(lod=lod,triangles=row['triangles'],nativeCornerSha256=h(faces),orderedPositionUVTopologyWindingExactFloat32=True) for lod in range(3)],identicalOriginalLOD0AtAllThreeLevels=True,sourceComputedNormalTangentsExportVerified=True,nativeNormalTangentReadbackAvailable=False,nativeMeshPackageIndependentReload=False)
template=before[base['geometry']['groups']['EX_meadow_-3_2_LawnTuft0']['actor']]
for kind in n.guard.MASTERS:
 group_id='EX_curved_grass_r20_'+kind;g=newgroups[group_id];source=[x for x in selected if x['kind']==kind];values=[root_values[(x['groupId'],x['instanceIndex'])] for x in source];master=source[0]['newMasterId']
 assert g==dict(actor=g['actor'],mesh=meshes[master],instances=len(source),cullStartCm=7200,cullEndCm=9000,qualityDetail=True,transformsSha256=h(values),masterId=master)
 assert g['actor'] not in before and g['actor'].startswith('/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.BreziVegetationPatch_')
 a=copy.deepcopy(template);assert a['class']=='/Script/BreziTwin.BreziVegetationPatch' and a['detailDensityScaling'] is True and len(a['components'])==1
 a['label']=group_id;a['tags']=['BreziCurvedGrass20261001R20','BreziLawnDetail'];c=a['components'][0]
 c['mesh']=meshes[master];c['materials']=[material];c['instanceCount']=len(values);c['overrideMaterials']=[];c['path']=g['actor']+'.'+c['name'];c['orderedInstanceTransformsSha256']=h(values)
 expected[g['actor']]=a
assert saved==expected
assert [r['beforeActorWitnessSha256'],r['expectedActorWitnessSha256'],r['savedActorWitnessSha256'],r['originalMaterialsWitnessSha256']]==[h(before),h(expected),h(saved),h(materials)]
geo=read(r['effectiveGeometry']);old=copy.deepcopy(base['geometry'])
for x in changes:old['groups'][x['groupId']]['instances']=x['retainedInstances'];old['groups'][x['groupId']]['transformsSha256']=x['retainedTransformsSha256']
old['groups'].update({k:{f:v for f,v in g.items() if f!='masterId'} for k,g in newgroups.items()});old['meshes'].update(meshes)
assert geo==old and len(geo['groups'])==1983 and sum(g['instances'] for g in geo['groups'].values())==632026
packages=[x.split('.')[0] for x in meshes.values()]+[material.split('.')[0]]+[x['asset'].split('.')[0] for x in mr['textures'].values()]+[x.split('.')[0] for x in r['importPipelines']]
assert r['importPipelines']==['/Game/Brezi/CurvedGrass20261001R20/Pipeline/'+k+'.'+k for k in ['Assets','Materials','Level']]
print(json.dumps(dict(sourceGeometryAndSelectionDecoded=True,originalCompleteWitnessCount=5306,savedCompleteWitnessCount=5309,originalRootPermutationGroups=4,replacedRoots=64,newGroups=3,newMasters=3,newIdenticalPilotLODs=9,all64StoredMatrixAndRecoveredTransformExactMeasured=True,allNativeOrderedF32CornersMatchSource=True,allOriginalFieldsExcept64RemovalsPreserved=True,packages=packages)))`;

export async function loadEditorSourceEvidence(source,{root}={}){
  source=path.resolve(source);root=path.resolve(root);const names=await fs.readdir(source),name='curved-grass-native-report-r4.json';
  if(names.includes('curved-grass-camera-stage-receipt.json'))return loadStagedGrassCamera(source,{root});
  const guardFiles=[6,5,4,3].map(n=>fileURLToPath(new URL(`exterior-editor-source-r${n}.mjs`,import.meta.url)));
  if(!names.includes(name)){const e=await loadR6(source,{root});e.additionalClosureFiles.push(...guardFiles);return e;}
  assert.equal(source,path.join(root,'output/unreal/exterior-20261002-r20d'));
  assert(!names.some(n=>n==='exterior-import-report.json'||/transmission-native-report|visibility-native-report|overlay-report|diagnostic-baseline-receipt/.test(n)), 'R20 cannot carry copied base or foreign overlay receipts');
  const project=path.join(source,'Project/BreziTwin'),receiptPath=path.join(source,name),report=await read(receiptPath),closure=new Set([receiptPath,...guardFiles]);
  validateCurvedGrassHeader(report,{source,project});
  async function pinned(pin){assert(pin&&path.isAbsolute(pin.path)&&path.resolve(pin.path)===pin.path&&hashLike(pin.sha256)&&Number.isInteger(pin.bytes)&&pin.bytes>=0);
    const stat=await fs.lstat(pin.path);assert(stat.isFile()&&!stat.isSymbolicLink());assert.equal(stat.size,pin.bytes);assert.equal(await sha(pin.path),pin.sha256);closure.add(pin.path);return pin.path;}
  const pj=async pin=>read(await pinned(pin));
  async function pinsIn(value){if(!value||typeof value!=='object')return;if(Object.hasOwn(value,'path')&&Object.hasOwn(value,'sha256')&&Object.hasOwn(value,'bytes')){await pinned(value);return;}
    for(const child of Object.values(value))await pinsIn(child);}
  const base=await pj(report.baseNativeReport),plan=await pj(report.selectedPlan);
  assert.equal(report.baseNativeReport.path,path.join(root,'output/unreal/exterior-20261001-r16a/exterior-import-report.json'));
  assert.equal(report.selectedPlan.path,path.join(root,'output/unreal/exterior-curved-grass-20261002-r1-study/curved-grass-plan.json'));
  assert.equal(plan.schema,SCHEMA);assert.equal(plan.schemaVersion,1);assert.equal(plan.owner,'scripts/unreal/exterior-curved-grass-study.py');
  assert.equal(plan.status,'source-only-original-curved-grass-root-replacement-native-pending');falseFlags(plan);assert.equal(plan.nativeExecuted,false);
  assert.deepEqual(base.activeDesign,{variant:'C',heatingLayout:'B',livingLayout:'B'});assert.deepEqual(base.setbacksMm,{street:3000,east:3000});
  assert.deepEqual(plan.activeDesign,base.activeDesign);assert.deepEqual(plan.setbacksMm,base.setbacksMm);assert.deepEqual(plan.baseNativeReport,report.baseNativeReport);
  assert.equal(plan.newSourceFiles.nativeHelper.live.sha256,ORIGINAL_HELPER_SHA);assert.equal(plan.newSourceFiles.nativeHelper.live.path,path.join(root,'scripts/unreal/exterior-curved-grass-native.py'));
  const repair=await pj(report.repairSupplement);assert.equal(report.repairSupplement.path,path.join(root,'output/unreal/exterior-curved-grass-20261002-r4-supplement/curved-grass-repair-supplement.json'));
  assert.equal(repair.schema,REPAIR_SCHEMA);assert.equal(repair.owner,'scripts/unreal/exterior-curved-grass-repair-r4.py');
  assert.equal(repair.status,'source-only-curved-grass-exact-native-transform-repair-pending');assert.equal(repair.originalPlan.sha256,PLAN_SHA);
  assert.equal(repair.previousMeasuredRepair.sha256,'a1ec3f2c8c206f254d0c052889c9f053bbe9d074efdec69d9b9257b7e7612803');
  for(const key of ['nativeExecuted','nativeAppearanceAccepted','fullPhotorealismAccepted','performanceAccepted','shippingPackageProduced','originalSourcePayloadsChanged','materialRecipeChanged','generalNumericEpsilonIntroduced','unfaithfulConstructorProbeUsedForAcceptance'])assert.equal(repair[key],false);
  assert.equal(repair.newSourceFiles.nativeHelper.live.path,path.join(root,OWNER));assert.equal(repair.newSourceFiles.nativeHelper.live.sha256,HELPER_SHA);
  assert.deepEqual(report.repairSourceFiles,repair.newSourceFiles);await pinsIn(repair);
  for(const [file,h] of Object.entries(repair.inputFiles)){const stat=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:stat.size});}
  assert.deepEqual(report.actualAudit,plan.audit);assert.deepEqual(report.newSourceFiles,plan.newSourceFiles);
  assert.equal(report.reusedBaseEvidencePlan.sha256,EVIDENCE_SHA);assert.equal(report.immutableGenericHelper.sha256,GENERIC_SHA);
  assert.deepEqual(report.reusedBaseEvidencePlan,plan.reusedBaseEvidencePlan);assert.deepEqual(report.immutableGenericHelper,plan.immutableGenericHelper);
  const evidence=await pj(report.reusedBaseEvidencePlan);assert.deepEqual(report.frozenPipeline,evidence.frozenPipeline);assert.deepEqual(report.consumedSourceSnapshot,evidence.consumedSourceSnapshot);
  await pinsIn(plan);await pinsIn(evidence);await pinsIn(report.engineEvidence);
  for(const key of ['witnessBefore','witnessAfter','originalMembersBefore','originalMaterialsBefore','effectiveGeometry'])await pinned(report[key]);
  for(const texture of Object.values(report.materialReport.textures))await pinned({...texture.source,bytes:(await fs.lstat(texture.source.path)).size});
  const beforeContent=await pj(report.baseContentInventory),contentInventory=await pj(report.afterContentInventory),projectProof=await pj(report.baseProjectProof);
  assert.deepEqual(report.baseContentInventory,evidence.baseContentInventory);assert.deepEqual(report.baseProjectProof,evidence.baseProjectProof);
  assert.equal(Object.keys(projectProof).length,132);
  for(const [relative,row] of Object.entries(projectProof))assert(!path.isAbsolute(relative)&&path.normalize(relative)===relative&&!relative.startsWith('../')&&
    (relative==='BreziTwin.uproject'||/^(Config|Source|Binaries)\//.test(relative))&&hashLike(row.sha256)&&Number.isInteger(row.bytes));
  for(const [relative,row] of Object.entries(beforeContent))assert.equal(row.sha256,base.afterAssetHashes[path.join(base.project,'Content',relative)]);
  assert.deepEqual(report.baseGeometryReadback,{meshCount:547,groupCount:1980,instanceCount:632026,allNewVisualsNoCollision:true});
  assert.deepEqual(report.savedGeometryReadback,{meshCount:550,groupCount:1983,instanceCount:632026,allNewVisualsNoCollision:true,originalOwnershipDelegation:{meshCount:547,groupCount:1980,instanceCount:631962,allNewVisualsNoCollision:true},separateOwnedGroupReadback:{groups:3,instances:64,originalExteriorOwnershipSpoofed:false,orderedNativeTransformsVerified:true}});
  const native=JSON.parse((await exec('python3',['-c',nativeCheck,path.join(root,OWNER),receiptPath],{timeout:120000,maxBuffer:1024*1024})).stdout);
  validateCurvedGrassAssetDelta(beforeContent,contentInventory,native.packages,report.assetDelta);
  const processPath=path.join(source,'curved-grass-native-r4.log.json'),processReceiptPath=path.join(source,'curved-grass-native-r4-process.json');
  const proc=await read(processPath),processReceipt=await read(processReceiptPath);
  assert.equal(processReceipt.processFile,processPath);assert.equal(processReceipt.processFileSha256,await sha(processPath));
  assert.equal(processReceipt.reportSha256,await sha(receiptPath));assert.equal(processReceipt.logFile,path.join(source,'curved-grass-native-r4.log'));
  assert.equal(processReceipt.logSha256,await sha(processReceipt.logFile));assert.equal(proc.code,0);assert.equal(proc.signal,null);assert.equal(proc.pid,report.nativeProcessId);
  assert(Number.isInteger(proc.pid)&&proc.pid>0);assert(Number.isFinite(Date.parse(proc.startedAt))&&Date.parse(proc.endedAt)>=Date.parse(proc.startedAt));
  assert.equal(proc.command,'/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd');assert.equal(proc.args[0],path.join(project,'BreziTwin.uproject'));
  for(const arg of ['-nullrhi','-run=pythonscript','-script='+path.join(root,OWNER),'-abslog='+processReceipt.logFile])assert(proc.args.includes(arg));
  assert.equal(processReceipt.sourcePinsUnchangedAfterNative,true);assert.equal(Object.keys(processReceipt.sourcePinsBeforeNative).length,NATIVE_INPUT_PIN_COUNT);
  assert.equal(processReceipt.controllerSha256BeforeNative,processReceipt.controllerSha256AfterNative);
  assert.equal(await sha(processReceipt.controller),processReceipt.controllerSha256BeforeNative);closure.add(processReceipt.controller);
  for(const [file,h] of Object.entries(processReceipt.sourcePinsBeforeNative)){const stat=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:stat.size});}
  for(const file of [processPath,processReceiptPath,processReceipt.logFile])closure.add(file);
  const module=path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),witness=report.nativeModuleWitness;
  assert.equal(witness.source,path.join(base.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'));assert.equal(witness.destination,module);
  assert.equal(witness.sha256,MODULE_SHA);assert.equal(witness.bytes,2818384);assert.equal(witness.independentInodes,true);
  const donor=await fs.stat(witness.source),own=await fs.stat(module);assert(donor.dev!==own.dev||donor.ino!==own.ino);assert.equal(own.size,witness.bytes);
  assert.equal(await sha(module),MODULE_SHA);closure.add(module);closure.add(witness.source);
  const summary={mode:'original-curved-grass-root-replacement',nativeProcessId:proc.pid,...native,packages:undefined,
    originalGroups:1980,savedGroups:1983,savedInstances:632026,originalMaterialGraphs:42,originalTextureObjects:74,newMaterialGraphs:1,newTextureObjects:4,newUassetPackages:11,
    sourcePinsUnchangedAfterNative:NATIVE_INPUT_PIN_COUNT,nativeAppearanceAccepted:false,performanceAccepted:false,fullPhotorealismAccepted:false};
  return {mode:summary.mode,project,nativeReceiptPath:receiptPath,base,summary,contentInventory,projectProof,additionalClosureFiles:[...closure],
    nativeModuleWitness:witness,moduleWitnessSource:report.baseNativeReport,receiptSummary:{baseNativeReport:report.baseNativeReport,selectedPlan:report.selectedPlan,
      savedMapUnloadedReloaded:true,materialPackagesIndependentlyReloaded:false,meshPackagesIndependentlyReloaded:false,summary}};
}

export function validateGrassDiagnosticViews(original,supplement,appended){
  assert.equal(supplement.schema,'brezi-original-curved-grass-close-camera-r1');
  assert.equal(supplement.owner,'scripts/unreal/exterior-curved-grass-camera-r1.py');
  assert.equal(supplement.status,'source-only-close-camera-native-pending');
  for(const key of ['nativeExecuted','nativeAppearanceAccepted','performanceAccepted','fullPhotorealismAccepted','vegetationPlacementChanged'])assert.equal(supplement[key],false);
  assert.equal(supplement.selectedGrassPlan.sha256,PLAN_SHA);
  assert.equal(supplement.originalViewRowsByteExactPrefix,true);assert.equal(supplement.lightingAndOriginalViewsUnchanged,true);
  const {views:oldViews,...oldRoot}=original,{views:newViews,...newRoot}=appended;
  assert.equal(original.coordinateSystem,'unreal-centimeters');assert.deepEqual(newRoot,oldRoot);
  assert.equal(newViews.length,oldViews.length+1);assert.deepEqual(newViews.slice(0,-1),oldViews);
  assert.deepEqual(newViews.at(-1),supplement.view);assert.equal(supplement.view.id,'exterior-curved-grass-close');
  assert.equal(supplement.view.horizontalFovDegrees,65);assert.equal(new Set(newViews.map(v=>v.id)).size,newViews.length);
  for(const key of ['eyeCm','targetCm'])assert(supplement.view[key].length===3&&supplement.view[key].every(Number.isFinite));
  assert(Math.hypot(...supplement.view.targetCm.map((v,i)=>v-supplement.view.eyeCm[i]))>.1);
  assert.equal(supplement.sourceCameraAudit.selectedRootCount,64);assert.equal(supplement.sourceCameraAudit.rootCentersIn16by9Frustum,37);
  assert.equal(supplement.sourceCameraAudit.nativeCameraVerified,false);assert.equal(supplement.sourceCameraAudit.rootCentersOnlyNotOcclusionOrNativeVisibility,true);
}

export function validateStagedGrassContent(before,after,supplement){
  assert.deepEqual(Object.keys(after).sort(),Object.keys(before).sort());
  assert.deepEqual(Object.keys(before).filter(k=>before[k].sha256!==after[k].sha256||before[k].bytes!==after[k].bytes).sort(),['Data/viewpoints.json']);
  assert.equal(before['Data/viewpoints.json'].sha256,supplement.originalViewpoints.sha256);
  assert.equal(after['Data/viewpoints.json'].sha256,supplement.appendedViewpoints.sha256);
  assert.equal(after['Data/viewpoints.json'].bytes,supplement.appendedViewpoints.bytes);
}

export function validateGrassStageHeader(stage,{source,root,receiptSha256}){
  const legacyBaseline=stage.schema==='brezi-curved-grass-close-camera-diagnostic-clone-r1';
  if(legacyBaseline){
    assert.equal(source,path.join(root,'output/unreal/exterior-20261002-r20-close-baseline'));
    assert.equal(receiptSha256,LEGACY_BASELINE_RECEIPT_SHA);assert.equal(stage.sourceKind,'original-r16');
    assert.equal(stage.owner,'scripts/unreal/exterior-curved-grass-camera-stage-r1.py');
  }else{
    assert.equal(stage.schema,'brezi-curved-grass-close-camera-diagnostic-clone-r2');
    assert.equal(stage.owner,'scripts/unreal/exterior-curved-grass-camera-stage-r2.py');
    assert.equal(stage.sourceKind,'saved-curved-grass-r20-r4');
  }
  assert.equal(stage.stagingHelper.path,path.join(root,stage.owner));
  assert.equal(stage.stagingHelper.sha256,legacyBaseline?LEGACY_BASELINE_STAGE_SHA:STAGING_HELPER_SHA);
  return legacyBaseline;
}

async function loadStagedGrassCamera(source,{root}){
  const receiptPath=path.join(source,'curved-grass-camera-stage-receipt.json'),stage=await read(receiptPath),closure=new Set([receiptPath]);
  const names=await fs.readdir(source);assert(!names.some(n=>n==='exterior-import-report.json'||/native-report|overlay-report|baseline-receipt/.test(n)),'Camera QA clone cannot carry copied native/foreign reports');
  assert.equal(path.dirname(source),path.join(root,'output/unreal'));
  const legacyBaseline=validateGrassStageHeader(stage,{source,root,receiptSha256:await sha(receiptPath)});
  assert.equal(stage.status,'verified-independent-qa-clone-close-camera-data-only');falseFlags(stage);
  for(const key of ['originalViewsPrefixPreserved','lightingUnchanged','nativeSourceUnchanged'])assert.equal(stage[key],true);
  for(const key of ['sceneMapChanged','nativeCameraRuntimeVerified'])assert.equal(stage[key],false);
  assert.deepEqual(stage.changedContentFiles,['Data/viewpoints.json']);
  const project=path.join(source,'Project/BreziTwin');assert.equal(stage.project,project);
  assert(['original-r16','saved-curved-grass-r20-r4'].includes(stage.sourceKind));
  const nativeSource=path.join(root,stage.sourceKind==='original-r16'?'output/unreal/exterior-20261001-r16a':'output/unreal/exterior-20261002-r20d');
  assert.equal(stage.sourceNativeOutput,nativeSource);assert.notEqual(source,nativeSource);
  const e=await loadEditorSourceEvidence(nativeSource,{root});assert.equal(stage.sourceNativeReport.path,e.nativeReceiptPath);
  async function pinned(pin){assert(pin&&path.isAbsolute(pin.path)&&path.resolve(pin.path)===pin.path&&hashLike(pin.sha256)&&Number.isInteger(pin.bytes)&&pin.bytes>=0);
    const stat=await fs.lstat(pin.path);assert(stat.isFile()&&!stat.isSymbolicLink());assert.equal(stat.size,pin.bytes);assert.equal(await sha(pin.path),pin.sha256);closure.add(pin.path);return pin.path;}
  const pj=async pin=>read(await pinned(pin));
  await pinned(stage.sourceNativeReport);
  let sourceContentInventory=e.contentInventory;
  if(stage.sourceKind==='original-r16'){
    const evidencePath=path.join(root,'output/unreal/exterior-canopy-transmission-20261001-r1-study/canopy-transmission-plan.json');
    assert.equal(await sha(evidencePath),EVIDENCE_SHA);closure.add(evidencePath);
    const evidence=await read(evidencePath);sourceContentInventory=await pj(evidence.baseContentInventory);
    assert.equal(Object.keys(sourceContentInventory).length,3975);assert.equal(Object.keys(e.contentInventory).length,3975);
    for(const [relative,row]of Object.entries(sourceContentInventory))assert.equal(row.sha256,e.contentInventory[relative].sha256);
    assert.deepEqual(stage.protectedProjectProof,evidence.baseProjectProof);
  }
  if(stage.sourceKind==='original-r16')assert.equal(stage.sourceNativeProcess,null);
  else{assert.equal(stage.sourceNativeProcess.path,path.join(nativeSource,'curved-grass-native-r4-process.json'));await pinned(stage.sourceNativeProcess);}
  assert.equal(stage.stagingHelper.path,path.join(root,stage.owner));assert.equal(stage.stagingHelper.sha256,legacyBaseline?LEGACY_BASELINE_STAGE_SHA:STAGING_HELPER_SHA);await pinned(stage.stagingHelper);
  assert.equal(stage.cameraSupplement.path,path.join(root,'output/unreal/exterior-curved-grass-20261002-camera-r1-supplement/curved-grass-camera-supplement.json'));
  assert.equal(stage.cameraSupplement.sha256,CAMERA_SHA);const supplement=await pj(stage.cameraSupplement);
  for(const [file,h] of Object.entries(supplement.inputFiles)){const stat=await fs.lstat(file);await pinned({path:file,sha256:h,bytes:stat.size});}
  const original=await pj(supplement.originalViewpoints),appended=await pj(supplement.appendedViewpoints);validateGrassDiagnosticViews(original,supplement,appended);
  assert.deepEqual(stage.view,supplement.view);assert.equal(stage.viewId,supplement.view.id);assert.deepEqual(stage.sourceCameraAudit,supplement.sourceCameraAudit);
  assert.equal(stage.viewpointFile.path,path.join(project,'Content/Data/viewpoints.json'));assert.equal(stage.viewpointFile.sha256,supplement.appendedViewpoints.sha256);await pinned(stage.viewpointFile);
  assert.equal(stage.afterContentInventory.path,path.join(source,'curved-grass-camera-content-after.json'));
  assert.equal(stage.protectedProjectProof.path,path.join(root,'output/unreal/exterior-canopy-transmission-20261001-r1-study/base-project-proof.json'));
  assert.equal(stage.protectedProjectProof.sha256,'8609ddd8ba991d6459bf2a7a2990ef00ae304067a1bc3f28038d04c28fa53022');
  const contentInventory=await pj(stage.afterContentInventory),projectProof=await pj(stage.protectedProjectProof);
  assert.equal(Object.keys(projectProof).length,132);
  if(e.projectProof)assert.deepEqual(projectProof,e.projectProof);
  assert.equal(stage.originalContentFileCount,Object.keys(sourceContentInventory).length);
  validateStagedGrassContent(sourceContentInventory,contentInventory,supplement);
  for(const [directory,rows] of [['Content',sourceContentInventory],['',projectProof]])for(const relative of Object.keys(rows)){
    const donor=await fs.stat(path.join(e.project,directory,relative)),own=await fs.lstat(path.join(project,directory,relative));
    assert(own.isFile()&&!own.isSymbolicLink());assert(donor.dev!==own.dev||donor.ino!==own.ino,'Camera clone is a source hardlink');
    if(directory===''){assert.equal(donor.size,rows[relative].bytes);assert.equal(await sha(path.join(e.project,relative)),rows[relative].sha256);closure.add(path.join(e.project,relative));}
  }
  const module=path.join(project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),nativeModuleWitness={
    source:path.join(e.project,'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),destination:module,sha256:MODULE_SHA,bytes:2818384,independentInodes:true};
  assert.equal(await sha(module),MODULE_SHA);closure.add(module);closure.add(nativeModuleWitness.source);
  const summary={...e.summary,mode:'curved-grass-close-camera-diagnostic-clone',sourceNativeMode:e.mode,sourceKind:stage.sourceKind,
    supplementalViews:1,selectedRootCentersInSourceFrustum:37,nativeCameraRuntimeVerified:false,nativeAppearanceAccepted:false,performanceAccepted:false,fullPhotorealismAccepted:false};
  return {mode:summary.mode,project,nativeReceiptPath:receiptPath,base:e.base,summary,contentInventory,projectProof,
    additionalClosureFiles:[...new Set([...e.additionalClosureFiles,...closure])],nativeModuleWitness,moduleWitnessSource:stage.sourceNativeReport,
    receiptSummary:{sourceNativeReport:stage.sourceNativeReport,sourceNativeProcess:stage.sourceNativeProcess,cameraStageReceipt:receiptPath,
      cameraSupplement:stage.cameraSupplement,originalNativeSourceUnchanged:true,sourceNativeEvidence:e.receiptSummary,summary}};
}
