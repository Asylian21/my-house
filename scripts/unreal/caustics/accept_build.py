#!/usr/bin/env python3
"""Accept a clean native build and preserve generated Game .app as historical bytes."""
from pathlib import Path
import argparse,json,re,shutil,subprocess,sys,uuid
sys.dont_write_bytecode=True
import native_process as H
import phase_runner as F

def defined_provider_symbols(text):
    names=[line.split()[-1] for line in text.splitlines() if re.match(r'^\s*[0-9a-fA-F]+\s+[Tt]\s+',line)]
    required=('RegisterFloorCausticsProvider_RenderThread','UnregisterFloorCausticsProvider_RenderThread',
              'CreateBreziFloorCausticsDiagnostic','CreateBreziCausticsTransport')
    for word in required:H.need(any(word in name for name in names),'Missing defined provider code: '+word)
    return {word:next(name for name in names if word in name) for word in required}

def accept(engine,project,run_root,mode,source_closure,graph_review,build_receipt,output):
    E,P,R=F.paths(engine,project,run_root);out=F.path(output);H.need(out.is_relative_to(R) and not out.exists(),'Choose new managed acceptance output')
    source=F.read(source_closure);review=F.read(graph_review);build=F.read(build_receipt)
    H.need(source['status']=='caustics-delivery-source-frozen' and source['engineRoot']==str(E) and source['projectRoot']==str(P),'Foreign/unfrozen source')
    H.need(review['status']=='pass' and not review['issues'],'Graph review missing')
    graph=F.path(graph_review).parent/'actions.json';H.need(H.sha(graph)==review['graphSha256'],'Graph changed')
    H.need(review['providerCompileActions'] and all(r['apiEnabled'] for r in review['providerCompileActions']),'Provider API not compiled')
    H.need(build['status']=='native-build-exited-zero-and-drained' and build['mode']==mode+'-build' and build['nativeExitCode']==0
      and not build['errors'] and not build['remainingOwned'] and not build['changedPinnedInputs'],'Native build did not cleanly close')
    H.need(build['engineRoot']==str(E) and build['projectRoot']==str(P) and build['inputs']['sourceClosure']==F.ref(source_closure)
      and build['graphReview']==F.ref(graph_review),'Build/source/review lineage differs')
    directory=F.path(build_receipt).parent
    H.need(build['directory']==str(directory) and directory.is_relative_to(R),'Foreign native build receipt')
    before=F.read(directory/'pins-before.json');after=F.read(directory/'pins-after.json');H.need(before==after,'Build input pins changed');F.check(after)
    logs=''
    for n in ('stdout.log','ubt.log'):
        q=directory/n;H.need(q.is_file() and H.sha(q)==build[n+'Sha256'],'Build log changed');logs+=q.read_text(errors='replace')
    H.need(not F.log_findings(logs),'Native/nested build failure in accepted logs')
    F.check(source['fileHashes']);H.need(F.project_pins(P)==source['projectSourcePins'],'Source set changed')
    H.need(F.build_outputs(E,P,mode)==build['buildOutputHashes'],'Native build output bytes changed before acceptance')
    files=[F.path(source_closure),F.path(graph_review),F.path(build_receipt),graph,directory/'stdout.log',directory/'ubt.log',directory/'pins-before.json',directory/'pins-after.json',Path(__file__).resolve()]
    historical=None
    if mode=='editor':
        renderer=E/'Engine/Binaries/Mac/libUnrealEditor-Renderer.dylib';plugin=P/'Plugins/BreziCausticsProbe/Binaries/Mac/libUnrealEditor-BreziCausticsProbe.dylib'
        modules=[E/'Engine/Binaries/Mac/UnrealEditor.modules',P/'Binaries/Mac/UnrealEditor.modules',plugin.parent/'UnrealEditor.modules'];maps=[F.read(p) for p in modules]
        H.need(len({m['BuildId'] for m in maps})==1,'Editor module BuildIds differ')
        for m,key,filename in zip(maps,('Renderer','BreziTwin','BreziCausticsProbe'),(renderer.name,'libUnrealEditor-BreziTwin.dylib',plugin.name)):
            H.need(m['Modules'][key]==filename,'Editor module mapping differs')
        symbols=subprocess.run(['/usr/bin/nm','-g',str(renderer)],check=True,capture_output=True,text=True).stdout
        imports=subprocess.run(['/usr/bin/nm','-u',str(plugin)],check=True,capture_output=True,text=True).stdout
        for word in ('RegisterFloorCausticsProvider','UnregisterFloorCausticsProvider'):H.need(word in symbols and word in imports,'Missing Renderer/plugin linkage')
        files += [renderer,plugin,P/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib',E/'Engine/Binaries/Mac/UnrealEditor.app/Contents/MacOS/UnrealEditor',*modules]
        evidence={'moduleBuildId':maps[0]['BuildId'],'rendererProviderLinkage':True}
    else:
        game=P/'Binaries/Mac/BreziTwin';target=P/'Binaries/Mac/BreziTwin.target';t=F.read(target)
        H.need(t['TargetName']=='BreziTwin' and t['Platform']=='Mac' and t['Configuration']=='Development','Wrong Game target')
        symbols=subprocess.run(['/usr/bin/nm',str(game)],check=True,capture_output=True,text=True).stdout
        definitions=defined_provider_symbols(symbols)
        bundle=P/'Binaries/Mac/BreziTwin.app';snapshot=out.parent/('postbuild-app-'+uuid.uuid4().hex)/'BreziTwin.app'
        original=F.inventory(bundle);H.need('Contents/PkgInfo' in original and 'Contents/Info.plist' in original and 'Contents/MacOS/BreziTwin' in original,'Incomplete generated Game app')
        snapshot.parent.mkdir(parents=True,exist_ok=False);shutil.copytree(bundle,snapshot)
        H.need(F.inventory(bundle)==original==F.inventory(snapshot),'Generated Game app changed during historical copy')
        H.need(all((bundle/rel).stat().st_ino!=(snapshot/rel).stat().st_ino for rel in original),'Historical copy aliases mutable generated file')
        files += [game,target,*[snapshot/rel for rel in sorted(original)]]
        historical={'sourcePath':str(bundle),'snapshotPath':str(snapshot),'snapshotFileHashes':original,
          'classification':'historical-postbuild-output-copy','originalAppCurrentInput':False,'independentFileInodes':True}
        evidence={'linkedRendererProviderCodePresent':True,'definedProviderSymbols':definitions,'gamePostbuildAppPresent':True,'packagedAppPending':True}
    pins={str(p):H.sha(p) for p in files};F.check(source['fileHashes']);F.check(pins)
    H.need(F.build_outputs(E,P,mode)==build['buildOutputHashes'],'Native build outputs changed during acceptance')
    out.parent.mkdir(parents=True,exist_ok=True)
    report={'schemaVersion':1,'status':'caustics-delivery-'+mode+'-build-accepted','errors':[],'engineRoot':str(E),'projectRoot':str(P),
      'fileHashes':pins,'sourceClosure':str(F.path(source_closure)),'historicalBuildApp':historical,'evidence':evidence,
      'scope':'Clean native compile/link plus copied historical postbuild app. Current inputs are raw Game, .target, source, or matching Editor DLLs. Cook/package/runtime remain separate.'}
    H.save(out,report);return {'status':report['status'],'receipt':str(out),'sha256':H.sha(out),'pins':len(pins)}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=('editor','game'))
    for n in ('engine','project','run-root','source-closure','graph-review','build-receipt','output'):p.add_argument('--'+n,required=True)
    try:print(json.dumps(accept(**vars(p.parse_args())),indent=2))
    except Exception as exc:print(type(exc).__name__+': '+str(exc),file=sys.stderr);sys.exit(1)
