import test from 'node:test';
import assert from 'node:assert/strict';
import {access,mkdtemp,rm,writeFile} from 'node:fs/promises';
import {tmpdir} from 'node:os';
import {resolve} from 'node:path';
import {createHash} from 'node:crypto';
import {buildRealtimeWalkContract,prepareRealtimeWalk} from '../scripts/unreal/realtime-walk-contract.mjs';

const hash=bytes=>createHash('sha256').update(bytes).digest('hex');
const encode=value=>Buffer.from(JSON.stringify(value,null,2)+'\n');
const inputFiles=['scene.json','walking.json','hidden-collision.json'];
const room='ROOM-1-03';

// This is a source-planner boundary fixture, not a house or native collision
// fixture. The full planner still runs in prepareRealtimeWalk; its pathfinding
// tests and native floor/sweep validation provide the other acceptance layers.
function fixture() {
  const scene={activeDesign:{variant:'C',heatingLayout:'B',livingLayout:'B'},
    units:'millimetres',coordinateSystem:'right-handed Z-up',objSha256:'a'.repeat(64)};
  const sceneBytes=encode(scene),sceneSha256=hash(sceneBytes);
  const walking={provenance:{sceneSha256}};
  const hidden={sourceManifestSha256:sceneSha256,mainObjSha256:scene.objSha256};
  const bytes=[sceneBytes,encode(walking),encode(hidden)];
  const full={sceneSha256,startEyeCm:[0,-400,165],steps:[
    {kind:'visit',regionId:room,targetCm:[0,-400,0]},
    {kind:'move',regionId:room,targetCm:[200,-400,0]},
    {kind:'move',regionId:room,targetCm:[200,-100,0]},
    {kind:'door',regionId:room,doorId:'closed-door',targetCm:[200,0,0]},
    {kind:'move',regionId:room,targetCm:[200,100,0]},
    {kind:'move',regionId:'ROOM-1-07',targetCm:[200,200,0]},
  ]};
  return {scene,walking,hidden,bytes,full};
}

test('realtime extraction stops before the first door and binds all exact source bytes',()=>{
  const {bytes,full}=fixture();
  const route=buildRealtimeWalkContract(full,bytes);
  assert.equal(route.regionId,room);
  assert.deepEqual(route.pointsCm,[[0,-400,0],[200,-400,0],[200,-100,0]]);
  assert.equal(route.oneWayDistanceCm,500);
  assert.equal(route.sceneSha256,hash(bytes[0]));
  assert.deepEqual(route.inputHashes,Object.fromEntries(inputFiles.map((name,i)=>[name,hash(bytes[i])])));
  assert.deepEqual(buildRealtimeWalkContract(full,bytes),route);
  assert.equal(full.startEyeCm[2],165,'extracting ground points must not alter the planned eye position');

  // Hashes attest to bytes, including whitespace, rather than reserialized JSON.
  const padded=bytes.map(value=>Buffer.concat([value,Buffer.from(' ')]));
  const paddedRoute=buildRealtimeWalkContract({...full,sceneSha256:hash(padded[0])},padded);
  for(const name of inputFiles)assert.notEqual(paddedRoute.inputHashes[name],route.inputHashes[name]);
  assert.deepEqual(paddedRoute.pointsCm,route.pointsCm);
});

test('a room transition without a door also terminates the route permanently',()=>{
  const {bytes,full}=fixture();
  full.steps.splice(3,1,{kind:'visit',regionId:'ROOM-1-07',targetCm:[200,0,0]});
  assert.deepEqual(buildRealtimeWalkContract(full,bytes).pointsCm,[[0,-400,0],[200,-400,0],[200,-100,0]]);
});

test('a plan from different scene bytes cannot be reused',()=>{
  const {bytes,full}=fixture();
  bytes[0]=Buffer.concat([bytes[0],Buffer.from(' ')]);
  assert.throws(()=>buildRealtimeWalkContract(full,bytes),/Planned route must match the exact source scene bytes/);
});

test('realtime extraction keeps the bounded leg-count and distance contract',()=>{
  const {bytes,full}=fixture();
  for(const steps of [full.steps.slice(0,2),Array.from({length:32},(_,i)=>({kind:'move',regionId:room,targetCm:[i*15,-400,0]}))])
    assert.throws(()=>buildRealtimeWalkContract({...full,steps},bytes),/at least two legs/);
  for(const distance of [299,2001]){
    const steps=[{kind:'move',regionId:room,targetCm:[distance/2,-400,0]},
      {kind:'move',regionId:room,targetCm:[distance,-400,0]}];
    assert.throws(()=>buildRealtimeWalkContract({...full,steps},bytes),/distance outside study bounds/);
  }
});

// These deliberately incomplete source documents reach the real planner's
// provenance gate. Assert the exact mismatched digests so a later unrelated
// failure (e.g. missing rooms) cannot make a stale-source test pass accidentally.
for(const [name,mutate] of [
  ['scene bytes changed',value=>{
    const prior=hash(value.bytes[0]);
    value.bytes[0]=Buffer.concat([value.bytes[0],Buffer.from(' ')]);
    return {actual:prior,expected:hash(value.bytes[0])};
  }],
  ['walking provenance is stale',value=>{
    value.walking.provenance.sceneSha256='b'.repeat(64);value.bytes[1]=encode(value.walking);
    return {actual:value.walking.provenance.sceneSha256,expected:hash(value.bytes[0])};
  }],
  ['collision scene provenance is stale',value=>{
    value.hidden.sourceManifestSha256='c'.repeat(64);value.bytes[2]=encode(value.hidden);
    return {actual:value.hidden.sourceManifestSha256,expected:hash(value.bytes[0])};
  }],
  ['collision OBJ provenance is stale',value=>{
    value.hidden.mainObjSha256='d'.repeat(64);value.bytes[2]=encode(value.hidden);
    return {actual:value.hidden.mainObjSha256,expected:value.scene.objSha256};
  }],
])test(`prepareRealtimeWalk refuses output when ${name}`,async()=>{
  const value=fixture(),mismatch=mutate(value);
  const directory=await mkdtemp(resolve(tmpdir(),'brezi-realtime-stale-'));
  try{
    for(const [i,name] of inputFiles.entries())await writeFile(resolve(directory,name),value.bytes[i]);
    const output=resolve(directory,'route.json');
    await assert.rejects(prepareRealtimeWalk(directory,output),error=>{
      assert.equal(error.code,'ERR_ASSERTION');
      assert.equal(error.actual,mismatch.actual);
      assert.equal(error.expected,mismatch.expected);
      return true;
    });
    await assert.rejects(access(output),{code:'ENOENT'});
  }finally{await rm(directory,{recursive:true,force:true});}
});
