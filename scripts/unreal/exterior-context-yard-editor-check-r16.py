"""CPU check of the saved R28 additive yard receipt, never a native/GPU run."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-yard-editor-check-r16.py'
HELPER = 'scripts/unreal/exterior-context-yard-native-r28-r2.py'
HELPER_SHA = '9a884bfea89eaa88ed0cfc239b83207e9e57f5b5094c2873886903b943cd96d2'
PREFLIGHT = ROOT / 'output/unreal/exterior-context-yard-20261002-r28-native-preflight-r2/source-preflight.json'
PREFLIGHT_SHA = '3482b79d8060305004ed9132c6bd67549fce634295e1fe39dfd14d60c221399a'
s = importlib.util.spec_from_file_location('r16_exact_saved_yard_native', ROOT / HELPER)
n = importlib.util.module_from_spec(s)
s.loader.exec_module(n)
g = n.guard


class RecordedAsset:
    """Only supplies the recorded asset path to the frozen pure counterfactual."""
    def __init__(self, path, material=None):
        self.path, self.material = path, material

    def get_path_name(self):
        return self.path

    def get_material(self, index):
        n.require(index == 0 and self.material is not None, 'Only the one recorded material slot is available')
        return RecordedAsset(self.material)


def validate_measurements(measurements, bundle):
    n.require(set(measurements) == set(g.MODELS), 'Exactly three source-root frame groups required')
    for mid in g.MODELS:
        row = measurements[mid]
        sources = [r for r in bundle['layout']['planting'] if r['modelId'] == mid]
        n.require(row['sourceRootIds'] == [r['id'] for r in sources]
                  and row['nativeUnregisteredTransientMeasurement'] is True
                  and row['oldActorOrMemberMutated'] is False, 'Measured source identity/scope differs')
        n.require(len(row['preInsertionValues']) == len(row['recoveredValues']) == len(row['actualMatrices']) == len(sources),
                  'Every new root must have its faithful measured frame')
        for source, pre, recovered, matrix in zip(sources, row['preInsertionValues'], row['recoveredValues'], row['actualMatrices']):
            for value in (pre, recovered):
                n.require(len(value) == 3 and all(g.finite(v, width) for v, width in zip(value, (3, 4, 3))),
                          'Malformed measured native Transform')
                n.exact(value[0], source['positionCm'], 'Measured root XYZ differs from authored source')
            n.exact(pre[2], [source['uniformScale']] * 3, 'Measured pre-insertion source scale differs')
            n.require(len(matrix) == 4 and all(g.finite(r, 4) for r in matrix), 'Malformed native FMatrix')
            n.exact(matrix[3][:3], source['positionCm'], 'Stored native root XYZ differs from source')
            n.exact([matrix[i][3] for i in range(4)], [0., 0., 0., 1.], 'Native homogeneous matrix differs')
    return measurements


def validate_saved(r, bundle, base, preflight):
    require = n.require
    read = lambda key: n.read(n.check_pin(r[key]))
    require(r['schema'] == g.SCHEMA and r['owner'] == HELPER and r['status'] == n.STATUS
            and r['output'] == str(g.CANDIDATE) and r['project'] == str(g.CANDIDATE / 'Project/BreziTwin'),
            'Only the actual own R28 saved overlay is eligible')
    require(r['sourceGeometryPlan'] == n.pin(g.SOURCE) and r['sourcePreflight'] == n.pin(PREFLIGHT)
            and r['baseNativeReport'] == base['reportPin'] and r['baseActualProcess'] == base['process']
            and r['inputFiles'] == preflight['inputFiles'], 'Exact saved base/source/preflight closure differs')
    require(r['nativeApiRepairSupplement'] == preflight['nativeApiRepairSupplement'] and r['commandletSubsystemAccessor'] == g.api_repair()['accessor']
            and r['staticMeshEditorSubsystemVerifiedAvailable'] is True and r['assetEditorSubsystemVerifiedAvailable'] is True, 'Known measured subsystem repair gate missing')
    require(r['activeDesign'] == {'variant': 'C', 'heatingLayout': 'B', 'livingLayout': 'B'}
            and r['setbacksMm'] == {'street': 3000, 'east': 3000}, 'Main design/setbacks differ')
    for key in ('nativeAppearanceAccepted', 'fullPhotorealismAccepted', 'performanceAccepted', 'shippingVerified',
                'materialPackagesIndependentlyUnloaded', 'nativeNormalTangentReadbackAvailable',
                'landUseOrDoorObserved', 'measuredElevation'):
        require(r[key] is False, 'Unsupported acceptance/evidence claim: ' + key)
    for key in ('nativeApplied', 'savedMapUnloadedReloaded', 'originalSavedR27Unchanged', 'sourceInputsUnchanged',
                'allOriginalActorPoliciesAndTransformsPreserved', 'originalPlantAssetsBytePreserved'):
        require(r[key] is True, 'Saved/preservation gate missing: ' + key)
    measurements = validate_measurements(read('nativeSourceFrameMeasurements'), bundle)
    mesh_sources = {m['id']: m for m in bundle['geometry']['meshes']}
    material_paths = {}
    require(len(r['newMaterials']) == 2, 'Exactly two graph variants required')
    for recipe, actual in zip(bundle['recipes'], r['newMaterials']):
        role = recipe['id'].removeprefix('context_yard_r28_')
        expected_path = recipe['newMaterial'] + '.' + recipe['newMaterial'].rsplit('/', 1)[-1]
        require(actual['asset'] == expected_path and actual['recipe'] == recipe
                and actual['graphSha256'] == n.digest(actual['graph']) and actual['compileErrors'] == []
                and actual['newTextureObjects'] == 0, 'New material recipe/path/compile proof differs')
        g.validate_graph_copy(recipe['originalGraph'], actual['graph'])
        original_material = bundle['layout']['existingMaterialReferences'][{'soil_bed':'context_garden_soil','worn_edge':'context_soil_exposure'}[role]]
        # World-position modes are native-recorded fields; their exact originals
        # are already bound by the unchanged native graph/source receipt.
        world_roles = {node['role'] for node in recipe['originalGraph']['nodes'] if node['class'] == 'MaterialExpressionWorldPosition'}
        require(set(actual['worldPositionOffsets']) == world_roles and all(isinstance(v,str) and v.startswith('<WorldPositionIncludedOffsets.') for v in actual['worldPositionOffsets'].values()),
                'Native-recorded source world-position fields missing')
        require(original_material['asset'] == recipe['sourceNativeMaterial'], 'Source PBR lookup differs')
        material_paths[role] = expected_path
    require(set(r['newMeshes']) == set(mesh_sources), 'Exactly four source ground meshes required')
    mesh_assets = {}
    for key, source in mesh_sources.items():
        asset = g.PREFIX + '/Geometry/yard-ground/StaticMeshes/' + key + '_LOD0.' + key + '_LOD0'
        require(r['newMeshes'][key] == asset, 'Imported source mesh path differs')
        material = material_paths.get(source['role']) or bundle['layout']['existingMaterialReferences'][source['materialKey']]['asset']
        mesh_assets[key] = RecordedAsset(asset, material)
    expected_ids = set(mesh_sources) | {'EX_context_yard_r28_' + k for k in g.MODELS}
    require(set(r['addedActors']) == expected_ids and len(set(r['addedActors'].values())) == 7,
            'Only four ground plus three shrub actor identities allowed')
    before, declared, saved = (read(k) for k in ('beforeActorWitness', 'expectedActorWitness', 'savedActorWitness'))
    require(before == base['witness'] and len(before) == 5343, 'Full original clean scene differs')
    added = n.source_expected_added(base, r['addedActors'], mesh_assets, {}, measurements, bundle)
    expected = copy.deepcopy(base['witness'])
    require(not set(added) & set(expected), 'A new identity replaces an original actor')
    expected.update(added)
    require(declared == expected == saved and len(saved) == 5350,
            'Saved full actor state differs from the declared source-template counterfactual')
    require([r[k] for k in ('beforeActorWitnessSha256', 'expectedActorWitnessSha256', 'savedActorWitnessSha256')]
            == [n.digest(v) for v in (before, expected, saved)], 'Full canonical actor digests differ')
    proof = r['savedReadback']
    expected_meshes = [{'mesh': r['newMeshes'][m['id']], 'triangles': len(m['indices']) // 3,
                        'nativeOrderedF32PositionUv0Uv1CornerSha256': n.digest(g.corners(m)),
                        'fullOrderedNativeGeometryVerified': True, 'nativeNormalTangentReadbackAvailable': False}
                       for m in bundle['geometry']['meshes']]
    require(proof['meshes'] == expected_meshes and sum(v['triangles'] for v in expected_meshes) == 2969,
            'Full2969 native ordered F32 position/UV0/UV1 corner receipt differs')
    roots = {v['id']: v for v in bundle['layout']['planting']}
    require(len(proof['footprints']) == len(roots) == 13
            and {v['rootId'] for v in proof['footprints']} == set(roots), 'All13 native all-LOD footprint records required')
    for actual in proof['footprints']:
        source = roots[actual['rootId']]
        require(actual['modelId'] == source['modelId'] and actual['actualRootXYZ'] == source['positionCm']
                and actual['sourceConservativeAllLodRadiusCm'] == source['radialEnvelopeCm']
                and actual['allNativeLodVerticesAndContainingCrownInsideSourceBedAndExclusions'] is True,
                'Native all-LOD footprint source identity differs')
        radius, height = actual['actualNativeAllLodRadiusCm'], actual['actualNativeAbovePivotHeightCm']
        require(type(radius) in (int, float) and math.isfinite(radius) and 0 < radius < source['radialEnvelopeCm']
                and type(height) in (int, float) and math.isfinite(height) and height > 0, 'Actual containing crown bound differs')
        xy = source['positionCm'][:2]
        require(bundle['soil'][source['buildingSourceId']].distance(xy, radius + 1) > radius
                and all(mask.distance(xy, radius + 21) > radius + 20 for mask in bundle['masks'].values()),
                'Actual native containing crown crosses source masks/bed')
    expected_proof_fields = {'fullActorCounterfactualValidated': True, 'savedActors': 5350, 'fullHismComponents': 2312,
                             'fullHismInstances': 676957, 'newRoots': 13, 'newGroups': 3, 'newGroundActors': 4,
                             'nativeNormalTangentReadbackAvailable': False, 'nativeAppearanceAccepted': False,
                             'performanceAccepted': False}
    require({k: v for k, v in proof.items() if k not in ('meshes', 'footprints')} == expected_proof_fields,
            'Saved proof scope/counts differ')
    hisms = [c for actor in saved.values() for c in actor['components']
             if c['class'] == '/Script/Engine.HierarchicalInstancedStaticMeshComponent']
    require(len(hisms) == 2312 and sum(c['instanceCount'] for c in hisms) == 676957, 'Whole-scene HISM count differs')
    pipelines = [g.PREFIX + '/Pipeline/' + key + '.' + key for key in ('Assets', 'Materials', 'Level')]
    require(r['importPipelineAssets'] == pipelines, 'Exact three import pipelines required')
    package_paths = list(r['newMeshes'].values()) + list(material_paths.values()) + pipelines
    packages = [p.split('.')[0].removeprefix('/Game/') + '.uasset' for p in package_paths]
    require(r['newContentPackages'] == packages and r['assetDelta'] == g.validate_content(base['content'], read('afterContentInventory'), packages),
            'Only map plus the exact nine new packages allowed')
    require(r['baseContentInventory'] == base['report']['afterContentInventory']
            and r['protectedProjectProof'] == base['report']['protectedProjectProof'], 'Original Content/protected byte closure differs')
    require([r[k] for k in ('scopedMaterialGraphs', 'scopedTextureObjects', 'newTextureObjects', 'originalActorCount', 'savedActorCount',
                           'newGroundActors', 'newHismGroups', 'newShrubRoots', 'newPackageCount', 'originalGrassMembersPreserved')]
            == [56, 77, 0, 5343, 5350, 4, 3, 13, 9, 8949], 'Exact source/runtime scope census differs')
    return {'mode': 'saved-purposeful-context-yard-overlay', 'nativeProcessId': r['nativeProcessId'],
            'originalActors': 5343, 'savedActors': 5350, 'newActors': 7, 'newGroundActors': 4, 'groundTriangles': 2969,
            'newShrubRoots': 13, 'newHismGroups': 3, 'fullSceneHismComponents': 2312, 'fullSceneHismInstances': 676957,
            'scopedMaterialGraphs': 56, 'scopedTextureObjects': 77, 'newTextureObjects': 0, 'newPackages': 9, 'contentFiles': 4043,
            'wholeActorCounterfactualValidated': True, 'fullOrderedF32GroundCornerReceiptMatchesSource': True,
            'nativeMeasuredRootFramesBoundToSavedOrderedTransforms': True, 'nativeSavedRawMatricesExactGateExecuted': True,
            'nativeAllLodVertexFootprintGateExecuted': True, 'containingCrownMasksIndependentlyChecked': True,
            'materialGraphCopiesValidated': True, 'originalGrassMembersPreserved': 8949,
            'nativeNormalTangentReadbackAvailable': False, 'materialPackagesIndependentlyUnloaded': False,
            'landUseOrDoorObserved': False, 'measuredElevation': False, 'nativeAppearanceAccepted': False,
            'fullPhotorealismAccepted': False, 'performanceAccepted': False, 'shippingVerified': False}


def main():
    n.require(n.sha(ROOT / HELPER) == HELPER_SHA and n.sha(PREFLIGHT) == PREFLIGHT_SHA, 'Frozen R28 helper/preflight changed')
    report_path = Path(sys.argv[1]).resolve()
    n.require(report_path == g.CANDIDATE / n.REPORT, 'Only own actual saved R28 report eligible')
    bundle, base = g.load_source(), g.saved_base()
    preflight = n.validate_preflight(PREFLIGHT, bundle, base)
    summary = validate_saved(n.read(report_path), bundle, base, preflight)
    print(json.dumps(summary))


if __name__ == '__main__':
    main()
