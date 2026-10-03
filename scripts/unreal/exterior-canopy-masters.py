"""Isolated successor canopies: unequal connected limbs and photographic leaves.

Only the 78 inferred roots in village_nearest_grove are targeted. Old generators,
materials and output revisions remain immutable. These are authored morphology
studies with licensed photographic leaf/bark maps, not scanned or surveyed trees.
"""
import argparse
from collections import Counter
from copy import deepcopy
import importlib.util
import hashlib
import json
import math
from pathlib import Path
import random

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-canopy-masters.py'
HELPER = ROOT/'scripts/unreal/exterior-garden-masters.py'
spec = importlib.util.spec_from_file_location('immutable_canopy_export_helper', HELPER)
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
base.OWNER = OWNER
add, sub, mul, dot, cross, unit = base.add, base.sub, base.mul, base.dot, base.cross, base.unit
BARK = 'ph_tree_small_02_branches'
REGION = 'village_nearest_grove'
SEED = 601227970
PROFILES = [('broadleaf', 'regional_broadleaf_a', 600., 'regional_oak_leaf', 9),
            ('upright', 'regional_upright_b', 800., 'regional_green_leaf', 10),
            ('orchard', 'regional_orchard_c', 450., 'regional_green_leaf', 8)]


def curve(points, t):
    return add(add(mul(points[0], (1-t)**2), mul(points[1], 2*t*(1-t))), mul(points[2], t*t))


def axis(old, z):
    """Original source lower trunk in native centimetres, shared with root flares."""
    trunk = old['branches'][0]; scale = old['sharedUniformScale']
    t = z/(trunk['points'][-1][2]*100*scale)
    p = curve(trunk['points'], t)
    return [p[0]*100*scale, -p[1]*100*scale, z]


def old_radius(old, z):
    trunk = old['branches'][0]; scale = old['sharedUniformScale']
    t = z/(trunk['points'][-1][2]*100*scale)
    return (trunk['radius']*(1-t)+trunk['tipRadius']*t)*100*scale


def evaluate(branch, t):
    if branch['kind'] != 'trunk': return curve(branch['points'], t)
    z = branch['height']*t
    if z <= 50: return axis(branch['oldBasalAxis'], z)
    return curve(branch['upperPoints'], (z-50)/(branch['height']-50))


def skeleton(profile, variant, old, aspect):
    family, source, h, leaf_key, nominal = profile
    rng = random.Random(SEED+PROFILES.index(profile)*104729+variant*7919)
    radius = {'broadleaf':252., 'upright':234., 'orchard':233.}[family]
    trunk_h = h*({'broadleaf':.82, 'upright':.91, 'orchard':.66}[family]+rng.uniform(-.045,.025))
    p50 = axis(old, 50)
    lean = rng.uniform(-.038,.043)*h; sway = rng.uniform(-.024,.029)*h
    branches = [{'kind':'trunk', 'parent':None, 'parentT':None, 'order':0, 'height':trunk_h,
                 'oldBasalAxis':{'branches':[old['branches'][0]], 'sharedUniformScale':old['sharedUniformScale']},
                 'upperPoints':[p50, [p50[0]+lean*.26,p50[1]+sway*.83,50+(trunk_h-50)*.57],
                                [p50[0]+lean,p50[1]+sway,trunk_h]],
                 'radius':old_radius(old,0), 'tipRadius':1.35}]
    clusters, leaves = [], []
    gap_yaw = rng.uniform(-math.pi,math.pi); primary_ids=[]

    def branch(parent, t, end, radius_cm, order, bend):
        start = evaluate(branches[parent], t)
        middle = add(add(start,mul(sub(end,start),.5)),bend)
        row={'kind':'limb','parent':parent,'parentT':t,'points':[start,middle,end],
             'radius':radius_cm,'tipRadius':max(.036,radius_cm*(.17 if order<3 else .11)), 'order':order}
        branches.append(row);return len(branches)-1

    n = nominal+variant-1
    for i in range(n):
        t = .23+.70*(i+.3)/n+rng.uniform(-.035,.035)
        start = evaluate(branches[0],t)
        az = i*2.399963+variant*.83+rng.uniform(-.25,.25)
        # A real missing/weak limb sector and unequal reaches interrupt the
        # former uniform envelope; individual leaves never fill this gap later.
        delta = math.atan2(math.sin(az-gap_yaw),math.cos(az-gap_yaw))
        weakness = .55 if abs(delta)<.48 else 1.
        reach = radius*rng.uniform(.47,.84)*weakness
        if family=='upright': tip_z=h*(.55+.33*(i/n)**.8+rng.uniform(-.048,.048))
        elif family=='orchard': tip_z=h*(.50+.28*(i/n)**.8+rng.uniform(-.055,.055))
        else: tip_z=h*(.54+.30*(i/n)**.8+rng.uniform(-.058,.058))
        end=[math.cos(az)*reach,math.sin(az)*reach,min(h*.90,max(start[2]+h*.045,tip_z))]
        if family=='orchard' and i%3==0:end[2]-=h*.035
        pid=branch(0,t,end,max(2.,old_radius(old,start[2])*.61),1,
                   [-math.cos(az)*reach*.08,-math.sin(az)*reach*.08,-h*rng.uniform(.012,.048)])
        primary_ids.append(pid)
    # One unequal living apical branch, rather than duplicated symmetric forks.
    top=evaluate(branches[0],.94)
    primary_ids.append(branch(0,.94,add(top,[radius*.13,radius*.06,h*.105]),2.1,1,[radius*.02,0,h*.026]))
    for pi,pid in enumerate(primary_ids):
        pb=branches[pid];az=math.atan2(pb['points'][-1][1]-pb['points'][0][1],pb['points'][-1][0]-pb['points'][0][0])
        for j in range(3 if pi%3 else 4):
            t=.38+j*.16+rng.uniform(-.035,.025);start=evaluate(pb,t)
            sign=-1 if j%2 else 1;theta=az+sign*rng.uniform(.30,.95)
            reach=radius*rng.uniform(.13,.28);rise=h*rng.uniform(-.018,.078)
            end=add(start,[reach*math.cos(theta),reach*math.sin(theta),rise])
            sid=branch(pid,t,end,pb['radius']*rng.uniform(.23,.36),2,[0,0,-h*.007])
            cluster_id=len(clusters)
            clusters.append({'id':cluster_id,'branch':sid,'center':evaluate(branches[sid],.70),
                             'primary':pid,'attachment':start,'yaw':theta})
            for shoot in range(15):
                f=.24+.75*(shoot+.35)/15+rng.uniform(-.013,.013)
                anchor=evaluate(branches[sid],f)
                # Alternating shoots follow the supporting limb. Unequal shoot
                # lengths and leaf roll create a ragged, layered silhouette.
                phi=theta+(-1 if shoot%2 else 1)*rng.uniform(.43,1.38)
                length=rng.uniform(42.,83.)*(.90 if family=='orchard'else 1.)
                end=add(anchor,[length*math.cos(phi),length*math.sin(phi),rng.uniform(-42.,73.)])
                twig=branch(sid,f,end,rng.uniform(.12,.25),3,[0,0,rng.uniform(-2.2,2.2)])
                for node in range(14):
                    leaf_t=.10+.89*(node+.12)/14
                    side=-1 if node%2 else 1
                    azimuth=phi+side*rng.uniform(.64,1.38)
                    tilt=rng.uniform(-.56,.54);roll=rng.uniform(-.86,.86)
                    along=[math.cos(azimuth)*math.cos(tilt),math.sin(azimuth)*math.cos(tilt),math.sin(tilt)]
                    leaves.append({'branch':twig,'t':leaf_t,'base':evaluate(branches[twig],leaf_t),
                                   'length':rng.uniform(11.4,16.8)*(.91 if family=='orchard'else 1.),
                                   'aspect':aspect,'along':along,'roll':roll,'curl':rng.uniform(-.10,.15),
                                   'twist':rng.uniform(-.10,.10),'cluster':cluster_id,'mirror':rng.random()<.5})
    return {'sourceFamily':source,'family':family,'variant':variant,'heightCm':h,'leafMaterial':leaf_key,
            'branches':branches,'clusters':clusters,'leaves':leaves,'gapYaw':gap_yaw,
            'basalAxisPreservedHeightCm':50.,'seed':SEED+PROFILES.index(profile)*104729+variant*7919}


def tube(mesh, branch, lod):
    order=branch['order'];segments=([12,6,4,2],[9,4,3,2],[7,3,2,1])[lod][order]
    sides=([14,9,6,4],[10,7,5,3],[8,5,4,3])[lod][order]
    ts={j/segments for j in range(segments+1)}
    if order==0:ts.update(z/branch['height']for z in (0.,10.,25.,40.,50.)if z<branch['height'])
    points,uv,faces=[],[],[]; path=[evaluate(branch,t)for t in sorted(ts)]
    chord=unit(sub(path[-1],path[0]));reference=[0,0,1]if abs(chord[2])<.99 else[0,1,0]
    stable=[1,0,0]if order==0 else unit(cross(chord,reference));distance=0.
    for j,(t,p)in enumerate(zip(sorted(ts),path)):
        tangent=unit(sub(path[min(len(path)-1,j+1)],path[max(0,j-1)]))
        a=unit(sub(stable,mul(tangent,dot(stable,tangent))));b=unit(cross(tangent,a))
        r=branch['radius']*(1-t)**.83+branch['tipRadius']*t
        if order==0 and p[2]<=50.+1e-7:
            a,b=[1,0,0],[0,1,0];r=old_radius(branch['oldBasalAxis'],p[2])
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


def leaf(mesh, record, lod, factor):
    along=record['along'];side=unit(cross(along,[0,0,1]));normal=unit(cross(side,along))
    roll=record['roll'];side,normal=add(mul(side,math.cos(roll)),mul(normal,math.sin(roll))),add(mul(normal,math.cos(roll)),mul(side,-math.sin(roll)))
    length=record['length']*factor;width=length*record['aspect']
    rows=([0,.24,.49,.75,1],[0,.5,1],[0,.53,1])[lod];columns=[0,.5,1]if lod<2 else[0,1]
    points,uv,faces=[],[],[]
    for t in rows:
        for u in columns:
            x=u-.5
            fold=length*(record['curl']*math.sin(math.pi*t)+.035*math.sin(math.pi*t)*(1-abs(x)*2))
            twist=length*record['twist']*x*t
            p=add(record['base'],add(mul(along,length*t),add(mul(side,width*x),mul(normal,fold+twist))))
            points.append(p);uv.append([1-u if record['mirror']else u,1-t])
    cols=len(columns)
    for j in range(len(rows)-1):
        for k in range(cols-1):
            a=j*cols+k;b=a+cols;faces.extend([(a,b,a+1),(a+1,b,b+1)])
    mesh.geometry(record['material'],points,uv,faces,[1,1,1,1])


def fast_basis(part):
    """Area normals and orthogonal UV tangent basis, with independent tests."""
    p=np.asarray(part['positions'],dtype=np.float64);uv=np.asarray(part['uv']);tri=np.asarray(part['triangles'])
    a,b,c=p[tri[:,0]],p[tri[:,1]],p[tri[:,2]];e1,e2=b-a,c-a;n=np.cross(e1,e2)
    base.require(np.min(np.linalg.norm(n,axis=1))>1e-9,'Degenerate canopy face')
    du,dv=uv[tri[:,1]]-uv[tri[:,0]],uv[tri[:,2]]-uv[tri[:,0]]
    det=du[:,0]*dv[:,1]-du[:,1]*dv[:,0];base.require(np.min(np.abs(det))>1e-12,'Degenerate canopy UV')
    t=(e1*dv[:,1,None]-e2*du[:,1,None])/det[:,None]
    bt=(e2*du[:,0,None]-e1*dv[:,0,None])/det[:,None]
    normal=np.zeros_like(p);tangent=np.zeros_like(p);bitangent=np.zeros_like(p)
    for k in range(3):
        np.add.at(normal,tri[:,k],n);np.add.at(tangent,tri[:,k],t);np.add.at(bitangent,tri[:,k],bt)
    normal/=np.linalg.norm(normal,axis=1)[:,None]
    tangent-=normal*np.sum(tangent*normal,axis=1)[:,None];tangent/=np.linalg.norm(tangent,axis=1)[:,None]
    handed=np.where(np.sum(np.cross(normal,tangent)*bitangent,axis=1)<0,-1.,1.)
    base.require(np.isfinite(normal).all()and np.isfinite(tangent).all(),'Invalid canopy tangent frame')
    return normal.tolist(),np.column_stack([tangent,handed]).tolist()


def fit(meshes, morph, source_mesh):
    points=np.asarray([p for mesh in meshes for part in mesh.parts.values()for p in part['positions']])
    top=points[:,2].max();height=morph['heightCm'];zfactor=(height-50)/(top-50)
    oldrad=source_mesh['radialEnvelopeCm'];rad=np.linalg.norm(points[:,:2],axis=1).max();xyfactor=min(1.,(oldrad-.8)/rad)
    # One common authoring map for every LOD. The existing basal trunk is locked
    # exactly; upper branch shape is fit to inherited source height/radial bounds.
    def position(p):
        weight=min(1.,max(0.,(p[2]-50)/70))
        s=1+(xyfactor-1)*weight
        return [p[0]*s,p[1]*s,p[2]if p[2]<=50 else 50+(p[2]-50)*zfactor]
    for mesh in meshes:
        for part in mesh.parts.values():part['positions']=[position(p)for p in part['positions']]
    morph['authoringFit']={'upperZFactor':zfactor,'outerXYFactor':xyfactor,'basalLockHeightCm':50.,
                          'oldActualRadiusCm':oldrad,'sourceHeightCm':height,
                          'allLodsShareSameMap':True,'actorScaleRemainsUniformAndUnchanged':True}
    return position


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
            mid=f'canopy_{family}_r1_{"abc"[variant]}'
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
                stride=(1,2,8)[lod]
                ids=[i for i in range(len(morph['leaves']))if i%stride==0 or i in extremes]
                for i in ids:
                    l={**morph['leaves'][i],'material':leaf_key}
                    leaf(mesh,l,lod,1. if i in extremes else(1.,1.20,2.20)[lod])
                meshes.append(mesh);selection[str(lod)]=ids
            transform=fit(meshes,morph,old_meshes[source_id])
            for lod,mesh in enumerate(meshes):
                points=np.asarray([p for part in mesh.parts.values()for p in part['positions']]);tri=sum(len(p['triangles'])for p in mesh.parts.values())
                base.require(tri<165000,'Canopy near LOD exceeds inherited maximum budget')
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
                 'form':'Irregular connected '+family+' canopy with unequal limbs, clustered growth and genuine crown gaps',
                 'composition':'Original authored growth form. Source tree positions/height are design interpretation, not species/age/site census.',
                 'originalPhotosUnmodified':True,'newMaterialRecipes':False,'branches':len(morph['branches']),
                 'leafCount':len(morph['leaves']),'clusterCount':len(morph['clusters']),'seed':morph['seed']}
            records.append(row);skeletons[mid]=morph
            proofs[mid]={'sourceFamily':source_id,'clusters':[{'id':c['id'],'branch':c['branch'],'centerCm':transform(c['center'])}for c in morph['clusters']],
                         'lodLeafIds':selection,'basalAxisSamplesCm':[axis(old[source_id],z)for z in (0,10,25,40,50)],
                         'basalRadiiCm':[old_radius(old[source_id],z)for z in (0,10,25,40,50)],'authoringFit':morph['authoringFit']}
            print('CANOPY',mid,[l['triangles']for l in lods],'radius',round(row['radialEnvelopeCm'],2),flush=True)
    inputs={str(p):base.sha(p)for p in (Path(__file__),HELPER,context,old_skeleton,library/'geometry-manifest.json',library/'material-manifest.json',
            ROOT/'scripts/unreal/test_exterior_canopy_masters.py',ROOT/'scripts/unreal/preview-canopy-masters.py')}
    for recipe in materials.values():
        for channel in recipe['maps'].values():inputs[channel['path']]=channel['sha256']
    geometry={'schema':1,'units':'metres','owner':OWNER,'revision':'R1 irregular grove canopy morphology',
              'axes':'glTF Y-up; Unreal native = [100*x,100*z,100*y]','status':'OFFLINE_NOT_NATIVE_ACCEPTED',
              'inputFiles':inputs,'meshes':records}
    base.write(output/'geometry-manifest.json',geometry);base.write(output/'material-manifest.json',materials)
    base.write(output/'asset-manifest.json',{'schema':1,'owner':OWNER,'inputFiles':inputs,
         'sources':[{'kind':'original-authored-geometry','generator':OWNER,'license':'Original project asset'},
                    {'kind':'photographic-individual-leaf-and-bark-maps','license':'CC0-1.0',
                     'sourceUrls':[materials[k]['sourceUrl']for k in materials]}],
         'scope':'Grove morphology only. Existing photos unmodified; regional planting is illustrative, not scanned geometry or botanical site survey.'})
    with (output/'growth-skeletons.json').open('x')as f:json.dump(skeletons,f,separators=(',',':'));f.write('\n')
    base.write(output/'morphology-audit.json',{'owner':OWNER,'meshes':proofs,'photosUnchanged':True})
    by_family={source_id:[r['id']for r in records if r['sourceFamily']==source_id]for _,source_id,*_ in PROFILES}
    before=deepcopy(trees)
    for i,row in enumerate(trees):
        original=row['meshId'];variants=by_family[original]
        choice=int(hashlib.sha256(row['id'].encode()).hexdigest()[:8],16)%3
        row.update(meshId=variants[choice],sourceMeshId=original)
    plan={key:deepcopy(source[key])for key in ('sourceSceneSha256','sourceObjSha256','activeDesign','housePlacement')}
    plan.update(schemaVersion=1,owner=OWNER,kind='grove-only-canopy-replacement',regionId=REGION,
                sourceContext={'path':str(context),'sha256':base.sha(context)},geometryManifest={'path':str(output/'geometry-manifest.json'),'sha256':base.sha(output/'geometry-manifest.json')},
                inputFiles={**inputs,str(output/'geometry-manifest.json'):base.sha(output/'geometry-manifest.json'),
                            str(output/'growth-skeletons.json'):base.sha(output/'growth-skeletons.json')},
                canopyPlacements=trees,originalCanopyPlacements=before,
                policy={'preserveRootYawScaleHeightAndRadialEnvelope':True,'targetGroveOnly':True,'sourcePhotographsUnmodified':True,
                        'speciesAgeAndExactRootNotSurveyed':True,'nativeAppearanceAccepted':False},
                audit={'originalRootsPreserved':78,'variants':9,'lods':27,'materialRecipesAdded':0,'perMesh':dict(Counter(r['meshId']for r in trees))})
    base.write(output/'canopy-plan.json',plan)
    summary={'status':'OFFLINE_GENERATED_NATIVE_PENDING','output':str(output),'canopyPlan':str(output/'canopy-plan.json'),
             'variants':9,'lods':27,'rootCount':78,'generatorSha256':base.sha(__file__),
             'lodTriangles':{r['id']:[l['triangles']for l in r['lods']]for r in records},
             'wholeGroveTriangleTotalsBeforeCulling':{
                 'before':[sum(old_meshes[r['meshId']]['lods'][lod]['triangles']for r in before)for lod in range(3)],
                 'after':[sum(next(m for m in records if m['id']==r['meshId'])['lods'][lod]['triangles']for r in trees)for lod in range(3)]}}
    base.write(output/'summary.json',summary);return summary


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',required=True);parser.add_argument('--context',required=True)
    parser.add_argument('--library',required=True);parser.add_argument('--old-skeleton',required=True)
    opt=parser.parse_args();print(json.dumps(build(opt.output,opt.context,opt.library,opt.old_skeleton)))
