"""R20 measured runtime repair: exact attributes; 66 radius-only float paths."""
import copy
import importlib.util
import math
from pathlib import Path
import struct
import sys

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-curved-grass-guards-r2.py'
ORIGINAL_SHA = '20e6dba5af91ce0ca5ffbe3d817ed4ceb6b0267a5fdfa4cda8329355d89a567d'
PROBE = ROOT/'output/unreal/exterior-20261002-r20a/curved-grass-numeric-probe-r2.json'
PROBE_SHA = '8a2cf482a568358de48f4d65ca2b19a2c066b448e44a6b1923e5d34e9c0dab9f'
PROBE_OWNER = 'scripts/unreal/exterior-curved-grass-numeric-probe-r2.py'
PROBE_OWNER_SHA = 'ce93ba415aac5660d29e64d908961090afbc9c5ece8722da81ce20fdba16c8df'
DIFFER_SHA = '0065aab8bfe8e75cfb8cf62c015d5c725a07050865c1187fca5debb94ebebbec'
ABSOLUTE_CAP_CM = 4e-15
MAXIMUM_DOUBLE_ULPS = 2


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT/'scripts/unreal'/filename)
    value = importlib.util.module_from_spec(spec)
    old = sys.dont_write_bytecode; sys.dont_write_bytecode = True
    try: spec.loader.exec_module(value)
    finally: sys.dont_write_bytecode = old
    return value


original = load('r20_r2_original_guard', 'exterior-curved-grass-guards.py')
differ = load('r20_r2_frozen_difference', 'exterior-curved-grass-numeric-probe-r1.py')
for key in dir(original):
    if not key.startswith('_') and key not in globals(): globals()[key] = getattr(original, key)
require(sha(ROOT/original.OWNER) == ORIGINAL_SHA and sha(ROOT/differ.OWNER) == DIFFER_SHA,
        'Frozen original guard/numeric differ changed')

# Exact measured paths are populated once from the pinned native R2 probe.
ALLOWED_PATHS = frozenset({
    '$.geometry[0].rootedRadialEnvelopeCm',
    '$.selection[10].scaledAllVertexRadiusCm',
    '$.selection[11].scaledAllVertexRadiusCm',
    '$.selection[13].scaledAllVertexRadiusCm',
    '$.selection[14].scaledAllVertexRadiusCm',
    '$.selection[15].originalAllLodRadiusCm',
    '$.selection[15].scaledAllVertexRadiusCm',
    '$.selection[16].originalAllLodRadiusCm',
    '$.selection[16].scaledAllVertexRadiusCm',
    '$.selection[17].originalAllLodRadiusCm',
    '$.selection[17].scaledAllVertexRadiusCm',
    '$.selection[18].originalAllLodRadiusCm',
    '$.selection[19].originalAllLodRadiusCm',
    '$.selection[20].originalAllLodRadiusCm',
    '$.selection[20].scaledAllVertexRadiusCm',
    '$.selection[21].originalAllLodRadiusCm',
    '$.selection[22].originalAllLodRadiusCm',
    '$.selection[22].scaledAllVertexRadiusCm',
    '$.selection[23].originalAllLodRadiusCm',
    '$.selection[23].scaledAllVertexRadiusCm',
    '$.selection[24].originalAllLodRadiusCm',
    '$.selection[25].originalAllLodRadiusCm',
    '$.selection[25].scaledAllVertexRadiusCm',
    '$.selection[26].originalAllLodRadiusCm',
    '$.selection[26].scaledAllVertexRadiusCm',
    '$.selection[27].originalAllLodRadiusCm',
    '$.selection[27].scaledAllVertexRadiusCm',
    '$.selection[28].originalAllLodRadiusCm',
    '$.selection[28].scaledAllVertexRadiusCm',
    '$.selection[29].originalAllLodRadiusCm',
    '$.selection[30].originalAllLodRadiusCm',
    '$.selection[31].originalAllLodRadiusCm',
    '$.selection[31].scaledAllVertexRadiusCm',
    '$.selection[32].originalAllLodRadiusCm',
    '$.selection[32].scaledAllVertexRadiusCm',
    '$.selection[33].originalAllLodRadiusCm',
    '$.selection[34].originalAllLodRadiusCm',
    '$.selection[35].scaledAllVertexRadiusCm',
    '$.selection[36].scaledAllVertexRadiusCm',
    '$.selection[38].scaledAllVertexRadiusCm',
    '$.selection[39].scaledAllVertexRadiusCm',
    '$.selection[3].scaledAllVertexRadiusCm',
    '$.selection[40].scaledAllVertexRadiusCm',
    '$.selection[41].scaledAllVertexRadiusCm',
    '$.selection[43].scaledAllVertexRadiusCm',
    '$.selection[44].scaledAllVertexRadiusCm',
    '$.selection[45].scaledAllVertexRadiusCm',
    '$.selection[47].scaledAllVertexRadiusCm',
    '$.selection[48].scaledAllVertexRadiusCm',
    '$.selection[49].scaledAllVertexRadiusCm',
    '$.selection[50].scaledAllVertexRadiusCm',
    '$.selection[51].scaledAllVertexRadiusCm',
    '$.selection[52].scaledAllVertexRadiusCm',
    '$.selection[53].scaledAllVertexRadiusCm',
    '$.selection[54].scaledAllVertexRadiusCm',
    '$.selection[55].scaledAllVertexRadiusCm',
    '$.selection[56].scaledAllVertexRadiusCm',
    '$.selection[57].scaledAllVertexRadiusCm',
    '$.selection[58].scaledAllVertexRadiusCm',
    '$.selection[5].scaledAllVertexRadiusCm',
    '$.selection[60].scaledAllVertexRadiusCm',
    '$.selection[61].scaledAllVertexRadiusCm',
    '$.selection[63].scaledAllVertexRadiusCm',
    '$.selection[7].scaledAllVertexRadiusCm',
    '$.selection[8].scaledAllVertexRadiusCm',
    '$.selection[9].scaledAllVertexRadiusCm',
})


def policy():
    return {'derivedRadiusPaths': sorted(ALLOWED_PATHS), 'maximumDoubleUlpDelta': MAXIMUM_DOUBLE_ULPS,
            'maximumAbsoluteDeltaCm': ABSOLUTE_CAP_CM, 'float32BitsMustRemainEqual': True,
            'allOtherFieldsAndTypesExact': True, 'noGeometryOrSelectionCanonicalization': True}


def measured_probe():
    require(sha(PROBE) == PROBE_SHA and sha(ROOT/PROBE_OWNER) == PROBE_OWNER_SHA,
            'Measured runtime probe/producer changed')
    value = read(PROBE)
    require(value['status'] == 'read-only-comprehensive-numeric-comparison-completed'
            and value['nativeProcessId'] == 36984 and value['mismatchCount'] == value['numericMismatchCount'] == 66
            and value['nonNumericMismatchCount'] == value['numericFloat32UnequalCount'] == 0
            and not value['mismatchListTruncated'], 'Incomplete or foreign measured numeric proof')
    require(all(value[k] is False for k in ('sceneOpened','nativeAssetsTouched','mapModified','gpuLaunch'))
            and all(value[k] is True for k in ('materialRecipeExactlyEqual','cameraExactlyEqual','auditExactlyEqual')),
            'Measured probe source-only/material/camera scope differs')
    require(value['selectionControls']['exactIdentityRootXYZYawScaleHeightControls'] is True
            and value['selectionControls']['savedCount'] == value['selectionControls']['derivedCount'] == 64,
            'Measured strict root/identity/height/scale controls changed')
    require(len(value['geometryAttributeComparisons']) == 3 and all(
        set(fields) == {'positionMetersYUp','normalYUp','uv0','indices','tangentYUp','expectedNativeVerticesCm','expectedNativeNormals'}
        and all(r['exactDecodedEquality'] and r['float32OrU32BinaryEqual'] and r['recursiveDifferences'] == 0
                for r in fields.values()) for fields in value['geometryAttributeComparisons'].values()),
            'Measured original attribute bytes changed')
    require({row['path'] for row in value['mismatches']} == ALLOWED_PATHS
            and all(row['kind'] == 'number' and row['float32Equal'] is True
                and row['doubleUlps'] <= MAXIMUM_DOUBLE_ULPS and row['absoluteDifference'] <= ABSOLUTE_CAP_CM
                for row in value['mismatches']), 'Measured difference scope widened')
    return value


def exact_except_measured(saved, derived, path='$'):
    differences = differ.differences(saved, derived, path)
    for row in differences:
        require(row['path'] in ALLOWED_PATHS and row['kind'] == 'number'
                and math.isfinite(row['saved']) and math.isfinite(row['derived'])
                and row['float32Equal'] is True and row['doubleUlps'] <= MAXIMUM_DOUBLE_ULPS
                and row['absoluteDifference'] <= ABSOLUTE_CAP_CM,
                'Unapproved geometry/root difference: ' + row['path'])
    return differences


def attribute_bits(rows, expected):
    def flat(value):
        if isinstance(value, list): return [v for entry in value for v in flat(entry)]
        return [value]
    for row, target in zip(rows, expected):
        for key in ('positionMetersYUp','normalYUp','uv0','indices','tangentYUp',
                    'expectedNativeVerticesCm','expectedNativeNormals'):
            a, b = flat(row[key]), flat(target[key]); fmt = 'I' if key == 'indices' else 'f'
            require(len(a) == len(b) and struct.pack('<'+fmt*len(a), *a) == struct.pack('<'+fmt*len(b), *b),
                    'Original serialized attribute bits changed: '+row['id']+'.'+key)


def validate_geometry(rows, originals):
    measured_probe()
    expected = original.converted_geometry(originals)
    differences = exact_except_measured(rows, expected, '$.geometry')
    attribute_bits(rows, expected)
    # Delegate every original geometric invariant against the verified derived
    # rows, after exact recursive comparison of all source attributes/metadata.
    result = original.validate_geometry(expected, originals)
    result['measuredRadiusComparison'] = {'observedThisRuntime': differences, 'policy': policy()}
    return result


def validate_selection(selected, placements, prototypes, camera, geometry):
    measured_probe()
    expected = original.select_roots(original.source_candidates(placements, prototypes, camera), geometry)
    differences = exact_except_measured(selected, expected, '$.selection')
    result = original.validate_selection(expected, placements, prototypes, camera, geometry)
    result['measuredRadiusComparison'] = {'observedThisRuntime': differences, 'policy': policy()}
    return result
