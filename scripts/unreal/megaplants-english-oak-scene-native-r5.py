"""Root-only scene creation from the39 already saved original USD packages.

Uses the active LevelEditor NewLevel route and explicit observed daylight
properties. No AssetImportTask, inactive WorldFactory, or actor duplication.
"""
import importlib.util
import json
import os
from pathlib import Path
import sys
import traceback

sys.dont_write_bytecode=True
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,Path(__file__).with_name(file))
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
g=module('oak_r5_native_scene_guard','megaplants-english-oak-scene-guards-r5.py')
n=module('oak_frozen_r3_native_observation','megaplants-english-oak-pilot-native-r3.py')
OWNER='scripts/unreal/megaplants-english-oak-scene-native-r5.py'
REPORT='oak-usd-scene-native-report-r5.json'
STATUS='saved-original-whole-D-from-preserved-USD-packages-explicit-daylight-subset-probe-r5'
PP_FIELDS=['auto_exposure_method','auto_exposure_min_brightness','auto_exposure_max_brightness','auto_exposure_bias',
           'auto_exposure_speed_up','auto_exposure_speed_down','motion_blur_amount']

def lighting_difference(left,right):
    import math
    import struct
    differences=[]
    def ordered(value):
        bits=struct.unpack('>Q',struct.pack('>d',value))[0]
        return (~bits)&((1<<64)-1) if bits>>63 else bits|(1<<63)
    def walk(a,b,path):
        if type(a) is not type(b):
            differences.append({'path':path,'source':a,'copied':b,'kind':'type','sourceType':type(a).__name__,'copiedType':type(b).__name__});return
        if isinstance(a,dict):
            if set(a)!=set(b):differences.append({'path':path,'kind':'dictionary-keys','source':sorted(a),'copied':sorted(b)})
            for key in sorted(set(a)&set(b)):walk(a[key],b[key],path+'.'+key)
        elif isinstance(a,list):
            if len(a)!=len(b):differences.append({'path':path,'kind':'list-length','source':len(a),'copied':len(b)})
            for i,(v,w) in enumerate(zip(a,b)):walk(v,w,path+'['+str(i)+']')
        elif isinstance(a,float):
            if struct.pack('>d',a)!=struct.pack('>d',b):
                finite=math.isfinite(a) and math.isfinite(b)
                differences.append({'path':path,'source':a,'copied':b,'kind':'float64',
                    'finite':finite,'absoluteDifference':abs(a-b) if finite else None,
                    'ulps':abs(ordered(a)-ordered(b)) if finite else None,
                    'sameFloat32':struct.pack('>f',a)==struct.pack('>f',b) if finite else False})
        elif a!=b:differences.append({'path':path,'source':a,'copied':b,'kind':'non-float'})
    walk(left,right,'$')
    quaternion_rows=[]
    for i,(a,b) in enumerate(zip(left,right)):
        if not isinstance(a,dict) or not isinstance(b,dict) or 'transform' not in a or 'transform' not in b:continue
        qa=a['transform'][1];qb=b['transform'][1]
        if len(qa)!=4 or len(qb)!=4:continue
        sign=1 if sum(v*w for v,w in zip(qa,qb))>=0 else -1
        ua=[v/math.sqrt(sum(x*x for x in qa)) for v in qa]
        ub=[sign*v/math.sqrt(sum(x*x for x in qb)) for v in qb]
        angle=math.degrees(4*math.atan2(math.sqrt(sum((v-w)**2 for v,w in zip(ua,ub))),math.sqrt(sum((v+w)**2 for v,w in zip(ua,ub)))))
        quaternion_rows.append({'index':i,'class':a.get('class'),'source':qa,'copied':qb,
            'signEquivalentMaxComponentDifference':max(abs(v-sign*w) for v,w in zip(qa,qb)),
            'rotationAngleDifferenceDegrees':angle})
    numeric=[v for v in differences if v['kind']=='float64']
    return {'differences':differences,'differenceCount':len(differences),'float64DifferenceCount':len(numeric),
        'nonFloat64DifferenceCount':len(differences)-len(numeric),
        'maxUlps':max((v['ulps'] or 0 for v in numeric),default=0),
        'maxAbsoluteDifference':max((v['absoluteDifference'] or 0 for v in numeric),default=0),
        'allDifferencesSameFloat32':all(v['sameFloat32'] for v in numeric) and len(numeric)==len(differences),
        'quaternionRows':quaternion_rows}

def lighting_snapshot(u,actor):
    row=n.lighting_snapshot(u,actor)
    for component in row['components']:
        original=actor.get_component_by_class(getattr(u,component['class']))
        component['properties']['mobility']=n.value(original.get_editor_property('mobility'))
    return row

def capture_property(u,v):
    if hasattr(v,'get_path_name'):
        g.require(not isinstance(v,u.Actor),'No old actor pointer may be kept for post-map copying')
        return {'kind':'asset-path','value':v.get_path_name()}
    if hasattr(v,'copy') and callable(v.copy):
        return {'kind':'wrapped-struct-copy','value':v.copy()}
    return {'kind':'scalar-or-enum','value':v}

def resolve_property(u,row):
    if row['kind']=='asset-path':
        asset=u.load_asset(row['value']);g.require(asset is not None,'Recorded daylight asset path failed to load')
        return asset
    return row['value']

def capture_light_values(u,actor):
    data={'actorClass':actor.get_class(),'transform':actor.get_actor_transform().copy(),
          'tags':[str(v) for v in actor.get_editor_property('tags')],'components':[]}
    for name,fields in n.LIGHT_FIELDS.items():
        component=actor.get_component_by_class(getattr(u,name))
        if component:
            data['components'].append({'class':name,'properties':
                 {key:capture_property(u,component.get_editor_property(key)) for key in ['mobility',*fields]}})
    if isinstance(actor,u.PostProcessVolume):
        settings=actor.get_editor_property('settings')
        data['postProcess']={'unbound':actor.get_editor_property('unbound'),
            'properties':{key:capture_property(u,settings.get_editor_property(key)) for key in PP_FIELDS},
            'overrides':{key:settings.get_editor_property('override_'+key) for key in PP_FIELDS}}
    return data

def spawn_light_values(u,actors,data):
    actor=actors.spawn_actor_from_class(data['actorClass'],u.Vector(0,0,0),u.Rotator(0,0,0))
    g.require(actor is not None,'Could not spawn explicit native daylight actor')
    actor.set_actor_transform(data['transform'],False,True)
    actor.set_editor_property('tags',[u.Name(v) for v in data['tags']])
    for row in data['components']:
        component=actor.get_component_by_class(getattr(u,row['class']))
        g.require(component is not None,'Fresh daylight actor lacks required component')
        for key,value in row['properties'].items():component.set_editor_property(key,resolve_property(u,value))
    if 'postProcess' in data:
        pp=data['postProcess'];actor.set_editor_property('unbound',pp['unbound'])
        settings=actor.get_editor_property('settings')
        for key,value in pp['properties'].items():settings.set_editor_property(key,resolve_property(u,value))
        for key,value in pp['overrides'].items():settings.set_editor_property('override_'+key,value)
        actor.set_editor_property('settings',settings)
    return actor

def camera_append(plan):
    file=g.PROJECT/'Content/Data/viewpoints.json';before=g.pin(g.BASE/'Project/BreziTwin/Content/Data/viewpoints.json')
    original=g.read(file);g.require(not any(v['id']==plan['camera']['id'] for v in original['views']),'Own R5 camera already exists')
    doc=dict(original);doc['views']=[*original['views'],plan['camera']]
    file.write_text(json.dumps(doc,indent=2,ensure_ascii=False)+'\n')
    g.require(g.read(file)==doc and {**doc,'views':doc['views'][:-1]}==original,'Original view prefix changed')
    return {'before':before,'after':g.pin(file),'originalPrefixExact':True,'addedCamera':plan['camera']}

def run(u):
    plan,source,base,before=g.validate_plan();g.validate_before(plan,before)
    g.require(Path(u.Paths.project_dir()).resolve()==g.PROJECT,'Only the existing own R3 project may run the scene repair')
    report_path=g.OUTPUT/REPORT;g.require(not report_path.exists(),'Preserve each scene-only attempt')
    for cls in ('UsdAssetUserData','SkeletalMeshActor','SkeletalMeshComponent','StaticMeshActor','MaterialFactoryNew',
                'MaterialExpressionConstant3Vector','MaterialExpressionConstant','LevelEditorSubsystem',
                'EditorActorSubsystem','UnrealEditorSubsystem'):
        g.require(hasattr(u,cls),'Required scene-only reflected API missing: '+cls)
    startup={'r.Nanite.AllowAssemblies':u.SystemLibrary.get_console_variable_int_value('r.Nanite.AllowAssemblies'),
             'r.Nanite.Foliage':u.SystemLibrary.get_console_variable_int_value('r.Nanite.Foliage')}
    g.require(startup=={'r.Nanite.AllowAssemblies':1,'r.Nanite.Foliage':0},'Keep the exact existing assembly-only startup')
    asset_paths=u.EditorAssetLibrary.list_assets(g.PREFIX+'/OriginalUSD',recursive=True,include_folder=False)
    assets=[u.load_asset(path) for path in asset_paths]
    g.require(len(assets)==39 and all(a is not None for a in assets),'Exactly39 preserved USD assets required')
    observed=[n.asset_observation(u,a) for a in assets]
    selected=n.whole_tree_observation(observed,source)
    tree_mesh=next(a for a in assets if a.get_path_name()==selected['path'])
    colors={tuple(r['vectorParameters']['BaseColor'][:3]) for r in observed if 'BaseColor' in r.get('vectorParameters',{})}
    g.require(colors=={(.1420000046491623,.06599999964237213,.03099999949336052),
                       (.08699999749660492,.15299999713897705,.020999999716877937)}
              and not any(isinstance(a,u.Texture) for a in assets),'Original constant materials/no replacement textures required')
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem);actors=u.get_editor_subsystem(u.EditorActorSubsystem)
    g.require(levels is not None and actors is not None and hasattr(levels,'new_level') and hasattr(levels,'get_current_level'),
              'Reflected active-map creation/current-level APIs required before scene work')
    g.require(levels.load_level('/Game/Brezi/Maps/Brezi'),'Could not read the own unchanged source map')
    light_classes=(u.DirectionalLight,u.SkyLight,u.SkyAtmosphere,u.VolumetricCloud,u.ExponentialHeightFog,u.PostProcessVolume)
    lights=[a for a in actors.get_all_level_actors() if isinstance(a,light_classes)]
    g.require(sum(isinstance(a,u.DirectionalLight) for a in lights)==1 and sum(isinstance(a,u.SkyLight) for a in lights)==1,
              'Exactly the actual original native day sun and sky required')
    observed_lights=[lighting_snapshot(u,a) for a in lights]
    light_values=[capture_light_values(u,a) for a in lights]
    source_light_receipt=g.OUTPUT/'oak-usd-scene-lighting-before-r5.json';g.write(source_light_receipt,observed_lights)
    # Do not retain source actor/component wrappers across NewMap.
    del lights
    g.require(not u.EditorAssetLibrary.does_asset_exist(g.MAP),'Fresh own R5 probe map required')
    g.require(levels.new_level(g.MAP,False),'Active editor NewLevel failed')
    world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_editor_world()
    current=levels.get_current_level()
    g.require(world is not None and current is not None and world.get_path_name()==g.MAP+'.EnglishOakPilotR5'
              and current.get_path_name()==g.MAP+'.EnglishOakPilotR5:PersistentLevel',
              'The fresh own editor world and current level must be active before any spawn')
    initialization={'newLevelReturnedTrue':True,'editorWorld':world.get_path_name(),'currentLevel':current.get_path_name()}
    copied=[spawn_light_values(u,actors,data) for data in light_values]
    copied_observed=[lighting_snapshot(u,a) for a in copied]
    copied_receipt=g.OUTPUT/'oak-usd-scene-lighting-copied-r5.json';g.write(copied_receipt,copied_observed)
    differences=lighting_difference(observed_lights,copied_observed)
    diff_receipt=g.OUTPUT/'oak-usd-scene-lighting-differences-r5.json'
    g.write(diff_receipt,{'schema':g.SCHEMA,'owner':OWNER,'nativeProcessId':os.getpid(),
        'source':g.pin(source_light_receipt),'copied':g.pin(copied_receipt),**differences,
        'numericalToleranceApplied':False,'nativeAppearanceAccepted':False})
    g.require(not differences['differences'],'Explicit observed daylight/PP subset differs; actual complete difference receipt preserved')
    tree_mesh=u.load_asset(selected['path'])
    g.require(isinstance(tree_mesh,u.SkeletalMesh),'Reload saved root asset by path after active-world change')
    tree=actors.spawn_actor_from_class(u.SkeletalMeshActor,u.Vector(0,0,0),u.Rotator(0,0,0))
    g.require(tree is not None,'Could not place saved original whole-D mesh')
    tree.set_actor_label('Original licensed English Oak D · constant USD materials')
    tree.set_editor_property('tags',[u.Name('BreziEnglishOakPilotR5')])
    component=tree.get_component_by_class(u.SkeletalMeshComponent);component.set_skeletal_mesh_asset(tree_mesh)
    component.set_collision_enabled(n.enum(u,'CollisionEnabled','NO_COLLISION'))
    ground=actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,-2),u.Rotator(0,0,0))
    g.require(ground is not None,'Could not create declared neutral ground actor')
    ground.set_actor_label('Oak pilot · neutral45m ground');ground.set_actor_scale3d(u.Vector(45,45,1))
    ground.set_editor_property('tags',[u.Name('BreziEnglishOakPilotR5')])
    gc=ground.get_component_by_class(u.StaticMeshComponent);gc.set_static_mesh(u.load_asset('/Engine/BasicShapes/Plane'))
    tools=u.AssetToolsHelpers.get_asset_tools()
    material=tools.create_asset('M_PilotNeutralGroundR5',g.PREFIX+'/Materials',u.Material,u.MaterialFactoryNew())
    g.require(material is not None,'Could not create separate neutral-ground material')
    color=u.MaterialEditingLibrary.create_material_expression(material,u.MaterialExpressionConstant3Vector,0,0)
    color.set_editor_property('constant',u.LinearColor(.18,.18,.18,1))
    g.require(u.MaterialEditingLibrary.connect_material_property(color,'',n.enum(u,'MaterialProperty','MP_BASE_COLOR')),
              'Neutral-ground color connection failed')
    for key,value in [('MP_ROUGHNESS',.8),('MP_SPECULAR',.25)]:
        node=u.MaterialEditingLibrary.create_material_expression(material,u.MaterialExpressionConstant,0,0)
        node.set_editor_property('r',value)
        g.require(u.MaterialEditingLibrary.connect_material_property(node,'',n.enum(u,'MaterialProperty',key)),
                  'Neutral-ground scalar connection failed')
    g.require(not u.MaterialEditingLibrary.recompile_material(material),'Neutral-ground material compile errors')
    gc.set_material(0,material);gc.set_editor_property('cast_shadow',False)
    g.require(u.EditorAssetLibrary.save_loaded_asset(material) and levels.save_current_level(),'Could not save the own probe scene')
    tree_path=tree.get_path_name();ground_path=ground.get_path_name()
    del copied,tree,ground,component,gc,world,current
    g.require(levels.load_level('/Game/Brezi/Maps/Brezi') and levels.load_level(g.MAP),'Own probe must unload/reload')
    saved={a.get_path_name():a for a in actors.get_all_level_actors()}
    g.require(tree_path in saved and ground_path in saved,'Saved original tree or neutral ground missing')
    saved_tree=saved[tree_path]
    g.require(n.value(saved_tree.get_actor_location())==[0.,0.,0.]
              and n.value(saved_tree.get_actor_scale3d())==[1.,1.,1.]
              and n.value(saved_tree.get_actor_rotation())==[0.,0.,0.]
              and saved_tree.get_component_by_class(u.SkeletalMeshComponent).get_skeletal_mesh_asset().get_path_name()==selected['path'],
              'Saved original whole-D mesh/root/rotation/scale differs')
    saved_lights=[a for a in saved.values() if isinstance(a,light_classes)]
    g.require(sorted([lighting_snapshot(u,a) for a in saved_lights],key=lambda r:r['class'])==
              sorted(observed_lights,key=lambda r:r['class']),'Saved observed daylight/PP subset differs')
    camera=camera_append(plan);after=g.inventory(g.PROJECT);delta=g.validate_delta(before,after)
    g.require(g.inventory(g.BASE/'Project/BreziTwin')==g.read(g.check_pin(plan['originalSavedR32Inventory'])),
              'Original saved R32 source changed')
    for row in plan['inputFiles']:g.check_pin(row)
    original_log=g.check_pin(g.read(g.check_pin(plan['crashedImportByteAudit']))['nativeLog']).read_text(errors='replace')
    warnings=[line for line in original_log.splitlines() if 'Compute a zero length normal vector' in line or 'LogSkeletalMesh: Warning:' in line]
    report={'schema':g.SCHEMA,'owner':OWNER,'status':STATUS,'nativeProcessId':os.getpid(),'selectedPlan':g.pin(g.PLAN),
       'originalSourcePlan':plan['originalSourcePlan'],'baseNativeReport':plan['baseNativeReport'],
       'sourceExtraction':plan['sourceExtraction'],'usdInspection':plan['usdInspection'],'project':str(g.PROJECT),'map':g.MAP,
       'initialRootClone':plan['initialRootClone'],'projectPreparation':plan['projectPreparation'],
       'crashedImportByteAudit':plan['crashedImportByteAudit'],'failedSceneByteAudit':plan['failedSceneByteAudit'],'nativeStartupReadback':startup,
       'assets':observed,'wholeTreeMesh':selected['path'],'selectedRootUsdPrimPath':source['stageRoot'],
       'treeActor':tree_path,'groundActor':ground_path,'activeEditorMapInitialization':initialization,
       'sourceLightingObserved':g.pin(source_light_receipt),'savedLightingObservedSubset':[lighting_snapshot(u,a) for a in saved_lights],
       'lightingDifferences':g.pin(diff_receipt),'copiedLightingObserved':g.pin(copied_receipt),
       'lightingScope':plan['lightingScope'],'explicitObservedLightingSubsetCopiedAndReloaded':True,
       'fullLightingPropertyCloneClaimed':False,'daylightCopiedByNativeActorDuplication':False,
       'assetImportExecuted':False,'savedOriginalUsdPackages':39,'all39SavedOriginalUsdPackagesByteExact':True,
       'originalConstantMaterialsPreserved':True,'nativeTextureObjectsImported':0,'observedOriginalImportWarnings':warnings,
       'cameraDataDelta':camera,'beforeInventory':plan['beforeInventory'],'afterInventory':after,'projectDelta':delta,
       'probeMapUnloadedReloaded':True,'originalMainMapUnchanged':True,'originalSavedR32ProjectUnchanged':True,
       'nativeAssemblyNodesReadbackAvailable':selected['nativeAssemblyNodesReadbackAvailable'],
       'nativeFullGeometryCornerReadbackAvailable':False,'importedNormalsTangentsPreserved':False,
       'windSidecarImported':False,'dynamicWindEvaluated':False,'actualNaniteGpuPassAttributedToTree':False,
       'walkingCollisionAccepted':False,'matchedExteriorLightingPairClaimed':False,
       'nativeApplied':True,'nativeAppearanceAccepted':False,'performanceAccepted':False,
       'fullPhotorealismAccepted':False,'shippingVerified':False,'packageVerified':False}
    g.write(report_path,report);print(json.dumps({'report':g.pin(report_path),'status':STATUS}))

if __name__=='__main__':
    import unreal
    try:run(unreal)
    except Exception:
        error=traceback.format_exc();print(error);file=g.OUTPUT/REPORT
        if not file.exists():g.write(file,{'schema':g.SCHEMA,'owner':OWNER,'status':'failed-scene-only-attempt-preserved',
            'nativeProcessId':os.getpid(),'error':error,'assetImportExecuted':False,'nativeApplied':False,
            'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False})
        raise
