"""Bind actual R5 setter measurement to one new scene, without a broad epsilon."""
import importlib.util
import json
from pathlib import Path
import shutil

_p=Path(__file__).with_name('megaplants-english-oak-scene-guards-r6.py')
_s=importlib.util.spec_from_file_location('oak_r6_scene_producer_guard',_p)
g=importlib.util.module_from_spec(_s);_s.loader.exec_module(g)

def main():
    g.require(not g.PLAN.exists(),'Preserve each selected scene measurement revision')
    previous,source,base,_=g.old.validate_plan()
    audit_path=g.OUTPUT/'root-native-scene-failure-byte-audit-r5-r1.json';audit=g.read(audit_path)
    difference_path=g.OUTPUT/'oak-usd-scene-lighting-differences-r5.json';difference=g.read(difference_path)
    own=[g.ROOT/('scripts/unreal/'+n) for n in ('megaplants-english-oak-scene-guards-r6.py',
        'megaplants-english-oak-scene-native-r6.py','megaplants-english-oak-scene-study-r6.py',
        'test_megaplants_english_oak_scene_r6.py')]
    pins=[*previous['inputFiles'],g.pin(g.old.PLAN),g.pin(g.SOURCE/'scene-source-readiness-r5.json'),
          g.pin(audit_path),audit['currentAfterInventory'],audit['process'],audit['terminal'],audit['report'],
          audit['rootByteAuditHelper'],g.pin(difference_path),difference['source'],difference['copied'],
          *[g.pin(p) for p in own]]
    pins += [g.pin(g.PROJECT/key) for key in audit['newContentFiles']]
    terminal=g.read(g.check_pin(audit['terminal']));pins.append(g.pin(Path(terminal['logFile'])))
    p={**previous,'schema':g.SCHEMA,'owner':'scripts/unreal/megaplants-english-oak-scene-study-r6.py',
        'status':'source-ready-scene-only-exact-measured-directional-setter-native-pending',
        'map':g.MAP,'groundMaterial':g.GROUND_MATERIAL,'camera':g.scene_camera(source),
        'previousScenePlan':g.pin(g.old.PLAN),'failedSceneByteAudit':g.pin(audit_path),
        'beforeInventory':audit['currentAfterInventory'],'numericalToleranceApplied':False,
        'measuredLightingReference':g.pin(difference_path),
        'lightingScope':'Fresh native actors copy exactly the recorded LIGHT_FIELDS, mobility,7 PP values/overrides,tags,location and scale. Only the fixed DirectionalLight quaternion uses its exact measured R5 native setter output, also required after reload. No general epsilon or full-property clone claim.',
        'lightingDiagnostic':'All source and copied binary64/type differences recorded; copied and saved snapshots must equal the exact measured R5 subset.',
        'actualAvailableBytesAtSourcePreflight':shutil.disk_usage(g.OUTPUT).free,
        'inputFiles':sorted({p['path']:p for p in pins}.values(),key=lambda p:p['path'])}
    g.write(g.PLAN,p)
    selected,_,_,before=g.validate_plan();g.validate_before(selected,before)
    print(json.dumps({'plan':g.pin(g.PLAN),'inputFiles':len(p['inputFiles']),
        'preservedOwnFiles':len(before),'assetImportExecuted':False,'numericalToleranceApplied':False,'nativeExecuted':False}))

if __name__=='__main__':main()
