"""Owned ArchViz exterior component overrides; never modify canonical meshes.

CPU import is safe. Native calls are explicit: apply_photoreal_exterior, save and
reload the map, then verify_photoreal_exterior. Select by semantic source names,
not historical DOM/MAT ordinals. Shader world positions are UE centimetres.
"""
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/photoreal-exterior.py'
INPUTS = ROOT / 'scripts/unreal/photoreal-exterior-inputs.json'
PREFIX = '/Game/Brezi/Photoreal/Exterior'
TAG = 'BreziPhotorealExterior:'
PALETTE = [.275, .170, .090]  # scene-linear natural warm timber, common to both scans
BANDS = {'hinoki_planks': [.025, .103, .179, .256, .410, .565, .796, .9475],
         'wood_planks': [.021, .263, .5895]}


def require(ok, message):
    if not ok: raise RuntimeError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def load_inputs():
    data = json.loads(INPUTS.read_text())
    require(data['schemaVersion'] == 1, 'Unknown exterior input manifest')
    for asset in data['assets'].values():
        require(asset['license'] == 'CC0-1.0' and set(asset['maps']) == {'albedo','normal','roughness','ao'}, 'Incomplete scan PBR set')
        for spec in asset['maps'].values():
            path = (ROOT / spec['path']).resolve()
            require(path.is_relative_to(ROOT) and path.is_file(), 'Missing scan: ' + str(path))
            require(sha(path) == spec['sha256'] and path.stat().st_size == spec['bytes'], 'Scan identity changed: ' + str(path))
            require(spec['width'] == 4096 and spec['height'] == 4096, 'Exterior scan is not 4K')
    return data


def select_targets(scene):
    """Only exterior wood and actual roof components, never furniture/doors."""
    require(scene.get('activeDesign') == {'variant':'C','heatingLayout':'B','livingLayout':'B'}, 'Exterior requires current C/B/B')
    layout = scene['deckBoardLayout']
    require(layout['widthMm'] == 145 and layout['jointMm'] == 8, 'Review changed deck-board design')
    targets = []
    for record in scene['objects']:
        if not record.get('enabled'): continue
        for index, slot in enumerate(record['materialSlots']):
            source = scene['materials'][slot]; name = source['name']; kind = None
            if name.startswith('real-larch-') and not name.startswith('real-larch-table:'):
                kind = 'soffit' if name.startswith('real-larch-porch-ceiling-') else 'facade'
            elif name.startswith('TERR-') and name.endswith(' · PBR materiál'):
                kind = 'deck'
            elif name == 'real-deck' and record['group'] == 'Decking':
                kind = 'deck-hatch'
            elif name == 'real-roof': kind = 'roof'
            elif name == 'real-roof-edge' and record['group'] == 'Roof' and any(token in record['name'].casefold() for token in
                ['falc','žľab','okapová','hrebeň','lem ·','strešná hrana','oplechovanie','manžeta','dymovod','hlavica','dažďový zvod']):
                kind = 'roof'
            if not kind: continue
            require(record['instances'] == 1 and source['alpha'] >= .999, 'Unexpected exterior instancing/transparency')
            grain = [0.,0.,1.]
            if kind == 'soffit':
                box = record['boundsMm']; dx = box['max'][0]-box['min'][0]; dz=box['max'][2]-box['min'][2]
                # Longitudinal plank follows the source sloping porch underside.
                sign = 1 if name.startswith('real-larch-porch-ceiling-0:') else -1
                length = math.hypot(dx,dz); grain = [dx/length,0.,sign*dz/length]
            elif kind.startswith('deck'): grain = [1.,0.,0.]
            asset = 'wood_planks' if kind.startswith('deck') else 'hinoki_planks'
            recipe = {'kind':kind, 'asset':asset if kind != 'roof' else None,
                'grain':grain, 'pitchCm':15.3 if kind.startswith('deck') else 5.,
                'jointCm':0. if kind.startswith('deck') else .1953125,
                'roughness':.74 if kind.startswith('deck') else .66,
                'roughnessAmplitude':.26,'albedoContrast':.50,'normalStrength':.38 if kind.startswith('deck') else .32,
                'palette':PALETTE, 'anchorCm':[0.,0.,0.], 'sourceName':name}
            targets.append({'id':record['id'],'index':index,'sourceSlot':slot,'sourceId':record['sourceId'],
                            'name':record['name'],'recipe':recipe})
    require({'facade','soffit','deck','roof'} <= {t['recipe']['kind'] for t in targets}, 'Exterior semantic coverage incomplete')
    require(len({(t['id'],t['index']) for t in targets}) == len(targets), 'Duplicate exterior target')
    return targets


def deck_grid_anchor(positions_mm):
    """Find the midpoint of the true 8 mm joint from source vertex residues.

    The board mesh is already merged. This avoids invented pitch starts and
    ensures a stochastic material change occurs in the empty joint, never on
    a 145 mm board face. Bounds alone are insufficient at trimmed perimeters.
    """
    counts = Counter(round((-p[1]/10) % 15.3, 3) for p in positions_mm)
    require(len(counts) >= 2, 'No source deck-board cross edges')
    candidates = []
    for a, ca in counts.items():
        for b, cb in counts.items():
            gap = (b-a) % 15.3
            if abs(gap-.8) < .004: candidates.append((ca+cb, a, gap))
    require(candidates, 'Deck source vertices do not prove an 8 mm joint')
    _, start, gap = max(candidates)
    return round((start+gap/2) % 15.3, 6)


def source_deck_positions(path, ids):
    positions=[]; result={i:[] for i in ids}; current=None
    for line in Path(path).read_text().splitlines():
        row=line.split()
        if not row: continue
        if row[0]=='v': positions.append(tuple(map(float,row[1:4])))
        elif row[0]=='o': current=row[1]
        elif row[0]=='f' and current in result:
            result[current].extend(positions[int(v.split('/')[0])-1] for v in row[1:])
    require(all(result.values()), 'Source deck OBJ coverage missing')
    return result


def prepare_targets(scene, geometry):
    targets=select_targets(scene); ids={t['id'] for t in targets if t['recipe']['kind']=='deck'}
    positions=source_deck_positions(Path(geometry)/'dom-mm.obj',ids)
    for target in targets:
        if target['id'] in positions:
            target['recipe']['anchorCm'][1]=deck_grid_anchor(positions[target['id']])
    return targets


BASIS = '''float3 N=normalize(NormalWS);
float3 T0=Grain-N*dot(Grain,N);
if(dot(T0,T0)<1e-8){float3 A=abs(N.x)<.8?float3(1,0,0):float3(0,1,0);T0=A-N*dot(A,N);}
float3 T=normalize(T0); float3 B=normalize(cross(N,T));
float3 P=Position-AnchorCm; float2 Q=float2(dot(P,T),dot(P,B));
'''
HASH = '''uint h=asuint((int)floor(Q.y/PitchCm)) ^ (asuint((int)cell)*0x9e3779b9u);
h^=h>>16; h*=0x7feb352du; h^=h>>15; h*=0x846ca68bu; h^=h>>16;
'''


def uv_code(asset, second=False):
    bands=BANDS[asset]; period=189. if asset=='hinoki_planks' else 150.
    # 2.7m cells blend with C1-continuous weight. Independent cell phases and
    # strips break the photographic repeat without rotating physical grain.
    # Cropping wood_planks U removes its photographed end joint, as in the
    # validated prior deck study. Metric derivatives account for the crop.
    along=('0.02+0.96*frac(Q.x/144.0+phase)' if asset=='wood_planks' else 'Q.x/189.0+phase')
    return BASIS + 'float cell=floor(Q.x/270.0)+'+('1.0' if second else '0.0')+';\n'+HASH+\
        'const float bands[%d]={%s};\n'%(len(bands),','.join(map(str,bands)))+\
        'float phase=float((h>>8)&65535u)/65536.0;\nreturn float2('+along+',bands[h%'+str(len(bands))+'u]+frac(Q.y/PitchCm)*PitchCm/'+str(period)+');'


BLEND = BASIS + 'float x=frac(Q.x/270.0);return x*x*(3.0-2.0*x);'
JOINT = BASIS + '''float width=JointCm/PitchCm; float x=Q.y/PitchCm+width*.5;
float fp=max(abs(ddx(x))+abs(ddy(x)),1e-5);float lo=x-fp*.5,hi=x+fp*.5;
float a=floor(lo)*width+min(frac(lo),width),b=floor(hi)*width+min(frac(hi),width);
return saturate((b-a)/fp);'''
WOOD_COLOR = '''float3 tint=lerp(float3(1,1,1),Scan/max(Mean,float3(.001,.001,.001)),Contrast);
return saturate(Palette*clamp(tint,.22,1.95)*lerp(1.0,.30,Joint));'''
WOOD_NORMAL = BASIS + '''return normalize(T*MapNormal.x*Strength+B*MapNormal.y*Strength+N*max(MapNormal.z,.1))*FaceSign;'''
WOOD_ROUGH = 'return clamp(Base+(Sample.r-Mean)*.26+Joint*.09,.50,.94);'
WOOD_AO = 'return lerp(.88+.12*Scan.r,.44,Joint);'
# A coil-coated surface is a dielectric paint layer. Metallic=0 is intentional:
# hidden steel does not turn its opaque pigmented coating into bare metal.
ROOF = '''float3 N=normalize(NormalWS);float3 A=abs(N.z)>.8?float3(1,0,0):float3(0,0,1);
float3 T=normalize(A-N*dot(A,N)),B=normalize(cross(N,T));
float2 p=float2(dot(Position,T),dot(Position,B))/.065;
float fade=1.0-smoothstep(.15,.45,max(fwidth(p.x),fwidth(p.y)));
float s=sin(p.x*6.2831853+sin(p.y*2.17));float t=sin(p.y*5.7321+sin(p.x*1.29));
float3 normal=normalize(N+T*s*.008*fade+B*t*.006*fade)*FaceSign;
return float4(normal,clamp(.37+(.018*s+.012*t)*fade,.33,.42));'''


def graph_snapshot(u, material):
    lib=u.MaterialEditingLibrary; nodes=list(lib.get_material_expressions(material))
    def value(v):
        if isinstance(v,(str,int,bool)): return v
        if isinstance(v,float): return round(v,8)
        if hasattr(v,'r'): return [round(float(getattr(v,k)),8) for k in ('r','g','b','a')]
        if hasattr(v,'get_path_name'): return v.get_path_name()
        return str(v)
    fields={'MaterialExpressionConstant':['r'],'MaterialExpressionConstant3Vector':['constant'],
        'MaterialExpressionCustom':['code','output_type'],'MaterialExpressionTextureSample':['texture','sampler_type','mip_value_mode'],
        'MaterialExpressionComponentMask':['r','g','b','a']}
    rows=[]
    for node in nodes:
        inputs=list(lib.get_inputs_for_material_expression(material,node));pins=list(lib.get_material_expression_input_names(node))
        rows.append({'role':node.get_editor_property('desc'),'class':node.get_class().get_name(),
            'values':{k:value(node.get_editor_property(k)) for k in fields.get(node.get_class().get_name(),[])},
            'inputs':[[str(pin),other.get_editor_property('desc') if other else None,
                str(lib.get_input_node_output_name_for_material_expression(node,other)) if other else None] for pin,other in zip(pins,inputs)]})
    roots={}
    for prop in ['BASE_COLOR','NORMAL','ROUGHNESS','METALLIC','SPECULAR','AMBIENT_OCCLUSION','WORLD_POSITION_OFFSET','OPACITY','EMISSIVE_COLOR']:
        pid=getattr(u.MaterialProperty,'MP_'+prop);node=lib.get_material_property_input_node(material,pid)
        roots[prop]=[node.get_editor_property('desc'),str(lib.get_material_property_input_node_output_name(material,pid))] if node else None
    return {'nodes':sorted(rows,key=lambda r:r['role']),'roots':roots,
        'flags':{key:value(material.get_editor_property(key)) for key in ['blend_mode','shading_model','two_sided','tangent_space_normal']},
        'naniteUsage':lib.has_material_usage(material,u.MaterialUsage.MATUSAGE_NANITE)}


class Writer:
    def __init__(self,u,inputs):
        self.u=u;self.inputs=inputs;self.assets=u.EditorAssetLibrary;self.lib=u.MaterialEditingLibrary
        self.textures={};self.paths=set();self.nodes={};self.serial=0

    def node(self,m,role,cls,**props):
        n=self.lib.create_material_expression(m,cls,-600,0);require(n is not None,'Exterior graph node creation failed')
        n.set_editor_property('desc',TAG+role)
        for k,v in props.items(): n.set_editor_property(k,v)
        return n

    def scalar(self,m,value):
        self.serial+=1;return self.node(m,'scalar-'+str(self.serial),self.u.MaterialExpressionConstant,r=float(value))

    def vector(self,m,value):
        self.serial+=1;return self.node(m,'vector-'+str(self.serial),self.u.MaterialExpressionConstant3Vector,constant=self.u.LinearColor(*value,1))

    def connect(self,a,ch,b,pin): require(self.lib.connect_material_expressions(a,ch,b,pin),'Exterior graph connection failed: '+pin)
    def out(self,n,channel,prop): require(self.lib.connect_material_property(n,channel,getattr(self.u.MaterialProperty,'MP_'+prop)),'Exterior material root failed: '+prop)

    def custom(self,m,role,code,inputs,output):
        custom_inputs=[]
        for key in inputs:
            entry=self.u.CustomInput()
            entry.set_editor_property('input_name',key)
            custom_inputs.append(entry)
        n=self.node(m,role,self.u.MaterialExpressionCustom,code=code,output_type=output,description=TAG+role,
            inputs=custom_inputs)
        for k,(source,channel) in inputs.items(): self.connect(source,channel,n,k)
        return n

    def texture(self,asset,role):
        key=asset+'/'+role
        if key in self.textures:return self.textures[key]['object']
        u=self.u;spec=self.inputs['assets'][asset]['maps'][role]
        path=PREFIX+'/Textures/T_'+asset+'_'+role+'_'+spec['sha256'][:12]
        require(not self.assets.does_asset_exist(path),'Exterior texture already exists; verify previous run instead of overwriting: '+path)
        task=u.AssetImportTask();task.set_editor_property('filename',str(ROOT/spec['path']))
        task.set_editor_property('destination_path',PREFIX+'/Textures');task.set_editor_property('destination_name',path.rsplit('/',1)[1])
        task.set_editor_property('automated',True);task.set_editor_property('replace_existing',False);task.set_editor_property('save',False)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);t=self.assets.load_asset(path)
        require(isinstance(t,u.Texture2D),'Exterior scan import failed')
        compression=u.TextureCompressionSettings.TC_NORMALMAP if role=='normal' else (u.TextureCompressionSettings.TC_DEFAULT if role=='albedo' else u.TextureCompressionSettings.TC_MASKS)
        for k,v in {'srgb':role=='albedo','flip_green_channel':role=='normal','compression_settings':compression,
            'address_x':u.TextureAddress.TA_WRAP,'address_y':u.TextureAddress.TA_WRAP,'lod_bias':0,'max_texture_size':0,
            'mip_gen_settings':u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP}.items():t.set_editor_property(k,v)
        require(t.blueprint_get_size_x()==4096 and t.blueprint_get_size_y()==4096,'Imported exterior texture is not 4K')
        self.assets.set_metadata_tag(t,'source_sha256',spec['sha256']);self.save(t)
        self.textures[key]={'object':t,'asset':t.get_path_name(),'source':spec['path'],'sha256':spec['sha256'],
            'srgb':role=='albedo','greenFlipped':role=='normal','compression':str(compression),'dimensions':[4096,4096]}
        return t

    def save(self,asset):
        self.assets.set_metadata_tag(asset,'BreziGeneratedBy',OWNER)
        require(self.assets.save_loaded_asset(asset,only_if_is_dirty=False),'Exterior asset save failed')
        self.paths.add(asset.get_path_name())

    def material(self,recipe):
        u=self.u;key=digest(recipe);name='M_'+recipe['kind'].replace('-','_')+'_'+key[:16]
        path=PREFIX+'/Materials/'+name
        require(not self.assets.does_asset_exist(path),'Exterior material exists; use fresh isolated output or verify previous run')
        m=u.AssetToolsHelpers.get_asset_tools().create_asset(name,PREFIX+'/Materials',u.Material,u.MaterialFactoryNew())
        require(m is not None,'Exterior material create failed');self.serial=0
        for k,v in {'blend_mode':u.BlendMode.BLEND_OPAQUE,'shading_model':u.MaterialShadingModel.MSM_DEFAULT_LIT,
            'two_sided':True,'tangent_space_normal':False}.items():m.set_editor_property(k,v)
        self.lib.set_base_material_usage(m,u.MaterialUsage.MATUSAGE_NANITE,True)
        pos=self.node(m,'position',u.MaterialExpressionWorldPosition);normal=self.node(m,'vertex-normal',u.MaterialExpressionVertexNormalWS)
        sign=self.node(m,'face-sign',u.MaterialExpressionTwoSidedSign)
        c={'Position':(pos,''),'NormalWS':(normal,'')}
        if recipe['kind']=='roof':
            detail=self.custom(m,'satin-coating',ROOF,{**c,'FaceSign':(sign,'')},u.CustomMaterialOutputType.CMOT_FLOAT4)
            n=self.node(m,'normal-channel',u.MaterialExpressionComponentMask,r=True,g=True,b=True,a=False)
            r=self.node(m,'roughness-channel',u.MaterialExpressionComponentMask,r=False,g=False,b=False,a=True)
            self.connect(detail,'',n,'');self.connect(detail,'',r,'');self.out(n,'','NORMAL');self.out(r,'','ROUGHNESS')
            # RAL 7016 visual approximation, not a measured paint swatch.
            self.out(self.vector(m,[.034,.042,.047]),'','BASE_COLOR')
            self.out(self.scalar(m,1),'','AMBIENT_OCCLUSION')
        else:
            asset=recipe['asset'];source=self.inputs['assets'][asset];period=source['periodCm']
            c.update(Grain=(self.vector(m,recipe['grain']),''),AnchorCm=(self.vector(m,recipe['anchorCm']),''))
            pitch=self.scalar(m,recipe['pitchCm']);q={**c,'PitchCm':(pitch,'')}
            uv=[self.custom(m,'scan-uv-'+str(i),uv_code(asset,bool(i)),q,u.CustomMaterialOutputType.CMOT_FLOAT2) for i in range(2)]
            # No floor/hash/frac discontinuity participates in mip selection.
            dx=self.custom(m,'scan-ddx',BASIS+'return ddx(Q)/'+str(period)+';',c,u.CustomMaterialOutputType.CMOT_FLOAT2)
            dy=self.custom(m,'scan-ddy',BASIS+'return ddy(Q)/'+str(period)+';',c,u.CustomMaterialOutputType.CMOT_FLOAT2)
            blend=self.custom(m,'longitudinal-blend',BLEND,c,u.CustomMaterialOutputType.CMOT_FLOAT1)
            joint=self.custom(m,'recessed-joint',JOINT,{**q,'JointCm':(self.scalar(m,recipe['jointCm']),'')},u.CustomMaterialOutputType.CMOT_FLOAT1)
            samples={}
            for role in ['albedo','normal','roughness','ao']:
                sampler=u.MaterialSamplerType.SAMPLERTYPE_COLOR if role=='albedo' else (u.MaterialSamplerType.SAMPLERTYPE_NORMAL if role=='normal' else u.MaterialSamplerType.SAMPLERTYPE_MASKS)
                pair=[]
                for i in range(2):
                    n=self.node(m,role+'-sample-'+str(i),u.MaterialExpressionTextureSample,texture=self.texture(asset,role),
                        sampler_type=sampler,mip_value_mode=u.TextureMipValueMode.TMVM_DERIVATIVE)
                    for a,pin in [(uv[i],'UVs'),(dx,'DDX(UVs)'),(dy,'DDY(UVs)')]:self.connect(a,'',n,pin)
                    pair.append(n)
                lerp=self.node(m,role+'-blend',u.MaterialExpressionLinearInterpolate)
                for a,ch,pin in [(pair[0],'RGB','A'),(pair[1],'RGB','B'),(blend,'','Alpha')]:self.connect(a,ch,lerp,pin)
                samples[role]=lerp
            color=self.custom(m,'coordinated-timber',WOOD_COLOR,{'Scan':(samples['albedo'],''),'Mean':(self.vector(m,source['maps']['albedo']['meanLinearRGB']),''),
                'Palette':(self.vector(m,recipe['palette']),''),'Contrast':(self.scalar(m,recipe['albedoContrast']),''),
                'Joint':(joint,'')},u.CustomMaterialOutputType.CMOT_FLOAT3)
            nm=self.custom(m,'wood-world-normal',WOOD_NORMAL,{**c,'MapNormal':(samples['normal'],''),'Strength':(self.scalar(m,recipe['normalStrength']),''),'FaceSign':(sign,'')},u.CustomMaterialOutputType.CMOT_FLOAT3)
            rough=self.custom(m,'wood-roughness',WOOD_ROUGH,{'Sample':(samples['roughness'],''),'Mean':(self.scalar(m,source['maps']['roughness']['meanDataR']),''),
                'Base':(self.scalar(m,recipe['roughness']),''),'Joint':(joint,'')},u.CustomMaterialOutputType.CMOT_FLOAT1)
            ao=self.custom(m,'wood-ambient-occlusion',WOOD_AO,{'Scan':(samples['ao'],''),'Joint':(joint,'')},u.CustomMaterialOutputType.CMOT_FLOAT1)
            for node,prop in [(color,'BASE_COLOR'),(nm,'NORMAL'),(rough,'ROUGHNESS'),(ao,'AMBIENT_OCCLUSION')]:self.out(node,'',prop)
        self.out(self.scalar(m,0),'','METALLIC');self.out(self.scalar(m,.5),'','SPECULAR')
        errors=list(self.lib.recompile_material(m));require(not errors,'Exterior shader compilation failed: '+str(errors))
        self.assets.set_metadata_tag(m,'BreziPhotorealRecipe',json.dumps(recipe,sort_keys=True));self.save(m)
        return m


def components(u,ids,actor_system=None):
    result={};actor_system=actor_system or u.get_editor_subsystem(u.EditorActorSubsystem)
    for actor in actor_system.get_all_level_actors():
        keys={str(t) for t in actor.get_editor_property('tags')} & ids
        if not keys:continue
        if actor.actor_has_tag('BreziWalkSupportProxy'):continue
        require(len(keys)==1,'Ambiguous exterior actor identity');key=next(iter(keys))
        require(key not in result,'Duplicate exterior actor identity')
        parts=list(actor.get_components_by_class(u.StaticMeshComponent));require(len(parts)==1,'Exterior target must have one mesh component')
        result[key]=parts[0]
    require(set(result)==ids,'Exterior actor coverage incomplete')
    return result


def geometry_witness(u,parts):
    result={}
    for id_,c in parts.items():
        t=c.get_world_transform();origin,extent,_=u.SystemLibrary.get_component_bounds(c);mesh=c.get_editor_property('static_mesh')
        require(all(abs(getattr(t.scale3d,k)-1)<1e-6 for k in ('x','y','z')),'Exterior physical mapping requires unit scale')
        result[id_]={'mesh':mesh.get_path_name(),'triangles':mesh.get_num_triangles(0),'sections':mesh.get_num_sections(0),
            'position':[round(getattr(t.translation,k),5) for k in ('x','y','z')],
            'rotation':[round(getattr(t.rotation,k),6) for k in ('x','y','z','w')],
            'bounds':[round(getattr(v,k),4) for v in (origin,extent) for k in ('x','y','z')],
            'collision':str(c.get_collision_enabled()),'profile':str(c.get_collision_profile_name()),
            'tags':sorted(map(str,c.get_editor_property('component_tags')))}
    return result


def apply_photoreal_exterior(scene,geometry,source_material_report,actor_system=None):
    import unreal as u
    inputs=load_inputs();targets=prepare_targets(scene,geometry);parts=components(u,{t['id'] for t in targets},actor_system)
    witness=geometry_witness(u,parts);expected={(r['id'],r['index']):r['asset'] for r in source_material_report['bindings']}
    # Validate every target before any package or binding mutation.
    for t in targets:
        c=parts[t['id']];base=c.get_material(t['index']);mesh=c.get_editor_property('static_mesh')
        require(base and base.get_path_name()==expected[(t['id'],t['index'])] and mesh.get_material(t['index'])==base,
            'Exterior source material binding is not the accepted baseline: '+t['name'])
    writer=Writer(u,inputs);cache={};report={'schemaVersion':1,'status':'photoreal-exterior-reload-pending',
        'generatedAt':datetime.now(timezone.utc).isoformat(),'sourceManifestSha256':sha(Path(geometry)/'scene.json'),
        'pipelineFiles':{OWNER:sha(__file__),str(INPUTS.relative_to(ROOT)):sha(INPUTS)},'bindings':[],
        'materials':{},'textures':[],'geometryWitness':witness,'geometryModified':False,'collisionModified':False,
        'savedReloaded':False,'nativeRenderedVerified':False,'scanLicense':'CC0-1.0',
        'limitations':['Photographed Hinoki and Wood Planks are illustrative timber finishes, not verified installed larch species.',
            'Roof color is an illustrative RAL 7016 approximation; no measured paint BRDF or colorimetry is claimed.',
            'Longitudinal stochastic blending suppresses repetition; native close-range and mip visual review is required.',
            'Facade 50 mm virtual joints are shaded detail. Existing 145 mm deck boards and 8 mm physical joints remain source geometry.',
            'AO maps describe microsurface cavities; Lumen/contact shadows and resident texture mips require native visual review.']}
    for t in targets:
        key=digest(t['recipe'])
        if key not in cache:
            m=writer.material(t['recipe']);cache[key]=m
            report['materials'][key]={'asset':m.get_path_name(),'recipe':t['recipe'],'graph':graph_snapshot(u,m)}
        c=parts[t['id']];m=cache[key];original=c.get_material(t['index']).get_path_name();c.set_material(t['index'],m)
        report['bindings'].append({**{k:t[k] for k in ['id','index','sourceSlot','sourceId','name']},
            'asset':m.get_path_name(),'originalAsset':original,'component':c.get_name()})
    require(geometry_witness(u,parts)==witness,'Exterior material assignment changed source geometry/collision')
    report['textures']=[{k:v for k,v in t.items() if k!='object'} for t in writer.textures.values()]
    report['generatedAssets']=sorted(writer.paths)
    path=Path(geometry).parent/'photoreal-exterior-report.json';path.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    return report


def verify_photoreal_exterior(scene,geometry,report,actor_system=None):
    import unreal as u
    require(sha(Path(geometry)/'scene.json')==report['sourceManifestSha256'],'Exterior source manifest changed')
    for relative,expected in report['pipelineFiles'].items():require(sha(ROOT/relative)==expected,'Exterior pipeline changed: '+relative)
    load_inputs();targets=prepare_targets(scene,geometry)
    require({(t['id'],t['index']) for t in targets}=={(t['id'],t['index']) for t in report['bindings']},'Exterior selection changed')
    parts=components(u,{t['id'] for t in targets},actor_system)
    require(geometry_witness(u,parts)==report['geometryWitness'],'Saved exterior geometry/collision changed')
    for row in report['bindings']:
        c=parts[row['id']];m=c.get_material(row['index']);mesh=c.get_editor_property('static_mesh')
        require(m and m.get_path_name()==row['asset'] and c.get_name()==row['component']
            and mesh.get_material(row['index']).get_path_name()==row['originalAsset'],'Exterior component or baseline mesh binding changed')
    for entry in report['materials'].values():
        m=u.EditorAssetLibrary.load_asset(entry['asset'])
        require(m and u.EditorAssetLibrary.get_metadata_tag(m,'BreziGeneratedBy')==OWNER
            and u.EditorAssetLibrary.get_metadata_tag(m,'BreziPhotorealRecipe')==json.dumps(entry['recipe'],sort_keys=True)
            and graph_snapshot(u,m)==entry['graph'],'Saved exterior material graph differs')
    for entry in report['textures']:
        t=u.EditorAssetLibrary.load_asset(entry['asset'])
        require(t and u.EditorAssetLibrary.get_metadata_tag(t,'BreziGeneratedBy')==OWNER
            and u.EditorAssetLibrary.get_metadata_tag(t,'source_sha256')==entry['sha256']
            and bool(t.get_editor_property('srgb'))==entry['srgb']
            and bool(t.get_editor_property('flip_green_channel'))==entry['greenFlipped']
            and str(t.get_editor_property('compression_settings'))==entry['compression']
            and [t.blueprint_get_size_x(),t.blueprint_get_size_y()]==entry['dimensions'],'Saved exterior scan decoding differs')
    report.update(status='photoreal-exterior-saved-reloaded-validated',savedReloaded=True)
    (Path(geometry).parent/'photoreal-exterior-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
    return report
