"""Isolated R17 component-only leaf transmission experiment; no import/cook.

CPU guards are importable without Unreal. Native main runs only in a fresh
root-prepared project clone, using the R16 consumed-source snapshot for scene
and graph readback. The original exterior report is never rewritten.
"""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import sys
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-canopy-transmission-native.py'
STUDY_OWNER = 'scripts/unreal/exterior-canopy-transmission-study.py'
SCHEMA = 'brezi-canopy-transmission-component-overlay-r1'
STATUS = 'source-only-canopy-transmission-native-trial-pending'
NATIVE_STATUS = 'verified-saved-canopy-transmission-component-overlay'
MAP = '/Game/Brezi/Maps/Brezi'
MAP_FILE = 'Brezi/Maps/Brezi.umap'
PREFIX = '/Game/Brezi/CanopyTransmissionR1/Materials'
ROLE = 'BreziExterior:leaf-transmission-scale'
LEAF_IDS = ('regional_oak_leaf', 'regional_green_leaf')
BARK = '/Game/Brezi/Exterior20260926/Materials/M_ph_tree_small_02_branches.M_ph_tree_small_02_branches'
MESH_IDS = tuple('canopy_fullness_' + family + '_r1_' + v
                 for family in ('broadleaf', 'upright', 'orchard') for v in 'abc')
NEW_ASSETS = {key: PREFIX + '/M_canopy_transmission_' + kind + '_r1.M_canopy_transmission_' + kind + '_r1'
              for key, kind in zip(LEAF_IDS, ('oak', 'green'))}
EXPECTED_BASE = struct.unpack('<f', struct.pack('<f', .08))[0]
EXPECTED_NEW = struct.unpack('<f', struct.pack('<f', .24))[0]


def require(value, message):
    if not value:
        raise RuntimeError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n')


def now():
    return datetime.now(timezone.utc).isoformat()


def pin(path):
    path = Path(path).resolve()
    require(path.is_file() and not path.is_symlink(), 'Missing/nonregular pinned file: ' + str(path))
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def check_pin(row):
    require(set(row) == {'path', 'sha256', 'bytes'}, 'Unexpected source pin schema')
    p = Path(row['path'])
    require(p.is_absolute() and p.resolve() == p and not p.is_symlink() and p.is_file(), 'Invalid source pin path')
    require(p.stat().st_size == row['bytes'] and sha(p) == row['sha256'], 'Pinned bytes changed: ' + str(p))
    return p


def inventory(directory):
    directory = Path(directory).resolve()
    result = {}
    for p in sorted(directory.rglob('*')):
        require(not p.is_symlink(), 'Symlink is not an independent project file: ' + str(p))
        if p.is_file():
            result[p.relative_to(directory).as_posix()] = {'sha256': sha(p), 'bytes': p.stat().st_size}
    return result


def project_proof(project):
    project = Path(project).resolve()
    rows = {}
    for name in ('Config', 'Source', 'Binaries'):
        require((project / name).is_dir(), 'Missing protected project tree: ' + name)
        rows.update({name + '/' + key: value for key, value in inventory(project / name).items()})
    descriptor = project / 'BreziTwin.uproject'
    rows[descriptor.name] = {k: v for k, v in pin(descriptor).items() if k != 'path'}
    return rows


def scalar_variant(graph):
    result = copy.deepcopy(graph)
    nodes = [n for n in result['nodes'] if n['role'] == ROLE]
    require(len(nodes) == 1 and nodes[0]['class'] == 'MaterialExpressionConstant'
            and nodes[0]['values'] == {'r': EXPECTED_BASE} and not nodes[0]['inputs'],
            'Original leaf transmission node is absent, ambiguous, or different')
    require(result['roots']['SUBSURFACE_COLOR'] == ['BreziExterior:leaf-transmission', ''], 'Unexpected subsurface root')
    transmission = [n for n in result['nodes'] if n['role'] == 'BreziExterior:leaf-transmission']
    require(len(transmission) == 1 and transmission[0]['values']['code'] == 'return Color*Strength*Mask;'
            and transmission[0]['inputs'] == [['Color', 'BreziExterior:scan-color', ''],
                ['Strength', ROLE, ''], ['Mask', 'BreziExterior:leaf-mask-fallback', '']], 'Unexpected transmission expression')
    nodes[0]['values']['r'] = EXPECTED_NEW
    return result


def canonical_scope(report):
    require(report.get('status') == 'exterior-import-validated' and report.get('savedReloaded') is True,
            'Base is not the actual saved native exterior')
    require(report['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}
            and report['setbacksMm'] == {'street': 3000, 'east': 3000}, 'Design/setback mismatch')
    materials = report['materials']['materials']
    require(len(materials) == 42 and len(report['materials']['textures']) == 74, 'Base material population changed')
    plants = report['savedPlantReadback']
    require(len(plants) == 135 and sum(len(p['lodTriangles']) for p in plants) == 405, 'Base plant library changed')
    chosen = {p['id']: p for p in plants if p['id'] in MESH_IDS}
    require(set(chosen) == set(MESH_IDS), 'Fullness masters missing')
    variants = {}
    for key in LEAF_IDS:
        original = materials[key]
        require(digest(original['graph']) == original['graphSha256'] and original['recipe']['subsurfaceScale'] == .08,
                'Original native graph/recipe mismatch')
        expected = scalar_variant(original['graph'])
        proposed_recipe = copy.deepcopy(original['recipe'])
        proposed_recipe['subsurfaceScale'] = .24
        variants[key] = {'originalAsset': original['asset'], 'originalGraphSha256': original['graphSha256'],
                         'newAsset': NEW_ASSETS[key], 'expectedGraph': expected, 'expectedGraphSha256': digest(expected),
                         'originalRecipe': original['recipe'], 'proposedRecipe': proposed_recipe, 'changedRole': ROLE,
                         'originalNativeFloat': EXPECTED_BASE, 'proposedNativeFloat': EXPECTED_NEW}
    by_mesh = {row['mesh']: row for row in chosen.values()}
    targets = []
    for group_id, row in report['geometry']['groups'].items():
        if row['mesh'] not in by_mesh:
            continue
        plant = by_mesh[row['mesh']]
        leaf_id = 'regional_oak_leaf' if 'broadleaf' in plant['id'] else 'regional_green_leaf'
        require(plant['materials'] == [BARK, materials[leaf_id]['asset']], 'Fullness source slot layout differs')
        targets.append({'groupId': group_id, 'baseGroup': row, 'masterId': plant['id'], 'leafMaterialId': leaf_id,
                        'slot': 1, 'unchangedBarkSlot': 0, 'unchangedBarkAsset': BARK,
                        'originalLeafAsset': materials[leaf_id]['asset'], 'newLeafAsset': NEW_ASSETS[leaf_id]})
    targets.sort(key=lambda r: r['groupId'])
    require(len(targets) == 23 and sum(r['baseGroup']['instances'] for r in targets) == 78, 'Grove target population differs')
    grove = report['canopyReplacement']
    require(grove['regionId'] == 'village_nearest_grove' and grove['trees'] == 78
            and len(grove['groupIds']) == 23 and set(grove['groupIds']) == {r['groupId'] for r in targets}
            and grove['savedReadback'] == {'status': 'verified-saved-grove-groups', 'groups': 23, 'instances': 78,
                'allNewVisualsNoCollision': True, 'orderedNativeTransformsVerifiedAfterReload': True},
            'Selected groups do not exactly match the saved grove canopy receipt')
    return {'variants': variants, 'targets': targets, 'fullnessMasters': [chosen[k] for k in MESH_IDS],
            'audit': {'originalMaterialGraphs': 42, 'proposedMaterialGraphs': 44, 'textureObjects': 74,
                      'plantStaticMeshes': 135, 'plantLods': 405, 'targetGroups': 23, 'targetInstances': 78,
                      'allExteriorGroups': len(report['geometry']['groups']),
                      'allExteriorInstances': sum(g['instances'] for g in report['geometry']['groups'].values()),
                      'allLevelActors': report['finalActorCount'], 'geometryChanges': 0,
                      'staticMeshSlotChanges': 0, 'newTextureObjects': 0}}


def validate_plan(plan, plan_path=None):
    require(plan.get('schema') == SCHEMA and plan.get('owner') == STUDY_OWNER and plan.get('status') == STATUS,
            'Unapproved overlay plan type/owner/status')
    require(plan.get('nativeAppearanceAccepted') is False and plan.get('fullPhotorealismAccepted') is False
            and plan.get('performanceAccepted') is False, 'Source plan claims native acceptance')
    report_path = check_pin(plan['baseNativeReport'])
    report = read(report_path)
    require(Path(report['output']).resolve() == report_path.parent
            and Path(report['project']).resolve() == report_path.parent / 'Project/BreziTwin', 'Foreign base report')
    require(report_path.parent.name == 'exterior-20261001-r16a', 'Only the selected R16 native base is supported')
    require(plan.get('activeDesign') == report['activeDesign'] and plan.get('setbacksMm') == report['setbacksMm'],
            'Study design or setbacks differ from the saved base')
    require({k: plan[k] for k in ('variants', 'targets', 'fullnessMasters', 'audit')} == canonical_scope(report),
            'Plan broadens/changes the native-derived target or scalar scope')
    content = read(check_pin(plan['baseContentInventory']))
    expected = {Path(k).relative_to(Path(report['project']) / 'Content').as_posix(): v
                for k, v in report['afterAssetHashes'].items()}
    require(set(content) == set(expected) and all(content[k]['sha256'] == v for k, v in expected.items()),
            'Base inventory does not close the actual native report')
    proof = read(check_pin(plan['baseProjectProof']))
    require(any(k.startswith('Binaries/') for k in proof) and 'BreziTwin.uproject' in proof, 'Native project proof incomplete')
    snapshot = read(check_pin(plan['consumedSourceSnapshot']))
    require(snapshot['nativeExitCode'] == 0 and snapshot['allHashesVerified'] is True, 'Unverified consumed source snapshot')
    frozen_root = report_path.parent / 'source-freeze/consumed-native-r1/workspace'
    rows = {r['source']: r for r in snapshot['files']}
    require(set(plan['frozenPipeline']) == set(report['pipelineFiles']), 'Frozen native pipeline coverage differs')
    for original, old_hash in report['pipelineFiles'].items():
        require(original in rows and rows[original]['sha256'] == old_hash, 'Native consumed source pin differs')
        expected_path = frozen_root / Path(original).relative_to(ROOT)
        actual_path = check_pin(plan['frozenPipeline'][original])
        require(actual_path == expected_path and plan['frozenPipeline'][original]['sha256'] == old_hash,
                'Readback helper is not the exact consumed native code')
    require(set(plan['newSourceFiles']) == {'generator', 'nativeHelper', 'tests', 'design'}, 'New source closure differs')
    for entry in plan['newSourceFiles'].values():
        live, frozen = check_pin(entry['live']), check_pin(entry['snapshot'])
        require(entry['live']['sha256'] == entry['snapshot']['sha256'] and live != frozen, 'New source snapshot/live mismatch')
    require(check_pin(plan['newSourceFiles']['nativeHelper']['live']) == Path(__file__).resolve(), 'Foreign native overlay helper')
    engine_fields = {'directFoliageShader', 'indirectFoliageShader', 'editorAssetLibraryHeader',
                     'materialEditingHeader', 'primitiveComponentHeader', 'editorBinary', 'editorModules'}
    require(set(plan['engineEvidence']) == engine_fields, 'Engine evidence closure differs')
    for row in plan['engineEvidence'].values():
        check_pin(row)
    modules = read(check_pin(plan['baseProjectModuleMap']))
    engine_modules = read(check_pin(plan['engineEvidence']['editorModules']))
    require(modules['BuildId'] == engine_modules['BuildId'] == plan['nativeEngineBuildId'], 'Selected Editor BuildId differs')
    module = check_pin(plan['nativeModule'])
    require(module == Path(report['project']) / 'Binaries/Mac' / modules['Modules']['BreziTwin']
            and plan['nativeModule']['sha256'] == '2db3c3ee40be6f0ae459a186fcee36ed9b0248aad7bcd300cb508cc69a9f0574',
            'Selected native Editor recorder module differs')
    tests = read(check_pin(plan['sourceGuardTests']))
    require(tests['status'] == 'passed' and tests['exitCode'] == 0 and tests['nativeExecuted'] is False
            and tests['nativeAppearanceAccepted'] is False, 'Source tests are incomplete or claim native evidence')
    if plan_path:
        require(Path(plan_path).resolve().parent == Path(plan['baseContentInventory']['path']).parent,
                'Plan and typed inventory are in different studies')
    return report, content, proof


def validate_asset_delta(before, after):
    require(set(before) <= set(after), 'Protected Content removed')
    changed = sorted(k for k in before if before[k] != after[k])
    require(changed == [MAP_FILE], 'Content changes exceed the one saved map')
    added = sorted(set(after) - set(before))
    packages = {asset.split('.')[0].removeprefix('/Game/') for asset in NEW_ASSETS.values()}
    require(all(Path(k).suffix in ('.uasset', '.uexp', '.ubulk') and str(Path(k).with_suffix('')) in packages
                for k in added), 'Unexpected asset/namespace addition')
    require({k for k in added if k.endswith('.uasset')} == {p + '.uasset' for p in packages},
            'Exactly two new material packages are required')
    return {'changedFiles': changed, 'newFiles': added, 'protectedFilesByteIdentical': len(before) - 1}


def expected_witness(before, targets):
    result = copy.deepcopy(before)
    changed_components = []
    for target in targets:
        actor = result[target['baseGroup']['actor']]
        candidates = [r for r in actor['components'] if r.get('mesh') == target['baseGroup']['mesh']
                      and r.get('instanceCount') == target['baseGroup']['instances']]
        require(len(candidates) == 1, 'Target HISM witness ambiguous/missing')
        component = candidates[0]
        require(component['materials'] == [target['unchangedBarkAsset'], target['originalLeafAsset']]
                and len(component['overrideMaterials']) <= 2, 'Target effective materials differ')
        require(component['orderedInstanceTransformsSha256'] == target['baseGroup']['transformsSha256'], 'Target transforms differ')
        slot = target['slot']
        old_override = component['overrideMaterials']
        require(all(v is None or v == component['materials'][i] for i, v in enumerate(old_override)),
                'Target has a foreign material override')
        override = old_override + [None] * (slot + 1 - len(old_override))
        override[slot] = target['newLeafAsset']
        component['overrideMaterials'] = override
        component['materials'][slot] = target['newLeafAsset']
        changed_components.append({'groupId': target['groupId'], 'actor': target['baseGroup']['actor'],
                                   'component': component['path'], 'slot': slot,
                                   'before': target['originalLeafAsset'], 'after': target['newLeafAsset'],
                                   'barkSlot0': component['materials'][0]})
    require(len({r['component'] for r in changed_components}) == 23, 'Duplicate target HISM components')
    return result, changed_components


def frozen_modules(plan):
    frozen = Path(plan['frozenPipeline'][str(ROOT / 'scripts/unreal/exterior-import.py')]['path']).parent
    cached = sys.modules.get('performance_scene_policy')
    require(cached is None or Path(cached.__file__).resolve() == frozen / 'performance_scene_policy.py',
            'Another performance policy is already imported')
    old_bytecode = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        def load(name, file):
            spec = importlib.util.spec_from_file_location(name, frozen / file)
            result = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(result)
            return result
        # The importer's ROOT and transitive module paths resolve inside the
        # exact consumed snapshot, not today's working source tree.
        importer = load('transmission_frozen_exterior', 'exterior-import.py')
        materials = load('transmission_frozen_materials', 'exterior-materials.py')
        return importer, materials
    finally:
        sys.dont_write_bytecode = old_bytecode


def native_witness(u, importer):
    actors = u.get_editor_subsystem(u.EditorActorSubsystem)
    rows = importer.helper.witness(importer.base, u, actors)
    for actor in actors.get_all_level_actors():
        row = rows[actor.get_path_name()]
        if isinstance(actor, u.BreziVegetationPatch):
            row['detailDensityScaling'] = bool(actor.get_detail_density_scaling())
        components = {c.get_path_name(): c for c in actor.get_components_by_class(u.SceneComponent)}
        for saved in row['components']:
            c = components[saved['path']]
            if isinstance(c, u.StaticMeshComponent):
                saved['overrideMaterials'] = [m.get_path_name() if m else None for m in c.get_editor_property('override_materials')]
                saved['drawPolicy'] = {key: c.get_editor_property(key) for key in
                    ('min_draw_distance', 'ld_max_draw_distance', 'cached_max_draw_distance', 'bounds_scale')}
                saved['additionalRenderFlags'] = {key: bool(c.get_editor_property(key)) for key in
                    ('cast_dynamic_shadow', 'cast_static_shadow', 'cast_contact_shadow', 'cast_far_shadow',
                     'receives_decals', 'use_as_occluder', 'never_distance_cull')}
            if isinstance(c, u.InstancedStaticMeshComponent):
                saved['instanceCullCm'] = [int(c.get_editor_property(key)) for key in
                    ('instance_start_cull_distance', 'instance_end_cull_distance')]
    return rows


def original_material_readback(u, materials, report):
    graphs = {}
    for key, record in report['materials']['materials'].items():
        asset = u.EditorAssetLibrary.load_asset(record['asset'])
        require(isinstance(asset, u.Material) and asset.get_path_name() == record['asset'], 'Original Material missing: ' + key)
        graph = materials.graph_snapshot(u, asset)
        require(digest(graph) == record['graphSha256'], 'Original graph changed: ' + key)
        require(u.EditorAssetLibrary.get_metadata_tag(asset, 'BreziGeneratedBy') == materials.OWNER
                and u.EditorAssetLibrary.get_metadata_tag(asset, 'BreziExteriorRecipe') == json.dumps(record['recipe'], sort_keys=True),
                'Original Material provenance changed')
        usage = {name: bool(u.MaterialEditingLibrary.has_material_usage(asset, value)) for name, value in
                 [('instancedStaticMeshes', materials.native_enum(u.MaterialUsage, 'INSTANCEDSTATICMESHES')),
                  ('nanite', u.MaterialUsage.MATUSAGE_NANITE)]}
        require(all(usage.values()), 'Original Material usage differs')
        graphs[key] = {'asset': record['asset'], 'graphSha256': digest(graph), 'usage': usage}
    textures = {}
    fields = ('srgb', 'flip_green_channel', 'compression_settings', 'address_x', 'address_y', 'lod_bias',
              'max_texture_size', 'virtual_texture_streaming', 'mip_gen_settings', 'power_of_two_mode',
              'do_scale_mips_for_alpha_coverage', 'never_stream')
    for key, record in report['materials']['textures'].items():
        asset = u.EditorAssetLibrary.load_asset(record['asset'])
        require(isinstance(asset, u.Texture2D) and asset.get_path_name() == record['asset'], 'Original Texture missing')
        values = {}
        for name in fields:
            v = asset.get_editor_property(name)
            values[name] = v if isinstance(v, (int, float, str, bool)) else str(v)
        coverage = asset.get_editor_property('alpha_coverage_thresholds')
        values['alphaCoverageThresholds'] = [float(getattr(coverage, axis)) for axis in 'xyzw']
        values['size'] = [asset.blueprint_get_size_x(), asset.blueprint_get_size_y()]
        values['sourceEncoding'] = str(asset.get_editor_property('source_color_settings').get_editor_property('encoding_override'))
        require(values['size'] == [record['width'], record['height']], 'Original texture dimensions differ')
        metadata = {name: u.EditorAssetLibrary.get_metadata_tag(asset, name) for name in
                    ('BreziGeneratedBy', 'source_sha256', 'BreziSourceLicense', 'BreziSourcePage', 'BreziSourceEncodingOverride')}
        require(metadata['BreziGeneratedBy'] == materials.OWNER and metadata['source_sha256'] == record['sourceSha256']
                and metadata['BreziSourceLicense'] == record['sourceLicense'] and metadata['BreziSourcePage'] == record['sourcePage'],
                'Original Texture provenance changed')
        textures[key] = {'asset': record['asset'], 'values': values, 'metadata': metadata}
    return {'graphs': graphs, 'textures': textures}


def variant_readback(u, materials, plan, plan_hash):
    result = {}
    for key, record in plan['variants'].items():
        asset = u.EditorAssetLibrary.load_asset(record['newAsset'])
        require(isinstance(asset, u.Material) and asset.get_path_name() == record['newAsset'], 'Overlay Material missing')
        graph = materials.graph_snapshot(u, asset)
        require(graph == record['expectedGraph'] and digest(graph) == record['expectedGraphSha256'],
                'Overlay graph delta exceeds the one transmission constant')
        require(u.EditorAssetLibrary.get_metadata_tag(asset, 'BreziGeneratedBy') == OWNER
                and u.EditorAssetLibrary.get_metadata_tag(asset, 'BreziTransmissionPlanSha256') == plan_hash
                and u.EditorAssetLibrary.get_metadata_tag(asset, 'BreziTransmissionOriginalAsset') == record['originalAsset']
                and u.EditorAssetLibrary.get_metadata_tag(asset, 'BreziTransmissionOriginalGraphSha256') == record['originalGraphSha256']
                and u.EditorAssetLibrary.get_metadata_tag(asset, 'BreziExteriorRecipe') == json.dumps(record['proposedRecipe'], sort_keys=True),
                'Overlay provenance missing/different')
        usage = {name: bool(u.MaterialEditingLibrary.has_material_usage(asset, value)) for name, value in
                 [('instancedStaticMeshes', materials.native_enum(u.MaterialUsage, 'INSTANCEDSTATICMESHES')),
                  ('nanite', u.MaterialUsage.MATUSAGE_NANITE)]}
        require(all(usage.values()), 'Duplicated Material usage differs')
        result[key] = {'asset': record['newAsset'], 'graph': graph, 'graphSha256': digest(graph), 'usage': usage}
    return result


def main():
    import unreal as u
    plan_path = Path(os.environ['BREZI_CANOPY_TRANSMISSION_PLAN']).resolve()
    plan_hash = os.environ['BREZI_CANOPY_TRANSMISSION_PLAN_SHA256']
    require(sha(plan_path) == plan_hash, 'Selected plan hash differs')
    plan = read(plan_path)
    report, content_before, project_before = validate_plan(plan, plan_path)
    output = Path(os.environ['BREZI_CANOPY_TRANSMISSION_OUTPUT']).resolve()
    base = Path(report['output'])
    require(output.is_relative_to(ROOT / 'output/unreal') and output.name.startswith('exterior-20261001-r17')
            and output != base and not output.is_relative_to(base), 'Only a new isolated R17 project may be changed')
    project = output / 'Project/BreziTwin'
    require(Path(u.Paths.project_dir()).resolve() == project, 'Wrong running Unreal project')
    require(Path(u.Paths.engine_dir()).resolve() == Path(plan['engineEvidence']['editorModules']['path']).parents[2],
            'Native process is using another engine installation')
    require(not (output / 'exterior-import-report.json').exists(), 'Do not copy/spoof the base exterior report into R17')
    receipt_file = output / 'canopy-transmission-native-report.json'
    require(not receipt_file.exists(), 'Use a fresh overlay candidate; prior receipts are immutable')
    require(inventory(base / 'Project/BreziTwin/Content') == content_before, 'Original R16 Content changed')
    require(project_proof(base / 'Project/BreziTwin') == project_before, 'Original R16 project/module changed')
    require(inventory(project / 'Content') == content_before and project_proof(project) == project_before,
            'R17 must start as exact independent saved R16 project bytes')
    # A hardlink would let saving an asset overwrite the donor.
    for directory, files in [('Content', content_before), ('', project_before)]:
        for relative in files:
            donor = base / 'Project/BreziTwin' / directory / relative
            own = project / directory / relative
            require((donor.stat().st_dev, donor.stat().st_ino) != (own.stat().st_dev, own.stat().st_ino), 'Project clone uses donor hardlinks')
    importer, materials = frozen_modules(plan)
    state = {'schema': SCHEMA, 'owner': OWNER, 'status': 'running', 'startedAt': now(),
             'nativeProcessId': os.getpid(), 'output': str(output), 'project': str(project),
             'baseNativeReport': plan['baseNativeReport'], 'selectedPlan': pin(plan_path),
             'baseContentInventory': plan['baseContentInventory'], 'baseProjectProof': plan['baseProjectProof'],
             'nativeEngineBuildId': plan['nativeEngineBuildId'], 'engineEvidence': plan['engineEvidence'],
             'nativeModuleWitness': {'source': plan['nativeModule']['path'],
                 'destination': str(project / Path(plan['nativeModule']['path']).relative_to(base / 'Project/BreziTwin')),
                 'sha256': plan['nativeModule']['sha256'], 'bytes': plan['nativeModule']['bytes'], 'independentInodes': True},
             'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False,
             'shippingPackageProduced': False, 'scope': 'Saved Editor map and two new full Materials; component-only leaf slot override.'}
    write(receipt_file, state)
    try:
        levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
        require(levels.load_level(MAP), 'Cannot load actual cloned native map')
        state['baseGeometryReadback'] = importer.readback(u, report['geometry'])
        before = native_witness(u, importer)
        require(len(before) == plan['audit']['allLevelActors'], 'Level actor count differs from native R16')
        expected, deltas = expected_witness(before, plan['targets'])
        original_materials = original_material_readback(u, materials, report)
        write(output / 'canopy-transmission-witness-before.json', before)
        write(output / 'canopy-transmission-original-materials-before.json', original_materials)
        assets = u.EditorAssetLibrary
        variants = {}
        for key, record in plan['variants'].items():
            destination = record['newAsset'].split('.')[0]
            require(not assets.does_asset_exist(destination), 'Overlay Material already exists')
            m = assets.duplicate_asset(record['originalAsset'].split('.')[0], destination)
            require(isinstance(m, u.Material), 'Cannot duplicate original full leaf Material')
            require(materials.graph_snapshot(u, m) == report['materials']['materials'][key]['graph'], 'Material duplicate changed original graph')
            nodes = [n for n in u.MaterialEditingLibrary.get_material_expressions(m)
                     if str(n.get_editor_property('desc')) == ROLE]
            require(len(nodes) == 1 and isinstance(nodes[0], u.MaterialExpressionConstant)
                    and float(nodes[0].get_editor_property('r')) == EXPECTED_BASE, 'Native tagged constant changed')
            nodes[0].set_editor_property('r', .24)
            assets.set_metadata_tag(m, 'BreziGeneratedBy', OWNER)
            assets.set_metadata_tag(m, 'BreziTransmissionPlanSha256', plan_hash)
            assets.set_metadata_tag(m, 'BreziTransmissionOriginalAsset', record['originalAsset'])
            assets.set_metadata_tag(m, 'BreziTransmissionOriginalGraphSha256', record['originalGraphSha256'])
            assets.set_metadata_tag(m, 'BreziExteriorRecipe', json.dumps(record['proposedRecipe'], sort_keys=True))
            assets.set_metadata_tag(m, 'BreziTransmissionExperiment', 'Scalar-only 0.08 to 0.24; appearance and performance unaccepted')
            require(not list(u.MaterialEditingLibrary.recompile_material(m) or []), 'Overlay Material shader compiler reported errors')
            require(assets.save_loaded_asset(m, only_if_is_dirty=False), 'Cannot save overlay Material')
            variants[key] = m
        variant_readback(u, materials, plan, plan_hash)
        actors = {a.get_path_name(): a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
        for target in plan['targets']:
            c = actors[target['baseGroup']['actor']].get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
            require(c is not None and c.get_material(1).get_path_name() == target['originalLeafAsset']
                    and c.get_material(0).get_path_name() == BARK, 'Unexpected target pre-override binding')
            c.set_material(1, variants[target['leafMaterialId']])
        require(levels.save_current_level(), 'Cannot save overlay map')
        # The reload proves serialized component overrides. We do not claim an
        # independent package reload: the later fresh Editor-game pilot supplies
        # that separate process evidence for the saved material package bytes.
        variants.clear()
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False), 'Cannot unload overlay map')
        require(levels.load_level(MAP), 'Cannot reload saved overlay map')
        state['savedGeometryReadback'] = importer.readback(u, report['geometry'])
        after = native_witness(u, importer)
        require(after == expected, 'Saved overlay changed protected actor/mesh/transform/light/cull/render/collision/material policy')
        material_after = original_material_readback(u, materials, report)
        require(material_after == original_materials, 'Original 42 graphs/74 texture settings or provenance changed')
        state['variants'] = variant_readback(u, materials, plan, plan_hash)
        content_after = inventory(project / 'Content')
        state['assetDelta'] = validate_asset_delta(content_before, content_after)
        require(project_proof(project) == project_before, 'Overlay changed source/config/binaries/descriptor')
        require(inventory(base / 'Project/BreziTwin/Content') == content_before
                and project_proof(base / 'Project/BreziTwin') == project_before, 'Original R16 donor changed')
        validate_plan(plan, plan_path)
        require(sha(plan_path) == plan_hash, 'Selected plan changed during native execution')
        write(output / 'canopy-transmission-witness-after.json', after)
        write(output / 'canopy-transmission-content-after.json', content_after)
        state.update(status=NATIVE_STATUS, savedMapUnloadedReloaded=True, materialPackagesIndependentlyReloaded=False,
                     componentBindings=deltas, actualAudit=plan['audit'],
                     beforeActorWitnessSha256=digest(before), expectedActorWitnessSha256=digest(expected),
                     savedActorWitnessSha256=digest(after), originalMaterialsWitnessSha256=digest(material_after),
                     effectiveLeafOverrideGroups=23, effectiveLeafOverrideInstances=78, originalR16Unchanged=True,
                     originalContentExceptMapByteIdentical=True, generatedAt=now(),
                     afterContentInventory=pin(output / 'canopy-transmission-content-after.json'),
                     witnessBefore=pin(output / 'canopy-transmission-witness-before.json'),
                     witnessAfter=pin(output / 'canopy-transmission-witness-after.json'),
                     originalMaterialsBefore=pin(output / 'canopy-transmission-original-materials-before.json'),
                     newSourceFiles=plan['newSourceFiles'], frozenPipeline=plan['frozenPipeline'],
                     consumedSourceSnapshot=plan['consumedSourceSnapshot'])
        write(receipt_file, state)
        print(json.dumps({'status': NATIVE_STATUS, 'receipt': pin(receipt_file), 'scope': state['scope'],
                          'appearanceAccepted': False, 'performanceAccepted': False}))
    except Exception as error:
        state.update(status='failed', error=str(error), generatedAt=now())
        write(receipt_file, state)
        raise


if __name__ == '__main__':
    main()
