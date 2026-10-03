"""R23 original provider PBR maps; no source pixels or old assets are edited."""
import importlib.util
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-roof-pbr-materials.py'
PREFIX='/Game/Brezi/RoofPbr20261002R23'
TAG='BreziRoofPbrR23:'

def require(ok,message):
    if not ok:raise RuntimeError(message)
def token(value):return str(value).split('.')[1].split(':')[0].replace('_','').upper()
def native_enum(u,group,name):
    target=name.replace('_','').upper();prefix={'MaterialShadingModel':'MSM','MaterialUsage':'MATUSAGE'}.get(group,'');kind=getattr(u,group)
    def normalized(symbol):
        value=symbol.replace('_','').upper();return value[len(prefix):]if prefix and value.startswith(prefix)else value
    names=[n for n in dir(kind)if normalized(n)==target];require(len(names)==1,'Exact native enum missing/ambiguous: '+group+'.'+name);return getattr(kind,names[0])
def enum_preflight(u):
    requests={'TextureCompressionSettings':['TCDefault','TCNormalmap','TCMasks'],'TextureSourceEncoding':['TSESRGB','TSENONE'],
        'MaterialShadingModel':['DEFAULTLIT'],'MaterialUsage':['INSTANCEDSTATICMESHES'],
        'MaterialSamplerType':['SAMPLERTYPECOLOR','SAMPLERTYPENORMAL','SAMPLERTYPEMASKS']}
    result={g:{k:str(native_enum(u,g,k))for k in keys}for g,keys in requests.items()}
    direct={'TextureAddress':['TA_WRAP'],'TextureMipGenSettings':['TMGS_FROM_TEXTURE_GROUP'],'TexturePowerOfTwoSetting':['NONE'],
        'BlendMode':['BLEND_OPAQUE'],'MaterialProperty':['MP_BASE_COLOR','MP_NORMAL','MP_ROUGHNESS','MP_METALLIC','MP_SPECULAR']}
    for group,keys in direct.items():result[group]={k:str(getattr(getattr(u,group),k))for k in keys}
    return result

def texture_snapshot(tex):
    properties=('srgb','flip_green_channel','compression_settings','address_x','address_y','lod_bias','max_texture_size',
        'virtual_texture_streaming','mip_gen_settings','power_of_two_mode','never_stream','do_scale_mips_for_alpha_coverage')
    enum_keys={'compression_settings','address_x','address_y','mip_gen_settings','power_of_two_mode'}
    values={k:str(tex.get_editor_property(k))if k in enum_keys else tex.get_editor_property(k)for k in properties}
    values['sourceEncoding']=str(tex.get_editor_property('source_color_settings').get_editor_property('encoding_override'))
    values['pixels']=[int(tex.blueprint_get_size_x()),int(tex.blueprint_get_size_y())]
    values['alphaCoverageThresholds']=[float(getattr(tex.get_editor_property('alpha_coverage_thresholds'),a))for a in 'xyzw']
    return values

def verify_texture_snapshot(snapshot,role):
    require(snapshot['pixels']==[2048,2048]and snapshot['srgb']==(role=='albedo')and snapshot['flip_green_channel']==(role=='normal'),'Actual map size/color/normal convention differs')
    require(token(snapshot['compression_settings'])==('TCNORMALMAP'if role=='normal'else'TCMASKS'if role=='roughness'else'TCDEFAULT'),'Actual texture compression differs')
    require(token(snapshot['sourceEncoding'])==('TSESRGB'if role=='albedo'else'TSENONE'),'Source encoding differs')
    require(token(snapshot['address_x'])==token(snapshot['address_y'])=='TAWRAP'and token(snapshot['mip_gen_settings'])=='TMGSFROMTEXTUREGROUP'and token(snapshot['power_of_two_mode'])=='NONE','Texture repeat/mip interpretation differs')
    require(snapshot['lod_bias']==snapshot['max_texture_size']==0 and all(snapshot[k]is False for k in ('virtual_texture_streaming','never_stream','do_scale_mips_for_alpha_coverage'))and snapshot['alphaCoverageThresholds']==[0.,0.,0.,0.],'Unexpected texture processing/alpha/streaming override')

def verify_graph(graph,textures):
    require(set(textures)=={'albedo','normal','roughness'},'Exactly three provider maps required')
    roots=graph['roots'];wanted={'BASE_COLOR':[TAG+'albedo','RGB'],'NORMAL':[TAG+'normal','RGB'],
        'ROUGHNESS':[TAG+'roughness','R'],'METALLIC':[TAG+'metallic-zero',''],'SPECULAR':[TAG+'dielectric-specular','']}
    require(all(roots.get(k)==v for k,v in wanted.items())and all(v is None for k,v in roots.items()if k not in wanted),'Map roots include tint/AO/opacity/displacement or wrong channels')
    nodes={n['role']:n for n in graph['nodes']};require(len(nodes)==len(graph['nodes'])==6 and set(nodes)=={TAG+k for k in ['metric-uv0','albedo','normal','roughness','metallic-zero','dielectric-specular']},'Unexpected/missing PBR graph node')
    require(nodes[TAG+'metric-uv0']['class']=='MaterialExpressionTextureCoordinate'and nodes[TAG+'metric-uv0']['values']=={'coordinate_index':0,'u_tiling':.5,'v_tiling':.5},'2m physical period/UV0 changed')
    for role,asset in textures.items():
        n=nodes[TAG+role];require(n['class']=='MaterialExpressionTextureSample'and n['values']['texture']==asset and token(n['values']['sampler_type'])==('SAMPLERTYPENORMAL'if role=='normal'else'SAMPLERTYPEMASKS'if role=='roughness'else'SAMPLERTYPECOLOR'),'PBR sample binding/type differs')
        require(n['inputs']==[['UVs',TAG+'metric-uv0',''],['Tex',None,None],['Apply View MipBias',None,None]],'Original photographic UV route changed')
    for role,value in [('metallic-zero',0.),('dielectric-specular',.5)]:require(nodes[TAG+role]['class']=='MaterialExpressionConstant'and nodes[TAG+role]['values']=={'r':value}and nodes[TAG+role]['inputs']==[],'Dielectric scalar changed')
    flags=graph['flags'];require(token(flags['blend_mode'])=='BLENDOPAQUE'and token(flags['shading_model'])=='MSMDEFAULTLIT'and flags['two_sided']is False and flags['tangent_space_normal']is True and flags['use_material_attributes']is False,'Native physical Material flags differ')

def build(u,recipe,snapshot,plan_sha):
    proof=enum_preflight(u) # Complete enum surface resolves before any writes.
    assets=u.EditorAssetLibrary;lib=u.MaterialEditingLibrary;tools=u.AssetToolsHelpers.get_asset_tools();textures={};rows={}
    for role,source in recipe['maps'].items():
        name='T_R23_RoofTiles_'+role+'_'+source['sha256'][:16];path=PREFIX+'/Textures/'+name;require(not assets.does_asset_exist(path),'Fresh texture namespace required')
        task=u.AssetImportTask()
        for k,v in dict(filename=source['path'],destination_path=PREFIX+'/Textures',destination_name=name,automated=True,replace_existing=False,save=False).items():task.set_editor_property(k,v)
        tools.import_asset_tasks([task]);tex=assets.load_asset(path);require(isinstance(tex,u.Texture2D),'Provider map import failed')
        for k,v in {'srgb':role=='albedo','flip_green_channel':role=='normal','compression_settings':native_enum(u,'TextureCompressionSettings','TCNormalmap'if role=='normal'else'TCMasks'if role=='roughness'else'TCDefault'),
            'address_x':u.TextureAddress.TA_WRAP,'address_y':u.TextureAddress.TA_WRAP,'lod_bias':0,'max_texture_size':0,
            'virtual_texture_streaming':False,'never_stream':False,'mip_gen_settings':u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP,
            'power_of_two_mode':u.TexturePowerOfTwoSetting.NONE,'do_scale_mips_for_alpha_coverage':False,'alpha_coverage_thresholds':u.Vector4(0,0,0,0)}.items():tex.set_editor_property(k,v)
        color=tex.get_editor_property('source_color_settings');color.set_editor_property('encoding_override',native_enum(u,'TextureSourceEncoding','TSESRGB'if role=='albedo'else'TSENONE'));tex.set_editor_property('source_color_settings',color)
        for k,v in {'BreziGeneratedBy':OWNER,'source_sha256':source['sha256'],'BreziSourceLicense':'CC0-1.0','BreziSourcePage':recipe['sourcePage'],'BreziRoofRole':role,'BreziRoofPlanSha256':plan_sha}.items():assets.set_metadata_tag(tex,k,v)
        require(assets.save_loaded_asset(tex,False),'Cannot save own original-map texture');saved=texture_snapshot(tex);verify_texture_snapshot(saved,role)
        textures[role]=tex;rows[role]=dict(asset=tex.get_path_name(),source=source,snapshot=saved)
    name='M_roof_tiles_original';path=PREFIX+'/Materials/'+name;require(not assets.does_asset_exist(path),'Fresh roof Material namespace required')
    material=tools.create_asset(name,PREFIX+'/Materials',u.Material,u.MaterialFactoryNew());require(isinstance(material,u.Material),'Roof Material creation failed')
    for k,v in dict(blend_mode=u.BlendMode.BLEND_OPAQUE,shading_model=native_enum(u,'MaterialShadingModel','DEFAULTLIT'),two_sided=False,tangent_space_normal=True,use_material_attributes=False).items():material.set_editor_property(k,v)
    lib.set_base_material_usage(material,native_enum(u,'MaterialUsage','INSTANCEDSTATICMESHES'),True)
    def node(role,cls,**values):
        n=lib.create_material_expression(material,cls,-600,0);require(n,'PBR expression missing');n.set_editor_property('desc',TAG+role)
        for k,v in values.items():n.set_editor_property(k,v)
        return n
    uv=node('metric-uv0',u.MaterialExpressionTextureCoordinate,coordinate_index=0,u_tiling=.5,v_tiling=.5);samples={}
    for role,tex in textures.items():
        sample=node(role,u.MaterialExpressionTextureSample,texture=tex,sampler_type=native_enum(u,'MaterialSamplerType','SAMPLERTYPENORMAL'if role=='normal'else'SAMPLERTYPEMASKS'if role=='roughness'else'SAMPLERTYPECOLOR'))
        require(lib.connect_material_expressions(uv,'',sample,'UVs'),'Cannot connect metric UV0');samples[role]=sample
    zero=node('metallic-zero',u.MaterialExpressionConstant,r=0.);spec=node('dielectric-specular',u.MaterialExpressionConstant,r=.5)
    for n,channel,key in [(samples['albedo'],'RGB','BASE_COLOR'),(samples['normal'],'RGB','NORMAL'),(samples['roughness'],'R','ROUGHNESS'),(zero,'','METALLIC'),(spec,'','SPECULAR')]:require(lib.connect_material_property(n,channel,getattr(u.MaterialProperty,'MP_'+key)),'PBR property route failed')
    errors=list(lib.recompile_material(material)or[]);require(not errors,'Roof Material compile errors: '+str(errors))
    for k,v in {'BreziGeneratedBy':OWNER,'BreziRoofPlanSha256':plan_sha,'BreziRoofRecipe':json.dumps(recipe,sort_keys=True)}.items():assets.set_metadata_tag(material,k,v)
    require(assets.save_loaded_asset(material,False),'Cannot save own roof Material');graph=snapshot(u,material);verify_graph(graph,{r:t.get_path_name()for r,t in textures.items()})
    return material,dict(owner=OWNER,asset=material.get_path_name(),recipe=recipe,textures=rows,graph=graph,shaderCompileErrors=errors,nativeEnumPreflight=proof,nativeAppearanceAccepted=False)

def verify(u,report,snapshot,recipe,plan_sha):
    require(report['owner']==OWNER and report['recipe']==recipe and report['shaderCompileErrors']==[]and report['nativeAppearanceAccepted']is False and enum_preflight(u)==report['nativeEnumPreflight'],'Roof graph source/enum receipt changed')
    assets=u.EditorAssetLibrary;material=assets.load_asset(report['asset']);require(isinstance(material,u.Material),'Saved roof graph missing')
    graph=snapshot(u,material);require(graph==report['graph'],'Saved roof graph changed');verify_graph(graph,{k:r['asset']for k,r in report['textures'].items()})
    require(assets.get_metadata_tag(material,'BreziGeneratedBy')==OWNER and assets.get_metadata_tag(material,'BreziRoofPlanSha256')==plan_sha and assets.get_metadata_tag(material,'BreziRoofRecipe')==json.dumps(recipe,sort_keys=True),'Saved roof provenance changed')
    for role,row in report['textures'].items():
        tex=assets.load_asset(row['asset']);saved=texture_snapshot(tex);verify_texture_snapshot(saved,role)
        require(row['source']==recipe['maps'][role]and row['snapshot']==saved and assets.get_metadata_tag(tex,'source_sha256')==row['source']['sha256']and assets.get_metadata_tag(tex,'BreziGeneratedBy')==OWNER and assets.get_metadata_tag(tex,'BreziRoofRole')==role and assets.get_metadata_tag(tex,'BreziRoofPlanSha256')==plan_sha,'Saved original-map settings/provenance differs')
    return material
