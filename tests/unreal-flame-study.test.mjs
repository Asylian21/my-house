import test from 'node:test';
import assert from 'node:assert/strict';
import {createHash} from 'node:crypto';
import {crc32,deflateSync} from 'node:zlib';
import {SCALES,TARGET_PRE_EXPOSURE,FLAME_SHADER_SHA256,sourcePose,sourceRoi,inspectFlamePng,makeStudyContract,inspectFlameRun,compareFlameRuns,compareLightingStates,compareScaleOneStates} from '../scripts/unreal/flame-study.mjs';
const sha=(b,a='sha256')=>createHash(a).update(b).digest('hex'),digest='a'.repeat(64);
const mesh='/Game/Brezi/VisualDetails/Stove/V_test/Meshes/stove-visuals/StaticMeshes/STOVEV_FLAMES.STOVEV_FLAMES',material='/Game/Brezi/VisualDetails/Stove/V_test/Materials/M_Stove_flames.M_Stove_flames';
const sun={dayLux:80000,dayRotationDegrees:[-28.258384533137132,30.870904963148355,0]};
const view={id:'interior',eyeCm:[1110,-440,165],targetCm:[630,-300,165],horizontalFovDegrees:76.09408506365219};
function authoring(){return{imported:{status:'import-validated',sourceManifestSha256:digest,stoveVisuals:{status:'stove-visuals-saved-reloaded-validated',sourceManifestSha256:digest,sourceObjSha256:digest,activeReloadEvidence:[{id:'STOVEV_FLAMES',mesh,material,triangles:12,flameMaterial:{shaderCodeSha256:FLAME_SHADER_SHA256,graphNodeCount:10,emissionAndOpacityShapeUnchanged:true,worldPositionOffsetConnected:false,defaultScalarParameters:{BreziFlameEmissionScale:1,BreziFlameStudyTimeSeconds:-1}}}]},optics:{instances:[{sourceSlot:'MAT_0036',asset:'/Game/Brezi/OpticsGenerated/MI_Glass.MI_Glass'}]}},stoveGeometry:{status:'stove-visual-geometry-validated',sourceManifestSha256:digest,sourceObjSha256:digest,objects:[{id:'STOVEV_FLAMES',triangles:12,nativeBoundsCm:{min:[673.7999878,-380.1999952,52],max:[685.7999878,-354.9999952,82.5]}}]},viewpoints:{coordinateSystem:'unreal-centimeters',views:[view],sun},packageSha256:digest,importSha256:digest,viewpointsSha256:digest,geometrySha256:digest,walkingSha256:digest,walking:{status:'source-walking-contract-exported',coordinateSystem:'unreal-centimeters',eyeHeightCm:165,provenance:{sceneSha256:digest,sourceObjSha256:digest},walkSurfaces:[{objectId:'DOM_00446',dynamic:false,kind:'interior',supportOffsetCm:0,nativeBoundsCm:{min:[634,-874,-4],max:[1235,-74,0]}}]}};}
const contract=makeStudyContract(authoring()),contractBytes=Buffer.from(JSON.stringify(contract));
function fixture(scale=1){
 const pose=sourcePose(contract),r=sun.dayRotationDegrees.map(v=>v*Math.PI/180),actualSun={count:1,lux:80000,visible:true,direction:[Math.cos(r[0])*Math.cos(r[1]),Math.cos(r[0])*Math.sin(r[1]),Math.sin(r[0])]};
 const flame={mesh,sourceMaterial:material,triangles:12,materialSlots:1,blendMode:3,unlit:true,twoSided:true,collisionProfile:'NoCollision',collisionMode:0,visible:true,hiddenInGame:false,actorHidden:false,disableDepthTest:false,boundsMinCm:contract.boundsMinCm,boundsMaxCm:contract.boundsMaxCm,refractionMethod:0,translucencyPass:0,translucencySortPriority:0,translucencySortDistanceOffset:0};
 const glass={mesh:contract.glassMesh,sourceMaterial:contract.glassMaterial,triangles:192,materialSlots:1,visible:true,hiddenInGame:false,actorHidden:false,disableDepthTest:false,refractionMethod:3,translucencyPass:0,translucencySortPriority:0,translucencySortDistanceOffset:0};
 const frame={index:0,file:'frame-000.png',pngSaved:true,emissionScale:scale,studyTimeSeconds:2,transientMaterialPointerBound:true,requestFrameCounter:260,captureFrameCounter:260,gameViewFrameCounter:260,renderFrameCounter:260,gameViewFamilyFrameNumber:260,renderFamilyFrameNumber:260,gameMainViewCount:1,renderMainViewCount:1,sceneIdentityPaired:true,...pose,viewFovDegrees:pose.horizontalFovDegrees,projectionJitter:[0,0],cameraCut:false,renderTargetPixels:[3840,2160],unscaledViewPixels:[3840,2160],screenshotPixels:[3840,2160],antiAliasingMethod:5,primaryScreenPercentageMethod:0,showFlagPostProcessing:true,showFlagAntiAliasing:true,showFlagTemporalAA:false,allowTemporalJitter:false,manualExposure:true,physicalCameraExposure:false,exposureBiasCurvePresent:false,localExposure:false,eyeAdaptationShowFlag:true,sceneColorTint:[1,1,1],manualExposureBias:Math.log2(TARGET_PRE_EXPOSURE),linearPreExposure:TARGET_PRE_EXPOSURE,worldDeltaSeconds:1/30,requestDeltaSeconds:1/30,appDeltaSeconds:1/30,worldSeconds:8,requestWorldSeconds:8,realSeconds:9,requestRealSeconds:9,requestWallSeconds:100,captureWallSeconds:100.1,pngWriteCompleteWallSeconds:100.2,flameComponent:structuredClone(flame),glassComponent:structuredClone(glass),sun:actualSun};
 const runtime={schemaVersion:1,status:'flame-study-captured',emissionScale:scale,studyTimeSeconds:2,targetPreExposure:TARGET_PRE_EXPOSURE,contractSha1:sha(contractBytes,'sha1'),sceneSha256:digest,sourceObjSha256:digest,simulationHz:30,warmupFrames:240,warmupGameViews:240,warmupRenderViews:240,warmupRenderFramesConsecutive:true,fixedClockRestored:true,originalMaterialPointerRestored:true,originalComponentStatesRestored:true,viewExtensionStoppedAndFlushed:true,qualitySettingsUnchanged:true,parentScalarDefaultsRead:true,parentDefaultEmissionScale:1,parentDefaultStudyTimeSeconds:-1,clock:{priorUseFixedFrameRate:false,currentUseFixedFrameRate:false,priorUseFixedTimeStep:false,currentUseFixedTimeStep:false,priorFixedFrameRate:60,currentFixedFrameRate:60,priorFixedDeltaSeconds:.01,currentFixedDeltaSeconds:.01},worldTimeArtificiallyFrozen:false,fpsMeasured:false,uiIncluded:false,highResolutionScreenshotUsed:false,physicalBrightnessCalibrated:false,lightingState:'day',cameraModeAndPriorViewRestored:true,nativeProcessId:123,requestedAA:5,qualitySettings:{'r.ScreenPercentage':'100','r.SecondaryScreenPercentage.GameViewport':'100','r.DynamicRes.OperationMode':'0','r.EyeAdaptation.PreExposureOverride':'0','r.AntiAliasingMethod':'5','r.EyeAdaptation.LensAttenuation':'.78','r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange':'1'},initialFlameComponent:flame,initialGlassComponent:glass,finalFlameComponent:structuredClone(flame),finalGlassComponent:structuredClone(glass),initialSun:actualSun,frames:[frame]};
 const standing={cameraMode:'walking',contractLoaded:true,worldContractValidated:true,sceneSha256:digest,sourceObjSha256:digest,expectedEyeHeightCm:165,groundedEyeSamples:241,unmeasuredOrAirborneEyeSamples:0,entryAttempts:1,successfulEntries:1,currentSupportObjectId:'DOM_00446',entrySupportObjectId:'DOM_00446',currentCameraEyeCm:contract.eyeCm,lastMeasuredEyeHeightCm:165,minMeasuredEyeHeightCm:165,maxMeasuredEyeHeightCm:165,maxEyeHeightErrorCm:0,worldContractErrors:[]};
 Object.assign(frame,{warmupGameViews:240,warmupRenderViews:240,warmupConsecutive:true,standing});
 const baseline=structuredClone(frame);Object.assign(baseline,{captureKind:'production-baseline',emissionScale:1,studyTimeSeconds:-1,transientMaterialPointerBound:false,manualExposure:false});
 frame.index=1;frame.file='frame-001.png';frame.captureKind='controlled-study';for(const key of ['requestFrameCounter','captureFrameCounter','gameViewFrameCounter','renderFrameCounter','gameViewFamilyFrameNumber','renderFamilyFrameNumber'])frame[key]+=241;
 runtime.frames=[baseline,frame];
 return{runtime,contract,contractBytes,scale,baselineImage:{pixels:[3840,2160],decodedPixelsVerified:true,rgbUnfiltered:true,roi:contract.roi,sha256:digest},image:{pixels:[3840,2160],decodedPixelsVerified:true,rgbUnfiltered:true,roi:contract.roi,sha256:digest},outcome:{code:0,signal:null,pid:123,renderersAfter:[],timedOut:false,logTruncated:false},log:'BreziStartupEntry: pid=123 phase=self-exec forcedFlags=-LLM,-DetectHitchesWithLLM\nBreziStartupEntry: pid=123 phase=enter-engine forcedFlags=-LLM,-DetectHitchesWithLLM\nEngine is initialized. Leaving FEngineLoop::Init()\nLogExit: Exiting',launch:{entryKind:'same-binary-self-exec',forcedFlags:['-LLM','-DetectHitchesWithLLM']},ax:{installedAtObjectiveCLoad:true,installationError:'none',engineGuard:'5.8.2-56702186-non-licensee',engineDeallocUnchanged:true,phase:'queues-drained-before-slate-shutdown',shutdownStarted:true,outstanding:0,applied:20,stressRequested:false},payloadBefore:{status:'packaged-payload-unchanged',digest},payloadAfter:{status:'packaged-payload-unchanged',digest}};
}
test('Synthetic complete paired-frame control is accepted without production claims',()=>{const r=inspectFlameRun(fixture());assert.equal(r.status,'controlled-flame-capture-validated',r.errors.join('; '));assert.equal(r.productionPromotionAllowed,false);assert.equal(r.physicalBrightnessCalibrated,false);});
const adversaries={
 'older five-node authoring':x=>{x.runtime.parentScalarDefaultsRead=false;},
 'latest frame fallback':x=>{x.runtime.frames[1].renderFrameCounter++;},
 'different world same frame':x=>{x.runtime.frames[1].sceneIdentityPaired=false;},
 'automatic exposure':x=>{x.runtime.frames[1].manualExposure=false;},
 'preexposure-only override':x=>{x.runtime.qualitySettings['r.EyeAdaptation.PreExposureOverride']='.001';},
 'wrong shader preexposure':x=>{x.runtime.frames[1].linearPreExposure*=2;},
 'local exposure active':x=>{x.runtime.frames[1].localExposure=true;},
 'wrong phase':x=>{x.runtime.frames[1].studyTimeSeconds=2.1;},
 'wrong scalar readback':x=>{x.runtime.frames[1].emissionScale=4;},
 'foreign flame asset':x=>{x.runtime.initialFlameComponent.mesh+='_foreign';},
 'visible old proxy triangles':x=>{x.runtime.initialFlameComponent.triangles=96;},
 'glass depth disabled':x=>{x.runtime.frames[1].glassComponent.disableDepthTest=true;},
 'glass sorting changed':x=>{x.runtime.frames[1].glassComponent.translucencySortPriority=1;},
 'original pointer not restored':x=>{x.runtime.originalMaterialPointerRestored=false;},
 'clock getter differs':x=>{x.runtime.clock.currentUseFixedFrameRate=true;},
 'launcher exit only':x=>{x.outcome.pid=124;},
 'child still alive':x=>{x.outcome.renderersAfter=[{name:'BreziTwin',pid:123}];},
 'capture then crash':x=>{x.outcome.code=null;x.outcome.signal='SIGSEGV';},
 'shader ensure despite exit zero':x=>{x.log+='\nHandled ensure: shader View unbound';},
 'undrained AX':x=>{x.ax.outstanding=1;},
 'package payload changed':x=>{x.payloadAfter.digest='b'.repeat(64);},
 'source scene changed':x=>{x.runtime.sceneSha256='b'.repeat(64);},
 'metadata-only PNG':x=>{x.image.rgbUnfiltered=false;},
 'wrong 4k camera':x=>{x.runtime.frames[1].eyeCm=[1111,-440,165];},
 'upscaled viewport':x=>{x.runtime.frames[1].unscaledViewPixels=[1920,1080];},
 'warmup missing RT frame':x=>{x.runtime.warmupRenderViews=239;},
};
for(const [name,mutate]of Object.entries(adversaries))test(`Reject ${name}`,()=>{const x=fixture();mutate(x);assert.equal(inspectFlameRun(x).status,'failed');});
test('Five-node authoring cannot produce launch contract',()=>{const x=authoring();x.imported.stoveVisuals.activeReloadEvidence[0].flameMaterial.graphNodeCount=5;assert.throws(()=>makeStudyContract(x),/ten-node/);});
test('Foreign shader or canonical mismatch cannot produce launch contract',()=>{const x=authoring();x.imported.stoveVisuals.activeReloadEvidence[0].flameMaterial.shaderCodeSha256=digest;assert.throws(()=>makeStudyContract(x),/Unregistered exact shader recipe/);const y=authoring();y.stoveGeometry.sourceManifestSha256='b'.repeat(64);assert.throws(()=>makeStudyContract(y),/provenance/);});
function run(scale){const x=fixture(scale),report=inspectFlameRun(x);return{report:{...report,image:x.image,contractSha256:sha(contractBytes),packageReceiptSha256:digest,executableSha256:digest,launch:x.launch,inputHashes:{a:digest},nativeHashes:{a:digest},helperHashes:{a:digest}},runtime:x.runtime,contract};}
test('Four matching scales compare; night remains a promotion prerequisite',()=>{const r=compareFlameRuns(SCALES.map(run));assert.equal(r.status,'four-controlled-flame-captures-comparable',r.errors.join('; '));assert.equal(r.selectedProductionScale,null);assert.equal(r.productionPromotionAllowed,false);});
test('Cross-scale jitter and package mismatch are rejected',()=>{for(const key of ['projectionJitter','packageReceiptSha256']){const runs=SCALES.map(run);if(key==='projectionJitter')runs[1].runtime.frames[1][key]=[.001,0];else runs[1].report[key]='b'.repeat(64);assert.equal(compareFlameRuns(runs).status,'failed');}});
test('Bounds projection is finite and entirely inside source native image',()=>{assert.deepEqual(sourceRoi(contract),contract.roi);assert.equal(contract.roi.length,4);assert.throws(()=>sourceRoi({...contract,eyeCm:[680,-370,60]}));});
function png(){
 const w=3840,h=2160,channels=4,stride=w*channels,raw=Buffer.alloc((stride+1)*h),color=[8,4,2,255];
 const paeth=(a,b,c)=>{const p=a+b-c,pa=Math.abs(p-a),pb=Math.abs(p-b),pc=Math.abs(p-c);return pa<=pb&&pa<=pc?a:pb<=pc?b:c;};
 for(let y=0;y<h;y++){const f=y%5,offset=y*(stride+1);raw[offset]=f;for(let x=0;x<stride;x++){const value=color[x%4],a=x>=4?value:0,b=y?value:0,c=y&&x>=4?value:0;raw[offset+x+1]=(value-[0,a,b,Math.floor((a+b)/2),paeth(a,b,c)][f])&255;}}
 const chunk=(name,p)=>{const b=Buffer.alloc(p.length+12);b.writeUInt32BE(p.length);b.write(name,4);p.copy(b,8);b.writeUInt32BE(crc32(b.subarray(4,-4)),b.length-4);return b;};
 const ihdr=Buffer.alloc(13);ihdr.writeUInt32BE(w);ihdr.writeUInt32BE(h,4);ihdr[8]=8;ihdr[9]=6;
 return Buffer.concat([Buffer.from([137,80,78,71,13,10,26,10]),chunk('IHDR',ihdr),chunk('IDAT',deflateSync(raw)),chunk('IEND',Buffer.alloc(0))]);
}
test('PNG pixels are actually unfiltered for all five filters; corrupt payload is rejected',()=>{const bytes=png(),r=inspectFlamePng(bytes,contract.roi);assert.deepEqual(r.pixels,[3840,2160]);assert.deepEqual(r.meanRgb,[8,4,2]);assert.deepEqual(r.minRgb,[8,4,2]);assert.deepEqual(r.maxRgb,[8,4,2]);assert.equal(r.saturatedPixelCount,0);const bad=Buffer.from(bytes);bad[100]^=1;assert.throws(()=>inspectFlamePng(bad,contract.roi),/CRC/);});

function nightFixture(scale=1){const x=fixture(scale),c=makeStudyContract({...authoring(),lightingState:'night'});x.contract=c;x.contractBytes=Buffer.from(JSON.stringify(c));x.runtime.contractSha1=sha(x.contractBytes,'sha1');x.runtime.lightingState='night';x.runtime.targetPreExposure=16;
 const p=-25*Math.PI/180,y=(sun.dayRotationDegrees[1]+150)*Math.PI/180,moon={count:1,lux:.15,visible:true,direction:[Math.cos(p)*Math.cos(y),Math.cos(p)*Math.sin(y),Math.sin(p)]};x.runtime.initialSun=moon;
 for(const frame of x.runtime.frames){frame.sun=moon;frame.linearPreExposure=16;}x.runtime.frames[1].manualExposureBias=4;return x;}
test('Night fixed exposure is independently controlled and accepted',()=>{const x=nightFixture(),r=inspectFlameRun(x);assert.equal(r.status,'controlled-flame-capture-validated',r.errors.join('; '));assert.equal(x.contract.targetPreExposure,16);});
for(const [name,mutate]of Object.entries({
 'production baseline was already manual':x=>{x.runtime.frames[0].manualExposure=true;},
 'production baseline time override active':x=>{x.runtime.frames[0].studyTimeSeconds=2;},
 'baseline PNG missing':x=>{x.baselineImage=null;},
 'unsupported eye':x=>{x.runtime.frames[1].standing.unmeasuredOrAirborneEyeSamples=1;},
 'foreign support collider':x=>{x.runtime.frames[1].standing.currentSupportObjectId='COLL_00000';},
 'orbit presented as standing':x=>{x.runtime.frames[0].standing.cameraMode='orbit';},
 'source eye height differs':x=>{x.runtime.frames[1].standing.lastMeasuredEyeHeightCm=166;},
 'controlled screenshot missed warmup':x=>{x.runtime.frames[1].requestFrameCounter++;},
 'night uses daytime exposure':x=>{x.runtime.frames[1].linearPreExposure=TARGET_PRE_EXPOSURE;},
}))test(`Reject state-specific ${name}`,()=>{const x=nightFixture();mutate(x);assert.equal(inspectFlameRun(x).status,'failed');});
function nightRun(scale){const x=nightFixture(scale),report=inspectFlameRun(x);return{report:{...report,image:x.image,contractSha256:sha(x.contractBytes),packageReceiptSha256:digest,executableSha256:digest,launch:x.launch,inputHashes:{a:digest},nativeHashes:{a:digest},helperHashes:{a:digest}},runtime:x.runtime,contract:x.contract};}
test('Day/night same package camera comparison does not select a default',()=>{const r=compareLightingStates(SCALES.map(run),SCALES.map(nightRun));assert.equal(r.status,'day-night-controlled-captures-ready-for-visual-review',r.errors.join('; '));assert.equal(r.productionPromotionAllowed,false);assert.equal(r.selectedProductionScale,null);});
test('Day/night changed package or camera is rejected',()=>{const a=SCALES.map(run),b=SCALES.map(nightRun);for(const r of b)r.report.executableSha256='b'.repeat(64);assert.equal(compareLightingStates(a,b).status,'failed');const c=SCALES.map(nightRun);for(const r of c)r.contract={...r.contract,eyeCm:[1111,-440,165]};assert.equal(compareLightingStates(a,c).status,'failed');});
test('Scale-one day/night capture keeps visual and performance acceptance separate',()=>{const r=compareScaleOneStates([run(1),nightRun(1)]);assert.equal(r.status,'scale-one-day-night-stills-ready-for-visual-review',r.errors.join('; '));assert.equal(r.productionPromotionAllowed,false);assert.equal(r.selectedProductionScale,null);assert.equal(r.motionVerified,false);assert.equal(r.fpsMeasured,false);});
for(const [name,mutate] of Object.entries({
 'failed process':r=>{r[0].report.status='failed';},
 'incomplete pair':r=>{r.pop();},
 'different scale':r=>{r[0].report.scale=4;},
 'changed package':r=>{r[1].report.packageReceiptSha256='b'.repeat(64);},
 'changed source shader':r=>{r[1].contract={...r[1].contract,flameShaderSha256:'b'.repeat(64)};},
 'changed actual camera':r=>{r[1].runtime.frames[1].eyeCm[0]++;},
 'missing cameras':r=>{r.forEach(x=>delete x.runtime.frames[1].eyeCm);},
 'missing controlled frame':r=>{r[0].runtime.frames.pop();},
 'reversed lighting states':r=>{r.reverse();},
}))test(`Scale-one rejects ${name}`,()=>{const r=[run(1),nightRun(1)].map(x=>structuredClone(x));mutate(r);assert.equal(compareScaleOneStates(r).status,'failed');});
test('A fourth capture crash returns a failure result without dereferencing absent frames',()=>{const runs=SCALES.map(run);runs[3]={report:{status:'failed',errors:['SIGSEGV'],scale:64},runtime:null,contract};assert.equal(compareFlameRuns(runs).status,'failed');assert.equal(compareLightingStates(runs,[]).status,'failed');});
test('Missing or altered app entry marker is rejected independently of native PID',()=>{for(const replacement of ['', 'BreziStartupEntry: pid=456 phase=enter-engine forcedFlags=-LLM,-DetectHitchesWithLLM']){const x=fixture();x.log=x.log.replace(/^BreziStartupEntry:.*phase=enter-engine.*$/m,replacement);assert.equal(inspectFlameRun(x).status,'failed');}});
test('Pitched camera projects with a unit horizontal right axis',()=>{const c={eyeCm:[0,0,0],targetCm:[1,0,1],horizontalFovDegrees:90,boundsMinCm:[10,2,10],boundsMaxCm:[10,2,10]};
 const projectedX=1920+1920*2/(20/Math.sqrt(2));assert.deepEqual(sourceRoi(c),[Math.floor(projectedX)-4,1076,Math.ceil(projectedX)+4,1084]);});

// New source-recipe and opt-in shape guards. Existing 58 tests above stay intact.
import {CANDIDATE_SHA,requireRecipeMetadata,parseShapeOptions,shapeFrameCount,shapePhase,makeShapeContract,inspectShapeRun} from '../scripts/unreal/flame-study.mjs';
const candidateProof=()=>({shaderCodeSha256:CANDIDATE_SHA,emissionAndOpacityMatchPinnedShader:true,alphaShapeChangedFromPreviousRevision:true,previousShaderSha256:FLAME_SHADER_SHA256});
test('Candidate exact current shader proof explicitly records changed alpha and preserved scalar defaults',()=>{
 const x=authoring(),m=x.imported.stoveVisuals.activeReloadEvidence[0].flameMaterial;
 delete m.emissionAndOpacityShapeUnchanged;Object.assign(m,candidateProof());const c=makeStudyContract(x);
 assert.equal(c.flameShaderSha256,CANDIDATE_SHA);assert.equal(c.emissionAndOpacityMatchPinnedShader,true);assert.equal(c.alphaShapeChangedFromPreviousRevision,true);
 assert.equal(c.previousShaderSha256,FLAME_SHADER_SHA256);assert.deepEqual(c.defaultScalarParameters,{BreziFlameEmissionScale:1,BreziFlameStudyTimeSeconds:-1});
});
for(const [name,mutate]of Object.entries({
 'unregistered recipe':r=>r.shaderCodeSha256='f'.repeat(64),
 'missing native getter proof':r=>delete r.emissionAndOpacityMatchPinnedShader,
 'false native getter proof':r=>r.emissionAndOpacityMatchPinnedShader=false,
 'alpha falsely unchanged':r=>r.alphaShapeChangedFromPreviousRevision=false,
 'previous recipe missing':r=>delete r.previousShaderSha256,
 'previous recipe mismatched':r=>r.previousShaderSha256=CANDIDATE_SHA,
 'ambiguous old unchanged field':r=>r.emissionAndOpacityShapeUnchanged=true,
}))test(`Recipe rejects ${name}`,()=>{const r=candidateProof();mutate(r);assert.throws(()=>requireRecipeMetadata(r,{allowHistoricalBaseline:true}));});
test('Candidate cannot fall back to historical legacy boolean',()=>assert.throws(()=>requireRecipeMetadata({shaderCodeSha256:CANDIDATE_SHA,emissionAndOpacityShapeUnchanged:true},{allowHistoricalBaseline:true})));
test('Current baseline proof requires explicit null predecessor; partial fields cannot use legacy fallback',()=>{
 const b={shaderCodeSha256:FLAME_SHADER_SHA256,emissionAndOpacityMatchPinnedShader:true,alphaShapeChangedFromPreviousRevision:false,previousShaderSha256:null};
 assert.equal(requireRecipeMetadata(b).historicalCompatibilityUsed,false);delete b.previousShaderSha256;b.emissionAndOpacityShapeUnchanged=true;
 assert.throws(()=>requireRecipeMetadata(b,{allowHistoricalBaseline:true}));
});
for(const args of [['--pose=interior','--state=day','--mode=stills','--scale=4'],['--pose=interior','--state=night','--mode=performance'],
 ['--pose=street','--state=day','--mode=stills'],['--pose=oblique','--state=day','--mode=sequence','--history-100'],
 ['--pose=interior','--pose=oblique','--mode=stills'],['--pose=oblique','--state=day']])
 test(`Reject invalid shape arguments ${JSON.stringify(args)}`,()=>assert.throws(()=>parseShapeOptions(args)));
function shapeFixture(mode='sequence',pose='interior') {
 const a=authoring();Object.assign(a.stoveGeometry,{stoveAxisSourceMm:[6653,3675],sourceRecords:{DOM_00522:{boundsMm:{min:[6398,3420,30],max:[6908,3930,1550]}}}});
 const eye=[665.3+300*Math.cos(Math.PI/6),-367.5-150,165],target=[665.3,-367.5,165];
 const poseProof={schemaVersion:1,status:'cpu-source-reachable-candidate-native-query-pending',sourceHashes:{
  'output/unreal/geometry/scene.json':digest,'output/unreal/geometry/dom-mm.obj':digest,'output/unreal/geometry/walking.json':digest,
  'output/unreal/stove-visuals/stove-visuals.json':digest},nativeEntryValidated:false,nativeTraversalValidated:false,nativeVisibilityValidated:false,
  blockedSourceObjectIds:[],diagnosticRadiusCm:300,diagnosticAzimuthDegrees:-30,eyeCm:eye,targetCm:target,horizontalFovDegrees:view.horizontalFovDegrees,
  sourceInterior:view,supportObjectIds:['DOM_00446']};
 const shape={pose,mode,lightingState:'day'},base=makeStudyContract(a),c=makeShapeContract(base,{shape,poseProof,stoveGeometry:a.stoveGeometry,walking:a.walking});
 const x=fixture(1);x.contract=c;x.contractBytes=Buffer.from(JSON.stringify(c));
 Object.assign(x.runtime,{schemaVersion:2,status:'flame-shape-captured',contractSha1:sha(x.contractBytes,'sha1'),shapeMode:mode,poseId:pose,
  shapePhaseSource:'indexed-MID-scalar-at-30-simulation-Hz',nativeStoveAxisVerified:true,sourceStoveAxisNativeCm:c.sourceStoveAxisCm,
  realTimePlaybackVerified:false,expectedCaptureFrames:shapeFrameCount(mode)});
 for(const f of x.runtime.frames){Object.assign(f,sourcePose(c));f.standing.currentCameraEyeCm=c.eyeCm;}
 x.image.roi=c.roi;x.baselineImage.roi=c.roi;x.images=[structuredClone(x.baselineImage),structuredClone(x.image)];
 const f=x.runtime.frames[1];
 for(let i=2;i<shapeFrameCount(mode);i++){
  const row=structuredClone(f),n=i-1;Object.assign(row,{index:i,file:`frame-${String(i).padStart(3,'0')}.png`,captureKind:'controlled-advancing-time',studyTimeSeconds:shapePhase(i)});
  for(const k of ['requestFrameCounter','captureFrameCounter','gameViewFrameCounter','renderFrameCounter','gameViewFamilyFrameNumber','renderFamilyFrameNumber'])row[k]+=n;
  for(const k of ['worldSeconds','requestWorldSeconds','realSeconds','requestRealSeconds'])row[k]+=n/30;
  for(const k of ['requestWallSeconds','captureWallSeconds','pngWriteCompleteWallSeconds'])row[k]+=n*.25;
  x.runtime.frames.push(row);x.images.push(structuredClone(x.image));
 }
 return {x,authoring:a,shape,poseProof,base};
}
for(const mode of ['stills','sequence'])for(const pose of ['interior','oblique'])test(`Synthetic exact ${pose}/${mode} captures accepted without performance or promotion`,()=>{
 const {x}=shapeFixture(mode,pose),r=inspectShapeRun(x);assert.equal(r.status,'flame-shape-capture-validated',r.errors.join('; '));
 assert.equal(x.runtime.frames.length,mode==='sequence'?62:2);assert.equal(r.productionPromotionAllowed,false);assert.equal(x.runtime.realTimePlaybackVerified,false);
});
for(const [name,mutate]of Object.entries({
 'late render family':x=>x.runtime.frames[20].renderFrameCounter++,
 'missing frame':x=>x.runtime.frames.splice(20,1),
 'null frame':x=>x.runtime.frames[20]=null,
 'first PNG inventory disagrees':x=>x.images[0].sha256='f'.repeat(64),
 'extra frame':x=>x.runtime.frames.push(structuredClone(x.runtime.frames.at(-1))),
 'missing PNG':x=>x.images.splice(20,1),
 'wrong phase':x=>x.runtime.frames[20].studyTimeSeconds+=.1,
 'frozen phase':x=>x.runtime.frames[20].studyTimeSeconds=2,
 'scale drift':x=>x.runtime.frames[20].emissionScale=4,
 'non-native target':x=>x.runtime.frames[20].renderTargetPixels=[1920,1080],
 'camera drift':x=>x.runtime.frames[20].eyeCm[0]++,
 'missed source support':x=>x.runtime.frames[20].standing.currentSupportObjectId='COLL_foreign',
 'airborne eye':x=>x.runtime.frames[20].standing.unmeasuredOrAirborneEyeSamples++,
 'wall-clock-derived phase cadence':x=>x.runtime.frames[20].worldDeltaSeconds=.25,
 'unfrozen first controlled still':x=>x.runtime.frames[1].studyTimeSeconds=2.1,
 'manual exposure lost':x=>x.runtime.frames[20].manualExposure=false,
 'new AA choice':x=>x.runtime.frames[20].antiAliasingMethod=1,
 'pre-exposure drift':x=>x.runtime.frames[20].linearPreExposure*=2,
 'glass changed':x=>x.runtime.frames[20].glassComponent.refractionMethod=0,
 'readback order inverted':x=>x.runtime.frames[20].requestWallSeconds=0,
 'capture then crash':x=>{x.outcome.code=null;x.outcome.signal='SIGSEGV';},
 'restoration failed':x=>x.runtime.originalMaterialPointerRestored=false,
 'stove axis not proven':x=>x.runtime.nativeStoveAxisVerified=false,
 'axis differed':x=>x.runtime.sourceStoveAxisNativeCm[0]++,
 'invented real-time claim':x=>x.runtime.realTimePlaybackVerified=true,
 'ordinary driver fabricated shape result':x=>x.runtime.schemaVersion=1,
}))test(`Sequence rejects ${name}`,()=>{const {x}=shapeFixture();mutate(x);assert.equal(inspectShapeRun(x).status,'failed');});
for(const [name,mutate]of Object.entries({
 'missing source proof':s=>s.poseProof=null,
 'stale OBJ':s=>s.poseProof.sourceHashes['output/unreal/geometry/dom-mm.obj']='f'.repeat(64),
 'changed radius':s=>s.poseProof.diagnosticRadiusCm=200,
 'blocked source approach':s=>s.poseProof.blockedSourceObjectIds=['DOM_00486'],
 'native reachability falsely claimed':s=>s.poseProof.nativeEntryValidated=true,
 'eye moved':s=>s.poseProof.eyeCm[0]++,
 'missing floor':s=>s.poseProof.supportObjectIds=[],
 'unregistered floor':s=>s.poseProof.supportObjectIds=['DOM_99999'],
}))test(`Oblique rejects ${name}`,()=>{const s=shapeFixture('stills','oblique');mutate(s);assert.throws(()=>makeShapeContract(s.base,{shape:s.shape,poseProof:s.poseProof,stoveGeometry:s.authoring.stoveGeometry,walking:s.authoring.walking}));});

test('The same eight intensity/state semantics accept the registered candidate recipe',()=>{
 const groups=['day','night'].map(state=>SCALES.map(scale=>{
  const a=authoring(),m=a.imported.stoveVisuals.activeReloadEvidence[0].flameMaterial;delete m.emissionAndOpacityShapeUnchanged;Object.assign(m,candidateProof());
  const c=makeStudyContract({...a,lightingState:state}),x=state==='night'?nightFixture(scale):fixture(scale);x.contract=c;x.contractBytes=Buffer.from(JSON.stringify(c));x.runtime.contractSha1=sha(x.contractBytes,'sha1');
  const report=inspectFlameRun(x);assert.equal(report.status,'controlled-flame-capture-validated',report.errors.join('; '));
  return {report:{...report,image:x.image,contractSha256:sha(x.contractBytes),packageReceiptSha256:digest,executableSha256:digest,launch:x.launch,inputHashes:{a:digest},nativeHashes:{a:digest},helperHashes:{a:digest}},runtime:x.runtime,contract:c};
 }));
 assert.equal(compareLightingStates(...groups).status,'day-night-controlled-captures-ready-for-visual-review');
});

for(const key of ['__proto__','toString','constructor'])test(`Prototype key ${key} is not a registered recipe`,()=>assert.throws(()=>requireRecipeMetadata({shaderCodeSha256:key,emissionAndOpacityMatchPinnedShader:true},{allowHistoricalBaseline:true})));


// A third exact recipe fixes only wrapped-coordinate derivatives; historical names stay pinned.
import {EDGE_DERIVATIVE_SHA} from '../scripts/unreal/flame-study.mjs';
const derivativeProof=()=>({shaderCodeSha256:EDGE_DERIVATIVE_SHA,emissionAndOpacityMatchPinnedShader:true,
 alphaShapeChangedFromPreviousRevision:true,previousShaderSha256:CANDIDATE_SHA});
test('Derivative recipe records the exact immediate predecessor without changing scale defaults',()=>{
 const a=authoring(),m=a.imported.stoveVisuals.activeReloadEvidence[0].flameMaterial;
 delete m.emissionAndOpacityShapeUnchanged;Object.assign(m,derivativeProof());
 const original=JSON.stringify(a),c=makeStudyContract(a);
 assert.equal(c.flameShaderSha256,EDGE_DERIVATIVE_SHA);assert.equal(c.previousShaderSha256,CANDIDATE_SHA);
 assert.equal(c.alphaShapeChangedFromPreviousRevision,true);assert.equal(c.emissionAndOpacityMatchPinnedShader,true);
 assert.deepEqual(c.defaultScalarParameters,{BreziFlameEmissionScale:1,BreziFlameStudyTimeSeconds:-1});
 assert.equal(c.triangles,12);assert.equal(c.graphNodeCount,10);assert.equal(JSON.stringify(a),original);
});
for(const [name,mutate]of Object.entries({
 'missing native proof':r=>delete r.emissionAndOpacityMatchPinnedShader,
 'false native proof':r=>r.emissionAndOpacityMatchPinnedShader=false,
 'missing alpha-change relation':r=>delete r.alphaShapeChangedFromPreviousRevision,
 'false alpha-change relation':r=>r.alphaShapeChangedFromPreviousRevision=false,
 'missing predecessor':r=>delete r.previousShaderSha256,
 'null predecessor':r=>r.previousShaderSha256=null,
 'skipped predecessor':r=>r.previousShaderSha256=FLAME_SHADER_SHA256,
 'self predecessor':r=>r.previousShaderSha256=EDGE_DERIVATIVE_SHA,
 'ambiguous legacy true':r=>r.emissionAndOpacityShapeUnchanged=true,
 'ambiguous legacy false':r=>r.emissionAndOpacityShapeUnchanged=false,
}))test(`Derivative recipe rejects ${name}`,()=>{const r=derivativeProof();mutate(r);assert.throws(()=>requireRecipeMetadata(r,{allowHistoricalBaseline:true}));});
test('Derivative cannot use historical legacy-only proof',()=>assert.throws(()=>requireRecipeMetadata(
 {shaderCodeSha256:EDGE_DERIVATIVE_SHA,emissionAndOpacityShapeUnchanged:true},{allowHistoricalBaseline:true})));
test('Both historical recipe proofs remain exact and unmodified',()=>{
 const legacy={shaderCodeSha256:FLAME_SHADER_SHA256,emissionAndOpacityShapeUnchanged:true},connected=candidateProof();
 const bytes=[JSON.stringify(legacy),JSON.stringify(connected)];
 const a=requireRecipeMetadata(legacy,{allowHistoricalBaseline:true}),b=requireRecipeMetadata(connected);
 assert.equal(a.historicalCompatibilityUsed,true);assert.equal(a.previousShaderSha256,null);
 assert.equal(b.historicalCompatibilityUsed,false);assert.equal(b.previousShaderSha256,FLAME_SHADER_SHA256);
 assert.deepEqual([JSON.stringify(legacy),JSON.stringify(connected)],bytes);
 assert.throws(()=>requireRecipeMetadata(legacy));
});
test('Derivative authoring retains ten-node, source triangle and neutral-default rejection gates',()=>{
 for(const mutate of [m=>m.graphNodeCount=9,m=>m.worldPositionOffsetConnected=true,
  m=>m.defaultScalarParameters.BreziFlameEmissionScale=4,m=>m.defaultScalarParameters.BreziFlameStudyTimeSeconds=2]){
  const a=authoring(),m=a.imported.stoveVisuals.activeReloadEvidence[0].flameMaterial;
  delete m.emissionAndOpacityShapeUnchanged;Object.assign(m,derivativeProof());mutate(m);assert.throws(()=>makeStudyContract(a));
 }
 const a=authoring(),row=a.imported.stoveVisuals.activeReloadEvidence[0];delete row.flameMaterial.emissionAndOpacityShapeUnchanged;
 Object.assign(row.flameMaterial,derivativeProof());row.triangles=14;assert.throws(()=>makeStudyContract(a));
});
for(const mode of ['stills','sequence'])test(`Derivative ${mode} uses the existing phase schedule without promotion`,()=>{
 const s=shapeFixture(mode,'oblique'),m=s.authoring.imported.stoveVisuals.activeReloadEvidence[0].flameMaterial;
 delete m.emissionAndOpacityShapeUnchanged;Object.assign(m,derivativeProof());
 const c=makeShapeContract(makeStudyContract(s.authoring),{shape:s.shape,poseProof:s.poseProof,stoveGeometry:s.authoring.stoveGeometry,walking:s.authoring.walking});
 assert.equal(c.flameShaderSha256,EDGE_DERIVATIVE_SHA);assert.equal(c.previousShaderSha256,CANDIDATE_SHA);
 assert.equal(c.shapeMode,mode);assert.equal(c.studyTimeSeconds,2);assert.deepEqual(c.defaultScalarParameters,{BreziFlameEmissionScale:1,BreziFlameStudyTimeSeconds:-1});
});
