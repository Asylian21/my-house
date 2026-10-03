"""CPU-only check of the actual saved R27 four-donor scene, never an engine run."""
import copy
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-realism-clean-integration-editor-check-r13.py'
HELPER = 'scripts/unreal/exterior-realism-clean-integration-native-r27.py'
HELPER_SHA = '2cdc51b8ebf6007f1493b06df969c3e04a1ec650b797897ebe2b18d9993ac8cc'
s = importlib.util.spec_from_file_location('r13_exact_saved_r27_native', ROOT / HELPER)
n = importlib.util.module_from_spec(s)
s.loader.exec_module(n)
g = n.guard


def validate_saved(r, plan, bundle):
    require = n.require
    donors = bundle['reports']
    read = lambda key: n.read(n.check_pin(r[key]))
    require(r['schema'] == g.SCHEMA and r['owner'] == HELPER and r['status'] == n.STATUS
            and r['selectedPlan'] == n.pin(g.PLAN) and r['savedDonors'] == plan['donors'],
            'Only the known saved R27 composition is eligible')
    require(r['output'] == str(g.CANDIDATE) and r['project'] == str(g.CANDIDATE / 'Project/BreziTwin')
            and r['inputFiles'] == plan['inputFiles'] and r['ownedSources'] == plan['ownedSources']
            and r['baseNativeReport'] == plan['baseNativeReport'], 'Own project/source identity differs')
    for key in ('nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted',
                'shippingPackageProduced', 'nativeMaterialPackagesIndependentlyReloaded',
                'nativeMeshPackagesIndependentlyReloaded', 'nativeNormalTangentReadbackAvailable',
                'originalExteriorOwnershipSpoofed', 'originalGrassMemberMutationApisCalled', 'seedRangeMutationApisCalled'):
        require(r[key] is False, 'Unsupported claim/mutation: ' + key)
    for key in ('savedMapUnloadedReloaded', 'originalR16Unchanged', 'sourceInputsUnchanged',
                'donorFilesNeverMutated', 'originalGrassRawMatricesAndObservedSeedControlsExact'):
        require(r[key] is True, 'Saved/source preservation proof missing: ' + key)
    require(r['activeDesign'] == bundle['base']['activeDesign'] and r['setbacksMm'] == bundle['base']['setbacksMm']
            and r['actualAudit'] == plan['audit'] == g.EXPECTED and r['scopeAudit'] == plan['scopeAudit']
            and r['knownReviewLimits'] == plan['knownReviewLimits']
            and r['combinedAppearanceGoNoGo'] == plan['combinedAppearanceGoNoGo']
            and r['excludedDonors'] == plan['excludedDonors'] == ['R20_CURVED_GRASS', 'R23_CREAM_ROOF'],
            'Design/scope/exclusion/review limits differ')
    policy_pin = bundle['evidence']['frozenPipeline'][str(ROOT / 'scripts/unreal/performance_scene_policy.py')]
    require(r['moduleOrderWitness'] == {**policy_pin, 'cachePreservedAcrossReusedHelpers': True,
                                      'cacheDeletedOrReplaced': False}, 'Frozen-first policy witness differs')

    before, declared, saved = (read(k) for k in ('beforeActorWitness', 'expectedActorWitness', 'savedActorWitness'))
    require(before == bundle['before'] and len(before) == 5306, 'Complete original 5306 actor witness differs')
    neighbor, foreground = r['newNeighborActors'], r['newForegroundActors']
    require(set(neighbor) == set(donors['neighbors']['addedActors']) and len(neighbor) == 32
            and set(foreground) == set(donors['foreground']['addedActors']) and len(foreground) == 5,
            'Exact 32 neighbor plus five foreground identities required')
    added = {**{'neighbors:' + k: v for k, v in neighbor.items()},
             **{'foreground:' + k: v for k, v in foreground.items()}}
    require(r['addedActorIdentityMap'] == added, 'Added identity map differs')
    expected = g.compose_all_expected(bundle['expectedOriginal'], bundle['templates'], added)
    require(declared == expected == saved and len(saved) == 5343,
            'Saved full actor state differs from the explicit field-only counterfactual')
    require([r[k] for k in ('beforeActorWitnessSha256', 'expectedActorWitnessSha256', 'savedActorWitnessSha256')]
            == [n.digest(v) for v in (before, expected, saved)], 'Complete actor canonical digests differ')
    require(r['leafComponentBindings'] == donors['leaf']['componentBindings']
            and r['neighborChanges'] == donors['neighbors']['componentChanges'], 'Leaf/neighbor component scope differs')
    culls = []
    for delta in donors['visibility']['componentCullOverrides']:
        row = copy.deepcopy(delta)
        row['retainedInstances'] = g.component(bundle['expectedOriginal'], row['actor'], row['component'])['instanceCount']
        culls.append(row)
    require(r['componentCullOverrides'] == culls and len(culls) == 601
            and sum(x['retainedInstances'] for x in culls) == 501890,
            'The original 601 cull groups must retain all 501890 instances')
    require(g.verify_grass_preservation(before, bundle['expectedOriginal'], bundle['base']) == plan['preservedGrassGroups'],
            'Original four grass group ordered transforms/policies differ')
    controls = read('originalGrassControlsBefore')
    require(controls == read('originalGrassControlsSaved') and set(controls) == set(g.GRASS_GROUPS),
            'Original raw matrix/main seed/custom-data records changed after save')
    for identity, count in g.GRASS_GROUPS.items():
        row = controls[identity]
        require(row['actor'] == bundle['base']['geometry']['groups'][identity]['actor'] and row['instances'] == count
                and len(row['rawMatrixBinary64Sha256']) == 64 and len(row['customDataSha256']) == 64
                and type(row['instancingRandomSeed']) is int and type(row['numCustomDataFloats']) is int
                and row['originalMemberMutationApisCalled'] is False and row['seedRangeMutationApisCalled'] is False,
                'Original grass raw/control scope differs')
        ranges = row['additionalRandomSeeds']
        require(ranges['available'] is False and ranges['rangeValuesObserved'] is False
                and ranges['rangePreservationClaimed'] is False and 'protected' in ranges['error'],
                'Protected additional seed ranges must remain explicitly unavailable')

    require(r['neighborReadback'] == donors['neighbors']['savedReadback'],
            'Copied 37 neighbor F32/source/default-material proofs differ')
    floor = copy.deepcopy(donors['foreground']['savedReadback'])
    for row in floor['groups']:
        require(row['actor'] == donors['foreground']['addedActors'][row['id']], 'Original foreground identity differs')
        row['actor'] = foreground[row['id']]
    require(r['foregroundReadback'] == floor and floor['savedGroups'] == 4 and floor['savedInstances'] == 512
            and floor['floor']['triangles'] == 1843 and floor['floor']['nativeNormalTangentReadbackAvailable'] is False,
            'Foreground F32 floor/graph/four-group/512-source-transform proof differs')
    require(read('originalGeometryAfter') == bundle['originalGeometryAfter']
            and r['baseGeometryReadback'] == donors['leaf']['baseGeometryReadback']
            and r['savedOriginalGeometryReadback'] == {'meshCount': 547, 'groupCount': 1980, 'instanceCount': 632026,
                                                     'allNewVisualsNoCollision': True},
            'Genuine original exterior ownership/geometry proof differs')
    hisms = [c for row in saved.values() for c in row['components']
             if c['class'] == '/Script/Engine.HierarchicalInstancedStaticMeshComponent']
    require(len(hisms) == r['actualFullSceneHismComponents'] == 2309
            and sum(c['instanceCount'] for c in hisms) == r['actualFullSceneHismInstances'] == 676944
            and r['actualRecordedExteriorHismGroups'] == 1984 and r['actualRecordedExteriorHismInstances'] == 632538,
            'Full-scene versus recorded exterior census differs')
    original = n.read(n.check_pin(donors['leaf']['originalMaterialsBefore']))
    material_paths = {row['asset'] for row in original['graphs'].values()} | {row['asset'] for row in donors['leaf']['variants'].values()} \
        | {row['asset'] for row in donors['neighbors']['materials']['materials'].values()} | {donors['foreground']['newMaterial']['asset']}
    texture_paths = {row['asset'] for row in original['textures'].values()} \
        | {row['asset'] for row in donors['neighbors']['materials']['textures'].values()}
    material_expected = {'original': original, 'leaf': donors['leaf']['variants'], 'neighbor': donors['neighbors']['materials'],
                         'foreground': donors['foreground']['newMaterial'], 'scopedMaterialGraphs': 54, 'scopedTextureObjects': 77,
                         'verifiedMaterialAssets': sorted(material_paths), 'verifiedTextureAssets': sorted(texture_paths)}
    require(read('materialsBefore') == read('materialsSaved') == material_expected
            and len(material_paths) == r['scopedMaterialGraphs'] == 54 and len(texture_paths) == r['scopedTextureObjects'] == 77,
            'Exact original42/74 plus admitted copied graph/texture set differs')
    delta = g.validate_content(bundle['content'], read('afterContentInventory'), bundle['packages'], plan['diagnosticViewpoints']['sha256'])
    require(r['assetDelta'] == delta and r['protectedProjectProof'] == plan['baseProjectProof']
            and r['originalPlantMastersPreserved'] == 135 and r['originalPlantLodsPreserved'] == 405,
            'Content/plant preservation proof differs')
    require(r['diagnosticViewpoints'] == n.pin(Path(r['project']) / 'Content/Data/viewpoints.json')
            and r['diagnosticViewpoints']['sha256'] == plan['diagnosticViewpoints']['sha256'],
            'Exact original camera prefix plus R18 diagnostic differs')
    return {'mode': 'saved-four-donor-clean-exterior-realism-integration', 'nativeProcessId': r['nativeProcessId'],
            'originalActors': 5306, 'savedActors': 5343, 'newActors': 37, 'copiedNewPackages': 59, 'contentFiles': 4034,
            'fullSceneHismComponents': 2309, 'fullSceneHismInstances': 676944, 'recordedExteriorHismGroups': 1984,
            'recordedExteriorHismInstances': 632538, 'leafGroups': 23, 'leafInstances': 78, 'visibilityGroups': 601,
            'retainedVisibilityInstances': 501890, 'originalGrassGroupsPreserved': 4, 'originalGrassMembersPreserved': 8949,
            'grassMemberMutations': 0, 'grassSeedRangeMutations': 0, 'additionalGrassSeedRangesReadbackAvailable': False,
            'foregroundRoots': 512, 'foregroundFloorTriangles': 1843, 'neighborAddedActors': 32, 'roofPbrComponentOverrides': 0,
            'scopedMaterialGraphs': 54, 'scopedTextureObjects': 77, 'wholeActorCounterfactualValidated': True,
            'executedSavedGeometryReceiptMatchesExactSourceDonors': True, 'nativeNormalTangentReadbackAvailable': False,
            'materialAndMeshPackagesIndependentlyReloaded': False, 'nativeAppearanceAccepted': False,
            'performanceAccepted': False, 'fullPhotorealismAccepted': False, 'shippingPackageProduced': False,
            'excludedDonors': plan['excludedDonors'], 'combinedAppearanceGoNoGo': plan['combinedAppearanceGoNoGo'],
            'knownReviewLimits': plan['knownReviewLimits']}


def main():
    n.require(n.sha(ROOT / HELPER) == HELPER_SHA, 'Frozen R27 helper changed')
    report_path = Path(sys.argv[1]).resolve()
    n.require(report_path == g.CANDIDATE / n.REPORT, 'Only own actual saved R27 report eligible')
    plan, bundle = g.validate_plan()
    summary = validate_saved(n.read(report_path), plan, bundle)
    g.actual_terminal(report_path, report_path.parent / 'realism-clean-integration-native-process.json', HELPER,
                      'realism-clean-integration-native')
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
