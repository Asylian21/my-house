"""Isolated R20 original curved-grass pilot. Only root launches native main.

Exactly64 existing retained-meadow members are replaced by3 original shapes.
No original asset/report is overwritten. Source/CPU checks are importable.
"""
from collections import Counter
import copy
import importlib.util
import math
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-curved-grass-native.py'
STUDY_OWNER = 'scripts/unreal/exterior-curved-grass-study.py'
MAP = '/Game/Brezi/Maps/Brezi'
MAP_FILE = 'Brezi/Maps/Brezi.umap'
NATIVE_STATUS = 'verified-saved-original-curved-grass-root-replacement'


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts/unreal'/filename)
    value = importlib.util.module_from_spec(spec)
    old = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try: spec.loader.exec_module(value)
    finally: sys.dont_write_bytecode = old
    return value


guard = module('r20_curved_grass_guard', 'exterior-curved-grass-guards.py')
maps = module('r20_curved_grass_maps', 'exterior-curved-grass-materials.py')
g = guard.common
require, read, write, sha, pin, check_pin, digest, now = (getattr(g, name) for name in
    ('require', 'read', 'write', 'sha', 'pin', 'check_pin', 'digest', 'now'))
PREFIX, TAG = guard.PREFIX, guard.TAG


def canonical_audit(report):
    require(report['status'] == 'exterior-import-validated' and report['savedReloaded'] is True,
            'Actual saved original R16 required')
    require(report['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}
            and report['setbacksMm'] == {'street': 3000, 'east': 3000}, 'Protected design/setbacks differ')
    plants = report['savedPlantReadback']
    require(len(plants) == 135 and sum(len(p['lodTriangles']) for p in plants) == 405
            and not any(p['id'].startswith('grass_medium_01') for p in plants), 'Original plant library differs/redundant pilot')
    require(len(report['materials']['materials']) == 42 and len(report['materials']['textures']) == 74,
            'Original material library differs')
    require(len(report['geometry']['groups']) == 1980 and report['finalActorCount'] == 5306
            and sum(r['instances'] for r in report['geometry']['groups'].values()) == 632026,
            'Original scene population differs')
    return {'originalGroups': 1980, 'originalActors': 5306, 'originalInstances': 632026,
        'affectedOriginalGroups': 4, 'removedOriginalMembers': 64, 'newGroups': 3,
        'newInstances': 64, 'netPopulationChange': 0, 'expectedSavedGroups': 1983,
        'expectedSavedActors': 5309, 'expectedSavedInstances': 632026,
        'originalPlantMasters': 135, 'originalPlantLods': 405, 'newMasters': 3, 'newPilotLods': 9,
        'newMaterials': 1, 'newTextures': 4, 'newImportPipelines': 3,
        'originalMaterialGraphs': 42, 'originalTextureObjects': 74,
        'removedOriginalNearTriangles': 16384, 'pilotTriangleCostByLod': [41104, 41104, 41104],
        'newPilotLodsIdenticalOriginalLOD0': True, 'originalProviderLodChainPresent': False,
        'managedLawnInstancesChanged': 0, 'nearGroveSourceEmptyForegroundFixed': False}


def source_inputs():
    return {'placements': guard.BASE/'exterior-placements.json',
        'prototypes': guard.BASE/'source-freeze/consumed-native-r1/workspace/output/unreal/rural-context-20260923-r4/lawn-geometry/prototypes.json',
        'camera': guard.BASE/'Project/BreziTwin/Content/Data/viewpoints.json'}


def load_selection_inputs():
    paths = source_inputs()
    placements, prototypes = read(paths['placements']), read(paths['prototypes'])
    camera = next(v for v in read(paths['camera'])['views'] if v['id'] == 'exterior-parcels')
    require(camera['eyeCm'] == [-5500, 4700, 230] and camera['targetCm'] == [1400, 1100, 90]
            and camera['horizontalFovDegrees'] == 65, 'Original PARCELS camera differs')
    return placements, prototypes, camera


def validate_plan(plan, plan_path=None):
    require(plan.get('schema') == guard.SCHEMA and plan.get('owner') == STUDY_OWNER
            and plan.get('status') == guard.STATUS, 'Unapproved original curved-grass plan')
    require(all(plan.get(k) is False for k in ('nativeExecuted', 'nativeAppearanceAccepted',
        'fullPhotorealismAccepted', 'performanceAccepted', 'shippingPackageProduced')), 'Source plan claims native acceptance')
    require(check_pin(plan['reusedBaseEvidencePlan']) == guard.EVIDENCE_PLAN
            and plan['reusedBaseEvidencePlan']['sha256'] == guard.EVIDENCE_PLAN_SHA
            and check_pin(plan['immutableGenericHelper']) == guard.SHARED
            and plan['immutableGenericHelper']['sha256'] == guard.SHARED_SHA, 'Immutable base evidence differs')
    evidence = read(guard.EVIDENCE_PLAN)
    report, content, protected = g.validate_plan(evidence, guard.EVIDENCE_PLAN)
    require(plan['baseNativeReport'] == evidence['baseNativeReport'] and plan['audit'] == canonical_audit(report),
            'Wrong original native base/pilot scope')
    require(plan['activeDesign'] == report['activeDesign'] and plan['setbacksMm'] == report['setbacksMm'],
            'Protected placement/design differs')
    require(set(plan['sourceInputs']) == set(source_inputs()), 'Source selection input closure differs')
    for key, expected in source_inputs().items(): require(check_pin(plan['sourceInputs'][key]) == expected, 'Foreign selection input')
    for key in ('originalReferenceReceipt', 'originalReferenceReview'): check_pin(plan[key])
    for row in plan['engineEvidence'].values(): check_pin(row)
    geometry = read(check_pin(plan['geometry']))
    require(geometry['owner'] == STUDY_OWNER and geometry['nativeExecuted'] is False, 'Unapproved geometry receipt')
    rows = geometry['meshes']
    guard.validate_geometry(rows, guard.original_meshes())
    guard.decode_glb(check_pin(plan['sourceGlb']), rows)
    selected = read(check_pin(plan['rootSelection']))
    placements, prototypes, camera = load_selection_inputs()
    guard.validate_selection(selected, placements, prototypes, camera, rows)
    require(plan['camera'] == camera, 'Pilot camera changed')
    recipe = read(check_pin(plan['materialRecipe']))
    maps.validate_recipe(recipe)
    tests = read(check_pin(plan['sourceGuardTests']))
    require(tests['status'] == 'passed' and tests['exitCode'] == 0 and tests['nativeExecuted'] is False,
            'Source geometry/scope guard tests did not pass')
    require(set(plan['newSourceFiles']) == {'generator', 'nativeHelper', 'geometryGuards', 'materials', 'tests', 'design'},
            'New owned source closure differs')
    for entry in plan['newSourceFiles'].values():
        live, frozen = check_pin(entry['live']), check_pin(entry['snapshot'])
        require(live != frozen and entry['live']['sha256'] == entry['snapshot']['sha256'], 'Owned source snapshot differs')
    require(check_pin(plan['newSourceFiles']['nativeHelper']['live']) == Path(__file__).resolve(), 'Foreign R20 helper')
    if plan_path:
        require(all(Path(plan[key]['path']).parent == Path(plan_path).parent for key in
            ('geometry', 'rootSelection', 'sourceGlb', 'materialRecipe', 'sourceGuardTests')), 'Study sidecar escapes selected output')
    return report, content, protected, evidence, rows, selected, recipe


def validate_asset_delta(before, after, packages):
    require(set(before) <= set(after), 'Original Content member removed')
    changed = sorted(k for k in before if before[k] != after[k])
    require(changed == [MAP_FILE], 'Another original native asset/data file changed')
    require(len(packages) == len(set(packages)) == 11 and all(p.startswith(PREFIX+'/') for p in packages),
            'Exact3mesh+1material+4texture+3pipeline packages required')
    expected = {p.removeprefix('/Game/') for p in packages}
    added = sorted(set(after) - set(before))
    require(all(Path(k).suffix in ('.uasset', '.uexp', '.ubulk') and str(Path(k).with_suffix('')) in expected
                for k in added), 'Unexpected new native package')
    require({k for k in added if k.endswith('.uasset')} == {p+'.uasset' for p in expected},
            'Exact new R20 package population differs')
    return {'changedFiles': changed, 'newFiles': added, 'removedFiles': [],
        'newUassetPackages': 11, 'protectedOriginalFilesByteIdentical': len(before)-1}


def cyclic(face): return min(tuple(face[i:]+face[:i]) for i in range(3))
def vec(value, axes='xyz'): return [float(getattr(value, axis)) for axis in axes]


def native_mesh_proof(u, mesh, row):
    expected = [cyclic([tuple(row['expectedNativeVerticesCm'][i]+row['uv0'][i])
                        for i in row['indices'][j:j+3]]) for j in range(0, len(row['indices']), 3)]
    require(mesh.get_num_lods() == 3, 'Exactly three identical pilot LODs required')
    proofs = []
    for lod in range(3):
        description = mesh.get_static_mesh_description(lod)
        require(description and mesh.get_num_triangles(lod) == row['triangles']
                and description.get_triangle_count() == row['triangles'], 'Original native triangle count differs')
        observed = []
        for index in range(row['triangles']):
            face = []
            for corner in range(3):
                vertex = description.get_triangle_vertex_instance(u.TriangleID(id_value=index), corner)
                p = vec(description.get_vertex_position(description.get_vertex_instance_vertex(vertex)))
                uv = vec(description.get_vertex_instance_uv(vertex, 0), 'xy')
                face.append(tuple(p+uv))
            observed.append(cyclic(face))
        require(observed == expected, 'Native original ordered position/UV/connectivity/winding differs: '+row['id'])
        proofs.append({'lod': lod, 'triangles': row['triangles'], 'nativeCornerSha256': digest(observed),
            'orderedPositionUVTopologyWindingExactFloat32': True})
    return {'id': row['id'], 'mesh': mesh.get_path_name(), 'lodProofs': proofs,
        'identicalOriginalLOD0AtAllThreeLevels': True, 'sourceComputedNormalTangentsExportVerified': True,
        'nativeNormalTangentReadbackAvailable': False, 'nativeMeshPackageIndependentReload': False}


def import_geometry(u, path, rows, material, importer):
    assets, actors = u.EditorAssetLibrary, u.get_editor_subsystem(u.EditorActorSubsystem)
    levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    pipelines = []
    for original, name in (('GLTFSceneAssets', 'Assets'), ('GLTFMaterials', 'Materials'), ('LevelActors', 'Level')):
        target = PREFIX+'/Pipeline/'+name
        require(not assets.does_asset_exist(target), 'Fresh own R20 pipeline required')
        pipeline = assets.duplicate_asset('/Game/Brezi/Pipeline/'+original, target)
        require(pipeline, 'Cannot duplicate original importer pipeline')
        pipelines.append(pipeline)
    mp = pipelines[0].get_editor_property('mesh_pipeline')
    for key, value in {'combine_static_meshes_behavior': u.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE,
            'collision': False, 'build_nanite': False, 'generate_lightmap_u_vs': False}.items(): mp.set_editor_property(key, value)
    common = pipelines[0].get_editor_property('common_meshes_properties')
    for key, value in {'remove_degenerates': False, 'recompute_normals': False,
            'recompute_tangents': False, 'use_full_precision_u_vs': True}.items(): common.set_editor_property(key, value)
    # GLTFMaterials is a wrapper; these exposed properties belong to the
    # generic assets pipeline's nested MaterialPipeline/TexturePipeline.
    material_pipeline = pipelines[0].get_editor_property('material_pipeline')
    material_pipeline.set_editor_property('import_materials', False)
    material_pipeline.get_editor_property('texture_pipeline').set_editor_property('import_textures', False)
    pipelines[2].set_editor_property('scene_hierarchy_type', u.InterchangeSceneHierarchyType.CREATE_LEVEL_ACTORS)
    params = u.ImportAssetParameters()
    for key, value in {'is_automated': True, 'replace_existing': False, 'force_show_dialog': False,
            'override_pipelines': [u.SoftObjectPath(p.get_path_name()) for p in pipelines],
            'import_level': levels.get_current_level()}.items(): params.set_editor_property(key, value)
    before = {a.get_path_name() for a in actors.get_all_level_actors()}
    manager = u.InterchangeManager.get_interchange_manager_scripted()
    require(manager.import_scene(PREFIX+'/Geometry', manager.create_source_data(str(path)), params), 'Original grass GLB import failed')
    expected = {r['id']+'_LOD0': r for r in rows}
    meshes, temporary = {}, []
    subsystem = importer.mesh_helper.static_mesh_subsystem(u)
    for actor in actors.get_all_level_actors():
        if actor.get_path_name() in before: continue
        temporary.append(actor)
        for component in actor.get_components_by_class(u.StaticMeshComponent):
            mesh = component.get_editor_property('static_mesh')
            require(mesh and mesh.get_path_name().startswith(PREFIX+'/'), 'Foreign original-grass importer asset')
            names = [name for name in expected if mesh.get_name() == name or mesh.get_name().endswith('_'+name)
                     or actor.get_actor_label() == name]
            require(len(names) == 1 and expected[names[0]]['id'] not in meshes, 'Ambiguous original-grass imported master')
            row, name = expected[names[0]], names[0]
            canonical = PREFIX+'/Geometry/StaticMeshes/'+name
            if mesh.get_path_name().split('.')[0] != canonical:
                require(assets.rename_asset(mesh.get_path_name().split('.')[0], canonical), 'Cannot canonicalize own mesh package')
                mesh = assets.load_asset(canonical)
            mesh.set_material(0, material)
            mesh.set_editor_property('has_navigation_data', False)
            for lod in (1, 2):
                require(subsystem.set_lod_from_static_mesh(mesh, lod, mesh, 0, True) == lod,
                        'Cannot copy original full geometry into bounded pilot LOD')
            for lod in range(3):
                settings = subsystem.get_lod_build_settings(mesh, lod)
                for key, value in {'use_full_precision_u_vs': True, 'generate_lightmap_u_vs': False,
                        'recompute_normals': False, 'recompute_tangents': False, 'remove_degenerates': False}.items():
                    settings.set_editor_property(key, value)
                subsystem.set_lod_build_settings(mesh, lod, settings)
            require(subsystem.set_lod_screen_sizes(mesh, [1., .025, .007]), 'Cannot retain original meadow LOD thresholds')
            assets.set_metadata_tag(mesh, 'BreziGeneratedBy', OWNER)
            assets.set_metadata_tag(mesh, 'BreziR20OriginalMeshIdentity', row['id'])
            require(assets.save_loaded_asset(mesh, only_if_is_dirty=False), 'Cannot save original curved-grass master')
            meshes[row['id']] = mesh
    require(set(meshes) == {r['id'] for r in rows}, 'Exactly three original masters required')
    importer.mesh_helper.finish_static_mesh_compilation(u, synchronous=True)
    for row in rows: native_mesh_proof(u, meshes[row['id']], row)
    for actor in reversed(temporary): require(actors.destroy_actor(actor), 'Cannot remove owned temporary import actor')
    for pipeline in pipelines: require(assets.save_loaded_asset(pipeline, only_if_is_dirty=False), 'Cannot save own R20 pipeline')
    expected_paths = {m.get_path_name().split('.')[0] for m in meshes.values()}
    removed = []
    for path in assets.list_assets(PREFIX+'/Geometry', recursive=True, include_folder=False):
        value = assets.load_asset(path)
        require(value, 'Missing own imported asset')
        if value.get_path_name().split('.')[0] in expected_paths: continue
        require(value.get_class().get_name() in ('InterchangeSceneImportAsset', 'ObjectRedirector'),
                'Unexpected own import artifact class')
        removed.append(value.get_path_name())
        require(assets.delete_asset(path), 'Cannot remove own transient import artifact')
    return meshes, [p.get_path_name() for p in pipelines], removed


def capture_original_instances(u, report, selected):
    actors = {a.get_path_name(): a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
    groups, values, chosen, components = report['geometry']['groups'], {}, {}, {}
    identity = [[0., 0., 0.], [0., 0., 0., 1.], [1., 1., 1.]]
    for group_id in sorted({r['groupId'] for r in selected}):
        source = groups[group_id]
        actor = actors[source['actor']]
        component = actor.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
        require(component and component.get_instance_count() == source['instances']
                and component.get_editor_property('static_mesh').get_path_name() == source['mesh'], 'Original target binding differs')
        require(report['geometry']['groups'][group_id]['qualityDetail'] is True
                and [component.get_editor_property(k) for k in ('instance_start_cull_distance', 'instance_end_cull_distance')]
                == [7200, 9000], 'Original target detail/culls differ')
        require([vec(actor.get_actor_transform().translation), vec(actor.get_actor_transform().rotation, 'xyzw'),
                 vec(actor.get_actor_transform().scale3d)] == identity
                and [vec(component.get_world_transform().translation), vec(component.get_world_transform().rotation, 'xyzw'),
                     vec(component.get_world_transform().scale3d)] == identity, 'Original group frame is not identity')
        values[group_id] = [guard.native_instance_value(component, i) for i in range(component.get_instance_count())]
        require(digest(values[group_id]) == source['transformsSha256'], 'Native original ordered member values differ')
        components[group_id] = component
        for row in (r for r in selected if r['groupId'] == group_id):
            value = component.get_instance_transform(row['instanceIndex'], False)
            if isinstance(value, tuple): require(value[0] is True, 'Cannot capture selected root'); value = value[1]
            chosen[(group_id, row['instanceIndex'])] = value
    require(len(chosen) == 64, 'Exactly64 actual original native root frames required')
    return values, chosen, components


def expected_new_actor(before_template, actor_path, group_id, mesh_path, material_path, values):
    result = copy.deepcopy(before_template)
    require(len(result['components']) == 1 and result['class'] == '/Script/BreziTwin.BreziVegetationPatch'
            and result['detailDensityScaling'] is True, 'Original meadow actor template differs')
    result['label'], result['tags'] = group_id, [TAG, 'BreziLawnDetail']
    c = result['components'][0]
    c.update(mesh=mesh_path, materials=[material_path], instanceCount=len(values), overrideMaterials=[],
             path=actor_path+'.'+c['name'], orderedInstanceTransformsSha256=digest(values))
    return result


def verify_new_root_values(row, original_value, actual, mesh):
    require(actual[0] == original_value[0], 'Actual native root XYZ changed')
    # FMatrix->FTransform decomposes a double-precision scaled rotation.
    # The authored input rotation is copied exactly; this bounded readback
    # comparison permits only double arithmetic roundoff, never changed yaw.
    require(min(max(abs(a-b) for a, b in zip(actual[1], original_value[1])),
                max(abs(a+b) for a, b in zip(actual[1], original_value[1]))) <= 1e-12,
            'Actual native yaw/rotation changed beyond double-matrix decomposition roundoff')
    require(max(abs(s-row['uniformScale']) for s in actual[2]) <= 1e-12, 'Actual native uniform height fit differs')
    radius = max(math.hypot(p[0]*actual[2][0], p[1]*actual[2][1]) for p in mesh['expectedNativeVerticesCm'])
    require(radius <= 14. and abs(mesh['rootedHeightCm']*actual[2][2]-row['authoredHeightCm']) <= 1e-9,
            'Actual decoded full-vertex crown/height exceeds original fit')
    return {'groupId': row['groupId'], 'originalIndex': row['instanceIndex'], 'newMasterId': row['newMasterId'],
        'originalNativeValue': original_value, 'savedNativeValue': actual,
        'nativeRootXYZExact': True, 'nativeInputRotationCopiedExactly': True,
        'decodedQuaternionMaximumComponentRoundoff': min(max(abs(a-b) for a,b in zip(actual[1], original_value[1])),
                                                       max(abs(a+b) for a,b in zip(actual[1], original_value[1]))),
        'decodedAllVertexRadiusCm': radius, 'authoredHeightCm': row['authoredHeightCm']}


def apply_scene(u, report, selected, rows, meshes, material, components, chosen, before, values, importer):
    expected, changes = guard.expected_original_witness(before, selected, values, report['geometry']['groups'])
    for change in changes:
        component = components[change['groupId']]
        require(component.remove_instances(sorted(change['removedOriginalIndices'], reverse=True)), 'Cannot remove exact original64members')
        actual = [guard.native_instance_value(component, i) for i in range(component.get_instance_count())]
        require(actual == [values[change['groupId']][i] for i in change['retainedOriginalIndicesInNativeOrder']],
                'Native RemoveAtSwap moved/changed another original member')
        component.get_owner().synchronize_instance_bounds()
    new_groups, root_proofs = {}, []
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    template = before[report['geometry']['groups']['EX_meadow_-3_2_LawnTuft0']['actor']]
    by_id = {r['id']: r for r in rows}
    for kind in guard.MASTERS:
        members = [r for r in selected if r['kind'] == kind]
        row = by_id[members[0]['newMasterId']]
        group_id = 'EX_curved_grass_r20_'+kind
        actor = actors.spawn_actor_from_class(u.load_class(None, '/Script/BreziTwin.BreziVegetationPatch'), u.Vector(0,0,0), u.Rotator())
        require(actor, 'Cannot spawn own bounded grass group')
        actor.set_actor_label(group_id); actor.set_folder_path('Brezi/CurvedGrass20261001R20')
        actor.set_editor_property('tags', [u.Name(TAG), u.Name('BreziLawnDetail')]); actor.set_actor_tick_enabled(False)
        component = actor.get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
        require(component.set_static_mesh(meshes[row['id']]), 'Cannot bind original curved master')
        importer.rural.new_component_policy(u, component)
        component.set_cull_distances(7200, 9000)
        component.set_editor_property('cast_shadow', False); component.set_editor_property('visible_in_ray_tracing', False)
        require(actor.set_detail_density_scaling(True), 'Cannot preserve original meadow quality scaling')
        transforms = []
        for member in members:
            original = chosen[(member['groupId'], member['instanceIndex'])]
            transform = u.Transform()
            transform.set_editor_property('translation', original.translation)
            transform.set_editor_property('rotation', original.rotation)
            transform.set_editor_property('scale3d', u.Vector(*([member['uniformScale']]*3)))
            transforms.append(transform)
        require(list(component.add_instances(transforms, True, False, False)) == list(range(len(members))),
                'Bounded new group member order differs')
        actor.synchronize_instance_bounds()
        actual = [guard.native_instance_value(component, i) for i in range(len(members))]
        for member, value in zip(members, actual):
            root_proofs.append(verify_new_root_values(member, values[member['groupId']][member['instanceIndex']], value, row))
        expected[actor.get_path_name()] = expected_new_actor(template, actor.get_path_name(), group_id,
            meshes[row['id']].get_path_name(), material.get_path_name(), actual)
        new_groups[group_id] = {'actor': actor.get_path_name(), 'mesh': meshes[row['id']].get_path_name(),
            'instances': len(members), 'cullStartCm': 7200, 'cullEndCm': 9000,
            'qualityDetail': True, 'transformsSha256': digest(actual), 'masterId': row['id']}
    require(len(expected) == 5309 and len(root_proofs) == 64, 'Pilot expected actor/population differs')
    return expected, changes, new_groups, root_proofs


def geometry_after(report, changes, new_groups, meshes):
    geometry = copy.deepcopy(report['geometry'])
    for change in changes:
        row = geometry['groups'][change['groupId']]
        row['instances'], row['transformsSha256'] = change['retainedInstances'], change['retainedTransformsSha256']
    geometry['groups'].update({k: {field: value for field, value in row.items() if field != 'masterId'} for k,row in new_groups.items()})
    geometry['meshes'].update({key: mesh.get_path_name() for key, mesh in meshes.items()})
    return geometry


def main():
    import unreal as u
    plan_path = Path(os.environ['BREZI_CURVED_GRASS_PLAN']).resolve()
    plan_hash = os.environ['BREZI_CURVED_GRASS_PLAN_SHA256']
    require(sha(plan_path) == plan_hash, 'Selected original grass plan changed')
    plan = read(plan_path)
    report, content_before, protected_before, evidence, rows, selected, recipe = validate_plan(plan, plan_path)
    output = Path(os.environ['BREZI_CURVED_GRASS_OUTPUT']).resolve()
    require(output.is_relative_to(ROOT/'output/unreal') and output.name.startswith('exterior-20261002-r20')
            and output != guard.BASE and not output.is_relative_to(guard.BASE), 'Only a new isolated R20 clone may change')
    project = output/'Project/BreziTwin'
    require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve() == project, 'Wrong native project')
    require(Path(u.Paths.engine_dir()).resolve() == Path(evidence['engineEvidence']['editorModules']['path']).parents[2],
            'Wrong native engine')
    require(not (output/'exterior-import-report.json').exists(), 'Do not copy/spoof original exterior report')
    receipt = output/'curved-grass-native-report.json'
    require(not receipt.exists(), 'Previous native receipts are immutable')
    for original in (guard.BASE/'Project/BreziTwin', project):
        require(g.inventory(original/'Content') == content_before and g.project_proof(original) == protected_before,
                'Original donor/fresh independent clone bytes differ')
    for directory, inventory in (('Content', content_before), ('', protected_before)):
        for relative in inventory:
            source, own = guard.BASE/'Project/BreziTwin'/directory/relative, project/directory/relative
            require((source.stat().st_dev, source.stat().st_ino) != (own.stat().st_dev, own.stat().st_ino), 'Donor hardlink forbidden')
    importer, old_materials = g.frozen_modules(evidence)
    state = {'schema': guard.SCHEMA, 'owner': OWNER, 'status': 'running', 'startedAt': now(),
        'nativeProcessId': os.getpid(), 'output': str(output), 'project': str(project),
        'baseNativeReport': plan['baseNativeReport'], 'selectedPlan': pin(plan_path),
        'baseContentInventory': evidence['baseContentInventory'], 'baseProjectProof': evidence['baseProjectProof'],
        'reusedBaseEvidencePlan': plan['reusedBaseEvidencePlan'], 'immutableGenericHelper': plan['immutableGenericHelper'],
        'nativeEngineBuildId': evidence['nativeEngineBuildId'], 'engineEvidence': plan['engineEvidence'],
        'nativeModuleWitness': {'source': evidence['nativeModule']['path'],
            'destination': str(project/Path(evidence['nativeModule']['path']).relative_to(guard.BASE/'Project/BreziTwin')),
            'sha256': evidence['nativeModule']['sha256'], 'bytes': evidence['nativeModule']['bytes'], 'independentInodes': True},
        'scope': '64 retained meadow root replacements;3 original grass masters;one original-map masked material.',
        'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False,
        'performanceAccepted': False, 'shippingPackageProduced': False}
    write(receipt, state)
    try:
        levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
        require(levels.load_level(MAP), 'Cannot load own original R16 map')
        state['baseGeometryReadback'] = importer.readback(u, report['geometry'])
        before = g.native_witness(u, importer)
        require(len(before) == 5306, 'Original full actor population differs')
        values, chosen, components = capture_original_instances(u, report, selected)
        original_maps = g.original_material_readback(u, old_materials, report)
        write(output/'curved-grass-witness-before.json', before)
        write(output/'curved-grass-original-members-before.json', values)
        write(output/'curved-grass-original-materials-before.json', original_maps)
        material, material_report = maps.build_materials(u, recipe, old_materials.graph_snapshot)
        meshes, pipelines, removed = import_geometry(u, check_pin(plan['sourceGlb']), rows, material, importer)
        expected, changes, new_groups, roots = apply_scene(u, report, selected, rows, meshes, material,
            components, chosen, before, values, importer)
        require(g.native_witness(u, importer) == expected, 'Native pilot changed another scene field')
        require(levels.save_current_level(), 'Cannot save own curved-grass pilot map')
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False), 'Cannot unload pilot map')
        require(levels.load_level(MAP), 'Cannot reload serialized pilot map')
        maps.verify_materials(u, material_report, old_materials.graph_snapshot)
        importer.mesh_helper.finish_static_mesh_compilation(u, synchronous=True)
        proofs = [native_mesh_proof(u, u.EditorAssetLibrary.load_asset(meshes[r['id']].get_path_name()), r) for r in rows]
        subsystem = importer.mesh_helper.static_mesh_subsystem(u)
        for row in rows:
            mesh = meshes[row['id']]
            require(mesh.get_material(0) == material and mesh.get_num_sections(0) == 1
                    and not mesh.get_editor_property('has_navigation_data')
                    and not mesh.get_editor_property('nanite_settings').get_editor_property('enabled'),
                    'Saved original-grass material/nav/Nanite scope changed')
            require(list(subsystem.get_lod_screen_sizes(mesh)) == [1., guard.f32(.025), guard.f32(.007)],
                    'Saved original meadow LOD thresholds differ')
            for lod in range(3):
                settings = subsystem.get_lod_build_settings(mesh, lod)
                require(settings.get_editor_property('use_full_precision_u_vs') and not any(settings.get_editor_property(k)
                    for k in ('generate_lightmap_u_vs','recompute_normals','recompute_tangents','remove_degenerates')),
                    'Saved original normal/tangent/UV/build preservation policy differs')
        geometry = geometry_after(report, changes, new_groups, meshes)
        state['savedGeometryReadback'] = importer.readback(u, geometry)
        after = g.native_witness(u, importer)
        require(after == expected, 'Saved complete actor witness changed beyond exact root replacements')
        require(g.original_material_readback(u, old_materials, report) == original_maps, 'Original42graphs/74textures changed')
        content_after = g.inventory(project/'Content')
        packages = [m.get_path_name().split('.')[0] for m in meshes.values()] + [material.get_path_name().split('.')[0]] \
                   + [r['asset'].split('.')[0] for r in material_report['textures'].values()] + [p.split('.')[0] for p in pipelines]
        state['assetDelta'] = validate_asset_delta(content_before, content_after, packages)
        require(g.project_proof(project) == protected_before, 'Original Config/Source/Binaries/descriptor changed')
        require(g.inventory(guard.BASE/'Project/BreziTwin/Content') == content_before
                and g.project_proof(guard.BASE/'Project/BreziTwin') == protected_before, 'Original R16 donor changed')
        require(sha(plan_path) == plan_hash, 'Selected source plan changed during native execution')
        for entry in plan['newSourceFiles'].values(): check_pin(entry['live']); check_pin(entry['snapshot'])
        write(output/'curved-grass-witness-after.json', after)
        write(output/'curved-grass-content-after.json', content_after)
        write(output/'curved-grass-geometry-after.json', geometry)
        state.update(status=NATIVE_STATUS, savedMapUnloadedReloaded=True, originalR16Unchanged=True,
            originalContentExceptMapByteIdentical=True, actualAudit=plan['audit'], originalMemberChanges=changes,
            newGroups=new_groups, newMasterProofs=proofs, sourceRootPlacementReadback=roots,
            materialReport=material_report, importPipelines=pipelines, removedOwnTransientImportArtifacts=removed,
            nativeMaterialPackagesIndependentlyReloaded=False, nativeMeshPackagesIndependentlyReloaded=False,
            nearSourceEmptyForegroundFixed=False, beforeActorWitnessSha256=digest(before),
            expectedActorWitnessSha256=digest(expected), savedActorWitnessSha256=digest(after),
            originalMaterialsWitnessSha256=digest(original_maps),
            afterContentInventory=pin(output/'curved-grass-content-after.json'),
            witnessBefore=pin(output/'curved-grass-witness-before.json'),
            witnessAfter=pin(output/'curved-grass-witness-after.json'),
            originalMembersBefore=pin(output/'curved-grass-original-members-before.json'),
            originalMaterialsBefore=pin(output/'curved-grass-original-materials-before.json'),
            effectiveGeometry=pin(output/'curved-grass-geometry-after.json'),
            newSourceFiles=plan['newSourceFiles'], frozenPipeline=evidence['frozenPipeline'],
            consumedSourceSnapshot=evidence['consumedSourceSnapshot'], generatedAt=now())
        write(receipt, state)
        print(__import__('json').dumps({'status': NATIVE_STATUS, 'receipt': pin(receipt),
            'audit': state['actualAudit'], 'nativeAppearanceAccepted': False, 'performanceAccepted': False}))
    except Exception as error:
        state.update(status='failed', error=str(error), generatedAt=now())
        write(receipt, state)
        raise


if __name__ == '__main__': main()
