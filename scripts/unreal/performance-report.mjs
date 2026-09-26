import {readFile,writeFile,readdir,realpath} from 'node:fs/promises';
import {resolve,isAbsolute} from 'node:path';
import {createHash} from 'node:crypto';
import {pathToFileURL} from 'node:url';
const sha=b=>createHash('sha256').update(b).digest('hex');

export function mergeMeasurementRows(localRows, additional) {
  if (!Array.isArray(localRows) || !Array.isArray(additional?.rows)) throw Error('Additional measurements must contain rows');
  const rows=[...localRows,...additional.rows],seen=new Set();
  for (const row of rows) {
    const directory=row?.artifacts?.directory;
    if (typeof directory!=='string' || !isAbsolute(directory)) throw Error('Measurement artifact directory must be absolute');
    for (const field of ['qaSha256','runtimeSha256','imageSha256'])
      if (typeof row.artifacts[field]!=='string' || row.artifacts[field].length!==64 || !/^[a-f0-9]{64}$/.test(row.artifacts[field]))
        throw Error(`Measurement artifact ${field} must be a lowercase SHA256 hash`);
    const identity=resolve(directory);
    if (seen.has(identity)) throw Error(`Duplicate measurement artifact directory: ${directory}`);
    seen.add(identity);
  }
  // Preserve each imported row, including its original paths, hashes and qualifications.
  return rows;
}

export async function writePerformanceReport(output, additionalPath) {
output=resolve(output);
let additional=null,additionalInput=null;
if (additionalPath) {
  const path=resolve(additionalPath),sourcePath=await realpath(path);
  const destinationPath=await realpath(resolve(output,'measurements.json')).catch(e=>{if(e.code==='ENOENT')return resolve(output,'measurements.json');throw e;});
  if (sourcePath===destinationPath) throw Error('Additional measurements cannot be the destination report');
  const bytes=await readFile(path);
  additional=JSON.parse(bytes);
  // Validate before writing any output, including an otherwise empty local report.
  mergeMeasurementRows([],additional);
  additionalInput={path,sha256:sha(bytes),generatedAt:additional.generatedAt??null,rowCount:additional.rows.length,
    method:'Imported saved rows unchanged; artifact paths/hashes retained, source measurements file not rewritten.'};
}
const localRows=[];
for(const session of await readdir(resolve(output,'qa'),{withFileTypes:true})){
  if(!session.isDirectory())continue;
  for(const run of await readdir(resolve(output,'qa',session.name),{withFileTypes:true})){
    if(!run.isDirectory())continue;
    const dir=resolve(output,'qa',session.name,run.name);
    try{
      const qbytes=await readFile(resolve(dir,'qa.json')),q=JSON.parse(qbytes);
      const rbytes=await readFile(resolve(dir,'runtime.json')),r=JSON.parse(rbytes);
      const focus=r.focusDuringBenchmark,frame=r.frameInterval,motion=r.realtimeOrbit??r.realtimeWalk;
      const valid=r.status==='capture-complete'&&frame?.status==='measured'&&r.screenshotSaved&&q.outcome?.code===0;
      const traced=q.args?.includes('-trace=cpu,gpu,frame')??false;
      const gpu=r.gpuFrameFromRHITimer;
      // Preserve the raw Metal query data. A purported single GPU frame longer
      // than the entire sampled wall-time window cannot describe this run.
      const gpuOutlier=gpu?.status==='measured'&&frame?.status==='measured'
        &&gpu.maxMs>frame.meanMs*frame.sampleCount;
      const gpuIntegrity={status:gpuOutlier?'unreliable-timestamp-outlier':gpu?.status??'unavailable',
        ...(gpuOutlier?{reason:'GPU maximum exceeds the entire measured wall-time window; raw GPU aggregates are retained but not accepted as timing evidence.'}:{})};
      const eligibleForAcceptance=valid&&q.status==='measured'&&frame.sampleCount>=240
        &&focus?.applicationForegroundThroughoutBenchmark===true&&!traced&&(!motion||motion.measurementCompleted===true);
      localRows.push({phase:q.phase,scene:q.scene,profile:q.profile,output:q.mode,motion:q.motion,software:q.software,
        statOverlays:q.statOverlays??(q.args?.some(a=>a.includes('stat gpu'))??false),
        nativeStatus:r.status,process:q.outcome,validation:q.status,valid,configuration:r.buildConfiguration??'Development',
        eligibleForAcceptance,
        fps:frame?.meanMs?1000/frame.meanMs:null,frame,gpu,gpuIntegrity,cpu:r.cpuGameThreadActive,
        render:r.cpuRenderThreadActive,pixels:r.screenshotPixels,foreground:focus?.applicationForegroundThroughoutBenchmark??false,
        foregroundFraction:focus?.sampleCount?focus.applicationForegroundSamples/focus.sampleCount:0,
        motionComplete:motion?.measurementCompleted??null,motionSamples:motion?.cameraSamples??null,
        cameraTravelCm:motion?.cameraTravelCm??null,settings:r.renderSettings,postprocess:r.finalViewPostProcessSettings,
        gpuProfile:r.gpuProfile,glassCaptures:r.doubleGlass?.reduce((n,p)=>n+p.captureCount,0),
        artifacts:{directory:dir,qaSha256:sha(qbytes),runtimeSha256:sha(rbytes),imageSha256:sha(await readFile(resolve(dir,'capture.png')))},
        packageReportSha256:q.packageReportSha256,limitations:[...(!valid?['native-process-or-capture-failure']:[]),
          ...(q.status!=='measured'?['qa-validation-failed']:[]),
          ...(frame?.sampleCount<240?['fewer-than-240-samples']:[]),...(motion&&motion.measurementCompleted!==true?['motion-completion-gate-not-met']:[]),
          ...(!focus?.applicationForegroundThroughoutBenchmark?['foreground-not-continuous']:[]),
          ...(traced?['traced-attribution-run-not-untraced-performance']:[]),
          ...(gpuOutlier?['gpu-timestamp-outlier-raw-aggregates-unreliable']:[])]});
    }catch(e){if(e.code!=='ENOENT')throw e;}
  }
}
const rows=additional?mergeMeasurementRows(localRows,additional):localRows;
const f=x=>typeof x==='number'?x.toFixed(2):'—';
const md=['# BreziTwin — native performance measurements','',
  'Derived from saved native Metal runtime reports. FPS = 1000 / mean wall-clock frame interval. GPU timers are separate; no physical display-presentation claim.',
  '', '| Phase | Scene | Profile | Output | Motion | FPS | Frame P50/P95/P99 ms | GPU mean ms | GT P99 ms | Frames | Limitations |',
  '|---|---|---|---|---|---:|---|---:|---:|---:|---|',
  ...rows.map(r=>`| ${r.phase} | ${r.scene} | ${r.profile} | ${r.pixels?.join('×')} | ${r.motion} | ${f(r.fps)} | ${f(r.frame?.p50Ms)} / ${f(r.frame?.p95Ms)} / ${f(r.frame?.p99Ms)} | ${r.gpuIntegrity.status==='unreliable-timestamp-outlier'?'unreliable':f(r.gpu?.meanMs)} | ${f(r.cpu?.p99Ms)} | ${r.frame?.sampleCount??0} | ${r.limitations.join(', ')||'none recorded'} |`),
  '', 'Original per-run PNG, JSON, process logs and available GPU profile/Insights files are linked by absolute directory in measurements.json.', ''];
await writeFile(resolve(output,'measurements.json'),JSON.stringify({generatedAt:new Date().toISOString(),
  ...(additionalInput?{additionalInput}:{}),rows},null,2)+'\n');
await writeFile(resolve(output,'measurements.md'),md.join('\n'));
console.log(JSON.stringify({rows:rows.length,phases:[...new Set(rows.map(r=>r.phase))],report:resolve(output,'measurements.md')}));
}

if (process.argv[1] && import.meta.url===pathToFileURL(resolve(process.argv[1])).href)
  await writePerformanceReport(process.argv[2]??'output/unreal/performance-20260923-r1',process.argv[3]);
