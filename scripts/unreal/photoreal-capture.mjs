// Actual packaged Metal evidence; no image synthesis or post-render retouching.
import { spawn } from 'node:child_process';
import { readFile, writeFile, mkdir, readdir, realpath } from 'node:fs/promises';
import { createHash, randomUUID } from 'node:crypto';
import { resolve } from 'node:path';
import { homedir } from 'node:os';
import assert from 'node:assert/strict';
import { verifyPackagedPayload } from './package-verify.mjs';
import { requireIdleApp, resolveAppLaunch, inspectLauncherExecution } from './app-launch.mjs';

const root = resolve(import.meta.dirname, '../..');
const output = resolve(root, process.env.BREZI_MODEL_OUTPUT ?? 'output/unreal/photoreal-20260923-r3');
const shot = process.argv[2] ?? 'terrace';
const poses = {
  terrace: { view:'terrace', eye:[-880,-1040,165], rotation:[0,38,0], fov:65 },
  living: { view:'interior', eye:[905,-730,145], rotation:[0,60,0], fov:76 },
  'living-wide': { view:'interior', eye:[865,-150,155], rotation:[0,-64,0], fov:72 },
  kitchen: { view:'interior', eye:[995,-465,172], rotation:[0,90,0], fov:70 },
  'sofa-detail': { view:'interior', eye:[965,-608,100], rotation:[-12,50,0], fov:58 },
  'wood-detail': { view:'terrace', eye:[-50,-205,140], rotation:[0,80,0], fov:58 },
  'roof-detail': { view:'terrace', eye:[-480,-500,400], rotation:[-4,58,0], fov:48 },
  'glass-exterior': { view:'terrace', eye:[430,-390,155], rotation:[0,41,0], fov:58 },
  'glass-interior': { view:'interior', eye:[790,-150,145], rotation:[0,-155,0], fov:58 },
  'grass-detail': { view:'terrace', eye:[-670,-520,75], rotation:[-30.018,0,0], fov:58 },
  'grass-edge': { view:'terrace', eye:[-650,-700,70], rotation:[-21.139,16.032,0], fov:60 },
  courtyard: { view:'terrace', eye:[-970,-1060,140], rotation:[0,39.046,0], fov:72 },
};
assert(Object.hasOwn(poses,shot),'Unknown photographic viewpoint');
const pose = poses[shot];
const sha = b => createHash('sha256').update(b).digest('hex');
const save = (p,v) => writeFile(p,JSON.stringify(v,null,2)+'\n');
const packagePath = resolve(output,'model-package.json'), packageBytes = await readFile(packagePath), receipt = JSON.parse(packageBytes);
assert.equal(receipt.status,'current-model-packaged');
const before = await verifyPackagedPayload(receipt.appPath,receipt.bundle);
const launch = await resolveAppLaunch(receipt.appPath,receipt.bundle);
await requireIdleApp();
const rearReflection = process.env.BREZI_DOUBLE_GLASS_QA === 'off' ? 'disabled' : 'enabled';
const id = shot+'-'+rearReflection+'-native-4k-'+randomUUID();
const evidence = resolve(output,'qa',id), sandbox = resolve(homedir(),'Library/Containers/local.brezi.twin/Data/Library/Application Support/BreziTwin/QA',id);
await mkdir(evidence,{recursive:true}); await mkdir(sandbox,{recursive:true});
const commands = ['r.ScreenPercentage 100','r.TSR.History.ScreenPercentage 200',
  'sg.GlobalIlluminationQuality 3','sg.ReflectionQuality 3','sg.ShadowQuality 3',
  'r.Lumen.TranslucencyReflections.FrontLayer.Enable 1',
  'r.Brezi.DoubleGlass '+(rearReflection === 'enabled' ? '1' : '0'),
  'EnableCheats',`BugItGo ${[...pose.eye,...pose.rotation].join(' ')}`,`FOV ${pose.fov}`];
const args = ['-windowed','-ResX=1920','-ResY=1080',`-UserDir=${sandbox}/`,`-abslog=${sandbox}/runtime.log`,
  '-BreziOutput=4k','-ExecCmds='+commands.join(','),'-BreziView='+pose.view,'-BreziCaptureScene',
  '-BreziWarmupFrames=360','-BreziBenchmarkFrames=120','-BreziExitAfterCapture','-BreziWalkAudit'];
const startedAt = new Date().toISOString(), logs = [];
const result = await new Promise((accept,reject) => {
  const child=spawn(launch.executable,args,{cwd:root,stdio:['ignore','pipe','pipe']});
  const timer=setTimeout(()=>{child.kill('SIGTERM');reject(Error('Native capture timed out'));},600000);
  for(const stream of [child.stdout,child.stderr])stream.on('data',c=>logs.push(c));
  child.once('error',reject); child.once('close',(code,signal)=>{clearTimeout(timer);accept({code,signal,pid:child.pid});});
});
const endedAt = new Date().toISOString(), processLog = Buffer.concat(logs);
await writeFile(resolve(evidence,'process.log'),processLog);
const nativeLog = await readFile(resolve(sandbox,'runtime.log')); await writeFile(resolve(evidence,'runtime.log'),nativeLog);
const outcome = {...result,startedAt,endedAt,timedOut:false,logTruncated:false,error:null,executable:launch.executable,args};
const launchValidation = inspectLauncherExecution(launch,outcome,processLog.toString()+'\n'+nativeLog.toString());
assert.equal(result.code,0); assert.equal(result.signal,null); assert.equal(launchValidation.status,'recorded-self-exec-entry-chain');
const diagnostic = resolve(sandbox,'Saved/Diagnostics'), files = (await readdir(diagnostic)).filter(n=>n.endsWith('.json'));
assert.equal(files.length,1);
const runtimeBytes=await readFile(resolve(diagnostic,files[0])), runtime=JSON.parse(runtimeBytes), pngPath=await realpath(runtime.screenshotPath);
assert(pngPath.startsWith(await realpath(diagnostic)+'/')); const png=await readFile(pngPath);
assert.equal(runtime.status,'capture-complete'); assert.equal(runtime.rhi,'Metal'); assert.equal(runtime.screenshotSaved,true);
assert.equal(runtime.renderSettings['r.ScreenPercentage'],100); assert.equal(runtime.renderSettings['r.TSR.History.ScreenPercentage'],200);
assert.deepEqual(runtime.screenshotPixels,[3840,2160]); assert.deepEqual([png.readUInt32BE(16),png.readUInt32BE(20)],[3840,2160]);
assert.equal(runtime.walking.sceneSha256,receipt.sourceManifestSha256);
assert.equal(runtime.walking.worldContractValidated,true); assert.deepEqual(runtime.walking.worldContractErrors,[]);
if (runtime.doubleGlass?.length) {
  assert.equal(runtime.doubleGlass.length,19);
  assert(runtime.doubleGlass.every(p=>p.configured && p.ior===1.52));
  assert(runtime.doubleGlass.every(p=>p.captureBudgetPerFrame===1 && p.warmupCaptureBudget>=1 && p.warmupCaptureBudget<=2
    && p.cameraSettleSeconds>=0.25 && p.captureUsesLumen===false && p.sceneInvalidation==='event-revision'),
    'Rear-interface capture must use the bounded event-driven policy');
  assert(runtime.doubleGlass.every(p=>p.renderTargetWidth<=512));
  if (rearReflection === 'disabled') assert(runtime.doubleGlass.every(p=>!p.enabled && !p.overlayVisible && p.renderTargetBytes===0));
  else if (shot.startsWith('glass-')) {
    assert(runtime.doubleGlass.some(p=>p.enabled && p.ready && p.pendingCaptures===0 && p.captureCount>=p.warmupCaptureBudget),
      'Close glass image has no settled rear-interface capture');
  }
} else assert(!shot.startsWith('glass-'),'Double-glass QA requires the new native capture actor');
const after=await verifyPackagedPayload(receipt.appPath,receipt.bundle); assert.equal(sha(await readFile(packagePath)),sha(packageBytes));
await writeFile(resolve(evidence,'capture.png'),png); await writeFile(resolve(evidence,'runtime.json'),runtimeBytes);
await save(resolve(evidence,'qa.json'),{status:'native-photoreal-capture-validated',shot,generatedAt:endedAt,
  packageReportSha256:sha(packageBytes),process:outcome,launchValidation,payloadBefore:before.status,payloadAfter:after.status,
  screenshotSha256:sha(png),runtimeReportSha256:sha(runtimeBytes),pixels:runtime.screenshotPixels,
  renderSettings:runtime.renderSettings,frameInterval:runtime.frameInterval,requestedCamera:pose,
  requestedRearReflection:rearReflection, doubleGlass:runtime.doubleGlass ?? null,
  twoPointPerspective:pose.rotation[0]===0&&pose.rotation[2]===0,visualQualityReviewed:false,
  scope:'Stationary native Metal 4K at 100% primary resolution; artistic acceptance and real-time frame-rate are separate.'});
console.log(JSON.stringify({status:'native-photoreal-capture-validated',evidence,screenshot:resolve(evidence,'capture.png')},null,2));
