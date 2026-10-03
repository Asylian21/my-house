"""Read closed original R22c/R24b PNG/runtime pair; write only fresh review files."""
import hashlib
import json
from pathlib import Path
import re
import struct
from urllib.parse import quote

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-original-tree-paired-review-r24.py'
OUT=ROOT/'output/unreal/exterior-validation-20260930-r1'
BEFORE=OUT/'qa/editor-pilot-r22c-integrated-r10-1790903900548-CzNNn7/editor-pilot-suite.json'
AFTER=OUT/'qa/editor-pilot-r24b-original-tree-r12-1790907542077-reskUg/editor-pilot-suite.json'


def pin(path):
    path=Path(path).resolve()
    return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'bytes':path.stat().st_size}


def read(path):return json.loads(Path(path).read_text())


def main():
    audit=OUT/'original-tree-paired-editor-r22c-r24b-audit-r1.json'
    page=OUT/'r24b-original-tree-comparison.html'
    assert not audit.exists() and not page.exists(), 'Immutable fresh paired review required'
    b,a=read(BEFORE),read(AFTER)
    x=next(c for c in b['cases'] if c['view']=='exterior-canopy-close');y=a['cases'][0]
    for suite in (b,a):
        assert suite['sourceInputsUnchanged'] is True and not suite['errors']
        assert suite['status']=='editor-game-suite-recorded-awaiting-independent-visual-review'
    assert x['outcome']=={'code':0,'signal':None,'pid':53435} and y['outcome']=={'code':0,'signal':None,'pid':63230}
    for case in (x,y):
        assert case['nativeEvidenceValidated'] is True and not case['shaderAndLoadErrors']
        assert case['sourceFovNativeReadbackAvailable'] is False
        assert pin(case['originalCapturePath'])['sha256']==case['originalCaptureSha256']
        assert pin(case['originalRuntimePath'])['sha256']==case['originalRuntimeSha256']
        process=read(case['processReceiptPath'])
        assert process['outcome']==case['outcome'] and process['nativeEvidenceValidated'] is True
        png=Path(case['originalCapturePath']).read_bytes()
        assert png[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',png[16:24])==(1920,1080)
    rb,ra=[read(c['originalRuntimePath']) for c in (x,y)]
    assert x['sourceCamera']==y['sourceCamera'] and x['observed']['actualCamera']==y['observed']['actualCamera']
    assert rb['renderSettings']==ra['renderSettings'] and rb['rhi']==ra['rhi']=='Metal'
    assert rb['shaderPlatform']==ra['shaderPlatform']=='METAL_SM6'
    assert rb['screenshotPixels']==ra['screenshotPixels']==[1920,1080]
    assert rb['warmupFrames']==ra['warmupFrames']==2400 and rb['requestedBenchmarkFrames']==ra['requestedBenchmarkFrames']==300
    assert rb['screenshotKind']==ra['screenshotKind']=='current-scene-render-target-preserving-view-history'
    evb=rb['finalViewPostProcessSettings']['renderThreadPreExposure']['exposureEV']
    eva=ra['finalViewPostProcessSettings']['renderThreadPreExposure']['exposureEV'];delta=eva-evb
    template=OUT/'r21b-comparison.html';text=template.read_text()
    old_after,old_before=re.findall(r'<img src="([^"]+)"',text)
    before_url,after_url=[quote(Path(c['originalCapturePath']).relative_to(OUT).as_posix(),safe='/') for c in (x,y)]
    text=text.replace(old_after,after_url).replace(old_before,before_url)
    text=re.sub(r'<title>.*?</title>','<title>Jeden pôvodný strom · R22c → R24b</title>',text)
    text=re.sub(r'<h1>.*?</h1>','<h1>Viditeľné vetvenie a nepravidelná koruna</h1>',text)
    text=re.sub(r'<p class="intro">.*?</p>',
        '<p class="intro">R24b nahrádza jeden strom pôvodným modelom Tree Small 02 od Poly Haven. V strede záberu pribudli odhalené konáre, jemné skupiny listov a vzdušnejšia silueta. Referenciou je bezprostredná základná scéna R22c.</p>',text)
    text=text.replace('R16 → R21b · Editor Development / Metal · 1920 × 1080 · automatická expozícia · umelecky navrhnutý, nezameraný povrch',
        'R22c → R24b · Editor Development / Metal SM6 · 1920 × 1080 · automatická expozícia · umelecké osadenie, bez potvrdenej ekologickej zhody')
    text=text.replace('R21b: nové trsy trávy a nízke byliny na detailnejšom zelenom povrchu','R24b: vzdušný strom s nepravidelnou korunou a viditeľným vetvením')
    text=text.replace('R16: hladké zelené popredie pred stromami','R22c: hustá takmer súvislá tmavá koruna stredného stromu')
    text=text.replace('Pred · R16','Pred · R22c').replace('Po · R21b','Po · R24b')
    text=text.replace('snímku R16','snímku R22c').replace('snímku R21b','snímku R24b')
    text=text.replace('canopy-foreground-paired-editor-r16-r21b-audit-r1.json',audit.name)
    text=re.sub(r'<footer>.*?</footer>',
        '<footer>Čiastočný vizuálny prínos pre jeden strom. Riedka nová koruna sa líši od hustých opakujúcich sa susedných stromov; plochý zelený podklad, opakujúce sa byliny a jednoduché domy zostávajú viditeľné. Celková fotorealistickosť, výkon a Shipping nie sú schválené. Expozícia sa zmenila o '+f'{delta:+.6f}'+' EV a nebola uzamknutá. Vytvorené Nanite dáta samy nepotvrdzujú použitý renderovací priechod.</footer>',text)
    assert 'R21' not in text and 'R16' not in text
    page.write_text(text)
    receipt={'schemaVersion':1,'owner':OWNER,'status':'actual-matched-editor-pair-reviewed-partial-visual-gain-full-no-go',
        'producer':pin(ROOT/OWNER),'htmlStyleTemplate':pin(template),'baselineSuite':pin(BEFORE),'candidateSuite':pin(AFTER),
        'baselineNativeReport':pin(ROOT/'output/unreal/exterior-20261002-r22c/realism-integration-native-report-r3.json'),
        'candidateNativeReport':pin(ROOT/'output/unreal/exterior-20261002-r24b/original-tree-native-report-r2.json'),
        'sourceAudit':pin(ROOT/'output/unreal/exterior-original-tree-20261002-r24-editor-r12-source-audit/cpu-native-source-audit.json'),
        'baseline':{'revision':'R22c','pid':53435,'originalPng':pin(x['originalCapturePath']),'originalRuntime':pin(x['originalRuntimePath']),'process':pin(x['processReceiptPath'])},
        'candidate':{'revision':'R24b','pid':63230,'originalPng':pin(y['originalCapturePath']),'originalRuntime':pin(y['originalRuntimePath']),'process':pin(y['processReceiptPath'])},
        'comparisonHtml':pin(page),'pairChecks':{'sameImmediateNativeBase':True,'sourceCameraExact':True,'observedCameraExact':True,'renderSettingsExact':True,
            'pixels':[1920,1080],'rhi':'Metal','shaderPlatform':'METAL_SM6','warmupFrames':2400,'benchmarkFrames':300,
            'sourceInputsUnchangedBoth':True,'nativeFovDirectReadbackAvailable':False,'originalPngsEdited':False},
        'exposure':{'mode':'automatic-unlocked','beforeEV':evb,'afterEV':eva,'deltaEV':delta,'fixedExposureComparison':False},
        'visualFindings':{'boundedVisibleGain':True,'gain':['Selected central tree has visible forked limbs and varied bark.',
            'Irregular airy crown and finer leaf clusters replace the old nearly continuous dark crown.'],
            'limits':['Sparse new tree differs from surrounding dense repeated crowns; no ecological fit established.',
                'Repeated background trees, flat green foreground, simple repeating herbs and generic houses remain.',
                'Only this close camera was reviewed; no all-view or whole-scene appearance claim.']},
        'geometryEvidenceLimits':{'sourceDescriptionTriangles':2062487,'sampledNativeTriangles':4096,'unsampledNativeTriangles':2058391,
            'nativeFallbackTriangles':2247,'nativeFallbackSections':3,'naniteResourceInputTriangles':2062487,'naniteResourceInputVertices':1777276,
            'actualPerMeshNaniteRenderPassObserved':False,'rNaniteConsoleValueBoth':1,'fullNativeCornerReadbackPerformed':False,'nativeNormalTangentReadbackAvailable':False},
        'editorTimingObservation':{'baseline':x['observed']['frameIntervalFacts'],'candidate':y['observed']['frameIntervalFacts'],
            'baselineFocus':x['observed']['foregroundTimingFacts'],'candidateFocus':y['observed']['foregroundTimingFacts'],'performanceAccepted':False},
        'shaderReadiness':{'errorsBoth':[],'pendingShaderCountAtCaptureObserved':False,'noErrorLogIsFullReadinessProof':False},
        'browserVerifiedByThisReview':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,
        'shippingVerified':False,'packageVerified':False,'activeSelectorPromotionApproved':False,'goNoGo':'PARTIAL_VISUAL_GAIN_ONE_TREE; FULL_REALISM_NO_GO'}
    audit.write_text(json.dumps(receipt,indent=2,allow_nan=False)+'\n')
    print(json.dumps({'audit':pin(audit),'html':pin(page),'deltaEV':delta,'originalImagesUnchanged':True}))


if __name__=='__main__':main()
