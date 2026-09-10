"""Read-only frozen receiver/BVH validation; optional --source-root verifies canonical OBJ."""
import argparse
import hashlib
import json
import math
from pathlib import Path

PLUGIN = Path(__file__).resolve().parents[1]


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_topology(contract):
    objects = contract['receiverObjects']
    triangles = contract['triangles']
    nodes = contract['bvhNodes']
    ids = [obj['id'] for obj in objects]
    require(len(set(ids)) == len(ids) == 45, 'Receiver identity count changed')
    require(len(triangles) == 1076 and len(nodes) == 359, 'Frozen receiver topology changed')
    require(contract['runtimeGeometryChanged'] is False, 'Runtime geometry mutation is forbidden')
    faces = set()
    for triangle in triangles:
        identity = (triangle['objectId'], triangle['sourceFaceIndex'])
        require(identity[0] in ids and type(identity[1]) is int and identity[1] >= 0 and identity not in faces, 'Invalid triangle identity')
        faces.add(identity)
        vertices = triangle['verticesMetres']
        require(len(vertices) == 3 and all(len(v) == 3 and all(math.isfinite(x) for x in v) for v in vertices), 'Invalid triangle vertices')
    visited, leaves = set(), []

    def visit(index, depth):
        require(type(index) is int and 0 <= index < len(nodes) and index not in visited, 'Cyclic, repeated or invalid BVH node')
        require(depth < 64, 'GPU BVH stack capacity exceeded')
        visited.add(index)
        node = nodes[index]
        require(all(len(node[k]) == 3 and all(math.isfinite(v) for v in node[k]) for k in ['low', 'high']), 'Invalid BVH bounds')
        require(all(a <= b for a, b in zip(node['low'], node['high'])), 'Inverted BVH bounds')
        require(('children' in node) != ('triangles' in node), 'Ambiguous BVH node')
        if 'children' in node:
            require(len(node['children']) == 2, 'Nonbinary BVH')
            points = []
            for child in node['children']:
                require(type(child) is int and child > index, 'BVH must have source forward child indices')
                visit(child, depth + 1)
                points.extend([nodes[child]['low'], nodes[child]['high']])
        else:
            indices = node['triangles']
            require(0 < len(indices) <= 8, 'Invalid BVH leaf capacity')
            require(all(type(i) is int and 0 <= i < len(triangles) for i in indices), 'Invalid BVH triangle index')
            leaves.extend(indices)
            points = [v for i in indices for v in triangles[i]['verticesMetres']]
        require(all(node['low'][axis] - 1e-9 <= point[axis] <= node['high'][axis] + 1e-9 for point in points for axis in range(3)), 'BVH does not enclose its exact source geometry')

    visit(0, 0)
    require(len(visited) == len(nodes), 'Unreachable BVH nodes')
    require(sorted(leaves) == list(range(len(triangles))), 'Missing or duplicate receiver triangles in BVH')
    return {'receiverObjectCount': len(ids), 'receiverTriangleCount': len(triangles), 'bvhNodeCount': len(nodes)}


def verify(source_root=None):
    resource = PLUGIN / 'Resources/receiver-contract.json'
    binding = json.loads((PLUGIN / 'Resources/source-binding.json').read_text())
    require(sha(resource) == binding['contractSha256'], 'Receiver bytes differ from reviewed SHA256')
    header = (PLUGIN / 'Source/BreziCausticsProbe/Private/BreziCausticsContract.h').read_text()
    require(binding['contractSha256'] in header and hashlib.sha1(resource.read_bytes()).hexdigest() in header, 'Compiled receiver pins differ from resource bytes')
    contract = json.loads(resource.read_text())
    result = verify_topology(contract)
    geometry = {k: contract[k] for k in ['receiverObjects', 'triangles', 'bvhNodes']}
    require(hashlib.sha256(json.dumps(geometry, sort_keys=True, separators=(',', ':')).encode()).hexdigest() == binding['receiverGeometrySha256'], 'Reviewed receiver geometry changed')
    if source_root:
        root = Path(source_root)
        proof_path = root / 'output/unreal/hidden-collision-source-proof.json'
        require(sha(proof_path) == binding['canonicalProofSha256'], 'Canonical geometry preservation proof changed')
        proof = json.loads(proof_path.read_text())
        require(proof['status'] == 'canonical-geometry-unchanged-auxiliary-source-captured' and proof['everyCanonicalObjectRecordIdentical'] is True, 'Missing canonical preservation proof')
        for path, digest in contract['sourceSha256'].items():
            require(sha(root / path) == digest, 'Stale caustics source: ' + path)
        scene = json.loads((root / 'output/unreal/geometry/scene.json').read_text())
        by_id = {obj['id']: obj for obj in scene['objects']}
        require(len(by_id) == proof['canonicalObjects'] == 1895, 'Canonical object identity changed')
        for obj in contract['receiverObjects']:
            require(obj == {k: by_id[obj['id']][k] for k in obj}, 'Canonical receiver record changed: ' + obj['id'])
        vertices, actual, current = [], [], None
        source_ids = {obj['id'] for obj in contract['receiverObjects']}
        counts = dict.fromkeys(source_ids, 0)
        with (root / 'output/unreal/geometry/dom-mm.obj').open() as handle:
            for line in handle:
                fields = line.split()
                if not fields:
                    continue
                if fields[0] == 'o':
                    current = fields[1]
                elif fields[0] == 'v':
                    x, y, z = map(float, fields[1:4])
                    vertices.append([x / 1000, -y / 1000, z / 1000])
                elif fields[0] == 'f' and current in source_ids:
                    require(len(fields) == 4, 'Source receiver has nontriangle face')
                    points = [vertices[int(f.split('/')[0]) - 1] for f in fields[1:]]
                    actual.append({'objectId': current, 'sourceFaceIndex': counts[current], 'verticesMetres': points})
                    counts[current] += 1
        require(actual == contract['triangles'], 'Frozen triangles differ from exact canonical OBJ faces')
    return {'status': 'CPU-frozen-contract-validated', 'sourceFilesVerified': bool(source_root), 'contractSha256': sha(resource), **result, 'nativeBuildExecuted': False, 'gpuExecuted': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root')
    print(json.dumps(verify(parser.parse_args().source_root), indent=2))
