"""Bound R39 materials: three original-photo-map opaque/two-sided graphs.

The selected native scene/clone binding must authenticate before UObject
access. Eleven original published PNG alternatives remain pixel-unedited;
full source optical equivalence and actual GPU format are not asserted.
"""
import importlib.util
from pathlib import Path
import struct
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-neighbor-props-materials-r39.py'
SCHEMA='brezi-original-three-neighbor-prop-material-r39'
def module(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
SOURCE_CONTRACT=ROOT/'scripts/unreal/exterior-neighbor-props-contract-r39-draft.py'
SOURCE_CONTRACT_SHA='fdfa061438bff7bb93390d9ea6a9b0d6a758457b46647429ff33a489429581c5'
import hashlib
if hashlib.sha256(SOURCE_CONTRACT.read_bytes()).hexdigest()!=SOURCE_CONTRACT_SHA:
    raise RuntimeError('Frozen source-only R39 recipe contract changed')
c=module('_r39_original_material_source_contract',SOURCE_CONTRACT)
GUARD=ROOT/'scripts/unreal/exterior-neighbor-props-guards-r39.py'
def binding_guard():
    return module('_r39_actual_native_material_binding',GUARD)
def validate_binding(bundle,binding):
    g=binding_guard();g.require_native_binding(binding)
    c.require(set(bundle)=={'source','base','binding'} and bundle['binding']==binding,
      'Exact authenticated final source/base/native binding packet required')
    return bundle['source']
DELEGATE=ROOT/'scripts/unreal/exterior-garden-fern-materials-r25.py'
DELEGATE_SHA='07de6de2e384802228b6316a15aca0fe327525084eb9141615508b1040fda34f'
def api():
    c.require(c.sha(DELEGATE)==DELEGATE_SHA,'Frozen pure material API changed');return module('_r39_private_material_api',DELEGATE)
def preflight_enums(u):
    d=api();pairs=[('MaterialShadingModel','DEFAULTLIT'),('MaterialUsage','INSTANCEDSTATICMESHES'),('TextureCompressionSettings','TCDefault'),('TextureCompressionSettings','TCNormalmap'),('TextureCompressionSettings','TCMasks'),
      ('TextureSourceEncoding','TSESRGB'),('TextureSourceEncoding','TSENONE'),('MaterialSamplerType','SAMPLERTYPECOLOR'),('MaterialSamplerType','SAMPLERTYPENORMAL'),('MaterialSamplerType','SAMPLERTYPEMASKS')]
    result={g+'.'+n:str(d.enum(u,g,n))for g,n in pairs}
    for g,names in {'BlendMode':['BLEND_OPAQUE'],'TextureAddress':['TA_WRAP'],'TextureMipGenSettings':['TMGS_FROM_TEXTURE_GROUP'],'TexturePowerOfTwoSetting':['NONE'],
      'MaterialProperty':['MP_BASE_COLOR','MP_NORMAL','MP_ROUGHNESS','MP_METALLIC','MP_SPECULAR']}.items():
        for n in names:result[g+'.'+n]=str(getattr(getattr(u,g),n))
    return result

def png_header(row):
    p=c.checked(row);b=p.read_bytes()[:33];c.require(b[:8]==b'\x89PNG\r\n\x1a\n' and b[12:16]==b'IHDR','Untouched published PNG required')
    w,h,bits,color,compression,filtering,interlace=struct.unpack('>IIBBBBB',b[16:29]);c.require((w,h,bits)==(2048,2048,16) and compression==filtering==interlace==0,'Original source PNG encoding differs')
    return {'pixels':[w,h],'sourceBits':bits,'pngColorType':color,'nativeGpuPixelFormatVerified':False}
def assets(recipe):
    key=recipe['key'];base=c.PREFIX+'/'+key;material=base+'/Materials/M_'+key+'.M_'+key
    textures={r:base+'/Textures/T_'+r+'_'+p['sha256'][:16]+'.T_'+r+'_'+p['sha256'][:16]for r,p in recipe['maps'].items()}
    return material,textures

def validate_recipes(bundle):
    c.require(bundle['proposalPin']==c.pin(c.SOURCE) and bundle['proposalPin']['sha256']==c.SOURCE_SHA
      and set(bundle['recipes'])==set(c.MODEL_IDS),'Exact original three-model recipe closure required')
    for key,recipe in bundle['recipes'].items():
        c.require(recipe==c.material_recipe(bundle['proposal']['models'][key],bundle['receipt']),
          'Only the declared original PNG alternatives/core factors are allowed: '+key)
    packages=[a for recipe in bundle['recipes'].values()for a in [assets(recipe)[0],*assets(recipe)[1].values()]]
    c.require(len(packages)==len(set(packages))==14,'Three graphs and eleven untouched map objects required')
    return sorted(packages)

def validate_graph(graph,recipe,textures):
    d=api();tag=c.TAG+recipe['key']+':';nodes={v['role']:v for v in graph['nodes']};roles=['uv',*recipe['maps'],'specular']
    if not recipe['metallicFactor']:roles.append('metallic-zero')
    c.require(len(nodes)==len(graph['nodes'])==6 and set(nodes)=={tag+r for r in roles},'Exactly six owned expressions required')
    c.require(nodes[tag+'uv']['class']=='MaterialExpressionTextureCoordinate' and nodes[tag+'uv']['values']=={'coordinate_index':0,'u_tiling':1.,'v_tiling':1.},'Exact UV0 identity route required')
    roots={'BASE_COLOR':[tag+'albedo','RGB'],'NORMAL':[tag+'normalGL','RGB'],'ROUGHNESS':[tag+'roughness','R'],
      'METALLIC':[tag+'metallic','R']if recipe['metallicFactor']else[tag+'metallic-zero',''],'SPECULAR':[tag+'specular','']}
    c.require(all(graph['roots'][k]==v for k,v in roots.items())and all(v is None for k,v in graph['roots'].items()if k not in roots),'Only original five PBR roots; no AO/opacity/WPO permitted')
    for role in recipe['maps']:
        n=nodes[tag+role];sampler='SAMPLERTYPENORMAL'if role=='normalGL'else'SAMPLERTYPECOLOR'if role=='albedo'else'SAMPLERTYPEMASKS'
        c.require(n['class']=='MaterialExpressionTextureSample' and n['values']['texture']==textures[role]and d.token(n['values']['sampler_type'])==sampler
          and n['inputs']==[['UVs',tag+'uv',''],['Tex',None,None],['Apply View MipBias',None,None]],'Original map/UV0/sampler differs: '+role)
    c.require(nodes[tag+'specular']['class']=='MaterialExpressionConstant' and nodes[tag+'specular']['values']=={'r':d.f32(recipe['ueSpecular'])},'Declared specular F0 mapping differs')
    if not recipe['metallicFactor']:c.require(nodes[tag+'metallic-zero']['class']=='MaterialExpressionConstant' and nodes[tag+'metallic-zero']['values']=={'r':0.},'Original pot metallic zero required')
    return {'originalCorePbrFactorsRequested':True,'wholeSourceOpticalEquivalenceClaimed':False,'sourcePixelEdits':False,'opacityRoot':None,'aoRoot':None,'wpoRoot':None}

def _policy(u,role):
    d=api();return {'srgb':role=='albedo','flip_green_channel':role=='normalGL','compression_settings':d.enum(u,'TextureCompressionSettings',
      'TCNormalmap'if role=='normalGL'else'TCDefault'if role=='albedo'else'TCMasks'),'address_x':u.TextureAddress.TA_WRAP,'address_y':u.TextureAddress.TA_WRAP,
      'lod_bias':0,'max_texture_size':0,'virtual_texture_streaming':False,'never_stream':False,'mip_gen_settings':u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP,
      'power_of_two_mode':u.TexturePowerOfTwoSetting.NONE,'do_scale_mips_for_alpha_coverage':False,'alpha_coverage_thresholds':u.Vector4(0,0,0,0)}
def check_texture_policy(u,snapshot,role):
    for k,v in _policy(u,role).items():
        wanted=[float(getattr(v,a))for a in 'xyzw']if k=='alpha_coverage_thresholds'else v if isinstance(v,(bool,int,float,str))else str(v)
        c.require(snapshot['alphaCoverageThresholds'if k=='alpha_coverage_thresholds'else k]==wanted,'Original source map policy readback differs: '+role+'.'+k)
    c.require(snapshot['sourceEncoding']==str(api().enum(u,'TextureSourceEncoding','TSESRGB'if role=='albedo'else'TSENONE'))and snapshot['pixels']==[2048,2048],'Original encoding/size differs')

def check_material_policy(u,material):
    d=api();policy=d.material_policy(material)
    for k,v in {'blend_mode':str(u.BlendMode.BLEND_OPAQUE),'shading_model':str(d.enum(u,'MaterialShadingModel','DEFAULTLIT')),'two_sided':True,'tangent_space_normal':True,'use_material_attributes':False}.items():
        c.require(policy[k]==v,'Original opaque/two-sided material policy differs: '+k)
    return policy

def _metadata(u,obj,key,role,source=None,write=False):
    wanted={'BreziGeneratedBy':OWNER,'BreziR39SourceStudySha256':c.SOURCE_SHA,'BreziR39Model':key,'BreziR39Role':role,'BreziSourceLicense':'CC0-1.0'}
    if source is not None:wanted['source_sha256']=source['sha256']
    for k,v in wanted.items():
        if write:u.EditorAssetLibrary.set_metadata_tag(obj,k,v)
        c.require(u.EditorAssetLibrary.get_metadata_tag(obj,k)==v,'Owned material/map metadata differs')
    return wanted

def _build_kernel(u,bundle,graph_snapshot):
    # Future bound owner must validate its current scene/clone before invoking this kernel.
    package_assets=validate_recipes(bundle);preflight=preflight_enums(u);d=api();lib=u.MaterialEditingLibrary;ea=u.EditorAssetLibrary;result={};reports={}
    for key,recipe in bundle['recipes'].items():
        material_path,texture_paths=assets(recipe);textures={};texture_reports={}
        for role,source in recipe['maps'].items():
            source_header=png_header(source);package,name=texture_paths[role].rsplit('.',1);c.require(not ea.does_asset_exist(package),'Fresh own map namespace required')
            task=u.AssetImportTask()
            for k,v in {'filename':str(c.checked(source)),'destination_path':package.rsplit('/',1)[0],'destination_name':name,'automated':True,'replace_existing':False,'save':False}.items():task.set_editor_property(k,v)
            u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);texture=ea.load_asset(package);c.require(isinstance(texture,u.Texture2D)and texture.get_path_name()==texture_paths[role],'Original map import failed')
            for k,v in _policy(u,role).items():texture.set_editor_property(k,v)
            color=texture.get_editor_property('source_color_settings');color.set_editor_property('encoding_override',d.enum(u,'TextureSourceEncoding','TSESRGB'if role=='albedo'else'TSENONE'));texture.set_editor_property('source_color_settings',color)
            metadata=_metadata(u,texture,key,role,source,True);textures[role]=texture;texture_snapshot=d.texture_snapshot(texture);check_texture_policy(u,texture_snapshot,role);texture_reports[role]={'asset':texture_paths[role],'source':source,'sourcePng':source_header,'snapshot':texture_snapshot,'metadata':metadata}
        package,name=material_path.rsplit('.',1);c.require(not ea.does_asset_exist(package),'Fresh own material namespace required')
        material=u.AssetToolsHelpers.get_asset_tools().create_asset(name,package.rsplit('/',1)[0],u.Material,u.MaterialFactoryNew());c.require(isinstance(material,u.Material),'Cannot create owned prop graph')
        for k,v in {'blend_mode':u.BlendMode.BLEND_OPAQUE,'shading_model':d.enum(u,'MaterialShadingModel','DEFAULTLIT'),'two_sided':True,'tangent_space_normal':True,'use_material_attributes':False}.items():material.set_editor_property(k,v)
        lib.set_base_material_usage(material,d.enum(u,'MaterialUsage','INSTANCEDSTATICMESHES'),True)
        tag=c.TAG+key+':'
        def node(role,cls,**values):
            n=lib.create_material_expression(material,cls,-700,0);c.require(n,'Cannot create owned expression');n.set_editor_property('desc',tag+role)
            for k,v in values.items():n.set_editor_property(k,v)
            return n
        uv=node('uv',u.MaterialExpressionTextureCoordinate,coordinate_index=0,u_tiling=1.,v_tiling=1.);samples={}
        for role,texture in textures.items():
            sampler='SAMPLERTYPENORMAL'if role=='normalGL'else'SAMPLERTYPECOLOR'if role=='albedo'else'SAMPLERTYPEMASKS'
            samples[role]=node(role,u.MaterialExpressionTextureSample,texture=texture,sampler_type=d.enum(u,'MaterialSamplerType',sampler));c.require(lib.connect_material_expressions(uv,'',samples[role],'UVs'),'Cannot bind UV0')
        metallic=samples['metallic']if recipe['metallicFactor']else node('metallic-zero',u.MaterialExpressionConstant,r=0.)
        specular=node('specular',u.MaterialExpressionConstant,r=recipe['ueSpecular'])
        for n,channel,prop in [(samples['albedo'],'RGB','BASE_COLOR'),(samples['normalGL'],'RGB','NORMAL'),(samples['roughness'],'R','ROUGHNESS'),(metallic,'R'if recipe['metallicFactor']else'','METALLIC'),(specular,'','SPECULAR')]:
            c.require(lib.connect_material_property(n,channel,getattr(u.MaterialProperty,'MP_'+prop)),'Cannot bind owned PBR root')
        errors=list(lib.recompile_material(material)or[]);c.require(not errors,'Owned prop graph compile errors: '+str(errors));graph=graph_snapshot(u,material);audit=validate_graph(graph,recipe,texture_paths)
        metadata=_metadata(u,material,key,'material',write=True);result[key]=material;reports[key]={'asset':material_path,'recipe':recipe,'graph':graph,'graphSha256':c.digest(graph),
          'policy':check_material_policy(u,material),'textures':texture_reports,'metadata':metadata,'compileErrors':errors,'graphAudit':audit,
          'instancedStaticMeshUsage':bool(lib.has_material_usage(material,d.enum(u,'MaterialUsage','INSTANCEDSTATICMESHES')))}
        c.require(reports[key]['instancedStaticMeshUsage'] is True,'Actual owned prop HISM material usage required')
    report={'schema':SCHEMA,'owner':OWNER,'sourceStudy':bundle['proposalPin'],'materialCount':3,'textureObjectCount':11,'materials':reports,
      'nativeEnumPreflight':preflight,'newPackageAssets':package_assets,
      'nativeSourceTexelsDecoded':False,'sourcePngBitDepthDoesNotProveGpuFormat':True,'nativeGpuPixelFormatVerified':False,'nativeNormalTangentReadbackAvailable':False,
      'materialPackagesIndependentlyUnloaded':False,'sourceOpticalModelExactlyReproduced':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False}
    return result,report

def _verify_kernel(u,bundle,report,graph_snapshot):
    package_assets=validate_recipes(bundle)
    c.require(report['schema']==SCHEMA and report['owner']==OWNER and report['sourceStudy']==bundle['proposalPin']and set(report['materials'])==set(c.MODEL_IDS)
      and report['newPackageAssets']==package_assets and report['materialCount']==3 and report['textureObjectCount']==11,'Only own complete three-material receipt required')
    for key,value in {'nativeSourceTexelsDecoded':False,'sourcePngBitDepthDoesNotProveGpuFormat':True,
      'nativeGpuPixelFormatVerified':False,'nativeNormalTangentReadbackAvailable':False,
      'materialPackagesIndependentlyUnloaded':False,'sourceOpticalModelExactlyReproduced':False,
      'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False}.items():
        c.require(report[key] is value,'Owned material evidence limit changed: '+key)
    d=api();result={}
    for key,row in report['materials'].items():
        recipe=bundle['recipes'][key];path,textures=assets(recipe);c.require(row['asset']==path and row['recipe']==recipe and set(row['textures'])==set(textures),'Source recipe/material/map identity differs')
        m=u.EditorAssetLibrary.load_asset(path);c.require(isinstance(m,u.Material)and graph_snapshot(u,m)==row['graph']and c.digest(row['graph'])==row['graphSha256']and check_material_policy(u,m)==row['policy'],'Saved graph/settings differ')
        c.require(row['instancedStaticMeshUsage'] is True and u.MaterialEditingLibrary.has_material_usage(m,d.enum(u,'MaterialUsage','INSTANCEDSTATICMESHES')),
          'Saved owned prop HISM material usage differs')
        c.require(_metadata(u,m,key,'material')==row['metadata']and row['compileErrors']==[],'Saved owned material metadata differs');validate_graph(row['graph'],recipe,textures)
        for role,t in row['textures'].items():
            c.require(t['asset']==textures[role]and t['source']==recipe['maps'][role]and png_header(t['source'])==t['sourcePng'],'Original texture source differs')
            texture=u.EditorAssetLibrary.load_asset(t['asset']);c.require(isinstance(texture,u.Texture2D)and d.texture_snapshot(texture)==t['snapshot']and _metadata(u,texture,key,role,t['source'])==t['metadata'],'Saved map settings/metadata differ');check_texture_policy(u,t['snapshot'],role)
        result[key]=m
    return result

def build_materials(u,bundle,binding,graph_snapshot):
    source=validate_binding(bundle,binding)
    materials,report=_build_kernel(u,source,graph_snapshot)
    report['nativeBinding']=binding
    report['sourceRecipeContract']={'path':str(SOURCE_CONTRACT),'sha256':SOURCE_CONTRACT_SHA,'bytes':SOURCE_CONTRACT.stat().st_size}
    return materials,report

def verify_materials(u,bundle,binding,report,graph_snapshot):
    source=validate_binding(bundle,binding)
    c.require(report['nativeBinding']==binding and report['sourceRecipeContract']==c.pin(SOURCE_CONTRACT),
      'Saved owned material report native binding/source contract differs')
    return _verify_kernel(u,source,report,graph_snapshot)
