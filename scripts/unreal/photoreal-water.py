"""Clear pool-water override for the current C/B/B source, without geometry edits.

The already validated OpticsWriter builds/readbacks the SingleLayerWater shader
and normal waves. Only its graph builder is reused: historical object/slot scope,
old native packages, mesh assignment and caustics pipelines are never invoked.
"""
import hashlib
import importlib.util
import json
import math
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/photoreal-water.py'
PREFIX = '/Game/Brezi/Photoreal/Water'
EXPECTED_DESIGN = {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}
ABSORPTION_PER_METRE = [.13, .045, .02]
SCATTERING_PER_METRE = [.002, .004, .006]


def require(ok, message):
    if not ok: raise RuntimeError(message)


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load_module(name, filename):
    spec=importlib.util.spec_from_file_location(name,ROOT/'scripts/unreal'/filename)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def recipe():
    return {'kind':'clear-single-layer-pool-water','ior':1.333,'roughness':.035,
        'opacity':0.,'baseColor':[0.,0.,0.],'metallic':0.,
        'absorptionPerMetre':ABSORPTION_PER_METRE,
        'scatteringPerMetre':SCATTERING_PER_METRE,
        'coefficientScaleToPerCentimetre':.01,'phaseG':0.,
        'colorScaleBehindWater':[1.,1.,1.],'twoSided':False,
        'worldSpaceNormal':True,'normalWaves':'12 submillimetre analytic gravity-wave modes from optics.py',
        'volumeDepth':'native scene depth to existing canonical pool basin',
        'geometryDisplacement':False,'dynamicCaustics':False}


def select_water(scene, baseline_report):
    require(scene.get('activeDesign')==EXPECTED_DESIGN,'Water requires explicit active C/B/B')
    baseline=baseline_report if 'bindings' in baseline_report else baseline_report['materials']
    records={r['id']:r for r in scene['objects']}; selected=[]
    for b in baseline['bindings']:
        source=scene['materials'][b['sourceSlot']]
        if source['name']!='real-pool-water':continue
        record=records[b['id']];bounds=record['boundsMm'];dimensions=[v-u for u,v in zip(bounds['min'],bounds['max'])]
        require(record['enabled'] and record['group']=='Pool'
            and record['metadata'].get('entityId')=='POOL-COURTYARD-6X27'
            and source['metallic']==0 and source['texture'] is None
            and len(record['materialSlots'])==1 and record['instances']==1
            and min(dimensions[:2])>1000 and abs(dimensions[2])<.02,
            'Source pool water is not the current flat canonical surface')
        selected.append({**b,'sourceName':source['name'],'sourceId':record['sourceId'],
            'boundsMm':bounds,'triangles':record['triangles']})
    require(len(selected)==1,'Clear water override requires exactly one canonical pool surface')
    return selected


def transmittance(distance_metres):
    """Unscattered single-path attenuation, useful for units/regression checks."""
    require(math.isfinite(distance_metres) and distance_metres>=0,'Invalid optical path length')
    return [math.exp(-(a+s)*distance_metres) for a,s in zip(ABSORPTION_PER_METRE,SCATTERING_PER_METRE)]


def writer(u, report):
    optics=load_module('brezi_photoreal_water_optics','optics.py')
    # Private module bindings affect only this new writer instance; do not call
    # apply_optics(), instance() or any historical scope/assignment function.
    optics.CONTENT=PREFIX;optics.OWNER=OWNER
    require(optics.ABSORPTION_PER_METRE==ABSORPTION_PER_METRE and optics.SCATTERING_PER_METRE==SCATTERING_PER_METRE,
            'Proven water coefficient recipe changed')
    require(len(optics.WAVES)==12 and all(0<w['amplitudeMetres']<.0004 for w in optics.WAVES),
            'Proven pool ripple spectrum changed')
    return optics, optics.OpticsWriter(report)


def readback(u, optics_writer, material):
    interior=load_module('brezi_photoreal_water_snapshot','photoreal-interior.py')
    require(material.get_editor_property('shading_model')==u.MaterialShadingModel.MSM_SINGLE_LAYER_WATER
        and material.get_editor_property('blend_mode')==u.BlendMode.BLEND_OPAQUE
        and material.get_editor_property('has_pixel_animation')
        and not material.get_editor_property('use_material_attributes'),'Water surface/shading policy differs')
    result=interior.snapshot(u,material)
    result['opticalOutput']=optics_writer.validate_output(material,True,u.RefractionMode.RM_INDEX_OF_REFRACTION)
    expressions=list(u.MaterialEditingLibrary.get_material_expressions(material));parameters={}
    for n in expressions:
        if isinstance(n,u.MaterialExpressionScalarParameter):
            parameters[str(n.get_editor_property('parameter_name'))]=round(float(n.get_editor_property('default_value')),8)
        elif isinstance(n,u.MaterialExpressionVectorParameter):
            c=n.get_editor_property('default_value');parameters[str(n.get_editor_property('parameter_name'))]=[round(float(getattr(c,k)),8) for k in ['r','g','b']]
    require(set(parameters)=={'IndexOfRefraction','Roughness','ScatteringPerMetre','AbsorptionPerMetre','PhaseG'},'Water parameter set differs')
    expected={'IndexOfRefraction':1.333,'Roughness':.035,'PhaseG':0.,
        'ScatteringPerMetre':SCATTERING_PER_METRE,'AbsorptionPerMetre':ABSORPTION_PER_METRE}
    for key,value in expected.items():
        a=parameters[key] if isinstance(value,list) else [parameters[key]];b=value if isinstance(value,list) else [value]
        require(all(math.isclose(x,y,rel_tol=1e-6,abs_tol=1e-7) for x,y in zip(a,b)),'Water parameter differs: '+key)
    for key,value in [('OPACITY',0.),('METALLIC',0.)]:
        root=u.MaterialEditingLibrary.get_material_property_input_node(material,getattr(u.MaterialProperty,'MP_'+key))
        require(isinstance(root,u.MaterialExpressionConstant) and float(root.get_editor_property('r'))==value,'Water opacity/metallicity differs')
    for key in ['WORLD_POSITION_OFFSET']:
        require(u.MaterialEditingLibrary.get_material_property_input_node(material,getattr(u.MaterialProperty,'MP_'+key)) is None,'Water must not displace source vertices')
    result['parameters']=parameters;return result


def write_report(geometry, report):
    (Path(geometry).parent/'photoreal-water-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')


def apply_water(scene, geometry, baseline_material_report):
    import unreal as u
    selected=select_water(scene,baseline_material_report)
    interior=load_module('brezi_photoreal_water_source','photoreal-interior.py')
    ids={b['id'] for b in selected};parts=interior.components(u,ids)
    witness=interior.helper().geometry_witness(u,ids);b=selected[0];component=parts[b['id']]
    original=component.get_material(b['index']);mesh=component.get_editor_property('static_mesh')
    require(original and original.get_path_name()==b['asset'] and mesh.get_material(b['index'])==original
        and u.EditorAssetLibrary.get_metadata_tag(original,'BreziGeneratedBy')=='scripts/unreal/model-refresh-import.py',
        'Pool water baseline material/component differs')
    original_graph=interior.snapshot(u,original)
    require(not u.EditorAssetLibrary.does_asset_exist(PREFIX+'/M_PoolWater'),'Water authoring requires a fresh owned namespace')
    report={'schemaVersion':1,'status':'authored-reload-pending','generatedAt':datetime.now(timezone.utc).isoformat(),
        'sourceManifestSha256':sha(Path(geometry)/'scene.json'),'namespace':PREFIX,
        'pipelineFiles':{p:sha(ROOT/p) for p in [OWNER,'scripts/unreal/optics.py','scripts/unreal/photoreal-interior.py','scripts/unreal/archviz-materials.py']},
        'recipe':recipe(),'masters':[],'bindings':[],'geometryWitness':witness,
        'originalMaterialGraphs':{original.get_path_name():original_graph},'textures':[],
        'geometryModified':False,'collisionModified':False,'sourceMeshSlotsModified':False,
        'savedReloaded':False,'nativeRenderedVerified':False,
        'documentation':['https://dev.epicgames.com/documentation/en-us/unreal-engine/single-layer-water-shading-model-in-unreal-engine'],
        'limitations':['Water attenuation and ripple amplitudes are authored visual parameters, not measured water samples.',
            'SingleLayerWater depends on screen color/depth and existing basin geometry; rendered Metal review is separate.',
            'No caustics, height displacement, pool dimensions, source matrices or collision changes are authored.']}
    optics,w=writer(u,report);material=w.master(True)
    u.EditorAssetLibrary.set_metadata_tag(material,'BreziPhotorealWaterRecipe',json.dumps(recipe(),sort_keys=True))
    require(u.EditorAssetLibrary.save_loaded_asset(material,only_if_is_dirty=False),'Pool water save failed')
    report['waterMaterial']={'asset':material.get_path_name(),'graph':readback(u,w,material)}
    report['waves']=optics.WAVES
    component.set_material(b['index'],material)
    report['bindings']=[{**b,'sourceAsset':b['asset'],'asset':material.get_path_name()}]
    require(interior.helper().geometry_witness(u,ids)==witness,'Water override modified source geometry/collision')
    require(interior.snapshot(u,original)==original_graph,'Water override changed source material')
    write_report(geometry,report);return report


def verify_water(scene, geometry, report):
    import unreal as u
    require(scene.get('activeDesign')==EXPECTED_DESIGN and sha(Path(geometry)/'scene.json')==report['sourceManifestSha256'],'Water source changed')
    for path,expected in report['pipelineFiles'].items():require(sha(ROOT/path)==expected,'Water pipeline changed after authoring')
    interior=load_module('brezi_photoreal_water_verify','photoreal-interior.py');optics,w=writer(u,{'masters':[]})
    ids={b['id'] for b in report['bindings']};parts=interior.components(u,ids)
    require(interior.helper().geometry_witness(u,ids)==report['geometryWitness'],'Saved water geometry/collision differs')
    m=u.EditorAssetLibrary.load_asset(report['waterMaterial']['asset'])
    require(m and readback(u,w,m)==report['waterMaterial']['graph'],'Saved water graph/parameters differ')
    require(u.EditorAssetLibrary.get_metadata_tag(m,'BreziGeneratedBy')==OWNER and u.EditorAssetLibrary.get_metadata_tag(m,'BreziPhotorealWaterRecipe')==json.dumps(recipe(),sort_keys=True),'Saved water ownership/recipe differs')
    for path,graph in report['originalMaterialGraphs'].items():require(interior.snapshot(u,u.EditorAssetLibrary.load_asset(path))==graph,'Water source material changed')
    for b in report['bindings']:
        c=parts[b['id']];mesh=c.get_editor_property('static_mesh')
        require(c.get_material(b['index']).get_path_name()==b['asset'] and mesh.get_material(b['index']).get_path_name()==b['sourceAsset'],'Saved water override or original mesh slot differs')
    report.update(status='saved-reloaded-validated',savedReloaded=True,verifiedAt=datetime.now(timezone.utc).isoformat())
    write_report(geometry,report);return report
