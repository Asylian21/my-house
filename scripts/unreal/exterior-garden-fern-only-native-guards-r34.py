"""Bounded R34 native binding: actual R29 base,36 ferns,437 raw survivors.

The immutable source plan remains source-only. A separate own native plan binds
the fresh clone and consumed implementation only once those artifacts exist.
"""
import copy
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-fern-only-native-guards-r34.py'
SCHEMA = 'brezi-garden-fern-only-native-r34'
CANDIDATE = ROOT/'output/unreal/exterior-20261002-r34a'
STUDY = ROOT/'output/unreal/exterior-garden-fern-only-20261002-r34-native-study'
PLAN = STUDY/'fern-only-native-plan.json'
PROPOSAL = ROOT/'output/unreal/exterior-garden-fern-only-20261002-r34-study/fern-only-source-plan.json'
PROPOSAL_SHA = '93839661f6b28054521ddf550388b8f2e5daa380fe93406e0c399a6ec807ceb2'
SOURCE_GUARD_SHA = '0b5619ead3c2113f697566049150f0c84db35b662b7106de5dae28eb66f083b2'
CLONE_STATUS = 'verified-original-r29a-independent-apfs-r34-clone-before-fern-only-native'
MATERIAL_READY = ROOT/'output/unreal/exterior-garden-fern-only-20261002-r34-material-source-readiness/source-readiness.json'
MATERIAL_READY_SHA = '5a23c29de7cd4d8d738d66b212112cbea3a9a08c8d51a6a444f62dcfe9c33a4e'


def module(name, path):
    path = Path(path)
    path = path if path.is_absolute() else ROOT/'scripts/unreal'/path
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


source_guard = module('r34_frozen_fern_only_source', 'exterior-garden-fern-only-guards-r34.py')
require, read, sha, pin, digest = (getattr(source_guard, k) for k in ('require', 'read', 'sha', 'pin', 'digest'))
check_pin = source_guard.checked
old_guard = module('r34_frozen_r30_raw_control_predicates', 'exterior-garden-composition-guards-r30-r3.py')
old = old_guard.old
step = old_guard.step
exact = old_guard.exact
expected_control = old_guard.expected_control
swap_remove_order = old_guard.swap_remove_order
expected_original = old_guard.expected_original
PREFIX, TAG = source_guard.PREFIX, source_guard.TAG
COUNTS = {'originalActors': 5351, 'savedActors': 5354, 'fullHismComponents': 2316, 'fullHismInstances': 676957,
          'originalGardenRoots': 473, 'retainedOriginalGardenRoots': 437, 'newOriginalFernRoots': 36,
          'newMeshAssets': 3, 'newMaterialGraphs': 1, 'newTextureObjects': 4, 'newPipelineAssets': 3,
          'newPackages': 11, 'scopedMaterialGraphs': 60, 'scopedTextureObjects': 91,
          'contentFiles': 4071, 'protectedFiles': 132}


def write(path, value):
    with Path(path).open('x') as file:
        json.dump(value, file, indent=2, allow_nan=False)
        file.write('\n')


def source_bundle():
    require(sha(PROPOSAL) == PROPOSAL_SHA and sha(ROOT/source_guard.OWNER) == SOURCE_GUARD_SHA,
            'Frozen fern-only source plan/guard changed')
    plan, ref = source_guard.load_source()
    for key in ('sourceCrownProof', 'materialRecipe', 'sourceLayout', 'producerSnapshot'):
        check_pin(plan[key])
    proof = read(check_pin(plan['sourceCrownProof']))
    require(proof['roots'] == 36 and proof['sourceVerticesChecked'] == 32124
            and proof['historicalNativeMeasurements'] == ref['r30']['newSourceNativeMeasurements']
            and proof['nativeR34Applied'] is proof['nativeR34FrameMeasurementPerformed'] is False,
            'Historical source crown proof must not claim new native measurement')
    recipe = read(check_pin(plan['materialRecipe']))
    require(recipe['schema'] == 'brezi-garden-fern-only-material-recipe-r34'
            and recipe['prefix'] == PREFIX+'/Fern' and recipe['newOwnerTag'] == 'BreziGardenFernOnlyR34:'
            and recipe['sourcePlan'] == ref['source']['recipe']['fernSourceStudy']
            and recipe['sourceDelegate'] == ref['source']['recipe']['fernDelegate']
            and recipe['sourceVariants'] == list(source_guard.MODELS)
            and recipe['privateSourceDelegateKeyMustRemainOriginal'] == 'ph_original_fern_02_b_r25'
            and recipe['originalAlphaMode'] == 'MASK' and recipe['originalDoubleSided'] is True
            and recipe['sourcePixelsEdited'] is False and recipe['nativeR34Applied'] is False
            and recipe['materialCount'] == 1 and recipe['textureObjectCount'] == 4,
            'Only one unchanged original fern atlas recipe allowed')
    source = {'proposal': plan, 'garden': ref['source']['garden'], 'placements': ref['placements'],
              'models': ref['models'], 'recipe': recipe,
              'draft': {'glb': plan['sourceGlb'], 'geometry': plan['geometryDescriptor']}}
    return {'source': source, 'base': ref['base'], 'groups': ref['groups'], 'reference': ref}


def added_expected(template, template_actor, actor, model, mesh, material, measurement):
    row = old.guard.yard.guard.clean.relocate_template(copy.deepcopy(template), template_actor, actor)
    row['label'] = 'R34_'+model
    row['tags'] = sorted(['BreziGenerated', TAG])
    row['detailDensityScaling'] = False
    row['actorTick'] = False
    c = row['components'][0]
    c['mesh'], c['materials'], c['overrideMaterials'] = mesh, [material], []
    c['instanceCount'] = len(measurement['rootIds'])
    c['orderedInstanceTransformsSha256'] = digest(measurement['recoveredValues'])
    return row


def package_paths(models):
    return ([PREFIX+'/Geometry/StaticMeshes/'+r['exportName'] for r in models.values()]
            +[PREFIX+'/Pipeline/'+k for k in ('Assets', 'Materials', 'Level')])


def validate_content(before, after, packages, map_changed=True):
    require(len(before) == 4060 and len(packages) == len(set(packages)) == 11, 'Exactly11 new packages required')
    relative = {p.removeprefix('/Game/')+'.uasset' for p in packages}
    require(all(p.startswith(PREFIX+'/') and '.' not in p.removeprefix(PREFIX+'/') for p in packages)
            and not set(before) & relative and set(after) == set(before) | relative,
            'Only exact R34 owned11 new packages allowed')
    changed = [key for key in before if before[key] != after[key]]
    require(changed == (['Brezi/Maps/Brezi.umap'] if map_changed else []), 'Original file outside own map changed')
    return {'changedOriginalFiles': changed, 'newOwnedPackages': sorted(relative),
            'originalContentFiles': 4060, 'savedContentFiles': 4071, 'newPackages': 11}


def validate_clone(base):
    path = CANDIDATE/'garden-fern-only-project-clone.json'
    c = read(path)
    project = CANDIDATE/'Project/BreziTwin'
    require(c['schema'] == SCHEMA and c['status'] == CLONE_STATUS
            and c['sourceProject'] == str(base['project']) and c['project'] == str(project)
            and c['nativeBaseReport'] == base['reportPin'] and c['sourceProposal'] == pin(PROPOSAL)
            and c['selectedPlan'] is None and c['nativeExecuted'] is False
            and c['fileCount'] == len(c['files']) == 4192 and c['contentFiles'] == 4060 and c['protectedFiles'] == 132,
            'Typed independent original R29 clone required')
    expected = {'Content/'+k: v for k, v in base['content'].items()}
    expected.update(base['protected'])
    seen = set()
    for row in c['files']:
        a, b = Path(row['source']), Path(row['destination'])
        relative = b.relative_to(project).as_posix()
        require(relative in expected and relative not in seen and a == base['project']/relative
                and row['independentInodes'] is True
                and {k: row[k] for k in ('sha256', 'bytes')} == expected[relative]
                and a.stat().st_size == b.stat().st_size == row['bytes']
                and (a.stat().st_dev, a.stat().st_ino) != (b.stat().st_dev, b.stat().st_ino),
                'Clone source/relative membership/size/inode differs')
        seen.add(relative)
    require(seen == set(expected), 'Clone exact4192 membership differs')
    return pin(path)


def material_readiness():
    require(sha(MATERIAL_READY) == MATERIAL_READY_SHA, 'Frozen fern-only material readiness differs')
    row = read(MATERIAL_READY)
    require(row['status'] == 'source-one-original-fern-owned-material-ready-native-pending'
            and row['owner'] == 'scripts/unreal/exterior-garden-fern-only-materials-r34.py'
            and row['sourceInputsUnchanged'] is True
            and row['inputFilesBefore'] == row['inputFilesAfter'] and len(row['inputFilesBefore']) == 23
            and row['tests']['cases'] == 6 and row['tests']['exitCode'] == 0
            and row['materialCount'] == 1 and row['textureObjectCount'] == 4
            and row['expectedNewPackageAssets'] == 5 and row['nativeExecuted'] is False,
            'Exact source-only material tests and original four-map closure required')
    for path, value in row['inputFilesBefore'].items():
        require(sha(path) == value, 'Frozen original material source differs')
    check_pin(row['tests']['log'])
    return row


def validate_plan():
    bundle = source_bundle()
    p, source, base = read(PLAN), bundle['source'], bundle['base']
    require(p['schema'] == SCHEMA and p['schemaVersion'] == 1
            and p['owner'] == 'scripts/unreal/exterior-garden-fern-only-native-study-r34.py'
            and p['status'] == 'source-ready-actual-r29-base-36-ferns-all-ornamentals-retained-native-pending'
            and p['sourceProposal'] == pin(PROPOSAL) and p['baseNativeReport'] == base['reportPin']
            and p['baseNativeProcess'] == base['process'] and p['baseCurrentByteAudit'] == base['audit']
            and p['candidateOutput'] == str(CANDIDATE) and p['projectClone'] == validate_clone(base)
            and p['expectedCounts'] == COUNTS and p['newGroupOrder'] == list(source_guard.MODELS)
            and p['retiredRootIds'] == [r['rootId'] for r in source['placements']]
            and p['wholeOneMemberHeroGroupRetirements'] == []
            and p['activeDesign'] == source['proposal']['activeDesign']
            and p['setbacksMm'] == {'street': 3000, 'east': 3000}
            and p['nativeExecutionRequirements'] == source['proposal']['nativeExecutionRequirements']
            and p['futureYardIntegration'] == source['proposal']['futureYardIntegration'], 'Exact actual-base source binding required')
    require(p['originalGardenGroupBindings'] == {key: {x: v[x] for x in ('actor', 'component', 'oldMesh')}
            for key, v in bundle['groups'].items()}, 'Actual19 original garden groups differ')
    material_readiness()
    require(p['materialReadiness'] == pin(MATERIAL_READY), 'Source-only material readiness binding differs')
    names = {'exterior-garden-fern-only-native-study-r34.py', 'exterior-garden-fern-only-native-guards-r34.py',
             'exterior-garden-fern-only-native-r34.py', 'exterior-garden-fern-only-materials-r34.py',
             'test_exterior_garden_fern_only_native_r34.py'}
    require(set(p['ownedSources']) == names, 'Exact five consumed own native sources required')
    for name, row in p['ownedSources'].items():
        require(Path(row['path']) == ROOT/'scripts/unreal'/name, 'Known own native source path required')
        check_pin(row)
    for path, value in p['inputFiles'].items():
        require(sha(path) == value, 'Consumed original/native source changed')
    for key in ('nativeApplied', 'nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted', 'shippingVerified', 'packageVerified'):
        require(p[key] is False, 'Source binding fabricates acceptance')
    return p, bundle
