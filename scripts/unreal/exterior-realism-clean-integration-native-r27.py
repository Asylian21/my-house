"""Root-only clean four-donor save into original R16; no grass restoration.

Only two leaf variants, neighbor retained chunks/new32 actors, 601 culls and
foreground5 actors are admitted. R20/R23 assets/mutators are never loaded.
"""
import copy
import hashlib
import os
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-realism-clean-integration-native-r27.py'
spec=__import__('importlib.util',fromlist=['spec_from_file_location'])
handle=spec.spec_from_file_location('r27_native_guard',ROOT/'scripts/unreal/exterior-realism-clean-integration-guards-r27.py')
guard=spec.module_from_spec(handle);handle.loader.exec_module(guard)
g=guard.g
require,read,write,sha,pin,check_pin,digest,now=(getattr(guard,k)for k in ('require','read','write','sha','pin','check_pin','digest','now'))
STATUS='verified-saved-four-donor-clean-exterior-realism-integration'
MAP='/Game/Brezi/Maps/Brezi'
REPORT='realism-clean-integration-native-report.json'
MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574'


def policy_witness(evidence,before=None):
    expected=check_pin(evidence['frozenPipeline'][str(ROOT/'scripts/unreal/performance_scene_policy.py')])
    cached=sys.modules.get('performance_scene_policy')
    require(cached is not None and Path(cached.__file__).resolve()==expected.resolve()
        and (before is None or cached is before),'Frozen original policy must survive all nested imports')
    return {'path':str(expected),'sha256':sha(expected),'bytes':expected.stat().st_size,
        'cachePreservedAcrossReusedHelpers':True,'cacheDeletedOrReplaced':False}


def helpers(bundle):
    importer,existing=g.frozen_modules(bundle['evidence'])
    frozen=sys.modules.get('performance_scene_policy');policy_witness(bundle['evidence'])
    def load(key,file):return guard.module('r27_reused_'+key,file)
    neighbor=load('neighbor','exterior-neighbor-finish-native-r3.py')
    foreground=load('foreground','exterior-canopy-foreground-native-r2.py')
    material=load('neighbor_material','exterior-neighbor-finish-materials.py')
    performance=load('extended_witness','performance-optimize.py')
    return {'neighbor':neighbor,'foreground':foreground,'neighborMaterial':material,'performance':performance,
        'moduleOrderWitness':policy_witness(bundle['evidence'],frozen),'importer':importer,'existing':existing,
        'rural':importer.rural,'meshHelper':importer.mesh_helper}


def full_witness(u,h):
    return guard.union_witness(g.native_witness(u,h['importer']),
        h['neighbor'].original_witness(u,u.get_editor_subsystem(u.EditorActorSubsystem),h['performance']))

def component_lookup(u,actor_path,name_or_path):
    actors={a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
    require(actor_path in actors,'Declared existing component actor missing')
    rows=[c for c in actors[actor_path].get_components_by_class(u.PrimitiveComponent)
        if c.get_name()==name_or_path or c.get_path_name()==name_or_path]
    require(len(rows)==1,'Declared component ambiguous');return rows[0]

def neighbor_material_assets(bundle,rows):
    new=bundle['reports']['neighbors']['materials']['materials'];original=bundle['base']['materials']['materials']
    needed={row['material']for row in rows};retained=needed-set(new)
    require(len(rows)==37 and len(new)==9 and len(needed)==13
        and retained=={'context_boundary_post','context_village_roof','context_village_wall','context_wire'}
        and retained<=set(original),'Exact37 neighbor rows need9 new plus4 original retained material keys')
    return {key:(new if key in new else original)[key]['asset']for key in sorted(needed)}

def apply_leaf_and_visibility(u,bundle):
    leaf=[];culls=[];retained=0
    for delta in bundle['reports']['leaf']['componentBindings']:
        c=component_lookup(u,delta['actor'],delta['component'])
        require(c.get_num_materials()==2 and c.get_material(0).get_path_name()==delta['barkSlot0']
            and c.get_material(1).get_path_name()==delta['before'],'Original component leaf/bark binding changed')
        value=u.EditorAssetLibrary.load_asset(delta['after']);require(value,'Copied leaf variant missing')
        c.set_material(1,value);leaf.append(copy.deepcopy(delta))
    for delta in bundle['reports']['visibility']['componentCullOverrides']:
        c=component_lookup(u,delta['actor'],delta['component'])
        expected=guard.component(bundle['expectedOriginal'],delta['actor'],delta['component'])
        require(isinstance(c,u.HierarchicalInstancedStaticMeshComponent)
            and c.get_instance_count()==expected['instanceCount']
            and c.get_editor_property('static_mesh').get_path_name()==expected['mesh']
            and [c.get_editor_property(k)for k in ('instance_start_cull_distance','instance_end_cull_distance')]==delta['beforeCullCm'],
            'Exact retained visibility target/model/original distances differ')
        c.set_cull_distances(*delta['afterCullCm']);row=copy.deepcopy(delta);row['retainedInstances']=c.get_instance_count()
        culls.append(row);retained+=c.get_instance_count()
    require(len(leaf)==23 and len(culls)==601 and retained==501890,'Exact leaf/cull combined scope differs')
    return leaf,culls

def verify_materials(u,bundle,h):
    reports=bundle['reports'];existing=h['existing']
    original=g.original_material_readback(u,existing,bundle['base'])
    leaf_plan=read(check_pin(reports['leaf']['selectedPlan']))
    leaf=g.variant_readback(u,existing,leaf_plan,reports['leaf']['selectedPlan']['sha256'])
    require(leaf==reports['leaf']['variants'],'Copied leaf variants differ from actual saved donor')
    h['neighborMaterial'].verify_materials(u,reports['neighbors']['materials'],existing.graph_snapshot)
    floor=u.EditorAssetLibrary.load_asset(reports['foreground']['newMaterial']['asset'])
    require(floor and existing.graph_snapshot(u,floor)==reports['foreground']['savedReadback']['materialGraph'],
        'Copied floor graph differs from actual saved donor')
    materials={r['asset']for r in original['graphs'].values()}|{r['asset']for r in leaf.values()}|{r['asset']for r in reports['neighbors']['materials']['materials'].values()}|{reports['foreground']['newMaterial']['asset']}
    textures={r['asset']for r in original['textures'].values()}|{r['asset']for r in reports['neighbors']['materials']['textures'].values()}
    require(len(materials)==54 and len(textures)==77,'Exact scoped54 graphs/77 textures required')
    return {'original':original,'leaf':leaf,'neighbor':reports['neighbors']['materials'],'foreground':reports['foreground']['newMaterial'],
        'scopedMaterialGraphs':54,'scopedTextureObjects':77,'verifiedMaterialAssets':sorted(materials),'verifiedTextureAssets':sorted(textures)}


def original_grass_controls(u,bundle):
    """Read only. All8949 raw matrices/control values; no member/seed setter."""
    result={}
    for row in bundle['preservedGrassGroups']:
        c=component_lookup(u,row['actor'],row['component']);data=c.get_editor_property('per_instance_sm_data')
        require(c.get_instance_count()==len(data)==row['instances'],'Original grass population changed')
        matrix_hash=hashlib.sha256()
        for member in data:
            matrix=member.get_editor_property('transform')
            for plane in ('x_plane','y_plane','z_plane','w_plane'):
                for axis in 'xyzw':matrix_hash.update(struct.pack('<d',float(getattr(getattr(matrix,plane),axis))))
        try:
            ranges=c.get_editor_property('AdditionalRandomSeeds')
            seed_ranges={'available':True,'ranges':[{'startInstanceIndex':int(r.get_editor_property('StartInstanceIndex')),
                'randomSeed':int(r.get_editor_property('RandomSeed'))}for r in ranges]}
        except Exception as error:
            seed_ranges={'available':False,'error':str(error),'rangeValuesObserved':False,'rangePreservationClaimed':False}
        result[row['groupId']]={'actor':row['actor'],'instances':len(data),'rawMatrixBinary64Sha256':matrix_hash.hexdigest(),
            'instancingRandomSeed':int(c.get_editor_property('instancing_random_seed')),
            'numCustomDataFloats':int(c.get_editor_property('num_custom_data_floats')),
            'customDataSha256':digest([float(v)for v in c.get_editor_property('per_instance_sm_custom_data')]),
            'additionalRandomSeeds':seed_ranges,'originalMemberMutationApisCalled':False,'seedRangeMutationApisCalled':False}
    require(len(result)==4 and sum(r['instances']for r in result.values())==8949,'Original grass controls scope differs')
    return result


def independent_copied_project(plan,bundle,output):
    project=output/'Project/BreziTwin';base=guard.BASE/'Project/BreziTwin'
    clone_path=output/'realism-clean-integration-project-clone.json';copy_path=output/'realism-clean-integration-package-copy.json'
    clone,copied=read(clone_path),read(copy_path)
    require(clone['schema']==guard.SCHEMA and clone['owner']==guard.COPY_OWNER and clone['status']==guard.CLONE_STATUS
        and clone['selectedPlan']==pin(guard.PLAN)and clone['baseNativeReport']==plan['baseNativeReport']
        and clone['project']==str(project)and clone['originalFileCount']==4107 and clone['newCopiedPackageCount']==59
        and clone['contentFileCount']==4034 and clone['nativeExecuted']is False and clone['packageCopyReceipt']==pin(copy_path)
        and clone['baseContentInventory']==plan['baseContentInventory']and clone['baseProjectProof']==plan['baseProjectProof']
        and clone['originalFilesIndependentAndByteIdentical']is True and clone['copiedPackagesIndependentAndByteIdentical']is True,
        'Typed clean original plus59 saved-package clone required')
    initial=pin(output/'clean-realism-integration-base-clone-proof.json')
    require(clone['originalBaseCloneProof']==initial and copied['originalBaseCloneProof']==initial,'Actual pending clone pin differs')
    pending=read(check_pin(initial))
    require(pending['status']==guard.INITIAL_STATUS and pending['selectedPlan']is None and pending['packageCopyPending']is True
        and pending['nativeExecuted']is False and pending['fileCount']==4107 and pending['baseNativeReport']==plan['baseNativeReport'],
        'Historical actual root pending-clone contract differs')
    expected_copies=[{**row,'destination':str(project/'Content'/row['relativeContentPath']),'independentInodes':True}for row in bundle['packages']]
    require(copied['schema']==guard.SCHEMA and copied['owner']==guard.COPY_OWNER and copied['status']==guard.COPY_STATUS
        and copied['selectedPlan']==pin(guard.PLAN)and copied['baseNativeReport']==plan['baseNativeReport']
        and copied['project']==str(project)and copied['copiedPackages']==expected_copies and copied['copiedPackageCount']==59
        and copied['nativeExecuted']is False and copied['sceneMapChanged']is False and copied['viewpointsChanged']is False
        and copied['excludedDonors']==['R20_CURVED_GRASS','R23_CREAM_ROOF']and copied['originalGrassInstanceDataNeverWritten']is True,
        'Actual clean saved-package copy scope differs')
    expected=copy.deepcopy(bundle['content']);expected.update({r['relativeContentPath']:{'sha256':r['sha256'],'bytes':r['bytes']}for r in bundle['packages']})
    require(g.inventory(project/'Content')==expected and g.project_proof(project)==bundle['protected']
        and g.inventory(base/'Content')==bundle['content']and g.project_proof(base)==bundle['protected'],'Fresh original/candidate bytes differ')
    for directory,rows in (('Content',bundle['content']),('',bundle['protected'])):
        for relative in rows:
            a,b=base/directory/relative,project/directory/relative
            require((a.stat().st_dev,a.stat().st_ino)!=(b.stat().st_dev,b.stat().st_ino),'Original hardlink forbidden')
    for row in bundle['packages']:
        a,b=Path(row['source']),project/'Content'/row['relativeContentPath']
        require((a.stat().st_dev,a.stat().st_ino)!=(b.stat().st_dev,b.stat().st_ino),'Copied saved-package hardlink forbidden')
    return project,expected


def main():
    import unreal as u
    plan_path=Path(os.environ['BREZI_CLEAN_REALISM_PLAN']).resolve()
    require(plan_path==guard.PLAN and sha(plan_path)==os.environ['BREZI_CLEAN_REALISM_PLAN_SHA256'],'Selected clean plan changed')
    plan,bundle=guard.validate_plan(plan_path)
    output=Path(os.environ['BREZI_CLEAN_REALISM_OUTPUT']).resolve();require(output==guard.CANDIDATE,'Only own fresh R27a may change')
    project,content_before=independent_copied_project(plan,bundle,output)
    require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==project
        and Path(u.Paths.engine_dir()).resolve()==Path('/Users/Shared/Epic Games/UE_5.8/Engine'),'Wrong own project/engine')
    require(not(output/'exterior-import-report.json').exists()and not(output/REPORT).exists(),'No copied original/prior clean native report')
    require(sha(project/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib')==MODULE_SHA
        and read(project/'Binaries/Mac/UnrealEditor.modules')['BuildId']=='55116800','Actual module/BuildId differs')
    h=helpers(bundle);reports=bundle['reports'];receipt=output/REPORT
    state={'schema':guard.SCHEMA,'owner':OWNER,'status':'running','startedAt':now(),'nativeProcessId':os.getpid(),
        'output':str(output),'project':str(project),'selectedPlan':pin(plan_path),'baseNativeReport':plan['baseNativeReport'],
        'savedDonors':plan['donors'],'inputFiles':plan['inputFiles'],'ownedSources':plan['ownedSources'],
        'moduleOrderWitness':h['moduleOrderWitness'],'projectClone':pin(output/'realism-clean-integration-project-clone.json'),
        'copiedPackageReceipt':pin(output/'realism-clean-integration-package-copy.json'),
        'activeDesign':bundle['base']['activeDesign'],'setbacksMm':bundle['base']['setbacksMm'],
        'nativeModuleWitness':{'source':str(guard.BASE/'Project/BreziTwin/Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),
            'destination':str(project/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),'sha256':MODULE_SHA,'bytes':2818384,'independentInodes':True},
        'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingPackageProduced':False,
        'knownReviewLimits':plan['knownReviewLimits'],'combinedAppearanceGoNoGo':plan['combinedAppearanceGoNoGo'],
        'excludedDonors':plan['excludedDonors'],'originalGrassMemberMutationApisCalled':False,'seedRangeMutationApisCalled':False,
        'nativeMaterialPackagesIndependentlyReloaded':False,'nativeMeshPackagesIndependentlyReloaded':False}
    write(receipt,state)
    try:
        levels=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot load own original R16 map')
        before=full_witness(u,h);require(before==bundle['before'],'Actual original full5306 witness differs')
        original_readback=h['importer'].readback(u,bundle['base']['geometry'])
        materials_before=verify_materials(u,bundle,h);grass_before=original_grass_controls(u,bundle)
        write(output/'clean-witness-before.json',before);write(output/'clean-materials-before.json',materials_before)
        write(output/'clean-original-grass-controls-before.json',grass_before)
        leaf,culls=apply_leaf_and_visibility(u,bundle)
        neighbor_bundle=h['neighbor'].guard.validated_candidate();neighbor_rows=h['neighbor'].export_records(neighbor_bundle)
        neighbor_paths=reports['neighbors']['meshes'];neighbor_meshes={k:u.EditorAssetLibrary.load_asset(v)for k,v in neighbor_paths.items()}
        neighbor_materials={k:u.EditorAssetLibrary.load_asset(v)for k,v in neighbor_material_assets(bundle,neighbor_rows).items()}
        require(all(neighbor_materials.values()),'Exact9 new/4 retained neighbor materials must load')
        target_components=h['neighbor'].affected_components(u,actors,bundle['base'],neighbor_bundle)
        changes,neighbor_added=h['neighbor'].apply_scene(u,neighbor_bundle,neighbor_rows,neighbor_meshes,target_components,h['rural'])
        require(changes==reports['neighbors']['componentChanges'],'Exact6 neighbor changes differ')
        neighbor_initial=h['neighbor'].verify_scene(u,neighbor_bundle,neighbor_rows,neighbor_paths,changes,neighbor_added,
            neighbor_materials,h['meshHelper'],h['rural'])
        foreground_bundle=h['foreground'].guard.load_source();floor=u.EditorAssetLibrary.load_asset(reports['foreground']['newMesh'])
        foreground_added=h['foreground'].apply_scene(u,foreground_bundle,floor,h['rural'])
        foreground_before=h['foreground'].verify_scene(u,foreground_bundle,foreground_added,reports['foreground']['newMesh'],
            reports['foreground']['newMaterial']['asset'],h['rural'],h['existing'],h['meshHelper'])
        added={**{'neighbors:'+k:v for k,v in neighbor_added.items()},**{'foreground:'+k:v for k,v in foreground_added.items()}}
        expected=guard.compose_all_expected(bundle['expectedOriginal'],bundle['templates'],added)
        require(full_witness(u,h)==expected,'Actual clean composition exceeds explicit5343 counterfactual')
        require(original_grass_controls(u,bundle)==grass_before,'Original grass raw matrices/mainseed/custom data changed before save')
        write(output/'clean-witness-expected.json',expected)
        view_file=project/'Content/Data/viewpoints.json';source_view=check_pin(plan['diagnosticViewpoints'])
        require(view_file.read_bytes()==(guard.BASE/'Project/BreziTwin/Content/Data/viewpoints.json').read_bytes(),'Original camera changed before append')
        view_file.write_bytes(source_view.read_bytes())
        require(levels.save_current_level(),'Cannot save own clean scene')
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot unload/reload saved clean scene')
        after=full_witness(u,h);require(after==expected,'Saved full5343 witness differs from clean counterfactual')
        hisms=[c for row in after.values()for c in row['components']if c['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent']
        require(len(hisms)==2309 and sum(c['instanceCount']for c in hisms)==676944,'Actual clean HISM scope differs')
        original_geometry=copy.deepcopy(bundle['originalGeometryAfter']);delegated=h['importer'].readback(u,original_geometry)
        require(delegated['groupCount']==1980 and delegated['instanceCount']==632026,'All original plant members/ownership must survive')
        grass_saved=original_grass_controls(u,bundle);require(grass_saved==grass_before,'Saved original grass raw matrices/observed seed/custom data differ')
        neighbor_saved=h['neighbor'].verify_scene(u,neighbor_bundle,neighbor_rows,neighbor_paths,changes,neighbor_added,
            neighbor_materials,h['meshHelper'],h['rural'])
        require(neighbor_saved==neighbor_initial,'All37 saved neighbor source/default material/policies differ')
        foreground_saved=h['foreground'].verify_scene(u,foreground_bundle,foreground_added,reports['foreground']['newMesh'],
            reports['foreground']['newMaterial']['asset'],h['rural'],h['existing'],h['meshHelper'])
        require(foreground_saved==foreground_before,'Saved floor/graph/4groups/512 transforms differ')
        materials_saved=verify_materials(u,bundle,h);require(materials_saved==materials_before,'Old/copied graph or texture changed')
        after_content=g.inventory(project/'Content');delta=guard.validate_content(bundle['content'],after_content,bundle['packages'],plan['diagnosticViewpoints']['sha256'])
        require(g.project_proof(project)==bundle['protected']and g.inventory(guard.BASE/'Project/BreziTwin/Content')==bundle['content']
            and g.project_proof(guard.BASE/'Project/BreziTwin')==bundle['protected'],'Protected/original source project changed')
        guard.validate_plan(plan_path);require(sha(plan_path)==os.environ['BREZI_CLEAN_REALISM_PLAN_SHA256'],'Plan changed during native')
        for name,value in (('clean-witness-saved.json',after),('clean-content-after.json',after_content),('clean-materials-saved.json',materials_saved),
            ('clean-effective-original-geometry.json',original_geometry),('clean-original-grass-controls-saved.json',grass_saved)):write(output/name,value)
        state.update(status=STATUS,completedAt=now(),savedMapUnloadedReloaded=True,originalR16Unchanged=True,sourceInputsUnchanged=True,
            actualAudit=plan['audit'],scopeAudit=plan['scopeAudit'],leafComponentBindings=leaf,componentCullOverrides=culls,
            neighborChanges=changes,newNeighborActors=neighbor_added,neighborReadback=neighbor_saved,
            newForegroundActors=foreground_added,foregroundReadback=foreground_saved,addedActorIdentityMap=added,
            baseGeometryReadback=original_readback,savedOriginalGeometryReadback=delegated,
            beforeActorWitnessSha256=digest(before),expectedActorWitnessSha256=digest(expected),savedActorWitnessSha256=digest(after),
            beforeActorWitness=pin(output/'clean-witness-before.json'),expectedActorWitness=pin(output/'clean-witness-expected.json'),
            savedActorWitness=pin(output/'clean-witness-saved.json'),afterContentInventory=pin(output/'clean-content-after.json'),
            originalGeometryAfter=pin(output/'clean-effective-original-geometry.json'),materialsBefore=pin(output/'clean-materials-before.json'),
            materialsSaved=pin(output/'clean-materials-saved.json'),originalGrassControlsBefore=pin(output/'clean-original-grass-controls-before.json'),
            originalGrassControlsSaved=pin(output/'clean-original-grass-controls-saved.json'),originalGrassRawMatricesAndObservedSeedControlsExact=True,
            protectedProjectProof=plan['baseProjectProof'],assetDelta=delta,scopedMaterialGraphs=54,scopedTextureObjects=77,
            originalPlantMastersPreserved=135,originalPlantLodsPreserved=405,originalExteriorOwnershipSpoofed=False,
            nativeNormalTangentReadbackAvailable=False,actualFullSceneHismComponents=len(hisms),actualFullSceneHismInstances=sum(c['instanceCount']for c in hisms),
            actualRecordedExteriorHismGroups=delegated['groupCount']+foreground_saved['savedGroups'],
            actualRecordedExteriorHismInstances=delegated['instanceCount']+foreground_saved['savedInstances'],
            diagnosticViewpoints=pin(view_file),donorFilesNeverMutated=True)
        write(receipt,state);print(__import__('json').dumps({'status':STATUS,'report':pin(receipt),'audit':plan['audit'],'nativeAppearanceAccepted':False}))
    except Exception as error:
        state.update(status='failed',error=str(error),completedAt=now());write(receipt,state);raise


if __name__=='__main__':main()
