"""R24 DRAFT: three original-provider material interpretations, ten own maps.

Photographic pixels and KHR UV mapping remain exact. Leaf BLEND→Masked is an
explicit UE interpretation; no realistic glass/tree/scan/performance claim.
"""
import importlib.util
import json
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-original-tree-materials.py'
PREFIX='/Game/Brezi/OriginalTree20261002R24'
TAG='BreziOriginalTreeR24:'
spec=importlib.util.spec_from_file_location('r24_owned_source_material_guards',ROOT/'scripts/unreal/exterior-original-tree-guards.py')
guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
require,pin,digest,sha=(getattr(guard,k)for k in ('require','pin','digest','sha'))


def f32(value):return struct.unpack('<f',struct.pack('<f',value))[0]
def token(value):return str(value).split('.')[1].split(':')[0].replace('_','').upper()


def enum(u,group,name):
    key=name.replace('_','').lower();prefix={'MaterialShadingModel':'msm','MaterialUsage':'matusage'}.get(group,'')
    def normalize(symbol):
        value=symbol.replace('_','').lower();return value[len(prefix):]if prefix and value.startswith(prefix)else value
    matches=[getattr(getattr(u,group),n)for n in dir(getattr(u,group))if normalize(n)==key]
    require(len(matches)==1,'Native enum missing/ambiguous '+group+'.'+name);return matches[0]


def validate_recipes(recipes,bundle=None):
    bundle=bundle or guard.load_source();require(recipes==bundle['recipes'] and len(recipes)==3,'Only frozen original three-section recipes may build')
    counts=0
    for index,row in enumerate(recipes):
        require(row['id']=='ph_original_tree_small_02_'+('branches','leaves','trunk')[index]+'_r24'
            and row['uvSet']==(1 if index==0 else 0)and row['nativeProposal']['metallicFactor']==0
            and row['nativeProposal']['worldPositionOffset']is None and row['nativeProposal']['occlusionRoot']is None,
            'Original UV/material roots changed')
        basis=row['nativeProposal']['normalTangentBasis'];require(basis['derivedAttribute']is True and basis['providerTangentAttribute']is False
            and basis['nativeImportRecomputeTangents']is False and basis['nativeImportRecomputeNormals']is False
            and basis['nativeTangentBasisVerified']is False,'Derived UV-specific basis must remain explicit/native-unverified')
        for map_ in row['sourceMaps'].values():guard.check_pin({'path':map_['path'],'sha256':map_['sha256'],'bytes':map_['bytes']});counts+=1
        if index==1:
            guard.check_pin({'path':row['alphaSource']['path'],'sha256':row['alphaSource']['sha256'],'bytes':row['alphaSource']['bytes']});counts+=1
            require(row['providerMaterial']['alphaMode']=='BLEND' and row['nativeProposal']['blendMode']=='MASKED'
                and row['nativeProposal']['opacityMask']=='Original published leaf alpha PNG.R','Explicit published leaf alpha conversion required')
    require(counts==10,'Exactly ten original maps required');return {'materials':3,'textures':10,'sourceOnly':True,'nativeAppearanceAccepted':False}


def texture_snapshot(tex):
    keys=('srgb','flip_green_channel','compression_settings','address_x','address_y','lod_bias','max_texture_size',
        'virtual_texture_streaming','never_stream','mip_gen_settings','power_of_two_mode','do_scale_mips_for_alpha_coverage')
    result={}
    for key in keys:
        value=tex.get_editor_property(key);result[key]=value if isinstance(value,(bool,int,float,str))else str(value)
    result['alphaCoverageThresholds']=[float(getattr(tex.get_editor_property('alpha_coverage_thresholds'),axis))for axis in 'xyzw']
    result['sourceEncoding']=str(tex.get_editor_property('source_color_settings').get_editor_property('encoding_override'))
    result['pixels']=[tex.blueprint_get_size_x(),tex.blueprint_get_size_y()];return result


def graph_snapshot(u,material,existing_graph_snapshot):
    graph=existing_graph_snapshot(u,material)
    # Historical snapshot has no Constant2Vector values. Record the two
    # reflected offset scalars explicitly for this owned graph only.
    offsets={str(n.get_editor_property('desc')):{k:float(n.get_editor_property(k))for k in ('r','g')}
        for n in u.MaterialEditingLibrary.get_material_expressions(material)if n.get_class().get_name()=='MaterialExpressionConstant2Vector'}
    for n in graph['nodes']:
        if n['role']in offsets:
            require(n['class']=='MaterialExpressionConstant2Vector'and n['role'].startswith(TAG),'Foreign UV offset expression')
            n['values']=offsets[n['role']]
    return graph


def check_graph(graph,recipe,texture_assets):
    leaf=recipe['alphaSource']is not None;branch=recipe['uvSet']==1;tag=TAG+recipe['id']+':'
    roots={'BASE_COLOR':[tag+'albedo','RGB'],'NORMAL':[tag+'normalGL','RGB'],'ROUGHNESS':[tag+'ARM','G'],
        'METALLIC':[tag+'metallic-factor',''],'SPECULAR':[tag+'dielectric-specular','']}
    if leaf:roots.update(OPACITY_MASK=[tag+'alpha','R'],SUBSURFACE_COLOR=[tag+'transmission',''])
    require(all(graph['roots'][key]==value for key,value in roots.items())
        and all(value is None for key,value in graph['roots'].items()if key not in roots),'Original explicit graph roots changed/extra AO or WPO route')
    nodes={n['role']:n for n in graph['nodes']};wanted={tag+k for k in ('uv','albedo','normalGL','ARM','metallic-factor','metallic-zero','dielectric-specular')}
    if branch:wanted|={tag+'KHR-offset',tag+'KHR-UV'}
    if leaf:wanted|={tag+'alpha',tag+'strength',tag+'transmission'}
    require(set(nodes)==wanted and len(nodes)==len(graph['nodes']),'Unexpected original tree graph node/duplicate role')
    uv=nodes[tag+'uv']['values'];transform=recipe['KHRTextureTransform']
    require(uv=={'coordinate_index':recipe['uvSet'],'u_tiling':f32(transform['scale'][0]),'v_tiling':f32(transform['scale'][1])},'Original UV set/scale changed')
    route=tag+'KHR-UV'if branch else tag+'uv'
    for role,path in texture_assets.items():
        n=nodes[tag+role];require(n['class']=='MaterialExpressionTextureSample'and n['values']['texture']==path
            and token(n['values']['sampler_type'])==('SAMPLERTYPENORMAL'if role=='normalGL'else'SAMPLERTYPEMASKS'if role in ('ARM','alpha')else'SAMPLERTYPECOLOR')
            and n['inputs']==[['UVs',route,''],['Tex',None,None],['Apply View MipBias',None,None]],'Original map/UV route changed')
    if branch:
        require(nodes[tag+'KHR-offset']['values']=={'r':f32(transform['offset'][0]),'g':f32(transform['offset'][1])}
            and nodes[tag+'KHR-UV']['inputs']==[['A',tag+'uv',''],['B',tag+'KHR-offset','']],'Original KHR offset route changed')
    require(nodes[tag+'metallic-factor']['inputs']==[['A',tag+'ARM','B'],['B',tag+'metallic-zero','']]
        and nodes[tag+'metallic-zero']['values']['r']==0. and nodes[tag+'dielectric-specular']['values']['r']==.5,'Provider metallic-zero/dielectric route changed')
    if leaf:require(nodes[tag+'strength']['values']['r']==f32(.08)
        and nodes[tag+'transmission']['inputs']==[['A',tag+'albedo','RGB'],['B',tag+'strength','']],'Explicit unaccepted foliage transmission changed')


def material_policy(u,material,recipe):
    leaf=recipe['alphaSource']is not None
    return {'blendMode':str(material.get_editor_property('blend_mode')),'shadingModel':str(material.get_editor_property('shading_model')),
        'twoSided':bool(material.get_editor_property('two_sided')),'tangentSpaceNormal':bool(material.get_editor_property('tangent_space_normal')),
        'useMaterialAttributes':bool(material.get_editor_property('use_material_attributes')),'opacityMaskClipValue':float(material.get_editor_property('opacity_mask_clip_value')),
        'naniteUsage':bool(u.MaterialEditingLibrary.has_material_usage(material,enum(u,'MaterialUsage','NANITE'))),
        'instancedStaticMeshUsage':bool(u.MaterialEditingLibrary.has_material_usage(material,enum(u,'MaterialUsage','INSTANCEDSTATICMESHES'))),
        'leafMaskedInterpretation':leaf,'nativeBasisReadbackAvailable':False}


def check_material_policy(u,material,recipe):
    leaf=recipe['alphaSource']is not None;actual=material_policy(u,material,recipe)
    require(actual=={'blendMode':str(u.BlendMode.BLEND_MASKED if leaf else u.BlendMode.BLEND_OPAQUE),
        'shadingModel':str(enum(u,'MaterialShadingModel','TWOSIDEDFOLIAGE'if leaf else'DEFAULTLIT')),
        'twoSided':True,'tangentSpaceNormal':True,'useMaterialAttributes':False,'opacityMaskClipValue':.5,
        'naniteUsage':True,'instancedStaticMeshUsage':True,'leafMaskedInterpretation':leaf,'nativeBasisReadbackAvailable':False},
        'Actual original-tree material policy/usage differs')
    return actual


def check_texture_policy(snapshot,role):
    require(snapshot['pixels']==[2048,2048]and snapshot['srgb']==(role=='albedo')and snapshot['flip_green_channel']==(role=='normalGL')
        and token(snapshot['compression_settings'])==('TCNORMALMAP'if role=='normalGL'else'TCMASKS'if role in ('ARM','alpha')else'TCDEFAULT')
        and token(snapshot['sourceEncoding'])==('TSESRGB'if role=='albedo'else'TSENONE'),'Original-tree native texture dimensions/optical interpretation differs')
    require(token(snapshot['address_x'])==token(snapshot['address_y'])=='TAWRAP'and token(snapshot['mip_gen_settings'])=='TMGSFROMTEXTUREGROUP'
        and token(snapshot['power_of_two_mode'])=='NONE'and snapshot['lod_bias']==snapshot['max_texture_size']==0
        and snapshot['virtual_texture_streaming']is False and snapshot['never_stream']is False
        and snapshot['do_scale_mips_for_alpha_coverage']==(role=='alpha')and snapshot['alphaCoverageThresholds']==([.5,0.,0.,0.]if role=='alpha'else[0.,0.,0.,0.]),
        'Original-tree native texture alpha/repeat/mip policy differs')


def build_materials(u,recipes,existing_graph_snapshot):
    validate_recipes(recipes);assets=u.EditorAssetLibrary;lib=u.MaterialEditingLibrary;native={};report={}
    # Resolve all enums before creating any owned asset.
    for group,name in [('TextureSourceEncoding','TSESRGB'),('TextureSourceEncoding','TSENONE'),('TextureCompressionSettings','TCDefault'),('TextureCompressionSettings','TCNormalmap'),('TextureCompressionSettings','TCMasks'),
        ('MaterialSamplerType','SAMPLERTYPECOLOR'),('MaterialSamplerType','SAMPLERTYPENORMAL'),('MaterialSamplerType','SAMPLERTYPEMASKS'),
        ('MaterialShadingModel','TWOSIDEDFOLIAGE'),('MaterialShadingModel','DEFAULTLIT'),('MaterialUsage','NANITE'),('MaterialUsage','INSTANCEDSTATICMESHES')]:enum(u,group,name)
    for recipe in recipes:
        leaf=recipe['alphaSource']is not None;branch=recipe['uvSet']==1;key=recipe['id'];tag=TAG+key+':'
        maps=dict(recipe['sourceMaps']);
        if leaf:maps['alpha']=recipe['alphaSource']
        textures={};texture_reports={}
        for role,row in maps.items():
            name='T_'+key+'_'+role+'_'+row['sha256'][:16];path=PREFIX+'/Textures/'+name
            require(not assets.does_asset_exist(path),'Fresh R24 map namespace required')
            task=u.AssetImportTask()
            for k,v in {'filename':row['path'],'destination_path':PREFIX+'/Textures','destination_name':name,'automated':True,'replace_existing':False,'save':False}.items():task.set_editor_property(k,v)
            u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);tex=assets.load_asset(path);require(isinstance(tex,u.Texture2D),'Cannot import original photographic map')
            for k,v in {'srgb':role=='albedo','flip_green_channel':role=='normalGL',
                'compression_settings':enum(u,'TextureCompressionSettings','TCNormalmap'if role=='normalGL'else'TCMasks'if role in ('ARM','alpha')else'TCDefault'),
                'address_x':u.TextureAddress.TA_WRAP,'address_y':u.TextureAddress.TA_WRAP,'lod_bias':0,'max_texture_size':0,
                'virtual_texture_streaming':False,'never_stream':False,'mip_gen_settings':u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP,
                'power_of_two_mode':u.TexturePowerOfTwoSetting.NONE,'do_scale_mips_for_alpha_coverage':role=='alpha',
                'alpha_coverage_thresholds':u.Vector4(.5,0,0,0)if role=='alpha'else u.Vector4(0,0,0,0)}.items():tex.set_editor_property(k,v)
            color=tex.get_editor_property('source_color_settings');color.set_editor_property('encoding_override',enum(u,'TextureSourceEncoding','TSESRGB'if role=='albedo'else'TSENONE'));tex.set_editor_property('source_color_settings',color)
            for k,v in {'BreziGeneratedBy':OWNER,'BreziR24SourceRole':role,'BreziSourceLicense':'CC0-1.0','BreziSourcePage':'https://polyhaven.com/a/tree_small_02','source_sha256':row['sha256']}.items():assets.set_metadata_tag(tex,k,v)
            require(assets.save_loaded_asset(tex,False),'Cannot save own original map');snapshot=texture_snapshot(tex);check_texture_policy(snapshot,role)
            textures[role]=tex;texture_reports[role]={'asset':tex.get_path_name(),'source':row,'snapshot':snapshot}
        name='M_'+key;require(not assets.does_asset_exist(PREFIX+'/Materials/'+name),'Fresh original tree graph namespace required')
        material=u.AssetToolsHelpers.get_asset_tools().create_asset(name,PREFIX+'/Materials',u.Material,u.MaterialFactoryNew());require(material,'Cannot create owned tree graph')
        for k,v in {'blend_mode':u.BlendMode.BLEND_MASKED if leaf else u.BlendMode.BLEND_OPAQUE,
            'shading_model':enum(u,'MaterialShadingModel','TWOSIDEDFOLIAGE'if leaf else'DEFAULTLIT'),'two_sided':True,
            'tangent_space_normal':True,'use_material_attributes':False,'opacity_mask_clip_value':.5}.items():material.set_editor_property(k,v)
        lib.set_base_material_usage(material,enum(u,'MaterialUsage','NANITE'),True)
        lib.set_base_material_usage(material,enum(u,'MaterialUsage','INSTANCEDSTATICMESHES'),True)
        def node(role,cls,**values):
            n=lib.create_material_expression(material,cls,-700,0);require(n,'Cannot create original tree expression');n.set_editor_property('desc',tag+role)
            for k,v in values.items():n.set_editor_property(k,v)
            return n
        def connect(a,channel,b,input_):require(lib.connect_material_expressions(a,channel,b,input_),'Cannot connect original tree graph')
        def root(a,channel,property_):require(lib.connect_material_property(a,channel,getattr(u.MaterialProperty,'MP_'+property_)),'Cannot bind original tree root')
        transform=recipe['KHRTextureTransform'];uv=node('uv',u.MaterialExpressionTextureCoordinate,coordinate_index=recipe['uvSet'],u_tiling=transform['scale'][0],v_tiling=transform['scale'][1]);route=uv
        if branch:
            offset=node('KHR-offset',u.MaterialExpressionConstant2Vector,r=transform['offset'][0],g=transform['offset'][1]);route=node('KHR-UV',u.MaterialExpressionAdd);connect(uv,'',route,'A');connect(offset,'',route,'B')
        samples={}
        for role,texture in textures.items():
            sample=node(role,u.MaterialExpressionTextureSample,texture=texture,sampler_type=enum(u,'MaterialSamplerType','SAMPLERTYPENORMAL'if role=='normalGL'else'SAMPLERTYPEMASKS'if role in ('ARM','alpha')else'SAMPLERTYPECOLOR'));connect(route,'',sample,'UVs');samples[role]=sample
        zero=node('metallic-zero',u.MaterialExpressionConstant,r=0.);metal=node('metallic-factor',u.MaterialExpressionMultiply);connect(samples['ARM'],'B',metal,'A');connect(zero,'',metal,'B')
        specular=node('dielectric-specular',u.MaterialExpressionConstant,r=.5)
        for n,channel,property_ in [(samples['albedo'],'RGB','BASE_COLOR'),(samples['normalGL'],'RGB','NORMAL'),(samples['ARM'],'G','ROUGHNESS'),(metal,'','METALLIC'),(specular,'','SPECULAR')]:root(n,channel,property_)
        if leaf:
            strength=node('strength',u.MaterialExpressionConstant,r=.08);transmission=node('transmission',u.MaterialExpressionMultiply);connect(samples['albedo'],'RGB',transmission,'A');connect(strength,'',transmission,'B');root(transmission,'','SUBSURFACE_COLOR');root(samples['alpha'],'R','OPACITY_MASK')
        errors=list(lib.recompile_material(material)or[]);require(not errors,'Original tree shader compile errors: '+str(errors))
        graph=graph_snapshot(u,material,existing_graph_snapshot);check_graph(graph,recipe,{k:v.get_path_name()for k,v in textures.items()})
        assets.set_metadata_tag(material,'BreziGeneratedBy',OWNER);assets.set_metadata_tag(material,'BreziR24Recipe',json.dumps(recipe,sort_keys=True));require(assets.save_loaded_asset(material,False),'Cannot save original tree graph')
        native[key]=material;report[key]={'asset':material.get_path_name(),'recipe':recipe,'graph':graph,'policy':check_material_policy(u,material,recipe),'textures':texture_reports,'compileErrors':errors}
    return native,{'owner':OWNER,'materials':report,'materialCount':3,'textureCount':10,'nativeAppearanceAccepted':False,'nativeNormalTangentReadbackAvailable':False}


def verify_materials(u,report,existing_graph_snapshot):
    require(report['owner']==OWNER and report['materialCount']==3 and report['textureCount']==10,'Typed three-graph/ten-map receipt required')
    recipes=[r['recipe']for r in report['materials'].values()];validate_recipes(recipes);native={}
    for key,row in report['materials'].items():
        material=u.EditorAssetLibrary.load_asset(row['asset']);require(isinstance(material,u.Material)and row['asset']==PREFIX+'/Materials/M_'+key+'.M_'+key,'Saved owned tree material missing/foreign')
        require(graph_snapshot(u,material,existing_graph_snapshot)==row['graph']and check_material_policy(u,material,row['recipe'])==row['policy']and row['compileErrors']==[],'Saved graph/material policy changed')
        require(u.EditorAssetLibrary.get_metadata_tag(material,'BreziGeneratedBy')==OWNER and u.EditorAssetLibrary.get_metadata_tag(material,'BreziR24Recipe')==json.dumps(row['recipe'],sort_keys=True),'Saved original tree recipe provenance changed')
        for role,value in row['textures'].items():
            tex=u.EditorAssetLibrary.load_asset(value['asset']);require(isinstance(tex,u.Texture2D)and texture_snapshot(tex)==value['snapshot'],'Saved original map settings changed')
            check_texture_policy(value['snapshot'],role)
            require(u.EditorAssetLibrary.get_metadata_tag(tex,'BreziGeneratedBy')==OWNER and u.EditorAssetLibrary.get_metadata_tag(tex,'source_sha256')==value['source']['sha256']and u.EditorAssetLibrary.get_metadata_tag(tex,'BreziR24SourceRole')==role,'Saved original map provenance changed')
        check_graph(row['graph'],row['recipe'],{k:v['asset']for k,v in row['textures'].items()});native[key]=material
    return native
