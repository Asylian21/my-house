"""R42 source-only first-yard concrete court and low inner edge.

Reads frozen source arrays/receipts and the actual saved R38 witness. It never
loads Unreal or a historical producer/checker, exports a GLB, or selects a
future native base. The old three-yard court, entry and plants remain intact;
one proposed visual overlay stays strictly inside the first authored court.
"""
import hashlib
import json
import math
from pathlib import Path
import struct
import sys

sys.dont_write_bytecode = True
from shapely import constrained_delaunay_triangles
from shapely.geometry import Point, Polygon, box, mapping, shape
from shapely.ops import unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-context-yard-court-study-r42.py'
OUTPUT = ROOT/'output/unreal/exterior-context-yard-court-20261002-r42-source-study'
SCHEMA = 'brezi-first-authored-neighbor-court-source-r42'
TARGET = '/Game/Brezi/Maps/Brezi.Brezi:PersistentLevel.StaticMeshActor_665'
BUILDING = 'BU.572063'
LAYOUT = ROOT/'output/unreal/exterior-context-yard-20261002-r28-study/yard-layout.json'
LAYOUT_SHA = '3ba5829cef341736b76a5bfce33eb961e919e7d9374ab9aed842bb2e85061ada'
MASKS = LAYOUT.parent/'source-exclusion-masks.json'
MASKS_SHA = 'cedd1bcc0a10ca3c2c0f91a4799c93f5430f1cbf7a4e0d1e8e121e574e816f62'
REPORT = ROOT/'output/unreal/exterior-20261002-r38b/soft-ground-native-report-r2.json'
REPORT_SHA = '077e36066dc49f2c3fa379893c39fc5659e8261385030d86266316e1bde9f2b9'
GLB = ROOT/'output/unreal/exterior-context-yard-20261002-r35-source-repair-proposal/yard-hard-coverage-r35.glb'
GLB_SHA = '99bedf1cf801d7f113b1a34e486dd17f50e9d475d55a1acf8611560bfa219fa9'
R32 = ROOT/'output/unreal/exterior-context-yard-ground-20261002-r32-study-r5/yard-ground-study-plan.json'
R32_SHA = '8378d06f00e9a11dceff51e4eb12a270eff492d6f729f09d3dfd804de326f650'
LOCK = ROOT/'scripts/archviz/assets.lock.json'
LOCK_SHA = '6cf3122023b10716de541bbac2b857da6b0fb6703ba0d2bed9d0642af366e24a'
GROUND_PNG = ROOT/'output/unreal/exterior-validation-20260930-r1/qa/editor-pilot-r38b-soft-ground-two-camera-r29-r3-1790954357075-1qWu4r/exterior-neighborhood-ground-r38-hPWm0M/userdir/Saved/Diagnostics/exterior-neighborhood-ground-r38-day-20261002T152357-scene.png'
GROUND_PNG_SHA = 'bc4a7f28cb2ca1f2cbaf29439eb7350a005faf20e2d121653f7abea928c2f8d9'
MAX_TRIANGLES = 2400


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()).hexdigest()


def pin(path, expected=None):
    p = Path(path).resolve()
    require(p.is_file() and not p.is_symlink(), 'Original regular input required')
    value = {'path': str(p), 'sha256': sha(p), 'bytes': p.stat().st_size}
    require(expected is None or value['sha256'] == expected, 'Frozen source differs: '+str(p))
    return value


def checked(record):
    pin(record['path'], record['sha256'])
    return json.loads(Path(record['path']).read_text())


def f32(value):
    return struct.unpack('<f', struct.pack('<f', value))[0]


def native_coordinate(value):
    """Fixed point of the declared generated cm -> glTF f32 m -> UE f32 cm."""
    for _ in range(16):
        next_value = f32(f32(value/100.)*100.)
        if struct.pack('<d', value) == struct.pack('<d', next_value):
            return value
        value = next_value
    raise ValueError('Generated coordinate did not reach a declared F32 fixed point')


def glb_mesh():
    raw = GLB.read_bytes()
    require(raw[:4] == b'glTF' and struct.unpack_from('<II', raw, 4) == (2, len(raw)), 'Original GLB2 required')
    chunks = {}; at = 12
    while at < len(raw):
        size, kind = struct.unpack_from('<II', raw, at)
        chunks[kind] = raw[at+8:at+8+size]; at += 8+size
    doc = json.loads(chunks[0x4e4f534a]); binary = chunks[0x004e4942]
    node = next(n for n in doc['nodes'] if n['name'] == 'yard_ground_r32_service_court_LOD0')
    require(not any(k in node for k in ('matrix', 'translation', 'rotation', 'scale', 'children')), 'Original identity ground node required')
    prim, = doc['meshes'][node['mesh']]['primitives']
    def accessor(index):
        a = doc['accessors'][index]; v = doc['bufferViews'][a['bufferView']]
        require(not a.get('normalized') and 'sparse' not in a, 'Original unnormalized dense source required')
        n = {'SCALAR': 1, 'VEC3': 3}[a['type']]; code = {5125: 'I', 5126: 'f'}[a['componentType']]
        stride = v.get('byteStride', 4*n); offset = v.get('byteOffset', 0)+a.get('byteOffset', 0)
        return [list(struct.unpack_from('<'+code*n, binary, offset+i*stride)) for i in range(a['count'])]
    p = accessor(prim['attributes']['POSITION'])
    vertices = [[f32(100*x), f32(100*z), f32(100*y)] for x,y,z in p]
    indices = [r[0] for r in accessor(prim['indices'])]
    return vertices, indices


def load_source():
    inputs = [pin(p,h) for p,h in ((LAYOUT,LAYOUT_SHA),(MASKS,MASKS_SHA),(REPORT,REPORT_SHA),(GLB,GLB_SHA),(R32,R32_SHA),(LOCK,LOCK_SHA),(GROUND_PNG,GROUND_PNG_SHA))]
    layout = json.loads(LAYOUT.read_text()); masks = json.loads(MASKS.read_text()); report = json.loads(REPORT.read_text())
    require(report['status'] == 'verified-saved-image-selected-fixed-world-soft-ground-material-overlay'
        and report['savedMapUnloadedReloaded'] is True and report['nativeProcessId'] == 72504, 'Actual saved R38 reference required')
    require(report['activeDesign'] == {'variant':'C','heatingLayout':'B','livingLayout':'B'}
        and report['setbacksMm'] == {'street':3000,'east':3000}, 'C/B/B and3000mm must remain fixed')
    witness = checked(report['savedActorWitness']); inputs.append(pin(report['savedActorWitness']['path'],report['savedActorWitness']['sha256']))
    raw_pin=pin(report['rawInstanceControlsSaved']['path'],report['rawInstanceControlsSaved']['sha256']);inputs.append(raw_pin)
    actor = witness[TARGET]; c, = actor['components']
    require(actor['transform'] == [[0.,0.,0.],[0.,0.,0.,1.],[1.,1.,1.]] and c['transform'] == actor['transform'], 'Identity existing court required')
    require(c['mesh'].endswith('yard_ground_r32_service_court_LOD0.yard_ground_r32_service_court_LOD0')
        and c['materials'] == ['/Game/Brezi/ContextYardGround20261002R32/Materials/M_yard_gravel_r32.M_yard_gravel_r32'], 'Exact current court binding required')
    yard = next(r for r in layout['yards'] if r['buildingSourceId'] == BUILDING)
    court = next(r for r in layout['surfaces'] if r['buildingSourceId'] == BUILDING and r['role'] == 'service_court')
    entry = next(r for r in layout['surfaces'] if r['buildingSourceId'] == BUILDING and r['role'] == 'entry_walk')
    require(court['sourceAreaM2'] == 9.817431384870023 and entry['sourceAreaM2'] == 6.638567479134447
        and len(layout['planting']) == 13, 'Exact selected footprint and13 old shrubs required')
    r32 = json.loads(R32.read_text()); original = checked(r32['proposal']); inputs.append(pin(r32['proposal']['path'],r32['proposal']['sha256']))
    oldmesh = next(m for m in original['meshes'] if m['role'] == 'service_court')
    span = next(s for s in oldmesh['sourceSurfaceRanges'] if s['sourcePieceId'] == 'yard_ground_r32_BU_572063_service_court')
    require(span['domainCm'] == court['domainCm'] and span['firstTriangle'] == 0 and span['triangles'] == 750, 'Original750-face first court source required')
    vertices, indices = glb_mesh(); faces = [indices[i:i+3] for i in range(0,span['triangles']*3,3)]
    polys = [Polygon([vertices[j][:2] for j in face]) for face in faces]
    require(all(p.area > 0 for p in polys), 'Positive original floor faces required')
    lock = json.loads(LOCK.read_text()); asset = lock['assets']['concrete_pavement']
    require(lock['license'] == 'CC0-1.0' and asset['tileSizeMetres'] == 1.8, 'Existing licensed1.8m original concrete required')
    maps = {}
    for role in ('diffuse','normal','roughness'):
        rec = asset['maps'][role]; path = ROOT/'output/archviz/assets/concrete_pavement'/Path(rec['path']).name
        row = pin(path); raw = path.read_bytes()
        require(len(raw) == rec['size'] and hashlib.md5(raw).hexdigest() == rec['md5'], 'Original provider concrete pixels differ')
        maps[role] = row; inputs.append(row)
    return {'inputs':inputs,'layout':layout,'masks':masks,'yard':yard,'court':court,'entry':entry,'actor':actor,'rawControlsPin':raw_pin,
        'wholeWitnessSha256':digest(witness),'oldOtherActorWitnessSha256':digest({k:v for k,v in witness.items()if k != TARGET}),
        'oldTargetActorSha256':digest(actor),'vertices':vertices,'faces':faces,'polys':polys,'index':STRtree(polys),
        'material':{'provider':'Poly Haven','license':lock['license'],'sourcePage':asset['page'],'physicalTileCm':180.,'originalMaps':maps}}


def source_height(bundle, xy):
    values = []; point = Point(xy)
    for ordinal in bundle['index'].query(point):
        ordinal = int(ordinal)
        if not bundle['polys'][ordinal].covers(point):
            continue
        a,b,c = [bundle['vertices'][j] for j in bundle['faces'][ordinal]]
        det = (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
        u = ((b[0]-xy[0])*(c[1]-xy[1])-(b[1]-xy[1])*(c[0]-xy[0]))/det
        v = ((c[0]-xy[0])*(a[1]-xy[1])-(c[1]-xy[1])*(a[0]-xy[0]))/det
        values.append((u*a[2]+v*b[2]+(1-u-v)*c[2],ordinal,[u,v,1-u-v]))
    require(values, 'New court vertex has no original decoded source floor beneath')
    return max(values)


def polygons(geometry):
    if geometry.is_empty:return []
    if geometry.geom_type == 'Polygon':return [geometry]
    return [p for g in geometry.geoms for p in polygons(g)]


def smooth(value):
    x = max(0., min(1., value)); return x*x*(3-2*x)


def proposed_mesh(bundle):
    court = shape(bundle['court']['domainCm']); entry = shape(bundle['entry']['domainCm'])
    # Five-millimetre inset exceeds generated coordinate rounding here. The
    # original gravel remains as the outermost strip: no footprint widens.
    domain = court.buffer(-.5, join_style=2)
    previous = domain; layers = []
    for distance in (2.,5.,8.,12.):
        inner = court.buffer(-distance,join_style=2); layers.append(previous.difference(inner)); previous = inner
    layers.append(previous)
    vertices=[]; uv=[]; indices=[]; ground=[]; lookup={}; faces=[]
    origin=bundle['yard']['entrance']['edgeOriginCm']; tangent=bundle['yard']['entrance']['tangent']; outward=bundle['yard']['entrance']['outward']
    x0,y0,x1,y1=domain.bounds
    for layer in layers:
        for x in range(math.floor(x0/40)*40,math.ceil(x1/40)*40,40):
            for y in range(math.floor(y0/40)*40,math.ceil(y1/40)*40,40):
                for poly in polygons(layer.intersection(box(x,y,x+40,y+40))):
                    for triangle in constrained_delaunay_triangles(poly).geoms:
                        require(poly.covers(triangle) and triangle.area > 0, 'Constrained source triangle escaped its layer')
                        xy=[[native_coordinate(v) for v in p] for p in list(triangle.exterior.coords)[:3]]
                        projected=Polygon(xy)
                        require(projected.area>0 and court.covers(projected) and projected.intersection(entry).area==0,
                            'Declared F32 triangle leaves exact court or enters entry walk')
                        a,b,c=xy
                        if (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])>0:xy=[a,c,b]
                        for p in xy:
                            key=tuple(p)
                            if key not in lookup:
                                z,ordinal,weights=source_height(bundle,p)
                                distance=Point(p).distance(court.boundary); entry_distance=Point(p).distance(entry)
                                # No raised ridge at the shared walk/court interface.
                                edge_amount=smooth((distance-.5)/1.5)*(1-smooth((distance-8.)/4.))
                                if entry_distance<=12.:edge_amount=0.
                                relief=.06+2.44*edge_amount
                                value=[*p,native_coordinate(z+relief)]
                                q=[p[k]-origin[k] for k in range(2)]
                                lookup[key]=len(vertices);vertices.append(value)
                                uv.append([f32(sum(q[k]*axis[k]for k in range(2))/180.)for axis in (tangent,outward)])
                                ground.append({'sourceTriangleOrdinal':ordinal,'sourceZCm':z,'barycentric':weights,'authoredReliefCm':relief,
                                    'decodedSourceReliefCm':value[2]-z,'entryDistanceCm':entry_distance,'courtBoundaryDistanceCm':distance})
                            indices.append(lookup[key])
                        faces.append(projected)
    require(len(indices)//3<=MAX_TRIANGLES,'Small source mesh budget exceeded')
    require(all(.04<r['decodedSourceReliefCm']<3. for r in ground),'Authored contact/low edge bound exceeded')
    require(2.<max(r['decodedSourceReliefCm']for r in ground)<3.,'Actual proposed edge must reach the requested2–3cm range')
    union=unary_union(faces)
    require(court.covers(union) and union.intersection(entry).area==0,'Full new triangle support widened hard footprint')
    require(all(union.intersection(shape(value)).area==0 for value in bundle['masks'].values()),'New support intersects original exclusions')
    require(all(union.intersection(Point(row['positionCm'][:2]).buffer(row['radialEnvelopeCm'])).area==0
        for row in bundle['layout']['planting']),'Existing13 shrub envelopes must remain clear')
    normals=[[0.,0.,0.]for _ in vertices]
    for offset in range(0,len(indices),3):
        ids=indices[offset:offset+3];a,b,c=[vertices[i]for i in ids]
        u=[c[k]-a[k]for k in range(3)];v=[b[k]-a[k]for k in range(3)]
        n=[u[1]*v[2]-u[2]*v[1],u[2]*v[0]-u[0]*v[2],u[0]*v[1]-u[1]*v[0]]
        require(n[2]>0,'Proposed upward geometric source normal required')
        for i in ids:normals[i]=[normals[i][k]+n[k]for k in range(3)]
    normals=[[f32(v/math.sqrt(sum(x*x for x in n)))for v in n]for n in normals]
    return {'id':'yard_court_r42_BU_572063_visual_overlay','verticesCm':vertices,'normals':normals,'uv0':uv,'indices':indices,
        'sourceWinding':'clockwise','sourceGroundWitnesses':ground,'domainCm':mapping(domain),'projectedTriangleUnionCm':mapping(union),
        'projectedTriangleUnionAreaM2':union.area/10000.,'originalCourtAreaM2':court.area/10000.,
        'originalCourtStillRetainedUnderAndOutsideOverlay':True,'originalOuterGravelStripWidthCm':.5,
        'authoredMaximumReliefCm':2.5,'sharedEntryInterfaceRaisedEdgeProposed':False,'collision':'NoCollision','navigation':False,
        'sourceOnly':True,'nativeExportPerformed':False,'nativeApplied':False}


def material_proposal(bundle):
    return {**bundle['material'],'uvMetric':'door-edge fixed local tangent/outward; same180cm phase on floor and ridge',
        'diffuse':'original RGB sRGB, tint[1,1,1]','normal':'original OpenGL; future green flip+TCNormalmap; strength.32 artistic',
        'roughness':'original Roughness.R linear; no AO/metallic inference','metallic':0.,'sourcePhotoPixelsEdited':False,
        'graphProposalOnly':True,'graphIndependentOfCamera':True,'normalStrengthPhotometricallyCalibrated':False,
        'nativeSharedTextureObjectAvailabilityVerified':False,'plannedNewMaterialGraphs':1,'plannedTextureObjects':'reuse actual authenticated existing concrete trio if policy matches; otherwise three owned originals, determined only by future native binding'}


def diagram(bundle, mesh, path):
    from PIL import Image, ImageDraw, ImageFont
    image=Image.new('RGB',(1400,1000),(247,246,241));draw=ImageDraw.Draw(image)
    font=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',19)
    title=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial.ttf',27)
    court=shape(bundle['court']['domainCm']);entry=shape(bundle['entry']['domainCm'])
    allparts=unary_union([court,entry]);x0,y0,x1,y1=allparts.bounds;scale=min(970/(x1-x0),710/(y1-y0))
    def xy(p):return (100+(p[0]-x0)*scale,790-(p[1]-y0)*scale)
    def fill(g,color):
        for p in polygons(g):
            draw.polygon([xy(v)for v in p.exterior.coords],fill=color,outline=(40,44,42))
            for ring in p.interiors:draw.polygon([xy(v)for v in ring.coords],fill=(247,246,241))
    draw.text((45,22),'R42 | FIRST AUTHOR-DEFINED COURT — SOURCE DIAGRAM',font=title,fill=(25,38,32))
    draw.text((45,60),'No native run, measured terrain, legal parcel boundary or appearance acceptance.',font=font,fill=(80,60,43))
    fill(entry,(174,154,122));fill(court,(212,209,198));fill(shape(mesh['domainCm']),(169,177,181))
    raised=unary_union([Polygon([mesh['verticesCm'][i][:2]for i in mesh['indices'][j:j+3]])
        for j in range(0,len(mesh['indices']),3)if max(mesh['sourceGroundWitnesses'][i]['authoredReliefCm']for i in mesh['indices'][j:j+3])>2.])
    fill(raised,(110,127,132))
    draw.text((1000,140),'UNCHANGED',font=title,fill=(44,55,43))
    for j,line in enumerate(('6.6386 m² gravel entry','13 existing shrub roots','Other two courts / beds','Architecture and all roots','C/B/B + both 3000 mm')):draw.text((1000,185+30*j),line,font=font,fill=(54,65,48))
    draw.text((1000,390),'PROPOSED',font=title,fill=(44,55,63))
    for j,line in enumerate(('9.8174 m² original court','Inset visual overlay only','Original concrete: 1.8 m','2–3 cm INNER ridge','No ridge at walk junction','NoCollision / no WPO')):draw.text((1000,435+30*j),line,font=font,fill=(52,68,72))
    # Technical section; exaggerated vertical scale, explicitly labeled.
    draw.text((45,835),'INNER EDGE SECTION: 0.06 cm contact lift → 2.5 cm ridge → 0.06 cm floor (vertical scale exaggerated)',font=font,fill=(37,45,44))
    points=[]
    for i in range(121):
        d=i/10.;a=smooth((d-.5)/1.5)*(1-smooth((d-8.)/4.));points.append((80+d*64,950-(.06+2.44*a)*26))
    draw.line([(80,950),(850,950)],fill=(125,111,83),width=3);draw.line(points,fill=(55,83,94),width=5)
    draw.text((970,865),'Planar old floor source: not survey.',font=font,fill=(83,68,49))
    draw.text((970,900),'Visual edge; no new walking collision.',font=font,fill=(83,68,49))
    image.save(path)


def write(path,value):
    with Path(path).open('x')as stream:json.dump(value,stream,indent=2,allow_nan=False);stream.write('\n')


def main():
    require(not OUTPUT.exists(),'Fresh R42 source output only')
    bundle=load_source();mesh=proposed_mesh(bundle)
    OUTPUT.mkdir(parents=True);write(OUTPUT/'court-source-geometry.json',mesh);diagram(bundle,mesh,OUTPUT/'court-source-technical-diagram.png')
    plan={'schema':SCHEMA,'owner':OWNER,'schemaVersion':1,'status':'source-only-first-court-review-native-and-image-base-pending',
        'inputs':bundle['inputs'],'sourceProducer':pin(ROOT/OWNER),'referenceSavedR38Report':pin(REPORT,REPORT_SHA),
        'visualReferenceOriginalPng':pin(GROUND_PNG,GROUND_PNG_SHA),'targetBuildingSourceId':BUILDING,'referenceOriginalActor':TARGET,
        'referenceWholeActorWitnessSha256':bundle['wholeWitnessSha256'],'referenceTargetActorSha256':bundle['oldTargetActorSha256'],
        'referenceOtherActorWitnessSha256':bundle['oldOtherActorWitnessSha256'],'referenceTargetActor':bundle['actor'],
        'referenceOriginalRawInstanceControls':bundle['rawControlsPin'],
        'sourceCourt':bundle['court'],'sourceEntryUnchanged':bundle['entry'],'source13ShrubsUnchangedSha256':digest(bundle['layout']['planting']),
        'sourceAllOtherSurfacesUnchangedSha256':digest([r for r in bundle['layout']['surfaces']if r['id']!=bundle['court']['id']]),
        'geometry':pin(OUTPUT/'court-source-geometry.json'),'technicalDiagram':pin(OUTPUT/'court-source-technical-diagram.png'),
        'materialProposal':material_proposal(bundle),'scope':{'oldActorMutations':0,'oldRootMutations':0,'newVisualMeshActorsProposed':1,
            'newVisualMeshObjectsProposed':1,'newPlantRoots':0,'triangleCount':len(mesh['indices'])//3,'vertexCount':len(mesh['verticesCm']),
            'maximumTriangles':MAX_TRIANGLES,'floorAndRidgeMaterialSectionsProposed':1},
        'sourceProof':{'allFullF32TrianglesInsideOriginalCourt':True,'entryWalkProjectedIntersectionAreaCm2':0.,
            'nonCollisionVisualContactOnly':True,'originalThreeYardCourtMeshRetained':True,'oldSharedMaterialGraphOrPhotoPixelsChanged':False,
            'maximumSourceReliefCm':max(r['decodedSourceReliefCm']for r in mesh['sourceGroundWitnesses']),
            'overlayProjectedAreaM2':mesh['projectedTriangleUnionAreaM2'],'currentNativeActorOrGeometryFreshlyDecoded':False},
        'activeDesign':{'variant':'C','heatingLayout':'B','livingLayout':'B'},'setbacksMm':{'street':3000,'east':3000},
        'selectedNativeBase':None,'selectedProjectClone':None,'selectedRootImageDecision':None,'nativePlan':None,'nativeReport':None,
        'nativeExecuted':False,'gpuExecuted':False,'nativeAppearanceAccepted':False,'fullPhotorealismAccepted':False,'performanceAccepted':False,
        'shippingVerified':False,'activeOutputPromoted':False,'limits':['Original700cm yard envelope is illustrative, not a legal parcel.',
            'Existing source elevation/contact is authored and unsurveyed; new ridge is visual only.',
            'Inset leaves original gravel strip, no path/door threshold or driveway connection inferred.',
            'Proposed PBR/photo color and low edge shadow require future matched native images; no pixels or visibility measured.',
            'Generated normals are authored geometry; native normal/tangent/UV readback remains pending.',
            'R39 image-selected base is pending; R38 is reference evidence only.']}
    write(OUTPUT/'court-source-plan.json',plan)
    require(all(pin(r['path'])==r for r in bundle['inputs']),'Consumed input changed during one source emission')
    print(json.dumps({'plan':pin(OUTPUT/'court-source-plan.json'),'geometry':plan['geometry'],'diagram':plan['technicalDiagram'],'scope':plan['scope']}))


if __name__=='__main__':main()
