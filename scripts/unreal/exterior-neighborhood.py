"""Append local settlement and gravel detail without changing official footprints.

Windows, rainwater goods and chimneys are authored visual estimates. No new
house, fence, ownership information or infrastructure is inferred on the empty
development parcels. The frame and real cadastral surfaces are inherited.
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

import shapely
from shapely.geometry import LineString, Point, Polygon
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-neighborhood.py'
SPEC = importlib.util.spec_from_file_location('neighborhood_buildings', ROOT / 'scripts/unreal/exterior-buildings.py')
base = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(base)
require, sha, read, encode = base.require, base.sha, base.read, base.encode


def box(mesh, origin, tangent, outward, start, finish, bottom, top, depth=4, solid=False):
    """Small facade box. All dimensions/positions are in UE centimetres."""
    def p(s, d, z):
        return [origin[0] + tangent[0]*s + outward[0]*d,
                origin[1] + tangent[1]*s + outward[1]*d, z]
    front = [p(start, depth, bottom), p(finish, depth, bottom),
             p(finish, depth, top), p(start, depth, top)]
    mesh.face(front, [*outward, 0])
    # Village facades are >=159m from the subject house. Relief planes retain
    # visible sash/reveal offset while avoiding 8 invisible side triangles per
    # tiny frame member; only chimney volumes need full spatial side faces.
    if not solid:
        return
    mesh.face([p(start, 0, bottom), *front[:2], p(finish, 0, bottom)], [0, 0, -1])
    mesh.face([p(start, 0, top), p(finish, 0, top), front[2], front[3]], [0, 0, 1])
    mesh.face([p(start, 0, bottom), p(start, 0, top), front[3], front[0]], [-tangent[0], -tangent[1], 0])
    mesh.face([p(finish, 0, bottom), front[1], front[2], p(finish, 0, top)], [*tangent, 0])


def tube(mesh, a, b, radius, sides=6):
    direction = [b[i]-a[i] for i in range(3)]
    length = math.sqrt(sum(v*v for v in direction))
    require(length > 1e-6, 'Degenerate pipe')
    axis = [v/length for v in direction]
    reference = [0., 0., 1.] if abs(axis[2]) < .9 else [1., 0., 0.]
    u = [axis[1]*reference[2]-axis[2]*reference[1],
         axis[2]*reference[0]-axis[0]*reference[2],
         axis[0]*reference[1]-axis[1]*reference[0]]
    norm = math.sqrt(sum(v*v for v in u)); u = [v/norm for v in u]
    v = [axis[1]*u[2]-axis[2]*u[1], axis[2]*u[0]-axis[0]*u[2], axis[0]*u[1]-axis[1]*u[0]]
    rings = [[ [point[k]+radius*(u[k]*math.cos(2*math.pi*j/sides)+v[k]*math.sin(2*math.pi*j/sides))
                 for k in range(3)] for j in range(sides)] for point in (a, b)]
    for j in range(sides):
        outward = [(rings[0][j][k]-a[k])/radius for k in range(3)]
        mesh.face([rings[0][j], rings[0][(j+1)%sides], rings[1][(j+1)%sides], rings[1][j]], outward)
    mesh.face(list(reversed(rings[0])), [-x for x in axis]); mesh.face(rings[1], axis)


def shapes(shape):
    if shape.is_empty:
        return []
    if shape.geom_type == 'Polygon':
        return [shape] if shape.area > 1 else []
    return [piece for part in getattr(shape, 'geoms', []) for piece in shapes(part)]


def build(context_path, buildings_path, scene_path):
    context, village, scene = map(read, (context_path, buildings_path, scene_path))
    require(context['sourceSceneSha256'] == village['sourceSceneSha256'] == sha(scene_path), 'Neighborhood frame differs')
    require(context['sourceObjSha256'] == village['sourceObjSha256'], 'Neighborhood architectural source differs')
    require(scene['activeDesign'] == {'variant':'C','heatingLayout':'B','livingLayout':'B'}, 'C/B/B required')
    require(context['housePlacement']['streetSetbackMm'] == context['housePlacement']['eastSetbackMm'] == 3000, 'Setbacks differ')
    protected = unary_union([Polygon(p) for p in context['protectedTrianglesCm']])
    chunks, counts, building_audit = {}, Counter(), []
    def chunk(cell, material):
        key = (tuple(cell), material)
        if key not in chunks:
            name = '_'.join(('m'+str(-v)) if v < 0 else str(v) for v in cell)
            chunks[key] = base.Mesh('neighborhood_'+name+'_'+material.removeprefix('context_'), material)
            chunks[key].record['maxDrawDistanceCm'] = 65000 if material != 'context_track' else 18000
        return chunks[key]

    # Trim and shadowed glazing make the official low massing read as houses
    # in the medium distance. This does not alter any source wall/roof mesh.
    selected = [b for b in village['buildings'] if b['sourceDistanceMetres'] <= 600]
    roof_sampler = base.GroundSampler({'meshes':[m for m in village['meshes'] if m['material'] in ('context_village_roof','context_village_darkroof')]})
    for building in selected:
        rng = random.Random(int(hashlib.sha256(building['id'].encode()).hexdigest()[:14], 16))
        cell = building['cell']; details = Counter()
        metal, trim, timber = (chunk(cell, mat) for mat in ('context_wire','context_village_wall','context_boundary_post'))
        floor = building['eaveElevationCm'] - building['estimatedWallHeightCm']
        eaves = building['eaveElevationCm']
        candidate_edges = []
        for rings in building['polygonsCm']:
            ring = base.canonical(rings[0])
            for a, b in zip(ring, ring[1:]+ring[:1]):
                length = math.dist(a, b)
                if length < 240:
                    continue
                tangent = [(b[k]-a[k])/length for k in (0,1)]
                outward = [tangent[1], -tangent[0]]
                candidate_edges.append((a, length, tangent, outward))
                glass_bottom, glass_top = floor+90, min(floor+225, eaves-42)
                quantity = max(1, math.floor((length-70)/260))
                spacing = (length-120)/quantity
                for i in range(quantity):
                    center = 60+spacing*(i+.5)
                    width = min(rng.uniform(102,133), spacing-55)
                    left, right = center-width/2, center+width/2
                    # Deep dark glazing, light reveal, sill and split sash.
                    box(trim,a,tangent,outward,left-9,right+9,glass_bottom-10,glass_top+10,3.5)
                    box(metal,a,tangent,outward,left,right,glass_bottom,glass_top,5)
                    frame = timber if rng.random() < .23 else metal
                    for x1,x2,z1,z2 in [(left,left+5,glass_bottom,glass_top),(right-5,right,glass_bottom,glass_top),
                                       (left,right,glass_bottom,glass_bottom+5),(left,right,glass_top-5,glass_top),
                                       (center-2.5,center+2.5,glass_bottom,glass_top)]:
                        box(frame,a,tangent,outward,x1,x2,z1,z2,7)
                    box(trim,a,tangent,outward,left-10,right+10,glass_bottom-14,glass_bottom-8,13)
                    counts['windows'] += 1; details['windows'] += 1
                # Facade plinth follows exact sampled ground at edge endpoints.
                def ground(p):
                    samples = building['renderedGroundSamples']
                    return min(samples, key=lambda row:math.dist(row['xyCm'],p))['renderedGroundZCm']
                a2 = [a[k]+outward[k]*8 for k in (0,1)]
                b2 = [b[k]+outward[k]*8 for k in (0,1)]
                tube(metal, [*a2,eaves-3], [*b2,eaves-3], 5.5, 6)
                tube(metal, [*a2,eaves-3], [*a2,ground(a)+20], 4., 6)
                counts['gutterRuns'] += 1; counts['downpipes'] += 1
                details['gutterRuns'] += 1; details['downpipes'] += 1
        if candidate_edges:
            # One restrained entrance per official building, positioned on its
            # longest side. Window positions use bays; a bay is replaced with a
            # timber lower panel for a door only where there is spare wall.
            a,length,tangent,outward = max(candidate_edges, key=lambda e:e[1])
            if length > 650:
                box(timber,a,tangent,outward,35,120,floor+6,floor+214,8)
                box(trim,a,tangent,outward,27,35,floor+6,floor+224,9)
                box(trim,a,tangent,outward,120,128,floor+6,floor+224,9)
                box(trim,a,tangent,outward,27,128,floor+214,floor+224,9)
                counts['entrances'] += 1; details['entrances'] += 1
        if building['sourceAreaM2'] > 70 and rng.random() < .60:
            shape = unary_union([Polygon(rings[0], rings[1:]) for rings in building['polygonsCm']])
            anchor = shape.representative_point()
            if shape.buffer(-40).covers(anchor):
                z,_ = roof_sampler.sample([anchor.x,anchor.y])
                chimney = chunk(cell,'context_village_wall')
                box(chimney,[anchor.x-18,anchor.y-22],[1,0],[0,1],0,36,z-8,z+75,44,solid=True)
                # Cap is a separate low dark horizontal volume.
                box(metal,[anchor.x-22,anchor.y-26],[1,0],[0,1],0,44,z+75,z+83,52,solid=True)
                counts['chimneys'] += 1; details['chimneys'] += 1
        building_audit.append({'sourceId':building['id'],'officialFootprintUnchanged':True,
                               'sourceDistanceMetres':building['sourceDistanceMetres'],'details':dict(details)})

    # Visible pebbles and sparse compacted-earth depressions are confined to
    # the retained gravel lane triangles. Subject access, legal edges and all
    # nearby collision surfaces remain protected.
    road_meshes = [m for m in context['meshes'] if m['material']=='context_track']
    road_sampler = base.GroundSampler({'meshes':road_meshes})
    road_shape = unary_union(road_sampler.shapes).difference(protected.buffer(35))
    road_shape = road_shape.intersection(Point(0,0).buffer(14500)).buffer(-18)
    rng = random.Random(60122620260930)
    road_audit = []
    minx,miny,maxx,maxy = road_shape.bounds
    for _ in range(35000):
        xy = [rng.uniform(minx,maxx),rng.uniform(miny,maxy)]
        radius = rng.uniform(3.,9.)
        footprint = Point(xy).buffer(radius,quad_segs=2)
        if not road_shape.covers(footprint):
            continue
        z,_ = road_sampler.sample(xy)
        cell = [math.floor(p/10000) for p in xy]
        pebble = chunk(cell, 'context_track')
        apex = [*xy,z+rng.uniform(.7,2.2)]
        ring = list(footprint.exterior.coords)[:-1]
        for a,b in zip(ring,ring[1:]+ring[:1]):
            pebble.triangle([*a,z+.12],[*b,z+.12],apex,[0,0,1])
        road_audit.append({'xyCm':xy,'radiusCm':radius,'groundZCm':z})
        if len(road_audit) >= 1250:
            break
    counts['lanePebbles'] = len(road_audit)
    # A fallow subdivision reads as mixed soil and vegetation rather than an
    # emerald lawn. Broken earth islands and paired worn tracks are illustrative
    # ground finishes clipped to the exact rendered cadastral-domain triangles.
    ground_meshes = {m['id']:m for m in context['meshes'] if m['material'] in
                     ('context_crop','context_arable','context_meadow','context_fallow')}
    ground_sampler = base.GroundSampler({'meshes':list(ground_meshes.values())})
    ground_regions = {}
    for surface in context['surfaces']:
        if surface['meshId'] not in ground_meshes or surface['finish']=='shoulder':
            continue
        mesh = ground_meshes[surface['meshId']]
        shape = unary_union([Polygon([mesh['verticesCm'][j][:2]for j in mesh['indices'][i:i+3]])
                             for i in range(0,len(mesh['indices']),3)]).difference(protected.buffer(45))
        if shape.area > 20000:
            key = surface['parcelNumber']
            if key in ground_regions:
                ground_regions[key]['shape'] = ground_regions[key]['shape'].union(shape)
            else:
                ground_regions[key] = {'shape':shape,'material':surface['material']}
    ground_parts, ground_audit = [], []
    for number,region in sorted(ground_regions.items()):
        shape = region['shape']; kind = region['material']
        rng = random.Random(int(hashlib.sha256(('ground-'+number).encode()).hexdigest()[:14],16))
        minx,miny,maxx,maxy = shape.bounds
        parts = []
        if number.startswith(('6012/','6035/')) and number != '6012/26':
            # Ground-condition variation never fabricates a built neighbor.
            amount = min(9,max(3,math.ceil(shape.area/1800000)))
            for _ in range(amount*18):
                center = [rng.uniform(minx,maxx),rng.uniform(miny,maxy)]
                if not shape.buffer(-90).covers(Point(center)):
                    continue
                radius = min(rng.uniform(210,430), math.sqrt(shape.area)*.15)
                angle = rng.uniform(0,math.pi)
                ring = []
                for j in range(24):
                    a = 2*math.pi*j/24
                    r = radius*(.83+.14*math.sin(3*a+angle)+.09*math.sin(7*a-angle))
                    ring.append([center[0]+r*math.cos(a)*1.18,center[1]+r*math.sin(a)*.76])
                patch = Polygon(ring).intersection(shape.buffer(-35))
                if patch.area > 18000:
                    parts.append(patch)
                if len(parts)>=amount:
                    break
            # A pair of low, uneven tractor/mower lanes crosses a bounded
            # part of the vacant plot, with scattered gaps and no legal-edge
            # paving expansion. Wheel strips are subtle 28cm earth exposures.
            rectangle = list(shape.minimum_rotated_rectangle.exterior.coords)[:-1]
            a,b = max(zip(rectangle,rectangle[1:]+rectangle[:1]),key=lambda p:math.dist(*p))
            length = math.dist(a,b);tangent=[(b[k]-a[k])/length for k in (0,1)]
            normal=[-tangent[1],tangent[0]];middle=shape.representative_point()
            for offset in (-72,72):
                for segment in range(3):
                    start = -length*.36+segment*length*.23
                    finish = start+length*.19
                    line = [[middle.x+tangent[0]*s+normal[0]*(offset+8*math.sin(s*.009)),
                             middle.y+tangent[1]*s+normal[1]*(offset+8*math.sin(s*.009))]
                            for s in [start+(finish-start)*i/6 for i in range(7)]]
                    parts.extend(shapes(LineString(line).buffer(14,cap_style='round').intersection(shape.buffer(-60))))
            landuse = 'ILLUSTRATIVE_MIXED_FALLOW_AND_WORN_ACCESS_UNBUILT'
        elif kind in ('context_crop','context_arable') and shape.area > 3000000:
            rectangle = list(shape.minimum_rotated_rectangle.exterior.coords)[:-1]
            a,b = max(zip(rectangle,rectangle[1:]+rectangle[:1]),key=lambda p:math.dist(*p))
            length = math.dist(a,b);tangent=[(b[k]-a[k])/length for k in (0,1)]
            normal=[-tangent[1],tangent[0]];middle=shape.representative_point()
            width = math.hypot(maxx-minx,maxy-miny)
            spacing = 155 if kind=='context_arable' else 240
            # Soil between broad late-season rows is a restrained fraction of
            # the field; all bounds and the existing vineyard remain intact.
            halfwidth = 28 if kind=='context_arable' else 18
            for offset in range(-math.ceil(width),math.ceil(width),spacing):
                ends=[[middle.x+tangent[0]*s+normal[0]*offset,middle.y+tangent[1]*s+normal[1]*offset]
                      for s in (-width,width)]
                parts.extend(shapes(LineString(ends).buffer(halfwidth,cap_style='flat').intersection(shape.buffer(-35))))
            landuse = 'ILLUSTRATIVE_LATE_SEASON_CULTIVATED_ROWS'
        else:
            continue
        if not parts:
            continue
        combined=unary_union(parts)
        require(combined.difference(shape).area<.01,'Ground patch leaves exact parcel domain')
        record={'parcelNumber':number,'surfaceMaterial':kind,'authoredLandUse':landuse,
                'legalDomainAreaM2':shape.area/10000,'soilFinishAreaM2':combined.area/10000,
                'soilFraction':combined.area/shape.area,'groundMatched':True,'legalBoundaryUnchanged':True}
        ground_audit.append(record)
        ground_parts.extend(shapes(combined))
    # Each exact soil footprint is split into an opaque interior and a narrow
    # feather ring. UV0.U is a geometric alpha witness, not texture UV: the
    # material samples its scanned PBR maps independently in world space.
    # Earcut preserves the annulus hole so inner/ring faces never overlap.
    feather_pieces,feather_audit = [],[]
    for part in ground_parts:
        width_estimate = 2*part.area/part.length
        feather = min(60.,width_estimate*.20)
        inner = part.buffer(-feather)
        for _ in range(8):
            if not inner.is_empty:
                break
            feather *= .5;inner=part.buffer(-feather)
        require(not inner.is_empty and feather>0,'Soil exposure has no opaque interior')
        ring=part.difference(inner)
        require(inner.intersection(ring).area<.001 and abs(inner.union(ring).area-part.area)<.01,
                'Soil feather split overlaps or changes original footprint')
        feather_audit.append({'outerAreaM2':part.area/10000,'innerAreaM2':inner.area/10000,
                              'featherWidthCm':feather,'partitionAreaErrorCm2':abs(inner.union(ring).area-part.area)})
        feather_pieces.extend((piece,part,feather,False)for piece in shapes(inner))
        feather_pieces.extend((piece,part,feather,True)for piece in shapes(ring))
    polygon_data = [[[list(p)for p in piece.exterior.coords[:-1]]]+
                    [[list(p)for p in hole.coords[:-1]]for hole in piece.interiors]
                    for piece,_,_,_ in feather_pieces]
    alpha_samples=[]
    for (piece,outer,feather,is_ring),data in zip(feather_pieces,base.triangulate(polygon_data)):
        middle=piece.representative_point();cell=[math.floor(v/10000)for v in (middle.x,middle.y)]
        mesh=chunk(cell,'context_soil_exposure');mesh.record['maxDrawDistanceCm']=26000
        for i in range(0,len(data['indices']),3):
            vertices=[]
            for j in data['indices'][i:i+3]:
                xy=data['points'][j];z,_=ground_sampler.sample(xy)
                vertices.append([*xy,z+.30])
            first=len(mesh.record['verticesCm'])
            mesh.triangle(*vertices,[0,0,1])
            for index in range(first,len(mesh.record['verticesCm'])):
                alpha=min(1.,max(0.,Point(mesh.record['verticesCm'][index][:2]).distance(outer.boundary)/feather)) if is_ring else 1.
                if alpha<1e-6:alpha=0.
                if alpha>1-1e-6:alpha=1.
                mesh.record['uvs'][index]=[alpha,0.]
                alpha_samples.append(alpha)
    require(alpha_samples and min(alpha_samples)==0 and max(alpha_samples)==1,'Missing geometric feather alpha endpoints')
    # Precompute removals against the exact frozen placement lists. The native
    # importer can apply these indices in linear time without a GIS dependency.
    removed={};exposure=unary_union(ground_parts)
    for name in ('meadowBladePlacements','meadowUnderstoryPlacements','groundCoverPlacements'):
        if name in context:
            points=shapely.points([p['positionCm'][:2]for p in context[name]])
            distances=shapely.distance(exposure,points)
            # Full conservative tuft circles, with one extra centimetre for
            # numerical margin. This fixes the previous centre-only35cm tuft
            # exclusion while keeping all trees and authored main garden.
            mask=[distance<=float(row['radiusCm'])+1. for distance,row in zip(distances,context[name])]
            removed[name]=[i for i,inside in enumerate(mask)if inside]
    counts['groundDetailParcels']=len(ground_audit)
    counts['groundDetailPatches']=len(ground_parts)
    counts['clearedGroundPlantInstances']=sum(map(len,removed.values()))
    meshes = [mesh.record for mesh in chunks.values() if mesh.record['indices']]
    require(meshes and counts['windows'] > 500 and counts['lanePebbles'] > 250, 'Neighborhood detail unexpectedly missing')
    require(len({m['id'] for m in meshes})==len(meshes), 'Duplicate neighborhood mesh')
    require(not set(m['id'] for m in meshes)&set(m['id']for m in context['meshes']+village['meshes']), 'Mesh identity conflict')
    require(all(len(m['indices'])//3 < 40000 for m in meshes), 'Neighborhood mesh chunk exceeds budget')
    for mesh in meshes:
        require(all(math.isfinite(v) for p in mesh['verticesCm']for v in p), 'Nonfinite detail vertex')
        require(all(0<=i<len(mesh['verticesCm'])for i in mesh['indices']), 'Detail index out of range')
        require(len(mesh['uvs'])==len(mesh['verticesCm']), 'Detail UV count differs')
    # Full new vertex envelopes are outside the house/access protected union;
    # detail on surveyed distant village footprints never touches the plot.
    conflicts = sum(protected.covers(Point(p[:2])) for m in meshes for p in m['verticesCm'])
    require(conflicts == 0, 'Neighborhood detail overlaps protected house/access geometry')
    paths = [Path(__file__).resolve(),ROOT/'scripts/unreal/exterior-buildings.py',context_path,buildings_path,scene_path]
    return {'schemaVersion':1,'owner':OWNER,'status':'authored-neighborhood-native-pending','units':'centimetres',
            'activeDesign':scene['activeDesign'],'housePlacement':context['housePlacement'],
            'sourceSceneSha256':context['sourceSceneSha256'],'sourceObjSha256':context['sourceObjSha256'],
            'generatorSha256':sha(Path(__file__)),'inputFiles':{str(p):sha(p)for p in paths},
            'sourceEvidence':{'officialBuildings':village['sourceEvidence'],'legalParcels':context['sourceEvidence'],
                              'detailEvidence':'AUTHOR_ESTIMATED_FACADE_AND_LANE_FINISH_NOT_SITE_SURVEY'},
            'meshes':meshes,'groups':[],'buildings':building_audit,'lanePebblePlacements':road_audit,
            'groundDetails':ground_audit,'groundDetailRemovedPlacementIndices':removed,
            'groundDetailPlacementSourceCounts':{name:len(context[name])for name in removed},
            'groundDetailFeatheringPolicy':{'material':'context_soil_exposure','alphaChannel':'UV0.U',
                 'pbrSampling':'WORLD_SPACE_INDEPENDENT_OF_UV0','outerAlpha':0,'innerAlpha':1,
                 'broadPatchMaximumFeatherCm':60,'stripFeatherFractionOfWidth':.20,
                 'allPartitionsNonOverlapping':True,'partitions':feather_audit,
                 'vertexAlphaRange':[min(alpha_samples),max(alpha_samples)],
                 'tuftExclusion':'distance(root,full exposure)<=radiusCm+1; entire conservative crown'},
            'summary':{'detailedOfficialBuildings':len(building_audit),'meshCount':len(meshes),
                       'triangles':sum(len(m['indices'])//3 for m in meshes),**dict(counts)},
            'audit':{'status':'PASS','protectedVertexConflicts':conflicts,'officialFootprintsUnchanged':True,
                     'developmentParcelsUnbuilt':True,'laneDetailWithinRetainedRoadTriangles':True,
                     'allNewVisualsNoCollision':True,'sourceGeometryNeverModified':True},
            'limits':['Window/door counts, materials, gutters and chimney shapes are illustrative estimates, not observations or building surveys.',
                      'Official building XY footprint accuracy is inherited; no centimetre measurement accuracy is claimed.',
                      'Empty development parcels retain their actual land and have no invented housing or infrastructure.',
                      'Gravel detail is an authored finish on retained lane triangles; all original access and collision stay unchanged.',
                      'Native material appearance, shadows and performance require separate packaged Unreal verification.']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('context','buildings','scene','output'):
        parser.add_argument('--'+name, type=Path,required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    require(output.is_relative_to(ROOT/'output/unreal'),'Neighborhood output must be isolated')
    target = output/'neighborhood-details.json'
    require(not target.exists(),'Neighborhood plan is immutable; use a new output')
    plan = build(args.context.resolve(),args.buildings.resolve(),args.scene.resolve())
    output.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as stream:stream.write(encode(plan))
    with (output/'summary.json').open('xb') as stream:stream.write(encode({'plan':str(target),'sha256':sha(target),**plan['summary'],'audit':plan['audit']}))
    environment = {'pythonExecutable':sys.executable,'pythonVersion':sys.version,'shapelyVersion':shapely.__version__,
                   'generatorSha256':plan['generatorSha256'],'planSha256':sha(target)}
    with (output/'build-environment.json').open('xb')as stream:stream.write(encode(environment))
    print(json.dumps({'plan':str(target),'sha256':sha(target),**plan['summary'],'audit':plan['audit']}))


if __name__=='__main__':main()
