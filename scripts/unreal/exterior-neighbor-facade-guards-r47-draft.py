"""UNBOUND R47 source guard; no UObject or runnable project entry.

A future immutable bound revision must pin the actual selected-base contract,
root image decision and independent clone. Caller-supplied non-null values do
not enable this draft. The R43 observations remain documentary source only.
"""
import copy
import hashlib
import json
from pathlib import Path
from types import MappingProxyType

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-neighbor-facade-guards-r47-draft.py'
SCHEMA = 'brezi-unbound-r47-existing-plaster-copy-material-contract'
SOURCE = ROOT/'output/unreal/exterior-neighbor-facade-20261002-r47-unbound-proposal/facade-plaster-proposal.json'
SOURCE_SHA = 'f278cf597ee810626e5e0d5b47d258512db1acc55b09e1d229e7580618ea86bf'
SOURCE_BYTES = 53948
OLD_GRAPH_SHA = '0cd028ef2d1fe088acb2a27d54a9bbf1379a2d875be7d16b0eb227ef007bf2e2'
NEW_GRAPH_SHA = '285d18939c7cb6ab6b6e56411becc818a807bcf8472f96b966c9d76f27c94979'
ORIGINAL = '/Game/Brezi/NeighborFinish20261001R18/Materials/M_neighbor_plaster_BU_572063.M_neighbor_plaster_BU_572063'
PREFIX = '/Game/Brezi/NeighborFacade20261002R47'
ASSET = PREFIX+'/Materials/M_plaster_BU_572063_r47.M_plaster_BU_572063_r47'
CHANGES = (
    ('BreziNeighborR18:photographic-contrast', .07500000298023224, .25),
    ('BreziNeighborR18:normal-strength', .20000000298023224, .5),
)
FUTURE_BINDING = MappingProxyType({
    'selectedBaseContract': None,
    'rootImageDecision': None,
    'independentProjectClone': None,
})


def require(ok, message):
    if not ok:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def pin(path):
    p = Path(path).resolve()
    return {'path': str(p), 'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'bytes': p.stat().st_size}


def checked(row):
    require(isinstance(row, dict) and set(row) == {'path', 'sha256', 'bytes'}, 'Exact file pin required')
    p = Path(row['path'])
    require(p.is_absolute() and p.resolve() == p and not p.is_symlink() and p.is_file()
        and pin(p) == row, 'Pinned file changed or is not a canonical ordinary file')
    return p


def load_contract():
    require(pin(SOURCE) == {'path': str(SOURCE), 'sha256': SOURCE_SHA, 'bytes': SOURCE_BYTES}, 'Immutable f278cf R47 proposal required')
    source = json.loads(SOURCE.read_text())
    require(source['status'] == 'source-only-unbound-two-scalar-one-copied-graph-proposal'
        and source['futureEntryRunnable'] is False and all(v is None for v in source['futureBinding'].values()),
        'Source proposal must remain unbound')
    original = source['originalMaterial']; proposed = source['proposedMaterial']
    require(original['asset'] == ORIGINAL and proposed['asset'] == ASSET
        and digest(original['graph']) == original['recordedGraphSha256'] == OLD_GRAPH_SHA
        and digest(proposed['graph']) == proposed['expectedGraphSha256'] == NEW_GRAPH_SHA,
        'Exact source and proposed complete graph required')
    restored = copy.deepcopy(proposed['graph'])
    require(len(original['graph']['nodes']) == len(restored['nodes']) == 22, 'Complete22-node graph required')
    old_nodes = {n['role']: n for n in original['graph']['nodes']}
    new_nodes = {n['role']: n for n in restored['nodes']}
    require(len(old_nodes) == len(new_nodes) == 22 and set(old_nodes) == set(new_nodes), 'Unique unchanged source roles required')
    for role, old, new in CHANGES:
        require(old_nodes[role]['class'] == new_nodes[role]['class'] == 'MaterialExpressionConstant'
            and old_nodes[role]['inputs'] == new_nodes[role]['inputs'] == []
            and old_nodes[role]['values'] == {'r': old} and new_nodes[role]['values'] == {'r': new},
            'Only the two declared encoded F32 Constant.r values may differ')
        new_nodes[role]['values']['r'] = old
    require(restored == original['graph'] and proposed['aux'] == original['aux']
        and proposed['usage'] == original['usage'] == {'instancedStaticMeshes': False, 'nanite': False},
        'All flags, roots, UV, photo routes, palette, aging, roughness, aux and usage must remain exact')
    require([r['actor'].rsplit('_', 1)[-1] for r in source['targetSlots']] == ['640', '643', '645']
        and all(r['slot'] == 0 and r['beforeMaterial'] == ORIGINAL for r in source['targetSlots'])
        and source['intendedDelta']['newMaterialPackages'] == 1
        and source['intendedDelta']['newTexturePackages'] == 0, 'Exact three-slot/one-material/zero-texture proposal required')
    require(set(source['originalMaps']) == {'albedo', 'normal', 'roughness'}, 'All three unchanged original maps required')
    for row in source['originalMaps'].values():
        require(row['recordedNativeTexture']['asset'] == row['nativeAsset'], 'Recorded original texture asset identity differs')
    return {'source': source, 'original': original, 'proposed': proposed}


def require_native_binding(binding):
    """First call in every UObject-capable kernel; this draft always rejects.

    A later bound guard must supply the immutable actual three pins, authenticate
    the selected process0/saved material and targets, root R46 image selection,
    and byte-identical independent project clone before enabling any kernel.
    No current or caller-supplied proof can substitute for that future revision.
    """
    require(all(v is not None for v in FUTURE_BINDING.values()),
        'UNBOUND R47: actual image-selected base and independent clone are not pinned; no UObject access')
    require(binding == dict(FUTURE_BINDING), 'Exact future frozen binding required')
    for row in binding.values():
        checked(row)
    return binding


def describe_draft():
    source = load_contract()['source']
    return {'schema': SCHEMA, 'owner': OWNER, 'source': pin(SOURCE),
        'futureBinding': dict(FUTURE_BINDING), 'runnable': False,
        'asset': ASSET, 'targetSlots': source['targetSlots'],
        'changes': source['proposedMaterial']['changes'],
        'originalGraphSha256': OLD_GRAPH_SHA, 'expectedGraphSha256': NEW_GRAPH_SHA,
        'requiredFutureIntegration': ['actual selected process0/saved report and current byte closure',
            'root R46 original-image decision for this R47 scope',
            'independent exact selected project clone',
            'three unchanged target witnesses, all other actors/raw roots/graphs/textures protected'],
        'nativeApplied': False, 'nativeAppearanceAccepted': False}


if __name__ == '__main__':
    raise RuntimeError('UNBOUND R47 guard has no producer/native entry')
