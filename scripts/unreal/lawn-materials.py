"""Component-only maintained-turf materials, safe to import outside Unreal.

The ground is an artist-calibrated CC0 procedural PBR asset, not a site scan.
Short polygon blades use opaque TwoSidedFoliage, native UV0.y root=0/tip=1,
and UV1.xy constant deterministic colour seeds on every vertex of each blade.
No source geometry, collision, visibility or source asset is changed here.
"""
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/lawn-materials.py'
INPUTS = ROOT / 'scripts/unreal/lawn-materials-inputs.json'
PREFIX = '/Game/Brezi/Photoreal/Lawn'
TAG = 'BreziPhotorealLawn:'


def require(ok, message):
    if not ok: raise RuntimeError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def jpeg_size(path):
    """Read SOF dimensions without external dependencies inside Unreal Python."""
    data = Path(path).read_bytes(); require(data[:2] == b'\xff\xd8', 'Not a JPEG')
    offset = 2
    while offset + 4 <= len(data):
        require(data[offset] == 255, 'Malformed JPEG marker'); offset += 1
        while data[offset] == 255: offset += 1
        marker = data[offset]; offset += 1
        require(marker not in (0xDA, 0xD9), 'JPEG has no frame dimensions')
        length = int.from_bytes(data[offset:offset+2], 'big')
        require(length >= 2 and offset + length <= len(data), 'Malformed JPEG segment')
        if marker in (0xC0, 0xC1, 0xC2):
            return [int.from_bytes(data[offset+5:offset+7], 'big'), int.from_bytes(data[offset+3:offset+5], 'big')]
        offset += length
    raise RuntimeError('JPEG frame missing')


def load_inputs():
    data = json.loads(INPUTS.read_text())
    require(data['schemaVersion'] == 1 and data['provider']['license'] == 'CC0-1.0', 'Unknown lawn input manifest')
    require(data['provider']['technique'] == 'Procedural' and data['provider']['scanClaim'] is False,
            'Lawn source provenance changed')
    require(set(data['maps']) == {'albedo', 'normal', 'roughness'}, 'Incomplete turf PBR inputs')
    for spec in data['maps'].values():
        path = (ROOT / spec['path']).resolve()
        require(path.is_relative_to(ROOT) and path.is_file(), 'Missing turf texture: ' + str(path))
        require(sha(path) == spec['sha256'] and path.stat().st_size == spec['bytes'], 'Turf texture changed: ' + str(path))
        require(jpeg_size(path) == spec['dimensions'] == [4096, 4096], 'Expected true 4K turf texture')
    return data


def select_targets(scene):
    require(scene.get('activeDesign') == {'variant':'C', 'heatingLayout':'B', 'livingLayout':'B'}, 'Lawn requires C/B/B')
    targets = []
    for record in scene['objects']:
        if not record.get('enabled'): continue
        for index, slot in enumerate(record['materialSlots']):
            source = scene['materials'][slot]
            if source['name'] != 'real-grass': continue
            require(record['group'] == 'Landscape' and record.get('metadata', {}).get('walkSurfaceId') == 'parcel-6012-26',
                    'Real-grass binding escaped the maintained parcel')
            require(record['instances'] == 1 and source['alpha'] == 1 and source['metallic'] == 0,
                    'Unexpected lawn source material/instancing')
            require(abs(record['boundsMm']['min'][2]-record['boundsMm']['max'][2]) < .01, 'Review sloped lawn normal basis')
            targets.append({'id':record['id'], 'index':index, 'sourceSlot':slot, 'sourceId':record['sourceId'], 'name':record['name']})
    require(len(targets) == 1, 'Expected one semantic maintained parcel surface')
    return targets


# All three texture phases share these continuous weights and translated UVs.
# Translation leaves the normal basis intact; ddx/ddy use unmodified world UV.
TRI = '''float2 cell=floor(UV); float2 f=UV-cell;
bool upper=f.x+f.y>1.0;
float3 W=upper ? float3(f.x+f.y-1.0,1.0-f.x,1.0-f.y) : float3(1.0-f.x-f.y,f.x,f.y);
'''
HASH = '''uint h=asuint((int)vertex.x)*0x9e3779b9u ^ asuint((int)vertex.y)*0x85ebca6bu ^ 0x601226u;
h^=h>>16; h*=0x7feb352du; h^=h>>15; h*=0x846ca68bu; h^=h>>16;
return UV+float2(h&65535u,h>>16)/65536.0;
'''


def phase_code(index):
    lower = ('float2(0,0)', 'float2(1,0)', 'float2(0,1)')[index]
    upper = ('float2(1,1)', 'float2(0,1)', 'float2(1,0)')[index]
    return TRI + 'float2 vertex=cell+(upper ? '+upper+' : '+lower+');\n' + HASH


MACRO = '''float2 P=Position.xy;
float2 noiseValue=float2(0,0);
[unroll] for(int octave=0;octave<2;octave++){
    float2 q=P/(octave==0 ? 180.0 : 550.0)+float2(9.17,23.41);
    float2 cell=floor(q), f=frac(q); f=f*f*(3.0-2.0*f);
    float4 values=float4(0,0,0,0);
    [unroll] for(int corner=0;corner<4;corner++){
        float2 v=cell+float2(corner&1,corner>>1);
        uint h=asuint((int)v.x)*0x9e3779b9u ^ asuint((int)v.y)*0x85ebca6bu ^ 0x117922u;
        h^=h>>16; h*=0x7feb352du; h^=h>>15; h*=0x846ca68bu; h^=h>>16;
        values[corner]=(h&65535u)/65535.0;
    }
    noiseValue[octave]=lerp(lerp(values.x,values.y,f.x),lerp(values.z,values.w,f.x),f.y);
}
float mowing=.02*cos(dot(P,float2(.9238795,.3826834))*3.14159265/95.0);
return float3(1.0+.16*(noiseValue.x-.5)+.12*(noiseValue.y-.5)+mowing,noiseValue.x,noiseValue.y);
'''
GROUND_COLOR = '''float3 ratio=clamp(Scan/max(Mean,float3(.001,.001,.001)),.2,2.5);
float3 color=Palette*lerp(float3(1,1,1),ratio,Contrast);
float dry=smoothstep(.60,.90,Macro.z)*.13;
return saturate(lerp(color,color*float3(1.12,1.015,.96),dry)*Macro.x);
'''
BLADE_COLOR = '''float height=saturate(UV.y);
float3 color=lerp(RootColor,TipColor,sqrt(height));
float rim=1.0-.07*abs(2.0*saturate(UV.x)-1.0);
float randomTint=.96+.08*Random;
float leafBrightness=lerp(.88,1.12,saturate(Blade.x));
float3 leafHue=lerp(float3(.94,1.03,.96),float3(1.07,.97,1.02),saturate(Blade.y));
float dry=smoothstep(.68,.92,Macro.z)*.10;
return saturate(lerp(color,color*float3(1.18,1.02,.92),dry)*Macro.x*rim*randomTint*leafBrightness*leafHue);
'''


def lattice(uv):
    require(len(uv) == 2 and all(math.isfinite(v) and abs(v) < 1e5 for v in uv), 'Invalid lawn UV')
    x,y=map(math.floor,uv); a,b=uv[0]-x,uv[1]-y
    if a+b > 1: return (a+b-1,1-a,1-b), ((x+1,y+1),(x,y+1),(x+1,y))
    return (1-a-b,a,b), ((x,y),(x+1,y),(x,y+1))


def phase_offset(vertex):
    x,y=vertex; h=(((x&0xffffffff)*0x9e3779b9)^((y&0xffffffff)*0x85ebca6b)^0x601226)&0xffffffff
    h^=h>>16;h=(h*0x7feb352d)&0xffffffff;h^=h>>15;h=(h*0x846ca68b)&0xffffffff;h^=h>>16
    return ((h&65535)/65536,(h>>16)/65536)


def sample_plan(uv):
    weights, vertices=lattice(uv)
    return weights, [tuple(a+b for a,b in zip(uv,phase_offset(v))) for v in vertices]


def enum(kind, token):
    matches=[name for name in dir(kind) if name.replace('_','').replace('MSM','').replace('MATUSAGE','') == token]
    require(len(matches) == 1, 'Unresolved Unreal lawn enum '+token); return getattr(kind,matches[0])


def graph_snapshot(u, material):
    lib=u.MaterialEditingLibrary
    def value(v):
        if isinstance(v,(str,int,bool)): return v
        if isinstance(v,float): return round(v,8)
        if hasattr(v,'r'): return [round(float(getattr(v,k)),8) for k in ('r','g','b','a')]
        if hasattr(v,'get_path_name'): return v.get_path_name()
        return str(v)
    fields={'MaterialExpressionConstant':['r'], 'MaterialExpressionConstant3Vector':['constant'],
        'MaterialExpressionCustom':['code','output_type'], 'MaterialExpressionTextureSample':['texture','sampler_type','mip_value_mode'],
        'MaterialExpressionTextureCoordinate':['coordinate_index','u_tiling','v_tiling','un_mirror_u','un_mirror_v']}
    rows=[]
    for node in lib.get_material_expressions(material):
        inputs=list(lib.get_inputs_for_material_expression(material,node)); pins=list(lib.get_material_expression_input_names(node))
        rows.append({'role':node.get_editor_property('desc'),'class':node.get_class().get_name(),
            'values':{k:value(node.get_editor_property(k)) for k in fields.get(node.get_class().get_name(),[])},
            'inputs':[[str(pin),other.get_editor_property('desc') if other else None,
                str(lib.get_input_node_output_name_for_material_expression(node,other)) if other else None] for pin,other in zip(pins,inputs)]})
    roots={}
    for prop in ['BASE_COLOR','NORMAL','ROUGHNESS','METALLIC','SPECULAR','AMBIENT_OCCLUSION','SUBSURFACE_COLOR',
                 'WORLD_POSITION_OFFSET','OPACITY','OPACITY_MASK','EMISSIVE_COLOR']:
        pid=getattr(u.MaterialProperty,'MP_'+prop); node=lib.get_material_property_input_node(material,pid)
        roots[prop]=[node.get_editor_property('desc'),str(lib.get_material_property_input_node_output_name(material,pid))] if node else None
    return {'nodes':sorted(rows,key=lambda row:row['role']),'roots':roots,
        'flags':{k:value(material.get_editor_property(k)) for k in ['blend_mode','shading_model','two_sided','tangent_space_normal']},
        'instancedUsage':lib.has_material_usage(material,enum(u.MaterialUsage,'INSTANCEDSTATICMESHES')),
        'naniteUsage':lib.has_material_usage(material,u.MaterialUsage.MATUSAGE_NANITE)}


class Writer:
    def __init__(self,u,inputs):
        self.u=u;self.inputs=inputs;self.lib=u.MaterialEditingLibrary;self.assets=u.EditorAssetLibrary
        self.textures={};self.paths=set();self.serial=0

    def node(self,m,role,cls,**props):
        node=self.lib.create_material_expression(m,cls,-600,0);require(node is not None,'Lawn graph creation failed')
        node.set_editor_property('desc',TAG+role)
        for k,v in props.items():node.set_editor_property(k,v)
        return node

    def scalar(self,m,value):
        self.serial+=1;return self.node(m,'scalar-'+str(self.serial),self.u.MaterialExpressionConstant,r=float(value))

    def vector(self,m,value):
        self.serial+=1;return self.node(m,'vector-'+str(self.serial),self.u.MaterialExpressionConstant3Vector,constant=self.u.LinearColor(*value,1))

    def connect(self,a,ch,b,pin):require(self.lib.connect_material_expressions(a,ch,b,pin),'Lawn input failed: '+pin)
    def out(self,node,channel,prop):require(self.lib.connect_material_property(node,channel,getattr(self.u.MaterialProperty,'MP_'+prop)),'Lawn output failed: '+prop)

    def custom(self,m,role,code,inputs,output):
        entries=[]
        for key in inputs:
            entry=self.u.CustomInput();entry.set_editor_property('input_name',key);entries.append(entry)
        node=self.node(m,role,self.u.MaterialExpressionCustom,code=code,output_type=output,description=TAG+role,inputs=entries)
        for key,(source,channel) in inputs.items():self.connect(source,channel,node,key)
        return node

    def save(self,asset):
        self.assets.set_metadata_tag(asset,'BreziGeneratedBy',OWNER)
        require(self.assets.save_loaded_asset(asset,only_if_is_dirty=False),'Lawn asset save failed')
        self.paths.add(asset.get_path_name())

    def texture(self,role):
        if role in self.textures:return self.textures[role]['object']
        u=self.u;spec=self.inputs['maps'][role];name='T_Grass004_'+role+'_'+spec['sha256'][:12]
        require(not self.assets.does_asset_exist(PREFIX+'/Textures/'+name),'Lawn texture exists; use new isolated output')
        task=u.AssetImportTask()
        for k,v in {'filename':str(ROOT/spec['path']),'destination_path':PREFIX+'/Textures','destination_name':name,
                    'automated':True,'replace_existing':False,'save':False}.items():task.set_editor_property(k,v)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);texture=self.assets.load_asset(PREFIX+'/Textures/'+name)
        require(isinstance(texture,u.Texture2D),'Lawn texture import failed')
        compression=u.TextureCompressionSettings.TC_NORMALMAP if role=='normal' else u.TextureCompressionSettings.TC_DEFAULT if role=='albedo' else u.TextureCompressionSettings.TC_MASKS
        # Texture::PostEditChange forces sRGB off for the CURRENT compression.
        # Set compression first so importer autodetection cannot silently leave
        # an albedo image linear when switching it back to TC_Default.
        policy={'compression_settings':compression,'srgb':role=='albedo','flip_green_channel':role=='normal',
            'address_x':u.TextureAddress.TA_WRAP,'address_y':u.TextureAddress.TA_WRAP,'lod_bias':0,'max_texture_size':0,
            'mip_gen_settings':u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP}
        for k,v in policy.items():texture.set_editor_property(k,v)
        for k,v in policy.items():require(texture.get_editor_property(k)==v,'Lawn texture import policy differs: '+k)
        require([texture.blueprint_get_size_x(),texture.blueprint_get_size_y()]==[4096,4096],'Lawn imported texture dimensions differ')
        self.assets.set_metadata_tag(texture,'source_sha256',spec['sha256']);self.save(texture)
        self.textures[role]={'object':texture,'role':role,'asset':texture.get_path_name(),'source':spec['path'],
            'sha256':spec['sha256'],'dimensions':[4096,4096],
            'policy':{k:(str(v) if not isinstance(v,(int,bool,float)) else v) for k,v in policy.items()}}
        return texture

    def material(self,kind):
        u=self.u;recipe={'kind':kind,**self.inputs['recipe'][kind]};name='M_'+kind+'_'+digest(recipe)[:16]
        require(not self.assets.does_asset_exist(PREFIX+'/Materials/'+name),'Lawn material exists; use new isolated output')
        material=u.AssetToolsHelpers.get_asset_tools().create_asset(name,PREFIX+'/Materials',u.Material,u.MaterialFactoryNew())
        require(material is not None,'Lawn material creation failed');self.serial=0
        for k,v in {'blend_mode':u.BlendMode.BLEND_OPAQUE,'shading_model':enum(u.MaterialShadingModel,'TWOSIDEDFOLIAGE') if kind=='blade' else u.MaterialShadingModel.MSM_DEFAULT_LIT,
                    'two_sided':kind=='blade','tangent_space_normal':kind=='blade'}.items():material.set_editor_property(k,v)
        self.lib.set_base_material_usage(material,u.MaterialUsage.MATUSAGE_NANITE,True)
        if kind=='blade':self.lib.set_base_material_usage(material,enum(u.MaterialUsage,'INSTANCEDSTATICMESHES'),True)
        pos=self.node(material,'world-position',u.MaterialExpressionWorldPosition)
        macro=self.custom(material,'shared-turf-macro',MACRO,{'Position':(pos,'')},u.CustomMaterialOutputType.CMOT_FLOAT3)
        if kind=='ground':
            uv=self.custom(material,'world-centimetres-to-turf-uv','return Position.xy/TileCm;',
                {'Position':(pos,''),'TileCm':(self.scalar(material,recipe['tileCm']),'')},u.CustomMaterialOutputType.CMOT_FLOAT2)
            weights=self.custom(material,'stochastic-weights',TRI+'return W;',{'UV':(uv,'')},u.CustomMaterialOutputType.CMOT_FLOAT3)
            phases=[self.custom(material,'phase-'+str(i),phase_code(i),{'UV':(uv,'')},u.CustomMaterialOutputType.CMOT_FLOAT2) for i in range(3)]
            dx=self.custom(material,'continuous-ddx','return ddx(UV);',{'UV':(uv,'')},u.CustomMaterialOutputType.CMOT_FLOAT2)
            dy=self.custom(material,'continuous-ddy','return ddy(UV);',{'UV':(uv,'')},u.CustomMaterialOutputType.CMOT_FLOAT2)
            samples={}
            for role in ('albedo','normal','roughness'):
                sampler=u.MaterialSamplerType.SAMPLERTYPE_COLOR if role=='albedo' else u.MaterialSamplerType.SAMPLERTYPE_NORMAL if role=='normal' else u.MaterialSamplerType.SAMPLERTYPE_MASKS
                nodes=[]
                for i,phase in enumerate(phases):
                    node=self.node(material,role+'-phase-'+str(i),u.MaterialExpressionTextureSample,texture=self.texture(role),
                        sampler_type=sampler,mip_value_mode=u.TextureMipValueMode.TMVM_DERIVATIVE)
                    for source,pin in [(phase,'UVs'),(dx,'DDX(UVs)'),(dy,'DDY(UVs)')]:self.connect(source,'',node,pin)
                    nodes.append(node)
                samples[role]=self.custom(material,role+'-registered-blend','return A*W.x+B*W.y+C*W.z;',
                    {**{k:(v,'RGB') for k,v in zip('ABC',nodes)},'W':(weights,'')},u.CustomMaterialOutputType.CMOT_FLOAT3)
            color=self.custom(material,'calm-turf-color',GROUND_COLOR,{'Scan':(samples['albedo'],''),'Macro':(macro,''),
                'Mean':(self.vector(material,self.inputs['maps']['albedo']['meanLinearRGB']),''),
                'Palette':(self.vector(material,recipe['paletteLinear']), ''),
                'Contrast':(self.scalar(material,recipe['albedoContrast']),'')},u.CustomMaterialOutputType.CMOT_FLOAT3)
            normal=self.custom(material,'ground-world-normal','return normalize(float3(MapNormal.xy*Strength,max(MapNormal.z,.10)));',
                {'MapNormal':(samples['normal'],''),'Strength':(self.scalar(material,recipe['normalStrength']),'')},u.CustomMaterialOutputType.CMOT_FLOAT3)
            rough=self.custom(material,'turf-effective-roughness','return .84+.13*saturate(Raw.r);',{'Raw':(samples['roughness'],'')},u.CustomMaterialOutputType.CMOT_FLOAT1)
            self.out(normal,'','NORMAL');self.out(rough,'','ROUGHNESS')
        else:
            uv=self.node(material,'blade-uv-root-to-tip',u.MaterialExpressionTextureCoordinate,coordinate_index=0,u_tiling=1.,v_tiling=1.,un_mirror_u=False,un_mirror_v=False)
            blade=self.node(material,'per-blade-color-seeds',u.MaterialExpressionTextureCoordinate,coordinate_index=1,u_tiling=1.,v_tiling=1.,un_mirror_u=False,un_mirror_v=False)
            random=self.node(material,'tuft-variation',u.MaterialExpressionPerInstanceRandom)
            color=self.custom(material,'blade-root-to-tip-color',BLADE_COLOR,{'UV':(uv,''),'Blade':(blade,''),'Macro':(macro,''),'Random':(random,''),
                'RootColor':(self.vector(material,recipe['rootLinear']),''),'TipColor':(self.vector(material,recipe['tipLinear']),'')},u.CustomMaterialOutputType.CMOT_FLOAT3)
            rough=self.custom(material,'blade-roughness','return .88-.07*saturate(UV.y)+.03*(Random-.5);',
                {'UV':(uv,''),'Random':(random,'')},u.CustomMaterialOutputType.CMOT_FLOAT1)
            sss=self.custom(material,'blade-transmission-color','return Color*Transmission;',
                {'Color':(color,''),'Transmission':(self.scalar(material,recipe['transmissionColorScale']),'')},u.CustomMaterialOutputType.CMOT_FLOAT3)
            self.out(rough,'','ROUGHNESS');self.out(sss,'','SUBSURFACE_COLOR');self.out(self.scalar(material,.5),'','OPACITY')
        self.out(color,'','BASE_COLOR');self.out(self.scalar(material,0),'','METALLIC')
        self.out(self.scalar(material,recipe['specular']),'','SPECULAR');self.out(self.scalar(material,1),'','AMBIENT_OCCLUSION')
        errors=list(self.lib.recompile_material(material));require(not errors,'Lawn shader compilation failed: '+str(errors))
        self.assets.set_metadata_tag(material,'BreziLawnRecipe',json.dumps(recipe,sort_keys=True));self.save(material)
        return material,recipe


def components(u,ids):
    result={}
    for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        keys={str(t) for t in actor.get_editor_property('tags')} & ids
        if not keys or actor.actor_has_tag('BreziWalkSupportProxy'):continue
        require(len(keys)==1,'Ambiguous lawn actor tag');key=next(iter(keys));require(key not in result,'Duplicate lawn actor')
        parts=list(actor.get_components_by_class(u.StaticMeshComponent));require(len(parts)==1,'Lawn actor must have one component')
        result[key]=parts[0]
    require(set(result)==ids,'Missing native maintained lawn');return result


def geometry_witness(u,parts):
    result={}
    for key,component in parts.items():
        transform=component.get_world_transform();origin,extent,_=u.SystemLibrary.get_component_bounds(component)
        mesh=component.get_editor_property('static_mesh');actor=component.get_owner()
        require(component.is_visible() and not component.get_editor_property('hidden_in_game')
                and not actor.get_editor_property('hidden'),'Maintained source lawn is hidden')
        require(all(abs(getattr(transform.scale3d,k)-1)<1e-6 for k in ('x','y','z')),'Lawn source scale changed')
        require(max(abs(getattr(transform.rotation,k)) for k in ('x','y'))<1e-6,'Lawn world normal basis requires level ground')
        result[key]={'mesh':mesh.get_path_name(),'triangles':mesh.get_num_triangles(0),'sections':mesh.get_num_sections(0),
            'position':[round(getattr(transform.translation,k),5) for k in ('x','y','z')],
            'rotation':[round(getattr(transform.rotation,k),6) for k in ('x','y','z','w')],
            'bounds':[round(getattr(v,k),4) for v in (origin,extent) for k in ('x','y','z')],
            'collision':str(component.get_collision_enabled()),'profile':str(component.get_collision_profile_name()),
            'collisionResponses':{name:str(component.get_collision_response_to_channel(getattr(u.CollisionChannel,name)))
                for name in dir(u.CollisionChannel) if name.startswith('ECC_') and name!='ECC_MAX'},
            'visible':bool(component.is_visible()),'hiddenInGame':bool(component.get_editor_property('hidden_in_game')),
            'actorHidden':bool(actor.get_editor_property('hidden')),'actorTags':sorted(map(str,actor.get_editor_property('tags'))),
            'tags':sorted(map(str,component.get_editor_property('component_tags')))}
    return result


def apply_materials(scene,geometry,baseline_material_report):
    import unreal as u
    inputs=load_inputs();targets=select_targets(scene);parts=components(u,{t['id'] for t in targets})
    witness=geometry_witness(u,parts);expected={(r['id'],r['index']):r['asset'] for r in baseline_material_report['bindings']}
    for target in targets:
        component=parts[target['id']];base=component.get_material(target['index']);mesh=component.get_editor_property('static_mesh')
        require(base and base.get_path_name()==expected[(target['id'],target['index'])] and mesh.get_material(target['index'])==base,
                'Lawn no longer binds accepted source material')
    writer=Writer(u,inputs);ground,ground_recipe=writer.material('ground');blade,blade_recipe=writer.material('blade')
    report={'schemaVersion':1,'status':'lawn-materials-reload-pending','generatedAt':datetime.now(timezone.utc).isoformat(),
        'sourceManifestSha256':sha(Path(geometry)/'scene.json'),'sourceObjSha256':sha(Path(geometry)/'dom-mm.obj'),
        'pipelineFiles':{OWNER:sha(__file__),str(INPUTS.relative_to(ROOT)):sha(INPUTS)},'bindings':[],
        'inputFiles':{str(INPUTS.relative_to(ROOT)):sha(INPUTS),**{entry['path']:entry['sha256'] for entry in inputs['maps'].values()}},
        'textures':[{k:v for k,v in t.items() if k!='object'} for t in writer.textures.values()],
        'materials':{kind:{'asset':material.get_path_name(),'recipe':recipe,'graph':graph_snapshot(u,material)}
            for kind,material,recipe in [('ground',ground,ground_recipe),('blade',blade,blade_recipe)]},
        'witness':witness,'geometryWitness':witness,'geometryModified':False,'collisionModified':False,
        'generatedAssets':sorted(writer.paths),'savedReloaded':False,'nativeRenderedVerified':False,
        'provider':inputs['provider'],'bladeUVContract':{'channel':0,'u':'width 0 to 1','v':'native root 0 to tip 1',
            'variationChannel':1,'variationU':'brightness seed 0 to 1, constant per blade',
            'variationV':'hue seed 0 to 1, constant per blade','variationAcrossLods':'same original blade retains the same seeds'},
        'limitations':['Grass004 is an artist-created procedural CC0 PBR asset, not a measured site scan.',
            'Provider tile reference is 140 cm; the ground is artist-scaled to 90 cm to suggest finer mown thatch beneath polygon blades.',
            'Colors, effective canopy roughness and foliage transmission are artistic approximations requiring native review.',
            'Ground is undisplaced; actual blade silhouettes and self-shadow depend on the separate short polygon geometry layer.',
            'No species, agricultural planting specification, measured BRDF or native visual acceptance is claimed.']}
    for target in targets:
        component=parts[target['id']];original=component.get_material(target['index']).get_path_name();component.set_material(target['index'],ground)
        report['bindings'].append({**target,'asset':ground.get_path_name(),'originalAsset':original,'component':component.get_name()})
    require(geometry_witness(u,parts)==witness,'Lawn material assignment changed protected source state')
    report.update(groundMaterial=report['materials']['ground'],bladeMaterial=report['materials']['blade'],sourceGroundRetained=True)
    (Path(geometry).parent/'lawn-materials-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    return report


def verify_materials(scene,geometry,report):
    import unreal as u
    require(sha(Path(geometry)/'scene.json')==report['sourceManifestSha256'] and sha(Path(geometry)/'dom-mm.obj')==report['sourceObjSha256'],
            'Lawn source geometry changed')
    for path,expected in report['pipelineFiles'].items():require(sha(ROOT/path)==expected,'Lawn pipeline changed: '+path)
    for path,expected in report['inputFiles'].items():require(sha(ROOT/path)==expected,'Lawn input changed: '+path)
    load_inputs();targets=select_targets(scene)
    require({(t['id'],t['index']) for t in targets}=={(t['id'],t['index']) for t in report['bindings']},'Lawn selection changed')
    parts=components(u,{t['id'] for t in targets});require(geometry_witness(u,parts)==report['witness'],'Lawn source state changed')
    for row in report['bindings']:
        component=parts[row['id']];material=component.get_material(row['index']);mesh=component.get_editor_property('static_mesh')
        require(material and material.get_path_name()==row['asset'] and component.get_name()==row['component']
                and mesh.get_material(row['index']).get_path_name()==row['originalAsset'],'Lawn effective or source binding changed')
    for entry in report['materials'].values():
        material=u.EditorAssetLibrary.load_asset(entry['asset'])
        require(material and u.EditorAssetLibrary.get_metadata_tag(material,'BreziGeneratedBy')==OWNER
                and u.EditorAssetLibrary.get_metadata_tag(material,'BreziLawnRecipe')==json.dumps(entry['recipe'],sort_keys=True)
                and graph_snapshot(u,material)==entry['graph'],'Saved lawn graph differs')
    for entry in report['textures']:
        texture=u.EditorAssetLibrary.load_asset(entry['asset']);require(texture is not None,'Saved lawn texture missing')
        require(u.EditorAssetLibrary.get_metadata_tag(texture,'BreziGeneratedBy')==OWNER
                and u.EditorAssetLibrary.get_metadata_tag(texture,'source_sha256')==entry['sha256']
                and [texture.blueprint_get_size_x(),texture.blueprint_get_size_y()]==entry['dimensions'],'Saved lawn texture source differs')
        for key,expected in entry['policy'].items():
            actual=texture.get_editor_property(key)
            require((actual if isinstance(actual,(int,bool,float)) else str(actual))==expected,'Saved lawn texture decoding changed: '+key)
    require(report['groundMaterial']==report['materials']['ground'] and report['bladeMaterial']==report['materials']['blade'],
            'Lawn material aliases differ')
    report.update(status='lawn-materials-saved-reloaded-validated',savedReloaded=True,sourceGroundRetained=True,verifiedAt=datetime.now(timezone.utc).isoformat())
    (Path(geometry).parent/'lawn-materials-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    return report
