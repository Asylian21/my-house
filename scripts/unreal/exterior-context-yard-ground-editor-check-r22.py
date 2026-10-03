"""CPU-only exact saved R32 receipt/counterfactual and source-frame checker.

No Unreal boot. All source floor F32 corners are reconstructed. Native recorded
root matrices are applied to source F32 three-LOD vertices for independent mask
checks. Native all-LOD vertices and saved-new matrices were checked by the
executed helper; no raw saved-new matrix/vertex sidecar was emitted separately.
"""
import copy
import importlib.util
import json
import math
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-yard-ground-editor-check-r22.py'
HELPER = 'scripts/unreal/exterior-context-yard-ground-native-r32.py'
HELPER_SHA = 'c30e4f323e6dad88f69c957112e528c8c326eb45fd3f970cc8388d33466d0537'
REPORT_SHA = '99b80074fe1309ee951ea662cf42f75ecd6d0a2bc711f0c76cc5d34e18891a19'
PLAN_SHA = '03c6e1a5ba25966c3f314c44908fa73cdd32e0097d25ba516f75e537940841b3'
PREFLIGHT_SHA = 'af2eb7c935c6354b384a375ad3127939d34fa14145b4f9a8deebd5e044a21684'
s = importlib.util.spec_from_file_location('r22_frozen_saved_R32', ROOT/HELPER)
n = importlib.util.module_from_spec(s)
s.loader.exec_module(n)
g = n.guard
PREFLIGHT = g.STUDY/'source-preflight-r1/source-preflight.json'


def header(report, plan, preflight):
    n.require(report['schema'] == g.SCHEMA and report['owner'] == HELPER and report['status'] == n.STATUS
              and report['output'] == str(g.CANDIDATE) and report['project'] == str(g.CANDIDATE/'Project/BreziTwin')
              and report['nativeProcessId'] == 5443, 'Only actual successful saved R32a accepted')
    n.require(all(report[k] is True for k in ('nativeApplied', 'savedMapUnloadedReloaded', 'sourceInputsUnchanged',
              'originalSavedR30bUnchanged', 'existingRootsPreserved', 'originalBedsAnd13ShrubsPreserved',
              'allGroundNativeOrderedF32PositionsUV0UV1WindingVerified')), 'Executed saved scope missing')
    n.require(all(report[k] is False for k in ('nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted',
              'shippingVerified', 'packageVerified', 'materialPackagesIndependentlyUnloaded', 'nativeNormalTangentReadbackAvailable',
              'measuredElevation', 'AdditionalRandomSeedsReadbackAvailable', 'existingMemberTransformOrSeedSetterUsed')),
              'Unsupported acceptance/readback or old-member setter')
    n.require(report['actualCounts'] == plan['expectedCounts'] == g.COUNTS and report['newTextureObjects'] == 0
              and report['activeDesign'] == plan['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}
              and report['setbacksMm'] == plan['setbacksMm'] == {'street': 3000, 'east': 3000}, 'Exact counts/CBB3000 required')
    n.require(plan['schema'] == g.SCHEMA and plan['owner'] == 'scripts/unreal/exterior-context-yard-ground-native-study-r32.py'
              and plan['status'] == 'source-ready-actual-saved-r30b-yard-ground-native-pending'
              and preflight['schema'] == g.SCHEMA and preflight['owner'] == HELPER
              and preflight['status'] == 'yard-ground-source-preflight-validated-native-pending'
              and preflight['testExitCode'] == 0 and preflight['nativeExecuted'] is False, 'Closed source/preflight types required')
    n.require(report['selectedPlan'] == preflight['selectedPlan'] == n.pin(g.PLAN)
              and report['sourcePreflight'] == n.pin(PREFLIGHT) and report['sourceStudy'] == plan['sourceStudy']
              and report['baseNativeReport'] == plan['baseNativeReport'] == preflight['baseNativeReport']
              and report['baseNativeProcess'] == plan['baseNativeProcess'] == preflight['baseNativeProcess']
              and report['projectClone'] == plan['initialRootClone'] == preflight['projectClone']
              and report['moduleOrderWitness'] == preflight['moduleOrderWitness'], 'Actual executed source/parent pin binding differs')
    n.require(report['inputFiles'] == preflight['inputFiles'] and len(report['inputFiles']) == 528, 'Exact528 source preflight pins required')


def geometry(report, bundle, plan):
    proofs = report['savedReadback']['meshProofs']
    n.require(len(proofs) == 3 and len(report['newMeshes']) == 3, 'Exactly3 source ground meshes required')
    for mesh, row in zip(bundle['proposal']['meshes'], proofs):
        expected = g.corners(mesh)
        n.require(row == {'mesh': report['newMeshes'][mesh['id']], 'triangles': len(expected),
                  'nativeOrderedF32PositionUv0Uv1CornerSha256': n.digest(expected),
                  'fullOrderedNativeGeometryVerified': True, 'nativeNormalTangentReadbackAvailable': False},
                  'Full source/native ordered F32 P/UV0/UV1/winding proof differs')
        n.require(n.digest(expected) == plan['sourceSummary']['sourceF32CornerHashes'][mesh['id']], 'Source corner pin differs')
    n.require(sum(r['triangles'] for r in proofs) == 32878
              and report['savedReadback']['fullActorCounterfactualValidated'] is True
              and report['savedReadback']['counts'] == g.COUNTS
              and report['savedReadback']['nativeNormalTangentReadbackAvailable'] is False
              and report['savedReadback']['nativeAppearanceAccepted'] is report['savedReadback']['performanceAccepted'] is False,
              'Full geometry census/evidence tier differs')


def finite(values, width):
    return isinstance(values, list) and len(values) == width and all(type(v) in (int, float) and math.isfinite(v) for v in values)


def measurements(report, bundle):
    values = n.read(n.check_pin(report['nativeSourceFrameMeasurements']))
    n.require(set(values) == set(g.MODELS), 'Exactly3 own measured low-growth groups required')
    seen = []
    footprints = report['savedReadback']['footprints']
    n.require(len(footprints) == 1274 and len({f['rootId'] for f in footprints}) == 1274, 'All1274 native footprint rows required')
    by_id = {f['rootId']: f for f in footprints}
    for model in g.MODELS:
        roots = [r for r in bundle['proposal']['planting'] if r['modelId'] == model]
        row = values[model]
        n.require(set(row) == {'rootIds', 'preInsertionValues', 'recoveredValues', 'actualMatrices',
                  'nativeUnregisteredMeshlessTransientMeasured', 'originalActorOrMemberMutated'}
                  and row['nativeUnregisteredMeshlessTransientMeasured'] is True and row['originalActorOrMemberMutated'] is False
                  and row['rootIds'] == [r['id'] for r in roots]
                  and len(row['preInsertionValues']) == len(row['recoveredValues']) == len(row['actualMatrices']) == len(roots),
                  'Actual measured identity/frame/order scope differs')
        for root, before, recovered, matrix in zip(roots, row['preInsertionValues'], row['recoveredValues'], row['actualMatrices']):
            for v in (before, recovered):
                n.require(isinstance(v, list) and len(v) == 3 and all(finite(q, width) for q, width in zip(v, (3, 4, 3))), 'Finite native Transform required')
                n.exact(v[0], root['positionCm'], 'Actual native/source root XYZ differs')
            n.exact(before[2], [root['uniformScale']]*3, 'Exact source-assigned uniform scale differs')
            n.require(len(matrix) == 4 and all(finite(v, 4) for v in matrix), 'Finite native FMatrix required')
            n.exact(matrix[3][:3], root['positionCm'], 'Actual native matrix/source XYZ differs')
            n.exact([v[3] for v in matrix], [0., 0., 0., 1.], 'Native matrix homogeneous fields differ')
            f = by_id[root['id']]
            n.require(f['modelId'] == model and f['actualRootXYZ'] == recovered[0]
                      and type(f['actualAllNativeLodRadiusCm']) in (int, float) and math.isfinite(f['actualAllNativeLodRadiusCm'])
                      and f['actualAllNativeLodRadiusCm'] > 0 and math.isfinite(f['actualAbovePivotHeightCm'])
                      and f['allNativeLodVerticesAndContainingCircleInsideSourceMasks'] is True
                      and f['originalShrubClearancePreserved'] is True, 'Executed all-LOD native footprint evidence differs')
        seen += row['rootIds']
    n.require(len(seen) == len(set(seen)) == 1274 and set(seen) == set(by_id), 'Complete new-root membership differs')
    return values


def source_native_points(model):
    """Proposed native F32 geometry from exact old three-LOD source, not a UE read."""
    file = Path(model['glbPath'])
    n.require(n.sha(file) == model['glbSha256'], 'Existing original plant source changed')
    raw = file.read_bytes()
    n.require(struct.unpack_from('<III', raw) == (0x46546c67, 2, len(raw)), 'Typed original GLB required')
    length, kind = struct.unpack_from('<II', raw, 12)
    n.require(kind == 0x4e4f534a, 'GLB JSON absent')
    doc, blob = json.loads(raw[20:20+length]), raw[28+length:]
    result = []
    for lod in model['lods']:
        node = next(v for v in doc['nodes'] if v.get('name') == lod['nodeName'])
        n.require(not any(k in node for k in ('translation', 'rotation', 'scale', 'matrix')), 'Original source node basis differs')
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            a = doc['accessors'][primitive['attributes']['POSITION']]
            view = doc['bufferViews'][a['bufferView']]
            n.require(a['componentType'] == 5126 and a['type'] == 'VEC3', 'Exact original F32 POSITION required')
            offset, stride = view.get('byteOffset', 0)+a.get('byteOffset', 0), view.get('byteStride', 12)
            for i in range(a['count']):
                x, z, y = struct.unpack_from('<fff', blob, offset+i*stride)
                result.append([g.f32(x*100), g.f32(y*100), g.f32(z*100)])
    n.require(result, 'Complete source3LOD points missing')
    return result


def actual_frame_source_masks(bundle, values):
    models = {r['id']: r for r in bundle['data']['plantGeometry']['meshes']}
    points = {m: source_native_points(models[m]) for m in g.MODELS}
    checked = 0
    for model in g.MODELS:
        roots = [r for r in bundle['proposal']['planting'] if r['modelId'] == model]
        for root, matrix in zip(roots, values[model]['actualMatrices']):
            center = matrix[3][:2]
            domain = bundle['plantingDomains'][root['buildingSourceId']]
            radius = 0.
            n.require(domain.contains(center), 'Actual native-recorded root outside source domain')
            for point in points[model]:
                local = [sum(point[j]*matrix[j][k] for j in range(3)) for k in range(3)]
                world = [matrix[3][k]+local[k] for k in range(3)]
                n.require(domain.contains(world[:2]) and all(not mask.contains(world[:2]) for mask in bundle['masks'].values()),
                          'Source F32 vertex through actual native matrix enters original exclusions')
                radius = max(radius, math.hypot(*local[:2]))
                checked += 1
            n.require(domain.distance(center, radius+1) > radius
                      and all(not mask.contains(center) and mask.distance(center, radius+21) > radius+20 for mask in bundle['masks'].values()),
                      'Complete source-F32 crown through recorded matrix enters exclusion')
            for shrub in bundle['layout']['planting']:
                n.require(math.dist(center, shrub['positionCm'][:2]) > radius+shrub['radialEnvelopeCm']+12., 'Original13 shrub clearance differs')
    return checked


def materials(report, bundle):
    maps = g.module('r22_exact_r32_material_counterfactual', 'exterior-context-yard-ground-materials-r32.py')
    graphs, textures = maps.validate_proposals(bundle['recipes'])
    row = report['newMaterialReport']
    n.require(row['schema'] == maps.SCHEMA and row['owner'] == maps.OWNER and row['sourceStudy'] == n.pin(maps.PLAN)
              and row['newMaterialGraphs'] == 2 and row['newTextureObjects'] == 0
              and row['newPackageAssets'] == sorted(maps.new_asset(k) for k in maps.ROLES)
              and set(row['materials']) == set(maps.ROLES) and row['sharedTextureWitnessBefore'] == textures
              and row['sharedTexturesUnchanged'] is True, 'Exact own graph/shared texture scope differs')
    for recipe in bundle['recipes']:
        identity = recipe['id']
        rec = row['materials'][identity]
        n.require(rec['asset'] == maps.new_asset(identity) and rec['recipe'] == recipe and rec['compileErrors'] == []
                  and rec['graphSha256'] == n.digest(rec['graph'])
                  and rec['graphDelta'] == maps.validate_graph(identity, graphs[identity], rec['graph'])
                  and rec['metadata'] == {'BreziGeneratedBy': maps.OWNER, 'BreziR32MaterialRole': identity,
                  'BreziR32SourceRecipeSha256': n.digest(recipe)} and rec['newTextureObjects'] == 0,
                  'Original graph copy outside exact owned UV1/opacity/Amount delta')
    for key in ('nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted', 'shippingVerified', 'packageVerified',
                'originalSourceTexturePixelsReimportedOrEdited', 'actualNativeTextureSourcePixelsDecoded',
                'actualNativeTextureGpuPixelFormatVerified', 'nativeDitherCoveragePixelsMeasured', 'materialPackagesIndependentlyUnloaded'):
        n.require(row[key] is False, 'Material source/receipt cannot invent native pixel proof/acceptance')
    return {k: rec['asset'] for k, rec in row['materials'].items()}


def counterfactual(report, plan, bundle, values, material_assets):
    base = n.read(n.check_pin(plan['baseNativeReport']))
    witness = n.read(n.check_pin(base['savedActorWitness']))
    original = n.read(n.check_pin(report['beforeActorWitness']))
    n.require(original == witness and n.digest(original) == report['beforeActorWitnessSha256'] and len(original) == 5356,
              'Recorded before not tied to immutable actual R30b full witness')
    frame_base = {'witness': witness}
    targets = g.target_components(frame_base)
    n.require(report['targets'] == plan['targets'] == targets, 'Only exact old R28 ground targets allowed')
    expected = g.expected_original(witness, targets, report['newMeshes'], material_assets)
    expected.update(g.added_expected(frame_base, targets, report['addedActors'], report['newMeshes'], material_assets, values, bundle))
    declared, saved = (n.read(n.check_pin(report[k])) for k in ('expectedActorWitness', 'savedActorWitness'))
    n.require(expected == declared == saved and len(saved) == 5360
              and n.digest(saved) == report['expectedActorWitnessSha256'] == report['savedActorWitnessSha256'],
              'Full5356 only2rebind+1hide+4add counterfactual differs')
    hisms = [c for a in saved.values() for c in a['components'] if c['class'] == '/Script/Engine.HierarchicalInstancedStaticMeshComponent']
    n.require(len(hisms) == 2321 and sum(c['instanceCount'] for c in hisms) == 678231, 'Full native HISM census differs')
    controls = n.read(n.check_pin(report['originalControlsSaved']))
    n.require(controls == n.read(n.check_pin(report['originalControlsBefore'])) and set(controls) ==
              {'grass', 'trees', 'retainedGarden', 'observedOldMaterials', 'r30MaterialReport'}, 'All original observed controls differ')
    for key, base_key in [('grass', 'originalGrassSaved'), ('trees', 'originalTreesSaved'),
                          ('retainedGarden', 'retainedGardenControlsSaved'), ('observedOldMaterials', 'originalMaterialsSaved')]:
        n.require(controls[key] == n.read(n.check_pin(base[base_key])), 'Original R30 garden/trees/grass/material controls changed')
    n.require(controls['r30MaterialReport'] == base['materialReport'], 'Original two R30 graphs/eight textures changed')
    before_content = n.read(n.check_pin(report['baseContentInventory']))
    after = n.read(n.check_pin(report['afterContentInventory']))
    n.require(report['baseContentInventory'] == base['afterContentInventory'] and report['protectedProjectProof'] == base['protectedProjectProof']
              and report['assetDelta'] == g.validate_content(before_content, after, report['newPackages'])
              and len(n.read(n.check_pin(report['protectedProjectProof']))) == 132, 'Closed saved8package/map-only inventory differs')
    n.require(set(report['newPackages']) == set(report['newMeshes'].values()) | set(material_assets.values()) | set(report['importPipelineAssets'])
              and report['importPipelineAssets'] == [g.PREFIX+'/Pipeline/'+k+'.'+k for k in ('Assets', 'Materials', 'Level')],
              'Known3mesh2material3pipeline package scope differs')


def validate_saved(report, plan, bundle, preflight):
    header(report, plan, preflight)
    n.require(bundle['summary'] == plan['sourceSummary'] == preflight['sourceSummary'], 'Independently reconstructed source summary differs')
    geometry(report, bundle, plan)
    values = measurements(report, bundle)
    assets = materials(report, bundle)
    counterfactual(report, plan, bundle, values, assets)
    checked = actual_frame_source_masks(bundle, values)
    return {'mode': 'saved-resolved-context-yard-ground-and-low-detail', 'nativeProcessId': 5443,
            **g.COUNTS, 'fullSceneHismComponents': 2321, 'fullSceneHismInstances': 678231,
            'wholeActorCounterfactualValidated': True, 'originalR30Garden435Retained38NewControlsExact': True,
            'original78Trees8949GrassControlsExact': True, 'original13ShrubsAndBedsPreserved': True,
            'sourceF32ThreeLodPointsThroughRecordedNativeMatricesChecked': checked,
            'allSourceF32ThreeLodVerticesThroughRecordedNativeMatricesInsideMasks': True,
            'nativeAllThreeLodFootprintProofViaExecutedHelper': True, 'freshNativePlantVertexDecodeByCpuChecker': False,
            'savedNewStoredMatricesExactViaExecutedNativeGate': True, 'savedNewStoredMatricesIndependentlyDecodedByCpuChecker': False,
            'nativeRecoveredFramesBoundToFullSavedComponentHashes': True, 'inputYawQuaternionNumericallyRecomputedByCpuChecker': False,
            'fullGroundNativeOrderedF32PositionsUv0Uv1SourceReconstructed': True,
            'independentExactRationalSourceDepthValidated': True, 'sourceDepthTriangleOverlaps': 9129,
            'sourceMinimumHardAboveUnderlayCm': 0.30655479431152344, 'measuredElevation': False,
            'nativeNormalTangentReadbackAvailable': False, 'nativeDitherCoveragePixelsVerified': False,
            'AdditionalRandomSeedsReadbackAvailable': False, 'existingMemberTransformOrSeedSetterUsed': False,
            'nativeApplied': True, 'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False,
            'performanceAccepted': False, 'shippingVerified': False, 'packageVerified': False}


def load_actual(path):
    n.require(Path(path).resolve() == g.CANDIDATE/n.REPORT and n.sha(path) == REPORT_SHA
              and n.sha(ROOT/HELPER) == HELPER_SHA and n.sha(g.PLAN) == PLAN_SHA and n.sha(PREFLIGHT) == PREFLIGHT_SHA,
              'Exact actual saved/helper/source bytes required')
    report, plan, pf = n.read(path), n.read(g.PLAN), n.read(PREFLIGHT)
    terminal = g.source.old.clean.actual_terminal(path, g.CANDIDATE/'context-yard-ground-native-process.json', HELPER, 'context-yard-ground-native')
    n.require(terminal['pid'] == 5443 and terminal['exitCode'] == 0, 'Actual completed process0 required')
    source_inputs = dict(plan['inputFiles'])
    for row in [n.pin(g.PLAN), plan['baseNativeReport'], *plan['baseNativeProcess'].values()]:
        if isinstance(row, dict) and 'path' in row:
            source_inputs[row['path']] = row['sha256']
    n.require(source_inputs == pf['inputFiles'] and len(source_inputs) == 528, 'Exact source-preflight closure differs')
    n.check_pin(pf['testLog'])
    n.check_pin(pf['testSource'])
    for file, value in source_inputs.items():
        n.require(n.sha(file) == value, 'Frozen input changed: '+file)
    bundle = g.load_source()
    return report, plan, bundle, pf


def adversarial(report, plan, bundle, preflight):
    count = 0
    for key, value in [('status', 'running'), ('nativeApplied', False), ('fullPhotorealismAccepted', True), ('nativeProcessId', 5444)]:
        row = copy.deepcopy(report)
        row[key] = value
        try:
            header(row, plan, preflight)
        except (RuntimeError, ValueError, KeyError):
            count += 1
        else:
            raise RuntimeError('Adversarial header accepted '+key)
    for field, value in [('triangles', 1), ('nativeOrderedF32PositionUv0Uv1CornerSha256', '0'*64)]:
        row = copy.deepcopy(report)
        row['savedReadback']['meshProofs'][0][field] = value
        try:
            geometry(row, bundle, plan)
        except (RuntimeError, ValueError, KeyError):
            count += 1
        else:
            raise RuntimeError('Adversarial geometry accepted '+field)
    row = copy.deepcopy(report)
    row['newMeshes']['yard_ground_r32_entry_walk'] = '/Game/Foreign.Mesh'
    try:
        geometry(row, bundle, plan)
    except (RuntimeError, ValueError, KeyError):
        count += 1
    else:
        raise RuntimeError('Foreign source mesh accepted')
    n.require(count == 7, 'All7 focused adversarial guards required')
    return count


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('report', nargs='?', type=Path, default=g.CANDIDATE/n.REPORT)
    parser.add_argument('--guard-tests', action='store_true')
    args = parser.parse_args()
    report, plan, bundle, preflight = load_actual(args.report)
    summary = validate_saved(report, plan, bundle, preflight)
    if args.guard_tests:
        summary['focusedAdversarialGuardsPassed'] = adversarial(report, plan, bundle, preflight)
    print(json.dumps(summary, indent=2, allow_nan=False))
