"""Small UNBOUND source/native contract for the R43 authored boundary trial.

No source producer, native consumer or inventory is run by this module. The
final source plan, source-diagram decision and pristine clone must be bound by
a new owner before any Unreal call. Existing R39c evidence is the selected
before state, not an acceptance of these future additions.
"""
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-parcel-boundary-guards-r43-draft.py'
SCHEMA = 'brezi-unbound-authored-open-garden-boundary-native-draft-r43'
PREFIX = '/Game/Brezi/ParcelBoundary20261002R43'
TAG = 'BreziParcelBoundaryR43:'
MATERIAL_ROLES = ('wood', 'metal', 'gravel')
SOURCE_PLAN = None
ROOT_SOURCE_DIAGRAM_DECISION = None
PROJECT_CLONE = None
NATIVE_PLAN = None
EXPECTED_NATIVE_COUNTS = None
NATIVE_REPORT = None
SELECTED_NATIVE_REPORT = {
    'path': str(ROOT/'output/unreal/exterior-20261002-r39c/neighbor-props-native-report-r3.json'),
    'sha256': '118f451095730e2ff0e62304d959626d4a81be53f03e41dd2229fe91831f4da5',
    'bytes': 648457,
}
ROOT_IMAGE_DECISION = {
    'path': str(ROOT/'output/unreal/exterior-neighbor-props-20261002-r39-image-base-selection-r1/root-image-base-selection-r1.json'),
    'sha256': '211bacaa3573b94542ca97f6820a070dfa50f45db4f0ab4ec3731bece8af076d',
    'bytes': 9331,
}
RECORDED_SELECTED_BASE_COUNTS = {
    'actors': 5368, 'hismComponents': 2329, 'hismInstances': 678205,
    'materialGraphs': 69, 'textureObjects': 108,
    'contentFiles': 4124, 'protectedFiles': 132,
}


def require(value, message):
    if not value:
        raise RuntimeError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                    allow_nan=False).encode()).hexdigest()


def f32(value):
    require(isinstance(value, (int, float)) and not isinstance(value, bool)
            and math.isfinite(value), 'Finite source coordinate required')
    return struct.unpack('<f', struct.pack('<f', value))[0]


def exact(a, b, message):
    """Binary64 values, including zero sign, remain strict for recorded state."""
    if isinstance(a, (int, float)) and not isinstance(a, bool) and isinstance(b, (int, float)) and not isinstance(b, bool):
        require(math.isfinite(a) and math.isfinite(b)
                and struct.pack('<d', float(a)) == struct.pack('<d', float(b)), message)
    elif isinstance(a, (list, tuple)) and isinstance(b, type(a)):
        require(len(a) == len(b), message)
        for x, y in zip(a, b):
            exact(x, y, message)
    elif isinstance(a, dict) and isinstance(b, dict):
        require(set(a) == set(b), message)
        for key in a:
            exact(a[key], b[key], message)
    else:
        require(type(a) is type(b) and a == b, message)


def require_native_binding(*_args, **_kwargs):
    raise RuntimeError('UNBOUND R43: final source, accepted diagram, clone, '
                       'material recipes and native plan/preflight are pending')


def validate_export_mesh(row):
    """Future study adapter packet, not a guessed source-producer schema.

    The adapter must retain the complete final authored source mesh separately,
    then record actual GLB F32 arrays and their expected native conversion. No
    provider geometry, native normals/tangents, or contact proof is inferred.
    Index order must be explicitly chosen and bound by that adapter.
    """
    required = {'id', 'material', 'sourceVerticesCm', 'gltfPositions',
                'expectedNativeVerticesCm', 'sourceNormals', 'gltfNormals',
                'sourceUv0', 'uv0', 'indices', 'sourceIndices',
                'exportWindingPolicy', 'sourceGeometrySha256'}
    require(set(row) == required and row['material'] in MATERIAL_ROLES,
            'Exact authored merged mesh/export packet required')
    n = len(row['sourceVerticesCm'])
    require(n > 0 and len(row['gltfPositions']) == len(row['expectedNativeVerticesCm'])
            == len(row['sourceNormals']) == len(row['gltfNormals']) == len(row['sourceUv0']) == len(row['uv0']) == n
            and row['indices'] and len(row['indices']) % 3 == 0
            and len(row['sourceIndices']) == len(row['indices'])
            and all(type(i) is int and 0 <= i < n for i in row['indices'] + row['sourceIndices']),
            'Complete ordered authored P/UV0/triangle arrays required')
    for original, encoded, native, source_normal, encoded_normal, source_uv, uv in zip(
            row['sourceVerticesCm'], row['gltfPositions'], row['expectedNativeVerticesCm'],
            row['sourceNormals'], row['gltfNormals'], row['sourceUv0'], row['uv0']):
        require(len(original) == len(encoded) == len(native) == len(source_normal) == len(encoded_normal) == 3
                and len(source_uv) == len(uv) == 2,
                'Exact source position/UV arity required')
        wanted = [f32(original[0]/100), f32(original[2]/100), f32(original[1]/100)]
        exact(encoded, wanted, 'GLB F32 position does not bind full source centimetres')
        expected = [f32(encoded[0]*100), f32(encoded[2]*100), f32(encoded[1]*100)]
        exact(native, expected, 'Native F32 position must follow actual encoded GLB basis')
        exact(encoded_normal, [f32(source_normal[0]), f32(source_normal[2]), f32(source_normal[1])],
              'GLB source normal conversion differs; numeric native normal readback remains pending')
        exact(uv, [f32(value) for value in source_uv], 'Actual encoded F32 UV0 must bind complete source UV0')
    require(row['exportWindingPolicy'] in ('source-order', 'source-triangle-corners-0-2-1'),
            'Explicit source-to-export winding policy required')
    indices = row['sourceIndices'] if row['exportWindingPolicy'] == 'source-order' else [
        row['sourceIndices'][i+j] for i in range(0, len(row['sourceIndices']), 3) for j in (0, 2, 1)]
    require(row['indices'] == indices, 'Exported winding/order differs from declared source conversion')
    require(isinstance(row['sourceGeometrySha256'], str) and len(row['sourceGeometrySha256']) == 64,
            'Final authored source geometry identity must be bound')
    return True


def expected_counterfactual(before, added):
    """All current actors remain byte-equivalent; only three new rows are added.

    A final owner must first bind each added row to its authored mesh, material,
    identity transform and explicit new-actor policy. This pure merge never
    derives an intended actor state merely from a saved row.
    """
    require(isinstance(before, dict) and len(before) == RECORDED_SELECTED_BASE_COUNTS['actors']
            and isinstance(added, dict) and len(added) == 3 and not set(before) & set(added),
            'Original full selected scene plus exactly three distinct additions required')
    require(all(row['class'] == '/Script/Engine.StaticMeshActor'
                and len(row['components']) == 1
                and row['components'][0]['class'] == '/Script/Engine.StaticMeshComponent'
                for row in added.values()), 'No new HISM or alternate actor class permitted')
    result = deepcopy(before)
    result.update(deepcopy(added))
    require(all(digest(result[key]) == digest(row) for key, row in before.items()),
            'Original actor data changed in counterfactual')
    return result


if __name__ == '__main__':
    require_native_binding()
