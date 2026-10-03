"""Isolated space-competition canopy study, never selected native input.

Authored connected growth graph, not scanned trees or measured species. The
published colonization/competition principles motivate this implementation; it
does not copy paper code. Frozen photographic maps and the original basal axis
are reused. Only new immutable outputs are written.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import random

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-canopy-growth.py'
HELPER = ROOT/'scripts/unreal/exterior-canopy-masters.py'
spec = importlib.util.spec_from_file_location('frozen_growth_export_helpers', HELPER)
frozen = importlib.util.module_from_spec(spec); spec.loader.exec_module(frozen)
base = frozen.base
base.OWNER = OWNER
add, sub, mul, dot, cross, unit = frozen.add, frozen.sub, frozen.mul, frozen.dot, frozen.cross, frozen.unit
axis, old_radius, evaluate, tube = frozen.axis, frozen.old_radius, frozen.evaluate, frozen.tube
PROFILES, BARK, REGION = frozen.PROFILES, frozen.BARK, frozen.REGION
SEED = 601227991
REFERENCE = ROOT/'output/unreal/exterior-canopy-masters-20260930-r1d'
REFERENCE_ROWS = {r['id']: r for r in json.loads((REFERENCE/'geometry-manifest.json').read_text())['meshes']}


def tube(mesh, branch, lod):
    order=branch['order'];segments=([12,6,4,2],[9,4,3,2],[7,3,2,1])[lod][order]
    sides=([14,9,6,4],[10,7,5,3],[8,5,4,3])[lod][order]
    ts={j/segments for j in range(segments+1)if order!=0 or not 50.<branch['height']*j/segments<70.}
    if order==0:ts.update(z/branch['height']for z in (0.,10.,25.,40.,50.)if z<branch['height'])
    points,uv,faces=[],[],[]; path=[evaluate(branch,t)for t in sorted(ts)]
    chord=unit(sub(path[-1],path[0]));reference=[0,0,1]if abs(chord[2])<.99 else[0,1,0]
    stable=[1,0,0]if order==0 else unit(cross(chord,reference));distance=0.
    for j,(t,p)in enumerate(zip(sorted(ts),path)):
        tangent=unit(sub(path[min(len(path)-1,j+1)],path[max(0,j-1)]))
        a=unit(sub(stable,mul(tangent,dot(stable,tangent))));b=unit(cross(tangent,a))
        r=branch['radius']*(1-t)**.83+branch['tipRadius']*t
        if order==0 and p[2]<=75.+1e-7:
            a,b=[1,0,0],[0,1,0]
            if p[2]<=50.+1e-7:r=old_radius(branch['oldBasalAxis'],p[2])
        if j:distance+=math.sqrt(dot(sub(p,path[j-1]),sub(p,path[j-1])))
        for k in range(sides+1):
            phi=math.tau*k/sides
            points.append(add(p,add(mul(a,r*math.cos(phi)),mul(b,r*math.sin(phi)))))
            uv.append([math.tau*branch['radius']*k/sides/25.,distance/25.])
    for j in range(len(path)-1):
        for k in range(sides):
            a=j*(sides+1)+k;b=a+sides+1
            faces.extend([(a,a+1,b),(a+1,b+1,b)])
    mesh.geometry(BARK,points,uv,faces,[1,1,1,1])



def skeleton(profile, variant, old, aspect):
    family, source, h, key, nominal = profile
    rng = random.Random(SEED + PROFILES.index(profile)*104729 + variant*7919)
    source_limit = REFERENCE_ROWS[f'canopy_{family}_r1_{"abc"[variant]}']['radialEnvelopeCm']
    radius = source_limit - 25
    p50 = axis(old, 50)
    trunk_h = h*({'broadleaf': .57, 'upright': .65, 'orchard': .49}[family]+rng.uniform(-.045, .025))
    lean, sway = rng.uniform(-.033, .032)*h, rng.uniform(-.025, .031)*h
    branches = [{'kind': 'trunk', 'parent': None, 'parentT': None, 'order': 0, 'height': trunk_h,
        'oldBasalAxis': {'branches': [old['branches'][0]], 'sharedUniformScale': old['sharedUniformScale']},
        'upperPoints': [p50, [p50[0]+lean*.37, p50[1]+sway*.71, 50+(trunk_h-50)*.55],
                        [p50[0]+lean, p50[1]+sway, trunk_h]],
        'radius': old_radius(old, 0), 'tipRadius': 1.35}]
    children = {0: []}
    def append(parent, t, end, order, bend=None):
        start = evaluate(branches[parent], t)
        bend = bend or [0, 0, 0]
        row = {'kind': 'limb', 'parent': parent, 'parentT': t, 'order': order,
               'points': [start, add(add(start, mul(sub(end, start), .5)), bend), end],
               'radius': .18, 'tipRadius': .065, 'growthIteration': -1}
        idx = len(branches); branches.append(row); children[idx] = []; children[parent].append(idx)
        return idx
    # Attraction samples describe one whole crown envelope, not ellipsoidal
    # leaf masses. Sparse sectors and uneven Z density survive graph growth.
    points = []
    gap_yaw = rng.uniform(-math.pi, math.pi)
    zbase = h*{'broadleaf': .27, 'upright': .28, 'orchard': .24}[family]
    for _ in range(4100):
        t = rng.uniform(0, 1); z = zbase+(h-zbase-18)*t
        theta = rng.uniform(-math.pi, math.pi)
        delta = math.atan2(math.sin(theta-gap_yaw), math.cos(theta-gap_yaw))
        if abs(delta)<.48 and rng.random()<.76:
            continue
        radial = radius*(math.sin(math.pi*t)**(.42 if family=='upright' else .28))
        radial *= math.sqrt(rng.random())*(.84+.16*math.sin(theta*3+variant*.83))
        points.append([radial*math.cos(theta)+lean*.25, radial*math.sin(theta)+sway*.25, z])
    attractors = np.asarray(points); original_attractors = len(points)
    seeds = []
    for i in range(nominal+variant):
        t = .30+.66*(i+.5)/(nominal+variant)
        start = evaluate(branches[0], t)
        theta = i*2.399963+variant*.91+rng.uniform(-.45, .45)
        reach = radius*rng.uniform(.22, .39)
        end = add(start, [reach*math.cos(theta), reach*math.sin(theta), h*rng.uniform(.025, .11)])
        seeds.append(append(0, t, end, 1, [0, 0, -h*.012]))
    seeds.append(append(0, 1., add(evaluate(branches[0], 1.), [lean*.16, sway*.1, h*.08]), 1))
    step = {'broadleaf': 18., 'upright': 21., 'orchard': 15.}[family]
    iterations = 0
    for iteration in range(38):
        eligible = [i for i in range(1, len(branches)) if len(children[i])<2]
        ends = np.asarray([branches[i]['points'][-1] for i in eligible])
        if len(attractors)==0 or not eligible or len(branches)>1250:
            break
        # Each environmental sample belongs to one closest active bud; it
        # cannot grow several overlapping branches into the same occupied cell.
        distance = np.linalg.norm(attractors[:, None, :]-ends[None, :, :], axis=2)
        closest = distance.argmin(axis=1); nearest = distance[np.arange(len(attractors)), closest]
        alive = nearest>step*.87
        attractors, closest, nearest = attractors[alive], closest[alive], nearest[alive]
        new_count = 0
        for j, parent in enumerate(eligible):
            targets = attractors[(closest==j)&(nearest<step*5.5)]
            if len(targets)<2:
                continue
            start = ends[j]
            direction = targets-start
            direction /= np.linalg.norm(direction, axis=1)[:, None]
            # Coarse top-light bias; unlit/surrounded buds cease growing when
            # attraction samples have been occupied by competing shoots.
            direction = direction.mean(axis=0)+[rng.uniform(-.05, .05), rng.uniform(-.05, .05), .13]
            direction /= np.linalg.norm(direction)
            end = start+direction*step*rng.uniform(.85, 1.13)
            if end[2]<zbase*.84 or end[2]>h-12 or np.linalg.norm(end[:2])>source_limit-17:
                continue
            idx = append(parent, 1., end.tolist(), 3,
                         [rng.uniform(-1.7, 1.7), rng.uniform(-1.7, 1.7), rng.uniform(-1.2, 1.2)])
            branches[idx]['growthIteration'] = iteration
            branches[idx]['assignedAttractors'] = len(targets)
            new_count += 1
        iterations = iteration+1
        if new_count==0:
            break
    terminal = [i for i in range(1, len(branches)) if not children[i]]
    clusters, leaves = [], []
    core = base.Mesh()
    for b in branches:
        tube(core, b, 0)
    core_triangles = sum(len(part['triangles']) for part in core.parts.values())
    spray_count = sum(2+(node+variant)%2 for node in range(len(terminal)))
    near_limit = REFERENCE_ROWS[f'canopy_{family}_r1_{"abc"[variant]}']['lods'][0]['triangles']
    leaf_nodes = max(5, min(10, int((near_limit-core_triangles-16*spray_count-200)/(8*spray_count))))
    # Equal leaf count ceilings do not create equal leaf balls: each living end
    # carries two to four actual tapered annual shoots with alternating leaves.
    for node, parent in enumerate(terminal):
        incoming = unit(sub(branches[parent]['points'][-1], branches[parent]['points'][0]))
        theta = math.atan2(incoming[1], incoming[0])
        sprays = 2+(node+variant)%2
        cluster = len(clusters)
        clusters.append({'id': cluster, 'branch': parent, 'center': evaluate(branches[parent], 1.),
                         'attachment': evaluate(branches[parent], 1.), 'yaw': theta})
        for shoot in range(sprays):
            t = .64+.33*(shoot+.4)/sprays
            anchor = evaluate(branches[parent], t)
            yaw = theta+(-1 if shoot%2 else 1)*rng.uniform(.37, 1.33)
            length = rng.uniform(24, 44)*( .84 if family=='orchard' else 1.)
            rise = rng.uniform(-.20, .47)*length
            end = add(anchor, [math.cos(yaw)*length, math.sin(yaw)*length, rise])
            sid = append(parent, t, end, 3, [0, 0, rng.uniform(-3, 3)])
            branches[sid]['terminalLeafShoot'] = True
            for k in range(leaf_nodes):
                leaf_t = .12+.87*(k+.15)/leaf_nodes
                azimuth = yaw+(-1 if k%2 else 1)*rng.uniform(.60, 1.12)
                tilt = rng.uniform(-.49, .54)
                along = [math.cos(azimuth)*math.cos(tilt), math.sin(azimuth)*math.cos(tilt), math.sin(tilt)]
                leaves.append({'branch': sid, 't': leaf_t, 'base': evaluate(branches[sid], leaf_t),
                    'length': rng.uniform(8.3, 12.7)*( .82 if family=='orchard' else 1.),
                    'aspect': aspect, 'along': along, 'roll': rng.uniform(-.88, .88),
                    'curl': rng.uniform(-.085, .13), 'twist': rng.uniform(-.10, .10),
                    'cluster': cluster, 'mirror': rng.random()<.5})
    # Pipe taper derives from the supported leaf shoots, rather than unrelated
    # random branch widths. All body branches support living terminal sprays.
    support = {}
    for i in range(len(branches)-1, 0, -1):
        support[i] = sum(support[c] for c in children[i]) if children[i] else 1
        r = max(.065, .115*support[i]**(1/2.1))
        branches[i]['radius'] = r*1.12
        branches[i]['tipRadius'] = r*.68
    return {'sourceFamily': source, 'family': family, 'variant': variant, 'heightCm': h, 'leafMaterial': key,
        'branches': branches, 'clusters': clusters, 'leaves': leaves, 'gapYaw': gap_yaw,
        'basalAxisPreservedHeightCm': 50., 'seed': SEED+PROFILES.index(profile)*104729+variant*7919,
        'growth': {'attractors': original_attractors, 'remainingAttractors': len(attractors),
                   'iterations': iterations, 'terminalSupportBranches': terminal,
                   'leavesPerTerminalShoot': leaf_nodes,
                   'method': 'Nearest active bud competition for whole-crown space with coarse upward light bias',
                   'leafClusterEllipsoids': False, 'nativeAppearanceAccepted': False}}


def leaf(mesh, record, lod, factor):
    along = record['along']; side = unit(cross(along, [0, 0, 1])); normal = unit(cross(side, along))
    roll = record['roll']
    side, normal = add(mul(side, math.cos(roll)), mul(normal, math.sin(roll))), add(mul(normal, math.cos(roll)), mul(side, -math.sin(roll)))
    length = record['length']*factor; width = length*record['aspect']
    rows = [0, .5, 1]; columns = [0, .5, 1] if lod<2 else [0, 1]
    points, uv, faces = [], [], []
    for t in rows:
        for u in columns:
            x = u-.5
            fold = length*(record['curl']*math.sin(math.pi*t)+.025*math.sin(math.pi*t)*(1-abs(x)*2))
            twist = length*record['twist']*x*t
            points.append(add(record['base'], add(mul(along, length*t), add(mul(side, width*x), mul(normal, fold+twist)))))
            uv.append([1-u if record['mirror'] else u, 1-t])
    cols = len(columns)
    for j in range(2):
        for k in range(cols-1):
            a = j*cols+k; b = a+cols
            faces.extend([(a, b, a+1), (a+1, b, b+1)])
    mesh.geometry(record['material'], points, uv, faces, [1, 1, 1, 1])


def projected_leaf_coverage(mesh, material, resolution=512):
    """Saved mesh surface footprint in six fixed camera directions, no floor."""
    part = mesh.parts[material]; positions = np.asarray(part['positions']); triangles = np.asarray(part['triangles'])
    values = []
    for azimuth in (0, math.pi/3, 2*math.pi/3, math.pi, 4*math.pi/3, 5*math.pi/3):
        right = np.asarray([math.cos(azimuth), math.sin(azimuth), 0])
        up = np.asarray([0, 0, 1])
        p = np.column_stack([positions@right, positions@up])
        # Fixed full tree frame shared by all LODs; opaque surface footprint is
        # an upper bound because individual-leaf alpha remains shader-controlled.
        p = (p+np.asarray([400., 0]))/np.asarray([800., 850.])*(resolution-1)
        image = Image.new('1', (resolution, resolution)); draw = ImageDraw.Draw(image)
        for tri in triangles:
            draw.polygon([tuple(row) for row in p[tri]], fill=1)
        values.append(float(np.asarray(image).mean()))
    return values


def fit(meshes, morph, source_mesh):
    bounded = deepcopy(source_mesh)
    bounded['radialEnvelopeCm'] = REFERENCE_ROWS[f'canopy_{morph["family"]}_r1_{"abc"[morph["variant"]]}']['radialEnvelopeCm']
    return frozen.fit(meshes, morph, bounded)


fast_basis = frozen.fast_basis


def build(output,context,library,old_skeleton):
    output,context,library,old_skeleton=map(lambda p:Path(p).resolve(),(output,context,library,old_skeleton))
    base.require(output.is_relative_to(ROOT/'output/unreal')and not output.exists(),'Use a fresh immutable canopy output')
    source=json.loads(context.read_text());old=json.loads(old_skeleton.read_text())
    materials_all=json.loads((library/'material-manifest.json').read_text())
    materials={k:deepcopy(materials_all[k])for k in (BARK,'regional_oak_leaf','regional_green_leaf')}
    old_meshes={r['id']:r for r in json.loads((library/'geometry-manifest.json').read_text())['meshes']}
    trees=[deepcopy(r)for r in source['regionalVegetationPlacements']if r['regionId']==REGION]
    base.require(len(trees)==78,'Unexpected source grove roots')
    output.mkdir(parents=True);records=[];skeletons={};proofs={}
    base.basis=fast_basis
    for key in materials:base.PALETTES[key]=[1,1,1]
    for profile in PROFILES:
        family,source_id,h,leaf_key,nominal=profile
        image=Image.open(materials[leaf_key]['maps']['albedo']['path']);aspect=image.width/image.height
        for variant in range(3):
            mid=f'canopy_growth_{family}_r1_{"abc"[variant]}'
            morph=skeleton(profile,variant,old[source_id],aspect)
            extremes=set()
            # Preserve several representatives from each real cluster at every
            # LOD, including the exact extremal leaf. No new random LOD shapes.
            for cid in range(len(morph['clusters'])):
                ids=[i for i,l in enumerate(morph['leaves'])if l['cluster']==cid]
                for axis_id in range(3):
                    extremes.add(min(ids,key=lambda i:morph['leaves'][i]['base'][axis_id]))
                    extremes.add(max(ids,key=lambda i:morph['leaves'][i]['base'][axis_id]))
            meshes=[];lods=[];selection={}
            for lod in range(3):
                mesh=base.Mesh()
                for branch in morph['branches']:tube(mesh,branch,lod)
                stride=(1,2,4)[lod]
                ids=[i for i in range(len(morph['leaves']))if i%stride==0 or i in extremes]
                for i in ids:
                    l={**morph['leaves'][i],'material':leaf_key}
                    leaf(mesh,l,lod,1. if i in extremes else(1.,1.18,1.60)[lod])
                meshes.append(mesh);selection[str(lod)]=ids
            transform=fit(meshes,morph,old_meshes[source_id])
            for lod,mesh in enumerate(meshes):
                points=np.asarray([p for part in mesh.parts.values()for p in part['positions']]);tri=sum(len(p['triangles'])for p in mesh.parts.values())
                base.require(tri<=REFERENCE_ROWS[f'canopy_{family}_r1_{"abc"[variant]}']['lods'][0]['triangles'],'Growth study exceeds current per-master near budget')
                lods.append({'level':lod,'nodeName':mid+'_LOD'+str(lod),'vertices':len(points),'triangles':tri,
                             'expectedBoundsCm':{'min':points.min(axis=0).tolist(),'max':points.max(axis=0).tolist()},
                             'radialEnvelopeCm':float(np.linalg.norm(points[:,:2],axis=1).max()),'leafCount':len(selection[str(lod)]),
                             'derivation':'Shared unequal connected branch hierarchy; nested photographic individual leaves with retained cluster representatives'})
            glb=output/'glb'/(mid+'.glb');base.write_glb(glb,lods,meshes)
            allpoints=np.asarray([p for mesh in meshes for part in mesh.parts.values()for p in part['positions']])
            row={'id':mid,'sourceFamily':source_id,'role':'tree','placementPolicy':'explicit-only','heightCm':h,
                 'materialKeys':[BARK,leaf_key],'glbPath':str(glb),'glbSha256':base.sha(glb),'lods':lods,
                 'allLodBoundsCm':{'min':allpoints.min(axis=0).tolist(),'max':allpoints.max(axis=0).tolist()},
                 'radialEnvelopeCm':float(np.linalg.norm(allpoints[:,:2],axis=1).max()),
                 'form':'Connected space-competition '+family+' growth with leaves only on terminal annual shoots',
                 'composition':'Original authored growth form. Source tree positions/height are design interpretation, not species/age/site census.',
                 'originalPhotosUnmodified':True,'newMaterialRecipes':False,'branches':len(morph['branches']),
                 'leafCount':len(morph['leaves']),'clusterCount':len(morph['clusters']),'seed':morph['seed']}
            records.append(row);skeletons[mid]=morph
            proofs[mid]={'sourceFamily':source_id,'clusters':[{'id':c['id'],'branch':c['branch'],'centerCm':transform(c['center'])}for c in morph['clusters']],
                         'lodLeafIds':selection,'projectedOpaqueLeafFootprintsByLod':[projected_leaf_coverage(mesh,leaf_key)for mesh in meshes],'basalAxisSamplesCm':[axis(old[source_id],z)for z in (0,10,25,40,50)],
                         'basalRadiiCm':[old_radius(old[source_id],z)for z in (0,10,25,40,50)],'authoringFit':morph['authoringFit']}
            print('CANOPY',mid,[l['triangles']for l in lods],'radius',round(row['radialEnvelopeCm'],2),flush=True)
    inputs={str(p):base.sha(p)for p in (Path(__file__),HELPER,frozen.HELPER,REFERENCE/'geometry-manifest.json',REFERENCE/'canopy-plan.json',context,old_skeleton,library/'geometry-manifest.json',library/'material-manifest.json',
            ROOT/'scripts/unreal/test_exterior_canopy_growth.py',ROOT/'scripts/unreal/preview-canopy-growth.py')}
    for recipe in materials.values():
        for channel in recipe['maps'].values():inputs[channel['path']]=channel['sha256']
    geometry={'schema':1,'units':'metres','owner':OWNER,'revision':'R1 isolated connected competition growth study',
              'axes':'glTF Y-up; Unreal native = [100*x,100*z,100*y]','status':'ISOLATED_STUDY_NOT_SELECTED_NATIVE_PENDING',
              'inputFiles':inputs,'meshes':records}
    base.write(output/'geometry-manifest.json',geometry);base.write(output/'material-manifest.json',materials)
    base.write(output/'asset-manifest.json',{'schema':1,'owner':OWNER,'inputFiles':inputs,
         'sources':[{'kind':'original-authored-geometry','generator':OWNER,'license':'Original project asset'},
                    {'kind':'photographic-individual-leaf-and-bark-maps','license':'CC0-1.0',
                     'sourceUrls':[materials[k]['sourceUrl']for k in materials]}],
         'scope':'Grove morphology only. Existing photos unmodified; regional planting is illustrative, not scanned geometry or botanical site survey.'})
    with (output/'growth-skeletons.json').open('x')as f:json.dump(skeletons,f,separators=(',',':'));f.write('\n')
    base.write(output/'morphology-audit.json',{'owner':OWNER,'meshes':proofs,'photosUnchanged':True,
        'coverageMethod':'Six fixed orthographic views of actual individual leaf triangles,512px full-tree frame. Opaque surface footprint is an upper bound; leaf shader alpha/native shading are excluded.',
        'lodLeafAreaApproximationFactors':[1.,1.18,1.60],
        'references':['https://algorithmicbotany.org/papers/colonization.egwnp2007.html',
                      'https://algorithmicbotany.org/papers/selforg.sig2009.html'],
        'originalImplementationNotPaperCode':True,'nativeAppearanceAccepted':False})
    by_family={source_id:[r['id']for r in records if r['sourceFamily']==source_id]for _,source_id,*_ in PROFILES}
    before=deepcopy(trees)
    for i,row in enumerate(trees):
        original=row['meshId'];variants=by_family[original]
        choice=int(hashlib.sha256(row['id'].encode()).hexdigest()[:8],16)%3
        row.update(meshId=variants[choice],sourceMeshId=original)
    plan={key:deepcopy(source[key])for key in ('sourceSceneSha256','sourceObjSha256','activeDesign','housePlacement')}
    plan.update(schemaVersion=1,owner=OWNER,kind='isolated-grove-canopy-growth-study',regionId=REGION,
                sourceContext={'path':str(context),'sha256':base.sha(context)},geometryManifest={'path':str(output/'geometry-manifest.json'),'sha256':base.sha(output/'geometry-manifest.json')},
                inputFiles={**inputs,str(output/'geometry-manifest.json'):base.sha(output/'geometry-manifest.json'),
                            str(output/'growth-skeletons.json'):base.sha(output/'growth-skeletons.json')},
                canopyPlacements=trees,originalCanopyPlacements=before,
                policy={'preserveRootYawScaleHeightAndRadialEnvelope':True,'targetGroveOnly':True,'sourcePhotographsUnmodified':True,
                        'speciesAgeAndExactRootNotSurveyed':True,'nativeAppearanceAccepted':False,'selectedNativeInput':False,'collisionActorsChanged':False},
                audit={'originalRootsPreserved':78,'variants':9,'lods':27,'materialRecipesAdded':0,'perMesh':dict(Counter(r['meshId']for r in trees))})
    base.write(output/'canopy-plan.json',plan)
    summary={'status':'ISOLATED_STUDY_NOT_SELECTED_NATIVE_PENDING','output':str(output),'canopyPlan':str(output/'canopy-plan.json'),
             'variants':9,'lods':27,'rootCount':78,'generatorSha256':base.sha(__file__),
             'lodTriangles':{r['id']:[l['triangles']for l in r['lods']]for r in records},
             'wholeGroveTriangleTotalsBeforeCulling':{
                 'currentR7':[sum(REFERENCE_ROWS[r['meshId']]['lods'][lod]['triangles']for r in json.loads((REFERENCE/'canopy-plan.json').read_text())['canopyPlacements'])for lod in range(3)],
                 'before':[sum(old_meshes[r['meshId']]['lods'][lod]['triangles']for r in before)for lod in range(3)],
                 'after':[sum(next(m for m in records if m['id']==r['meshId'])['lods'][lod]['triangles']for r in trees)for lod in range(3)]}}
    base.require(summary['wholeGroveTriangleTotalsBeforeCulling']['after'][0]<=summary['wholeGroveTriangleTotalsBeforeCulling']['currentR7'][0],'Actual growth population exceeds current near canopy budget')
    base.write(output/'summary.json',summary);return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True);parser.add_argument('--context',required=True)
    parser.add_argument('--library',required=True);parser.add_argument('--old-skeleton',required=True)
    opt=parser.parse_args();print(json.dumps(build(opt.output,opt.context,opt.library,opt.old_skeleton)))
