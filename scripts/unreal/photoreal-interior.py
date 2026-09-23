"""Owned C/B/B cloth, stone and glass component overrides; no mesh mutation.

Run apply_photoreal_interior(scene, geometry, baseline_report) in an isolated
copy of the accepted native map, then save/reload and call verify_photoreal_interior.
The source mesh slots, geometry, source material assets and collisions stay intact.
"""
import hashlib
import importlib.util
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/photoreal-interior.py'
INPUTS = ROOT / 'scripts/unreal/photoreal-interior-inputs.json'
PREFIX = '/Game/Brezi/Photoreal/Interior'
TAG = 'BreziPhotorealInterior:'
EXPECTED_DESIGN = {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}
CLOTH_NAMES = {'real-office-chair-fabric', 'real-interior-upholstery',
    'real-interior-accent-fabric', 'C-BOY-109-woven-bed-upholstery',
    'C-GIRL-108-woven-bed-upholstery', 'Living warm sofa | real-interior-upholstery',
    'Living warm accent | real-interior-accent-fabric',
    'Living warm fabric | real-interior-upholstery', 'real-fabric', 'real-upholstery-dark'}
STONE_NAMES = {'Kitchen 2026 · čierny kameň · saténový povrch',
    'real-interior-worktop', 'real-interior-media-stone',
    'Living warm stone | real-interior-media-stone', 'Living warm stone | real-interior-worktop'}
GLASS_NAMES = {'real-glass', 'real-bathroom-shower-glass'}


def require(ok, message):
    if not ok: raise RuntimeError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def digest(value): return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def helper():
    spec = importlib.util.spec_from_file_location('brezi_photoreal_finish_helper', ROOT / 'scripts/unreal/archviz-materials.py')
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def inputs():
    data = json.loads(INPUTS.read_text())
    require(data['schemaVersion'] == 1, 'Unknown interior texture manifest')
    for asset in data['assets'].values():
        require(asset['license'] == 'CC0-1.0', 'Interior scan license changed')
        for role, spec in asset['maps'].items():
            path = (ROOT / spec['path']).resolve()
            require(path.is_relative_to(ROOT) and path.is_file() and sha(path) == spec['sha256'], 'Missing or changed interior texture: ' + role)
            require(hashlib.md5(path.read_bytes()).hexdigest() == spec['md5'], 'Interior provider checksum differs')
            require(min(spec['width'], spec['height']) >= 2048, 'Interior scan resolution below2K')
    for path,spec in data.get('solidPaletteSources',{}).items():
        require(sha(ROOT/path)==spec['sha256'],'Source cloth palette texture changed')
    return data


def solid_palette(source):
    color=source['color']
    if not source.get('texture'):return list(color)
    # Source export already stores linear PBR multipliers. Decode the old sRGB
    # texture only once, offline, and keep its mean; never sample its pattern.
    path='public'+source['texture']
    palette=json.loads(INPUTS.read_text())['solidPaletteSources'].get(path)
    require(palette is not None,'Cloth source palette has no audited mean: '+path)
    return [round(a*b,8) for a,b in zip(color,palette['meanLinearRGB'])]


def recipe(source):
    name = source['name']
    if name in CLOTH_NAMES:
        require(source['alpha'] == 1 and source['metallic'] == 0, 'Cloth source classification changed')
        return {'kind': 'woven-linen', 'scan': 'rough_linen', 'roughness': .86,
            'roughnessVariation': .16, 'normalStrength': .48, 'colorVariation': .08,
            'clothMask': .38, 'fuzzColorScale': .20, 'specular': .32,
            'projection': 'object-local metric smooth triplanar', 'sourcePaletteRetained': True,
            'solidColorLinear':solid_palette(source),'sourceTexturePatternRemoved':True}
    if name in STONE_NAMES:
        return {'kind': 'honed-stone', 'roughness': .46 if (source.get('texture') or '').endswith('/stone-dark-albedo.jpg') else .58,
            'roughnessVariation': .024, 'specular': .45,
            'normalPolicy': 'retain accepted source stone normal graph', 'sourcePaletteRetained': True}
    if name in GLASS_NAMES:
        return {'kind': 'architectural-thin-glass', 'ior': 1.52,
            'specular': ((1.52 - 1) / (1.52 + 1)) ** 2 / .08,
            'roughness': .022, 'transmittance': [.986, .994, .990],
            'opacity': 0., 'twoSided': False, 'refraction': 'RM_NONE',
            'coverage': 'outward shell only; reject inward duplicate faces',
            'opticalModel': 'front-interface reflection and two-interface Fresnel transmission attenuation',
            'spatiallyResolvedDoubleGlazing': False}
    return None


def selected_bindings(scene, baseline_report):
    baseline = baseline_report['materials'] if 'bindings' not in baseline_report else baseline_report
    records = {r['id']: r for r in scene['objects']}
    result = []
    for binding in baseline['bindings']:
        source = scene['materials'][binding['sourceSlot']]; r = recipe(source)
        if not r: continue
        record = records[binding['id']]
        # This source slot is intentionally also used by a thin sink-water layer.
        if source['name'] == 'real-bathroom-shower-glass' and 'UTILITY-SINK' in record['sourceId']: continue
        if r['kind'] == 'architectural-thin-glass':
            dimensions = sorted(b-a for a,b in zip(record['boundsMm']['min'], record['boundsMm']['max']))
            require(record['triangles'] in (12,16) and abs(dimensions[0] - (24 if source['name']=='real-glass' else 15)) < .02,
                    'Glass is no longer a reviewed thin closed shell: ' + record['sourceId'])
        result.append({**binding, 'sourceName': source['name'], 'sourceId': record['sourceId'], 'recipe': r})
    require(all(any(b['recipe']['kind'] == k for b in result) for k in ['woven-linen','honed-stone','architectural-thin-glass']),
            'Interior material scope lacks cloth, stone or glazing')
    return result


def glass_source_audit(scene, geometry, bindings):
    """Verify each glass shell has only outward or reversed duplicate triangles.

    OBJ normals and triangle centroids expose the doubled gable prism; the
    shader coverage gate rejects its inward duplicate faces without mesh edits.
    """
    ids = {b['id'] for b in bindings if b['recipe']['kind']=='architectural-thin-glass'}
    records = {r['id']:r for r in scene['objects']}; vertices=[None]; normals=[None]; active=None
    result={id_: {'outward':0,'inward':0,'degenerate':0} for id_ in ids}
    for line in (Path(geometry)/'dom-mm.obj').read_text().splitlines():
        p=line.split()
        if not p:continue
        if p[0]=='v':vertices.append([float(x) for x in p[1:4]])
        elif p[0]=='vn':normals.append([float(x) for x in p[1:4]])
        elif p[0]=='o':active=p[1] if p[1] in ids else None
        elif p[0]=='f' and active:
            require(len(p)==4,'Glass source no longer triangulated')
            v=[vertices[int(x.split('/')[0])] for x in p[1:]]
            n=[normals[int(x.split('/')[2])] for x in p[1:]]
            center=[(a+b)/2 for a,b in zip(records[active]['boundsMm']['min'],records[active]['boundsMm']['max'])]
            score=sum((sum(pt[k] for pt in v)/3-center[k])*sum(nn[k] for nn in n)/3 for k in range(3))
            result[active]['outward' if score>1e-4 else 'inward' if score < -1e-4 else 'degenerate']+=1
    for id_, entry in result.items():
        require(entry['degenerate']==0 and entry['outward'] in (8,12)
            and entry['inward'] in (0,8) and sum(entry.values())==records[id_]['triangles'], 'Unreviewed glass source normals: '+id_)
    return result


UV = '''float3 n=normalize(LocalNormal); float3 p=LocalPosition;
if (Axis < .5) return float2(-p.y*sign(n.x),-p.z)/PhysicalSize;
if (Axis < 1.5) return float2(p.x*sign(n.y),-p.z)/PhysicalSize;
return float2(p.y*sign(n.z),-p.x)/PhysicalSize;'''
WEIGHT = 'float3 w=pow(abs(normalize(LocalNormal)),4);return w/max(dot(w,1),.00001);'
BLEND = 'return X*Weight.x+Y*Weight.y+Z*Weight.z;'
NORMAL = '''float3 n=normalize(LocalNormal);
float3 gx=float3(0,-sign(n.x)*NX.x,-NX.y);
float3 gy=float3(sign(n.y)*NY.x,0,-NY.y);
float3 gz=float3(-NZ.y,sign(n.z)*NZ.x,0);
float3 g=gx*Weight.x+gy*Weight.y+gz*Weight.z;
return normalize(n+(g-n*dot(g,n))*Strength);'''
COLOR = '''float ratio=dot(Scan,float3(.2126,.7152,.0722))/Mean;
return saturate(Base*clamp(1+Strength*(ratio-1),.70,1.32));'''


class Writer:
    def __init__(self, u, data):
        self.u=u;self.data=data;self.lib=u.MaterialEditingLibrary;self.assets=u.EditorAssetLibrary
        self.textures={};self.h=helper()
    def node(self,m,name,cls,**props):
        n=self.lib.create_material_expression(m,cls,-700,0);require(n is not None,'Cannot create interior node '+name)
        n.set_editor_property('desc',TAG+name)
        for k,v in props.items():n.set_editor_property(k,v)
        return n
    def scalar(self,m,v):return self.node(m,'value',self.u.MaterialExpressionConstant,r=float(v))
    def vector(self,m,v):return self.node(m,'color',self.u.MaterialExpressionConstant3Vector,constant=self.u.LinearColor(*v,1))
    def connect(self,a,p,b,q):require(self.lib.connect_material_expressions(a,p,b,q),'Interior graph connection failed '+q)
    def out(self,n,p,prop):require(self.lib.connect_material_property(n,p,prop),'Interior material output failed')
    def custom(self,m,name,code,pins,kind):
        args=[]
        for key in pins:
            a=self.u.CustomInput();a.set_editor_property('input_name',key);args.append(a)
        n=self.node(m,name,self.u.MaterialExpressionCustom,inputs=args,code=code,description=TAG+name,output_type=kind)
        for key,(a,p) in pins.items():self.connect(a,p,n,key)
        return n
    def texture(self,role):
        if role in self.textures:return self.textures[role]['object']
        spec=self.data['assets']['rough_linen']['maps'][role];name='T_Linen_'+role+'_'+spec['sha256'][:10];path=PREFIX+'/Textures/'+name;u=self.u
        require(not self.assets.does_asset_exist(path),'Interior texture namespace is not fresh: '+path)
        task=u.AssetImportTask()
        for k,v in {'filename':str(ROOT/spec['path']),'destination_path':PREFIX+'/Textures','destination_name':name,
            'automated':True,'save':False,'replace_existing':False,'factory':u.TextureFactory()}.items():task.set_editor_property(k,v)
        u.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task]);objects=task.get_objects()
        require(len(objects)==1 and isinstance(objects[0],u.Texture2D),'Interior texture import failed')
        texture=objects[0]
        compression=u.TextureCompressionSettings.TC_NORMALMAP if role=='normal' else u.TextureCompressionSettings.TC_DEFAULT if role=='albedo' else u.TextureCompressionSettings.TC_MASKS
        # Blue linen albedo can trigger UE normal-map autodetection. Set its
        # compression first: Texture::ValidateSettings clamps sRGB=false while
        # TC_Normalmap/TC_Masks is active, even during a Python property write.
        texture.set_editor_property('compression_settings',compression)
        texture.set_editor_property('srgb',role=='albedo')
        texture.set_editor_property('flip_green_channel',role=='normal')
        # Keep the immutable provider original. A full square4K mipchain
        # is built by UE; physical UV dimensions preserve the photographed ratio.
        texture.set_editor_property('power_of_two_mode',u.TexturePowerOfTwoSetting.RESIZE_TO_SPECIFIC_RESOLUTION)
        texture.set_editor_property('resize_during_build_x',4096)
        texture.set_editor_property('resize_during_build_y',4096)
        texture.set_editor_property('mip_gen_settings',u.TextureMipGenSettings.TMGS_FROM_TEXTURE_GROUP)
        texture.set_editor_property('never_stream',False)
        texture.set_editor_property('address_x',u.TextureAddress.TA_WRAP);texture.set_editor_property('address_y',u.TextureAddress.TA_WRAP)
        self.assets.set_metadata_tag(texture,'BreziGeneratedBy',OWNER);self.assets.set_metadata_tag(texture,'source_sha256',spec['sha256'])
        require(texture.get_editor_property('srgb')==(role=='albedo')
            and texture.get_editor_property('compression_settings')==compression
            and texture.get_editor_property('flip_green_channel')==(role=='normal'),
            'Interior texture interpretation did not apply: '+role+' '+texture.get_path_name())
        require(self.assets.save_loaded_asset(texture,only_if_is_dirty=False),'Texture save failed')
        self.textures[role]={'object':texture,'asset':texture.get_path_name(),'sha256':spec['sha256'],'source':spec['path'],'role':role,
            'srgb':role=='albedo','flipGreen':role=='normal','buildResolution':[4096,4096],
            'powerOfTwoMode':str(texture.get_editor_property('power_of_two_mode')),'mipGen':str(texture.get_editor_property('mip_gen_settings')),
            'neverStream':bool(texture.get_editor_property('never_stream')),'compression':str(texture.get_editor_property('compression_settings'))}
        return texture
    def sample(self,m,role,uv):
        u=self.u;sampler=u.MaterialSamplerType.SAMPLERTYPE_NORMAL if role=='normal' else u.MaterialSamplerType.SAMPLERTYPE_COLOR if role=='albedo' else u.MaterialSamplerType.SAMPLERTYPE_MASKS
        n=self.node(m,'scan-'+role,u.MaterialExpressionTextureSample,texture=self.texture(role),sampler_type=sampler)
        self.connect(uv,'',n,'UVs');return n
    def coords(self,m):
        u=self.u;p=self.node(m,'world-position',u.MaterialExpressionWorldPosition)
        local=self.node(m,'local-position',u.MaterialExpressionTransformPosition,transform_source_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_WORLD,transform_type=u.MaterialPositionTransformSource.TRANSFORMPOSSOURCE_LOCAL);self.connect(p,'',local,'')
        n=self.node(m,'vertex-normal',u.MaterialExpressionVertexNormalWS)
        normal=self.node(m,'local-normal',u.MaterialExpressionTransform,transform_source_type=u.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_WORLD,transform_type=u.MaterialVectorCoordTransform.TRANSFORM_LOCAL);self.connect(n,'',normal,'')
        return {'LocalPosition':(local,''),'LocalNormal':(normal,'')}
    def cloth(self,m,r):
        u=self.u;p=u.MaterialProperty;t=u.CustomMaterialOutputType;coords=self.coords(m)
        m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_CLOTH);m.set_editor_property('tangent_space_normal',False)
        base=self.vector(m,r['solidColorLinear'])
        size=self.data['assets']['rough_linen']['physicalSizeCm']
        size_node=self.node(m,'physical-size-cm',u.MaterialExpressionConstant2Vector,r=size[0],g=size[1])
        weight=self.custom(m,'blend-weights',WEIGHT,{'LocalNormal':coords['LocalNormal']},t.CMOT_FLOAT3)
        uvs=[self.custom(m,'metric-uv-'+str(i),UV,{**coords,'PhysicalSize':(size_node,''),'Axis':(self.scalar(m,i),'')},t.CMOT_FLOAT2) for i in range(3)]
        sampled={role:[self.sample(m,role,uv) for uv in uvs] for role in ['albedo','normal','roughness','ao']}
        def blend(role):
            return self.custom(m,'triplanar-'+role,BLEND,{'Weight':(weight,''),**{axis:(s,'RGB') for axis,s in zip(['X','Y','Z'],sampled[role])}},t.CMOT_FLOAT3)
        scan=blend('albedo');mean=sum(x*w for x,w in zip(self.data['assets']['rough_linen']['maps']['albedo']['meanLinearRGB'],[.2126,.7152,.0722]))
        color=self.custom(m,'palette-linen',COLOR,{'Base':(base,''),'Scan':(scan,''),'Mean':(self.scalar(m,mean),''),'Strength':(self.scalar(m,r['colorVariation']),'')},t.CMOT_FLOAT3)
        self.out(color,'',p.MP_BASE_COLOR)
        normal=self.custom(m,'fiber-normal',NORMAL,{'LocalNormal':coords['LocalNormal'],'Weight':(weight,''),'Strength':(self.scalar(m,r['normalStrength']),''),**{key:(s,'RGB') for key,s in zip(['NX','NY','NZ'],sampled['normal'])}},t.CMOT_FLOAT3)
        world=self.node(m,'normal-world',u.MaterialExpressionTransform,transform_source_type=u.MaterialVectorCoordTransformSource.TRANSFORMSOURCE_LOCAL,transform_type=u.MaterialVectorCoordTransform.TRANSFORM_WORLD);self.connect(normal,'',world,'')
        sign=self.node(m,'face-sign',u.MaterialExpressionTwoSidedSign);facing=self.node(m,'face-normal',u.MaterialExpressionMultiply);self.connect(world,'',facing,'A');self.connect(sign,'',facing,'B');self.out(facing,'',p.MP_NORMAL)
        rough=self.custom(m,'woven-roughness','return clamp(Base+(Scan.r-Mean)*Amount,.68,.98);',{'Base':(self.scalar(m,r['roughness']),''),'Scan':(blend('roughness'),''),'Mean':(self.scalar(m,self.data['assets']['rough_linen']['maps']['roughness']['meanDataR']),''),'Amount':(self.scalar(m,r['roughnessVariation']),'')},t.CMOT_FLOAT1);self.out(rough,'',p.MP_ROUGHNESS)
        ao=self.custom(m,'fiber-cavity','return lerp(1.0,Scan.r,.35);',{'Scan':(blend('ao'),'')},t.CMOT_FLOAT1);self.out(ao,'',p.MP_AMBIENT_OCCLUSION)
        fuzz=self.node(m,'fuzz-color',u.MaterialExpressionMultiply);self.connect(color,'',fuzz,'A');self.connect(self.scalar(m,r['fuzzColorScale']),'',fuzz,'B')
        self.out(fuzz,'',p.MP_SUBSURFACE_COLOR)
        self.out(self.scalar(m,r['specular']),'',p.MP_SPECULAR)
        # UE5.8 hides MP_CustomData0 from Python. MakeMaterialAttributes' legacy
        # ClearCoat pin routes to that same attribute, used as Cloth strength.
        attributes=self.node(m,'cloth-attributes',u.MaterialExpressionMakeMaterialAttributes)
        import re
        normalize=lambda value:re.sub(r'[^a-z0-9]','',str(value).lower())
        pins=list(self.lib.get_material_expression_input_names(attributes))
        for wanted,key in [('BaseColor','BASE_COLOR'),('Metallic','METALLIC'),('Specular','SPECULAR'),('Roughness','ROUGHNESS'),('Normal','NORMAL'),('AmbientOcclusion','AMBIENT_OCCLUSION'),('SubsurfaceColor','SUBSURFACE_COLOR')]:
            root=self.lib.get_material_property_input_node(m,getattr(p,'MP_'+key))
            if root is None:continue
            matches=[str(pin) for pin in pins if normalize(pin)==normalize(wanted)]
            require(len(matches)==1,'Missing cloth attribute '+wanted);self.connect(root,'',attributes,matches[0])
        matches=[str(pin) for pin in pins if normalize(pin)=='clearcoat']
        require(len(matches)==1,'Missing cloth custom-data attribute');self.connect(self.scalar(m,r['clothMask']),'',attributes,matches[0])
        m.set_editor_property('use_material_attributes',True);self.out(attributes,'',p.MP_MATERIAL_ATTRIBUTES)
    def stone(self,m,r):
        u=self.u;coords=self.coords(m)
        micro=self.custom(m,'honed-roughness','float3 p=LocalPosition/.17;float fade=1-smoothstep(.2,.6,length(fwidth(p)));return clamp(Base+sin(p.x*6.283)*sin(p.y*6.283)*Amplitude*fade,.38,.68);',
            {'LocalPosition':coords['LocalPosition'],'Base':(self.scalar(m,r['roughness']),''),'Amplitude':(self.scalar(m,r['roughnessVariation']),'')},u.CustomMaterialOutputType.CMOT_FLOAT1)
        self.out(micro,'',u.MaterialProperty.MP_ROUGHNESS);self.out(self.scalar(m,r['specular']),'',u.MaterialProperty.MP_SPECULAR)
    def glass(self,m,r):
        u=self.u;p=u.MaterialProperty
        m.set_editor_property('blend_mode',u.BlendMode.BLEND_TRANSLUCENT);m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_THIN_TRANSLUCENT)
        m.set_editor_property('two_sided',False);m.set_editor_property('refraction_method',u.RefractionMode.RM_NONE)
        m.set_editor_property('translucency_lighting_mode',u.TranslucencyLightingMode.TLM_SURFACE_PER_PIXEL_LIGHTING)
        m.set_editor_property('screen_space_reflections',True)
        self.out(self.vector(m,[0,0,0]),'',p.MP_BASE_COLOR)
        for prop,value in [(p.MP_METALLIC,0),(p.MP_OPACITY,0),(p.MP_SPECULAR,r['specular']),(p.MP_ROUGHNESS,r['roughness'])]:self.out(self.scalar(m,value),'',prop)
        output=self.node(m,'thin-transmission',u.MaterialExpressionThinTranslucentMaterialOutput)
        self.connect(self.vector(m,r['transmittance']),'',output,'TransmittanceColor')
        world=self.node(m,'glass-position',u.MaterialExpressionWorldPosition);center=self.node(m,'glass-bounds-center',u.MaterialExpressionObjectPositionWS);normal=self.node(m,'glass-vertex-normal',u.MaterialExpressionVertexNormalWS)
        coverage=self.custom(m,'outward-shell-coverage','return step(.0001,dot(Normal,Position-Center));',{'Normal':(normal,''),'Position':(world,''),'Center':(center,'')},u.CustomMaterialOutputType.CMOT_FLOAT1)
        self.connect(coverage,'',output,'SurfaceCoverage')
    def material(self,original,r):
        name='M_'+r['kind'].replace('-','_')+'_'+digest({'source':original.get_path_name(),'recipe':r})[:12]
        path=PREFIX+'/Materials/'+name
        require(not self.assets.does_asset_exist(path),'Interior material namespace is not fresh: '+path)
        material=self.assets.duplicate_asset(original.get_path_name(),path);require(material is not None,'Interior material clone failed')
        {'woven-linen':self.cloth,'honed-stone':self.stone,'architectural-thin-glass':self.glass}[r['kind']](material,r)
        if r['kind']!='architectural-thin-glass':self.lib.set_base_material_usage(material,self.u.MaterialUsage.MATUSAGE_NANITE,True)
        errors=list(self.lib.recompile_material(material));require(not errors,'Interior native material compile failed: '+str(errors))
        self.assets.set_metadata_tag(material,'BreziGeneratedBy',OWNER);self.assets.set_metadata_tag(material,'BreziPhotorealInteriorRecipe',json.dumps(r,sort_keys=True))
        require(self.assets.save_loaded_asset(material,only_if_is_dirty=False),'Interior material save failed')
        return material


def snapshot(u,m):
    h=helper(); result=h.graph_snapshot(u,m)
    for key in ['shading_model','two_sided','refraction_method','translucency_lighting_mode','screen_space_reflections','use_material_attributes']:
        result[key]=str(m.get_editor_property(key))
    for key in ['SPECULAR','AMBIENT_OCCLUSION','SUBSURFACE_COLOR','MATERIAL_ATTRIBUTES','REFRACTION']:
        n=u.MaterialEditingLibrary.get_material_property_input_node(m,getattr(u.MaterialProperty,'MP_'+key));result['roots'][key]=n.get_name() if n else None
    return result


def components(u,ids):
    result={}
    for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
        tags={str(t) for t in actor.get_editor_property('tags')}&ids
        if not tags or actor.actor_has_tag('BreziWalkSupportProxy'):continue
        require(len(tags)==1,'Ambiguous source actor')
        id_=next(iter(tags));parts=actor.get_components_by_class(u.StaticMeshComponent)
        require(id_ not in result and len(parts)==1,'Ambiguous source component '+id_);result[id_]=parts[0]
    require(set(result)==ids,'Incomplete interior source components');return result


def write_report(geometry,report):
    (Path(geometry).parent/'photoreal-interior-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')


def apply_photoreal_interior(scene,geometry,baseline_report):
    import unreal as u
    require(scene.get('activeDesign')==EXPECTED_DESIGN,'Interior requires active C/B/B')
    selected=selected_bindings(scene,baseline_report);data=inputs();writer=Writer(u,data)
    ids={b['id'] for b in selected};parts=components(u,ids);witness=writer.h.geometry_witness(u,ids)
    originals={};planned=[]
    for b in selected:
        c=parts[b['id']];m=c.get_material(b['index']);mesh=c.get_editor_property('static_mesh')
        require(m is not None and m.get_path_name()==b['asset'] and mesh.get_material(b['index'])==m,'Interior baseline material binding differs')
        require(u.EditorAssetLibrary.get_metadata_tag(m,'BreziGeneratedBy')=='scripts/unreal/model-refresh-import.py','Interior source material owner differs')
        originals[b['asset']]=snapshot(u,m);planned.append((b,c,m))
    report={'schemaVersion':1,'status':'authored-reload-pending','generatedAt':datetime.now(timezone.utc).isoformat(),
        'sourceManifestSha256':sha(Path(geometry)/'scene.json'),'pipelineFiles':{OWNER:sha(__file__),'scripts/unreal/photoreal-interior-inputs.json':sha(INPUTS)},
        'materials':{},'textures':[],'bindings':[],'geometryWitness':witness,'originalMaterialGraphs':originals,
        'glassSourceAudit':glass_source_audit(scene,geometry,selected),'geometryModified':False,'collisionModified':False,
        'savedReloaded':False,'nativeRenderedVerified':False,'sourceMeshSlotsModified':False,
        'limitations':['Rough Linen is a photographed CC0 finish choice, not the specification of an installed fabric.',
            'Thin glass provides one spatial reflection and two-interface transmission attenuation; the24mm source assembly is not reconstructed as separately refracting IGU panes. An optional DoubleGlass pass adds the rear-interface image.',
            'RM_NONE intentionally avoids displaced screen-color distortion. Lumen/Metal reflections need rendered review.',
            'Furniture shapes remain source geometry in this module; seams and cushion deformation belong to the geometry pass.']}
    created={}
    for b,c,original in planned:
        key=b['sourceSlot']
        if key not in created:
            m=writer.material(original,b['recipe']);created[key]=m
            report['materials'][key]={'asset':m.get_path_name(),'sourceAsset':original.get_path_name(),'sourceName':b['sourceName'],'recipe':b['recipe'],'graph':snapshot(u,m)}
        material=created[key];c.set_material(b['index'],material)
        report['bindings'].append({**b,'sourceAsset':b['asset'],'asset':material.get_path_name()})
    report['textures']=[{k:v for k,v in entry.items() if k!='object'} for entry in writer.textures.values()]
    require(writer.h.geometry_witness(u,ids)==witness,'Interior overrides changed geometry or collision')
    for path,graph in originals.items():require(snapshot(u,u.EditorAssetLibrary.load_asset(path))==graph,'Interior authoring changed a source material')
    write_report(geometry,report);return report


def verify_photoreal_interior(scene,geometry,report):
    import unreal as u
    require(scene.get('activeDesign')==EXPECTED_DESIGN and sha(Path(geometry)/'scene.json')==report['sourceManifestSha256'],'Interior source changed')
    for path,expected in report['pipelineFiles'].items():require(sha(ROOT/path)==expected,'Interior pipeline changed after authoring')
    inputs();ids={b['id'] for b in report['bindings']};parts=components(u,ids)
    require(helper().geometry_witness(u,ids)==report['geometryWitness'],'Interior saved geometry/collision differs')
    for slot,entry in report['materials'].items():
        material=u.EditorAssetLibrary.load_asset(entry['asset'])
        require(material and snapshot(u,material)==entry['graph'],'Interior saved material graph differs '+slot)
        require(u.EditorAssetLibrary.get_metadata_tag(material,'BreziGeneratedBy')==OWNER and u.EditorAssetLibrary.get_metadata_tag(material,'BreziPhotorealInteriorRecipe')==json.dumps(entry['recipe'],sort_keys=True),'Interior saved ownership/recipe differs')
    for path,graph in report['originalMaterialGraphs'].items():require(snapshot(u,u.EditorAssetLibrary.load_asset(path))==graph,'Interior changed original source material')
    for b in report['bindings']:
        c=parts[b['id']];mesh=c.get_editor_property('static_mesh')
        require(c.get_material(b['index']).get_path_name()==b['asset'] and mesh.get_material(b['index']).get_path_name()==b['sourceAsset'],'Interior saved component override or source mesh slot differs')
    for entry in report['textures']:
        texture=u.EditorAssetLibrary.load_asset(entry['asset'])
        require(texture and texture.get_editor_property('srgb')==entry['srgb'] and texture.get_editor_property('flip_green_channel')==entry['flipGreen'] and str(texture.get_editor_property('compression_settings'))==entry['compression'] and u.EditorAssetLibrary.get_metadata_tag(texture,'source_sha256')==entry['sha256'],'Interior saved texture interpretation differs: '+entry['role']+' '+entry['asset'])
        require([texture.get_editor_property('resize_during_build_x'),texture.get_editor_property('resize_during_build_y')]==entry['buildResolution'] and str(texture.get_editor_property('power_of_two_mode'))==entry['powerOfTwoMode'] and str(texture.get_editor_property('mip_gen_settings'))==entry['mipGen'] and bool(texture.get_editor_property('never_stream'))==entry['neverStream'],'Interior saved mip build differs')
    report.update(status='saved-reloaded-validated',savedReloaded=True,verifiedAt=datetime.now(timezone.utc).isoformat())
    write_report(geometry,report);return report
