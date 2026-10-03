"""CPU-only saved R35 R2 checker. No Unreal boot or fresh native decoding.

Reconstructs the full declared scene from actual R32; checks recorded original
and survivor matrices, all source corner hashes against executed native proof,
and source supports through the recorded native matrices. Appearance is pending.
"""
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-yard-repair-editor-check-r26.py'
HELPER = 'scripts/unreal/exterior-context-yard-repair-native-r35-r2.py'
HELPER_SHA = 'b6727fbd255329c2b8e513df6f32c837fa37ef53e78f4aeb9ff048904ac7ad94'
REPORT_SHA = '22f38c206686040bb8027b2f5cd7abc479ff2749a5edd78cafabed8191ecc7ed'
PLAN_SHA = '866871425239ab51a3cd73086f5627219286b323793eedbc8f1c3fac3815d3e6'
PREFLIGHT_SHA = '279ddd587003c15f0860acecd58ff948cae9689739b53f246f0af9ed11f3afed'
assert hashlib.sha256((ROOT/HELPER).read_bytes()).hexdigest() == HELPER_SHA
s = importlib.util.spec_from_file_location('r26_exact_saved_r35r2_native', ROOT/HELPER)
n = importlib.util.module_from_spec(s)
s.loader.exec_module(n)
g = n.guard
PREFLIGHT = n.PLAN.parent/'source-preflight-r2/source-preflight.json'


def header(r, plan, pf):
    g.require(r['schema'] == n.SCHEMA and r['schemaVersion'] == 1 and r['owner'] == HELPER
              and r['repairSchema'] == n.REPAIR_SCHEMA and r['status'] == n.STATUS
              and r['output'] == str(n.CANDIDATE) and r['project'] == str(n.CANDIDATE/'Project/BreziTwin')
              and r['nativeProcessId'] == 37031, 'Only actual saved successful R35 R2 accepted')
    for key in ('nativeApplied', 'savedMapUnloadedReloaded', 'sourceInputsUnchanged', 'originalSavedR32Unchanged',
                'existingUnrelatedRootsMatricesPoliciesUnchanged', 'allOriginal8949GrassAnd78TreesRawControlsExact',
                'allOriginalGardenRawControlsExact'):
        g.require(r[key] is True, 'Executed saved native proof missing: '+key)
    for key in ('nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted', 'shippingVerified',
                'packageVerified', 'nativeNormalTangentReadbackAvailable', 'materialPackagesIndependentlyUnloaded',
                'AdditionalRandomSeedsReadbackAvailable', 'perInstanceShaderRandomValuePreservationClaimed',
                'sourceGroundElevationSurveyed', 'tallGardenCompositionApplied'):
        g.require(r[key] is False, 'Unsupported acceptance/readback: '+key)
    g.require(r['actualCounts'] == plan['expectedCounts'] == n.COUNTS
              and r['activeDesign'] == plan['activeDesign'] == {'variant':'C','heatingLayout':'B','livingLayout':'B'}
              and r['setbacksMm'] == plan['setbacksMm'] == {'street':3000,'east':3000}, 'Scope/counts/CBB3000 differs')
    g.require(plan['nativeOwner'] == HELPER and plan['repairSchema'] == n.REPAIR_SCHEMA
              and r['priorFailedAttempt'] == plan['priorFailedAttempt']
              and pf['owner'] == HELPER and pf['status'] == 'scoped-yard-repair-source-preflight-validated-native-pending'
              and pf['nativeExecuted'] is False and pf['tests']['exitCode'] == 0, 'Closed R2 preflight/repair type differs')
    for key in ('selectedPlan', 'baseNativeReport', 'projectClone', 'moduleOrderWitness', 'inputFiles'):
        g.require(r[key] == pf[key], 'Executed preflight binding differs: '+key)
    g.require(r['selectedPlan'] == n.pin(n.PLAN) and r['sourcePreflight'] == n.pin(PREFLIGHT)
              and r['sourceProposal'] == plan['sourceProposal'] and r['baseNativeReport'] == plan['baseNativeReport']
              and r['baseNativeProcess'] == plan['baseNativeProcess']
              and len(r['inputFiles']) == 595 and r['inputFiles'][str(ROOT/HELPER)] == HELPER_SHA,
              'Actual consumed source packet differs')


def ecology(r, bundle):
    controls = g.checked(r['originalEcologyControls'])
    retained = g.checked(r['retainedEcologyBeforeSave'])
    saved = g.checked(r['retainedEcologySaved'])
    g.require(set(controls) == set(retained) == set(saved) == set(bundle['ecologyGroups']), 'Exactly8 affected controls required')
    freshness = []
    removals = []
    for key, group in bundle['ecologyGroups'].items():
        control = controls[key]
        g.validate_native_controls(control, group, bundle)
        expected = g.expected_control(control, group['selectedSourceIndices'])
        g.require(retained[key] == saved[key] == expected, 'Only exact original source-index survivors accepted')
        for field in ('recoveredValues', 'storedMatrices', 'customData'):
            g.exact(saved[key][field], expected[field], 'Binary64/signed-zero surviving controls changed')
        freshness.extend(g.native_support_checks(control, group, bundle))
        removals.append({'groupId': key, 'actor': group['actor'],
            'removedOriginalSourceIndices': group['selectedSourceIndices'], 'removedRoots': len(group['selectedSourceIndices']),
            'nativeRemoveAtSwapOrder': g.swap_remove_order(control['instanceCount'], group['selectedSourceIndices']),
            'retainedOriginalSourceOrder': expected['sourceRootIndices'],
            'onlyActualExistingWrappedStructsReordered': True, 'transformOrMatrixRecompositionPerformed': False,
            'seedSetterUsed': False})
    g.require(len(freshness) == 34 and g.checked(r['nativeFreshnessSupport']) == freshness,
              'All34 complete three-LOD supports through recorded native matrices differ')
    a = r['repairA']
    g.require(a['retiredRoots'] == 34 and a['affectedGroups'] == 8 and a['retainedAffectedRoots'] == 1919
              and a['actualRemoveReadback'] == removals and a['freshNativeMatrixAllSourceThreeLodSupportIntersections'] == 34
              and a['AdditionalRandomSeedsReadbackAvailable'] is a['perInstanceShaderRandomValuePreservationClaimed'] is False,
              'Exact native retirement scope differs')
    expected_geometry = n.ecology_expected_geometry(bundle)
    actual = a['nativeSelectedEcologyGeometry']
    g.require(set(actual) == set(expected_geometry), 'All8 actual source ecology masters required')
    triangles = 0
    for model, source in expected_geometry.items():
        wanted = {'asset': source['mesh'], 'materials': source['materials'], 'lods': [],
                  'nativeNormalTangentReadbackAvailable': False, 'freshAllThreeNativeLodsDecoded': True}
        for lod in source['lods']:
            triangles += len(lod['corners'])
            wanted['lods'].append({'level': lod['level'], 'triangles': len(lod['corners']),
                'sourcePrimitives': lod['sourcePrimitives'],
                'nativeOrderedF32PositionUv0Uv1CornersSha256': g.digest(lod['corners']),
                'fullNativeSourcePositionUvTopologyWindingVerified': True})
        g.require(actual[model] == wanted, 'Recorded full native three-LOD P/UV/section/winding receipt differs')
    g.require(triangles == 5220, 'Exact24LOD/5220 triangle census differs')
    bundle['nativeEcologyControls'] = controls
    return controls


def hard_geometry(r, bundle):
    proofs = r['repairB']['hardMeshProofs']
    g.require(set(proofs) == set(r['newMeshes']) == set(bundle['floorRecords']), 'Exactly2 new hard meshes required')
    count = 0
    for key, mesh in bundle['floorRecords'].items():
        corners = bundle['base']['native'].guard.corners(mesh)
        count += len(corners)
        g.require(proofs[key] == {'mesh': r['newMeshes'][key], 'triangles': len(corners),
            'nativeOrderedF32PositionUv0Uv1CornerSha256': g.digest(corners),
            'fullOrderedNativeGeometryVerified': True, 'nativeNormalTangentReadbackAvailable': False},
            'Full recorded hard F32 P/UV0/UV1/winding differs')
    b = r['repairB']
    g.require(count == b['uniqueHardMeshTriangles'] == 4519
              and b['onlySourceHardUv1CoverageRChanged'] is b['allOriginalPositionNormalsIndexUv0Uv1GSourceBytesPreserved'] is True
              and b['nativeNormalsTangentsReadbackAvailable'] is b['sourceCoveragePixelsCausallyProven'] is False,
              'Hard UV1-only source scope/evidence tier differs')


def materials(r, bundle):
    maps = g.module('r26_exact_r35_material_delta', ROOT/'scripts/unreal/exterior-context-yard-repair-materials-r35.py')
    c = r['repairC'];m = c['materialReport'];source = bundle['materialVariant']
    g.require(c['target'] == bundle['backdropTarget'] and c['otherFourteenMaterialComponentsUnchanged'] is True
              and c['wholeComponentScopeNotTinySpatialOverlay'] is True
              and c['nearResponseCoefficientOriginal'] == .30 and c['nearResponseCoefficientProposed'] == .65,
              'Exact one-component backdrop scope differs')
    g.require(m['schema'] == maps.SCHEMA and m['owner'] == maps.OWNER and m['asset'] == maps.ASSET
              and m['originalAsset'] == source['originalAsset'] and m['originalGraphSha256'] == source['originalGraphSha256']
              and m['graph'] == source['proposedGraph'] and m['graphSha256'] == g.digest(m['graph'])
              and m['graphDelta'] == maps.validate_variant(source['originalFullGraph'], m['graph'])
              and m['compileErrors'] == [] and m['newPackageAssets'] == [maps.ASSET]
              and m['newTextureObjects'] == 0 and m['sharedTextureWitness'] == bundle['materialSharedTextures'],
              'Original58-node graph/shared-texture policy outside exact2-code delta')
    old = g.checked(r['originalControlsBefore'])['actualOriginalR32Controls']['observedOldMaterials']['original56']['clean']['original']['graphs']['context_distant_terrain']
    g.require(m['usage'] == old['usage'], 'Original material usage differs')
    g.require(m['worldPositionShaderOffsets'] == {'BreziExterior:world-position':'<WorldPositionIncludedOffsets.WPT_DEFAULT: 0>'},
              'Recorded world-position mode differs from executed unchanged source default')
    for key in ('sourcePixelsEdited', 'materialPackagesIndependentlyUnloaded', 'nativeAppearanceAccepted', 'fullPhotorealismAccepted'):
        g.require(m[key] is False, 'Unsupported material pixel/appearance claim')
    return m['asset']


def old_controls(r, bundle, before):
    a, b = g.checked(r['originalControlsBefore']), g.checked(r['originalControlsSaved'])
    g.require(a == b and set(a) == {'actualOriginalR32Controls', 'all13YardShrubsAnd1274LowRootsRawControls'}, 'Original controls changed')
    g.require(a['actualOriginalR32Controls'] == g.checked(bundle['base']['report']['originalControlsSaved']),
              'Original garden/78tree/8949grass/material controls differ from actual R32')
    rows = a['all13YardShrubsAnd1274LowRootsRawControls']
    g.require(len(rows) == 6 and sum(v['instanceCount'] for v in rows.values()) == 1287, 'All13 shrubs/1274 low roots required')
    for actor, row in rows.items():
        cs = [c for c in before[actor]['components'] if c['class'] == '/Script/Engine.HierarchicalInstancedStaticMeshComponent']
        g.require(len(cs) == 1 and cs[0]['instanceCount'] == row['instanceCount']
                  and cs[0]['orderedInstanceTransformsSha256'] == g.digest(row['recoveredValues'])
                  and row['additionalRandomSeedsReadbackAvailable'] is row['seedRangesReconstructed'] is False, 'Old yard native raw controls unbound')
        for key in ('recoveredValues', 'storedMatrices', 'customData'):
            g.exact(row[key], b['all13YardShrubsAnd1274LowRootsRawControls'][actor][key], 'Old yard binary64 controls changed')


def validate_saved(r, plan, bundle, pf):
    header(r, plan, pf)
    n.validate_plan_header(plan, bundle)
    ecology(r, bundle);hard_geometry(r, bundle);material = materials(r, bundle)
    before = g.checked(r['beforeActorWitness'])
    expected = g.expected_counterfactual(before, bundle, r['newMeshes'], material)
    declared, saved = g.checked(r['expectedActorWitness']), g.checked(r['savedActorWitness'])
    g.require(before == bundle['base']['witness'] and expected == declared == saved,
              'Full5360 independent declared counterfactual differs from actual saved state')
    for key, row in [('beforeActorWitnessSha256', before), ('expectedActorWitnessSha256', expected), ('savedActorWitnessSha256', saved)]:
        g.require(r[key] == g.digest(row), 'Recorded full witness hash differs')
    old_controls(r, bundle, before)
    content = g.checked(r['afterContentInventory'])
    g.require(r['assetDelta'] == g.validate_content(bundle['base']['content'], content, r['newPackages'])
              and g.checked(r['protectedProjectProof']) == bundle['base']['protected'], 'Exact map+6 Content/protected scope differs')
    return {'mode':'saved-r35r2-three-scoped-yard-repairs', 'nativeProcessId':37031,
        'savedActors':5360, 'fullHismComponents':2321, 'fullHismInstances':678197,
        'retiredOriginalEcologyRoots':34, 'retainedAffectedOriginalEcologyRoots':1919,
        'all24NativeEcologyLodRecordedF32CornersVerified':True, 'nativeEcologyTriangles':5220,
        'hardUv1ROnlyTriangles':4519, 'materialGraphs':64, 'textureObjects':95,
        'contentFiles':4092, 'protectedFiles':132, 'newPackages':6,
        'fullActorCounterfactualValidated':True, 'recordedRawControlsPreserved':True,
        'sourceSupportsThroughRecordedActualMatricesChecked':34,
        'freshNativeActorOrGeometryDecodeByCpuChecker':False,
        'AdditionalRandomSeedsReadbackAvailable':False, 'materialPackagesIndependentlyUnloaded':False,
        'nativeNormalTangentReadbackAvailable':False, 'nativeAppearanceAccepted':False,
        'fullPhotorealismAccepted':False, 'performanceAccepted':False, 'shippingVerified':False, 'packageVerified':False}


if __name__ == '__main__':
    path = Path(sys.argv[1]).resolve()
    g.require(path == n.CANDIDATE/n.REPORT and g.sha(path) == REPORT_SHA
              and g.sha(n.PLAN) == PLAN_SHA and g.sha(PREFLIGHT) == PREFLIGHT_SHA, 'Fixed actual report/source pins differ')
    bundle = g.validate_source()
    print(json.dumps(validate_saved(g.read(path), g.read(n.PLAN), bundle, g.read(PREFLIGHT)), allow_nan=False))
