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


def validate_plants(manifest):
    require(manifest['meshes'], 'No plant meshes')
    ids = set()
    for row in manifest['meshes']:
        require(row['id'] not in ids and row['role'] in ('tree','shrub','vine','groundcover','grass','nettle','forb','ornamental'), 'Duplicate or invalid plant role')
        ids.add(row['id'])
        require(sha(row['glbPath']) == row['glbSha256'], 'Plant GLB differs')
        require(len(row['lods']) == 3 and row['materialKeys'] and row['heightCm'] > 0, 'Missing plant LOD/material/height')
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
            require(subsystem.set_lod_screen_sizes(mesh,[1.,.32,.10] if row['role']=='tree' else [1.,.15,.04]),'Plant LOD screens failed')
            require(u.EditorAssetLibrary.save_loaded_asset(mesh,False),'Plant mesh save failed'); result[row['id']] = mesh
    return result


def verify_plants(u, manifest, paths, materials):
    mesh_helper.finish_static_mesh_compilation(u,synchronous=True)
    subsystem=mesh_helper.static_mesh_subsystem(u); rows=[]
    for row in manifest['meshes']:
        mesh=u.EditorAssetLibrary.load_asset(paths[row['id']]); require(mesh,'Saved plant mesh missing')
        screens=list(subsystem.get_lod_screen_sizes(mesh)); target=[1.,.32,.10] if row['role']=='tree' else [1.,.15,.04]
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
        if role=='shrub' and variants['vine'] and rng.random()<.75: options=variants['vine']
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
        put(row['role'],row['positionCm'],row['heightCm'],row['yawDeg'],1.,12000,row['radiusCm'])
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
    require(context['owner'] in ('scripts/unreal/exterior-context.py','scripts/unreal/exterior-meadow.py','scripts/unreal/exterior-meadow-blades.py','scripts/unreal/exterior-regional-vegetation.py'),'Unreviewed exterior context generator')
    require(context['generatorSha256']==sha(ROOT/context['owner']),'Context generator drift')
    require(context['sourceSceneSha256']==sha(output/'geometry/scene.json') and context['sourceObjSha256']==sha(output/'geometry/dom-mm.obj'),'Context architectural source differs')
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
    if garden:
        require(garden['sourceSceneSha256']==sha(output/'geometry/scene.json') and garden['sourceObjSha256']==sha(output/'geometry/dom-mm.obj'),'Garden source differs')
        context['ornamentalPlacements']=garden['ornamentalPlacements']
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
    old_plan = read(output/'geometry/rural-context-geometry.json'); old_report = read(output/'rural-import-report.json')
    yard_path=Path(os.environ['BREZI_EXTERIOR_YARD']).resolve() if os.environ.get('BREZI_EXTERIOR_YARD') else None
    yard=read(yard_path) if yard_path else None
    if yard:
        require(yard['owner']=='scripts/unreal/exterior-yard.py' and yard['generatorSha256']==sha(ROOT/yard['owner']),'Yard generator drift')
        require(yard['sourceSceneSha256']==context['sourceSceneSha256'] and yard['sourceObjSha256']==context['sourceObjSha256'],'Yard architectural frame differs')
        require(yard['activeDesign']==scene['activeDesign'] and yard['audit']['status']=='PASS','Yard source audit failed')
        require(yard['audit']['minimumGroundBoundaryClearanceCm']>=14 and yard['audit']['minimumProtectedClearanceCm']>=18,'Yard crown exclusions failed')
        context['yardBladePlacements']=yard['yardBladePlacements']
    checkpoint = output/'exterior-checkpoint'; checkpoint.mkdir()
    for name in (MAP_FILE,VIEWS_FILE): shutil.copy2(content/name,checkpoint/Path(name).name)
    dependencies = ('exterior-import.py','exterior-context.py','exterior-materials.py','rural-import.py','lawn-geometry.py','realism-import.py','realism-room-details-import.py','realism-fixtures-import.py','performance-optimize.py','performance_scene_policy.py')
    pipeline = {str(ROOT/'scripts/unreal'/name):sha(ROOT/'scripts/unreal'/name) for name in dependencies}
    inputs = {str(p):sha(p) for p in [context_path,asset_dir/'geometry-manifest.json',asset_dir/'material-manifest.json',asset_dir/'asset-manifest.json']}
    inputs.update(manifest.get('inputFiles',{}))
    inputs.update(read(asset_dir/'asset-manifest.json').get('inputFiles',{}))
    inputs.update(context.get('inputFiles',{}))
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
    if garden:
        inputs[str(garden_path)]=sha(garden_path);inputs.update(garden['inputFiles'])
    if buildings:
        inputs[str(buildings_path)]=sha(buildings_path);inputs.update(buildings['inputFiles'])
    if yard:
        inputs[str(yard_path)]=sha(yard_path);inputs.update(yard['inputFiles'])
    if diagnostic:
        inputs[str(diagnostic_path)]=sha(diagnostic_path);inputs.update(diagnostic['inputFiles'])
        for view in diagnostic['views']:inputs[str(ROOT/view['source'])]=diagnostic['generatorSha256']
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
    report['meadowBasePlanting']={'instances':len(context.get('meadowBasePlacements',[])),'cullEndCm':9000}
    if yard:report['yardPlanting']={'plan':str(yard_path),'audit':yard['audit'],'interpretation':yard['interpretation']}
    if diagnostic:report['diagnosticViews']={'manifest':str(diagnostic_path),'viewIds':[v['id'] for v in diagnostic['views']],
        'policy':diagnostic['policy'],'nativeRenderedVerified':False}
    if buildings:
        report['village']={k:buildings[k] for k in ('sourceEvidence','limits','summary','heightPolicy') if k in buildings}
        report['village']['plan']=str(buildings_path)
    write(output/'exterior-import-report.json',report)
    try:
        actors = u.get_editor_subsystem(u.EditorActorSubsystem); levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
        require(levels.load_level(MAP),'Cannot load exterior map'); original = helper.witness(base,u,actors)
        matmod = module('exterior_materials','exterior-materials.py')
        materials, report['materials'] = matmod.build_materials(material_manifest,prefix=PREFIX,ortho_manifest=ortho_path,
                                                               seasonal_fields_manifest=seasonal_path,field_macro_manifest=field_macro_path)
        pipeline_assets = pipelines(u)
        glb = output/'exterior-context.glb'; rural.write_glb(glb,context)
        inputs[str(glb)] = sha(glb)
        context_meshes = import_meshes(u,glb,{r['id']+'_LOD0':[r['material']] for r in context['meshes']},materials,pipeline_assets,'Context')
        plant_meshes = import_plants(u,manifest,materials,pipeline_assets)
        plant_paths={k:v.get_path_name() for k,v in plant_meshes.items()}
        verify_plants(u,manifest,plant_paths,materials)
        hidden = hide_original(u,actors,original,old_plan,old_report,terrain=bool(terrain),garden=context.get('ornamentalPlacements'))
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
        groups = [*plant_groups(manifest,old_plan,context),*meadow_groups,*regional]
        report['regionalVegetation']={'instances':sum(len(g['instances']) for g in regional),'groups':len(regional),
            'placementPolicy':'explicit audited mesh identity and uniform all-LOD crown scale',
            'source':context.get('regionalVegetationPolicy',{})}
        report['geometry'] = build_scene(u,context,groups,materials,{**context_meshes,**plant_meshes,**meadow_meshes},output)
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
