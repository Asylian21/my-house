"""Bounded authored broadleaf windbreak study; no new planting or species claim.

Pure Python generates a new immutable artifact from the inherited rural plan.
No original file, instance, material, collision or native package is modified.
Optional Blender preview compares identical cameras/materials, not Unreal proof.
"""
import argparse
from collections import Counter
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/realism-trees-geometry.py'
SEED = 60122693
PROFILES = ('irregular-oval', 'ascending-narrow', 'forked-spreading')
SOURCE_IDS = tuple(f'tree_{kind}_{v}' for v in range(3) for kind in ('bark', 'leaf'))
GROUP_IDS = tuple(f'windbreak_{v}_{part}' for v in range(3) for part in range(2))


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def add(a, b): return tuple(x+y for x, y in zip(a, b))
def sub(a, b): return tuple(x-y for x, y in zip(a, b))
def mul(a, s): return tuple(x*s for x in a)
def norm(a): return math.sqrt(sum(x*x for x in a))
def unit(a): return mul(a, 1/max(norm(a), 1e-12))
def cross(a, b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def mix(a, b, t): return add(mul(a, 1-t), mul(b, t))


def curve(points, t):
    a, b, c = points
    return add(add(mul(a, (1-t)**2), mul(b, 2*t*(1-t))), mul(c, t*t))


def bounds(points):
    return {key: [fn(p[i] for p in points) for i in range(3)]
            for key, fn in (('min', min), ('max', max))}


class Mesh:
    def __init__(self, identity, material):
        self.id, self.material = identity, material
        self.points, self.faces, self.uvs = [], [], []

    def vertex(self, p, uv):
        self.points.append(p); self.uvs.append(uv)
        return len(self.points)-1

    def face(self, *indices):
        for i in range(1, len(indices)-1):
            self.faces.append((indices[0], indices[i], indices[i+1]))

    def branch(self, points, radius, end_radius, segments, sides):
        rings = []
        for j in range(segments+1):
            t = j/segments; center = curve(points, t)
            axis = unit(sub(curve(points, min(1, t+.001)), curve(points, max(0, t-.001))))
            tangent = unit(cross(axis, (0, 0, 1) if abs(axis[2]) < .94 else (1, 0, 0)))
            bitangent = cross(axis, tangent)
            r = radius*(1-t)+end_radius*t
            rings.append([self.vertex(add(center, mul(add(mul(tangent, math.cos(k*math.tau/sides)),
                                                          mul(bitangent, math.sin(k*math.tau/sides))), r)),
                                      (k/sides, t*norm(sub(points[2], points[0]))/80)) for k in range(sides)])
        for lo, hi in zip(rings, rings[1:]):
            for k in range(sides):
                n = (k+1) % sides
                self.face(lo[k], lo[n], hi[n], hi[k])
        self.face(*reversed(rings[0])); self.face(*rings[-1])

    def leaf(self, base, length, width, yaw, tilt, roll, level):
        along = (math.cos(yaw)*math.cos(tilt), math.sin(yaw)*math.cos(tilt), math.sin(tilt))
        side = (-math.sin(yaw), math.cos(yaw), 0)
        up = unit(cross(along, side))
        side, up = add(mul(side, math.cos(roll)), mul(up, math.sin(roll))), add(mul(up, math.cos(roll)), mul(side, -math.sin(roll)))
        def point(t, w, bend=0):
            return add(base, add(mul(along, length*t), add(mul(side, width*w), mul(up, width*bend))))
        if level == 0:
            # Pointed oval, asymmetric blade and shallow curved midrib. The
            # petiole/base is exactly on the terminal twig, never a random cloud.
            shape = ((0, 0), (.28, -.40), (.65, -.49), (1, 0), (.68, .44), (.28, .38))
            center = self.vertex(point(.48, 0, .11), (.5, .48))
            edge = [self.vertex(point(t, w, -.045*t*t), (.5+w, t)) for t, w in shape]
            for a, b in zip(edge, edge[1:]+edge[:1]): self.face(center, a, b)
        elif level == 1:
            edge = [self.vertex(point(t, w), (.5+w, t)) for t, w in ((0, 0), (.48, -.45), (1, 0), (.48, .45))]
            center = self.vertex(point(.48, 0, .07), (.5, .48))
            for a, b in zip(edge, edge[1:]+edge[:1]): self.face(center, a, b)
        else:
            edge = [self.vertex(point(t, w), (.5+w, t)) for t, w in ((0, 0), (.48, -.45), (1, 0), (.48, .45))]
            self.face(*edge)

    def data(self, level):
        # Authored right-handed faces -> native clockwise triangles.
        return {'id': self.id, 'material': self.material, 'nanite': False, 'level': level,
                'verticesCm': [[round(v, 6) for v in p] for p in self.points],
                'indices': [i for a, b, c in self.faces for i in (a, c, b)],
                'uvs': [[round(x, 6) for x in uv] for uv in self.uvs], 'winding': 'clockwise'}


def skeleton(variant):
    """One coherent growth hierarchy shared by every LOD, deterministic by tree."""
    rng = random.Random(SEED+variant*991)
    height = (730, 910, 640)[variant]
    branches, leaves = [], []
    def branch(parent, parent_t, points, radius, end_radius, order):
        identity = len(branches)
        branches.append({'id': identity, 'parent': parent, 'parentT': parent_t,
                         'points': points, 'radiusCm': radius, 'tipRadiusCm': end_radius, 'order': order})
        return identity
    leader = ((0, 0, 0), (rng.uniform(-25, 25), rng.uniform(-16, 16), height*.47),
              (rng.uniform(-52, 52), rng.uniform(-37, 37), height*.96))
    branch(None, None, leader, (11.5, 10.5, 13)[variant], .4, 0)
    # Competing leaders produce connected crotches and crown divisions rather
    # than a pole carrying a stack of separate foliage shelves.
    for j, fraction in enumerate((.34, .51) if variant != 1 else (.46, .64)):
        start = curve(leader, fraction)
        angle = j*2.7+variant*1.14+.4
        reach = (80, 52, 109)[variant]
        end = (math.cos(angle)*reach, math.sin(angle)*reach, height*(.91-j*.08))
        mid = add(mix(start,end,.51),(math.cos(angle)*-17,math.sin(angle)*-17,8))
        branch(0, fraction, (start,mid,end), (5.0,4.1,6.0)[variant], .5, 0)
    for i in range(24):
        parent = i % 3
        fraction = (.26, .34, .24)[variant]+(i//3)*(.63/7)+rng.uniform(-.020,.020)
        fraction = min(.95, fraction)
        parent_points = branches[parent]['points']
        start = curve(parent_points, fraction)
        az = i*2.399963+rng.uniform(-.30, .30)+variant*.82
        crown = math.sin(math.pi*min(.99, fraction))**(.67 if variant == 0 else 1.0)
        radius = (146, 114, 160)[variant]*crown*rng.uniform(.82, 1.10)
        rise = (88, 118, 68)[variant]*rng.uniform(.70, 1.20)
        end = add(start, (math.cos(az)*radius, math.sin(az)*radius, rise))
        elbow = add(mix(start, end, .52), (-math.sin(az)*rng.uniform(-14, 14), math.cos(az)*rng.uniform(-14, 14), -17))
        primary = branch(parent, fraction, (start, elbow, end), 3.8*(1-fraction)+1.0, .60, 1)
        for j in range(4):
            t = .22+j*.23
            anchor = curve(branches[primary]['points'], t)
            side = -1 if j % 2 else 1
            saz = az+side*rng.uniform(.58, 1.13)
            reach = rng.uniform(43, 75)*(1-.30*t)
            send = add(anchor, (math.cos(saz)*reach, math.sin(saz)*reach, rng.uniform(30, 86)))
            control = add(mix(anchor, send, .5), (0, 0, rng.uniform(-8, 4)))
            secondary = branch(primary, t, (anchor, control, send), .9*(1-t)+.40, .20, 2)
            for k in range(4):
                st = .30+k*.20
                base = curve(branches[secondary]['points'], st)
                azimuth = saz+(-1 if k % 2 else 1)*rng.uniform(.62, 1.3)
                length = rng.uniform(29, 44)
                tip = add(base, (math.cos(azimuth)*length, math.sin(azimuth)*length, rng.uniform(-24, 43)))
                mid = add(mix(base, tip, .5), (0, 0, rng.uniform(1, 5)))
                twig = branch(secondary, st, (base, mid, tip), .22, .045, 3)
                for leaf in range(16):
                    lt = .10+leaf*.058
                    point = curve(branches[twig]['points'], lt)
                    lay = azimuth+(-1 if leaf % 2 else 1)*rng.uniform(.68, 1.22)
                    leaves.append({'branch': twig, 't': lt, 'base': point,
                                   'length': rng.uniform(11.5, 15), 'widthRatio': rng.uniform(.48, .64),
                                   'yaw': lay, 'tilt': rng.uniform(-.48, .55), 'roll': rng.uniform(-.65, .65),
                                   'indexOnTwig': leaf})
    return branches, leaves


def prototype(variant, level, graph):
    branches, leaves = graph
    bark, foliage = Mesh(f'realism_tree_bark_{variant}', 'bark'), Mesh(f'realism_tree_leaf_{variant}', 'leaf')
    segments = ((10, 3, 3, 2), (8, 3, 2, 1), (6, 3, 1, 0))[level]
    sides = ((12, 7, 5, 3), (8, 5, 4, 3), (6, 4, 3, 0))[level]
    for b in branches:
        order = b['order']
        if segments[order]: bark.branch(b['points'], b['radiusCm'], b['tipRadiusCm'], segments[order], sides[order])
    keep = (tuple(range(16)), (0,2,4,6,8,10,12,15), (0,3,6,9,12,15))[level]
    # Preserve blade surface area when reducing shape corners and leaf count.
    # Far leaves are geometry, no alpha overdraw or camera-facing cards.
    size = math.sqrt(16/len(keep))*(1 if level == 0 else 1.15)
    for leaf in leaves:
        if leaf['indexOnTwig'] in keep:
            length = leaf['length']*size
            foliage.leaf(leaf['base'], length, length*leaf['widthRatio'], leaf['yaw'], leaf['tilt'], leaf['roll'], level)
    return bark.data(level), foliage.data(level)


def source_contract(plan):
    by_id = {m['id']: m for m in plan['meshes'] if m['id'] in SOURCE_IDS}
    groups = [g for g in plan['groups'] if g['id'] in GROUP_IDS]
    require(set(by_id) == set(SOURCE_IDS) and len(groups) == 6, 'Exact six original windbreak parts required')
    require(len({g['id'] for g in groups}) == 6, 'Duplicate windbreak group')
    for variant in range(3):
        selected = sorted([g for g in groups if g['id'].startswith(f'windbreak_{variant}_')], key=lambda g:g['id'])
        require(selected[0]['instances'] == selected[1]['instances'], 'Bark/leaf placement differs')
        for part, group in enumerate(selected):
            require(group['meshId'] == f'tree_{("bark", "leaf")[part]}_{variant}', 'Tree binding differs')
            require(group['collision'] == 'NoCollision', 'Tree source collision requires review')
            require(group['instances'] and group['cullStartCm'] == 37500 and group['cullEndCm'] == 50000, 'Tree cull contract differs')
    return by_id, groups


def build_plan(source):
    originals, groups = source_contract(source)
    meshes, witnesses = [], []
    for variant in range(3):
        graph = skeleton(variant)
        levels = [prototype(variant, lod, graph) for lod in range(3)]
        oldparts = [originals[f'tree_{kind}_{variant}'] for kind in ('bark', 'leaf')]
        oldpoints = [p for m in oldparts for lod in [m, *m['lods']] for p in lod['verticesCm']]
        envelope = bounds(oldpoints)
        radius = max(math.hypot(*p[:2]) for p in oldpoints)
        newpoints = [p for pair in levels for m in pair for p in m['verticesCm']]
        rawbounds = bounds(newpoints)
        # One XY factor for every LOD and both woody/leaf parts keeps the entire
        # crown within the already validated original road exclusion envelope.
        xy = min([radius*.98/max(math.hypot(*p[:2]) for p in newpoints)] +
                 [abs(envelope[k][axis])/abs(rawbounds[k][axis])*.98 for axis in (0, 1) for k in ('min', 'max')])
        lods = []
        for lod, pair in enumerate(levels):
            top = max(p[2] for m in pair for p in m['verticesCm'])
            z = envelope['max'][2]/top
            bottom = min(p[2] for m in pair for p in m['verticesCm'])
            negative_z = min(1, envelope['min'][2]/bottom) if bottom < 0 else 1
            for m in pair:
                m['verticesCm'] = [[round(p[0]*xy, 6), round(p[1]*xy, 6), round(p[2]*(negative_z if p[2]<0 else z), 6)] for p in m['verticesCm']]
            lods.append({'scaleXYZ': [xy, xy, z], 'triangles': sum(len(m['indices'])//3 for m in pair),
                         'boundsCm': bounds([p for m in pair for p in m['verticesCm']]),
                         'oldTriangles': sum(len(([m,*m['lods']][lod])['indices'])//3 for m in oldparts)})
            require(lods[-1]['triangles'] <= lods[-1]['oldTriangles']*1.50, 'Tree triangle budget exceeds bounded 50% study allowance')
            require(abs(lods[-1]['boundsCm']['max'][2]-envelope['max'][2]) < 2e-6, 'Tree height differs')
        for part in range(2):
            m = levels[0][part]; m['lods'] = [levels[1][part], levels[2][part]]
            m['sourceMeshId'] = oldparts[part]['id']
            m['lodScreenSizes'] = [1., .45, .12]
            meshes.append(m)
        witnesses.append({'variant': variant, 'profile': PROFILES[variant], 'sourceEnvelopeCm': envelope,
                          'sourceRadiusCm': radius, 'branchCountByOrder': dict(Counter(b['order'] for b in graph[0])),
                          'leafCountLod0': len(graph[1]), 'growthHierarchySha256': digest(graph), 'lods': lods})
    result = {'schemaVersion': 1, 'owner': OWNER, 'status': 'offline-study-not-native-approved',
              'units': 'centimeters', 'meshes': meshes,
              'groups': [{**g, 'sourceGroupId': g['id'], 'sourceMeshId': g['meshId'],
                          'id': 'realism_'+g['id'], 'meshId': 'realism_'+g['meshId']} for g in groups],
              'prototypes': witnesses, 'sourceInstancePlansSha256': digest(groups),
              'sourceTreeCount': sum(len(g['instances']) for g in groups if g['meshId'].startswith('tree_bark')),
              'provenance': 'Authored generic temperate broadleaf growth study. No botanical species/inventory claim; no scanned geometry or textures added.',
              'materialPolicy': 'Reuse exact inherited bark/leaf material bindings for a controlled geometry comparison.',
              'nativePolicy': 'Retain original meshes, instances, transforms and collision. Hide only six exact original visual HISM contributions; clone ordered native transforms into six new collisionless HISM.',
              'limitations': ['No suitable licensed temperate broadleaf scan exists in the current local asset set.',
                              'Curved hierarchical branch geometry does not establish botanically accurate species.',
                              'Offline renders establish only a controlled silhouette comparison; native lighting, LOD motion and frame time remain unverified.']}
    return result


def load_module(filename):
    sys.path.insert(0, str(ROOT/'scripts/unreal'))
    spec = importlib.util.spec_from_file_location(filename.replace('-', '_'), ROOT/'scripts/unreal'/filename)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def build(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    require(output.is_relative_to(ROOT/'output/unreal') and not output.exists(), 'Use a NEW output/unreal study directory')
    plan = build_plan(json.loads(source.read_text()))
    output.mkdir(parents=True)
    geometry = output/'realism-trees-geometry.json'
    geometry.write_text(json.dumps(plan, separators=(',', ':'), allow_nan=False)+'\n')
    glb = output/'realism-trees.glb'
    load_module('rural-import.py').write_glb(glb, plan)
    report = {k:v for k,v in plan.items() if k not in ('meshes', 'groups')}
    report.update(sourcePlan=str(source), sourcePlanSha256=sha(source), geometry=geometry.name, geometrySha256=sha(geometry),
                  glb=glb.name, glbSha256=sha(glb), pipelineFiles={str((ROOT/'scripts/unreal'/name).relative_to(ROOT)): sha(ROOT/'scripts/unreal'/name)
                  for name in ('realism-trees-geometry.py', 'rural-import.py', 'performance_scene_policy.py')},
                  sourceGroups=[{'sourceGroupId':g['sourceGroupId'], 'sourceMeshId':g['sourceMeshId'],
                                 'targetMeshId':g['meshId'], 'instances':len(g['instances']),
                                 'instancesSha256':digest(g['instances'])} for g in plan['groups']])
    (output/'geometry-report.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'output':str(output), 'treeCount':plan['sourceTreeCount'],
                      'trianglesByPrototypeLOD':[[x['triangles'] for x in r['lods']] for r in plan['prototypes']]}))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--source-plan', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    build(args.source_plan, args.output)
