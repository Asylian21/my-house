"""Stdlib guard for one selected fuller canopy study and an exact135 library.

This guard preserves real old owners; it never rewrites the old growth or
meadow contracts. Source geometry review is separate from native acceptance.
"""
from collections import Counter
from copy import deepcopy
from functools import lru_cache
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import struct

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-canopy-fullness-native.py'
ADAPTER = 'scripts/unreal/exterior-canopy-fullness-integration.py'
GENERATOR = 'scripts/unreal/exterior-canopy-fullness-study.py'
STUDY = ROOT/'output/unreal/exterior-canopy-fullness-20261001-r1-study'
# Filled only after actual geometry/alpha review of all nine generated crowns.
STUDY_PINS = {'broadleaf-alpha-union-comparison.png': '2651f2603325ef4a304beb5dec257f36fac58a75fe7895f813d8f32756dd6bdc',
 'broadleaf-colored-source-comparison.png': '345b8f4bfe157c8604ed32790cff90edc7742891692552a923b84d9a90cb7efc',
 'build.log': '0aa99619f90963a745084e97e44c61eece57949fd458650f0d2cdf5db5b41beb',
 'canopy-plan.json': '9b6dc59420986b5d56b39ed68ea092b7e11c11e3b82f8f0866b47d515a834e77',
 'generator-source.py': '0f5e95288e47440d902fecaa08700b2328f5fc0d41dbe901ad5df346760bcb29',
 'geometry-manifest.json': 'f6f36617fa3462eaf6190695b73ac27f00517f4acea6b51037b2f11746f43d32',
 'geometry-validation.json': '30ab8a6bb3d96856bbe82df677ac8c29eb6b76c007505d913433ea9fe263204c',
 'glb/canopy_fullness_broadleaf_r1_a.glb': 'e241c2e48f7115f4526db6342b55fe12cf0d2fb89c19d4914218ed7674057323',
 'glb/canopy_fullness_broadleaf_r1_b.glb': '432701103b9fa64b0010cd51c54735911750465422e5bf10f194b967bedaa212',
 'glb/canopy_fullness_broadleaf_r1_c.glb': '0e9b8054b3a20dafe64b4ba9cc2d938e7709e09254ed3aa0c5aae142a331574f',
 'glb/canopy_fullness_orchard_r1_a.glb': '1f51f7655b70068f6c1406890d6b30a6f8401e231c5504e0849f1b85c2c5898b',
 'glb/canopy_fullness_orchard_r1_b.glb': '0c2be76804befc1fe6cd6e35b915f52a8649ee482ad9d8cf9cbee7608e2f1897',
 'glb/canopy_fullness_orchard_r1_c.glb': '90ec6978b6352f16c7d15535608b6cb0da0475abbf0da51ea7f20f09ce63ee2e',
 'glb/canopy_fullness_upright_r1_a.glb': '6f529df861ed19b427e6121618b43a8a8c5b23fb131d5bc5dab5d05baca414fc',
 'glb/canopy_fullness_upright_r1_b.glb': '012917376eef7f2bf0871904dbe32563903890d4014b6243e0f991600597109c',
 'glb/canopy_fullness_upright_r1_c.glb': '9d3e861441f9365a48fd557f1dc3e0da811433b9cf2747362064319eb7935800',
 'material-manifest.json': '555da7f3f36cb6b5843e578fa76b298bf47d4740e13c70e5e2397e1a325bb064',
 'morphology-additions.json': 'da37e51decf6c9c166b62ab3dfff61047d45e98e88a58985c3018493d3524490',
 'orchard-alpha-union-comparison.png': '630b45ae2393bc8b043d8f08a475799be97ee80040b6c6ee5a9afb2cbe40486e',
 'orchard-colored-source-comparison.png': '94ef3be21495af79adea534be40b6cdc4342db428555094fe32ad4528fa56694',
 'source-measurement.json': 'c279ef389750a9272a952fa7d545b2280fb405b97275221ea217e48652ca7caa',
 'source-receipt.json': 'bbb195be6b34d06be0a8965fb097a38e46a5be4528300068ccb97f31719265c6',
 'source-review.json': '8311b7d2687992bd4eae4592baf4b874f5756c793f9c9d450c567017dd331639',
 'summary.json': 'f4424c965e2d41beecff5c6c7593a5685cb493d8e2ca28171630084ab4b3bd13',
 'upright-alpha-union-comparison.png': 'a24cc6212bfb51b0564f8af678bf289445e001f222247763589f6ffc369cacd7',
 'upright-colored-source-comparison.png': 'f7a65d99aabccb54a4ae48f20bce82950608ad5ce8edaf81483426fe1637c138'}
GENERATOR_SHA = '0f5e95288e47440d902fecaa08700b2328f5fc0d41dbe901ad5df346760bcb29'
SOURCE_REVIEW_SELECTED = True
BASE = ROOT/'output/unreal/exterior-meadow-infill-integration-20261001-r1'
BASE_PINS = {
    'geometry-manifest.json': 'a39e13e9b58821815fd783857e09e58d1023e4a64ab10e45a2a4da608954ceb9',
    'material-manifest.json': '42dbaddc637c479d30482b1524217d8e9c288ff89de8f64d9f38396a1e63fbbb',
    'photo-material-manifest.json': '9a0275363882594afb4b656ffbd7528866ad63366d03cf938bf562ac6ec5c88e',
    'asset-manifest.json': '6f439d6f5034ee95e4f0776f92e2bfbd95c6ed0a7a89a53c9b9019ffacd1d22c',
}
DELEGATES = {
    'exterior-meadow-infill-native.py': '94e8a223db3ddd2b7da215df1560bbce5c6918771cb0792c19b02b490d8e29d5',
    'exterior-canopy-native.py': '2788c643f4bd924f2fa72714d18ad009a7b4aa599ba86df58baf7582f765a172',
}
STATUS = 'FULLER_CANOPY_INTEGRATION_SOURCE_ONLY_NATIVE_PENDING'
IDS = {f'canopy_fullness_{family}_r1_{variant}' for family in ('broadleaf','upright','orchard') for variant in 'abc'}
EXTRA = {'sourceFullnessPlan','fullnessGeometryManifest','sourceOriginal126Library','validatedOriginal126Subset'}
ATTRS = {'POSITION':('VEC3',3),'NORMAL':('VEC3',3),'TANGENT':('VEC4',4),'TEXCOORD_0':('VEC2',2),'COLOR_0':('VEC4',4)}
_INSPECTIONS = {}


def require(ok, message):
    if not ok: raise RuntimeError(message)


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1048576), b''): h.update(block)
    return h.hexdigest()


def digest(value): return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
def same(a,b): return digest(a) == digest(b)
def fixed(directory,name,pins): return {'path':str(directory/name),'sha256':pins[name]}


def pinned(record):
    require(isinstance(record,dict) and set(record) == {'path','sha256'}, 'Fullness source pin shape differs')
    path = (ROOT/record['path']).resolve()
    require(path.is_relative_to(ROOT) and path.is_file() and sha(path) == record['sha256'], 'Fullness source pin drift: '+str(path))
    return path


def pin(path):
    path = Path(path).resolve()
    require(path.is_relative_to(ROOT) and path.is_file(), 'Fullness path escaped or missing')
    return {'path':str(path),'sha256':sha(path)}


def read_pin(record): return json.loads(pinned(record).read_text())


@lru_cache(maxsize=2)
def module(filename):
    path = pinned({'path':str(ROOT/'scripts/unreal'/filename),'sha256':DELEGATES[filename]})
    spec = importlib.util.spec_from_file_location('fullness_delegate_'+filename.replace('-','_'),path)
    result = importlib.util.module_from_spec(spec); spec.loader.exec_module(result)
    return result


def approved():
    required = {'canopy-plan.json','geometry-manifest.json','morphology-additions.json','geometry-validation.json',
        'material-manifest.json','summary.json','generator-source.py','source-review.json','source-receipt.json'}
    require(SOURCE_REVIEW_SELECTED and required <= set(STUDY_PINS) and GENERATOR_SHA and sha(ROOT/GENERATOR) == GENERATOR_SHA,
        'Fullness all-family source geometry/alpha review has not selected a frozen study')
    result = {name:read_pin(fixed(STUDY,name,STUDY_PINS)) for name in required if name.endswith('.json')}
    pinned(fixed(STUDY,'generator-source.py',STUDY_PINS))
    require(STUDY_PINS['generator-source.py'] == GENERATOR_SHA, 'Fullness actual generated source snapshot differs')
    review = result['source-review.json']; receipt = result['source-receipt.json']
    require(review['nativeTrialRecommended'] is True and review['sourceSelectionOnly'] is True and
        review['nativeAppearanceAccepted'] is False and review['nativePerformanceAccepted'] is False and
        review['fullRealismAccepted'] is False and receipt['actualBuildExitCode'] == 0 and receipt['postBuildInputsUnchanged'] is True,
        'Fullness selected source review must remain source-only with actual closed build')
    return result


def integration_inputs():
    source = approved(); original = read_pin(fixed(BASE,'geometry-manifest.json',BASE_PINS)); result = {}
    def add(path, expected):
        require(path not in result or result[path] == expected, 'Fullness input pin conflict')
        pinned({'path':path,'sha256':expected}); result[path] = expected
    for values in (original['inputFiles'],source['canopy-plan.json']['inputFiles'],source['geometry-manifest.json']['inputFiles']):
        for path,expected in values.items(): add(path,expected)
    for directory, values in ((BASE,BASE_PINS),(STUDY,STUDY_PINS)):
        for name,expected in values.items(): add(str(directory/name),expected)
    for mesh in source['geometry-manifest.json']['meshes']: add(mesh['glbPath'],mesh['glbSha256'])
    for filename,expected in DELEGATES.items(): add(str(ROOT/'scripts/unreal'/filename),expected)
    for path in (ROOT/OWNER,ROOT/ADAPTER): add(str(path),sha(path))
    return result


def validated_libraries(full):
    """Return genuine old126/120/100 manifests without changing old owners."""
    source = approved(); original = read_pin(fixed(BASE,'geometry-manifest.json',BASE_PINS))
    extension = source['geometry-manifest.json']
    require(full.get('owner') == ADAPTER and full.get('generatorSha256') == sha(ROOT/ADAPTER) and full.get('status') == STATUS,
        'Fullness135 library owner/source status differs')
    require(set(full) == set(original)|EXTRA and same(full['meshes'],original['meshes']+extension['meshes']) and
        len(full['meshes']) == 135 and sum(len(m['lods']) for m in full['meshes']) == 405,
        'Fullness135 must preserve exact ordered original126 plus nine selected masters')
    for key,value in original.items():
        if key not in {'owner','generatorSha256','inputFiles','status','meshes','revision'}:
            require(same(full[key],value), 'Fullness original126 metadata changed: '+key)
    require(same(full['sourceOriginal126Library'],fixed(BASE,'geometry-manifest.json',BASE_PINS)) and
        same(full['sourceFullnessPlan'],fixed(STUDY,'canopy-plan.json',STUDY_PINS)) and
        same(full['fullnessGeometryManifest'],fixed(STUDY,'geometry-manifest.json',STUDY_PINS)) and
        same(full['inputFiles'],integration_inputs()), 'Fullness135 source closure differs')
    require(full['validatedOriginal126Subset']['sha256'] == BASE_PINS['geometry-manifest.json'] and
        same(read_pin(full['validatedOriginal126Subset']),original), 'Fullness genuine old126 subset differs')
    old = module('exterior-meadow-infill-native.py').validated_libraries(original)
    return {'original126':original,**old}


def _glb(path, generator, master):
    raw = Path(path).read_bytes()
    require(len(raw) >= 28 and struct.unpack_from('<4sII',raw) == (b'glTF',2,len(raw)), 'Fullness GLB header differs')
    n,kind = struct.unpack_from('<II',raw,12); require(kind == 0x4e4f534a,'Fullness GLB JSON missing')
    doc = json.loads(raw[20:20+n]); offset = 20+n
    size,kind = struct.unpack_from('<II',raw,offset); data = raw[offset+8:]
    require(kind == 0x004e4942 and len(data) == size and doc['buffers'] == [{'byteLength':size}] and
        set(doc) == {'asset','scene','scenes','nodes','meshes','buffers','bufferViews','accessors','materials'} and
        doc['asset'] == {'version':'2.0','generator':generator} and doc['scene'] == 0 and
        doc['scenes'] == [{'nodes':[0,1,2]}] and len(doc['nodes']) == len(doc['meshes']) == 3,
        'Fullness unmeasured GLB node/transform/skin/animation differs')
    def block(index, kind, width, indices=False):
        a = doc['accessors'][index]; view = doc['bufferViews'][a['bufferView']]
        require(set(a) <= {'bufferView','componentType','count','type','min','max'} and
            a['componentType'] == (5125 if indices else 5126) and a['type'] == kind and type(a['count']) is int and a['count'] > 0 and
            set(view) == {'buffer','byteOffset','byteLength','target'} and view['buffer'] == 0 and
            view['target'] == (34963 if indices else 34962) and view['byteLength'] == a['count']*width*4 and
            0 <= view['byteOffset'] <= len(data)-view['byteLength'], 'Fullness actual accessor packing differs')
        return data[view['byteOffset']:view['byteOffset']+view['byteLength']]
    nodes = []
    for lod,node in enumerate(doc['nodes']):
        mesh = doc['meshes'][lod]; name = master+'_LOD'+str(lod)
        require(node == {'name':name,'mesh':lod} and set(mesh) == {'name','primitives'} and mesh['name'] == name,
            'Fullness actual node identity/transform differs')
        parts = {}
        for primitive in mesh['primitives']:
            require(set(primitive) == {'attributes','indices','material','mode'} and primitive['mode'] == 4 and
                set(primitive['attributes']) == set(ATTRS),'Fullness primitive modifiers/material attributes differ')
            material = doc['materials'][primitive['material']]['name']; require(material not in parts,'Fullness duplicate primitive')
            parts[material] = {key:block(primitive['attributes'][key],*spec) for key,spec in ATTRS.items()}
            parts[material]['indices'] = block(primitive['indices'],'SCALAR',1,True)
        nodes.append(parts)
    return nodes


def _vec(raw,width): return list(struct.iter_unpack('<'+'f'*width,raw))
def _indices(raw): return [value[0] for value in struct.iter_unpack('<I',raw)]


def _twig(twig,lod,fit,growth):
    segments,sides = ((3,5),(2,4),(1,3))[lod]
    path = [growth._quadratic(twig['points'],j/segments) for j in range(segments+1)]
    chord = growth._unit(growth._sub(path[-1],path[0])); stable = growth._unit(growth._cross(chord,[0,0,1]))
    points,uv,faces,distance = [],[],[],0.
    for j,p in enumerate(path):
        t = j/segments; direction = growth._unit(growth._sub(path[min(segments,j+1)],path[max(0,j-1)]))
        a = growth._unit(growth._sub(stable,growth._mul(direction,growth._dot(stable,direction))))
        b = growth._unit(growth._cross(direction,a)); radius = twig['radius']*(1-t)+twig['tipRadius']*t
        if j: distance += math.dist(p,path[j-1])
        for k in range(sides+1):
            angle = math.tau*k/sides
            points.append(growth._add(p,growth._mul(growth._add(growth._mul(a,math.cos(angle)),growth._mul(b,math.sin(angle))),radius)))
            uv.append([math.tau*twig['radius']*k/sides/25,distance/25])
    for j in range(segments):
        for k in range(sides):
            a = j*(sides+1)+k; b = a+sides+1; faces.extend([(a,a+1,b),(a+1,b+1,b)])
    return [growth._growth_fit(p,fit) for p in points],uv,faces


def _piece(part,offset,index_offset,piece,label,growth):
    positions,uv,faces = piece
    actual_p = _vec(part['POSITION'][offset*12:(offset+len(positions))*12],3)
    native = [(100*p[0],100*p[2],100*p[1]) for p in actual_p]
    require(len(native) == len(positions) and all(math.dist(a,b) < .0003 for a,b in zip(native,positions)),
        'Fullness actual '+label+' positions differ from connected controls')
    actual_uv = _vec(part['TEXCOORD_0'][offset*8:(offset+len(positions))*8],2)
    require(all(math.dist(a,b) < .00002 for a,b in zip(actual_uv,uv)), 'Fullness actual '+label+' UV differs')
    expected = [offset+i for a,b,c in faces for i in (a,c,b)]
    require(_indices(part['indices'][index_offset*4:(index_offset+len(expected))*4]) == expected,
        'Fullness actual '+label+' topology differs')
    frames = growth._growth_basis(positions,uv,faces)
    actual_n = _vec(part['NORMAL'][offset*12:(offset+len(positions))*12],3)
    actual_t = _vec(part['TANGENT'][offset*16:(offset+len(positions))*16],4)
    require(all(math.dist(n,a) < .000025 and math.dist(t,b) < .000025 for (n,t),a,b in zip(frames,actual_n,actual_t)),
        'Fullness actual '+label+' area normal/photographic UV tangent differs')
    return offset+len(positions),index_offset+len(expected)


def _measure(part,old):
    count = len(part['POSITION'])//12; require(count > 0 and all(len(part[key]) == count*width*4 for key,(_,width) in ATTRS.items()),
        'Fullness actual attribute census differs')
    require(all(part[key][:len(value)] == value for key,value in old.items()), 'Fullness original primitive attribute/index prefix changed')
    p = _vec(part['POSITION'],3); native = [(100*v[0],100*v[2],100*v[1]) for v in p]
    require(all(all(math.isfinite(x) for x in v) for v in p),'Fullness actual position non-finite')
    old_vertices = len(old['POSITION'])//12
    for n,t,uv,c in zip(struct.iter_unpack('<3f',part['NORMAL'][old_vertices*12:]),struct.iter_unpack('<4f',part['TANGENT'][old_vertices*16:]),
        struct.iter_unpack('<2f',part['TEXCOORD_0'][old_vertices*8:]),struct.iter_unpack('<4f',part['COLOR_0'][old_vertices*16:])):
        require(all(math.isfinite(x) for values in (n,t,uv,c) for x in values) and abs(sum(x*x for x in n)-1) < .00006 and
            abs(sum(x*x for x in t[:3])-1) < .00006 and abs(sum(a*b for a,b in zip(n,t))) < .00003 and t[3] in (-1,1) and c == (1.,1.,1.,1.),
            'Fullness added normal/tangent/neutral color differs')
    require(len(part['indices'])%12 == 0,'Fullness non-triangle indices')
    for a,b,c in struct.iter_unpack('<III',part['indices'][len(old['indices']):]):
        require(old_vertices <= min(a,b,c) <= max(a,b,c) < count,'Fullness added topology refers outside added vertices')
        e1 = [p[b][i]-p[a][i] for i in range(3)]; e2 = [p[c][i]-p[a][i] for i in range(3)]
        cross = [e1[1]*e2[2]-e1[2]*e2[1],e1[2]*e2[0]-e1[0]*e2[2],e1[0]*e2[1]-e1[1]*e2[0]]
        mean = [sum(struct.unpack_from('<3f',part['NORMAL'],index*12)[i] for index in (a,b,c)) for i in range(3)]
        require(sum(x*x for x in cross) > 1e-24 and sum(a*b for a,b in zip(cross,mean)) > 0,'Fullness added degenerate/opposed surface')
    return {'vertices':count,'triangles':len(part['indices'])//12,'native':native}


def _geometry(manifest,old_manifest,additions,morphology,old_proof,growth):
    original = {row['id']:row for row in old_manifest['meshes']}; measured = {}
    require(len(manifest['meshes']) == 9 and {row['id'] for row in manifest['meshes']} == IDS and set(additions) == IDS,
        'Fullness exact nine master/additions inventory differs')
    for row in manifest['meshes']:
        source = original[row['sourceGrowthMasterId']]; key = row['id']; controls = additions[key]
        require(key == source['id'].replace('canopy_growth_','canopy_fullness_') and row['placementPolicy'] == 'explicit-only' and
            row['role'] == 'tree' and row['materialKeys'] == source['materialKeys'] and row['heightCm'] == source['heightCm'] and
            row['sourceFamily'] == source['sourceFamily'] and [lod['level'] for lod in row['lods']] == [0,1,2],
            'Fullness original family/height/material/explicit-only policy differs')
        old_nodes = _glb(pinned({'path':source['glbPath'],'sha256':source['glbSha256']}),growth.GROWTH,source['id'])
        nodes = _glb(pinned({'path':row['glbPath'],'sha256':row['glbSha256']}),GENERATOR,key)
        morph = morphology[source['id']]; fit = old_proof['meshes'][source['id']]['authoringFit']; leaf_key = morph['leafMaterial']
        require(same(controls['authoringFit'],fit),'Fullness original fitted crown changed')
        twigs,leaves = controls['newTwigs'],controls['newLeaves']
        require(len(twigs) == row['newConnectedAnnualTwigs'] and len(leaves) == row['newLeafCount'] and
            row['leafCount'] == source['leafCount']+len(leaves) and row['branches'] == source['branches']+len(twigs),
            'Fullness actual twig/leaf master census differs')
        for i,twig in enumerate(twigs):
            require(type(twig['cluster']) is int and 0 <= twig['cluster'] < len(morph['clusters']),
                'Fullness annual twig cluster is unowned')
            support = morph['clusters'][twig['cluster']]['branch']
            parent = twig['parentOriginalBranch']; require(type(parent) is int and 0 <= parent < len(morph['branches']) and
                twig['id'] == i and twig['parentT'] == 1 and support in morph['growth']['terminalSupportBranches'] and
                (parent == support or morph['branches'][parent].get('terminalLeafShoot') is True and morph['branches'][parent]['parent'] == support) and
                math.dist(twig['points'][0],growth._growth_evaluate(morph['branches'][parent],1)) < 1e-7 and
                .035 <= twig['tipRadius'] <= .065 and .10 <= twig['radius'] <= .15 and twig['tipRadius'] < twig['radius'],
                'Fullness annual twig detached from common original all-LOD terminal endpoint')
        for leaf in leaves:
            twig = twigs[leaf['twig']]; require(0 < leaf['t'] < 1 and leaf['cluster'] == twig['cluster'] and
                math.dist(leaf['base'],growth._quadratic(twig['points'],leaf['t'])) < 1e-7,
                'Fullness added individual leaf detached from annual twig')
        all_points,costs,restored_counts = [],[],[]
        for lod,(parts,old_parts) in enumerate(zip(nodes,old_nodes)):
            require(set(parts) == set(old_parts) == set(source['materialKeys']),'Fullness actual photographic primitives differ')
            measurements = [_measure(part,old_parts[material]) for material,part in parts.items()]
            points = [p for m in measurements for p in m['native']]; triangles = sum(m['triangles'] for m in measurements)
            target = row['lods'][lod]; bounds = {key:[fn(p[i] for p in points) for i in range(3)] for key,fn in (('min',min),('max',max))}
            radius = max(math.hypot(p[0],p[1]) for p in points)
            require(target['vertices'] == len(points) and target['triangles'] == triangles and
                all(abs(bounds[k][i]-target['expectedBoundsCm'][k][i]) < .0002 for k in ('min','max') for i in range(3)) and
                abs(radius-target['radialEnvelopeCm']) < .0002 and radius <= source['radialEnvelopeCm']+.001 and
                all(source['allLodBoundsCm']['min'][i]-.001 <= p[i] <= source['allLodBoundsCm']['max'][i]+.001 for p in points for i in range(3)),
                'Fullness decoded whole crown exceeds original or declared envelope/counts')
            bark = parts[growth.BARK]; cursor = len(old_parts[growth.BARK]['POSITION'])//12,len(old_parts[growth.BARK]['indices'])//4
            for twig in twigs: cursor = _piece(bark,*cursor,_twig(twig,lod,fit,growth),'annual twig',growth)
            require(cursor == (len(bark['POSITION'])//12,len(bark['indices'])//4),'Fullness unowned added bark geometry')
            leaf_part = parts[leaf_key]; cursor = len(old_parts[leaf_key]['POSITION'])//12,len(old_parts[leaf_key]['indices'])//4
            near = old_nodes[0][leaf_key]; missing = [] if lod == 0 else sorted(set(range(source['leafCount']))-set(old_proof['meshes'][source['id']]['lodLeafIds'][str(lod)]))
            for identity in missing:
                if lod == 1:
                    v,ind = cursor
                    for attr,(_,width) in ATTRS.items():
                        require(leaf_part[attr][v*width*4:(v+9)*width*4] == near[attr][identity*9*width*4:(identity+1)*9*width*4],
                            'Fullness restored mid leaf identity changed')
                    face = [value-identity*9+v for value in _indices(near['indices'][identity*24*4:(identity+1)*24*4])]
                    require(_indices(leaf_part['indices'][ind*4:(ind+24)*4]) == face,'Fullness restored mid leaf topology changed')
                    cursor = v+9,ind+24
                else:
                    near_p = _vec(near['POSITION'][identity*9*12:(identity+1)*9*12],3); near_uv = _vec(near['TEXCOORD_0'][identity*9*8:(identity+1)*9*8],2)
                    selection = (0,2,3,5,6,8)
                    p = [(100*near_p[i][0],100*near_p[i][2],100*near_p[i][1]) for i in selection]
                    cursor = _piece(leaf_part,*cursor,(p,[near_uv[i] for i in selection],[(0,2,1),(1,2,3),(2,4,3),(3,4,5)]),'restored far leaf',growth)
            for leaf in leaves:
                p,uv,faces = growth._growth_leaf(leaf,lod,1)
                cursor = _piece(leaf_part,*cursor,([growth._growth_fit(v,fit) for v in p],uv,faces),'added individual leaf',growth)
            require(cursor == (len(leaf_part['POSITION'])//12,len(leaf_part['indices'])//4) and
                target['restoredNearLeafIdentities'] == len(missing) and target['leafCount'] == source['leafCount']+len(leaves),
                'Fullness lost original near leaf identity or unowned added leaf geometry')
            added_p = [p for material,part in parts.items() for p in _vec(part['POSITION'][len(old_parts[material]['POSITION']):],3)]
            require(all(100*p[1] > 50.01 for p in added_p),'Fullness appendage changes original basal50cm')
            all_points.extend(points); costs.append(triangles); restored_counts.append(len(missing))
        measured[key] = {'radius':max(math.hypot(p[0],p[1]) for p in all_points),'minZ':min(p[2] for p in all_points),
            'maxZ':max(p[2] for p in all_points),'triangles':costs,'restoredNearLeafIdentitiesByLod':restored_counts}
    return measured


def validated_replacements(plan,manifest,context,full,scene_sha,obj_sha):
    source = approved(); require(same(plan,source['canopy-plan.json']) and same(manifest,source['geometry-manifest.json']),
        'Fullness selected immutable plan/geometry differs')
    require(plan['owner'] == manifest['owner'] == GENERATOR and plan['kind'] == 'isolated-fuller-connected-canopy-study' and
        plan['nativeAppearanceAccepted'] is False and plan['sourceSceneSha256'] == scene_sha and plan['sourceObjSha256'] == obj_sha and
        same(read_pin(plan['sourceContext']),context) and same(plan['geometryManifest'],fixed(STUDY,'geometry-manifest.json',STUDY_PINS)) and
        same(plan['fullnessGeometryManifest'],plan['geometryManifest']), 'Fullness truthful owner/frame/source geometry differs')
    libraries = validated_libraries(full); growth = module('exterior-canopy-native.py')
    old_plan = read_pin(plan['sourceOriginalGrowthPlan']); old_manifest = read_pin(plan['sourceOriginalGrowthGeometry'])
    require(same(plan['originalCanopyPlacements'],old_plan['canopyPlacements']) and len(plan['canopyPlacements']) == 78,
        'Fullness original78 growth roots/order differ')
    inputs = integration_inputs()
    for path,expected in old_plan['inputFiles'].items():
        require(path not in inputs or inputs[path] == expected,'Fullness original growth input conflict'); inputs[path] = expected
        pinned({'path':path,'sha256':expected})
    cache_key = scene_sha,obj_sha
    if cache_key not in _INSPECTIONS:
        basis = growth.validated_replacements(old_plan,old_manifest,context,libraries['original126'],scene_sha,obj_sha)
        old_proof = read_pin(basis['audit']['morphologyProof']); morphology = read_pin(basis['audit']['sourceSkeleton'])
        measured = _geometry(manifest,old_manifest,source['morphology-additions.json'],morphology,old_proof,growth)
        _INSPECTIONS[cache_key] = {'basis':basis,'measured':measured}
    inspected = _INSPECTIONS[cache_key]; measured = inspected['measured']; counts = Counter(); budgets = [0,0,0]; minimum = math.inf
    for row,old in zip(plan['canopyPlacements'],old_plan['canopyPlacements']):
        key = old['meshId'].replace('canopy_growth_','canopy_fullness_'); actual = measured[key]
        require(row['meshId'] == key and same({k:v for k,v in row.items() if k != 'meshId'},{k:v for k,v in old.items() if k != 'meshId'}),
            'Fullness original root/yaw/scale/cull/metadata changed')
        scale = row['scale']; require(len(scale) == 3 and type(scale[0]) in (int,float) and 0 < scale[0] == scale[1] == scale[2] and
            actual['minZ'] >= -.0002 and actual['radius']*scale[0] <= old['radiusCm']+.001 and
            (actual['maxZ']-actual['minZ'])*scale[0] <= old['heightCm']+.001,
            'Fullness decoded all-LOD crown exceeds original source circle/height')
        minimum = min(minimum,min(old['clearanceCm'].values())+old['radiusCm']-actual['radius']*scale[0])
        budgets = [a+b for a,b in zip(budgets,actual['triangles'])]; counts[key] += 1
    require(minimum >= 0,'Fullness decoded crown enters original protected circle exclusions')
    replacements = {row['id']:row for row in plan['canopyPlacements']}
    require(len(context['regionalVegetationPlacements'])-78 == 1022 and all(
        replacements.get(row['id'],row) == row for row in context['regionalVegetationPlacements'] if row['regionId'] != growth.REGION),
        'Fullness non-grove original rows changed')
    require(same(plan['audit']['perMesh'],source['geometry-validation.json']) and
        plan['audit']['allInstancesTriangleBudgetByLod'] == budgets and
        plan['audit']['originalAllInstancesTriangleBudgetByLod'] == inspected['basis']['audit']['allInstancesTriangleBudgetByLod'],
        'Fullness truthful geometry audit/population budget differs')
    audit = {'status':'verified-source-grove-canopy-fullness','masters':9,'lods':27,'instances':78,'deletedTrees':0,'hiddenOriginalActors':0,
        'nonGroveRegionalRowsPreserved':1022,'allOriginalRootYawScaleMetadataPreserved':True,'allLodBasalCompatibilityHeightCm':50,
        'allDecodedEnvelopesInsideOriginal':True,'actualOriginalAttributeAndIndexPrefixesByteExact':True,
        'actualConnectedAnnualTwigAndIndividualLeafGeometryVerified':True,'actualAllOriginalNearLeafIdentitiesRetainedEveryLod':True,
        'actualAppendedAreaNormalsAndUvTangentsVerified':True,'minimumDecodedCrownClearanceCm':minimum,
        'allInstancesTriangleBudgetByLod':budgets,'placementCountsByMaster':dict(counts),'sourceMaterialsUnchanged':True,'collisionActorsChanged':False,
        'sourceContext':deepcopy(plan['sourceContext']),'originalGrowthWitness':inspected['basis']['audit'],
        'morphologyProof':fixed(STUDY,'geometry-validation.json',STUDY_PINS),'additionsProof':plan['additionsProof'],
        'sourceSkeleton':inspected['basis']['audit']['sourceSkeleton'],'nativeAppearanceAccepted':False,'performanceAccepted':False,
        'farCostAccepted':False,'nativeVerified':False,'fullPhotorealismAccepted':False}
    return {'placements':deepcopy(plan['canopyPlacements']),'audit':audit,'inputPins':inputs}
