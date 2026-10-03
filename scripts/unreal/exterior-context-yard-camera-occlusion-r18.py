"""Read-only source vegetation-volume checks for the corrected yard camera.

No renderer, native raycast or visibility assertion. The complete AABB of all
eye→yard/crown-support segments is tested against conservative source volumes.
Leaf bounds decode original source POSITIONs; lower bark triangles are clipped
at the top of the relevant corridor, so a crown box is not misused as a trunk.
"""
import json
import math
from pathlib import Path
import struct

ROOT=Path(__file__).resolve().parents[2]
OWNER='scripts/unreal/exterior-context-yard-camera-occlusion-r18.py'
CONTEXT=ROOT/'output/unreal/exterior-context-20260927-r8/context-plan.json'
MANIFEST=ROOT/'output/unreal/exterior-canopy-fullness-integration-20261001-r2/geometry-manifest.json'
CANOPY=ROOT/'output/unreal/exterior-canopy-fullness-20261001-r1-study/canopy-plan.json'
ECOLOGY=ROOT/'output/unreal/exterior-canopy-ecology-20260930-r4/canopy-ecology-plan.json'

def require(ok,message):
    if not ok:raise ValueError(message)
def read(file):return json.loads(Path(file).read_text())
def overlap(a,b):return all(a[0][i]<=b[1][i]and b[0][i]<=a[1][i]for i in range(3))
def bounds(points):return [[min(p[k]for p in points)for k in range(3)],[max(p[k]for p in points)for k in range(3)]]
def transformed(local,root):
    yaw=math.radians(root.get('yawDeg',root.get('yawDegrees',0.)));c,s=math.cos(yaw),math.sin(yaw)
    scale=root.get('scale',[root.get('uniformScale',1.)]*3);xyz=root['positionCm']
    def world(p):
        x,y,z=[p[i]*scale[i]for i in range(3)]
        return [xyz[0]+x*c-y*s,xyz[1]+x*s+y*c,xyz[2]+z]
    return bounds([world([x,y,z])for x in(local[0][0],local[1][0])for y in(local[0][1],local[1][1])for z in(local[0][2],local[1][2])])

def actual_source_parts(model):
    data=Path(model['glbPath']).read_bytes();length,kind=struct.unpack_from('<II',data,12)
    require(struct.unpack_from('<III',data)==(0x46546c67,2,len(data))and kind==0x4e4f534a,'Known existing normalized GLB required')
    doc=json.loads(data[20:20+length]);blob=data[28+length:];leaves=[];bark=[]
    def values(number,width,code):
        a=doc['accessors'][number];v=doc['bufferViews'][a['bufferView']];size=struct.calcsize('<'+code*width)
        require(a['componentType']==(5126 if code=='f' else 5125),'Unexpected source attribute component')
        offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',size)
        return [struct.unpack_from('<'+code*width,blob,offset+i*stride)for i in range(a['count'])]
    for lod in model['lods']:
        node=next(n for n in doc['nodes']if n.get('name')==lod['nodeName'])
        require(not any(k in node for k in('matrix','translation','rotation','scale')),'Unaccounted normalized source transform')
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            points=[[x*100,y*100,z*100]for x,z,y in values(primitive['attributes']['POSITION'],3,'f')]
            material=model['materialKeys'][primitive.get('material',0)]
            if any(token in material.lower()for token in('leaf','leaves','foliage')):
                leaves.extend(points)
            else:
                require('indices'in primitive,'Tree bark must be indexed source geometry')
                ids=[row[0]for row in values(primitive['indices'],1,'I')]
                bark.extend([points[j]for j in ids[i:i+3]]for i in range(0,len(ids),3))
    require(leaves,'Tree source material leaf partition is unavailable')
    return {'leafBoundsCm':bounds(leaves),'barkTrianglesCm':bark,'decodedLeafPositionsAllLods':len(leaves),'decodedBarkTrianglesAllLods':len(bark)}

def clipped_lower_bark_bounds(parts,root,world_top):
    scale=root['scale'][2];top=(world_top-root['positionCm'][2])/scale;points=[]
    for tri in parts['barkTrianglesCm']:
        if min(p[2]for p in tri)>top:continue
        previous=tri[-1];previous_inside=previous[2]<=top
        for point in tri:
            inside=point[2]<=top
            if inside!=previous_inside:
                t=(top-previous[2])/(point[2]-previous[2]);points.append([previous[i]+t*(point[i]-previous[i])for i in range(3)])
            if inside:points.append(point)
            previous,previous_inside=point,inside
    return transformed(bounds(points),root)if points else None

def conservative_model_box(model,root):
    local=[[min(l['expectedBoundsCm']['min'][k]for l in model['lods'])for k in range(3)],
           [max(l['expectedBoundsCm']['max'][k]for l in model['lods'])for k in range(3)]]
    return transformed(local,root)

def camera_volumes(view,support):
    eye=[[v-30 for v in view['eyeCm']],[v+30 for v in view['eyeCm']]]
    corridor=bounds([view['eyeCm'],*support])
    return eye,corridor

def support_cone(view,support):
    """Convex hull of eye and complete support AABB, contains every ray."""
    b=bounds(support)
    points=[view['eyeCm'],*[[x,y,z]for x in(b[0][0],b[1][0])for y in(b[0][1],b[1][1])for z in(b[0][2],b[1][2])]]
    axes=[[1.,0.,0.],[0.,1.,0.],[0.,0.,1.]]
    def cross(a,b):return[a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
    def sub(a,b):return[a[k]-b[k]for k in range(3)]
    from itertools import combinations
    for a,b,c in combinations(points,3):axes.append(cross(sub(b,a),sub(c,a)))
    for a,b in combinations(points,2):
        for unit in axes[:3]:axes.append(cross(sub(b,a),unit))
    projections=[]
    for axis in axes:
        length=math.sqrt(sum(v*v for v in axis))
        if length==0.:continue
        unit=[v/length for v in axis];values=[sum(p[k]*unit[k]for k in range(3))for p in points]
        projections.append((unit,min(values),max(values)))
    return {'points':points,'projections':projections}

def cone_overlap(cone,b):
    # All arbitrary axes are valid separating directions. The set includes
    # every hull face normal, AABB normal, and every hull-edge/AABB-edge cross
    # direction. Extra diagonal axes do not remove an actual intersection.
    for axis,lo,hi in cone['projections']:
        b_lo=sum((b[0][k]if axis[k]>=0 else b[1][k])*axis[k]for k in range(3))
        b_hi=sum((b[1][k]if axis[k]>=0 else b[0][k])*axis[k]for k in range(3))
        rounding=8*math.ulp(max(abs(lo),abs(hi),abs(b_lo),abs(b_hi)))
        if b_hi<lo-rounding or hi<b_lo-rounding:return False
    return True

def audit(view,support,layout,old_view):
    context=read(CONTEXT);manifest=read(MANIFEST);models={m['id']:m for m in manifest['meshes']}
    replacements={r['id']:r for r in read(CANOPY)['canopyPlacements']}
    regional=[replacements.get(r['id'],r)for r in context['regionalVegetationPlacements']]
    eye,corridor=camera_volumes(view,support);old_eye,old_corridor=camera_volumes(old_view,support)
    cone=support_cone(view,support)
    parts={};leaf_eye=[];leaf_corridor=[];bark_eye=[];bark_corridor=[];old_eye_hits=[];old_corridor_hits=[];near=[]
    for root in regional:
        model=models[root['meshId']];full=conservative_model_box(model,root)
        # Every regional all-LOD envelope is checked before this selective
        # decode. Remote envelopes cannot intersect either camera/corridor.
        if not any(overlap(full,b)for b in(eye,corridor,old_eye,old_corridor)):continue
        if model['role']!='tree':
            if overlap(full,eye):leaf_eye.append(root['id'])
            if overlap(full,corridor):leaf_corridor.append(root['id'])
            continue
        if model['id']not in parts:parts[model['id']]=actual_source_parts(model)
        record=parts[model['id']];leaf=transformed(record['leafBoundsCm'],root)
        if overlap(leaf,eye):leaf_eye.append(root['id'])
        if overlap(leaf,corridor):leaf_corridor.append(root['id'])
        if overlap(leaf,old_eye):old_eye_hits.append(root['id'])
        if overlap(leaf,old_corridor):old_corridor_hits.append(root['id'])
        lower_eye=clipped_lower_bark_bounds(record,root,eye[1][2])
        lower_corridor=clipped_lower_bark_bounds(record,root,corridor[1][2])
        if lower_eye and overlap(lower_eye,eye):bark_eye.append(root['id'])
        if lower_corridor and overlap(lower_corridor,corridor):bark_corridor.append(root['id'])
        near.append({'id':root['id'],'meshId':root['meshId'],'sourceRootPositionCm':root['positionCm'],
                     'sourceAllLodLeafBoundsCm':leaf,'relevantLowerBarkEyeBoundsCm':lower_eye,
                     'relevantLowerBarkCorridorBoundsCm':lower_corridor})
    require(not leaf_eye and not leaf_corridor and not bark_eye and not bark_corridor,'Corrected camera/corridor intersects original source tree foliage or wood')
    require('village_nearest_grove_15'in old_eye_hits,'R17 tree-crown camera regression was not reproduced from actual leaf POSITIONs')
    # Original authored tree/vine/shrub source rows are bounded by the exact
    # radius-limit/height policy of the frozen importer. None of these remote
    # source records receives a guessed current native mesh identity.
    context_hits=[]
    for row in context['treePlacements']:
        radius=row.get('crownDiameterCm',200.)/2.;height=row.get('heightCm',700.);xyz=row['positionCm']
        maximum_ratio=max(l['expectedBoundsCm']['max'][2]/m['heightCm']for m in manifest['meshes']
            if m['role']in('tree','vine','shrub')and m.get('placementPolicy')!='explicit-only'for l in m['lods'])
        volume=[[xyz[0]-radius,xyz[1]-radius,xyz[2]-2.],[xyz[0]+radius,xyz[1]+radius,xyz[2]+height*maximum_ratio]]
        if overlap(volume,eye)or overlap(volume,corridor):context_hits.append(row['id'])
    require(not context_hits,'Corrected camera/corridor overlaps an original source context tree/shrub envelope')
    ecology=read(ECOLOGY);eco_eye=[];eco_corridor=[];ecology_count=0
    for group in ecology['groups']:
        model=models[group['meshId']]
        for row in group['instances']:
            ecology_count+=1;volume=conservative_model_box(model,row)
            if overlap(volume,eye):eco_eye.append([group['id'],row.get('id'),row['positionCm']])
            if overlap(volume,corridor)and cone_overlap(cone,volume):eco_corridor.append([group['id'],row.get('id'),row['positionCm']])
    require(not eco_eye,'Corrected eye intersects existing low source grove vegetation')
    yard_eye=[];yard_corridor=[];subjects={'yard_r28_plant_0','yard_r28_plant_1'}
    for row in layout['planting']:
        volume=conservative_model_box(models[row['modelId']],row)
        if overlap(volume,eye):yard_eye.append(row['id'])
        if row['id']not in subjects and overlap(volume,corridor):yard_corridor.append(row['id'])
    require(not yard_eye and not yard_corridor,'A non-target yard shrub occludes the proposed eye/support corridor')
    # Whole source low-growth arrays are remote; check every authored root
    # using its source circle/height envelope rather than asserting a native
    # resynthesis of the historic random master choices/height overrides.
    low_counts={};low_hits=[]
    for key in('groundCoverPlacements','meadowBladePlacements','meadowUnderstoryPlacements'):
        rows=context[key];low_counts[key]=len(rows)
        for row in rows:
            xyz=row['positionCm'];radius=row.get('radiusCm',40.);height=row.get('heightCm',80.)
            volume=[[xyz[0]-radius,xyz[1]-radius,xyz[2]-2.],[xyz[0]+radius,xyz[1]+radius,xyz[2]+height]]
            if overlap(volume,eye)or overlap(volume,corridor):low_hits.append(row.get('id'))
    require(not low_hits,'Corrected camera/corridor intersects an original low source growth root envelope')
    return {'scope':'Conservative complete source eye/support-corridor volumes; not a native raycast or visibility proof',
            'sourceEyeClearanceBoxCm':eye,'sourceCompleteYardAndTwoCrownSupportCorridorCm':corridor,
            'sourceCompleteSupportConeVerticesCm':cone['points'],'sourceConeSeparatingProjectionAxes':len(cone['projections']),
            'regionalSourceTreesAndShrubsChecked':len(regional),'originalContextTreeVineShrubRowsChecked':len(context['treePlacements']),
            'sourceLowRootArraysChecked':low_counts,'sourceGroveEcologyInstancesChecked':ecology_count,
            'ownedR28ShrubsChecked':13,'intentionalSubjectsExcludedFromCorridor':['yard_r28_plant_0','yard_r28_plant_1'],
            'sourceEyeTreeLeafHits':leaf_eye,'sourceCorridorTreeLeafHits':leaf_corridor,
            'sourceEyeLowerBarkHits':bark_eye,'sourceCorridorLowerBarkHits':bark_corridor,
            'sourceContextTreeOrShrubHits':context_hits,'sourceEyeEcologyHits':eco_eye,'sourceCorridorEcologyHits':eco_corridor,
            'sourceEyeYardShrubHits':yard_eye,'sourceCorridorOtherYardShrubHits':yard_corridor,
            'sourceLowRootArrayHits':low_hits,'priorR17SourceEyeLeafCrownHits':old_eye_hits,
            'priorR17SourceCorridorLeafCrownHits':old_corridor_hits,'selectivelyDecodedNearTreeParts':near,
            'decodedSourceModelCounts':{key:{k:v for k,v in value.items()if k.startswith('decoded')}for key,value in parts.items()},
            'sourceTreeLeafAndLowerWoodEyeAndCompleteCorridorClear':True,
            'sourceAllVegetationEyeClear':True,
            'sourceLowGrowthCorridorOverlapsRemain':len(eco_corridor),
            'sourceCompleteCorridorAllVegetationClear':not eco_corridor,
            'nativeRaycastExecuted':False,'nativeVisibilityVerified':False}
