"""R24 DRAFT, root-only: one original-tree HISM on actual saved R22.

No source pixels/attributes or existing native packages are changed. The one
native source mesh keeps three sections and both UVs. Nanite resources may be
measured after build; eligibility/build are not rendering/performance acceptance.
"""
import argparse
from copy import deepcopy
from datetime import datetime,timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import subprocess
import sys
import time

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-original-tree-native.py'
REPORT='original-tree-native-report.json'
PREFIX='/Game/Brezi/OriginalTree20261002R24'
TAG='BreziOriginalTree20261002R24'
spec=importlib.util.spec_from_file_location('r24_original_native_guard',ROOT/'scripts/unreal/exterior-original-tree-guards.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
require,read,sha,pin,check_pin,digest=(getattr(guard,k)for k in ('require','read','sha','pin','check_pin','digest'))
MODULE_SHA='2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574'
READBACK_TIMINGS=[]


def now():return datetime.now(timezone.utc).isoformat()
def report_write(path,value):Path(path).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n')
def vec(v,axes='xyz'):return [float(getattr(v,a))for a in axes]
def matrix(component,index):
    value=component.get_editor_property('per_instance_sm_data')[index].get_editor_property('transform')
    return [[float(getattr(getattr(value,p),a))for a in 'xyzw']for p in ('x_plane','y_plane','z_plane','w_plane')]
def transform_value(value):return [vec(value.translation),vec(value.rotation,'xyzw'),vec(value.scale3d)]
def instance_value(component,index):
    value=component.get_instance_transform(index,False)
    if isinstance(value,tuple):require(value[0]is True,'Cannot read actual tree instance');value=value[1]
    return value


def primary_api_pins():
    engine=Path('/Users/Shared/Epic Games/UE_5.8/Engine')
    files=['Source/Runtime/Engine/Classes/Engine/StaticMesh.h','Source/Runtime/Engine/Private/StaticMesh.cpp',
        'Source/Runtime/MeshDescription/Public/MeshDescriptionBase.h','Source/Runtime/StaticMeshDescription/Public/StaticMeshDescription.h',
        'Source/Runtime/Engine/Classes/Components/InstancedStaticMeshComponent.h','Source/Runtime/Engine/Private/InstancedStaticMesh.cpp',
        'Source/Runtime/Engine/Private/HierarchicalInstancedStaticMesh.cpp','Source/Runtime/Engine/Public/Materials/MaterialInterface.h',
        'Source/Editor/MaterialEditor/Public/MaterialEditingLibrary.h','Source/Runtime/Engine/Public/Materials/Material.h',
        'Source/Runtime/Engine/Classes/Engine/EngineTypes.h','Source/Runtime/Engine/Classes/Engine/Texture.h',
        'Plugins/Interchange/Runtime/Source/Pipelines/Public/InterchangeGenericAssetsPipelineSharedSettings.h',
        'Plugins/Interchange/Runtime/Source/Pipelines/Public/InterchangeGenericAssetsPipeline.h',
        'Plugins/Interchange/Runtime/Source/Pipelines/Public/InterchangeGenericMaterialPipeline.h',
        'Plugins/Interchange/Runtime/Source/Pipelines/Public/InterchangeGenericTexturePipeline.h']
    return {p:pin(engine/p)for p in files}


def preflight(directory,base_report):
    directory=Path(directory).resolve();require(directory.is_relative_to(ROOT/'output/unreal')and not directory.exists(),'Fresh source preflight required')
    bundle=guard.load_source();base=guard.load_saved_base(base_report)
    module_order=helpers(base)['moduleOrderWitness']
    directory.mkdir();descriptor=directory/'source-import-untransformed.gltf';guard.write(descriptor,guard.import_descriptor(bundle,directory))
    binary=bundle['binaryPath'].read_bytes();parts=[];started=time.perf_counter()
    for i,primitive in enumerate(bundle['original']['meshes'][0]['primitives']):
        full=guard.corner_hash(guard.source_corners(bundle['original'],binary,primitive))
        indices=guard.sample_triangle_indices(full['triangles'],guard.SAMPLE_COUNTS[i])
        parts.append({'section':i,'material':bundle['original']['materials'][i]['name'],**full,
            'sampleTriangleIndices':indices,**guard.sampled_corner_hash((j,guard.source_face(bundle['original'],binary,primitive,j))for j in indices)})
    require(sum(p['triangles']for p in parts)==2062487,'All original three-section triangles required')
    bounds=guard.source_bounds(bundle['original'],binary);source_seconds=time.perf_counter()-started
    pipelines={str(ROOT/'scripts/unreal'/p):sha(ROOT/'scripts/unreal'/p)for p in ('exterior-original-tree-native.py','exterior-original-tree-materials.py','exterior-original-tree-guards.py')}
    for row in base['report']['ownedSources'].values():pipelines[row['live']['path']]=row['live']['sha256']
    inputs={r['path']:r['sha256']for r in bundle['r2']['inputFiles'].values()};inputs.update({r['path']:r['sha256']for r in primary_api_pins().values()})
    inputs.update(base['report']['inputFiles'])
    terminal=read(base['process']['receipt']['path']);inputs.update(terminal['sourcePinsBeforeNative'])
    for row in (base['pin'],base['process']['receipt'],base['process']['raw'],base['process']['log']):inputs[row['path']]=row['sha256']
    tests=ROOT/'scripts/unreal/test_exterior_original_tree_native.py';pipelines[str(tests)]=sha(tests)
    command=[sys.executable,str(tests),'-v'];completed=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
    test_log=directory/'cpu-source-tests.log';test_log.write_text(completed.stdout+completed.stderr)
    require(completed.returncode==0 and 'Ran 17 tests in 'in completed.stderr and completed.stderr.rstrip().endswith('OK'),'Actual focused R24 CPU source tests failed')
    test_receipt=directory/'cpu-source-tests.json';guard.write(test_receipt,{'schemaVersion':1,'owner':OWNER,'status':'passed',
        'command':command,'exitCode':completed.returncode,'testCount':17,'log':pin(test_log),
        'sourcePins':{str(ROOT/'scripts/unreal'/p):sha(ROOT/'scripts/unreal'/p)for p in ('exterior-original-tree-native.py','exterior-original-tree-materials.py','exterior-original-tree-guards.py','test_exterior_original_tree_native.py')},
        'nativeExecuted':False,'nativeAppearanceAccepted':False})
    inputs[str(test_receipt)]=sha(test_receipt);inputs[str(test_log)]=sha(test_log)
    record={'schemaVersion':1,'owner':OWNER,'status':'original-tree-source-preflight-validated-native-pending',
        'baseNativeReport':base['pin'],'baseNativeProcess':base['process'],'baseNativeHelper':base['nativeHelperPin'],'sourceStudy':pin(guard.R1/'original-tree-source-plan.json'),
        'baseHelperModuleOrderWitness':module_order,
        'tangentSupplement':pin(guard.R2/'original-tree-tangent-supplement-r2.json'),'importDescriptor':pin(descriptor),
        'nativePlacementContract':guard.placement_contract(bundle),'nativeExpectedSections':parts,
        'sourceTests':pin(test_receipt),
        'nativeExpectedSourceBounds':bounds,'sourceFullCornerHashCpuSeconds':source_seconds,
        'nativeReadbackContract':{'sampleTriangleCounts':list(guard.SAMPLE_COUNTS),'totalSampleTriangles':4096,
            'reflectedGetterCallsPerSampleTriangle':16,'estimatedGeometryGetterCallsPerPass':65536,
            'fullNativeCornerReadbackPerformed':False,'nativeGetterThroughputMeasured':False,
            'sourceFullCornerHashesAreNativeProof':False,'sourceBoundsCompatibilityCapCm':.002},
        'primaryApiPins':primary_api_pins(),'pipelineFiles':pipelines,'inputFiles':inputs,
        'nativeApplied':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,
        'nativeNormalTangentReadbackAvailable':False,'sourcePlantChoiceArtistic':True,'ecologicalFitVerified':False,
        'naniteResourceBuildPending':True,'naniteRenderPassVerified':False,'performanceAccepted':False}
    guard.write(directory/'source-preflight.json',record);print(json.dumps({'preflight':pin(directory/'source-preflight.json'),'sections':parts,'nativeApplied':False}))


def validated_preflight(path,bundle,base):
    r=read(path);require(r['schemaVersion']==1 and r['owner']==OWNER and r['status']=='original-tree-source-preflight-validated-native-pending'
        and r['baseNativeReport']==base['pin']and r['baseNativeProcess']==base['process']and r['baseNativeHelper']==base['nativeHelperPin']and r['sourceStudy']==pin(guard.R1/'original-tree-source-plan.json')
        and r['tangentSupplement']==pin(guard.R2/'original-tree-tangent-supplement-r2.json')and r['nativeApplied']is False,'Actual successful-base typed preflight required')
    descriptor=check_pin(r['importDescriptor']);require(read(descriptor)==guard.import_descriptor(bundle,descriptor.parent)
        and r['nativePlacementContract']==guard.placement_contract(bundle),'Source import/placement scope changed')
    require(r['primaryApiPins']==primary_api_pins(),'Reviewed engine primary API changed')
    tests=read(check_pin(r['sourceTests']));require(tests['owner']==OWNER and tests['schemaVersion']==1 and tests['status']=='passed'
        and tests['testCount']==17 and tests['exitCode']==0 and tests['nativeExecuted']is False
        and tests['sourcePins']=={str(ROOT/'scripts/unreal'/p):sha(ROOT/'scripts/unreal'/p)for p in ('exterior-original-tree-native.py','exterior-original-tree-materials.py','exterior-original-tree-guards.py','test_exterior_original_tree_native.py')},'Focused actual CPU source test closure changed')
    check_pin(tests['log'])
    for p,h in {**r['pipelineFiles'],**r['inputFiles']}.items():require(sha(p)==h,'Consumed source/API changed: '+p)
    for file in (OWNER,'scripts/unreal/exterior-original-tree-materials.py','scripts/unreal/exterior-original-tree-guards.py'):
        require(str(ROOT/file)in r['pipelineFiles'],'Own executable source pin missing')
    require([p['triangles']for p in r['nativeExpectedSections']]==[94814,1939380,28293],'Exact source section census required')
    require([p['sampleTriangleIndices']for p in r['nativeExpectedSections']]==[guard.sample_triangle_indices(p['triangles'],count)for p,count in zip(r['nativeExpectedSections'],guard.SAMPLE_COUNTS)]
        and [p['sampleTriangles']for p in r['nativeExpectedSections']]==list(guard.SAMPLE_COUNTS)
        and r['nativeReadbackContract']=={'sampleTriangleCounts':list(guard.SAMPLE_COUNTS),'totalSampleTriangles':4096,
            'reflectedGetterCallsPerSampleTriangle':16,'estimatedGeometryGetterCallsPerPass':65536,
            'fullNativeCornerReadbackPerformed':False,'nativeGetterThroughputMeasured':False,
            'sourceFullCornerHashesAreNativeProof':False,'sourceBoundsCompatibilityCapCm':.002},'Bounded honest native geometry sample contract changed')
    return r,descriptor


def helpers(base):
    require(pin(base['nativeHelper'])==base['nativeHelperPin']and str(base['nativeHelper'])==str(ROOT/base['report']['owner']),'Actual saved base executable pin/owner differs')
    composed=guard.module('r24_frozen_saved_base_native',base['nativeHelper'].name)
    _,bundle=base['guard'].validate_plan();h=composed.helpers(bundle)
    h.update(composed=composed,baseBundle=bundle,treeMaterials=guard.module('r24_owned_maps','exterior-original-tree-materials.py'))
    return h


def native_mesh_proof(u,mesh,preflight):
    started=time.perf_counter()
    d=mesh.get_static_mesh_description(0);require(d and d.get_triangle_count()==2062487 and d.get_polygon_count()==2062487 and d.get_polygon_group_count()==3
        and mesh.get_num_lods()==1 and len(mesh.get_editor_property('static_materials'))==3,'Actual full original three-section source mesh required')
    result=[];offset=0
    for expected in preflight['nativeExpectedSections']:
        section=expected['section'];count=expected['triangles'];faces=[]
        require(d.get_num_polygon_group_polygons(u.PolygonGroupID(id_value=section))==count,'Actual source section polygon census differs')
        for j in expected['sampleTriangleIndices']:
            triangle=u.TriangleID(id_value=offset+j)
            require(int(d.get_triangle_polygon_group(triangle).id_value)==section,'Source section/triangle order changed')
            face=[]
            for corner in range(3):
                vi=d.get_triangle_vertex_instance(triangle,corner);p=vec(d.get_vertex_position(d.get_vertex_instance_vertex(vi)))
                face.append(tuple(p+vec(d.get_vertex_instance_uv(vi,0),'xy')+vec(d.get_vertex_instance_uv(vi,1),'xy')))
            faces.append((j,face))
        sample=guard.sampled_corner_hash(faces)
        require(sample=={k:expected[k]for k in sample},'Actual sampled native F32 positions/UV0/UV1/winding differ: '+expected['material'])
        result.append({'section':section,'material':expected['material'],'sourceSectionPolygonCount':count,
            'sampleTriangleIndices':expected['sampleTriangleIndices'],**sample,
            'fullSourceCornerHashCpuOnly':expected['orderedFloat32PositionUV0UV1CornersSha256']});offset+=count
    bounds=mesh.get_bounds();origin,extent=vec(bounds.origin),vec(bounds.box_extent)
    minimum=[a-b for a,b in zip(origin,extent)];maximum=[a+b for a,b in zip(origin,extent)]
    expected=preflight['nativeExpectedSourceBounds'];cap=preflight['nativeReadbackContract']['sourceBoundsCompatibilityCapCm']
    require(max(abs(a-b)for a,b in zip(minimum+maximum,expected['minimumCm']+expected['maximumCm']))<=cap,'Actual mesh bounds exceed source FLOAT compatibility cap')
    require(mesh.get_num_sections(0)==3,'Actual render fallback must retain three material sections')
    timing={'pass':len(READBACK_TIMINGS)+1,'sampleTriangles':4096,'geometryReflectedGetterCalls':65536,'elapsedSeconds':time.perf_counter()-started}
    READBACK_TIMINGS.append(timing);print(json.dumps({'nativeGeometrySampleTiming':timing}))
    return {'mesh':mesh.get_path_name(),'sourceSections':result,'sourceTriangles':offset,'sourceDescriptionVertices':d.get_vertex_count(),
        'sourceDescriptionVertexInstances':d.get_vertex_instance_count(),'nativeSampledPositionUV0UV1SectionOrderVerified':True,
        'nativeFullPositionUV0UV1CornerReadbackPerformed':False,'sampledNativeTriangles':4096,'unsampledNativeTriangles':2058391,
        'nativeSourceSectionPolygonCountsVerified':True,'nativeBounds':{'originCm':origin,'extentCm':extent,'minimumCm':minimum,'maximumCm':maximum},
        'nativeBoundsSourceFloatCompatibilityCapCm':cap,
        'nativeNormalTangentReadbackAvailable':False,'nativeTangentHandednessVerified':False,'sourceDerivedTangentRequestOnly':True,
        'sourceLODCount':1,'renderFallbackTriangles':mesh.get_num_triangles(0),'renderFallbackSections':mesh.get_num_sections(0)}


def nanite_readback(mesh):
    settings=mesh.get_editor_property('nanite_settings');require(settings.get_editor_property('enabled'),'Owned tree Nanite setting missing')
    vertices=int(mesh.get_num_nanite_vertices());triangles=int(mesh.get_num_nanite_triangles())
    require(vertices>0 and triangles>0,'Actual owned tree has no built nonempty Nanite resource census')
    return {'enabled':True,'nativeResourceInputVertices':vertices,'nativeResourceInputTriangles':triangles,
        'actualNonemptyResourceGetterVerified':True,'hasValidNaniteDataDirectGetterAvailable':False,
        'proof':'Installed reflected getters return positive counts only with HasValidNaniteData and nonempty RootData.',
        'nativeRenderPassVerified':False,'performanceAccepted':False,'shippingVerified':False}


def import_geometry(u,descriptor,bundle,materials,h):
    assets=u.EditorAssetLibrary;actors=u.get_editor_subsystem(u.EditorActorSubsystem);levels=u.get_editor_subsystem(u.LevelEditorSubsystem);pipelines=[]
    for original,name in [('GLTFSceneAssets','Assets'),('GLTFMaterials','Materials'),('LevelActors','Level')]:
        path=PREFIX+'/Pipeline/'+name;require(not assets.does_asset_exist(path),'Fresh owned tree import pipelines required')
        p=assets.duplicate_asset('/Game/Brezi/Pipeline/'+original,path);require(p,'Cannot duplicate owned tree pipeline');pipelines.append(p)
    mp=pipelines[0].get_editor_property('mesh_pipeline')
    for k,v in {'combine_static_meshes_behavior':u.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE,'collision':False,'build_nanite':True,'generate_lightmap_u_vs':False}.items():mp.set_editor_property(k,v)
    common=pipelines[0].get_editor_property('common_meshes_properties')
    for k,v in {'bake_meshes':False,'bake_pivot_meshes':False,'import_lods':False,'remove_degenerates':False,
        'recompute_normals':False,'recompute_tangents':False,'use_full_precision_u_vs':True}.items():common.set_editor_property(k,v)
    nested=pipelines[0].get_editor_property('material_pipeline');nested.set_editor_property('import_materials',False);nested.get_editor_property('texture_pipeline').set_editor_property('import_textures',False)
    pipelines[2].set_editor_property('scene_hierarchy_type',u.InterchangeSceneHierarchyType.CREATE_LEVEL_ACTORS)
    params=u.ImportAssetParameters()
    for k,v in {'is_automated':True,'replace_existing':False,'force_show_dialog':False,'override_pipelines':[u.SoftObjectPath(p.get_path_name())for p in pipelines],'import_level':levels.get_current_level()}.items():params.set_editor_property(k,v)
    before={a.get_path_name()for a in actors.get_all_level_actors()};manager=u.InterchangeManager.get_interchange_manager_scripted()
    require(manager.import_scene(PREFIX+'/Geometry',manager.create_source_data(str(descriptor)),params),'Original tree import failed')
    temporary=[a for a in actors.get_all_level_actors()if a.get_path_name()not in before];meshes={}
    for actor in temporary:
        for c in actor.get_components_by_class(u.StaticMeshComponent):
            mesh=c.get_editor_property('static_mesh');require(mesh and mesh.get_path_name().startswith(PREFIX+'/Geometry/'),'Foreign imported tree asset');meshes[mesh.get_path_name()]=mesh
    require(len(meshes)==1,'Exactly one original multi-section tree mesh may import');mesh=next(iter(meshes.values()));slots=mesh.get_editor_property('static_materials')
    require(len(slots)==3,'Exactly three original material slots required')
    for i,(slot,recipe)in enumerate(zip(slots,bundle['recipes'])):
        name=str(slot.get_editor_property('imported_material_slot_name'))
        require(name==bundle['original']['materials'][i]['name'],'Imported original material section order/name changed');mesh.set_material(i,materials[recipe['id']])
    mesh.set_editor_property('has_navigation_data',False);build=h['meshHelper'].static_mesh_subsystem(u).get_lod_build_settings(mesh,0)
    for k,v in {'recompute_normals':False,'recompute_tangents':False,'remove_degenerates':False,'generate_lightmap_u_vs':False,'use_full_precision_u_vs':True}.items():build.set_editor_property(k,v)
    h['meshHelper'].static_mesh_subsystem(u).set_lod_build_settings(mesh,0,build)
    for key,value in {'BreziGeneratedBy':OWNER,'BreziR24OriginalSourceBinary':sha(bundle['binaryPath']),'BreziR24DerivedTangentBuffer':sha(bundle['tangentPath']),'BreziR24SourceDescriptor':sha(descriptor)}.items():assets.set_metadata_tag(mesh,key,value)
    require(assets.save_loaded_asset(mesh,False),'Cannot save owned original tree mesh');h['meshHelper'].finish_static_mesh_compilation(u,synchronous=True)
    for actor in reversed(temporary):require(actors.destroy_actor(actor),'Cannot remove temporary tree import actor')
    for p in pipelines:require(assets.save_loaded_asset(p,False),'Cannot save own import pipeline')
    removed=[]
    for path in assets.list_assets(PREFIX+'/Geometry',recursive=True,include_folder=False):
        if path.split('.')[0]==mesh.get_path_name().split('.')[0]:continue
        value=assets.load_asset(path);require(value and value.get_class().get_name()=='InterchangeSceneImportAsset','Unexpected owned importer asset')
        removed.append(path);require(assets.delete_asset(path),'Cannot remove own reimport metadata')
    return mesh,[p.get_path_name()for p in pipelines],removed


def selected_component(u,bundle,base,h):
    path=bundle['selection']['originalNativeActor'];actors={a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
    require(path in actors,'Selected actual original tree group missing');actor=actors[path];c=actor.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
    row=base['witness'][path];require(c and c.get_instance_count()==4 and len(row['components'])==1 and actor.get_actor_label()==bundle['selection']['groupId'],'Only original four-member tree group may change')
    identity=[[0.,0.,0.],[0.,0.,0.,1.],[1.,1.,1.]]
    require(transform_value(actor.get_actor_transform())==identity and transform_value(c.get_world_transform())==identity,'Original tree HISM frame is not identity')
    require(c.get_editor_property('num_custom_data_floats')==0 and not c.get_editor_property('per_instance_sm_custom_data'),'Unreviewed custom instance rows cannot be reordered')
    values=[transform_value(instance_value(c,i))for i in range(4)];matrices=[matrix(c,i)for i in range(4)]
    require(digest(values)==row['components'][0]['orderedInstanceTransformsSha256'],'Actual four original ordered roots changed')
    root=bundle['selection']['originalSourceRow']['positionCm'];require(max(abs(a-b)for a,b in zip(values[0][0],root))<=.02,'Original selected root differs from source envelope witness')
    return actor,c,values,matrices,instance_value(c,0)


def retire_selected(actor,c,values,matrices):
    require(c.remove_instances([0]),'Cannot retire exact selected old tree index0')
    require([matrix(c,i)for i in range(3)]==[matrices[i]for i in (3,1,2)],'Unreviewed native removal ordering')
    data=c.get_editor_property('per_instance_sm_data')
    c.set_editor_property('per_instance_sm_data',[data[1],data[2],data[0]])
    actor.synchronize_instance_bounds()
    require([matrix(c,i)for i in range(3)]==matrices[1:]and [transform_value(instance_value(c,i))for i in range(3)]==values[1:],
        'Remaining three original stored matrices/order changed')
    return {'retiredOriginalIndex':0,'retainedOriginalIndices':[1,2,3],'storedMatricesBefore':matrices,
        'storedMatricesRetained':matrices[1:],'allRetainedNativeMatrixAndRecoveredTransformBytesExact':True,
        'nativeRemovalInitialOrder':[3,1,2],'retainedSourceOrderRestoredWithoutTransformRecomposition':True}


def apply_new(u,bundle,mesh,original,h):
    actors=u.get_editor_subsystem(u.EditorActorSubsystem);actor=actors.spawn_actor_from_class(u.load_class(None,'/Script/BreziTwin.BreziVegetationPatch'),u.Vector(0,0,0),u.Rotator())
    require(actor,'Cannot spawn one owned full-original tree actor');actor.tags=[u.Name('BreziGenerated'),u.Name(TAG)];actor.set_actor_label('R24_original_tree_village_nearest_grove_3');actor.set_folder_path('Brezi/OriginalTree20261002R24');actor.set_actor_tick_enabled(False)
    c=actor.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent);require(c and actor.get_editor_property('root_component')==c and c.get_owner()==actor,'Owned original tree HISM must be actor root')
    h['rural'].new_component_policy(u,c);require(c.set_static_mesh(mesh),'Cannot bind owned original tree master');c.set_editor_property('cast_shadow',True);c.set_editor_property('visible_in_ray_tracing',True);c.set_editor_property('disallow_nanite',False)
    c.set_cull_distances(62500,125000);actor.set_detail_density_scaling(False)
    contract=guard.placement_contract(bundle);value=u.Transform();value.set_editor_property('translation',u.Vector(*[a+b for a,b in zip(vec(original.translation),contract['instanceOriginOffsetCm'])]))
    value.set_editor_property('rotation',original.rotation);value.set_editor_property('scale3d',u.Vector(*contract['instanceUniformScale']))
    require(vec(value.rotation,'xyzw')==vec(original.rotation,'xyzw'),'Original selected native rotation was not copied exactly')
    input_value=transform_value(value);require(list(c.add_instances([value],True,False,False))==[0],'Only one original-tree instance may add');actor.synchronize_instance_bounds()
    return actor.get_path_name(),{'sourceInputTransform':input_value,'actualRecoveredTransform':transform_value(instance_value(c,0)),'actualStoredMatrix':matrix(c,0),'nativeComputedInputVersusRecoveredTransformExactClaim':False}


def actual_matrix_footprint(bundle,stored,source_root):
    """CPU projection of actual stored matrix, never a GPU readback claim."""
    binary=bundle['binaryPath'].read_bytes();minimum=[math.inf]*3;maximum=[-math.inf]*3;radius=0.;count=0
    center=stored[3][:2]
    for primitive in bundle['original']['meshes'][0]['primitives']:
        accessor,offset,stride=guard.accessor_layout(bundle['original'],primitive['attributes']['POSITION'])
        for i in range(accessor['count']):
            x,y,z=struct.unpack_from('<fff',binary,offset+i*stride);local=[guard.f32(x*100),guard.f32(z*100),guard.f32(y*100)]
            world=[sum(local[k]*stored[k][axis]for k in range(3))+stored[3][axis]for axis in range(3)]
            radius=max(radius,math.hypot(world[0]-center[0],world[1]-center[1]));count+=1
            for axis in range(3):minimum[axis]=min(minimum[axis],world[axis]);maximum[axis]=max(maximum[axis],world[axis])
    require(count==1777278 and radius<bundle['selection']['originalSourceRow']['radiusCm']
        and abs(minimum[2]-source_root[2])<=.02 and abs(maximum[2]-minimum[2]-bundle['selection']['newActorProposal']['authoredHeightCm'])<=.03,
        'Actual stored-matrix complete shape escaped original root/height/crown envelope')
    poly=guard.module('r24_frozen_source_mask_projection','exterior-grove-substrate-native.py')
    ecology=read(check_pin(bundle['r1']['inputFiles']['ecology']));lawn=read(check_pin(bundle['r1']['inputFiles']['managedLawn']))
    masks={k:poly._PolygonIndex(v)for k,v in ecology['exclusionDomainsCm'].items()}
    masks['managedLawn']=poly._PolygonIndex({'type':'MultiPolygon','coordinates':[[r+[r[0]]if r[0]!=r[-1]else r]for r in lawn['managedLawnKeepPolygonsCm']]})
    clearances={}
    for key,mask in masks.items():
        distance=min(poly.base._distance(center,a,b)for a,b in mask.edges)
        require(not mask.contains(center)and distance-radius>75,'Actual stored-matrix complete circle intersects source exclusion: '+key)
        clearances[key]=distance-radius
    ring=ecology['sourceRegion']['polygonCm'];domain=poly._PolygonIndex({'type':'Polygon','coordinates':[ring+[ring[0]]]})
    grove=min(poly.base._distance(center,a,b)for a,b in domain.edges)-radius
    require(domain.contains(center)and grove>0,'Actual stored-matrix full circle leaves original grove')
    return {'decodedFullOriginalVertices':count,'actualStoredMatrixProjectedWorldBoundsCm':[minimum,maximum],
        'allVertexContainingCircleRadiusCm':radius,'sourceExclusionCircleClearancesCm':clearances,
        'originalGroveCircleClearanceCm':grove,'completeOriginalTriangleInteriorsConservativelyProven':2062487,
        'nativeStoredMatrixReadbackUsed':True,'float32ProjectionIsGpuReadback':False,
        'sourceLandUseAndElevationSurveyed':False,'normalTangentNativeReadbackAvailable':False}


def verify_scene(u,bundle,mesh,added_path,new_before,h):
    actors={a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
    require({p for p,a in actors.items()if a.actor_has_tag(TAG)}=={added_path},'Only one owned tree actor allowed')
    a=actors[added_path];c=a.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
    require(c and c.get_instance_count()==1 and c.get_editor_property('static_mesh')==mesh and not a.is_actor_tick_enabled()
        and not a.get_detail_density_scaling()and not a.actor_has_tag('BreziLawnDetail')and a.get_editor_property('root_component')==c,
        'Owned tree/root/density classification differs')
    identity=[[0.,0.,0.],[0.,0.,0.,1.],[1.,1.,1.]]
    require(transform_value(a.get_actor_transform())==transform_value(c.get_world_transform())==identity,'Owned tree frame must remain exact identity')
    require(c.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION and str(c.get_collision_profile_name())=='NoCollision'
        and not c.get_editor_property('can_ever_affect_navigation')and not c.get_editor_property('generate_overlap_events')and not c.is_component_tick_enabled()
        and c.get_editor_property('cast_shadow')and c.get_editor_property('visible_in_ray_tracing')and not c.get_editor_property('disallow_nanite')
        and c.is_visible()and not c.get_editor_property('hidden_in_game')and [c.get_editor_property(k)for k in ('instance_start_cull_distance','instance_end_cull_distance')]==[62500,125000],
        'Owned tree collision/render/cull policies changed')
    require(transform_value(instance_value(c,0))==new_before['actualRecoveredTransform']and matrix(c,0)==new_before['actualStoredMatrix'],'Saved owned tree matrix/recovered transform changed')
    return {'actor':added_path,'instanceCount':1,'actualRecoveredTransform':transform_value(instance_value(c,0)),'actualStoredMatrix':matrix(c,0),
        'originalRootRotationCopiedBeforeInsertion':True,'nativeMatrixProjectionIsGpuReadback':False,
        'fullOriginalVertexMaskProofSourceReference':bundle['r1']['maskReview'],'sourceNodeFit':guard.placement_contract(bundle),
        'nativeNormalsTangentsHandednessReadbackAvailable':False,'nativeVisualAccepted':False}


def main():
    import unreal as u
    output=Path(os.environ['BREZI_ORIGINAL_TREE_OUTPUT']).resolve();project=output/'Project/BreziTwin'
    require(output.is_relative_to(ROOT/'output/unreal')and output!=guard.BASE and Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==project,'Own isolated actual R22 clone required')
    bundle=guard.load_source();base=guard.load_saved_base(os.environ['BREZI_ORIGINAL_TREE_BASE_REPORT']);preflight_path=Path(os.environ['BREZI_ORIGINAL_TREE_PREFLIGHT']).resolve();preflight,descriptor=validated_preflight(preflight_path,bundle,base)
    require(sha(preflight_path)==os.environ['BREZI_ORIGINAL_TREE_PREFLIGHT_SHA256'],'Selected frozen original-tree preflight SHA differs')
    content=project/'Content';g=base['guard'].g;require(g.inventory(content)==base['content']and g.project_proof(project)==base['protected'],'Actual independent candidate must exactly match saved R22 bytes')
    clone_pin=guard.validate_clone(output/'original-tree-project-clone.json',project,base)
    for directory,rows in (('Content',base['content']),('',base['protected'])):
        for p in rows:
            src=guard.BASE/'Project/BreziTwin'/directory/p;dst=project/directory/p;require((src.stat().st_dev,src.stat().st_ino)!=(dst.stat().st_dev,dst.stat().st_ino),'No original/native hardlinks')
    require(sha(project/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib')==MODULE_SHA,'Frozen native module changed')
    source_module=guard.BASE/'Project/BreziTwin/Binaries/Mac/libUnrealEditor-BreziTwin.dylib';destination_module=project/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'
    source_build=read(guard.BASE/'Project/BreziTwin/Binaries/Mac/UnrealEditor.modules')['BuildId'];destination_build=read(project/'Binaries/Mac/UnrealEditor.modules')['BuildId']
    require(source_build==destination_build=='55116800'and source_module.stat().st_size==destination_module.stat().st_size==2818384,'Frozen actual module/engine identity changed')
    module_witness={'source':str(source_module),'destination':str(destination_module),'sha256':MODULE_SHA,'bytes':2818384,
        'sourceSha256':sha(source_module),'destinationSha256':sha(destination_module),'independentInodes':source_module.stat().st_ino!=destination_module.stat().st_ino,
        'sourceBuildId':source_build,'destinationBuildId':destination_build,'nativeModuleModified':False}
    report_path=output/REPORT;require(not report_path.exists(),'Fresh own typed original-tree report required');checkpoint=output/'original-tree-checkpoint';require(not checkpoint.exists(),'Fresh own checkpoint required');checkpoint.mkdir()
    h=helpers(base);require(h['moduleOrderWitness']==preflight['baseHelperModuleOrderWitness'],'Actual frozen-first saved-base helper module order changed')
    report={'schemaVersion':1,'owner':OWNER,'status':'original-tree-native-running','nativeProcessId':os.getpid(),'startedAt':now(),'output':str(output),'project':str(project),
        'baseNativeReport':base['pin'],'baseNativeProcess':base['process'],'baseNativeHelper':base['nativeHelperPin'],'projectClone':clone_pin,'sourceStudy':pin(guard.R1/'original-tree-source-plan.json'),
        'tangentSupplement':pin(guard.R2/'original-tree-tangent-supplement-r2.json'),'sourcePreflight':pin(preflight_path),
        'pipelineFiles':preflight['pipelineFiles'],'inputFiles':preflight['inputFiles'],'activeDesign':bundle['r1']['activeDesign'],
        'setbacksMm':{'street':3000,'east':3000},'nativeNormalTangentReadbackAvailable':False,'nativeAppearanceAccepted':False,
        'nativeModuleWitness':module_witness,
        'baseHelperModuleOrderWitness':h['moduleOrderWitness'],
        'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'packageVerified':False,'ecologicalFitVerified':False}
    report_write(report_path,report)
    try:
        levels=u.get_editor_subsystem(u.LevelEditorSubsystem);require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level('/Game/Brezi/Maps/Brezi'),'Cannot load own saved R22 map')
        before=h['composed'].full_witness(u,h);require(before==base['witness'],'Actual full5346 saved base actors/policies differ')
        before_materials=h['composed'].verify_materials(u,h['baseBundle'],h)
        old_actor,c,old_values,old_matrices,chosen=selected_component(u,bundle,base,h)
        materials,material_report=h['treeMaterials'].build_materials(u,bundle['recipes'],h['existing'].graph_snapshot)
        mesh,pipelines,metadata=import_geometry(u,descriptor,bundle,materials,h);source_mesh=native_mesh_proof(u,mesh,preflight);nanite=nanite_readback(mesh)
        retirement=retire_selected(old_actor,c,old_values,old_matrices);added,new_before=apply_new(u,bundle,mesh,chosen,h)
        original_expected=guard.expected_original(before,bundle['selection'],old_values[1:]);after_apply=h['composed'].full_witness(u,h)
        guard.validate_actor_delta(before,original_expected,after_apply,added);expected=deepcopy(original_expected);expected[added]=after_apply[added]
        native_scene=verify_scene(u,bundle,mesh,added,new_before,h);footprint=actual_matrix_footprint(bundle,new_before['actualStoredMatrix'],old_values[0][0])
        for name,value in [('before-actor-witness',before),('expected-actor-witness',expected),('base-content-inventory',base['content']),('protected-project-proof',base['protected']),('before-materials',before_materials)]:guard.write(checkpoint/(name+'.json'),value)
        require(levels.save_current_level(),'Cannot save own original-tree map');require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level('/Game/Brezi/Maps/Brezi'),'Cannot unload/reload saved original tree')
        saved=h['composed'].full_witness(u,h);require(saved==expected,'Saved original tree exceeds exact5347 full counterfactual')
        saved_actors={a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
        retained_component=saved_actors[bundle['selection']['originalNativeActor']].get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
        require(retained_component and retained_component.get_instance_count()==3 and [matrix(retained_component,i)for i in range(3)]==old_matrices[1:]
            and [transform_value(instance_value(retained_component,i))for i in range(3)]==old_values[1:],'Remaining original tree matrix/order changed after reload')
        saved_mesh=u.EditorAssetLibrary.load_asset(mesh.get_path_name());require(native_mesh_proof(u,saved_mesh,preflight)==source_mesh and nanite_readback(saved_mesh)==nanite,'Saved three-section source/Nanite resources changed')
        h['treeMaterials'].verify_materials(u,material_report,h['existing'].graph_snapshot);saved_scene=verify_scene(u,bundle,saved_mesh,added,new_before,h);require(saved_scene==native_scene,'Saved own tree source instance/policy differs')
        after_materials=h['composed'].verify_materials(u,h['baseBundle'],h);require(after_materials==before_materials,'Any of saved56 existing graphs/84 textures changed')
        after_content=g.inventory(content);known=[mesh.get_path_name(),*pipelines,*[r['asset']for r in material_report['materials'].values()],*[v['asset']for r in material_report['materials'].values()for v in r['textures'].values()]]
        packages=[p.split('.')[0].removeprefix('/Game/')+'.uasset'for p in known];delta=guard.validate_content(base['content'],after_content,packages)
        require(g.project_proof(project)==base['protected']and g.inventory(guard.BASE/'Project/BreziTwin/Content')==base['content']and g.project_proof(guard.BASE/'Project/BreziTwin')==base['protected'],'Protected/original saved base bytes changed')
        for p,v in {**preflight['inputFiles'],**preflight['pipelineFiles']}.items():require(sha(p)==v,'Executed tree/source inputs changed')
        for name,value in [('saved-actor-witness',saved),('after-content-inventory',after_content),('saved-materials',after_materials)]:guard.write(checkpoint/(name+'.json'),value)
        report.update(status='verified-saved-single-original-tree-overlay',completedAt=now(),savedMapUnloadedReloaded=True,
            savedActorCount=5347,originalActorCount=5346,newTreeActors=1,retiredTreeInstances=1,retainedOriginalTreeInstances=3,
            originalRootRetirement=retirement,newTree=saved_scene,actualStoredMatrixFullVertexMaskProof=footprint,newMesh=mesh.get_path_name(),materials=material_report,
            nativeSourceGeometry=source_mesh,nativeGeometrySampleTimings=READBACK_TIMINGS,naniteResourceReadback=nanite,importPipelineAssets=pipelines,removedOwnedReimportMetadata=metadata,
            beforeActorWitness=pin(checkpoint/'before-actor-witness.json'),expectedActorWitness=pin(checkpoint/'expected-actor-witness.json'),savedActorWitness=pin(checkpoint/'saved-actor-witness.json'),
            beforeActorWitnessSha256=digest(before),expectedActorWitnessSha256=digest(expected),savedActorWitnessSha256=digest(saved),
            baseContentInventory=pin(checkpoint/'base-content-inventory.json'),afterContentInventory=pin(checkpoint/'after-content-inventory.json'),protectedProjectProof=pin(checkpoint/'protected-project-proof.json'),
            originalMaterialTextureBefore=pin(checkpoint/'before-materials.json'),originalMaterialTextureSaved=pin(checkpoint/'saved-materials.json'),
            originalMaterialGraphsPreserved=56,originalTextureObjectsPreserved=84,assetDelta=delta,newContentPackages=packages,
            nativeModuleSha256=MODULE_SHA,originalSavedR22Unchanged=True,nativeNaniteResourcesBuilt=True,naniteRenderPassVerified=False,
            nativeGeometryPackagesIndependentlyReloaded=False,nativeMaterialsPackagesIndependentlyReloaded=False,
            sourcePlantChoiceArtistic=True,sourceRootGroundElevationSurveyed=False)
        report_write(report_path,report);print(json.dumps({'report':pin(report_path),'status':report['status'],'sourceTriangles':2062487,'nativeAppearanceAccepted':False}))
    except Exception as error:
        report.update(status='original-tree-native-failed',error=str(error),completedAt=now());report_write(report_path,report);raise


if __name__=='__main__':
    if '--preflight'in sys.argv:
        parser=argparse.ArgumentParser();parser.add_argument('--preflight',type=Path,required=True);parser.add_argument('--base-report',type=Path,required=True);args=parser.parse_args();preflight(args.preflight,args.base_report)
    else:main()
