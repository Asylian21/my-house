"""Prepare a typed source-only original-D trial against actual saved R32/clone."""
import importlib.util
import itertools
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys

_p=Path(__file__).with_name('megaplants-english-oak-pilot-guards-r2.py')
_s=importlib.util.spec_from_file_location('oak_original_guard',_p)
g=importlib.util.module_from_spec(_s);_s.loader.exec_module(g)
ENGINE=Path('/Users/Shared/Epic Games/UE_5.8/Engine')

def normalized(v):
    length=math.sqrt(sum(x*x for x in v));return [x/length for x in v]

def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]

def camera_fit(source_bounds,camera):
    # The installed USDTypesConversion.cpp swaps Y and Z for Y-up and scales m→cm.
    lo,hi=source_bounds['min'],source_bounds['max']
    points=[[x*100,z*100,y*100] for x,y,z in itertools.product(*[(lo[i],hi[i]) for i in range(3)])]
    eye,target=camera['eyeCm'],camera['targetCm'];forward=normalized([t-e for t,e in zip(target,eye)])
    right=normalized(cross([0,0,1],forward));up=cross(forward,right)
    ht=math.tan(math.radians(camera['horizontalFovDegrees']/2));vt=ht*9/16
    rows=[]
    for p in points:
        q=[x-e for x,e in zip(p,eye)];depth=sum(a*b for a,b in zip(q,forward))
        x=sum(a*b for a,b in zip(q,right));y=sum(a*b for a,b in zip(q,up))
        rows.append({'pointCm':p,'depthCm':depth,'horizontalNormalized':x/(depth*ht),
                     'verticalNormalized':y/(depth*vt)})
    g.require(all(r['depthCm']>0 and abs(r['horizontalNormalized'])<1 and abs(r['verticalNormalized'])<1 for r in rows),
              'Original whole-D source bounds must fit the fixed source camera')
    return rows

def make_plan():
    extraction=g.read(g.SOURCE/'source-extraction-receipt.json');inspection=g.read(g.SOURCE/'usd-source-inspection-r1.json')
    selected=g.validate_source(extraction,inspection)
    base=g.BASE/'context-yard-ground-native-report.json';clone=g.OUTPUT/'oak-usd-project-clone.json'
    camera={'id':'english-oak-original-D-close-r1','label':'Original licensed English Oak D · isolated USD shape pilot',
            'eyeCm':[2000,-2800,700],'targetCm':[0,0,650],'horizontalFovDegrees':58,
            'source':'scripts/unreal/megaplants-english-oak-pilot-study-r2.py: full original D bounds; no source scaling',
            'presentation':{'intent':'Experimental original whole-USD geometry/constant-material inspection',
                            'sourceEvidence':'ORIGINAL_LICENSED_USD_SOURCE_BOUNDS_ONLY_NATIVE_VISIBILITY_PENDING'}}
    primary=[
      'Plugins/Importers/USDImporter/USDImporter.uplugin','Plugins/Runtime/USDCore/USDCore.uplugin',
      'Plugins/Interchange/Extensions/OpenUSD/InterchangeOpenUSD.uplugin',
      'Plugins/Experimental/ProceduralVegetationEditor/ProceduralVegetationEditor.uplugin',
      'Plugins/Importers/USDImporter/Source/USDStageImporter/Public/USDStageImportOptions.h',
      'Plugins/Importers/USDImporter/Source/USDStageImporter/Private/USDStageAssetImportFactory.h',
      'Plugins/Importers/USDImporter/Source/USDStageImporter/Private/USDStageAssetImportFactory.cpp',
      'Plugins/Importers/USDImporter/Source/USDStageImporter/Private/USDStageImporter.cpp',
      'Plugins/Importers/USDImporter/Source/USDSchemas/Private/USDNaniteAssemblyTranslator.cpp',
      'Plugins/Runtime/USDCore/Source/USDUtilities/Private/USDTypesConversion.cpp',
      'Plugins/Runtime/USDCore/Source/USDUtilities/Private/USDShadeConversion.cpp',
      'Plugins/Runtime/USDCore/Source/UnrealUSDWrapper/Public/UnrealUSDWrapper.h',
      'Source/Runtime/Engine/Classes/Engine/NaniteAssemblyData.h','Source/Runtime/Engine/Classes/Engine/SkeletalMesh.h',
      'Source/Runtime/Engine/Classes/Engine/EngineTypes.h','Source/Runtime/Engine/Classes/Components/SkeletalMeshComponent.h',
      'Source/Runtime/Engine/Classes/Kismet/KismetSystemLibrary.h',
      'Source/Editor/UnrealEd/Public/Subsystems/EditorActorSubsystem.h',
      'Source/Editor/UnrealEd/Private/Subsystems/EditorActorSubsystem.cpp',
      'Source/Editor/UnrealEd/Private/Factories/WorldFactory.cpp',
      'Source/Editor/UnrealEd/Classes/Factories/WorldFactory.h',
      'Source/Editor/LevelEditor/Public/LevelEditorSubsystem.h',
      'Source/Editor/UnrealEd/Private/Subsystems/EditorAssetSubsystem.cpp',
      'Source/Editor/MaterialEditor/Public/MaterialEditingLibrary.h',
      'Source/Runtime/Engine/Classes/Components/DirectionalLightComponent.h',
      'Source/Runtime/Engine/Classes/Components/SkyLightComponent.h',
      'Source/Runtime/Engine/Classes/Components/VolumetricCloudComponent.h',
      'Source/Runtime/Engine/Classes/Components/ExponentialHeightFogComponent.h',
      'Source/Runtime/Engine/Classes/Components/SkyAtmosphereComponent.h',
      'Source/Runtime/Engine/Classes/Components/LightComponent.h',
      'Source/Runtime/Engine/Classes/Components/LightComponentBase.h',
      'Plugins/Importers/USDImporter/Binaries/Mac/libUnrealEditor-USDStageImporter.dylib',
      'Plugins/Importers/USDImporter/Binaries/Mac/libUnrealEditor-USDSchemas.dylib',
      'Plugins/Runtime/USDCore/Binaries/Mac/libUnrealEditor-UnrealUSDWrapper.dylib',
      'Plugins/Importers/USDImporter/Binaries/Mac/UnrealEditor.modules',
      'Plugins/Runtime/USDCore/Binaries/Mac/UnrealEditor.modules']
    own=['megaplants-english-oak-source-r1.py','megaplants-english-oak-inspect-r1.py',
         'megaplants-english-oak-pilot-guards-r2.py','megaplants-english-oak-pilot-stage-r2.py',
         'megaplants-english-oak-pilot-native-r2.py','megaplants-english-oak-pilot-study-r2.py',
         'test_megaplants_english_oak_pilot_r2.py']
    base_record=g.read(base)
    pins=[g.pin(ENGINE/p) for p in primary]+[g.pin(g.ROOT/'scripts/unreal'/p) for p in own]
    pins += [g.pin(g.ROOT/'docs/unreal-megaplants-english-oak-pilot-r1.md'),g.pin(base),g.pin(clone),
             g.pin(g.SOURCE/'source-extraction-receipt.json'),g.pin(g.SOURCE/'usd-source-inspection-r1.json'),
             extraction['archive'],*[{k:r[k] for k in ('path','sha256','bytes')} for r in extraction['files']],
             base_record['afterContentInventory'],base_record['protectedProjectProof'],base_record['savedActorWitness'],
             g.pin(g.BASE/'root-native-byte-audit-r32a.json'),
             g.pin(g.BASE/'context-yard-ground-native.log.json'),g.pin(g.BASE/'context-yard-ground-native-process.json')]
    unique={r['path']:r for r in pins}
    bounds=selected['defaultTimeRootBoundsSourceUnits'][0]['bounds'];fit=camera_fit(bounds,camera)
    result={'schema':g.SCHEMA,'owner':'scripts/unreal/megaplants-english-oak-pilot-study-r2.py',
      'status':'source-ready-whole-original-D-native-pilot-pending','output':str(g.OUTPUT),'project':str(g.PROJECT),
      'namespace':g.PREFIX,'map':g.MAP,'pluginAddition':g.PLUGIN,
      'sourceArchive':extraction['archive'],'sourceExtraction':g.pin(g.SOURCE/'source-extraction-receipt.json'),
      'usdInspection':g.pin(g.SOURCE/'usd-source-inspection-r1.json'),'selectedUsd':selected['source'],
      'stageRoot':selected['rootPrims'][0],'sourceUpAxis':'Y','sourceMetersPerUnit':1.,
      'sourceWholeTreeBoundsMetres':bounds,'sourceBaseFanTriangles':1035730,
      'sourceUniquePrototypeFanTriangles':108253,'sourceUniqueBuildFanTriangles':1143983,
      'sourcePointInstancerMembers':188,'sourceBasePlusExpandedFanTrianglesEstimate':3680767,
      'sourceAllOriginalIndicesNormalsUvsTransformsPreserved':True,
      'baseNativeReport':g.pin(base),'initialRootClone':g.pin(clone),
      'baseProcessRaw':g.pin(g.BASE/'context-yard-ground-native.log.json'),
      'baseProcessTerminal':g.pin(g.BASE/'context-yard-ground-native-process.json'),
      'baseCurrentByteAudit':g.pin(g.BASE/'root-native-byte-audit-r32a.json'),
      'treePlacement':{'locationCm':[0,0,0],'rotationDegrees':[0,0,0],'scale':[1,1,1]},
      'ground':{'sizeCm':[4500,4500],'surfaceZCm':-2,'colorLinear':[.18,.18,.18],'roughness':.8,'specular':.25},
      'camera':camera,'cameraAspectRatio':16/9,'cameraSourceBoundsAllCornersInside':True,'cameraSourceFit':fit,
      'materialScope':'Exact original constant USD preview materials, no texture substitutions; separate authored neutral ground',
      'windSidecarAttachmentEstablished':False,'dynamicWindEvaluationAccepted':False,'materialSubstitutionAllowed':False,
      'licenseScope':'Accepted Fab EULA/NoAI; original content operation and arrangement only, no image generation or training',
      'actualAvailableBytesAtSourcePreflight':shutil.disk_usage(g.OUTPUT).free,'nativeLaunchMinimumFreeBytes':3*1024**3,
      'nativeScratchBytesEstimated':None,'nativeScratchCapEnforced':False,
      'rootExternalOwnPidDiskGrowthMonitorSuggestionBytes':2*1024**3,
      'nativeExecuted':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,
      'performanceAccepted':False,'shippingVerified':False,'packageVerified':False,
      'sourceRevision':2,'supersededUnusedSourcePlan':g.pin(g.SOURCE/'oak-usd-pilot-plan-r1.json'),
      'historicalBeforePinRepair':'Descriptor/camera before pins bind immutable R32 source instead of mutable own files',
      'inputFiles':sorted(unique.values(),key=lambda r:r['path'])}
    return result

def main():
    g.require(not g.PLAN.exists(),'Preserve immutable selected plan history')
    result=make_plan();g.write(g.PLAN,result)
    plan,base=g.validate_plan();g.validate_clone(plan,base)
    print(json.dumps({'plan':g.pin(g.PLAN),'inputFiles':len(plan['inputFiles']),
                      'actualAvailableBytes':result['actualAvailableBytesAtSourcePreflight'],'nativeExecuted':False}))

if __name__=='__main__':main()
