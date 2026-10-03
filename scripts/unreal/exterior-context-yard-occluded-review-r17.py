"""CPU-only negative review of two unchanged original, tree-occluded yard PNGs."""
import importlib.util
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-context-yard-occluded-review-r17.py'
OUT=ROOT/'output/unreal/exterior-validation-20260930-r1'
AUDIT=OUT/'purposeful-context-yard-occluded-paired-review-r17-r1.json'
DELEGATE=ROOT/'scripts/unreal/exterior-context-yard-paired-review-r28.py'
SPEC=importlib.util.spec_from_file_location('r17_frozen_original_capture_proofs',DELEGATE)
proof=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(proof)
PATHS=[OUT/'qa/editor-pilot-r27a-yard572063-baseline-r17-1790913455634-lzUian/editor-pilot-suite.json',
 OUT/'qa/editor-pilot-r28b-yard572063-candidate-r17-1790913639937-1Zayyt/editor-pilot-suite.json']
PIDS=[75017,75382]
SOURCE_SHAS=['5575c0e37a9d48733b5c7ed3746f1731cc2b7958634a845c87b9700ff4fc9498',
 'dfbca65515fc08aea52515195ab5ef752fe07cdca622cd41964e99875ced2456']


def main():
 assert not AUDIT.exists(),'Fresh negative review required'
 assert proof.pin(DELEGATE)['sha256']=='9f4cd05084b69521be9a15c1407fabaedbd88ecc3fd41f4ab33996cb461d4e49'
 suites=[proof.read(p)for p in PATHS];cases=[];rows=[];runtimes=[]
 for suite,path,pid,source_sha in zip(suites,PATHS,PIDS,SOURCE_SHAS):
  assert suite['status']=='editor-game-suite-recorded-awaiting-independent-visual-review'and suite['sourceInputsUnchanged']is True and not suite['errors']
  assert suite['requestedViews']==['exterior-context-yard-572063-close-r17']and len(suite['cases'])==1
  assert suite['requestedBuild']=='Development'and suite['requestedTransport']=='UnrealEditor -game'and suite['requestedProfile']=='cinematic'and suite['requestedOutput']=='retina'
  evidence=suite['nativeSourceEvidence'];assert evidence['mode']=='purposeful-first-context-yard-matched-camera-qa-clone'
  assert evidence['sourceNativeReport']['sha256']==source_sha and evidence['originalNativeSourceUnchanged']is True
  pins={key:proof.verify_pin(evidence[key])for key in ['nativeReceipt','sourceNativeReport','sourceNativeProcess','cameraSupplement']}
  assert evidence['cameraStageReceipt']==pins['nativeReceipt']['path'];pins['cameraStageReceipt']=pins['nativeReceipt']
  a,b=proof.verify_pin(suite['inputClosureBefore']),proof.verify_pin(suite['inputClosureAfter'])
  assert a['sha256']==b['sha256']and a['bytes']==b['bytes']and proof.read(a['path'])==proof.read(b['path'])
  assert len(proof.read(a['path']))==suite['inputClosureBefore']['fileCount']==suite['inputClosureAfter']['fileCount']
  case=suite['cases'][0];cases.append(case);runtimes.append(proof.read(case['originalRuntimePath']))
  rows.append({'suite':proof.pin(path),'capture':proof.case_proof(case,pid),'sourceEvidence':pins,
   'inputClosureBefore':a,'inputClosureAfter':b,'recordedClosureFileCount':suite['inputClosureBefore']['fileCount'],
   'recordedInputClosureExact':True,'currentWholeClosureFilesRehashedByThisReview':False})
 x,y=cases;rb,ra=runtimes
 assert x['sourceCamera']==y['sourceCamera']and x['observed']['actualCamera']==y['observed']['actualCamera']
 assert rb['renderSettings']==ra['renderSettings']and rb['rhi']==ra['rhi']=='Metal'and rb['shaderPlatform']==ra['shaderPlatform']=='METAL_SM6'
 assert rb['screenshotPixels']==ra['screenshotPixels']==[1920,1080]and rb['warmupFrames']==ra['warmupFrames']==2400and rb['requestedBenchmarkFrames']==ra['requestedBenchmarkFrames']==300
 assert rb['screenshotKind']==ra['screenshotKind']=='current-scene-render-target-preserving-view-history'
 ppb,ppa=rb['finalViewPostProcessSettings'],ra['finalViewPostProcessSettings'];fields=[k for k in ppb if ppb[k]!=ppa[k]]
 assert set(ppb)==set(ppa)and fields==['renderThreadPreExposure']
 evb,eva=(p['renderThreadPreExposure']['exposureEV']for p in(ppb,ppa))
 for c in cases:
  facts,focus=c['observed']['frameIntervalFacts'],c['observed']['foregroundTimingFacts']
  assert facts['status']=='measured'and facts['sampleCount']==focus['sampleCount']==300
  assert focus['gameWindowActiveSamples']==focus['sceneViewportKeyboardFocusSamples']==300and focus['applicationForegroundSamples']==0
 receipt={'schemaVersion':1,'owner':OWNER,'status':'actual-matched-yard-pair-reviewed-camera-occluded-no-appearance-acceptance',
  'producer':proof.pin(ROOT/OWNER),'originalCaptureProofDelegate':proof.pin(DELEGATE),'baseline':rows[0],'candidate':rows[1],
  'sourceCamera':x['sourceCamera'],'observedCamera':x['observed']['actualCamera'],'renderSettings':rb['renderSettings'],
  'pairChecks':{'sourceCameraExact':True,'observedCameraExact':True,'renderSettingsExact':True,'composedPostProcessExceptExposureExact':True,
   'postProcessDifferenceFields':fields,'nativeFovDirectReadbackAvailable':False,'pixels':[1920,1080],'warmupFrames':2400,'benchmarkFrames':300},
  'exposure':{'mode':'automatic-unlocked','beforeEV':evb,'afterEV':eva,'deltaEV':eva-evb,'fixedExposureComparison':False},
  'visualReview':{'originalImagesIndependentlyViewed':2,'originalPngsEdited':False,'usefulYardAppearanceComparison':False,
   'dominantOccluder':'Close oak-like leaves and branches cover most of both frames. Building and ground are visible only through gaps.',
   'visibleDifference':'A small pale shrub and a gray approach patch are visible through a central-left gap in the candidate. The full paths, beds and shrub layout cannot be assessed.',
   'measuredOcclusionPercentage':None,'segmentedOcclusionAreaPerformed':False,'cameraInsideTreeGeometricProofPerformed':False,
   'sourceBuildingEyeAndFrustumPredicatesAreOcclusionProof':False,'appearanceGainAccepted':False},
  'editorTimingObservation':{'baseline':x['observed']['frameIntervalFacts'],'candidate':y['observed']['frameIntervalFacts'],'performanceAccepted':False},
  'nativeOrGpuExecutedByThisReview':False,'browserVerifiedByThisReview':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,
  'performanceAccepted':False,'shippingVerified':False,'packageVerified':False,'goNoGo':'CAMERA_OCCLUDED_NEGATIVE_EVIDENCE; FULL_REALISM_NO_GO'}
 AUDIT.write_text(json.dumps(receipt,indent=2,allow_nan=False,ensure_ascii=False)+'\n')
 print(json.dumps({'audit':proof.pin(AUDIT),'originalImagesReviewed':2,'exposureDeltaEV':eva-evb,'nativeExecuted':False}))


if __name__=='__main__':main()
