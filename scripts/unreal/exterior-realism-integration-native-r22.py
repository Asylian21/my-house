"""Root-only saved-donor scene composition into a fresh original R16 clone.

No geometry/material import or original asset edits. Exact74 already saved
packages are copied before launch; this helper applies only declared components
and independently witnessed new actors, then saves/unloads/reloads the map.
"""
import copy
import os
from pathlib import Path
import sys

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-realism-integration-native-r22.py'
spec=__import__('importlib.util',fromlist=['spec_from_file_location'])
handle=spec.spec_from_file_location('r22_native_composition_guard',ROOT/'scripts/unreal/exterior-realism-integration-guards-r22.py')
guard=spec.module_from_spec(handle);handle.loader.exec_module(guard)
g=guard.g
require,read,write,sha,pin,check_pin,digest,now=(getattr(guard,k)for k in ('require','read','write','sha','pin','check_pin','digest','now'))
STATUS='verified-saved-six-donor-exterior-realism-integration'
MAP='/Game/Brezi/Maps/Brezi'
REPORT='realism-integration-native-report.json'
MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574'


def helpers(bundle):
    def load(key,file):return guard.module('r22_reused_'+key,file)
    neighbor=load('neighbor','exterior-neighbor-finish-native-r3.py')
    grass=load('grass','exterior-curved-grass-native-r4.py')
    foreground=load('foreground','exterior-canopy-foreground-native-r2.py')
    roof=load('roof','exterior-roof-pbr-native.py')
    material=load('neighbor_material','exterior-neighbor-finish-materials.py')
    performance=load('extended_witness','performance-optimize.py')
    importer,existing=g.frozen_modules(bundle['evidence'])
    return {'neighbor':neighbor,'grass':grass,'foreground':foreground,'roof':roof,'neighborMaterial':material,
        'performance':performance,'importer':importer,'existing':existing,'rural':importer.rural,'meshHelper':importer.mesh_helper}


def full_witness(u,h):
    return guard.union_witness(g.native_witness(u,h['importer']),
        h['neighbor'].original_witness(u,u.get_editor_subsystem(u.EditorActorSubsystem),h['performance']))


def verify_materials(u,bundle,h):
    reports=bundle['reports'];existing=h['existing']
    original=g.original_material_readback(u,existing,bundle['base'])
    leaf_plan=read(check_pin(reports['leaf']['selectedPlan']))
    leaf=g.variant_readback(u,existing,leaf_plan,reports['leaf']['selectedPlan']['sha256'])
    require(leaf==reports['leaf']['variants'],'Copied leaf variants differ from actual saved donor')
    h['neighborMaterial'].verify_materials(u,reports['neighbors']['materials'],existing.graph_snapshot)
    h['grass'].maps.verify_materials(u,reports['grass']['materialReport'],existing.graph_snapshot)
    roof_bundle=h['roof'].guard.load_source()
    h['roof'].materials.verify(u,reports['roof']['materialReport'],existing.graph_snapshot,
        roof_bundle['recipe'],h['roof'].guard.PLAN_SHA)
    floor=u.EditorAssetLibrary.load_asset(reports['foreground']['newMaterial']['asset'])
    require(floor and existing.graph_snapshot(u,floor)==reports['foreground']['savedReadback']['materialGraph'],
            'Copied floor graph differs from actual saved donor')
    material_paths={row['asset']for row in original['graphs'].values()}|{row['asset']for row in leaf.values()} \
        |{row['asset']for row in reports['neighbors']['materials']['materials'].values()} \
        |{reports['grass']['materialReport']['asset'],reports['foreground']['newMaterial']['asset'],reports['roof']['materialReport']['asset']}
    texture_paths={row['asset']for row in original['textures'].values()} \
        |{row['asset']for row in reports['neighbors']['materials']['textures'].values()} \
        |{row['asset']for row in reports['grass']['materialReport']['textures'].values()} \
        |{row['asset']for row in reports['roof']['materialReport']['textures'].values()}
    require(len(material_paths)==56 and len(texture_paths)==84,'Verified unique scoped56 graphs/84 texture assets required')
    return {'original':original,'leaf':leaf,'neighbor':reports['neighbors']['materials'],
        'grass':reports['grass']['materialReport'],'foreground':reports['foreground']['newMaterial'],
        'roof':reports['roof']['materialReport'],'scopedMaterialGraphs':len(material_paths),'scopedTextureObjects':len(texture_paths),
        'verifiedMaterialAssets':sorted(material_paths),'verifiedTextureAssets':sorted(texture_paths)}


def component_lookup(u,actor_path,name_or_path):
    actors={a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
    require(actor_path in actors,'Declared existing component actor missing')
    rows=[c for c in actors[actor_path].get_components_by_class(u.PrimitiveComponent)
        if c.get_name()==name_or_path or c.get_path_name()==name_or_path]
    require(len(rows)==1,'Declared component ambiguous');return rows[0]


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
    require(len(leaf)==23 and len(culls)==601 and retained==501826,'Exact leaf/cull combined scope differs')
    return leaf,culls


def roof_overrides(u,bundle,added_neighbor):
    changes=[]
    for delta in bundle['reports']['roof']['componentMaterialOverrides']:
        path=added_neighbor[delta['sourceMeshId']];c=component_lookup(u,path,delta['componentName'])
        require(c.get_editor_property('static_mesh').get_path_name()==delta['mesh']and c.get_num_materials()==1
            and c.get_material(0).get_path_name()==delta['beforeMaterial'],'New neighbor roof slot input differs')
        material=u.EditorAssetLibrary.load_asset(delta['afterMaterial']);require(material,'Copied roof PBR material missing')
        c.set_material(0,material);row=copy.deepcopy(delta);row['sourceDonorActor']=delta['actor'];row['actor']=path;changes.append(row)
    require(len(changes)==4,'Only4 source-defined roof component overrides required');return changes


def neighbor_geometry_after_roof(u,bundle,h,rows,mesh_paths):
    """R18 source mesh/default material proof after separate R23 slot overrides.

    R18's original verify_scene requires original effective component roof
    materials. It is used before those overrides. After reload we independently
    preserve its37 geometry/default-material/build checks; the full composed
    actor counterfactual checks every policy and exact4 effective overrides.
    """
    proofs={};subsystem=h['meshHelper'].static_mesh_subsystem(u)
    for row in rows:
        mesh=u.EditorAssetLibrary.load_asset(mesh_paths[row['id']])
        wanted=bundle['reports']['neighbors']['materials']['materials'][row['material']]['asset']
        require(mesh and mesh.get_material(0).get_path_name()==wanted
            and not mesh.get_editor_property('has_navigation_data')
            and not mesh.get_editor_property('nanite_settings').get_editor_property('enabled'),
            'Copied neighbor source mesh default material/nav/Nanite changed')
        settings=subsystem.get_lod_build_settings(mesh,0)
        require(settings.get_editor_property('use_full_precision_u_vs')and not settings.get_editor_property('generate_lightmap_u_vs')
            and not settings.get_editor_property('recompute_normals'),'Copied neighbor UV/normal build policy changed')
        proofs[row['id']]=h['neighbor'].native_mesh_proof(u,mesh,row)
    require(len(proofs)==37,'All37 actual copied source neighbor meshes required');return proofs


def independent_copied_project(plan,bundle,output):
    project=output/'Project/BreziTwin';base=guard.BASE/'Project/BreziTwin'
    clone=read(output/'realism-integration-project-clone.json');copy_path=output/'realism-integration-package-copy.json'
    copied=read(copy_path)
    require(clone['status']=='verified-byte-identical-independent-apfs-r22a-project-clone-before-realism-integration-native-r1'
        and clone['selectedPlan']==pin(guard.PLAN)and clone['baseNativeReport']==plan['baseNativeReport']
        and clone['originalFileCount']==4107 and clone['newCopiedPackageCount']==74
        and clone['nativeExecuted']is False and clone['packageCopyReceipt']==pin(copy_path)
        and clone['baseContentInventory']==plan['baseContentInventory']and clone['baseProjectProof']==plan['baseProjectProof'],
        'Typed original plus saved-package clone required')
    expected_copies=[{**row,'destination':str(project/'Content'/row['relativeContentPath']),'independentInodes':True}for row in bundle['packages']]
    require(copied['schema']==guard.SCHEMA and copied['owner']=='scripts/unreal/exterior-realism-integration-copy-r22.py'
        and copied['status']=='verified-byte-identical-independent-apfs-saved-donor-packages-copied'
        and copied['selectedPlan']==pin(guard.PLAN)and copied['baseNativeReport']==plan['baseNativeReport']
        and copied['project']==str(project)and copied['copiedPackages']==expected_copies and copied['copiedPackageCount']==74
        and copied['nativeExecuted']is False and copied['sceneMapChanged']is False and copied['viewpointsChanged']is False,
        'Actual root-only saved-package copy receipt differs')
    expected=copy.deepcopy(bundle['content']);expected.update({r['relativeContentPath']:{'sha256':r['sha256'],'bytes':r['bytes']}for r in bundle['packages']})
    require(g.inventory(project/'Content')==expected and g.project_proof(project)==bundle['protected']
        and g.inventory(base/'Content')==bundle['content']and g.project_proof(base)==bundle['protected'],
        'Fresh original/candidate native bytes differ')
    for directory,rows in (('Content',bundle['content']),('',bundle['protected'])):
        for relative in rows:
            a,b=base/directory/relative,project/directory/relative
            require((a.stat().st_dev,a.stat().st_ino)!=(b.stat().st_dev,b.stat().st_ino),'Original native hardlink forbidden')
    for row in bundle['packages']:
        a,b=Path(row['source']),project/'Content'/row['relativeContentPath']
        require((a.stat().st_dev,a.stat().st_ino)!=(b.stat().st_dev,b.stat().st_ino),'Copied saved-package hardlink forbidden')
    return project,expected


def main():
    import unreal as u
    plan_path=Path(os.environ['BREZI_REALISM_INTEGRATION_PLAN']).resolve()
    require(plan_path==guard.PLAN and sha(plan_path)==os.environ['BREZI_REALISM_INTEGRATION_PLAN_SHA256'],'Selected frozen integration plan changed')
    plan,bundle=guard.validate_plan(plan_path)
    output=Path(os.environ['BREZI_REALISM_INTEGRATION_OUTPUT']).resolve();require(output==guard.CANDIDATE,'Only fresh selected R22a may change')
    project,content_before=independent_copied_project(plan,bundle,output)
    require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==project
        and Path(u.Paths.engine_dir()).resolve()==Path('/Users/Shared/Epic Games/UE_5.8/Engine'),'Wrong own project/native engine')
    require(not(output/'exterior-import-report.json').exists()and not(output/REPORT).exists(),'No copied/fake original or previous native report')
    require(sha(project/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib')==MODULE_SHA
        and read(project/'Binaries/Mac/UnrealEditor.modules')['BuildId']=='55116800','Actual original recorder module/engine BuildId differs')
    h=helpers(bundle);reports=bundle['reports'];receipt=output/REPORT
    state={'schema':guard.SCHEMA,'owner':OWNER,'status':'running','startedAt':now(),'nativeProcessId':os.getpid(),
        'output':str(output),'project':str(project),'selectedPlan':pin(plan_path),'baseNativeReport':plan['baseNativeReport'],
        'savedDonors':plan['donors'],'inputFiles':plan['inputFiles'],'ownedSources':plan['ownedSources'],
        'projectClone':pin(output/'realism-integration-project-clone.json'),'copiedPackageReceipt':pin(output/'realism-integration-package-copy.json'),
        'activeDesign':bundle['base']['activeDesign'],'setbacksMm':bundle['base']['setbacksMm'],
        'nativeModuleWitness':{'source':str(guard.BASE/'Project/BreziTwin/Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),
            'destination':str(project/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'),'sha256':MODULE_SHA,'bytes':2818384,'independentInodes':True},
        'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingPackageProduced':False,
        'knownReviewLimits':plan['knownReviewLimits'],'combinedAppearanceGoNoGo':plan['combinedAppearanceGoNoGo'],
        'nativeMaterialPackagesIndependentlyReloaded':False,'nativeMeshPackagesIndependentlyReloaded':False}
    write(receipt,state)
    try:
        levels=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot load own original R16 map')
        before=full_witness(u,h);require(before==bundle['before'],'Actual original full5306 actor/policy witness differs')
        original_readback=h['importer'].readback(u,bundle['base']['geometry'])
        materials_before=verify_materials(u,bundle,h)
        write(output/'realism-integration-witness-before.json',before)
        write(output/'realism-integration-materials-before.json',materials_before)
        n=h['grass'];selected=bundle['grassSelected'];rows=bundle['grassRows']
        values,chosen,components=n.capture_original_instances(u,bundle['base'],selected)
        require(values==read(check_pin(reports['grass']['originalMembersBefore'])),'Actual original grass roots differ from saved donor')
        _,transform_lookup=n.transform_guard.validated_probe(selected,rows)
        mesh_paths=read(check_pin(reports['grass']['effectiveGeometry']))['meshes']
        meshes={row['id']:u.EditorAssetLibrary.load_asset(mesh_paths[row['id']])for row in rows}
        grass_material=u.EditorAssetLibrary.load_asset(reports['grass']['materialReport']['asset'])
        _,membership,grass_groups,grass_roots=n.apply_scene(u,bundle['base'],selected,rows,meshes,grass_material,
            components,chosen,before,values,h['importer'],transform_lookup)
        require(membership==reports['grass']['originalMemberChanges'],'Grass RemoveAtSwap composition changed')
        leaf,culls=apply_leaf_and_visibility(u,bundle)
        neighbor_bundle=h['neighbor'].guard.validated_candidate();neighbor_rows=h['neighbor'].export_records(neighbor_bundle)
        neighbor_paths=reports['neighbors']['meshes'];neighbor_meshes={k:u.EditorAssetLibrary.load_asset(v)for k,v in neighbor_paths.items()}
        neighbor_materials={k:u.EditorAssetLibrary.load_asset(v['asset'])for k,v in reports['neighbors']['materials']['materials'].items()}
        target_components=h['neighbor'].affected_components(u,actors,bundle['base'],neighbor_bundle)
        changes,neighbor_added=h['neighbor'].apply_scene(u,neighbor_bundle,neighbor_rows,neighbor_meshes,target_components,h['rural'])
        require(changes==reports['neighbors']['componentChanges'],'Exact6 neighbor old-field changes differ')
        neighbor_initial=h['neighbor'].verify_scene(u,neighbor_bundle,neighbor_rows,neighbor_paths,changes,neighbor_added,
            neighbor_materials,h['meshHelper'],h['rural'])
        foreground_bundle=h['foreground'].guard.load_source()
        floor=u.EditorAssetLibrary.load_asset(reports['foreground']['newMesh'])
        foreground_added=h['foreground'].apply_scene(u,foreground_bundle,floor,h['rural'])
        foreground_before=h['foreground'].verify_scene(u,foreground_bundle,foreground_added,reports['foreground']['newMesh'],
            reports['foreground']['newMaterial']['asset'],h['rural'],h['existing'],h['meshHelper'])
        roof_changes=roof_overrides(u,bundle,neighbor_added)
        added={**{'neighbors:'+k:v for k,v in neighbor_added.items()},**{'grass:'+k:v['actor']for k,v in grass_groups.items()},
            **{'foreground:'+k:v for k,v in foreground_added.items()}}
        expected=guard.compose_all_expected(bundle['expectedOriginal'],bundle['templates'],added)
        require(full_witness(u,h)==expected,'Actual integration exceeds explicit5346 actor counterfactual')
        write(output/'realism-integration-witness-expected.json',expected)
        view_file=project/'Content/Data/viewpoints.json';source_view=check_pin(plan['diagnosticViewpoints'])
        require(view_file.read_bytes()==(guard.BASE/'Project/BreziTwin/Content/Data/viewpoints.json').read_bytes(),
                'Original camera prefix changed before diagnostic staging')
        view_file.write_bytes(source_view.read_bytes())
        require(levels.save_current_level(),'Cannot save own combined scene map')
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot unload/reload saved combined map')
        after=full_witness(u,h);require(after==expected,'Saved combined scene differs from exact5346 actor counterfactual')
        hisms=[c for row in after.values()for c in row['components']if c['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent']
        require(len(hisms)==2312 and sum(c['instanceCount']for c in hisms)==676944,
                'Actual full-scene HISM component/population census differs')
        original_geometry=copy.deepcopy(bundle['originalGeometryAfter'])
        delegated=h['importer'].readback(u,original_geometry)
        require(delegated['groupCount']==1980 and delegated['instanceCount']==631962,'Original typed ownership/readback changed')
        saved_grass=n.transform_guard.verify_saved_groups(u,grass_groups,selected,rows,values,transform_lookup)
        require(saved_grass==grass_roots,'All64 saved matrix/Transform proofs differ from exact measured insertion')
        grass_mesh_proofs=[n.native_mesh_proof(u,u.EditorAssetLibrary.load_asset(mesh_paths[row['id']]),row)for row in rows]
        neighbor_saved=neighbor_geometry_after_roof(u,bundle,h,neighbor_rows,neighbor_paths)
        require(neighbor_saved==neighbor_initial['meshProofs'],'All37 saved neighbor geometry/default slots changed')
        foreground_saved=h['foreground'].verify_scene(u,foreground_bundle,foreground_added,reports['foreground']['newMesh'],
            reports['foreground']['newMaterial']['asset'],h['rural'],h['existing'],h['meshHelper'])
        require(foreground_saved==foreground_before,'Saved foreground geometry/graph/source512 proof changed')
        materials_saved=verify_materials(u,bundle,h);require(materials_saved==materials_before,'Any copied/original graph/texture changed')
        after_content=g.inventory(project/'Content')
        delta=guard.validate_content(bundle['content'],after_content,bundle['packages'],plan['diagnosticViewpoints']['sha256'])
        require(g.project_proof(project)==bundle['protected']and g.inventory(guard.BASE/'Project/BreziTwin/Content')==bundle['content']
            and g.project_proof(guard.BASE/'Project/BreziTwin')==bundle['protected'],'Protected or original donor project changed')
        require(sha(plan_path)==os.environ['BREZI_REALISM_INTEGRATION_PLAN_SHA256'],'Selected plan changed during native')
        guard.validate_plan(plan_path)
        write(output/'realism-integration-witness-saved.json',after)
        write(output/'realism-integration-content-after.json',after_content)
        write(output/'realism-integration-materials-saved.json',materials_saved)
        write(output/'realism-integration-effective-original-geometry.json',original_geometry)
        state.update(status=STATUS,completedAt=now(),savedMapUnloadedReloaded=True,originalR16Unchanged=True,
            sourceInputsUnchanged=True,actualAudit=plan['audit'],scopeAudit=plan['scopeAudit'],
            leafComponentBindings=leaf,componentCullOverrides=culls,originalMemberChanges=membership,
            newGrassGroups=grass_groups,newGrassRootReadback=saved_grass,newGrassMeshProofs=grass_mesh_proofs,
            neighborChanges=changes,newNeighborActors=neighbor_added,neighborGeometryReadback=neighbor_saved,
            newForegroundActors=foreground_added,foregroundReadback=foreground_saved,roofComponentOverrides=roof_changes,
            addedActorIdentityMap=added,baseGeometryReadback=original_readback,savedOriginalGeometryReadback=delegated,
            beforeActorWitnessSha256=digest(before),expectedActorWitnessSha256=digest(expected),savedActorWitnessSha256=digest(after),
            beforeActorWitness=pin(output/'realism-integration-witness-before.json'),expectedActorWitness=pin(output/'realism-integration-witness-expected.json'),
            savedActorWitness=pin(output/'realism-integration-witness-saved.json'),afterContentInventory=pin(output/'realism-integration-content-after.json'),
            originalGeometryAfter=pin(output/'realism-integration-effective-original-geometry.json'),
            materialsBefore=pin(output/'realism-integration-materials-before.json'),materialsSaved=pin(output/'realism-integration-materials-saved.json'),
            protectedProjectProof=plan['baseProjectProof'],assetDelta=delta,scopedMaterialGraphs=56,scopedTextureObjects=84,
            originalPlantMastersPreserved=135,originalPlantLodsPreserved=405,
            originalExteriorOwnershipSpoofed=False,nativeNormalTangentReadbackAvailable=False,
            actualFullSceneHismComponents=len(hisms),actualFullSceneHismInstances=sum(c['instanceCount']for c in hisms),
            actualRecordedExteriorHismGroups=delegated['groupCount']+3+foreground_saved['savedGroups'],
            actualRecordedExteriorHismInstances=delegated['instanceCount']+64+foreground_saved['savedInstances'],
            diagnosticViewpoints=pin(view_file),donorFilesNeverMutated=True)
        write(receipt,state);print(__import__('json').dumps({'status':STATUS,'report':pin(receipt),'audit':plan['audit'],
            'nativeAppearanceAccepted':False,'performanceAccepted':False}))
    except Exception as error:
        state.update(status='failed',error=str(error),completedAt=now());write(receipt,state);raise


if __name__=='__main__':main()
