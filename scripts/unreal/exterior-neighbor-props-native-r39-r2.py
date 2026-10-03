"""Root-only bound original whole neighbor props on selected saved R38b.

All old actors, wrapped instance hashes, material graphs/usage and visible
texture settings are read before and after. The complete hose's original
node pose composes with declared physical assembly roots; no old pose setter.
"""
import argparse
import copy
from datetime import datetime, timezone
import hashlib
import importlib.util
import io
import json
import math
import os
from pathlib import Path
import struct
import sys
import unittest
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-neighbor-props-native-r39-r2.py'
def module(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
g=module('_r39_bound_guards',ROOT/'scripts/unreal/exterior-neighbor-props-guards-r39-r2.py')
c=g.c
require,read,write,sha,pin,digest=(getattr(g,k)for k in ('require','read','write','sha','pin','digest'))
REPORT='neighbor-props-native-report-r2.json'
STATUS='verified-saved-six-whole-original-neighbor-prop-assemblies'
MAP='/Game/Brezi/Maps/Brezi'
TEST_COUNT=10
TEMPLATE='/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.BreziVegetationPatch_1000'
MATERIAL=ROOT/'scripts/unreal/exterior-neighbor-props-materials-r39.py'
MATERIAL_SHA='e70c25fb6530c0e62859e574d10196de21c74c79eb1f3cc5307855da5ba90e68'
MATERIAL_READY=ROOT/'output/unreal/exterior-neighbor-props-20261002-r39-material-readiness/material-source-readiness.json'
MATERIAL_READY_SHA='8c43b8dc4327084da623b4e899a3dbe17661471f2f645814ce931f4f9277a6d5'
def now():return datetime.now(timezone.utc).isoformat()
def report_write(path,row):Path(path).write_text(json.dumps(row,indent=2,sort_keys=True,allow_nan=False)+'\n')
def actors(u):return {a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
def transform_value(v):return [[float(getattr(v.translation,k))for k in 'xyz'],[float(getattr(v.rotation,k))for k in 'xyzw'],[float(getattr(v.scale3d,k))for k in 'xyz']]
def instance_value(c,i):
    value=c.get_instance_transform(i,False)
    if isinstance(value,tuple):require(value[0]is True,'Actual instance getter failed');value=value[1]
    return value

def matrix(c,i):
    value=c.get_editor_property('per_instance_sm_data')[i].get_editor_property('transform')
    return [[float(getattr(getattr(value,p),a))for a in 'xyzw']for p in ('x_plane','y_plane','z_plane','w_plane')]
def exact(a,b,message):
    if isinstance(a,(int,float))and not isinstance(a,bool)and isinstance(b,(int,float))and not isinstance(b,bool):
        require(math.isfinite(a)and math.isfinite(b)and struct.pack('<d',float(a))==struct.pack('<d',float(b)),message)
    elif isinstance(a,list)and isinstance(b,list):
        require(len(a)==len(b),message)
        for x,y in zip(a,b):exact(x,y,message)
    elif isinstance(a,dict)and isinstance(b,dict):
        require(set(a)==set(b),message)
        for k in a:exact(a[k],b[k],message)
    else:require(type(a)==type(b)and a==b,message)
def helpers(bundle):
    require(set(bundle)=={'source','base','binding','nodePoseCalibration'}and set(bundle['base']['readerPacket'])=={'base'}
        and bundle['base']['readerPacket']['base']['report']is bundle['base']['parentReport'],
        'Use the genuine frozen R38 native parent-reader packet')
    h=bundle['base']['native'].helpers(bundle['base']['readerPacket'])
    require(all(k in h for k in ('cleanNative','existing','rural','meshHelper','materials','treeMaterials','moduleOrderWitness')),
        'Frozen-first reader API incomplete')
    return h

def template_contract(bundle):
    row=bundle['base']['savedWitness'][TEMPLATE];comps=row['components']
    require(row['class']=='/Script/BreziTwin.BreziVegetationPatch'and not row['detailDensityScaling']and not row['actorTick']
        and row['transform']==[[0.,0.,0.],[0.,0.,0.,1.],[1.,1.,1.]]and not row['hidden']and len(comps)==1,
        'Only exact rooted source policy template permitted')
    policy=comps[0]
    require(policy['name']=='Instances'and policy['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent'
        and policy['transform']==row['transform']and policy['visible']and not policy['hiddenInGame']and policy['renderFlags']['cast_shadow']
        and policy['overrideMaterials']==[]and policy['tags']==[],'Visible root-local original HISM policy required')
    return row

def cyclic(face): return min(tuple(face[i:]+face[:i])for i in range(3))
def expected_corners(part):
    return [cyclic([tuple(part['nativeVerticesCm'][i]+part['uv0'][i])for i in part['indices'][at:at+3]])for at in range(0,len(part['indices']),3)]
def validate_corner_rows(part,actual):
    require(actual==expected_corners(part),'Complete original ordered native F32 P/UV0/topology/winding differs')
    return c.digest(actual)
def full_part_identity(u,mesh,part):
    require(mesh and mesh.get_class().get_path_name()=='/Script/Engine.StaticMesh' and mesh.get_path_name().startswith(c.PREFIX+'/Geometry/')
      and mesh.get_num_lods()==1 and len(mesh.get_editor_property('static_materials'))==1,'Only fresh own one-LOD/source-slot master permitted')
    desc=mesh.get_static_mesh_description(0);require(desc and desc.get_triangle_count()==mesh.get_num_triangles(0)==part['triangles']and mesh.get_num_sections(0)==1,'Full native original triangle/section census differs')
    rows=[]
    for at in range(part['triangles']):
        t=u.TriangleID(id_value=at);require(int(desc.get_triangle_polygon_group(t).id_value)==0,'Original material section order differs');face=[]
        for corner in range(3):
            vi=desc.get_triangle_vertex_instance(t,corner);p=desc.get_vertex_position(desc.get_vertex_instance_vertex(vi));uv=desc.get_vertex_instance_uv(vi,0)
            face.append(tuple(float(getattr(p,k))for k in 'xyz')+tuple(float(getattr(uv,k))for k in 'xy'))
        rows.append(cyclic(face))
    h=validate_corner_rows(part,rows)
    return {'sourcePart':part['key'],'asset':mesh.get_path_name(),'triangles':part['triangles'],'vertices':part['vertices'],'sections':1,
      'fullOrderedNativeF32PositionUv0TopologyWindingSha256':h,'sourceIdentityFromCountAlone':False,'sourceIdentityFromNameOrLabel':False,
      'nativeNormalTangentReadbackAvailable':False,'originalTangentPresent':False,'sourceNormalAttributeBytesUnchanged':True,
      'nativeGeneratedTangentsActuallyMeasured':False,'originalProviderLodChainPresent':False,'nativeAppearanceAccepted':False}

def temporary_inventory(u,temporary,transform_value):
    rows=[]
    for actor in temporary:
        parent=actor.get_attach_parent_actor();components=[];root=actor.get_editor_property('root_component')
        for component in actor.get_components_by_class(u.ActorComponent):
            row={'path':component.get_path_name(),'name':component.get_name(),'class':component.get_class().get_path_name(),
                'isActorRoot':component==root,'owner':component.get_owner().get_path_name()if component.get_owner()else None}
            if isinstance(component,u.StaticMeshComponent):
                mesh=component.get_editor_property('static_mesh');row['mesh']=mesh.get_path_name()if mesh else None
            components.append(row)
        rows.append({'actor':actor.get_path_name(),'class':actor.get_class().get_path_name(),'label':actor.get_actor_label(),
          'transform':transform_value(actor.get_actor_transform()),'parent':parent.get_path_name()if parent else None,'components':components,
          'primitiveComponents':[p.get_path_name()for p in actor.get_components_by_class(u.PrimitiveComponent)]})
    return {'owner':OWNER,'scope':'observed-new-import-objects-before-any-binding-gate','objects':rows,'labelsUsedForIdentity':False,'geometryIdentityEstablished':False}

def bind_imported_parts(u,model_parts,temporary,inventory):
    require({a.get_path_name()for a in temporary}=={r['actor']for r in inventory['objects']},'Exact temporary import delta required')
    count_to_part={p['triangles']:p for p in model_parts};require(len(count_to_part)==len(model_parts),'Unique triangle count routing required')
    found={};bindings=[];containers=[];paths={a.get_path_name()for a in temporary}
    for actor,row in zip(temporary,inventory['objects']):
        require(row['actor']==actor.get_path_name()and(row['parent']is None or row['parent']in paths),'Observed import parent must belong to owned delta')
        components=actor.get_components_by_class(u.StaticMeshComponent)
        if components:
            require(len(components)==1 and row['primitiveComponents']==[components[0].get_path_name()]and row['class']in('/Script/Engine.StaticMeshActor','/Script/Engine.Actor'),'Exactly one source rendering primitive per imported part required')
            require(actor.get_editor_property('root_component')==components[0]and components[0].get_owner()==actor,'Observed original node pose must be the actual rendering root pose')
            mesh=components[0].get_editor_property('static_mesh');require(mesh and mesh.get_num_triangles(0)in count_to_part,'No unique source part routes this master')
            part=count_to_part[mesh.get_num_triangles(0)];require(part['key']not in found,'Duplicate full original part identity')
            proof=full_part_identity(u,mesh,part)
            # The original nonbaked coil translation is an explicit future runtime gate.
            expected=[g.native_node_translation(part),[0.,0.,0.,1.],[1.,1.,1.]]
            require(row['transform']==expected,'Original unbaked source-node pose differs; preserve checkpoint and repair explicitly')
            found[part['key']]=mesh;bindings.append({**proof,'actualImportedActor':row['actor'],'actualImportedLabel':row['label'],
              'sourceNode':part['nodeName'],'originalSourceMeshName':part['originalSourceMeshName'],
              'sourceNodeTranslationMeters':part['sourceNodeTranslationMeters'],'actualImportedNodePose':row['transform'],
              'wrappedOriginalNodeTransform':actor.get_actor_transform(),'sourceLabelsUsedForIdentity':False})
        else:
            require(row['class']=='/Script/Engine.Actor'and not row['primitiveComponents']and len(row['components'])<=1 and row['parent']is None
              and row['transform']==[[0.,0.,0.],[0.,0.,0.,1.],[1.,1.,1.]]
              and all(v['class']=='/Script/Engine.SceneComponent'for v in row['components']),'Only new identity nonrendering scene container may accompany whole source')
            containers.append(row)
    require(set(found)=={p['key']for p in model_parts}and len({m.get_path_name()for m in found.values()})==len(found)and len(containers)<=1,'Every original part plus at most one nonrendering container required')
    container_paths={p['actor']for p in containers};require(all(r['parent']is None or r['parent']in container_paths for r in inventory['objects']if r not in containers),'Source parts may attach only to owned container')
    return found,bindings,containers

def _import_kernel(u,bundle,materials,h,checkpoint):
    """Future h contract: actors(), fullWitness(), transformValue(), meshHelper.

    Caller must supply frozen importer/policy and future selected full-before
    closure; this kernel never modifies an old actor/component/material.
    """
    require(set(materials)==set(c.MODEL_IDS),'Exactly three own source material objects required')
    ea=u.EditorAssetLibrary;actor_system=u.get_editor_subsystem(u.EditorActorSubsystem);level=u.get_editor_subsystem(u.LevelEditorSubsystem)
    subsystem=h['meshHelper'].static_mesh_subsystem(u);require(subsystem,'Required installed StaticMeshEditor accessor unavailable')
    pipelines=[]
    for source,name in [('GLTFSceneAssets','Assets'),('GLTFMaterials','Materials'),('LevelActors','Level')]:
        target=c.PREFIX+'/Pipeline/'+name;require(not ea.does_asset_exist(target),'Fresh owned import pipeline required')
        obj=ea.duplicate_asset('/Game/Brezi/Pipeline/'+source,target);require(obj,'Cannot duplicate owned pipeline');pipelines.append(obj)
    for k,v in {'combine_static_meshes_behavior':u.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE,'collision':False,'build_nanite':False,'generate_lightmap_u_vs':False}.items():pipelines[0].get_editor_property('mesh_pipeline').set_editor_property(k,v)
    for k,v in {'bake_meshes':False,'bake_pivot_meshes':False,'import_lods':False,'remove_degenerates':False,'recompute_normals':False,'recompute_tangents':True,'use_full_precision_u_vs':True}.items():pipelines[0].get_editor_property('common_meshes_properties').set_editor_property(k,v)
    material_pipeline=pipelines[0].get_editor_property('material_pipeline');material_pipeline.set_editor_property('import_materials',False);material_pipeline.get_editor_property('texture_pipeline').set_editor_property('import_textures',False)
    pipelines[2].set_editor_property('scene_hierarchy_type',u.InterchangeSceneHierarchyType.CREATE_LEVEL_ACTORS)
    params=u.ImportAssetParameters()
    for k,v in {'is_automated':True,'replace_existing':False,'force_show_dialog':False,'override_pipelines':[u.SoftObjectPath(p.get_path_name())for p in pipelines],'import_level':level.get_current_level()}.items():params.set_editor_property(k,v)
    before=h['fullWitness'](u);result={};poses={};observations=[]
    for model_id in c.MODEL_IDS:
        existing=set(h['actors'](u));manager=u.InterchangeManager.get_interchange_manager_scripted()
        imported=manager.import_scene(c.PREFIX+'/Geometry/'+model_id,manager.create_source_data(str(c.checked(bundle['proposal']['models'][model_id]['gltf']))),params)
        temporary=[a for p,a in h['actors'](u).items()if p not in existing]
        inventory=temporary_inventory(u,temporary,h['transformValue']);checkpoint(model_id+'-objects-before-gates',inventory)
        require(imported,'Original whole-model import failed');h['meshHelper'].finish_static_mesh_compilation(u,synchronous=True)
        found,bindings,containers=bind_imported_parts(u,bundle['parts'][model_id],temporary,inventory)
        checkpoint(model_id+'-full-part-identities',{'parts':[{k:v for k,v in r.items()if k!='wrappedOriginalNodeTransform'}for r in bindings],'containers':containers})
        for part in bundle['parts'][model_id]:
            mesh=found[part['key']];target=c.PREFIX+'/Geometry/StaticMeshes/'+model_id+'_part_'+str(part['nodeIndex'])
            if mesh.get_path_name().split('.')[0]!=target:require(ea.rename_asset(mesh.get_path_name().split('.')[0],target),'Cannot canonicalize own original part');mesh=ea.load_asset(target)
            mesh.set_material(0,materials[model_id]);mesh.set_editor_property('has_navigation_data',False)
            settings=subsystem.get_lod_build_settings(mesh,0)
            for k,v in {'use_full_precision_u_vs':True,'generate_lightmap_u_vs':False,'recompute_normals':False,'recompute_tangents':True,'remove_degenerates':False}.items():settings.set_editor_property(k,v)
            subsystem.set_lod_build_settings(mesh,0,settings)
            for k,v in {'BreziGeneratedBy':OWNER,'BreziR39SourceStudySha256':c.SOURCE_SHA,'BreziR39OriginalSourcePart':part['key'],'BreziR39OriginalNodeName':part['nodeName']}.items():ea.set_metadata_tag(mesh,k,v)
            require(ea.save_loaded_asset(mesh,only_if_is_dirty=False),'Cannot save own original part')
            result[part['key']]=mesh;poses[part['key']]=next(r['wrappedOriginalNodeTransform']for r in bindings if r['sourcePart']==part['key'])
        h['meshHelper'].finish_static_mesh_compilation(u,synchronous=True)
        for part in bundle['parts'][model_id]:full_part_identity(u,result[part['key']],part)
        for actor in reversed(temporary):require(actor_system.destroy_actor(actor),'Cannot remove owned import delta')
        require(set(h['actors'](u))==existing and h['fullWitness'](u)==before,'Import left temporary actors or modified original full scene')
        observations.extend({k:v for k,v in r.items()if k!='wrappedOriginalNodeTransform'}for r in bindings)
    require(len(result)==4 and len(poses)==4,'Four source masters, including both hose parts, must remain')
    return result,poses,{'sourcePartProofs':observations,'pipelineAssets':[p.get_path_name()for p in pipelines],
      'fullOriginalMeshTriangles':26601,'hoseOriginalPartsPreserved':2,'originalSourcePoseReadbackActuallyMeasured':True,
      'nativeNormalTangentReadbackAvailable':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False}


def import_geometry(u,bundle,materials,h,directory):
    g.require_native_binding(bundle['binding'])
    api={'actors':actors,'fullWitness':lambda unreal:h['cleanNative'].full_witness(unreal,h),
         'transformValue':transform_value,'meshHelper':h['meshHelper']}
    checkpoint=lambda name,row:write(directory/(name+'.json'),row)
    meshes,poses,proof=_import_kernel(u,bundle['source'],materials,api,checkpoint)
    assets=u.EditorAssetLibrary;canonical={m.get_path_name().split('.')[0]for m in meshes.values()};removed=[]
    for path in assets.list_assets(g.PREFIX+'/Geometry',recursive=True,include_folder=False):
        obj=assets.load_asset(path)
        if obj and obj.get_path_name().split('.')[0]in canonical:continue
        require(obj and obj.get_class().get_name()in ('InterchangeSceneImportAsset','ObjectRedirector'),'Unexpected owned import artifact')
        removed.append(obj.get_path_name());require(assets.delete_asset(path),'Cannot remove own import metadata')
    for asset in proof['pipelineAssets']:
        obj=assets.load_asset(asset);require(obj and assets.save_loaded_asset(obj,only_if_is_dirty=False),'Cannot save own pipeline')
    return meshes,poses,{**proof,'removedOwnImportMetadata':removed}



def material_packet(bundle):
    require(set(bundle)=={'source','base','binding','nodePoseCalibration'},'Exact additive measured-node source packet required')
    return {k:bundle[k]for k in ('source','base','binding')}

def material_module():
    require(sha(MATERIAL)==MATERIAL_SHA,'Immutable original material writer changed')
    result=module('_r39_r2_private_immutable_material_writer',MATERIAL)
    result.binding_guard=lambda:g
    return result

def material_adapter_evidence():
    return {'source':pin(MATERIAL),'targetBindingGuard':pin(ROOT/'scripts/unreal/exterior-neighbor-props-guards-r39-r2.py'),
        'onlyPrivateModuleBindingLoaderChanged':True,'originalSourceAndMaterialGraphKernelsUnchanged':True,
        'originalModulesOrSourceFilesMutated':False,'sourcePacketNarrowedToOriginalThreeKeys':True}

def authored_root(u,row):
    """New-source constructor only: preserve double authored XYZ via wrapped fields."""
    t=u.Transform();p=t.get_editor_property('translation')
    for axis,value in zip('xyz',row['positionCm']):p.set_editor_property(axis,value)
    t.set_editor_property('translation',p)
    angle=math.radians(row['yawDegrees'])/2.;q=t.get_editor_property('rotation')
    wanted=[0.,0.,math.sin(angle),math.cos(angle)]
    for axis,value in zip('xyzw',wanted):q.set_editor_property(axis,value)
    t.set_editor_property('rotation',q);scale=t.get_editor_property('scale3d')
    for axis in 'xyz':scale.set_editor_property(axis,row['uniformScale'])
    t.set_editor_property('scale3d',scale)
    exact(transform_value(t),[row['positionCm'],wanted,[row['uniformScale']]*3],'Authored double XYZ/yaw/uniform scale constructor differs')
    return t


def validate_intended_pose(row,part,root,node,composed,independent):
    angle=math.radians(row['yawDegrees'])/2.
    exact(root,[row['positionCm'],[0.,0.,math.sin(angle),math.cos(angle)],[row['uniformScale']]*3],
        'Measured assembly root differs from exact six authored physical inputs')
    exact(node,[g.native_node_translation(part),[0.,0.,0.,1.],[1.,1.,1.]],
        'Original whole-part nonbaked node pose differs')
    exact(composed,independent,'Actual composed original-node pose differs from independent root/point transform')
    exact(composed[1:],root[1:],'Source identity node must preserve declared root rotation/scale')
    return True


def measure(u,bundle,poses):
    source=bundle['source'];values={};proof={}
    for model,parts in source['parts'].items():
        for part in parts:
            key=part['key'];rows=[r for r in source['proposal']['placements']if r['modelId']==model]
            transient=u.new_object(u.HierarchicalInstancedStaticMeshComponent)
            require(transient and transient.get_path_name().startswith('/Engine/Transient.')
                and transient.get_editor_property('static_mesh')is None,'Unowned meshless transient only')
            inputs=[];roots=[];nodes=[];independent=[];desired=[]
            for row in rows:
                root=authored_root(u,row);node=poses[key];node_value=transform_value(node)
                composed=u.MathLibrary.compose_transforms(node,root)
                location=u.MathLibrary.transform_location(root,node.translation)
                expected=[[float(getattr(location,k))for k in 'xyz'],transform_value(root)[1],transform_value(root)[2]]
                value=transform_value(composed)
                validate_intended_pose(row,part,transform_value(root),node_value,value,expected)
                require(transient.add_instance(composed,False)==len(inputs),'Ordered transient composition measurement failed')
                inputs.append(value);roots.append(transform_value(root));nodes.append(node_value);independent.append(expected);desired.append(composed)
            recovered=[transform_value(instance_value(transient,i))for i in range(len(rows))]
            matrices=[matrix(transient,i)for i in range(len(rows))]
            for value,got,stored in zip(inputs,recovered,matrices):
                exact(got[0],value[0],'Transient recovered assembly position changed')
                exact(stored[3][:3],value[0],'Stored composed translation changed')
            proof[key]={'part':key,'modelId':model,'nodeIndex':part['nodeIndex'],'assemblyRootIds':[r['id']for r in rows],
                'authoredAssemblyInputs':[{k:r[k]for k in ('id','modelId','positionCm','yawDegrees','uniformScale')}for r in rows],
                'assemblyInputValues':roots,'originalImportedNodeValues':nodes,'independentRootTransformPointValues':independent,
                'composedInputValues':inputs,'recoveredValues':recovered,'storedMatrices':matrices,
                'actualMeshlessTransientMeasured':True,'originalWholeSourceNodeTransformComposed':True,
                'intendedSixAuthoredAssembliesIndependentlyCompared':True,'hostVsNativeLibmBitEquivalenceClaimed':False,
                'actualSurfaceCollisionOrPhysicalContactVerified':False,'sourceOnlyContactAndClearanceProposal':True}
            transient.clear_instances();require(transient.get_instance_count()==0,'Transient members remain');values[key]=desired
    validate_measurement_receipt(bundle,proof)
    return values,proof


def validate_measurement_receipt(bundle,proof):
    source=bundle['source'];parts={p['key']:p for rows in source['parts'].values()for p in rows};require(set(proof)==set(parts),'Every complete original source part measured')
    for key,m in proof.items():
        part=parts[key];rows=[r for r in source['proposal']['placements']if r['modelId']==part['modelId']]
        require(m['assemblyRootIds']==[r['id']for r in rows]and m['actualMeshlessTransientMeasured']is True
            and m['originalWholeSourceNodeTransformComposed']is True and m['intendedSixAuthoredAssembliesIndependentlyCompared']is True,
            'Exact ordered assemblies and original-node composition receipt required')
        required=('authoredAssemblyInputs','assemblyInputValues','originalImportedNodeValues','independentRootTransformPointValues',
                  'composedInputValues','recoveredValues','storedMatrices')
        require(all(len(m[k])==len(rows)for k in required),'Every intended/measured part member must be bound')
        for i,row in enumerate(rows):
            require(m['authoredAssemblyInputs'][i]=={k:row[k]for k in ('id','modelId','positionCm','yawDegrees','uniformScale')},'Source authored placement identity differs')
            validate_intended_pose(row,part,m['assemblyInputValues'][i],m['originalImportedNodeValues'][i],m['composedInputValues'][i],m['independentRootTransformPointValues'][i])
            actual=m['recoveredValues'][i];stored=m['storedMatrices'][i]
            exact(actual[0],m['composedInputValues'][i][0],'Recorded recovered placement differs')
            require(len(stored)==4 and all(len(r)==4 and all(math.isfinite(x)for x in r)for r in stored)
                and all(stored[j][3]==0 for j in range(3))and stored[3][3]==1,'Finite affine composed native matrix required')
            exact(stored[3][:3],actual[0],'Recorded matrix position differs')
    require(sum(len(v['assemblyRootIds'])for v in proof.values())==8
        and len(set(i for v in proof.values()for i in v['assemblyRootIds']))==6,'Eight parts must represent six whole assemblies')
    return True


def relocate(value,old,new):
    if isinstance(value,str):return new+value[len(old):]if value==old or value.startswith(old+'.')else value
    if isinstance(value,list):return [relocate(v,old,new)for v in value]
    if isinstance(value,dict):return {k:relocate(v,old,new)for k,v in value.items()}
    return value


def added_expected(bundle,key,path,mesh,material,measurement):
    row=relocate(copy.deepcopy(template_contract(bundle)),TEMPLATE,path)
    row['label']='R39_'+key.replace(':','_');row['tags']=sorted(['BreziGenerated',g.TAG]);row['actorTick']=False;row['detailDensityScaling']=False
    component=row['components'][0];component['mesh']=mesh;component['materials']=[material];component['overrideMaterials']=[]
    component['instanceCount']=len(measurement['assemblyRootIds']);component['orderedInstanceTransformsSha256']=digest(measurement['recoveredValues'])
    return row


def apply_new(u,bundle,h,values,measurements,meshes,materials):
    template=template_contract(bundle);system=u.get_editor_subsystem(u.EditorActorSubsystem);new={};added={};parts={p['key']:p for rows in bundle['source']['parts'].values()for p in rows}
    require(not any(a.actor_has_tag(g.TAG)for a in actors(u).values()),'Fresh owned actor tag required')
    for key,part in parts.items():
        a=system.spawn_actor_from_class(u.load_class(None,'/Script/BreziTwin.BreziVegetationPatch'),u.Vector(0,0,0),u.Rotator());require(a,'Cannot spawn own props group')
        a.tags=[u.Name('BreziGenerated'),u.Name(g.TAG)];a.set_actor_label('R39_'+key.replace(':','_'));a.set_folder_path('Brezi/NeighborProps20261002R39');a.set_actor_tick_enabled(False)
        component=a.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
        require(component and a.get_editor_property('root_component')==component and component.get_owner()==a,'Owned root HISM predicate failed')
        h['rural'].new_component_policy(u,component);require(component.set_static_mesh(meshes[key]),'Cannot bind original source part master')
        require(a.set_detail_density_scaling(False),'Cannot disable unmanaged detail scaling for authored props')
        policy=template['components'][0]
        for section in ('renderFlags','passFlags','drawPolicy','additionalRenderFlags'):
            for prop,value in policy[section].items():
                if prop=='cached_max_draw_distance':require(component.get_editor_property(prop)==value,'Derived new draw-distance cache differs')
                else:component.set_editor_property(prop,value)
        component.set_visibility(policy['visible'],False);component.set_hidden_in_game(policy['hiddenInGame'],False)
        component.set_cull_distances(*policy['instanceCullCm'])
        require(list(component.add_instances(values[key],True,False,False))==list(range(len(values[key]))),'Only unique measured complete part poses may add')
        a.synchronize_instance_bounds();path=a.get_path_name();new[key]=path
        added[path]=added_expected(bundle,key,path,meshes[key].get_path_name(),materials[part['modelId']].get_path_name(),measurements[key])
    return new,added


def verify_new(u,bundle,h,new,measurements,meshes,materials):
    validate_measurement_receipt(bundle,measurements);scene=actors(u)
    require({p for p,a in scene.items()if a.actor_has_tag(g.TAG)}==set(new.values()),'Owned actor tag delta differs')
    parts={p['key']:p for rows in bundle['source']['parts'].values()for p in rows}
    for key,path in new.items():
        a=scene[path];component=a.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent);m=measurements[key]
        require(a.get_editor_property('root_component')==component and component.get_owner()==a
            and component.get_instance_count()==len(m['assemblyRootIds'])and component.get_editor_property('static_mesh').get_path_name()==meshes[key].get_path_name()
            and component.get_num_materials()==1 and component.get_material(0).get_path_name()==materials[parts[key]['modelId']].get_path_name(),
            'Saved complete original part/master/material binding differs')
        exact([transform_value(instance_value(component,i))for i in range(component.get_instance_count())],m['recoveredValues'],'Saved measured original-node composed Transform differs')
        exact([matrix(component,i)for i in range(component.get_instance_count())],m['storedMatrices'],'Saved measured composed FMatrix differs')


def old_material_witness(u,bundle,h,directory):
    require(not directory.exists(),'Fresh old-material diagnostics required');directory.mkdir();result={}
    for index,(asset,row)in enumerate(sorted(bundle['base']['materialRecords'].items())):
        material=u.EditorAssetLibrary.load_asset(asset);require(isinstance(material,u.Material),'Protected original material unavailable')
        graph=bundle['base']['native'].graph_snapshot(u,material,h,row['route']);aux=h['materials'].aux_snapshot(u,material)
        usage={'instancedStaticMeshes':bool(u.MaterialEditingLibrary.has_material_usage(material,h['existing'].native_enum(u.MaterialUsage,'INSTANCEDSTATICMESHES'))),
               'nanite':bool(u.MaterialEditingLibrary.has_material_usage(material,u.MaterialUsage.MATUSAGE_NANITE))}
        got={'asset':asset,'reader':row['route'],'graph':graph,'graphSha256':digest(graph),'aux':aux,'usage':usage,
             'usagePreviouslyRecorded':row['usageRecordedInSelectedNativeReceipt']}
        if 'metadata'in row:got['metadata']={k:u.EditorAssetLibrary.get_metadata_tag(material,k)for k in row['metadata']}
        write(directory/('graph-'+str(index).zfill(3)+'.json'),got)
        require(graph==row['graph']and aux==row['aux'],'Protected full original graph/aux changed: '+asset)
        if row['usageRecordedInSelectedNativeReceipt']:require(usage==row['usage'],'Protected old64 saved usage changed: '+asset)
        if 'metadata'in row:require(got['metadata']==row['metadata'],'Protected R38 graph metadata changed')
        result[asset]=got
    require(len(result)==66,'All66 original graph records required');return result


def old_texture_witness(u,bundle,h):
    result={}
    for asset,row in bundle['base']['textureRecords'].items():
        texture=u.EditorAssetLibrary.load_asset(asset);require(isinstance(texture,u.Texture2D),'Protected original Texture2D unavailable')
        got=h['materials'].texture_snapshot(u,texture)
        require(got==row,
            'Original97 visible24 settings/dimensions changed: '+asset)
        result[asset]=got
    return result


def original_raw(u,bundle,witness):
    got=bundle['base']['native'].raw_instance_controls(u,witness);wanted=bundle['base']['rawControls']
    originals={k:v for k,v in got.items()if k in wanted}
    exact(originals,wanted,'All2325 original wrapped matrix/mainseed/custom/order controls must remain exact')
    require(len(originals)==2325 and sum(v['instances']for v in originals.values())==678197,'Entire old instance census must be retained')
    return originals


def primary_api():
    engine=Path('/Users/Shared/Epic Games/UE_5.8/Engine');paths={
        'doubleTransforms':engine/'Source/Runtime/Engine/Classes/Kismet/KismetMathLibrary.h',
        'rootActor':engine/'Source/Runtime/Engine/Classes/GameFramework/Actor.h',
        'wrappedInstanceStorage':engine/'Source/Runtime/Engine/Classes/Components/InstancedStaticMeshComponent.h',
        'originalGlTFBasis':engine/'Plugins/Interchange/Runtime/Source/Parsers/GLTFCore/Private/GLTF/ConversionUtilities.h',
        'originalGlTFAttributes':engine/'Plugins/Interchange/Runtime/Source/Parsers/GLTFCore/Private/GLTF/GLTFMesh.cpp',
        'originalGlTFIndices':engine/'Plugins/Interchange/Runtime/Source/Parsers/GLTFCore/Private/GLTFMeshFactory.cpp',
        'ownedMeshPipeline':engine/'Plugins/Interchange/Runtime/Source/Pipelines/Public/InterchangeGenericAssetsPipeline.h',
        'materialUsageAndCompile':engine/'Source/Editor/MaterialEditor/Public/MaterialEditingLibrary.h'}
    require('ComposeTransforms'in paths['doubleTransforms'].read_text()and 'TransformLocation'in paths['doubleTransforms'].read_text()
        and 'GetAttachParentActor'in paths['rootActor'].read_text()and 'PerInstanceSMData'in paths['wrappedInstanceStorage'].read_text()
        and 'Vec.X, Vec.Z, Vec.Y'in paths['originalGlTFBasis'].read_text()
        and 'Indices[(TriangleIndex * 3 + Corner)]'in paths['originalGlTFIndices'].read_text(),
        'Installed original nonmirrored source/transform route changed')
    return {k:pin(v)for k,v in paths.items()}


def validate_plan(bundle=None):
    if bundle is None:bundle=g.load_contract()
    plan=read(g.PLAN)
    require(plan['schema']==g.SCHEMA and plan['schemaVersion']==2 and plan['owner']=='scripts/unreal/exterior-neighbor-props-native-study-r39-r2.py'
        and plan['nativeOwner']==OWNER and plan['status']=='image-selected-whole-original-neighbor-props-source-ready-native-r2-pending'
        and plan['binding']==bundle['binding']and plan['expectedCounts']==g.COUNTS
        and plan['templateActor']==TEMPLATE and plan['templateActorWitness']==template_contract(bundle)
        and plan['repairSchema']==g.REPAIR_SCHEMA and plan['repairEvidence']==g.repair_evidence()and plan['nodePoseCalibration']==bundle['nodePoseCalibration']
        and plan['sourceProposal']==bundle['source']['proposalPin']and plan['nativeExecuted']is False and plan['gpuExecuted']is False,
        'Exact bound original source/new21-package plan required')
    require(plan['expectedNewPackageAssets']==g.expected_new_packages(bundle['source'])and plan['primaryApi']==primary_api(),
        'Declared own packages/installed APIs changed')
    require(sha(MATERIAL)==MATERIAL_SHA and sha(MATERIAL_READY)==MATERIAL_READY_SHA,
        'Frozen original material writer/readiness changed')
    require(all(sha(p)==value for p,value in plan['inputFiles'].items()),'Frozen selected source closure changed')
    return plan,bundle


def preflight(directory,bundle=None):
    directory=Path(directory).resolve();require(directory==g.STUDY/'source-preflight'and not directory.exists(),'One fresh native preflight only')
    plan,bundle=validate_plan(bundle);h=helpers(bundle)
    directory.mkdir();stream=io.StringIO();suite=unittest.TestSuite()
    tests=module('_r39_r2_changed_calibration_contracts',ROOT/'scripts/unreal/test_exterior_neighbor_props_native_r39_r2.py')
    tests.CalibrationContracts.BUNDLE=bundle
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(tests.CalibrationContracts))
    guards=module('_r39_r2_guard_calibration_contracts',ROOT/'scripts/unreal/test_exterior_neighbor_props_guards_r39_r2.py')
    guards.CalibrationContracts.BUNDLE=bundle
    suite.addTests(unittest.defaultTestLoader.loadTestsFromTestCase(guards.CalibrationContracts))
    result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite);log=directory/'cpu-guards.log';log.write_text(stream.getvalue())
    require(result.wasSuccessful()and result.testsRun==TEST_COUNT,'Meaningful changed-contract suite failed: '+str(result.testsRun))
    files={**plan['inputFiles'],str(g.PLAN):sha(g.PLAN)}
    require(all(sha(p)==value for p,value in files.items()),'Consumed source bytes changed during mandatory tests')
    row={'schema':g.SCHEMA,'schemaVersion':2,'owner':OWNER,'status':'image-selected-whole-original-neighbor-props-preflight-validated-native-r2-pending',
        'createdAt':now(),'selectedPlan':pin(g.PLAN),'binding':bundle['binding'],'repairSchema':g.REPAIR_SCHEMA,'repairEvidence':g.repair_evidence(),'nodePoseCalibration':bundle['nodePoseCalibration'],'expectedCounts':g.COUNTS,
        'inputFiles':files,'moduleOrderWitness':h['moduleOrderWitness'],'primaryApi':primary_api(),
        'tests':{'exitCode':0,'testCount':TEST_COUNT,'log':pin(log),'sources':[pin(ROOT/'scripts/unreal'/v)for v in (
            'test_exterior_neighbor_props_native_r39_r2.py','test_exterior_neighbor_props_guards_r39_r2.py')],
            'execution':'one in-process measured-node calibration/binding suite; frozen prior30 cases are inherited executed evidence',
            'nativeApisActuallyExercised':False},'nativeExecuted':False,'gpuExecuted':False,'nativeAppearanceAccepted':False,
        'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,'activeOutputPromoted':False}
    write(directory/'source-preflight.json',row)
    print(json.dumps({'preflight':pin(directory/'source-preflight.json'),'testCount':TEST_COUNT,'nativeExecuted':False}),flush=True)
    return row


def validate_preflight(path,plan,bundle):
    require(Path(path).resolve()==g.STUDY/'source-preflight/source-preflight.json','Exact own preflight path required')
    pf=read(path)
    require(pf['schema']==g.SCHEMA and pf['schemaVersion']==2 and pf['owner']==OWNER
        and pf['status']=='image-selected-whole-original-neighbor-props-preflight-validated-native-r2-pending'
        and pf['selectedPlan']==pin(g.PLAN)and pf['binding']==bundle['binding']and pf['expectedCounts']==g.COUNTS
        and pf['repairSchema']==g.REPAIR_SCHEMA and pf['repairEvidence']==g.repair_evidence()and pf['nodePoseCalibration']==bundle['nodePoseCalibration']
        and pf['inputFiles']=={**plan['inputFiles'],str(g.PLAN):sha(g.PLAN)}and pf['tests']['exitCode']==0
        and pf['tests']['testCount']==TEST_COUNT and pf['primaryApi']==primary_api()
        and pf['nativeExecuted']is False and pf['gpuExecuted']is False,'Exact executed source/preflight closure required')
    for row in pf['tests']['sources']+[pf['tests']['log']]:g.checked(row)
    require(all(sha(p)==v for p,v in pf['inputFiles'].items()),'Consumed source bytes changed')
    return pf


def main():
    import unreal as u
    require(Path(os.environ['BREZI_NEIGHBOR_PROPS_OUTPUT']).resolve()==g.CANDIDATE
        and Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve()==g.PROJECT,'Exact owned fresh R39 project only')
    require(sha(g.PLAN)==os.environ['BREZI_NEIGHBOR_PROPS_PLAN_SHA256'],'Exact selected plan SHA required')
    path=Path(os.environ['BREZI_NEIGHBOR_PROPS_PREFLIGHT']).resolve()
    require(sha(path)==os.environ['BREZI_NEIGHBOR_PROPS_PREFLIGHT_SHA256']and not(g.CANDIDATE/REPORT).exists(),'Exact executed preflight/fresh report only')
    plan,bundle=validate_plan();pf=validate_preflight(path,plan,bundle);h=helpers(bundle)
    require(h['moduleOrderWitness']==pf['moduleOrderWitness'],'Frozen-first module order differs')
    require(sha(MATERIAL)==MATERIAL_SHA,'Frozen three-material helper changed');maps=material_module();maps.preflight_enums(u)
    directory=g.CANDIDATE/'neighbor-props-checkpoint';require(not directory.exists(),'Fresh observed checkpoint required');directory.mkdir()
    base=bundle['base'];report={'schema':g.SCHEMA,'schemaVersion':2,'owner':OWNER,'status':'running','startedAt':now(),
        'nativeProcessId':os.getpid(),'project':str(g.PROJECT),'output':str(g.CANDIDATE),'selectedPlan':pin(g.PLAN),'sourcePreflight':pin(path),
        'sourceProposal':bundle['source']['proposalPin'],'binding':bundle['binding'],'baseNativeReport':base['reportPin'],
        'baseNativeProcess':base['processPin'],'baseCurrentByteAudit':base['auditPin'],'selectedRootImageDecision':pin(g.IMAGE_DECISION),
        'projectClone':pin(g.CLONE),'baseContentInventory':base['report']['afterContentInventory'],'protectedProjectProof':base['report']['protectedProjectProof'],
        'repairSchema':g.REPAIR_SCHEMA,'repairEvidence':g.repair_evidence(),'nodePoseCalibration':bundle['nodePoseCalibration'],
        'privateMaterialBindingAdapter':material_adapter_evidence(),'inputFiles':pf['inputFiles'],'nativeApplied':False,'savedMapUnloadedReloaded':False,'sourceInputsUnchanged':False,
        'activeDesign':{'variant':'C','heatingLayout':'B','livingLayout':'B'},'setbacksMm':{'street':3000,'east':3000},
        'sourceOriginalGeometryAndPhotoPixelsEdited':False,'originalActorTransformInstanceOrMaterialSettersCalled':False,
        'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,'shippingVerified':False,
        'packageVerified':False,'activeOutputPromoted':False,'nativeNormalTangentReadbackAvailable':False,'nativeGpuPixelFormatVerified':False,
        'allSixAssemblyActorsIndividuallyVisibleVerified':False,'actualNativeSurfaceContactCollisionOrSurveyVerified':False}
    report_write(g.CANDIDATE/REPORT,report)
    try:
        own=g.PROJECT/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib';original=base['project']/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib'
        require(sha(own)==sha(original)and own.stat().st_ino!=original.stat().st_ino,'Original module must remain byte-identical and independent')
        levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot load own candidate map')
        before=h['cleanNative'].full_witness(u,h);require(before==base['savedWitness'],'Entire selected original5364 actor witness differs')
        raw=original_raw(u,bundle,before);old_graphs=old_material_witness(u,bundle,h,directory/'graphs-before');old_textures=old_texture_witness(u,bundle,h)
        for name,value in [('before-actors',before),('raw-controls-before',raw),('old-materials-before',old_graphs),('old-textures-before',old_textures)]:write(directory/(name+'.json'),value)
        reader=lambda unreal,material:h['existing'].graph_snapshot(unreal,material)
        materials,built=maps.build_materials(u,material_packet(bundle),bundle['binding'],reader)
        require(set(materials)==set(g.MODEL_IDS)and len(built['newPackageAssets'])==14,'Exact original three graphs/11 maps required')
        for asset in built['newPackageAssets']:
            obj=u.EditorAssetLibrary.load_asset(asset);require(obj and u.EditorAssetLibrary.save_loaded_asset(obj,only_if_is_dirty=False),'Cannot save own original PBR object')
        meshes,poses,import_proof=import_geometry(u,bundle,materials,h,directory)
        require(h['cleanNative'].full_witness(u,h)==before,'Owned imports changed an original actor')
        values,measurements=measure(u,bundle,poses)
        write(directory/'source-native-measurements.json',measurements)
        require(h['cleanNative'].full_witness(u,h)==before,'Meshless intended-pose measurements changed original scene')
        new,added=apply_new(u,bundle,h,values,measurements,meshes,materials);expected=g.expected_counterfactual(before,added)
        verify_new(u,bundle,h,new,measurements,meshes,materials)
        require(h['cleanNative'].full_witness(u,h)==expected,'Complete four-source-template props counterfactual differs before save')
        write(directory/'expected-actors.json',expected)
        require(levels.save_current_level(),'Cannot save whole-original props map')
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False)and levels.load_level(MAP),'Cannot unload/reload saved props map')
        materials_saved=maps.verify_materials(u,material_packet(bundle),bundle['binding'],built,reader)
        meshes_saved={k:u.EditorAssetLibrary.load_asset(m.get_path_name())for k,m in meshes.items()}
        verify_new(u,bundle,h,new,measurements,meshes_saved,materials_saved)
        saved=h['cleanNative'].full_witness(u,h);require(saved==expected,'Saved complete original5364+4 counterfactual differs')
        raw_saved=original_raw(u,bundle,saved);exact(raw_saved,raw,'Original2325 raw controls changed across save/reload')
        graph_saved=old_material_witness(u,bundle,h,directory/'graphs-saved');tex_saved=old_texture_witness(u,bundle,h)
        require(graph_saved==old_graphs and tex_saved==old_textures,'Original66 graphs/usage or97 visible texture snapshots changed')
        geometry={p['key']:full_part_identity(u,meshes_saved[p['key']],p)for rows in bundle['source']['parts'].values()for p in rows}
        require(sum(v['triangles']for v in geometry.values())==26601,'Full original26601 native triangle proof required')
        assets=g.expected_new_packages(bundle['source']);content=g.validate_clone(bundle,after=True);delta=g.validate_content_delta(base['content'],content,assets)
        hisms=[v for row in saved.values()for v in row['components']if v['class']=='/Script/Engine.HierarchicalInstancedStaticMeshComponent']
        require((len(saved),len(hisms),sum(v['instanceCount']for v in hisms))==(5368,2329,678205),'Saved complete future props census differs')
        for name,value in [('saved-actors',saved),('raw-controls-saved',raw_saved),('old-materials-saved',graph_saved),('old-textures-saved',tex_saved),
                           ('after-content',content),('new-materials',built),('geometry-readback',geometry),('import-readback',import_proof)]:write(directory/(name+'.json'),value)
        require(all(sha(p)==v for p,v in pf['inputFiles'].items()),'Frozen consumed source bytes changed during native')
        report.update(status=STATUS,completedAt=now(),nativeApplied=True,savedMapUnloadedReloaded=True,sourceInputsUnchanged=True,
            moduleOrderWitness=h['moduleOrderWitness'],nativeModuleWitness={'source':str(original),'destination':str(own),'sha256':sha(own),
                'bytes':own.stat().st_size,'independentInodes':True},beforeActorWitness=pin(directory/'before-actors.json'),
            expectedActorWitness=pin(directory/'expected-actors.json'),savedActorWitness=pin(directory/'saved-actors.json'),
            beforeActorWitnessSha256=digest(before),expectedActorWitnessSha256=digest(expected),savedActorWitnessSha256=digest(saved),
            rawInstanceControlsBefore=pin(directory/'raw-controls-before.json'),rawInstanceControlsSaved=pin(directory/'raw-controls-saved.json'),
            originalMaterialWitnessBefore=pin(directory/'old-materials-before.json'),originalMaterialWitnessSaved=pin(directory/'old-materials-saved.json'),
            originalTextureWitnessBefore=pin(directory/'old-textures-before.json'),originalTextureWitnessSaved=pin(directory/'old-textures-saved.json'),
            materialGraphDiagnosticFiles={phase:[pin(p)for p in sorted((directory/('graphs-'+phase)).glob('graph-*.json'))]for phase in ('before','saved')},
            newMaterialReport=pin(directory/'new-materials.json'),materialReport=built,newSourceNativeMeasurements=pin(directory/'source-native-measurements.json'),
            nativeGeometryReadback=geometry,nativeGeometryReadbackReceipt=pin(directory/'geometry-readback.json'),importReadback=pin(directory/'import-readback.json'),
            newOwnedGroups={key:{'actor':actor,'part':key,'mesh':meshes_saved[key].get_path_name(),'material':materials_saved[measurements[key]['modelId']].get_path_name(),
                'instances':len(measurements[key]['assemblyRootIds']),'assemblyRootIds':measurements[key]['assemblyRootIds']}for key,actor in new.items()},
            afterContentInventory=pin(directory/'after-content.json'),assetDelta=delta,newPackages=assets,actualCounts=g.COUNTS,
            allOriginal5364ActorsAnd2325RawControlsExact=True,allOriginal66MaterialGraphsAuxObservedUsageExact=True,
            allOriginal97TextureSettingsAndSourceBytesExact=True,allFourOriginalPartsFullNativeIdentityVerified=True,
            allSixIntendedAssembliesAndOriginalHoseNodePosesIndependentlyCompared=True,
            allEightMeasuredPosesExactBeforeAppliedAndSaved=True,oldAdditionalRandomSeedRangesPreservationClaimed=False,
            sourceNormalsPreservedAndDerivedUvTangentsRequested=True,nativeTangentsNumericallyVerified=False)
        report_write(g.CANDIDATE/REPORT,report);print(json.dumps({'report':pin(g.CANDIDATE/REPORT),'status':STATUS}),flush=True)
    except Exception as error:
        report.update(status='failed',completedAt=now(),error=str(error));report_write(g.CANDIDATE/REPORT,report);raise


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--preflight',type=Path);args=parser.parse_args()
    if args.preflight:preflight(args.preflight)
    else:main()
