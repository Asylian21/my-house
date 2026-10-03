"""CPU actual saved R34 source/whole-actor/geometry/control receipt decoder.

No fresh engine getters or GPU are invoked. The executed native saved-matrix
gate remains distinct from the source-matrix sidecar and saved component hash.
"""
import argparse
import copy
import importlib.util
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-fern-only-editor-check-r24.py'
s = importlib.util.spec_from_file_location('r24_saved_fern_source_guards', ROOT/'scripts/unreal/exterior-garden-fern-only-native-guards-r34.py')
g = importlib.util.module_from_spec(s)
s.loader.exec_module(g)
REPORT = g.CANDIDATE/'garden-fern-only-native-report.json'
REPORT_SHA = 'd233329bee2ffcb95419c8266ff8c1f50931ba8f642ded23ab20330f1d334cb8'
PREFLIGHT_SHA = 'c576a977777ef33af745840dbdf734d34168816683c0ed199c9d7c9a920366f2'
PLAN_SHA = 'bc8227ee4c84be48b4859fb9b5ad47f8df390c889e0aa07933dd8df784c15b31'


def validate_header(r):
    g.require(r['schema'] == g.SCHEMA and r['schemaVersion'] == 1
        and r['owner'] == 'scripts/unreal/exterior-garden-fern-only-native-r34.py'
        and r['status'] == 'verified-saved-36-original-fern-garden-all-ornamentals-retained'
        and r['nativeProcessId'] == 21209 and r['output'] == str(g.CANDIDATE)
        and r['project'] == str(g.CANDIDATE/'Project/BreziTwin'), 'Only actual successful saved R34 receipt accepted')
    true = ('nativeApplied', 'savedMapUnloadedReloaded', 'sourceInputsUnchanged', 'originalSavedR29Unchanged',
        'originalGarden437RawMatricesOrderMainSeedCustomDataExact', 'allOriginal12OrnamentalActorsAndMembersUnchanged',
        'allOriginal41FlowersUnchanged', 'remaining384OriginalLowStarsUnchanged', 'original8949GrassRawControlsExact',
        'allOriginal78TreeRawControlsExact', 'allOriginalGroveActorsFullWitnessExact', 'sourceHeightRoleChanges36Explicit')
    false = ('nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted', 'shippingVerified', 'packageVerified',
        'ecologicalFitVerified', 'surveyedPlacementVerified', 'nativeNormalTangentReadbackAvailable',
        'meshMaterialPackagesIndependentlyUnloaded', 'AdditionalRandomSeedsReadbackAvailable', 'retainedTransformRecompositionPerformed',
        'seedMutationPerformed', 'perInstanceShaderRandomValuePreservationClaimed', 'sourceGroundElevationSurveyed', 'yardIntegrationApplied')
    g.require(all(r[k] is True for k in true) and all(r[k] is False for k in false), 'Native limits/retained source scope overstated')
    g.require(r['actualCounts'] == g.COUNTS and r['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}
        and r['setbacksMm'] == {'street': 3000, 'east': 3000} and r['wholeOneMemberHeroRetirements'] == []
        and r['uniqueSourceTriangles'] == 3848 and r['instancedSourceTriangles'] == 46176,
        'Exact36/437 counts/design/original hero scope required')


def side(row):
    return g.read(g.check_pin(row))


def validate_saved(r, plan, bundle, preflight):
    validate_header(r)
    source, base, groups = bundle['source'], bundle['base'], bundle['groups']
    g.require(r['selectedPlan'] == g.pin(g.PLAN) and r['selectedPlan']['sha256'] == PLAN_SHA
        and r['sourceProposal'] == g.pin(g.PROPOSAL) and r['sourcePreflight']['sha256'] == PREFLIGHT_SHA
        and r['baseNativeReport'] == base['reportPin'] and r['baseNativeProcess'] == base['process']
        and r['baseCurrentByteAudit'] == base['audit'] and r['projectClone'] == plan['projectClone'] == preflight['projectClone']
        and r['sourceGeometryDescriptor'] == source['proposal']['geometryDescriptor'], 'Actual selected source/base/initial clone differs')
    g.require(plan['sourceProposal'] == r['sourceProposal'] and plan['expectedCounts'] == g.COUNTS
        and plan['wholeOneMemberHeroGroupRetirements'] == [] and plan['nativeApplied'] is False
        and preflight['owner'] == r['owner'] and preflight['schemaVersion'] == 1
        and preflight['status'] == 'source-preflight-validated-36-ferns-original-ornamentals-retained-native-pending'
        and preflight['nativeExecuted'] is False and preflight['selectedPlan'] == r['selectedPlan']
        and preflight['tests']['exitCode'] == 0 and preflight['tests']['testCount'] == 10
        and preflight['expectedCounts'] == g.COUNTS and r['inputFiles'] == preflight['inputFiles']
        and len(r['inputFiles']) == 453, 'Exact source-only preflight/native receipt closure required')
    for path, value in r['inputFiles'].items():
        g.require(g.sha(path) == value, 'Frozen consumed source differs')
    g.check_pin(preflight['tests']['log'])
    g.require(r['moduleOrderWitness'] == preflight['moduleOrderWitness']
        and r['stepProjectionPolicy'] == preflight['stepProjectionPolicy'] == g.step.POLICY, 'Executed frozen-first/112-step-edge policy differs')
    before, declared, saved = (side(r[k]) for k in ('beforeActorWitness', 'expectedActorWitness', 'savedActorWitness'))
    g.require(before == base['witness'] and len(before) == 5351, 'All5351 original actors not bound to saved R29')
    for k, value in (('beforeActorWitnessSha256', before), ('expectedActorWitnessSha256', declared), ('savedActorWitnessSha256', saved)):
        g.require(r[k] == g.digest(value), 'Full actor witness hash differs')
    original = side(r['originalGardenControls'])
    g.require(original == bundle['reference']['controls'], 'Actual19 original garden components/473 raw frames not bound to R29')
    retained = g.source_guard.retained_controls(bundle['reference'])
    g.require(side(r['retainedGardenControlsBeforeSave']) == side(r['retainedGardenControlsSaved']) == retained,
        '437 survivors raw matrices/recovered order/mainseed/custom data differ')
    expected = g.expected_original(before, groups, original, source['proposal'])
    byid = {identity: (actor, i) for actor, control in original.items() for i, identity in enumerate(control['rootIds'])}
    measurements = side(r['newSourceNativeMeasurements'])
    g.require(list(measurements) == list(g.source_guard.MODELS) == list(r['newOwnedGroups']) == list(r['nativeGeometryReadback']), 'Only exact3 fern forms required')
    materials = r['materialReport']
    maps = g.module('r24_cpu_owned_fern_material_graph', 'exterior-garden-fern-only-materials-r34.py')
    maps.validate_recipe(source['recipe'])
    g.require(materials['schema'] == maps.SCHEMA and materials['owner'] == maps.OWNER
        and materials['recipe'] == source['recipe'] and materials['sourceRecipe'] == g.pin(maps.RECIPE)
        and materials['materialCount'] == 1 and materials['textureObjectCount'] == 4
        and materials['newPackageAssets'] == maps._package_assets(materials['delegate']), 'One original atlas graph/four maps receipt differs')
    maps._graph(materials['delegate'])
    for k in ('sourcePixelsEdited', 'nativeImportedPixelsDecoded', 'nativeSourcePixelFormatReadbackAvailable', 'nativeGpuPixelFormatReadbackAvailable',
              'nativeNormalTangentReadbackAvailable', 'materialPackagesIndependentlyUnloaded', 'nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted'):
        g.require(materials[k] is False, 'Material source/native evidence overstated')
    for index, model in enumerate(g.source_guard.MODELS):
        m, row, desc = measurements[model], r['newOwnedGroups'][model], source['models'][model]
        fits = [p for p in source['placements'] if p['model'] == model]
        g.require(row['rootIds'] == m['rootIds'] == [p['rootId'] for p in fits] and len(fits) == row['instances'] == 12
            and row['actor'] == '/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.BreziVegetationPatch_'+str(2313+index)
            and row['mesh'] == g.PREFIX+'/Geometry/StaticMeshes/'+desc['exportName']+'.'+desc['exportName']
            and row['material'] == materials['asset'], 'Exact saved12-root own fern component identity differs')
        g.require(len(m['inputValues']) == len(m['recoveredValues']) == len(m['storedMatrices']) == 12
            and m['actualUnregisteredMeshlessTransientMeasurement'] is True and m['wrappedOriginalXYZAndRotationCopied'] is True
            and m['hostQuaternionReconstructionPerformed'] is False and m['sourceUniformScaleAssigned'] is True,
            'Faithful wrapped-frame source measurement required')
        for fit, value, recovered, matrix in zip(fits, m['inputValues'], m['recoveredValues'], m['storedMatrices']):
            actor, i = byid[fit['rootId']]
            old = original[actor]['recoveredValues'][i]
            g.exact(value, [old[0], old[1], fit['scale']], 'Wrapped original XYZ/quaternion/input scale differs')
            g.exact(recovered[0], old[0], 'Measured old root/contact differs')
            g.exact(matrix[3][:3], old[0], 'Stored original translation differs')
        old_group = next(v for v in groups.values() if fits[0]['rootId'] in [p['id'] for p in v['rows']])
        expected[row['actor']] = g.added_expected(old_group['witness'], old_group['actor'], row['actor'], model, row['mesh'], row['material'], m)
        proof = r['nativeGeometryReadback'][model]
        def cyclic(face): return min(tuple(face[i:]+face[:i]) for i in range(3))
        corners = [cyclic([tuple(desc['expectedNativeVerticesCm'][i]+desc['uv0'][i]) for i in desc['indices'][j:j+3]]) for j in range(0, len(desc['indices']), 3)]
        g.require(proof['asset'] == row['mesh'] and proof['lodCount'] == proof['sections'] == 1
            and proof['triangles'] == desc['triangles'] and proof['nativeCornerSha256'] == g.digest(corners)
            and proof['fullOrderedNativeF32PositionUV0WindingVerified'] is True and proof['sourceNormalBytesPreserved'] is True
            and proof['nativeTangentsRequestedFromOriginalUv'] is True, 'Full3848 actual ordered native F32 P/UV0 source proof differs')
        for k in ('originalProviderLodChainPresent', 'sourceTangentsPresent', 'nativeTangentGenerationNumericallyVerified',
                  'nativeNormalTangentReadbackAvailable', 'nativeNaniteRequested', 'meshPackageIndependentlyUnloaded'):
            g.require(proof[k] is False, 'Geometry native/tangent evidence overstated')
    g.require(expected == declared == saved and len(saved) == 5354, 'Whole5354 strict actor counterfactual differs')
    hisms = [c for a in saved.values() for c in a['components'] if c['class'] == '/Script/Engine.HierarchicalInstancedStaticMeshComponent']
    g.require(len(hisms) == 2316 and sum(c['instanceCount'] for c in hisms) == 676957, 'Whole scene HISM census differs')
    heroes = source['garden']['ornamentalPlacements']
    hero_actors = {byid[p['id']][0] for p in heroes}
    g.require(len(heroes) == 12 and all(before[a] == saved[a] for a in hero_actors), 'Any original ornamental actor/member changed')
    for before_key, after_key in (('originalTreesBefore', 'originalTreesSaved'), ('originalGrassBefore', 'originalGrassSaved'), ('originalMaterialsBefore', 'originalMaterialsSaved')):
        g.require(side(r[before_key]) == side(r[after_key]), 'Original tree/grass/material observed controls differ')
    g.require(side(r['originalMaterialsSaved'])['scopedMaterialGraphs'] == 59
        and side(r['originalMaterialsSaved'])['scopedTextureObjects'] == 87, 'Original59/87 material scope differs')
    native = g.module('r24_cpu_matrix_crown_projection', 'exterior-garden-fern-only-native-r34.py')
    fresh = native.source_footprints(source, measurements)
    g.require(len(fresh) == len(r['sourceCrownMaskProof']) == 36 and sum(p['decodedSourceF32VerticesChecked'] for p in fresh) == 32124, 'All36 source crowns required')
    # Execute inequalities independently; libm-derived radius/height/clearance
    # doubles are not compared bit-for-bit between host and Unreal Python.
    for actual, independent in zip(r['sourceCrownMaskProof'], fresh):
        for k in ('rootId', 'model', 'decodedSourceF32VerticesChecked', 'actualStoredMatrix', 'originalNativeXYZExact',
                  'allVerticesAndFullCircleInOriginalBed', 'fullCircleExcludesOriginalSteps', 'sourceHeightRoleChanged'):
            g.require(actual[k] == independent[k], 'Source-matrix crown identity/mask gate differs')
        g.require(all(type(actual[k]) in (float, int) and math.isfinite(actual[k]) and actual[k] > 0
            for k in ('actualContainingCircleRadiusCm', 'bedBoundaryCircleClearanceCm', 'stepBoundaryCircleClearanceCm')), 'Finite positive original-circle clearance required')
    packages = [p for p in g.package_paths(source['models'])]+[p.split('.')[0] for p in materials['newPackageAssets']]
    g.require(set(packages) == set(r['newPackages']) and len(r['newPackages']) == 11, 'Exact3mesh/1graph4tex/3pipeline packages required')
    g.require(g.validate_content(base['content'], side(r['afterContentInventory']), r['newPackages']) == r['assetDelta'], 'Map-only+11 recorded Content closure differs')
    return {'mode': 'saved-36-original-fern-garden-all-ornamentals-retained', 'nativeProcessId': 21209,
            **g.COUNTS, 'originalOrnamentalMembersPreserved': 12, 'originalFlowersPreserved': 41,
            'wholeActorCounterfactualValidated': True, 'retainedRawMatrixOrderMainSeedCustomDataExact': True,
            'fullNativeF32PositionUV0TopologyProofTriangles': 3848, 'sourceCrownVertices': 32124,
            'sourceCrownInequalitiesIndependentlyExecuted': True, 'freshDerivedRadiusHeightStatsBitEqualityRequired': False,
            'storedNewMatricesIndependentlyDecodedAfterSaveByCpuChecker': False,
            'executedNativeSavedNewMatrixGateAndSavedComponentHashesVerified': True,
            'AdditionalRandomSeedsReadbackAvailable': False, 'perInstanceShaderRandomValuePreservationClaimed': False,
            'nativeNormalTangentReadbackAvailable': False, 'freshNativeAssetDecodePerformedByCpuChecker': False,
            'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False, 'performanceAccepted': False,
            'shippingVerified': False, 'packageVerified': False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('report', type=Path)
    parser.add_argument('--guard-tests', action='store_true')
    args = parser.parse_args()
    g.require(args.report.resolve() == REPORT and g.sha(REPORT) == REPORT_SHA, 'Only actual unchanged R34 native report accepted')
    r, plan = g.read(REPORT), g.read(g.PLAN)
    g.require(g.sha(g.PLAN) == PLAN_SHA, 'Frozen selected R34 plan differs')
    preflight = side(r['sourcePreflight'])
    result = validate_saved(r, plan, g.source_bundle(), preflight)
    if args.guard_tests:
        mutations = [('status', 'running'), ('nativeProcessId', 21210), ('nativeApplied', False),
                     ('fullPhotorealismAccepted', True), ('wholeOneMemberHeroRetirements', [{'rootId': 'garden_ornamental_6'}]),
                     ('allOriginal12OrnamentalActorsAndMembersUnchanged', False)]
        for key, value in mutations:
            changed = copy.deepcopy(r)
            changed[key] = value
            try: validate_header(changed)
            except (RuntimeError, KeyError): continue
            raise RuntimeError('Adversarial saved header accepted: '+key)
        result['adversarialHeaderGuards'] = 6
    print(json.dumps(result, allow_nan=False))


if __name__ == '__main__':
    main()
