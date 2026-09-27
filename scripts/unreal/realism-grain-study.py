"""Offline grain-orientation proposal only; never loads Unreal or changes a project.

Scope is a semantic allowlist. Longest AABB alone must not rotate cabinet fronts,
veneered carcasses, vertical legs or posts. Native material authoring is deferred.
"""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COHORT = {1457: ('tabletop', 'Y'), 1458: ('longitudinal apron', 'Y'), 1459: ('longitudinal apron', 'Y'),
          1460: ('transverse apron', 'X'), 1461: ('transverse apron', 'X'),
          **{value: ('chair top rail', 'Y') for value in (1474,1483,1492,1501,1510,1519)}}
SOURCE_NAME = 'Living warm oak | real-interior-kitchen-front'
# Right-handed member frames: their local Z is the solid timber's longitudinal axis.
FRAMES = {'X': ((0,1,0),(0,0,1),(1,0,0)), 'Y': ((0,0,1),(1,0,0),(0,1,0))}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text())


def dot(a, b):
    return sum(x*y for x,y in zip(a,b))


def basis(normal, axis=None):
    """CPU counterpart of existing dominant-face projection in a member frame."""
    frame = FRAMES[axis] if axis else ((1,0,0),(0,1,0),(0,0,1))
    n = tuple(dot(normal, v) for v in frame)
    a = tuple(abs(v) for v in n)
    sign = lambda v: 1 if v > 0 else -1 if v < 0 else 0
    if a[0] >= a[1] and a[0] >= a[2]:
        t, v = (0,-sign(n[0]),0), (0,0,-1)
    elif a[1] >= a[2]:
        t, v = (sign(n[1]),0,0), (0,0,-1)
    else:
        t, v = (0,sign(n[2]),0), (-1,0,0)
    world = lambda local: tuple(sum(frame[j][i]*local[j] for j in range(3)) for i in range(3))
    return world(t), world(v)


def selection(scene):
    require(scene['activeDesign'] == {'variant':'C','heatingLayout':'B','livingLayout':'B'}, 'Only C/B/B allowed')
    by_id = {row['id']: row for row in scene['objects']}
    result = []
    for number,(kind,axis) in COHORT.items():
        id_ = f'DOM_{number:05d}'
        row = by_id[id_]
        require(row['name'].startswith('LIVING-103-DINING ·') and row['materialNames'] == [SOURCE_NAME], 'Cohort semantics/material differs')
        expected_term = {'tabletop':'stôl · doska','longitudinal apron':'výstuha pozdĺžna',
                         'transverse apron':'výstuha priečna','chair top rail':'horná dubová priečka'}[kind]
        require(expected_term in row['name'], 'Cohort member identity differs')
        require(row['enabled'] and row['instances'] == 1 and not any(row['metadata'].get(k) for k in ('doorMotion','walkSurface','dynamicCameraOccluder')), 'Unsupported moving/instanced member')
        size = [row['boundsMm']['max'][i]-row['boundsMm']['min'][i] for i in range(3)]
        index = 'XYZ'.index(axis)
        require(size[index] > 2*max(size[i] for i in range(3) if i != index), 'Semantic timber axis no longer dominant')
        result.append({'sourceId':id_,'name':row['name'],'kind':kind,'worldGrainAxis':axis,
                       'dimensionsMm':size,'boundsMm':row['boundsMm'],'memberFrameWorld':FRAMES[axis]})
    return result


def create_proposal(output):
    project = ROOT/'output/unreal/realism-20260926-r4'
    scene_file = project/'geometry/scene.json'
    native_file = ROOT/'output/unreal/realism-20260926-r2/realism-import-report.json'
    photoreal_file = project/'photoreal-import-report.json'
    scene, receipt, photoreal = read(scene_file), read(native_file), read(photoreal_file)
    materials = receipt['savedMaterialReadback']['materials']
    matches = [(path,row) for path,row in materials.items() if row['recipe']['sourceName'] == SOURCE_NAME]
    require(len(matches) == 1, 'Ambiguous saved living oak material')
    asset, material = matches[0]
    graph = material['graph']
    custom = [row for row in graph['nodes'] if row['class'] == 'MaterialExpressionCustom' and row['role'] in ('BreziRealism:coherent-metric-uv','BreziRealism:coherent-scan-normal')]
    require(len(custom) == 2 and all('V=float3(0,0,-1);' in row['values']['code'] for row in custom), 'Saved native grain-basis evidence differs')
    material_file = project/'Project/BreziTwin/Content'/Path(asset.split('.')[0].removeprefix('/Game/')).with_suffix('.uasset')
    original_material_file = ROOT/'output/unreal/realism-20260926-r2/Project/BreziTwin/Content'/material_file.relative_to(project/'Project/BreziTwin/Content')
    require(sha(material_file) == receipt['afterAssetHashes'][str(original_material_file)], 'R4 living oak asset no longer matches saved native graph')
    bindings = receipt['materialBindingChanges']
    rows = selection(scene)
    for row in rows:
        overlay = photoreal['geometry']['objects']['PH_'+row['sourceId']]
        found = [b for b in bindings if b['actor'] == overlay['actor'] and b['slot'] == 0 and b['after'] == asset]
        require(len(found) == 1, 'Visible bevel binding missing from native receipt')
        row.update(nativeVisualActor=overlay['actor'], nativeVisualMesh=overlay['mesh'], nativeVisualComponent=found[0]['component'], materialSlot=0,
                   baselineMaterial=asset, originalSourceActorRetained=True)
    pinned = {str(p):sha(p) for p in (scene_file,native_file,photoreal_file,material_file,Path(__file__),ROOT/'scripts/unreal/realism-materials.py')}
    proposal = {'schemaVersion':1,'status':'offline-proposal-validated','owner':'scripts/unreal/realism-grain-study.py',
                'appliedToNativeProject':False,'inputPins':pinned,'sourceMaterial':asset,'sourceMaterialGraph':graph,
                'objects':rows,'targetBindingCount':len(rows),'proposedNewMaterialCount':2,
                'axisCounts':{axis:sum(row['worldGrainAxis']==axis for row in rows) for axis in ('X','Y')},
                'baselineMaterialBindingCount':sum(b['after']==asset for b in bindings),
                'cause':'Texture grain follows V; saved dominant-world-face basis always uses vertical -Z on side faces, irrespective of member axis.',
                'mutationBoundary':'Two duplicated materials under /Game/Brezi/Realism/Grain. Only the UV and world-normal Custom expression code prefixes change together. Exactly eleven existing visible PH bevel component slot overrides; original source components/assets remain unchanged.',
                'protectedFinish':['183 cm scan scale','object-center phase','albedo/normal/roughness textures','palette','contrast','roughness','normal strength','all other graph nodes/edges/flags'],
                'limitations':['Proposal only: no native authoring, render or performance claim.', 'End faces still use the existing oak scan; no end-grain photograph is claimed.', 'Dominant-face bevel behavior is retained; this stage only corrects longitudinal timber orientation.']}
    Path(output).mkdir(parents=True,exist_ok=False)
    (Path(output)/'grain-proposal.json').write_text(json.dumps(proposal,indent=2,ensure_ascii=False)+'\n')
    return proposal


if __name__ == '__main__':
    result = create_proposal(ROOT/'output/unreal/realism-grain-study-20260926-r1')
    print(json.dumps({key:result[key] for key in ('status','targetBindingCount','proposedNewMaterialCount','axisCounts','baselineMaterialBindingCount')}))
