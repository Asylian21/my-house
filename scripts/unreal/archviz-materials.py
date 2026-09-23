"""Add owned, source-name selected architectural finish detail to current C/B/B.

Integration: baseline source validation first; apply_archviz_materials(scene,
geometry, source_material_report), save/reload map, verify_archviz_materials(...).
The baseline graph/bindings remain intact. Only detail roots are added; no mesh,
collision, transform, door metadata, light or camera changes occur in this module.
"""
import hashlib
import json
import math
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/archviz-materials.py'
INPUTS = ROOT / 'scripts/unreal/archviz-material-inputs.json'
PREFIX = '/Game/Brezi/Archviz/Textures'
SOURCE_OWNER = 'scripts/unreal/model-refresh-import.py'
TAG = 'BreziArchvizDetail:'


def require(ok, message):
    if not ok: raise RuntimeError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def load_inputs():
    data = json.loads(INPUTS.read_text())
    require(data['schemaVersion'] == 1, 'Unknown detail input schema')
    for name, asset in data['assets'].items():
        for role, spec in asset['maps'].items():
            path = (ROOT / spec['path']).resolve()
            require(path.is_relative_to(ROOT) and path.is_file() and sha(path) == spec['sha256'], 'Changed/missing detail map: ' + name + '/' + role)
            if spec.get('md5'): require(hashlib.md5(path.read_bytes()).hexdigest() == spec['md5'], 'CC0 download identity differs')
    return data


def recipe(source):
    """Bound semantic names/texture families; never captured DOM/MAT ordinals."""
    name, texture = source['name'].lower(), source.get('texture') or ''
    r = {'roughness': source['roughness'], 'normalStrength': .22, 'roughnessAmplitude': .045,
         'microSlope': .012, 'microPeriodCm': .12, 'albedoStrength': 0., 'normalSpace': 'local',
         'geometryModified': False, 'sourcePaletteRetained': True}
    if source['alpha'] < .999: return None
    if any(texture.endswith('/' + t + '-albedo.jpg') for t in ['living-natural-oak', 'oak-veneer', 'vinyl-oak']):
        r.update(kind='photo-oak', asset='oak_veneer_01', normalStrength=.38,
                 roughnessAmplitude=.17, albedoStrength=.35, microSlope=.007,
                 sourceNormal='vinyl-oak' if texture.endswith('/vinyl-oak-albedo.jpg') else None)
    elif name in ['real-wall', 'real-soffit', 'real-interior-wall', 'real-interior-plaster', 'real-interior-ceiling']:
        r.update(kind='photo-plaster', asset='white_plaster_02', normalStrength=.21,
                 roughnessAmplitude=.10, albedoStrength=.025, microSlope=.006)
    elif name in ['real-concrete', 'real-paving', 'real-paving-entry']:
        r.update(kind='photo-concrete', asset='concrete_pavement', normalStrength=.32,
                 roughnessAmplitude=.16, albedoStrength=.05, microSlope=.013)
    elif texture.endswith('/tile-porcelain-albedo.jpg') or texture.endswith('/tile-wall-albedo.jpg'):
        r.update(kind='source-tile', sourceNormal='tile-porcelain' if 'porcelain' in texture else 'tile-wall',
                 normalStrength=.48, microSlope=.006, normalSpace='tangent')
    elif texture.endswith('/stone-dark-albedo.jpg') or texture.endswith('/living-warm-stone-albedo.jpg'):
        r.update(kind='source-stone', sourceNormal='stone-dark', normalStrength=.38,
                 microSlope=.008, roughnessAmplitude=.055, normalSpace='tangent')
    elif name in ['real-interior-epoxy']:
        r.update(kind='source-epoxy', sourceNormal='epoxy-grey', normalStrength=.32, microSlope=.004, normalSpace='tangent')
    elif name in ['kitchen 2026 · kartáčovaná oceľ', 'real-interior-steel', 'real-interior-brushed-brass', 'real-office-desk-black-steel', 'real-technical-copper']:
        r.update(kind='brushed-metal', microPeriodCm=.06, microSlope=.02, roughnessAmplitude=.06)
    elif name in ['real-glass-frame', 'real-fence-metal', 'real-roof-edge', 'real-interior-fireplace',
                  'real-interior-door-leaf', 'real-interior-door-frame', 'real-interior-skirting',
                  'kitchen 2026 · zapustené profily', 'kitchen-pendant · graphite anodised aluminium']:
        r.update(kind='coated-finish', microPeriodCm=.09, microSlope=.005, roughnessAmplitude=.025)
    else: return None
    if r['normalSpace'] == 'local': r['twoSidedWorldNormalCorrected'] = True
    return r


# Right-handed object-local basis. V runs down the vertical faces and along
# -X on horizontal surfaces. Texture pixels/normal handedness remain consistent.
BASIS = '''
float3 n = normalize(LocalNormal);
float3 a = abs(n), T, V;
if (a.x >= a.y && a.x >= a.z) { T=float3(0,-sign(n.x),0); V=float3(0,0,-1); }
else if (a.y >= a.z) { T=float3(sign(n.y),0,0); V=float3(0,0,-1); }
else { T=float3(0,sign(n.z),0); V=float3(-1,0,0); }
'''
PROJECTION = BASIS + 'return float2(dot(LocalPosition,T),dot(LocalPosition,V)) / PeriodCm;'
DETAIL = BASIS + '''
float2 p = float2(dot(LocalPosition,T),dot(LocalPosition,V)) / MicroPeriodCm;
float fade = 1.0-smoothstep(.18,.48,max(fwidth(p.x),fwidth(p.y)));
float variation = (sin(p.x*6.2831853 + sin(p.y*.47))*.6 + sin(p.y*4.4429)*.4)*fade;
float sx = cos(p.x*6.2831853 + sin(p.y*.47))*MicroSlope*fade;
float sy = cos(p.y*4.4429)*MicroSlope*.3*fade;
float3 detail = normalize(float3(SourceNormal.xy*NormalStrength, max(SourceNormal.z,.1)) + float3(sx,sy,0));
float3 result = TangentMode > .5 ? detail : normalize(n*detail.z + T*detail.x + V*detail.y);
float rough = clamp(BaseRoughness + (RoughSample-RoughMean)*RoughAmplitude + variation*RoughAmplitude*.25,.06,.99);
return float4(result,rough);
'''
COLOR = '''
// A grayscale scan detail modulates the existing color; it cannot recolor oak
// or turn black worktops into a new stone. Mean calibration is input-pinned.
float ratio=dot(Scan,float3(.2126,.7152,.0722))/max(MeanLuminance,.001);
return saturate(BaseColor * clamp(1.0 + Strength*(ratio-1.0),.72,1.28));
'''


def properties(u):
    return {name: getattr(u.MaterialProperty, 'MP_' + name) for name in ['BASE_COLOR','ROUGHNESS','NORMAL','METALLIC','OPACITY','OPACITY_MASK','EMISSIVE_COLOR']}


def graph_snapshot(u, material, original_only=False):
    lib = u.MaterialEditingLibrary
    nodes = list(lib.get_material_expressions(material))
    values = []
    fields = {'MaterialExpressionConstant':['r'], 'MaterialExpressionConstant3Vector':['constant'],
        'MaterialExpressionTextureCoordinate':['coordinate_index','u_tiling','v_tiling','un_mirror_u','un_mirror_v'],
        'MaterialExpressionCustom':['code','description','output_type'],
        'MaterialExpressionTextureSample':['texture','sampler_type'],
        'MaterialExpressionTransform':['transform_source_type','transform_type'],
        'MaterialExpressionTransformPosition':['transform_source_type','transform_type'],
        'MaterialExpressionComponentMask':['r','g','b','a']}
    def scalar(v):
        if isinstance(v, bool) or isinstance(v, int) or isinstance(v, str): return v
        if isinstance(v, float): return round(v, 7)
        if hasattr(v, 'r') and hasattr(v, 'g'): return [round(getattr(v, k), 7) for k in ['r','g','b','a']]
        if hasattr(v, 'get_path_name'): return v.get_path_name()
        return str(v)
    for node in nodes:
        if original_only and str(node.get_editor_property('desc')).startswith(TAG): continue
        cls = node.get_class().get_name()
        values.append({'name': node.get_name(), 'class': cls,
            'fields': {key: scalar(node.get_editor_property(key)) for key in fields.get(cls, [])},
            'inputs': [entry.get_name() if entry else None for entry in lib.get_inputs_for_material_expression(material, node)]})
    result = {'nodes': sorted(values, key=lambda r:r['name'])}
    if not original_only:
        result['roots'] = {key: (node.get_name() if node else None) for key, prop in properties(u).items()
                           for node in [lib.get_material_property_input_node(material, prop)]}
        result['tangentSpaceNormal'] = bool(material.get_editor_property('tangent_space_normal'))
        result['blend'] = str(material.get_editor_property('blend_mode'))
    return result


class DetailWriter:
    def __init__(self, u, inputs):
        self.u=u; self.inputs=inputs; self.lib=u.MaterialEditingLibrary; self.assets=u.EditorAssetLibrary
        self.tools=u.AssetToolsHelpers.get_asset_tools(); self.textures={}

    def node(self, material, name, cls, **props):
        node=self.lib.create_material_expression(material, cls, -800, 0)
        require(node is not None, 'Could not create archviz node '+name)
        node.set_editor_property('desc', TAG+name)
        for key,value in props.items(): node.set_editor_property(key,value)
        return node

    def scalar(self,m,value): return self.node(m,'scalar',self.u.MaterialExpressionConstant,r=float(value))
    def vector(self,m,values): return self.node(m,'vector',self.u.MaterialExpressionConstant3Vector,constant=self.u.LinearColor(*values,1))
    def connect(self,a,output,b,pin): require(self.lib.connect_material_expressions(a,output,b,pin),'Could not connect detail graph '+pin)
    def output(self,node,pin,prop): require(self.lib.connect_material_property(node,pin,prop),'Could not attach archviz output')
    def custom(self,m,name,code,inputs,output_type):
        pins=[]
        for key in inputs:
            pin=self.u.CustomInput();pin.set_editor_property('input_name',key);pins.append(pin)
        node=self.node(m,name,self.u.MaterialExpressionCustom,inputs=pins,code=code,description=TAG+name,output_type=output_type)
        for key,(source,output) in inputs.items():self.connect(source,output,node,key)
        return node

    def texture(self,asset,role):
        key=(asset,role)
        if key in self.textures:return self.textures[key]['object']
        spec=self.inputs['assets'][asset]['maps'][role];path=ROOT/spec['path'];u=self.u
        name='T_'+asset+'_'+role+'_'+spec['sha256'][:12]; package=PREFIX+'/'+name
        require(not self.assets.does_asset_exist(package),'Archviz detail requires a fresh owned namespace: '+package)
        task=u.AssetImportTask()
        for prop,value in {'filename':str(path),'destination_path':PREFIX,'destination_name':name,'automated':True,
            'save':False,'replace_existing':False,'factory':u.TextureFactory()}.items():task.set_editor_property(prop,value)
        self.tools.import_asset_tasks([task]);objects=task.get_objects()
        require(len(objects)==1 and isinstance(objects[0],u.Texture2D),'Archviz texture import failed')
        texture=objects[0]
        texture.set_editor_property('srgb',role=='albedo')
        texture.set_editor_property('compression_settings',{'normal':u.TextureCompressionSettings.TC_NORMALMAP,'roughness':u.TextureCompressionSettings.TC_MASKS}.get(role,u.TextureCompressionSettings.TC_DEFAULT))
        texture.set_editor_property('flip_green_channel',role=='normal')
        texture.set_editor_property('address_x',u.TextureAddress.TA_WRAP);texture.set_editor_property('address_y',u.TextureAddress.TA_WRAP)
        self.assets.set_metadata_tag(texture,'BreziGeneratedBy',OWNER)
        self.assets.set_metadata_tag(texture,'source_path',spec['path']);self.assets.set_metadata_tag(texture,'source_sha256',spec['sha256'])
        require(self.assets.save_loaded_asset(texture,only_if_is_dirty=False),'Archviz texture save failed')
        self.textures[key]={'object':texture,'asset':texture.get_path_name(),'source':spec['path'],'sha256':spec['sha256'],'role':role,
            'srgb':role=='albedo','normalGreenFlipped':role=='normal','license':self.inputs['assets'][asset]['license'],
            'providerPage':self.inputs['assets'][asset].get('page'),'compression':str(texture.get_editor_property('compression_settings'))}
        return texture

    def sample(self,m,asset,role,uv):
        node=self.node(m,asset+'-'+role,self.u.MaterialExpressionTextureSample,texture=self.texture(asset,role),
            sampler_type={'normal':self.u.MaterialSamplerType.SAMPLERTYPE_NORMAL,'roughness':self.u.MaterialSamplerType.SAMPLERTYPE_MASKS}.get(role,self.u.MaterialSamplerType.SAMPLERTYPE_COLOR))
        self.connect(uv,'',node,'UVs');return node

    def face_world_normal(self, material, normal):
        # UE flips tangent-space normals on backfaces automatically, but does
        # not flip a custom world-space normal. DOUBLESIDE source triangles can
        # share a plane with reversed winding, so either winding must shade as
        # the visible face. Leave tangent-space materials on the engine path.
        sign=self.node(material,'world-normal-face-sign',self.u.MaterialExpressionTwoSidedSign)
        facing=self.node(material,'world-normal-facing',self.u.MaterialExpressionMultiply)
        self.connect(normal,'',facing,'A');self.connect(sign,'',facing,'B')
        return facing

    def apply(self,material,r):
        u=self.u; props=properties(u)
        original=graph_snapshot(u,material,True); base=self.lib.get_material_property_input_node(material,props['BASE_COLOR'])
        require(base is not None and self.lib.get_material_property_input_node(material,props['NORMAL']) is None,'Expected baseline source graph without an existing normal')
        world=self.node(material,'world-position',u.MaterialExpressionWorldPosition)
        position=self.node(material,'local-position',u.MaterialExpressionTransformPosition,
            transform_source_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD,
            transform_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL)
        self.connect(world,'',position,'')
        world_normal=self.node(material,'vertex-normal',u.MaterialExpressionVertexNormalWS)
        normal=self.node(material,'local-normal',u.MaterialExpressionTransform,
            transform_source_type=u.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_WORLD,
            transform_type=u.MaterialVectorCoordTransform.TRANSFORM_LOCAL)
        self.connect(world_normal,'',normal,'')
        coords={'LocalPosition':(position,''),'LocalNormal':(normal,'')}
        source_normal=(self.vector(material,[0,0,1]),'');rough=(self.scalar(material,.5),'');rough_mean=.5
        if r.get('asset'):
            asset=self.inputs['assets'][r['asset']]
            uv=self.custom(material,'physical-uv',PROJECTION,{**coords,'PeriodCm':(self.scalar(material,asset['periodCm']), '')},u.CustomMaterialOutputType.CMOT_FLOAT2)
            source_normal=(self.sample(material,r['asset'],'normal',uv),'RGB')
            rough=(self.sample(material,r['asset'],'roughness',uv),'R');rough_mean=asset['maps']['roughness']['meanDataR']
            if r['albedoStrength']:
                color=self.sample(material,r['asset'],'albedo',uv)
                mean=sum(a*b for a,b in zip(asset['maps']['albedo']['meanLinearRGB'],[.2126,.7152,.0722]))
                overlay=self.custom(material,'palette-grain',COLOR,{'BaseColor':(base,''),'Scan':(color,'RGB'),
                    'MeanLuminance':(self.scalar(material,mean),''),'Strength':(self.scalar(material,r['albedoStrength']),'')},u.CustomMaterialOutputType.CMOT_FLOAT3)
                self.output(overlay,'',props['BASE_COLOR'])
        if r.get('sourceNormal'):
            mappings=[n for n in self.lib.get_material_expressions(material) if isinstance(n,u.MaterialExpressionCustom)
                and n.get_editor_property('description')=='BreziModelRefreshSourceUV']
            require(len(mappings)==1,'Source UV normal requires one original UV mapping')
            uvnormal=(self.sample(material,r['sourceNormal'],'normal',mappings[0]),'RGB')
            if r.get('asset'):
                # The floor's existing UV normal carries plank joints. Convert
                # it to local space before adding photographic pore detail.
                converted=self.node(material,'source-normal-local',u.MaterialExpressionTransform,
                    transform_source_type=u.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_TANGENT,
                    transform_type=u.MaterialVectorCoordTransform.TRANSFORM_LOCAL)
                self.connect(*uvnormal,converted,'')
                combined=self.custom(material,'source-joints',BASIS+'return normalize(LocalNormal + (JointNormal-LocalNormal)*.4);',
                    {**coords,'JointNormal':(converted,'')},u.CustomMaterialOutputType.CMOT_FLOAT3)
                coords['LocalNormal']=(combined,'')
            else:source_normal=uvnormal
        detail=self.custom(material,'finish',DETAIL,{**coords,'SourceNormal':source_normal,'RoughSample':rough,
            'RoughMean':(self.scalar(material,rough_mean),''),'BaseRoughness':(self.scalar(material,r['roughness']),''),
            'NormalStrength':(self.scalar(material,r['normalStrength']),''),'RoughAmplitude':(self.scalar(material,r['roughnessAmplitude']),''),
            'MicroPeriodCm':(self.scalar(material,r['microPeriodCm']),''),'MicroSlope':(self.scalar(material,r['microSlope']),''),
            'TangentMode':(self.scalar(material,1 if r['normalSpace']=='tangent' else 0),'')},u.CustomMaterialOutputType.CMOT_FLOAT4)
        nm=self.node(material,'normal-channel',u.MaterialExpressionComponentMask,r=True,g=True,b=True,a=False);self.connect(detail,'',nm,'')
        rf=self.node(material,'roughness-channel',u.MaterialExpressionComponentMask,r=False,g=False,b=False,a=True);self.connect(detail,'',rf,'')
        material.set_editor_property('tangent_space_normal',r['normalSpace']=='tangent')
        if r['normalSpace']=='local':
            transformed=self.node(material,'normal-world',u.MaterialExpressionTransform,
                transform_source_type=u.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_LOCAL,transform_type=u.MaterialVectorCoordTransform.TRANSFORM_WORLD)
            self.connect(nm,'',transformed,'');nm=self.face_world_normal(material,transformed)
        self.output(nm,'',props['NORMAL']);self.output(rf,'',props['ROUGHNESS'])
        self.lib.set_base_material_usage(material,u.MaterialUsage.MATUSAGE_NANITE,True)
        require(not list(self.lib.recompile_material(material)),'Native archviz detail compile failed: '+material.get_path_name())
        require(graph_snapshot(u,material,True)==original,'Enhancement modified original source graph')
        return original



def geometry_witness(u, source_ids):
    result = {}
    for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        ids = {str(tag) for tag in actor.get_editor_property('tags')} & source_ids
        if not ids: continue
        require(len(ids) == 1, 'Ambiguous geometry witness identity')
        id_ = next(iter(ids)); require(id_ not in result, 'Duplicate source geometry witness')
        parts=[]
        for c in actor.get_components_by_class(u.StaticMeshComponent):
            t=c.get_world_transform();scale=t.scale3d
            require(all(abs(getattr(scale,k)-1) < 1e-6 for k in ('x','y','z')), 'Physical finish projection requires unit native scale')
            origin,extent,_=u.SystemLibrary.get_component_bounds(c)
            parts.append({'mesh':c.get_editor_property('static_mesh').get_path_name(),
                'translation':[round(getattr(t.translation,k),6) for k in ('x','y','z')],
                'rotation':[round(getattr(t.rotation,k),6) for k in ('x','y','z','w')],
                'scale':[round(getattr(scale,k),6) for k in ('x','y','z')],
                'bounds':[round(getattr(v,k),5) for v in (origin,extent) for k in ('x','y','z')],
                'collision':str(c.get_collision_enabled()),'profile':str(c.get_collision_profile_name()),
                'tags':sorted(map(str,c.get_editor_property('component_tags')))})
        result[id_]=parts
    require(set(result)==source_ids,'Geometry witness coverage differs')
    return result


def write_receipt(geometry,report):
    path=Path(geometry).parent/'archviz-materials-report.json'
    path.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')


def apply_archviz_materials(scene, geometry, source_material_report):
    import unreal as u
    require(scene.get('activeDesign')=={'variant':'C','heatingLayout':'B','livingLayout':'B'},'Archviz requires explicit current C/B/B')
    inputs=load_inputs();writer=DetailWriter(u,inputs); planned=[]
    witness=geometry_witness(u,{r['id'] for r in source_material_report['bindings']})
    # Validate the full selected graph ownership/source binding before mutation.
    for slot,entry in sorted(source_material_report['materials'].items()):
        source=scene['materials'][slot];r=recipe(source)
        if not r:continue
        material=u.EditorAssetLibrary.load_asset(entry['asset'])
        require(material is not None and entry['asset'].startswith('/Game/Brezi/ModelRefresh/Materials/M_MAT_')
            and u.EditorAssetLibrary.get_metadata_tag(material,'BreziGeneratedBy')==SOURCE_OWNER
            and u.EditorAssetLibrary.get_metadata_tag(material,'source_recipe_json')==json.dumps(entry['recipe'],sort_keys=True)
            and not u.EditorAssetLibrary.get_metadata_tag(material,'BreziArchvizRecipe'),'Source material is not a pristine owned baseline: '+slot)
        planned.append((slot,material,source,r))
    require(planned,'No current architectural finish materials resolved')
    report={'schemaVersion':1,'status':'archviz-materials-authored-reload-pending','generatedAt':datetime.now(timezone.utc).isoformat(),
        'sourceManifestSha256':sha(Path(geometry)/'scene.json'),'materials':{},'textures':[],
        'pipelineFiles':{OWNER:sha(__file__),'scripts/unreal/archviz-material-inputs.json':sha(INPUTS)},
        'bindings':source_material_report['bindings'],'geometryWitness':witness,'geometryModified':False,'collisionModified':False,
        'limitations':['Photographed CC0 scan details are illustrative finish choices, not measurements of a selected installed product.',
            'Albedo hue/UV/palette remain sourced; photographed detail is mean-centered grayscale modulation capped at0.72–1.28.',
            'Microfinish is authored and derivative-filtered. No displacement, changed joints, changed geometry or optical glass calibration.',
            'Source glass tint/alpha/roughness and emissive materials are preserved. Native Metal rendered review is separate.'],
        'nativeRenderedVerified':False,'savedReloaded':False}
    for slot,material,source,r in planned:
        original=writer.apply(material,r)
        u.EditorAssetLibrary.set_metadata_tag(material,'BreziArchvizRecipe',json.dumps(r,sort_keys=True))
        require(u.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False),'Archviz material save failed')
        report['materials'][slot]={'asset':material.get_path_name(),'sourceName':source['name'],'recipe':r,
            'originalGraph':original,'graph':graph_snapshot(u,material),'sourceRecipe':source_material_report['materials'][slot]['recipe'],
            'naniteUsage':bool(u.MaterialEditingLibrary.has_material_usage(material,u.MaterialUsage.MATUSAGE_NANITE))}
    report['textures']=[{k:v for k,v in entry.items() if k!='object'} for entry in writer.textures.values()]
    require(geometry_witness(u,set(witness))==witness,'Detail authoring modified geometry/collision')
    write_receipt(geometry,report);return report


def repair_world_normal_facing(scene, geometry, previous):
    """One explicit migration of the accepted pre-sign graphs; caller pins the
    previous complete native receipt and archives all target packages first.
    This function cannot recreate materials or change any existing graph node.
    """
    import copy
    import unreal as u
    require(previous['status']=='archviz-materials-saved-reloaded-validated','Normal repair requires validated prior detail graphs')
    require(previous['sourceManifestSha256']==sha(Path(geometry)/'scene.json'),'Normal repair source changed')
    writer=DetailWriter(u,load_inputs());planned=[]
    for slot,entry in sorted(previous['materials'].items()):
        old_recipe=entry['recipe'];new_recipe=recipe(scene['materials'][slot])
        expected={**old_recipe,'twoSidedWorldNormalCorrected':True} if old_recipe['normalSpace']=='local' else old_recipe
        require(new_recipe==expected,'Normal repair would change another finish recipe: '+slot)
        material=u.EditorAssetLibrary.load_asset(entry['asset'])
        require(material and graph_snapshot(u,material)==entry['graph']
            and graph_snapshot(u,material,True)==entry['originalGraph'],'Normal repair prior graph differs: '+slot)
        require(u.EditorAssetLibrary.get_metadata_tag(material,'BreziGeneratedBy')==SOURCE_OWNER
            and u.EditorAssetLibrary.get_metadata_tag(material,'BreziArchvizRecipe')==json.dumps(old_recipe,sort_keys=True),
            'Normal repair material ownership/recipe differs: '+slot)
        if old_recipe['normalSpace']!='local':continue
        require(not old_recipe.get('twoSidedWorldNormalCorrected'),'Normal facing repair is already applied')
        normal=u.MaterialEditingLibrary.get_material_property_input_node(material,u.MaterialProperty.MP_NORMAL)
        require(isinstance(normal,u.MaterialExpressionTransform)
            and normal.get_editor_property('transform_source_type')==u.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_LOCAL
            and normal.get_editor_property('transform_type')==u.MaterialVectorCoordTransform.TRANSFORM_WORLD
            and not material.get_editor_property('tangent_space_normal'),'Prior normal is not the expected world-space detail output')
        planned.append((slot,entry,material,normal,new_recipe))
    require(planned,'No accepted world-space normal roots require repair')
    report=copy.deepcopy(previous)
    for slot,entry,material,normal,new_recipe in planned:
        writer.output(writer.face_world_normal(material,normal),'',u.MaterialProperty.MP_NORMAL)
        require(not list(u.MaterialEditingLibrary.recompile_material(material)),'World normal repair compile failed: '+slot)
        after=graph_snapshot(u,material)
        before_nodes={node['name']:node for node in entry['graph']['nodes']}
        after_nodes={node['name']:node for node in after['nodes']}
        require(all(after_nodes.get(name)==node for name,node in before_nodes.items())
            and len(after_nodes)==len(before_nodes)+2,'Normal repair modified an existing graph node: '+slot)
        require(all(after['roots'][name]==root for name,root in entry['graph']['roots'].items() if name!='NORMAL')
            and after['blend']==entry['graph']['blend'] and after['tangentSpaceNormal']==entry['graph']['tangentSpaceNormal'],
            'Normal repair modified another material output: '+slot)
        u.EditorAssetLibrary.set_metadata_tag(material,'BreziArchvizRecipe',json.dumps(new_recipe,sort_keys=True))
        require(u.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False),'World normal repair save failed')
        report['materials'][slot].update(recipe=new_recipe,graph=after)
    report['pipelineFiles'][OWNER]=sha(__file__)
    report.update(status='archviz-materials-authored-reload-pending',savedReloaded=False,nativeRenderedVerified=False,
        normalFacingRepair={'kind':'explicit-two-sided-sign-for-world-normal-only','materialSlots':[slot for slot,*_ in planned],
            'unchangedTangentMaterialCount':len(report['materials'])-len(planned),'existingGraphNodesPreserved':True})
    return report


def verify_archviz_materials(scene, geometry, report):
    import unreal as u
    require(report['sourceManifestSha256']==sha(Path(geometry)/'scene.json'),'Archviz source changed')
    for path,expected in report['pipelineFiles'].items():require(sha(ROOT/path)==expected,'Archviz recipe writer changed')
    load_inputs()
    require(geometry_witness(u,set(report['geometryWitness']))==report['geometryWitness'],'Saved archviz geometry/collision changed')
    facing_count=0
    for slot,entry in report['materials'].items():
        material=u.EditorAssetLibrary.load_asset(entry['asset'])
        require(material is not None and graph_snapshot(u,material)==entry['graph'],'Saved archviz material graph differs: '+slot)
        require(graph_snapshot(u,material,True)==entry['originalGraph'],'Saved source base graph changed: '+slot)
        require(u.EditorAssetLibrary.get_metadata_tag(material,'BreziArchvizRecipe')==json.dumps(entry['recipe'],sort_keys=True)
            and u.EditorAssetLibrary.get_metadata_tag(material,'source_recipe_json')==json.dumps(entry['sourceRecipe'],sort_keys=True)
            and u.MaterialEditingLibrary.has_material_usage(material,u.MaterialUsage.MATUSAGE_NANITE),'Saved material metadata/Nanite usage changed')
        if entry['recipe']['normalSpace']=='local':
            root=u.MaterialEditingLibrary.get_material_property_input_node(material,u.MaterialProperty.MP_NORMAL)
            require(entry['recipe'].get('twoSidedWorldNormalCorrected') and isinstance(root,u.MaterialExpressionMultiply)
                and root.get_editor_property('desc')==TAG+'world-normal-facing','World normal lacks explicit face correction: '+slot)
            pins=[str(name) for name in u.MaterialEditingLibrary.get_material_expression_input_names(root)]
            inputs=list(u.MaterialEditingLibrary.get_inputs_for_material_expression(material,root))
            require(pins.count('A')==1 and pins.count('B')==1,'World normal facing pins differ')
            normal,sign=inputs[pins.index('A')],inputs[pins.index('B')]
            require(isinstance(normal,u.MaterialExpressionTransform)
                and normal.get_editor_property('transform_source_type')==u.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_LOCAL
                and normal.get_editor_property('transform_type')==u.MaterialVectorCoordTransform.TRANSFORM_WORLD
                and isinstance(sign,u.MaterialExpressionTwoSidedSign)
                and sign.get_editor_property('desc')==TAG+'world-normal-face-sign',
                'World normal must multiply the local-to-world result by TwoSidedSign: '+slot)
            facing_count+=1
    for entry in report['textures']:
        texture=u.EditorAssetLibrary.load_asset(entry['asset'])
        require(texture is not None and u.EditorAssetLibrary.get_metadata_tag(texture,'BreziGeneratedBy')==OWNER
            and u.EditorAssetLibrary.get_metadata_tag(texture,'source_sha256')==entry['sha256']
            and texture.get_editor_property('srgb')==entry['srgb']
            and texture.get_editor_property('flip_green_channel')==entry['normalGreenFlipped']
            and str(texture.get_editor_property('compression_settings'))==entry['compression'],'Saved texture data/normal convention differs')
    expected={(r['id'],r['index']):r['asset'] for r in report['bindings']};seen=set();source_ids={key[0] for key in expected}
    for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        ids=[str(tag) for tag in actor.get_editor_property('tags') if str(tag) in source_ids]
        if not ids:continue
        require(len(ids)==1,'Ambiguous source material actor')
        for component in actor.get_components_by_class(u.StaticMeshComponent):
            if actor.actor_has_tag('BreziWalkSupportProxy'):continue
            for index in range(component.get_num_materials()):
                key=(ids[0],index);material=component.get_material(index);mesh=component.get_editor_property('static_mesh')
                require(key in expected and material and material.get_path_name()==expected[key] and mesh.get_material(index)==material,'Archviz changed source binding/override')
                seen.add(key)
    require(seen==set(expected),'Archviz source material binding coverage differs')
    report.update(status='archviz-materials-saved-reloaded-validated',savedReloaded=True,verifiedAt=datetime.now(timezone.utc).isoformat(),
        worldNormalFacing={'verifiedMaterialCount':facing_count,'operation':'local-to-world normal multiplied by TwoSidedSign',
            'tangentMaterialCount':len(report['materials'])-facing_count,'tangentNormalsUseEngineFaceCorrection':True})
    write_receipt(geometry,report);return report
