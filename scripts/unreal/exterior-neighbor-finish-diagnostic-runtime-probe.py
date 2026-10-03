"""Native embedded-Python numeric comparison only. No scene/assets/GPU calls.

Root launches this script in the unchanged own R18 clone. Source R2, source
helpers and original project Content are read only; writes one NEW JSON receipt.
"""
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import platform
import sys

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-neighbor-finish-diagnostic-runtime-probe.py'


def main():
    import unreal as u
    output=Path(os.environ['BREZI_NEIGHBOR_PROBE_OUTPUT']).resolve()
    require= lambda ok,msg: None if ok else (_ for _ in ()).throw(ValueError(msg))
    require(output==ROOT/'output/unreal/exterior-20261001-r18a','Probe is restricted to unchanged own first R18 clone')
    require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==output/'Project/BreziTwin','Wrong numeric-probe project')
    receipt=output/'neighbor-finish-diagnostic-runtime-probe.json';require(not receipt.exists(),'Numeric probe receipt must be fresh')
    source=ROOT/'scripts/unreal/exterior-neighbor-finish-diagnostic.py'
    require(hashlib.sha256(source.read_bytes()).hexdigest()=='52bc4aea5b0bd994a74692a6c956176995d044ad84300ef373afb3f3b98a1d08','Original consumed diagnostic helper changed')
    spec=importlib.util.spec_from_file_location('diagnostic_original_runtime_probe',source);d=importlib.util.module_from_spec(spec);spec.loader.exec_module(d)
    supplement_path=d.OUTPUT/'neighbor-finish-diagnostic-supplement.json'
    require(d.sha(supplement_path)=='f1692dd83cd5caa15800845b5e31a18eeecbf22cc8587f4fc55bcf8a66293b18','Consumed original R2 supplement changed')
    supplement=d.read(supplement_path)
    view,audit=d.derive_camera(d.read(supplement['villagePath']),d.read(supplement['contextPath']),d.read(supplement['terrainPath']))
    diffs=[]
    def compare(expected,actual,path):
        if type(expected) in (int,float) and type(actual) in (int,float):
            if expected!=actual:diffs.append({'path':path,'expected':expected,'actual':actual,'absoluteDelta':abs(expected-actual),'finite':math.isfinite(expected) and math.isfinite(actual),'expectedUlp':math.ulp(float(expected)),'actualUlp':math.ulp(float(actual)),'deltaInLargerUlps':abs(expected-actual)/max(math.ulp(float(expected)),math.ulp(float(actual)))})
        elif isinstance(expected,dict) and isinstance(actual,dict):
            if set(expected)!=set(actual):diffs.append({'path':path,'nonNumericMismatch':True,'expectedKeys':sorted(expected),'actualKeys':sorted(actual)})
            else:
                for k in expected:compare(expected[k],actual[k],path+'.'+k)
        elif isinstance(expected,list) and isinstance(actual,list):
            if len(expected)!=len(actual):diffs.append({'path':path,'nonNumericMismatch':True,'expectedLength':len(expected),'actualLength':len(actual)})
            else:
                for i,(a,b) in enumerate(zip(expected,actual)):compare(a,b,path+'['+str(i)+']')
        elif type(expected) is not type(actual) or expected!=actual:diffs.append({'path':path,'nonNumericMismatch':True,'expected':expected,'actual':actual})
    compare({'view':supplement['view'],'audit':supplement['sourceCameraAudit']},{'view':view,'audit':audit},'$')
    result={'schemaVersion':1,'owner':OWNER,'status':'native-embedded-python-diagnostic-comparison-only','nativeProcessId':os.getpid(),'project':str(output/'Project/BreziTwin'),'pythonVersion':sys.version,'platform':platform.platform(),'sourceHelperSha256':d.sha(source),'sourceSupplementSha256':d.sha(supplement_path),'expectedView':supplement['view'],'actualView':view,'expectedAudit':supplement['sourceCameraAudit'],'actualAudit':audit,'differences':diffs,'maximumAbsoluteDelta':max((x.get('absoluteDelta',0) for x in diffs),default=0),'maximumUlpDelta':max((x.get('deltaInLargerUlps',0) for x in diffs),default=0),'nonNumericMismatchCount':sum(x.get('nonNumericMismatch',False) for x in diffs),'sceneLoadedOrChanged':False,'assetCallsExecuted':False,'nativeApplied':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False}
    receipt.write_text(json.dumps(result,indent=2,ensure_ascii=False,allow_nan=False)+'\n');print(json.dumps({'receipt':str(receipt),'differences':diffs,'sceneLoadedOrChanged':False}))


if __name__=='__main__':main()
