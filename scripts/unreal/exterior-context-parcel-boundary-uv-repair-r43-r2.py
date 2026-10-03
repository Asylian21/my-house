"""Additive R43 source repair:wood UV axis and complete existing mask checks.

No source geometry generation, terrain replay, photo edits, Unreal or native.
The successful R1 plan/producer/diagram/geometry remain unchanged.
"""
import copy
import hashlib
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
from shapely.geometry import MultiPoint, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-parcel-boundary-uv-repair-r43-r2.py'
R1 = ROOT/'output/unreal/exterior-context-parcel-boundary-20261002-r43-source-study/boundary-source-plan.json'
R1_SHA = '1bff32abd3ba6ab4671fbd052785e21399757f6845491026d78937a8778f0056'
OUTPUT = ROOT/'output/unreal/exterior-context-parcel-boundary-20261002-r43-source-uv-repair-r2'
REPAIR_SCHEMA = 'brezi-r43-owned-wood-grain-axis-and-full-exclusion-source-repair-r2'


def require(ok, message):
    if not ok: raise ValueError(message)


def read(path): return json.loads(Path(path).read_text())


def pin(path):
    path = Path(path).resolve(); data = path.read_bytes()
    return {'path': str(path), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def checked(row):
    require(pin(row['path']) == row, 'Frozen R43 source pin differs')
    return Path(row['path'])


def write(path, value):
    with Path(path).open('x') as f: json.dump(value, f, separators=(',', ':'), allow_nan=False); f.write('\n')


def rotate_uv(uv):
    # Determinant+1 quarter turn:source longest-axis U becomes photo-grain V.
    return [[-v, u] for u, v in uv]


def validate_full_exclusions(geometry, masks):
    require(set(masks) == {'protected', 'subject', 'roads', 'buildings', 'cultivatedGround'}, 'Exact original full masks required')
    solids = unary_union([MultiPoint([p[:2] for p in row['verticesCm']]).convex_hull for row in geometry['objects']])
    floor = shape(geometry['connector']['sourceDomainCm'])
    results = {key: {'solidIntersectionCm2': solids.intersection(shape(value)).area,
                     'connectorIntersectionCm2': floor.intersection(shape(value)).area} for key, value in masks.items()}
    require(all(r['solidIntersectionCm2'] == r['connectorIntersectionCm2'] == 0 for r in results.values()),
            'Every solid and connector must avoid all immutable full exclusions')
    return results


def corrected_geometry(original):
    expected = copy.deepcopy(original)
    for row in expected['objects']:
        if row['material'] == 'wood': row['uv0'] = rotate_uv(row['uv0'])
    for row in expected['meshes']:
        if row['materialKey'] == 'wood': row['uv0'] = rotate_uv(row['uv0'])
    return expected


def validate_delta(original, corrected):
    require(corrected == corrected_geometry(original), 'Only exact wood UV0 [-V,U] adaptation permitted')
    # No metadata, POSITION/NORMAL/index/topology/other UV or photo changes.
    require(corrected['newSourceTriangles'] == 12566 and len(corrected['meshes']) == 3,
            'Original three merged source meshes/topology retained')


def load_source():
    require(pin(R1)['sha256'] == R1_SHA, 'Successful R1 source plan must remain exact')
    plan = read(R1); original = read(checked(plan['geometry']))
    checked(plan['sourceSnapshot']); checked(plan['technicalDiagram']); checked(plan['cameraProjection'])
    masks = read(checked(plan['inputFiles']['exclusions']))
    result = corrected_geometry(original); validate_delta(original, result)
    proof = validate_full_exclusions(result, masks)
    return plan, original, result, masks, proof


def main():
    require(not OUTPUT.exists(), 'Exclusive additive source repair output required')
    plan, original, geometry, masks, proof = load_source()
    OUTPUT.mkdir(parents=True)
    write(OUTPUT/'boundary-geometry-uv-r2.json', geometry)
    shutil.copyfile(ROOT/OWNER, OUTPUT/'source-repair.py')
    repaired = copy.deepcopy(plan)
    repaired.update({'schemaVersion': 2, 'owner': OWNER, 'repairSchema': REPAIR_SCHEMA,
        'status': 'source-only-mapped-open-boundary-corrected-wood-grain-and-full-exclusion-review-native-pending',
        'sourceRevisionR1': pin(R1), 'geometry': pin(OUTPUT/'boundary-geometry-uv-r2.json'),
        'sourceSnapshot': pin(OUTPUT/'source-repair.py'),
        'woodUvAxisRepair': {'oldLongestMemberAxis': 'U', 'actualUntouchedPhotoGrainAxis': 'V',
            'newUv0FromOld': ['-V', 'U'], 'uvFrameDeterminant': 1, 'metricTileCm': 150,
            'sourceNormalsPositionsIndicesAndOtherUvsUnchanged': True, 'providerPhotoPixelsEdited': False,
            'nativeNormalTangentOrShadingVerified': False},
        'fullOriginalExclusionSupplement': proof,
        'sourceCameraProofAndDiagramReusedByteExact': True})
    repaired['inputFiles']['successfulR1SourcePlan'] = pin(R1)
    repaired['inputFiles']['successfulR1Geometry'] = plan['geometry']
    repaired['limits'].append('Connector Z is sampled at its generated triangle vertices; ground-face traversal proves XY support/elevation bounds, not continuous mesh-ground contact.')
    repaired['limits'].append('Technical diagram was drawn before root clone binding; its future-clone caption refers to pending final native-consumer binding. The actual prepared clone receipt is separately pinned.')
    write(OUTPUT/'boundary-source-plan-r2.json', repaired)
    print(json.dumps({'plan': pin(OUTPUT/'boundary-source-plan-r2.json'), 'geometry': repaired['geometry'],
        'diagram': repaired['technicalDiagram'], 'sourcePositionsNormalsTopologyUnchanged': True,
        'allFiveFullExclusionIntersectionCm2': proof, 'nativeOrGpuRun': False}))


if __name__ == '__main__': main()
