"""One isolated fuller connected-canopy study; no native import or acceptance.

Frozen original primitive arrays remain byte-exact prefixes. New irregular
annual twigs attach to existing branch curves, using the same licensed leaf
photos. Missing near leaf identities are restored in mid/far; density is not
reduced as a substitute for tessellation. Source alpha unions decide whether
this treatment produces meaningful mass, separately from native appearance.
"""
import hashlib
import json
import math
from pathlib import Path
import random
import struct
from collections import Counter
from copy import deepcopy

import numpy as np
from PIL import Image, ImageDraw
from shapely.geometry import MultiPoint

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-canopy-fullness-study.py'
SOURCE = ROOT / 'output/unreal/exterior-canopy-growth-20260930-r1c-study'
DIAGNOSTIC = ROOT / 'output/unreal/exterior-canopy-diagnostic-20261001-r1b/diagnostic.json'
OUTPUT = ROOT / 'output/unreal/exterior-canopy-fullness-20261001-r1-study'
BARK = 'ph_tree_small_02_branches'
SEED = 601201441
ATTRIBUTE_TYPES = {'POSITION': 'VEC3', 'NORMAL': 'VEC3', 'TANGENT': 'VEC4',
                   'TEXCOORD_0': 'VEC2', 'COLOR_0': 'VEC4'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).write_text(json.dumps(value, indent=2) + '\n')


def curve(points, t):
    a, b, c = np.asarray(points, dtype=float)
    return a * (1-t)**2 + b * 2*t*(1-t) + c * t*t


def fitted(p, fit):
    p = np.asarray(p, dtype=float).copy()
    weight = np.clip((p[..., 2]-50)/70, 0, 1)
    p[..., :2] *= (1+(fit['outerXYFactor']-1)*weight)[..., None]
    p[..., 2] = np.where(p[..., 2] <= 50, p[..., 2],
                         50+(p[..., 2]-50)*fit['upperZFactor'])
    return p


def unit(p):
    p = np.asarray(p, dtype=float)
    return p / np.linalg.norm(p)


def frames(p, uv, faces):
    a, b, c = p[faces[:, 0]], p[faces[:, 1]], p[faces[:, 2]]
    e1, e2 = b-a, c-a
    face = np.cross(e1, e2)
    require(np.min(np.linalg.norm(face, axis=1)) > 1e-12, 'New degenerate face')
    du, dv = uv[faces[:, 1]]-uv[faces[:, 0]], uv[faces[:, 2]]-uv[faces[:, 0]]
    det = du[:, 0]*dv[:, 1]-du[:, 1]*dv[:, 0]
    require(np.min(np.abs(det)) > 1e-12, 'New degenerate UV')
    tangent = (e1*dv[:, 1, None]-e2*du[:, 1, None])/det[:, None]
    bitangent = (e2*du[:, 0, None]-e1*dv[:, 0, None])/det[:, None]
    n, t, bt = np.zeros_like(p), np.zeros_like(p), np.zeros_like(p)
    for k in range(3):
        np.add.at(n, faces[:, k], face)
        np.add.at(t, faces[:, k], tangent)
        np.add.at(bt, faces[:, k], bitangent)
    n /= np.linalg.norm(n, axis=1)[:, None]
    t -= n*np.sum(t*n, axis=1)[:, None]
    t /= np.linalg.norm(t, axis=1)[:, None]
    sign = np.where(np.sum(np.cross(n, t)*bt, axis=1) < 0, -1., 1.)
    return n.astype('<f4'), np.column_stack([t, sign]).astype('<f4')


def geometry(native, uv, faces):
    p = np.asarray(native, dtype=float)[:, [0, 2, 1]]/100
    uv = np.asarray(uv, dtype=float)
    # The native-to-glTF axis reflection requires the same winding reversal as
    # the frozen garden/canopy writer; frames then describe the same leaf side.
    faces = np.asarray(faces, dtype=np.uint32)[:, [0, 2, 1]]
    n, t = frames(p, uv, faces)
    return {'POSITION': p.astype('<f4'), 'NORMAL': n, 'TANGENT': t,
            'TEXCOORD_0': uv.astype('<f4'),
            'COLOR_0': np.ones((len(p), 4), dtype='<f4'),
            'indices': faces.reshape(-1).astype('<u4')}


def leaf_geometry(leaf, lod, fit):
    along = unit(leaf['along'])
    side = unit(np.cross(along, [0, 0, 1]))
    normal = unit(np.cross(side, along))
    c, s = math.cos(leaf['roll']), math.sin(leaf['roll'])
    side, normal = side*c+normal*s, normal*c-side*s
    length, width = leaf['length'], leaf['length']*leaf['aspect']
    columns = [0, .5, 1] if lod < 2 else [0, 1]
    points, uv, faces = [], [], []
    for t in (0, .5, 1):
        for u in columns:
            x = u-.5
            fold = length*(leaf['curl']*math.sin(math.pi*t)
                           + .025*math.sin(math.pi*t)*(1-abs(x)*2))
            twist = length*leaf['twist']*x*t
            points.append(np.asarray(leaf['base'])+along*length*t
                          + side*width*x+normal*(fold+twist))
            uv.append([1-u if leaf['mirror'] else u, 1-t])
    n = len(columns)
    for j in range(2):
        for k in range(n-1):
            a, b = j*n+k, (j+1)*n+k
            faces.extend([(a, b, a+1), (a+1, b, b+1)])
    return geometry(fitted(points, fit), uv, faces)


def twig_geometry(twig, lod, fit):
    segments, sides = (3, 5) if lod == 0 else (2, 4) if lod == 1 else (1, 3)
    path = [curve(twig['points'], t) for t in np.linspace(0, 1, segments+1)]
    chord = unit(path[-1]-path[0])
    stable = unit(np.cross(chord, [0, 0, 1]))
    points, uv, faces, distance = [], [], [], 0.
    for j, p in enumerate(path):
        t = j/segments
        direction = unit(path[min(segments, j+1)]-path[max(0, j-1)])
        a = unit(stable-direction*np.dot(stable, direction))
        b = unit(np.cross(direction, a))
        radius = twig['radius']*(1-t)+twig['tipRadius']*t
        if j:
            distance += np.linalg.norm(path[j]-path[j-1])
        for k in range(sides+1):
            phi = math.tau*k/sides
            points.append(p+radius*(a*math.cos(phi)+b*math.sin(phi)))
            uv.append([math.tau*twig['radius']*k/sides/25, distance/25])
    for j in range(segments):
        for k in range(sides):
            a, b = j*(sides+1)+k, (j+1)*(sides+1)+k
            faces.extend([(a, a+1, b), (a+1, b+1, b)])
    return geometry(fitted(points, fit), uv, faces)


def decode(path):
    raw = Path(path).read_bytes()
    require(struct.unpack_from('<4sII', raw) == (b'glTF', 2, len(raw)), 'GLB header')
    length, kind = struct.unpack_from('<II', raw, 12)
    require(kind == 0x4e4f534a, 'GLB JSON')
    d = json.loads(raw[20:20+length]); offset = 20+length
    n, kind = struct.unpack_from('<II', raw, offset)
    require(kind == 0x004e4942 and offset+8+n == len(raw), 'GLB BIN')
    binary = raw[offset+8:]
    def array(index):
        a = d['accessors'][index]; v = d['bufferViews'][a['bufferView']]
        dtype = {5126: '<f4', 5125: '<u4'}[a['componentType']]
        cols = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4}[a['type']]
        require(not v.get('byteStride') and not a.get('sparse'), 'Unexpected accessor')
        return np.frombuffer(binary, dtype=dtype, count=a['count']*cols,
                             offset=v['byteOffset']+a.get('byteOffset', 0)).reshape(-1, cols).copy()
    nodes = []
    for node in d['nodes']:
        parts = {}
        for primitive in d['meshes'][node['mesh']]['primitives']:
            key = d['materials'][primitive['material']]['name']
            parts[key] = {name: array(i) for name, i in primitive['attributes'].items()}
            parts[key]['indices'] = array(primitive['indices']).reshape(-1)
        nodes.append(parts)
    return nodes


def joined(original, additions):
    if not additions:
        return {key: value.copy() for key, value in original.items()}
    result = {key: np.concatenate([original[key], *[x[key] for x in additions]])
              for key in ATTRIBUTE_TYPES}
    offset = len(original['POSITION']); indices = [original['indices']]
    for part in additions:
        indices.append(part['indices']+offset); offset += len(part['POSITION'])
    result['indices'] = np.concatenate(indices).astype('<u4')
    return result


def saved_glb(path, mesh_id, nodes):
    d = {'asset': {'version': '2.0', 'generator': OWNER}, 'scene': 0,
         'scenes': [{'nodes': [0, 1, 2]}], 'nodes': [], 'meshes': [],
         'buffers': [], 'bufferViews': [], 'accessors': [],
         'materials': [{'name': key} for key in nodes[0]]}
    data = bytearray()
    def accessor(array, type_name, target):
        while len(data) % 4:
            data.append(0)
        array = np.asarray(array, dtype='<u4' if type_name == 'SCALAR' else '<f4')
        start = len(data); block = array.tobytes(); data.extend(block)
        d['bufferViews'].append({'buffer': 0, 'byteOffset': start, 'byteLength': len(block), 'target': target})
        record = {'bufferView': len(d['bufferViews'])-1, 'componentType': 5125 if type_name == 'SCALAR' else 5126,
                  'count': len(array), 'type': type_name}
        if type_name == 'VEC3':
            record.update(min=array.min(axis=0).tolist(), max=array.max(axis=0).tolist())
        d['accessors'].append(record)
        return len(d['accessors'])-1
    for lod, parts in enumerate(nodes):
        name = mesh_id+'_LOD'+str(lod); primitives = []
        for material, (key, part) in enumerate(parts.items()):
            attributes = {key: accessor(part[key], kind, 34962) for key, kind in ATTRIBUTE_TYPES.items()}
            indices = accessor(part['indices'], 'SCALAR', 34963)
            primitives.append({'attributes': attributes, 'indices': indices, 'material': material, 'mode': 4})
        d['nodes'].append({'name': name, 'mesh': lod}); d['meshes'].append({'name': name, 'primitives': primitives})
    d['buffers'] = [{'byteLength': len(data)}]
    text = json.dumps(d, separators=(',', ':')).encode(); text += b' '*((-len(text)) % 4)
    path.write_bytes(struct.pack('<4sII', b'glTF', 2, 28+len(text)+len(data))
                     + struct.pack('<II', len(text), 0x4e4f534a)+text
                     + struct.pack('<II', len(data), 0x004e4942)+data)


def inside(parts, row):
    points = np.concatenate([x['POSITION'][:, [0, 2, 1]]*100 for x in parts])
    bounds = row['allLodBoundsCm']
    return (np.all(points >= np.asarray(bounds['min'])-.0002)
            and np.all(points <= np.asarray(bounds['max'])+.0002)
            and np.max(np.linalg.norm(points[:, :2], axis=1)) <= row['radialEnvelopeCm']+.0002
            and np.min(points[:, 2]) > 50.01)


def appendage_candidates(row, morph, proof):
    rng = random.Random(SEED+int(morph['variant'])*7919+int(morph['heightCm'])*17)
    fit = proof['authoringFit']; clusters = morph['clusters']; height = morph['heightCm']
    centers = np.asarray([fitted(x['center'], fit) for x in clusters])
    radius = row['radialEnvelopeCm']
    weights = []
    for i, p in enumerate(centers):
        z = p[2]/height; r = np.linalg.norm(p[:2])/radius; yaw = math.atan2(p[1], p[0])
        middle = math.exp(-((z-.53)/.25)**2)
        inner = .25+1.50*max(0., 1-r)**.70
        sector = .62+.38*math.sin(yaw*2.1+z*4.3+morph['variant']*.77)**2
        uneven = rng.uniform(.30, 1.65)
        weights.append(middle*inner*sector*uneven)
    weights = np.asarray(weights); weights /= weights.mean()
    originals = Counter(x['cluster'] for x in morph['leaves'])
    target = len(morph['leaves'])
    accepted_twigs, accepted_leaves, quotas, rejected = [], [], [], 0
    for cid, cluster in enumerate(clusters):
        original_leaves = [x for x in morph['leaves'] if x['cluster'] == cid]
        parent = morph['branches'][cluster['branch']]
        supported = [i for i, x in enumerate(morph['branches'])
                     if x.get('terminalLeafShoot') and x['parent'] == cluster['branch']]
        desired = max(0, round(originals[cid]*weights[cid]))
        nodes = morph['growth']['leavesPerTerminalShoot']
        shoots = max(0, round(desired/nodes)); made = 0
        for shoot in range(shoots):
            for attempt in range(16):
                parent_id = cluster['branch'] if rng.random() < .65 else rng.choice(supported)
                actual_parent = morph['branches'][parent_id]
                # Endpoints are common to all original bark tessellations.
                # Attaching there avoids a Bezier/chord separation in far LOD.
                parent_t = 1.; start = curve(actual_parent['points'], parent_t)
                incoming = unit(np.asarray(actual_parent['points'][-1])-actual_parent['points'][0])
                toward = math.atan2(-start[1], -start[0])
                yaw = toward+rng.uniform(-1.30, 1.30)
                if rng.random() < .22:
                    yaw = math.atan2(incoming[1], incoming[0])+rng.uniform(-1.8, 1.8)
                length = rng.uniform(25, 43)*( .84 if morph['family'] == 'orchard' else 1.)
                end = start+np.array([math.cos(yaw)*length, math.sin(yaw)*length,
                                      rng.uniform(-.25, .35)*length])
                bend = (start+end)/2+np.array([rng.uniform(-2, 2), rng.uniform(-2, 2), rng.uniform(-3.5, 3.5)])
                twig = {'id': len(accepted_twigs), 'parentOriginalBranch': parent_id,
                        'parentT': parent_t, 'cluster': cid, 'points': [start.tolist(), bend.tolist(), end.tolist()],
                        'radius': rng.uniform(.10, .15), 'tipRadius': rng.uniform(.035, .065)}
                leaves = []
                for k in range(nodes):
                    t = .10+.86*(k+.5)/nodes
                    az = yaw+(-1 if k % 2 else 1)*rng.uniform(.52, 1.25)
                    tilt = rng.uniform(-.52, .48)
                    leaf = {'twig': twig['id'], 'cluster': cid, 't': t,
                            'base': curve(twig['points'], t).tolist(),
                            'length': rng.uniform(8.3, 12.7)*(.82 if morph['family'] == 'orchard' else 1.),
                            'aspect': original_leaves[0]['aspect'],
                            'along': [math.cos(az)*math.cos(tilt), math.sin(az)*math.cos(tilt), math.sin(tilt)],
                            'roll': rng.uniform(-.92, .92), 'curl': rng.uniform(-.12, .17),
                            'twist': rng.uniform(-.12, .12), 'mirror': rng.random() < .5}
                    leaves.append(leaf)
                geometry_sets = [twig_geometry(twig, lod, fit) for lod in range(3)]
                geometry_sets += [leaf_geometry(x, 0, fit) for x in leaves]
                geometry_sets += [leaf_geometry(x, 2, fit) for x in leaves]
                if inside(geometry_sets, row):
                    accepted_twigs.append(twig); accepted_leaves.extend(leaves); made += nodes; break
                rejected += 1
        quotas.append({'cluster': cid, 'normalizedMassWeight': float(weights[cid]),
                       'originalLeaves': originals[cid], 'targetAdditionalLeaves': desired,
                       'actualAdditionalLeaves': made})
    return accepted_twigs, accepted_leaves, quotas, rejected, target


def restore_near_leaf(near, index, lod):
    selected = np.arange(index*9, index*9+9)
    if lod == 1:
        result = {k: near[k][selected].copy() for k in ATTRIBUTE_TYPES}
        result['indices'] = near['indices'][index*24:index*24+24].copy()-index*9
        return result
    selection = selected[[0, 2, 3, 5, 6, 8]]
    native = near['POSITION'][selection][:, [0, 2, 1]]*100
    uv = near['TEXCOORD_0'][selection]
    faces = [(0, 2, 1), (1, 2, 3), (2, 4, 3), (3, 4, 5)]
    return geometry(native, uv, faces)


def validate_actual(nodes, originals, row):
    evidence = []
    for lod, parts in enumerate(nodes):
        prefixes, count, bounds_points = {}, 0, []
        for key, part in parts.items():
            old = originals[lod][key]
            for attr, values in old.items():
                require(part[attr][:len(values)].tobytes() == values.tobytes(), 'Original array prefix changed '+attr)
            prefixes[key] = {attr: hashlib.sha256(values.tobytes()).hexdigest() for attr, values in old.items()}
            p = part['POSITION'].astype(float); n = part['NORMAL'].astype(float); t = part['TANGENT'].astype(float)
            f = part['indices'].reshape(-1, 3); uv = part['TEXCOORD_0'].astype(float)
            require(all(np.isfinite(x).all() for x in [p, n, t, uv, part['COLOR_0']]), 'Non-finite saved attribute')
            require(np.max(np.abs(np.linalg.norm(n, axis=1)-1)) < 3e-5, 'Saved normal not unit')
            require(np.max(np.abs(np.linalg.norm(t[:, :3], axis=1)-1)) < 3e-5, 'Saved tangent not unit')
            require(np.max(np.abs(np.sum(n*t[:, :3], axis=1))) < 3e-5, 'Saved tangent not orthogonal')
            require(set(np.unique(t[:, 3])) <= {-1., 1.}, 'Saved tangent handedness')
            face = np.cross(p[f[:, 1]]-p[f[:, 0]], p[f[:, 2]]-p[f[:, 0]])
            require(np.min(np.linalg.norm(face, axis=1)) > 1e-12, 'Saved degenerate triangle')
            mean_normal = (n[f[:, 0]]+n[f[:, 1]]+n[f[:, 2]])/3
            require(np.min(np.sum(face*mean_normal, axis=1)) > 0, 'Saved opposed normal/winding')
            native = p[:, [0, 2, 1]]*100; bounds_points.append(native); count += len(f)
        p = np.concatenate(bounds_points); b = row['allLodBoundsCm']
        require(np.all(p >= np.asarray(b['min'])-.001) and np.all(p <= np.asarray(b['max'])+.001), 'Saved source bounds exceeded')
        require(np.max(np.linalg.norm(p[:, :2], axis=1)) <= row['radialEnvelopeCm']+.001, 'Saved source radial cap exceeded')
        evidence.append({'lod': lod, 'triangles': count, 'vertices': len(p),
                         'boundsCm': {'min': p.min(axis=0).tolist(), 'max': p.max(axis=0).tolist()},
                         'radialEnvelopeCm': float(np.max(np.linalg.norm(p[:, :2], axis=1))),
                         'originalAttributeAndIndexPrefixesSha256': prefixes,
                         'allFiniteUnitOrthogonalFramesAndWindingVerified': True,
                         'allWithinOriginalCrownEnvelope': True})
    return evidence


def build():
    require(not OUTPUT.exists(), 'Choose the one fresh immutable study output')
    OUTPUT.mkdir(); (OUTPUT/'glb').mkdir()
    (OUTPUT/'generator-source.py').write_bytes(Path(__file__).read_bytes())
    original_manifest = json.loads((SOURCE/'geometry-manifest.json').read_text())
    skeletons = json.loads((SOURCE/'growth-skeletons.json').read_text())
    morphology = json.loads((SOURCE/'morphology-audit.json').read_text())
    recipes = json.loads((SOURCE/'material-manifest.json').read_text())
    original_plan = json.loads((SOURCE/'canopy-plan.json').read_text())
    input_pins = {str(SOURCE/name): sha(SOURCE/name) for name in ['geometry-manifest.json', 'growth-skeletons.json', 'morphology-audit.json', 'material-manifest.json', 'canopy-plan.json']}
    input_pins[str(DIAGNOSTIC)] = sha(DIAGNOSTIC)
    input_pins[str(Path(__file__).resolve())] = sha(Path(__file__).resolve())
    input_pins[str(OUTPUT/'generator-source.py')] = sha(OUTPUT/'generator-source.py')
    for recipe in recipes.values():
        for mapping in recipe['maps'].values():
            require(sha(mapping['path']) == mapping['sha256'], 'Photo input changed')
            input_pins[mapping['path']] = mapping['sha256']
    records, audits, additions = [], {}, {}
    for row in original_manifest['meshes']:
        require(sha(row['glbPath']) == row['glbSha256'], 'Original GLB changed')
        input_pins[row['glbPath']] = row['glbSha256']
        original = decode(row['glbPath']); morph = skeletons[row['id']]; proof = morphology['meshes'][row['id']]
        twigs, leaves, quotas, rejected, target = appendage_candidates(row, morph, proof)
        leaf_key = morph['leafMaterial']; fit = proof['authoringFit']; nodes = []
        restored_counts = []
        for lod in range(3):
            twig_parts = [twig_geometry(x, lod, fit) for x in twigs]
            leaf_parts = [leaf_geometry(x, lod, fit) for x in leaves]
            missing = [] if lod == 0 else sorted(set(range(row['leafCount']))-set(proof['lodLeafIds'][str(lod)]))
            leaf_parts = [restore_near_leaf(original[0][leaf_key], i, lod) for i in missing]+leaf_parts
            restored_counts.append(len(missing))
            nodes.append({BARK: joined(original[lod][BARK], twig_parts),
                          leaf_key: joined(original[lod][leaf_key], leaf_parts)})
        new_id = row['id'].replace('canopy_growth_', 'canopy_fullness_')
        glb = OUTPUT/'glb'/(new_id+'.glb'); saved_glb(glb, new_id, nodes)
        actual = decode(glb); validation = validate_actual(actual, original, row)
        lods = [{'level': lod, 'nodeName': new_id+'_LOD'+str(lod),
                 'triangles': v['triangles'], 'vertices': v['vertices'], 'expectedBoundsCm': v['boundsCm'],
                 'radialEnvelopeCm': v['radialEnvelopeCm'], 'leafCount': row['leafCount']+len(leaves),
                 'originalRetainedLeaves': row['lods'][lod]['leafCount'], 'restoredNearLeafIdentities': restored_counts[lod],
                 'newLeaves': len(leaves), 'derivation': 'Original arrays preserved; all original near leaf identities plus all irregular added connected annual-shoot leaves; tessellation alone reduces far geometry'}
                for lod, v in enumerate(validation)]
        record = {**deepcopy(row), 'id': new_id, 'sourceGrowthMasterId': row['id'],
                  'glbPath': str(glb), 'glbSha256': sha(glb), 'lods': lods,
                  'leafCount': row['leafCount']+len(leaves), 'originalLeafCount': row['leafCount'],
                  'newLeafCount': len(leaves), 'newConnectedAnnualTwigs': len(twigs),
                  'branches': row['branches']+len(twigs),
                  'form': 'Same connected original crown with irregular fuller inner/middle annual shoots; original natural gaps and envelope retained',
                  'nativeAppearanceAccepted': False}
        records.append(record)
        audits[new_id] = {'sourceMaster': row['id'], 'sourceNearLeaves': row['leafCount'],
                         'targetAdditionalLeavesTreatment': target, 'actualAdditionalLeaves': len(leaves),
                         'newAnnualTwigs': len(twigs), 'clusterAllocation': quotas, 'rejectedEnvelopeAttempts': rejected,
                         'originalBarkAndLeafPrimitivePrefixesByteExactAllLods': True,
                         'missingNearLeafIdsRestoredByLOD': restored_counts,
                         'savedDecodedGeometry': validation, 'nativeAppearanceAccepted': False}
        additions[new_id] = {'originalMorphologyPin': {'path': str(SOURCE/'growth-skeletons.json'), 'sha256': input_pins[str(SOURCE/'growth-skeletons.json')]},
                             'newTwigs': twigs, 'newLeaves': leaves, 'authoringFit': fit}
        print('FULLNESS_BUILT', new_id, 'addedLeaves', len(leaves), 'twigs', len(twigs), 'triangles', [x['triangles'] for x in lods], flush=True)
    counts = Counter(x['meshId'] for x in original_plan['canopyPlacements'])
    population = [sum(counts[r['sourceGrowthMasterId']]*r['lods'][lod]['triangles'] for r in records) for lod in range(3)]
    original_population = [sum(counts[r['id']]*r['lods'][lod]['triangles'] for r in original_manifest['meshes']) for lod in range(3)]
    plan = deepcopy(original_plan); remap = {r['sourceGrowthMasterId']: r['id'] for r in records}
    plan['originalCanopyPlacements'] = deepcopy(original_plan['canopyPlacements'])
    for row in plan['canopyPlacements']:
        row['meshId'] = remap[row['meshId']]
    plan.update(owner=OWNER, kind='isolated-fuller-connected-canopy-study',
                inputFiles=input_pins, nativeAppearanceAccepted=False, status='SOURCE_ONLY_NATIVE_PENDING',
                original78RootTransformsAndMetadataPreserved=True)
    for old, new in zip(original_plan['canopyPlacements'], plan['canopyPlacements']):
        require({k: v for k, v in old.items() if k != 'meshId'} == {k: v for k, v in new.items() if k != 'meshId'}, 'Original root metadata changed')
    manifest = {**deepcopy(original_manifest), 'owner': OWNER, 'revision': 'R1 one fuller connected annual-shoot treatment',
                'status': 'SOURCE_ONLY_NATIVE_PENDING', 'inputFiles': input_pins, 'meshes': records}
    write(OUTPUT/'geometry-manifest.json', manifest)
    (OUTPUT/'material-manifest.json').write_bytes((SOURCE/'material-manifest.json').read_bytes())
    write(OUTPUT/'morphology-additions.json', additions); write(OUTPUT/'geometry-validation.json', audits)
    plan['sourceOriginalGrowthPlan'] = {'path': str(SOURCE/'canopy-plan.json'), 'sha256': sha(SOURCE/'canopy-plan.json')}
    plan['sourceOriginalGrowthGeometry'] = {'path': str(SOURCE/'geometry-manifest.json'), 'sha256': sha(SOURCE/'geometry-manifest.json')}
    plan['fullnessGeometryManifest'] = {'path': str(OUTPUT/'geometry-manifest.json'), 'sha256': sha(OUTPUT/'geometry-manifest.json')}
    plan['geometryManifest'] = deepcopy(plan['fullnessGeometryManifest'])
    plan['additionsProof'] = {'path': str(OUTPUT/'morphology-additions.json'), 'sha256': sha(OUTPUT/'morphology-additions.json')}
    plan['decodedGeometryValidation'] = {'path': str(OUTPUT/'geometry-validation.json'), 'sha256': sha(OUTPUT/'geometry-validation.json')}
    plan['audit'] = {'status': 'source-only-fuller-connected-canopy-not-native-accepted',
                     'originalRootsPreserved': True, 'variants': 9, 'lods': 27,
                     'materialRecipesAdded': 0, 'perMesh': audits,
                     'allInstancesTriangleBudgetByLod': population,
                     'originalAllInstancesTriangleBudgetByLod': original_population,
                     'nativeAppearanceAccepted': False}
    write(OUTPUT/'canopy-plan.json', plan)
    summary = {'status': 'SOURCE_GENERATED_MEASURED_VISUAL_REVIEW_PENDING_NATIVE_NO_GO', 'owner': OWNER,
               'masters': 9, 'lods': 27, 'originalRoots': 78, 'rootTransformsPreserved': True,
               'originalPrimitiveAttributeAndIndexPrefixesByteExact': True,
               'oldCrownEnvelopeAndBasal50cmPreserved': True, 'sourceRecipesAndPhotosByteExact': True,
               'allInstancesTriangleBudgetByLod': population, 'originalAllInstancesTriangleBudgetByLod': original_population,
               'nativeAppearanceAccepted': False, 'nativePerformanceAccepted': False,
               'sourceAppearanceAccepted': False, 'sourceAlphaUnionMeasured': False,
               'inputPins': input_pins, 'generatorPin': {'path': str(OUTPUT/'generator-source.py'), 'sha256': sha(OUTPUT/'generator-source.py')}}
    write(OUTPUT/'summary.json', summary)
    return records, original_manifest['meshes'], recipes, summary


def raster(part, key, recipe, matrix, right, lo, size, cm_per_pixel, hull_mask):
    native = part['POSITION'][:, [0, 2, 1]].astype(float)*100
    native = native@matrix.T
    points = np.column_stack([native@right, native[:, 2]])
    points = (points-lo)/cm_per_pixel+1
    uv = part['TEXCOORD_0']; triangles = part['indices'].reshape(-1, 3)
    opacity = np.asarray(Image.open(recipe['maps']['alpha']['path']).convert('L'), dtype=float)/255
    albedo = np.asarray(Image.open(recipe['maps']['albedo']['path']).convert('RGB'), dtype=float)/255
    th, tw = opacity.shape; ah, aw = albedo.shape[:2]
    opaque, alpha_mask = np.zeros(tuple(size), bool), np.zeros(tuple(size), bool)
    image = np.full((*size, 3), 237, dtype=np.uint8)
    image[hull_mask] = [205, 212, 218]
    depth_buffer = np.full(tuple(size), -np.inf)
    normal = part['NORMAL'][:, [0, 2, 1]].astype(float)@matrix.T
    light = unit([-.40, -.30, .86])
    for face in triangles:
        p, tex = points[face], uv[face]
        mn = np.maximum(0, np.floor(p.min(axis=0)).astype(int))
        mx = np.minimum(size-1, np.ceil(p.max(axis=0)).astype(int))
        if np.any(mx < mn):
            continue
        x, y = np.arange(mn[0], mx[0]+1)+.5, np.arange(mn[1], mx[1]+1)+.5
        xx, yy = np.meshgrid(x, y, indexing='ij'); a, b, c = p
        det = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(det) < 1e-10:
            continue
        b0 = ((b[1]-c[1])*(xx-c[0])+(c[0]-b[0])*(yy-c[1]))/det
        b1 = ((c[1]-a[1])*(xx-c[0])+(a[0]-c[0])*(yy-c[1]))/det
        b2 = 1-b0-b1; inside_mask = (b0 >= -1e-9)&(b1 >= -1e-9)&(b2 >= -1e-9)
        if not inside_mask.any():
            continue
        u = np.clip(b0*tex[0, 0]+b1*tex[1, 0]+b2*tex[2, 0], 0, 1)
        v = np.clip(b0*tex[0, 1]+b1*tex[1, 1]+b2*tex[2, 1], 0, 1)
        tu, tv = u*(tw-1), v*(th-1)
        tx, ty = np.floor(tu).astype(int), np.floor(tv).astype(int)
        tx1, ty1 = np.minimum(tw-1, tx+1), np.minimum(th-1, ty+1)
        fx, fy = tu-tx, tv-ty
        value = (opacity[ty, tx]*(1-fx)*(1-fy)+opacity[ty, tx1]*fx*(1-fy)
                 + opacity[ty1, tx]*(1-fx)*fy+opacity[ty1, tx1]*fx*fy)
        visible = inside_mask&(value >= recipe['opacityMaskClipValue'])
        block = (slice(mn[0], mx[0]+1), slice(mn[1], mx[1]+1))
        opaque[block] |= inside_mask; alpha_mask[block] |= visible
        view_direction = np.cross([0, 0, 1], right)
        depths = native[face]@view_direction
        depth = b0*depths[0]+b1*depths[1]+b2*depths[2]
        render = visible&(depth >= depth_buffer[block])
        if render.any():
            rgb = albedo[np.clip(np.rint(v*(ah-1)).astype(int), 0, ah-1),
                         np.clip(np.rint(u*(aw-1)).astype(int), 0, aw-1)]
            n = b0[..., None]*normal[face[0]]+b1[..., None]*normal[face[1]]+b2[..., None]*normal[face[2]]
            n /= np.maximum(np.linalg.norm(n, axis=-1)[..., None], 1e-10)
            diffuse = .64+.36*np.abs(n@light)
            rgb = np.clip(rgb*recipe.get('albedoScale', 1)*diffuse[..., None]*255, 0, 255).astype(np.uint8)
            image[block][render] = rgb[render]; depth_buffer[block][render] = depth[render]
    hull_pixels = hull_mask.sum()
    measure = {'opaqueCardUnionM2': float(opaque.sum()*cm_per_pixel**2/10000),
               'alphaLeafUnionM2': float(alpha_mask.sum()*cm_per_pixel**2/10000),
               'alphaLeafUnionFractionOfOriginalNearLeafConvexHull': float((alpha_mask&hull_mask).sum()/hull_pixels),
               'alphaOutsideOriginalNearLeafConvexHullM2': float((alpha_mask&~hull_mask).sum()*cm_per_pixel**2/10000)}
    union_image = np.full((*size, 3), 237, dtype=np.uint8)
    union_image[hull_mask] = [205, 212, 218]; union_image[opaque] = [125, 146, 135]
    union_image[alpha_mask] = [31, 86, 43]
    colored = Image.fromarray(image.transpose(1, 0, 2)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    union = Image.fromarray(union_image.transpose(1, 0, 2)).transpose(Image.Transpose.FLIP_TOP_BOTTOM)
    return measure, colored, union


def surface_areas(nodes, leaf_key):
    result = []
    for node in nodes:
        p = node[leaf_key]['POSITION'].astype(float); f = node[leaf_key]['indices'].reshape(-1, 3)
        result.append(float(np.linalg.norm(np.cross(p[f[:, 1]]-p[f[:, 0]], p[f[:, 2]]-p[f[:, 0]]), axis=1).sum()/2))
    return result


def comparisons(records, originals, recipes, summary):
    diag = json.loads(DIAGNOSTIC.read_text()); cameras = diag['nativeCameraLODSourceEstimate']
    measurements, area_records = [], []
    by_id = {row['id']: row for row in originals}
    for row in records:
        old_row = by_id[row['sourceGrowthMasterId']]
        old_nodes, new_nodes = decode(old_row['glbPath']), decode(row['glbPath'])
        key = next(key for key in old_nodes[0] if key != BARK)
        fraction = float((np.asarray(Image.open(recipes[key]['maps']['alpha']['path']).convert('L'))
                          >= recipes[key]['opacityMaskClipValue']*255).mean())
        a, b = surface_areas(old_nodes, key), surface_areas(new_nodes, key)
        area_records.append({'id': row['id'], 'originalLeafSurfaceAreaM2ByLOD': a,
                             'candidateLeafSurfaceAreaM2ByLOD': b,
                             'candidateToOriginalNearLeafSurfaceAreaRatios': [x/a[0] for x in b],
                             'candidateAreaRetentionRelativeFullerNear': [x/b[0] for x in b],
                             'sourceAlphaImageRetainedFraction': fraction,
                             'modeledAlphaAdjustedCandidateLeafAreaM2ByLOD': [x*fraction for x in b]})
        if not row['id'].endswith('_b'):
            continue
        family = row['id'].split('_')[2]
        choices = [x for x in cameras['metrics'] if x['meshId'] == old_row['id'] and x['visibleFrustumApproximation']]
        witness = sorted(choices, key=lambda x: x['distanceCm'])[len(choices)//2]
        instance = witness['row']; yaw = math.radians(instance['yawDeg'])
        rotation = np.array([[math.cos(yaw), -math.sin(yaw), 0], [math.sin(yaw), math.cos(yaw), 0], [0, 0, 1]])
        direction = np.asarray(instance['positionCm'])-np.asarray(cameras['camera']['eyeCm']); direction[2] = 0; direction = unit(direction)
        base_yaw = math.atan2(direction[1], direction[0])
        colored_page, union_page = Image.new('RGB', (3600, 2520), 'white'), Image.new('RGB', (3600, 2520), 'white')
        color_draw, union_draw = ImageDraw.Draw(colored_page), ImageDraw.Draw(union_page)
        family_measures = []
        for axis, offset in enumerate((0, math.pi/3, 2*math.pi/3)):
            azimuth = base_yaw+offset; forward = np.array([math.cos(azimuth), math.sin(azimuth), 0])
            right = unit(np.cross(forward, [0, 0, 1])); near = old_nodes[0][key]['POSITION'][:, [0, 2, 1]]*100@rotation.T
            projected = np.column_stack([near@right, near[:, 2]])
            all_new_points = np.concatenate([n[key]['POSITION'][:, [0, 2, 1]]*100@rotation.T for n in new_nodes])
            all_new_projection = np.column_stack([all_new_points@right, all_new_points[:, 2]])
            lo = np.minimum(projected.min(axis=0), all_new_projection.min(axis=0))-2
            hi = np.maximum(projected.max(axis=0), all_new_projection.max(axis=0))+2
            cm_per_pixel = 1.; size = np.ceil((hi-lo)/cm_per_pixel).astype(int)+3
            hull = MultiPoint(projected).convex_hull; hull_image = Image.new('1', tuple(size)); draw = ImageDraw.Draw(hull_image)
            draw.polygon([tuple((np.asarray(p)-lo)/cm_per_pixel+1) for p in hull.exterior.coords], fill=1)
            hull_mask = np.asarray(hull_image).T
            comparison = {'axisOffsetDegrees': offset*180/math.pi, 'originalNearHullM2': hull.area/10000,
                          'cameraSource': 'Original native canopy-lod horizontal direction at unchanged representative root; additional directions +60,+120 degrees',
                          'rootWitness': instance['id'], 'orthographicCmPerPixel': cm_per_pixel, 'lods': []}
            for lod in range(3):
                records_pair = []
                for which, nodes in enumerate((old_nodes, new_nodes)):
                    measure, color, union = raster(nodes[lod][key], key, recipes[key], rotation, right, lo, size, cm_per_pixel, hull_mask)
                    records_pair.append(measure)
                    label = ('ORIGINAL' if which == 0 else 'FULLER')+f' LOD{lod} axis{axis*60}'
                    for image, page, painter in ((color, colored_page, color_draw), (union, union_page, union_draw)):
                        image.thumbnail((580, 780)); x = (lod*2+which)*600; y = axis*840
                        page.paste(image, (x+10, y+45)); painter.text((x+10, y+10), label, fill='black')
                comparison['lods'].append({'lod': lod, 'original': records_pair[0], 'candidate': records_pair[1]})
            near_area = comparison['lods'][0]['candidate']['alphaLeafUnionM2']
            for x in comparison['lods']:
                x['candidateAlphaUnionRetentionFromFullerNear'] = x['candidate']['alphaLeafUnionM2']/near_area
                x['candidateAlphaUnionGainRelativeOriginalSameLOD'] = x['candidate']['alphaLeafUnionM2']/x['original']['alphaLeafUnionM2']
            family_measures.append(comparison)
            print('FULLNESS_ALPHA', row['id'], axis, [(x['original']['alphaLeafUnionFractionOfOriginalNearLeafConvexHull'], x['candidate']['alphaLeafUnionFractionOfOriginalNearLeafConvexHull'], x['candidateAlphaUnionRetentionFromFullerNear']) for x in comparison['lods']], flush=True)
        colored_page.save(OUTPUT/f'{family}-colored-source-comparison.png'); union_page.save(OUTPUT/f'{family}-alpha-union-comparison.png')
        measurements.append({'id': row['id'], 'axes': family_measures})
    measure = {'status': 'ACTUAL_SOURCE_GLBS_MEASURED_NO_NATIVE_ACCEPTANCE', 'owner': OWNER,
               'method': 'Hash-matched saved GLB leaf triangles, original source alpha bilinear mip0 at cutoff0.333. Orthographic1cm/pixel. Convex hull of original near leaves is a shared diagnostic domain, not realism gate. Colored panels use original albedo and approximate geometric diffuse for source inspection only. No native light, shadows, mip chain, TAA, overdraw, wind or GPU-selectedLOD trace.',
               'surfaceAreas': area_records, 'projectedAlphaUnions': measurements,
               'originalPhotosUnmodified': True, 'nativeAppearanceAccepted': False,
               'nativePerformanceAccepted': False}
    write(OUTPUT/'source-measurement.json', measure)
    summary.update(sourceAlphaUnionMeasured=True,
                   sourceMeasurement={'path': str(OUTPUT/'source-measurement.json'), 'sha256': sha(OUTPUT/'source-measurement.json')},
                   status='SOURCE_MEASURED_VISUAL_REVIEW_PENDING_NATIVE_NO_GO')
    write(OUTPUT/'summary.json', summary)
    print('FULLNESS_DONE', OUTPUT, summary['allInstancesTriangleBudgetByLod'], flush=True)


if __name__ == '__main__':
    comparisons(*build())
