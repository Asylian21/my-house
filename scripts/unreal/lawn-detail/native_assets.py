"""Owned grass assets; no Unreal import/execution until called by native_layer.

Only the four pinned short GLBs are accepted. Numeric native normals/tangents
are deliberately NOT certified: their scalar getters are not reflected in 5.8.
"""
import hashlib
import json
import math
from pathlib import Path
import struct

OWNER = 'scripts/unreal/lawn-detail/native_layer.py'
PREFIX = '/Game/Brezi/LawnDetail'
IDS = tuple('grass_bermuda_01_small_'+c for c in 'abcd')
ROLE = 'BreziLawnNodeRole'


def require(ok, message):
    if not ok: raise RuntimeError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def values(value): return json.loads(json.dumps(value,allow_nan=False))


def source_mesh(path, expected):
    data=Path(path).read_bytes()
    require(sha(path)==expected['sha256'], 'Grass GLB bytes changed')
    require(len(data)>=20 and struct.unpack_from('<III',data)==(0x46546c67,2,len(data)), 'Malformed grass GLB')
    chunks={};offset=12
    while offset<len(data):
        size,kind=struct.unpack_from('<II',data,offset);offset+=8
        require(kind not in chunks and size%4==0 and offset+size<=len(data),'Malformed GLB chunks')
        chunks[kind]=data[offset:offset+size];offset+=size
    require(set(chunks)=={0x4e4f534a,0x004e4942},'Unexpected GLB chunks')
    doc=json.loads(chunks[0x4e4f534a]);binary=chunks[0x004e4942]
    require(len(doc['nodes'])==len(doc['meshes'])==1 and doc['nodes'][0]['mesh']==0
            and not any(k in doc['nodes'][0] for k in ('matrix','translation','rotation','scale','children','skin')),'Unexpected prototype node transform')
    primitives=doc['meshes'][0]['primitives'];require(len(primitives)==1,'Prototype primitive count differs')
    primitive=primitives[0]
    require(primitive.get('mode',4)==4 and set(primitive['attributes'])=={'POSITION','NORMAL','TEXCOORD_0','TANGENT'}
            and 'targets' not in primitive,'Prototype geometry attributes differ')
    def accessor(index,kind,component=None):
        a=doc['accessors'][index];require(a['type']==kind and 'sparse' not in a and not a.get('normalized',False),'Unsupported accessor')
        if component is not None: require(a['componentType']==component,'Unexpected accessor component type')
        fmt={5121:'B',5123:'H',5125:'I',5126:'f'}[a['componentType']];count={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[kind]
        view=doc['bufferViews'][a['bufferView']];require(view.get('buffer',0)==0 and 0<a['count']<=1000,'Accessor budget/buffer differs')
        width=struct.calcsize('<'+fmt*count);stride=view.get('byteStride',width);start=view.get('byteOffset',0)+a.get('byteOffset',0)
        require(stride>=width and start+(a['count']-1)*stride+width<=view.get('byteOffset',0)+view['byteLength']<=len(binary),'Accessor out of bounds')
        result=[struct.unpack_from('<'+fmt*count,binary,start+i*stride) for i in range(a['count'])]
        require(all(math.isfinite(v) for row in result for v in row),'Nonfinite GLB attribute');return result
    attrs=primitive['attributes'];p=accessor(attrs['POSITION'],'VEC3',5126);uv=accessor(attrs['TEXCOORD_0'],'VEC2',5126)
    normals=accessor(attrs['NORMAL'],'VEC3',5126);tangents=accessor(attrs['TANGENT'],'VEC4',5126)
    indices=[v[0] for v in accessor(primitive['indices'],'SCALAR')]
    require(len(p)==len(uv)==len(normals)==len(tangents)==expected['exportedVertices'] and len(indices)==3*expected['triangles']
            and all(isinstance(i,int) and 0<=i<len(p) for i in indices),'GLB topology differs')
    # GLTFCore ConvertVec3 is {X,Z,Y}; GetTexCoords copies float2 unchanged.
    native=[[100*x,100*z,100*y] for x,y,z in p]
    faces=[[(native[i],list(uv[i])) for i in indices[n:n+3]] for n in range(0,len(indices),3)]
    return {'faces':faces,'vertices':len(p),'triangles':len(faces),'sha256':expected['sha256'],
            'normalPayloadSha256':digest(normals),'tangentPayloadSha256':digest(tangents)}


def compare_faces(actual, expected):
    """Bijection with cyclic winding, UVs and multiplicity; never reversed winding."""
    require(len(actual)==len(expected),'Native/source triangle count differs');remaining=list(expected);pe=ue=0.
    for triangle in actual:
        match=None
        for i,source in enumerate(remaining):
            for shift in range(3):
                p=max(abs(triangle[c][0][k]-source[(c+shift)%3][0][k]) for c in range(3) for k in range(3))
                v=max(abs(triangle[c][1][k]-source[(c+shift)%3][1][k]) for c in range(3) for k in range(2))
                if p<=.0002 and v<=2e-6:match=(i,p,v);break
            if match is not None:break
        require(match is not None,'Grass position/winding/UV0 source correspondence failed')
        index,p,v=match;remaining.pop(index);pe=max(pe,p);ue=max(ue,v)
    return {'maximumPositionErrorCm':pe,'maximumUV0Error':ue,'triangleMultiplicityAndWindingVerified':True}


def mesh_proof(u,mesh,source,material):
    require(isinstance(mesh,u.StaticMesh) and mesh.get_num_sections(0)==1 and mesh.get_num_triangles(0)==source['triangles']
            and mesh.get_num_tex_coords(0)==1 and len(mesh.get_editor_property('static_materials'))==1
            and mesh.get_material(0)==material,'Grass mesh sections/material/UV channels differ')
    require(not mesh.get_editor_property('nanite_settings').get_editor_property('enabled')
            and not mesh.get_editor_property('has_navigation_data'),'Grass mesh Nanite/navigation policy differs')
    description=mesh.get_static_mesh_description(0)
    require(description is not None and description.get_triangle_count()==source['triangles'],'Grass source MeshDescription missing')
    rows=[];instances=set()
    for index in range(description.get_triangle_count()):
        tri=u.TriangleID(id_value=index);require(description.is_triangle_valid(tri),'Sparse grass triangle IDs unsupported');row=[]
        for corner in range(3):
            vi=description.get_triangle_vertex_instance(tri,corner);require(description.is_vertex_instance_valid(vi),'Invalid grass corner')
            v=description.get_vertex_instance_vertex(vi);require(description.is_vertex_valid(v),'Invalid grass vertex')
            p=description.get_vertex_position(v);uv=description.get_vertex_instance_uv(vi,0)
            row.append(([float(p.x),float(p.y),float(p.z)],[float(uv.x),float(uv.y)]));instances.add(int(vi.id_value))
        rows.append(row)
    require(len(instances)==description.get_vertex_instance_count(),'Incomplete native grass corner readback')
    result=compare_faces(rows,source['faces'])
    result.update(asset=mesh.get_path_name(),triangles=source['triangles'],uvChannels=1,nanite=False,
                  nativeTriangleUV0Sha256=digest(rows),sourceGLBSha256=source['sha256'],nativeNumericNormalsVerified=False,
                  nativeNumericTangentsVerified=False,sourceNormalPayloadSha256=source['normalPayloadSha256'],
                  sourceTangentPayloadSha256=source['tangentPayloadSha256'])
    return result


def enum(u,kind,token):
    matches=[n for n in dir(kind) if token==n.replace('_','').replace('MSM','').replace('MATUSAGE','')]
    require(len(matches)==1,'Ambiguous native enum '+token);return getattr(kind,matches[0])


def output_name(value):
    if isinstance(value,tuple) and len(value)==2 and value[0] is True:return value[1]
    return value


def graph_spec(u):
    return {'uv':(u.MaterialExpressionTextureCoordinate,{'coordinate_index':0,'u_tiling':1.,'v_tiling':1.,'un_mirror_u':False,'un_mirror_v':False}),
            **{k:(u.MaterialExpressionTextureSample,{}) for k in ('albedo','alpha','normal','roughness')},
            'fade':(u.MaterialExpressionPerInstanceFadeAmount,{}),'mask':(u.MaterialExpressionMultiply,{}),
            'transmission':(u.MaterialExpressionMultiply,{'const_b':.35}),
            'opacity':(u.MaterialExpressionConstant,{'r':.5})}


def links():
    return [('uv','',k,'UVs') for k in ('albedo','alpha','normal','roughness')]+[
        ('alpha','R','mask','A'),('fade','','mask','B'),('albedo','RGB','transmission','A')]


def outputs():
    return {'BASE_COLOR':('albedo','RGB'),'NORMAL':('normal','RGB'),'ROUGHNESS':('roughness','R'),
            'OPACITY_MASK':('mask',''),'SUBSURFACE_COLOR':('transmission',''),'OPACITY':('opacity','')}


class Assets:
    def __init__(self,u,prefix,recipe,report,prototype_dir):
        self.u,self.prefix,self.recipe,self.report,self.prototype_dir=u,prefix,recipe,report,Path(prototype_dir)
        self.a,self.lib=u.EditorAssetLibrary,u.MaterialEditingLibrary
        self.tools=u.AssetToolsHelpers.get_asset_tools();self.paths=set()
        require(prefix==PREFIX+'/R_'+recipe[:16] and len(recipe)==64,'Unsafe grass namespace')

    def own(self,obj):
        require(obj is not None and obj.get_path_name().startswith(self.prefix+'/'),'Grass object escaped namespace')
        self.a.set_metadata_tag(obj,'BreziGeneratedBy',OWNER);self.a.set_metadata_tag(obj,'BreziLawnRecipe',self.recipe)
        self.paths.add(obj.get_path_name());return obj

    def existing(self,path):
        require(path.startswith(self.prefix+'/'),'Grass lookup escaped namespace')
        obj=self.a.load_asset(path) if self.a.does_asset_exist(path) else None
        if obj is not None:
            require(self.a.get_metadata_tag(obj,'BreziGeneratedBy')==OWNER and self.a.get_metadata_tag(obj,'BreziLawnRecipe')==self.recipe,'Refusing unowned/stale grass asset '+path)
            self.paths.add(obj.get_path_name())
        return obj

    def save(self,obj):require(self.a.save_loaded_asset(obj,only_if_is_dirty=False),'Own grass asset save failed')

    def texture_proof(self,texture,role,entry):
        u=self.u
        expected={'srgb':role=='albedo','flip_green_channel':role=='normal','lod_bias':0,'max_texture_size':0,
            'compression_settings':u.TextureCompressionSettings.TC_NORMALMAP if role=='normal' else u.TextureCompressionSettings.TC_DEFAULT if role=='albedo' else u.TextureCompressionSettings.TC_MASKS,
            'address_x':u.TextureAddress.TA_WRAP,'address_y':u.TextureAddress.TA_WRAP,'mip_gen_settings':u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP}
        require(isinstance(texture,u.Texture2D) and self.existing(texture.get_path_name())==texture,'Grass texture identity differs')
        require(self.a.get_metadata_tag(texture,'source_sha256')==entry['sha256'],'Grass texture source differs')
        for k,v in expected.items(): require(texture.get_editor_property(k)==v,'Grass texture policy differs: '+k)
        size=[texture.blueprint_get_size_x(),texture.blueprint_get_size_y()]
        require(size==entry['size']==[1024,1024],'Grass texture dimensions differ')
        return {'asset':texture.get_path_name(),'sourceSha256':entry['sha256'],'pixels':size,'srgb':role=='albedo','greenFlippedOnce':role=='normal','residentMipsVerified':False}

    def textures(self):
        u=self.u;result={}
        for role,entry in self.report['models']['grass_bermuda_01']['textures'].items():
            require(role in ('albedo','alpha','normal','roughness'),'Unexpected grass texture role')
            file=self.prototype_dir/entry['path'];require(sha(file)==entry['sha256'],'Grass map changed')
            name='T_Grass_'+role;texture=self.existing(self.prefix+'/Textures/'+name)
            if texture is None:
                task=u.AssetImportTask()
                for k,v in {'filename':str(file),'destination_path':self.prefix+'/Textures','destination_name':name,
                            'automated':True,'save':False,'replace_existing':False,'factory':u.TextureFactory()}.items():task.set_editor_property(k,v)
                self.tools.import_asset_tasks([task]);objects=task.get_objects()
                require(len(objects)==1 and isinstance(objects[0],u.Texture2D),'Expected one grass texture');texture=self.own(objects[0])
                for k,v in {'srgb':role=='albedo','flip_green_channel':role=='normal','lod_bias':0,'max_texture_size':0,
                    'compression_settings':u.TextureCompressionSettings.TC_NORMALMAP if role=='normal' else u.TextureCompressionSettings.TC_DEFAULT if role=='albedo' else u.TextureCompressionSettings.TC_MASKS,
                    'address_x':u.TextureAddress.TA_WRAP,'address_y':u.TextureAddress.TA_WRAP,'mip_gen_settings':u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP}.items():texture.set_editor_property(k,v)
                self.a.set_metadata_tag(texture,'source_sha256',entry['sha256']);self.save(texture)
            self.texture_proof(texture,role,entry);result[role]=texture
        require(set(result)=={'albedo','alpha','normal','roughness'},'Four grass maps required');return result

    def material_proof(self,material):
        u,lib=self.u,self.lib
        require(self.existing(material.get_path_name())==material and isinstance(material,u.Material),'Grass material identity differs')
        for k,v in {'blend_mode':u.BlendMode.BLEND_MASKED,'two_sided':True,'tangent_space_normal':True,'use_material_attributes':False,
                    'shading_model':enum(u,u.MaterialShadingModel,'TWOSIDEDFOLIAGE')}.items():require(material.get_editor_property(k)==v,'Grass material policy differs '+k)
        require(abs(material.get_editor_property('opacity_mask_clip_value')-.45)<1e-6,'Grass alpha cutoff differs')
        require(lib.has_material_usage(material,enum(u,u.MaterialUsage,'INSTANCEDSTATICMESHES')),'Grass HISM material usage missing')
        expressions=list(lib.get_material_expressions(material));nodes={str(self.a.get_metadata_tag(n,ROLE)):n for n in expressions};spec=graph_spec(u)
        require(len(nodes)==len(expressions)==len(spec) and nodes.keys()==spec.keys(),'Grass graph roles/topology differ')
        textures={}
        for role,(cls,props) in spec.items():
            require(isinstance(nodes[role],cls),'Grass graph node class differs '+role)
            for k,v in props.items():
                actual=nodes[role].get_editor_property(k)
                require(abs(actual-v)<1e-6 if isinstance(v,float) else actual==v,'Grass node setting differs '+role+'.'+k)
            if role in ('albedo','alpha','normal','roughness'):
                sampler=u.MaterialSamplerType.SAMPLERTYPE_NORMAL if role=='normal' else u.MaterialSamplerType.SAMPLERTYPE_COLOR if role=='albedo' else u.MaterialSamplerType.SAMPLERTYPE_MASKS
                require(nodes[role].get_editor_property('sampler_type')==sampler,'Grass sampler differs')
                textures[role]=self.texture_proof(nodes[role].get_editor_property('texture'),role,self.report['models']['grass_bermuda_01']['textures'][role])
        for src,out,dst,pin in links():
            names=list(map(str,lib.get_material_expression_input_names(nodes[dst])));inputs=list(lib.get_inputs_for_material_expression(material,nodes[dst]))
            require(pin in names and len(inputs)==len(names) and inputs[names.index(pin)]==nodes[src],'Grass graph connection differs')
            expected=out or str(lib.get_material_expression_output_names(nodes[src])[0])
            require(output_name(lib.get_input_node_output_name_for_material_expression(nodes[dst],nodes[src]))==expected,'Grass graph source channel differs')
        # Reject extra links, including an unexpected B input on the artistic transmission scalar.
        wanted={(dst,pin) for _,_,dst,pin in links()}
        for role,node in nodes.items():
            names=list(map(str,lib.get_material_expression_input_names(node)));inputs=list(lib.get_inputs_for_material_expression(material,node))
            require(len(names)==len(inputs),'Grass graph input getter size differs')
            for name,input_ in zip(names,inputs):require(input_ is None or (role,name) in wanted,'Unexpected grass graph input '+role+'.'+name)
        for prop,(role,out) in outputs().items():
            pid=getattr(u.MaterialProperty,'MP_'+prop);expected=out or str(lib.get_material_expression_output_names(nodes[role])[0])
            require(lib.get_material_property_input_node(material,pid)==nodes[role] and output_name(lib.get_material_property_input_node_output_name(material,pid))==expected,'Grass material output/channel differs '+prop)
        for prop in ('WORLD_POSITION_OFFSET','EMISSIVE_COLOR','METALLIC','SPECULAR','AMBIENT_OCCLUSION'):
            require(lib.get_material_property_input_node(material,getattr(u.MaterialProperty,'MP_'+prop)) is None,'Unexpected grass material output '+prop)
        # MP_PixelDepthOffset is not reflected in the 5.8 Python enum.
        require(u.BreziRendererSettingsAudit.has_no_pixel_depth_offset_connection(material) is True,
                'Unexpected grass pixel depth offset')
        return {'asset':material.get_path_name(),'graphNodes':len(nodes),'alphaCutoff':.45,'masked':True,'twoSidedFoliage':True,
                'opacityMask':'UV0.alpha.R * PerInstanceFadeAmount','artisticTransmissionScale':.35,'opacity':.5,
                'worldPositionOffset':False,'textures':textures,'renderedVerified':False}

    def material(self):
        u=self.u;material=self.existing(self.prefix+'/Materials/M_Grass')
        if material is None:
            textures=self.textures();material=self.own(self.tools.create_asset('M_Grass',self.prefix+'/Materials',u.Material,u.MaterialFactoryNew()))
            for k,v in {'blend_mode':u.BlendMode.BLEND_MASKED,'two_sided':True,'tangent_space_normal':True,'use_material_attributes':False,
                        'opacity_mask_clip_value':.45,'shading_model':enum(u,u.MaterialShadingModel,'TWOSIDEDFOLIAGE')}.items():material.set_editor_property(k,v)
            self.lib.set_base_material_usage(material,enum(u,u.MaterialUsage,'INSTANCEDSTATICMESHES'),True);nodes={}
            for role,(cls,props) in graph_spec(u).items():
                node=self.lib.create_material_expression(material,cls,-600,0);require(node is not None,'Grass graph creation failed')
                self.a.set_metadata_tag(node,ROLE,role)
                for k,v in props.items():node.set_editor_property(k,v)
                if role in textures:
                    node.set_editor_property('texture',textures[role]);node.set_editor_property('sampler_type',u.MaterialSamplerType.SAMPLERTYPE_NORMAL if role=='normal' else u.MaterialSamplerType.SAMPLERTYPE_COLOR if role=='albedo' else u.MaterialSamplerType.SAMPLERTYPE_MASKS)
                nodes[role]=node
            for src,out,dst,pin in links():require(self.lib.connect_material_expressions(nodes[src],out,nodes[dst],pin),'Grass material link failed')
            for prop,(role,out) in outputs().items():require(self.lib.connect_material_property(nodes[role],out,getattr(u.MaterialProperty,'MP_'+prop)),'Grass material output failed')
            errors=list(self.lib.recompile_material(material));require(not errors,'Grass material compile errors '+str(errors));self.save(material)
        return material,self.material_proof(material)

    def pipeline(self):
        u=self.u;path=self.prefix+'/Pipeline/GrassAssets';pipeline=self.existing(path);new=pipeline is None
        if new:pipeline=self.own(self.a.duplicate_asset('/Interchange/Pipelines/DefaultGLTFSceneAssetsPipeline.DefaultGLTFSceneAssetsPipeline',path))
        settings=[(pipeline,{'use_source_name_for_asset':False}),
            (pipeline.get_editor_property('mesh_pipeline'),{'combine_static_meshes_behavior':u.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE,'collision':False,'build_nanite':False,'generate_lightmap_u_vs':False}),
            (pipeline.get_editor_property('common_meshes_properties'),{'remove_degenerates':False,'recompute_normals':False,'recompute_tangents':False,'use_high_precision_tangent_basis':True,'use_full_precision_u_vs':True}),
            (pipeline.get_editor_property('material_pipeline'),{'import_materials':False}),
            (pipeline.get_editor_property('material_pipeline').get_editor_property('texture_pipeline'),{'import_textures':False})]
        for obj,props in settings:
            for k,v in props.items():
                if new:obj.set_editor_property(k,v)
                require(obj.get_editor_property(k)==v,'Grass Interchange policy differs '+k)
        if new:self.save(pipeline)
        return pipeline

    def meshes(self,material,sources):
        u=self.u;pipeline=self.pipeline();registry=u.AssetRegistryHelpers.get_asset_registry();result={};proofs={}
        rows={p['id']:p for p in self.report['prototypes'] if p['id'] in IDS}
        for id_ in IDS:
            directory=self.prefix+'/Meshes/'+id_;paths=self.a.list_assets(directory,recursive=True,include_folder=False)
            if not paths:
                manager=u.InterchangeManager.get_interchange_manager_scripted();params=u.ImportAssetParameters()
                for k,v in {'is_automated':True,'replace_existing':False,'force_show_dialog':False,'override_pipelines':[u.SoftObjectPath(pipeline.get_path_name())]}.items():params.set_editor_property(k,v)
                require(manager.import_asset(directory,manager.create_source_data(str(self.prototype_dir/rows[id_]['file'])),params),'Grass GLB import failed')
                registry.scan_paths_synchronous([directory],force_rescan=True);paths=self.a.list_assets(directory,recursive=True,include_folder=False)
                require(len(paths)==1,'Unexpected assets produced by grass-only import')
                mesh=self.own(self.a.load_asset(paths[0]));require(isinstance(mesh,u.StaticMesh),'Grass import is not StaticMesh')
                self.a.set_metadata_tag(mesh,'BreziLawnPrototype',id_);self.a.set_metadata_tag(mesh,'source_sha256',rows[id_]['sha256'])
                mesh.set_material(0,material);mesh.set_editor_property('has_navigation_data',False);self.save(mesh)
            require(len(paths)==1,'Unexpected grass mesh directory inventory');mesh=self.existing(paths[0])
            require(self.a.get_metadata_tag(mesh,'BreziLawnPrototype')==id_ and self.a.get_metadata_tag(mesh,'source_sha256')==rows[id_]['sha256'],'Grass prototype ownership/source differs')
            proofs[id_]=mesh_proof(u,mesh,sources[id_],material);result[id_]=mesh
        return result,proofs
