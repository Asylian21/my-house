"""Root-only CPU staging of a data-only close-camera QA clone; no native API."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-curved-grass-camera-stage-r2.py'
sys.dont_write_bytecode=True
def load(name,file):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/unreal'/file)
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
camera=load('r20_stage_frozen_camera','exterior-curved-grass-camera-r1.py')
g=camera.g.common
require,read,write,sha,pin=g.require,g.read,g.write,g.sha,g.pin


def actual_source(source,process_path=None):
    source=Path(source).resolve();evidence=read(camera.g.EVIDENCE_PLAN)
    if source==camera.g.BASE:
        report_path=source/'exterior-import-report.json'
        require(sha(report_path)==evidence['baseNativeReport']['sha256'],'Actual original R16 report changed')
        report=read(report_path);require(report['status']=='exterior-import-validated' and report['savedReloaded'] is True,
                'Original R16 was not saved/reloaded')
        return report_path,read(evidence['baseContentInventory']['path']),read(evidence['baseProjectProof']['path']),None
    report_path=source/'curved-grass-native-report-r4.json'
    report=read(report_path)
    require(source.is_relative_to(ROOT/'output/unreal') and source.name.startswith('exterior-20261002-r20')
            and report['schema']=='brezi-original-curved-grass-root-replacement-r1'
            and report['owner']=='scripts/unreal/exterior-curved-grass-native-r4.py'
            and report['status']=='verified-saved-original-curved-grass-root-replacement'
            and report['repairSchema']=='brezi-original-curved-grass-exact-native-transform-repair-r4'
            and report['savedMapUnloadedReloaded'] is True and report['originalR16Unchanged'] is True,
            'Only actual saved repaired R20 can supply a grass camera candidate')
    require(report['output']==str(source) and report['project']==str(source/'Project/BreziTwin')
            and all(report[k] is False for k in ('nativeAppearanceAccepted','fullPhotorealismAccepted',
                'performanceAccepted','shippingPackageProduced')),'Repaired grass report identity/scope flags differ')
    repair=load('r20_camera_stage_repair','exterior-curved-grass-repair-r4.py');repair.validated_supplement()
    require(report['repairSupplement']==pin(repair.OUTPUT/'curved-grass-repair-supplement.json')
            and report['selectedPlan']==pin(camera.PLAN)
            and report['transformComparisonPolicy']==repair.transforms.policy()
            and report['faithfulTransformProbe']==pin(repair.transforms.PROBE)
            and report['all64StoredMatrixAndRecoveredTransformExactMeasuredBeforeSaveAndAfterReload'] is True,
            'Actual native selected repair/source/exact64 serialized matrix proof differs')
    require(process_path is not None,'Actual sealed native process receipt required')
    process_path=Path(process_path).resolve();require(process_path==source/'curved-grass-native-r4-process.json','Foreign native process receipt')
    process=read(process_path);raw=Path(process['processFile']);require(raw==source/'curved-grass-native-r4.log.json'
            and Path(process['logFile'])==source/'curved-grass-native-r4.log' and sha(raw)==process['processFileSha256'],
            'Actual native process bytes changed')
    run=read(raw)
    require(run['command']=='/Users/Shared/Epic Games/UE_5.8/Engine/Binaries/Mac/UnrealEditor-Cmd'
            and run['args'][0]==str(source/'Project/BreziTwin/BreziTwin.uproject')
            and '-run=pythonscript' in run['args'] and '-nullrhi' in run['args']
            and run['code']==0 and run['pid']==report['nativeProcessId'] and run['signal'] is None
            and '-script='+str(ROOT/'scripts/unreal/exterior-curved-grass-native-r4.py') in run['args']
            and process['reportSha256']==sha(report_path) and process['sourcePinsUnchangedAfterNative'] is True
            and process['controllerSha256BeforeNative']==process['controllerSha256AfterNative']==sha(process['controller'])
            and sha(process['logFile'])==process['logSha256'],'Saved R20 actual terminal process/closure differs')
    for file,h in process['sourcePinsBeforeNative'].items():require(sha(file)==h,'Saved native source pin changed')
    require(report['expectedActorWitnessSha256']==report['savedActorWitnessSha256']
            and report['assetDelta']['changedFiles']==['Brezi/Maps/Brezi.umap']
            and report['assetDelta']['newUassetPackages']==11,'Actual native original/pilot scope differs')
    content=read(camera.g.check_pin(report['afterContentInventory']))
    require(len(content)==3986,'Actual saved grass Content count differs')
    return report_path,content,read(evidence['baseProjectProof']['path']),process_path


def stage(source,output,process_path=None):
    s=camera.validated_supplement();source=Path(source).resolve();output=Path(output).resolve()
    require(output.is_relative_to(ROOT/'output/unreal') and output!=source and not output.is_relative_to(source)
            and output!=camera.g.BASE and not output.is_relative_to(camera.g.BASE),'Only independent root-prepared QA clone may change')
    report_path,before,protected,process_path=actual_source(source,process_path)
    project=output/'Project/BreziTwin';source_project=source/'Project/BreziTwin'
    receipt=output/'curved-grass-camera-stage-receipt.json';require(not receipt.exists(),'Prior camera staging receipts are immutable')
    require(g.inventory(project/'Content')==before and g.inventory(source_project/'Content')==before
            and g.project_proof(project)==protected and g.project_proof(source_project)==protected,'Independent QA clone/source bytes differ')
    for relative in before:
        a,b=source_project/'Content'/relative,project/'Content'/relative
        require((a.stat().st_dev,a.stat().st_ino)!=(b.stat().st_dev,b.stat().st_ino),'QA clone Content hardlink forbidden')
    for relative in protected:
        a,b=source_project/relative,project/relative
        require((a.stat().st_dev,a.stat().st_ino)!=(b.stat().st_dev,b.stat().st_ino),'QA clone protected-file hardlink forbidden')
    destination=project/'Content/Data/viewpoints.json'
    require(destination.read_bytes()==Path(s['originalViewpoints']['path']).read_bytes(),'Stage requires original exact camera prefix')
    destination.write_bytes(Path(s['appendedViewpoints']['path']).read_bytes())
    after=g.inventory(project/'Content')
    require(set(before)==set(after) and [k for k in before if before[k]!=after[k]]==['Data/viewpoints.json']
            and sha(destination)==s['appendedViewpoints']['sha256'],'Only exact close camera data may change')
    require(g.project_proof(project)==protected and g.inventory(source_project/'Content')==before
            and g.project_proof(source_project)==protected,'Camera stage modified protected/source bytes')
    write(output/'curved-grass-camera-content-after.json',after)
    write(receipt,{'schema':'brezi-curved-grass-close-camera-diagnostic-clone-r2','owner':OWNER,
        'status':'verified-independent-qa-clone-close-camera-data-only','generatedAt':g.now(),
        'sourceKind':'original-r16' if source==camera.g.BASE else 'saved-curved-grass-r20-r4',
        'sourceNativeOutput':str(source),'sourceNativeReport':pin(report_path),
        'sourceNativeProcess':pin(process_path) if process_path else None,'project':str(project),
        'cameraSupplement':pin(camera.OUTPUT/'curved-grass-camera-supplement.json'),'stagingHelper':pin(ROOT/OWNER),
        'viewpointFile':pin(destination),'viewId':camera.VIEW_ID,'view':s['view'],
        'sourceCameraAudit':s['sourceCameraAudit'],'afterContentInventory':pin(output/'curved-grass-camera-content-after.json'),
        'protectedProjectProof':read(camera.g.EVIDENCE_PLAN)['baseProjectProof'],
        'changedContentFiles':['Data/viewpoints.json'],'originalContentFileCount':len(before),
        'originalViewsPrefixPreserved':True,'lightingUnchanged':True,'nativeSourceUnchanged':True,
        'sceneMapChanged':False,'nativeCameraRuntimeVerified':False,'nativeAppearanceAccepted':False,
        'performanceAccepted':False,'fullPhotorealismAccepted':False,'shippingPackageProduced':False})
    print(json.dumps({'receipt':pin(receipt),'viewId':camera.VIEW_ID,'sourceKind':read(receipt)['sourceKind']}))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--source',required=True);parser.add_argument('--output',required=True)
    parser.add_argument('--process');args=parser.parse_args();stage(args.source,args.output,args.process)
