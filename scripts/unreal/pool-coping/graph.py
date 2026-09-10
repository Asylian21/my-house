"""Signed planar PBR for the six axis-aligned faces of existing coping boxes."""
import hashlib,math
OWNER='scripts/unreal/pool-coping/coping.py'
PREFIX='/Game/Brezi/PoolCoping'
TAG='BreziPoolCopingRecipe'
ROLES={'albedo':('Diffuse','SAMPLERTYPE_COLOR'),'normalMap':('nor_gl','SAMPLERTYPE_NORMAL'),'roughMap':('Rough','SAMPLERTYPE_MASKS')}
BASIS='''float3 N = normalize(NormalWS);
float3 A = abs(N), T, B;
if (A.x >= A.y && A.x >= A.z) { float s = N.x < 0 ? -1 : 1; T=float3(0,1,0); B=float3(0,0,s); }
else if (A.y >= A.z) { float s = N.y < 0 ? -1 : 1; T=float3(1,0,0); B=float3(0,0,-s); }
else { float s = N.z < 0 ? -1 : 1; T=float3(1,0,0); B=float3(0,s,0); }
'''
CODES={
 'uv':BASIS+'return float2(dot(Position,T),dot(Position,B)) / PeriodCm;',
 'normal':BASIS+'return normalize(T*(MapNormal.x*Strength) + B*(MapNormal.y*Strength) + N*MapNormal.z);',
 'color':'return lerp(BaseColor, MapColor * Tint, Blend);',
 'roughness':'return clamp(Base + Amplitude * (MapR - Mean), Minimum, Maximum);',
}
CUSTOM={'uv':(['Position','NormalWS','PeriodCm'],'CMOT_FLOAT2'),'normal':(['MapNormal','NormalWS','Strength'],'CMOT_FLOAT3'),'color':(['BaseColor','MapColor','Tint','Blend'],'CMOT_FLOAT3'),'roughness':(['MapR','Base','Amplitude','Mean','Minimum','Maximum'],'CMOT_FLOAT1')}
LINKS=[('position','','uv','Position'),('normalWS','','uv','NormalWS'),('period','','uv','PeriodCm'),*[('uv','',r,'UVs') for r in ROLES],('normalMap','RGB','normal','MapNormal'),('normalWS','','normal','NormalWS'),('normalStrength','','normal','Strength'),('baseColor','','color','BaseColor'),('albedo','RGB','color','MapColor'),('tint','','color','Tint'),('albedoMix','','color','Blend'),('roughMap','R','roughness','MapR'),*[('rough'+role,'','roughness',pin) for role,pin in [('Base','Base'),('Amplitude','Amplitude'),('Mean','Mean'),('Min','Minimum'),('Max','Maximum')]]]
OUTPUTS=[('BASE_COLOR','color'),('NORMAL','normal'),('ROUGHNESS','roughness'),('METALLIC','metallic'),('SPECULAR','specular')]

def require(ok,message):
 if not ok:raise RuntimeError(message)
def out(v):return v[1] if isinstance(v,tuple) and len(v)==2 and v[0] is True else v
def srgb(v):return v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4
def validate_parameters(m):
 scalar=[m['tileMm'],m['normalStrength'],m['albedoMix'],m['metallic'],m['specular'],*m['roughness'].values(),*m['baseColorLinear'],*m['tintLinear']]
 require(all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in scalar),'Coping nonfinite material parameter')
 require(0<m['tileMm']<=10000 and 0<=m['normalStrength']<=1 and 0<=m['albedoMix']<=1 and m['metallic']==0 and m['specular']==.5 and m['geometryDisplacement'] is False,'Coping material/mapping policy differs')
 require(len(m['baseColorLinear'])==len(m['tintLinear'])==3 and all(abs(a-srgb(b/255))<1e-8 for a,b in zip(m['baseColorLinear'],(214,210,198))) and all(0<v<=4 for v in m['tintLinear']),'Coping declared source-color conversion/tint differs')
 r=m['roughness'];require(set(r)=={'base','amplitude','mapMean','min','max'} and r['base']==.9 and 0<=r['amplitude']<=1 and 0<=r['mapMean']<=1 and 0<=r['min']<=r['base']<=r['max']<=1,'Coping authored matte roughness policy differs')
 return True

def scalar_values(m):
 r=m['roughness'];return {'period':m['tileMm']/10,'normalStrength':m['normalStrength'],'albedoMix':m['albedoMix'],'roughBase':r['base'],'roughAmplitude':r['amplitude'],'roughMean':r['mapMean'],'roughMin':r['min'],'roughMax':r['max'],'metallic':0.,'specular':.5}
def vector_values(m):return {'baseColor':m['baseColorLinear'],'tint':m['tintLinear']}
def identity(u,material,contract):
 require(isinstance(material,u.Material) and material.get_path_name()==contract['materialPath'],'Coping material type/path differs')
 for k,v in {'BreziGeneratedBy':OWNER,TAG:contract['recipeSha256'],'source_material_slot':'MAT_0102'}.items():require(u.EditorAssetLibrary.get_metadata_tag(material,k)==v,'Coping material ownership differs: '+k)

def material_proof(u,material,contract,base):
 identity(u,material,contract);m=contract['reference']['material'];validate_parameters(m);lib=u.MaterialEditingLibrary;assets=u.EditorAssetLibrary
 for k,v in {'blend_mode':u.BlendMode.BLEND_OPAQUE,'shading_model':u.MaterialShadingModel.MSM_DEFAULT_LIT,'two_sided':False,'tangent_space_normal':False,'use_material_attributes':False}.items():require(material.get_editor_property(k)==v,'Coping surface policy differs: '+k)
 require(lib.has_material_usage(material,u.MaterialUsage.MATUSAGE_NANITE),'Coping Nanite usage absent')
 expressions=list(lib.get_material_expressions(material));nodes={str(assets.get_metadata_tag(n,'BreziOakNodeRole')):n for n in expressions}
 wanted={'position','normalWS',*ROLES,*CUSTOM,*scalar_values(m),*vector_values(m)}
 require(len(expressions)==len(nodes)==21 and set(nodes)==wanted,'Coping graph role/count differs')
 require(isinstance(nodes['position'],u.MaterialExpressionWorldPosition) and nodes['position'].get_editor_property('world_position_shader_offset')==u.WorldPositionIncludedOffsets.WPT_DEFAULT and isinstance(nodes['normalWS'],u.MaterialExpressionVertexNormalWS),'Coping position/normal source differs')
 for role,(names,typ) in CUSTOM.items():
  n=nodes[role];require(isinstance(n,u.MaterialExpressionCustom) and n.get_editor_property('code')==CODES[role] and [str(x.get_editor_property('input_name')) for x in n.get_editor_property('inputs')]==names and n.get_editor_property('output_type')==getattr(u.CustomMaterialOutputType,typ),'Coping custom code/interface differs: '+role)
 actual_scalars={};actual_vectors={}
 for role,v in scalar_values(m).items():
  n=nodes[role];require(isinstance(n,u.MaterialExpressionConstant) and abs(float(n.get_editor_property('r'))-v)<1e-6,'Coping scalar differs: '+role);actual_scalars[role]=float(n.get_editor_property('r'))
 for role,v in vector_values(m).items():
  n=nodes[role];require(isinstance(n,u.MaterialExpressionConstant3Vector),'Coping vector class differs');c=n.get_editor_property('constant');actual_vectors[role]=[float(getattr(c,k)) for k in ('r','g','b')];require(all(abs(a-b)<1e-6 for a,b in zip(actual_vectors[role],v)),'Coping vector differs: '+role)
 for origin,channel,target,pin in LINKS:
  names=list(map(str,lib.get_material_expression_input_names(nodes[target])));inputs=list(lib.get_inputs_for_material_expression(material,nodes[target]))
  require(len(names)==len(inputs) and pin in names and inputs[names.index(pin)]==nodes[origin],'Coping graph link differs: '+target+'.'+pin)
  require(out(lib.get_input_node_output_name_for_material_expression(nodes[target],nodes[origin]))==(channel or list(lib.get_material_expression_output_names(nodes[origin]))[0]),'Coping graph edge channel differs')
 for role,n in nodes.items():
  names=list(map(str,lib.get_material_expression_input_names(n)));inputs=list(lib.get_inputs_for_material_expression(material,n));expected={pin:nodes[a] for a,_,b,pin in LINKS if b==role}
  require(len(names)==len(inputs) and {k:v for k,v in zip(names,inputs) if v is not None}==expected,'Unexpected coping graph input: '+role)
 for prop,role in OUTPUTS:
  pid=getattr(u.MaterialProperty,'MP_'+prop);require(lib.get_material_property_input_node(material,pid)==nodes[role] and out(lib.get_material_property_input_node_output_name(material,pid))==list(lib.get_material_expression_output_names(nodes[role]))[0],'Coping material output differs: '+prop)
 for prop in ('WORLD_POSITION_OFFSET','OPACITY','OPACITY_MASK','EMISSIVE_COLOR','MATERIAL_ATTRIBUTES'):require(lib.get_material_property_input_node(material,getattr(u.MaterialProperty,'MP_'+prop)) is None,'Forbidden coping output: '+prop)
 require(u.BreziRendererSettingsAudit.has_no_pixel_depth_offset_connection(material),'Coping PDO connected')
 textures={}
 for role,(source,sampler) in ROLES.items():
  n=nodes[role];require(isinstance(n,u.MaterialExpressionTextureSample) and n.get_editor_property('sampler_type')==getattr(u.MaterialSamplerType,sampler) and n.get_editor_property('mip_value_mode')==u.TextureMipValueMode.TMVM_NONE and n.get_editor_property('automatic_view_mip_bias') is True and n.get_editor_property('sampler_source')==u.SamplerSourceMode.SSM_FROM_TEXTURE_ASSET,'Coping sampler/mip policy differs: '+role)
  textures[role]=base.texture_proof(u,n.get_editor_property('texture'),role,contract['candidate']['maps'][source]['sha256'],OWNER)
 return {'asset':material.get_path_name(),'recipeSha256':contract['recipeSha256'],'nodeCount':21,'linkCount':len(LINKS),'textureSampleCount':3,'exactGraphVerified':True,'allInputsAccountedFor':True,'nativeScalars':actual_scalars,'nativeVectors':actual_vectors,'parameters':m,'mapping':'signed-dominant-axis-world-planar','worldSpaceNormal':True,'sourceUvSampled':False,'normalGreenFlipCount':1,'normalShaderGreenFlipCount':0,'roughnessRemapped':True,'roughnessAuthoredNotMeasured':True,'albedoAuthoredColorConversion':True,'sourceScaleProvenance':contract['reference']['source']['physicalScaleProvenance'],'worldPositionOffsetConnected':False,'pixelDepthOffsetConnected':False,'implicitContinuousGradientsWithinEachPlanarFace':True,'stockAutomaticViewMipBias':True,'textures':textures,'shaderSha256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in CODES.items()},'renderedVerified':False,'residentMipsVerified':False,'nativeNormalTangentNumericProof':False}

def create_material(u,contract,base):
 m=contract['reference']['material'];validate_parameters(m);writer=base.Writer(u,contract['prefix'],contract,{'owner':OWNER,'materialName':'M_PoolCoping','palette':m['baseColorLinear'],'basisCode':BASIS})
 material=writer.existing(contract['materialPath'])
 if material:
  proof=material_proof(u,material,contract,base);return material.get_path_name(),{material.get_path_name(),*[v['asset'] for v in proof['textures'].values()]}
 material=u.AssetToolsHelpers.get_asset_tools().create_asset('M_PoolCoping',contract['prefix']+'/Materials',u.Material,u.MaterialFactoryNew());require(material is not None,'Coping material creation failed')
 for k,v in {'BreziGeneratedBy':OWNER,TAG:contract['recipeSha256'],'source_material_slot':'MAT_0102'}.items():writer.assets.set_metadata_tag(material,k,v)
 for k,v in {'blend_mode':u.BlendMode.BLEND_OPAQUE,'shading_model':u.MaterialShadingModel.MSM_DEFAULT_LIT,'two_sided':False,'tangent_space_normal':False,'use_material_attributes':False}.items():material.set_editor_property(k,v)
 writer.lib.set_base_material_usage(material,u.MaterialUsage.MATUSAGE_NANITE,True)
 writer.node(material,'position',u.MaterialExpressionWorldPosition,world_position_shader_offset=u.WorldPositionIncludedOffsets.WPT_DEFAULT);writer.node(material,'normalWS',u.MaterialExpressionVertexNormalWS)
 for role,v in scalar_values(m).items():writer.node(material,role,u.MaterialExpressionConstant,r=v)
 for role,v in vector_values(m).items():writer.node(material,role,u.MaterialExpressionConstant3Vector,constant=u.LinearColor(*v,1))
 for role,(names,typ) in CUSTOM.items():writer.custom(material,role,CODES[role],names,getattr(u.CustomMaterialOutputType,typ))
 for role,(source,sampler) in ROLES.items():writer.node(material,role,u.MaterialExpressionTextureSample,texture=writer.texture(role,source),sampler_type=getattr(u.MaterialSamplerType,sampler),mip_value_mode=u.TextureMipValueMode.TMVM_NONE,sampler_source=u.SamplerSourceMode.SSM_FROM_TEXTURE_ASSET,automatic_view_mip_bias=True)
 for origin,channel,target,pin in LINKS:
  names=list(map(str,writer.lib.get_material_expression_input_names(writer.nodes[target])));outputs=list(map(str,writer.lib.get_material_expression_output_names(writer.nodes[origin])));require(pin in names and (not channel or channel in outputs),'Coping reflected graph pin unavailable: '+target+'.'+pin)
 for a,channel,b,pin in LINKS:require(writer.lib.connect_material_expressions(writer.nodes[a],channel,writer.nodes[b],pin),'Coping graph connect failed')
 for prop,role in OUTPUTS:require(writer.lib.connect_material_property(writer.nodes[role],'',getattr(u.MaterialProperty,'MP_'+prop)),'Coping output connect failed')
 errors=list(writer.lib.recompile_material(material));require(not errors,'Coping material compile failed: '+str(errors));writer.save(material);material_proof(u,material,contract,base)
 return material.get_path_name(),set(writer.paths)
