"""UNBOUND R39 original-model import kernels. No map application entry exists.

Counts route candidates; complete ordered F32 P/UV0/section/winding establishes
four source part identities. Both hose parts and its source coil pose are kept.
Old-scene closure and final assembly actor ownership await root image selection.
"""
import importlib.util
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-neighbor-props-native-r39-draft.py'
def module(name,p):
    spec=importlib.util.spec_from_file_location(name,p);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
c=module('_r39_native_contract',ROOT/'scripts/unreal/exterior-neighbor-props-contract-r39-draft.py')
require=c.require

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
        parent=actor.get_attach_parent_actor();components=[]
        for component in actor.get_components_by_class(u.ActorComponent):
            row={'path':component.get_path_name(),'name':component.get_name(),'class':component.get_class().get_path_name()}
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
            mesh=components[0].get_editor_property('static_mesh');require(mesh and mesh.get_num_triangles(0)in count_to_part,'No unique source part routes this master')
            part=count_to_part[mesh.get_num_triangles(0)];require(part['key']not in found,'Duplicate full original part identity')
            proof=full_part_identity(u,mesh,part)
            # The original nonbaked coil translation is an explicit future runtime gate.
            expected=[part['proposedNativeNodeTranslationCm'],[0.,0.,0.,1.],[1.,1.,1.]]
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

def import_geometry(u,bundle,binding,materials,h,checkpoint):
    c.require_bound(binding);return _import_kernel(u,bundle,materials,h,checkpoint)
def apply_scene(*args,**kwargs):
    c.require_bound(kwargs.get('binding'))

def main():
    c.require_bound()
if __name__=='__main__':main()
