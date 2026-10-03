"""CPU review of four unchanged original R27/R28 captures; no Unreal or image edits."""
import hashlib
import html
import json
import math
from pathlib import Path
import re
import struct
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-yard-paired-review-r28.py'
OUT = ROOT/'output/unreal/exterior-validation-20260930-r1'
BEFORE = OUT/'qa/editor-pilot-r27a-clean-integration-r13-1790909195856-YzhP5f/editor-pilot-suite.json'
AFTER = OUT/'qa/editor-pilot-r28b-purposeful-yards-r16-1790911889414-cjzjUw/editor-pilot-suite.json'
TEMPLATE = OUT/'r22c-four-view-paired-review-r1.html'
AUDIT = OUT/'purposeful-context-yards-two-view-paired-review-r28-r1.json'
PAGE = OUT/'r28b-purposeful-yards-two-view-comparison-r1.html'
VIEWS = ['neighbor-finish-close-r18','exterior-parcels']
BASE_PIDS = [67825,67565]
NEW_PIDS = [72368,72591]
FINDINGS = [
 {'title':'Susedné dvory','visibleGain':True,
  'finding':'Pred dverami pribudla sivá prístupová plocha a vpredu dva hnedé záhony so štyrmi viditeľnými kríkmi. Priestor má čitateľnejšie využitie než pôvodná prázdna zelená plocha.',
  'limits':'Sivá plocha má ostré polygónové obrysy. Na jej okrajoch sú tmavé trojuholníky a drobné škvrny. Plochý zelený okolitý podklad, opakované kríky, procedurálne škridly a bledé ploché okná naďalej pôsobia počítačovo. Trasa k dverám je umelecký návrh, nie pozorovaný vstup alebo zameraný dvor.'},
 {'title':'Okolité parcely · kontrolný záber','visibleGain':False,
  'finding':'Po nezávislom prezretí oboch pôvodných PNG je široký pohľad vizuálne takmer nezmenený. Nové susedné záhony a cesty tu nie sú čitateľné.',
  'limits':'Pravidelná jemná tráva, opakované žlté porasty a plochý vzdialený mapový terén ostávajú. Zdrojovo nulový počet nových yard vrcholov vo fruste nie je dôkaz bitovo rovnakého obrazu; automatická expozícia sa mierne líši.'},
]


def read(p): return json.loads(Path(p).read_text())
def pin(p):
 p=Path(p).resolve();return {'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def verify_pin(row):
 actual=pin(row['path']);assert actual['sha256']==row['sha256'] and actual['bytes']==row['bytes'];return actual
def url(p): return quote(Path(p).resolve().relative_to(OUT).as_posix(),safe='/')


def case_proof(case,pid):
 assert case['outcome']=={'code':0,'signal':None,'pid':pid} and case['nativeEvidenceValidated'] is True
 assert not case['shaderAndLoadErrors'] and case['sourceFovNativeReadbackAvailable'] is False
 assert all(case[k] is False for k in ['shippingVerified','packageVerified','nativeAppearanceAccepted','performanceAccepted','fullPhotorealismAccepted'])
 png,runtime=pin(case['originalCapturePath']),pin(case['originalRuntimePath'])
 assert png['sha256']==case['originalCaptureSha256'] and runtime['sha256']==case['originalRuntimeSha256']
 raw=Path(png['path']).read_bytes();assert raw[:8]==b'\x89PNG\r\n\x1a\n' and struct.unpack('>II',raw[16:24])==(1920,1080)
 process=read(case['processReceiptPath']);assert process['outcome']==case['outcome'] and process['nativeEvidenceValidated'] is True
 assert process['originalCaptureSha256']==png['sha256'] and process['originalRuntimeSha256']==runtime['sha256']
 return {'pid':pid,'originalPng':png,'originalRuntime':runtime,'process':pin(case['processReceiptPath'])}


def suite_proof(suite,path,views,mode,native_sha):
 assert suite['status']=='editor-game-suite-recorded-awaiting-independent-visual-review' and suite['sourceInputsUnchanged'] is True and not suite['errors']
 assert suite['requestedViews']==[c['view'] for c in suite['cases']]==views
 assert suite['requestedBuild']=='Development' and suite['requestedTransport']=='UnrealEditor -game' and suite['requestedProfile']=='cinematic' and suite['requestedOutput']=='retina'
 evidence=suite['nativeSourceEvidence'];assert evidence['mode']==mode and evidence['nativeReceipt']['sha256']==native_sha
 native=verify_pin(evidence['nativeReceipt']);assert read(native['path'])['savedMapUnloadedReloaded'] is True
 a,b=verify_pin(suite['inputClosureBefore']),verify_pin(suite['inputClosureAfter']);assert a['sha256']==b['sha256'] and a['bytes']==b['bytes']
 closure=read(a['path']);assert closure==read(b['path']) and len(closure)==suite['inputClosureBefore']['fileCount']==suite['inputClosureAfter']['fileCount']
 return {'suite':pin(path),'nativeReport':native,'inputClosureBefore':a,'inputClosureAfter':b,'unchangedCapturedInputFileCount':len(closure),
         'closureFilesIdentical':True,'currentWholeInputClosureRehashedByThisReview':False,'nativeSummary':evidence['summary']}


def source_frustum_count(vertices,camera):
 eye=camera['eyeCm'];d=[b-a for a,b in zip(eye,camera['targetCm'])];length=math.sqrt(sum(v*v for v in d));f=[v/length for v in d]
 r=[f[1],-f[0],0];length=math.hypot(r[0],r[1]);r=[v/length for v in r]
 u=[r[1]*f[2]-r[2]*f[1],r[2]*f[0]-r[0]*f[2],r[0]*f[1]-r[1]*f[0]];tan=math.tan(math.radians(camera['horizontalFovDegrees']/2))
 count=0
 for p in vertices:
  d=[a-b for a,b in zip(p,eye)];z=sum(a*b for a,b in zip(d,f))
  count+=z>0 and abs(sum(a*b for a,b in zip(d,r)))<=z*tan and abs(sum(a*b for a,b in zip(d,u)))<=z*tan/(1920/1080)
 return count


def main():
 assert not AUDIT.exists() and not PAGE.exists(),'Fresh immutable review paths required'
 before,after=read(BEFORE),read(AFTER)
 bp=suite_proof(before,BEFORE,['exterior-canopy-close','exterior-parcels','neighbor-finish-close-r18','exterior-garden'],
  'saved-four-donor-clean-exterior-realism-integration','5575c0e37a9d48733b5c7ed3746f1731cc2b7958634a845c87b9700ff4fc9498')
 ap=suite_proof(after,AFTER,VIEWS,'saved-purposeful-context-yard-overlay','dfbca65515fc08aea52515195ab5ef752fe07cdca622cd41964e99875ced2456')
 native=read(ap['nativeReport']['path']);assert native['baseNativeReport']==bp['nativeReport'] and native['originalSavedR27Unchanged'] is True
 geometry_plan=verify_pin(native['sourceGeometryPlan']);plan=read(geometry_plan['path']);geometry=verify_pin(plan['geometry']);meshes=read(geometry['path'])['meshes']
 assert len(meshes)==4 and sum(len(m['verticesCm']) for m in meshes)==2191 and sum(len(m['indices'])//3 for m in meshes)==2969
 vertices=[v for m in meshes for v in m['verticesCm']]
 old_cases={c['view']:c for c in before['cases']};new_cases={c['view']:c for c in after['cases']};comparisons=[];cards=[]
 for i,view in enumerate(VIEWS):
  x,y=old_cases[view],new_cases[view];old,new=case_proof(x,BASE_PIDS[i]),case_proof(y,NEW_PIDS[i]);rb,ra=read(x['originalRuntimePath']),read(y['originalRuntimePath'])
  assert x['sourceCamera']==y['sourceCamera'] and x['observed']['actualCamera']==y['observed']['actualCamera']
  assert rb['renderSettings']==ra['renderSettings'] and rb['rhi']==ra['rhi']=='Metal' and rb['shaderPlatform']==ra['shaderPlatform']=='METAL_SM6'
  assert rb['screenshotPixels']==ra['screenshotPixels']==[1920,1080] and rb['warmupFrames']==ra['warmupFrames']==2400 and rb['requestedBenchmarkFrames']==ra['requestedBenchmarkFrames']==300
  assert rb['screenshotKind']==ra['screenshotKind']=='current-scene-render-target-preserving-view-history'
  ppb,ppa=rb['finalViewPostProcessSettings'],ra['finalViewPostProcessSettings'];different=[k for k in ppb if ppb[k]!=ppa[k]]
  assert set(ppb)==set(ppa) and different==['renderThreadPreExposure']
  evb,eva=ppb['renderThreadPreExposure']['exposureEV'],ppa['renderThreadPreExposure']['exposureEV']
  for c in (x,y):
   facts,focus=c['observed']['frameIntervalFacts'],c['observed']['foregroundTimingFacts']
   assert facts['status']=='measured' and facts['sampleCount']==focus['sampleCount']==300
   assert focus['gameWindowActiveSamples']==focus['sceneViewportKeyboardFocusSamples']==300 and focus['applicationForegroundSamples']==0
  in_frustum=source_frustum_count(vertices,x['sourceCamera']);assert in_frustum>0 if i==0 else in_frustum==0
  finding=FINDINGS[i];comparison={'view':view,'baseline':old,'candidate':new,'sourceCamera':x['sourceCamera'],'observedCamera':x['observed']['actualCamera'],
   'renderSettings':rb['renderSettings'],'composedPostProcessPolicy':{k:v for k,v in ppb.items() if k!='renderThreadPreExposure'},
   'pairChecks':{'sourceCameraExact':True,'observedCameraExact':True,'renderSettingsExact':True,'composedPostProcessExceptExposureExact':True,'postProcessDifferenceFields':different,
     'nativeFovDirectReadbackAvailable':False,'pixels':[1920,1080],'rhi':'Metal','shaderPlatform':'METAL_SM6','warmupFrames':2400,'benchmarkFrames':300},
   'exposure':{'mode':'automatic-unlocked','beforeEV':evb,'afterEV':eva,'deltaEV':eva-evb,'fixedExposureComparison':False},
   'sourceGroundFrustum':{'allSourceVerticesTested':2191,'sourceGroundVerticesInsideFrustum':in_frustum,'sourceOnly':True,'plantOcclusionVerified':False,'sourceZeroMeansPixelEquality':False},
   'visualFindings':finding,'editorTimingObservation':{'baseline':x['observed']['frameIntervalFacts'],'candidate':y['observed']['frameIntervalFacts'],
     'baselineFocus':x['observed']['foregroundTimingFacts'],'candidateFocus':y['observed']['foregroundTimingFacts'],'performanceAccepted':False},
   'shaderReadiness':{'errorsBoth':[],'pendingShaderCountAtCaptureObserved':False,'noErrorLogIsFullReadinessProof':False}}
  comparisons.append(comparison);title=html.escape(finding['title']);first,second=url(old['originalPng']['path']),url(new['originalPng']['path'])
  cards.append(f'''<section class="card" id="view-{i}"><div class="heading"><h2>{title}</h2><span>R27a → R28b</span></div><div class="compare" data-view="{view}"><img class="original" src="{first}" alt="Referenčný pôvodný PNG R27a: {title}"><img class="candidate" src="{second}" alt="Pôvodný PNG R28b: {title}"><div class="divider"></div><span class="tag before">R27a · pôvodný PNG</span><span class="tag after">R28b · pôvodný PNG</span></div><div class="controls"><button type="button" data-value="0">R27a</button><input type="range" min="0" max="100" value="50" aria-label="Podiel záberu R28b: {title}"><button type="button" data-value="100">R28b</button><output>50 % nový</output></div><div class="notes"><p><b>Čo vidno:</b> {html.escape(finding['finding'])}</p><p><b>Čo stále prekáža:</b> {html.escape(finding['limits'])}</p></div><details><summary>Kamera a skutočné merania</summary><p>Referenčný proces {BASE_PIDS[i]} / R28b {NEW_PIDS[i]} · oba exit 0 · Metal SM6 · 1920 × 1080 · 2 400 zahrievacích + 300 meraných snímok.</p><p>Zdrojová aj pozorovaná kamera, render a PP okrem automatickej expozície sú presne rovnaké. Priamy readback FOV chýba. Expozícia {evb:.6f} → {eva:.6f} EV (Δ {eva-evb:+.6f}), nebola uzamknutá.</p><p>Zdrojové vrcholy nových plôch vo fruste: {in_frustum}/2 191. Ide o zdrojovú kontrolu, nie o dokazovanie viditeľných pixelov alebo zakrytia. Interval snímok {x['observed']['frameIntervalFacts']['meanMs']:.3f} → {y['observed']['frameIntervalFacts']['meanMs']:.3f} ms, bez výkonnostného prijatia.</p><p><a href="{first}">PNG R27a</a> <code>{old['originalPng']['sha256']}</code><br><a href="{second}">PNG R28b</a> <code>{new['originalPng']['sha256']}</code></p></details></section>''')
 template=TEMPLATE.read_text();style=re.search(r'<style>(.*?)</style>',template,re.S).group(1);script=re.search(r'<script>(.*?)</script>',template,re.S).group(1)
 page=f'''<!doctype html><html lang="sk"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>R28b · pôvodné porovnanie susedných dvorov</title><style>{style}</style><header><div class="status">Čitateľnejšie dvory · ostré okraje zostávajú · plná fotorealistickosť NO_GO</div><h1>Susedné dvory R27a a R28b</h1><p class="intro">Dve zhodné kamery a štyri nezmenené pôvodné PNG z Unreal Engine. Nová prístupová plocha, záhony a kríky sú čitateľné v blízkom zábere domu. Široký pohľad na parcely je kontrolný a vizuálne takmer nezmenený. R28b vychádza zo skutočne uloženej R27a. Umelecká kompozícia nepreukazuje pozorované využitie pozemku, vstup ani meranú výšku terénu. Automatická expozícia sa mierne líši.</p><nav><a href="#view-0">Susedné dvory</a><a href="#view-1">Kontrolný pohľad na parcely</a></nav></header><main>{''.join(cards)}</main><footer><p>Všetky štyri pôvodné PNG boli nezávisle prezreté. Žiadny obrázok nebol upravený alebo vytvorený AI. Štyri nové plochy majú celkovo 2 969 trojuholníkov a zdroj navrhuje 13 kríkov; v tomto blízkom zábere sú čitateľné štyri. Tmavé trojuholníkové okraje, ostrá geometria, ploché zelené okolie, opakované kríky, procedurálna strecha a jednoduché okná zostávajú. Prínos rozloženia nie je celková akceptácia vzhľadu, výkonu ani Shipping.</p><a href="{AUDIT.name}">Presný pôvod, merania a obmedzenia</a></footer><script>{script}</script></html>'''
 PAGE.write_text(page)
 receipt={'schemaVersion':1,'owner':OWNER,'status':'actual-two-matched-editor-pairs-reviewed-purposeful-yards-full-no-go','producer':pin(ROOT/OWNER),
  'htmlStyleAndSliderTemplate':pin(TEMPLATE),'baseline':{'revision':'R27a',**bp},'candidate':{'revision':'R28b',**ap},'sourceGeometryPlan':geometry_plan,'sourceGroundGeometry':geometry,
  'comparisonHtml':pin(PAGE),'comparisons':comparisons,'comparisonScope':{'sameImmediateNativeBase':True,'reference':'Actual saved R27a is R28b base; same cameras/render settings.',
   'sourceNewYardGroundTriangles':2969,'sourceNewShrubRoots':13,'originalSceneActorsPreserved':5343,'allOriginalActorCounterfactualDeclaredByNative':True,
   'rootProducedNativeByteAuditRepeatedByThisReview':False,'landUseOrDoorObserved':False,'measuredElevation':False},
  'visualReview':{'originalImagesIndependentlyViewed':4,'pairedViews':2,'originalPngsEdited':False,'boundedVisibleGainViews':[VIEWS[0]],'almostUnchangedViews':[VIEWS[1]],
   'visibleShrubsInReviewedClose':4,'all13ShrubsVisuallyVerified':False,'pixelEqualityClaim':False,'allSceneViewAcceptance':False,'realisticGlazingVerified':False},
  'browserVerifiedByThisReview':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False,
  'activeSelectorPromotionApproved':False,'goNoGo':'BOUNDED_LAYOUT_GAIN_WITH_EDGE_ARTIFACTS; FULL_REALISM_NO_GO'}
 AUDIT.write_text(json.dumps(receipt,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
 print(json.dumps({'audit':pin(AUDIT),'html':pin(PAGE),'pairs':2,'images':4,'originalImagesUnchanged':True,'exposureDeltasEV':[p['exposure']['deltaEV'] for p in comparisons],
  'sourceGroundFrustumCounts':[p['sourceGroundFrustum']['sourceGroundVerticesInsideFrustum'] for p in comparisons]}))


if __name__=='__main__': main()
