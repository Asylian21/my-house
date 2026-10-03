"""UNFROZEN R25 draft. Root alone launches native, after actual saved R22 exists.

One original garden HISM member is rebound to one original Fern02 shape. All
original actor fields except that mesh/material/ordered scale hash survive.
No scene population, layout, camera, collision, source pixel or old asset edit.
"""
import argparse
import copy
from datetime import datetime, timezone
import os
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-fern-native-r25.py'
spec = __import__('importlib.util', fromlist=['spec_from_file_location'])
s = spec.spec_from_file_location('r25_fern_guard', ROOT/'scripts/unreal/exterior-garden-fern-guards-r25.py')
guard = spec.module_from_spec(s)
s.loader.exec_module(guard)
require, sha, pin, read, write, digest = (getattr(guard, k) for k in ('require', 'sha', 'pin', 'read', 'write', 'digest'))
PREFIX = guard.PREFIX
MAP = '/Game/Brezi/Maps/Brezi'
REPORT = 'garden-fern-native-report.json'
STATUS = 'verified-saved-original-fern-single-own-garden-root'
MODULE_SHA = '2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574'


def now():
    return datetime.now(timezone.utc).isoformat()


def vec(value, axes='xyz'):
    return [float(getattr(value, key)) for key in axes]


def transform_value(value):
    if isinstance(value, tuple) and len(value) == 2 and value[0] is True:
        value = value[1]
    require(value is not None and hasattr(value, 'translation'), 'Native instance Transform unavailable')
    return [vec(value.translation), vec(value.rotation, 'xyzw'), vec(value.scale3d)]


def stored_matrix(component):
    data = component.get_editor_property('per_instance_sm_data')
    require(len(data) == 1, 'Exactly one native stored member required')
    matrix = data[0].get_editor_property('transform')
    return [[float(getattr(getattr(matrix, plane), axis)) for axis in 'xyzw']
            for plane in ('x_plane', 'y_plane', 'z_plane', 'w_plane')]


def numeric_exact(actual, expected, message):
    def encode(value):
        if isinstance(value, (list, tuple)):
            return b''.join(encode(v) for v in value)
        require(type(value) in (int, float), 'Invalid binary64 numeric control')
        return struct.pack('<d', value)
    require(encode(actual) == encode(expected), message)


def transient_scale_measurement(u, component, proposal):
    """Same wrapped native rotation/XYZ, one source scale; actual storage, no model."""
    original = component.get_instance_transform(0, False)
    if isinstance(original, tuple):
        require(original[0] is True, 'Original single-root Transform unreadable')
        original = original[1]
    before = transform_value(original)
    desired = u.Transform()
    desired.set_editor_property('translation', original.translation)
    desired.set_editor_property('rotation', original.rotation)
    desired.set_editor_property('scale3d', u.Vector(*proposal['scale']))
    numeric_exact(transform_value(desired), [before[0], before[1], proposal['scale']],
                  'Original wrapped XYZ/rotation or requested uniform scale changed before insertion')
    transient = u.new_object(u.HierarchicalInstancedStaticMeshComponent)
    require(transient and transient.get_path_name().startswith('/Engine/Transient.')
            and transient.get_editor_property('static_mesh') is None, 'Unowned no-mesh transient HISM required')
    require(transient.add_instance(desired, False) == 0, 'Cannot measure single native scale serialization')
    measurement = {'originalValue': before, 'preInsertionValue': transform_value(desired),
                   'recoveredValue': transform_value(transient.get_instance_transform(0, False)),
                   'storedMatrix': stored_matrix(transient), 'actualNativeTransientMeasurement': True,
                   'nativeQuaternionReconstructedFromHostFloats': False,
                   'originalWrappedTranslationAndRotationCopiedDirectly': True,
                   'transientComponentOwnedBySceneActor': False}
    transient.clear_instances()
    require(transient.get_instance_count() == 0, 'Transient measurement members were not cleared')
    numeric_exact(measurement['recoveredValue'][0], before[0], 'Native serialization changed original root XYZ')
    return desired, measurement


def footprint(bundle, measurement, value, matrix):
    numeric_exact(value, measurement['recoveredValue'], 'Saved recovered Transform differs from actual measured serialization')
    numeric_exact(matrix, measurement['storedMatrix'], 'Saved actual FMatrix differs from measured serialization')
    root = bundle['root']
    points = bundle['row']['expectedNativeVerticesCm']
    local = [[sum(p[j]*matrix[j][axis] for j in range(3)) for axis in range(3)] for p in points]
    import math
    radius = max(math.hypot(p[0], p[1]) for p in local)
    old_guard = guard.module('r25_original_own_bed_mask', guard.ROOT/'scripts/unreal/exterior-garden-organic-native.py')
    boundary = old_guard._boundary(bundle['garden']['sourceMulchTrianglesCm'][root['sourceBedId']])
    actual_xy = value[0][:2]
    boundary_distance = min(old_guard._distance(actual_xy, a, b) for a, b in boundary)
    require(radius <= root['radiusCm']+guard.NUMERICAL_CROWN_CAP_CM
            and radius+guard.NUMERICAL_CROWN_CAP_CM < boundary_distance, 'Saved complete native FLOAT crown escapes original envelope/bed')
    require(max(abs(actual_xy[i]-root['positionCm'][i]) for i in range(2)) <= .002,
            'Original native root differs from source XYZ beyond declared source-to-native FLOAT bound')
    world = [[value[0][i]+p[i] for i in range(3)] for p in local]
    require(all(any(old_guard._triangle_inside(p[:2], tri)
                    for tri in bundle['garden']['sourceMulchTrianglesCm'][root['sourceBedId']]) for p in world),
            'Actual complete native fern vertices escape original bed')
    return {'rootId': root['id'], 'actualNativeRootXYZ': value[0],
        'originalNativeRootXYZExact': True, 'originalWrappedRotationCopiedExactlyBeforeSerialization': True,
        'recoveredTransformAndStoredMatrixExactActualMeasuredBinary64': True,
        'actualStoredMatrix': matrix, 'savedNativeValue': value,
        'actualNativeAllVertexRadiusCm': radius,
        'actualNativeAboveRootHeightCm': max(p[2] for p in local),
        'actualNativeBelowRootDepthCm': -min(p[2] for p in local),
        'fullContainingCircleToOriginalBedBoundaryClearanceCm': boundary_distance-radius,
        'decodedAllNativeFloat32VerticesChecked': len(world),
        'sourceToNativeCrownNumericalCapCm': guard.NUMERICAL_CROWN_CAP_CM,
        'originalSourceAbovePivotHeightCm': root['actualHeightCm'],
        'sourceProposedFernAbovePivotHeightCm': bundle['plan']['placementProposal']['abovePivotHeightCm'],
        'heightEquivalenceClaimed': False, 'nativeAppearanceAccepted': False}


def cyclic(face):
    return min(tuple(face[i:]+face[:i]) for i in range(3))


def mesh_proof(u, mesh, row):
    expected = [cyclic([tuple(row['expectedNativeVerticesCm'][i]+row['uv0'][i])
                       for i in row['indices'][j:j+3]]) for j in range(0, len(row['indices']), 3)]
    require(mesh.get_num_lods() == 3 and len(mesh.get_editor_property('static_materials')) == 1
            and not mesh.get_editor_property('has_navigation_data'),
            'Three identical collisionless one-slot original-mesh pilot LODs required')
    subsystem = u.get_editor_subsystem(u.StaticMeshEditorSubsystem)
    screens = list(subsystem.get_lod_screen_sizes(mesh))
    require(screens == [guard.f32(v) for v in (1., .15, .04)], 'Saved actual pilot LOD screens differ')
    proofs = []
    for lod in range(3):
        settings = subsystem.get_lod_build_settings(mesh, lod)
        require(all(settings.get_editor_property(key) == value for key, value in {
            'use_full_precision_u_vs': True, 'generate_lightmap_u_vs': False,
            'recompute_normals': False, 'recompute_tangents': True, 'remove_degenerates': False}.items()),
            'Saved original normal/UV and requested tangent build policy differs')
        description = mesh.get_static_mesh_description(lod)
        require(description and description.get_triangle_count() == mesh.get_num_triangles(lod)
                == row['triangles'] and mesh.get_num_sections(lod) == 1, 'Saved original fern triangle/section count differs')
        observed = []
        for index in range(row['triangles']):
            face = []
            for corner in range(3):
                vi = description.get_triangle_vertex_instance(u.TriangleID(id_value=index), corner)
                p = description.get_vertex_position(description.get_vertex_instance_vertex(vi))
                uv = description.get_vertex_instance_uv(vi, 0)
                face.append(tuple(vec(p)+vec(uv, 'xy')))
            observed.append(cyclic(face))
        require(observed == expected, 'Original native FLOAT positions/UV/order/connectivity/winding differs')
        proofs.append({'lod': lod, 'triangles': len(observed), 'nativeCornerSha256': digest(observed),
                       'orderedNativeFloat32PositionUvWindingVerified': True})
    return {'mesh': mesh.get_path_name(), 'lodProofs': proofs, 'actualLodScreenSizes': screens,
        'savedBuildPolicyVerified': True,
        'originalFullShapeAtAllThreePilotLods': True, 'originalProviderLodChainPresent': False,
        'sourceNormalsPreservedInExport': True, 'originalSourceTangentsPresent': False,
        'nativeTangentsRequestedFromOriginalUv': True, 'nativeTangentGenerationNumericallyVerified': False,
        'nativeNormalTangentReadbackAvailable': False,
        'nativeMeshPackageIndependentlyUnloaded': False}


def import_geometry(u, path, bundle, material, h):
    assets = u.EditorAssetLibrary
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    pipelines = []
    for original, name in (('GLTFSceneAssets', 'Assets'), ('GLTFMaterials', 'Materials'), ('LevelActors', 'Level')):
        target = PREFIX+'/Pipeline/'+name
        require(not assets.does_asset_exist(target), 'Fresh own R25 pipeline required')
        p = assets.duplicate_asset('/Game/Brezi/Pipeline/'+original, target)
        require(p, 'Cannot duplicate original generic importer pipeline')
        pipelines.append(p)
    for key, value in {'combine_static_meshes_behavior': u.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE,
                       'collision': False, 'build_nanite': False, 'generate_lightmap_u_vs': False}.items():
        pipelines[0].get_editor_property('mesh_pipeline').set_editor_property(key, value)
    for key, value in {'remove_degenerates': False, 'recompute_normals': False,
                       'recompute_tangents': True, 'use_full_precision_u_vs': True}.items():
        pipelines[0].get_editor_property('common_meshes_properties').set_editor_property(key, value)
    generic_material = pipelines[0].get_editor_property('material_pipeline')
    generic_material.set_editor_property('import_materials', False)
    generic_material.get_editor_property('texture_pipeline').set_editor_property('import_textures', False)
    pipelines[2].set_editor_property('scene_hierarchy_type', u.InterchangeSceneHierarchyType.CREATE_LEVEL_ACTORS)
    params = u.ImportAssetParameters()
    for key, value in {'is_automated': True, 'replace_existing': False, 'force_show_dialog': False,
        'override_pipelines': [u.SoftObjectPath(p.get_path_name()) for p in pipelines],
        'import_level': levels.get_current_level()}.items():
        params.set_editor_property(key, value)
    before = {a.get_path_name() for a in actors.get_all_level_actors()}
    manager = u.InterchangeManager.get_interchange_manager_scripted()
    require(manager.import_scene(PREFIX+'/Geometry', manager.create_source_data(str(path)), params), 'Original fern subset import failed')
    temporary = [a for a in actors.get_all_level_actors() if a.get_path_name() not in before]
    found = [c.get_editor_property('static_mesh') for a in temporary
             for c in a.get_components_by_class(u.StaticMeshComponent)]
    require(len(found) == 1 and found[0] and found[0].get_path_name().startswith(PREFIX+'/'),
            'Exactly one owned original fern StaticMesh required')
    mesh = found[0]
    name = guard.MODEL+'_LOD0'
    require(mesh.get_name() == name or mesh.get_name().endswith('_'+name), 'Original fern mesh identity differs')
    canonical = PREFIX+'/Geometry/StaticMeshes/'+name
    if mesh.get_path_name().split('.')[0] != canonical:
        require(assets.rename_asset(mesh.get_path_name().split('.')[0], canonical), 'Cannot canonicalize own fern mesh')
        mesh = assets.load_asset(canonical)
    mesh.set_material(0, material)
    mesh.set_editor_property('has_navigation_data', False)
    subsystem = h['meshHelper'].static_mesh_subsystem(u)
    for lod in (1, 2):
        require(subsystem.set_lod_from_static_mesh(mesh, lod, mesh, 0, True) == lod, 'Cannot copy original full-shape pilot LOD')
    for lod in range(3):
        settings = subsystem.get_lod_build_settings(mesh, lod)
        for key, value in {'use_full_precision_u_vs': True, 'generate_lightmap_u_vs': False,
            'recompute_normals': False, 'recompute_tangents': True, 'remove_degenerates': False}.items():
            settings.set_editor_property(key, value)
        subsystem.set_lod_build_settings(mesh, lod, settings)
    require(subsystem.set_lod_screen_sizes(mesh, [1., .15, .04]), 'Cannot retain original garden screen thresholds')
    assets.set_metadata_tag(mesh, 'BreziGeneratedBy', OWNER)
    assets.set_metadata_tag(mesh, 'BreziR25OriginalSource', digest(bundle['plan']['sourceGltf']))
    require(assets.save_loaded_asset(mesh, only_if_is_dirty=False), 'Cannot save original fern master')
    h['meshHelper'].finish_static_mesh_compilation(u, synchronous=True)
    mesh_proof(u, mesh, bundle['row'])
    require(list(subsystem.get_lod_screen_sizes(mesh)) == [guard.f32(v) for v in (1., .15, .04)],
            'Actual pilot LOD screen thresholds differ')
    for actor in reversed(temporary):
        require(actors.destroy_actor(actor), 'Cannot remove own temporary fern import actor')
    removed = []
    for path in assets.list_assets(PREFIX+'/Geometry', recursive=True, include_folder=False):
        value = assets.load_asset(path)
        if value and value.get_path_name().split('.')[0] == canonical:
            continue
        require(value and value.get_class().get_name() in ('InterchangeSceneImportAsset', 'ObjectRedirector'),
                'Unexpected own fern imported artifact')
        removed.append(value.get_path_name())
        require(assets.delete_asset(path), 'Cannot remove own transient import metadata')
    for p in pipelines:
        require(assets.save_loaded_asset(p, only_if_is_dirty=False), 'Cannot save own fern pipeline')
    return mesh, [p.get_path_name() for p in pipelines], removed


def primary_api():
    engine = Path('/Users/Shared/Epic Games/UE_5.8/Engine')
    path = engine/'Source/Runtime/Engine/Classes/Components/InstancedStaticMeshComponent.h'
    text = path.read_text()
    require('UFUNCTION(BlueprintCallable, Category = "Components|InstancedStaticMesh")\n\tENGINE_API virtual bool UpdateInstanceTransform'
            in text and 'TArray<FInstancedStaticMeshInstanceData> PerInstanceSMData;' in text,
            'Installed reflected single-member update/storage API differs')
    return pin(path)


def preflight(output):
    output = Path(output).resolve()
    require(output.is_relative_to(ROOT/'output/unreal') and not output.exists(), 'Fresh source preflight output required')
    bundle = guard.source()
    base = guard.saved_native_base()  # Deliberately blocks before any write while saved base is unavailable.
    guard.validate_clone(base)
    sources = [ROOT/OWNER, ROOT/guard.OWNER, ROOT/'scripts/unreal/exterior-garden-fern-materials-r25.py']
    require(all(p.is_file() for p in sources), 'New R25 source draft is incomplete')
    inputs = preflight_inputs(bundle, base)
    output.mkdir()
    glb = output/'one-original-fern.glb'
    geometry = guard.write_glb(glb, bundle)
    data = {'schema': guard.SCHEMA, 'owner': OWNER, 'status': 'source-only-fern-native-preflight-validated',
        'createdAt': now(), 'sourcePlan': pin(guard.SOURCE), 'sourceFreeze': pin(guard.FREEZE),
        'actualNativeBase': base['reportPin'], 'actualNativeBaseProcess': base['process'],
        'actualRootClone': pin(guard.NATIVE_OUTPUT/'garden-fern-project-clone.json'),
        'targetOutput': str(guard.NATIVE_OUTPUT), 'sourceGeometry': geometry,
        'targetActor': base['targetActor'], 'targetComponent': base['targetComponent'],
        'oldMesh': base['oldMesh'], 'inputFiles': inputs, 'primaryInstanceApi': primary_api(),
        'proposedAbovePivotHeightCm': bundle['plan']['placementProposal']['abovePivotHeightCm'],
        'originalAbovePivotHeightCm': bundle['root']['actualHeightCm'],
        'newOriginalMesh': 1, 'newPilotLods': 3, 'pilotLodsIdenticalOriginal': True,
        'originalProviderLodChainPresent': False, 'newMaterials': 1, 'newTextures': 4, 'newPipelines': 3,
        'newActors': 0, 'newRoots': 0, 'changedExistingRoot': 1, 'newPackages': 9,
        'nativeApplied': False, 'nativeAppearanceAccepted': False,
        'fullPhotorealismAccepted': False, 'performanceAccepted': False, 'shippingVerified': False}
    write(output/'source-preflight.json', data)
    print(__import__('json').dumps(pin(output/'source-preflight.json')))


def preflight_inputs(bundle, base):
    terminal = read(base['process']['path'])
    inputs = {**bundle['plan']['inputFiles'], **base['report']['inputFiles'],
              **terminal['sourcePinsBeforeNative']}
    for p in [ROOT/OWNER, ROOT/guard.OWNER, ROOT/'scripts/unreal/exterior-garden-fern-materials-r25.py',
              ROOT/'scripts/unreal/test_exterior_garden_fern_native_r25.py', guard.SOURCE, guard.FREEZE,
              guard.BASE_REPORT, Path(base['raw']['path']), Path(base['process']['path']),
              guard.NATIVE_OUTPUT/'garden-fern-project-clone.json']:
        inputs[str(p)] = sha(p)
    return inputs


def validate_preflight(path, bundle, base):
    data = read(path)
    require(data['schema'] == guard.SCHEMA and data['owner'] == OWNER
            and data['status'] == 'source-only-fern-native-preflight-validated'
            and data['sourcePlan'] == pin(guard.SOURCE) and data['sourceFreeze'] == pin(guard.FREEZE)
            and data['actualNativeBase'] == base['reportPin'] and data['actualNativeBaseProcess'] == base['process']
            and data['actualRootClone'] == pin(guard.NATIVE_OUTPUT/'garden-fern-project-clone.json')
            and data['targetOutput'] == str(guard.NATIVE_OUTPUT)
            and data['targetActor'] == base['targetActor'] and data['targetComponent'] == base['targetComponent'],
            'Typed R25 source/actual saved-base preflight differs')
    require(data['inputFiles'] == preflight_inputs(bundle, base), 'Exact R25 preflight source closure differs')
    require(data['newActors'] == data['newRoots'] == 0 and data['changedExistingRoot'] == 1
            and data['newOriginalMesh'] == 1 and data['newPilotLods'] == 3
            and data['newMaterials'] == 1 and data['newTextures'] == 4
            and data['newPipelines'] == 3 and data['newPackages'] == 9
            and data['pilotLodsIdenticalOriginal'] is True and data['originalProviderLodChainPresent'] is False,
            'Exact one-root/one-original-shape native scope differs')
    require(all(data[k] is False for k in ('nativeApplied', 'nativeAppearanceAccepted',
            'fullPhotorealismAccepted', 'performanceAccepted', 'shippingVerified')), 'Preflight cannot grant native acceptance')
    for p, value in data['inputFiles'].items():
        require(sha(p) == value, 'Consumed R25 preflight input changed')
    require(data['primaryInstanceApi'] == primary_api(), 'Installed measured instance API changed')
    guard.decode_glb(guard.checked(data['sourceGeometry']), bundle)
    return data


def main():
    import unreal as u
    bundle = guard.source()
    base = guard.saved_native_base()
    preflight_path = Path(os.environ['BREZI_FERN_PREFLIGHT']).resolve()
    require(sha(preflight_path) == os.environ['BREZI_FERN_PREFLIGHT_SHA256'], 'Selected typed fern preflight changed')
    pf = validate_preflight(preflight_path, bundle, base)
    output = Path(os.environ['BREZI_FERN_OUTPUT']).resolve()
    require(output == guard.NATIVE_OUTPUT, 'Only exact fresh R25a may change')
    project = output/'Project/BreziTwin'
    source_project = Path(base['report']['project'])
    require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve() == project,
            'Wrong own native project')
    require(not (output/REPORT).exists() and not (output/'exterior-import-report.json').exists(),
            'No copied/fake original or prior fern native report')
    original = base['native'].g
    require(original.inventory(project/'Content') == base['content']
            and original.project_proof(project) == base['protected']
            and original.inventory(source_project/'Content') == base['content']
            and original.project_proof(source_project) == base['protected'], 'Fresh actual saved-base project bytes differ')
    clone = read(output/'garden-fern-project-clone.json')
    guard.validate_clone(base)
    require(clone['schema'] == guard.SCHEMA
            and clone['status'] == 'verified-byte-identical-independent-apfs-r25a-original-r22-project-clone-before-fern-native'
            and clone['sourcePlan'] == pin(guard.SOURCE) and clone['nativeBaseReport'] == base['reportPin']
            and clone['fileCount'] == 4181 and clone['contentFiles'] == 4049
            and clone['protectedFiles'] == 132 and clone['nativeExecuted'] is False,
            'Typed fresh actual saved R22 root-owned independent clone required')
    for directory, rows in (('Content', base['content']), ('', base['protected'])):
        for relative in rows:
            a, b = source_project/directory/relative, project/directory/relative
            require((a.stat().st_dev, a.stat().st_ino) != (b.stat().st_dev, b.stat().st_ino), 'Original native hardlink forbidden')
    require(sha(project/'Binaries/Mac/libUnrealEditor-BreziTwin.dylib') == MODULE_SHA
            and read(project/'Binaries/Mac/UnrealEditor.modules')['BuildId'] == '55116800', 'Actual native module/engine differs')
    h = base['native'].helpers(base['nativeBundle'])  # Frozen policy must be loaded FIRST.
    maps = guard.module('r25_new_fern_materials', ROOT/'scripts/unreal/exterior-garden-fern-materials-r25.py')
    maps.preflight_enums(u)
    state = {'schema': guard.SCHEMA, 'owner': OWNER, 'status': 'running', 'startedAt': now(),
        'nativeProcessId': os.getpid(), 'output': str(output), 'project': str(project),
        'selectedSourcePlan': pin(guard.SOURCE), 'sourcePreflight': pin(preflight_path),
        'baseNativeReport': base['reportPin'], 'baseNativeProcess': base['process'],
        'projectClone': pin(output/'garden-fern-project-clone.json'), 'inputFiles': pf['inputFiles'],
        'activeDesign': base['report']['activeDesign'], 'setbacksMm': base['report']['setbacksMm'],
        'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False,
        'performanceAccepted': False, 'shippingVerified': False, 'nativeApplied': False,
        'nativeNormalTangentReadbackAvailable': False, 'materialPackagesIndependentlyReloaded': False,
        'nativeMeshPackagesIndependentlyReloaded': False}
    receipt = output/REPORT
    write(receipt, state)
    try:
        levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False) and levels.load_level(MAP), 'Cannot load own saved R22 map')
        before = base['native'].full_witness(u, h)
        require(before == base['witness'], 'Actual full5346 saved-base actors/policies differ')
        materials_before = base['native'].verify_materials(u, base['nativeBundle'], h)
        require(materials_before == base['materials'], 'Any original56graph/84texture witness differs')
        component = base['native'].component_lookup(u, base['targetActor'], base['targetComponent'])
        require(component.get_instance_count() == 1 and component.get_editor_property('static_mesh').get_path_name() == base['oldMesh'],
                'Exact one inherited garden member/model required')
        desired, measurement = transient_scale_measurement(u, component, bundle['plan']['placementProposal'])
        require(base['native'].full_witness(u, h) == before, 'Transient measurement changed a scene actor')
        write(output/'fern-native-scale-measurement.json', measurement)
        write(output/'fern-witness-before.json', before)
        write(output/'fern-materials-original-before.json', materials_before)
        material, material_report = maps.build_materials(u, bundle['plan'], h['existing'].graph_snapshot)
        mesh, pipelines, removed = import_geometry(u, guard.checked(pf['sourceGeometry']), bundle, material, h)
        require(base['native'].full_witness(u, h) == before, 'Temporary asset import changed an original actor')
        require(component.set_static_mesh(mesh), 'Cannot bind one original fern to existing garden member')
        component.set_editor_property('override_materials', [])
        require(component.update_instance_transform(0, desired, False, True, True), 'Cannot apply one uniformly fitted native root')
        component.get_owner().synchronize_instance_bounds()
        value = transform_value(component.get_instance_transform(0, False))
        proof = footprint(bundle, measurement, value, stored_matrix(component))
        expected = guard.expected_witness(before, base['targetActor'], base['targetComponent'],
            base['oldMesh'], mesh.get_path_name(), material.get_path_name(), value)
        require(base['native'].full_witness(u, h) == expected, 'Single-root change exceeds exact full5346 actor counterfactual')
        write(output/'fern-witness-expected.json', expected)
        require(levels.save_current_level(), 'Cannot save one-root candidate map')
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False) and levels.load_level(MAP), 'Cannot unload/reload saved one-root candidate')
        after = base['native'].full_witness(u, h)
        require(after == expected, 'Saved full5346 actor witness differs from single-root counterfactual')
        hisms = [c for row in after.values() for c in row['components']
                 if c['class'] == '/Script/Engine.HierarchicalInstancedStaticMeshComponent']
        require(len(hisms) == 2312 and sum(c['instanceCount'] for c in hisms) == 676944,
                'Saved actual full-scene HISM count/population changed')
        saved_component = base['native'].component_lookup(u, base['targetActor'], base['targetComponent'])
        saved_value = transform_value(saved_component.get_instance_transform(0, False))
        saved_proof = footprint(bundle, measurement, saved_value, stored_matrix(saved_component))
        require(saved_proof == proof, 'Saved native full-crown/root serialization changed')
        saved_material = maps.verify_materials(u, material_report, bundle['plan'], h['existing'].graph_snapshot)
        saved_mesh = u.EditorAssetLibrary.load_asset(mesh.get_path_name())
        require(saved_mesh.get_material(0) == saved_material and saved_component.get_material(0) == saved_material
                and saved_component.get_num_materials() == 1, 'Saved default/effective material binding differs')
        saved_mesh_proof = mesh_proof(u, saved_mesh, bundle['row'])
        materials_saved = base['native'].verify_materials(u, base['nativeBundle'], h)
        require(materials_saved == materials_before, 'Original56graphs/84textures changed after reload')
        after_content = original.inventory(project/'Content')
        package_paths = [saved_mesh.get_path_name().split('.')[0], saved_material.get_path_name().split('.')[0]]
        package_paths += [r['asset'].split('.')[0] for r in material_report['textures'].values()]
        package_paths += [p.split('.')[0] for p in pipelines]
        delta = guard.validate_content(base['content'], after_content, package_paths)
        require(original.project_proof(project) == base['protected']
                and original.inventory(source_project/'Content') == base['content']
                and original.project_proof(source_project) == base['protected'], 'Protected or original saved R22 project changed')
        validate_preflight(preflight_path, bundle, base)
        write(output/'fern-witness-saved.json', after)
        write(output/'fern-materials-original-saved.json', materials_saved)
        write(output/'fern-content-after.json', after_content)
        state.update(status=STATUS,endedAt=now(),savedMapUnloadedReloaded=True,nativeApplied=True,
            originalSavedR22Unchanged=True,sourceInputsUnchanged=True,changedOriginalRoot=1,newActors=0,newRoots=0,
            inheritedPlantAssetsBytePreserved=True,inheritedPlantNativeLodsRemeasuredHere=False,
            actualFullActorCount=len(after),actualFullHismComponents=len(hisms),
            actualFullHismInstances=sum(c['instanceCount'] for c in hisms),
            originalScopedMaterialGraphsPreserved=56,originalScopedTextureObjectsPreserved=84,
            newMaterialGraphs=1,newTextureObjects=4,totalScopedMaterialGraphs=57,totalScopedTextureObjects=88,
            changedComponent={'actor':base['targetActor'],'component':base['targetComponent'],
                'groupId':guard.GROUP,'beforeMesh':base['oldMesh'],'afterMesh':saved_mesh.get_path_name()},
            sourceGeometry=pf['sourceGeometry'],nativeMeshReadback=saved_mesh_proof,
            sourceRootHeightChangeExplicit=True,savedRootReadback=saved_proof,nativeScaleMeasurement=pin(output/'fern-native-scale-measurement.json'),
            materialReport=material_report,importPipelineAssets=pipelines,discardedTransientMetadata=removed,
            beforeActorWitness=pin(output/'fern-witness-before.json'),expectedActorWitness=pin(output/'fern-witness-expected.json'),
            savedActorWitness=pin(output/'fern-witness-saved.json'),savedActorWitnessSha256=digest(after),
            expectedActorWitnessSha256=digest(expected),originalMaterialsBefore=pin(output/'fern-materials-original-before.json'),
            originalMaterialsSaved=pin(output/'fern-materials-original-saved.json'),afterContentInventory=pin(output/'fern-content-after.json'),
            protectedProjectProof=base['report']['protectedProjectProof'],assetDelta=delta)
        write(receipt, state)
        print(__import__('json').dumps({'report':pin(receipt),'status':STATUS,'nativeAppearanceAccepted':False}))
    except Exception as error:
        state.update(status='failed',endedAt=now(),error=str(error))
        write(receipt,state)
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight-output', type=Path)
    args = parser.parse_args()
    if args.preflight_output:
        preflight(args.preflight_output)
    else:
        main()
