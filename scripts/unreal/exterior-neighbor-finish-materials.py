"""R18-only material graphs. Old materials/textures are loaded read-only.

The frozen R1 recipes remain untouched. Glass opacity .08 and forward surface
lighting are explicit new native implementation parameters, not observed glass.
"""
import hashlib
import json
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-neighbor-finish-materials.py'
PREFIX='/Game/Brezi/NeighborFinish20261001R18'
TAG='BreziNeighborR18:'
GLASS_OPACITY=.08

PLASTER_COLOR='''float3 scan=clamp(MapAlbedo/max(MeanAlbedo,.01),.35,1.8);
float h=max(Position.z-GroundZ,0.); float low=1-smoothstep(0.,AgeHeight,h);
float varied=.55+.45*sin(Position.x*.071+Position.y*.047)*sin(Position.x*.019-Position.y*.027);
return Palette*(1+Contrast*(scan-1))*(1-Darkening*low*varied);'''
PLASTER_ROUGH='return clamp(Base+Amplitude*(MapRoughness-Mean)+.035*(1-smoothstep(0.,AgeHeight,max(Position.z-GroundZ,0.))),.05,.99);'
PLASTER_NORMAL='return normalize(float3(MapNormal.xy*Strength,max(.05,MapNormal.z)));'
ROOF_COLOR='''float2 cm=UV*100.;float course=floor(cm.y/CourseCm);
float2 local=float2(frac(cm.x/WidthCm+.5*fmod(course,2.)),frac(cm.y/CourseCm));
float joint=(1-smoothstep(.012,.045,min(local.x,1-local.x)))*.09;
float phase=sin(course*2.718+floor(cm.x/WidthCm)*1.414)*.5+.5;
return Palette*(1+Variation*(phase-.5)-joint);'''
ROOF_NORMAL='''float2 cm=UV*100.;float course=floor(cm.y/CourseCm);
float x=frac(cm.x/WidthCm+.5*fmod(course,2.));float y=frac(cm.y/CourseCm);
float sx=6.28318530718*ReliefCm/WidthCm*cos(x*6.28318530718);
float sy=(y>.92?-.5: .06)*ReliefCm;
return normalize(float3(-sx,sy,1.));'''
ROOF_ROUGH='float2 cm=UV*100.;return clamp(Base+Variation*sin(floor(cm.x/WidthCm)*1.414+floor(cm.y/CourseCm)*2.718),.1,.99);'


def require(ok,message):
    if not ok:raise ValueError(message)


def stored_float(v):return struct.unpack('<f',struct.pack('<f',v))[0]


def glass_optical_values(snapshot):
    nodes={row['role']:row for row in snapshot['nodes']};values={}
    for name,root,role in [('metallic','METALLIC','dielectric-metallic'),('roughness','ROUGHNESS','roughness-base'),
                            ('opacity','OPACITY','proposed-thin-glass-opacity'),('indexOfRefraction','REFRACTION','proposed-glass-ior')]:
        require(snapshot['roots'][root][0]==TAG+role,'Saved glass optical root differs: '+root)
        values[name]=nodes[TAG+role]['values']['r']
    require(values=={'metallic':0.,'roughness':stored_float(.12),'opacity':stored_float(GLASS_OPACITY),'indexOfRefraction':1.5},'Saved native glass optical scalar values differ')
    values.update(refractionMethod=snapshot['flags']['refraction_method'],blendMode=snapshot['flags']['blend_mode'],
                  translucencyLightingMode=snapshot['flags']['translucency_lighting_mode'])
    return values


def enum(u,group,name):
    target=name.replace('_','').lower();kind=getattr(u,group)
    matches=[getattr(kind,n) for n in dir(kind) if n.replace('_','').lower()==target]
    require(len(matches)==1,'Installed native enum unavailable/ambiguous: '+group+'.'+name)
    return matches[0]


def texture_snapshot(tex):
    properties=('srgb','flip_green_channel','compression_settings','address_x','address_y','lod_bias',
                'max_texture_size','virtual_texture_streaming','mip_gen_settings','power_of_two_mode','never_stream')
    values={k:str(tex.get_editor_property(k)) if k in {'compression_settings','address_x','address_y','mip_gen_settings','power_of_two_mode'} else tex.get_editor_property(k) for k in properties}
    values['source_encoding']=str(tex.get_editor_property('source_color_settings').get_editor_property('encoding_override'))
    values['pixels']=[int(tex.blueprint_get_size_x()),int(tex.blueprint_get_size_y())]
    return values


def graph_snapshot(u,material,existing_snapshot):
    result=existing_snapshot(u,material)
    node=u.MaterialEditingLibrary.get_material_property_input_node(material,u.MaterialProperty.MP_REFRACTION)
    result['roots']['REFRACTION']=[str(node.get_editor_property('desc')),str(u.MaterialEditingLibrary.get_material_property_input_node_output_name(material,u.MaterialProperty.MP_REFRACTION))] if node else None
    result['flags']['translucency_lighting_mode']=str(material.get_editor_property('translucency_lighting_mode'))
    result['flags']['refraction_method']=str(material.get_editor_property('refraction_method'))
    nodes={n['role']:n for n in result['nodes']}
    for expression in u.MaterialEditingLibrary.get_material_expressions(material):
        if isinstance(expression,u.MaterialExpressionWorldPosition):
            desc=str(expression.get_editor_property('desc'))
            require(desc in nodes,'WorldPosition expression omitted from graph snapshot')
            nodes[desc]['values']['world_position_shader_offset']=str(expression.get_editor_property('world_position_shader_offset'))
    return result


class Writer:
    def __init__(self,u,existing_snapshot):
        self.u=u;self.assets=u.EditorAssetLibrary;self.lib=u.MaterialEditingLibrary
        self.existing_snapshot=existing_snapshot;self.textures={};self.texture_reports={}

    def node(self,m,role,cls,**props):
        node=self.lib.create_material_expression(m,cls,-600,0);require(node,'Cannot create R18 expression: '+role)
        node.set_editor_property('desc',TAG+role)
        for k,v in props.items():node.set_editor_property(k,v)
        return node

    def scalar(self,m,role,v):return self.node(m,role,self.u.MaterialExpressionConstant,r=float(v))
    def vector(self,m,role,v):return self.node(m,role,self.u.MaterialExpressionConstant3Vector,constant=self.u.LinearColor(*v,1))
    def out(self,node,property_name,channel=''):require(self.lib.connect_material_property(node,channel,getattr(self.u.MaterialProperty,'MP_'+property_name)),'R18 material root connection failed: '+property_name)
    def connect(self,a,channel,b,pin):require(self.lib.connect_material_expressions(a,channel,b,pin),'R18 material connection failed: '+pin)

    def custom(self,m,role,code,inputs,width=3):
        pins=[]
        for name in inputs:
            pin=self.u.CustomInput();pin.set_editor_property('input_name',name);pins.append(pin)
        node=self.node(m,role,self.u.MaterialExpressionCustom,code=code,description=TAG+role,inputs=pins,
                       output_type=getattr(self.u.CustomMaterialOutputType,'CMOT_FLOAT'+str(width)))
        for name,(source,channel) in inputs.items():self.connect(source,channel,node,name)
        return node

    def texture(self,role,spec):
        if role in self.textures:return self.textures[role]
        u=self.u;name='T_R18_Plaster_'+role+'_'+spec['sha256'][:16];path=PREFIX+'/Textures/'+name
        require(not self.assets.does_asset_exist(path),'Fresh R18 texture namespace required')
        source=(ROOT/spec['path']).resolve();require(hashlib.sha256(source.read_bytes()).hexdigest()==spec['sha256'],'R18 local texture source drift')
        task=u.AssetImportTask()
        for key,value in {'filename':str(source),'destination_path':PREFIX+'/Textures','destination_name':name,'automated':True,'replace_existing':False,'save':False}.items():task.set_editor_property(key,value)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);tex=self.assets.load_asset(path)
        require(isinstance(tex,u.Texture2D),'R18 texture import failed')
        compression=enum(u,'TextureCompressionSettings','TCNormalmap' if role=='normal' else 'TCMasks' if role=='roughness' else 'TCDefault')
        for key,value in {'srgb':role=='albedo','flip_green_channel':role=='normal','compression_settings':compression,
                          'address_x':u.TextureAddress.TA_WRAP,'address_y':u.TextureAddress.TA_WRAP,'lod_bias':0,
                          'max_texture_size':0,'virtual_texture_streaming':False,'never_stream':False,
                          'mip_gen_settings':u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP,
                          'power_of_two_mode':u.TexturePowerOfTwoSetting.NONE}.items():tex.set_editor_property(key,value)
        color=tex.get_editor_property('source_color_settings');color.set_editor_property('encoding_override',enum(u,'TextureSourceEncoding','TSESRGB' if role=='albedo' else 'TSENONE'));tex.set_editor_property('source_color_settings',color)
        for key,value in {'BreziGeneratedBy':OWNER,'source_sha256':spec['sha256'],'BreziSourceLicense':'CC0-1.0','BreziSourcePage':'https://polyhaven.com/a/white_plaster_02'}.items():self.assets.set_metadata_tag(tex,key,value)
        require(self.assets.save_loaded_asset(tex,only_if_is_dirty=False),'Cannot save new R18 texture')
        snapshot=texture_snapshot(tex);require(snapshot['pixels']==[2048,2048],'R18 texture resolution differs')
        self.textures[role]=tex;self.texture_reports[role]={'asset':tex.get_path_name(),'sourcePath':str(source),'sourceSha256':spec['sha256'],'sourceRole':role,'snapshot':snapshot}
        return tex

    def sample(self,m,role,spec,uv):
        sampler=enum(self.u,'MaterialSamplerType','SAMPLERTYPENORMAL' if role=='normal' else 'SAMPLERTYPEMASKS' if role=='roughness' else 'SAMPLERTYPECOLOR')
        node=self.node(m,'plaster-'+role,self.u.MaterialExpressionTextureSample,texture=self.texture(role,spec),sampler_type=sampler)
        self.connect(uv,'',node,'UVs');return node

    def create(self,key,recipe):
        u=self.u;path=PREFIX+'/Materials/M_'+key;require(not self.assets.does_asset_exist(path),'Fresh R18 material namespace required')
        material=u.AssetToolsHelpers.get_asset_tools().create_asset('M_'+key,PREFIX+'/Materials',u.Material,u.MaterialFactoryNew());require(material,'Cannot create R18 material')
        glass=recipe['kind']=='neighbor-window-dielectric'
        for name,value in {'blend_mode':u.BlendMode.BLEND_TRANSLUCENT if glass else u.BlendMode.BLEND_OPAQUE,
                           'shading_model':u.MaterialShadingModel.MSM_DEFAULT_LIT,'two_sided':False,
                           'tangent_space_normal':True,'use_material_attributes':False}.items():material.set_editor_property(name,value)
        if glass:
            material.set_editor_property('translucency_lighting_mode',enum(u,'TranslucencyLightingMode','TLMSurfacePerPixelLighting'))
            material.set_editor_property('refraction_method',enum(u,'RefractionMode','RMIndexOfRefraction'))
        uv=self.node(material,'metric-UV0',u.MaterialExpressionTextureCoordinate,coordinate_index=0,u_tiling=1.,v_tiling=1.)
        kind=recipe['kind'];normal=self.vector(material,'flat-tangent-normal',[0,0,1]);specular=recipe.get('specular',.3)
        if kind=='neighbor-plaster-scan':
            require(recipe['periodCm']==100 and recipe['normalConvention']=='OPENGL_GREEN_POSITIVE_V','Native plaster mapping/convention differs')
            samples={role:self.sample(material,role,spec,uv) for role,spec in recipe['maps'].items()}
            position=self.node(material,'source-ground-aging-position',u.MaterialExpressionWorldPosition,
                               world_position_shader_offset=enum(u,'WorldPositionIncludedOffsets','WPTDefault'))
            ground=sum(r['renderedGroundZCm'] for r in recipe['aging']['sourceGroundSamples'])/len(recipe['aging']['sourceGroundSamples'])
            common={'Position':(position,''),'GroundZ':(self.scalar(material,'source-sampled-ground-z',ground),''),
                    'AgeHeight':(self.scalar(material,'authored-aging-height',recipe['aging']['heightCm']),'')}
            color=self.custom(material,'photographic-plaster-basecolor',PLASTER_COLOR,{**common,'MapAlbedo':(samples['albedo'],''),
                'MeanAlbedo':(self.vector(material,'source-map-linear-mean',recipe['maps']['albedo']['meanLinearRGB']),''),
                'Palette':(self.vector(material,'authored-plaster-palette',recipe['linearPalette']),''),
                'Contrast':(self.scalar(material,'photographic-contrast',recipe['albedoContrast']),''),
                'Darkening':(self.scalar(material,'authored-ground-aging-darkening',recipe['aging']['maximumAlbedoDarkening']),'')})
            normal=self.custom(material,'photographic-plaster-normal',PLASTER_NORMAL,{'MapNormal':(samples['normal'],''),'Strength':(self.scalar(material,'normal-strength',recipe['normalStrength']),'')})
            rough=self.custom(material,'photographic-plaster-roughness',PLASTER_ROUGH,{**common,'MapRoughness':(samples['roughness'],'R'),
                 'Base':(self.scalar(material,'roughness-base',recipe['roughnessBase']),''),'Amplitude':(self.scalar(material,'roughness-map-amplitude',recipe['roughnessMapAmplitude']),''),
                 'Mean':(self.scalar(material,'source-roughness-mean',recipe['maps']['roughness']['meanDataR']),'')},1)
        elif kind=='neighbor-procedural-roof-tile':
            require(recipe['evidence']=='PROJECT_AUTHORED_NOT_SCANNED_CERAMIC_ATLAS' and not recipe['maps'],'Roof photographic claim forbidden')
            common={'UV':(uv,''),'WidthCm':(self.scalar(material,'authored-tile-width-cm',recipe['tileWidthCm']),''),
                    'CourseCm':(self.scalar(material,'authored-tile-course-cm',recipe['tileCourseCm']),'')}
            color=self.custom(material,'authored-procedural-roof-basecolor',ROOF_COLOR,{**common,'Palette':(self.vector(material,'authored-roof-palette',recipe['linearPalette']),''),'Variation':(self.scalar(material,'authored-roof-albedo-variation',recipe['albedoVariation']),'')})
            normal=self.custom(material,'authored-procedural-roof-normal',ROOF_NORMAL,{**common,'ReliefCm':(self.scalar(material,'authored-tile-relief-cm',recipe['reliefHeightCm']),'')})
            rough=self.custom(material,'authored-procedural-roof-roughness',ROOF_ROUGH,{**common,'Base':(self.scalar(material,'roughness-base',recipe['roughnessBase']),''),'Variation':(self.scalar(material,'authored-roof-roughness-variation',recipe['roughnessVariation']),'')},1)
        else:
            color=self.vector(material,'authored-color',recipe.get('linearTint',recipe.get('linearPalette')))
            rough=self.scalar(material,'roughness-base',recipe['roughness'])
        for node,root in [(color,'BASE_COLOR'),(normal,'NORMAL'),(rough,'ROUGHNESS')]:self.out(node,root)
        self.out(self.scalar(material,'dielectric-metallic',0),'METALLIC');self.out(self.scalar(material,'surface-specular',specular),'SPECULAR');self.out(self.scalar(material,'unbaked-occlusion',1),'AMBIENT_OCCLUSION')
        if glass:
            self.out(self.scalar(material,'proposed-thin-glass-opacity',GLASS_OPACITY),'OPACITY')
            self.out(self.scalar(material,'proposed-glass-ior',recipe['indexOfRefraction']),'REFRACTION')
        errors=list(self.lib.recompile_material(material) or []);require(not errors,'R18 shader compilation errors: '+str(errors))
        for name,value in {'BreziGeneratedBy':OWNER,'BreziR18Recipe':json.dumps(recipe,sort_keys=True),'BreziR18NativeParameters':json.dumps({'glassOpacity':GLASS_OPACITY if glass else None,'mapsReuseOriginalAssetObjects':False},sort_keys=True)}.items():self.assets.set_metadata_tag(material,name,value)
        require(self.assets.save_loaded_asset(material,only_if_is_dirty=False),'Cannot save new R18 material')
        snapshot=graph_snapshot(u,material,self.existing_snapshot)
        return material,{'asset':material.get_path_name(),'recipe':recipe,'graph':snapshot,'shaderCompileErrors':errors,
                         'proposedGlassOpacity':GLASS_OPACITY if glass else None,
                         'nativeGlassOpticalValues':glass_optical_values(snapshot) if glass else None,'nativeAppearanceAccepted':False}


def build_materials(u,recipes,existing_snapshot):
    require(len(recipes)==9,'Exactly nine R18 graphs required');writer=Writer(u,existing_snapshot);assets={};report={}
    for key,recipe in recipes.items():assets[key],report[key]=writer.create(key,recipe)
    require(len(writer.texture_reports)==3,'Exactly three new photographic plaster textures required')
    return assets,{'owner':OWNER,'materials':report,'textures':writer.texture_reports,'nativeAppearanceAccepted':False}


def verify_materials(u,report,existing_snapshot):
    result={}
    require(len(report['materials'])==9 and len(report['textures'])==3,'R18 material/texture readback counts differ')
    for key,row in report['materials'].items():
        material=u.EditorAssetLibrary.load_asset(row['asset']);require(isinstance(material,u.Material),'R18 saved material missing')
        require(json.loads(u.EditorAssetLibrary.get_metadata_tag(material,'BreziR18Recipe'))==row['recipe'],'Saved R18 typed recipe differs')
        require(graph_snapshot(u,material,existing_snapshot)==row['graph'],'Saved R18 material graph/native values changed')
        if key=='neighbor_window_dielectric':
            require(material.get_editor_property('blend_mode')==u.BlendMode.BLEND_TRANSLUCENT,'Saved glass blend differs')
            require(material.get_editor_property('refraction_method')==enum(u,'RefractionMode','RMIndexOfRefraction'),'Saved glass IOR interpretation differs')
            require(glass_optical_values(row['graph'])==row['nativeGlassOpticalValues'],'Saved native glass readback receipt differs')
            roots=row['graph']['roots'];require(roots['METALLIC'][0]==TAG+'dielectric-metallic' and roots['ROUGHNESS'][0]==TAG+'roughness-base' and roots['OPACITY'][0]==TAG+'proposed-thin-glass-opacity','Saved glass physical scalar bindings differ')
        result[key]=material
    for role,row in report['textures'].items():
        tex=u.EditorAssetLibrary.load_asset(row['asset']);require(texture_snapshot(tex)==row['snapshot'],'Saved R18 texture object/settings differ')
        require(u.EditorAssetLibrary.get_metadata_tag(tex,'source_sha256')==row['sourceSha256'],'Saved R18 texture source pin differs')
    return result
