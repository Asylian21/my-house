"""Eight-node opaque mulch graph. Native functions never launch the engine."""
import hashlib

OWNER='scripts/unreal/planting-surfaces/mulch.py'
PREFIX='/Game/Brezi/PlantingSurfaces/Mulch'
TAG='BreziMulchRecipe'
UV_CODE='return WorldPosition.xy / 200.0;'
NORMAL_CODE='return normalize(MapNormal);'
ROLES={'albedo':('Diffuse','SAMPLERTYPE_COLOR'), 'normalMap':('nor_gl','SAMPLERTYPE_NORMAL'), 'roughMap':('Rough','SAMPLERTYPE_MASKS')}
LINKS=[('position','','uv','WorldPosition'),*[('uv','',role,'UVs') for role in ROLES],('normalMap','RGB','normal','MapNormal')]
OUTPUTS=[('BASE_COLOR','albedo','RGB'),('NORMAL','normal',''),('ROUGHNESS','roughMap','R'),('METALLIC','metallic',''),('SPECULAR','specular','')]

def require(ok,message):
 if not ok:raise RuntimeError(message)
def out(v):return v[1] if isinstance(v,tuple) and len(v)==2 and v[0] is True else v
def identity(u,material,contract):
 require(isinstance(material,u.Material) and material.get_path_name()==contract['materialPath'],'Mulch material type/path differs')
 for k,v in {'BreziGeneratedBy':OWNER,TAG:contract['recipeSha256'],'source_material_slot':'MAT_0091'}.items():require(u.EditorAssetLibrary.get_metadata_tag(material,k)==v,'Mulch material ownership differs: '+k)

def material_proof(u,material,contract,base):
 identity(u,material,contract);lib=u.MaterialEditingLibrary;assets=u.EditorAssetLibrary
 for key,value in {'blend_mode':u.BlendMode.BLEND_OPAQUE,'shading_model':u.MaterialShadingModel.MSM_DEFAULT_LIT,'two_sided':False,'tangent_space_normal':False,'use_material_attributes':False}.items():require(material.get_editor_property(key)==value,'Mulch surface policy differs: '+key)
 require(lib.has_material_usage(material,u.MaterialUsage.MATUSAGE_NANITE),'Mulch Nanite usage absent')
 expressions=list(lib.get_material_expressions(material));nodes={str(assets.get_metadata_tag(n,'BreziOakNodeRole')):n for n in expressions}
 require(len(expressions)==len(nodes)==8 and set(nodes)=={'position','uv','normal','metallic','specular',*ROLES},'Mulch graph roles/count differ')
 require(isinstance(nodes['position'],u.MaterialExpressionWorldPosition) and nodes['position'].get_editor_property('world_position_shader_offset')==u.WorldPositionIncludedOffsets.WPT_DEFAULT,'Mulch absolute world input differs')
 for role,code,names,typ in [('uv',UV_CODE,['WorldPosition'],'CMOT_FLOAT2'),('normal',NORMAL_CODE,['MapNormal'],'CMOT_FLOAT3')]:
  n=nodes[role];require(isinstance(n,u.MaterialExpressionCustom) and n.get_editor_property('code')==code and [str(x.get_editor_property('input_name')) for x in n.get_editor_property('inputs')]==names and n.get_editor_property('output_type')==getattr(u.CustomMaterialOutputType,typ),'Mulch custom code/interface differs: '+role)
 for role,value in [('metallic',0.),('specular',.5)]:require(isinstance(nodes[role],u.MaterialExpressionConstant) and float(nodes[role].get_editor_property('r'))==value,'Mulch scalar differs: '+role)
 for origin,channel,target,pin in LINKS:
  names=list(map(str,lib.get_material_expression_input_names(nodes[target])));inputs=list(lib.get_inputs_for_material_expression(material,nodes[target]))
  require(len(names)==len(inputs) and pin in names and inputs[names.index(pin)]==nodes[origin],f'Mulch link differs: {origin}.{channel} -> {target}.{pin}; inputs={names}')
  require(out(lib.get_input_node_output_name_for_material_expression(nodes[target],nodes[origin]))==(channel or list(lib.get_material_expression_output_names(nodes[origin]))[0]),'Mulch link output channel differs')
 for role,n in nodes.items():
  names=list(map(str,lib.get_material_expression_input_names(n)));inputs=list(lib.get_inputs_for_material_expression(material,n));expected={pin:nodes[a] for a,_,b,pin in LINKS if b==role}
  require(len(names)==len(inputs) and {k:v for k,v in zip(names,inputs) if v is not None}==expected,'Unexpected mulch graph input: '+role)
 for prop,role,channel in OUTPUTS:
  pid=getattr(u.MaterialProperty,'MP_'+prop);require(lib.get_material_property_input_node(material,pid)==nodes[role] and out(lib.get_material_property_input_node_output_name(material,pid))==(channel or list(lib.get_material_expression_output_names(nodes[role]))[0]),'Mulch output differs: '+prop)
 for prop in ('WORLD_POSITION_OFFSET','OPACITY','OPACITY_MASK','EMISSIVE_COLOR'):require(lib.get_material_property_input_node(material,getattr(u.MaterialProperty,'MP_'+prop)) is None,'Forbidden mulch output: '+prop)
 require(u.BreziRendererSettingsAudit.has_no_pixel_depth_offset_connection(material),'Mulch PDO connected')
 textures={}
 for role,(source,sampler) in ROLES.items():
  n=nodes[role];require(isinstance(n,u.MaterialExpressionTextureSample) and n.get_editor_property('sampler_type')==getattr(u.MaterialSamplerType,sampler) and n.get_editor_property('mip_value_mode')==u.TextureMipValueMode.TMVM_NONE and n.get_editor_property('automatic_view_mip_bias') is True and n.get_editor_property('sampler_source')==u.SamplerSourceMode.SSM_FROM_TEXTURE_ASSET,'Mulch sampler/mip policy differs: '+role)
  textures[role]=base.texture_proof(u,n.get_editor_property('texture'),role,contract['candidate']['maps'][source]['sha256'],OWNER)
 return {'asset':material.get_path_name(),'recipeSha256':contract['recipeSha256'],'nodeCount':8,'linkCount':5,'textureSampleCount':3,'exactGraphVerified':True,'allInputsAccountedFor':True,'tileMm':2000,'worldSpaceNormal':True,'worldBasis':[[1,0,0],[0,1,0],[0,0,1]],'sourceUvSampled':False,'normalStrength':1,'normalGreenFlipCount':1,'roughnessRawLinear':True,'roughnessRemapped':False,'tintLinear':[1,1,1],'metallic':0,'specular':.5,'worldPositionOffsetConnected':False,'pixelDepthOffsetConnected':False,'implicitContinuousGradients':True,'stockAutomaticViewMipBias':True,'textures':textures,'shaderSha256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in {'uv':UV_CODE,'normal':NORMAL_CODE}.items()},'renderedVerified':False,'residentMipsVerified':False}

def create_material(u,contract,base):
 writer=base.Writer(u,contract['prefix'],contract,{'owner':OWNER,'materialName':'M_Mulch','palette':[1,1,1],'basisCode':'// +UE X,+UE Y,+UE Z: flat source bed top.'})
 material=writer.existing(contract['materialPath'])
 if material:
  proof=material_proof(u,material,contract,base);return material.get_path_name(),{material.get_path_name(),*[v['asset'] for v in proof['textures'].values()]}
 material=u.AssetToolsHelpers.get_asset_tools().create_asset('M_Mulch',contract['prefix']+'/Materials',u.Material,u.MaterialFactoryNew());require(material is not None,'Mulch material creation failed')
 for k,v in {'BreziGeneratedBy':OWNER,TAG:contract['recipeSha256'],'source_material_slot':'MAT_0091'}.items():writer.assets.set_metadata_tag(material,k,v)
 for k,v in {'blend_mode':u.BlendMode.BLEND_OPAQUE,'shading_model':u.MaterialShadingModel.MSM_DEFAULT_LIT,'two_sided':False,'tangent_space_normal':False,'use_material_attributes':False}.items():material.set_editor_property(k,v)
 writer.lib.set_base_material_usage(material,u.MaterialUsage.MATUSAGE_NANITE,True)
 writer.node(material,'position',u.MaterialExpressionWorldPosition,world_position_shader_offset=u.WorldPositionIncludedOffsets.WPT_DEFAULT)
 writer.custom(material,'uv',UV_CODE,['WorldPosition'],u.CustomMaterialOutputType.CMOT_FLOAT2)
 writer.custom(material,'normal',NORMAL_CODE,['MapNormal'],u.CustomMaterialOutputType.CMOT_FLOAT3)
 for role,(source,sampler) in ROLES.items():writer.node(material,role,u.MaterialExpressionTextureSample,texture=writer.texture(role,source),sampler_type=getattr(u.MaterialSamplerType,sampler),mip_value_mode=u.TextureMipValueMode.TMVM_NONE,sampler_source=u.SamplerSourceMode.SSM_FROM_TEXTURE_ASSET,automatic_view_mip_bias=True)
 for role,value in [('metallic',0.),('specular',.5)]:writer.node(material,role,u.MaterialExpressionConstant,r=value)
 for origin,channel,target,pin in LINKS:
  names=list(map(str,writer.lib.get_material_expression_input_names(writer.nodes[target])));outs=list(map(str,writer.lib.get_material_expression_output_names(writer.nodes[origin])))
  require(pin in names and (not channel or channel in outs),f'Mulch API pin absent: {origin}.{channel} -> {target}.{pin}; inputs={names}; outputs={outs}')
 for origin,channel,target,pin in LINKS:require(writer.lib.connect_material_expressions(writer.nodes[origin],channel,writer.nodes[target],pin),f'Mulch connection failed: {origin}.{channel} -> {target}.{pin}')
 for prop,role,channel in OUTPUTS:require(writer.lib.connect_material_property(writer.nodes[role],channel,getattr(u.MaterialProperty,'MP_'+prop)),'Mulch output connection failed: '+prop)
 errors=list(writer.lib.recompile_material(material));require(not errors,'Mulch compile failed: '+str(errors));writer.save(material);material_proof(u,material,contract,base)
 return material.get_path_name(),set(writer.paths)
