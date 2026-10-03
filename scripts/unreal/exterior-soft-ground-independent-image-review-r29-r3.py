"""Record this agent's five original-image observations and bounded runtime facts.

No images are copied/edited, no captured source inventory is rehashed, and no
historical source/native producer or Unreal process is launched.
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-soft-ground-independent-image-review-r29-r3.py'
V=ROOT/'output/unreal/exterior-validation-20260930-r1'
OUT=ROOT/'output/unreal/exterior-context-yard-soft-coherence-20261002-r38-independent-image-review-r29-r3'
CASES=[
 ('garden-before','editor-pilot-r37b-selected-garden-yard-r28-1790945953708-UNkW4D','exterior-garden',57776,
  'c0fb4a7260227387cf503bdb0d8298ad0a0512c56887f8af83bcaf41018ffb57'),
 ('garden-after','editor-pilot-r38b-soft-ground-garden-r29-r3-1790953242674-oiT2Wb','exterior-garden',88916,
  '39366ae6391c4b9a953639a891413b67e6027ac8d43e98a956173e71cffb6041'),
 ('yard-before','editor-pilot-r37b-selected-garden-yard-close-r28-1790946792493-m5ASuo','exterior-context-yard-572063-close-r18',59731,
  'd6e346007d80e782a5fb7a3b25945ee185c054da5d14fa0c168a143c59fb71f2'),
 ('yard-after','editor-pilot-r38b-soft-ground-two-camera-r29-r3-1790954357075-1qWu4r','exterior-context-yard-572063-close-r18',93499,
  'c56f08594b272f44e5249e8284cdcf7fa8521f203bd5fdd50dfc72f34569a111'),
 ('ground-candidate-only','editor-pilot-r38b-soft-ground-two-camera-r29-r3-1790954357075-1qWu4r','exterior-neighborhood-ground-r38',93795,
  'bc4a7f28cb2ca1f2cbaf29439eb7350a005faf20e2d121653f7abea928c2f8d9')]
def read(p):return json.loads(Path(p).read_text())
def pin(p):
    p=Path(p).resolve();return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def checked(row):
    assert pin(row['path'])=={k:row[k]for k in ('path','sha256','bytes')};return read(row['path'])
def capture(row):
    key,suite_name,view,pid,png_sha=row;suite_pin=pin(V/'qa'/suite_name/'editor-pilot-suite.json');suite=read(suite_pin['path'])
    assert suite['status']=='editor-game-suite-recorded-awaiting-independent-visual-review'and suite['sourceInputsUnchanged']is True
    assert suite['errors']==[]and suite['nativeIdleAfter']['activeNativeProcesses']==[]and suite['warmupFrames']==2400 and suite['benchmarkFrames']==300
    before=checked(suite['inputClosureBefore']);after=checked(suite['inputClosureAfter'])
    assert before==after and len(before)==suite['inputClosureBefore']['fileCount']==suite['inputClosureAfter']['fileCount']
    cases=[c for c in suite['cases']if c['view']==view];assert len(cases)==1;case=cases[0]
    assert case['processId']==pid and case['outcome']=={'code':0,'signal':None,'pid':pid}and case['shaderAndLoadErrors']==[]
    assert case['nativeEvidenceValidated']is True and case['sourceFovNativeReadbackAvailable']is False
    assert read(case['processReceiptPath'])==case
    png=pin(case['originalCapturePath']);runtime_pin=pin(case['originalRuntimePath']);r=read(runtime_pin['path'])
    assert png['sha256']==case['originalCaptureSha256']==png_sha and runtime_pin['sha256']==case['originalRuntimeSha256']
    header=Path(png['path']).read_bytes()[:24];assert header[:8]==b'\x89PNG\r\n\x1a\n'and struct.unpack('>II',header[16:24])==(1920,1080)
    assert r['processId']==pid and r['status']=='capture-complete'and r['activeView']==view and r['buildConfiguration']=='Development'
    assert r['screenshotSaved']is True and r['screenshotPixels']==[1920,1080]and r['warmupFrames']==2400 and r['requestedBenchmarkFrames']==300
    return {'key':key,'suite':suite_pin,'process':pin(case['processReceiptPath']),'sourceCamera':case['sourceCamera'],
      'originalPng':png,'originalRuntime':runtime_pin,'runtime':r,'recordedSourceFiles':len(before),
      'recordedBeforeAfterSourceClosureEqual':True,'capturedProjectFilesFreshlyRehashedByReview':False,
      'stdoutOrRuntimeLogsFreshlyValidatedByThisReview':False,'fullOriginalActuallyViewedByInfillReview':True}
def main():
    assert not OUT.exists(),'Independent review output must be new'
    helper=ROOT/'scripts/unreal/exterior-garden-yard-paired-review-r28.py';spec=importlib.util.spec_from_file_location('r29_independent_pp',helper)
    q=importlib.util.module_from_spec(spec);spec.loader.exec_module(q)
    images={row[0]:capture(row)for row in CASES};pairs={}
    for label in ['garden','yard']:
        before,after=images[label+'-before'],images[label+'-after'];a,b=before['runtime'],after['runtime']
        exact={k:q.difference(a[k],b[k])for k in ['renderSettings','lighting','exteriorLighting']}
        exact['sourceCamera']=q.difference(before['sourceCamera'],after['sourceCamera'])
        exact['observedCamera']=q.difference(a['walking']['presentationCamera'],b['walking']['presentationCamera'])
        exact['staticPostProcess']=q.difference(q.static_pp(a['finalViewPostProcessSettings']),q.static_pp(b['finalViewPostProcessSettings']))
        assert all(not differences for differences in exact.values())
        ev=[r['finalViewPostProcessSettings']['renderThreadPreExposure']['exposureEV']for r in [a,b]]
        pairs[label]={'comparison':'immediate-R37-parent-to-R38-two-slot-overlay','exactCameraRenderLightStaticPostProcess':True,'differences':exact,
          'exposure':{'beforeEV':ev[0],'afterEV':ev[1],'deltaEV':ev[1]-ev[0],'mode':'automatic-unlocked','fixedExposureComparison':False},
          'observedMeanFrameIntervalMs':[a['frameInterval']['meanMs'],b['frameInterval']['meanMs']],
          'performanceAccepted':False,'nativeFovDirectReadbackAvailable':False,'dynamicCloudAndTimePhaseControlEstablished':False,
          'specificMaterialOrGeometryPixelCauseIsolated':False}
    result={'schema':'brezi-r38-five-original-independent-image-observations-r29-r3','schemaVersion':1,'owner':OWNER,
      'reviewer':'infill_review','status':'five-originals-reviewed-local-yard-coherence-gain-full-no-go',
      'images':{k:{field:v for field,v in row.items()if field!='runtime'}for k,row in images.items()},'pairs':pairs,
      'findings':{'garden':'Bed layout, front fern band and tall silver-plume forms are effectively held. No additional garden gain. Repeated bright flowers, leggy planting/mulch gaps, sharp bed edge and uniform lawn remain CG.',
        'yard':'Bright green angular bed/island boundaries are softened into a more continuous brown-green surface. This is a narrow local coherence gain. Gray court edge, sparse planted beds, plain facades, flat glass/door and broad flat ground remain CG.',
        'ground':'Candidate-only view places the neighboring houses between the existing tree trunks/crowns. The large uniform plate, exposed soil and empty house surroundings still lack habitation cues. No matching baseline or gain claim.'},
      'conditionalBasePreference':'R38b for the next inhabited-props review candidate only; root selection still required',
      'specificVisibleSourceRootCountsEstablished':False,'originalPixelsModified':False,'nativeAppearanceAccepted':False,
      'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,
      'producer':pin(ROOT/OWNER),'pureDifferenceHelper':pin(helper)}
    OUT.mkdir();target=OUT/'independent-five-original-review.json';target.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(pin(target)))
if __name__=='__main__':main()
