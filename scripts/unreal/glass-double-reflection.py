"""Optional rear-interface reflection image; does not alter primary glass assets.

Each runtime actor mirrors the current camera at the actual rear source face,
then projects that linear HDR image onto the camera-facing source face. This is
a planar mirror approximation: Fresnel/two-path absorption use IOR 1.52, but
Snell lateral displacement and further internal reflections are not traced.
"""
import hashlib
import importlib.util
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/glass-double-reflection.py'
PREFIX = '/Game/Brezi/Photoreal/DoubleGlass'
CPP = 'unreal/BreziTwin/Source/BreziTwin/BreziDoubleGlassActor.cpp'
HEADER = 'unreal/BreziTwin/Source/BreziTwin/BreziDoubleGlassActor.h'
POLICY = 'unreal/BreziTwin/Source/BreziTwin/BreziDoubleGlassCapturePolicy.h'
EXPECTED_DESIGN = {'variant':'C','heatingLayout':'B','livingLayout':'B'}
IOR = 1.52
TINT = [.986,.994,.990]

UV_CODE = '''float3 d=Position-Eye;
float denominator=dot(d,PaneNormal);
float safeDenominator=abs(denominator)<1e-5 ? -1e-5 : denominator;
float3 hit=Eye+d*(dot(RearPlane-Eye,PaneNormal)/safeDenominator);
float3 w=hit-CaptureOrigin;
float z=dot(w,CaptureForward);
float safeZ=max(z,1e-4);
return float2(.5+.5*dot(w,CaptureRight)/(safeZ*Projection.x),
              .5-.5*dot(w,CaptureUp)*Projection.y/(safeZ*Projection.x));'''

EMISSION_CODE = '''float noV=saturate(dot(normalize(Eye-Position),normalize(PaneNormal)));
float F0=pow((IOR-1)/(IOR+1),2);
float F=F0+(1-F0)*pow(1-noV,5);
float3 roundTrip=pow(Tint,2/max(noV,.001));
// Only the near outward main face. This also rejects inward gable duplicates
// and the thin edge caps without changing source topology.
float outward=step(.0001,dot(VertexNormal,Position-PaneCenter));
float facing=step(.98,dot(normalize(VertexNormal),normalize(PaneNormal)));
float valid=step(0,UV.x)*step(UV.x,1)*step(0,UV.y)*step(UV.y,1);
float inFront=step(.001,dot(Position-CaptureOrigin,CaptureForward));
return max(Image,0)*F*pow(1-F,2)*roundTrip*outward*facing*valid*inFront*saturate(Ready);'''


def require(ok,message):
    if not ok:raise RuntimeError(message)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def interior_module():
    s=importlib.util.spec_from_file_location('brezi_double_glass_readback',ROOT/'scripts/unreal/photoreal-interior.py')
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


def select_glass(scene,baseline_report):
    require(scene.get('activeDesign')==EXPECTED_DESIGN,'Double glass requires explicit active C/B/B')
    baseline=baseline_report if 'bindings' in baseline_report else baseline_report['materials']
    objects={r['id']:r for r in scene['objects']};result=[]
    for b in baseline['bindings']:
        source=scene['materials'][b['sourceSlot']]
        if source['name']!='real-glass':continue
        r=objects[b['id']];size=[y-x for x,y in zip(r['boundsMm']['min'],r['boundsMm']['max'])]
        require(r['enabled'] and r['instances']==1 and len(r['materialSlots'])==1 and b['index']==0
            and abs(min(size)-24)<.02 and r['triangles'] in (12,16),
            'Double-glass source is not the reviewed 24 mm architectural shell: '+r['sourceId'])
        result.append({**b,'sourceName':source['name'],'sourceId':r['sourceId'],
            'boundsMm':r['boundsMm'],'triangles':r['triangles'],
            'recipe':{'kind':'architectural-thin-glass'}})
    require(len(result)==19,'Expected 19 current architectural panes, excluding shower and utility/stove glass')
    return result


def energy(no_v,tint=TINT):
    require(0<=no_v<=1,'Invalid view cosine')
    f0=((IOR-1)/(IOR+1))**2;f=f0+(1-f0)*(1-no_v)**5
    a=[x**(1/max(no_v,.001)) for x in tint]
    return {'front':f,'rear':[f*(1-f)**2*x*x for x in a],
        'transmission':[(1-f)**2*x for x in a]}


def dot(a,b):return sum(x*y for x,y in zip(a,b))
def sub(a,b):return [x-y for x,y in zip(a,b)]
def mirror(point,plane,normal):return [x-2*dot(sub(point,plane),normal)*n for x,n in zip(point,normal)]


def project_rear(position,eye,rear_plane,normal,capture_origin,forward,right,up,tan_half,aspect):
    d=sub(position,eye);denominator=dot(d,normal)
    require(abs(denominator)>1e-8,'Ray parallel to rear plane')
    hit=[x+y*dot(sub(rear_plane,eye),normal)/denominator for x,y in zip(eye,d)]
    w=sub(hit,capture_origin);z=dot(w,forward)
    require(z>0,'Projected point is behind capture')
    return [.5+.5*dot(w,right)/(z*tan_half),.5-.5*dot(w,up)*aspect/(z*tan_half)]


def build_material(u):
    name='M_RearInterface';path=PREFIX+'/'+name
    require(not u.EditorAssetLibrary.does_asset_exist(path),'Double glass namespace is not fresh')
    m=u.AssetToolsHelpers.get_asset_tools().create_asset(name,PREFIX,u.Material,u.MaterialFactoryNew())
    require(m is not None,'Cannot create supplemental glass material')
    m.set_editor_property('blend_mode',u.BlendMode.BLEND_ADDITIVE)
    m.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
    m.set_editor_property('two_sided',False)
    m.set_editor_property('refraction_method',u.RefractionMode.RM_NONE)
    lib=u.MaterialEditingLibrary
    def node(cls,**props):
        n=lib.create_material_expression(m,cls,-500,0);require(n is not None,'Cannot create glass expression')
        for k,v in props.items():n.set_editor_property(k,v)
        return n
    def scalar(name,value):return node(u.MaterialExpressionScalarParameter,parameter_name=name,default_value=float(value))
    def vector(name,value):return node(u.MaterialExpressionVectorParameter,parameter_name=name,default_value=u.LinearColor(*value,0))
    def connect(a,output,b,pin):require(lib.connect_material_expressions(a,output,b,pin),'Glass connection failed '+pin)
    def custom(name,code,pins,kind):
        args=[]
        for key in pins:
            item=u.CustomInput();item.set_editor_property('input_name',key);args.append(item)
        n=node(u.MaterialExpressionCustom,description=name,code=code,inputs=args,output_type=kind)
        for key,(item,output) in pins.items():connect(item,output,n,key)
        return n
    position=node(u.MaterialExpressionWorldPosition);eye=node(u.MaterialExpressionCameraPositionWS)
    normal=node(u.MaterialExpressionVertexNormalWS)
    vectors={k:vector(k,value) for k,value in {
        'CaptureOrigin':[0,0,0],'CaptureForward':[1,0,0],'CaptureRight':[0,1,0],'CaptureUp':[0,0,1],
        'CaptureProjection':[1,1,0],'PaneCenter':[0,0,0],'PaneNormal':[1,0,0],'RearPlane':[0,0,0]}.items()}
    pins={k:(v,'RGB') for k,v in vectors.items() if k!='PaneCenter'}
    pins['Projection']=pins.pop('CaptureProjection')
    pins.update(Position=(position,''),Eye=(eye,''))
    uv=custom('Rear plane projective coordinates',UV_CODE,pins,u.CustomMaterialOutputType.CMOT_FLOAT2)
    black=u.EditorAssetLibrary.load_asset('/Engine/EngineResources/Black')
    require(black is not None,'Required native black fallback texture absent')
    sample=node(u.MaterialExpressionTextureSampleParameter2D,parameter_name='RearImage',texture=black,
        sampler_type=u.MaterialSamplerType.SAMPLERTYPE_COLOR if black.get_editor_property('srgb') else u.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR)
    connect(uv,'',sample,'UVs')
    emission=custom('First rear-interface Fresnel path',EMISSION_CODE,
        {'Position':(position,''),'Eye':(eye,''),'VertexNormal':(normal,''),
         'PaneCenter':(vectors['PaneCenter'],'RGB'),'PaneNormal':(vectors['PaneNormal'],'RGB'),
         'CaptureOrigin':(vectors['CaptureOrigin'],'RGB'),'CaptureForward':(vectors['CaptureForward'],'RGB'),
         'UV':(uv,''),'Image':(sample,'RGB'),'Ready':(scalar('Ready',0),''),
         'IOR':(scalar('IndexOfRefraction',IOR),''),'Tint':(vector('SinglePathTint',TINT),'RGB')},u.CustomMaterialOutputType.CMOT_FLOAT3)
    require(lib.connect_material_property(emission,'',u.MaterialProperty.MP_EMISSIVE_COLOR),'Glass emission connection failed')
    require(lib.connect_material_property(scalar('AdditiveOpacity',1),'',u.MaterialProperty.MP_OPACITY),'Glass additive opacity connection failed')
    u.EditorAssetLibrary.set_metadata_tag(m,'BreziGeneratedBy',OWNER)
    u.EditorAssetLibrary.set_metadata_tag(m,'BreziOpticalApproximation','Rear source-plane mirror; first secondary Fresnel path, no Snell ray displacement')
    lib.recompile_material(m)
    require(u.EditorAssetLibrary.save_loaded_asset(m,only_if_is_dirty=False),'Glass material save failed')
    return m


def write_report(geometry,report):
    (Path(geometry).parent/'glass-double-reflection-report.json').write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')


def apply_glass(scene,geometry,baseline_material_report):
    import unreal as u
    selected=select_glass(scene,baseline_material_report);interior=interior_module()
    ids={b['id'] for b in selected};parts=interior.components(u,ids)
    witness=interior.helper().geometry_witness(u,ids)
    actor_class=u.load_class(None,'/Script/BreziTwin.BreziDoubleGlassActor')
    require(actor_class is not None,'Double glass native helper must be compiled before import')
    subsystem=u.get_editor_subsystem(u.EditorActorSubsystem)
    require(not any(a.get_class()==actor_class for a in subsystem.get_all_level_actors()),'Double glass actors already exist')
    material=build_material(u)
    report={'schemaVersion':1,'status':'authored-reload-pending','generatedAt':datetime.now(timezone.utc).isoformat(),
        'sourceManifestSha256':sha(Path(geometry)/'scene.json'),'namespace':PREFIX,
        'pipelineFiles':{p:sha(ROOT/p) for p in [OWNER,CPP,HEADER,POLICY]},
        'recipe':{'ior':IOR,'singlePathTint':TINT,'rearWeight':'F*(1-F)^2*tint^(2/NoV)',
            'projection':'camera mirrored at actual rear source face; project camera-ray/rear-plane intersection',
            'primaryReflection':'original ThinTranslucent and Lumen unchanged','sourceThicknessMm':24,
            'captureWidth':512,'captureWidthMaximum':512,'captureWarmupFrames':2,
            'captureUsesLumen':False,'captureBudgetPerFrame':1,'cameraSettleSeconds':.25,
            'runtimeDisable':'r.Brezi.DoubleGlass 0','sceneChangeDetection':'event-driven world revision for doors, lighting and quality; explicit SceneRevision for additional procedural shader changes'},
        'material':{'asset':material.get_path_name(),'graph':interior.snapshot(u,material)},
        'bindings':[],'geometryWitness':witness,'primaryMaterialGraphs':{},
        'glassSourceAudit':interior.glass_source_audit(scene,geometry,selected),
        'sourceGeometryModified':False,'sourceCollisionModified':False,'sourceMeshSlotsModified':False,
        'savedReloaded':False,'nativeRenderedVerified':False,
        'limitations':['Rear image uses a planar mirror at the24mm source rear face, not Snell-correct ray transport through individual IGU panes.',
            'Only the first rear-interface return is added; higher internal bounces are omitted.',
            'Rear overlay is hidden while the camera or scene changes, then settles with at most one capture per frame after 250 ms; primary glass is unchanged.',
            'Supplemental additive layers are hidden in all reflection captures to avoid feedback; original primary glazing remains visible.',
            'The source24mm shell is an optical envelope, not a measured glass/gas/low-e assembly specification.']}
    for b in selected:
        c=parts[b['id']];primary=c.get_material(0)
        require(primary and primary.get_editor_property('shading_model')==u.MaterialShadingModel.MSM_THIN_TRANSLUCENT
            and primary.get_path_name().startswith('/Game/Brezi/Photoreal/Interior/'),
            'Expected accepted primary photoreal thin glass: '+b['id'])
        report['primaryMaterialGraphs'][primary.get_path_name()]=interior.snapshot(u,primary)
        a=subsystem.spawn_actor_from_class(actor_class,u.Vector(0,0,0),u.Rotator(0,0,0))
        require(a is not None,'Failed to spawn rear-reflection actor')
        a.set_actor_label('Brezi rear reflection '+b['id'])
        a.set_editor_property('tags',[u.Name('BreziDoubleGlassOwned')])
        a.set_editor_property('source_component',c);a.set_editor_property('overlay_material',material)
        a.set_editor_property('capture_width',512);a.set_editor_property('warmup_captures',2)
        a.set_editor_property('maximum_distance_cm',20000.)
        overlay=a.get_editor_property('overlay')
        require(overlay.get_editor_property('static_mesh') is None
            and overlay.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION,'Overlay must be inert and collision-free before play')
        report['bindings'].append({**b,'primaryAsset':primary.get_path_name(),'actor':a.get_path_name(),
            'actorLabel':a.get_actor_label(),'sourceComponent':c.get_path_name(),'sourceMesh':c.get_editor_property('static_mesh').get_path_name(),
            'sourceMeshMaterial':c.get_editor_property('static_mesh').get_material(0).get_path_name()})
    require(interior.helper().geometry_witness(u,ids)==witness,'Double glass mutated source geometry/collision')
    write_report(geometry,report);return report


def verify_glass(scene,geometry,report):
    import unreal as u
    require(scene.get('activeDesign')==EXPECTED_DESIGN and sha(Path(geometry)/'scene.json')==report['sourceManifestSha256'],'Double glass source differs')
    for path,expected in report['pipelineFiles'].items():require(sha(ROOT/path)==expected,'Double glass helper changed after authoring')
    interior=interior_module();ids={b['id'] for b in report['bindings']};parts=interior.components(u,ids)
    require(interior.helper().geometry_witness(u,ids)==report['geometryWitness'],'Double glass saved geometry/collision differs')
    material=u.EditorAssetLibrary.load_asset(report['material']['asset'])
    require(material and interior.snapshot(u,material)==report['material']['graph'],'Saved supplemental material differs')
    require(u.EditorAssetLibrary.get_metadata_tag(material,'BreziGeneratedBy')==OWNER,'Saved double glass owner differs')
    actors={a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
    for path,graph in report['primaryMaterialGraphs'].items():require(interior.snapshot(u,u.EditorAssetLibrary.load_asset(path))==graph,'Primary glass material changed')
    for b in report['bindings']:
        a=actors.get(b['actor']);c=parts[b['id']]
        require(a and a.get_editor_property('source_component')==c and a.get_editor_property('overlay_material')==material,'Saved rear actor linkage differs')
        require({str(x) for x in a.get_editor_property('tags')}=={'BreziDoubleGlassOwned'},'Rear actor must not claim raw source identity')
        require(a.get_editor_property('capture_width')==512 and a.get_editor_property('warmup_captures')==2,'Saved capture budget differs')
        require(a.get_editor_property('overlay').get_collision_enabled()==u.CollisionEnabled.NO_COLLISION,'Rear overlay has collision')
        require(c.get_material(0).get_path_name()==b['primaryAsset'] and c.get_editor_property('static_mesh').get_path_name()==b['sourceMesh']
            and c.get_editor_property('static_mesh').get_material(0).get_path_name()==b['sourceMeshMaterial'],'Original source binding changed')
    report.update(status='saved-reloaded-validated',savedReloaded=True,verifiedAt=datetime.now(timezone.utc).isoformat())
    write_report(geometry,report);return report
