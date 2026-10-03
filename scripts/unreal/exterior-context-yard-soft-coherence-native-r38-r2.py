"""Root-only two-slot R38 material pilot; no geometry or instance mutators.

The original frozen reader policy is established without replaying historical
source generators. Full actor and raw instance hashes are read before and after
the save. GPU permission-field containment remains unverified.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-context-yard-soft-coherence-native-r38-r2.py'
_s=importlib.util.spec_from_file_location('r38_actual_guard',ROOT/'scripts/unreal/exterior-context-yard-soft-coherence-guards-r38-r2.py')
g=importlib.util.module_from_spec(_s);_s.loader.exec_module(g)
require,read,write,pin,sha,digest=(getattr(g,k)for k in ('require','read','write','pin','sha','digest'))
REPORT='soft-ground-native-report-r2.json'
STATUS='verified-saved-image-selected-fixed-world-soft-ground-material-overlay'
MAP='/Game/Brezi/Maps/Brezi'
def now():return datetime.now(timezone.utc).isoformat()


def helpers(bundle):
    """Minimal actual frozen reader packet, not historical load_donors()."""
    r=bundle['base']['report'];plan=read(g.checked(r['selectedPlan']))
    clean_plan=read(g.checked(plan['frozenFirstHelperEvidence']))
    clean=g.module('r38_frozen_clean_readers',clean_plan['ownedSources']['native']['live'])
    packet={'evidence':read(g.checked(clean_plan['reusedBaseEvidencePlan'])),
        'preservedGrassGroups':clean_plan['preservedGrassGroups']}
    h=clean.helpers(packet)
    h.update(cleanNative=clean,cleanBundle=packet,byteHelper=clean.g,
        materials=g.module('r38_owned_material_builder',pin(ROOT/'scripts/unreal/exterior-context-yard-soft-coherence-materials-r38-r2.py')),
        treeMaterials=g.module('r38_frozen_tree_reader',pin(ROOT/'scripts/unreal/exterior-original-tree-materials.py')))
    for name in ('exterior-realism-clean-integration-native-r27.py','exterior-original-tree-materials.py',
        'exterior-neighbor-finish-materials.py','exterior-neighbor-finish-native-r3.py','performance-optimize.py'):
        p=ROOT/'scripts/unreal'/name
        require(r['inputFiles'][str(p)]==sha(p),'Actual protected reader changed: '+name)
    return h


def project_state(bundle,h,after=False):
    byte=h['byteHelper'];base=bundle['base'];g.validate_clone(bundle,after)
    protected=byte.project_proof(g.PROJECT);content=byte.inventory(g.PROJECT/'Content')
    require(protected==base['protected']and byte.project_proof(base['project'])==base['protected']
        and byte.inventory(base['project']/'Content')==base['content'],'Original base or132 protected bytes changed')
    if after:delta=g.validate_content_delta(base['content'],content)
    else:require(content==base['content'],'Fresh own Content must equal selected actual base');delta=None
    return content,delta


def graph_records(bundle):
    r=bundle['base']['report'];expected=r['materialReadback']['graphs'];records={}
    routes=r['materialReaderDispatch']
    require({k:len(v)for k,v in routes.items()}=={'basic':49,'neighbor':9,'tree':3},'Closed49/9/3 source dispatch required')
    for row in r['materialGraphDiagnosticFiles']['saved']:
        value=read(g.checked(row));asset=value['asset'];graph=value['actualCompleteGraph']
        require(asset not in records and digest(graph)==value['actualCompleteGraphSha256']==expected[asset]['graphSha256']
            and asset in routes[value['reader']],'Actual complete saved61 graph identity differs')
        records[asset]={'graph':graph,'route':value['reader']}
    require(len(records)==61,'All61 original complete source graphs required')
    # Three actual saved donor graphs use the same basic reader. Their full
    # source shapes are available in the frozen source-plan donor receipts.
    for source in ('backdropR35','groundR32'):
        rdonor=read(g.checked(bundle['plan']['inputs'][source]))
        rows=[rdonor['repairC']['materialReport']]if source=='backdropR35'else list(rdonor['newMaterialReport']['materials'].values())
        for row in rows:
            require(row['asset']not in records and digest(row['graph'])==expected[row['asset']]['graphSha256'],'Exact three donor graph shapes required')
            records[row['asset']]={'graph':row['graph'],'route':'basic'}
    require(set(records)==set(expected)and len(records)==64,'All64 original full material graphs required')
    return records


def graph_snapshot(u,material,h,route='basic'):
    if route=='neighbor':return h['neighborMaterial'].graph_snapshot(u,material,h['existing'].graph_snapshot)
    if route=='tree':return h['treeMaterials'].graph_snapshot(u,material,h['existing'].graph_snapshot)
    require(route=='basic','Unknown material reader forbidden')
    return h['existing'].graph_snapshot(u,material)


def texture_witness(u,bundle,h):
    assets=bundle['base']['report']['materialReadback']['textureAssets'];require(len(set(assets))==len(assets)==96,'Exactly96 old textures required')
    result={}
    for asset in assets:
        texture=u.EditorAssetLibrary.load_asset(asset)
        require(isinstance(texture,u.Texture2D)and texture.get_path_name()==asset,'Actual original Texture2D missing')
        result[asset]=h['materials'].texture_snapshot(u,texture)
    return result


def material_witness(u,bundle,h,directory):
    require(not directory.exists(),'Fresh graph diagnostic directory required');directory.mkdir()
    records=graph_records(bundle);result={}
    for index,(asset,row)in enumerate(sorted(records.items())):
        m=u.EditorAssetLibrary.load_asset(asset);require(isinstance(m,u.Material),'Protected material missing')
        graph=graph_snapshot(u,m,h,row['route']);aux=h['materials'].aux_snapshot(u,m)
        usage={'instancedStaticMeshes':bool(u.MaterialEditingLibrary.has_material_usage(m,h['existing'].native_enum(u.MaterialUsage,'INSTANCEDSTATICMESHES'))),
            'nanite':bool(u.MaterialEditingLibrary.has_material_usage(m,u.MaterialUsage.MATUSAGE_NANITE))}
        got={'asset':asset,'reader':row['route'],'graph':graph,'graphSha256':digest(graph),'aux':aux,'usage':usage}
        write(directory/('graph-'+str(index).zfill(3)+'.json'),got)  # Observed shape preserved before rejection.
        require(graph==row['graph'],'Original complete material graph differs: '+asset)
        result[asset]=got
    return result


def raw_instance_controls(u,witness):
    """All existing ISM/HISM wrapped matrices, no Transform reconstruction."""
    controls={};total=0
    actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
    for actor in actors:
        for c in actor.get_components_by_class(u.InstancedStaticMeshComponent):
            path=c.get_path_name();data=c.get_editor_property('per_instance_sm_data');count=c.get_instance_count()
            require(len(data)==count,'Actual wrapped instance count differs')
            source=[v for v in witness[actor.get_path_name()]['components']if v['name']==c.get_name()]
            require(len(source)==1 and source[0]['instanceCount']==count,'Raw component must bind full witness')
            matrices=hashlib.sha256()
            for value in data:
                matrix=value.get_editor_property('transform')
                for plane in ('x_plane','y_plane','z_plane','w_plane'):
                    for axis in 'xyzw':matrices.update(struct.pack('<d',float(getattr(getattr(matrix,plane),axis))))
            try:
                ranges=c.get_editor_property('AdditionalRandomSeeds')
                additional={'available':True,'values':[{'startInstanceIndex':int(v.get_editor_property('StartInstanceIndex')),
                    'randomSeed':int(v.get_editor_property('RandomSeed'))}for v in ranges]}
            except Exception:additional={'available':False,'rangePreservationClaimed':False}
            controls[path]={'actor':actor.get_path_name(),'component':c.get_name(),'instances':count,
                'rawMatrixBinary64Sha256':matrices.hexdigest(),'mainRandomSeed':int(c.get_editor_property('instancing_random_seed')),
                'numCustomDataFloats':int(c.get_editor_property('num_custom_data_floats')),
                'customDataSha256':digest([float(v)for v in c.get_editor_property('per_instance_sm_custom_data')]),
                'additionalRandomSeeds':additional,'transformSeedOrInstanceMutationApisCalled':False}
            total+=count
    expected=[c for a in witness.values()for c in a['components']if 'instanceCount'in c]
    require(len(controls)==len(expected)and total==sum(c['instanceCount']for c in expected),'All existing instanced controls must be covered')
    return controls


def apply_two_slots(u,bundle,h,materials):
    for role,target in bundle['targets'].items():
        c=h['cleanNative'].component_lookup(u,target['actor'],target['component'])
        require(c.get_editor_property('static_mesh').get_path_name()==target['originalMesh']
            and c.get_material(0).get_path_name()==target['originalMaterial'],'Actual selected target mesh/material changed')
        c.set_material(0,materials[role])


def validate_plan(bundle=None):
    if bundle is None:bundle=g.load_contract()
    plan=read(g.PLAN)
    require(plan['schema']==g.SCHEMA and plan['schemaVersion']==2 and plan['owner']==OWNER
        and plan['status']=='image-selected-soft-ground-source-validated-native-pending'
        and plan['binding']==bundle['binding']and plan['expectedActorWitnessSha256']==digest(bundle['expected'])
        and plan['expectedCounts']=={'actors':5364,'hismComponents':2325,'hismInstances':678197,'originalMaterialGraphs':64,
            'originalTextureObjects':96,'newMaterialGraphs':2,'newTextureObjects':1,'newPackages':3,'contentFiles':4103,'protectedFiles':132}
        and plan['nativeExecuted']is False and plan['repairSchema']==g.REPAIR_SCHEMA and plan['repairEvidence']==bundle['repairEvidence'],'Closed final actual selected plan required')
    require(all(sha(p)==value for p,value in plan['inputFiles'].items()),'Frozen final consumed source differs')
    return plan,bundle


def validate_preflight(path,plan,bundle):
    pf=read(path)
    require(pf['schema']==g.SCHEMA and pf['owner']==OWNER and pf['status']=='image-selected-soft-ground-source-preflight-validated-native-pending'
        and pf['selectedPlan']==pin(g.PLAN)and pf['binding']==bundle['binding']and pf['nativeExecuted']is False
        and pf['inputFiles']=={**plan['inputFiles'],str(g.PLAN):sha(g.PLAN)}
        and pf['cpuTests']['exitCode']==0 and pf['schemaVersion']==2 and pf['repairSchema']==g.REPAIR_SCHEMA,'Exact executed preflight required')
    require(all(sha(p)==v for p,v in pf['inputFiles'].items()),'Consumed preflight sources differ')
    return pf


def main():
    import unreal as u
    require(Path(os.environ['BREZI_SOFT_GROUND_OUTPUT']).resolve()==g.CANDIDATE
        and Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==g.PROJECT,'Only exact owned R38 candidate allowed')
    require(sha(g.PLAN)==os.environ['BREZI_SOFT_GROUND_PLAN_SHA256'],'Final frozen plan differs')
    pf_path=Path(os.environ['BREZI_SOFT_GROUND_PREFLIGHT']).resolve()
    require(pf_path==g.STUDY/'source-preflight/source-preflight.json'and sha(pf_path)==os.environ['BREZI_SOFT_GROUND_PREFLIGHT_SHA256'],'Final frozen preflight differs')
    require(not(g.CANDIDATE/REPORT).exists(),'Fresh native report required')
    plan,bundle=validate_plan();pf=validate_preflight(pf_path,plan,bundle)
    checkpoint=g.CANDIDATE/'soft-ground-checkpoint';require(not checkpoint.exists(),'Fresh checkpoint required');checkpoint.mkdir()
    report={'schema':g.SCHEMA,'schemaVersion':2,'owner':OWNER,'status':'running','startedAt':now(),'nativeProcessId':os.getpid(),
        'output':str(g.CANDIDATE),'project':str(g.PROJECT),'selectedPlan':pin(g.PLAN),'sourcePreflight':pin(pf_path),
        'sourceStudy':bundle['source'],'binding':bundle['binding'],'repairSchema':g.REPAIR_SCHEMA,'repairEvidence':bundle['repairEvidence'],'baseNativeReport':bundle['base']['reportPin'],
        'baseNativeProcess':bundle['base']['process'],'selectedRootImageDecision':bundle['base']['selection'],
        'baseCurrentByteAudit':bundle['base']['audit'],'projectClone':bundle['base']['clone'],
        'baseContentInventory':bundle['base']['report']['afterContentInventory'],'protectedProjectProof':bundle['base']['report']['protectedProjectProof'],
        'inputFiles':pf['inputFiles'],'nativeApplied':False,'savedMapUnloadedReloaded':False,
        'activeDesign':{'variant':'C','heatingLayout':'B','livingLayout':'B'},'setbacksMm':{'street':3000,'east':3000},
        'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False,
        'activeOutputPromoted':False,'nativeGpuOutsideEquivalenceVerified':False,'nativeGpuPixelFormatVerified':False,
        'nativeTexelsDecoded':False,'freshNativeGeometryAttributeReadback':False,'nativeNormalTangentReadbackAvailable':False,
        'newActors':0,'newMeshes':0,'originalGeometryAndRootMutationApisCalled':False,'sourcePhotoPixelsEdited':False}
    write(g.CANDIDATE/REPORT,report)
    try:
        h=helpers(bundle);h['materials'].preflight_enums(u);h['materials'].preflight_reflection(u)
        content,_=project_state(bundle,h)
        module=g.PROJECT/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib';origin=bundle['base']['project']/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'
        require(sha(module)==sha(origin)==g.MODULE_SHA and read(g.PROJECT/'Binaries/Mac/UnrealEditor.modules')['BuildId']=='55116800'
            and(module.stat().st_dev,module.stat().st_ino)!=(origin.stat().st_dev,origin.stat().st_ino),'Original Recipe4 module must be exact and independent')
        report['moduleOrderWitness']=h['moduleOrderWitness'];report['nativeModuleWitness']={'source':str(origin),'destination':str(module),
            'sha256':sha(module),'bytes':module.stat().st_size,'independentInodes':True}
        levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot load own map')
        before=h['cleanNative'].full_witness(u,h);require(before==bundle['base']['before'],'Whole selected actual5364 scene differs')
        raw=raw_instance_controls(u,before)
        old_graphs=material_witness(u,bundle,h,checkpoint/'graphs-before');old_textures=texture_witness(u,bundle,h)
        for name,value in [('before-actors',before),('expected-actors',bundle['expected']),('raw-controls-before',raw),('old-materials-before',old_graphs),('old-textures-before',old_textures)]:write(checkpoint/(name+'.json'),value)
        reader=lambda unreal,material:graph_snapshot(unreal,material,h)
        textures=lambda unreal:texture_witness(unreal,bundle,h)
        materials,built=h['materials'].build_materials(u,bundle,bundle['binding'],reader,textures)
        apply_two_slots(u,bundle,h,materials)
        require(h['cleanNative'].full_witness(u,h)==bundle['expected'],'Two-slot full counterfactual differs before save')
        require(levels.save_current_level(),'Cannot save own material-only candidate map')
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot unload/reload saved candidate')
        saved=h['cleanNative'].full_witness(u,h);require(saved==bundle['expected'],'Saved full two-slot counterfactual differs')
        raw_saved=raw_instance_controls(u,saved);require(raw_saved==raw,'Every original raw matrix/mainseed/custom/order must remain exact')
        h['materials'].verify_materials(u,bundle,bundle['binding'],built,reader,textures)
        saved_graphs=material_witness(u,bundle,h,checkpoint/'graphs-saved');saved_textures=texture_witness(u,bundle,h)
        require(saved_graphs==old_graphs and saved_textures==old_textures,'Original64 graph/aux/usage or96 texture settings changed')
        content,delta=project_state(bundle,h,True);require(len(content)==4103,'Exactly4103 final Content files required')
        hisms=[c for actor in saved.values()for c in actor['components']if c['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent']
        require((len(saved),len(hisms),sum(c['instanceCount']for c in hisms))==(5364,2325,678197),'Saved full original census differs')
        require(all(sha(p)==v for p,v in pf['inputFiles'].items()),'Frozen consumed source changed')
        for name,value in [('saved-actors',saved),('raw-controls-saved',raw_saved),('old-materials-saved',saved_graphs),('old-textures-saved',saved_textures),('after-content',content),('new-materials',built)]:write(checkpoint/(name+'.json'),value)
        report.update(status=STATUS,completedAt=now(),nativeApplied=True,savedMapUnloadedReloaded=True,sourceInputsUnchanged=True,
            beforeActorWitness=pin(checkpoint/'before-actors.json'),expectedActorWitness=pin(checkpoint/'expected-actors.json'),savedActorWitness=pin(checkpoint/'saved-actors.json'),
            beforeActorWitnessSha256=digest(before),expectedActorWitnessSha256=digest(bundle['expected']),savedActorWitnessSha256=digest(saved),
            rawInstanceControlsBefore=pin(checkpoint/'raw-controls-before.json'),rawInstanceControlsSaved=pin(checkpoint/'raw-controls-saved.json'),
            allOriginalRawMatricesMainSeedsCustomDataExact=True,additionalSeedRangesPreservationClaimed=False,
            originalMaterialWitnessBefore=pin(checkpoint/'old-materials-before.json'),originalMaterialWitnessSaved=pin(checkpoint/'old-materials-saved.json'),
            originalTextureWitnessBefore=pin(checkpoint/'old-textures-before.json'),originalTextureWitnessSaved=pin(checkpoint/'old-textures-saved.json'),
            newMaterialReport=pin(checkpoint/'new-materials.json'),newMaterials=built,
            materialGraphDiagnosticFiles={phase:[pin(p)for p in sorted((checkpoint/('graphs-'+phase)).glob('graph-*.json'))]for phase in ('before','saved')},
            afterContentInventory=pin(checkpoint/'after-content.json'),assetDelta=delta,newPackages=built['newPackageAssets'],
            actualCounts={'savedActors':5364,'fullHismComponents':2325,'fullHismInstances':678197,'scopedMaterialGraphs':66,
                'scopedTextureObjects':97,'contentFiles':4103,'protectedFiles':132,'newPackages':3},
            nativeMaskPropertyPolicyVerified=True,original64MaterialGraphsAndAuxExact=True,original96TextureSettingsAndPackagesExact=True)
        write(g.CANDIDATE/REPORT,report);print(json.dumps({'report':pin(g.CANDIDATE/REPORT),'status':STATUS}))
    except Exception as error:
        report.update(status='failed',completedAt=now(),error=str(error));write(g.CANDIDATE/REPORT,report);raise


if __name__=='__main__':main()
