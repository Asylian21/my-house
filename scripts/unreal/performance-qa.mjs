// Sequential, uncapped wall-time measurements of the actual packaged Metal app.
// Every launch owns a fresh sandbox; historical app contents are read-only.
import {spawn} from 'node:child_process';
import {readFile, writeFile, mkdir, readdir, copyFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {homedir} from 'node:os';
import {createHash, randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
import {verifyPackagedPayload} from './package-verify.mjs';
import {resolveAppLaunch, requireIdleApp, inspectLauncherExecution} from './app-launch.mjs';
import {prepareRealtimeWalk} from './realtime-walk-contract.mjs';

const root=resolve(import.meta.dirname,'../..');
const output=resolve(root,process.env.BREZI_PERFORMANCE_OUTPUT??'output/unreal/performance-20260923-r1');
const source=resolve(root,process.env.BREZI_MODEL_OUTPUT??'output/unreal/rural-context-20260923-r4');
const phase=process.env.BREZI_QA_PHASE??'baseline';
const baseline=phase.startsWith('baseline');
const sha=b=>createHash('sha256').update(b).digest('hex');
const save=(p,v)=>writeFile(p,JSON.stringify(v,null,2)+'\n');
const bytes=await readFile(resolve(source,'model-package.json')),receipt=JSON.parse(bytes);
await verifyPackagedPayload(receipt.appPath,receipt.bundle);
const launch=await resolveAppLaunch(receipt.appPath,receipt.bundle);
const shipping=receipt.gameConfiguration==='Shipping';
const select=(name,defaults)=>process.env[name]?.split(',')??defaults;
const scenes=select('BREZI_QA_SCENES',['street-day','terrace-day','interior-day','interior-night']);
const profiles=select('BREZI_QA_PROFILES',['performance','balanced','native']);
const outputs=select('BREZI_QA_OUTPUTS',['retina','4k']);
const motions=select('BREZI_QA_MOTIONS',['static','orbit']);
const seconds=Number(process.env.BREZI_QA_SECONDS??60);
const software=process.env.BREZI_QA_SOFTWARE==='1';
const trace=process.env.BREZI_QA_TRACE==='1';
const statOverlays=process.env.BREZI_QA_STATS!=='0'&&!shipping;
const extra=process.env.BREZI_QA_CVARS?.split(';')??[];
assert(!shipping||extra.length===0,'Shipping ignores ExecCmds; use the explicit verified diagnostic switches instead of arbitrary cvar overrides');
const session=resolve(output,'qa',`${phase}-${Date.now()}`);await mkdir(session,{recursive:true});
const results=[];
for(const profile of profiles)for(const mode of outputs)for(const scene of scenes)for(const motion of motions){
  const id=`${scene}-${mode}-${profile}-${motion}${software?'-software':''}-${randomUUID()}`;
  const evidence=resolve(session,id);await mkdir(evidence);
  const sandbox=resolve(homedir(),'Library/Containers/local.brezi.twin/Data/Library/Application Support/BreziTwin/QA',id);await mkdir(sandbox,{recursive:true});
  const [view,time]=scene.split('-');
  if(motion==='walk'){
    assert.equal(view,'interior','Real-time route starts at the validated interior arrival');
    await prepareRealtimeWalk(resolve(source,'geometry'),resolve(sandbox,'walk-route.json'));
  }
  const pair={native:[100,baseline?200:100],balanced:[67,100],performance:[50,100]}[profile];
  assert(pair,'Unknown profile');assert(['static','orbit','walk'].includes(motion));
  // Explicit old cvars avoid the historical diagnostic profile lock. New builds
  // exercise their named recipe, rather than silently replacing it with commands.
  const cmds=[...(baseline?[`r.ScreenPercentage ${pair[0]}`,`r.TSR.History.ScreenPercentage ${pair[1]}`]:[]),
    'r.VSync 0','t.MaxFPS 0',...(software?['r.Lumen.HardwareRayTracing 0']:[]),...extra];
  if(motion==='static'&&statOverlays)cmds.push('stat unit','stat gpu','stat scenerendering');
  const args=['-windowed','-ResX=1920','-ResY=1080',`-UserDir=${sandbox}/`,`-abslog=${sandbox}/runtime.log`,
    `-BreziOutput=${mode}`,`-BreziView=${view}`,`-BreziRenderProfile=${profile}`,'-BreziCaptureScene','-BreziExitAfterCapture',
    '-BreziWarmupFrames=240','-BreziBenchmarkFrames=300','-BreziWalkAudit',`-ExecCmds=${cmds.join(',')}`,
    ...(!baseline?['-BreziBenchmarkUncapped',...(software?['-BreziSoftwareLumen']:[])]:[]),
    ...(time==='night'?['-BreziNight']:[]),
    ...(motion==='orbit'?['-BreziRealtimeOrbit',`-BreziBenchmarkSeconds=${seconds}`]:[]),
    ...(motion==='walk'?['-BreziRealtimeWalk',`-BreziRealtimeWalkRoute=${sandbox}/walk-route.json`,`-BreziBenchmarkSeconds=${seconds}`]:[]),
    ...(motion==='static'&&!shipping?['-BreziProfileGPU']:[]),
    // The installed UE5.8 dedicated PSO pool outlives traced thread-local memory
    // at shutdown. Use the normal task graph only in this attribution launch.
    ...(trace?['-trace=cpu,gpu,frame','-notracethreading',
      '-ini:Engine:[ConsoleVariables]:r.pso.PrecompileThreadPoolSize=0,[ConsoleVariables]:r.pso.PrecompileThreadPoolPercentOfHardwareThreads=0',
      `-tracefile=${sandbox}/runtime.utrace`]:[])];
  const row={id,phase,profile,mode,scene,motion,software,statOverlays:motion==='static'&&statOverlays,source,evidence,args,packageReportSha256:sha(bytes),startedAt:new Date().toISOString()};
  console.log(JSON.stringify({event:'start',id,evidence}));
  try{
    await requireIdleApp();const chunks=[];
    const outcome=await new Promise((accept,reject)=>{
      const child=spawn(launch.executable,args,{cwd:root,stdio:['ignore','pipe','pipe']});
      const timer=setTimeout(()=>{child.kill('SIGTERM');},900000);
      for(const s of [child.stdout,child.stderr])s.on('data',c=>chunks.push(c));
      child.once('error',e=>{clearTimeout(timer);reject(e);});
      child.once('close',(code,signal)=>{clearTimeout(timer);accept({code,signal,pid:child.pid});});
    });
    const processLog=Buffer.concat(chunks);await writeFile(resolve(evidence,'process.log'),processLog);
    const log=await readFile(resolve(sandbox,'runtime.log')).catch(e=>{if(shipping&&e.code==='ENOENT')return Buffer.from('');throw e;});
    await writeFile(resolve(evidence,'runtime.log'),log);
    const entry=inspectLauncherExecution(launch,outcome,processLog+'\n'+log);
    Object.assign(row,{outcome,entry});
    const diagnostics=resolve(sandbox,'Saved/Diagnostics');
    const files=await readdir(diagnostics),reports=files.filter(p=>p.endsWith('.json'));assert.equal(reports.length,1);
    const raw=await readFile(resolve(diagnostics,reports[0])),r=JSON.parse(raw);
    await writeFile(resolve(evidence,'runtime.json'),raw);
    for(const f of files.filter(f=>f.endsWith('.log')))await copyFile(resolve(diagnostics,f),resolve(evidence,f));
    await copyFile(r.screenshotPath,resolve(evidence,'capture.png'));
    if(trace)await copyFile(resolve(sandbox,'runtime.utrace'),resolve(evidence,'runtime.utrace'));
    assert.equal(r.status,'capture-complete');assert.equal(r.rhi,'Metal');
    assert.equal(r.renderSettings['r.ScreenPercentage'],pair[0]);assert.equal(r.renderSettings['r.TSR.History.ScreenPercentage'],pair[1]);
    assert.equal(r.walking.worldContractValidated,true);assert.deepEqual(r.walking.worldContractErrors,[]);
    assert.equal(r.walking.sceneSha256,receipt.sourceManifestSha256);
    assert.deepEqual(r.screenshotPixels,mode==='4k'?[3840,2160]:[1920,1080]);
    for(const override of extra){
      const match=override.trim().match(/^(\S+)\s+(-?\d+(?:\.\d+)?)$/);
      assert(match,'Only numeric, verifiable cvar study overrides are supported');
      const [,name,value]=match;
      if(name==='r.Brezi.DoubleGlass')assert(r.doubleGlass.every(p=>p.enabled===(Number(value)!==0)));
      else {assert(name in r.renderSettings,'Requested cvar has no runtime readback: '+name);assert.equal(r.renderSettings[name],Number(value));}
    }
    Object.assign(row,{status:'measured',runtimeReportSha256:sha(raw),screenshotSha256:sha(await readFile(resolve(evidence,'capture.png'))),
      pixels:r.screenshotPixels,frame:r.frameInterval,gpu:r.gpuFrameFromRHITimer,cpu:r.cpuGameThreadActive,render:r.cpuRenderThreadActive,
      settings:r.renderSettings,postprocess:r.finalViewPostProcessSettings,gpuProfile:r.gpuProfile,
      foreground:r.focusDuringBenchmark,movement:r.realtimeOrbit??r.realtimeWalk??null,glass:r.doubleGlass});
    if(motion==='orbit')assert.equal(r.realtimeOrbit.measurementCompleted,true);
    if(motion==='walk'){
      assert.equal(r.realtimeWalk.measurementCompleted,true);
      assert.equal(r.walking.cameraMode,'walking');assert(r.walking.groundedEyeSamples>0);
      assert.equal(r.walking.unmeasuredOrAirborneEyeSamples,0);assert(r.walking.maxEyeHeightErrorCm<=.2);
      row.walking=r.walking;
    }
    if(software)assert.equal(r.renderSettings['r.Lumen.HardwareRayTracing'],0);
    if(!baseline){
      const expected={native:[3,3,3,3,3,3,1,1],balanced:[2,2,2,2,2,2,.65,.75],performance:[2,1,2,1,1,1,.35,.5]}[profile];
      for(const [i,name] of ['GlobalIllumination','Shadow','Reflection','Foliage','PostProcess','Effects'].entries())
        assert.equal(r.renderSettings[`sg.${name}Quality`],expected[i]);
      assert(Math.abs(r.renderSettings['foliage.DensityScale']-expected[6])<1e-5);
      assert(Math.abs(r.finalViewPostProcessSettings.lumenFinalGatherQuality-expected[7])<1e-5);
      const pp={native:[1,1,1,15000,15000],balanced:[.75,1,1,10000,10000],performance:[.5,.5,.5,6000,6000]}[profile];
      for(const [i,name] of ['lumenReflectionQuality','lumenSceneLightingQuality','lumenSceneDetail','lumenSceneViewDistance','lumenMaxTraceDistance'].entries())
        assert(Math.abs(r.finalViewPostProcessSettings[name]-pp[i])<1e-5,`Effective ${name} differs`);
      assert.equal(r.renderSettings['r.Brezi.LocalLightShadows'],profile==='performance'?0:1);
      assert.equal(r.renderSettings['r.VSync'],0);assert.equal(r.renderSettings['t.MaxFPS'],0);
      if(profile==='performance')assert.equal(r.renderSettings['r.Lumen.HardwareRayTracing'],0);
      assert.equal(r.doubleGlass.length,19);
      assert(r.doubleGlass.every(p=>p.configured&&p.ior===1.52));
      assert(r.doubleGlass.every(p=>profile==='native'?p.enabled:(!p.enabled&&!p.overlayVisible)));
      assert(r.doubleGlass.every(p=>p.captureBudgetPerFrame===1&&p.warmupCaptureBudget<=2&&p.captureUsesLumen===false));
    }
    if(shipping){
      assert.equal(outcome.code,0);assert.equal(outcome.signal,null);assert.equal(r.processId,outcome.pid);
      assert.equal(r.buildConfiguration,'Shipping');
      assert(entry.errors.every(e=>e==='Engine initialization after app entry was not observed'));
      row.shippingLaunch={status:'native-report-pid-and-configuration-verified',loggingAvailable:log.length>0};
    }else assert.equal(entry.status,'recorded-self-exec-entry-chain');
  }catch(e){row.status='failed';row.error=String(e.stack??e);process.exitCode=1;}
  row.endedAt=new Date().toISOString();await save(resolve(evidence,'qa.json'),row);results.push(row);
  await save(resolve(session,'summary.json'),{phase,source,packageReportSha256:sha(bytes),results});
  console.log(JSON.stringify({event:'end',id,status:row.status,frame:row.frame,error:row.error}));
}
await verifyPackagedPayload(receipt.appPath,receipt.bundle);
console.log(JSON.stringify({status:process.exitCode?'completed-with-failures':'suite-complete',session}));
