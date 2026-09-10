#!/usr/bin/env python3
"""CPU-only before/seal join for an actual fresh cook and IoStore archive.
No Unreal, cook, archive, extraction, signing or source writes are performed.
"""
from pathlib import Path
import argparse,csv,hashlib,json,os,re,shlex,time
ROOT=next(p for p in Path(__file__).resolve().parents if (p/'lib/twin-site.ts').is_file())
BINDING=None; BINDING_SHA='af9cc202a4fb4a204a47f915e457f249e4180e43b1fc55bf105c02ae1b743737'
PAIR=None; PAIR_SHA='edc8d3d6d8113cff291d257ef76f3857ff017efd039ce6b12c6178d114577f5e'
REVISION=None
STATUS='native-delivery-exited-zero-and-drained'

def need(v,m):
    if not v:raise ValueError(m)
def digest(p,kind='sha256'):
    p=Path(p);need(p.is_absolute() and p.resolve()==p and p.is_file() and not p.is_symlink(),'Missing/linked file: '+str(p))
    h=hashlib.new(kind)
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def check(pins):
    need(bool(pins),'Empty source closure')
    for p,h in pins.items():need(digest(p)==h,'Changed input: '+p)
def save(p,r):
    p=Path(p).absolute();need(not p.is_symlink(),'Linked output');p=p.resolve()
    need(not p.exists() and p.parent.is_dir(),'Choose a new existing-parent output path')
    with p.open('x') as f:json.dump(r,f,indent=2,allow_nan=False);f.write('\n')
def tree(root):
    root=Path(root);need(root.is_dir() and root.resolve()==root,'Missing/linked tree: '+str(root));out={}
    for parent,ds,fs in os.walk(root):
        for n in ds+fs:need(not (Path(parent)/n).is_symlink(),'Linked tree entry')
        for n in fs:
            p=Path(parent)/n;out[str(p)]=digest(p)
    return out

def project_pins(project):
    pins={}
    for name in ('Source','Config','Build','Content'):
        if (project/name).is_dir():pins.update(tree(project/name))
    # Exact ordinary cooker output files are not authoring inputs.
    pins={p:h for p,h in pins.items() if not (Path(p).parent.name=='FileOpenOrder' and Path(p).name in ('EditorOpenOrder.log','CookerOpenOrder.log'))}
    for p in (project/'Plugins').rglob('*'):
        need(not p.is_symlink(),'Linked plugin input')
        if p.is_file() and ('Intermediate' not in p.parts) and ('Binaries' not in p.parts):pins[str(p)]=digest(p)
    p=project/'BreziTwin.uproject';pins[str(p)]=digest(p)
    return pins

def authority(project):
    need(BINDING is not None and PAIR is not None,'Call configure_authority with explicit reviewed evidence paths')
    if REVISION is not None:
        import scene_revision as sr
        a,pins=sr.check_pair(REVISION['path'],REVISION['sha256'],BINDING,PAIR,REVISION['pairSha256'],project)
        b=read(BINDING)
        need(project==Path(REVISION['project']),'Revision belongs to another project')
        for rel,h in b['sourceFileHashes'].items():
            p=ROOT/rel;need(digest(p)==h,'Authoritative source changed: '+rel);pins[str(p)]=h
        for rel,h in b['assetFileHashes'].items():
            p=project/rel;need(digest(p)==h['sha256'],'Optical source asset changed: '+rel);pins[str(p)]=h['sha256']
        for rel,h in a['requiredAdditionalPackages'].items():
            p=project/rel;need(digest(p)==h,'Additional runtime package changed: '+rel);pins[str(p)]=h
        need(digest(project/'Plugins/BreziCausticsProbe/Resources/transport-scene-binding.json')==a['bindingSha256'],'Compiled binding resource changed')
        return b,pins
    need(digest(BINDING)==BINDING_SHA and digest(PAIR)==PAIR_SHA,'Reviewed binding/pair changed')
    b=read(BINDING);pair=read(PAIR);pins={str(BINDING):BINDING_SHA,str(PAIR):PAIR_SHA}
    need(pair['status']=='two-phase-opaque-transport-readbacks-validated' and len(pair['proofs'])==2,'Accepted Editor pair missing')
    for p,h in pair['proofs'].items():
        need(digest(p)==h,'Editor proof changed');pins[p]=h;r=read(p)
        need(r['status']=='opaque-scene-transport-and-composite-readback-validated' and r['sceneBindingSha256']==BINDING_SHA
             and r['waterBindingSha256']==b['activeWaterBindingSha256'] and r['scene']['matchedReceivers']==45
             and r['scene']['matchedWater']==1,'Editor geometry/wave proof differs')
        # Native evidence stays immutable. Historical plugin build inputs may be
        # deliberately replaced by reviewed continuous code; they are not relabeled current.
        for n,h in r['nativeHashes'].items():
            q=Path(r['captureDirectory'])/n;need(digest(q)==h,'Editor native evidence changed');pins[str(q)]=h
    for rel,h in b['sourceFileHashes'].items():
        p=ROOT/rel;need(digest(p)==h,'Authoritative geometry/material source changed: '+rel);pins[str(p)]=h
    for rel,h in b['assetFileHashes'].items():
        p=project/rel;need(digest(p)==h['sha256'],'Cloned source asset differs: '+rel);pins[str(p)]=h['sha256']
    p=project/'Content/Brezi/Maps/Brezi.umap';need(digest(p)==b['mapSha256'],'Cloned map differs');pins[str(p)]=b['mapSha256']
    p=project/'Plugins/BreziCausticsProbe/Resources/transport-scene-binding.json';need(digest(p)==BINDING_SHA,'Compiled resource binding differs');pins[str(p)]=BINDING_SHA
    return b,pins

def configure_authority(binding,editor_pair):
    global BINDING,PAIR,REVISION
    # Paths are caller-owned; reviewed hashes remain fixed compiled contract constants.
    binding=Path(binding).absolute();pair=Path(editor_pair).absolute()
    need(digest(binding)==BINDING_SHA and digest(pair)==PAIR_SHA,'Reviewed authority bytes differ')
    BINDING=binding;PAIR=pair;REVISION=None

def configure_revision(authority_path,authority_sha256,binding,editor_pair,pair_sha256,project):
    """Explicit source revision plus two real post-build captures; no implicit fallback."""
    global BINDING,PAIR,REVISION
    import scene_revision as sr
    project=Path(project).absolute();binding=Path(binding).absolute();pair=Path(editor_pair).absolute()
    sr.check_pair(authority_path,authority_sha256,binding,pair,pair_sha256,project)
    BINDING=binding;PAIR=pair
    REVISION={'path':str(Path(authority_path).absolute()),'sha256':authority_sha256,'pairSha256':pair_sha256,'project':str(project)}

def identities():
    return {'sourceBindingSha256':digest(BINDING),'editorPairSha256':digest(PAIR),
        **({'sourceAuthoritySha256':REVISION['sha256']} if REVISION else {})}

def before(project,cook_output,output):
    project=Path(project).resolve();cooked=Path(cook_output).absolute()
    need(cooked.resolve()==cooked and not cooked.exists(),'Fresh cook output must not exist before launch')
    need(not (project/'Plugins/BreziCausticsProbe/Resources/cooked-runtime-binding.json').exists(),'Stale runtime receipt in source plugin')
    b,pins=authority(project)
    current=project_pins(project);pins.update(current)
    check(pins)
    r={'status':'before-fresh-cook-source-snapshot','projectRoot':str(project),'cookOutput':str(cooked),'cookOutputExisted':False,
       'createdUnixNs':time.time_ns(),**identities(),'sourcePins':pins,
       'projectSourcePins':current,'sourceAssetHashes':b['assetFileHashes'],'sourceMapSha256':b['mapSha256'],'sourceInputsChecked':len(pins),'generatorSha256':digest(Path(__file__).resolve())}
    save(output,r);return r

def closed(path,mode):
    path=Path(path).resolve();r=read(path)
    need(r['status']==STATUS and r['mode']==mode and r['nativeExitCode']==0 and r['errors']==[]
         and r['changedPinnedInputs']==[] and r['remainingOwned']==[],'Native '+mode+' did not close cleanly')
    need(Path(r['directory'])==path.parent,'Foreign native phase receipt')
    a=read(path.parent/'pins-before.json');z=read(path.parent/'pins-after.json');need(a and a==z,'Phase pins changed');check(z)
    for name in ('stdout.log','cook.log'):
        if name+'Sha256' in r:need(digest(path.parent/name)==r[name+'Sha256'],'Phase log changed')
    return r

def parse_response(path):
    out={}
    for line in Path(path).read_text(encoding='utf-8-sig').splitlines():
        a=shlex.split(line)
        if not a:continue
        need(len(a)>=2 and Path(a[0]).is_absolute(),'Malformed IoStore response')
        dest=a[1].replace('\\','/').removeprefix('../../../')
        need(dest not in out,'Duplicate IoStore destination');out[dest]=a[0]
    return out

def package_rows(csv_path,required):
    with Path(csv_path).open(encoding='utf-8-sig',newline='') as f:rows=[{k.strip():v.strip() for k,v in r.items()} for r in csv.DictReader(f,skipinitialspace=True)]
    out={}
    for package,relative in required.items():
        dest='BreziTwin/'+relative
        matches=[r for r in rows if r.get('Filename','').replace('\\','/').removeprefix('../../../')==dest and r.get('ChunkType')=='ExportBundleData']
        need(len(matches)==1,'Missing/duplicate actual container export: '+dest);r=matches[0]
        need(r['ContainerName']=='BreziTwin-Mac' and int(r['Size'])>0 and re.fullmatch('0x[0-9a-fA-F]{40}',r['Hash'])
             and re.fullmatch('[0-9a-fA-F]{24}',r['ChunkId']) and r['PackageName'] in ('',package),'Invalid native package/chunk entry')
        out[package]=r
    return out

def seal(snapshot,cook_receipt,archive_receipt,io_commands,io_response,listing_csv,listing_receipt,output):
    snapshot=Path(snapshot).resolve();s=read(snapshot);need(s['status']=='before-fresh-cook-source-snapshot' and s['cookOutputExisted'] is False,'No pre-cook snapshot')
    need(s['generatorSha256']==digest(Path(__file__).resolve()),'Generator changed after before snapshot')
    project=Path(s['projectRoot']);b,authority_pins=authority(project);check(s['sourcePins'])
    need(project_pins(project)==s['projectSourcePins'],'Project source/content additions, deletions or changes after snapshot')
    need(all(s['sourcePins'].get(k)==h for k,h in authority_pins.items()),'Authority absent from pre-cook snapshot')
    c=closed(cook_receipt,'cook');a=closed(archive_receipt,'archive');cooked=Path(s['cookOutput'])
    need(c['cookOutput']==a['cookOutput']==str(cooked) and a['cookReceipt']==str(Path(cook_receipt).resolve()),'Archive/cook lineage differs')
    need('-OutputDir='+str(cooked) in c['argv'] and '-run=Cook' in c['argv'] and '-TargetPlatform=Mac' in c['argv']
         and '-nullrhi' in c['argv'] and not any(x.lower().startswith('-iterat') for x in c['argv']),'Not declared fresh Mac cook')
    stdout=Path(c['directory'])/'stdout.log';born=stdout.stat().st_birthtime
    need(s['createdUnixNs']<=int(born*1e9),'Source snapshot was not before actual native cook log creation')
    need(all(x in a['argv'] for x in ('-skipbuild','-skipcook','-pak','-package','-archive','-CookOutputDir='+str(cooked))),'Unexpected archive input mode')
    cooked_manifest=Path(cook_receipt).resolve().parent/'cooked-files.json';old=read(cooked_manifest)
    actual={str(Path(p).relative_to(cooked)):h for p,h in tree(cooked).items()}
    need(old and all(actual.get(k)==h for k,h in old.items()) and set(actual)-set(old)<={'BreziTwin/Metadata/Crypto.json'},'Accepted cooked outputs changed')
    required={'/Game/'+p.removeprefix('Content/').rsplit('.',1)[0]:p for p in b['assetFileHashes']}
    required[b['mapPackage']]='Content/Brezi/Maps/Brezi.umap';need(len(required)==56,'Expected55 optical assets+map')
    additional=read(REVISION['path'])['requiredAdditionalPackages'] if REVISION else {}
    for rel in additional:
        package='/Game/'+rel.removeprefix('Content/').rsplit('.',1)[0]
        need(package not in required,'Additional runtime package overlaps optical scope');required[package]=rel
    response=Path(io_response).resolve();commands=Path(io_commands).resolve()
    command_rows=[shlex.split(x) for x in commands.read_text(encoding='utf-8-sig').splitlines() if x.strip()]
    need(any('-ResponseFile='+str(response) in x and '-ContainerName=BreziTwin-Mac' in x for x in command_rows),'Actual IoStore command does not name response/container')
    # Both response and command come from this successful UAT attempt, not hand-authored lists.
    run=Path(a['directory']);need(response.is_relative_to(run) and commands.is_relative_to(run),'IoStore response outside actual archive attempt')
    mappings=parse_response(response);cooked_assets={}
    for package,rel in required.items():
        p=cooked/'BreziTwin'/rel;need(mappings.get('BreziTwin/'+rel)==str(p),'IoStore input not current cooked package: '+package)
        stem=p.with_suffix('');parts=sorted(p.parent.glob(stem.name+'.*'));need(p in parts,'Cooked package absent')
        entries={str(q.relative_to(cooked)):digest(q) for q in parts if q.suffix in ('.uasset','.umap','.uexp','.ubulk','.uptnl')}
        need(entries and all(old.get(k)==h for k,h in entries.items()),'Cooked sidecar absent from original successful cook');cooked_assets[package]=entries
        for relpart in entries:
            if Path(relpart).suffix in ('.ubulk','.uptnl'):need(mappings.get(relpart)==str(cooked/relpart),'Cooked bulk sidecar absent from IoStore input')
    app=Path(a['appPath']);pakdir=app/'Contents/UE/BreziTwin/Content/Paks';container_pins=tree(pakdir)
    need(all(Path(p).parent==pakdir for p in container_pins),'Unexpected nested container directory')
    required_names={'BreziTwin-Mac.pak','BreziTwin-Mac.utoc','BreziTwin-Mac.ucas','global.utoc','global.ucas'}
    need(required_names<={Path(p).name for p in container_pins},'Incomplete standalone containers')
    listing=read(listing_receipt);csv_path=Path(listing_csv).resolve()
    need(listing['exitCode']==0 and listing['inputsBefore']==listing['inputsAfter']==container_pins
         and listing['outputSha256']==digest(csv_path) and '-Csv='+str(csv_path) in listing['argv']
         and '-ListContainer='+str(pakdir/'BreziTwin-Mac.utoc') in listing['argv'],'Actual fresh IoStore listing receipt differs')
    need(digest(listing['stdoutPath'])==listing['stdoutSha256'],'Listing raw log changed')
    packages=package_rows(csv_path,required)
    files=[{'name':Path(p).name,'bytes':Path(p).stat().st_size,'sha256':h,'sha1':digest(p,'sha1')} for p,h in sorted(container_pins.items())]
    check(s['sourcePins']);check(container_pins)
    evidence=[snapshot,Path(cook_receipt).resolve(),Path(archive_receipt).resolve(),commands,response,csv_path,Path(listing_receipt).resolve(),cooked_manifest]
    r={'schemaVersion':1,'status':'cooked-source-container-lineage-validated',**identities(),
       'activeWaterBindingSha256':b['activeWaterBindingSha256'],'sourceMapSha256':b['mapSha256'],'nativeAuthoredStateSha256':b['nativeAuthoredStateSha256'],
       'sourceSnapshotSha256':digest(snapshot),'cookReceiptSha256':digest(cook_receipt),'archiveReceiptSha256':digest(archive_receipt),'ioStoreListingSha256':digest(csv_path),
       'receiverCount':45,'waterCount':1,'receiverTriangles':1076,'waterTriangles':4608,'waveCount':12,'sourceAssetHashes':b['assetFileHashes'],
       'additionalRuntimePackageHashes':additional,
       'sourcePinsUnchangedAcrossCookAndArchive':True,'freshCookOutput':True,'allRequiredPackagesInContainer':True,'runtimeTriangleBijectionReexecuted':False,
       'containerFiles':files,'packages':packages,'cookedPackageFileHashes':cooked_assets,'evidenceHashes':{str(p):digest(p) for p in evidence},
       'generatorSha256':digest(Path(__file__).resolve()),'nativeCookPid':c['pid'],'nativeArchivePid':a['pid'],
       'fullOpticsValidated':False,'singleBeerApplicationProven':False,'photorealismAccepted':False,'performanceAccepted':False,
       'limitations':['Editor source triangle/wave proof reused through unchanged source and actual cook/container lineage; no Game CPU triangle re-read.',
       'IoStore optimizes headers: cooked uasset hashes are not equated with serialized container chunk bytes.',
       'Pass this detached receipt to startup sealing as an optional resource; install only after its original-signature check, before its final signing. Final payload hashes must include it.',
       'Container checks are corruption/lineage checks, not independent signatures or full glass/alpha/BRDF/Beer proof.']}
    out=Path(output).absolute().resolve();need(not out.is_relative_to(app) and not out.is_relative_to(cooked) and not out.is_relative_to(project),'Generate detached receipt outside native inputs')
    save(out,r);return r

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='mode',required=True)
    before_p=sub.add_parser('before')
    for k in ('project','cook-output','output'):before_p.add_argument('--'+k,type=Path,required=True)
    seal_p=sub.add_parser('seal')
    for k in ('snapshot','cook-receipt','archive-receipt','io-commands','io-response','listing-csv','listing-receipt','output'):seal_p.add_argument('--'+k,type=Path,required=True)
    for parser in (before_p,seal_p):
        parser.add_argument('--binding',type=Path,required=True)
        parser.add_argument('--editor-pair',type=Path,required=True)
        parser.add_argument('--source-authority',type=Path)
        parser.add_argument('--source-authority-sha256')
        parser.add_argument('--editor-pair-sha256')
    a=vars(p.parse_args());binding=a.pop('binding');pair=a.pop('editor_pair')
    revision=a.pop('source_authority');revision_sha=a.pop('source_authority_sha256');pair_sha=a.pop('editor_pair_sha256')
    if any(x is not None for x in (revision,revision_sha,pair_sha)):
        need(all(x is not None for x in (revision,revision_sha,pair_sha)),'All explicit revision/pair identities are required')
        project=a.get('project') or Path(read(a['snapshot'])['projectRoot'])
        configure_revision(revision,revision_sha,binding,pair,pair_sha,project)
    else:configure_authority(binding,pair)
    mode=a.pop('mode');r=before(**a) if mode=='before' else seal(**a)
    print(json.dumps({k:r[k] for k in ('status','sourceBindingSha256','editorPairSha256')},indent=2))
