"""UNBOUND R41 native integration design; this is not a launch entry point.

The private import/assembly kernels use APIs already used by saved native
helpers. They are not called by this module. A new bound owner must supply a
selected original-image decision, actual saved base, independent clone, native
attribute/policy proof and exact source-corner routing before any execution.
No historical source producer, raster, or fixture is imported or rerun here.
"""
from copy import deepcopy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-lawn-leaf-strip-native-r41-draft.py'
SCHEMA = 'brezi-unbound-original-photo-leaf-strip-native-integration-draft-r41'
PREFIX = '/Game/Brezi/LawnLeafStrip20261002R41'
PLAN = ROOT/'output/unreal/exterior-lawn-leaf-strip-20261002-r41-source-study-r3/leaf-strip-source-plan.json'
PLAN_SHA = 'ca6b55d22c3fdf934da09410a4244462844f0223db3b18ad9f0f69468a4e1db5'
READINESS = ROOT/'output/unreal/exterior-lawn-leaf-strip-20261002-r41-source-readiness-r3/source-readiness.json'
READINESS_SHA = '5f631487ddae71d0c80bdc690a13d0c3c956d2bfc41e3efce60db2723e60c2ab'
MATERIAL = '/Game/Brezi/Exterior20260926/Materials/M_lawn_photographic_blade.M_lawn_photographic_blade'
MATERIAL_GRAPH_SHA = '2c933cabfa14ac5e3ed4e2c7b801be05bed6d121382da0dd7e6a3724b936c05a'
SELECTED_BASE = None
ROOT_IMAGE_DECISION = None
PROJECT_CLONE = None
NATIVE_PLAN = None
NATIVE_REPORT = None
NATIVE_PROCESS_ID = None
NATIVE_ATTRIBUTE_AND_POLICY_PROOF = None


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def pinned_json(pin):
    path = Path(pin['path']).resolve()
    require(path.is_relative_to(ROOT) and path.is_file()
            and sha(path) == pin['sha256']
            and ('bytes' not in pin or path.stat().st_size == pin['bytes']),
            'Frozen R41 source pin differs: '+str(path))
    return json.loads(path.read_text())


def source_contract():
    """Read existing pinned receipts only; does not regenerate their evidence."""
    plan = pinned_json({'path': str(PLAN), 'sha256': PLAN_SHA, 'bytes': 13210})
    ready = pinned_json({'path': str(READINESS), 'sha256': READINESS_SHA, 'bytes': 15410})
    require(ready['selectedSourceProposal'] == {'path': str(PLAN), 'sha256': PLAN_SHA, 'bytes': 13210}
            and ready['status'] == 'source-proposal-frozen-native-and-image-decision-pending',
            'The frozen source-only R41 readiness is required')
    require(plan['schema'] == 'brezi-original-photo-lawn-leaf-body-uv-source-proposal-r41'
            and plan['revision'] == 3 and plan['schemaVersion'] == 1
            and all(plan[key] is None for key in ('futureSelectedNativeBase',
                'futureRootImageDecision', 'futureProjectClone', 'futureNativePlan',
                'futureNativeReport', 'futureActualNativeProcessId')),
            'Historical source proposal must remain unbound')
    proof = pinned_json(plan['uvTangentPreservation'])
    controls = pinned_json(plan['recordedManagedLawnControls'])
    require(proof['only120Uv0AndTangentAccessorRangesChanged'] is True
            and proof['documentAndAllOtherBinaryBytesUnchanged'] is True
            and proof['positionNormalColorUv1IndexRootLayoutExact'] is True
            and proof['nativeNormalTangentNumericReadbackPerformed'] is False,
            'R41 source UV/tangent change and native-readback limits differ')
    nodes = {row['node']: row for row in proof['nodes']}
    masters = {}
    for row in nodes.values():
        require(row['lod'] in (0, 1, 2), 'Only the three actually available source LODs are allowed')
        masters.setdefault(row['meshId'], {})[row['lod']] = row
    groups = controls['exactSourceGroups']
    require(len(nodes) == 60 and len(masters) == 20
            and all(set(lods) == {0, 1, 2} for lods in masters.values())
            and len(groups) == len({row['actor'] for row in groups}) == 40
            and sum(row['instances'] for row in groups) == 102011
            and {row['sourceMeshId'] for row in groups}.issubset(masters)
            and sum(row['triangles'] for row in nodes.values()) == 10944,
            'The exact 20-master / 60-LOD / 40-group / 102011-member scope differs')
    require(plan['recordedNativeMaterialGraphSha256'] == MATERIAL_GRAPH_SHA
            and plan['budget']['newTextures'] == plan['budget']['newMaterialGraphs'] == 0,
            'No material or map substitution is allowed')
    # These hashes bind source attributes, not native numeric N/T/C readback.
    return {'plan': plan, 'sourceReadiness': ready, 'proof': proof,
            'recordedControls': controls, 'nodes': nodes, 'masters': masters,
            'groups': groups, 'binding': None}


def require_native_binding(*_args, **_kwargs):
    raise RuntimeError('UNBOUND R41 DRAFT: actual image selection, saved base, clone, '
                       'attribute/policy proof and bound owner/preflight are pending')


def validate_current_witness(current, contract):
    """Bind each historical target to the subsequently selected full witness.

    Exact target digests must still match; unrelated actors may have been added
    by another independently approved scope. This is not a current native read.
    """
    for target in contract['groups']:
        require(target['actor'] in current, 'Selected saved map lacks an original lawn target')
        row = current[target['actor']]
        require(digest(row) == target['recordedActorWitnessSha256']
                and len(row['components']) == 1
                and digest(row['components'][0]) == target['recordedComponentWitnessSha256']
                and row['components'][0]['instanceCount'] == target['instances']
                and row['components'][0]['orderedInstanceTransformsSha256'] ==
                    target['recordedOrderedInstanceTransformsSha256']
                and row['components'][0]['materials'] == [MATERIAL],
                'Selected original lawn actor/component/member/material identity differs')
    return True


def counterfactual(current, contract, new_master_paths):
    """Exactly forty old component mesh paths may change; no other scene field."""
    validate_current_witness(current, contract)
    require(set(new_master_paths) == set(contract['masters'])
            and len(set(new_master_paths.values())) == 20
            and all(path.startswith(PREFIX+'/Geometry/') for path in new_master_paths.values()),
            'Exactly twenty disjoint owned master paths required')
    expected = deepcopy(current)
    for target in contract['groups']:
        expected[target['actor']]['components'][0]['mesh'] = new_master_paths[target['sourceMeshId']]
    return expected


def _import_node_assets(u, contract, h):
    """Private future kernel; new bound owner must authorize before calling it.

    h.meshHelper is the pinned, commandlet-compatible lawn-geometry helper.
    h.writeCheckpoint is a future owner's evidence writer, not an Unreal API.
    Count and labels do not route source identity. The future owner must run a
    complete ordered-corner matcher before using any returned mesh as a master.
    """
    assets = u.EditorAssetLibrary
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
    require(not assets.list_assets(PREFIX, recursive=True, include_folder=False),
            'A fresh owned R41 namespace is required')
    subsystem = h['meshHelper'].static_mesh_subsystem(u)
    h['meshHelper'].finish_static_mesh_compilation(u, synchronous=True)
    pipelines = []
    for original, name in (('GLTFSceneAssets', 'Assets'), ('GLTFMaterials', 'Materials'), ('LevelActors', 'Level')):
        pipeline = assets.duplicate_asset('/Game/Brezi/Pipeline/'+original, PREFIX+'/Pipeline/'+name)
        require(pipeline, 'Cannot create own R41 import pipeline')
        pipelines.append(pipeline)
    mesh_pipeline = pipelines[0].get_editor_property('mesh_pipeline')
    for key, value in {'combine_static_meshes_behavior': u.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE,
                       'collision': False, 'build_nanite': False, 'generate_lightmap_u_vs': False}.items():
        mesh_pipeline.set_editor_property(key, value)
    common = pipelines[0].get_editor_property('common_meshes_properties')
    for key, value in {'bake_meshes': False, 'bake_pivot_meshes': False, 'import_lods': False,
                       'remove_degenerates': False, 'recompute_normals': False, 'recompute_tangents': False,
                       'use_full_precision_u_vs': True}.items():
        common.set_editor_property(key, value)
    material_pipeline = pipelines[0].get_editor_property('material_pipeline')
    material_pipeline.set_editor_property('import_materials', False)
    material_pipeline.get_editor_property('texture_pipeline').set_editor_property('import_textures', False)
    pipelines[2].set_editor_property('scene_hierarchy_type', u.InterchangeSceneHierarchyType.CREATE_LEVEL_ACTORS)
    params = u.ImportAssetParameters()
    for key, value in {'is_automated': True, 'replace_existing': False, 'force_show_dialog': False,
                       'override_pipelines': [u.SoftObjectPath(p.get_path_name()) for p in pipelines],
                       'import_level': levels.get_current_level()}.items():
        params.set_editor_property(key, value)
    before = {a.get_path_name() for a in actors.get_all_level_actors()}
    manager = u.InterchangeManager.get_interchange_manager_scripted()
    ok = manager.import_scene(PREFIX+'/Geometry', manager.create_source_data(contract['plan']['sourceGeometryProposal']['path']), params)
    temporary = [a for a in actors.get_all_level_actors() if a.get_path_name() not in before]
    meshes = {}
    observed = []
    for actor in temporary:
        for component in actor.get_components_by_class(u.StaticMeshComponent):
            mesh = component.get_editor_property('static_mesh')
            observed.append({'actor': actor.get_path_name(), 'labelObservation': actor.get_actor_label(),
                             'component': component.get_name(), 'mesh': mesh.get_path_name() if mesh else None})
            if mesh:
                meshes[mesh.get_path_name()] = mesh
    h['writeCheckpoint']('import-return-and-temporary-nodes',
                         {'importReturned': bool(ok), 'temporary': observed})
    require(ok and len(meshes) == 60
            and all(mesh.get_class().get_name() == 'StaticMesh' and path.startswith(PREFIX+'/Geometry/')
                    for path, mesh in meshes.items()), 'The exact 60 original source-node meshes must import')
    h['meshHelper'].finish_static_mesh_compilation(u, synchronous=True)
    return {'meshes': meshes, 'temporaryActors': temporary, 'pipelines': pipelines, 'subsystem': subsystem}


def _assemble_20_masters(u, contract, imported, old_masters, exact_node_meshes, h):
    """Private assembly kernel following actual SetLodFromStaticMesh routes.

    exact_node_meshes must be produced by complete source/native P/UV0/UV1/
    section/winding proof, including all sixty nodes. Equivalent LOD aliases
    are acceptable only when all their complete source signatures coincide;
    labels or triangle counts alone never prove identity.

    h.verifyMeshPolicy and h.verifyLodCorners are required future bound-owner
    functions. No policy/attribute proof is synthesized by this draft.
    """
    require(set(exact_node_meshes) == set(contract['nodes'])
            and len({mesh.get_path_name() for mesh in exact_node_meshes.values()}) == 60
            and set(old_masters) == set(contract['masters']), 'Exact old/new twenty-master routing required')
    assets = u.EditorAssetLibrary
    subsystem = imported['subsystem']
    result = {}
    for mid, lods in contract['masters'].items():
        original = old_masters[mid]
        require(original.get_num_lods() == 3 and len(original.get_editor_property('static_materials')) == 1
                and original.get_material(0).get_path_name() == MATERIAL,
                'Original exact three-LOD/one-material master required')
        master = exact_node_meshes[lods[0]['node']]
        # Every owned source LOD needs the same actual material object before
        # attachment: SetLodFromStaticMesh reuses slots by material identity.
        # Leaving temporary LOD slots null would append an unintended slot.
        for lod in (0, 1, 2):
            exact_node_meshes[lods[lod]['node']].set_editor_property(
                'static_materials', original.get_editor_property('static_materials'))
        for lod in (1, 2):
            require(subsystem.set_lod_from_static_mesh(master, lod, exact_node_meshes[lods[lod]['node']], 0, True) == lod,
                    'Cannot attach the original available R41 source LOD')
        for lod in (0, 1, 2):
            # Preserve the current selected master policy. In particular do not
            # invent a new tangent/reduction/normal setting from source alone.
            settings = subsystem.get_lod_build_settings(original, lod)
            subsystem.set_lod_build_settings(master, lod, settings)
            # Reflected in the installed primary header. Python availability
            # must still be preflighted by the future owner before any import.
            reduction = subsystem.get_lod_reduction_settings(original, lod)
            subsystem.set_lod_reduction_settings(master, lod, reduction)
        master.set_editor_property('has_navigation_data', original.get_editor_property('has_navigation_data'))
        h['meshHelper'].finish_static_mesh_compilation(u, synchronous=True)
        master.modify(True)
        screens = list(subsystem.get_lod_screen_sizes(original))
        require(len(screens) == 3 and subsystem.set_lod_screen_sizes(master, screens),
                'Exact original LOD screen policy required')
        require(list(subsystem.get_lod_screen_sizes(master)) == screens, 'Native screen policy changed')
        require(master.get_num_lods() == 3 and len(master.get_editor_property('static_materials')) == 1
                and master.get_material(0).get_path_name() == MATERIAL,
                'The exact original three LODs and one material slot must survive attachment')
        h['verifyMeshPolicy'](master, original)
        for lod in (0, 1, 2):
            h['verifyLodCorners'](master, lod, original, contract['nodes'][lods[lod]['node']])
        require(assets.save_loaded_asset(master, False), 'Cannot save the owned R41 master')
        result[mid] = master
    return result


def _cleanup_owned_imports(u, imported, masters, h):
    """No generic deletion: retain twenty masters/three pipelines only.

    Before deletion, all attached LODs must have passed full corner/policy
    verification. Forty unretained own source meshes and actual observed own
    InterchangeSceneImportAsset metadata are the only eligible asset classes.
    Unknown packages stop the future attempt rather than expand the whitelist.
    """
    assets = u.EditorAssetLibrary
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    keep = {mesh.get_path_name().split('.')[0] for mesh in masters.values()}
    keep.update(pipeline.get_path_name().split('.')[0] for pipeline in imported['pipelines'])
    require(len(keep) == 23 and all(path.startswith(PREFIX+'/') for path in keep),
            'Only the own twenty masters and three pipelines may remain')
    disposable = {path.split('.')[0] for path in imported['meshes']
                  if path.split('.')[0] not in keep}
    require(len(disposable) == 40, 'Exactly forty own source-LOD mesh assets may be retired')
    for actor in reversed(imported['temporaryActors']):
        require(actors.destroy_actor(actor), 'Cannot remove the own temporary import actor')
    observed = list(assets.list_assets(PREFIX, recursive=True, include_folder=False))
    h['writeCheckpoint']('owned-package-inventory-before-cleanup', {'assets': observed, 'keep': sorted(keep)})
    removed = []
    for path in observed:
        package = path.split('.')[0]
        if package in keep:
            continue
        obj = assets.load_asset(path)
        require(package.startswith(PREFIX+'/Geometry/') and obj
                and ((package in disposable and obj.get_class().get_name() == 'StaticMesh')
                     or (package not in disposable and obj.get_class().get_name() == 'InterchangeSceneImportAsset')),
                'Unknown owned package must not be silently deleted')
        require(assets.delete_asset(path), 'Cannot retire the exact own temporary import asset')
        removed.append(path)
    for obj in list(masters.values())+imported['pipelines']:
        require(assets.save_loaded_asset(obj, False), 'Cannot save the own retained R41 asset')
    require({path.split('.')[0] for path in assets.list_assets(PREFIX, recursive=True, include_folder=False)} == keep,
            'Final own R41 package namespace differs from exactly twenty meshes/three pipelines')
    return removed


def _mesh_only_40_rebinds(u, contract, masters, h):
    """Only set_static_mesh; no member/frame/random/custom/material setter.

    h.readRawControl must freshly observe the selected native component and
    verify matrix bytes, main seed, custom data and ordered recovered frames.
    h.verifyRecordedControl authenticates its fixed R41 historical target.
    Complete before/expected/saved scene and original packages stay the future
    bound owner's responsibility. This function does not save a map.
    """
    require(set(masters) == set(contract['masters']), 'All twenty masters required')
    changed = []
    for target in contract['groups']:
        c = h['componentLookup'](u, target['actor'], 'Instances')
        before = h['readRawControl'](c)
        h['verifyRecordedControl'](target, before)
        require(c.get_instance_count() == target['instances']
                and c.get_material(0).get_path_name() == MATERIAL,
                'Original lawn population/material differs before rebind')
        require(c.set_static_mesh(masters[target['sourceMeshId']]), 'Cannot bind the own master')
        after = h['readRawControl'](c)
        require(digest(before) == digest(after), 'Original raw/order/seed/custom control changed at mesh rebind')
        require(c.get_material(0).get_path_name() == MATERIAL, 'Lawn material binding changed')
        changed.append({'actor': target['actor'], 'instances': target['instances'],
                        'mesh': masters[target['sourceMeshId']].get_path_name(),
                        'rawControlBefore': before, 'rawControlAfter': after})
    require(len(changed) == 40 and sum(row['instances'] for row in changed) == 102011,
            'Exact forty mesh-only lawn rebinds required')
    return changed


def build_materials(*args, **kwargs):
    raise RuntimeError('R41 forbids material creation, texture import and existing pixel changes')


def apply_native(*args, **kwargs):
    require_native_binding()


if __name__ == '__main__':
    require_native_binding()
