// Reuse the conservative source planner; stop before any door or room change.
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {readFile, writeFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {fileURLToPath} from 'node:url';
import {buildWalkthroughContract} from './walkthrough-contract.mjs';

const INPUT_FILES=['scene.json','walking.json','hidden-collision.json'];

// Pure boundary after source planning: preserve its points and stop at its first
// door/room transition. Tests can exercise this without a generated house export.
export function buildRealtimeWalkContract(full, bytes) {
  assert.equal(bytes.length,INPUT_FILES.length,'Expected all three source inputs');
  const sceneSha256=createHash('sha256').update(bytes[0]).digest('hex');
  assert.equal(full.sceneSha256,sceneSha256,'Planned route must match the exact source scene bytes');
  const points=[full.startEyeCm.map((v,i)=>i===2?0:v)];
  for(const step of full.steps){
    if(step.kind==='door'||step.regionId!=='ROOM-1-03')break;
    if(step.kind==='move')points.push(step.targetCm);
  }
  assert(points.length>=3 && points.length<=32,'Expected living-to-kitchen source aisle with at least two legs');
  const distanceCm=points.slice(1).reduce((sum,p,i)=>sum+Math.hypot(p[0]-points[i][0],p[1]-points[i][1]),0);
  assert(distanceCm>=300&&distanceCm<=2000,'Source aisle distance outside study bounds');
  return {schemaVersion:1,sceneSha256,pointsCm:points,oneWayDistanceCm:distanceCm,
    regionId:'ROOM-1-03',source:'Initial same-room segments of buildWalkthroughContract before the first door',
    traversal:'back-and-forth; ordinary native CMC motion; native floor/sweep validation required',
    inputHashes:Object.fromEntries(INPUT_FILES.map((p,i)=>[p,createHash('sha256').update(bytes[i]).digest('hex')]))};
}

export async function prepareRealtimeWalk(geometry, destination) {
  const bytes=await Promise.all(INPUT_FILES.map(p=>readFile(resolve(geometry,p))));
  const [scene,walking,hidden]=bytes.map(b=>JSON.parse(b));
  const sceneSha256=createHash('sha256').update(bytes[0]).digest('hex');
  const full=buildWalkthroughContract(scene,walking,hidden,{sceneSha256});
  const contract=buildRealtimeWalkContract(full,bytes);
  await writeFile(destination,JSON.stringify(contract,null,2)+'\n');
  return contract;
}
if(process.argv[1]&&resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  const [geometry,destination]=process.argv.slice(2);assert(geometry&&destination,'geometry directory and destination required');
  console.log(JSON.stringify(await prepareRealtimeWalk(geometry,destination)));
}
