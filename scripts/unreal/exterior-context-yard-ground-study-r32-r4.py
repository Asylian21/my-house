"""One bounded source R32 yard-ground proposal; no Unreal/native mutation.

Diagnoses the actual R28 edge geometry, retains its exact entrance/court/bed
footprints and shrubs, and proposes resolved feather topology, clipped PBR
substrate and low mixed growth. The previews are source diagrams, not renders.
"""
import importlib.util
import json
import math
from pathlib import Path
import random
import shutil
import struct
import sys

sys.dont_write_bytecode = True
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from shapely import constrained_delaunay_triangles
from shapely.geometry import Point, Polygon, box, mapping, shape
from shapely.ops import unary_union

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-yard-ground-study-r32-r4.py'
OUTPUT = ROOT/'output/unreal/exterior-context-yard-ground-20261002-r32-study-r4'
SOURCE = ROOT/'output/unreal/exterior-context-yard-20261002-r28-study'
GEOMETRY = ROOT/'output/unreal/exterior-context-yard-20261002-r28-geometry-study'
BASE = ROOT/'output/unreal/exterior-20261002-r28b'
PNG = ROOT/'output/unreal/exterior-validation-20260930-r1/qa/editor-pilot-r28b-purposeful-yards-r16-1790911889414-cjzjUw/neighbor-finish-close-r18-WJXgsl/userdir/Saved/Diagnostics/neighbor-finish-close-r18-day-20261002T033205-scene.png'
MODELS = ('grass_medium_02_a', 'grass_bermuda_clump_a', 'celandine_01_e')
EXPECTED_BASE_SHA = 'dfbca65515fc08aea52515195ab5ef752fe07cdca622cd41964e99875ced2456'
EXPECTED_PNG_SHA = '128506618c1c075891d817e8bb3e142aaf00288c5cd7a580d6afaa3d9d234dc3'

def module(name, file):
    spec = importlib.util.spec_from_file_location(name, file)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

p = module('r32_original_r28_pure_source', ROOT/'scripts/unreal/exterior-context-yard-study-r28.py')
q = module('r32_r3_exact_generated_quantization', ROOT/'scripts/unreal/exterior-context-yard-ground-quantization-r32-r4.py')
require, read, sha, pin, digest, write, polygons = p.require, p.read, p.sha, p.pin, p.digest, p.write, p.polygons
f32 = lambda value: struct.unpack('<f', struct.pack('<f', value))[0]

def smooth(value):
    value = min(1., max(0., value))
    return value*value*(3.-2.*value)

def coverage_statistics(mesh, first=0, count=None):
    count = len(mesh['indices'])//3 if count is None else count
    total = zero = weighted = 0.
    zero_count = 0
    for offset in range(first*3, (first+count)*3, 3):
        ids = mesh['indices'][offset:offset+3]
        a, b, c = [mesh['verticesCm'][i] for i in ids]
        area = abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))/2.
        values = [mesh['uv1'][i][0] for i in ids]
        total += area
        weighted += area*sum(values)/3.
        if max(values) <= 1e-10:
            zero += area
            zero_count += 1
    return {'triangles': count, 'sourceAreaM2': total/10000.,
            'allZeroCoverageTriangles': zero_count,
            'allZeroCoverageAreaPercent': 100.*zero/total,
            'areaWeightedMeanLinearCoverage': weighted/total,
            'model': 'Triangle-interpolated UV1.x mean coverage, not native dither pixels or accepted appearance'}

def conforming_triangles(domain, feather_cm, accounting, cell_cm=40):
    """Resolve narrow feather with 2cm rings; coarse cells only along/core.

    Every nonempty layer includes both of its offset boundaries. A triangle
    cannot jump from outer zero coverage directly to an isolated grid corner.
    """
    previous = domain
    levels = list(np.arange(2., feather_cm, 2.)) + [feather_cm] if feather_cm else []
    layers = []
    for distance in levels:
        inner = domain.buffer(-float(distance), quad_segs=16)
        layers.append(previous.difference(inner))
        previous = inner
    layers.append(previous)
    for layer in layers:
        if layer.is_empty:
            continue
        x0, y0, x1, y1 = layer.bounds
        for x in range(math.floor(x0/cell_cm)*cell_cm, math.ceil(x1/cell_cm)*cell_cm, cell_cm):
            for y in range(math.floor(y0/cell_cm)*cell_cm, math.ceil(y1/cell_cm)*cell_cm, cell_cm):
                for poly in polygons(layer.intersection(box(x,y,x+cell_cm,y+cell_cm))):
                    retess,proof=q.quantized_cell_triangles(poly)
                    accounting.append({'sourceCellCm':[x,y,x+cell_cm,y+cell_cm],
                      'sourceDomainCm':mapping(poly),**proof})
                    yield from retess

def mesh(domain, identity, feather, ground, soil_fraction=None, sample_ground=True, hard_max_relief=None):
    vertices, uv0, uv1, indices, witnesses, lookup = [], [], [], [], {}, {}
    triangles = [];cells=[]
    for triangle in conforming_triangles(domain, feather,cells):
        face = []
        for xy in triangle:
            xy = tuple(float(v) for v in xy)
            if xy not in lookup:
                boundary = Point(xy).distance(domain.boundary)
                coverage = smooth(boundary/feather) if feather else 1.
                # Relief is authored, not a survey. The substrate stays below
                # the original R28 hard-core surface; the latter is retained.
                contact = ground.sample(xy) if sample_ground else {'zCm':0., 'diagnosticOnly':True}
                if hard_max_relief is None:
                    relief = .005 + .008*coverage
                else:
                    # Exact original R28 hard-ground source formula, evaluated
                    # at newly inserted points. It stays above the underlay.
                    noise=.5+.5*math.sin(xy[0]/37+math.sin(xy[1]/53)*.4)*math.cos(xy[1]/61)
                    relief=.02+(hard_max_relief-.02)*(.25+.75*noise)
                i = len(vertices)
                vertices.append([xy[0],xy[1],contact['zCm']+relief])
                uv0.append([xy[0]/100.,xy[1]/100.])
                uv1.append([coverage, soil_fraction(xy) if soil_fraction else 0.])
                witnesses[str(i)] = {'sourceGround':contact,'artistAddedReliefCm':relief}
                lookup[xy] = i
            face.append(lookup[xy])
        indices.extend(face)
        triangles.append(Polygon(triangle))
    union = unary_union(triangles)
    original_union=unary_union([shape(row['sourceDomainCm'])for row in cells])
    require(original_union.symmetric_difference(domain).area < .001, 'R32 original cell partition lost its authored polygon')
    result=q.compact_exact_zero_faces({'id':identity,'verticesCm':vertices,'uv0':uv0,'uv1':uv1,'indices':indices,
      'domainCm':mapping(domain),'sourceGroundVertexWitnesses':witnesses})
    # Compaction has an explicit source-ID witness; recompute normals solely
    # from every retained positive-area face, without unreferenced vertices.
    normals = np.zeros((len(result['verticesCm']),3))
    vs = np.asarray(result['verticesCm'])
    for ids in np.asarray(result['indices']).reshape(-1,3):
        a,b,c = vs[ids]
        normal = np.cross(c-a,b-a)
        require(normal[2] > 0., 'R32 source native face inverted')
        normals[ids] += normal
    normals /= np.linalg.norm(normals,axis=1)[:,None]
    require(np.isfinite(normals).all(), 'Invalid source ground normals')
    return {**result,'normals':normals.tolist(),
            'quantizedPlanarPartition':{'cells':cells,'wholeOriginalAuthoredCellPartitionConserved':True,
                'authoredToProposedNativeF32FloorSymmetricDifferenceAreaCm2':union.symmetric_difference(domain).area,
                'proposedNativeF32FloorAreaCm2':union.area,'quantizedFloorDomainCm':mapping(union),
                'allCoincidentFloorCoordinatesShareSingleHeightEvaluation':True,
                'positiveAreaQuantizedRegionsDiscarded':False,'approximateAreaThresholdUsed':False},
            'sourceAreaM2':domain.area/10000.,'sourceWinding':'clockwise',
            'featherCm':feather,'sourceOnly':True,'nativeApplied':False,
            'nativeNormalTangentReadbackAvailable':False}

def source_model_points(model):
    """Decode every POSITION in all3 existing normalized source GLB LODs."""
    data = Path(model['glbPath']).read_bytes()
    require(sha(model['glbPath']) == model['glbSha256'], 'Existing licensed plant source changed')
    require(struct.unpack_from('<III',data) == (0x46546c67,2,len(data)), 'Invalid plant GLB')
    length, kind = struct.unpack_from('<II',data,12)
    require(kind == 0x4e4f534a, 'Plant JSON chunk missing')
    doc = json.loads(data[20:20+length]); blob=data[28+length:]
    result = []
    for lod in model['lods']:
        node = next(n for n in doc['nodes'] if n.get('name') == lod['nodeName'])
        require(not any(k in node for k in ('matrix','translation','rotation','scale')), 'Unaccounted plant node transform')
        points = []
        for primitive in doc['meshes'][node['mesh']]['primitives']:
            accessor = doc['accessors'][primitive['attributes']['POSITION']]
            view = doc['bufferViews'][accessor['bufferView']]
            require(accessor['componentType'] == 5126 and accessor['type'] == 'VEC3', 'Unexpected plant POSITION layout')
            offset=view.get('byteOffset',0)+accessor.get('byteOffset',0);stride=view.get('byteStride',12)
            for i in range(accessor['count']):
                x,z,y = struct.unpack_from('<fff',blob,offset+i*stride)
                points.append([x*100.,y*100.,z*100.])
        require(points, 'Empty actual all-LOD source positions')
        result.append(points)
    return result

def choose_plants(yard_rows, planting_domains, ground, models, native):
    """Clipped mixed patches, kept away from access and existing shrub crowns."""
    roots = []
    by_model = {key:source_model_points(models[key]) for key in MODELS}
    bounds = {key:{'radius':max(math.hypot(x,y) for lod in rows for x,y,z in lod),
                       'minZ':min(z for lod in rows for x,y,z in lod)} for key,rows in by_model.items()}
    observed = {row['id']:row for row in native['savedPlantReadback']}
    for yard in yard_rows:
        identity=yard['buildingSourceId'];domain=planting_domains[identity]
        x0,y0,x1,y1=domain.bounds; rng=random.Random(320000+int(identity.split('.')[1]))
        candidates=[]
        for x in np.arange(x0+10,x1,22):
            for y in np.arange(y0+10,y1,22):
                xy=[float(x+rng.uniform(-7,7)),float(y+rng.uniform(-7,7))]
                if not domain.contains(Point(xy)):
                    continue
                field=.5+.5*math.sin(xy[0]/84.+math.cos(xy[1]/119.))*math.sin(xy[1]/96.)
                # Deliberate uneven patches leave the actual approach clear.
                if rng.random() > .42+.53*field:
                    continue
                pick=rng.random();key=MODELS[0] if pick<.68 else MODELS[1] if pick<.88 else MODELS[2]
                height=rng.uniform(*( (9.,15.) if key==MODELS[0] else (6.,10.) if key==MODELS[1] else (4.5,7.) ))
                scale=height/models[key]['heightCm'];radius=bounds[key]['radius']*scale
                crown=Point(xy).buffer(radius/math.cos(math.pi/128),quad_segs=32)
                if not domain.covers(crown):
                    continue
                yaw=rng.uniform(-180.,180.);co,si=math.cos(math.radians(yaw)),math.sin(math.radians(yaw))
                # Full decoded source vertices, no near-only or bbox shortcut.
                require(all(domain.covers(Point(xy[0]+scale*(co*x-si*y),xy[1]+scale*(si*x+co*y)))
                            for lod in by_model[key] for x,y,z in lod), 'Plant all-LOD vertex left the allowed source footprint')
                contact=ground.sample(xy)
                row={'id':'yard_ground_r32_plant_'+str(len(roots)+len(candidates)), 'buildingSourceId':identity,
                     'modelId':key,'positionCm':xy+[contact['zCm']-bounds[key]['minZ']*scale+.03],
                     'yawDegrees':yaw,'uniformScale':scale,'heightCm':height,'allLodSourceRadialEnvelopeCm':radius,
                     'sourceGround':contact,'sourceAllLodVerticesChecked':sum(map(len,by_model[key])),
                     'sourceAllLodContainingCircleInsidePlantingDomain':True,
                     'nativeMesh':observed[key]['mesh'],'nativeMaterials':observed[key]['materials'],
                     'nativeLodTriangles':observed[key]['lodTriangles'],'nativeRootFrameMeasured':False,
                     'nativeApplied':False}
                candidates.append(row)
        # Bound this one authored pilot, not a scene-wide density or performance gate.
        candidates=candidates[:682]
        for row in candidates:row['id']='yard_ground_r32_plant_'+str(len(roots));roots.append(row)
    return roots, {key:{'sourceAllLodVertexCounts':[len(lod) for lod in by_model[key]],
                        'sourceAllLodRadialEnvelopeCm':bounds[key]['radius'],
                        'nativeAsset':observed[key]['mesh'],'nativeMaterials':observed[key]['materials'],
                        'existingSource':pin(models[key]['glbPath'])} for key in MODELS}

def write_glb(file, meshes):
    binary=bytearray();accessors=[];views=[];entries=[];nodes=[]
    def accessor(values,width,component=5126,target=34962):
        if component==5126:values=[[f32(v)for v in row]for row in values]
        flat=[v for row in values for v in (row if isinstance(row,list) else [row])]
        binary.extend(b'\0'*((-len(binary))%4));start=len(binary)
        binary.extend(struct.pack('<'+('f' if component==5126 else 'I')*len(flat),*flat))
        views.append({'buffer':0,'byteOffset':start,'byteLength':len(binary)-start,'target':target})
        a={'bufferView':len(views)-1,'componentType':component,'count':len(values),'type':{1:'SCALAR',2:'VEC2',3:'VEC3'}[width]}
        if width==3:a.update(min=[min(row[k] for row in values) for k in range(3)],max=[max(row[k] for row in values) for k in range(3)])
        accessors.append(a);return len(accessors)-1
    for row in meshes:
        attrs={'POSITION':accessor([[x/100,z/100,y/100] for x,y,z in row['verticesCm']],3),
               'NORMAL':accessor([[x,z,y] for x,y,z in row['normals']],3),
               'TEXCOORD_0':accessor(row['uv0'],2),'TEXCOORD_1':accessor(row['uv1'],2)}
        entries.append({'name':row['id']+'_LOD0','primitives':[{'attributes':attrs,'indices':accessor(row['indices'],1,5125,34963),'mode':4}]})
        nodes.append({'name':row['id']+'_LOD0','mesh':len(entries)-1})
    doc={'asset':{'version':'2.0','generator':OWNER},'scene':0,'scenes':[{'nodes':list(range(len(nodes)))}],
         'nodes':nodes,'meshes':entries,'accessors':accessors,'bufferViews':views,'buffers':[{'byteLength':len(binary)}]}
    js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*((-len(js))%4);binary+=b'\0'*((-len(binary))%4)
    file.write_bytes(struct.pack('<III',0x46546c67,2,28+len(js)+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary)

def validate_source_glb(file,meshes):
    data=file.read_bytes();require(struct.unpack_from('<III',data)==(0x46546c67,2,len(data)),'Written source GLB framing differs')
    length,kind=struct.unpack_from('<II',data,12);require(kind==0x4e4f534a,'Written GLB JSON chunk differs')
    doc=json.loads(data[20:20+length]);binary_length,binary_kind=struct.unpack_from('<II',data,20+length)
    require(binary_kind==0x004e4942 and binary_length==len(data)-(28+length),'Written source GLB binary chunk differs')
    blob=data[28+length:];rows=[]
    def values(number,width,code):
        a=doc['accessors'][number];v=doc['bufferViews'][a['bufferView']]
        require(a['componentType']==(5126 if code=='f' else 5125),'GLB attribute component changed')
        offset=v.get('byteOffset',0)+a.get('byteOffset',0);size=struct.calcsize('<'+code*width)
        require(offset+a['count']*size<=len(blob),'GLB attribute escapes binary payload')
        return [list(struct.unpack_from('<'+code*width,blob,offset+i*size))for i in range(a['count'])]
    require(len(doc['meshes'])==len(meshes)==3,'Exactly three source masters required')
    for i,source in enumerate(meshes):
        entry=doc['meshes'][i];primitive=entry['primitives'][0];attrs=primitive['attributes']
        require(entry['name']==source['id']+'_LOD0' and primitive['mode']==4,'Written source mesh identity/mode changed')
        expected={'POSITION':[[f32(x/100),f32(z/100),f32(y/100)]for x,y,z in source['verticesCm']],
            'NORMAL':[[f32(x),f32(z),f32(y)]for x,y,z in source['normals']],
            'TEXCOORD_0':[[f32(v)for v in row]for row in source['uv0']],
            'TEXCOORD_1':[[f32(v)for v in row]for row in source['uv1']]}
        require(set(attrs)==set(expected),'Written attributes changed or fabricated tangent present')
        decoded={key:values(attrs[key],3 if key in('POSITION','NORMAL') else 2,'f')for key in expected}
        require(decoded==expected,'Written source attributes differ from exact F32 producer values')
        ids=[row[0]for row in values(primitive['indices'],1,'I')]
        require(ids==source['indices'],'Written full source indices changed')
        require(all(math.isfinite(v)for rows2 in decoded.values()for row in rows2 for v in row),'Nonfinite source GLB values')
        require(all(0. <= v <= 1. for row in decoded['TEXCOORD_1']for v in row),'Source coverage/layer mask outside normalized range')
        normal_error=max(abs(math.sqrt(sum(v*v for v in row))-1.)for row in decoded['NORMAL'])
        require(normal_error<=3.*2.**-23,'Written source normal exceeds three-component F32 unit precision')
        a=doc['accessors'][attrs['POSITION']]
        require(a['min']==[min(p[k]for p in decoded['POSITION'])for k in range(3)]
            and a['max']==[max(p[k]for p in decoded['POSITION'])for k in range(3)],'GLB declared bounds are not exact decoded source positions')
        native=[[f32(x*100),f32(y*100),f32(z*100)]for x,z,y in decoded['POSITION']]
        require(native==decoded_native_proposal(source['verticesCm']),'GLB proposed native basis changed')
        require(all(q.cross(*[native[j]for j in ids[offset:offset+3]])[2]<0.
            for offset in range(0,len(ids),3)),'Retained full F32 source face winding/area changed')
        rows.append({'id':source['id'],'vertices':len(native),'triangles':len(ids)//3,
            'fullPositionNormalUv0Uv1IndexArraysExactlySourceF32':True,'allDecodedFacesPositiveFootprintAndClockwise':True,
            'maximumSourceF32NormalUnitLengthError':normal_error,'sourceF32NormalErrorBound':3.*2.**-23,
            'declaredBoundsExactlyDecodedPositions':True,'tangentAttributePresent':False,
            'nativeNormalTangentReadbackAvailable':False,'nativeExecuted':False})
    return {'scope':'Complete written source GLB decoding and proposed generated native F32 basis only',
        'meshes':rows,'nativeExecuted':False,'nativeAppearanceAccepted':False}

def combine_meshes(rows, role):
    result={'id':'yard_ground_r32_'+role,'role':role,'verticesCm':[],'normals':[],'uv0':[],'uv1':[],'indices':[],
            'sourceGroundVertexWitnesses':{},'sourceSurfaceRanges':[],'sourceOnly':True,'nativeApplied':False,
            'nativeNormalTangentReadbackAvailable':False,'sourceWinding':'clockwise'}
    domains=[]
    for row in rows:
        offset=len(result['verticesCm']);first=len(result['indices'])//3
        for key in ('verticesCm','normals','uv0','uv1'):result[key].extend(row[key])
        result['indices'].extend(i+offset for i in row['indices'])
        result['sourceGroundVertexWitnesses'].update({str(int(i)+offset):value for i,value in row['sourceGroundVertexWitnesses'].items()})
        result['sourceSurfaceRanges'].append({'sourcePieceId':row['id'],'firstTriangle':first,'triangles':len(row['indices'])//3,
            'domainCm':row['domainCm'],'materialProposal':row['materialProposal'],
            'quantizedTopologyAccounting':row['quantizedTopologyAccounting'],
            'quantizedPlanarPartition':row['quantizedPlanarPartition']})
        domains.append(shape(row['domainCm']))
    result['domainCm']=mapping(unary_union(domains));result['sourceAreaM2']=sum(g.area for g in domains)/10000.
    return result

def decoded_native_proposal(points):
    return [[f32(f32(v/100.)*100.)for v in row]for row in points]

def source_overlap_depth_proof(meshes):
    """Check every hard/underlay triangle overlap extremum after F32 route.

    Both height fields are linear per actual proposed triangle. Their
    difference has its extrema at all vertices of the clipped intersection.
    This is source geometry evidence, not a saved native depth observation.
    """
    from shapely.strtree import STRtree
    soft=next(row for row in meshes if row['role']=='yard_substrate')
    points=decoded_native_proposal(soft['verticesCm']);soft_tri=[];polys=[]
    for i in range(0,len(soft['indices']),3):
        values=[points[j]for j in soft['indices'][i:i+3]];polygon=Polygon([p[:2]for p in values])
        require(polygon.area>0.,'Decoded source underlay triangle became degenerate')
        soft_tri.append(values);polys.append(polygon)
    index=STRtree(polys);minimum=math.inf;maximum=-math.inf;overlaps=vertices_checked=0
    def height(values,xy):
        a,b,c=values;den=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        require(den!=0.,'Decoded source depth triangle is degenerate')
        u=((b[0]-xy[0])*(c[1]-xy[1])-(b[1]-xy[1])*(c[0]-xy[0]))/den
        v=((c[0]-xy[0])*(a[1]-xy[1])-(c[1]-xy[1])*(a[0]-xy[0]))/den
        return u*a[2]+v*b[2]+(1.-u-v)*c[2]
    for row in meshes:
        if row['role'] not in ('entry_walk','service_court'):continue
        hard=decoded_native_proposal(row['verticesCm'])
        for i in range(0,len(row['indices']),3):
            values=[hard[j]for j in row['indices'][i:i+3]];polygon=Polygon([p[:2]for p in values])
            require(polygon.area>0.,'Decoded source hard triangle became degenerate')
            for j in index.query(polygon):
                overlap=polygon.intersection(polys[int(j)])
                if overlap.area==0.:continue
                overlaps+=1
                for clipped in polygons(overlap):
                    for xy in list(clipped.exterior.coords)[:-1]:
                        gap=height(values,xy)-height(soft_tri[int(j)],xy);vertices_checked+=1
                        minimum=min(minimum,gap);maximum=max(maximum,gap)
                        require(gap>0.,'Source hard surface is coplanar with/below its underlay')
    require(overlaps>0 and vertices_checked>0,'Source underlay overlap was not measured')
    return {'scope':'Complete source proposed F32 native-route triangle intersections, not saved native pixels',
            'triangleOverlaps':overlaps,'intersectionVerticesChecked':vertices_checked,
            'minimumHardAboveUnderlayCm':minimum,'maximumHardAboveUnderlayCm':maximum,
            'allHardAboveUnderlayAfterProposedNativeF32Route':True,'nativeExecuted':False}

def draw_alpha_comparison(file, old, resolved):
    """Interpolate actual source UV1 at pixels, independent of UE/lighting."""
    width,height=1600,1210
    image=Image.new('RGB',(width,height),(239,240,232));draw=ImageDraw.Draw(image)
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',20)
    title=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',25)
    draw.text((32,20),'R32 SOURCE UV1 COVERAGE / NOT A NATIVE RENDER',font=title,fill=(30,40,32))
    draw.text((32,59),'Same exact 32 cm worn polygons: old 40 cm sampling versus boundary-conforming 2 cm rings.',font=font,fill=(40,55,40))
    for row_index, (source,new) in enumerate(zip(old,resolved)):
        bounds=shape(source['domainCm']).bounds;scale=min(700/(bounds[2]-bounds[0]),290/(bounds[3]-bounds[1]))
        for column,m in enumerate((source,new)):
            left=40+column*800;top=145+row_index*350
            canvas=np.zeros((280,720),dtype=np.float32)
            for offset in range(0,len(m['indices']),3):
                ids=m['indices'][offset:offset+3]
                pts=np.array([[(m['verticesCm'][i][0]-bounds[0])*scale,(bounds[3]-m['verticesCm'][i][1])*scale]for i in ids])
                lo=np.maximum(0,np.floor(pts.min(axis=0)).astype(int));hi=np.minimum([719,279],np.ceil(pts.max(axis=0)).astype(int))
                if (hi<lo).any():continue
                a,b,c=pts;den=(b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
                if abs(den)<1e-12:continue
                yy,xx=np.mgrid[lo[1]:hi[1]+1,lo[0]:hi[0]+1];xx=xx+.5;yy=yy+.5
                u=((b[0]-xx)*(c[1]-yy)-(b[1]-yy)*(c[0]-xx))/den
                v=((c[0]-xx)*(a[1]-yy)-(c[1]-yy)*(a[0]-xx))/den;w=1-u-v
                mask=(u>=-1e-8)&(v>=-1e-8)&(w>=-1e-8)
                values=[m['uv1'][i][0]for i in ids];alpha=u*values[0]+v*values[1]+w*values[2]
                region=canvas[lo[1]:hi[1]+1,lo[0]:hi[0]+1];region[mask]=np.maximum(region[mask],alpha[mask])
            color=(np.array([222,230,203])[None,None,:]*(1-canvas[:,:,None])+np.array([90,63,37])[None,None,:]*canvas[:,:,None]).astype(np.uint8)
            image.paste(Image.fromarray(color),(left,top));stats=coverage_statistics(m)
            draw.text((left,top-30),source['surfaceId']+' / '+('OLD'if column==0 else'RESOLVED'),font=font,fill=(35,44,37))
            draw.text((left,top+284),f"zero area {stats['allZeroCoverageAreaPercent']:.2f}% / mean {stats['areaWeightedMeanLinearCoverage']:.3f}",font=font,fill=(35,44,37))
    image.save(file)

def draw_layout(file, layouts, soils, planting_domains, roots, feet):
    image=Image.new('RGB',(1700,1650),(238,239,231));draw=ImageDraw.Draw(image)
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',19)
    title=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial Bold.ttf',25)
    draw.text((35,20),'R32 CLIPPED YARD GROUND + LOW MIXED GROWTH / SOURCE ONLY',font=title,fill=(30,43,36))
    draw.text((35,59),'Original gravel, soil beds and13 shrubs retained; no road connection or legal yard boundary asserted.',font=font,fill=(47,57,45))
    colors={'entry_walk':(197,177,139),'service_court':(188,174,137),'soil_bed':(122,88,53),'worn_edge':(171,154,105)}
    for n,yard in enumerate(layouts['yards']):
        key=yard['buildingSourceId'];domain=soils[key];bb=unary_union([domain,feet[key]]).bounds
        scale=min(1450/(bb[2]-bb[0]),390/(bb[3]-bb[1]));left=850-(bb[2]-bb[0])*scale/2;top=155+n*480
        xy=lambda p:(left+(p[0]-bb[0])*scale,top+(bb[3]-p[1])*scale)
        def paint(g,color,outline=None):
            for poly in polygons(g):
                draw.polygon([xy(q)for q in poly.exterior.coords],fill=color,outline=outline)
                for ring in poly.interiors:draw.polygon([xy(q)for q in ring.coords],fill=(224,229,209))
        paint(domain,(150,164,111),(117,136,98));paint(feet[key],(107,120,120),(60,79,80))
        for row in layouts['surfaces']:
            if row['buildingSourceId']==key and row['role']!='worn_edge':paint(shape(row['domainCm']),colors[row['role']],(111,106,88))
        for root in layouts['planting']:
            if root['buildingSourceId']==key:
                px,py=xy(root['positionCm']);radius=root['radialEnvelopeCm']*scale
                draw.ellipse((px-radius,py-radius,px+radius,py+radius),fill=(75,104,69),outline=(40,77,50),width=2)
        for root in roots:
            if root['buildingSourceId']==key:
                px,py=xy(root['positionCm']);radius=max(1.5,root['allLodSourceRadialEnvelopeCm']*scale)
                fill=(68,109,57)if root['modelId']==MODELS[0]else(94,128,61)if root['modelId']==MODELS[1]else(146,158,61)
                draw.ellipse((px-radius,py-radius,px+radius,py+radius),fill=fill)
        draw.text((40,top-40),f"{key}: clipped substrate {domain.area/10000:.2f} m² / low roots {sum(r['buildingSourceId']==key for r in roots)}",font=title,fill=(39,54,41))
    draw.text((35,1600),'No native material/occlusion/performance or complete-realism acceptance is inferred from this layout.',font=font,fill=(67,72,58))
    image.save(file)

def main():
    require(not OUTPUT.exists(),'Use one fresh isolated R32 source output')
    base=read(BASE/'context-yard-native-report-r2.json')
    require(sha(BASE/'context-yard-native-report-r2.json')==EXPECTED_BASE_SHA and base['status']=='verified-saved-purposeful-context-yards-overlay','Actual saved R28b required')
    require(sha(PNG)==EXPECTED_PNG_SHA,'Actual reviewed neighbor PNG changed')
    plan=read(SOURCE/'yard-source-plan.json');layout=read(plan['layout']['path']);masks={key:shape(value)for key,value in read(plan['masks']['path']).items()}
    old=read(GEOMETRY/'yard-ground-geometry.json')['meshes'];old_worn=next(m for m in old if m['role']=='worn_edge')
    data={key:read(ROOT/p.SOURCES[key])for key in ('buildings','context','terrain','plantGeometry','nativeR16')}
    models={m['id']:m for m in data['plantGeometry']['meshes']};native=data['nativeR16']
    feet={b['id']:unary_union([Polygon(poly[0],poly[1:])for poly in b['polygonsCm']])for b in data['buildings']['buildings'] if b['id']in p.TARGETS}
    exclusions=unary_union([value.buffer(20)for value in masks.values()])
    allowed={key:feet[key].buffer(700).difference(exclusions)for key in p.TARGETS}
    soft,planting={},{ }
    for key in p.TARGETS:
        surfaces=[r for r in layout['surfaces']if r['buildingSourceId']==key]
        hard=unary_union([shape(r['domainCm'])for r in surfaces if r['role']in ('entry_walk','service_court')])
        beds=unary_union([shape(r['domainCm'])for r in surfaces if r['role']=='soil_bed'])
        # Grow from purposefully authored use, not a rectangular field fill.
        domain=unary_union([hard.buffer(145),beds.buffer(115)]).intersection(allowed[key]).difference(beds)
        require(not domain.is_empty and domain.is_valid and domain.difference(allowed[key]).area<1e-5,'Invalid clipped yard substrate')
        soft[key]=domain
        shrub_bounds=unary_union([Point(r['positionCm'][:2]).buffer(r['radialEnvelopeCm']+12)for r in layout['planting']if r['buildingSourceId']==key])
        planting[key]=domain.difference(hard.buffer(20)).difference(shrub_bounds)
    ground=p.Ground(data['context'],data['terrain'],unary_union(list(soft.values())).buffer(50))
    resolved=[];diagnostic=[]
    for row in layout['surfaces']:
        if row['role']!='worn_edge':continue
        domain=shape(row['domainCm']);r=next(x for x in old_worn['sourceSurfaceRanges']if x['surfaceId']==row['id'])
        offset=r['firstTriangle']*3;indexes=old_worn['indices'][offset:offset+r['triangles']*3]
        original={**old_worn,'indices':indexes,'surfaceId':row['id'],'domainCm':row['domainCm']}
        new=mesh(domain,'r32_resolved_same_worn_'+row['buildingSourceId'].replace('.','_'),8,ground,sample_ground=False);new['surfaceId']=row['id']
        resolved.append((original,new));diagnostic.append({'surfaceId':row['id'],'old':coverage_statistics(original),'samePolygonResolved':coverage_statistics(new)})
    meshes=[]
    for role in ('entry_walk','service_court'):
        for row in layout['surfaces']:
            if row['role']==role:
                m=mesh(shape(row['domainCm']),'yard_ground_r32_'+row['buildingSourceId'].replace('.','_')+'_'+role,6,ground,
                       hard_max_relief=row['maximumAddedReliefCm'])
                # Native trial must reuse original source contact/relief at the
                # new tessellated points; no arbitrary elevation compensation.
                m['role']=role;m['retainExactR28AuthoredFootprint']=True;m['materialProposal']='gravel_pbr_resolved_inside_feather'
                meshes.append(m)
    for key in p.TARGETS:
        hard=unary_union([shape(r['domainCm'])for r in layout['surfaces']if r['buildingSourceId']==key and r['role']in('entry_walk','service_court')])
        def soil_fraction(xy):
            distance=Point(xy).distance(hard.boundary)
            # A connected worn verge, not a black-only soil outline.
            near=1.-smooth(distance/80.)
            variation=.5+.5*math.sin(xy[0]/83.+.4*math.sin(xy[1]/121.))
            return .08+.10*variation+.17*near
        m=mesh(soft[key],'yard_ground_r32_'+key.replace('.','_')+'_substrate',18,ground,soil_fraction)
        m['role']='yard_substrate';m['materialProposal']='metric_grass_and_earth_pbr_with_uv1_y_mix'
        m['retainExactR28BedsAndAllShrubRoots']=True;meshes.append(m)
    meshes=[combine_meshes([row for row in meshes if row['role']==role],role)for role in ('entry_walk','service_court','yard_substrate')]
    overlap_proof=source_overlap_depth_proof(meshes)
    roots,model_proof=choose_plants(layout['yards'],planting,ground,models,native)
    require(roots and len(roots)<=2046,'Empty/unbounded low mixed source layer')
    budgets=[sum(row['nativeLodTriangles'][lod]for row in roots)for lod in range(3)]
    references={key:native['materials']['materials'][key]for key in ('context_track','context_garden_soil')}
    recipes=[{'id':'yard_gravel_r32','duplicateSource':references['context_track']['asset'],'sourceGraphSha256':references['context_track']['graphSha256'],
              'baseRecipe':references['context_track']['recipe'],'changes':{'OpacityMask':'UV1.x through native DitherTemporalAA.Result','edgeGeometry':'6cm internal feather resolved with2cm offset rings'},'newTextureObjects':0},
             {'id':'yard_substrate_r32','duplicateSource':references['context_garden_soil']['asset'],'sourceGraphSha256':references['context_garden_soil']['graphSha256'],
              'baseRecipe':references['context_garden_soil']['recipe'],'changes':{'groundLayerAmount':'Grass004 amount=1-UV1.y for all albedo/normal/roughness layer mixes',
              'soilFractionRange':[.08,.35],'OpacityMask':'UV1.x through native DitherTemporalAA.Result','edgeGeometry':'18cm feather resolved with2cm offset rings'},'newTextureObjects':0}]
    OUTPUT.mkdir(parents=True)
    write(OUTPUT/'edge-coverage-diagnosis.json',{'actualReviewedPng':pin(PNG),'oldGeometry':pin(GEOMETRY/'yard-ground-geometry.json'),
          'nativeCornerProofSourceMatched':True,'oldCellCm':40,'oldBandCm':32,'oldFeatherCm':8,'rows':diagnostic,
          'finding':'Coarse40cm triangulation places most32cm strip corners on zero-coverage boundaries; isolated interior corners produce actual triangle-shaped masked islands.',
          'materialAmplification':{'wornAlbedoScale':.3,'wornTint':[.65,.53,.4]},'nativeAppearanceAccepted':False})
    write(OUTPUT/'yard-ground-proposal.json',{'meshes':meshes,'planting':roots,'sourcePlantModels':model_proof,
         'substrateDomainsCm':{key:mapping(value)for key,value in soft.items()},'plantingDomainsCm':{key:mapping(value)for key,value in planting.items()},
         'retainedLayout':pin(plan['layout']['path']),'retainedShrubIds':[r['id']for r in layout['planting']],
         'sourceExclusionMasks':pin(plan['masks']['path'])})
    write(OUTPUT/'material-copy-proposals.json',recipes)
    write(OUTPUT/'source-overlap-depth-proof.json',overlap_proof)
    write_glb(OUTPUT/'yard-ground-r32.glb',meshes)
    write(OUTPUT/'source-glb-validation.json',validate_source_glb(OUTPUT/'yard-ground-r32.glb',meshes))
    draw_alpha_comparison(OUTPUT/'edge-source-coverage-comparison.png',[r[0]for r in resolved],[r[1]for r in resolved])
    draw_layout(OUTPUT/'yard-ground-source-layout.png',layout,soft,planting,roots,feet)
    shutil.copyfile(ROOT/OWNER,OUTPUT/'source-producer.py')
    inputs=[ROOT/OWNER,ROOT/'scripts/unreal/exterior-context-yard-ground-quantization-r32-r4.py',ROOT/'scripts/unreal/exterior-context-yard-study-r28.py',BASE/'context-yard-native-report-r2.json',PNG,
            SOURCE/'yard-source-plan.json',Path(plan['layout']['path']),Path(plan['masks']['path']),GEOMETRY/'yard-ground-geometry.json',
            *[ROOT/p.SOURCES[k]for k in data],*[Path(model_proof[key]['existingSource']['path'])for key in MODELS]]
    for rec in references.values():
        for source in [rec['recipe'],rec['recipe'].get('groundCover',{})]:
            for tex in source.get('maps',{}).values():
                require(sha(tex['path'])==tex['sha256'],'Original existing PBR texture changed');inputs.append(Path(tex['path']))
    audit={'sourceOnly':True,'yardCount':3,'retainedShrubs':13,'originalPathsAndBedsFootprintsExact':True,
           'newSourceGroundMeshes':len(meshes),'sourceGroundTriangles':sum(len(m['indices'])//3 for m in meshes),
           'sourceGroundVertices':sum(len(m['verticesCm'])for m in meshes),'clippedSubstrateAreaM2':sum(g.area for g in soft.values())/10000.,
           'lowPlantRoots':len(roots),'sourcePlantTrianglesByLod':budgets,'sourcePlantPopulationByModel':{key:sum(r['modelId']==key for r in roots)for key in MODELS},
           'nativePackagesOrGraphsChanged':False,'existingNativeRootsRemoved':0,'newTexturePixels':0,
           'activeDesign':base['activeDesign'],'setbacksMm':base['setbacksMm'],'nativeApplied':False,
           'nativeAppearanceAccepted':False,'performanceAccepted':False,'fullPhotorealismAccepted':False,'shippingAccepted':False}
    write(OUTPUT/'yard-ground-study-plan.json',{'schema':'brezi-context-yard-resolved-edge-and-clipped-low-growth-source-r32-r4','owner':OWNER,
         'status':'source-only-layout-and-geometry-review-native-pending','diagnosticSavedNativeReport':pin(BASE/'context-yard-native-report-r2.json'),
         'selectedNativeBase':None,'selectedNativeBasePending':True,'intendedFutureNativeBase':'actual saved exterior-20261002-r30a, only after successful closed report',
         'generator':pin(ROOT/OWNER),'snapshot':pin(OUTPUT/'source-producer.py'),'inputFiles':[pin(f)for f in sorted(set(inputs))],
         'edgeDiagnosis':pin(OUTPUT/'edge-coverage-diagnosis.json'),'proposal':pin(OUTPUT/'yard-ground-proposal.json'),
         'sourceGlb':pin(OUTPUT/'yard-ground-r32.glb'),'materialCopyProposals':pin(OUTPUT/'material-copy-proposals.json'),'audit':audit,
         'sourceOverlapDepthProof':pin(OUTPUT/'source-overlap-depth-proof.json'),
         'sourceGlbValidation':pin(OUTPUT/'source-glb-validation.json'),
         'quantizedTopologyAccounting':{'discardedExactZeroFaces':sum(r['quantizedTopologyAccounting']['discardedFaceCount']for m in meshes for r in m['sourceSurfaceRanges']),
             'discardedBeforeHeightExactZeroProjectedRegions':sum(len(cell['discardedBeforeHeightExactZeroProjectedRegions'])for m in meshes for r in m['sourceSurfaceRanges']for cell in r['quantizedPlanarPartition']['cells']),
             'discardedDecodedProjectedFootprintAreaCm2':0.,'approximatePruningUsed':False,'nonzeroFacesDropped':False,
             'authoredToProposedNativeF32FloorSymmetricDifferenceAreaCm2ByPiece':{r['sourcePieceId']:r['quantizedPlanarPartition']['authoredToProposedNativeF32FloorSymmetricDifferenceAreaCm2']for m in meshes for r in m['sourceSurfaceRanges']}},
         'unselectedPriorSourceDraft':pin(ROOT/'output/unreal/exterior-context-yard-ground-20261002-r32-study/draft-review-no-go.json'),
         'futureNativeScope':['Retain all R28 paths/beds/shrub roots and all original architecture/roads/lighting.',
              'A later typed candidate may rebind only the2 original hard-ground components to resolved source geometry/material.',
              'Hide only the old worn-edge component; its exact footprints are contained in the new connected substrate.',
              'Add clipped substrate and low plant groups; all old transforms/material assets remain unchanged.'],
         'limits':['Three7m artist envelopes are not legal parcels or observed land use. Contacts derive existing unsurveyed source triangles.',
              'Coverage comparison is exact source UV interpolation, not native temporal-dither pixels, shading or acceptance.',
              'Existing processed photo-textured grass/herb masters are reused; no new original-provider fidelity claim.',
              'Native full saved geometry/material/actor/root-frame and visual checks are still required. Native N/T not measured.']})
    print(json.dumps({'plan':pin(OUTPUT/'yard-ground-study-plan.json'),'audit':audit}))

if __name__=='__main__':
    main()
