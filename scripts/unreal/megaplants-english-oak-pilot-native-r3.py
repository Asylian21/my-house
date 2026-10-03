"""Root-only isolated original whole-D USD import and neutral probe map.

Original source materials are faithfully translated. No texture replacement,
original scene setter, wind sidecar attachment, or photoreal acceptance is made.
"""
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys
import traceback

sys.dont_write_bytecode=True
_p=Path(__file__).with_name('megaplants-english-oak-pilot-guards-r3.py')
_s=importlib.util.spec_from_file_location('oak_original_guard',_p)
g=importlib.util.module_from_spec(_s);_s.loader.exec_module(g)
OWNER='scripts/unreal/megaplants-english-oak-pilot-native-r3.py'
REPORT='oak-usd-native-pilot-report-r3.json'
STATUS='saved-original-whole-D-usd-experimental-probe-materials-constant'

def value(v):
    if v is None or isinstance(v,(str,int,float,bool)):return v
    if hasattr(v,'get_path_name'):return {'object':v.get_path_name()}
    if all(hasattr(v,k) for k in ('translation','rotation','scale3d')):
        return [value(v.translation),value(v.rotation),value(v.scale3d)]
    for names in [('r','g','b','a'),('pitch','yaw','roll'),('x','y','z','w'),('x','y','z')]:
        if all(hasattr(v,k) for k in names):return [getattr(v,k) for k in names]
    try:return [value(x) for x in v]
    except TypeError:return str(v)

def enum(u,cls,token):
    kind=getattr(u,cls);matches=[getattr(kind,n) for n in dir(kind) if n.upper().replace('_','')==token.upper().replace('_','')]
    g.require(len(matches)==1,'Explicit installed enum unavailable/ambiguous: '+cls+'.'+token)
    return matches[0]

def settings(u,plan):
    for name in ('UsdStageAssetImportFactory','UsdStageImportOptions','UsdAssetUserData',
                 'AssetImportTask','WorldFactory','SkeletalMeshActor'):
        g.require(hasattr(u,name),'Required installed reflected USD/probe API missing: '+name)
    options=u.UsdStageImportOptions()
    exact={'import_actors':False,'import_geometry':True,'import_materials':True,
           'import_skeletal_animations':False,'import_level_sequences':False,'import_groom_assets':False,
           'import_sparse_volume_textures':False,'import_sounds':False,'import_only_used_materials':True,
           'use_existing_asset_cache':False,'prims_to_import':[plan['stageRoot']],
           'purposes_to_import':2,'nanite_triangle_threshold':0,'render_context_to_import':'',
           'material_purpose':'allPurpose','subdivision_level':0,'override_stage_options':False,
           'import_at_specific_time_code':False,'share_assets_for_identical_prims':True,
           'prim_path_folder_structure':True,'use_prim_kinds_for_collapsing':False,
           'merge_identical_material_slots':True,'interpret_lods':True}
    for k,v in exact.items():options.set_editor_property(k,v)
    options.set_editor_property('existing_asset_policy',enum(u,'ReplaceAssetPolicy','IGNORE'))
    options.set_editor_property('fallback_collision_type',enum(u,'UsdCollisionType','NONE'))
    actual={k:value(options.get_editor_property(k)) for k in exact}
    # FName NAME_None is exposed as the string "None" in Python; the USD
    # universal render context is the empty token. Normalize only this field.
    g.require(actual['render_context_to_import'] in ('','None'),'Universal USD render context required')
    actual['render_context_to_import']=''
    g.require(actual==exact,'USD import option readback differs')
    return options,actual

LIGHT_FIELDS={
 'DirectionalLightComponent':['intensity','light_color','indirect_lighting_intensity','volumetric_scattering_intensity',
    'cast_shadows','atmosphere_sun_light','light_source_angle','cast_cloud_shadows','cloud_shadow_strength',
    'cloud_shadow_on_surface_strength','cloud_shadow_on_atmosphere_strength','cloud_shadow_extent',
    'cloud_shadow_map_resolution_scale','cloud_shadow_ray_sample_count_scale'],
 'SkyLightComponent':['intensity','light_color','real_time_capture','source_type','cubemap','lower_hemisphere_color',
    'cloud_ambient_occlusion','cloud_ambient_occlusion_strength','cloud_ambient_occlusion_extent',
    'cloud_ambient_occlusion_map_resolution_scale','cloud_ambient_occlusion_aperture_scale'],
 'VolumetricCloudComponent':['material','layer_bottom_altitude','layer_height','tracing_start_max_distance','tracing_max_distance',
    'view_sample_count_scale','reflection_view_sample_count_scale_value','shadow_view_sample_count_scale',
    'shadow_reflection_view_sample_count_scale_value','use_per_sample_atmospheric_light_transmittance',
    'sky_light_cloud_bottom_occlusion','visible_in_real_time_sky_captures'],
 'ExponentialHeightFogComponent':['fog_density','fog_height_falloff','start_distance','fog_max_opacity','enable_volumetric_fog',
    'fog_inscattering_luminance','directional_inscattering_luminance'],
 'SkyAtmosphereComponent':['bottom_radius','atmosphere_height','multi_scattering_factor','rayleigh_scattering_scale',
    'rayleigh_scattering','rayleigh_exponential_distribution','mie_scattering_scale','mie_scattering',
    'mie_absorption_scale','mie_absorption','mie_anisotropy','mie_exponential_distribution','other_absorption_scale',
    'other_absorption','ground_albedo']}

def lighting_snapshot(u,actor):
    row={'class':actor.get_class().get_path_name(),'transform':value(actor.get_actor_transform()),
         'tags':[str(x) for x in actor.get_editor_property('tags')],'components':[]}
    # Required fields are proven authored recipe inputs. Any extra inaccessible field
    # aborts this trial before creating the probe world, rather than silently omitting it.
    for name,fields in LIGHT_FIELDS.items():
        component=actor.get_component_by_class(getattr(u,name))
        if component:
            row['components'].append({'class':name,'properties':{k:value(component.get_editor_property(k)) for k in fields}})
    if isinstance(actor,u.PostProcessVolume):
        props=actor.get_editor_property('settings')
        fields=['auto_exposure_method','auto_exposure_min_brightness','auto_exposure_max_brightness','auto_exposure_bias',
                'auto_exposure_speed_up','auto_exposure_speed_down','motion_blur_amount']
        row['postProcess']={'unbound':actor.get_editor_property('unbound'),
                            'properties':{k:value(props.get_editor_property(k)) for k in fields},
                            'overrides':{k:props.get_editor_property('override_'+k) for k in fields}}
    return row

def asset_observation(u,asset):
    row={'path':asset.get_path_name(),'class':asset.get_class().get_path_name()}
    if isinstance(asset,(u.StaticMesh,u.SkeletalMesh)):
        settings=asset.get_editor_property('nanite_settings')
        row['naniteEnabledSetting']=bool(settings.get_editor_property('enabled'))
        try:
            assembly=settings.get_editor_property('nanite_assembly_data')
            parts=assembly.get_editor_property('parts')
            def actual_part_path(part):
                soft=part.get_editor_property('mesh_object_path')
                values=soft.to_tuple()
                g.require(len(values)==1 and isinstance(values[0],str) and values[0].startswith(g.PREFIX+'/OriginalUSD/'),
                          'Measured SoftObjectPath must contain exactly one own original asset string')
                resolved=u.SystemLibrary.get_object_from_soft_path(soft)
                g.require(resolved is not None and resolved.get_path_name()==values[0],
                          'Measured soft-path tuple and reflected resolved native object differ')
                return values[0]
            row['assemblyPartPaths']=[actual_part_path(p) for p in parts]
            expected_part_class=u.SkeletalMesh if isinstance(asset,u.SkeletalMesh) else u.StaticMesh
            g.require(all(p.startswith(g.PREFIX+'/') and isinstance(u.load_asset(p),expected_part_class)
                          for p in row['assemblyPartPaths']),'Assembly part escaped own imported meshes or correct skeletal/static class')
            row['assemblyPartClass']='/Script/Engine.SkeletalMesh' if isinstance(asset,u.SkeletalMesh) else '/Script/Engine.StaticMesh'
            row['softObjectPathReadbackRoute']='actual-R2-diagnostic-to_tuple-single-string-and-get_object_from_soft_path'
            row['assemblyPartsReadbackAvailable']=True
        except Exception as e:
            row['assemblyPartsReadbackAvailable']=False;row['assemblyPartsReadbackLimitation']=str(e)
        try:
            nodes=settings.get_editor_property('nanite_assembly_data').get_editor_property('nodes')
            row['nativeAssemblyNodeCount']=len(nodes)
            row['nativeAssemblyNodePartIndices']=[int(n.get_editor_property('part_index')) for n in nodes]
            row['nativeAssemblyNodesReadbackAvailable']=True
        except Exception as e:
            row['nativeAssemblyNodesReadbackAvailable']=False
            row['nativeAssemblyNodesReadbackLimitation']=str(e)
        row['usdAssetUserData']=[{'class':item.get_class().get_path_name(),
                                 'primPaths':[str(p) for p in item.get_editor_property('prim_paths')]}
                                for item in asset.get_editor_property('asset_user_data')
                                if isinstance(item,u.UsdAssetUserData)]
        row['nativeFullCornersReadbackAvailable']=False
    if isinstance(asset,u.MaterialInstanceConstant):
        names=u.MaterialEditingLibrary.get_vector_parameter_names(asset)
        row['vectorParameters']={str(n):value(u.MaterialEditingLibrary.get_material_instance_vector_parameter_value(asset,n)) for n in names}
        row['parent']=value(asset.get_editor_property('parent'))
        row['authoredTextureParameterCount']=len(asset.get_editor_property('texture_parameter_values'))
        g.require(row['authoredTextureParameterCount']==0,'Unexpected substituted/authored native texture')
    return row

def camera_append(plan):
    file=g.PROJECT/'Content/Data/viewpoints.json';before=g.pin(g.BASE/'Project/BreziTwin/Content/Data/viewpoints.json');doc=g.read(file)
    g.require(not any(v['id']==plan['camera']['id'] for v in doc['views']),'Probe camera already exists')
    original=json.loads(json.dumps(doc));doc['views'].append(plan['camera'])
    file.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+'\n')
    saved=g.read(file);g.require({**saved,'views':saved['views'][:-1]}==original,'Original camera prefix changed')
    return {'before':before,'after':g.pin(file),'originalPrefixExact':True,'addedCamera':plan['camera']}

def whole_tree_observation(observed,plan):
    selected=[r for r in observed if r['class']=='/Script/Engine.SkeletalMesh'
              and any(plan['stageRoot'] in item['primPaths'] for item in r.get('usdAssetUserData',[]))
              and r.get('naniteEnabledSetting') is True and r.get('assemblyPartsReadbackAvailable') is True
              and r.get('assemblyPartClass')=='/Script/Engine.SkeletalMesh' and r.get('assemblyPartPaths')]
    g.require(len(selected)==1,'Exactly one source-root-bound skeletal Nanite assembly required')
    row=selected[0]
    g.require(len(row['assemblyPartPaths'])==plan['sourcePointInstancerUniquePrototypes']
              and len(set(row['assemblyPartPaths']))==len(row['assemblyPartPaths'])
              and all(p.startswith(g.PREFIX+'/OriginalUSD/') for p in row['assemblyPartPaths']),
              'All eleven distinct original skeletal prototype references must remain in own imported namespace')
    if row['nativeAssemblyNodesReadbackAvailable']:
        g.require(row['nativeAssemblyNodeCount']==plan['sourcePointInstancerMembers']
                  and set(row['nativeAssemblyNodePartIndices'])==set(range(plan['sourcePointInstancerUniquePrototypes'])),
                  'Actual assembly node census must match every original point-instancer member/prototype')
    return row

def run(u):
    plan,base=g.validate_plan();g.validate_clone(plan,base,prepared=True)
    g.require(Path(u.Paths.project_dir()).resolve()==g.PROJECT,'Root must launch only the prepared own probe project')
    report_path=g.OUTPUT/REPORT;g.require(not report_path.exists(),'Preserve every native pilot attempt')
    before=g.inventory(g.PROJECT);source_before=g.inventory(g.BASE/'Project/BreziTwin')
    disk_before=shutil.disk_usage(g.PROJECT).free
    g.require(disk_before>=3*1024**3,'Actual free disk must be at least3GiB before this isolated native import')
    g.require(not any(k.startswith('Content/'+g.PREFIX.removeprefix('/Game/')+'/') for k in before),
              'Fresh own pilot namespace already populated')
    options,option_readback=settings(u,plan)
    startup_assemblies=u.SystemLibrary.get_console_variable_int_value('r.Nanite.AllowAssemblies')
    startup_foliage=u.SystemLibrary.get_console_variable_int_value('r.Nanite.Foliage')
    g.require(startup_assemblies==1 and startup_foliage==0,
              'Fresh startup must enable only assemblies, leaving Nanite Foliage at the original default')
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    g.require(levels.load_level('/Game/Brezi/Maps/Brezi'),'Could not open own untouched main map read-only')
    light_classes=(u.DirectionalLight,u.SkyLight,u.SkyAtmosphere,u.VolumetricCloud,u.ExponentialHeightFog,u.PostProcessVolume)
    lights=[a for a in actors.get_all_level_actors() if isinstance(a,light_classes)]
    g.require(sum(isinstance(a,u.DirectionalLight) for a in lights)==1 and sum(isinstance(a,u.SkyLight) for a in lights)==1,
              'Exactly original native day sun and sky required')
    light_before=[lighting_snapshot(u,a) for a in lights]
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    collapse_before=u.SystemLibrary.get_console_variable_int_value('USD.CollapseTopLevelPointInstancers')
    u.SystemLibrary.execute_console_command(world,'USD.CollapseTopLevelPointInstancers 0')
    g.require(u.SystemLibrary.get_console_variable_int_value('USD.CollapseTopLevelPointInstancers')==0,'Assembly collapse must be disabled')
    task=u.AssetImportTask();task.set_editor_property('filename',plan['selectedUsd']['path'])
    task.set_editor_property('destination_path',g.PREFIX+'/OriginalUSD');task.set_editor_property('automated',True)
    task.set_editor_property('replace_existing',False);task.set_editor_property('save',True)
    task.set_editor_property('options',options);task.set_editor_property('factory',u.UsdStageAssetImportFactory())
    tools=u.AssetToolsHelpers.get_asset_tools();tools.import_asset_tasks([task])
    paths=u.EditorAssetLibrary.list_assets(g.PREFIX+'/OriginalUSD',recursive=True,include_folder=False)
    assets=[u.load_asset(p) for p in paths];g.require(assets and all(a is not None for a in assets),'Original USD did not import assets')
    g.require(not any(isinstance(a,u.Texture) for a in assets),'Original no-texture source must not import substituted textures')
    observed=[asset_observation(u,a) for a in assets]
    expected_colors={(0.1420000046491623,0.06599999964237213,0.03099999949336052),
                     (0.08699999749660492,0.15299999713897705,0.020999999716877937)}
    actual_colors={tuple(r['vectorParameters']['BaseColor'][:3]) for r in observed
                   if 'BaseColor' in r.get('vectorParameters',{})}
    g.require(actual_colors==expected_colors,'Both exact original USD constant diffuse colors must survive translation')
    selected_observation=whole_tree_observation(observed,plan)
    tree_mesh=next(a for a in assets if a.get_path_name()==selected_observation['path'])
    g.require(isinstance(tree_mesh,u.SkeletalMesh),'Selected source root must be the actual skeletal mesh object')
    import_log=(g.OUTPUT/'oak-usd-native-r3.log').read_text(errors='replace')
    import_warnings=[line for line in import_log.splitlines()
                     if 'Compute a zero length normal vector' in line or 'LogSkeletalMesh: Warning:' in line]
    g.require('Failed to build Nanite Assembly' not in import_log and 'zero joint bindings' not in import_log,
              'Original assembly builder failed or skipped bound parts')
    g.require(light_before==[lighting_snapshot(u,a) for a in lights],'Original light properties changed during import')
    probe=tools.create_asset('EnglishOakPilot',g.PREFIX+'/Maps',u.World,u.WorldFactory())
    g.require(probe is not None,'Could not create a separate own probe world')
    copied=actors.duplicate_actors(lights,probe,u.Vector(0,0,0))
    g.require(len(copied)==len(lights) and [lighting_snapshot(u,a) for a in copied]==light_before,'Native daylight duplication differs')
    g.require(u.EditorAssetLibrary.save_loaded_asset(probe),'Could not save separate probe world')
    g.require(levels.load_level(g.MAP),'Could not open own probe map')
    tree=actors.spawn_actor_from_class(u.SkeletalMeshActor,u.Vector(0,0,0),u.Rotator(0,0,0))
    tree.set_actor_label('Original licensed English Oak D · constant USD materials')
    tree.set_editor_property('tags',[u.Name('BreziEnglishOakPilotR3')])
    component=tree.get_component_by_class(u.SkeletalMeshComponent);component.set_skeletal_mesh_asset(tree_mesh)
    component.set_collision_enabled(enum(u,'CollisionEnabled','NO_COLLISION'))
    ground=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,-2),u.Rotator(0,0,0))
    ground.set_actor_label('Oak pilot · neutral 45 m ground')
    ground.set_editor_property('tags',[u.Name('BreziEnglishOakPilotR3')]);ground.set_actor_scale3d(u.Vector(45,45,1))
    gc=ground.get_component_by_class(u.StaticMeshComponent);gc.set_static_mesh(u.load_asset('/Engine/BasicShapes/Plane'))
    material=tools.create_asset('M_PilotNeutralGround',g.PREFIX+'/Materials',u.Material,u.MaterialFactoryNew())
    g.require(material is not None,'Could not create explicit neutral ground material')
    color=u.MaterialEditingLibrary.create_material_expression(material,u.MaterialExpressionConstant3Vector,0,0)
    color.set_editor_property('constant',u.LinearColor(.18,.18,.18,1))
    u.MaterialEditingLibrary.connect_material_property(color,'',enum(u,'MaterialProperty','MP_BASE_COLOR'))
    for k,v in [('MP_ROUGHNESS',.8),('MP_SPECULAR',.25)]:
        node=u.MaterialEditingLibrary.create_material_expression(material,u.MaterialExpressionConstant,0,0);node.set_editor_property('r',v)
        u.MaterialEditingLibrary.connect_material_property(node,'',enum(u,'MaterialProperty',k))
    errors=u.MaterialEditingLibrary.recompile_material(material);g.require(not errors,'Neutral ground compile errors')
    gc.set_material(0,material);gc.set_editor_property('cast_shadow',False)
    g.require(u.EditorAssetLibrary.save_loaded_asset(material),'Could not save neutral ground material')
    g.require(levels.save_current_level(),'Could not save own probe map')
    tree_path=tree.get_path_name();ground_path=ground.get_path_name()
    g.require(levels.load_level('/Game/Brezi/Maps/Brezi') and levels.load_level(g.MAP),'Probe map must unload/reload')
    saved={a.get_path_name():a for a in actors.get_all_level_actors()}
    g.require(tree_path in saved and ground_path in saved,'Saved whole tree/ground missing')
    saved_tree=saved[tree_path];g.require(value(saved_tree.get_actor_location())==[0.,0.,0.] and value(saved_tree.get_actor_scale3d())==[1.,1.,1.],
                                      'Original tree root/scale changed')
    saved_mesh=saved_tree.get_component_by_class(u.SkeletalMeshComponent).get_skeletal_mesh_asset()
    g.require(saved_mesh.get_path_name()==tree_mesh.get_path_name(),'Saved whole assembly binding changed')
    saved_lights=[a for a in saved.values() if isinstance(a,light_classes)]
    g.require(sorted((lighting_snapshot(u,a) for a in saved_lights),key=lambda r:r['class'])==
              sorted(light_before,key=lambda r:r['class']),'Saved observed original daylight properties differ')
    camera=camera_append(plan)
    after=g.inventory(g.PROJECT);delta=g.validate_delta(before,after)
    u.SystemLibrary.execute_console_command(u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world(),
                                           'USD.CollapseTopLevelPointInstancers '+str(collapse_before))
    g.require(u.SystemLibrary.get_console_variable_int_value('USD.CollapseTopLevelPointInstancers')==collapse_before,
              'Own import-only CVar must be restored')
    g.require(g.inventory(g.BASE/'Project/BreziTwin')==source_before,'Original saved R32 project changed')
    for row in plan['inputFiles']:g.check_pin(row)
    report={'schema':g.SCHEMA,'owner':OWNER,'status':STATUS,'nativeProcessId':os.getpid(),'selectedPlan':g.pin(g.PLAN),
       'sourceArchive':plan['sourceArchive'],'sourceExtraction':plan['sourceExtraction'],'usdInspection':plan['usdInspection'],
       'baseNativeReport':plan['baseNativeReport'],'initialRootClone':plan['initialRootClone'],
       'projectPreparation':g.pin(g.OUTPUT/'oak-usd-project-preparation-r3.json'),'project':str(g.PROJECT),'map':g.MAP,
       'usdImportFactory':'UsdStageAssetImportFactory','optionsReadback':option_readback,'assets':observed,
       'startupReadback':{'r.Nanite.AllowAssemblies':startup_assemblies,'r.Nanite.Foliage':startup_foliage},
       'selectedRootUsdPrimPath':plan['stageRoot'],'selectedRootNativeName':tree_mesh.get_name(),
       'nameOnlySelectionUsed':False,'allSourcePrototypePartReferencesMeasured':True,
       'wholeTreeMesh':tree_mesh.get_path_name(),'treeActor':tree_path,'groundActor':ground_path,
       'nativeSourceLightingObserved':light_before,'daylightCopiedByNativeActorDuplication':True,
       'probeMapUnloadedReloaded':True,'originalMainMapUnchanged':True,'originalSavedR32ProjectUnchanged':True,
       'cameraDataDelta':camera,'projectDelta':delta,'beforeInventory':before,'afterInventory':after,
       'originalUsdSourceUnmodified':True,'sourceAxisUnitsPreservedByUsdImporter':True,
       'nativeTextureObjectsImported':0,'originalConstantMaterialsPreserved':True,
       'importCollapseCvarBeforeAndRestored':collapse_before,'importCollapseCvarDuring':0,
       'actualFreeBytesBeforeNative':disk_before,'actualFreeBytesAfterNative':shutil.disk_usage(g.PROJECT).free,
       'nativeScratchBytesEstimated':None,'nativeScratchCapEnforced':False,
       'windSidecarImported':False,'dynamicWindEvaluated':False,'nativeFullGeometryCornerReadbackAvailable':False,
       'nativeAssemblyNodeCountReadbackAvailable':selected_observation['nativeAssemblyNodesReadbackAvailable'],
       'importedNormalsTangentsPreserved':False,'actualNaniteGpuPassAttributedToTree':False,
       'observedImporterWarnings':import_warnings,
       'nativeApplied':True,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,
       'performanceAccepted':False,'shippingVerified':False,'packageVerified':False}
    g.write(report_path,report);print(json.dumps({'report':g.pin(report_path),'status':STATUS}))

if __name__=='__main__':
    import unreal
    try:run(unreal)
    except Exception:
        error=traceback.format_exc();print(error)
        target=g.OUTPUT/REPORT
        if not target.exists():
            g.write(target,{'schema':g.SCHEMA,'owner':OWNER,'status':'failed-original-USD-pilot-attempt-preserved',
                            'nativeProcessId':os.getpid(),'error':error,'nativeAppearanceAccepted':False,
                            'fullPhotorealismAccepted':False,'performanceAccepted':False,
                            'shippingVerified':False,'packageVerified':False})
        raise
