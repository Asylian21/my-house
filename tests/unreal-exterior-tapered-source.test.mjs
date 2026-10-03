// Host guards for the real source adapter; no new native import is implied.
import test from 'node:test';
import assert from 'node:assert/strict';
import {readFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {validateNaturalLawnPlan,validateNaturalLawnReceipt} from '../scripts/unreal/exterior-source.mjs';

const root=resolve(import.meta.dirname,'..');
const planPath=resolve(root,'output/unreal/exterior-lawn-tapered-integration-20261001-r1c/lawn-natural-plan.json');
const planBytes=await readFile(planPath),sourcePlan=JSON.parse(planBytes);
const nativeBasis=JSON.parse(await readFile(resolve(root,'output/unreal/exterior-20261001-r10/exterior-import-report.json')));
const hash=bytes=>createHash('sha256').update(bytes).digest('hex');

function fixture() {
  // Only the already verified legacy hide witness is taken from R10. The
  // proposed new source fields form a test fixture, never a native receipt.
  const plan=structuredClone(sourcePlan),report=structuredClone(nativeBasis);
  report.inputFiles[planPath]=hash(planBytes);
  report.naturalLawn.plan=planPath;report.naturalLawn.planSha256=hash(planBytes);
  report.naturalLawn.audit=structuredClone(plan.audit);
  for(const key of ['coverageReceipt','boundaryCoverageReceipt']) {
    report.naturalLawn[key]=structuredClone(plan[key]);report.inputFiles[plan[key].path]=plan[key].sha256;
  }
  return {plan,report};
}

test('actual covered taper source preserves independent coverage and the original saved legacy scope',async()=>{
  const {plan,report}=fixture();
  validateNaturalLawnPlan(report,plan);validateNaturalLawnReceipt(report);
  assert.equal(plan.owner,'scripts/unreal/exterior-lawn-tapered-integration.py');
  assert.equal(plan.lawnPlacements.length,102011);assert.equal(plan.groups.length,40);
  for(const [key,body]of [['coverageReceipt','physicalCoverage'],['boundaryCoverageReceipt','boundaryCoverage']]) {
    const bytes=await readFile(plan[key].path);
    assert.equal(hash(bytes),plan[key].sha256);assert.deepEqual(JSON.parse(bytes),plan.audit[body]);
  }
});

test('tapered source cannot impersonate the old upright owner or borrow its coverage labels',()=>{
  for(const change of [
    plan=>{plan.owner='scripts/unreal/exterior-lawn-upright.py';},
    plan=>{plan.audit.status='MEASURED_UPRIGHT_MANAGED_LAWN_STUDY_NOT_NATIVE_ACCEPTED';},
    plan=>{plan.audit.physicalCoverage.status='MEASURED_UPRIGHT_STUDY_COVERAGE_NOT_NATIVE_ACCEPTED';},
    plan=>{plan.audit.boundaryCoverage.status='MEASURED_UPRIGHT_STUDY_BOUNDARY_COVERAGE_NOT_NATIVE_ACCEPTED';},
  ]) {
    const {plan,report}=fixture();change(plan);report.naturalLawn.audit=structuredClone(plan.audit);
    assert.throws(()=>validateNaturalLawnPlan(report,plan));
  }
});

test('self-consistent tapered claims below physical coverage or boundary limits are rejected',()=>{
  for(const change of [
    plan=>{plan.audit.physicalCoverage.windows[0].lods[0].projectedCoverage=.749;},
    plan=>{plan.audit.physicalCoverage.windows[0].lods[2].tenCmBinCoverageP10=.54;},
    plan=>{plan.audit.boundaryCoverage.windows[1].lods[1].boundaryBands[2].physicalCoverFraction=.49;},
    plan=>{plan.audit.physicalCoverage.windows[0].lods[0].bareTenCmBins=1;},
    plan=>{plan.audit.allInstancesTriangleBudgetByLod[2]=20000000;},
  ]) {
    const {plan,report}=fixture();change(plan);report.naturalLawn.audit=structuredClone(plan.audit);
    assert.throws(()=>validateNaturalLawnPlan(report,plan));assert.throws(()=>validateNaturalLawnReceipt(report));
  }
});

test('both new taper coverage receipts must be separately pinned and match the source plan',()=>{
  for(const key of ['coverageReceipt','boundaryCoverageReceipt'])for(const action of ['omit','hash','borrow']) {
    const {plan,report}=fixture();
    if(action==='omit')delete report.inputFiles[plan[key].path];
    else if(action==='hash')report.inputFiles[plan[key].path]='a'.repeat(64);
    else report.naturalLawn[key]=structuredClone(nativeBasis.naturalLawn[key]);
    assert.throws(()=>validateNaturalLawnPlan(report,plan));
  }
});
