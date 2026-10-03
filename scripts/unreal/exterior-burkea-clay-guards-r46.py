"""Selected R43b, five material slots and five owned packages; no geometry delta."""
import copy, hashlib, importlib.util, json, math, struct, sys
from pathlib import Path
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-burkea-clay-guards-r46.py'
NATIVE_OWNER = 'scripts/unreal/exterior-burkea-clay-native-r46.py'
SCHEMA = 'brezi-selected-r43b-burkea-and-clay-roof-material-native-r46'
CANDIDATE = ROOT/'output/unreal/exterior-20261002-r46a'
PROJECT = CANDIDATE/'Project/BreziTwin'
STUDY = ROOT/'output/unreal/exterior-burkea-clay-20261002-r46-native-study'
PLAN = STUDY/'combined-material-native-plan.json'
CLONE = CANDIDATE/'combined-material-project-clone-r46-r1.json'
CLONE_SHA = 'f05c88c14f37545b9675058870844b06eaef9c9de2790113d85ddd6980f65e3b'
DECISION = ROOT/'output/unreal/exterior-context-parcel-boundary-20261002-r43-image-base-selection-r1/root-image-base-selection-r1.json'
DECISION_SHA = '869013e1e2b564aee21532acabcd737d0b8dda2e6bd78357e487469d647974d3'
PACKET = ROOT/'scripts/unreal/exterior-burkea-clay-base-packet-r46.py'
PACKET_SHA = '32b866475c009efc8ca7020b09bb74139f991b536a40d431f69e0a3989cb9346'
ROOF = ROOT/'scripts/unreal/exterior-clay-roof-materials-r46.py'
ROOF_SHA = '8e3b4f973d5e9d21877a02a46366890c803969982792f1112e34d2b2722c6a78'
LEAF_KERNEL = ROOT/'scripts/unreal/exterior-burkea-transmission-native-r44-draft.py'
LEAF_KERNEL_SHA = 'a0254949cbe053368e67e5f3c7e0da788068c78471a3af5b6c8eebf460804d4a'
LEAF_MATH = ROOT/'scripts/unreal/exterior-burkea-transmission-draft-r44.py'
LEAF_MATH_SHA = '00860160d0c479cc84da5f89bf79646a8611fa123a1700596c495878cca8ec5f'
COUNTS = {'originalActors':5371,'savedActors':5371,'fullHismComponents':2329,
    'fullHismInstances':678205,'originalMaterialGraphs':72,'savedMaterialGraphs':74,
    'originalTextureObjects':114,'savedTextureObjects':117,'originalContentFiles':4139,
    'savedContentFiles':4144,'protectedFiles':132,'newMaterialGraphs':2,'newTextureObjects':3,
    'newPackages':5,'changedMaterialSlots':5,'newActors':0,'newMeshes':0}

def require(ok, message):
    if not ok: raise RuntimeError(message)
def read(path): return json.loads(Path(path).read_bytes())
def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',', ':'),allow_nan=False).encode()).hexdigest()
def pin(path):
    path=Path(path).resolve();return {'path':str(path),'sha256':sha(path),'bytes':path.stat().st_size}
def checked(row):
    require(type(row)is dict and set(row)=={'path','sha256','bytes'},'Exact immutable file pin required')
    p=Path(row['path']);require(p.is_absolute()and p.resolve()==p and not p.is_symlink()and pin(p)==row,'Consumed file changed: '+str(p));return p
def fixed(path, expected):
    require(sha(path)==expected,'Fixed selected source changed: '+str(path));return pin(path)
def module(name,path,expected=None):
    if expected is not None: fixed(path,expected)
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('x')as f:json.dump(value,f,indent=2,sort_keys=True,allow_nan=False);f.write('\n')
def exact(a,b,message):
    if isinstance(a,(int,float))and not isinstance(a,bool)and isinstance(b,(int,float))and not isinstance(b,bool):
        require(math.isfinite(a)and math.isfinite(b)and struct.pack('<d',float(a))==struct.pack('<d',float(b)),message)
    elif isinstance(a,(list,tuple))and type(a)is type(b):
        require(len(a)==len(b),message)
        for x,y in zip(a,b):exact(x,y,message)
    elif isinstance(a,dict)and isinstance(b,dict):
        require(set(a)==set(b),message)
        for k in a:exact(a[k],b[k],message)
    else:require(type(a)is type(b)and a==b,message)
def observer():return module('_r46_base_packet',PACKET,PACKET_SHA)
def leaf_math():return module('_r46_leaf_math',LEAF_MATH,LEAF_MATH_SHA)
def roof_contract():
    roof=module('_r46_roof_helper_contract',ROOF,ROOF_SHA);return roof.contract()
def expected_binding():
    p=observer();fixed(DECISION,DECISION_SHA);fixed(CLONE,CLONE_SHA)
    return {'schema':SCHEMA,'schemaVersion':1,'nativeOwner':NATIVE_OWNER,
        'selectedNativeReport':p.fixed(p.REPORT,p.REPORT_SHA),'selectedNativeProcess':p.fixed(p.PROCESS,p.PROCESS_SHA),
        'selectedRawProcess':p.fixed(p.RAW,p.RAW_SHA),'selectedCurrentByteAudit':p.fixed(p.AUDIT,p.AUDIT_SHA),
        'rootImageDecision':pin(DECISION),'projectClone':pin(CLONE),'candidateProject':str(PROJECT),
        'leafSourceProposal':p.fixed(p.LEAF_PROPOSAL,p.LEAF_SHA),'roofSourceProposal':p.fixed(p.ROOF_PROPOSAL,p.ROOF_SHA),
        'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,
        'shippingVerified':False,'activeOutputPromoted':False}
def require_native_binding(binding):
    require(digest(binding)==digest(expected_binding()),'Exact selected R43b/actual clone binding required');return True
def load_contract():
    p=observer();binding=expected_binding();source=p.load_sources();base=p.load_observed_base();decision=read(DECISION)
    require(decision['schema']=='brezi-r43b-root-image-base-selection-r1'and decision['schemaVersion']==1
        and decision['status']=='selected-saved-r43b-only-as-next-combined-leaf-and-clay-roof-material-pilot-base'
        and decision['sourceNativeReport']==base['reportPin']and decision['sourceNativeProcess']==base['processPin']
        and decision['sourceCurrentByteAudit']==base['auditPin']and decision['selectedNativeProcessId']==44798
        and decision['allFourOriginalPngsViewedByRoot']is True and decision['independentVisualPeerReceived']is True
        and decision['localBoundaryCueAcceptedForNextTrialOnly']is True,'Actual scoped four-original image decision required')
    for key in ('rootVisualReview','independentVisualReview'):checked(decision[key])
    for key in ('fullPhotorealismAccepted','performanceAccepted','shippingVerified','activeOutputPromoted'):
        require(decision[key]is False,'Selection does not imply full acceptance')
    bundle={'source':source,'base':base,'binding':binding};validate_clone_header(bundle)
    expected_counterfactual(base['savedWitness'],bundle);return bundle
def expected_packages(source):
    wanted=[source['leaf']['proposal']['proposedMaterial']['ownAsset'],*source['roof']['proposal']['proposedAssets'].values()]
    require(len(wanted)==len(set(wanted))==5,'Exactly two graphs and three original maps required');return sorted(wanted)
def expected_counterfactual(before,bundle):
    require(len(before)==5371 and digest(before)==bundle['base']['report']['savedActorWitnessSha256'], 'Full selected original witness required')
    leaf=leaf_math();historical=bundle['source']['leaf']['proposal']['historicalObservationOnly']
    require(digest(before[leaf.ACTOR])==historical['targetActorSha256'],'Exact historical leaf target held in selected R43b')
    result=leaf.expected_scene(before,before[leaf.ACTOR]);roof=roof_contract()
    result=roof.expected_counterfactual(result,bundle['source']['roof']['proposal'],bundle['source']['roof']['proposal']['proposedAssets']['material'])
    changed=sorted(k for k in before if digest(before[k])!=digest(result[k]))
    require(len(changed)==5 and set(result)==set(before),'Exactly five existing component slots, no actors or geometry');return result
def validate_clone_header(bundle):
    c=read(CLONE);b=bundle['base'];binding=bundle['binding']
    require(c['schema']=='brezi-image-selected-saved-r43b-combined-material-project-clone-r46'and c['schemaVersion']==1
        and c['status']=='verified-byte-identical-independent-apfs-image-selected-saved-r43b-before-five-slot-material-pilot-r46'
        and c['sourceImageSelection']==binding['rootImageDecision']and c['sourceNativeReport']==b['reportPin']
        and c['sourceNativeProcess']==b['processPin']and c['sourceCurrentByteAudit']==b['auditPin']
        and c['project']==str(PROJECT)and c['sourceProject']==str(b['project'])
        and c['nativeExecuted']is False and c['materialPilotPending']is True and c['nativeIdleAfter']==[], 'Actual independent pristine R46 clone required')
    expected={'Content/'+k:v for k,v in b['content'].items()};expected.update(b['protected']);seen=set()
    require(c['fileCount']==len(c['files'])==len(expected)==4271 and c['contentFiles']==4139 and c['protectedFiles']==132,'Initial 4271 project census required')
    for r in c['files']:
        dst=Path(r['destination']);rel=dst.relative_to(PROJECT).as_posix()
        require(rel not in seen and r['source']==str(b['project']/rel)and r['independentInodes']is True
            and {k:r[k]for k in ('sha256','bytes')}==expected[rel],'Exact initial source/candidate clone row required');seen.add(rel)
    require(seen==set(expected),'Closed initial clone scope required');return c
def inventories(project):
    rows={}
    for path in Path(project).rglob('*'):
        if not path.is_file():continue
        rel=path.relative_to(project).as_posix()
        if rel.split('/')[0]not in ('Content','Config','Source','Binaries')and rel!='BreziTwin.uproject':continue
        require(not path.is_symlink(),'No project symlink');rows[rel]={'sha256':sha(path),'bytes':path.stat().st_size}
    return {k[8:]:v for k,v in rows.items()if k.startswith('Content/')},{k:v for k,v in rows.items()if not k.startswith('Content/')}
def validate_content_delta(before,after,source):
    require(len(before)==4139 and len(after)==4144 and set(before)<=set(after),'Only five new packages permitted')
    changed=sorted(k for k in before if before[k]!=after[k]);require(changed==['Brezi/Maps/Brezi.umap'],'Only original map may change')
    new=sorted(set(after)-set(before));want=sorted(a.split('.')[0].replace('/Game/','')+'.uasset'for a in expected_packages(source))
    require(new==want,'Only declared five material/photo packages, no redirectors or geometry');return {'changedOriginalFiles':changed,'newRelativeFiles':new}
def validate_clone(bundle,after=False):
    clone=validate_clone_header(bundle);base=bundle['base'];original,original_protected=inventories(base['project']);content,protected=inventories(PROJECT)
    require(original==base['content']and protected==original_protected==base['protected'],'Canonical base bytes and protected132 unchanged')
    for row in clone['files']:require(Path(row['source']).stat().st_ino!=Path(row['destination']).stat().st_ino,'Independent cloned inodes required')
    if after:validate_content_delta(base['content'],content,bundle['source'])
    else:require(content==base['content'],'Pristine selected R43b project bytes required')
    return content
