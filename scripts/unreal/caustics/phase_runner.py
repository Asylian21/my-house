#!/usr/bin/env python3
"""Explicit isolated-candidate source/graph/build/cook/archive phases; never runs the app."""
from pathlib import Path
import argparse,json,os,re,sys,uuid
sys.dont_write_bytecode=True
import native_process as H
HERE=Path(__file__).resolve().parent
MODES={'editor-graph':120,'game-graph':120,'editor-build':900,'game-build':900,'cook':900,'archive':600}
STATUS='native-delivery-exited-zero-and-drained'
GENERATED={'Build/Mac/BreziTwin.PackageVersionCounter','Build/Mac/FileOpenOrder/EditorOpenOrder.log','Build/Mac/FileOpenOrder/CookerOpenOrder.log'}

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def path(p):
    p=Path(p).absolute();H.need(p.resolve()==p and not p.is_symlink(),'Noncanonical path: '+str(p));return p
def inventory(root):
    root=path(root);H.need(root.is_dir(),'Missing tree '+str(root));rows={}
    for folder,dirs,files in os.walk(root):
        for n in dirs+files:H.need(not (Path(folder)/n).is_symlink(),'Linked tree entry')
        for n in files:
            p=Path(folder)/n;H.need(p.is_file(),'Nonregular tree entry');rows[str(p.relative_to(root))]=H.sha(p)
    return rows
def project_pins(P):
    pins={}
    for name in ('Source','Config','Build','Content'):
        if (P/name).is_dir():
            for rel,h in inventory(P/name).items():
                p=P/name/rel
                if str(p.relative_to(P)) not in GENERATED:pins[str(p)]=h
    for rel,h in inventory(P/'Plugins').items():
        if not set(Path(rel).parts)&{'Binaries','Intermediate','__pycache__'}:pins[str(P/'Plugins'/rel)]=h
    pins[str(P/'BreziTwin.uproject')]=H.sha(P/'BreziTwin.uproject');return pins

def generated_metadata(P):
    return {rel:H.sha(P/rel) if (P/rel).is_file() else None for rel in sorted(GENERATED)}

def paths(engine,project,run_root):
    E,P,R=map(path,(engine,project,run_root));marker=E/'.brezi-isolated-engine'
    H.need(E.is_dir() and marker.is_file() and not marker.is_symlink() and marker.read_text().rstrip('\r\n')==str(E),'Wrong isolated engine marker')
    H.need(P.is_relative_to(E) and P.is_dir() and (P/'BreziTwin.uproject').is_file(),'Project must be an existing BreziTwin clone inside marked engine')
    H.need(R.is_relative_to(E/'.brezi-managed') and not R.is_relative_to(P),'Run root must be separate candidate managed output')
    return E,P,R

def pinned(ref):
    p=path(ref['path']);H.need(p.is_file() and H.sha(p)==ref['sha256'],'Changed receipt '+str(p));return read(p)
def check(pins):
    for p,h in pins.items():H.need(path(p).is_file() and H.sha(p)==h,'Changed input '+p)
def merged(out,pins):
    for p,h in pins.items():H.need(p not in out or out[p]==h,'Conflicting pin '+p);out[p]=h

def context(E,P,toolchain):
    t=pinned(toolchain);pins=dict(t['fileHashes']);H.need(pins,'Empty build-tool closure')
    required=[E/'Engine/Binaries/ThirdParty/DotNet/10.0/mac-arm64/dotnet',
      E/'Engine/Binaries/DotNET/AutomationTool/AutomationTool.dll',E/'.brezi-managed/user-settings/UnrealBuildTool/BuildConfiguration.xml']
    required += [E/'Engine/Binaries/DotNET'/d/f for d in ('UnrealBuildTool','AutomationTool') for f in ('UnrealBuildTool.dll','EpicGames.Build.dll')]
    H.need(all(str(p) in pins for p in required),'Toolchain receipt must pin dotnet, UBT/AT assemblies and BuildConfiguration.xml')
    H.need(all(path(p).is_relative_to(E) for p in pins),'Foreign build-tool input')
    check(pins);pins[toolchain['path']]=toolchain['sha256']
    for p in (E/'.brezi-isolated-engine',HERE/'phase_runner.py',HERE/'native_process.py'):pins[str(p)]=H.sha(p)
    return pins

def source(engine,project,run_root,toolchain,engine_manifest,output):
    E,P,R=paths(engine,project,run_root);pins=context(E,P,toolchain)
    manifest=path(engine_manifest);m=read(manifest)
    H.need(H.sha(manifest.parent/'engine.patch')==m['patchSha256'],'Engine patch changed')
    H.need(H.sha(E/'Engine/Build/Build.version')==m['engineBuildVersionSha256'],'Engine version mismatch')
    for row in m['files']:
        q=E/row['path'];H.need(q.is_file() and H.sha(q)==row['resultSha256'],'Engine overlay source mismatch');pins[str(q)]=row['resultSha256']
    for q in (manifest,manifest.parent/'engine.patch',E/'Engine/Build/Build.version'):pins[str(q)]=H.sha(q)
    current=project_pins(P);merged(pins,current);check(pins)
    out=path(output);H.need(not out.exists() and out.is_relative_to(R),'New source receipt must be inside selected run root');out.parent.mkdir(parents=True,exist_ok=True)
    H.save(out,{'schemaVersion':1,'status':'caustics-delivery-source-frozen','errors':[],'engineRoot':str(E),'projectRoot':str(P),
      'fileHashes':pins,'projectSourcePins':current,'toolchain':toolchain,'engineManifest':str(manifest),'sourceInventoryExact':True,
      'generatedMetadataExcluded':generated_metadata(P),'scope':'Source and tool inputs only. Graph/build/cook/native runtime evidence remain separate.'})
    return {'status':'caustics-delivery-source-frozen','receipt':str(out),'sha256':H.sha(out)}

def input_pins(cfg):
    E,P,R=paths(cfg['engineRoot'],cfg['projectRoot'],cfg['runRoot']);pins=context(E,P,cfg['toolchain'])
    statuses={'sourceClosure':'caustics-delivery-source-frozen','acceptedEditor':'caustics-delivery-editor-build-accepted','acceptedGame':'caustics-delivery-game-build-accepted'}
    for role,ref in cfg['inputs'].items():
        value=pinned(ref);H.need(value['status']==statuses[role] and not value.get('errors'),'Unaccepted '+role)
        H.need(value['engineRoot']==str(E) and value['projectRoot']==str(P),'Foreign '+role)
        hashes=value['fileHashes'];H.need(hashes and all(Path(p).is_absolute() for p in hashes),'Empty/relative closure')
        # Rewritten generated P.app is never a current input. Acceptance must snapshot it first.
        H.need(not any(Path(p).is_relative_to(P/'Binaries/Mac/BreziTwin.app') for p in hashes),'Accepted receipt pins mutable generated P.app; snapshot it as historical evidence first')
        check(hashes);merged(pins,hashes);pins[ref['path']]=ref['sha256']
        if role=='sourceClosure':H.need(project_pins(P)==value['projectSourcePins'],'Project source set/bytes changed')
    if cfg['mode'].endswith('-build'):
        review=pinned(cfg['graphReview']);H.need(review['status']=='pass' and not review['issues'],'Unreviewed native graph')
        graph=Path(cfg['graphReview']['path']).parent/'actions.json'
        H.need(H.sha(graph)==review['graphSha256'],'Reviewed graph changed')
        H.need(review['providerCompileActions'] and all(x['apiEnabled'] for x in review['providerCompileActions']),'Provider compile API disabled')
        gp=graph.parent/'process.json';g=read(gp)
        H.need(g['status']=='graph-exported-review-pending' and g['nativeExitCode']==0 and not g['errors'] and not g['remainingOwned']
          and g['mode']==cfg['mode'].replace('-build','-graph') and g['engineRoot']==str(E) and g['projectRoot']==str(P)
          and g['inputs']['sourceClosure']==cfg['inputs']['sourceClosure'],'Reviewed graph is not this source/target phase')
        pins[str(gp)]=H.sha(gp);pins[str(graph)]=H.sha(graph);pins[cfg['graphReview']['path']]=cfg['graphReview']['sha256']
    if cfg['mode']=='archive':
        receipt=path(cfg['cookReceipt']);cook=read(receipt)
        H.need(cook['status']==STATUS and cook['mode']=='cook' and cook['nativeExitCode']==0 and not cook['errors'] and not cook['remainingOwned'],'Unaccepted native cook')
        H.need(cook['inputs']==cfg['inputs'] and cook['engineRoot']==str(E) and cook['projectRoot']==str(P),'Cook/archive identity differs')
        H.need(Path(cook['cookOutput'])==Path(cfg['cookOutput']) and receipt.is_relative_to(R),'Foreign cook output')
        q=receipt.parent/'cooked-files.json';H.need(inventory(Path(cfg['cookOutput']))==read(q),'Accepted cooked bytes changed')
        pins[str(receipt)]=H.sha(receipt);pins[str(q)]=H.sha(q)
        for q in (P/'Binaries/Mac/BreziTwin',P/'Binaries/Mac/BreziTwin.target'):H.need(str(q) in pins,'Raw Game/target missing accepted closure')
    return pins

def plan(engine,project,run_root,mode,attempt,toolchain,source_closure,accepted_editor=None,accepted_game=None,cook_receipt=None,graph_review=None,_directory=None):
    E,P,R=paths(engine,project,run_root);H.need(mode in MODES and re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9_-]{0,47}',attempt),'Invalid phase/attempt')
    out=path(_directory) if _directory else R/(mode+'-'+attempt+'-'+uuid.uuid4().hex)
    H.need(out.parent==R and re.fullmatch(re.escape(mode+'-'+attempt+'-')+r'[0-9a-f]{32}',out.name),'Invalid phase directory')
    dotnet=E/'Engine/Binaries/ThirdParty/DotNet/10.0/mac-arm64/dotnet'
    env={'BREZI_UE_WRITABLE_ROOT':str(E/'.brezi-managed/user-settings'),'UE_SKIP_UBT_SDK_SETUP':'0','TMPDIR':str(out/'tmp')+'/',
         'PATH':str(dotnet.parent)+':'+os.environ.get('PATH',''),'uebp_LOCAL_ROOT':str(E),'uebp_LogFolder':str(out/'uat/logs'),
         'uebp_FinalLogFolder':str(out/'uat/final-logs'),'uebp_EngineSavedFolder':str(out/'uat/saved')}
    inputs={'sourceClosure':source_closure};cwd=E/'Engine/Source';cook_output=None
    if mode in ('cook','archive'):
        H.need(accepted_editor and accepted_game,'Cook/archive require accepted Editor and Game');inputs.update(acceptedEditor=accepted_editor,acceptedGame=accepted_game)
    if mode.endswith(('-graph','-build')):
        target='BreziTwinEditor' if mode.startswith('editor') else 'BreziTwin'
        argv=[str(dotnet),str(E/'Engine/Binaries/DotNET/UnrealBuildTool/UnrealBuildTool.dll'),target,'Mac','Development',
          '-Project='+str(P/'BreziTwin.uproject'),'-Architecture=arm64','-NoHotReload','-SkipPreBuildTargets','-NoUBTMakefiles',
          '-NoUBA','-NoXGE','-NoFASTBuild','-NoSNDBS','-MaxParallelActions=4','-Log='+str(out/'ubt.log')]
        if mode.endswith('-graph'):argv.append('-WriteOutdatedActions='+str(out/'actions.json'))
        else:H.need(graph_review,'Build requires independently reviewed graph')
    elif mode=='cook':
        ddc=E/'.ddc';H.need(ddc.is_dir() and not ddc.is_symlink() and len(str(ddc))<120,'Explicit prepared candidate .ddc missing/too long')
        cook_output=out/'cooked/Mac';cwd=E/'Engine/Binaries/Mac'
        argv=[str(cwd/'UnrealEditor-Cmd'),str(P/'BreziTwin.uproject'),'-run=Cook','-TargetPlatform=Mac','-Map=/Game/Brezi/Maps/Brezi',
          '-OutputDir='+str(cook_output),'-nullrhi','-unattended','-nosplash','-stdout','-FullStdOutLogOutput','-DDC=(Local)',
          '-DDC-NoDefaultGraph','-LocalDataCachePath='+str(ddc),'-ShaderWorkingDir='+str(out/'shader-work')+'/',
          '-UserDir='+str(out/'cook-user')+'/', '-abslog='+str(out/'cook.log'),'-notraceserver','-SkipZenStore','-CookProcessCount=1',
          '-ini:Engine:[ConsoleVariables]:r.Brezi.FloorCaustics=0,[ConsoleVariables]:r.ShaderCompiler.AllowDistributedCompilation=0,'
          '[ConsoleVariables]:r.ShaderCompiler.DumpShaderTimeStats=1,[DevOptions.Shaders]:NumUnusedShaderCompilingThreads=14,'
          '[DevOptions.Shaders]:NumUnusedShaderCompilingThreadsDuringGame=14,[DevOptions.Shaders]:ShaderCompilerCoreCountThreshold=2147483647']
    else:
        H.need(cook_receipt,'Archive needs exact successful cook receipt');c=read(cook_receipt);cook_output=path(c['cookOutput'])
        H.need(cook_output.is_relative_to(path(cook_receipt).parent),'Cook output escape')
        # One argv value: UAT forwards the quoted derived path to its own Xcode invocation.
        derived=str(out/'xcode-derived-data');H.need('"' not in derived and '\n' not in derived,'Unsupported derived-data path')
        argv=[str(dotnet),str(E/'Engine/Binaries/DotNET/AutomationTool/AutomationTool.dll'),'-NoCompile','BuildCookRun',
          '-project='+str(P/'BreziTwin.uproject'),'-noP4','-platform=Mac','-clientconfig=Development','-skipbuild','-skipcook',
          '-CookOutputDir='+str(cook_output),'-stage','-pak','-package','-archive','-stagingdirectory='+str(out/'stage'),
          '-archivedirectory='+str(out/'archive'),'-xcodebuildoptions=-derivedDataPath "'+derived+'"','-utf8output','-unattended']
    cfg={'schemaVersion':1,'attempt':attempt,'mode':mode,'engineRoot':str(E),'projectRoot':str(P),'runRoot':str(R),'directory':str(out),'argv':argv,'cwd':str(cwd),
      'environmentSet':env,'environmentUnset':['BREZI_UE_MAC_RENDERER_RULES','UBT_EXTRA_ARGS','UE_BUILD_FROM_XCODE'],
      'deadlineSeconds':MODES[mode],'maxShaderWorkers':4,'maxParallelActions':4,'toolchain':toolchain,'inputs':inputs,
      'cookReceipt':str(path(cook_receipt)) if cook_receipt else None,'cookOutput':str(cook_output) if cook_output else None,
      'graphReview':graph_review,'executionPolicy':'standard-authorized-local-cli-with-owned-process-supervision',
      'hostFiles':{str(p):H.sha(p) for p in (Path(__file__).resolve(),HERE/'native_process.py')}}
    input_pins(cfg);return cfg

def build_outputs(E,P,mode):
    if mode.startswith('editor'):
        plugin=P/'Plugins/BreziCausticsProbe/Binaries/Mac'
        files=[E/'Engine/Binaries/Mac/libUnrealEditor-Renderer.dylib',E/'Engine/Binaries/Mac/UnrealEditor.modules',
          E/'Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor',P/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib',
          P/'Binaries/Mac/UnrealEditor.modules',plugin/'libUnrealEditor-BreziCausticsProbe.dylib',plugin/'UnrealEditor.modules']
    else:
        files=[P/'Binaries/Mac/BreziTwin',P/'Binaries/Mac/BreziTwin.target']
        bundle=P/'Binaries/Mac/BreziTwin.app';files += [bundle/rel for rel in inventory(bundle)]
    for p in files:H.need(path(p).is_file(),'Missing native build product '+str(p))
    return {str(p):H.sha(p) for p in files}

def log_findings(text):
    error=[s for s in text.splitlines() if re.search(r'\b(?:Error|Fatal):|Ensure condition failed|invalid ShaderMap|Failed to compile Material|UnauthorizedAccessException',s,re.I)]
    if '** BUILD FAILED **' in text or 'The following build commands failed:' in text:error.append('Nested Xcode build failed despite UAT terminal status')
    return sorted(set(error))

def execute(cfg,check_only=False):
    H.need(cfg['hostFiles']=={str(p):H.sha(p) for p in (Path(__file__).resolve(),HERE/'native_process.py')},'Host changed since plan')
    expected=plan(cfg['engineRoot'],cfg['projectRoot'],cfg['runRoot'],cfg['mode'],cfg['attempt'],cfg['toolchain'],
      cfg['inputs']['sourceClosure'],cfg['inputs'].get('acceptedEditor'),cfg['inputs'].get('acceptedGame'),cfg['cookReceipt'],cfg['graphReview'],_directory=cfg['directory'])
    H.need(cfg==expected,'Plan command/configuration drift')
    pins=input_pins(cfg);out=path(cfg['directory']);H.need(not out.exists(),'Preserve existing attempt')
    if check_only:return {'status':'preflight-only-not-executed','mode':cfg['mode'],'directory':str(out),'pinCount':len(pins),'argv':cfg['argv']}
    H.reject_conflicts(H.processes(),cfg)
    out.mkdir(parents=True,exist_ok=False)
    for rel in ('tmp','shader-work','cook-user','uat/logs','uat/final-logs','uat/saved'):(out/rel).mkdir(parents=True,exist_ok=True)
    H.save(out/'command.json',cfg);H.save(out/'pins-before.json',pins)
    generated_before=generated_metadata(Path(cfg['projectRoot']))
    try:value=H.supervise(cfg,out)
    except BaseException as exc:
        value={**cfg,'pid':None,'nativeExitCode':None,'remainingOwned':[],'ownedDrainVerified':False,
          'errors':['Supervisor prelaunch failure: '+type(exc).__name__+': '+str(exc)]}
    try:
        value['generatedMetadata']={'before':generated_before,'after':generated_metadata(Path(cfg['projectRoot']))}
        after={q:H.sha(q) if Path(q).is_file() else None for q in pins};H.save(out/'pins-after.json',after)
        value['changedPinnedInputs']=[q for q in pins if pins[q]!=after[q]]
        if value['changedPinnedInputs']:value['errors'].append('Pinned phase inputs changed')
        src=pinned(cfg['inputs']['sourceClosure'])
        H.need(project_pins(Path(cfg['projectRoot']))==src['projectSourcePins'],'Project source additions/deletions/changes across phase')
        logs=[]
        for n in ('stdout.log','ubt.log','cook.log'):
            q=out/n
            if q.is_file():value[n+'Sha256']=H.sha(q);logs.append(q.read_text(errors='replace'))
        text='\n'.join(logs);value['errorLines']=log_findings(text);value['warningLines']=sorted(set(s for s in text.splitlines() if 'Warning:' in s))
        if value['errorLines']:value['errors'].append('Native error/fallback/nested-failure lines; preserve raw evidence')
        mode=cfg['mode']
        if mode.endswith('-graph'):
            graph=read(out/'actions.json');H.need(isinstance(graph['Actions'],list),'Malformed graph')
            value['graph']={'path':str(out/'actions.json'),'sha256':H.sha(out/'actions.json'),'actionCount':len(graph['Actions']),'rootAuditPending':True}
        elif mode.endswith('-build'):
            value['buildOutputHashes']=build_outputs(Path(cfg['engineRoot']),Path(cfg['projectRoot']),mode)
            value['generatedAppIsHistoricalBuildOutput']=mode=='game-build'
        elif mode=='cook':
            rows=inventory(Path(cfg['cookOutput']));H.save(out/'cooked-files.json',rows);value['cookedFileCount']=len(rows)
            H.need(any(p.endswith('Content/Brezi/Maps/Brezi.umap') for p in rows),'Fresh cooked map missing')
            H.need(any(p.endswith('GlobalShaderCache-METAL_SM6.bin') for p in rows),'Metal global shader cache missing')
            H.need(re.search(r'Success - 0 error\(s\)',text),'Cook success footer missing');value['shaderTypeAndWarningReviewPending']=True
        elif mode=='archive':
            old=read(Path(cfg['cookReceipt']).parent/'cooked-files.json');now=inventory(Path(cfg['cookOutput']))
            H.need(all(now.get(k)==v for k,v in old.items()) and set(now)-set(old)<={'BreziTwin/Metadata/Crypto.json'},'Accepted cook bytes changed')
            value['additiveCookMetadata']={k:v for k,v in now.items() if k not in old}
            apps=list((out/'archive/Mac').glob('*.app'));H.need(len(apps)==1,'Unique archive app missing')
            H.need('BUILD SUCCESSFUL' in text and 'AutomationTool exiting with ExitCode=0' in text,'UAT success footer missing')
            value['appPath']=str(apps[0]);value['sealingAndPackageVerificationPending']=True
    except Exception as exc:value['errors'].append('Phase evidence: '+str(exc))
    value['errors']=list(dict.fromkeys(value['errors']))
    value['status']=('graph-exported-review-pending' if cfg['mode'].endswith('-graph') else
       'native-build-exited-zero-and-drained' if cfg['mode'].endswith('-build') else STATUS) if not value['errors'] else 'phase-failed'
    H.save(out/'process.json',value);return value

def ref(p):
    p=path(p);return {'path':str(p),'sha256':H.sha(p)}
def main():
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
    s=sub.add_parser('source');p=sub.add_parser('plan');r=sub.add_parser('run')
    for q in (s,p):
        for n in ('engine','project','run-root','toolchain-pins','toolchain-sha256','output'):q.add_argument('--'+n,required=True)
    s.add_argument('--engine-manifest',required=True)
    p.add_argument('mode',choices=MODES);p.add_argument('--attempt',required=True);p.add_argument('--source-closure',required=True)
    for n in ('accepted-editor','accepted-game','cook-receipt','graph-review'):p.add_argument('--'+n)
    r.add_argument('--plan',required=True);r.add_argument('--sha256',required=True);r.add_argument('--check',action='store_true')
    a=parser.parse_args()
    if a.command=='run':
        result=execute(pinned({'path':str(path(a.plan)),'sha256':a.sha256}),a.check)
        print(json.dumps({k:result.get(k) for k in ('status','mode','directory','pid','nativeExitCode','errors','appPath','pinCount','argv')},indent=2));return 1 if result.get('errors') else 0
    toolchain={'path':str(path(a.toolchain_pins)),'sha256':a.toolchain_sha256}
    if a.command=='source':result=source(a.engine,a.project,a.run_root,toolchain,a.engine_manifest,a.output)
    else:
        cfg=plan(a.engine,a.project,a.run_root,a.mode,a.attempt,toolchain,ref(a.source_closure),ref(a.accepted_editor) if a.accepted_editor else None,
          ref(a.accepted_game) if a.accepted_game else None,a.cook_receipt,ref(a.graph_review) if a.graph_review else None)
        out=path(a.output);H.need(out.is_relative_to(path(a.run_root)) and not out.exists(),'Plan output must be new within run root')
        out.parent.mkdir(parents=True,exist_ok=True);H.save(out,cfg);result={'status':'delivery-plan-saved','plan':str(out),'sha256':H.sha(out),'directory':cfg['directory'],'cookOutput':cfg['cookOutput']}
    print(json.dumps(result,indent=2));return 0
if __name__=='__main__':
    try:sys.exit(main())
    except Exception as exc:print(type(exc).__name__+': '+str(exc),file=sys.stderr);sys.exit(1)
