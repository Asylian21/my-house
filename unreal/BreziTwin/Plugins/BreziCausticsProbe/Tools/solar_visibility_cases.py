"""Derive bounded opaque solar rays from exact canonical OBJ faces; no engine calls.

Resource is a source test fixture, never a production sun-visibility contract.
Run with --source-root <repo> --output <new-json-path> after source review.
"""
import argparse
from array import array
import hashlib
import importlib.util
import json
import math
from pathlib import Path

# Reviewed canonical joined roof planes. The exporter display group alone is
# insufficient (some metal doors also use group Roof); retain explicit identity.
REVIEWED_ROOF_OBJECT_IDS = {'DOM_01483','DOM_01484','DOM_01485','DOM_01486'}


def sha(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def derive(root):
    root = Path(root)
    geometry = root / 'output/unreal/geometry'
    plugin = root / 'unreal/BreziTwin/Plugins/BreziCausticsProbe'
    spec = importlib.util.spec_from_file_location('reference', plugin / 'Tools/receiver_reference.py')
    ref = importlib.util.module_from_spec(spec); spec.loader.exec_module(ref)
    scene_path, obj_path = geometry / 'scene.json', geometry / 'dom-mm.obj'
    receiver_path = plugin / 'Resources/receiver-contract.json'
    scene, receiver = json.loads(scene_path.read_text()), json.loads(receiver_path.read_text())
    obj_sha = sha(obj_path)
    if scene['objSha256'] != obj_sha:
        raise ValueError('Canonical OBJ is not bound to scene')
    if receiver['sourceSha256']['output/unreal/geometry/scene.json'] != sha(scene_path):
        raise ValueError('Receiver source scene must be reviewed before regenerating cases')
    objects = {o['id']: o for o in scene['objects']}
    for oid in REVIEWED_ROOF_OBJECT_IDS:
        obj=objects[oid]
        if obj['metadata'].get('entityId')!='HOUSE-DESIGN' or obj['metadata'].get('cameraOccluder') is not True:
            raise ValueError('Reviewed joined roof-plane provenance changed')
    floor = objects['DOM_01720']
    low, high = floor['boundsMm']['min'], floor['boundsMm']['max']
    x0, x1, y0, y1 = low[0]/1000, high[0]/1000, -high[1]/1000, -low[1]/1000
    # The normal-only waves do not displace source water geometry. A fixed 2mm
    # launch offset is explicit, bounded and used identically in CPU and GPU.
    z = receiver['waterMeanPlaneMetres'] + .002
    sun = ref.unit(receiver['sunRayTravelDirection'])
    direction = tuple(-v for v in sun)
    if direction[2] <= 0: raise ValueError('Daylight source fixture required')
    grid = (32, 16)
    origins = [(x0+(col+.5)*(x1-x0)/grid[0], y0+(row+.5)*(y1-y0)/grid[1], z)
               for row in range(grid[1]) for col in range(grid[0])]
    bridge = json.loads((geometry / 'bridge-report.json').read_text())
    if bridge['sourceObjSha256'] != obj_sha or bridge['sceneSha256'] != sha(scene_path):
        raise ValueError('Native render/archive selection is stale')
    archived = set(bridge['archiveReasons'])
    uncertain, opaque = [], []
    boxes = {}
    for oid, obj in objects.items():
        if not obj['enabled'] or oid in archived: continue
        lo, hi = obj['boundsMm']['min'], obj['boundsMm']['max']
        boxes[oid] = {'low': (lo[0]/1000, -hi[1]/1000, lo[2]/1000),
                      'high': (hi[0]/1000, -lo[1]/1000, hi[2]/1000)}
        mats = [scene['materials'][slot] for slot in obj['materialSlots']]
        # Landscape is deliberately UNKNOWN even when a proxy's scalar alpha=1:
        # native foliage replacements and alpha textures cannot be proven by OBJ.
        if obj['group'] == 'Landscape' or not mats or any(m['alpha'] != 1 for m in mats):
            uncertain.append(oid)
        else:
            opaque.append(oid)
    relevant = {oid for oid in opaque if any(ref.BVH.box(o, direction, boxes[oid], 500) for o in origins)}
    vertices = array('d'); triangles = []; roof_triangles = []; current = None; face_index = 0
    canonical_counts = {}
    with obj_path.open() as handle:
        for line in handle:
            if line.startswith('o '):
                current = line.split()[1]; face_index = 0
                if current not in objects: raise ValueError('Unregistered source OBJ object')
            elif line.startswith('v '):
                x,y,zv = map(float,line.split()[1:4]); vertices.extend((x/1000,-y/1000,zv/1000))
            elif line.startswith('f '):
                parts = line.split()[1:]
                if len(parts) != 3: raise ValueError('Canonical OBJ must contain exact triangles')
                is_roof = current in opaque and current in REVIEWED_ROOF_OBJECT_IDS
                if current in relevant or is_roof:
                    points=[]
                    for part in parts:
                        i=int(part.split('/')[0])-1
                        if i<0 or 3*i+2>=len(vertices): raise ValueError('Invalid source vertex')
                        points.append(tuple(vertices[3*i:3*i+3]))
                    a,b,c=points
                    tri={'objectId':current,'sourceFaceIndex':face_index,'verticesMetres':points,
                         'a':a,'e1':ref.sub(b,a),'e2':ref.sub(c,a),
                         'low':tuple(min(p[j] for p in points) for j in range(3)),
                         'high':tuple(max(p[j] for p in points) for j in range(3))}
                    if is_roof: roof_triangles.append(tri)
                face_index+=1;canonical_counts[current]=face_index
    if any(canonical_counts.get(k)!=o['triangles'] for k,o in objects.items()):
        raise ValueError('Canonical object/triangle identities changed')
    # There need not be any real opaque pool shadow for this sun. Positive
    # controls remain explicitly outside the aperture: 2cm upstream from an
    # exact roof-face centroid, not an invented blocker or a changed sun.
    controls=[]; controlled_objects={}
    for tri in roof_triangles:
        if controlled_objects.get(tri['objectId'],0)>=2: continue
        centroid=tuple(sum(v[j] for v in tri['verticesMetres'])/3 for j in range(3))
        cross=ref.cross(tri['e1'],tri['e2']);area2=math.sqrt(ref.dot(cross,cross))
        if area2<.01 or centroid[2]<z+.5 or abs(ref.dot(ref.mul(cross,1/area2),direction))<.25:continue
        controls.append({'origin':ref.sub(centroid,ref.mul(direction,.02)),
                         'sourceObjectId':tri['objectId'],'sourceFaceIndex':tri['sourceFaceIndex']})
        controlled_objects[tri['objectId']]=controlled_objects.get(tri['objectId'],0)+1
        if len(controls)==24:break
    primary_count=len(origins);origins.extend(c['origin'] for c in controls)
    relevant={oid for oid in opaque if any(ref.BVH.box(o,direction,boxes[oid],500) for o in origins)}
    # Second face-only pass reuses the exact global vertices and includes every
    # opaque object potentially intersecting any aperture or control ray.
    with obj_path.open() as handle:
        for line in handle:
            if line.startswith('o '):current=line.split()[1];face_index=0
            elif line.startswith('f '):
                if current in relevant:
                    points=[]
                    for part in line.split()[1:]:
                        i=int(part.split('/')[0])-1;points.append(tuple(vertices[3*i:3*i+3]))
                    a,b,c=points
                    triangles.append({'objectId':current,'sourceFaceIndex':face_index,'verticesMetres':points,
                                      'a':a,'e1':ref.sub(b,a),'e2':ref.sub(c,a),
                                      'low':tuple(min(p[j] for p in points) for j in range(3)),
                                      'high':tuple(max(p[j] for p in points) for j in range(3))})
                face_index+=1
    bvh=ref.BVH(triangles)
    eligible={'blocked':[],'unblocked':[]}; excluded=0;control_diagnostics=[]
    for sample,origin in enumerate(origins):
        hit,distance=bvh.first(origin,direction)
        if distance>500: hit=None;distance=500
        # Avoid claiming empty optical space across any unverified source volume.
        unknown=[oid for oid in uncertain if ref.BVH.box(origin,direction,boxes[oid],distance)]
        if sample>=primary_count:
            control_diagnostics.append({'origin':origin,'expected':controls[sample-primary_count],
                                        'first':(triangles[hit[0]]['objectId'],triangles[hit[0]]['sourceFaceIndex'],distance) if hit else None,
                                        'uncertain':unknown})
        if unknown:
            excluded+=1;continue
        expected='blocked' if hit else 'unblocked'
        control=controls[sample-primary_count] if sample>=primary_count else None
        if control and (not hit or triangles[hit[0]]['objectId']!=control['sourceObjectId'] or
                        triangles[hit[0]]['sourceFaceIndex']!=control['sourceFaceIndex'] or abs(distance-.02)>1e-8):continue
        row={'id':f'solar-grid-{sample:04d}','sourceSampleIndex':sample,
             'role':'off-aperture-source-roof-positive-control' if control else 'pool-aperture-solar-ray',
             'originMetres':origin,'originCm':[v*100 for v in origin],
             'directionTowardSun':direction,'tMinCm':.01,'tMaxCm':50000,
             'expected':expected,'expectedHitDistanceCm':distance*100 if hit else None,
             'expectedSourceObjectId':None,'expectedSourceFaceIndex':None,'expectedSourceTriangleMetres':None}
        if hit:
            tri=triangles[hit[0]]
            row.update(expectedSourceObjectId=tri['objectId'],expectedSourceFaceIndex=tri['sourceFaceIndex'],
                       expectedSourceTriangleMetres=tri['verticesMetres'])
        eligible[expected].append(row)
    selected=[]
    for kind in ['blocked','unblocked']:
        rows=eligible[kind]
        if len(rows)<2:
            raise ValueError(f'Only {len(rows)} source-proven {kind} rays; do not invent a blocker or change the sun; controls='+json.dumps(control_diagnostics))
        # Widely separated deterministic grid samples; source positions never move.
        selected.extend(rows[i] for i in sorted({0,len(rows)//2,len(rows)-1}))
    return {'schemaVersion':1,'status':'source-derived-opaque-geometry-test-cases-native-pending',
            'coordinateSystem':'unreal-axes-centimetres','sceneSha256':sha(scene_path),'sourceObjSha256':obj_sha,
            'receiverContractSha256':sha(receiver_path),'sourceBridgeSha256':sha(geometry/'bridge-report.json'),
            'solarTravelDirection':sun,'waterMeanPlaneMetres':receiver['waterMeanPlaneMetres'],
            'launchOffsetMetres':.002,'positiveControlOffsetMetres':.02,'sourceSamplingGrid':grid,'cases':selected,
            'derivation':{'sourceObjects':len(objects),'sourceTriangles':sum(canonical_counts.values()),
                          'relevantOpaqueObjects':len(relevant),'relevantOpaqueTriangles':len(triangles),
                          'sourceOpaqueEligibleCounts':{k:len(v) for k,v in eligible.items()},
                          'excludedUnverifiedVolumeRays':excluded,'uncertainSourceObjectIds':uncertain,
                           'referenceAlgorithm':'float64 exact source OBJ triangle BVH; uncertain AABB exclusion before first hit'},
            'nativeHitDistanceToleranceCm':.05,'cameraInvarianceDistanceToleranceCm':.02,
            'minimumDistinctCameraDistanceCm':100,'productionLightingBound':False,'sunVisibilityImplemented':False,
            'limitations':['Finite 500m canonical source test only; no complete optical visibility claim.',
                           'Off-aperture roof positive controls do not imply an opaque shadow reaches the pool.',
                           'Landscape and nonopaque source material volumes excluded, not converted to solid optical geometry.',
                           'Native TLAS is per-view culled and can use Nanite fallback; opaque inline rays ignore leaf alpha and transmission.',
                           'Source first face is CPU evidence; native TLAS instance/primitive IDs are not canonical IDs.']}


def generate(source_root,output):
    """Invalidate stale success before derivation; failed files cannot match compiled pins."""
    output=Path(output);output.parent.mkdir(parents=True,exist_ok=True)
    def save(value):
        temporary=output.with_name(output.name+'.tmp')
        temporary.write_text(json.dumps(value,indent=2)+'\n');temporary.replace(output)
    save({'status':'solar-source-derivation-pending','sunVisibilityImplemented':False})
    try:result=derive(Path(source_root))
    except Exception as error:
        save({'status':'solar-source-derivation-failed','sunVisibilityImplemented':False,'error':str(error)})
        raise
    save(result);return result


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source-root',required=True,type=Path);parser.add_argument('--output',required=True,type=Path)
    args=parser.parse_args();result=generate(args.source_root,args.output)
    print(json.dumps({'status':result['status'],'caseCount':len(result['cases']),'derivation':result['derivation']},indent=2))
