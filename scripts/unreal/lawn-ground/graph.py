"""Native graph construction/readback only; all entrypoints require caller scope."""
import hashlib, importlib.util
from pathlib import Path
HERE=Path(__file__).resolve().parent
OWNER='scripts/unreal/lawn-ground/lawn_ground.py'
PREFIX='/Game/Brezi/LawnGround'
RECIPE_TAG='BreziLawnGroundRecipe'
ROLES={'albedo':('Diffuse','SAMPLERTYPE_COLOR'),'normalMap':('nor_gl','SAMPLERTYPE_NORMAL'),'roughMap':('Rough','SAMPLERTYPE_MASKS')}
OUTPUTS=[('BASE_COLOR','tintedColor',''),('NORMAL','normal',''),('ROUGHNESS','roughness',''),('METALLIC','metallic',''),('SPECULAR','specular','')]

def require(value,message):
 if not value:raise RuntimeError(message)
def shader():
 spec=importlib.util.spec_from_file_location('brezi_lawn_ground_shader',HERE/'shading.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m
def out_name(value):return value[1] if isinstance(value,tuple) and len(value)==2 and value[0] is True else value

def links():
 r=[('uv0','','scaledUV','UV0')]
 r += [('scaledUV','',k,'UV') for k in ('weights','gradientX','gradientY','phase0','phase1','phase2')]
 for i in range(3):
  for role in ROLES:
   name=role+str(i)
   r += [('phase'+str(i),'',name,'UVs'),('gradientX','',name,'DDX(UVs)'),('gradientY','',name,'DDY(UVs)')]
   target={'albedo':'color','normalMap':'normal','roughMap':'roughness'}[role]
   r.append((name,'R' if role=='roughMap' else 'RGB',target,'ABC'[i]))
 r += [('weights','',k,'W') for k in ('color','normal','roughness')]
 return r+[('color','','tintedColor','A'),('artistTint','','tintedColor','B')]

def expected_roles():return {'uv0','artistTint','tintedColor','metallic','specular',*shader().CODES,*[r+str(i) for r in ROLES for i in range(3)]}

def material_identity(u,material,contract):
 a=u.EditorAssetLibrary
 require(isinstance(material,u.Material) and material.get_path_name()==contract['materialPath'] and a.get_metadata_tag(material,'BreziGeneratedBy')==OWNER and a.get_metadata_tag(material,RECIPE_TAG)==contract['recipeSha256'] and a.get_metadata_tag(material,'source_material_slot')=='MAT_0001','Lawn ground material identity/owner/recipe differs')

def material_proof(u,material,contract,base):
 lib,a,s=u.MaterialEditingLibrary,u.EditorAssetLibrary,shader()
 material_identity(u,material,contract)
 require(contract['reference']['material']['roughness']==s.ROUGHNESS_POLICY,'Lawn effective roughness contract differs')
 props={'blend_mode':u.BlendMode.BLEND_OPAQUE,'shading_model':u.MaterialShadingModel.MSM_DEFAULT_LIT,'two_sided':False,'tangent_space_normal':True,'use_material_attributes':False}
 for key,value in props.items():require(material.get_editor_property(key)==value,'Lawn material policy differs: '+key)
 require(lib.has_material_usage(material,u.MaterialUsage.MATUSAGE_NANITE),'Lawn material Nanite usage absent')
 expressions=list(lib.get_material_expressions(material));nodes={str(a.get_metadata_tag(n,'BreziOakNodeRole')):n for n in expressions}
 require(set(nodes)==expected_roles() and len(nodes)==len(expressions)==24,'Lawn graph exact node roles/count differs')
 require(isinstance(nodes['uv0'],u.MaterialExpressionTextureCoordinate),'UV0 node class differs')
 for k,v in {'coordinate_index':0,'u_tiling':1.,'v_tiling':1.,'un_mirror_u':False,'un_mirror_v':False}.items():require(nodes['uv0'].get_editor_property(k)==v,'UV0 input policy differs: '+k)
 require(isinstance(nodes['artistTint'],u.MaterialExpressionConstant3Vector) and isinstance(nodes['tintedColor'],u.MaterialExpressionMultiply),'Artist tint graph differs')
 color=nodes['artistTint'].get_editor_property('constant');tint=contract['reference']['material']['tintLinear']
 require([float(getattr(color,k)) for k in ('r','g','b')]==tint,'Artist tint values differ')
 for role,value in [('metallic',0.),('specular',.5)]:require(isinstance(nodes[role],u.MaterialExpressionConstant) and float(nodes[role].get_editor_property('r'))==value,'Lawn scalar differs: '+role)
 for role,code in s.CODES.items():
  n=nodes[role]
  require(isinstance(n,u.MaterialExpressionCustom) and n.get_editor_property('code')==code and [str(x.get_editor_property('input_name')) for x in n.get_editor_property('inputs')]==s.INPUTS[role] and n.get_editor_property('output_type')==getattr(u.CustomMaterialOutputType,s.OUTPUT_TYPES[role]),'Lawn custom code/input/output differs: '+role)
 for origin,output,target,pin in links():
  names=list(map(str,lib.get_material_expression_input_names(nodes[target])));inputs=list(lib.get_inputs_for_material_expression(material,nodes[target]))
  require(len(names)==len(inputs) and pin in names and inputs[names.index(pin)]==nodes[origin],f'Lawn graph link differs: {origin}.{output} -> {target}.{pin}; inputs={names}')
  expected=output or list(lib.get_material_expression_output_names(nodes[origin]))[0]
  require(out_name(lib.get_input_node_output_name_for_material_expression(nodes[target],nodes[origin]))==expected,'Lawn graph output channel differs: '+origin+' -> '+target)
 # No extra TextureObject/Apply View MipBias/custom connections may bypass the exact recipe.
 for role,n in nodes.items():
  names=list(map(str,lib.get_material_expression_input_names(n)));inputs=list(lib.get_inputs_for_material_expression(material,n))
  require(len(names)==len(inputs),'Lawn complete input readback differs: '+role)
  expected={pin:nodes[origin] for origin,output,target,pin in links() if target==role}
  require({name:node for name,node in zip(names,inputs) if node is not None}==expected,'Unexpected lawn graph input connection: '+role)
 for prop,role,channel in OUTPUTS:
  pid=getattr(u.MaterialProperty,'MP_'+prop)
  require(lib.get_material_property_input_node(material,pid)==nodes[role] and out_name(lib.get_material_property_input_node_output_name(material,pid))==(channel or list(lib.get_material_expression_output_names(nodes[role]))[0]),'Lawn material output differs: '+prop)
 for prop in ('WORLD_POSITION_OFFSET','OPACITY','OPACITY_MASK','EMISSIVE_COLOR'):
  require(lib.get_material_property_input_node(material,getattr(u.MaterialProperty,'MP_'+prop)) is None,'Forbidden lawn material output: '+prop)
 require(u.BreziRendererSettingsAudit.has_no_pixel_depth_offset_connection(material),'Lawn material PDO connection present or audit unavailable')
 textures={}
 for role,(source_role,sampler) in ROLES.items():
  for i in range(3):
   n=nodes[role+str(i)]
   require(isinstance(n,u.MaterialExpressionTextureSample) and n.get_editor_property('sampler_type')==getattr(u.MaterialSamplerType,sampler) and n.get_editor_property('mip_value_mode')==u.TextureMipValueMode.TMVM_DERIVATIVE,'Lawn sample mode differs')
   require(bool(n.get_editor_property('automatic_view_mip_bias')) is True and 'SSM_FROM_TEXTURE_ASSET' in str(n.get_editor_property('sampler_source')),'Lawn stock texture sampler/bias policy differs')
   p=base.texture_proof(u,n.get_editor_property('texture'),role,contract['candidate']['maps'][source_role]['sha256'],OWNER)
   if role in textures:require(p==textures[role],'Three lawn phases use different texture assets')
   textures[role]=p
 return {'asset':material.get_path_name(),'recipeSha256':contract['recipeSha256'],'nodeCount':24,'linkCount':len(links()),'exactGraphVerified':True,'textureSampleCount':9,'phaseCount':3,'allGraphInputsAccountedFor':True,'stockAutomaticViewMipBias':True,'samplerSource':'SSM_FROM_TEXTURE_ASSET','sameWeightsAndOffsetsAllMaps':True,'continuousUvGradients':True,'tangentSpaceNormal':True,'normalRotationApplied':False,'normalStrength':1,'roughnessInputMapLinear':True,'roughnessInputInvertGammaOrSquare':False,'roughnessRemapApplied':True,'effectiveRoughness':dict(s.ROUGHNESS_POLICY),'artistTintLinear':tint,'naniteUsage':True,'pixelDepthOffsetConnected':False,'worldPositionOffsetConnected':False,'textures':textures,'shaderSha256':{k:hashlib.sha256(v.encode()).hexdigest() for k,v in s.CODES.items()},'renderedVerified':False,'residentMipsVerified':False}

def create_material(u,contract,base):
 s=shader();prefix=contract['prefix'];writer=base.Writer(u,prefix,contract,{'owner':OWNER,'materialName':'M_LawnGround','palette':(1,1,1),'basisCode':'// Translation-only source UV0 basis.'})
 material=writer.existing(contract['materialPath'])
 if material:
  proof=material_proof(u,material,contract,base)
  return material.get_path_name(),{material.get_path_name(),*[v['asset'] for v in proof['textures'].values()]}
 material=u.AssetToolsHelpers.get_asset_tools().create_asset('M_LawnGround',prefix+'/Materials',u.Material,u.MaterialFactoryNew());require(material is not None,'Lawn ground material creation failed')
 for k,v in {'BreziGeneratedBy':OWNER,RECIPE_TAG:contract['recipeSha256'],'source_material_slot':'MAT_0001'}.items():writer.assets.set_metadata_tag(material,k,v)
 for k,v in {'blend_mode':u.BlendMode.BLEND_OPAQUE,'shading_model':u.MaterialShadingModel.MSM_DEFAULT_LIT,'two_sided':False,'tangent_space_normal':True,'use_material_attributes':False}.items():material.set_editor_property(k,v)
 writer.lib.set_base_material_usage(material,u.MaterialUsage.MATUSAGE_NANITE,True)
 writer.node(material,'uv0',u.MaterialExpressionTextureCoordinate,coordinate_index=0,u_tiling=1.,v_tiling=1.,un_mirror_u=False,un_mirror_v=False)
 for role,code in s.CODES.items():writer.custom(material,role,code,s.INPUTS[role],getattr(u.CustomMaterialOutputType,s.OUTPUT_TYPES[role]))
 for role,(source_role,sampler) in ROLES.items():
  texture=writer.texture(role,source_role)
  for i in range(3):writer.node(material,role+str(i),u.MaterialExpressionTextureSample,texture=texture,sampler_type=getattr(u.MaterialSamplerType,sampler),mip_value_mode=u.TextureMipValueMode.TMVM_DERIVATIVE)
 writer.node(material,'artistTint',u.MaterialExpressionConstant3Vector,constant=u.LinearColor(*contract['reference']['material']['tintLinear'],1))
 writer.node(material,'tintedColor',u.MaterialExpressionMultiply)
 for role,value in [('metallic',0.),('specular',.5)]:writer.node(material,role,u.MaterialExpressionConstant,r=value)
 # Preflight the exact public pins before connecting the first edge.
 for origin,output,target,pin in links():
  names=list(map(str,writer.lib.get_material_expression_input_names(writer.nodes[target])));outs=list(map(str,writer.lib.get_material_expression_output_names(writer.nodes[origin])))
  require(pin in names and (not output or output in outs),f'Lawn native API pins absent: {origin}.{output} -> {target}.{pin}; inputs={names}; outputs={outs}')
 for origin,output,target,pin in links():require(writer.lib.connect_material_expressions(writer.nodes[origin],output,writer.nodes[target],pin),f'Lawn connect failed: {origin}.{output} -> {target}.{pin}')
 for prop,role,channel in OUTPUTS:require(writer.lib.connect_material_property(writer.nodes[role],channel,getattr(u.MaterialProperty,'MP_'+prop)),'Lawn output connection failed: '+prop)
 errors=list(writer.lib.recompile_material(material));require(not errors,'Lawn native material compile failed: '+str(errors))
 writer.save(material);material_proof(u,material,contract,base)
 return material.get_path_name(),set(writer.paths)
