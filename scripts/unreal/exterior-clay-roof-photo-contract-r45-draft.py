"""Unbound R45 source and four-slot counterfactual kernels, never a base selector."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-clay-roof-photo-contract-r45-draft.py'
SCHEMA = 'brezi-unbound-four-roof-slot-original-clay-photo-kernel-r45'
PROPOSAL = ROOT/'output/unreal/exterior-clay-roof-photo-20261002-r45-unbound-proposal/clay-roof-photo-proposal.json'
PROPOSAL_SHA = 'b1c2d14be64ff121683a358d0d614e9cbfae67a411cfe45a5ae44a1faf8798ea'
PREFIX = '/Game/Brezi/ClayRoofPhoto20261002R45'
TAG = 'BreziClayRoofPhotoR45:'
FUTURE_BINDING = {'selectedNativeReport': None, 'selectedNativeProcess': None,
    'selectedCurrentByteAudit': None, 'rootImageDecision': None, 'projectClone': None,
    'selectedProject': None, 'nativePlan': None, 'nativeReport': None, 'expectedFullSceneCounts': None}


def require(ok, message):
    if not ok: raise RuntimeError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def load_source():
    raw = PROPOSAL.read_bytes()
    require(hashlib.sha256(raw).hexdigest() == PROPOSAL_SHA, 'Immutable R45 proposal changed')
    source = json.loads(raw)
    require(source['schema'] == 'brezi-unbound-original-red-clay-roof-photo-material-proposal-r45'
        and source['schemaVersion'] == 1 and all(v is None for v in source['futureBinding'].values()),
        'Only the frozen unbound source proposal may be described')
    require(source['scope']['existingTrianglesReused'] == 332 and source['scope']['componentSlotSetters'] == 4
        and source['scope']['newAssetPackages'] == 4 and source['scope']['newActors'] == 0
        and source['scope']['rootTransformInstanceCollisionOrNavigationSetters'] == 0,
        'Only four component slot0 overrides/one graph/three originals are proposed')
    require([r['actor'].rsplit('_', 1)[-1] for r in source['targets']] == ['631', '632', '634', '635']
        and sum(r['triangles'] for r in source['targets']) == 332 and all(r['slot'] == 0 for r in source['targets']),
        'Exact source roof/ridge targets differ')
    require(source['materialProposal']['uv']['shaderScale'] == [.25, -.25]
        and source['materialProposal']['normalChain']['reflectionSignCorrection'] == [1, -1, 1]
        and source['materialProposal']['graph']['plannedNodeCount'] == 8,
        'Metric V reflection and unchanged-tangent normal correction are inseparable')
    for row in [source['source']['receipt'], *source['source']['originalMaps'].values()]:
        p = Path(row['path'])
        require(p.is_absolute() and p.resolve() == p and not p.is_symlink()
            and p.stat().st_size == row['bytes'] and hashlib.sha256(p.read_bytes()).hexdigest() == row['sha256'],
            'Untouched official original source bytes changed')
    return source


def require_native_binding():
    # A future selected-base revision must authenticate every field. This draft
    # cannot be enabled by caller-supplied fields or inferred R39/R43 census.
    require(all(v is not None for v in FUTURE_BINDING.values()),
        'R45 remains unbound until selected R43 originals, actual saved proof and independent clone exist')
    raise RuntimeError('R45 draft has no final native owner; create a separately reviewed bound revision')


def expected_counterfactual(before, source, material_path):
    """Pure illustrative kernel; authenticated future before witness is still required."""
    require(material_path == source['proposedAssets']['material'], 'Only one own material may be applied')
    result = copy.deepcopy(before)
    for target in source['targets']:
        require(target['actor'] in before and digest(before[target['actor']]) == target['recordedR39ActorSha256'],
            'Future selected target must retain the exact reference actor; R39 is not a selected base')
        components = [c for c in before[target['actor']]['components'] if c['path'] == target['component']]
        require(len(components) == 1 and digest(components[0]) == target['recordedR39ComponentSha256']
            and components[0]['mesh'] == target['currentMesh']
            and components[0]['materials'] == [target['currentMaterial']]
            and components[0]['overrideMaterials'] == target['currentOverrideMaterials'],
            'Exact original component mesh/default/slot policy required')
        c = next(c for c in result[target['actor']]['components'] if c['path'] == target['component'])
        c['materials'] = [material_path]
        c['overrideMaterials'] = [material_path]
    require(set(result) == set(before), 'No actor may be created or retired')
    return result


def describe_draft():
    source = load_source()
    return {'schema': SCHEMA, 'schemaVersion': 1, 'owner': OWNER, 'status': 'unbound-source-only-native-kernels',
        'sourceProposal': {'path': str(PROPOSAL), 'sha256': PROPOSAL_SHA, 'bytes': PROPOSAL.stat().st_size},
        'futureBinding': copy.deepcopy(FUTURE_BINDING), 'targets': source['targets'],
        'newPackageAssets': sorted(source['proposedAssets'].values()),
        'changedOriginalComponents': 4, 'changedOriginalSlot': 0, 'existingTrianglesUnchanged': 332,
        'oldMeshDefaultMaterialsEdited': False, 'oldRawRootsOrGeometryEdited': False,
        'nativeExecuted': False, 'nativeAppearanceAccepted': False, 'fullPhotorealismAccepted': False,
        'performanceAccepted': False, 'shippingVerified': False, 'activeOutputPromoted': False}
