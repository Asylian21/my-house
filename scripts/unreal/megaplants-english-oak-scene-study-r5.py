"""Bind only the actual R4 failure to a new strict, observed R5 light trial."""
import importlib.util
import json
from pathlib import Path
import shutil

_p=Path(__file__).with_name('megaplants-english-oak-scene-guards-r5.py')
_s=importlib.util.spec_from_file_location('oak_r5_scene_producer_guard',_p)
g=importlib.util.module_from_spec(_s);_s.loader.exec_module(g)

def main():
    g.require(not g.PLAN.exists(),'Preserve each selected scene measurement proposal')
    previous,source,base,_=g.old.validate_plan()
    audit_path=g.OUTPUT/'root-native-scene-failure-byte-audit-r4-r1.json';audit=g.read(audit_path)
    own=[g.ROOT/('scripts/unreal/'+n) for n in ('megaplants-english-oak-scene-guards-r5.py',
        'megaplants-english-oak-scene-native-r5.py','megaplants-english-oak-scene-study-r5.py',
        'test_megaplants_english_oak_scene_r5.py')]
    pins=[*previous['inputFiles'],g.pin(g.old.PLAN),g.pin(g.SOURCE/'scene-source-readiness-r4.json'),
          g.pin(audit_path),audit['currentAfterInventory'],audit['process'],audit['terminal'],audit['report'],
          audit['rootByteAuditHelper'],*[g.pin(p) for p in own]]
    pins += [g.pin(g.PROJECT/key) for key in audit['newContentFiles']]
    terminal=g.read(g.check_pin(audit['terminal']))
    pins.append(g.pin(Path(terminal['logFile'])))
    p={**previous,'schema':g.SCHEMA,'owner':'scripts/unreal/megaplants-english-oak-scene-study-r5.py',
        'status':'source-ready-scene-only-lighting-difference-measurement-native-pending',
        'map':g.MAP,'groundMaterial':g.GROUND_MATERIAL,'camera':g.scene_camera(source),
        'previousScenePlan':g.pin(g.old.PLAN),'failedSceneByteAudit':g.pin(audit_path),
        'beforeInventory':audit['currentAfterInventory'],'numericalToleranceApplied':False,
        'lightingDiagnostic':'Write complete actual source/copied snapshots plus every type/value/binary64 difference before the strict equality gate. No inferred numerical tolerance.',
        'actualAvailableBytesAtSourcePreflight':shutil.disk_usage(g.OUTPUT).free,
        'inputFiles':sorted({p['path']:p for p in pins}.values(),key=lambda p:p['path'])}
    g.write(g.PLAN,p)
    selected,_,_,before=g.validate_plan();g.validate_before(selected,before)
    print(json.dumps({'plan':g.pin(g.PLAN),'inputFiles':len(p['inputFiles']),
        'preservedOwnFiles':len(before),'assetImportExecuted':False,'numericalToleranceApplied':False,'nativeExecuted':False}))

if __name__=='__main__':main()
