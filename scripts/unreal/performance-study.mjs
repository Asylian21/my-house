// Exploratory GPU-cost study of a packaged Development build. Not acceptance QA:
// performance-qa.mjs owns the validated Shipping matrix and its assertions.
import {spawn} from 'node:child_process';
import {readFile, writeFile, mkdir, readdir, copyFile} from 'node:fs/promises';
import {resolve} from 'node:path';
import {homedir} from 'node:os';
import {createHash, randomUUID} from 'node:crypto';
import assert from 'node:assert/strict';
import {verifyPackagedPayload} from './package-verify.mjs';
import {resolveAppLaunch, requireIdleApp} from './app-launch.mjs';

export function parseGPUProfile(text){
  const rows=[];
  for(const line of String(text).split('\n')){
    const cells=line.split('┃');
    if(cells.length<5)continue;
    const exclusive=cells[1].match(/([\d.]+) ms\s*$/),inclusive=cells[2].match(/([\d.]+) ms\s*$/);
    if(!exclusive||!inclusive)continue;
    const label=cells[3].replace(/\s+$/,''),indent=label.length-label.trimStart().length;
    if(!label.trim())continue;
    rows.push({depth:(indent-1)/3,name:label.trim(),inclusiveMs:Number(inclusive[1]),exclusiveMs:Number(exclusive[1])});
  }
  const frame=Number(String(text).match(/Frame Time\s*:\s*([\d.]+)ms/)?.[1]??NaN);
  const scene=rows.findIndex(r=>r.name==='Scene');
  const passes=[];
  if(scene>=0)for(let i=scene+1;i<rows.length&&rows[i].depth>rows[scene].depth;i++)
    if(rows[i].depth===rows[scene].depth+1&&rows[i].inclusiveMs>0)passes.push(rows[i]);
  passes.sort((a,b)=>b.inclusiveMs-a.inclusiveMs);
  return {frameMs:frame,passes,rows};
}

if(import.meta.url===`file://${process.argv[1]}`){
  const root=resolve(import.meta.dirname,'../..');
  const source=resolve(root,process.env.BREZI_MODEL_OUTPUT??'');
  const output=resolve(root,process.env.BREZI_STUDY_OUTPUT??'output/unreal/performance-study');
  const receiptBytes=await readFile(resolve(source,'model-package.json')),receipt=JSON.parse(receiptBytes);
  assert.equal(receipt.gameConfiguration,'Development','GPU attribution requires a Development package');
  await verifyPackagedPayload(receipt.appPath,receipt.bundle);
  const launch=await resolveAppLaunch(receipt.appPath,receipt.bundle);
  const list=name=>process.env[name]?.split(',').filter(Boolean);
  const scenes=list('BREZI_STUDY_SCENES')??['interior-day'];
  const profiles=list('BREZI_STUDY_PROFILES')??['performance','balanced','native','cinematic'];
  const outputs=list('BREZI_STUDY_OUTPUTS')??['4k'];
  // Semicolon-separated variants; each variant is a comma-separated console command list.
  // An `ini:name value` entry goes to the sandbox Engine.ini instead: any command-line
  // mention of r.ScreenPercentage* locks the named profile as a raw override.
  const variants=(process.env.BREZI_STUDY_VARIANTS??'').split(';').map(v=>v.trim());
  const [resX,resY]=(process.env.BREZI_STUDY_WINDOW??'1920x1080').split('x').map(Number);
  const profileGPU=process.env.BREZI_STUDY_PROFILE_GPU!=='0';
  const session=resolve(output,`${process.env.BREZI_STUDY_LABEL??'study'}-${Date.now()}`);await mkdir(session,{recursive:true});
  const results=[];
  for(const variant of variants)for(const profile of profiles)for(const mode of outputs)for(const scene of scenes){
    const [,view,time]=/^(.+)-(day|night)$/.exec(scene);assert(receipt.viewpoints.includes(view),'Unknown viewpoint '+view);
    const id=`${scene}-${mode}-${profile}-${randomUUID().slice(0,8)}`,evidence=resolve(session,id);await mkdir(evidence);
    const sandbox=resolve(homedir(),'Library/Containers/local.brezi.twin/Data/Library/Application Support/BreziTwin/QA',id);await mkdir(sandbox,{recursive:true});
    const entries=variant?variant.split(',').map(s=>s.trim()).filter(Boolean):[];
    const ini=entries.filter(s=>s.startsWith('ini:')).map(s=>s.slice(4).trim().replace(/\s+/,'='));
    if(ini.length){
      await mkdir(resolve(sandbox,'Saved/Config/Mac'),{recursive:true});
      await writeFile(resolve(sandbox,'Saved/Config/Mac/Engine.ini'),['[ConsoleVariables]',...ini,''].join('\n'));
    }
    const cmds=['r.VSync 0','t.MaxFPS 0',...entries.filter(s=>!s.startsWith('ini:'))];
    const args=['-windowed',`-ResX=${resX}`,`-ResY=${resY}`,`-UserDir=${sandbox}/`,`-abslog=${sandbox}/runtime.log`,
      `-BreziOutput=${mode}`,`-BreziView=${view}`,`-BreziRenderProfile=${profile}`,'-BreziCaptureScene','-BreziExitAfterCapture',
      '-BreziWarmupFrames=240','-BreziBenchmarkFrames=240','-BreziBenchmarkUncapped',`-ExecCmds=${cmds.join(',')}`,
      ...(time==='night'?['-BreziNight']:[]),...(profileGPU?['-BreziProfileGPU']:[])];
    const row={id,profile,mode,scene,variant,args,startedAt:new Date().toISOString()};
    console.log(JSON.stringify({event:'start',id,variant}));
    try{
      await requireIdleApp();
      const outcome=await new Promise((accept,reject)=>{
        const child=spawn(launch.executable,args,{cwd:root,stdio:'ignore'});
        const timer=setTimeout(()=>child.kill('SIGTERM'),600000);
        child.once('error',e=>{clearTimeout(timer);reject(e);});
        child.once('close',(code,signal)=>{clearTimeout(timer);accept({code,signal,pid:child.pid});});
      });
      const diagnostics=resolve(sandbox,'Saved/Diagnostics'),files=await readdir(diagnostics);
      const report=files.find(f=>f.endsWith('.json')),r=JSON.parse(await readFile(resolve(diagnostics,report)));
      await copyFile(resolve(diagnostics,report),resolve(evidence,'runtime.json'));
      if(r.screenshotPath)await copyFile(r.screenshotPath,resolve(evidence,'capture.png')).catch(()=>{});
      const log=files.find(f=>f.endsWith('-gpu-profile.log'));
      const gpuProfile=log?parseGPUProfile(await readFile(resolve(diagnostics,log),'utf8')):null;
      if(log)await copyFile(resolve(diagnostics,log),resolve(evidence,'gpu-profile.log'));
      Object.assign(row,{status:r.status,outcome,pixels:r.screenshotPixels,
        foreground:r.focusDuringBenchmark,frameMeanMs:r.frameInterval?.meanMs,frameP95Ms:r.frameInterval?.p95Ms,
        gpuMeanMs:r.gpuFrameFromRHITimer?.meanMs,settings:r.renderSettings,
        viewRect:r.presentation?.sceneViewportPixels,
        profiledFrameMs:gpuProfile?.frameMs,topPasses:gpuProfile?.passes.slice(0,18).map(p=>[p.name,p.inclusiveMs])});
    }catch(e){row.status='failed';row.error=String(e.stack??e);}
    row.endedAt=new Date().toISOString();results.push(row);
    await writeFile(resolve(evidence,'study.json'),JSON.stringify(row,null,2)+'\n');
    await writeFile(resolve(session,'summary.json'),JSON.stringify({source,packageReportSha256:createHash('sha256').update(receiptBytes).digest('hex'),results},null,2)+'\n');
    console.log(JSON.stringify({event:'end',id,status:row.status,frameMeanMs:row.frameMeanMs,gpuMeanMs:row.gpuMeanMs,profiledFrameMs:row.profiledFrameMs}));
  }
  console.log(JSON.stringify({status:'study-complete',session}));
}
