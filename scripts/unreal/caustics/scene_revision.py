"""Generate a pre-build scene identity; accept numerical evidence only after capture.

The receiver/water resource describes a retained geometric submodel. The current
scene and its walking provenance have their own identity. Neither is relabelled.
"""
from pathlib import Path
import hashlib, importlib.util, json, re

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'lib/twin-site.ts').is_file())
PRIVATE = 'Plugins/BreziCausticsProbe/Source/BreziCausticsProbe/Private'
RESOURCES = 'Plugins/BreziCausticsProbe/Resources'
LEGACY_PAIR = 'edc8d3d6d8113cff291d257ef76f3857ff017efd039ce6b12c6178d114577f5e'

def need(v,m):
    if not v: raise ValueError(m)
def sha(p,kind='sha256'):
    p=Path(p).absolute();need(p.resolve()==p and p.is_file() and not p.is_symlink(),'Missing/linked file: '+str(p))
    return hashlib.new(kind,p.read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def encode(v): return (json.dumps(v,ensure_ascii=False,indent=2,allow_nan=False)+'\n').encode()
def checks(pins):
    need(bool(pins),'Empty input closure')
    for p,h in pins.items():need(sha(p)==h,'Changed input: '+str(p))

def source_pins(relative):
    result={}
    for name,h in relative.items():
        p=ROOT/name
        need(not Path(name).is_absolute() and '..' not in Path(name).parts and p.resolve()==p and p.is_relative_to(ROOT),'Source pin escapes workspace')
        result[str(p)]=h
    return result

def header(a,authority_sha='',legacy_pair=LEGACY_PAIR):
    fields={'AuthoritySha256':authority_sha,'LegacyEditorPairSha256':legacy_pair,
        'CurrentSceneSha256':a['sceneSha256'],'CurrentObjSha256':a['objSha256'],
        'ReceiverOriginSceneSha256':a['receiverOriginSceneSha256'],'ReceiverOriginObjSha256':a['receiverOriginObjSha256'],
        'BindingSha256':a['bindingSha256'],'BindingSha1':a['bindingSha1'],
        'MapSha256':a['mapSha256'],'WaterSha256':a['waterBindingSha256'],
        'TransportSha256':a['transportSha256'],'TransportSha1':a['transportSha1'],
        'DeliverySha256':a['deliverySha256'],'DeliverySha1':a['deliverySha1']}
    for k,v in fields.items():
        need((k in {'AuthoritySha256','LegacyEditorPairSha256'} and v=='') or re.fullmatch('[0-9a-f]{'+('40' if k.endswith('Sha1') else '64')+'}',v),'Invalid generated identity: '+k)
    return '#pragma once\n// Generated pre-build source identities. Numerical capture/pair evidence is post-build.\n#include "CoreMinimal.h"\nnamespace BreziSceneRevision\n{\n'+''.join(
        'inline constexpr const TCHAR* '+k+' = TEXT("'+v+'");\n' for k,v in fields.items())+'}\n'

def verify_hidden_collision(project,binding,hidden_collision):
    """Reuse the original pure source reader and join unchanged saved native hulls."""
    project=Path(project).absolute();path=Path(hidden_collision).absolute();directory=path.parent
    need(path.name=='hidden-collision.json' and path.resolve()==path,'Use the exact exported hidden-collision.json path')
    scene_path=directory/'scene.json';scene=read(scene_path)
    need(sha(scene_path)==binding['sourceSceneSha256'] and sha(directory/'dom-mm.obj')==binding['sourceObjSha256'],
         'Hidden collision export belongs to another scene/OBJ')
    reader_path=ROOT/'scripts/unreal/hidden_collision.py'
    spec=importlib.util.spec_from_file_location('brezi_revision_hidden_collision',reader_path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    contract,records,triangles=module.verify_inputs(scene,directory) # CPU only; this API never authors/saves.
    sources=[ROOT/name for name,h in binding['sourceFileHashes'].items() if h==binding['importReportSha256']]
    need(len(sources)==1,'Historical import path is ambiguous')
    historical_path=sources[0];need(sha(historical_path)==binding['importReportSha256'],'Historical import changed')
    historical=read(historical_path)['hiddenCollision']
    need(historical['status']=='hidden-collision-saved-reloaded-validated'
         and historical['verification']['savedReloaded'] is True and historical['verification']['nativeTrianglesMeasured'] is True,
         'Historical hidden saved geometry proof absent')
    need(len(records)==historical['objectCount']==57 and sum(map(len,triangles.values()))==historical['triangleCount']==684
         and len(historical['assetHashes'])==58,'Hidden collision scope changed')
    old_sources=[ROOT/name for name,h in binding['sourceFileHashes'].items() if h==historical['sourceManifestSha256']]
    need(len(old_sources)==1,'Historical source scene is ambiguous')
    old_dir=old_sources[0].parent;old_path=old_dir/'hidden-collision.json';old_capture=old_dir/'hidden-collision-source.json'
    need(sha(old_path)==historical['sourceContractSha256'] and sha(old_capture)==historical['sourceCaptureSha256'],
         'Historical hidden source changed')
    old=read(old_path)
    provenance={'sourceManifestSha256','mainObjSha256','sourceCaptureSha256'}
    need({k:v for k,v in contract.items() if k not in provenance}=={k:v for k,v in old.items() if k not in provenance},
         'Hidden collider records, geometry or policy changed')
    capture=read(directory/'hidden-collision-source.json');prior_capture=read(old_capture)
    need({k:v for k,v in capture.items() if k!='mainObjSha256'}=={k:v for k,v in prior_capture.items() if k!='mainObjSha256'},
         'Hidden source capture geometry or metadata changed')
    need(contract['supplementSha256']==historical['sourceGlbSha256'],'Hidden GLB differs from saved native proof')
    old_installed=project/'Content/Data/hidden-collision.json'
    need(sha(old_installed) in {historical['sourceContractSha256'],sha(path)},'Installed hidden manifest has unreviewed origin')
    native_assets={}
    for name,h in historical['assetHashes'].items():
        need(name.startswith('unreal/BreziTwin/Content/Brezi/HiddenCollision/') and name.endswith('.uasset')
             and '..' not in Path(name).parts,'Foreign hidden collision asset')
        rel=name.removeprefix('unreal/BreziTwin/')
        need(sha(project/rel)==h,'Saved hidden collision asset changed: '+rel);native_assets[rel]=h
    inputs=[path,scene_path,directory/'dom-mm.obj',directory/'hidden-collision-source.json',directory/'brezi-collision-only.glb',
            reader_path,historical_path,old_path,old_capture,old_sources[0]]
    # verify_inputs checked these source-writer pins; retain them in the new authority.
    inputs.extend(ROOT/name for name in ('scripts/unreal/hidden-collision-export.mjs','scripts/archviz/scene-export.ts','scripts/archviz/export.mjs'))
    pins={str(p.relative_to(ROOT)):sha(p) for p in inputs}
    return {'sha256':sha(path),'sourceFileHashes':pins,'assetFileHashes':native_assets,
            'proof':{'colliders':57,'triangles':684,'savedAssetFiles':58,'sourceRecordsAndCaptureUnchanged':True,
                     'sourceSupplementBytesUnchanged':True,'savedAssetsByteEqual':True,
                     'nativeCollisionQueriesReexecuted':False,'nativeWorldValidationPending':True}}

def generate(project,binding,walking,hidden_collision,output):
    project,binding,walking,hidden_collision,output=[Path(p).absolute() for p in (project,binding,walking,hidden_collision,output)]
    need(all(p.resolve()==p for p in (project,binding,walking,hidden_collision,output)),'Linked path')
    need('.brezi-managed' in project.parts and (project/'BreziTwin.uproject').is_file(),'Use an isolated project')
    need(not output.exists() and output.parent.is_dir() and not output.is_relative_to(project),'Choose a new external report')
    b=read(binding);resources=project/RESOURCES
    need(b['receiverObjectCount']==45 and b['receiverTriangleCount']==1076 and len(b['objects'])==46 and len(b['assetFileHashes'])==55,'Optical scope changed')
    need(b['mapPackage']=='/Game/Brezi/Maps/Brezi' and sha(project/'Content/Brezi/Maps/Brezi.umap')==b['mapSha256'],'Map is not the reviewed native revision')
    checks(source_pins(b['sourceFileHashes']))
    checks({str(project/p):h['sha256'] for p,h in b['assetFileHashes'].items()})
    receiver=read(resources/'receiver-contract.json');water=read(resources/'active-water-binding.json')
    need(sha(resources/'receiver-contract.json')==b['receiverContractSha256'] and sha(resources/'active-water-binding.json')==b['activeWaterBindingSha256'],'Frozen optical resources changed')
    old_walk=read(project/'Content/Data/walking.json');new_walk=read(walking)
    need({k:v for k,v in old_walk.items() if k!='provenance'}=={k:v for k,v in new_walk.items() if k!='provenance'},'This revision changes walking constraints; independently adopt them first')
    need(new_walk['provenance']['sceneSha256']==b['sourceSceneSha256'] and new_walk['provenance']['sourceObjSha256']==b['sourceObjSha256'],'New walking provenance differs')
    hidden=verify_hidden_collision(project,b,hidden_collision)
    need(hidden_collision.parent==walking.parent,'Walking and hidden collision must use the same export directory')
    providers={}
    for name in ('transport-provider.json','delivery-provider.json'):
        p=read(resources/name)
        need(p['receiverContractSha256']==b['receiverContractSha256'] and p['waterBindingSha256']==b['activeWaterBindingSha256'],'Provider optical resource differs')
        p.update(sceneSha256=b['sourceSceneSha256'],sourceObjSha256=b['sourceObjSha256'],sceneBindingSha256=sha(binding))
        providers[name]=encode(p)
    identity={'schemaVersion':1,'status':'pre-build-source-scene-revision',
        'sceneSha256':b['sourceSceneSha256'],'objSha256':b['sourceObjSha256'],
        'receiverOriginSceneSha256':receiver['sourceSha256']['output/unreal/geometry/scene.json'],
        'receiverOriginObjSha256':receiver['sourceSha256']['output/unreal/geometry/dom-mm.obj'],
        'receiverContractSha256':b['receiverContractSha256'],'waterBindingSha256':b['activeWaterBindingSha256'],
        'bindingSha256':sha(binding),'bindingSha1':sha(binding,'sha1'),'mapSha256':b['mapSha256'],'walkingSha256':sha(walking),
        'hiddenCollisionSha256':hidden['sha256'],'hiddenCollisionSourceFileHashes':hidden['sourceFileHashes'],
        'hiddenCollisionAssetHashes':hidden['assetFileHashes'],'hiddenCollisionProof':hidden['proof'],
        'transportSha256':hashlib.sha256(providers['transport-provider.json']).hexdigest(),'transportSha1':hashlib.sha1(providers['transport-provider.json']).hexdigest(),
        'deliverySha256':hashlib.sha256(providers['delivery-provider.json']).hexdigest(),'deliverySha1':hashlib.sha1(providers['delivery-provider.json']).hexdigest(),
        'receiverCount':45,'waterCount':1,'opticalAssetCount':55,'nativeTransportAccepted':False,
        'requiredAdditionalPackages':b.get('sourceRevision',{}).get('requiredAdditionalPackages',{}),
        'generatorSha256':sha(__file__)}
    need(len(identity['requiredAdditionalPackages'])==3,'This reviewed revision must bind three new deck packages')
    for rel,h in identity['requiredAdditionalPackages'].items():
        need(rel.startswith('Content/Brezi/MaterialStudies/DeckGap/') and rel.endswith('.uasset') and '..' not in Path(rel).parts,'Invalid extra package')
        need(sha(project/rel)==h,'Changed new deck package')
    checks(source_pins(hidden['sourceFileHashes']));checks({str(project/p):h for p,h in hidden['assetFileHashes'].items()})
    data=encode(identity);authority_sha=hashlib.sha256(data).hexdigest()
    generated={resources/'scene-revision.json':data,resources/'transport-scene-binding.json':binding.read_bytes(),
        project/PRIVATE/'BreziSceneRevision.h':header(identity,authority_sha,'').encode(),project/'Content/Data/walking.json':walking.read_bytes(),
        project/'Content/Data/hidden-collision.json':hidden_collision.read_bytes()}
    generated.update({resources/name:data for name,data in providers.items()})
    before={str(p):sha(p) if p.exists() else None for p in generated}
    for p,data in generated.items():p.write_bytes(data)
    result={'status':'source-scene-revision-generated-build-and-capture-pending','project':str(project),
        'authoritySha256':authority_sha,'authority':str(resources/'scene-revision.json'),'binding':str(resources/'transport-scene-binding.json'),
        'before':before,'fileHashes':{str(p):sha(p) for p in generated},'nativeTransportAccepted':False,'packagedAppContainsRevision':False}
    output.write_bytes(encode(result));return result

def check_pair(identity_path,expected_authority,binding_path,pair_path,expected_pair,project):
    """Join two actual captures to immutable pre-build inputs, before any cook."""
    project=Path(project).absolute();identity_path=Path(identity_path).absolute()
    need(sha(identity_path)==expected_authority and sha(pair_path)==expected_pair,'Source authority or accepted pair changed')
    a=read(identity_path);pair=read(pair_path)
    need(a['schemaVersion']==1 and a['status']=='pre-build-source-scene-revision','Unknown source authority')
    need((project/PRIVATE/'BreziSceneRevision.h').read_text()==header(a,expected_authority,''),'Compiled source revision header differs')
    need(sha(binding_path)==a['bindingSha256'],'Pair configured with another source binding')
    need(sha(project/'Content/Brezi/Maps/Brezi.umap')==a['mapSha256'] and sha(project/'Content/Data/walking.json')==a['walkingSha256'],'Current map/walking differs')
    hidden_pins={}
    if 'hiddenCollisionSha256' in a:
        hidden_path=project/'Content/Data/hidden-collision.json'
        need(sha(hidden_path)==a['hiddenCollisionSha256'],'Current hidden collision manifest differs')
        hidden_pins=source_pins(a['hiddenCollisionSourceFileHashes'])
        hidden_pins.update({str(project/p):h for p,h in a['hiddenCollisionAssetHashes'].items()})
        hidden_pins[str(hidden_path)]=a['hiddenCollisionSha256'];checks(hidden_pins)
    need(pair['status']=='two-phase-opaque-transport-readbacks-validated' and len(pair['proofs'])==2,'Fresh native pair absent')
    phases=set();pids=set();pins={str(identity_path):expected_authority,str(Path(pair_path).absolute()):expected_pair,**hidden_pins}
    for p,h in pair['proofs'].items():
        need(sha(p)==h,'Native phase proof changed');r=read(p);pins[p]=h
        need(r['status']=='opaque-scene-transport-and-composite-readback-validated' and r['sceneBindingSha256']==a['bindingSha256']
            and r['waterBindingSha256']==a['waterBindingSha256'] and r['transportContractSha256']==a['transportSha256'],'Native proof belongs to another scene or optical contract')
        need(r['scene']['matchedReceivers']==45 and r['scene']['matchedWater']==1,'Native geometry scope incomplete')
        need(r['inputHashes'].get(str(identity_path))==expected_authority,'Authority was not pinned by native capture and validator')
        for rel,expected in (('Content/Brezi/Maps/Brezi.umap',a['mapSha256']),('Content/Data/walking.json',a['walkingSha256'])):
            need(r['inputHashes'].get(str(project/rel))==expected,'Current scene was not captured')
        if 'hiddenCollisionSha256' in a:
            need(r['inputHashes'].get(str(project/'Content/Data/hidden-collision.json'))==a['hiddenCollisionSha256'],
                 'Hidden collision manifest was not pinned before capture')
        checks(r['inputHashes']);pins.update(r['inputHashes']);phases.add(r['requestedMaterialTimeSeconds']);pids.add(r['nativePid'])
    need(phases=={0,.125} and len(pids)==2,'Need two distinct current native phases')
    need(set(pair['requestedMaterialPhasesSeconds'])==phases and set(pair['nativePids'])==pids,'Paired native phases do not match the proofs')
    return a,pins

if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('project','binding','walking','hidden-collision','output'):p.add_argument('--'+name,required=True)
    result=generate(**vars(p.parse_args()))
    print(json.dumps({k:result[k] for k in ('status','authority','authoritySha256')},indent=2))
