"""NEW R24/R25 diagnostic, root-only native execution, no scene/asset writes.

The failed helpers and their assets remain immutable. This script loads exactly
one already saved partial mesh per invocation, without loading a map. Four
triangles (12 corners) per group/section/LOD compare source-original and reversed
index order as separate hypotheses. It grants no repaired-import acceptance.
"""
import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-original-import-basis-diagnostic-r2.py'
SCHEMA = 'brezi-original-import-basis-readonly-diagnostic-r2'
FAILURES = {
    'tree': {'directory': 'exterior-20261002-r24a', 'report': 'original-tree-native-report.json',
        'reportSha': '16963c9382a90ff950b0d463e408d231ab0d0c8cdb511288dde363b863209017',
        'stem': 'original-tree-native', 'pid': 56559, 'sourceCount': 476,
        'owner': 'scripts/unreal/exterior-original-tree-native.py',
        'guard': 'scripts/unreal/exterior-original-tree-guards.py',
        'asset': '/Game/Brezi/OriginalTree20261002R24/Geometry/source-import-untransformed/StaticMeshes/BezierCurve_002.BezierCurve_002',
        'auditSha': '0465263ce4304c0ec9a3e3bec0003e3a5a51b37f37f80a230cf4e9b1c09c6fd4', 'newPackages': 17},
    'fern': {'directory': 'exterior-20261002-r25a', 'report': 'garden-fern-native-report.json',
        'reportSha': '18e0b39ff883d75052b33303f3f9221bb4f33a94c910ee7ccf1dbf2688cf0498',
        'stem': 'garden-fern-native-r1', 'pid': 55672, 'sourceCount': 474,
        'owner': 'scripts/unreal/exterior-garden-fern-native-r25.py',
        'guard': 'scripts/unreal/exterior-garden-fern-guards-r25.py',
        'asset': '/Game/Brezi/GardenFern20261002R25/Geometry/StaticMeshes/garden_fern_original_b_r25_LOD0.garden_fern_original_b_r25_LOD0',
        'auditSha': '5d340349247dbc07bc7d8faef9ef92af4a8fd4e94fe9cbbed7abc2a07fa9e3d3', 'newPackages': 6},
}


def require(ok, message):
    if not ok:
        raise RuntimeError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024*1024):
            h.update(block)
    return h.hexdigest()


def pin(path):
    path = Path(path).resolve()
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def read(path):
    return json.loads(Path(path).read_text())


def checked(row):
    path = Path(row['path'])
    require(path.is_file() and sha(path) == row['sha256'] and path.stat().st_size == row['bytes'],
            'Immutable diagnostic pin changed: '+str(path))
    return path


def write(path, value):
    with Path(path).open('x') as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write('\n')


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(value)
    return value


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def canonical(face):
    rows = [tuple(row) for row in face]
    return min(tuple(rows[index:]+rows[:index]) for index in range(3))


def face_hash(faces):
    h = hashlib.sha256()
    for face in faces:
        for row in canonical(list(face)):
            require(all(math.isfinite(v) for v in row), 'Nonfinite diagnostic corner')
            h.update(struct.pack('<'+'f'*len(row), *row))
    return h.hexdigest()


def original_face(document, binary, primitive, triangle):
    def accessor(index):
        a = document['accessors'][index]
        v = document['bufferViews'][a['bufferView']]
        count = {'VEC2': 2, 'VEC3': 3, 'SCALAR': 1}[a['type']]
        width = {5126: 4, 5123: 2, 5125: 4}[a['componentType']]
        require(v['buffer'] == 0 and not a.get('sparse'), 'Unsupported original source accessor')
        return a, v.get('byteOffset', 0)+a.get('byteOffset', 0), v.get('byteStride', width*count)
    pa, po, ps = accessor(primitive['attributes']['POSITION'])
    _, uo, us = accessor(primitive['attributes']['TEXCOORD_0'])
    uv1 = accessor(primitive['attributes']['TEXCOORD_1']) if 'TEXCOORD_1' in primitive['attributes'] else None
    ia, io, stride = accessor(primitive['indices'])
    require(0 <= triangle < ia['count']//3, 'Diagnostic triangle outside original source')
    fmt = '<H' if ia['componentType'] == 5123 else '<I'
    face = []
    for corner in range(3):
        vertex = struct.unpack_from(fmt, binary, io+(3*triangle+corner)*stride)[0]
        require(0 <= vertex < pa['count'], 'Original index outside vertices')
        x, y, z = struct.unpack_from('<fff', binary, po+vertex*ps)
        row = (f32(100*x), f32(100*z), f32(100*y), *struct.unpack_from('<ff', binary, uo+vertex*us))
        if uv1:
            _, offset, step = uv1
            row += struct.unpack_from('<ff', binary, offset+vertex*step)
        face.append(row)
    return face


def comparison(observed, original):
    """Exact alternatives, no epsilon/guard correction; preserve raw corners."""
    expected = [canonical(list(face)) for face in original]
    actual = [canonical(list(face)) for face in observed]
    reversed_ = [canonical([face[0], face[2], face[1]]) for face in original]
    original_positions = [canonical([row[:3] for row in face]) for face in original]
    actual_positions = [canonical([row[:3] for row in face]) for face in observed]
    point_sets = [sorted(face) for face in expected] == [sorted(face) for face in actual]
    differing = []
    for index, (wanted, got) in enumerate(zip(expected, actual)):
        if wanted != got:
            differing.append({'sampleIndex': index, 'sourceOriginalCanonical': wanted,
                'actualCanonical': got, 'sourceReversedCanonical': reversed_[index]})
    return {'sourceOriginalOrderExact': actual == expected,
        'sourceOriginalOrderBinary32Exact': face_hash(observed) == face_hash(original),
        'sourceReversedOrderExact': actual == reversed_,
        'sourceReversedOrderBinary32Exact': face_hash(observed) == face_hash([[f[0], f[2], f[1]] for f in original]),
        'trianglePointUVSetsExactIgnoringWinding': point_sets,
        'positionOnlyOriginalOrderExact': actual_positions == original_positions,
        'sourceOriginalCornerSha256': face_hash(original),
        'sourceReversedCornerSha256': face_hash([[f[0], f[2], f[1]] for f in original]),
        'actualCornerSha256': face_hash(observed), 'sampleTriangles': len(actual),
        'sampleCorners': len(actual)*3, 'mismatchCountAgainstOriginalOrder': len(differing),
        'differencesAgainstOriginalOrder': differing[:4], 'epsilonApplied': False,
        'fullNativeCornerReadbackPerformed': False, 'nativeNormalTangentReadbackAvailable': False}


def failure_basis(case):
    spec = FAILURES[case]
    directory = ROOT/'output/unreal'/spec['directory']
    report_path = directory/spec['report']
    require(sha(report_path) == spec['reportSha'], 'Actual immutable failed report differs')
    report = read(report_path)
    require(report['owner'] == spec['owner'] and report['status'] in ('failed', 'original-tree-native-failed')
            and report['nativeProcessId'] == spec['pid'], 'Exact failed native process required')
    raw_path = directory/(spec['stem']+'.log.json')
    process_path = directory/(spec['stem']+'-process.json')
    raw, process = read(raw_path), read(process_path)
    require(raw['code'] == 255 and raw['signal'] is None and raw['pid'] == spec['pid']
            and process['processFileSha256'] == sha(raw_path) and process['reportSha256'] == sha(report_path)
            and process['sourcePinsUnchangedAfterNative'] is True
            and len(process['sourcePinsBeforeNative']) == spec['sourceCount'], 'Actual failed terminal/source witness differs')
    for path, digest in process['sourcePinsBeforeNative'].items():
        require(sha(path) == digest, 'Frozen failed source changed: '+path)
    audit_path = directory/'failed-native-content-byte-audit-root-r1.json'
    require(sha(audit_path) == spec['auditSha'], 'Actual failed native byte audit changed')
    audit = read(audit_path)
    require(audit['status'] == 'actual-after-failed-native-old-content-byte-audit'
            and audit['checkedOriginalFiles'] == audit['baseContentCount'] == 4049
            and audit['changedOriginalFiles'] == audit['missingOriginalFiles'] == []
            and len(audit['newPackageFiles']) == spec['newPackages'], 'Failure must preserve all original scene/asset bytes')
    files = {str(directory/'Project/BreziTwin/Content'/p): sha(directory/'Project/BreziTwin/Content'/p)
             for p in audit['newPackageFiles']}
    map_path = directory/'Project/BreziTwin/Content/Brezi/Maps/Brezi.umap'
    files[str(map_path)] = sha(map_path)
    return {'project': str(directory/'Project/BreziTwin'), 'asset': spec['asset'],
        'report': pin(report_path), 'rawProcess': pin(raw_path), 'process': pin(process_path),
        'byteAudit': pin(audit_path), 'sourcePins': process['sourcePinsBeforeNative'],
        'failedProjectPackagePins': files, 'guard': pin(ROOT/spec['guard']),
        'oldSceneMapUnchangedByFailedImport': True}


def source_groups(case):
    g = module('readonly_'+case+'_frozen_guard', ROOT/FAILURES[case]['guard'])
    groups = []
    if case == 'tree':
        bundle = g.load_source()
        document, binary = bundle['original'], bundle['binaryPath'].read_bytes()
        offset = 0
        for section, primitive in enumerate(document['meshes'][0]['primitives']):
            count = document['accessors'][primitive['indices']]['count']//3
            indices = [0, 1, count//2, count-1]
            groups.append({'section': section, 'lod': 0, 'sourceTriangles': count,
                'triangleIndices': [offset+j for j in indices], 'sourceLocalTriangleIndices': indices,
                'uvChannels': 2, 'sourceOriginalCorners': [original_face(document, binary, primitive, j) for j in indices]})
            offset += count
        return groups, {'sourceTriangles': 2062487, 'sourceSections': 3, 'sourceLods': 1}
    bundle = g.source()
    document, binary = bundle['gltf'], bundle['binaries'][0]
    primitive = document['meshes'][0]['primitives'][0]
    indices = [0, 1, 1192, 2383]
    for lod in range(3):
        groups.append({'section': 0, 'lod': lod, 'sourceTriangles': 2384,
            'triangleIndices': indices, 'sourceLocalTriangleIndices': indices, 'uvChannels': 1,
            'sourceOriginalCorners': [original_face(document, binary, primitive, j) for j in indices]})
    return groups, {'sourceTriangles': 2384, 'sourceSections': 1, 'sourceLods': 3}


def primary_pins():
    engine = Path('/Users/Shared/Epic Games/UE_5.8/Engine')
    paths = ['Plugins/Interchange/Runtime/Source/Parsers/GLTFCore/Private/GLTF/ConversionUtilities.h',
        'Plugins/Interchange/Runtime/Source/Parsers/GLTFCore/Private/GLTFMeshFactory.cpp',
        'Plugins/Interchange/Runtime/Source/Pipelines/Public/InterchangeGenericAssetsPipelineSharedSettings.h',
        'Source/Runtime/MeshDescription/Public/MeshDescriptionBase.h',
        'Source/Runtime/StaticMeshDescription/Public/StaticMeshDescription.h',
        'Source/Runtime/Engine/Classes/Engine/StaticMesh.h']
    return {path: pin(engine/path) for path in paths}


def preflight(output):
    output = Path(output).resolve()
    require(output.is_relative_to(ROOT/'output/unreal') and not output.exists(), 'Fresh diagnostic output required')
    cases, inputs = {}, {str(ROOT/OWNER): sha(ROOT/OWNER)}
    for case in FAILURES:
        basis = failure_basis(case)
        groups, counts = source_groups(case)
        cases[case] = {**basis, 'groups': groups, 'expectedCounts': counts}
        inputs.update(basis['sourcePins']); inputs.update(basis['failedProjectPackagePins'])
        for key in ('report', 'rawProcess', 'process', 'byteAudit', 'guard'):
            row = basis[key]; inputs[row['path']] = row['sha256']
    for row in primary_pins().values():
        inputs[row['path']] = row['sha256']
    output.mkdir()
    value = {'schema': SCHEMA, 'owner': OWNER, 'status': 'source-only-readonly-diagnostic-native-pending',
        'cases': cases, 'inputFiles': inputs, 'primaryApiPins': primary_pins(),
        'nativeExecuted': False, 'sceneLoadedOrChanged': False, 'assetMutationApisCalled': False,
        'guardRelaxed': False, 'nativeAppearanceAccepted': False,
        'hypothesis': 'Original glTF index order may already map to UE clockwise facing; an additional reversal is tested separately.',
        'sampleCornersPerGroup': 12, 'fullNativeCornerReadbackPerformed': False,
        'nativeNormalTangentReadbackAvailable': False}
    write(output/'import-basis-diagnostic-plan.json', value)
    print(json.dumps(pin(output/'import-basis-diagnostic-plan.json')))


def vec(value, axes='xyz'):
    return [float(getattr(value, axis)) for axis in axes]


def main():
    import unreal as u
    path = Path(os.environ['BREZI_IMPORT_BASIS_DIAGNOSTIC_PLAN']).resolve()
    require(sha(path) == os.environ['BREZI_IMPORT_BASIS_DIAGNOSTIC_PLAN_SHA256'], 'Selected diagnostic plan changed')
    plan = read(path)
    require(plan['schema'] == SCHEMA and plan['owner'] == OWNER
            and plan['status'] == 'source-only-readonly-diagnostic-native-pending'
            and plan['primaryApiPins'] == primary_pins(), 'Typed immutable diagnostic required')
    for p, digest in plan['inputFiles'].items():
        require(sha(p) == digest, 'Consumed diagnostic/failure source changed: '+p)
    case = os.environ['BREZI_IMPORT_BASIS_DIAGNOSTIC_CASE']
    require(case in FAILURES, 'Unknown failed import case')
    basis = plan['cases'][case]
    require(Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir())).resolve() == Path(basis['project']),
            'Diagnostic may load only the exact failed project')
    result_path = path.parent/('native-'+case+'-diagnostic.json')
    require(not result_path.exists(), 'Diagnostic result is immutable; use a new revision to repeat')
    mesh = u.EditorAssetLibrary.load_asset(basis['asset'])
    require(isinstance(mesh, u.StaticMesh), 'Saved partial original mesh missing')
    rows, lods = [], {}
    for group in basis['groups']:
        lod = group['lod']; description = mesh.get_static_mesh_description(lod)
        require(description, 'Partial saved source MeshDescription missing')
        if lod not in lods:
            lods[lod] = {'sourceDescriptionTriangles': description.get_triangle_count(),
                'sourceDescriptionPolygons': description.get_polygon_count(),
                'sourceDescriptionPolygonGroups': description.get_polygon_group_count(),
                'sourceDescriptionVertices': description.get_vertex_count(),
                'sourceDescriptionVertexInstances': description.get_vertex_instance_count(),
                'renderTriangles': mesh.get_num_triangles(lod), 'renderSections': mesh.get_num_sections(lod)}
        observed, sections = [], []
        for index in group['triangleIndices']:
            triangle = u.TriangleID(id_value=index)
            sections.append(int(description.get_triangle_polygon_group(triangle).id_value))
            face = []
            for corner in range(3):
                vi = description.get_triangle_vertex_instance(triangle, corner)
                point = vec(description.get_vertex_position(description.get_vertex_instance_vertex(vi)))
                for channel in range(group['uvChannels']):
                    point += vec(description.get_vertex_instance_uv(vi, channel), 'xy')
                face.append(tuple(point))
            observed.append(face)
        rows.append({'section': group['section'], 'lod': lod, 'sampleTriangleIndices': group['triangleIndices'],
            'actualSectionIds': sections, 'actualRawCorners': observed,
            'sourceOriginalRawCorners': group['sourceOriginalCorners'],
            'comparison': comparison(observed, group['sourceOriginalCorners']),
            'sourceSectionPolygonCount': description.get_num_polygon_group_polygons(u.PolygonGroupID(id_value=group['section']))})
    bounds = mesh.get_bounds()
    result = {'schema': SCHEMA, 'owner': OWNER, 'status': 'measured-readonly-import-basis-diagnostic',
        'case': case, 'nativeProcessId': os.getpid(), 'completedAt': datetime.now(timezone.utc).isoformat(),
        'plan': pin(path), 'failedReport': basis['report'], 'failedByteAudit': basis['byteAudit'],
        'asset': mesh.get_path_name(), 'lodCount': mesh.get_num_lods(),
        'materialSlots': [str(row.get_editor_property('imported_material_slot_name'))
            for row in mesh.get_editor_property('static_materials')],
        'lodCounts': lods, 'bounds': {'originCm': vec(bounds.origin), 'extentCm': vec(bounds.box_extent)},
        'groups': rows, 'totalSampleTriangles': sum(len(row['sampleTriangleIndices']) for row in rows),
        'totalSampleCorners': sum(row['comparison']['sampleCorners'] for row in rows),
        'assetLoadCallsExecuted': True, 'sceneLoadedOrChanged': False, 'assetMutationApisCalled': False,
        'guardRelaxed': False, 'nativeApplied': False, 'nativeAppearanceAccepted': False,
        'nativeNormalTangentReadbackAvailable': False, 'fullNativeCornerReadbackPerformed': False,
        'allSampleGroupsOriginalOrderExact': all(row['comparison']['sourceOriginalOrderExact'] for row in rows),
        'allSampleGroupsReversedOrderExact': all(row['comparison']['sourceReversedOrderExact'] for row in rows)}
    for p, digest in plan['inputFiles'].items():
        require(sha(p) == digest, 'Read-only diagnostic changed protected/source/package bytes: '+p)
    write(result_path, result)
    print(json.dumps({'result': pin(result_path), 'originalOrderExact': result['allSampleGroupsOriginalOrderExact'],
        'reversedOrderExact': result['allSampleGroupsReversedOrderExact'], 'sceneLoadedOrChanged': False}))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight', type=Path)
    args = parser.parse_args()
    if args.preflight:
        preflight(args.preflight)
    else:
        main()
