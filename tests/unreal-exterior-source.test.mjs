import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {mkdtemp,readFile,writeFile,rm} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {validateExteriorReceipt,validateNaturalLawnReceipt,validateNaturalLawnPlan,validateGroveReceipt,validateGrovePlanOwner,validateGrovePlanReceipt,plantLodScreenSizes} from '../scripts/unreal/exterior-source.mjs';

const root=fileURLToPath(new URL('../',import.meta.url));
const uprightPath=resolve(root,'output/unreal/exterior-lawn-upright-20260930-r4-study/lawn-natural-plan.json');
const uprightBytes=await readFile(uprightPath),uprightPlan=JSON.parse(uprightBytes);
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');

function uprightFixture() {
  const plan=structuredClone(uprightPlan),a='a'.repeat(64);
  const counts=[10118,10153,10147,10019],original=[24474,24836,24588,24446];
  const rural='/source/rural-report.json',ruralPlan='/source/rural-plan.json';
  const hidden=counts.map((count,i)=>({actor:'actor'+i,component:'component'+i,legacyLawnGroup:'LawnTuft'+i,
    detailDensityScalingAfter:false,preserved:{instanceCount:count,orderedInstanceTransformsSha256:a},sourcePlacement:{sha256:a},
    sourceRuralTrim:{report:{path:rural,sha256:a},plan:{path:ruralPlan,sha256:a},
      group:{before:original[i],kept:count,removed:original[i]-count,transformsSha256:a,sourceInstanceOrderPreserved:true},
      membership:'ordered-source-placement-subset-of-pinned-rural-keep-polygons'}}));
  return {plan,report:{inputFiles:{[uprightPath]:hash(uprightBytes),[rural]:a,[ruralPlan]:a,
      [plan.coverageReceipt.path]:plan.coverageReceipt.sha256,[plan.boundaryCoverageReceipt.path]:plan.boundaryCoverageReceipt.sha256},
    sourceRenderChanges:hidden,naturalLawn:{plan:uprightPath,planSha256:hash(uprightBytes),audit:structuredClone(plan.audit),
      coverageReceipt:structuredClone(plan.coverageReceipt),boundaryCoverageReceipt:structuredClone(plan.boundaryCoverageReceipt),
      hiddenOriginalGroups:hidden,savedReadback:{status:'verified-hidden-original-lawn',actors:4,instances:40437,
        originalMeshesMaterialsGroundAndCollisionPreserved:true,hiddenDetailDensityScalingDisabled:true}}}};
}

function fixture() {
  const a='1'.repeat(64),b='2'.repeat(64),project='/project';
  const map=project+'/Content/Brezi/Maps/Brezi.umap',views=project+'/Content/Data/viewpoints.json';
  const original=project+'/Content/Brezi/Geometry/House.uasset',added=project+'/Content/Brezi/Exterior20260926/Plant.uasset';
  const source={donor:'/donor',content:{[map]:a,[views]:a,[original]:a}};
  const before={sun:{intensity:80000},views:[{id:'interior',eyeCm:[0,0,160]}]};
  const report={schemaVersion:1,owner:'scripts/unreal/exterior-import.py',status:'exterior-import-validated',project,sourceOutput:source.donor,
    activeDesign:{variant:'C',heatingLayout:'B',livingLayout:'B'},setbacksMm:{street:3000,east:3000},
    savedReloaded:true,protectedContentUnchanged:true,sourceGeometryCollisionAndTransformsPreserved:true,originalMaterialAssetsPreserved:true,
    beforeAssetHashes:source.content,afterAssetHashes:{...source.content,[map]:b,[views]:b,[added]:b},newAssets:[added],
    changedAssets:[map,views].map(path=>({path,beforeSha256:a,afterSha256:b})),
    viewpoints:{before,after:{...structuredClone(before),views:[...structuredClone(before.views),{id:'exterior',eyeCm:[100,0,160]}]}},
    originalActorCount:100,finalActorCount:101,addedActors:['new-plant'],
    protectedActorWitnessSha256:a,savedProtectedActorWitnessSha256:a,authoredActorWitnessSha256:b,savedActorWitnessSha256:b,
    savedGeometryReadback:{meshCount:1,instanceCount:20,allNewVisualsNoCollision:true},
    context:{parcelCount:117},materialReadback:{status:'verified-saved-exterior-materials'}};
  return structuredClone({report,source,project,map,views,original,added,a,b});
}

test('exterior receipt accepts additive visuals with unchanged original architecture',()=>{
  const f=fixture();assert.deepEqual(validateExteriorReceipt(f),f.report.afterAssetHashes);
});
test('historical geometry and material packages cannot be rewritten or removed',()=>{
  for(const mutate of [f=>f.report.afterAssetHashes[f.original]=f.b,f=>delete f.report.afterAssetHashes[f.original]]){
    const f=fixture();mutate(f);assert.throws(()=>validateExteriorReceipt(f));
  }
});
test('a changed architectural selection, setback or saved witness rejects promotion',()=>{
  for(const mutate of [f=>f.report.activeDesign.variant='A',f=>f.report.setbacksMm.street=2800,
    f=>f.report.savedProtectedActorWitnessSha256=f.b,f=>f.report.savedActorWitnessSha256=f.a,
    f=>f.report.savedGeometryReadback.allNewVisualsNoCollision=false,f=>f.report.savedReloaded=false]){
    const f=fixture();mutate(f);assert.throws(()=>validateExteriorReceipt(f));
  }
});
test('new cameras cannot change existing views or sunlight',()=>{
  for(const mutate of [f=>f.report.viewpoints.after.views[0].eyeCm[0]=1,
    f=>f.report.viewpoints.after.sun={intensity:100},f=>f.report.viewpoints.after.views[1].id='interior']){
    const f=fixture();mutate(f);assert.throws(()=>validateExteriorReceipt(f));
  }
});
test('new exterior assets cannot escape their namespace',()=>{
  for(const suffix of ['../Other/Plant.uasset','Plant.py','/tmp/Plant.uasset']){
    const f=fixture(),path=f.project+'/Content/Brezi/Exterior20260926/'+suffix;
    f.report.afterAssetHashes[path]=f.b;f.report.newAssets=Object.keys(f.report.afterAssetHashes).filter(p=>!Object.hasOwn(f.source.content,p)).sort();
    assert.throws(()=>validateExteriorReceipt(f));
  }
});

test('small natural lawn retains curved LODs without changing existing plant families',()=>{
  assert.deepEqual(plantLodScreenSizes({role:'tree'}),[1,.32,.10]);
  assert.deepEqual(plantLodScreenSizes({role:'grass'}),[1,.15,.04]);
  const lawn={id:'lawn_natural_green_a',role:'grass',placementPolicy:'explicit-only',materialKeys:['lawn_natural_blade'],lodScreenSizes:[1,.025,.007]};
  assert.deepEqual(plantLodScreenSizes(lawn),[1,.025,.007]);
  for(const change of [{id:'unreviewed_grass'},{role:'tree'},{placementPolicy:'random'},{materialKeys:['garden_blade_green']},{lodScreenSizes:[1,.15,.04]}]) {
    assert.throws(()=>plantLodScreenSizes({...lawn,...change}));
  }
});

test('grove litter requires pinned additive meshes and saved collision-free bindings',()=>{
  const plan='/grove/substrate-plan.json',hash='3'.repeat(64),id='context_grove_substrate_0';
  const report={inputFiles:{[plan]:hash},geometry:{actors:{[id]:'/Map.EX_'+id},
    meshes:{[id]:'/Game/Brezi/Exterior20260926/Geometry/Context/'+id}},
    groveSubstrate:{plan,planSha256:hash,regionId:'village_nearest_grove',sourceGroundUnchanged:true,hiddenOriginalActors:0,
      validation:{status:'verified-source-grove-substrate'},meshIds:[id],
      savedReadback:{status:'verified-saved-grove-substrate',meshes:1,allNewVisualsNoCollision:true,nativeMeshBindingsVerifiedAfterReload:true}}};
  validateGroveReceipt(report);
  for(const mutate of [r=>delete r.inputFiles[plan],r=>r.groveSubstrate.hiddenOriginalActors=1,
    r=>r.groveSubstrate.sourceGroundUnchanged=false,r=>r.groveSubstrate.regionId='private_garden',
    r=>r.groveSubstrate.validation.status='unverified',r=>r.groveSubstrate.meshIds=[id,id],
    r=>r.groveSubstrate.meshIds=['unreviewed_ground'],r=>delete r.geometry.actors[id],
    r=>r.geometry.meshes[id]='/Game/Existing/Ground',r=>r.groveSubstrate.savedReadback.meshes=2,
    r=>r.groveSubstrate.savedReadback.allNewVisualsNoCollision=false,
    r=>r.groveSubstrate.savedReadback.nativeMeshBindingsVerifiedAfterReload=false]) {
    const broken=structuredClone(report);mutate(broken);assert.throws(()=>validateGroveReceipt(broken));
  }
});

test('natural lawn promotion requires the saved legacy replacement and density witness',()=>{
  const a='a'.repeat(64),plan='/natural/plan.json',rural='/source/rural-report.json',ruralPlan='/source/rural-plan.json';
  const counts=[10118,10153,10147,10019],original=[24474,24836,24588,24446];
  const hidden=Array.from({length:4},(_,i)=>({actor:'actor'+i,component:'component'+i,legacyLawnGroup:'LawnTuft'+i,
    detailDensityScalingAfter:false,preserved:{instanceCount:counts[i],orderedInstanceTransformsSha256:a},sourcePlacement:{sha256:a},
    sourceRuralTrim:{report:{path:rural,sha256:a},plan:{path:ruralPlan,sha256:a},
      group:{before:original[i],kept:counts[i],removed:original[i]-counts[i],transformsSha256:a,sourceInstanceOrderPreserved:true},
      membership:'ordered-source-placement-subset-of-pinned-rural-keep-polygons'}}));
  const report={inputFiles:{[plan]:a,[rural]:a,[ruralPlan]:a},sourceRenderChanges:hidden,naturalLawn:{plan,planSha256:a,
    audit:{status:'PASS_STATIC_GEOMETRY_AND_CLEARANCE',instances:24918,groups:80,sourceMasksUnchanged:true},hiddenOriginalGroups:hidden,
    savedReadback:{status:'verified-hidden-original-lawn',actors:4,instances:40437,
      originalMeshesMaterialsGroundAndCollisionPreserved:true,hiddenDetailDensityScalingDisabled:true}}};
  validateNaturalLawnReceipt(report);
  const continuous=structuredClone(report),coverage='/natural/coverage.json';
  continuous.naturalLawn.audit.status='PASS_STATIC_CONTINUOUS_MANAGED_GEOMETRY_NOT_NATIVE_ACCEPTED';
  assert.throws(()=>validateNaturalLawnReceipt(continuous));
  continuous.naturalLawn.coverageReceipt={path:coverage,sha256:a};continuous.inputFiles[coverage]=a;
  validateNaturalLawnReceipt(continuous);
  continuous.inputFiles[coverage]='b'.repeat(64);assert.throws(()=>validateNaturalLawnReceipt(continuous));
  const fine=structuredClone(report);fine.naturalLawn.audit.status='PASS_STATIC_FINE_MANAGED_GEOMETRY_NOT_NATIVE_ACCEPTED';
  assert.throws(()=>validateNaturalLawnReceipt(fine));
  fine.naturalLawn.coverageReceipt={path:coverage,sha256:a};fine.inputFiles[coverage]=a;
  assert.throws(()=>validateNaturalLawnReceipt(fine));
  const boundary='/natural/boundary.json';fine.naturalLawn.boundaryCoverageReceipt={path:boundary,sha256:a};fine.inputFiles[boundary]=a;
  validateNaturalLawnReceipt(fine);
  const missingBoundary=structuredClone(fine);delete missingBoundary.inputFiles[boundary];assert.throws(()=>validateNaturalLawnReceipt(missingBoundary));
  delete fine.inputFiles[coverage];assert.throws(()=>validateNaturalLawnReceipt(fine));
  for(const mutate of [r=>r.naturalLawn.savedReadback.hiddenDetailDensityScalingDisabled=false,
    r=>r.naturalLawn.hiddenOriginalGroups[0].detailDensityScalingAfter=true,
    r=>r.naturalLawn.hiddenOriginalGroups[0].preserved.instanceCount--,
    r=>r.sourceRenderChanges=[],r=>r.inputFiles[plan]='b'.repeat(64),
    r=>delete r.inputFiles[ruralPlan],r=>r.naturalLawn.hiddenOriginalGroups[0].sourceRuralTrim.group.sourceInstanceOrderPreserved=false,
    r=>r.naturalLawn.hiddenOriginalGroups[0].preserved.orderedInstanceTransformsSha256='missing']) {
    const broken=structuredClone(report);mutate(broken);assert.throws(()=>validateNaturalLawnReceipt(broken));
  }
});

test('grove receipt requires saved additive membership and preserves all tree roots',()=>{
  const a='a'.repeat(64),plan='/grove/canopy-plan.json',ecology='/grove/ecology-plan.json';
  const groups={canopy:{mesh:'/Game/Brezi/Exterior20260926/Geometry/Canopy.Canopy',instances:78,qualityDetail:false,transformsSha256:a},
    ecology:{mesh:'/Game/Brezi/Exterior20260926/Geometry/Litter.Litter',instances:24851,qualityDetail:false,transformsSha256:a}};
  const saved=instances=>({status:'verified-saved-grove-groups',groups:1,instances,allNewVisualsNoCollision:true,orderedNativeTransformsVerifiedAfterReload:true});
  const report={inputFiles:{[plan]:a,[ecology]:a},geometry:{groups},
    canopyReplacement:{plan,planSha256:a,regionId:'village_nearest_grove',hiddenOriginalActors:0,trees:78,deletedTrees:0,
      validation:{status:'verified-source-grove-canopy-replacement'},nonGroveRegionalRowsPreserved:true,groupIds:['canopy'],savedReadback:saved(78)},
    canopyEcology:{plan:ecology,planSha256:a,regionId:'village_nearest_grove',hiddenOriginalActors:0,sourceGroundUnchanged:true,
      validation:{status:'verified-source-grove-ecology'},audit:{instances:24851,groups:1},groupIds:['ecology'],savedReadback:saved(24851)}};
  validateGroveReceipt(report);
  for(const mutate of [r=>r.canopyReplacement.deletedTrees=1,r=>r.canopyReplacement.hiddenOriginalActors=1,
    r=>r.canopyReplacement.nonGroveRegionalRowsPreserved=false,r=>r.canopyEcology.sourceGroundUnchanged=false,
    r=>r.canopyReplacement.groupIds=['missing'],r=>r.canopyEcology.groupIds=['ecology','ecology'],
    r=>r.geometry.groups.canopy.instances--,r=>r.geometry.groups.canopy.qualityDetail=true,
    r=>r.geometry.groups.canopy.transformsSha256='missing',r=>r.canopyEcology.savedReadback.orderedNativeTransformsVerifiedAfterReload=false,
    r=>delete r.inputFiles[plan],r=>r.canopyReplacement.validation.status='unverified']) {
    const broken=structuredClone(report);mutate(broken);assert.throws(()=>validateGroveReceipt(broken));
  }
});

test('actual upright source plan keeps pinned physical and boundary gates with the legacy saved witness',async()=>{
  const {plan,report}=uprightFixture();
  validateNaturalLawnReceipt(report);validateNaturalLawnPlan(report,plan);
  assert.equal(plan.lawnPlacements.length,102011);assert.equal(plan.groups.length,40);
  for(const [key,body] of [['coverageReceipt','physicalCoverage'],['boundaryCoverageReceipt','boundaryCoverage']]) {
    const bytes=await readFile(plan[key].path);
    assert.equal(hash(bytes),plan[key].sha256);assert.deepEqual(JSON.parse(bytes),plan.audit[body]);
  }
});

test('upright lawn cannot omit or drift either source coverage pin',()=>{
  for(const key of ['coverageReceipt','boundaryCoverageReceipt'])for(const action of ['missing','unlisted','hash','plan-pin']) {
    const {plan,report}=uprightFixture(),path=report.naturalLawn[key].path;
    if(action==='missing')delete report.naturalLawn[key];
    else if(action==='unlisted')delete report.inputFiles[path];
    else if(action==='hash')report.naturalLawn[key].sha256='b'.repeat(64);
    else plan[key].sha256='b'.repeat(64);
    assert.throws(()=>{validateNaturalLawnReceipt(report);validateNaturalLawnPlan(report,plan);});
  }
});

test('self-consistently repinned upright owner/status and coverage downgrades reject promotion',async()=>{
  const mutations=[p=>p.owner='scripts/unreal/unknown.py',
    p=>p.audit.status='PASS_STATIC_FINE_MANAGED_GEOMETRY_NOT_NATIVE_ACCEPTED',
    p=>p.audit.physicalCoverage.status='PASS_STATIC_PHYSICAL_COVERAGE_NOT_NATIVE_ACCEPTED',
    p=>p.audit.boundaryCoverage.status='PASS_STATIC_BOUNDARY_LEAF_COVERAGE_NOT_NATIVE_ACCEPTED',
    p=>p.audit.physicalCoverage.criteria.minimumTopViewCoverage=.70,
    p=>p.audit.physicalCoverage.windows[0].lods[0].projectedCoverage=.74,
    p=>p.audit.physicalCoverage.windows[0].lods[0].bareTenCmBins=1,
    p=>p.audit.boundaryCoverage.criteria.outsideSourceDomainPermittedCm=1,
    p=>p.audit.boundaryCoverage.windows[0].originCm=[0,0],
    p=>p.audit.boundaryCoverage.windows[0].inwardUnitXY=[0,0],
    p=>p.audit.boundaryCoverage.windows[0].lods[0].boundaryBands[1].physicalCoverFraction=.39,
    p=>p.audit.allInstancesTriangleBudgetByLod[2]=18571201,
    p=>p.audit.nativeAppearanceAccepted=true];
  const temporary=await mkdtemp(resolve(root,'output/unreal/upright-node-negative-'));
  try {
    for(const [index,mutate] of mutations.entries()) {
      const {plan,report}=uprightFixture();mutate(plan);
      for(const [key,body] of [['coverageReceipt','physicalCoverage'],['boundaryCoverageReceipt','boundaryCoverage']]) {
        const path=resolve(temporary,index+'-'+key+'.json'),bytes=Buffer.from(JSON.stringify(plan.audit[body]));
        await writeFile(path,bytes);plan[key]={path,sha256:hash(bytes)};
        report.naturalLawn[key]=structuredClone(plan[key]);report.inputFiles[path]=hash(bytes);
      }
      const path=resolve(temporary,index+'-plan.json'),bytes=Buffer.from(JSON.stringify(plan));
      await writeFile(path,bytes);report.naturalLawn.plan=path;report.naturalLawn.planSha256=hash(bytes);
      report.inputFiles[path]=hash(bytes);report.naturalLawn.audit=structuredClone(plan.audit);
      const repinned=JSON.parse(await readFile(path));
      assert.equal(hash(await readFile(path)),report.naturalLawn.planSha256);
      assert.throws(()=>{validateNaturalLawnReceipt(report);validateNaturalLawnPlan(report,repinned);},undefined,'Unsafe repinned case '+index);
    }
  } finally {await rm(temporary,{recursive:true,force:true});}
});

test('canopy growth ownership is explicit and cannot broaden other grove branches',()=>{
  for(const owner of ['scripts/unreal/exterior-canopy-masters.py','scripts/unreal/exterior-canopy-growth.py'])
    validateGrovePlanOwner({owner},'canopyReplacement');
  for(const owner of ['scripts/unreal/exterior-canopy-ecology.py','scripts/unreal/exterior-canopy-ecology-unflared.py'])
    validateGrovePlanOwner({owner},'canopyEcology');
  for(const [owner,key] of [['scripts/unreal/exterior-canopy-growth.py','canopyEcology'],
    ['scripts/unreal/exterior-canopy-ecology.py','canopyReplacement'],['scripts/unreal/unknown.py','canopyReplacement']])
    assert.throws(()=>validateGrovePlanOwner({owner},key));
  assert.throws(()=>validateGrovePlanOwner({owner:'scripts/unreal/exterior-canopy-growth.py'},'unknown'));
});

test('actual saved canopy growth and original replacement receipts retain their exact owner/status pairs',async()=>{
  for(const [candidate,expectedOwner,expectedStatus] of [
    ['exterior-20260930-r9','scripts/unreal/exterior-canopy-growth.py','verified-source-grove-canopy-growth'],
    ['exterior-20260930-r8','scripts/unreal/exterior-canopy-masters.py','verified-source-grove-canopy-replacement']]) {
    const report=JSON.parse(await readFile(resolve(root,'output/unreal',candidate,'exterior-import-report.json')));
    const grove=report.canopyReplacement,bytes=await readFile(grove.plan),plan=JSON.parse(bytes);
    assert.equal(hash(bytes),grove.planSha256);assert.equal(report.inputFiles[grove.plan],grove.planSha256);
    assert.equal(plan.owner,expectedOwner);assert.equal(grove.validation.status,expectedStatus);
    validateGroveReceipt(report);validateGrovePlanReceipt(report,plan,'canopyReplacement');
    assert.equal(grove.savedReadback.instances,78);assert.equal(grove.deletedTrees,0);
  }
});

test('self-consistently repinned canopy plans cannot swap growth and original native validation status',async()=>{
  const report=JSON.parse(await readFile(resolve(root,'output/unreal/exterior-20260930-r9/exterior-import-report.json')));
  const plan=JSON.parse(await readFile(report.canopyReplacement.plan));
  const temporary=await mkdtemp(resolve(root,'output/unreal/canopy-node-status-negative-'));
  try {
    for(const [index,owner,status] of [
      [0,'scripts/unreal/exterior-canopy-growth.py','verified-source-grove-canopy-replacement'],
      [1,'scripts/unreal/exterior-canopy-masters.py','verified-source-grove-canopy-growth']]) {
      const unsafePlan=structuredClone(plan),unsafeReport=structuredClone(report);
      unsafePlan.owner=owner;unsafeReport.canopyReplacement.validation.status=status;
      const path=resolve(temporary,index+'-plan.json'),bytes=Buffer.from(JSON.stringify(unsafePlan));
      await writeFile(path,bytes);unsafeReport.canopyReplacement.plan=path;
      unsafeReport.canopyReplacement.planSha256=hash(bytes);unsafeReport.inputFiles[path]=hash(bytes);
      validateGroveReceipt(unsafeReport);
      assert.throws(()=>validateGrovePlanReceipt(unsafeReport,JSON.parse(bytes),'canopyReplacement'),
        /Grove plan owner\/native status pair differs/);
    }
  } finally {await rm(temporary,{recursive:true,force:true});}
});
