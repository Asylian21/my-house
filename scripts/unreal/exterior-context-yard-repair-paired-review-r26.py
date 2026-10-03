"""Review only the closed R32R23/R35R26 original PNG pair; write fresh JSON/HTML.

No Unreal, altered images, crops, exposure normalization or performance verdict.
Candidate identity and independent visual observations are finalized after capture.
"""
import datetime
import hashlib
import html
import json
from pathlib import Path
import struct
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-yard-repair-paired-review-r26.py'
V = ROOT/'output/unreal/exterior-validation-20260930-r1'
BASELINE = V/'qa/editor-pilot-r32a-yard-close-candidate-r23-1790925017474-O2kB4F/editor-pilot-suite.json'
CANDIDATE = V/'qa/editor-pilot-r35b-yard572063-repair-r26-1790937844652-UluAfx/editor-pilot-suite.json'
OUTPUT = V/'r35b-yard-repair-r26-review-r1'
VIEW = 'exterior-context-yard-572063-close-r18'
BASELINE_SHA = '8b5363e2cf70a0d8dfc78967b4079fda881fe9bcadb6258c73c34354000af599'
CANDIDATE_SHA = 'ca89bf4eee78d176bd497f4063ee9e88aa8f3408c9bf7c5c383de3cd23415748'
CANDIDATE_PID = 42228
VISUAL_OBSERVATIONS = [
    'Zelený vnútorný obrys medzi časťami štrkového dvora už nie je viditeľný; sivý vstupný povrch pôsobí súvislejšie.',
    'Pôvodné širokolisté trsy a tenké stonky, ktoré boli v prednom štrkovom povrchu, v novom zábere na tejto ploche nevidieť. Rastliny mimo pevných plôch zostali viditeľné.',
    'Na zelenom podklade mimo štrku je viditeľná výraznejšia jemná farebná a textúrna variácia. Ide o spoločný výsledok troch úprav; jednotlivý pixelový účinok materiálu týmto párom neizolujeme.',
    'Vonkajší prechod sivého štrku do zeleného podkladu stále sleduje ostré hranaté obrysy. Jemná geometrická deliaca línia v sivej ploche je naďalej rozpoznateľná.',
    'Predný slamový podklad zostáva plochý a výrazný; nízke rastliny sú riedke a opakujú sa. Fasády, okná a veľké rovné plochy okolo domov pôsobia jednoducho.',
    'V tomto pohľade je preukázaný čiastočný prínos opravy dvora. Celé prostredie stále nespĺňa požiadavku nerozoznateľnosti od reality.',
]
BOUNDED_VISIBLE_GAIN = True


def require(ok, message):
    if not ok: raise RuntimeError(message)
def read(path): return json.loads(Path(path).read_text())
def pin(path):
    p = Path(path).resolve();h = hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return {'path':str(p),'sha256':h.hexdigest(),'bytes':p.stat().st_size}
def fixed(path, sha):
    row = pin(path);require(row['sha256'] == sha,'Actual fixed receipt changed: '+str(path));return row
def write(path, row):
    with Path(path).open('x') as f:json.dump(row,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')


def difference(a, b, prefix=''):
    if type(a) is not type(b):return [{'path':prefix,'before':a,'after':b}]
    if isinstance(a,dict):
        result=[]
        for key in sorted(set(a)|set(b)):
            p=prefix+'.'+key if prefix else key
            if key not in a or key not in b:result.append({'path':p,'before':a.get(key),'after':b.get(key),'presenceChanged':True})
            else:result.extend(difference(a[key],b[key],p))
        return result
    if isinstance(a,list):
        if len(a)!=len(b):return [{'path':prefix,'before':a,'after':b}]
        return [row for i,(x,y) in enumerate(zip(a,b)) for row in difference(x,y,prefix+'['+str(i)+']')]
    return [] if a==b else [{'path':prefix,'before':a,'after':b}]


def closed_case(path, expected_sha, pid):
    suite_pin=fixed(path,expected_sha);suite=read(path)
    require(suite['status']=='editor-game-suite-recorded-awaiting-independent-visual-review'
            and suite['errors']==[] and suite['sourceInputsUnchanged'] is True
            and suite['requestedViews']==[VIEW] and len(suite['cases'])==1,'Closed unchanged one-view Editor suite required')
    case=suite['cases'][0];process=read(case['processReceiptPath'])
    require(case==process and case['outcome']=={'code':0,'signal':None,'pid':pid}
            and case['view']==VIEW and case['nativeEvidenceValidated'] is True
            and case['sourceFovNativeReadbackAvailable'] is False and case['shaderAndLoadErrors']==[],
            'Actual process0/camera/error proof differs')
    image=fixed(case['originalCapturePath'],case['originalCaptureSha256'])
    runtime_pin=fixed(case['originalRuntimePath'],case['originalRuntimeSha256']);runtime=read(runtime_pin['path'])
    raw=Path(image['path']).read_bytes()[:24]
    require(raw[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',raw[16:24])==(1920,1080), 'Original1920x1080 PNG required')
    require(runtime['processId']==pid and runtime['status']=='capture-complete'
            and runtime['activeView']==VIEW and runtime['buildConfiguration']=='Development'
            and runtime['rhi']=='Metal' and runtime['shaderPlatform']=='METAL_SM6'
            and runtime['screenshotPixels']==[1920,1080] and runtime['screenshotSaved'] is True
            and runtime['screenshotKind']=='current-scene-render-target-preserving-view-history'
            and runtime['warmupFrames']==2400 and runtime['requestedBenchmarkFrames']==300,
            'Actual native capture/render transport differs')
    before,after=read(suite['inputClosureBefore']['path']),read(suite['inputClosureAfter']['path'])
    require(before==after and len(before)==suite['inputClosureBefore']['fileCount']==suite['inputClosureAfter']['fileCount'],
            'Recorded runtime pre/post source closure differs')
    bp=fixed(suite['inputClosureBefore']['path'],suite['inputClosureBefore']['sha256'])
    ap=fixed(suite['inputClosureAfter']['path'],suite['inputClosureAfter']['sha256'])
    require(bp['sha256']==ap['sha256'],'Before/after closure artifact bytes differ')
    return {'suite':suite_pin,'case':case,'process':pin(case['processReceiptPath']),'originalPng':image,'originalRuntime':runtime_pin,
            'runtime':runtime,'sourceClosureBefore':bp,'sourceClosureAfter':ap,'recordedSourceClosureFiles':len(before),
            'stdout':pin(case['stdoutPath']),'runtimeLog':pin(case['runtimeLogPath'])},suite


def static_pp(pp):
    # These are observation counters and exposure/jitter samples, not PP settings.
    result={k:v for k,v in pp.items()if k not in ('observedMainViews','viewFamilyFrameNumber','renderThreadPreExposure','renderThreadAntiAliasing')}
    aa=pp['renderThreadAntiAliasing']
    result['renderThreadAntiAliasing']={k:v for k,v in aa.items()if k not in
        ('observedRenderThreadSamples','viewFamilyFrameNumber','projectionJitterX','projectionJitterY')}
    return result


def page(before,after,comparison):
    def src(row):return quote(Path(row['originalPng']['path']).relative_to(V).as_posix(),safe='/')
    images=[('../'+src(before),'Pred · R32','Pôvodný zelený obrys a rastliny na štrku'),
            ('../'+src(after),'Po · R35','Oprava obrysu, pôvodných trsov a lokálnej odozvy terénu')]
    ev=comparison['exposure'];parts=[]
    for url,label,description in images:
        parts.append('<figure><figcaption><strong>'+html.escape(label)+'</strong><span>'+html.escape(description)+'</span></figcaption>'
                     '<a href="'+url+'" target="_blank" rel="noopener"><img src="'+url+'" alt="'+html.escape(label)+' · pôvodná snímka Unreal Engine"></a>'
                     '<a class="original" href="'+url+'" target="_blank" rel="noopener">Otvoriť pôvodný PNG 1920 × 1080</a></figure>')
    observations=''.join('<li>'+html.escape(s)+'</li>'for s in VISUAL_OBSERVATIONS)
    return '''<!doctype html><html lang="sk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Dvor · pôvodné snímky R32 → R35</title><style>
*{box-sizing:border-box}body{margin:0;background:#10171d;color:#eef2f0;font:16px/1.55 system-ui,sans-serif}main{max-width:1800px;margin:auto;padding:34px 24px}h1{font-size:clamp(25px,3vw,40px);line-height:1.15;margin:0 0 12px}p{max-width:1050px;color:#cbd7d5}.pair{display:grid;grid-template-columns:1fr 1fr;gap:18px;margin:28px 0}figure{margin:0;border:1px solid #334640;background:#17231e;border-radius:12px;overflow:hidden}figcaption{padding:15px 18px}figcaption strong,figcaption span{display:block}figcaption span{font-size:14px;color:#b6c8be}img{display:block;width:100%;height:auto}.original{display:block;padding:12px 18px;color:#b8e8cc}a{color:#b8e8cc}section{max-width:1150px}li{margin:.6em 0}code{font-size:.9em}footer{margin-top:28px;padding:18px 0;border-top:1px solid #334640;color:#cbd7d5;font-size:14px}@media(max-width:900px){.pair{grid-template-columns:1fr}main{padding:24px 14px}}</style>
<main><h1>Dvor: čistejší štrk a súvislý vstup</h1>
<p>Priame pôvodné snímky z rovnakej kamery. R35 odstraňuje iba 34 pôvodných trsov zasahujúcich do pevných povrchov, upravuje krytie dvoch štrkových plôch a odozvu jedného terénneho materiálu. Osadenie domu, vstupy, záhony a 13 kríkov zostali zachované.</p>
<p>Unreal Editor Development · Metal SM6 · 1920 × 1080 · 2 400 zahrievacích a 300 meraných snímok · umelecká úprava okolia bez tvrdenia geodetickej presnosti.</p>
<div class="pair">'''+''.join(parts)+'''</div><section><h2>Pozorovanie pôvodných snímok</h2><ul>'''+observations+'''</ul>
<p>Automatická expozícia nebola uzamknutá. Pred: '''+f'{ev["beforeEV"]:.6f}'+''' EV; po: '''+f'{ev["afterEV"]:.6f}'+''' EV; rozdiel: '''+f'{ev["deltaEV"]:+.6f}'+''' EV. Snímky neboli zosvetľované, normalizované, orezané ani upravené. Všetky zaznamenané rozdiely kamery, svetla, postprocessu a renderu sú uvedené v <a href="paired-review.json">dôkazovom zázname</a>.</p>
<p>''' + ('Čiastočný viditeľný prínos v tomto pohľade.' if BOUNDED_VISIBLE_GAIN else 'Viditeľný prínos nie je v tomto pohľade dostatočne preukázaný.') + ''' Celková fotorealistickosť zostáva otvorená.</p></section>
<footer>Pohľad je kontrola jedného dvora. Výkon, Shipping, fotorealizmus celého prostredia ani ďalšie pohľady nie sú schválené. Súbory sú pôvodné výstupy Unreal Engine; ich zobrazenie sa iba prispôsobuje šírke stránky.</footer></main></html>'''


def main():
    require(CANDIDATE_PID is not None and isinstance(CANDIDATE_SHA,str) and isinstance(VISUAL_OBSERVATIONS,list)
            and VISUAL_OBSERVATIONS and type(BOUNDED_VISIBLE_GAIN)is bool,
            'Actual closed candidate identity and independently viewed original-image observations required')
    before,b=closed_case(BASELINE,BASELINE_SHA,16517);after,a=closed_case(CANDIDATE,CANDIDATE_SHA,CANDIDATE_PID)
    require(b['source']==str(ROOT/'output/unreal/exterior-20261002-r32a-yard-close-candidate-r23')
            and a['source']==str(ROOT/'output/unreal/exterior-20261002-r35b-yard-close-candidate-r26'), 'Known actual matched camera sources required')
    rb,ra=before['runtime'],after['runtime'];camera_diffs=difference(before['case']['sourceCamera'],after['case']['sourceCamera'])
    observed_diffs=difference(rb['walking']['presentationCamera'],ra['walking']['presentationCamera'])
    render_diffs=difference(rb['renderSettings'],ra['renderSettings']);light_diffs=difference(rb['lighting'],ra['lighting'])
    fixture_diffs=difference(rb['exteriorLighting'],ra['exteriorLighting']);pp_diffs=difference(rb['finalViewPostProcessSettings'],ra['finalViewPostProcessSettings'])
    evb=rb['finalViewPostProcessSettings']['renderThreadPreExposure']['exposureEV'];eva=ra['finalViewPostProcessSettings']['renderThreadPreExposure']['exposureEV']
    comparison={'sourceCameraExact':not camera_diffs,'observedCameraExact':not observed_diffs,'sourceCameraDifferences':camera_diffs,
        'observedCameraDifferences':observed_diffs,'renderSettingsDifferences':render_diffs,'renderSettingsExact':not render_diffs,
        'lightingStateDifferences':light_diffs,'exteriorFixtureDifferences':fixture_diffs,
        'fullPostProcessObservationDifferences':pp_diffs,'staticPostProcessSettingDifferences':difference(static_pp(rb['finalViewPostProcessSettings']),static_pp(ra['finalViewPostProcessSettings'])),
        'exposure':{'mode':'automatic-unlocked','beforeEV':evb,'afterEV':eva,'deltaEV':eva-evb,'fixedExposureComparison':False},
        'nativeFovDirectReadbackAvailable':False,'sourceHorizontalFovDegrees':before['case']['sourceCamera']['horizontalFovDegrees'],
        'originalPngsEdited':False,'matchedLightingGeometryAndMaterialCausalIsolationClaimed':False,
        'combinedScope':'34 original ecology retirements, 2 hard UV1.R coverage changes and 1 backdrop material coefficient change; no individual pixel-cause isolation.'}
    require(not camera_diffs and not observed_diffs,'Unmatched camera cannot be published as this fixed-view pair')
    artifacts=[fixed(ROOT/'output/unreal/exterior-20261002-r32a/context-yard-ground-native-report.json','99b80074fe1309ee951ea662cf42f75ecd6d0a2bc711f0c76cc5d34e18891a19'),
        fixed(ROOT/'output/unreal/exterior-20261002-r35b/context-yard-repair-native-report-r2.json','22f38c206686040bb8027b2f5cd7abc479ff2749a5edd78cafabed8191ecc7ed'),
        fixed(ROOT/'output/unreal/exterior-context-yard-20261002-r35-editor-r26-readiness-r1/editor-source-readiness.json','773e4ccd2669eb8d9e61157e42d8cebfe4fd6089ee96ee5eab8477a665336652')]
    OUTPUT.mkdir(parents=True,exist_ok=False)
    (OUTPUT/'index.html').write_text(page(before,after,comparison))
    receipt={'schema':'brezi-original-r32-r35-yard-repair-fixed-camera-paired-review-r26','schemaVersion':1,'owner':OWNER,
        'recordedAtUtc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'status':'actual-original-editor-pair-reviewed-full-realism-NO_GO',
        'producer':pin(ROOT/OWNER),'baseline':before,'candidate':after,'pairComparison':comparison,'inputNativeArtifacts':artifacts,
        'visualObservations':VISUAL_OBSERVATIONS,'boundedVisibleGain':BOUNDED_VISIBLE_GAIN,
        'independentReviewerViewedBothOriginalPngs':True,'originalPixelsModified':False,
        'allRuntimeSourceClosureFilesIndependentlyRehashedByThisReview':False,'recordedRuntimeBeforeAfterReceiptsChecked':True,
        'performance':{'baselineFocus':rb['focusDuringBenchmark'],'candidateFocus':ra['focusDuringBenchmark'],
            'baselineFrameInterval':rb['frameInterval'],'candidateFrameInterval':ra['frameInterval'],'performanceAccepted':False},
        'html':pin(OUTPUT/'index.html'),'browserVerifiedByThisProducer':False,
        'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,
        'shippingVerified':False,'packageVerified':False,'activeSelectorPromotionApproved':False}
    write(OUTPUT/'paired-review.json',receipt)
    (OUTPUT/'producer-source.py').write_bytes((ROOT/OWNER).read_bytes())
    write(OUTPUT/'artifact-receipt.json',{'owner':OWNER,'files':[pin(OUTPUT/f)for f in ['index.html','paired-review.json','producer-source.py']],
        'originalPngs':[before['originalPng'],after['originalPng']],'originalPixelsChanged':False})
    print(json.dumps({'review':pin(OUTPUT/'paired-review.json'),'html':pin(OUTPUT/'index.html'),'exposureDeltaEV':eva-evb}))


if __name__=='__main__':main()
