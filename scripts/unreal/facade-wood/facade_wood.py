"""Exact twelve-source facade finish; explicit import hook, never starts Unreal.

Destination on adoption: scripts/unreal/facade-wood/. Texture/species is an
illustrative Hinoki photograph for source-named larch, not an as-built survey.
"""
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'lib/twin-site.ts').is_file())
HERE = Path(__file__).resolve().parent
OWNER = 'scripts/unreal/facade-wood/facade_wood.py'
PREFIX = '/Game/Brezi/Materials/FacadePhotoWood'
RECIPE_TAG = 'BreziFacadeRecipe'
SLOTS = {'DOM_00061':'MAT_0011', 'DOM_00062':'MAT_0011', 'DOM_00063':'MAT_0011',
         'DOM_00126':'MAT_0012', 'DOM_00147':'MAT_0019', 'DOM_00149':'MAT_0020',
         'DOM_00151':'MAT_0021', 'DOM_00157':'MAT_0022', 'DOM_00158':'MAT_0023',
         'DOM_00159':'MAT_0024', 'DOM_00164':'MAT_0025', 'DOM_00165':'MAT_0026'}
SCENE_SHA = '61ba228f4b72a5ee5fc754e60e112ff70d03605f8cf56fec97bccc3519b8863b'
OBJ_SHA = 'a42e9eb169d929bc67056ad21bf3885e3f1a32838f15c328cb98bacd008fa455'


def require(ok, message):
    if not ok: raise RuntimeError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                    separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def same_saved_values(a, b):
    # The Node host rewrites JSON numbers (0.0 becomes 0); Unreal also returns
    # tuples that JSON stores as arrays. Compare exact values, without rounding.
    return json.loads(json.dumps(a, allow_nan=False)) == json.loads(json.dumps(b, allow_nan=False))


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def shader(): return module('brezi_facade_shading', HERE/'shading.py')


def verify_inputs(scene, geometry):
    geometry = Path(geometry)
    reference = json.loads((HERE/'reference.json').read_text())
    require(reference['sceneSha256'] == SCENE_SHA and reference['objSha256'] == OBJ_SHA,
            'Facade reference geometry changed')
    require(sha(geometry/'scene.json') == SCENE_SHA and sha(geometry/'dom-mm.obj') == OBJ_SHA,
            'Facade canonical geometry changed; review source intent before reauthoring')
    require(digest(scene) == digest(json.loads((geometry/'scene.json').read_text())), 'Facade supplied scene differs')
    records = {r['id']: r for r in scene['objects']}
    require(len(records) == len(scene['objects']), 'Duplicate source IDs')
    require({i:r['slot'] for i,r in reference['sourceObjects'].items()} == SLOTS, 'Facade target set changed')
    for id_,slot in SLOTS.items():
        row = records[id_]
        require(row['enabled'] and row['instances'] == 1 and row['materialSlots'] == [slot]
                and digest(row) == reference['sourceObjects'][id_]['recordSha256'], 'Facade source record differs: '+id_)
    slot_users = {r['id'] for r in records.values() if set(r['materialSlots']) & set(SLOTS.values())}
    require(slot_users == set(SLOTS) and records['DOM_01876']['materialSlots'] == ['MAT_0111'],
            'Facade material scope leaked to another source object')
    for relative, expected in {**reference['evidence'], **reference['sourceIntentFiles']}.items():
        require(sha(ROOT/relative) == expected, 'Facade source/photo evidence changed: '+relative)
    for role,spec in reference['maps'].items():
        path = ROOT/spec['path']
        require(path.stat().st_size == spec['bytes'] and sha(path) == spec['sha256'], 'Facade 4K map changed: '+role)
    s = shader()
    require(reference['periodCm'] == s.PERIOD_CM and reference['pitchMm'] == s.PITCH_CM*10
            and reference['jointMm'] == s.JOINT_CM*10 and reference['jointShade'] == s.JOINT_SHADE
            and reference['normalStrength'] == s.NORMAL_STRENGTH
            and reference['photoBandStarts'] == list(s.BANDS), 'Facade shader/reference scalar policy differs')
    paths = [HERE/'facade_wood.py', HERE/'shading.py', HERE/'reference.json', ROOT/'scripts/unreal/tv-oak/tv_oak.py']
    pipeline = {str(p.relative_to(ROOT)):sha(p) for p in paths}
    pipeline.update(reference['evidence']); pipeline.update(reference['sourceIntentFiles'])
    pipeline.update({m['path']:m['sha256'] for m in reference['maps'].values()})
    recipe = {'reference':reference, 'pipelineFiles':pipeline}
    return {'recipeSha256':digest(recipe), 'recipe':recipe, 'pipelineFiles':pipeline,
            'candidate':{'maps':reference['maps']}, 'reference':reference, 'records':{i:records[i] for i in SLOTS}}


def read_source(obj_path, contract):
    positions,uvs,faces = [],[],{i:[] for i in SLOTS}
    current = slot = None
    for line in Path(obj_path).read_text().splitlines():
        a = line.split()
        if not a: continue
        if a[0] == 'v': positions.append(tuple(map(float,a[1:4])))
        elif a[0] == 'vt': uvs.append(tuple(map(float,a[1:3])))
        elif a[0] == 'o': current = a[1]
        elif a[0] == 'usemtl': slot = a[1]
        elif a[0] == 'f' and current in faces:
            require(len(a) == 4 and slot == SLOTS[current], 'Facade OBJ topology/slot changed')
            refs = [tuple(map(int,v.split('/')[:2])) for v in a[1:]]
            require(all(v>0 and t>0 for v,t in refs), 'Unsupported OBJ indices')
            faces[current].append([(positions[v-1],(uvs[t-1][0],1-uvs[t-1][1])) for v,t in refs])
    for id_,rows in faces.items():
        require(len(rows) == contract['records'][id_]['triangles'], 'Facade OBJ source count differs')
    return faces


def native_snapshot(u, mesh):
    description = mesh.get_static_mesh_description(0)
    require(description is not None and description.get_triangle_count() > 0, 'Missing native source MeshDescription')
    rows,instances = [],set()
    for index in range(description.get_triangle_count()):
        tri = u.TriangleID(id_value=index)
        require(description.is_triangle_valid(tri), 'Facade triangle ID holes unsupported')
        row = []
        for corner in range(3):
            instance = description.get_triangle_vertex_instance(tri,corner)
            require(description.is_vertex_instance_valid(instance), 'Invalid native facade corner')
            vertex = description.get_vertex_instance_vertex(instance)
            require(description.is_vertex_valid(vertex), 'Invalid facade vertex')
            p = description.get_vertex_position(vertex); uv = description.get_vertex_instance_uv(instance,0)
            value = {'instance':int(instance.id_value), 'vertex':int(vertex.id_value),
                     'pCm':[float(p.x),float(p.y),float(p.z)], 'uv0':[float(uv.x),float(uv.y)]}
            require(all(math.isfinite(x) for x in value['pCm']+value['uv0']), 'Nonfinite native geometry/UV')
            instances.add(value['instance']); row.append(value)
        rows.append(row)
    require(len(instances) == description.get_vertex_instance_count(), 'Incomplete facade native corner coverage')
    return {'rows':rows, 'vertexCount':description.get_vertex_count(), 'instanceCount':len(instances),
            'renderTriangles':mesh.get_num_triangles(0), 'renderSections':mesh.get_num_sections(0)}


def source_proof(snapshot, source, id_):
    rows = snapshot['rows']; require(len(rows) == len(source), 'Facade native source count differs: '+id_)
    remaining = set(range(len(source))); maximum = maximum_uv = 0.0
    for row in rows:
        actual = [([v['pCm'][0]*10,-v['pCm'][1]*10,v['pCm'][2]*10],v['uv0']) for v in row]
        matches = []
        for index in remaining:
            for rotation in range(3):
                wanted = source[index][rotation:] + source[index][:rotation]
                err = max(abs(x-y) for (p,_),(q,_) in zip(actual,wanted) for x,y in zip(p,q))
                uv_err = max(abs(x-y) for (_,p),(_,q) in zip(actual,wanted) for x,y in zip(p,q))
                if err <= .002 and uv_err <= .000002: matches.append((index,err,uv_err))
        require(len(matches) == 1, 'Facade triangle is absent/ambiguous/reversed or UV0 differs: '+id_)
        index,err,uv_err = matches[0]; remaining.remove(index)
        maximum=max(maximum,err); maximum_uv=max(maximum_uv,uv_err)
    require(not remaining, 'Facade source triangle coverage incomplete')
    return {'method':'public-MeshDescription-position-UV0-cyclic-triangle-match', 'objectId':id_,
            'triangleCount':len(rows), 'sourcePositionToleranceMm':.002, 'maximumPositionErrorMm':maximum,
            'uv0Tolerance':.000002, 'maximumUv0Error':maximum_uv, 'windingAndMultiplicityVerified':True,
            'nativeSourceSnapshotSha256':digest(snapshot), 'normalTangentAttributeReadback':False}


def graph_links():
    s = shader()
    links = [(origin,'',role,pin) for role in s.CODES for origin,pin in
             [('position','Position'),('normalWS','NormalWS'),('grain','Grain'),('anchor','AnchorCm')]
             if pin in s.INPUTS[role]]
    links += [(origin,'',role,pin) for role in ('albedo','normalMap','roughMap') for origin,pin in
              [('sampleUV','UVs'),('gradientX','DDX(UVs)'),('gradientY','DDY(UVs)')]]
    return links + [('normalMap','RGB','normal','MapNormal'), ('albedo','RGB','color','A'), ('joint','','color','B')]


OUTPUTS = [('BASE_COLOR','color',''), ('ROUGHNESS','roughMap','R'), ('NORMAL','normal',''),
           ('METALLIC','metallic',''), ('SPECULAR','specular','')]


def out_name(value):
    return value[1] if isinstance(value,tuple) and len(value)==2 and value[0] is True else value


def material_proof(u, material, contract, slot, base):
    lib,assets,s = u.MaterialEditingLibrary,u.EditorAssetLibrary,shader()
    require(isinstance(material,u.Material) and assets.get_metadata_tag(material,'BreziGeneratedBy') == OWNER
            and assets.get_metadata_tag(material,RECIPE_TAG) == contract['recipeSha256']
            and assets.get_metadata_tag(material,'source_material_slot') == slot, 'Facade material owner/recipe/slot changed')
    for key,value in {'blend_mode':u.BlendMode.BLEND_OPAQUE, 'shading_model':u.MaterialShadingModel.MSM_DEFAULT_LIT,
                      'two_sided':False,'tangent_space_normal':False,'use_material_attributes':False}.items():
        require(material.get_editor_property(key) == value, 'Facade material policy differs: '+key)
    require(lib.has_material_usage(material,u.MaterialUsage.MATUSAGE_NANITE), 'Facade material Nanite flag missing')
    expressions = list(lib.get_material_expressions(material))
    nodes = {str(assets.get_metadata_tag(n,'BreziOakNodeRole')):n for n in expressions}
    expected = {'position','normalWS','grain','anchor',*s.CODES,'albedo','normalMap','roughMap','color','metallic','specular'}
    require(set(nodes)==expected and len(nodes)==len(expressions)==15, 'Facade graph topology differs')
    classes = {'position':u.MaterialExpressionWorldPosition,'normalWS':u.MaterialExpressionVertexNormalWS,
               'grain':u.MaterialExpressionConstant3Vector,'anchor':u.MaterialExpressionConstant3Vector,
               'color':u.MaterialExpressionMultiply,'metallic':u.MaterialExpressionConstant,'specular':u.MaterialExpressionConstant}
    for role,cls in classes.items(): require(isinstance(nodes[role],cls), 'Facade node class differs: '+role)
    require(nodes['position'].get_editor_property('world_position_shader_offset') == u.WorldPositionIncludedOffsets.WPT_DEFAULT,
            'Facade position is not absolute world space')
    for role,values in {'anchor':contract['reference']['anchorCm'], 'grain':contract['reference']['grainNativeBySlot'][slot]}.items():
        v=nodes[role].get_editor_property('constant')
        require(all(abs(float(getattr(v,k))-x)<1e-6 for k,x in zip(('r','g','b'),values)), 'Facade vector differs: '+role)
    for role,value in [('metallic',0),('specular',.5)]:
        require(float(nodes[role].get_editor_property('r'))==value, 'Facade scalar differs')
    for role,code in s.CODES.items():
        n=nodes[role]
        require(isinstance(n,u.MaterialExpressionCustom) and n.get_editor_property('code')==code
                and [str(i.get_editor_property('input_name')) for i in n.get_editor_property('inputs')] == s.INPUTS[role]
                and n.get_editor_property('output_type') == getattr(u.CustomMaterialOutputType,
                    'CMOT_FLOAT3' if role=='normal' else 'CMOT_FLOAT1' if role=='joint' else 'CMOT_FLOAT2'),
                'Facade custom shader inputs/code/type differ: '+role)
    for origin,output,target,pin in graph_links():
        names=[str(v) for v in lib.get_material_expression_input_names(nodes[target])]
        sources=list(lib.get_inputs_for_material_expression(material,nodes[target]))
        require(len(names)==len(sources) and pin in names and sources[names.index(pin)]==nodes[origin], 'Facade graph link differs')
        expected_output=output or list(lib.get_material_expression_output_names(nodes[origin]))[0]
        require(out_name(lib.get_input_node_output_name_for_material_expression(nodes[target],nodes[origin]))==expected_output,
                'Facade graph channel differs')
    for prop,role,channel in OUTPUTS:
        pid=getattr(u.MaterialProperty,'MP_'+prop)
        require(lib.get_material_property_input_node(material,pid)==nodes[role]
                and out_name(lib.get_material_property_input_node_output_name(material,pid)) ==
                (channel or list(lib.get_material_expression_output_names(nodes[role]))[0]), 'Facade output differs: '+prop)
    for prop in ('WORLD_POSITION_OFFSET','OPACITY','OPACITY_MASK','EMISSIVE_COLOR'):
        require(lib.get_material_property_input_node(material,getattr(u.MaterialProperty,'MP_'+prop)) is None,
                'Facade unexpected geometry/optical input')
    textures={}
    for role,source_role,sampler in [('albedo','Diffuse',u.MaterialSamplerType.SAMPLERTYPE_COLOR),
                                   ('normalMap','nor_gl',u.MaterialSamplerType.SAMPLERTYPE_NORMAL),
                                   ('roughMap','Rough',u.MaterialSamplerType.SAMPLERTYPE_MASKS)]:
        node=nodes[role]
        require(isinstance(node,u.MaterialExpressionTextureSample) and node.get_editor_property('sampler_type')==sampler
                and node.get_editor_property('mip_value_mode')==u.TextureMipValueMode.TMVM_DERIVATIVE,
                'Facade sampler policy differs')
        textures[role]=base.texture_proof(u,node.get_editor_property('texture'),role,
                         contract['candidate']['maps'][source_role]['sha256'],OWNER)
    return {'asset':material.get_path_name(),'sourceSlot':slot,'graphNodes':15,'graphLinks':len(graph_links()),
            'exactGraphVerified':True,'naniteUsage':True,'absoluteWorldProjection':True,'unwrappedGradients':True,
            'grainNative':contract['reference']['grainNativeBySlot'][slot], 'anchorCm':contract['reference']['anchorCm'],
            'textures':textures,'shaderSha256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in s.CODES.items()},
            'renderedVerified':False,'residentMipsVerified':False}


def create_material(u, contract, slot, base):
    s=shader(); name='M_Facade_'+slot; prefix=PREFIX+'/R_'+contract['recipeSha256'][:16]
    writer=base.Writer(u,prefix,contract,{'owner':OWNER,'materialName':name,'palette':(1,1,1),'basisCode':s.BASIS})
    material=writer.existing(prefix+'/Materials/'+name)
    if material:
        material_proof(u,material,contract,slot,base); writer.paths.add(material.get_path_name())
        for n in writer.lib.get_material_expressions(material):
            if isinstance(n,u.MaterialExpressionTextureSample): writer.paths.add(n.get_editor_property('texture').get_path_name())
        return material,writer.paths
    material=u.AssetToolsHelpers.get_asset_tools().create_asset(name,prefix+'/Materials',u.Material,u.MaterialFactoryNew())
    require(material is not None,'Facade material creation failed')
    for key,value in {'BreziGeneratedBy':OWNER,RECIPE_TAG:contract['recipeSha256'],'source_material_slot':slot}.items():
        writer.assets.set_metadata_tag(material,key,value)
    for key,value in {'blend_mode':u.BlendMode.BLEND_OPAQUE,'shading_model':u.MaterialShadingModel.MSM_DEFAULT_LIT,
                      'two_sided':False,'tangent_space_normal':False,'use_material_attributes':False}.items():
        material.set_editor_property(key,value)
    writer.lib.set_base_material_usage(material,u.MaterialUsage.MATUSAGE_NANITE,True)
    writer.node(material,'position',u.MaterialExpressionWorldPosition)
    writer.node(material,'normalWS',u.MaterialExpressionVertexNormalWS)
    for role,value in {'anchor':contract['reference']['anchorCm'],'grain':contract['reference']['grainNativeBySlot'][slot]}.items():
        writer.node(material,role,u.MaterialExpressionConstant3Vector,constant=u.LinearColor(*value,1))
    for role,code in s.CODES.items():
        writer.custom(material,role,code,s.INPUTS[role],getattr(u.CustomMaterialOutputType,
            'CMOT_FLOAT3' if role=='normal' else 'CMOT_FLOAT1' if role=='joint' else 'CMOT_FLOAT2'))
    for role,source_role,sampler in [('albedo','Diffuse',u.MaterialSamplerType.SAMPLERTYPE_COLOR),
                                   ('normalMap','nor_gl',u.MaterialSamplerType.SAMPLERTYPE_NORMAL),
                                   ('roughMap','Rough',u.MaterialSamplerType.SAMPLERTYPE_MASKS)]:
        writer.node(material,role,u.MaterialExpressionTextureSample,texture=writer.texture(role,source_role),
                    sampler_type=sampler,mip_value_mode=u.TextureMipValueMode.TMVM_DERIVATIVE)
    writer.node(material,'color',u.MaterialExpressionMultiply)
    for role,value in [('metallic',0),('specular',.5)]: writer.node(material,role,u.MaterialExpressionConstant,r=value)
    for origin,output,target,pin in graph_links():
        require(writer.lib.connect_material_expressions(writer.nodes[origin],output,writer.nodes[target],pin),'Facade connection failed')
    for prop,role,channel in OUTPUTS:
        require(writer.lib.connect_material_property(writer.nodes[role],channel,getattr(u.MaterialProperty,'MP_'+prop)),
                'Facade material output failed')
    errors=list(writer.lib.recompile_material(material)); require(not errors,'Facade graph compile failed: '+str(errors))
    writer.save(material); material_proof(u,material,contract,slot,base)
    return material,writer.paths


def preflight(u, contract, assets_by_id, source, base, require_facade=False):
    bindings=base.components(u,SLOTS); snapshots={}; proofs={}
    require(len({assets_by_id[i].get_path_name() for i in SLOTS})==len(SLOTS),'Facade meshes alias across source IDs')
    for id_,slot in SLOTS.items():
        mesh=assets_by_id[id_]; actor,component=bindings[id_]; record=contract['records'][id_]
        require(isinstance(mesh,u.StaticMesh) and component.get_editor_property('static_mesh')==mesh
                and len(mesh.get_editor_property('static_materials'))==1 and mesh.get_num_sections(0)==1,
                'Facade source mesh/component/slot differs: '+id_)
        for key,value in {'source_object_id':id_,'source_id':record['sourceId'],
                          'source_group':record['group'],'source_name':record['name']}.items():
            require(u.EditorAssetLibrary.get_metadata_tag(mesh,key)==value,'Facade mesh source identity differs: '+id_)
        require(not list(component.get_editor_property('override_materials')),
                'Refusing a component material override on facade source: '+id_)
        # OBJ meshes already contain world coordinates; moving/rotating/scaling
        # an actor must not silently retain a source-aligned projection claim.
        transform=component.get_world_transform(); p=transform.translation; r=transform.rotation; scale=transform.scale3d
        require(max(abs(float(v)) for v in (p.x,p.y,p.z,r.x,r.y,r.z))<1e-6
                and abs(abs(float(r.w))-1)<1e-6 and max(abs(float(v)-1) for v in (scale.x,scale.y,scale.z))<1e-6,
                'Facade native component transform differs from baked source coordinates')
        material=mesh.get_material(0); assets=u.EditorAssetLibrary
        require(material is not None and component.get_material(0)==material
                and assets.get_metadata_tag(material,'source_material_slot')==slot,'Facade current source slot differs')
        owner=assets.get_metadata_tag(material,'BreziGeneratedBy')
        if owner==OWNER: material_proof(u,material,contract,slot,base)
        else: require(not require_facade and owner=='scripts/unreal/materials.py','Refusing foreign facade material: '+id_)
        snapshots[id_]=native_snapshot(u,mesh)
        proofs[id_]=source_proof(snapshots[id_],source[id_],id_)
    return snapshots,proofs


def apply_facade_wood(scene, assets_by_id, geometry):
    import unreal as u
    from materials import _asset_hashes
    contract=verify_inputs(scene,geometry); source=read_source(Path(geometry)/'dom-mm.obj',contract)
    base=module('brezi_facade_photo_base',ROOT/'scripts/unreal/tv-oak/tv_oak.py')
    before,proofs=preflight(u,contract,assets_by_id,source,base)
    originals={i:assets_by_id[i].get_material(0) for i in SLOTS}
    materials,paths={},set()
    for slot in sorted(set(SLOTS.values())):
        materials[slot],made=create_material(u,contract,slot,base); paths.update(made)
    # Entire source set and every graph are valid before the first assignment.
    changed=[]
    try:
        for id_,slot in SLOTS.items():
            mesh=assets_by_id[id_]; changed.append(id_); mesh.set_material(0,materials[slot])
            require(native_snapshot(u,mesh)==before[id_],'Facade assignment altered geometry or UV0: '+id_)
            require(u.EditorAssetLibrary.save_loaded_asset(mesh,only_if_is_dirty=False),'Facade mesh save failed')
        after,_=preflight(u,contract,assets_by_id,source,base,True)
        require(after==before,'Facade post-save source attributes changed')
    except Exception as exc:
        rollback=[]
        for id_ in changed:
            try:
                assets_by_id[id_].set_material(0,originals[id_])
                require(u.EditorAssetLibrary.save_loaded_asset(assets_by_id[id_],only_if_is_dirty=False),'save failed')
            except Exception as restore: rollback.append(id_+': '+str(restore))
        raise RuntimeError('Facade assignment failed: '+str(exc)+'; rollback errors='+str(rollback)) from exc
    return {'status':'facade-wood-authored-validated','recipeSha256':contract['recipeSha256'],
            'pipelineFiles':contract['pipelineFiles'],'assetHashes':_asset_hashes(paths),
            'assignedMeshHashes':_asset_hashes([assets_by_id[i].get_path_name() for i in SLOTS]),
            'objects':proofs,'materials':{slot:material_proof(u,m,contract,slot,base) for slot,m in materials.items()},
            'objectCount':12,'materialCount':10,'textureCount':3,'sourceObjSha256':OBJ_SHA,'sourceSceneSha256':SCENE_SHA,
            'geometryAndUv0BeforeAfterEqual':True,'geometryUvNormalTangentSetterCalled':False,
            'savedReloadVerified':False,'renderedVerified':False,'limitations':contract['reference']['limits']}


def validate_saved_facade_wood(scene, assets_by_id, geometry, authored):
    """Call after a real map unload/reload. Caller owns/records that lifecycle."""
    import unreal as u
    from materials import _asset_hashes
    contract=verify_inputs(scene,geometry)
    require(authored['status']=='facade-wood-authored-validated' and authored['recipeSha256']==contract['recipeSha256'],
            'Saved facade expected receipt differs')
    base=module('brezi_facade_photo_base',ROOT/'scripts/unreal/tv-oak/tv_oak.py')
    source=read_source(Path(geometry)/'dom-mm.obj',contract)
    _,proofs=preflight(u,contract,assets_by_id,source,base,True)
    require(same_saved_values(proofs,authored['objects']),'Reloaded facade geometry/UV0/source proof differs')
    materials={slot:material_proof(u,assets_by_id[id_].get_material(0),contract,slot,base) for id_,slot in SLOTS.items()}
    # Native texture dimensions are tuples in memory and JSON arrays on disk.
    require(same_saved_values(materials,authored['materials']),'Reloaded facade material graph differs')
    paths={m['asset'] for m in materials.values()}
    paths.update(t['asset'] for m in materials.values() for t in m['textures'].values())
    require(_asset_hashes(paths)==authored['assetHashes']
            and _asset_hashes([assets_by_id[i].get_path_name() for i in SLOTS])==authored['assignedMeshHashes'],
            'Saved facade asset bytes changed')
    return {'status':'facade-saved-state-readback-validated','recipeSha256':contract['recipeSha256'],
            'objectCount':len(proofs),'materialCount':len(materials),'sourceProofsEqual':True,
            'graphProofsEqual':True,'savedAssetHashesEqual':True,'callerMustProveUnloadReload':True,'renderedVerified':False}
