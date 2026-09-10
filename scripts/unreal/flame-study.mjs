import { spawn, execFile } from 'node:child_process';
import { createHash, randomUUID } from 'node:crypto';
import { mkdir, readFile, readdir, writeFile, access } from 'node:fs/promises';
import { dirname, resolve, relative } from 'node:path';
import { homedir } from 'node:os';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { promisify } from 'node:util';
import { inflateSync } from 'node:zlib';
const self = fileURLToPath(import.meta.url);
let root = dirname(self);
while (true) { try { await access(resolve(root, 'package.json')); break; } catch { const next=dirname(root); if(next===root) throw Error('Repository root not found'); root=next; } }
const { inspectMotionPng } = await import(pathToFileURL(resolve(root,'scripts/unreal/motion-qa.mjs')));
const { verifyPackagedPayload } = await import(pathToFileURL(resolve(root,'scripts/unreal/package-verify.mjs')));
const { inspectAXInitializer } = await import(pathToFileURL(resolve(root,'scripts/unreal/ax-initializer-qa.mjs')));
// Canonical and output-only tests use the same adopted startup policy.
// Capture entry points independently refuse to run from an output-only copy.
const launchHelperPath=resolve(root,'scripts/unreal/app-launch.mjs');
const {resolveAppLaunch,inspectLauncherExecution,requireIdleApp}=await import(pathToFileURL(launchHelperPath));
export const SCALES=Object.freeze([1,4,16,64]);
export const TARGET_PRE_EXPOSURE=0.0010780160082504153;
export const STATE_PRE_EXPOSURE=Object.freeze({day:TARGET_PRE_EXPOSURE,night:16});
export const FLAME_SHADER_SHA256='682b7d0e89131964e95d845fa365b0a9a1d448ffe256f25be8eb36288bd2c48c';
const BASELINE_SHA='682b7d0e89131964e95d845fa365b0a9a1d448ffe256f25be8eb36288bd2c48c';
export const CANDIDATE_SHA='08a70ffa9d33bdddad0842b8d4a01e5737748acd6ff32cb21c4cc4ea3268172a';
export const EDGE_DERIVATIVE_SHA='45b0871f6776cc197686ff19cb8e7253babdc0c1ca41943d479f504a76f137bc';
const recipes=Object.freeze({
  [BASELINE_SHA]:Object.freeze({alphaShapeChangedFromPreviousRevision:false,previousShaderSha256:null}),
  [CANDIDATE_SHA]:Object.freeze({alphaShapeChangedFromPreviousRevision:true,previousShaderSha256:BASELINE_SHA}),
  [EDGE_DERIVATIVE_SHA]:Object.freeze({alphaShapeChangedFromPreviousRevision:true,previousShaderSha256:CANDIDATE_SHA}),
});

/** Called only after the existing exact native graph/provenance checks.
 * Legacy acceptance is explicit, baseline-only, and must never rewrite old receipts.
 */
export function requireRecipeMetadata(receipt,{allowHistoricalBaseline=false}={}) {
  const sha=receipt?.shaderCodeSha256,expected=typeof sha==='string'&&Object.hasOwn(recipes,sha)?recipes[sha]:undefined;
  if (!expected) throw Error('Unregistered exact shader recipe');
  const newNames=['emissionAndOpacityMatchPinnedShader','alphaShapeChangedFromPreviousRevision','previousShaderSha256'];
  const hasAnyNewField=newNames.some(k=>Object.hasOwn(receipt,k));
  if (hasAnyNewField) {
    if (receipt.emissionAndOpacityMatchPinnedShader!==true
        || receipt.alphaShapeChangedFromPreviousRevision!==expected.alphaShapeChangedFromPreviousRevision
        || receipt.previousShaderSha256!==expected.previousShaderSha256)
      throw Error('Current recipe getter proof or revision relation differs');
    if (sha!==BASELINE_SHA && Object.hasOwn(receipt,'emissionAndOpacityShapeUnchanged'))
      throw Error('Candidate must not carry ambiguous legacy unchanged-shape metadata');
    return {shaderCodeSha256:sha,...expected,proofScope:'exact-current-pinned-shader',historicalCompatibilityUsed:false};
  }
  if (allowHistoricalBaseline && sha===BASELINE_SHA && receipt.emissionAndOpacityShapeUnchanged===true)
    return {shaderCodeSha256:sha,...expected,proofScope:'exact-baseline-legacy-saved-proof',historicalCompatibilityUsed:true};
  throw Error('Missing current recipe proof; legacy fallback is baseline-only and opt-in');
}

const hash=(b,algorithm='sha256')=>createHash(algorithm).update(b).digest('hex');
const finite=x=>typeof x==='number'&&Number.isFinite(x);
const near=(a,b,e)=>finite(a)&&finite(b)&&Math.abs(a-b)<=e;
const vec=(v,n)=>Array.isArray(v)&&v.length===n&&v.every(finite);
const vn=(a,b,e)=>vec(a,b?.length)&&a.every((v,i)=>near(v,b[i],e));
const canonical=v=>Array.isArray(v)?v.map(canonical):v&&typeof v==='object'?Object.fromEntries(Object.keys(v).sort().map(k=>[k,canonical(v[k])])):v;
const equal=(a,b)=>JSON.stringify(canonical(a))===JSON.stringify(canonical(b));
const json=b=>JSON.parse(b.toString('utf8'));
const jsonBytes=v=>Buffer.from(JSON.stringify(v,null,2)+'\n');
const requireThat=(value,message)=>{if(!value)throw Error(message);};
const shaShape=s=>typeof s==='string'&&/^[0-9a-f]{64}$/.test(s);

export function sourcePose(c) {
  requireThat(vec(c.eyeCm,3)&&vec(c.targetCm,3)&&finite(c.horizontalFovDegrees),'Source camera is invalid');
  const d=c.targetCm.map((v,i)=>v-c.eyeCm[i]), length=Math.hypot(...d), f=d.map(v=>v/length), h=Math.hypot(f[0],f[1]);
  requireThat(length>0&&h>0,'Degenerate source camera');
  return {eyeCm:c.eyeCm,forward:f,up:[-f[2]*f[0]/h,-f[2]*f[1]/h,h],horizontalFovDegrees:c.horizontalFovDegrees};
}
export function sourceRoi(c) {
  const p=sourcePose(c), horizontal=Math.hypot(p.forward[0],p.forward[1]), right=[-p.forward[1]/horizontal,p.forward[0]/horizontal,0], points=[];
  const dot=(a,b)=>a.reduce((s,v,i)=>s+v*b[i],0), scale=1920/Math.tan(c.horizontalFovDegrees*Math.PI/360);
  requireThat(vec(c.boundsMinCm,3)&&vec(c.boundsMaxCm,3),'Source flame bounds missing');
  for(let mask=0;mask<8;mask++){
    const d=c.boundsMinCm.map((v,i)=>(mask&(1<<i)?c.boundsMaxCm[i]:v)-c.eyeCm[i]);
    const z=dot(d,p.forward);requireThat(z>1,'Flame bounds cross the camera plane');
    points.push([1920+dot(d,right)/z*scale,1080-dot(d,p.up)/z*scale]);
  }
  const roi=[Math.floor(Math.min(...points.map(p=>p[0])))-4,Math.floor(Math.min(...points.map(p=>p[1])))-4,
    Math.ceil(Math.max(...points.map(p=>p[0])))+4,Math.ceil(Math.max(...points.map(p=>p[1])))+4];
  requireThat(roi[0]>=0&&roi[1]>=0&&roi[2]<=3840&&roi[3]<=2160&&roi[2]>roi[0]&&roi[3]>roi[1],'Flame ROI is outside native frame');return roi;
}

/** CRC/deflate verified by shared helper; actually unfilter RGB to measure only registered ROI. */
export function inspectFlamePng(bytes,roi) {
  const proof=inspectMotionPng(bytes);requireThat(vec(roi,4)&&roi.every(Number.isInteger)&&roi[0]>=0&&roi[1]>=0&&roi[2]<=3840&&roi[3]<=2160&&roi[2]>roi[0]&&roi[3]>roi[1],'Invalid pixel ROI');
  let channels, parts=[];
  for(let offset=8;offset<bytes.length;){const n=bytes.readUInt32BE(offset), type=bytes.toString('ascii',offset+4,offset+8), p=bytes.subarray(offset+8,offset+8+n); if(type==='IHDR')channels=p[9]===6?4:3; if(type==='IDAT')parts.push(p);offset+=n+12;}
  const stride=3840*channels, raw=inflateSync(Buffer.concat(parts),{maxOutputLength:(stride+1)*2160}), rows=[Buffer.alloc(stride),Buffer.alloc(stride)];
  const sums=[0,0,0], min=[255,255,255], max=[0,0,0], histogram=new Uint32Array(256);let saturated=0,pixels=0;
  const paeth=(a,b,c)=>{const p=a+b-c,pa=Math.abs(p-a),pb=Math.abs(p-b),pc=Math.abs(p-c);return pa<=pb&&pa<=pc?a:pb<=pc?b:c;};
  for(let y=0;y<2160;y++){
    const row=rows[y%2],prev=rows[(y+1)%2],off=y*(stride+1),filter=raw[off];
    for(let x=0;x<stride;x++){const a=x>=channels?row[x-channels]:0,b=y?prev[x]:0,c=y&&x>=channels?prev[x-channels]:0;
      row[x]=(raw[off+x+1]+[0,a,b,Math.floor((a+b)/2),paeth(a,b,c)][filter])&255;}
    if(y<roi[1]||y>=roi[3])continue;
    for(let x=roi[0];x<roi[2];x++){const rgb=[row[x*channels],row[x*channels+1],row[x*channels+2]];
      if(channels===4)requireThat(row[x*channels+3]===255,'ROI contains non-opaque screenshot alpha');
      for(let k=0;k<3;k++){sums[k]+=rgb[k];min[k]=Math.min(min[k],rgb[k]);max[k]=Math.max(max[k],rgb[k]);}
      if(rgb.includes(255))saturated++;histogram[Math.round(.2126*rgb[0]+.7152*rgb[1]+.0722*rgb[2])]++;pixels++;
    }
  }
  const percentile=q=>{let count=0;for(let i=0;i<256;i++){count+=histogram[i];if(count>=Math.ceil(q*pixels))return i;}};
  return {...proof,rgbUnfiltered:true,roi,pixelCount:pixels,meanRgb:sums.map(v=>v/pixels),minRgb:min,maxRgb:max,saturatedPixelCount:saturated,
    lumaCodeP50:percentile(.5),lumaCodeP95:percentile(.95),lumaMeaning:'Rec709 weights of stored display code values, not linear radiance or isolated flame contribution'};
}

export function makeStudyContract({imported,stoveGeometry,viewpoints,walking,lightingState='day',packageSha256,importSha256,viewpointsSha256,geometrySha256,walkingSha256}){
  requireThat(imported?.status==='import-validated'&&imported.stoveVisuals?.status==='stove-visuals-saved-reloaded-validated','Current stove authoring must be saved/reloaded/validated');
  const stove=imported.stoveVisuals, candidates=stove.activeReloadEvidence?.filter(v=>v.id==='STOVEV_FLAMES')??[];
  requireThat(candidates.length===1,'Expected exactly one active flame receipt');const f=candidates[0],m=f.flameMaterial,recipe=requireRecipeMetadata(m,{allowHistoricalBaseline:true});
  requireThat(f.triangles===12&&m?.shaderCodeSha256===recipe.shaderCodeSha256&&m.graphNodeCount===10
    &&m.worldPositionOffsetConnected===false&&equal(m.defaultScalarParameters,{BreziFlameEmissionScale:1,BreziFlameStudyTimeSeconds:-1}),
  'Parameterized ten-node flame graph has not been strictly authored and verified; current five-node assets cannot run this study');
  const objects=stoveGeometry?.objects?.filter(o=>o.id==='STOVEV_FLAMES')??[],glasses=imported.optics?.instances?.filter(i=>i.sourceSlot==='MAT_0036')??[];
  const view=viewpoints?.views?.find(v=>v.id==='interior');
  requireThat(stoveGeometry?.status==='stove-visual-geometry-validated'&&objects.length===1&&objects[0].triangles===12&&glasses.length===1&&viewpoints.coordinateSystem==='unreal-centimeters'&&view,'Source flame geometry, glass or camera missing');
  requireThat(stove.sourceManifestSha256===imported.sourceManifestSha256&&stoveGeometry.sourceManifestSha256===imported.sourceManifestSha256
    &&stoveGeometry.sourceObjSha256===stove.sourceObjSha256,'Canonical source provenance differs');
  requireThat(['day','night'].includes(lightingState)&&walking?.status==='source-walking-contract-exported'&&walking.coordinateSystem==='unreal-centimeters'
    &&walking.provenance?.sceneSha256===imported.sourceManifestSha256&&walking.provenance?.sourceObjSha256===stove.sourceObjSha256&&walking.eyeHeightCm===165,
    'Source standing camera contract differs');
  const allowedFloorIds=walking.walkSurfaces.filter(s=>s.dynamic===false&&s.kind==='interior'&&s.nativeBoundsCm.min[0]<=view.eyeCm[0]&&s.nativeBoundsCm.max[0]>=view.eyeCm[0]
    &&s.nativeBoundsCm.min[1]<=view.eyeCm[1]&&s.nativeBoundsCm.max[1]>=view.eyeCm[1]&&near(s.nativeBoundsCm.max[2]+s.supportOffsetCm,view.eyeCm[2]-walking.eyeHeightCm,.02)).map(s=>s.objectId).sort();
  requireThat(allowedFloorIds.length>0,'Source camera has no authored support-plane candidate');
  const c={schemaVersion:1,lightingState,walkingSha256,eyeHeightCm:walking.eyeHeightCm,allowedFloorIds,sourceManifestSha256:imported.sourceManifestSha256,sourceObjSha256:stove.sourceObjSha256,
    packageSha256,importSha256,viewpointsSha256,stoveGeometrySha256:geometrySha256,mesh:f.mesh,material:f.material,triangles:12,
    glassMesh:'/Game/Brezi/Geometry/brezi-twin/StaticMeshes/DOM_00526.DOM_00526',glassMaterial:glasses[0].asset,
    flameShaderSha256:recipe.shaderCodeSha256,defaultScalarParameters:m.defaultScalarParameters,graphNodeCount:10,
    boundsMinCm:objects[0].nativeBoundsCm.min,boundsMaxCm:objects[0].nativeBoundsCm.max,eyeCm:view.eyeCm,targetCm:view.targetCm,horizontalFovDegrees:view.horizontalFovDegrees,
    sun:viewpoints.sun,studyTimeSeconds:2,targetPreExposure:STATE_PRE_EXPOSURE[lightingState],scales:SCALES};
  for(const name of ['sourceManifestSha256','sourceObjSha256','packageSha256','importSha256','viewpointsSha256','stoveGeometrySha256','walkingSha256'])requireThat(shaShape(c[name]),`Missing pinned hash ${name}`);
  // Do not add fields to historical baseline contracts: saved byte hashes remain reproducible.
  if (!recipe.historicalCompatibilityUsed) Object.assign(c,{emissionAndOpacityMatchPinnedShader:true,
    alphaShapeChangedFromPreviousRevision:recipe.alphaShapeChangedFromPreviousRevision,previousShaderSha256:recipe.previousShaderSha256});
  c.roi=sourceRoi(c);return c;
}


export function parseShapeOptions(args) {
  requireThat(Array.isArray(args)&&args.length===3&&['--pose=interior','--pose=oblique'].includes(args[0])
    &&['--state=day','--state=night'].includes(args[1])&&['--mode=stills','--mode=sequence'].includes(args[2]),
    'Shape command requires exactly --pose=interior|oblique --state=day|night --mode=stills|sequence; no quality or scale overrides');
  return {pose:args[0].slice(7),lightingState:args[1].slice(8),mode:args[2].slice(7)};
}
export function shapeFrameCount(mode) { requireThat(['stills','sequence'].includes(mode),'Invalid shape mode'); return mode==='sequence'?62:2; }
export function shapePhase(index) { requireThat(Number.isInteger(index)&&index>=0&&index<=61,'Invalid shape index');return index===0?-1:index===1?2:Math.fround(2+(index-1)/30); }
export function makeShapeContract(base,{shape,poseProof,stoveGeometry,walking}) {
  requireThat(base?.schemaVersion===1&&shape&&['interior','oblique'].includes(shape.pose)&&['stills','sequence'].includes(shape.mode)
    &&shape.lightingState===base.lightingState,'Shape source selection differs');
  const axis=stoveGeometry?.stoveAxisSourceMm,body=stoveGeometry?.sourceRecords?.DOM_00522?.boundsMm;
  requireThat(vec(axis,2)&&body&&axis.every((v,i)=>near(v,(body.min[i]+body.max[i])/2,1e-9)),'Source stove axis differs');
  const sourceStoveAxisCm=[axis[0]/10,-axis[1]/10,0],c={...base,schemaVersion:2,shapeMode:shape.mode,poseId:shape.pose,
    sourceInteriorEyeCm:base.eyeCm,sourceInteriorTargetCm:base.targetCm,sourceStoveAxisCm};
  if(shape.pose==='oblique') {
    requireThat(poseProof?.schemaVersion===1&&poseProof.status==='cpu-source-reachable-candidate-native-query-pending'
      &&poseProof.sourceHashes?.['output/unreal/geometry/scene.json']===base.sourceManifestSha256
      &&poseProof.sourceHashes?.['output/unreal/geometry/dom-mm.obj']===base.sourceObjSha256
      &&poseProof.sourceHashes?.['output/unreal/geometry/walking.json']===base.walkingSha256
      &&poseProof.sourceHashes?.['output/unreal/stove-visuals/stove-visuals.json']===base.stoveGeometrySha256
      &&poseProof.nativeEntryValidated===false&&poseProof.nativeTraversalValidated===false&&poseProof.nativeVisibilityValidated===false
      &&equal(poseProof.blockedSourceObjectIds,[])&&poseProof.diagnosticRadiusCm===300&&poseProof.diagnosticAzimuthDegrees===-30,
      'Oblique CPU source proof is absent, stale or claims native coverage');
    const eye=[sourceStoveAxisCm[0]+300*Math.cos(Math.PI/6),sourceStoveAxisCm[1]-150,165],target=[sourceStoveAxisCm[0],sourceStoveAxisCm[1],165];
    requireThat(vn(poseProof.eyeCm,eye,1e-9)&&vn(poseProof.targetCm,target,1e-9)
      &&near(poseProof.horizontalFovDegrees,base.horizontalFovDegrees,1e-9)&&equal(poseProof.sourceInterior.eyeCm,base.eyeCm)
      &&equal(poseProof.sourceInterior.targetCm,base.targetCm)&&Array.isArray(poseProof.supportObjectIds)&&poseProof.supportObjectIds.length>0,
      'Oblique pose differs from source-derived diagnostic recipe');
    const floors=walking.walkSurfaces.filter(f=>poseProof.supportObjectIds.includes(f.objectId));
    requireThat(floors.length===poseProof.supportObjectIds.length&&new Set(poseProof.supportObjectIds).size===floors.length
      &&floors.every(f=>f.dynamic===false&&f.kind==='interior'&&f.nativeBoundsCm.min[0]<=eye[0]&&f.nativeBoundsCm.max[0]>=eye[0]
        &&f.nativeBoundsCm.min[1]<=eye[1]&&f.nativeBoundsCm.max[1]>=eye[1]&&near(f.nativeBoundsCm.max[2]+f.supportOffsetCm,0,.02)),
      'Oblique source supports differ');
    Object.assign(c,{eyeCm:eye,targetCm:target,allowedFloorIds:poseProof.supportObjectIds,obliqueProofSha256:hash(jsonBytes(poseProof))});
  }
  c.roi=sourceRoi(c);return c;
}

export function inspectFlameRun(args) { return inspectFlameCapture(args,false); }
export function inspectShapeRun(args) { return inspectFlameCapture(args,true); }
function inspectFlameCapture({runtime:r,contract:c,contractBytes,scale,image,baselineImage,images,outcome,log,launcherLog,launch,ax,payloadBefore,payloadAfter},shape) {
  const errors=[],check=(v,m)=>{if(!v)errors.push(m);};
  check(SCALES.includes(scale)&&r?.schemaVersion===(shape?2:1)&&r.status===(shape?'flame-shape-captured':'flame-study-captured'),'Native study did not complete');
  if(shape) {
    check(scale===1&&c?.schemaVersion===2&&['stills','sequence'].includes(c.shapeMode)&&['interior','oblique'].includes(c.poseId)
      &&r?.shapeMode===c.shapeMode&&r?.poseId===c.poseId&&r?.shapePhaseSource==='indexed-MID-scalar-at-30-simulation-Hz'
      &&r?.expectedCaptureFrames===shapeFrameCount(c.shapeMode)&&r?.realTimePlaybackVerified===false
      &&r?.nativeStoveAxisVerified===true&&vn(r?.sourceStoveAxisNativeCm,c.sourceStoveAxisCm,.005),'Native shape mode, source axis or scope differs');
  }
  check(r?.parentScalarDefaultsRead===true&&r?.parentDefaultEmissionScale===1&&r?.parentDefaultStudyTimeSeconds===-1,'Runtime parent scalar defaults differ');
  check(r?.emissionScale===scale&&r?.studyTimeSeconds===2&&r?.targetPreExposure===c.targetPreExposure&&r?.lightingState===c.lightingState,'Study scale, phase or exposure differs');
  check(Buffer.isBuffer(contractBytes)&&r?.contractSha1===hash(contractBytes,'sha1')&&equal(json(contractBytes),c),'Native contract bytes do not match');
  check(r?.sceneSha256===c.sourceManifestSha256&&r?.sourceObjSha256===c.sourceObjSha256,'Actual source world differs');
  check(r?.simulationHz===30&&r?.warmupFrames===240&&r?.warmupGameViews===240&&r?.warmupRenderViews===240&&r?.warmupRenderFramesConsecutive===true,'Missing exact 240-frame GT/RT warmup');
  for(const key of ['fixedClockRestored','originalMaterialPointerRestored','originalComponentStatesRestored','viewExtensionStoppedAndFlushed','qualitySettingsUnchanged','cameraModeAndPriorViewRestored'])check(r?.[key]===true,`Restoration proof missing: ${key}`);
  const clock=r?.clock;
  check(clock&&typeof clock.priorUseFixedFrameRate==='boolean'&&typeof clock.priorUseFixedTimeStep==='boolean'
    &&clock.priorUseFixedFrameRate===clock.currentUseFixedFrameRate&&clock.priorUseFixedTimeStep===clock.currentUseFixedTimeStep
    &&near(clock.priorFixedFrameRate,clock.currentFixedFrameRate,0)&&near(clock.priorFixedDeltaSeconds,clock.currentFixedDeltaSeconds,0),'Actual clock getter restoration differs');
  for(const k of ['worldTimeArtificiallyFrozen','fpsMeasured','uiIncluded','highResolutionScreenshotUsed','physicalBrightnessCalibrated'])check(r?.[k]===false,`Unsupported scope: ${k}`);
  check(outcome?.code===0&&outcome.signal===null&&!outcome.timedOut&&!outcome.logTruncated&&!outcome.error&&Number.isSafeInteger(outcome.pid)
    &&outcome.pid>0&&r?.nativeProcessId===outcome.pid&&equal(outcome.renderersAfter,[]),'Actual renderer PID did not cleanly terminate');
  check(typeof log==='string'&&/LogExit: Exiting/.test(log)&&!/invalid ShaderMap|uncooked shader map|Failed to compile Material|Default Material will be used|Fatal error:|Assertion failed:|Ensure condition failed:|Handled ensure|LogShaderCompilers: Error|LogMaterial: Error/i.test(log),'Exit log is missing or contains shader/ensure/fatal failure');
  const axCheck=inspectAXInitializer(ax);errors.push(...axCheck.errors);
  errors.push(...inspectLauncherExecution(launch,outcome,launcherLog??log).errors);
  check(payloadBefore?.status==='packaged-payload-unchanged'&&payloadAfter?.status==='packaged-payload-unchanged'&&equal(payloadBefore,payloadAfter),'Package payload changed');
  const frames=r?.frames??[];check(Array.isArray(frames)&&frames.length===(shape&&['stills','sequence'].includes(c?.shapeMode)?shapeFrameCount(c.shapeMode):2),'Expected exact bounded capture count');const f=frames[1]??{},baseline=frames[0]??{},p=sourcePose(c);
  check(f.index===1&&f.file==='frame-001.png'&&f.captureKind==='controlled-study'&&f.pngSaved===true&&f.emissionScale===scale&&f.studyTimeSeconds===2&&f.transientMaterialPointerBound===true,'Exact transient parameter or capture identity missing');
  check(Number.isSafeInteger(f.requestFrameCounter)&&f.requestFrameCounter>0&&['captureFrameCounter','gameViewFrameCounter','renderFrameCounter'].every(k=>f[k]===f.requestFrameCounter)
    &&Number.isSafeInteger(f.gameViewFamilyFrameNumber)&&f.gameViewFamilyFrameNumber===f.renderFamilyFrameNumber&&f.gameMainViewCount===1&&f.renderMainViewCount===1&&f.sceneIdentityPaired===true,'GT/RT screenshot family mismatch');
  check(vn(f.eyeCm,p.eyeCm,.01)&&vn(f.forward,p.forward,1e-6)&&vn(f.up,p.up,1e-6)&&near(f.horizontalFovDegrees,p.horizontalFovDegrees,1e-4)
    &&near(f.viewFovDegrees,p.horizontalFovDegrees,1e-4)&&vec(f.projectionJitter,2)&&f.cameraCut===false,'Actual camera differs from exact source interior');
  check(['renderTargetPixels','unscaledViewPixels','screenshotPixels'].every(k=>vn(f[k],[3840,2160],0)),'Actual native view/target/readback is not 4K');
  check(image?.decodedPixelsVerified===true&&image?.rgbUnfiltered===true&&vn(image.pixels===undefined?null:image.pixels,[3840,2160],0),'PNG pixels not decoded');
  check(vn(image?.roi,sourceRoi(c),0)&&shaShape(image?.sha256),'PNG ROI/hash differs');
  check(f.showFlagPostProcessing===true&&f.showFlagAntiAliasing===true&&typeof f.showFlagTemporalAA==='boolean'&&typeof f.allowTemporalJitter==='boolean','Required render show flags missing');
  const quality=r?.qualitySettings??{};
  for(const [name,value] of [['r.ScreenPercentage',100],['r.SecondaryScreenPercentage.GameViewport',100],['r.DynamicRes.OperationMode',0],['r.EyeAdaptation.PreExposureOverride',0]])check(quality[name]!=null&&Number(quality[name])===value,`Native quality differs: ${name}`);
  check([1,2,4,5].includes(f.antiAliasingMethod)&&Number(quality['r.AntiAliasingMethod'])===f.antiAliasingMethod&&r?.requestedAA===f.antiAliasingMethod,'Effective AA differs');
  const lens=Number(quality['r.EyeAdaptation.LensAttenuation']), extended=Number(quality['r.DefaultFeature.AutoExposure.ExtendDefaultLuminanceRange']);
  const luminance=extended!==0?.78/Math.max(lens,.01):1;
  check(f.manualExposure===true&&f.physicalCameraExposure===false&&f.exposureBiasCurvePresent===false&&f.localExposure===false&&f.eyeAdaptationShowFlag===true
    &&vn(f.sceneColorTint,[1,1,1],1e-6)&&finite(lens)&&near(f.manualExposureBias,Math.log2(c.targetPreExposure*luminance),1e-6)
    &&near(f.linearPreExposure/c.targetPreExposure,1,1e-4),'Paired RT manual exposure differs');
  check(near(f.worldDeltaSeconds,1/30,1e-6)&&near(f.requestDeltaSeconds,1/30,1e-6)&&near(f.appDeltaSeconds,1/30,1e-6)
    &&near(f.worldSeconds,f.requestWorldSeconds,1e-5)&&near(f.realSeconds,f.requestRealSeconds,1e-5)
    &&finite(f.requestWallSeconds)&&f.captureWallSeconds>=f.requestWallSeconds&&f.pngWriteCompleteWallSeconds>=f.captureWallSeconds,'Actual clock/capture ordering differs');
  const fc=r?.initialFlameComponent,gc=r?.initialGlassComponent;
  check(fc?.mesh===c.mesh&&fc?.sourceMaterial===c.material&&fc?.triangles===12&&fc?.materialSlots===1&&fc?.blendMode===3&&fc?.unlit===true&&fc?.twoSided===true
    &&fc?.collisionProfile==='NoCollision'&&fc?.collisionMode===0&&fc?.visible===true&&fc?.hiddenInGame===false&&fc?.actorHidden===false&&fc?.disableDepthTest===false
    &&vn(fc?.boundsMinCm,c.boundsMinCm,.005)&&vn(fc?.boundsMaxCm,c.boundsMaxCm,.005),'Exact native flame geometry/material policy differs');
  check(gc?.mesh===c.glassMesh&&gc?.sourceMaterial===c.glassMaterial&&gc?.triangles===192&&gc?.materialSlots===1&&gc?.visible===true&&gc?.hiddenInGame===false&&gc?.actorHidden===false&&gc?.disableDepthTest===false&&gc?.refractionMethod===3,'Glass source identity or visibility differs');
  check(equal(fc,f.flameComponent)&&equal(fc,r?.finalFlameComponent)&&equal(gc,f.glassComponent)&&equal(gc,r?.finalGlassComponent),'Flame/glass geometry or compositing state changed');
  const rot=c.sun?.dayRotationDegrees, pitch=(c.lightingState==='night'?-25:rot?.[0])*Math.PI/180,yaw=(c.lightingState==='night'?rot?.[1]+150:rot?.[1])*Math.PI/180,dir=[Math.cos(pitch)*Math.cos(yaw),Math.cos(pitch)*Math.sin(yaw),Math.sin(pitch)];
  check(r?.initialSun?.count===1&&r.initialSun.visible===true&&near(r.initialSun.lux,c.lightingState==='night'?.15:c.sun?.dayLux,.01)&&vn(r.initialSun.direction,dir,1e-6)&&equal(r.initialSun,f.sun),'Source lighting-state sun differs');
  check(baseline.index===0&&baseline.file==='frame-000.png'&&baseline.captureKind==='production-baseline'&&baseline.emissionScale===1&&baseline.studyTimeSeconds===-1
    &&baseline.transientMaterialPointerBound===false&&baseline.manualExposure===false&&finite(baseline.linearPreExposure)&&baseline.linearPreExposure>0,
    'Untouched production material/exposure baseline missing');
  check(baselineImage?.decodedPixelsVerified===true&&baselineImage?.rgbUnfiltered===true&&vn(baselineImage.pixels,[3840,2160],0)&&vn(baselineImage.roi,c.roi,0),
    'Production baseline PNG not decoded');
  check(equal(fc,baseline.flameComponent)&&equal(gc,baseline.glassComponent)&&equal(r?.initialSun,baseline.sun),'Baseline source/compositing state differs');
  check(f.requestFrameCounter===baseline.requestFrameCounter+241&&f.renderFamilyFrameNumber===baseline.renderFamilyFrameNumber+241,
    'Controlled frame did not follow production baseline plus 240 rendered warmup frames');
  for(const shot of [baseline,f]) {
    check(shot.warmupGameViews===240&&shot.warmupRenderViews===240&&shot.warmupConsecutive===true,'Each phase requires independent exact GT/RT warmup');
    check(Number.isSafeInteger(shot.requestFrameCounter)&&shot.requestFrameCounter>0&&['captureFrameCounter','gameViewFrameCounter','renderFrameCounter'].every(k=>shot[k]===shot.requestFrameCounter)
      &&Number.isSafeInteger(shot.gameViewFamilyFrameNumber)&&shot.gameViewFamilyFrameNumber===shot.renderFamilyFrameNumber&&shot.gameMainViewCount===1&&shot.renderMainViewCount===1&&shot.sceneIdentityPaired===true,'Baseline/control GT/RT identity mismatch');
    check(vn(shot.eyeCm,p.eyeCm,.01)&&vn(shot.forward,p.forward,1e-6)&&vn(shot.up,p.up,1e-6)&&near(shot.horizontalFovDegrees,p.horizontalFovDegrees,1e-4)
      &&near(shot.viewFovDegrees,p.horizontalFovDegrees,1e-4)&&shot.cameraCut===false&&['renderTargetPixels','unscaledViewPixels','screenshotPixels'].every(k=>vn(shot[k],[3840,2160],0)),
      'Baseline/control actual native camera or 4K dimensions differ');
    const w=shot.standing;
    check(w?.cameraMode==='walking'&&w.contractLoaded===true&&w.worldContractValidated===true&&w.sceneSha256===c.sourceManifestSha256&&w.sourceObjSha256===c.sourceObjSha256
      &&w.expectedEyeHeightCm===c.eyeHeightCm&&w.groundedEyeSamples>=240&&w.unmeasuredOrAirborneEyeSamples===0&&w.entryAttempts===1&&w.successfulEntries===1
      &&c.allowedFloorIds.includes(w.currentSupportObjectId)&&c.allowedFloorIds.includes(w.entrySupportObjectId)&&vn(w.currentCameraEyeCm,c.eyeCm,.01)
      &&near(w.lastMeasuredEyeHeightCm,c.eyeHeightCm,.02)&&near(w.minMeasuredEyeHeightCm,c.eyeHeightCm,.02)&&near(w.maxMeasuredEyeHeightCm,c.eyeHeightCm,.02)
      &&finite(w.maxEyeHeightErrorCm)&&w.maxEyeHeightErrorCm<=.02&&equal(w.worldContractErrors,[]),'Actual standing eye/support proof differs');
  }
  if(shape) {
    check(Array.isArray(images)&&images.length===frames.length&&equal(images[0],baselineImage)&&equal(images[1],image),'Shape image inventory differs');
    for (let i=2;i<Math.min(frames.length,62);i++) {
      const shot=frames[i],prev=frames[i-1],im=images?.[i];
      if (!shot || typeof shot!=='object' || !prev || typeof prev!=='object') {check(false,`Shape frame ${i} is missing`);continue;}
      check(shot?.index===i&&shot?.file===`frame-${String(i).padStart(3,'0')}.png`&&shot.captureKind==='controlled-advancing-time'
        &&shot.pngSaved===true&&shot.emissionScale===1&&shot.studyTimeSeconds===shapePhase(i)&&shot.transientMaterialPointerBound===true,
        `Shape frame ${i} actual material phase/index differs`);
      check(shot.requestFrameCounter===prev.requestFrameCounter+1&&['captureFrameCounter','gameViewFrameCounter','renderFrameCounter'].every(k=>shot[k]===shot.requestFrameCounter)
        &&shot.gameViewFamilyFrameNumber===shot.renderFamilyFrameNumber&&shot.renderFamilyFrameNumber===prev.renderFamilyFrameNumber+1
        &&shot.gameMainViewCount===1&&shot.renderMainViewCount===1&&shot.sceneIdentityPaired===true,`Shape frame ${i} is not exact consecutive GT/RT/readback`);
      check(shot.warmupGameViews===240&&shot.warmupRenderViews===240&&shot.warmupConsecutive===true,`Shape frame ${i} lost established warmup proof`);
      check(vn(shot.eyeCm,p.eyeCm,.01)&&vn(shot.forward,p.forward,1e-6)&&vn(shot.up,p.up,1e-6)&&near(shot.horizontalFovDegrees,p.horizontalFovDegrees,1e-4)
        &&near(shot.viewFovDegrees,p.horizontalFovDegrees,1e-4)&&vec(shot.projectionJitter,2)&&shot.cameraCut===false,`Shape frame ${i} source camera differs`);
      check(['renderTargetPixels','unscaledViewPixels','screenshotPixels'].every(k=>vn(shot[k],[3840,2160],0))
        &&im?.decodedPixelsVerified===true&&im?.rgbUnfiltered===true&&vn(im?.pixels,[3840,2160],0)&&vn(im?.roi,c.roi,0)&&shaShape(im?.sha256),`Shape frame ${i} PNG/4K proof missing`);
      for(const key of ['antiAliasingMethod','primaryScreenPercentageMethod','showFlagPostProcessing','showFlagAntiAliasing','showFlagTemporalAA','allowTemporalJitter',
        'manualExposure','physicalCameraExposure','exposureBiasCurvePresent','localExposure','eyeAdaptationShowFlag','manualExposureBias','sceneColorTint','flameComponent','glassComponent','sun'])
        check(equal(shot[key],f[key]),`Shape frame ${i} controlled ${key} drifted`);
      check(near(shot.linearPreExposure/c.targetPreExposure,1,1e-4)&&near(shot.worldDeltaSeconds,1/30,1e-6)&&near(shot.requestDeltaSeconds,1/30,1e-6)&&near(shot.appDeltaSeconds,1/30,1e-6)
        &&near(shot.worldSeconds,shot.requestWorldSeconds,1e-5)&&near(shot.realSeconds,shot.requestRealSeconds,1e-5)
        &&near(shot.worldSeconds-prev.worldSeconds,1/30,1e-4)&&near(shot.realSeconds-prev.realSeconds,1/30,1e-4)
        &&shot.requestWallSeconds>=prev.pngWriteCompleteWallSeconds&&shot.captureWallSeconds>=shot.requestWallSeconds&&shot.pngWriteCompleteWallSeconds>=shot.captureWallSeconds,
        `Shape frame ${i} phase clock/exposure/readback order differs`);
      const w=shot.standing;
      check(w?.cameraMode==='walking'&&w.contractLoaded===true&&w.worldContractValidated===true&&w.sceneSha256===c.sourceManifestSha256&&w.sourceObjSha256===c.sourceObjSha256
        &&w.expectedEyeHeightCm===165&&w.groundedEyeSamples>=240&&w.unmeasuredOrAirborneEyeSamples===0&&w.entryAttempts===1&&w.successfulEntries===1
        &&c.allowedFloorIds.includes(w.currentSupportObjectId)&&c.allowedFloorIds.includes(w.entrySupportObjectId)&&vn(w.currentCameraEyeCm,c.eyeCm,.01)
        &&near(w.lastMeasuredEyeHeightCm,165,.02)&&near(w.minMeasuredEyeHeightCm,165,.02)&&near(w.maxMeasuredEyeHeightCm,165,.02)
        &&finite(w.maxEyeHeightErrorCm)&&w.maxEyeHeightErrorCm<=.02&&equal(w.worldContractErrors,[]),`Shape frame ${i} standing support differs`);
    }
  }
  return {status:errors.length?'failed':shape?'flame-shape-capture-validated':'controlled-flame-capture-validated' ,errors,scale,lightingState:c.lightingState,physicalBrightnessCalibrated:false,productionPromotionAllowed:false,
    requiredNext:shape?'Inspect the phase-2 still and all requested sampled-time images in day/night and oblique views. Synchronous samples do not prove real-time playback or select a production default.':'Review all four daylight PNGs and separately test any proposed candidate in daylight and night. This study does not select a production default.'};
}

export function compareFlameRuns(runs) {
  const errors=[],check=(v,m)=>{if(!v)errors.push(m);};
  check(Array.isArray(runs)&&runs.length===4&&equal(runs.map(r=>r.report.scale),SCALES),'Four ordered 1/4/16/64 runs are required');
  if(!Array.isArray(runs)||runs.length!==4)return{status:'failed',errors};
  for(const [i,run]of runs.entries())if(run?.report?.status!=='controlled-flame-capture-validated'||run.report.errors?.length!==0||run.runtime?.frames?.length!==2)errors.push(`Run ${i} lacks completed capture evidence`);
  if(errors.length)return{status:'failed',errors,productionPromotionAllowed:false};
  const base=runs[0];
  for(const [i,run] of runs.entries()) {
    check(run.report.status==='controlled-flame-capture-validated'&&run.report.errors.length===0,`Run ${i} failed validation`);
    for(const name of ['contractSha256','packageReceiptSha256','executableSha256','launch','inputHashes','nativeHashes','helperHashes'])check(equal(run.report[name],base.report[name]),`Run ${i} provenance differs: ${name}`);
    check(equal(run.contract,base.contract),`Run ${i} source contract differs`);
    const a=base.runtime.frames[1],b=run.runtime.frames[1];
    for(const field of ['eyeCm','forward','up','horizontalFovDegrees','viewFovDegrees','projectionJitter','antiAliasingMethod','primaryScreenPercentageMethod','cameraCut','allowTemporalJitter',
      'showFlagPostProcessing','showFlagAntiAliasing','showFlagTemporalAA','manualExposure','physicalCameraExposure','exposureBiasCurvePresent','localExposure','eyeAdaptationShowFlag','manualExposureBias','sceneColorTint',
      'flameComponent','glassComponent','sun']) check(equal(a[field],b[field]),`Run ${i} paired state differs: ${field}`);
    check(near(a.linearPreExposure/b.linearPreExposure,1,1e-5)&&equal(run.runtime.qualitySettings,base.runtime.qualitySettings),`Run ${i} exposure or quality changed`);
  }
  return{status:errors.length?'failed':'four-controlled-flame-captures-comparable',errors,productionPromotionAllowed:false,physicalBrightnessCalibrated:false,
    nightCandidateQa:'required-before-any-production-default-change',selectedProductionScale:null,
    statistics:runs.map(r=>({scale:r.report.scale,image:r.report.image,conservativeSingleCardRedPreExposedBound:8*.78*r.report.scale*r.runtime.frames[1].linearPreExposure})),
    boundMeaning:'Authored Custom-output upper bound times maximum opacity and paired CPU View.PreExposure. It is not an observed pixel, glass transmission, linear HDR readback or photometric calibration.',
    limitations:'Exact jitter mismatch fails comparison. Synchronous still screenshots are not FPS or motion proof. Dynamic water/foliage may differ; the ROI includes unchanged stove/background and glass, not an isolated flame pass. Tone-mapped RGB is not proportional to emission scale. Visual day and night review remains required.'};
}
export function compareLightingStates(dayRuns,nightRuns) {
  const states=[{lightingState:'day',...compareFlameRuns(dayRuns)},{lightingState:'night',...compareFlameRuns(nightRuns)}],errors=[];
  if(states.some(s=>s.status==='failed'))return{status:'failed',errors:['Both complete four-scale lighting states are required'],states,selectedProductionScale:null,productionPromotionAllowed:false};
  const a=dayRuns?.[0],b=nightRuns?.[0];
  if(!a||!b||a.contract.lightingState!=='day'||b.contract.lightingState!=='night')errors.push('Both lighting states are required');
  else {
    for(const name of ['packageReceiptSha256','executableSha256','launch','inputHashes','nativeHashes','helperHashes'])if(!equal(a.report[name],b.report[name]))errors.push(`Day/night provenance differs: ${name}`);
    const strip=c=>{const {lightingState,targetPreExposure,...rest}=c;return rest;};
    if(!equal(strip(a.contract),strip(b.contract)))errors.push('Day/night camera, geometry or source contract differs');
    for(const k of ['eyeCm','forward','up','horizontalFovDegrees','viewFovDegrees'])if(!equal(a.runtime.frames[1][k],b.runtime.frames[1][k]))errors.push(`Day/night actual standing camera differs: ${k}`);
  }
  for(const state of states)if(state.status==='failed')errors.push(`${state.lightingState} scale comparison failed`);
  return{status:errors.length?'failed':'day-night-controlled-captures-ready-for-visual-review',errors,states,selectedProductionScale:null,productionPromotionAllowed:false,physicalBrightnessCalibrated:false};
}
async function rendererInventory() {
  const found=[];
  for(const name of ['BreziTwin','BreziStartupLauncher','UnrealEditor','UnrealEditor-Cmd']){
    try{const r=await promisify(execFile)('pgrep',['-x',name]);for(const pid of r.stdout.trim().split(/\s+/).filter(Boolean))found.push({name,pid:Number(pid)});}
    catch(e){if(e.code!==1)throw e;}
  }return found;
}
async function requireNoRenderer(){await requireIdleApp();const list=await rendererInventory();requireThat(list.length===0,`Renderer slot is occupied: ${JSON.stringify(list)}`);}
async function currentHashes(files){const out={};for(const file of files)out[file]=hash(await readFile(resolve(root,file)));return out;}
async function checkHashes(expected){for(const [file,digest]of Object.entries(expected))requireThat(hash(await readFile(resolve(root,file)))===digest,`Pinned source changed: ${file}`);}
async function context(lightingState,shape=null) {
  const geometry=resolve(root,process.env.BREZI_GEOMETRY??process.env.UNREAL_OUTPUT??'output/unreal/geometry'),output=dirname(geometry);
  const paths={package:'output/unreal/package-report.json',import:relative(root,resolve(output,'import-report.json')),scene:relative(root,resolve(geometry,'scene.json')),
    viewpoints:relative(root,resolve(geometry,'viewpoints.json')),walking:relative(root,resolve(geometry,'walking.json')),stoveGeometry:relative(root,resolve(output,'stove-visuals/stove-visuals.json'))};
  const bytes=Object.fromEntries(await Promise.all(Object.entries(paths).map(async([key,path])=>[key,await readFile(resolve(root,path))])));
  const p=json(bytes.package),imp=json(bytes.import),views=json(bytes.viewpoints),geom=json(bytes.stoveGeometry);
  requireThat(p.status==='packaged'&&imp.status==='import-validated'&&p.mapFileSha256===imp.mapFileSha256&&p.nativeAuthoredStateSha256===imp.nativeAuthoredStateSha256
    &&imp.sourceManifestSha256===hash(bytes.scene)&&imp.viewpointsSha256===hash(bytes.viewpoints)&&imp.walkingSha256===hash(bytes.walking),'Current package/import/source differs');
  let c=makeStudyContract({imported:imp,stoveGeometry:geom,viewpoints:views,walking:json(bytes.walking),lightingState,walkingSha256:hash(bytes.walking),packageSha256:hash(bytes.package),importSha256:hash(bytes.import),viewpointsSha256:hash(bytes.viewpoints),geometrySha256:hash(bytes.stoveGeometry)});
  let poseProof=null;
  if(shape) {
    if(shape.pose==='oblique') {
      const result=await promisify(execFile)('python3',[resolve(root,'scripts/unreal/flame-shape/derive-pose.py'),'--stdout'],{cwd:root,maxBuffer:8*1024*1024});
      poseProof=json(Buffer.from(result.stdout));await checkHashes(poseProof.sourceHashes);
      bytes.poseProof=jsonBytes(poseProof);
    }
    c=makeShapeContract(c,{shape,poseProof,stoveGeometry:geom,walking:json(bytes.walking)});
  }
  const nativeHashes=p.nativeSourceFiles??{};
  requireThat(Object.keys(nativeHashes).length>0&&['BreziFlameStudy.h','BreziFlameStudy.cpp','BreziPlayerController.h','BreziPlayerController.cpp'].every(f=>shaShape(nativeHashes[`unreal/BreziTwin/Source/BreziTwin/${f}`])),'Packaged native flame component or controller hookup is missing');
  const inputHashes={...imp.pipelineFiles,...imp.finalAssetHashes,'unreal/BreziTwin/Content/Brezi/Maps/Brezi.umap':imp.mapFileSha256,...Object.fromEntries(Object.entries(paths).map(([key,path])=>[path,hash(bytes[key])])),...(poseProof?.sourceHashes??{})};
  await checkHashes(nativeHashes);await checkHashes(inputHashes);
  const helpers=['scripts/unreal/flame-study.mjs','scripts/unreal/motion-qa.mjs','scripts/unreal/package-verify.mjs','scripts/unreal/app-launch.mjs','scripts/unreal/startup-entry.mjs','scripts/unreal/startup-entry-package.mjs','scripts/unreal/macho-signature.mjs','scripts/unreal/ax-initializer-qa.mjs'];
  const helperHashes=await currentHashes([...helpers,...(shape?.pose==='oblique'?['scripts/unreal/flame-shape/derive-pose.py']:[])]),contractBytes=jsonBytes(c);
  const payload=await verifyPackagedPayload(p.appPath,p.bundle),launch=await resolveAppLaunch(p.appPath,p.bundle);
  return{bytes,p,imp,c,shape,contractBytes,nativeHashes,inputHashes,helperHashes,launch,executable:launch.executable,executableSha256:launch.executableSha256,payload};
}
async function runOne(ctx,scale,evidence) {
  await requireNoRenderer();await checkHashes({...ctx.nativeHashes,...ctx.inputHashes,...ctx.helperHashes});
  const payloadBefore=await verifyPackagedPayload(ctx.p.appPath,ctx.p.bundle);
  const id=`flame-study-${ctx.c.lightingState}-${scale}-${randomUUID()}`,sandbox=resolve(homedir(),'Library/Containers/local.brezi.twin/Data/Library/Application Support/BreziTwin/QA',id);
  await mkdir(sandbox,{recursive:true});await mkdir(evidence,{recursive:true});
  await writeFile(resolve(sandbox,'contract.json'),ctx.contractBytes);await writeFile(resolve(evidence,'contract.json'),ctx.contractBytes);
  for(const [name,b]of Object.entries(ctx.bytes))await writeFile(resolve(evidence,`${name}.json`),b);
  const args=['-windowed','-ResX=1600','-ResY=900',`-UserDir=${sandbox}/`,`-BreziFlameStudyScale=${scale}`,`-BreziFlameStudyContract=${resolve(sandbox,'contract.json')}`,'-BreziFlameStudyExit',...(ctx.shape?[`-BreziFlameShape=${ctx.shape.mode}`]:[]),...(ctx.c.lightingState==='night'?['-BreziNight']:[])];
  const chunks=[];let total=0,timedOut=false,logTruncated=false;
  const outcome=await new Promise(accept=>{
    const child=spawn(ctx.executable,args,{cwd:root,stdio:['ignore','pipe','pipe']});let timer,killTimer,finished=false;
    const stop=()=>{child.kill('SIGTERM');killTimer??=setTimeout(()=>child.kill('SIGKILL'),10000);};
    timer=setTimeout(()=>{timedOut=true;stop();},360000);
    process.once('SIGINT',stop);process.once('SIGTERM',stop);
    const finish=v=>{if(finished)return;finished=true;clearTimeout(timer);clearTimeout(killTimer);process.removeListener('SIGINT',stop);process.removeListener('SIGTERM',stop);accept({...v,pid:child.pid??null});};
    for(const stream of [child.stdout,child.stderr])stream.on('data',b=>{total+=b.length;if(total<=64*1024*1024)chunks.push(b);else{logTruncated=true;stop();}});
    child.once('error',e=>finish({code:null,signal:null,error:e.message}));child.once('close',(code,signal)=>finish({code,signal}));
  });
  Object.assign(outcome,{timedOut,logTruncated,renderersAfter:await rendererInventory()});
  const rawLog=Buffer.concat(chunks),errors=[];await writeFile(resolve(evidence,'process.log'),rawLog);
  let runtime=null,ax=null,image=null,baselineImage=null,payloadAfter=null;const savedLogs=[],images=[];
  for(const [source,target]of [['Saved/Diagnostics/flame-study/runtime.json','runtime.json'],['Saved/Diagnostics/AX/initializer.json','ax-initializer.json'],...Array.from({length:ctx.shape?shapeFrameCount(ctx.shape.mode):2},(_,i)=>{const file=`frame-${String(i).padStart(3,'0')}.png`;return [`Saved/Diagnostics/flame-study/${file}`,file];})]){
    try{const b=await readFile(resolve(sandbox,source));await writeFile(resolve(evidence,target),b);
      if(target==='runtime.json')runtime=json(b);else if(target==='ax-initializer.json')ax=json(b);else {const index=Number(target.slice(6,9));images[index]=inspectFlamePng(b,ctx.c.roi);if(index===0)baselineImage=images[index];if(index===1)image=images[index];}}
    catch(e){errors.push(`${target}: ${e.message}`);}
  }
  try{for(const name of await readdir(resolve(sandbox,'Saved/Logs'))){if(!name.endsWith('.log'))continue;const b=await readFile(resolve(sandbox,'Saved/Logs',name));savedLogs.push(b);await writeFile(resolve(evidence,`engine-${savedLogs.length}.log`),b);}}catch(e){errors.push(`Saved engine logs: ${e.message}`);}
  const log=Buffer.concat([rawLog,...savedLogs.map(b=>Buffer.concat([Buffer.from('\n'),b]))]);await writeFile(resolve(evidence,'combined.log'),log);
  try{payloadAfter=await verifyPackagedPayload(ctx.p.appPath,ctx.p.bundle);await checkHashes({...ctx.nativeHashes,...ctx.inputHashes,...ctx.helperHashes});
    requireThat(equal(await resolveAppLaunch(ctx.p.appPath,ctx.p.bundle),ctx.launch),'Launcher or engine startup policy changed');}
  catch(e){errors.push(e.message);}
  const report=(ctx.shape?inspectShapeRun:inspectFlameRun)({runtime,contract:ctx.c,contractBytes:ctx.contractBytes,scale,image,baselineImage,images,outcome,log:log.toString('utf8'),launcherLog:rawLog.toString('utf8'),launch:ctx.launch,ax,payloadBefore,payloadAfter});
  report.errors.push(...errors);if(report.errors.length)report.status='failed';
  Object.assign(report,{generatedAt:new Date().toISOString(),process:outcome,args,sandbox,image,baselineImage,...(ctx.shape?{images}:{}),payloadBefore,payloadAfter,
    contractSha256:hash(ctx.contractBytes),packageReceiptSha256:hash(ctx.bytes.package),executableSha256:ctx.executableSha256,launch:ctx.launch,
    inputHashes:ctx.inputHashes,nativeHashes:ctx.nativeHashes,helperHashes:ctx.helperHashes});
  const artifactHashes={};for(const file of await readdir(evidence))artifactHashes[file]=hash(await readFile(resolve(evidence,file)));report.artifactHashes=artifactHashes;
  await writeFile(resolve(evidence,'flame-study.json'),jsonBytes(report));
  return{report,runtime,contract:ctx.c};
}
async function captureStudy(){
  requireThat(self===resolve(root,'scripts/unreal/flame-study.mjs'),'Output-only draft cannot launch a renderer. Integrate and compile through the coordinated root pipeline first.');
  await requireNoRenderer();const directory=resolve(root,'output/unreal/runtime',`flame-study-${randomUUID()}`);await mkdir(directory,{recursive:true});
  const groups=[];
  for(const lightingState of ['day','night']){
    const ctx=await context(lightingState),runs=[];
    for(const scale of SCALES){const run=await runOne(ctx,scale,resolve(directory,lightingState,`scale-${scale}`));runs.push(run);if(run.report.status==='failed')break;}
    const comparison=compareFlameRuns(runs);groups.push(runs);if(comparison.status==='failed')break;
  }
  const result=compareLightingStates(groups[0]??[],groups[1]??[]);
  await writeFile(resolve(directory,'study.json'),jsonBytes(result));console.log(JSON.stringify({directory,...result},null,2));if(result.status==='failed')process.exitCode=1;
}


async function captureShape(args) {
  requireThat(self===resolve(root,'scripts/unreal/flame-study.mjs'),'Output-only draft cannot launch a renderer. Integrate through the coordinated root pipeline first.');
  const shape=parseShapeOptions(args);await requireNoRenderer();
  const directory=resolve(root,'output/unreal/runtime',`flame-shape-${shape.pose}-${shape.lightingState}-${shape.mode}-${randomUUID()}`);
  const ctx=await context(shape.lightingState,shape),run=await runOne(ctx,1,directory);
  const result={status:run.report.status,errors:run.report.errors,directory,shape,productionScale:1,productionPromotionAllowed:false,
    fpsMeasured:false,realTimePlaybackVerified:false,physicalBrightnessCalibrated:false};
  await writeFile(resolve(directory,'study.json'),jsonBytes(result));console.log(JSON.stringify(result,null,2));
  if(result.status==='failed')process.exitCode=1;
}

async function loadRun(directory){
  const report=json(await readFile(resolve(directory,'flame-study.json')));
  requireThat(report.artifactHashes&&Object.keys(report.artifactHashes).length>0,'Saved artifact hash inventory missing');
  for(const [file,digest]of Object.entries(report.artifactHashes)){requireThat(!file.includes('/')&&!file.includes('..')&&shaShape(digest),'Unsafe saved artifact path/hash');requireThat(hash(await readFile(resolve(directory,file)))===digest,`Saved artifact changed: ${file}`);}
  const contractBytes=await readFile(resolve(directory,'contract.json')),contract=json(contractBytes),runtime=json(await readFile(resolve(directory,'runtime.json')));
  const p=await readFile(resolve(directory,'package.json')),imp=await readFile(resolve(directory,'import.json')),viewpoints=await readFile(resolve(directory,'viewpoints.json')),geom=await readFile(resolve(directory,'stoveGeometry.json'));
  let rebuilt=makeStudyContract({imported:json(imp),stoveGeometry:json(geom),viewpoints:json(viewpoints),walking:json(await readFile(resolve(directory,'walking.json'))),walkingSha256:hash(await readFile(resolve(directory,'walking.json'))),lightingState:contract.lightingState,packageSha256:hash(p),importSha256:hash(imp),viewpointsSha256:hash(viewpoints),geometrySha256:hash(geom)});
  const shape=contract.schemaVersion===2?{pose:contract.poseId,mode:contract.shapeMode,lightingState:contract.lightingState}:null;
  if(shape) rebuilt=makeShapeContract(rebuilt,{shape,stoveGeometry:json(geom),walking:json(await readFile(resolve(directory,'walking.json'))),
    poseProof:shape.pose==='oblique'?json(await readFile(resolve(directory,'poseProof.json'))):null});
  requireThat(equal(rebuilt,contract)&&report.contractSha256===hash(contractBytes)&&report.packageReceiptSha256===hash(p)&&equal(report.launch,json(p).bundle?.launch),'Saved source/package/launcher contract mismatch');
  const image=inspectFlamePng(await readFile(resolve(directory,'frame-001.png')),contract.roi),baselineImage=inspectFlamePng(await readFile(resolve(directory,'frame-000.png')),contract.roi);
  const images=shape?await Promise.all(Array.from({length:shapeFrameCount(shape.mode)},async(_,i)=>inspectFlamePng(await readFile(resolve(directory,`frame-${String(i).padStart(3,'0')}.png`)),contract.roi))):undefined;
  const current=(shape?inspectShapeRun:inspectFlameRun)({runtime,contract,contractBytes,scale:report.scale,image,baselineImage,images,outcome:report.process,
    log:(await readFile(resolve(directory,'combined.log'))).toString('utf8'),launcherLog:(await readFile(resolve(directory,'process.log'))).toString('utf8'),launch:report.launch,ax:json(await readFile(resolve(directory,'ax-initializer.json'))),payloadBefore:report.payloadBefore,payloadAfter:report.payloadAfter});
  requireThat(current.status!=='failed'&&report.status===current.status&&equal(report.image,image)&&equal(report.baselineImage,baselineImage)&&(!shape||equal(report.images,images))&&report.errors.length===0,`Saved evidence failed independent reread: ${current.errors.join('; ')}`);
  return{report,runtime,contract};
}
async function revalidateStudy(directory){const groups=[];for(const lightingState of ['day','night']){const runs=[];for(const scale of SCALES)runs.push(await loadRun(resolve(directory,lightingState,`scale-${scale}`)));groups.push(runs);}
 const result=compareLightingStates(groups[0],groups[1]);
 const path=resolve(directory,`revalidation-${randomUUID()}.json`);await writeFile(path,jsonBytes(result));console.log(JSON.stringify({path,...result},null,2));if(result.status==='failed')process.exitCode=1;}

// Bounded scale-one entry: reuse the exact existing native two-frame driver and
// validators. This is a visual review input, never intensity promotion or FPS QA.
export function compareScaleOneStates(runs) {
  const errors=[];
  if (!Array.isArray(runs) || runs.length!==2 || runs.some((r,i)=>r?.report?.status!=='controlled-flame-capture-validated'
      || r.report.errors?.length!==0 || r.report.scale!==1 || r.runtime?.frames?.length!==2
      || !['eyeCm','forward','up'].every(k=>vec(r.runtime.frames[1]?.[k],3))
      || !['horizontalFovDegrees','viewFovDegrees'].every(k=>finite(r.runtime.frames[1]?.[k]))
      || r.contract?.lightingState!==['day','night'][i]))
    return {status:'failed',errors:['Two validated scale-one day/night runs are required'],productionPromotionAllowed:false,selectedProductionScale:null};
  const [a,b]=runs;
  for (const key of ['packageReceiptSha256','executableSha256','launch','inputHashes','nativeHashes','helperHashes'])
    if (!equal(a.report[key],b.report[key])) errors.push(`Day/night provenance differs: ${key}`);
  const strip=c=>{const {lightingState,targetPreExposure,...rest}=c;return rest;};
  if (!equal(strip(a.contract),strip(b.contract))) errors.push('Day/night source contract differs');
  for (const key of ['eyeCm','forward','up','horizontalFovDegrees','viewFovDegrees'])
    if (!equal(a.runtime?.frames?.[1]?.[key],b.runtime?.frames?.[1]?.[key])) errors.push(`Day/night paired camera differs: ${key}`);
  return {status:errors.length?'failed':'scale-one-day-night-stills-ready-for-visual-review',errors,
    capturedScale:1,selectedProductionScale:null,productionPromotionAllowed:false,physicalBrightnessCalibrated:false,
    motionVerified:false,fpsMeasured:false};
}
async function captureScaleOne() {
  requireThat(self===resolve(root,'scripts/unreal/flame-study.mjs'),'Output-only draft cannot launch a renderer. Integrate through the coordinated root pipeline first.');
  await requireNoRenderer();
  const directory=resolve(root,'output/unreal/runtime',`flame-scale-one-${randomUUID()}`),runs=[];
  await mkdir(directory,{recursive:true});
  for (const lightingState of ['day','night']) {
    const ctx=await context(lightingState);
    const run=await runOne(ctx,1,resolve(directory,lightingState,'scale-1'));
    runs.push(run); if(run.report.status==='failed') break;
  }
  const result=compareScaleOneStates(runs);
  await writeFile(resolve(directory,'study.json'),jsonBytes(result));
  console.log(JSON.stringify({directory,...result},null,2)); if(result.status==='failed') process.exitCode=1;
}


async function revalidateShape(directory) {
  const run=await loadRun(directory);requireThat(run.contract.schemaVersion===2,'Expected a shape study');
  const result={status:run.report.status,errors:run.report.errors,originalReportSha256:hash(await readFile(resolve(directory,'flame-study.json'))),
    productionPromotionAllowed:false,fpsMeasured:false,realTimePlaybackVerified:false};
  const file=resolve(directory,`revalidation-${randomUUID()}.json`);await writeFile(file,jsonBytes(result));console.log(JSON.stringify({file,...result},null,2));
}

if(process.argv[1]&&resolve(process.argv[1])===self){const [command,...args]=process.argv.slice(2);if(command==='capture'&&args.length===0)await captureStudy();else if(command==='capture-scale-one'&&args.length===0)await captureScaleOne();else if(command==='capture-shape')await captureShape(args);else if(command==='revalidate-shape'&&args.length===1)await revalidateShape(resolve(args[0]));else if(command==='revalidate'&&args.length===1)await revalidateStudy(resolve(args[0]));else throw Error('Usage: node scripts/unreal/flame-study.mjs capture | capture-scale-one | capture-shape --pose=interior|oblique --state=day|night --mode=stills|sequence | revalidate-shape <shape-directory> | revalidate <study-directory>');}
