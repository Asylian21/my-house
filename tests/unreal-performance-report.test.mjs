import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtemp,mkdir,writeFile,readFile,rm,symlink} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {execFile} from 'node:child_process';
import {promisify} from 'node:util';
import {mergeMeasurementRows,writePerformanceReport} from '../scripts/unreal/performance-report.mjs';

const sha=bytes=>createHash('sha256').update(bytes).digest('hex');
const row=(directory,phase='baseline')=>({phase,scene:'street-day',profile:'balanced',output:'retina',motion:'static',
  packageReportSha256:'1'.repeat(64),eligibleForAcceptance:false,
  gpuIntegrity:{status:'unavailable'},limitations:['historical-qualification'],
  artifacts:{directory,qaSha256:'2'.repeat(64),runtimeSha256:'3'.repeat(64),imageSha256:'4'.repeat(64)}});

test('merge preserves historical row fields and artifact hashes without mutating either input',()=>{
  const local=[row('/current/qa/shipping-final-123/current','shipping-final')],old={generatedAt:'old',rows:[row('/original/qa/baseline-123/old')]};
  const before=JSON.stringify({local,old});const result=mergeMeasurementRows(local,old);
  assert.equal(result.length,2);assert.deepEqual(result,[...local,...old.rows]);
  assert.equal(result[1].artifacts.directory,'/original/qa/baseline-123/old');
  assert.equal(JSON.stringify({local,old}),before);
});
test('merge rejects duplicate normalized artifact directories and incomplete imported provenance',()=>{
  const original=row('/historical/qa/run');
  for (const directory of ['/historical/qa/run','/historical/qa/../qa/run/'])
    assert.throws(()=>mergeMeasurementRows([original],{rows:[row(directory)]}),/Duplicate measurement artifact directory/);
  assert.throws(()=>mergeMeasurementRows([],{rows:[original,structuredClone(original)]}),/Duplicate measurement artifact directory/);
  assert.throws(()=>mergeMeasurementRows([],{rows:[row('relative/artifact')]}),/must be absolute/);
  const broken=structuredClone(original);delete broken.artifacts.runtimeSha256;
  assert.throws(()=>mergeMeasurementRows([],{rows:[broken]}),/runtimeSha256/);
  assert.throws(()=>mergeMeasurementRows([],{entries:[]}),/must contain rows/);
});
test('report CLI imports additional measurements, retains source bytes and records the input hash',async t=>{
  const dir=await mkdtemp(resolve(tmpdir(),'brezi-report-merge-'));t.after(()=>rm(dir,{recursive:true,force:true}));
  const output=resolve(dir,'fresh');await mkdir(resolve(output,'qa'),{recursive:true});
  const path=resolve(dir,'historical-measurements.json'),old={generatedAt:'historical-date',rows:[row('/historical/qa/baseline-123/old')]};
  const bytes=JSON.stringify(old,null,2)+'\n';await writeFile(path,bytes);
  await promisify(execFile)(process.execPath,[resolve(import.meta.dirname,'../scripts/unreal/performance-report.mjs'),output,path]);
  const result=JSON.parse(await readFile(resolve(output,'measurements.json'),'utf8'));
  assert.deepEqual(result.rows,old.rows);assert.equal(result.additionalInput.path,path);
  assert.equal(result.additionalInput.sha256,sha(bytes));assert.equal(result.additionalInput.rowCount,1);
  assert.equal(await readFile(path,'utf8'),bytes);
  const ownReport=resolve(output,'measurements.json'),alias=resolve(dir,'report-alias.json');
  const protectedBytes=await readFile(ownReport,'utf8');await symlink(ownReport,alias);
  await assert.rejects(writePerformanceReport(output,ownReport),/cannot be the destination report/);
  await assert.rejects(writePerformanceReport(output,alias),/cannot be the destination report/);
  assert.equal(await readFile(ownReport,'utf8'),protectedBytes);
});
