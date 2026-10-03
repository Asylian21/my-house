"""Native exterior revision. Historical assets and architectural actors survive.

Only an inherited map, appended presentation cameras and newly owned assets
change. All context surfaces and plants are visual, with no navigation/collision.
"""
import copy
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import random
import shutil
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts/unreal'))
PREFIX = '/Game/Brezi/Exterior20260926'
TAG = 'BreziExterior20260926'
OWNER = 'scripts/unreal/exterior-import.py'
MAP = '/Game/Brezi/Maps/Brezi'
MAP_FILE = 'Brezi/Maps/Brezi.umap'
VIEWS_FILE = 'Data/viewpoints.json'
TAPERED_LAWN_GENERATOR = 'scripts/unreal/exterior-lawn-tapered-integration.py'
PHOTO_LAWN_GENERATOR = 'scripts/unreal/exterior-lawn-photo-integration.py'
NATURAL_LAWN_GENERATORS = ('scripts/unreal/exterior-lawn-natural.py',
    'scripts/unreal/exterior-lawn-natural-managed.py', 'scripts/unreal/exterior-lawn-coverage.py',
    'scripts/unreal/exterior-lawn-fine.py', 'scripts/unreal/exterior-lawn-upright.py', TAPERED_LAWN_GENERATOR, PHOTO_LAWN_GENERATOR)
COVERED_LAWN_GENERATORS = ('scripts/unreal/exterior-lawn-coverage.py',
    'scripts/unreal/exterior-lawn-fine.py', 'scripts/unreal/exterior-lawn-upright.py', TAPERED_LAWN_GENERATOR)
BOUNDARY_LAWN_GENERATORS = ('scripts/unreal/exterior-lawn-fine.py',
    'scripts/unreal/exterior-lawn-upright.py', TAPERED_LAWN_GENERATOR)
ORGANIC_GARDEN_GENERATOR = 'scripts/unreal/exterior-garden-organic-bushy.py'


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts/unreal' / filename)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


base = module('exterior_baseline', 'performance-optimize.py')
helper = module('exterior_witness', 'realism-room-details-import.py')
rural = module('exterior_geometry', 'rural-import.py')
common = module('exterior_common', 'realism-import.py')
mesh_helper = module('exterior_mesh_helpers', 'lawn-geometry.py')
require, sha, read, write, now, digest, inventory = (getattr(common, name) for name in
    ('require', 'sha', 'read', 'write', 'now', 'digest', 'inventory'))


def validate_changes(before, after, content):
    require(before.keys() <= after.keys(), 'Original exterior Content removed')
    allowed = {str(content / MAP_FILE), str(content / VIEWS_FILE)}
    for p, value in before.items():
        require(p in allowed or after[p] == value, 'Original asset modified: ' + p)
    for p in after.keys() - before.keys():
        require(Path(p).is_relative_to(content / 'Brezi/Exterior20260926') and Path(p).suffix in ('.uasset', '.uexp', '.ubulk'),
                'New exterior asset outside namespace: ' + p)


def restore(output):
    output = Path(output).resolve(); report = read(output / 'exterior-import-report.json')
    require(report['status'] == 'failed' and output.is_relative_to(ROOT / 'output/unreal'), 'No failed exterior attempt')
    try: os.kill(report['nativeProcessId'], 0)
    except ProcessLookupError: pass
    else: raise RuntimeError('Native process still alive')
    content = output / 'Project/BreziTwin/Content'; before = report['beforeAssetHashes']; current = inventory(content)
    require(current == report['failedContentHashes'], 'Failed Content drifted')
    validate_changes(before, current, content)
    for name in (MAP_FILE, VIEWS_FILE):
        require(sha(output / 'exterior-checkpoint' / Path(name).name) == before[str(content / name)], 'Checkpoint drift')
    history = output / 'exterior-history' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'); history.mkdir(parents=True)
    for name in (MAP_FILE, VIEWS_FILE):
        shutil.copy2(content / name, history / ('failed-' + Path(name).name))
        shutil.copy2(output / 'exterior-checkpoint' / Path(name).name, content / name)
    for p in current.keys() - before.keys():
        target = history / 'assets' / Path(p).relative_to(content); target.parent.mkdir(parents=True, exist_ok=True); shutil.move(p, target)
    require(inventory(content) == before, 'Exterior restoration differs')
    for name in ('exterior-import-report.json','exterior-import-process.json','exterior-import.log','exterior-import.log.json','exterior-checkpoint'):
        p = output / name
        if p.exists(): shutil.move(p, history / name)
    print(json.dumps({'status':'failed-exterior-restored','history':str(history)}))


def plant_lod_screens(row):
    if 'lodScreenSizes' in row:
        natural = row['id'].startswith('lawn_natural_') and row['materialKeys']==['lawn_natural_blade']
        photo_ids = {'lawn_photo_'+str(f)+'_'+str(v) for f in range(2) for v in range(8)} | {
            'lawn_photo_edge_'+str(f)+'_'+str(v) for f in range(2) for v in range(2)}
        photo = row['id'] in photo_ids and row['materialKeys']==['lawn_photographic_blade']
        require((natural or photo) and row['role']=='grass'
                and row.get('placementPolicy')=='explicit-only'
                and row['lodScreenSizes']==[1.,.025,.007], 'Unreviewed plant LOD override')
        return [1.,.025,.007]
    return [1.,.32,.10] if row['role']=='tree' else [1.,.15,.04]


def lawn_native_filename(owner):
    if owner == PHOTO_LAWN_GENERATOR:
        return 'exterior-lawn-photo-native.py'
    return 'exterior-lawn-tapered-native.py' if owner == TAPERED_LAWN_GENERATOR else 'exterior-lawn-native.py'


def validate_plants(manifest):
    require(manifest['meshes'], 'No plant meshes')
    ids = set()
    for row in manifest['meshes']:
        require(row['id'] not in ids and row['role'] in ('tree','shrub','vine','groundcover','grass','nettle','forb','ornamental'), 'Duplicate or invalid plant role')
        ids.add(row['id'])
        require(sha(row['glbPath']) == row['glbSha256'], 'Plant GLB differs')
        require(len(row['lods']) == 3 and row['materialKeys'] and row['heightCm'] > 0, 'Missing plant LOD/material/height')
        plant_lod_screens(row)
        for lod in row['lods']:
            require(lod['triangles'] > 0 and all(math.isfinite(v) for xyz in lod['expectedBoundsCm'].values() for v in xyz), 'Invalid plant bounds')


def garden_placements(obj_path):
    """Sample inside the actual existing mulch polygons, including full crowns."""
    wanted={'DOM_01965','DOM_01966'}; excluded={'DOM_01961','DOM_01962','DOM_01963','DOM_01964'}
    vertices=[]; triangles={key:[] for key in wanted|excluded}; current=None
    for line in Path(obj_path).open():
        p=line.split()
        if not p: continue
        if p[0]=='v': vertices.append((float(p[1])/10,-float(p[2])/10,float(p[3])/10))
        elif p[0]=='o': current=p[1]
        elif p[0]=='f' and current in triangles:
            face=[vertices[int(v.split('/')[0])-1] for v in p[1:]]
            triangles[current].extend([face[0],face[i],face[i+1]] for i in range(1,len(face)-1))
    def inside(p,t):
        c=[(t[(i+1)%3][0]-t[i][0])*(p[1]-t[i][1])-(t[(i+1)%3][1]-t[i][1])*(p[0]-t[i][0]) for i in range(3)]
        return min(c)>=-1e-7 or max(c)<=1e-7
    def distance(p,a,b):
        dx,dy=b[0]-a[0],b[1]-a[1];t=max(0.,min(1.,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy)))
        return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)
    obstacles=[t for key in excluded for t in triangles[key] if abs((t[1][0]-t[0][0])*(t[2][1]-t[0][1])-(t[1][1]-t[0][1])*(t[2][0]-t[0][0]))>1e-7]
    require(obstacles and all(triangles[key] for key in excluded),'Missing garden stepping stones')
    rng=random.Random(260920269);result=[]
    for key in sorted(wanted):
        tris=triangles[key];require(tris,'Missing original mulch bed '+key)
        edge_counts={}
        for t in tris:
            for i in range(3):
                edge=tuple(sorted((tuple(round(v,5) for v in t[i][:2]),tuple(round(v,5) for v in t[(i+1)%3][:2]))))
                edge_counts[edge]=edge_counts.get(edge,0)+1
        edges=[e for e,n in edge_counts.items() if n==1]
        xmin,ymin=[min(p[i] for t in tris for p in t) for i in (0,1)]
        xmax,ymax=[max(p[i] for t in tris for p in t) for i in (0,1)]
        for ix in range(math.ceil((xmax-xmin)/30)):
            for iy in range(math.ceil((ymax-ymin)/30)):
                p=[xmin+(ix+.5)*30+rng.uniform(-8,8),ymin+(iy+.5)*30+rng.uniform(-8,8),tris[0][0][2]+.6]
                selector=rng.random();role='shrub' if selector<.07 else 'grass' if selector<.29 else 'groundcover'
                radius=32. if role=='shrub' else 17.;height=rng.uniform(32,55) if role=='shrub' else rng.uniform(17,30) if role=='grass' else rng.uniform(10,18)
                if not any(inside(p,t) for t in tris) or min(distance(p,*edge) for edge in edges)<radius+2.: continue
                if any(inside(p,t) or min(distance(p,t[i],t[(i+1)%3]) for i in range(3))<radius+4. for t in obstacles): continue
                result.append({'sourceBedId':key,'role':role,'positionCm':p,'heightCm':height,'radiusCm':radius,'yawDeg':rng.uniform(0,360)})
    require(len(result)>=80,'Unexpectedly empty garden polygons')
    return result


def pipelines(u):
    result = []
    for original, name in [('GLTFSceneAssets','Assets'),('GLTFMaterials','Materials'),('LevelActors','Level')]:
        p = u.EditorAssetLibrary.duplicate_asset('/Game/Brezi/Pipeline/' + original, PREFIX + '/Pipeline/' + name)
        require(p, 'Cannot create exterior import pipeline'); result.append(p)
    mp = result[0].get_editor_property('mesh_pipeline')
    for key, value in [('combine_static_meshes_behavior',u.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE),
                       ('collision',False),('build_nanite',False),('generate_lightmap_u_vs',False)]: mp.set_editor_property(key, value)
    common_props = result[0].get_editor_property('common_meshes_properties')
    for key, value in [('remove_degenerates',False),('recompute_normals',False),('recompute_tangents',True),('use_full_precision_u_vs',True)]:
        common_props.set_editor_property(key,value)
    result[2].set_editor_property('scene_hierarchy_type',u.InterchangeSceneHierarchyType.CREATE_LEVEL_ACTORS)
    for p in result: require(u.EditorAssetLibrary.save_loaded_asset(p,False),'Pipeline save failed')
    return result


def import_meshes(u, file, expected, materials, pipeline, destination):
    actors = u.get_editor_subsystem(u.EditorActorSubsystem); levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    params = u.ImportAssetParameters()
    for key, value in [('is_automated',True),('replace_existing',False),('force_show_dialog',False),
                       ('override_pipelines',[u.SoftObjectPath(p.get_path_name()) for p in pipeline]),('import_level',levels.get_current_level())]:
        params.set_editor_property(key,value)
    before = {a.get_path_name() for a in actors.get_all_level_actors()}; manager = u.InterchangeManager.get_interchange_manager_scripted()
    require(manager.import_scene(PREFIX + '/Geometry/' + destination,manager.create_source_data(str(file)),params),'Exterior GLB import failed')
    result, temporary = {}, []
    for a in actors.get_all_level_actors():
        if a.get_path_name() in before: continue
        temporary.append(a)
        for c in a.get_components_by_class(u.StaticMeshComponent):
            mesh = c.get_editor_property('static_mesh'); require(mesh, 'Imported component lacks mesh')
            names = [key for key in expected if key == a.get_actor_label() or mesh.get_name() == key or mesh.get_name().endswith('_' + key)]
            require(len(names) == 1 and names[0] not in result, 'Ambiguous exterior mesh: ' + mesh.get_name() + ' / ' + a.get_actor_label())
            name = names[0]; keys = expected[name]
            slots=mesh.get_editor_property('static_materials')
            require(len(slots) == len(keys), 'Material slot count differs for ' + name)
            assigned=[]
            for i, slot in enumerate(slots):
                if len(keys)==1: key=keys[0]
                else:
                    identity=' '.join(str(slot.get_editor_property(p)) for p in ('material_slot_name','imported_material_slot_name'))
                    candidates=[k for k in keys if k in identity]
                    require(len(candidates)==1,'Unresolved imported material slot '+name+': '+identity)
                    key=candidates[0]
                require(key not in assigned,'Duplicate imported material slot'); assigned.append(key)
                mesh.set_material(i,materials[key])
            mesh.set_editor_property('has_navigation_data',False)
            u.EditorAssetLibrary.set_metadata_tag(mesh,'BreziGeneratedBy',OWNER)
            require(u.EditorAssetLibrary.save_loaded_asset(mesh,False),'Mesh save failed'); result[name] = mesh
    for a in reversed(temporary): require(actors.destroy_actor(a),'Cannot remove temporary import actor')
    require(set(result) == set(expected), 'Missing imported exterior mesh')
    return result


def mesh_bounds(mesh):
    box = mesh.get_bounding_box()
    return {'min':rural.vec(box.min),'max':rural.vec(box.max)}


def import_plants(u, manifest, materials, pipeline):
    by_file = {}
    for row in manifest['meshes']: by_file.setdefault(row['glbPath'], []).append(row)
    result = {}; subsystem = mesh_helper.static_mesh_subsystem(u)
    # static mesh helpers also support native import completion without GPU work.
    for index, (file, rows) in enumerate(by_file.items()):
        expected = {lod['nodeName']:row['materialKeys'] for row in rows for lod in row['lods']}
        imported = import_meshes(u,file,expected,materials,pipeline,'Plants_' + str(index))
        mesh_helper.finish_static_mesh_compilation(u,synchronous=True)
        for row in rows:
            mesh = imported[row['lods'][0]['nodeName']]
            for lod in row['lods']:
                actual = mesh_bounds(imported[lod['nodeName']]); target = lod['expectedBoundsCm']
                error = max(abs(actual[k][i]-target[k][i]) for k in ('min','max') for i in range(3))
                require(error < .05, 'Plant cm/axis/bounds mismatch: '+lod['nodeName']+' '+str((actual,target)))
            for lod in row['lods'][1:]:
                require(subsystem.set_lod_from_static_mesh(mesh,lod['level'],imported[lod['nodeName']],0,True)==lod['level'],'Plant LOD attach failed')
            mesh.modify(True)
            require(subsystem.set_lod_screen_sizes(mesh,plant_lod_screens(row)),'Plant LOD screens failed')
            require(u.EditorAssetLibrary.save_loaded_asset(mesh,False),'Plant mesh save failed'); result[row['id']] = mesh
    return result


def verify_plants(u, manifest, paths, materials):
    mesh_helper.finish_static_mesh_compilation(u,synchronous=True)
    subsystem=mesh_helper.static_mesh_subsystem(u); rows=[]
    for row in manifest['meshes']:
        mesh=u.EditorAssetLibrary.load_asset(paths[row['id']]); require(mesh,'Saved plant mesh missing')
        screens=list(subsystem.get_lod_screen_sizes(mesh)); target=plant_lod_screens(row)
        require(len(screens)==3 and all(abs(a-b)<1e-5 for a,b in zip(screens,target)),'Saved plant LOD settings differ')
        for lod in row['lods']:
            description=mesh.get_static_mesh_description(lod['level'])
            require(description and description.get_triangle_count()==lod['triangles'] and mesh.get_num_triangles(lod['level'])==lod['triangles'],'Plant LOD topology count differs')
        bound=[m.get_editor_property('material_interface').get_path_name() for m in mesh.get_editor_property('static_materials')]
        require(sorted(bound)==sorted(materials[k].get_path_name() for k in row['materialKeys']),'Saved plant slot bindings differ')
        rows.append({'id':row['id'],'mesh':paths[row['id']],'lodTriangles':[l['triangles'] for l in row['lods']],'lodScreens':screens,'materials':bound})
    return rows


def own_actor(u, a, label):
    a.set_editor_property('tags',[u.Name(TAG)]); a.set_actor_label(label)
    a.set_folder_path('Brezi/Exterior20260926'); a.set_actor_tick_enabled(False)
    return a


def plant_groups(manifest, old_plan, context):
    """Reuse verified near-road exclusion positions; interpret distant crop rows."""
    rng = random.Random(26092026)
    variants = {role:[m for m in manifest['meshes'] if m['role']==role and m.get('placementPolicy')!='explicit-only'] for role in ('grass','nettle','shrub','tree','vine','groundcover','forb','ornamental')}
    groups = {}
    def put(role, position, height, yaw, width=1., cull=22000, radius_limit=None, candidates=None, explicit_scale=None):
        options = candidates or variants[role]; require(options, 'Missing vegetation role: '+role)
        if candidates is None and role=='shrub' and variants['vine'] and rng.random()<.75: options=variants['vine']
        green=[r for r in options if r['id'].startswith('grass_bermuda')]
        if green and rng.random()<.88: options=green
        if role=='nettle': options=[r for r in options if 'tall' in r['id']] or options
        row = options[rng.randrange(len(options))]
        if row['id'].startswith('grass_bermuda') and height>34: height=rng.uniform(25,34)
        if role=='nettle' and height>38: height=rng.uniform(26,38)
        scale = height/row['heightCm']
        if radius_limit is not None:
            radius=max(math.hypot(x,y) for lod in row['lods'] for x in (lod['expectedBoundsCm']['min'][0],lod['expectedBoundsCm']['max'][0])
                       for y in (lod['expectedBoundsCm']['min'][1],lod['expectedBoundsCm']['max'][1]))
            width=min(width,radius_limit/max(radius*scale,1e-9))
        cell=2400 if role in ('grass','groundcover','nettle','forb') else 1800
        key = f'EX_{role}_{math.floor(position[0]/cell)}_{math.floor(position[1]/cell)}_{row["id"]}_{cull}'
        g = groups.setdefault(key,{'id':key,'meshId':row['id'],'role':role,'cullEndCm':cull,'instances':[]})
        transform_scale=explicit_scale or [scale*width,scale*width,scale]
        require(len(transform_scale)==3 and all(math.isfinite(v) and v>0 for v in transform_scale),'Invalid plant scale')
        g['instances'].append({'positionCm':list(position),'yawDeg':yaw,'scale':transform_scale})
    old_meshes={m['id']:m for m in old_plan['meshes']}
    for g in old_plan['groups']:
        role = 'grass' if g['meshId'].startswith('dry_grass') else 'nettle' if g['meshId'] in ('ragweed','thistle') else None
        if role is None: continue
        old_mesh=old_meshes[g['meshId']]
        old_radius=max(math.hypot(p[0],p[1]) for lod in [old_mesh,*old_mesh.get('lods',[])] for p in lod['verticesCm'])
        for row in g['instances']:
            radius=min(40.,old_radius*min(row['scale'][:2]))
            chosen=role
            if role=='nettle' and variants['shrub'] and rng.random()<.68: chosen='shrub'
            height = rng.uniform(22,52) if chosen=='grass' else rng.uniform(36,72)
            put(chosen,row['positionCm'],height,row['yawDeg'],rng.uniform(.85,1.2),12000,radius)
            # Low leaf litter/groundcover beneath taller planting. Every new
            # cluster remains inside the old plant's conservative footprint.
            if variants['groundcover'] and radius>18 and rng.random()<.7:
                for j in range(3):
                    angle=rng.uniform(0,math.tau); distance=radius*.45
                    p=[row['positionCm'][0]+math.cos(angle)*distance,row['positionCm'][1]+math.sin(angle)*distance,row['positionCm'][2]]
                    put('groundcover',p,rng.uniform(9,17),rng.uniform(0,360),1.,9000,radius*.45)
    for row in context.get('treePlacements',[]):
        semantic = row.get('kind',row.get('role',row.get('semantic','')))
        role = 'vine' if 'vine' in semantic and variants['vine'] else 'shrub' if any(s in semantic for s in ('vine','orchard','shrub')) else 'tree'
        height = row.get('heightCm',rng.uniform(130,170) if role=='shrub' else rng.uniform(450,700))
        put(role,row['positionCm'],height,row.get('yawDeg',rng.uniform(0,360)),row.get('widthScale',1.),50000,
            row.get('crownDiameterCm',200.)*.5)
    for row in context.get('groundCoverPlacements',[]):
        radius=row.get('radiusCm',35.)
        put(row.get('role','grass'),row['positionCm'],row.get('heightCm',rng.uniform(30,65)),row.get('yawDeg',rng.uniform(0,360)),1.,22000,radius)
        if variants['groundcover']:
            for j in range(3):
                a=rng.uniform(0,math.tau);p=[row['positionCm'][0]+math.cos(a)*radius*.5,row['positionCm'][1]+math.sin(a)*radius*.5,row['positionCm'][2]]
                put('groundcover',p,rng.uniform(9,18),rng.uniform(0,360),1.,13000,radius*.45)
    for row in context.get('gardenPlacements',[]):
        options = [m for m in manifest['meshes'] if m['id']==row['meshId']] if row.get('meshId') else None
        if row.get('meshId'):
            require(len(options)==1 and options[0]['role']==row['role'],'Garden detail mesh/role differs')
            require(len(row['scale'])==3 and max(row['scale'])-min(row['scale'])<1e-7,'Garden detail requires uniform scale')
        put(row['role'],row['positionCm'],row['heightCm'],row['yawDeg'],1.,row.get('cullEndCm',12000),row['radiusCm'],options,row.get('scale'))
    for row in context.get('meadowBasePlacements',[]):
        options=[m for m in variants['grass'] if m['id'].startswith('grass_bermuda')]
        require(options,'Meadow base requires green Bermuda prototypes')
        put('grass',row['positionCm'],row['heightCm'],row['yawDeg'],1.,9000,row['radiusCm'],options)
    for row in context.get('ornamentalPlacements',[]):
        pool=manifest['meshes'] if row.get('meshId') else variants['ornamental']
        options=[m for m in pool if m['role']=='ornamental' and m.get('form')==row['form'] and (not row.get('meshId') or m['id']==row['meshId'])]
        require(options,'Missing real garden plant form '+row['form'])
        put('ornamental',row['positionCm'],row['heightCm'],row['yawDeg'],1.,18000,row['radiusCm'],options,row.get('scale'))
    return list(groups.values())


def regional_groups(manifest, context):
    """Use the audited canopy placement exactly; never select a random species."""
    meshes={m['id']:m for m in manifest['meshes']}; groups={}
    for row in context.get('regionalVegetationPlacements',[]):
        mesh=meshes.get(row['meshId'])
        require(mesh and mesh['role'] in ('tree','shrub') and mesh.get('placementPolicy')=='explicit-only','Regional canopy requires an explicit tree/shrub asset')
        position,scale,yaw=row['positionCm'],row['scale'],row['yawDeg']
        require(len(position)==3 and all(math.isfinite(v) for v in position),'Invalid regional canopy position')
        require(len(scale)==3 and all(math.isfinite(v) and .1<=v<=3. for v in scale) and max(scale)-min(scale)<1e-7,'Regional canopies require bounded uniform scale')
        require(math.isfinite(yaw),'Invalid regional canopy rotation')
        cull=row['cullEndCm']
        require(isinstance(cull,(int,float)) and math.isfinite(cull) and 20000<=cull<=180000,'Invalid regional canopy draw distance')
        cell=5000
        key=f'EX_regional_{math.floor(position[0]/cell)}_{math.floor(position[1]/cell)}_{mesh["id"]}_{cull}'
        group=groups.setdefault(key,{'id':key,'meshId':mesh['id'],'role':mesh['role'],'cullEndCm':cull,'instances':[]})
        group['instances'].append({'positionCm':list(position),'yawDeg':yaw,'scale':list(scale)})
    return list(groups.values())


def native_meadow(u, context, source, prototype_path):
    """Instance the original authored blade meshes without modifying their assets."""
    placements=[*context.get('meadowBladePlacements',[]),*context.get('meadowUnderstoryPlacements',[]),*context.get('yardBladePlacements',[])]
    if not placements: return {}, [], {}
    evidence=read(source/'photoreal-import-report.json')['lawn']['geometry']
    records=read(prototype_path); lookup={r['id']:r for r in records}
    meshes={}; proof={}; bounds={}; subsystem=mesh_helper.static_mesh_subsystem(u)
    for variant in range(4):
        key=f'LawnTuft{variant}'; mesh=u.EditorAssetLibrary.load_asset(evidence['groups'][key]['mesh'])
        require(mesh,'Missing original native blade mesh')
        require([m.get_editor_property('material_interface').get_path_name() for m in mesh.get_editor_property('static_materials')]==[evidence['material']],'Native blade material differs')
        screens=list(subsystem.get_lod_screen_sizes(mesh))
        require(len(screens)==3 and all(abs(a-b)<1e-6 for a,b in zip(screens,evidence['lodScreenSizes'])),'Native blade LOD screens differ')
        proof[key]={'mesh':mesh.get_path_name(),'material':evidence['material'],'lodScreens':screens,
                    'lodProofs':[mesh_helper.mesh_proof(u,mesh,lookup[f'{key}_LOD{lod}'],lod) for lod in range(3)]}
        vertices=[p for r in records if r['variant']==variant for p in r['verticesMm']]
        bounds[key]={'height':max(p[2] for p in vertices)/10,'radius':max(math.hypot(p[0],p[1]) for p in vertices)/10}
        meshes[key]=mesh
    rng=random.Random(260920263); groups={}; maximum_radius=0.
    for row in placements:
        key=f'LawnTuft{rng.randrange(4)}'; p=row['positionCm']; shape=bounds[key]
        # Full-vertex radial bounds include every LOD and remain valid at any yaw.
        xy=row['radiusCm']/shape['radius']; z=row['heightCm']/shape['height']
        require(xy>0 and z>0 and row['radiusCm']<=14.,'Native meadow exceeds audited crown')
        gid=f'EX_meadow_{math.floor(p[0]/2000)}_{math.floor(p[1]/2000)}_{key}'
        g=groups.setdefault(gid,{'id':gid,'meshId':key,'role':'grass','cullEndCm':9000,'qualityDetail':True,'instances':[]})
        g['instances'].append({'positionCm':p,'yawDeg':row['yawDeg'],'scale':[xy,xy,z]})
        maximum_radius=max(maximum_radius,shape['radius']*xy)
    return meshes,list(groups.values()),{'instances':len(placements),'meadowInstances':len(context.get('meadowBladePlacements',[])),
        'understoryInstances':len(context.get('meadowUnderstoryPlacements',[])),
        'yardInstances':len(context.get('yardBladePlacements',[])),'prototypes':proof,
        'maximumWorldCrownRadiusCm':maximum_radius,'cullEndCm':9000,'originalAssetsUnchanged':True}


def hide_original(u, actors, original, old_plan, old_report, terrain=False, garden=None):
    lookup = {a.get_path_name():a for a in actors.get_all_level_actors()}; names = []
    for g in old_plan['groups']:
        if g['meshId'].startswith(('dry_grass','tree_')) or g['meshId'] in ('ragweed','thistle'):
            names.append(old_report['geometry']['groups'][g['id']]['actor'])
    for row in old_plan['meshes']:
        if row['id'].startswith('road_extension_'): names.append(old_report['geometry']['actors'][row['id']])
    changes = []
    for path in names:
        a = lookup[path]; require(a.actor_has_tag('BreziRural20260923'),'Unexpected hidden actor')
        for c in a.get_components_by_class(u.StaticMeshComponent):
            c.set_visibility(False,False); c.set_hidden_in_game(True,False)
            for flag in helper.RENDER_FLAGS: c.set_editor_property(flag,False)
            changes.append({'actor':path,'component':c.get_path_name(),'reason':'replace-procedural-rural-visual'})
    if terrain:
        component_path=old_report['sourceEdits']['DOM_02039']['component']
        matched=[]
        for a in actors.get_all_level_actors():
            for c in a.get_components_by_class(u.StaticMeshComponent):
                if a.get_path_name()+'/'+c.get_name()!=component_path: continue
                require('DOM_02039' in str(c.get_editor_property('static_mesh').get_path_name()),'Unexpected distant fallback mesh')
                c.set_visibility(False,False);c.set_hidden_in_game(True,False)
                for flag in helper.RENDER_FLAGS:c.set_editor_property(flag,False)
                matched.append({'actor':a.get_path_name(),'component':c.get_path_name(),'reason':'replace-flat-background-with-elevation-context'})
        require(len(matched)==1,'Distant terrain source missing');changes.extend(matched)
    if garden:
        wanted={key for row in garden for key in row['sourceIds']};found=[]
        require(wanted=={'DOM_'+str(i).zfill(5) for i in range(1967,2003)},'Unexpected garden replacement scope')
        for a in actors.get_all_level_actors():
            for c in a.get_components_by_class(u.StaticMeshComponent):
                mesh=c.get_editor_property('static_mesh')
                if not mesh or mesh.get_name() not in wanted: continue
                found.append(mesh.get_name());c.set_visibility(False,False);c.set_hidden_in_game(True,False)
                for flag in helper.RENDER_FLAGS:c.set_editor_property(flag,False)
                changes.append({'actor':a.get_path_name(),'component':c.get_path_name(),'sourceId':mesh.get_name(),'reason':'replace-crossed-garden-cards-with-spatial-planting'})
        require(len(found)==len(wanted) and set(found)==wanted,'Garden card source mapping differs')
    return changes


def rebind_garden_soil(u, actors, old_report, materials, green_sources=()):
    changes=[]
    selected={v:k for k,v in old_report['geometry']['actors'].items() if k.startswith('verge_') or k in ('parcel_outer_raw_soil','rear_field_topsoil_mound')}
    require(set(green_sources)<=set(selected.values()),'Unreviewed yard material binding')
    for a in actors.get_all_level_actors():
        if a.get_path_name() not in selected: continue
        target=materials['context_meadow' if selected[a.get_path_name()] in green_sources else 'context_garden_soil']
        require(a.actor_has_tag('BreziRural20260923'),'Garden soil target is not a rural visual')
        for c in a.get_components_by_class(u.StaticMeshComponent):
            require(c.get_num_materials()==1,'Unexpected garden soil slots')
            previous=c.get_material(0);require(previous and '/Rural20260923/' in previous.get_path_name(),'Unexpected garden soil source')
            c.set_material(0,target)
            changes.append({'actor':a.get_path_name(),'component':c.get_path_name(),'slot':0,'before':previous.get_path_name(),'after':target.get_path_name()})
    require(len(changes)==len(selected),'Incomplete garden soil bindings')
    beds=[]
    for a in actors.get_all_level_actors():
        for c in a.get_components_by_class(u.StaticMeshComponent):
            mesh=c.get_editor_property('static_mesh')
            if not mesh or mesh.get_name() not in ('DOM_01965','DOM_01966'):continue
            require(c.get_num_materials()==1,'Unexpected original mulch slots');previous=c.get_material(0)
            c.set_material(0,materials['context_mulch']);beds.append(mesh.get_name())
            changes.append({'actor':a.get_path_name(),'component':c.get_path_name(),'slot':0,'before':previous.get_path_name(),'after':materials['context_mulch'].get_path_name()})
    require(sorted(beds)==['DOM_01965','DOM_01966'],'Missing original mulch bed')
    return changes


def build_scene(u, context, plants, materials, meshes, output):
    actors = u.get_editor_subsystem(u.EditorActorSubsystem); result = {'actors':{},'groups':{},'meshes':{}}
    prototypes={g['meshId'] for g in context.get('groups',[])}
    for row in context['meshes']:
        mesh = meshes[row['id']+'_LOD0']
        result['meshes'][row['id']] = mesh.get_path_name()
        if row['id'] in prototypes: continue
        a = own_actor(u,actors.spawn_actor_from_class(u.StaticMeshActor,u.Vector(0,0,0),u.Rotator()),'EX_'+row['id'])
        c = a.static_mesh_component; c.set_static_mesh(mesh); rural.new_component_policy(u,c)
        c.set_editor_property('cast_shadow',row.get('castShadow',row['material']=='context_boundary_post'))
        if row.get('maxDrawDistanceCm'):c.set_cull_distance(float(row['maxDrawDistanceCm']))
        result['actors'][row['id']] = a.get_path_name(); result['meshes'][row['id']] = mesh.get_path_name()
    for g in [*plants,*context.get('groups',[])]:
        prototype = meshes.get(g['meshId'],meshes.get(g['meshId']+'_LOD0'))
        require(prototype,'Missing exterior instance prototype')
        a = own_actor(u,actors.spawn_actor_from_class(u.load_class(None,'/Script/BreziTwin.BreziVegetationPatch'),u.Vector(0,0,0),u.Rotator()),g['id'])
        c = a.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
        c.set_static_mesh(prototype); rural.new_component_policy(u,c)
        c.set_cull_distances(int(g['cullEndCm']*.8),g['cullEndCm']); c.set_editor_property('cast_shadow',g.get('castShadow',True))
        c.set_editor_property('visible_in_ray_tracing',True)
        c.set_editor_property('affect_distance_field_lighting',g.get('role') in ('tree','shrub','vine'))
        if g['id'].startswith('EX_transition_'):
            require(g['meshId'] in ('grass_medium_02_a','grass_medium_02_b','grass_medium_02_c')
                    and g.get('qualityDetail') is False and g.get('castShadow') is False and g['cullEndCm']==4000,
                    'Unreviewed compact transition group policy')
            require(a.set_detail_density_scaling(False),'Cannot preserve compact transition density')
        if g.get('qualityDetail'):
            a.set_editor_property('tags',[u.Name(TAG),u.Name('BreziLawnDetail')])
            # Existing runtime quality control restores cinematic shadows and
            # ray tracing; lower profiles can reduce this visual-only detail.
            c.set_editor_property('cast_shadow',False);c.set_editor_property('visible_in_ray_tracing',False)
            require(a.set_detail_density_scaling(True),'Cannot enable native meadow quality scaling')
        indices = list(c.add_instances([rural.instance_transform(u,r) for r in g['instances']],True,False,False))
        require(indices==list(range(len(g['instances']))),'Plant instances differ'); a.synchronize_instance_bounds()
        result['groups'][g['id']] = {'actor':a.get_path_name(),'mesh':prototype.get_path_name(),'instances':len(indices),
                                   'cullStartCm':int(g['cullEndCm']*.8),'cullEndCm':g['cullEndCm'],
                                   'qualityDetail':g.get('qualityDetail',False),
                                   'transformsSha256':digest([base.instance_value(c,i) for i in range(len(indices))])}
    write(output/'exterior-placements.json',plants)
    return result


def readback(u, record):
    actors = {a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
    count = 0
    for row in record['groups'].values():
        c = actors[row['actor']].get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
        require(c.get_instance_count()==row['instances'] and c.get_editor_property('static_mesh').get_path_name()==row['mesh'],'Plant readback differs')
        require(c.get_editor_property('instance_start_cull_distance')==row['cullStartCm'] and c.get_editor_property('instance_end_cull_distance')==row['cullEndCm'],'Saved exterior cull distances differ')
        if row['qualityDetail']:
            a=actors[row['actor']]
            require(a.actor_has_tag('BreziLawnDetail') and a.get_detail_density_scaling(),'Saved meadow quality scaling differs')
            require(not c.get_editor_property('cast_shadow') and not c.get_editor_property('visible_in_ray_tracing'),'Saved meadow authored quality flags differ')
        require(digest([base.instance_value(c,i) for i in range(c.get_instance_count())])==row['transformsSha256'],'Saved plant positions differ')
        count += c.get_instance_count()
    owned = [a for a in actors.values() if a.actor_has_tag(TAG)]
    require({a.get_path_name() for a in owned}==set(record['actors'].values())|{r['actor'] for r in record['groups'].values()},'Exterior ownership differs')
    for a in owned:
        for c in a.get_components_by_class(u.PrimitiveComponent):
            require(c.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION and not c.get_editor_property('can_ever_affect_navigation'),'Exterior collision introduced')
    return {'meshCount':len(record['meshes']),'groupCount':len(record['groups']),'instanceCount':count,'allNewVisualsNoCollision':True}


def verify_transition_scene(u, validation, source_context, geometry, materials, plant_paths, native_topology, include_groups=True):
    """Read saved bindings and every additive instance against source transforms."""
    actors={a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
    source_meshes={m['id']:m for m in source_context['meshes']}
    original_native={m['sourceMeshId']:m for m in native_topology['rows']}
    bindings=[]; position_error=scale_error=rotation_error=0.; instances=0
    for binding in validation['materialBindings']:
        identity=binding['sourceMeshId']; source_mesh=source_meshes[identity]
        actor=actors[geometry['actors'][identity]]; component=actor.static_mesh_component
        mesh=component.get_editor_property('static_mesh'); material=materials[binding['proposedSharedMaterialKey']]
        require(mesh.get_path_name()==geometry['meshes'][identity], 'Saved transition source mesh binding differs')
        require(component.get_num_materials()==1 and component.get_material(0)==material,
                'Saved transition shared material binding differs')
        actor_transform=base.transform(actor.get_actor_transform())
        require(actor_transform==[[0.,0.,0.],[0.,0.,0.,1.],[1.,1.,1.]],
                'Saved transition ground transform differs')
        description=mesh.get_static_mesh_description(0)
        triangles=len(source_mesh['indices'])//3
        original=original_native[identity]
        require(original['sourceGeometrySha256']==binding['sourceGeometrySha256']
                and original['sourceTriangles']==original['descriptionTriangles']==triangles,
                'Original native transition source topology differs: '+identity)
        render_triangles=mesh.get_num_triangles(0)
        require(description and description.get_triangle_count()==triangles
                and description.get_vertex_count()==original['descriptionVertices']==len(source_mesh['verticesCm'])
                and render_triangles==original['renderTriangles'],
                'Saved transition source/render topology differs: '+identity)
        actual=mesh_bounds(mesh)
        expected={key:[fn(p[axis] for p in source_mesh['verticesCm']) for axis in range(3)]
                  for key,fn in [('min',min),('max',max)]}
        bounds_error=max(abs(actual[key][axis]-expected[key][axis]) for key in expected for axis in range(3))
        require(bounds_error<.05,
                'Saved transition source ground bounds differ')
        require(component.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION
                and not component.get_editor_property('can_ever_affect_navigation'), 'Transition ground collision introduced')
        bindings.append({'sourceMeshId':identity,'actor':actor.get_path_name(),'mesh':mesh.get_path_name(),
                         'material':material.get_path_name(),'triangles':triangles,
                         'renderTriangles':render_triangles,'descriptionVertices':description.get_vertex_count(),
                         'sourceGeometrySha256':binding['sourceGeometrySha256'],'actualBoundsCm':actual,
                         'expectedBoundsCm':expected,'maximumBoundsErrorCm':bounds_error,
                         'actorTransform':actor_transform,'collision':'NoCollision','canEverAffectNavigation':False})
    group_ids=[]
    for group in (validation['groups'] if include_groups else []):
        saved=geometry['groups'][group['id']]; actor=actors[saved['actor']]
        component=actor.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
        require(saved['instances']==component.get_instance_count()==len(group['instances'])
                and saved['mesh']==plant_paths[group['meshId']], 'Saved transition instance prototype/count differs')
        require(not component.get_editor_property('cast_shadow') and not actor.get_detail_density_scaling(),
                'Saved transition low-margin quality flags differ')
        require(component.get_editor_property('instance_start_cull_distance')==group['cullStartCm']
                and component.get_editor_property('instance_end_cull_distance')==group['cullEndCm'],
                'Saved transition cull policy differs')
        for index,row in enumerate(group['instances']):
            expected=base.transform(rural.instance_transform(u,row)); actual=base.instance_value(component,index)
            position_error=max(position_error,max(abs(a-b) for a,b in zip(actual[0],expected[0])))
            scale_error=max(scale_error,max(abs(a-b) for a,b in zip(actual[2],expected[2])))
            rotation_error=max(rotation_error,min(max(abs(a-b) for a,b in zip(actual[1],expected[1])),
                                                  max(abs(a+b) for a,b in zip(actual[1],expected[1]))))
            instances+=1
        group_ids.append(group['id'])
    # HISM instance matrices store float32 values. These explicit native
    # readback bounds are smaller than the source study's 1mm crown guard.
    require(position_error<=.002 and scale_error<=1e-6 and rotation_error<=2e-6,
            'Saved transition source transforms exceed float32 readback bounds')
    require(len(bindings)==65 and (len(group_ids)==158 and instances==7000 if include_groups else not group_ids and instances==0),
            'Saved transition inventory differs')
    return {'status':'verified-saved-neighborhood-transition' if include_groups else 'verified-saved-neighborhood-ground-bindings',
            'materialBindings':bindings,'groupIds':group_ids,
            'instances':instances,'maximumPositionErrorCm':position_error,'maximumScaleError':scale_error,
            'maximumQuaternionErrorSignEquivalent':rotation_error,'allNewVisualsNoCollision':True,
            'sourceGroundBoundsTopologyAndOriginVerified':True,'sourceTransformsComparedAfterReload':True,
            'nativeVisualAccepted':False,'performanceAccepted':False}


def verify_continuous_meadow_scene(u, plan, validation, source_context, geometry, materials,
                                  meadow_groups, plant_paths, native_topology, transition_validation):
    """Read actual saved soil topology, retained heights and ordered restorations."""
    actors={a.get_path_name():a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
    ground=verify_transition_scene(u,transition_validation,source_context,geometry,materials,plant_paths,
                                  native_topology,include_groups=False)
    omitted=plan['soilOverlayProposal']['omitMeshIds']
    require(len(omitted)==4 and all(k not in geometry['actors'] and k not in geometry['meshes'] for k in omitted),
            'Saved unbuilt soil overlays remain')
    replacement_proofs={r['sourceMeshId']:r for r in plan['soilOverlayProposal']['triangles'] if r.get('replacementMeshSha256')}
    source_subsets={m['id']:m for m in validation['neighborhoodMeshes'] if m['id'] in replacement_proofs}
    require(len(source_subsets)==4,'Saved cultivated subset source inventory differs')
    subsets=[]
    for identity,source_mesh in source_subsets.items():
        actor=actors[geometry['actors'][identity]];component=actor.static_mesh_component
        mesh=component.get_editor_property('static_mesh');material=materials['context_soil_exposure']
        require(mesh.get_path_name()==geometry['meshes'][identity] and component.get_num_materials()==1
                and component.get_material(0)==material,'Saved cultivated soil mesh/material differs')
        require(base.transform(actor.get_actor_transform())==[[0.,0.,0.],[0.,0.,0.,1.],[1.,1.,1.]],
                'Saved cultivated soil origin differs')
        proof=rural.mesh_proof(u,mesh,source_mesh,0)
        description=mesh.get_static_mesh_description(0)
        require(0<description.get_vertex_count()<=len(source_mesh['verticesCm'])
                and proof['maximumSourcePositionFloat32ErrorCm']<=.002
                and digest(source_mesh)==replacement_proofs[identity]['replacementMeshSha256'],
                'Saved cultivated source representation differs')
        require(component.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION
                and not component.get_editor_property('can_ever_affect_navigation'),'Cultivated soil collision introduced')
        subsets.append({'sourceMeshId':identity,'actor':actor.get_path_name(),'mesh':mesh.get_path_name(),
            'material':material.get_path_name(),'triangles':proof['triangles'],
            'sourceGeometrySha256':replacement_proofs[identity]['replacementMeshSha256'],
            'descriptionVertices':description.get_vertex_count(),'sourceVertices':len(source_mesh['verticesCm']),
            'referencedSourceVertices':len(set(source_mesh['indices'])),
            'maximumPositionErrorCm':proof['maximumSourcePositionFloat32ErrorCm'],
            'maximumUVError':proof['maximumSourceUVFloat32Error'],
            'triangleConnectivityWindingVerified':proof['topologyUVAndCmScaleVerified'],
            'nativeFloat32RepresentationExact':proof['nativeFloat32RepresentationExact'],
            'collision':'NoCollision','canEverAffectNavigation':False})
    cultivated_unchanged=[]
    neighborhood_meshes={m['id']:m for m in validation['neighborhoodMeshes']}
    for identity in plan['soilOverlayProposal']['unchangedCultivatedMeshIds']:
        source_mesh=neighborhood_meshes[identity];actor=actors[geometry['actors'][identity]]
        component=actor.static_mesh_component;mesh=component.get_editor_property('static_mesh')
        material=materials['context_soil_exposure']
        require(mesh.get_path_name()==geometry['meshes'][identity] and component.get_num_materials()==1
                and component.get_material(0)==material and base.transform(actor.get_actor_transform())==[[0.,0.,0.],[0.,0.,0.,1.],[1.,1.,1.]],
                'Saved unchanged cultivated soil binding/origin differs')
        proof=rural.mesh_proof(u,mesh,source_mesh,0)
        require(component.get_collision_enabled()==u.CollisionEnabled.NO_COLLISION
                and not component.get_editor_property('can_ever_affect_navigation'),
                'Unchanged cultivated soil collision introduced')
        cultivated_unchanged.append({'sourceMeshId':identity,'actor':actor.get_path_name(),'mesh':mesh.get_path_name(),
            'material':material.get_path_name(),'triangles':proof['triangles'],'sourceGeometrySha256':digest(source_mesh),
            'descriptionVertices':mesh.get_static_mesh_description(0).get_vertex_count(),
            'maximumPositionErrorCm':proof['maximumSourcePositionFloat32ErrorCm'],
            'triangleConnectivityWindingVerified':proof['topologyUVAndCmScaleVerified'],
            'nativeFloat32RepresentationExact':proof['nativeFloat32RepresentationExact']})
    cultivated_triangles=sum(row['triangles'] for row in [*subsets,*cultivated_unchanged])
    require(len(cultivated_unchanged)==7 and cultivated_triangles==2801,
            'Saved all eleven cultivated soil pieces differ')
    retirement=plan['futureVisualRetirement']
    retired_ids=[*retirement['transitionGroupIds'],*retirement['pilotGroupIds']]
    require(len(retired_ids)==len(set(retired_ids))==259 and all(k not in geometry['groups'] for k in retired_ids),
            'Retired meadow pilot/transition groups remain')
    position_error=scale_error=rotation_error=0.;compared=restored_instances=0
    original_prototypes={g['meshId']:(g['nativeMesh'],g['nativeMaterial']) for g in validation['restoredGroups']}
    require(set(original_prototypes)=={'LawnTuft0','LawnTuft1','LawnTuft2','LawnTuft3'},
            'Continuous original native prototype lookup incomplete')
    for group in [*meadow_groups,*validation['restoredGroups']]:
        saved=geometry['groups'][group['id']];actor=actors[saved['actor']]
        component=actor.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
        require(component.get_instance_count()==saved['instances']==len(group['instances']),
                'Saved continuous meadow source membership differs')
        expected_mesh,expected_material=original_prototypes[group['meshId']]
        require(saved['mesh']==component.get_editor_property('static_mesh').get_path_name()==expected_mesh
                and component.get_num_materials()==1 and component.get_material(0).get_path_name()==expected_material,
                'Saved continuous original prototype/material differs')
        if group['id'].startswith('EX_meadow_restored_'):
            require(saved['mesh']==group['nativeMesh'] and component.get_material(0).get_path_name()==group['nativeMaterial'],
                    'Saved restoration original prototype/material differs')
            restored_instances+=component.get_instance_count()
        require(actor.actor_has_tag('BreziLawnDetail') and actor.get_detail_density_scaling()
                and not component.get_editor_property('cast_shadow')
                and not component.get_editor_property('visible_in_ray_tracing')
                and component.get_editor_property('instance_start_cull_distance')==7200
                and component.get_editor_property('instance_end_cull_distance')==9000,
                'Saved continuous meadow authored quality/cull policy differs')
        for index,row in enumerate(group['instances']):
            expected=base.transform(rural.instance_transform(u,row));actual=base.instance_value(component,index)
            position_error=max(position_error,max(abs(a-b) for a,b in zip(actual[0],expected[0])))
            scale_error=max(scale_error,max(abs(a-b) for a,b in zip(actual[2],expected[2])))
            rotation_error=max(rotation_error,min(max(abs(a-b) for a,b in zip(actual[1],expected[1])),
                                                  max(abs(a+b) for a,b in zip(actual[1],expected[1]))))
            compared+=1
    require(position_error<=.002 and scale_error<=1e-6 and rotation_error<=2e-6,
            'Saved continuous source transforms exceed float32 readback bounds')
    require(restored_instances==39834 and len(geometry['groups'])==1980
            and sum(g['instances'] for g in geometry['groups'].values())==632026
            and len(geometry['meshes'])==547 and len(geometry['actors'])==544,
            'Saved continuous full inventory differs')
    return {'status':'verified-saved-continuous-meadow-layout','restoredGroups':164,'restoredInstances':restored_instances,
        'heightOnlyOverrides':validation['audit']['retainedHeightOnlyOverrides'],
        'soilTrianglesOmitted':103392,'cultivatedRetained':cultivated_triangles,'bindings':len(ground['materialBindings']),
        'groupIds':[g['id'] for g in validation['restoredGroups']],
        'retiredGroupIds':retired_ids,'retiredGroupsAbsent':True,'materialBindings':ground['materialBindings'],
        'soilSubsets':subsets,'cultivatedUnchanged':cultivated_unchanged,'orderedNativeTransformsVerifiedAfterReload':True,
        'sourceGroundBoundsTopologyAndOriginVerified':ground['sourceGroundBoundsTopologyAndOriginVerified'],
        'sourceTransformsComparedAfterReload':True,'comparedNativeMeadowInstances':compared,
        'maximumPositionErrorCm':position_error,'maximumScaleError':scale_error,
        'maximumQuaternionErrorSignEquivalent':rotation_error,'allNewVisualsNoCollision':True,
        'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False}


def main():
    import unreal as u
    source, output = base.checked_paths(ROOT/os.environ['BREZI_PERFORMANCE_SOURCE'],ROOT/os.environ['BREZI_MODEL_OUTPUT'])
    project = output/'Project/BreziTwin'; content = project/'Content'
    require(Path(u.Paths.project_dir()).resolve()==project,'Wrong exterior project')
    provenance = read(output/'performance-source.json'); before = inventory(content)
    require(before==provenance['content'] and not (output/'exterior-import-report.json').exists(),'Exterior requires exact fresh inherited scene')
    donor_before = inventory(source/'Project/BreziTwin/Content')
    context_path = Path(os.environ['BREZI_EXTERIOR_CONTEXT']).resolve()
    asset_dir = Path(os.environ['BREZI_EXTERIOR_ASSETS']).resolve()
    context = read(context_path); manifest = read(asset_dir/'geometry-manifest.json'); material_manifest = read(asset_dir/'material-manifest.json')
    photo_material_path = Path(os.environ['BREZI_EXTERIOR_LAWN_PHOTO_MATERIAL']).resolve() if os.environ.get('BREZI_EXTERIOR_LAWN_PHOTO_MATERIAL') else None
    infill_path = Path(os.environ['BREZI_EXTERIOR_MEADOW_INFILL']).resolve() if os.environ.get('BREZI_EXTERIOR_MEADOW_INFILL') else None
    infill = read(infill_path) if infill_path else None
    continuous_path=Path(os.environ['BREZI_EXTERIOR_CONTINUOUS_MEADOW']).resolve() if os.environ.get('BREZI_EXTERIOR_CONTINUOUS_MEADOW') else None
    continuous=read(continuous_path) if continuous_path else None
    continuous_module=None;continuous_validation=None
    canopy_path=Path(os.environ['BREZI_EXTERIOR_CANOPY']).resolve() if os.environ.get('BREZI_EXTERIOR_CANOPY') else None
    canopy=read(canopy_path) if canopy_path else None
    fullness = canopy and canopy.get('owner') == 'scripts/unreal/exterior-canopy-fullness-study.py'
    fullness_module=None; preserved_plant_manifest=manifest
    if fullness:
        fullness_module=module('exterior_canopy_fullness_native','exterior-canopy-fullness-native.py')
        preserved_plant_manifest=fullness_module.validated_libraries(manifest)['original126']
    infill_module = None; infill_validation = None; photo_plant_manifest = preserved_plant_manifest
    photo_module = None; original_plant_manifest = preserved_plant_manifest
    if infill:
        require(photo_material_path is not None, 'Low meadow pilot requires the frozen photographic library')
        infill_module = module('exterior_meadow_infill_native', 'exterior-meadow-infill-native.py')
        libraries = infill_module.validated_libraries(preserved_plant_manifest)
        photo_plant_manifest = libraries['original120']
        original_plant_manifest = libraries['original100']
    if photo_material_path:
        photo_module = module('exterior_lawn_photo_native', 'exterior-lawn-photo-native.py')
        original_plant_manifest = photo_module.validated_base_library(photo_plant_manifest)
        require(manifest['photoMaterialManifest']=={'path':str(photo_material_path),'sha256':sha(photo_material_path)},
                'Photo lawn library/material sidecar differs')
    require(context['owner'] in ('scripts/unreal/exterior-context.py','scripts/unreal/exterior-meadow.py','scripts/unreal/exterior-meadow-blades.py','scripts/unreal/exterior-regional-vegetation.py'),'Unreviewed exterior context generator')
    require(context['generatorSha256']==sha(ROOT/context['owner']),'Context generator drift')
    require(context['sourceSceneSha256']==sha(output/'geometry/scene.json') and context['sourceObjSha256']==sha(output/'geometry/dom-mm.obj'),'Context architectural source differs')
    source_context=copy.deepcopy(context)
    if infill:
        extension_pin = infill['infillGeometryManifest']
        require(sha(extension_pin['path']) == extension_pin['sha256'], 'Low meadow geometry extension drift')
        infill_validation = infill_module.validated_infill(infill, read(extension_pin['path']), preserved_plant_manifest,
            context['sourceSceneSha256'], context['sourceObjSha256'], source_context)
    transition_path=Path(os.environ['BREZI_EXTERIOR_NEIGHBORHOOD_TRANSITION']).resolve() if os.environ.get('BREZI_EXTERIOR_NEIGHBORHOOD_TRANSITION') else None
    transition=read(transition_path) if transition_path else None
    transition_validation=None
    native_topology=None; native_topology_path=None
    if transition:
        transition_module=module('exterior_neighborhood_transition_native','exterior-neighborhood-transition-native.py')
        transition_validation=transition_module.validated_transition(transition,source_context,preserved_plant_manifest,
            context['sourceSceneSha256'],context['sourceObjSha256'])
        native_topology_path=ROOT/'output/unreal/exterior-validation-20260930-r1/r12-native-ground-topology-baseline.json'
        require(sha(native_topology_path)=='be3733f6e20cca1080e352d85f66bc5cd063b39632326885330582d0ba1a641a',
                'Original native ground topology observation differs')
        native_topology=read(native_topology_path)
        require(native_topology['status']=='VERIFIED_ACTUAL_ORIGINAL_AND_PROPOSED_NATIVE_GROUND_TOPOLOGY_IDENTICAL'
                and native_topology['all65ActualNativeTopologyVertexCountsAndBoundsUnchanged']
                and native_topology['allSourceDescriptionTriangleCountsExact']
                and native_topology['oldSceneAndCloneAndFailedProposalContentHashesUnchangedAfterReadOnlyProbes']
                and native_topology['sourceNativeBaseline']=={'path':str(ROOT/'output/unreal/exterior-20261001-r11/exterior-import-report.json'),
                    'sha256':'6608bfdada21b9de8540dfead615a668a60cd1a2ff6cceab6c8c0eded0cd5e21'}
                and len(native_topology['rows'])==len({r['sourceMeshId']for r in native_topology['rows']})==65,
                'Original native transition topology proof is incomplete')
    ecology_path=Path(os.environ['BREZI_EXTERIOR_ECOLOGY']).resolve() if os.environ.get('BREZI_EXTERIOR_ECOLOGY') else None
    ecology=read(ecology_path) if ecology_path else None
    canopy_module=None; canopy_validation=None; ecology_validation=None; ecology_groups=[]
    if canopy or ecology:canopy_module=module('exterior_canopy_native','exterior-canopy-native.py')
    for plan in (canopy,ecology):
        if plan:
            pin=plan['geometryManifest'];require(sha(pin['path'])==pin['sha256'],'Grove geometry manifest drift')
            require(plan['sourceContext']=={'path':str(context_path),'sha256':sha(context_path)},'Grove source context differs')
    if canopy:
        replacement_module=fullness_module if fullness else canopy_module
        canopy_validation=replacement_module.validated_replacements(canopy,read(canopy['geometryManifest']['path']),
            source_context,manifest,context['sourceSceneSha256'],context['sourceObjSha256'])
        replacements={r['id']:r for r in canopy_validation['placements']}
        require(len(replacements)==78,'Grove tree replacement inventory differs')
        original_rows=context['regionalVegetationPlacements']
        context['regionalVegetationPlacements']=[replacements.get(r['id'],r) for r in original_rows]
        require(all(a==b for a,b in zip(original_rows,context['regionalVegetationPlacements']) if a['id'] not in replacements),
                'Non-grove regional vegetation changed')
    if ecology:
        ecology_validation=canopy_module.validated_ecology(ecology,read(ecology['geometryManifest']['path']),
            source_context,preserved_plant_manifest,context['sourceSceneSha256'],context['sourceObjSha256'])
        ecology_groups=ecology_validation['groups']
    snapshot=context_path.parent/'inputs/cuzk-parcels.gml'
    require(sha(snapshot)==context['sourceEvidence']['sha256'],'Official parcel snapshot differs')
    terrain_path=Path(os.environ['BREZI_EXTERIOR_TERRAIN']).resolve() if os.environ.get('BREZI_EXTERIOR_TERRAIN') else None
    terrain=read(terrain_path) if terrain_path else None
    ortho_path=Path(os.environ['BREZI_EXTERIOR_ORTHO']).resolve() if os.environ.get('BREZI_EXTERIOR_ORTHO') else None
    ortho=read(ortho_path) if ortho_path else None
    seasonal_path=Path(os.environ['BREZI_EXTERIOR_SEASONAL_FIELDS']).resolve() if os.environ.get('BREZI_EXTERIOR_SEASONAL_FIELDS') else None
    seasonal=read(seasonal_path) if seasonal_path else None
    field_macro_path=Path(os.environ['BREZI_EXTERIOR_FIELD_MACRO']).resolve() if os.environ.get('BREZI_EXTERIOR_FIELD_MACRO') else None
    field_macro=read(field_macro_path) if field_macro_path else None
    projection_path=Path(os.environ['BREZI_EXTERIOR_ORTHO_PROJECTION']).resolve() if os.environ.get('BREZI_EXTERIOR_ORTHO_PROJECTION') else None
    projection=read(projection_path) if projection_path else None
    if projection:
        require(ortho and projection['schemaVersion']==1 and projection['owner']=='scripts/unreal/exterior-ortho-projection-mask.py','Unreviewed aerial projection mask')
        require(projection['generatorSha256']==sha(ROOT/projection['owner']),'Aerial projection generator drift')
        require(projection['sourceSceneSha256']==context['sourceSceneSha256'] and projection['sourceObjSha256']==context['sourceObjSha256'],'Aerial projection architectural frame differs')
        require(projection['activeDesign']==context['activeDesign'],'Aerial projection selection differs')
        require(projection['inputFiles'].get(str(context_path))==sha(context_path),'Aerial projection context differs')
    if field_macro:
        require(field_macro['owner'] in ('scripts/unreal/exterior-field-macro.py','scripts/unreal/exterior-field-macro-r3.py') and field_macro['schemaVersion']==1,'Unreviewed field macro generator')
        require(field_macro['inputFiles'].get(str(ROOT/field_macro['owner']))==sha(ROOT/field_macro['owner']),'Field macro generator drift')
        require(field_macro['sourceSceneSha256']==context['sourceSceneSha256'] and field_macro['sourceObjSha256']==context['sourceObjSha256'],'Field macro architectural frame differs')
        require(field_macro['inputFiles'].get(str(context_path))==sha(context_path),'Field macro context differs')
        require(field_macro['summary']['protectedIntersections']==field_macro['summary']['unsupportedPixels']==0,'Field macro exclusions failed')
    if ortho:
        require(terrain and ortho['schemaVersion']==1,'Orthophoto requires verified terrain')
        require(ortho['inputFiles'].get(str(terrain_path))==sha(terrain_path),'Orthophoto terrain reference differs')
        scene_pins=[h for p,h in ortho['inputFiles'].items() if p.endswith('/geometry/scene.json')]
        require(scene_pins==[context['sourceSceneSha256']],'Orthophoto architectural frame differs')
        require(ortho['worldFrame']['housePlacement']['streetSetbackMm']==ortho['worldFrame']['housePlacement']['eastSetbackMm']==3000,'Orthophoto setbacks differ')
    if seasonal:
        require(ortho and seasonal['schemaVersion']==1,'Seasonal fields require verified orthophoto')
        require(seasonal['orthoManifest']=={'path':str(ortho_path),'sha256':sha(ortho_path)},'Seasonal fields orthophoto reference differs')
        require(seasonal['sourceObservationUnchanged'] is True,'Seasonal fields must retain source observations')
    if terrain:
        require(terrain['generatorSha256']==sha(ROOT/'scripts/unreal/exterior-terrain.py'),'Terrain generator drift')
        require(terrain['sourceSceneSha256']==context['sourceSceneSha256'],'Terrain architectural reference differs')
        require(terrain['activeDesign']==context['activeDesign'] and terrain['heightPolicy']['verticalExaggeration']==1.,'Invalid terrain reference')
        require(terrain['noDataFallback']['enabled'] and terrain['noDataFallback']['measured'] is False,'Unresolved terrain must be explicit')
        require(terrain['noDataFallback']['replaceOriginalFlatVisualSourceIds']==['DOM_02039'],'Unreviewed terrain replacement')
        context['meshes'].extend(terrain['meshes']);context.setdefault('groups',[]).extend(terrain.get('groups',[]))
        require(len({m['id'] for m in context['meshes']})==len(context['meshes']),'Duplicate terrain/context mesh')
    buildings_path=Path(os.environ['BREZI_EXTERIOR_BUILDINGS']).resolve() if os.environ.get('BREZI_EXTERIOR_BUILDINGS') else None
    buildings=read(buildings_path) if buildings_path else None
    if buildings:
        require(buildings['sourceSceneSha256']==context['sourceSceneSha256'],'Village architectural reference differs')
        require(buildings['activeDesign']==context['activeDesign'],'Village selection differs')
        context['meshes'].extend(buildings['meshes']);context.setdefault('groups',[]).extend(buildings.get('groups',[]))
        require(len({m['id'] for m in context['meshes']})==len(context['meshes']),'Duplicate village/context mesh')
    if field_macro:require(buildings_path and field_macro['inputFiles'].get(str(buildings_path))==sha(buildings_path),'Field macro buildings differ')
    substrate_path=Path(os.environ['BREZI_EXTERIOR_GROVE_SUBSTRATE']).resolve() if os.environ.get('BREZI_EXTERIOR_GROVE_SUBSTRATE') else None
    substrate=read(substrate_path) if substrate_path else None
    substrate_validation=None;substrate_module=None
    if substrate:
        substrate_module=module('exterior_grove_substrate_native','exterior-grove-substrate-native.py')
        substrate_validation=substrate_module.validated_substrate(substrate,source_context,
            context['sourceSceneSha256'],context['sourceObjSha256'])
        recipe_pin=substrate['materialManifest']
        require(sha(recipe_pin['path'])==recipe_pin['sha256'],'Grove substrate material source drift')
        substrate_recipes=read(recipe_pin['path'])
        require(set(substrate_recipes)=={'canopy_floor_litter'} and
                material_manifest.get('canopy_floor_litter')==substrate_recipes['canopy_floor_litter'],
                'Grove substrate merged photographic recipe differs')
        context['meshes'].extend(substrate_validation['meshes'])
        require(len({m['id'] for m in context['meshes']})==len(context['meshes']),'Duplicate grove substrate/context mesh')
    neighborhood_path=Path(os.environ['BREZI_EXTERIOR_NEIGHBORHOOD']).resolve() if os.environ.get('BREZI_EXTERIOR_NEIGHBORHOOD') else None
    neighborhood=read(neighborhood_path) if neighborhood_path else None
    if transition:
        require(neighborhood_path and transition['sourceNeighborhood']=={'path':str(neighborhood_path),'sha256':sha(neighborhood_path)},
                'Transition requires the exact original neighborhood/removal plan')
        by_id={m['id']:m for m in context['meshes']}
        for binding in transition_validation['materialBindings']:
            mesh=by_id[binding['sourceMeshId']]
            require(mesh['material']==binding['expectedMaterialKey'] and digest(mesh)==binding['sourceGeometrySha256'],
                    'Transition original source geometry/material differs')
            mesh['material']=binding['proposedSharedMaterialKey']
    if neighborhood:
        require(neighborhood['owner']=='scripts/unreal/exterior-neighborhood.py' and neighborhood['generatorSha256']==sha(ROOT/neighborhood['owner']),'Neighborhood generator drift')
        require(neighborhood['sourceSceneSha256']==context['sourceSceneSha256'] and neighborhood['sourceObjSha256']==context['sourceObjSha256'],'Neighborhood architectural frame differs')
        require(neighborhood['activeDesign']==context['activeDesign'],'Neighborhood selection differs')
        require(neighborhood['inputFiles'].get(str(context_path))==sha(context_path),'Neighborhood context differs')
        if continuous:
            require(transition and infill,'Continuous meadow requires exact historical transition/pilot source plans')
            continuous_module=module('exterior_meadow_continuous_native','exterior-meadow-continuous-native.py')
            continuous_validation=continuous_module.validated_layout(continuous,source_context,neighborhood,transition,
                context['sourceSceneSha256'],context['sourceObjSha256'])
            require(continuous_validation['plan']=={'path':str(continuous_path),'sha256':sha(continuous_path)},
                    'Continuous source plan path differs')
            context['meshes'].extend(continuous_validation['neighborhoodMeshes'])
            for name,rows in continuous_validation['retainedContextArrays'].items():context[name]=rows
        else:context['meshes'].extend(neighborhood['meshes'])
        context.setdefault('groups',[]).extend(neighborhood.get('groups',[]))
        require(len({m['id'] for m in context['meshes']})==len(context['meshes']),'Duplicate neighborhood/context mesh')
        # The generator intersects recorded plant footprints against the ground
        # patches offline. Applying its pinned indices avoids both plant/soil
        # intersections and a GIS dependency inside the native editor.
        for name,indices in ({} if continuous else neighborhood.get('groundDetailRemovedPlacementIndices',{})).items():
            require(name in ('meadowBladePlacements','meadowUnderstoryPlacements','groundCoverPlacements'),'Unreviewed ground vegetation removal')
            rows=context.get(name,[])
            require(len(rows)==neighborhood['groundDetailPlacementSourceCounts'][name],'Ground vegetation source count differs')
            require(len(indices)==len(set(indices)) and all(isinstance(i,int) and 0<=i<len(rows) for i in indices),'Invalid ground vegetation indices')
            excluded=set(indices);context[name]=[r for i,r in enumerate(rows) if i not in excluded]
    require(not continuous or continuous_validation is not None,'Continuous meadow requires its exact original neighborhood')
    # Survey graphics remain in the pinned source plan. The default photographic
    # presentation shows the physical land; opt in to dashed parcel overlays.
    survey_overlay=os.environ.get('BREZI_EXTERIOR_SURVEY_OVERLAY','0')=='1'
    survey_meshes=[m['id'] for m in context['meshes'] if m['material']=='context_parcel_line']
    if not survey_overlay:context['meshes']=[m for m in context['meshes'] if m['id'] not in survey_meshes]
    validate_plants(manifest)
    scene = read(output/'geometry/scene.json')
    require(scene['activeDesign']=={'variant':'C','heatingLayout':'B','livingLayout':'B'},'C/B/B required')
    require(scene['house']['placement']['streetSetbackMm']==scene['house']['placement']['eastSetbackMm']==3000,'Setbacks differ')
    for key in ('DOM_01965','DOM_01966'):
        bed=next(r for r in scene['objects'] if r['id']==key)
        require(bed['sourceId'].startswith('Mulčovaný trvalkový záhon') and bed['metadata']['walkSurfaceKind']=='terrain','Garden bed reference differs')
    context['gardenPlacements']=garden_placements(output/'geometry/dom-mm.obj')
    garden_path=Path(os.environ['BREZI_EXTERIOR_GARDEN']).resolve() if os.environ.get('BREZI_EXTERIOR_GARDEN') else None
    garden=read(garden_path) if garden_path else None
    organic_garden_validation=None
    if garden:
        require(garden['sourceSceneSha256']==sha(output/'geometry/scene.json') and garden['sourceObjSha256']==sha(output/'geometry/dom-mm.obj'),'Garden source differs')
        context['ornamentalPlacements']=garden['ornamentalPlacements']
        if garden.get('gardenDetailPlacements') is not None:
            require(garden['owner'] in ('scripts/unreal/exterior-garden-drifts.py','scripts/unreal/exterior-garden-masters.py','scripts/unreal/exterior-garden-flower-masters.py',ORGANIC_GARDEN_GENERATOR) and garden['generatorSha256']==sha(ROOT/garden['owner']),'Garden detail generator drift')
            require(garden['activeDesign']==context['activeDesign'],'Garden detail design differs')
            if garden['owner']==ORGANIC_GARDEN_GENERATOR:
                organic_helper=module('exterior_garden_organic_native','exterior-garden-organic-native.py')
                organic_garden_validation=organic_helper.validated_garden(garden,original_plant_manifest,
                    context['sourceSceneSha256'],context['sourceObjSha256'])
            context['gardenPlacements']=garden['gardenDetailPlacements']
    context['views'].append({'id':'exterior-garden','label':'Záhrada · priestorová podsadba','eyeCm':[-1060.,-830.,145.],'targetCm':[-900.,-430.,35.],'horizontalFovDegrees':62.,'source':OWNER})
    diagnostic_path=Path(os.environ['BREZI_EXTERIOR_DIAGNOSTIC_VIEWS']).resolve() if os.environ.get('BREZI_EXTERIOR_DIAGNOSTIC_VIEWS') else None
    diagnostic=read(diagnostic_path) if diagnostic_path else None
    if diagnostic:
        require(diagnostic['status']=='PASS_STATIC_CAMERA_GEOMETRY_AND_PLAN_REVIEW_NATIVE_PENDING','Diagnostic camera geometry not reviewed')
        require(diagnostic['policy']['appendOnly'] is True and diagnostic['policy']['existingViewsChanged'] is False,'Diagnostic views must append')
        require(diagnostic['policy']['activeDesign']==scene['activeDesign'],'Diagnostic camera design differs')
        require(diagnostic['inputFiles'].get(str(context_path))==sha(context_path),'Diagnostic camera context differs')
        require(terrain_path and diagnostic['inputFiles'].get(str(terrain_path))==sha(terrain_path),'Diagnostic camera terrain differs')
        require(buildings_path and diagnostic['inputFiles'].get(str(buildings_path))==sha(buildings_path),'Diagnostic camera buildings differ')
        for view in diagnostic['views']:
            require(view['id'].startswith('exterior-canopy-') and 25<=view['horizontalFovDegrees']<=90,'Unreviewed diagnostic camera')
            require(all(len(view[k])==3 and all(math.isfinite(v) for v in view[k]) for k in ('eyeCm','targetCm')),'Invalid diagnostic camera coordinates')
            require(sha(ROOT/view['source'])==diagnostic['generatorSha256'],'Diagnostic camera generator drift')
        context['views'].extend(diagnostic['views'])
    ecology_views_path=Path(os.environ['BREZI_EXTERIOR_ECOLOGY_VIEWS']).resolve() if os.environ.get('BREZI_EXTERIOR_ECOLOGY_VIEWS') else None
    ecology_views=read(ecology_views_path) if ecology_views_path else None
    if ecology_views:
        require(ecology and canopy and diagnostic and terrain_path and buildings_path,'Grove floor camera requires the exact source scene and both grove plans')
        require(ecology_views['owner'] in ('scripts/unreal/exterior-canopy-ecology-views.py','scripts/unreal/exterior-canopy-growth-views.py')
                and ecology_views['generatorSha256']==sha(ROOT/ecology_views['owner'])
                and ecology_views['status']=='PASS_STATIC_ECOLOGY_CAMERA_GEOMETRY_NATIVE_PENDING','Grove floor camera generator drift')
        require(ecology_views['activeDesign']==scene['activeDesign'] and ecology_views['housePlacement']==scene['house']['placement']
                and ecology_views['sourceSceneSha256']==context['sourceSceneSha256']
                and ecology_views['sourceObjSha256']==context['sourceObjSha256'],'Grove floor camera frame differs')
        for key,path in [('sourceContext',context_path),('sourceTerrain',terrain_path),('sourceBuildings',buildings_path),
                         ('sourceEcology',ecology_path),('sourceCanopy',canopy_path),('priorDiagnosticViews',diagnostic_path)]:
            if key=='sourceCanopy' and fullness:
                # The original camera is reused at unchanged tree roots. Its
                # receipt continues to identify the original growth plan.
                path=Path(canopy['sourceOriginalGrowthPlan']['path']).resolve()
            if key=='sourceEcology' and ecology['owner']=='scripts/unreal/exterior-canopy-ecology-unflared.py' and ecology_views['owner']=='scripts/unreal/exterior-canopy-ecology-views.py':
                # The same camera remains valid after omitting decorative
                # collars; the strict helper proves every other row unchanged.
                path=Path(ecology['sourceEcology']['path']).resolve()
            require(ecology_views[key]=={'path':str(path),'sha256':sha(path)}
                    and ecology_views['inputFiles'].get(str(path))==sha(path),'Grove floor camera source drift: '+key)
        require(ecology_views['policy']['appendOnly'] is True and ecology_views['policy']['existingViewsChanged'] is False
                and ecology_views['policy']['existingTreeTransformsPreserved'] is True
                and ecology_views['policy']['nativeExecution'] is False,'Grove floor camera policy differs')
        require(len(ecology_views['views'])==1 and ecology_views['views'][0]['id']=='exterior-canopy-floor','Unreviewed grove floor camera')
        view=ecology_views['views'][0]
        require(view['source']==ecology_views['owner'] and 25<=view['horizontalFovDegrees']<=90
                and all(len(view[k])==3 and all(math.isfinite(v) for v in view[k]) for k in ('eyeCm','targetCm')),
                'Invalid grove floor camera')
        context['views'].extend(ecology_views['views'])
    old_plan = read(output/'geometry/rural-context-geometry.json'); old_report = read(output/'rural-import-report.json')
    yard_path=Path(os.environ['BREZI_EXTERIOR_YARD']).resolve() if os.environ.get('BREZI_EXTERIOR_YARD') else None
    yard=read(yard_path) if yard_path else None
    if yard:
        require(yard['owner']=='scripts/unreal/exterior-yard.py' and yard['generatorSha256']==sha(ROOT/yard['owner']),'Yard generator drift')
        require(yard['sourceSceneSha256']==context['sourceSceneSha256'] and yard['sourceObjSha256']==context['sourceObjSha256'],'Yard architectural frame differs')
        require(yard['activeDesign']==scene['activeDesign'] and yard['audit']['status']=='PASS','Yard source audit failed')
        require(yard['audit']['minimumGroundBoundaryClearanceCm']>=14 and yard['audit']['minimumProtectedClearanceCm']>=18,'Yard crown exclusions failed')
        context['yardBladePlacements']=yard['yardBladePlacements']
    natural_lawn_path=Path(os.environ['BREZI_EXTERIOR_LAWN']).resolve() if os.environ.get('BREZI_EXTERIOR_LAWN') else None
    natural_lawn=read(natural_lawn_path) if natural_lawn_path else None
    lawn_module=None; lawn_groups=[]; lawn_views=None; lawn_rural=None; lawn_rural_path=None; photo_validation=None
    if natural_lawn:
        require(natural_lawn['owner'] in NATURAL_LAWN_GENERATORS
                and natural_lawn['generatorSha256']==sha(ROOT/natural_lawn['owner']), 'Natural lawn generator drift')
        natural_manifest_path=Path(natural_lawn['geometryManifest']['path']).resolve()
        require(sha(natural_manifest_path)==natural_lawn['geometryManifest']['sha256'], 'Natural lawn geometry manifest drift')
        natural_manifest=read(natural_manifest_path)
        master={row['id']:row for row in manifest['meshes']}
        require(all(master.get(row['id'])==row for row in natural_manifest['meshes']), 'Natural lawn differs from imported master')
        lawn_module=module('exterior_lawn_native', lawn_native_filename(natural_lawn['owner']))
        if natural_lawn['owner']==PHOTO_LAWN_GENERATOR:
            require(photo_material_path is not None, 'Photographic lawn requires its validated material sidecar')
            photo_validation=lawn_module.validate_photo(natural_lawn,natural_manifest,photo_plant_manifest,
                context['sourceSceneSha256'],context['sourceObjSha256'])
            lawn_groups=photo_validation['groups']
        else:
            require(photo_material_path is None, 'Photographic material requires the matching lawn plan')
            lawn_groups=lawn_module.validated_groups(natural_lawn,natural_manifest,context['sourceSceneSha256'],context['sourceObjSha256'])
        lawn_rural=read(source/'rural-import-report.json')
        rural_plan_pins=[p for p in lawn_rural['inputFiles'] if p.endswith('/geometry/rural-context-geometry.json')]
        require(len(rural_plan_pins)==1, 'Ambiguous inherited managed lawn plan')
        lawn_rural_path=(ROOT/rural_plan_pins[0]).resolve()
        require(sha(lawn_rural_path)==lawn_rural['inputFiles'][rural_plan_pins[0]], 'Inherited managed lawn plan drift')
        lawn_views_path=Path(os.environ['BREZI_EXTERIOR_LAWN_VIEWS']).resolve() if os.environ.get('BREZI_EXTERIOR_LAWN_VIEWS') else None
        lawn_views=read(lawn_views_path) if lawn_views_path else None
        if lawn_views:
            require(lawn_views['owner'] in ('scripts/unreal/preview-lawn-natural.py', *NATURAL_LAWN_GENERATORS[1:])
                    and lawn_views['generatorSha256']==sha(ROOT/lawn_views['owner']), 'Natural lawn camera generator drift')
            expected_view_status=('PASS_PRIVATE_MANAGED_LAWN_XY_ONLY_NOT_NATIVE_ACCEPTED'
                                  if lawn_views['owner'] in COVERED_LAWN_GENERATORS or lawn_views['owner']==PHOTO_LAWN_GENERATOR
                                  else 'PASS_PRIVATE_LAWN_XY_ONLY_NOT_NATIVE_ACCEPTED')
            require(lawn_views['status']==expected_view_status
                    and lawn_views['activeDesign']==scene['activeDesign']
                    and lawn_views['sourceSceneSha256']==context['sourceSceneSha256']
                    and lawn_views['sourceObjSha256']==context['sourceObjSha256'], 'Natural lawn camera frame differs')
            require(lawn_views['plan']=={'path':str(natural_lawn_path),'sha256':sha(natural_lawn_path)}, 'Natural lawn camera plan drift')
            if lawn_views['owner'] in NATURAL_LAWN_GENERATORS[1:]:
                require(lawn_views['managedLawnPlan']==natural_lawn['managedLawnPlan'], 'Managed lawn camera mask drift')
            require(sorted(v['id'] for v in lawn_views['views'])==['exterior-lawn-detail','exterior-lawn-edge'], 'Unreviewed natural lawn cameras')
            for view in lawn_views['views']:
                require(view['source']=='scripts/unreal/preview-lawn-natural.py' and 25<=view['horizontalFovDegrees']<=90
                        and all(len(view[k])==3 and all(math.isfinite(v) for v in view[k]) for k in ('eyeCm','targetCm')), 'Invalid lawn camera')
            context['views'].extend(lawn_views['views'])
    checkpoint = output/'exterior-checkpoint'; checkpoint.mkdir()
    for name in (MAP_FILE,VIEWS_FILE): shutil.copy2(content/name,checkpoint/Path(name).name)
    dependencies = ('exterior-import.py','exterior-context.py','exterior-materials.py','rural-import.py','lawn-geometry.py','realism-import.py','realism-room-details-import.py','realism-fixtures-import.py','performance-optimize.py','performance_scene_policy.py')
    pipeline = {str(ROOT/'scripts/unreal'/name):sha(ROOT/'scripts/unreal'/name) for name in dependencies}
    if organic_garden_validation:
        garden_helper=ROOT/'scripts/unreal/exterior-garden-organic-native.py'
        pipeline[str(garden_helper)]=sha(garden_helper)
    if natural_lawn:
        lawn_helper=ROOT/'scripts/unreal'/lawn_native_filename(natural_lawn['owner'])
        pipeline[str(lawn_helper)]=sha(lawn_helper)
        if photo_validation:
            for name in ('exterior-lawn-tapered-native.py','exterior-lawn-photo-source.mjs'):
                path=ROOT/'scripts/unreal'/name;pipeline[str(path)]=sha(path)
    if canopy or ecology:pipeline[str(ROOT/'scripts/unreal/exterior-canopy-native.py')]=sha(ROOT/'scripts/unreal/exterior-canopy-native.py')
    if fullness:
        for name in ('exterior-canopy-fullness-native.py','exterior-canopy-fullness-integration.py'):
            path=ROOT/'scripts/unreal'/name;pipeline[str(path)]=sha(path)
    if substrate:pipeline[str(ROOT/'scripts/unreal/exterior-grove-substrate-native.py')]=sha(ROOT/'scripts/unreal/exterior-grove-substrate-native.py')
    if transition:pipeline[str(ROOT/'scripts/unreal/exterior-neighborhood-transition-native.py')]=sha(ROOT/'scripts/unreal/exterior-neighborhood-transition-native.py')
    if infill:
        for name in ('exterior-meadow-infill-native.py', 'exterior-meadow-infill-integration.py', 'exterior-meadow-infill-source.mjs'):
            path=ROOT/'scripts/unreal'/name;pipeline[str(path)]=sha(path)
    if continuous:
        for name in ('exterior-meadow-continuous-study.py','exterior-meadow-continuous-native.py','exterior-meadow-continuous-source.mjs'):
            path=ROOT/'scripts/unreal'/name;pipeline[str(path)]=sha(path)
    inputs = {str(p):sha(p) for p in [context_path,asset_dir/'geometry-manifest.json',asset_dir/'material-manifest.json',asset_dir/'asset-manifest.json']}
    inputs.update(manifest.get('inputFiles',{}))
    inputs.update(read(asset_dir/'asset-manifest.json').get('inputFiles',{}))
    inputs.update(context.get('inputFiles',{}))
    if infill:
        inputs[str(infill_path)] = sha(infill_path)
        inputs.update(infill_validation['inputPins'])
        for pin in (infill['infillGeometryManifest'], preserved_plant_manifest['validatedOriginal120Subset'], preserved_plant_manifest['validatedOriginal100Subset']):
            inputs[pin['path']] = pin['sha256']
    if continuous:
        inputs[str(continuous_path)]=sha(continuous_path);inputs.update(continuous_validation['inputPins'])
    if fullness:
        inputs.update(canopy_validation['inputPins'])
        subset=manifest['validatedOriginal126Subset'];inputs[subset['path']]=subset['sha256']
    if substrate:
        inputs[str(substrate_path)]=sha(substrate_path);inputs.update(substrate['inputFiles'])
    for path,plan in ((canopy_path,canopy),(ecology_path,ecology)):
        if plan:
            inputs[str(path)]=sha(path);inputs.update(plan['inputFiles'])
            inputs[plan['geometryManifest']['path']]=plan['geometryManifest']['sha256']
            directory=Path(plan['geometryManifest']['path']).parent
            material_source=directory/'material-manifest.json';inputs[str(material_source)]=sha(material_source)
    if canopy:
        proof=canopy_validation['audit']['morphologyProof']
        require(sha(proof['path'])==proof['sha256'],'Grove morphology proof drift')
        inputs[proof['path']]=proof['sha256']
    if ecology:
        ecology_bundle_path=Path(ecology['geometryManifest']['path']).parent/'canopy-ecology-manifest.json'
        inputs[str(ecology_bundle_path)]=sha(ecology_bundle_path)
        ecology_bundle=read(ecology_bundle_path)
        for key in ('plan','geometryManifest','materialManifest','geometryProof','glb'):
            pin=ecology_bundle[key];require(sha(pin['path'])==pin['sha256'],'Grove ecology source proof drift: '+key)
            inputs[pin['path']]=pin['sha256']
    for p in (snapshot,context_path.parent/'inputs/source-receipt.json'): inputs[str(p)]=sha(p)
    build_receipt=context_path.parent/'build-environment.json'
    if build_receipt.exists():
        inputs[str(build_receipt)]=sha(build_receipt)
        environment=read(build_receipt)
        inputs.update(environment.get('inputFiles',{}));inputs.update(environment.get('files',{}))
    if terrain:
        inputs[str(terrain_path)]=sha(terrain_path);inputs.update(terrain['inputFiles'])
    if ortho:
        inputs[str(ortho_path)]=sha(ortho_path);inputs.update(ortho['inputFiles'])
    if seasonal:
        inputs[str(seasonal_path)]=sha(seasonal_path);inputs.update(seasonal['inputFiles'])
        inputs[seasonal['shader']['path']]=seasonal['shader']['sha256']
        for layer in seasonal['layers']:inputs[layer['maskPath']]=layer['maskSha256']
    if field_macro:
        inputs[str(field_macro_path)]=sha(field_macro_path);inputs.update(field_macro['inputFiles'])
        inputs[field_macro['texture']['path']]=field_macro['texture']['sha256']
    if projection:
        inputs[str(projection_path)]=sha(projection_path);inputs.update(projection['inputFiles'])
        inputs[projection['texture']['path']]=projection['texture']['sha256']
    if garden:
        inputs[str(garden_path)]=sha(garden_path);inputs.update(garden['inputFiles'])
    if neighborhood:
        inputs[str(neighborhood_path)]=sha(neighborhood_path);inputs.update(neighborhood['inputFiles'])
    if transition:
        inputs[str(transition_path)]=sha(transition_path)
        inputs.update(transition_validation['audit']['inputFiles'])
        inputs[str(native_topology_path)]=sha(native_topology_path)
        inputs.update(native_topology['inputFiles'])
        inputs[native_topology['sourceNativeBaseline']['path']]=native_topology['sourceNativeBaseline']['sha256']
    if buildings:
        inputs[str(buildings_path)]=sha(buildings_path);inputs.update(buildings['inputFiles'])
    if yard:
        inputs[str(yard_path)]=sha(yard_path);inputs.update(yard['inputFiles'])
    if natural_lawn:
        inputs[str(natural_lawn_path)]=sha(natural_lawn_path);inputs.update(natural_lawn['inputFiles'])
        inputs[str(natural_manifest_path)]=sha(natural_manifest_path)
        if natural_lawn['owner'] in COVERED_LAWN_GENERATORS:
            coverage_pin=natural_lawn['coverageReceipt']
            require(sha(coverage_pin['path'])==coverage_pin['sha256'],'Physical lawn coverage receipt drift')
            inputs[coverage_pin['path']]=coverage_pin['sha256']
            coverage_bundle=natural_manifest_path.parent/'lawn-natural-manifest.json'
            inputs[str(coverage_bundle)]=sha(coverage_bundle)
            if natural_lawn['owner'] in BOUNDARY_LAWN_GENERATORS:
                boundary_pin=natural_lawn['boundaryCoverageReceipt']
                require(sha(boundary_pin['path'])==boundary_pin['sha256'],'Boundary lawn coverage receipt drift')
                inputs[boundary_pin['path']]=boundary_pin['sha256']
        inputs[str(source/'photoreal-import-report.json')]=sha(source/'photoreal-import-report.json')
        inputs[str(source/'rural-import-report.json')]=sha(source/'rural-import-report.json')
        inputs[str(lawn_rural_path)]=sha(lawn_rural_path)
        if lawn_views:
            inputs[str(lawn_views_path)]=sha(lawn_views_path)
            inputs[str(ROOT/lawn_views['owner'])]=lawn_views['generatorSha256']
            for view in lawn_views['views']:inputs[str(ROOT/view['source'])]=sha(ROOT/view['source'])
    if diagnostic:
        inputs[str(diagnostic_path)]=sha(diagnostic_path);inputs.update(diagnostic['inputFiles'])
        for view in diagnostic['views']:inputs[str(ROOT/view['source'])]=diagnostic['generatorSha256']
    if ecology_views:
        inputs[str(ecology_views_path)]=sha(ecology_views_path);inputs.update(ecology_views['inputFiles'])
        inputs[str(ROOT/ecology_views['owner'])]=ecology_views['generatorSha256']
    native_prototypes=None
    if context.get('meadowBladePlacements') or context.get('meadowUnderstoryPlacements') or context.get('yardBladePlacements'):
        lawn_report=read(source/'photoreal-import-report.json')['lawn']['geometry']
        matches=[p for p in lawn_report['inputFiles'] if p.endswith('/prototypes.json') and 'rural-context-20260923-r4' in p]
        require(len(matches)==1,'Ambiguous source native blade geometry')
        native_prototypes=ROOT/matches[0]
        inputs[str(native_prototypes)]=lawn_report['inputFiles'][matches[0]]
        inputs[str(source/'photoreal-import-report.json')]=sha(source/'photoreal-import-report.json')
    for row in manifest['meshes']: inputs[row['glbPath']] = row['glbSha256']
    for row in material_manifest.values():
        for spec in row['maps'].values(): inputs[spec['path']] = spec['sha256']
    for p, h in inputs.items(): require(sha(p)==h,'Exterior source pin differs: '+p)
    report = {'schemaVersion':1,'owner':OWNER,'status':'pending','startedAt':now(),'project':str(project),'sourceOutput':str(source),'output':str(output),
              'nativeProcessId':os.getpid(),'beforeAssetHashes':before,'pipelineFiles':pipeline,'inputFiles':inputs,'activeDesign':scene['activeDesign'],
              'setbacksMm':{'street':3000,'east':3000},'nativeRenderedVerified':False,
              'plantGeometryManifest':str(asset_dir/'geometry-manifest.json')}
    if infill:
        report['meadowInfill'] = {'plan': str(infill_path), 'planSha256': sha(infill_path),
            'geometryManifest': infill['infillGeometryManifest'], 'audit': infill_validation['audit'],
            'groupIds': [g['id'] for g in infill_validation['groups']],
            'scope': 'Additive low meadow in two bounded authored pilot sectors; original populations and surfaces retained',
            'nativeAppearanceAccepted': False, 'performanceAccepted': False}
        if continuous:
            report['meadowInfill'].update(groupsRetiredByContinuousMeadow=True,appliedGroups=0,appliedInstances=0,
                historicalSourceGroupIds=report['meadowInfill']['groupIds'],groupIds=[],
                scope='Historical pilot source validated; none of its groups or instances are placed in this continuous-layout candidate.')
    if continuous:
        report['continuousMeadow']={'plan':str(continuous_path),'planSha256':sha(continuous_path),
            'audit':continuous_validation['audit'],'restoredGroupIds':[g['id'] for g in continuous_validation['restoredGroups']],
            'retirementHistoricalSourcePlans':continuous_validation['retirementHistoricalSourcePlans'],
            'nativeRenderedVerified':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False}
    if substrate:
        report['groveSubstrate']={'plan':str(substrate_path),'planSha256':sha(substrate_path),
            'regionId':'village_nearest_grove','audit':substrate['audit'],'validation':substrate_validation['audit'],
            'sourceGroundUnchanged':True,'hiddenOriginalActors':0,
            'meshIds':[m['id'] for m in substrate_validation['meshes']]}
    if terrain:
        report['terrain']={key:terrain[key] for key in ('sourceEvidence','heightPolicy','noDataFallback','peakSample','limits','summary')}
        report['terrain']['plan']=str(terrain_path)
        report['terrain']['grid']={key:terrain['grid'][key] for key in ('width','height','validSamples','missingSamples','minimumBpvMetres','maximumBpvMetres')}
    if ortho:
        report['orthophoto']={key:ortho[key] for key in ('provider','dataset','sourceCurrencyYear','license','limits','sourcePixelEdits')}
        report['orthophoto'].update(manifest=str(ortho_path),manifestSha256=sha(ortho_path),
            scope='Colour mapping on distant visual terrain only; original house, plot and collision unchanged')
    if seasonal:
        report['seasonalFields']={'manifest':str(seasonal_path),'manifestSha256':sha(seasonal_path),
            'claim':seasonal['claim'],'attribution':seasonal['attribution'],'application':seasonal['application'],
            'sourceObservationUnchanged':True}
    if field_macro:report['fieldMacro']={'manifest':str(field_macro_path),'manifestSha256':sha(field_macro_path),
        'factorRange':field_macro['factorRange'],'allowedMaterialKeys':field_macro['allowedMaterialKeys'],
        'summary':field_macro['summary'],'limitations':field_macro['limitations']}
    report['gardenPlanting']={'sourceBedIds':['DOM_01965','DOM_01966'],'instances':len(context['gardenPlacements']),'fullCanopyWithinOriginalMulch':True,
                             'ornamentalReplacements':len(context.get('ornamentalPlacements',[])),'originalPlantAssetsPreserved':True}
    if organic_garden_validation:
        report['gardenPlanting'].update(plan=str(garden_path),planSha256=sha(garden_path),validation=organic_garden_validation)
    report['meadowBasePlanting']={'instances':len(context.get('meadowBasePlacements',[])),'cullEndCm':9000}
    if yard:report['yardPlanting']={'plan':str(yard_path),'audit':yard['audit'],'interpretation':yard['interpretation']}
    if natural_lawn:report['naturalLawn']={'plan':str(natural_lawn_path),'planSha256':sha(natural_lawn_path),
        'audit':natural_lawn['audit'],'replacementPolicy':natural_lawn['replacementPolicy'],
        'viewIds':[v['id'] for v in lawn_views['views']] if lawn_views else [],'nativeRenderedVerified':False}
    if photo_validation:report['naturalLawn']['photographicValidation']=photo_validation['audit']
    if natural_lawn and natural_lawn['owner'] in COVERED_LAWN_GENERATORS:
        report['naturalLawn']['coverageReceipt']=natural_lawn['coverageReceipt']
        if natural_lawn['owner'] in BOUNDARY_LAWN_GENERATORS:
            report['naturalLawn']['boundaryCoverageReceipt']=natural_lawn['boundaryCoverageReceipt']
    if canopy:report['canopyReplacement']={'plan':str(canopy_path),'planSha256':sha(canopy_path),
        'audit':canopy['audit'],'validation':canopy_validation['audit'],'regionId':canopy['regionId'],
        'trees':78,'deletedTrees':0,'hiddenOriginalActors':0,'nonGroveRegionalRowsPreserved':True,'nativeRenderedVerified':False}
    if ecology:report['canopyEcology']={'plan':str(ecology_path),'planSha256':sha(ecology_path),
        'audit':ecology['audit'],'validation':ecology_validation['audit'],'regionId':ecology['regionId'],
        'hiddenOriginalActors':0,'sourceGroundUnchanged':True,'nativeRenderedVerified':False}
    if diagnostic:report['diagnosticViews']={'manifest':str(diagnostic_path),'viewIds':[v['id'] for v in diagnostic['views']],
        'policy':diagnostic['policy'],'nativeRenderedVerified':False}
    if ecology_views:report['ecologyViews']={'manifest':str(ecology_views_path),'manifestSha256':sha(ecology_views_path),
        'viewIds':[v['id'] for v in ecology_views['views']],'cameraAudits':ecology_views['cameraAudits'],
        'policy':ecology_views['policy'],'nativeRenderedVerified':False}
    if buildings:
        report['village']={k:buildings[k] for k in ('sourceEvidence','limits','summary','heightPolicy') if k in buildings}
        report['village']['plan']=str(buildings_path)
    if neighborhood:report['neighborhoodDetails']={'plan':str(neighborhood_path),'summary':neighborhood['summary'],'limits':neighborhood['limits']}
    if continuous:
        report['neighborhoodDetails']['historicalSourceSummary']=report['neighborhoodDetails'].pop('summary')
        report['neighborhoodDetails']['appliedMeshCount']=continuous_validation['audit']['neighborhoodMeshes']
        report['neighborhoodDetails']['appliedSourceTriangles']=continuous_validation['audit']['neighborhoodTriangles']
    if transition:report['neighborhoodTransition']={'plan':str(transition_path),'planSha256':sha(transition_path),
        'validation':transition_validation['audit'],'sourceMaterialBindings':transition_validation['materialBindings'],
        'nativeTopologyBaseline':{'path':str(native_topology_path),'sha256':sha(native_topology_path)},
        'nativeRenderedVerified':False,'nativeVisualAccepted':False,'performanceAccepted':False}
    if continuous:report['neighborhoodTransition'].update(groupsRetiredByContinuousMeadow=True,appliedGroups=0,appliedInstances=0)
    report['surveyPresentation']={'overlayEnabled':survey_overlay,'sourceParcelGeometryUnchanged':True,'surveyMeshCount':len(survey_meshes)}
    write(output/'exterior-import-report.json',report)
    try:
        actors = u.get_editor_subsystem(u.EditorActorSubsystem); levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
        require(levels.load_level(MAP),'Cannot load exterior map'); original = helper.witness(base,u,actors)
        matmod = module('exterior_materials','exterior-materials.py')
        materials, report['materials'] = matmod.build_materials(material_manifest,prefix=PREFIX,ortho_manifest=ortho_path,
                                                               seasonal_fields_manifest=seasonal_path,field_macro_manifest=field_macro_path,
                                                               projection_manifest=projection_path,transition=transition_path,lawn_photo=photo_material_path)
        # Prepared recipes can add verified native interpretation evidence.
        # Keep that closure in the import/package inputs as well as the
        # material receipt, rejecting any contradictory identity.
        for field in ('inputFiles','pipelineFiles'):
            for path,value in report['materials'][field].items():
                require(path not in report[field] or report[field][path]==value,
                        'Conflicting exterior material dependency: '+path)
                report[field][path]=value
        pipeline_assets = pipelines(u)
        glb = output/'exterior-context.glb'; rural.write_glb(glb,context)
        inputs[str(glb)] = sha(glb)
        context_meshes = import_meshes(u,glb,{r['id']+'_LOD0':[r['material']] for r in context['meshes']},materials,pipeline_assets,'Context')
        plant_meshes = import_plants(u,manifest,materials,pipeline_assets)
        plant_paths={k:v.get_path_name() for k,v in plant_meshes.items()}
        verify_plants(u,manifest,plant_paths,materials)
        hidden = hide_original(u,actors,original,old_plan,old_report,terrain=bool(terrain),garden=context.get('ornamentalPlacements'))
        if natural_lawn:
            lawn_hidden=lawn_module.hide_original_lawn(u,actors,read(source/'photoreal-import-report.json'),lawn_rural,read(lawn_rural_path))
            hidden.extend(lawn_hidden)
            report['naturalLawn']['hiddenOriginalGroups']=lawn_hidden
            for row in lawn_hidden:
                for key in ('report','plan'):
                    pin=row['sourceRuralTrim'][key]
                    require(sha(pin['path'])==pin['sha256'], 'Inherited managed lawn witness drift')
                    inputs[pin['path']]=pin['sha256']
        material_changes=rebind_garden_soil(u,actors,old_report,materials,yard['greenSourceMeshIds'] if yard else ())
        expected = copy.deepcopy(original)
        for row in hidden:
            c = next(c for c in expected[row['actor']]['components'] if c['path']==row['component'])
            c['visible']=False; c['hiddenInGame']=True
            c['renderFlags']={flag:False for flag in helper.RENDER_FLAGS}
        for row in material_changes:
            c=next(c for c in expected[row['actor']]['components'] if c['path']==row['component'])
            require(c['materials'][row['slot']]==row['before'],'Garden soil baseline binding differs')
            c['materials'][row['slot']]=row['after']
        meadow_meshes,meadow_groups,report['nativeMeadow']=native_meadow(u,context,source,native_prototypes)
        regional=regional_groups(manifest,context)
        groups = [*plant_groups(manifest,old_plan,context),*meadow_groups,*regional,*lawn_groups,*ecology_groups,
                  *(transition_validation['groups'] if transition_validation and not continuous else []),
                  *(infill_validation['groups'] if infill_validation and not continuous else []),
                  *(continuous_validation['restoredGroups'] if continuous else [])]
        require(len({g['id'] for g in groups})==len(groups),'Duplicate exterior plant group')
        report['regionalVegetation']={'instances':sum(len(g['instances']) for g in regional),'groups':len(regional),
            'placementPolicy':'explicit audited mesh identity and uniform all-LOD crown scale',
            'source':context.get('regionalVegetationPolicy',{})}
        report['geometry'] = build_scene(u,context,groups,materials,{**context_meshes,**plant_meshes,**meadow_meshes},output)
        if canopy:
            canopy_ids={r['meshId'] for r in canopy_validation['placements']}
            canopy_groups=[g for g in regional if g['meshId'] in canopy_ids]
            require(sum(len(g['instances']) for g in canopy_groups)==78,'Native grove tree group count differs')
            report['canopyReplacement']['groupIds']=[g['id'] for g in canopy_groups]
        if ecology:report['canopyEcology']['groupIds']=[g['id'] for g in ecology_groups]
        authored = helper.witness(base,u,actors); added = sorted(authored.keys()-original.keys())
        require(all(authored[p]==expected[p] for p in expected),'Exterior altered protected architectural witness')
        views_before = read(content/VIEWS_FILE); views_after = copy.deepcopy(views_before)
        views_after['views'].extend(context.get('views',[])); require(len({r['id'] for r in views_after['views']})==len(views_after['views']),'Duplicate exterior view')
        write(content/VIEWS_FILE,views_after)
        require(levels.save_current_level(),'Cannot save exterior map'); require(u.EditorLoadingAndSavingUtils.new_blank_map(False),'Cannot unload exterior map')
        require(levels.load_level(MAP),'Cannot reload exterior map'); reloaded = helper.witness(base,u,actors)
        require(authored==reloaded,'Saved exterior witness differs'); require(all(reloaded[p]==expected[p] for p in expected),'Saved protected witness differs')
        report['savedGeometryReadback'] = readback(u,report['geometry'])
        report['savedPlantReadback'] = verify_plants(u,manifest,plant_paths,materials)
        if infill and not continuous:
            saved_groups = report['geometry']['groups']
            infill_groups = infill_validation['groups']
            require(all(g['id'] in saved_groups and saved_groups[g['id']]['instances'] == len(g['instances'])
                        for g in infill_groups), 'Saved low meadow group membership/count differs')
            report['meadowInfill']['savedGroups'] = len(infill_groups)
            report['meadowInfill']['savedInstances'] = sum(saved_groups[g['id']]['instances'] for g in infill_groups)
        if transition and not continuous:
            report['neighborhoodTransition']['savedReadback']=verify_transition_scene(u,transition_validation,source_context,
                report['geometry'],materials,plant_paths,native_topology)
        if continuous:
            report['continuousMeadow']['savedReadback']=verify_continuous_meadow_scene(u,continuous,continuous_validation,
                source_context,report['geometry'],materials,meadow_groups,plant_paths,native_topology,transition_validation)
        if substrate:
            saved_actors={a.get_path_name():a for a in actors.get_all_level_actors()}
            for mesh_id in report['groveSubstrate']['meshIds']:
                actor=saved_actors[report['geometry']['actors'][mesh_id]]
                component=actor.static_mesh_component
                require(component.get_editor_property('static_mesh').get_path_name()==report['geometry']['meshes'][mesh_id],
                        'Saved grove substrate mesh binding differs')
                require(actor.get_actor_location()==u.Vector(0,0,0) and not component.get_editor_property('cast_shadow'),
                        'Saved grove substrate origin/shadow policy differs')
            report['groveSubstrate']['savedReadback']={'status':'verified-saved-grove-substrate',
                'meshes':len(report['groveSubstrate']['meshIds']),'allNewVisualsNoCollision':True,
                'nativeMeshBindingsVerifiedAfterReload':True}
        for key,expected_groups in [('canopyReplacement',canopy_groups if canopy else []),('canopyEcology',ecology_groups)]:
            if key not in report:continue
            for group in expected_groups:
                actual=report['geometry']['groups'][group['id']]
                require(actual['instances']==len(group['instances']) and actual['mesh']==plant_paths[group['meshId']],
                        'Saved grove mesh/group membership differs')
            report[key]['savedReadback']={'status':'verified-saved-grove-groups','groups':len(expected_groups),
                'instances':sum(len(g['instances']) for g in expected_groups),'allNewVisualsNoCollision':True,
                'orderedNativeTransformsVerifiedAfterReload':True}
        if natural_lawn:report['naturalLawn']['savedReadback']=lawn_module.verify_hidden_lawn(u,actors,lawn_hidden)
        report['materialReadback'] = matmod.verify_materials(report['materials'])
        after = inventory(content); validate_changes(before,after,content)
        require(inventory(source/'Project/BreziTwin/Content')==donor_before,'Historical donor changed')
        for group in ('inputFiles','pipelineFiles'):
            for p,h in report['materials'].get(group,{}).items():
                path=str((ROOT/p).resolve()); require(sha(path)==h,'Material input drift'); report[group][path]=h
        for p,h in {**pipeline,**inputs}.items(): require(sha(p)==h,'Source drift during exterior authoring')
        report.update(status='exterior-import-validated',savedReloaded=True,protectedContentUnchanged=True,sourceGeometryCollisionAndTransformsPreserved=True,
                      originalMaterialAssetsPreserved=True,sourceRenderChanges=hidden,materialBindingChanges=material_changes,originalActorCount=len(original),finalActorCount=len(reloaded),addedActors=added,
                      protectedActorWitnessSha256=digest(expected),savedProtectedActorWitnessSha256=digest({p:reloaded[p] for p in expected}),
                      authoredActorWitnessSha256=digest(authored),savedActorWitnessSha256=digest(reloaded),
                      viewpoints={'before':views_before,'after':views_after},context={'parcelCount':len(context['parcels']),'boundarySegments':len(context['parcelBoundaries']),'sourceEvidence':context.get('sourceEvidence')},
                      afterAssetHashes=after,newAssets=sorted(after.keys()-before.keys()),
                      changedAssets=[{'path':p,'beforeSha256':before[p],'afterSha256':after[p]} for p in before if before[p]!=after[p]])
        u.log('BREZI_EXTERIOR validated')
    except Exception as error:
        report.update(status='failed',error=str(error),failedContentHashes=inventory(content)); raise
    finally:
        report['generatedAt']=now(); write(output/'exterior-import-report.json',report)


if __name__=='__main__':
    if len(sys.argv)==3 and sys.argv[1]=='--restore': restore(sys.argv[2])
    else: main()
