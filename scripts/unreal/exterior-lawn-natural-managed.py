"""Fresh managed-only plan successor; frozen natural lawn masters stay exact.

The earlier full source-lawn study included intentionally unmanaged rural cover.
This derivative intersects that exact source domain with the actual pinned rural
keep polygons and retains only complete all-LOD crowns with an additional 1 mm.
No geometry, material, scan, historical plan or native project is overwritten.
"""
import argparse
from collections import Counter
from copy import deepcopy
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-lawn-natural-managed.py'


def require(ok,message):
    if not ok:raise ValueError(message)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):return json.loads(Path(path).read_text())


def write(path,value,compact=False):
    with Path(path).open('x')as stream:
        json.dump(value,stream,ensure_ascii=False,allow_nan=False,indent=None if compact else 2,
                  separators=(',',':')if compact else None);stream.write('\n')


def source_to_native(shape):
    return shapely.transform(shape,lambda xyz:np.column_stack([xyz[:,0]/10,-xyz[:,1]/10]))


def native_to_source(shape):
    return shapely.transform(shape,lambda xyz:np.column_stack([xyz[:,0]*10,-xyz[:,1]*10]))


def build(base,rural_path,output):
    base,rural_path,output=map(lambda p:Path(p).resolve(),(base,rural_path,output))
    require(output.is_relative_to(ROOT/'output/unreal')and not output.exists(),'Use a fresh immutable managed lawn output')
    original=read(base/'lawn-natural-plan.json');rural=read(rural_path);library=read(base/'geometry-manifest.json')
    require(original['owner']=='scripts/unreal/exterior-lawn-natural.py','Wrong frozen natural source owner')
    require(original['activeDesign']==rural['metadata']['activeDesign']=={'variant':'C','livingLayout':'B','heatingLayout':'B'},'Only C/B/B is supported')
    require(original['housePlacement']==rural['metadata']['housePlacement'],'Rural placement frame mismatch')
    require(original['housePlacement']['streetSetbackMm']==original['housePlacement']['eastSetbackMm']==3000,'3000 mm setbacks required')
    # Frozen rural geometry predates explicit top-level scene/OBJ frame hashes.
    # Pin its sibling scene/OBJ directly instead of inventing missing metadata.
    require(original['sourceSceneSha256']==sha(rural_path.parent/'scene.json')and
            original['sourceObjSha256']==sha(rural_path.parent/'dom-mm.obj'),'Rural/source frame mismatch')
    for path,digest in original['inputFiles'].items():require(sha(path)==digest,'Frozen natural input drift: '+path)
    kept=rural['managedLawnKeepPolygonsCm'];require(len(kept)==2,'Unexpected managed keep geometry')
    keep=unary_union([Polygon(p)for p in kept]);require(keep.is_valid,'Invalid managed keep union')
    source=source_to_native(shapely.from_geojson(original['lawnDomainSourceMm']))
    # Exact shared polygon edges can leave zero-area line members in a GEOS
    # GeometryCollection; only its unchanged polygon area is a planting domain.
    domain=source.intersection(keep).buffer(0)
    require(domain.is_valid and 140<domain.area/10000<150,'Unexpected exact managed lawn area')
    rows={row['id']:row for row in library['meshes']};groups=[];rejected=Counter();minimum=math.inf;outside_roots=0
    for group in original['groups']:
        result=deepcopy(group);result['instances']=[]
        radius=max(lod['radialEnvelopeCm']for lod in rows[group['meshId']]['lods'])
        for item in group['instances']:
            point=shapely.Point(item['positionCm'][:2]);scale=item['scale'][0];world_radius=radius*scale
            if not keep.contains(point):outside_roots+=1;rejected['root-outside-managed-keep']+=1;continue
            distance=point.distance(domain.boundary)
            require(math.isfinite(distance),'Nonfinite managed domain clearance')
            if not domain.contains(point)or distance<=world_radius+.1:rejected['whole-crown-managed-clearance']+=1;continue
            row=deepcopy(item);row['clearanceMm']=distance*10;row['enclosingRadiusMm']=world_radius*10+1
            row['radiusCm']=world_radius;result['instances'].append(row);minimum=min(minimum,(distance-world_radius)*10-1)
        if result['instances']:groups.append(result)
    placements=[{'meshId':group['meshId'],**row}for group in groups for row in group['instances']]
    require(8500<len(placements)<10000,'Unexpected managed-only natural lawn count')
    budgets=[sum(len(group['instances'])*rows[group['meshId']]['lods'][lod]['triangles']for group in groups)for lod in range(3)]
    input_files=deepcopy(original['inputFiles'])
    for path in [Path(__file__),rural_path,rural_path.parent/'scene.json',rural_path.parent/'dom-mm.obj',
        *[base/name for name in ('lawn-natural-plan.json','lawn-natural-manifest.json',
        'geometry-manifest.json','material-manifest.json','asset-manifest.json','lawn-natural-prototypes.json','lawn-natural.glb')]]:
        input_files[str(path)]=sha(path)
    audit={**original['audit'],'status':'PASS_STATIC_MANAGED_GEOMETRY_AND_CLEARANCE','instances':len(placements),'groups':len(groups),
        'edgeInstances':sum(row['edge']for row in placements),'perMesh':dict(Counter(row['meshId']for row in placements)),
        'nearTriangleBudget':budgets[0],'allInstancesTriangleBudgetByLod':budgets,
        'minimumAdditionalCrownClearanceMm':minimum,'exactAllowedDomainM2':domain.area/10000,
        'fullSourceLawnM2':source.area/10000,'unmanagedSourceLawnExcludedM2':source.difference(keep).area/10000,
        'sourceR1Instances':len(original['lawnPlacements']),'excludedR1RootsOutsideKeep':outside_roots,
        'excludedR1WholeCrownsAtManagedBoundary':rejected['whole-crown-managed-clearance'],
        'managedLawnKeepPolygonsPreserved':True,'masterGeometryAndMaterialUnchanged':True,'nativeVerified':False,
        'crownProof':'Complete radial envelope of every unchanged actual GLB LOD vertex, inside exact source lawn intersected with actual pinned rural keep union, plus1mm; WPO forbidden.',
        'rejected':dict(rejected),'boundaryPlacement':'Retained original irregular patches; no new edge layer across management boundary.'}
    # Recompute statistics for the exact retained population; full-domain values
    # cannot serve as evidence for this narrower rendering plan.
    roots=np.array([row['positionCm'][:2]for row in placements])*10
    audit['sixtyMmLatticePhaseAmplitudeXY']=[float(abs(np.exp(2j*np.pi*roots[:,i]/60).mean()))for i in range(2)]
    interior=np.array([row['scale'][0]for row in placements if not row['edge']])
    audit['interiorHeightScaleRange']=[float(interior.min()),float(interior.max())]
    audit['interiorHeightScaleStandardDeviation']=float(interior.std())
    audit['coherentDryGrowthInstances']=sum(row['growthClass']for row in placements)
    audit.pop('nearestPatchCentreDistanceMm',None)
    common={'owner':OWNER,'generatorSha256':sha(__file__),'inputFiles':input_files,
        'managedLawnPlan':{'path':str(rural_path),'sha256':sha(rural_path)},'managedLawnKeepPolygonsCm':kept,
        'derivedFrom':{'path':str(base/'lawn-natural-plan.json'),'sha256':sha(base/'lawn-natural-plan.json')}}
    plan=deepcopy(original);plan.update(common,groups=groups,lawnPlacements=placements,audit=audit,
        sourceLawnDomainSourceMm=original['lawnDomainSourceMm'],lawnDomainSourceMm=shapely.to_geojson(native_to_source(domain)))
    plan['replacementPolicy'].update(managedOnly=True,completeCrownsInsideManagedKeep=True,
        unmanagedRuralGroundcoverPreserved=True)
    library.update(common,revision='Natural curved lawn R2 confined to pinned rural managed lawn')
    output.mkdir(parents=True);write(output/'geometry-manifest.json',library)
    plan['geometryManifest']={'path':str(output/'geometry-manifest.json'),'sha256':sha(output/'geometry-manifest.json')}
    write(output/'material-manifest.json',read(base/'material-manifest.json'))
    sources=read(base/'asset-manifest.json');sources.update(common)
    sources['scope']='Only the exact rural managed subset of the existing source lawn; source masters/photos/materials unchanged.'
    write(output/'asset-manifest.json',sources);write(output/'lawn-natural-plan.json',plan,compact=True);write(output/'lawn-natural-audit.json',audit)
    manifest=read(base/'lawn-natural-manifest.json');manifest.update(common,audit=audit,status='PASS_STATIC_MANAGED_NOT_NATIVE_ACCEPTED')
    for key,name in [('plan','lawn-natural-plan.json'),('geometryManifest','geometry-manifest.json'),('materialManifest','material-manifest.json')]:
        manifest[key]={'path':str(output/name),'sha256':sha(output/name)}
    manifest['integrationContract']='Merge unchanged explicit-only masters and append exact managed-only groups. Hide only four verified inherited lawn actors; preserve all existing unmanaged rural/yard/meadow/herb groups. Native crowns must satisfy pinned rural keep union as well as original source lawn/exclusions.'
    write(output/'lawn-natural-manifest.json',manifest)
    views=read(base/'lawn-qa-views.json');views.update(owner=OWNER,generatorSha256=sha(__file__),managedLawnPlan=common['managedLawnPlan'],
        plan={'path':str(output/'lawn-natural-plan.json'),'sha256':sha(output/'lawn-natural-plan.json')})
    for view in views['views']:
        for key in('eyeCm','targetCm'):require(domain.contains(shapely.Point(view[key][:2])),'Existing lawn camera escaped managed lawn')
    write(output/'lawn-qa-views.json',views)
    return audit


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',required=True);parser.add_argument('--rural',required=True);parser.add_argument('--output',required=True)
    a=parser.parse_args();print(json.dumps(build(a.base,a.rural,a.output)))
