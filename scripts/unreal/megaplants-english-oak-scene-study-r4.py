"""Bind the actual preserved R3 USD import to a separate scene-only R4 trial."""
import importlib.util
import json
from pathlib import Path
import shutil

_p=Path(__file__).with_name('megaplants-english-oak-scene-guards-r4.py')
_s=importlib.util.spec_from_file_location('oak_r4_scene_guard',_p)
g=importlib.util.module_from_spec(_s);_s.loader.exec_module(g)

def main():
    g.require(not g.PLAN.exists(),'Preserve selected post-import plan history')
    source,base=g.original.validate_plan()
    audit_path=g.OUTPUT/'root-native-crash-byte-audit-r3-r1.json';audit=g.read(audit_path)
    before=g.inventory(g.PROJECT)
    before_path=g.SOURCE/'oak-usd-scene-before-inventory-r4.json';g.write(before_path,before)
    original=g.inventory(g.BASE/'Project/BreziTwin')
    original_path=g.SOURCE/'oak-usd-original-r32-before-scene-r4.json';g.write(original_path,original)
    engine=Path('/Users/Shared/Epic Games/UE_5.8/Engine')
    own=[g.ROOT/('scripts/unreal/'+name) for name in
         ('megaplants-english-oak-scene-guards-r4.py','megaplants-english-oak-scene-native-r4.py',
          'megaplants-english-oak-scene-study-r4.py','test_megaplants_english_oak_scene_r4.py')]
    primary=[engine/p for p in ('Source/Editor/LevelEditor/Private/LevelEditorSubsystem.cpp',
        'Source/Editor/LevelEditor/Public/LevelEditorSubsystem.h',
        'Source/Editor/UnrealEd/Private/Subsystems/EditorActorSubsystem.cpp',
        'Plugins/Experimental/PythonScriptPlugin/Source/PythonScriptPlugin/Private/PyWrapperStruct.cpp',
        'Source/Runtime/Engine/Classes/Components/SceneComponent.h')]
    pins=[*source['inputFiles'],g.pin(g.original.PLAN),g.pin(g.SOURCE/'source-readiness-r3.json'),
          g.pin(before_path),g.pin(original_path),g.pin(audit_path),audit['process'],audit['terminal'],
          audit['nativeLog'],audit['preparation'],*[g.pin(p) for p in own+primary]]
    pins += [g.pin(g.PROJECT/'Content'/key) for key in audit['newContentFiles']]
    unique={p['path']:p for p in pins}
    plan={'schema':g.SCHEMA,'owner':'scripts/unreal/megaplants-english-oak-scene-study-r4.py',
       'status':'source-ready-original-saved-USD-scene-only-native-pending','project':str(g.PROJECT),
       'output':str(g.OUTPUT),'map':g.MAP,'groundMaterial':g.GROUND_MATERIAL,
       'originalSourcePlan':g.pin(g.original.PLAN),'sourceExtraction':source['sourceExtraction'],
       'usdInspection':source['usdInspection'],'baseNativeReport':source['baseNativeReport'],
       'initialRootClone':source['initialRootClone'],'projectPreparation':audit['preparation'],
       'crashedImportByteAudit':g.pin(audit_path),'beforeInventory':g.pin(before_path),
       'originalSavedR32Inventory':g.pin(original_path),'camera':g.scene_camera(source),
       'treePlacement':source['treePlacement'],'ground':source['ground'],
       'lightingScope':'Fresh native actors copying exactly the recorded LIGHT_FIELDS plus component mobility,7 PP values/override flags, native wrapped transform and tags; no full-property duplication claim',
       'activeMapInitialization':'LevelEditorSubsystem.new_level then non-null editor world and current level path readback before any spawn',
       'assetImportExecuted':False,'savedOriginalUsdPackages':39,'savedOriginalUsdPackageBytes':209572529,
       'fullLightingPropertyCloneClaimed':False,'nativeExecuted':False,
       'nativeAppearanceAccepted':False,'performanceAccepted':False,'fullPhotorealismAccepted':False,
       'shippingVerified':False,'packageVerified':False,'actualAvailableBytesAtSourcePreflight':shutil.disk_usage(g.OUTPUT).free,
       'inputFiles':sorted(unique.values(),key=lambda r:r['path'])}
    g.write(g.PLAN,plan)
    selected,original_plan,original_base,expected=g.validate_plan();g.validate_before(selected,expected)
    print(json.dumps({'plan':g.pin(g.PLAN),'inputFiles':len(plan['inputFiles']),'originalAndSavedUsdFiles':len(expected),
                      'assetImportExecuted':False,'nativeExecuted':False}))

if __name__=='__main__':main()
