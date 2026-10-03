"""R19: exact component-only meadow/ecology visibility overlay.

Importable CPU guards; Unreal is imported only by main. Only the root may run
main in a fresh independent clone of the saved original R16 project.
"""
import copy
import importlib.util
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-meadow-visibility-native.py'
STUDY_OWNER = 'scripts/unreal/exterior-meadow-visibility-study.py'
SCHEMA = 'brezi-meadow-ecology-visibility-component-overlay-r1'
STATUS = 'source-only-meadow-ecology-visibility-native-trial-pending'
NATIVE_STATUS = 'verified-saved-meadow-ecology-visibility-component-overlay'
BASE = ROOT / 'output/unreal/exterior-20261001-r16a'
EVIDENCE_PLAN = ROOT / 'output/unreal/exterior-canopy-transmission-20261001-r1-study/canopy-transmission-plan.json'
EVIDENCE_PLAN_SHA = '2f9032afd061b5681844911959fb9247af8a1197a2c8cded78f1ee5cdbcd0ccb'
SHARED = ROOT / 'scripts/unreal/exterior-canopy-transmission-native.py'
SHARED_SHA = '10cc942f098e130f8f22f0acb9948f4381bdc0226d5db2af17a4665fd701bc6b'
MAP = '/Game/Brezi/Maps/Brezi'
MAP_FILE = 'Brezi/Maps/Brezi.umap'
PROPOSED = [18000, 24000]
ECOLOGY_IDS = tuple('canopy_ecology_' + family + '_' + str(i)
                    for family, count in (('litter', 3), ('twig', 3), ('herb', 3), ('grass', 2))
                    for i in range(count))


def load_shared():
    # This exact immutable helper supplies generic byte/actor/material proofs.
    # Its transmission mutation/main is never called by this experiment.
    old = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec = importlib.util.spec_from_file_location('visibility_immutable_base_guards', SHARED)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = old
    module.require(module.sha(SHARED) == SHARED_SHA, 'Immutable generic helper changed')
    return module


g = load_shared()
require, read, write, pin, check_pin, sha, digest, now = (
    getattr(g, key) for key in ('require', 'read', 'write', 'pin', 'check_pin', 'sha', 'digest', 'now'))


def canonical_scope(report):
    require(report.get('status') == 'exterior-import-validated' and report.get('savedReloaded') is True,
            'Base must be the actual saved R16 exterior')
    require(report['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}
            and report['setbacksMm'] == {'street': 3000, 'east': 3000}, 'Protected design differs')
    require(len(report['materials']['materials']) == 42 and len(report['materials']['textures']) == 74,
            'Original material population differs')
    plants = report['savedPlantReadback']
    require(len(plants) == 135 and sum(len(p['lodTriangles']) for p in plants) == 405,
            'Original plant library differs')
    prototypes = report['nativeMeadow']['prototypes']
    require(set(prototypes) == {'LawnTuft' + str(i) for i in range(4)}, 'Four exact original tufts required')
    require(all(p['lodScreens'] == [1., .02500000037252903, .007000000216066837]
                and [r['triangles'] for r in p['lodProofs']] == [256, 64, 24]
                for p in prototypes.values()), 'Original tuft LODs differ')
    by_mesh = {p['mesh']: key for key, p in prototypes.items()}
    groups = report['geometry']['groups']
    lawn_ids = {key for key, row in groups.items() if row['mesh'] in by_mesh}
    ecology = report['canopyEcology']
    ecology_ids = ecology['groupIds']
    require(len(ecology_ids) == len(set(ecology_ids)) == 130
            and ecology['regionId'] == 'village_nearest_grove'
            and ecology['savedReadback'] == {'status': 'verified-saved-grove-groups', 'groups': 130,
                'instances': 24773, 'allNewVisualsNoCollision': True,
                'orderedNativeTransformsVerifiedAfterReload': True}, 'Exact saved ecology scope differs')
    ecology_ids = set(ecology_ids)
    require(ecology_ids <= set(groups) and not lawn_ids & ecology_ids, 'Scope overlap/missing groups')
    require(len(lawn_ids) == 471 and sum(groups[k]['instances'] for k in lawn_ids) == 477117,
            'Exact native meadow population differs')
    ecology_masters = {p['mesh']: p for p in plants if p['id'] in ECOLOGY_IDS}
    require({p['id'] for p in ecology_masters.values()} == set(ECOLOGY_IDS),
            'Exact eleven selected ecology masters differ; historical flare meshes are excluded')
    targets = []
    for key in sorted(lawn_ids | ecology_ids):
        row = groups[key]
        require(row['qualityDetail'] is True and type(row['cullStartCm']) is int
                and type(row['cullEndCm']) is int, 'Target native detail/cull schema differs')
        if key in lawn_ids:
            require([row['cullStartCm'], row['cullEndCm']] == [7200, 9000], 'Meadow original culls differ')
            master, family, scope = by_mesh[row['mesh']], 'meadow', 'local-meadow'
        else:
            require(row['mesh'] in ecology_masters, 'Ecology bound to an unrelated mesh')
            master = ecology_masters[row['mesh']]['id']
            family, scope = master.split('_')[2], 'grove-ecology'
            expected_end = {'litter': 8000, 'twig': 10000, 'herb': 12000, 'grass': 10000}[family]
            require([row['cullStartCm'], row['cullEndCm']] == [int(.8 * expected_end), expected_end],
                    'Ecology family original culls differ')
        targets.append({'groupId': key, 'scope': scope, 'family': family, 'masterId': master,
                        'baseGroup': copy.deepcopy(row), 'proposedCullCm': list(PROPOSED)})
    require(sum(groups[k]['instances'] for k in ecology_ids) == 24773, 'Ecology population differs')
    return {'targets': targets, 'scopes': [
        {'id': 'local-meadow', 'groupIds': sorted(lawn_ids), 'groups': 471, 'instances': 477117,
         'originalCullCm': [7200, 9000], 'proposedCullCm': list(PROPOSED),
         'mixedNativeCellScope': 'Original meadow, understory and 15111 yard roots share 20m native cells; all stay intact.'},
        {'id': 'grove-ecology', 'groupIds': sorted(ecology_ids), 'groups': 130, 'instances': 24773,
         'originalCullByFamilyCm': {'litter': [6400, 8000], 'twig': [8000, 10000],
                                   'herb': [9600, 12000], 'grass': [8000, 10000]},
         'proposedCullCm': list(PROPOSED)}],
        'audit': {'targetGroups': 601, 'targetInstances': 501890, 'meadowGroups': 471,
                  'meadowInstances': 477117, 'ecologyGroups': 130, 'ecologyInstances': 24773,
                  'allExteriorGroups': len(groups),
                  'allExteriorInstances': sum(r['instances'] for r in groups.values()),
                  'allLevelActors': report['finalActorCount'], 'materialGraphs': 42, 'textureObjects': 74,
                  'plantStaticMeshes': 135, 'plantLods': 405, 'newAssets': 0,
                  'geometryChanges': 0, 'materialChanges': 0, 'transformChanges': 0}}


def validate_plan(plan, plan_path=None):
    require(plan.get('schema') == SCHEMA and plan.get('owner') == STUDY_OWNER and plan.get('status') == STATUS,
            'Unapproved visibility plan type/owner/status')
    require(all(plan.get(key) is False for key in ('nativeExecuted', 'nativeAppearanceAccepted',
                'fullPhotorealismAccepted', 'performanceAccepted', 'shippingPackageProduced')),
            'Source plan claims native acceptance')
    require(check_pin(plan['reusedBaseEvidencePlan']) == EVIDENCE_PLAN
            and plan['reusedBaseEvidencePlan']['sha256'] == EVIDENCE_PLAN_SHA
            and check_pin(plan['immutableGenericHelper']) == SHARED
            and plan['immutableGenericHelper']['sha256'] == SHARED_SHA, 'Immutable base evidence differs')
    evidence = read(EVIDENCE_PLAN)
    report, content, protected = g.validate_plan(evidence, EVIDENCE_PLAN)
    require(plan['baseNativeReport'] == evidence['baseNativeReport']
            and Path(report['output']).resolve() == BASE, 'Foreign or altered original R16 base')
    require({key: plan[key] for key in ('targets', 'scopes', 'audit')} == canonical_scope(report),
            'Visibility plan broadens exact scopes or changes approved distances')
    require(plan['activeDesign'] == report['activeDesign'] and plan['setbacksMm'] == report['setbacksMm'],
            'Protected placement/design differs')
    require(set(plan['newSourceFiles']) == {'generator', 'nativeHelper', 'tests', 'design'}, 'New source closure differs')
    for entry in plan['newSourceFiles'].values():
        live, frozen = check_pin(entry['live']), check_pin(entry['snapshot'])
        require(live != frozen and entry['live']['sha256'] == entry['snapshot']['sha256'], 'New source snapshot differs')
    require(check_pin(plan['newSourceFiles']['nativeHelper']['live']) == Path(__file__).resolve(), 'Foreign visibility helper')
    for row in plan['diagnosticInputs'].values(): check_pin(row)
    for row in plan['engineEvidence'].values(): check_pin(row)
    diagnostic = read(check_pin(plan['sourceDiagnostic']))
    require(diagnostic['nativeExecuted'] is False and diagnostic['performanceAccepted'] is False
            and diagnostic['selectedPolicyCm'] == PROPOSED, 'Diagnostic misstates evidence or policy')
    tests = read(check_pin(plan['sourceGuardTests']))
    require(tests['status'] == 'passed' and tests['exitCode'] == 0 and tests['nativeExecuted'] is False,
            'Source guard tests did not pass')
    if plan_path:
        require(Path(plan_path).resolve().parent == Path(plan['sourceDiagnostic']['path']).parent,
                'Study sidecars are in another output')
    return report, content, protected, evidence


def validate_asset_delta(before, after):
    require(set(before) == set(after), 'Visibility overlay must not add or remove any Content file')
    changed = sorted(k for k in before if before[k] != after[k])
    require(changed == [MAP_FILE], 'Visibility overlay changed another native asset/data file')
    return {'changedFiles': changed, 'newFiles': [], 'removedFiles': [],
            'protectedFilesByteIdentical': len(before) - 1}


def expected_witness(before, targets):
    result = copy.deepcopy(before)
    deltas = []
    require(len(targets) == len({r['groupId'] for r in targets}) == 601, 'Exact unique 601 targets required')
    for target in targets:
        original = target['baseGroup']
        actor = result[original['actor']]
        candidates = [r for r in actor['components'] if r.get('mesh') == original['mesh']
                      and r.get('instanceCount') == original['instances']]
        require(len(candidates) == 1, 'Target component ambiguous/missing')
        component = candidates[0]
        require(component['class'] == '/Script/Engine.HierarchicalInstancedStaticMeshComponent'
                and component['orderedInstanceTransformsSha256'] == original['transformsSha256']
                and component['instanceCullCm'] == [original['cullStartCm'], original['cullEndCm']]
                and actor['detailDensityScaling'] is True, 'Target pre-mutation native policy differs')
        require(target['proposedCullCm'] == PROPOSED and all(type(v) is int for v in target['proposedCullCm']),
                'Unapproved cull distance')
        component['instanceCullCm'] = list(PROPOSED)
        deltas.append({'groupId': target['groupId'], 'scope': target['scope'], 'family': target['family'],
                       'actor': original['actor'], 'component': component['path'],
                       'beforeCullCm': [original['cullStartCm'], original['cullEndCm']],
                       'afterCullCm': list(PROPOSED), 'instances': original['instances']})
    require(len({d['component'] for d in deltas}) == 601, 'Component targeted twice')
    return result, deltas


def geometry_after(original, targets):
    result = copy.deepcopy(original)
    for target in targets:
        row = result['groups'][target['groupId']]
        require(row == target['baseGroup'], 'Geometry receipt target differs from selected base')
        row['cullStartCm'], row['cullEndCm'] = target['proposedCullCm']
    return result


def main():
    import unreal as u
    plan_path = Path(os.environ['BREZI_MEADOW_VISIBILITY_PLAN']).resolve()
    plan_hash = os.environ['BREZI_MEADOW_VISIBILITY_PLAN_SHA256']
    require(sha(plan_path) == plan_hash, 'Selected visibility plan changed')
    plan = read(plan_path)
    report, content_before, project_before, evidence = validate_plan(plan, plan_path)
    output = Path(os.environ['BREZI_MEADOW_VISIBILITY_OUTPUT']).resolve()
    require(output.is_relative_to(ROOT / 'output/unreal') and output.name.startswith('exterior-20261001-r19')
            and output != BASE and not output.is_relative_to(BASE), 'Only a new isolated R19 may be changed')
    project = output / 'Project/BreziTwin'
    require(Path(u.Paths.project_dir()).resolve() == project, 'Wrong running native project')
    require(Path(u.Paths.engine_dir()).resolve() == Path(evidence['engineEvidence']['editorModules']['path']).parents[2],
            'Another native engine is running')
    require(not (output / 'exterior-import-report.json').exists(), 'Do not copy/spoof the original base report')
    receipt_path = output / 'meadow-visibility-native-report.json'
    require(not receipt_path.exists(), 'Prior native overlay receipts are immutable')
    for original in (BASE / 'Project/BreziTwin', project):
        require(g.inventory(original / 'Content') == content_before and g.project_proof(original) == project_before,
                'Original R16 bytes or fresh independent clone differ')
    for directory, rows in [('Content', content_before), ('', project_before)]:
        for relative in rows:
            donor, own = BASE / 'Project/BreziTwin' / directory / relative, project / directory / relative
            require((donor.stat().st_dev, donor.stat().st_ino) != (own.stat().st_dev, own.stat().st_ino),
                    'Clone uses donor hardlinks')
    importer, materials = g.frozen_modules(evidence)
    state = {'schema': SCHEMA, 'owner': OWNER, 'status': 'running', 'startedAt': now(),
             'nativeProcessId': os.getpid(), 'output': str(output), 'project': str(project),
             'baseNativeReport': plan['baseNativeReport'], 'selectedPlan': pin(plan_path),
             'baseContentInventory': evidence['baseContentInventory'], 'baseProjectProof': evidence['baseProjectProof'],
             'reusedBaseEvidencePlan': plan['reusedBaseEvidencePlan'],
             'immutableGenericHelper': plan['immutableGenericHelper'],
             'nativeEngineBuildId': evidence['nativeEngineBuildId'], 'engineEvidence': evidence['engineEvidence'],
             'nativeModuleWitness': {'source': evidence['nativeModule']['path'],
                 'destination': str(project / Path(evidence['nativeModule']['path']).relative_to(BASE / 'Project/BreziTwin')),
                 'sha256': evidence['nativeModule']['sha256'], 'bytes': evidence['nativeModule']['bytes'],
                 'independentInodes': True},
             'scope': 'Exactly 601 saved HISM distance pairs: 471 local meadow + 130 grove ecology; map only.',
             'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False,
             'performanceAccepted': False, 'shippingPackageProduced': False}
    write(receipt_path, state)
    try:
        levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
        require(levels.load_level(MAP), 'Cannot load actual independent saved R16 map')
        state['baseGeometryReadback'] = importer.readback(u, report['geometry'])
        before = g.native_witness(u, importer)
        require(len(before) == plan['audit']['allLevelActors'], 'Native actor population differs')
        expected, deltas = expected_witness(before, plan['targets'])
        material_before = g.original_material_readback(u, materials, report)
        write(output / 'meadow-visibility-witness-before.json', before)
        write(output / 'meadow-visibility-original-materials-before.json', material_before)
        actors = {a.get_path_name(): a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()}
        component_by_group = {d['groupId']: d['component'] for d in deltas}
        for target in plan['targets']:
            row = target['baseGroup']
            c = actors[row['actor']].get_component_by_class(u.HierarchicalInstancedStaticMeshComponent)
            require(c is not None and c.get_path_name() == component_by_group[target['groupId']]
                    and c.get_instance_count() == row['instances']
                    and c.get_editor_property('static_mesh').get_path_name() == row['mesh']
                    and [c.get_editor_property(k) for k in ('instance_start_cull_distance', 'instance_end_cull_distance')]
                    == [row['cullStartCm'], row['cullEndCm']], 'Target component changed before mutation')
            c.set_cull_distances(*target['proposedCullCm'])
        require(levels.save_current_level(), 'Cannot save visibility map')
        require(u.EditorLoadingAndSavingUtils.new_blank_map(False), 'Cannot unload visibility map')
        require(levels.load_level(MAP), 'Cannot reload serialized visibility map')
        state['savedGeometryReadback'] = importer.readback(u, geometry_after(report['geometry'], plan['targets']))
        after = g.native_witness(u, importer)
        require(after == expected, 'Unexpected actor/model/material/transform/light/density/collision/render-policy change')
        material_after = g.original_material_readback(u, materials, report)
        require(material_after == material_before, 'Original42graphs/74texture settings or provenance changed')
        content_after = g.inventory(project / 'Content')
        state['assetDelta'] = validate_asset_delta(content_before, content_after)
        require(g.project_proof(project) == project_before, 'Config/Source/Binaries/descriptor changed')
        require(g.inventory(BASE / 'Project/BreziTwin/Content') == content_before
                and g.project_proof(BASE / 'Project/BreziTwin') == project_before, 'Original R16 donor changed')
        validate_plan(plan, plan_path)
        require(sha(plan_path) == plan_hash, 'Selected source plan changed during native execution')
        write(output / 'meadow-visibility-witness-after.json', after)
        write(output / 'meadow-visibility-content-after.json', content_after)
        state.update(status=NATIVE_STATUS, savedMapUnloadedReloaded=True,
                     componentCullOverrides=deltas, actualAudit=plan['audit'], scopes=plan['scopes'],
                     beforeActorWitnessSha256=digest(before), expectedActorWitnessSha256=digest(expected),
                     savedActorWitnessSha256=digest(after), originalMaterialsWitnessSha256=digest(material_after),
                     effectiveCullOverrideGroups=601, effectiveCullOverrideInstances=501890,
                     originalR16Unchanged=True, originalContentExceptMapByteIdentical=True,
                     generatedAt=now(), afterContentInventory=pin(output / 'meadow-visibility-content-after.json'),
                     witnessBefore=pin(output / 'meadow-visibility-witness-before.json'),
                     witnessAfter=pin(output / 'meadow-visibility-witness-after.json'),
                     originalMaterialsBefore=pin(output / 'meadow-visibility-original-materials-before.json'),
                     newSourceFiles=plan['newSourceFiles'], frozenPipeline=evidence['frozenPipeline'],
                     consumedSourceSnapshot=evidence['consumedSourceSnapshot'],
                     nearSourceEmptyForegroundFixed=False)
        write(receipt_path, state)
        print(json.dumps({'status': NATIVE_STATUS, 'receipt': pin(receipt_path), 'audit': plan['audit'],
                          'appearanceAccepted': False, 'performanceAccepted': False}))
    except Exception as error:
        state.update(status='failed', error=str(error), generatedAt=now())
        write(receipt_path, state)
        raise


if __name__ == '__main__':
    main()
