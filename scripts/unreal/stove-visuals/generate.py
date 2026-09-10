"""CPU-only, source-bound native stove visual derivative. Never edits source OBJ.

python3 scripts/unreal/stove-visuals/generate.py
Coordinates in the recipe are millimetres relative to the source stove axis;
the GLB uses the existing bridge's right-handed Y-up metres.
"""
import argparse
import hashlib
import json
import math
import struct
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REVISION = "NATIVE-STOVE-CHAMBER-20260908-1"
BASE = "FIREPLACE-STOVE-2026-08-24 · "
GUARDS = {
    "DOM_00522": ("BODY · matne čierne valcové teleso Ø510", "MAT_0034", 256, True),
    "DOM_00525": ("FIRE-GLOW · žeravé ohnisko", "MAT_0035", 192, False),
    "DOM_00531": ("LOG-1 · horiace poleno", "MAT_0035", 80, False),
    "DOM_00532": ("LOG-2 · horiace poleno", "MAT_0035", 80, False),
    "DOM_00533": ("FLAME-1 · plameň", "MAT_0035", 96, False),
    "DOM_00534": ("FLAME-2 · plameň", "MAT_0035", 96, False),
    "DOM_00535": ("FLAME-3 · plameň", "MAT_0035", 96, False),
}
PRESERVED = {"DOM_00526": ("CURVED-GLASS · zaoblené panoramatické dvierka 118°", "MAT_0036", 192, False)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def canonical_hash(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def obj_geometry(path, ids):
    vertices, output, current = [], {}, None
    for line in Path(path).read_text().splitlines():
        fields = line.split()
        if not fields:
            continue
        if fields[0] == "o":
            current = fields[1]
            if current in ids:
                require(current not in output, "Duplicate source OBJ object")
                output[current] = []
        elif fields[0] == "v":
            vertices.append(tuple(map(float, fields[1:])))
        elif fields[0] == "f" and current in ids:
            require(len(fields) == 4, "Source OBJ is no longer triangulated")
            triangle = tuple(vertices[int(field.split("/")[0])-1] for field in fields[1:])
            require(all(len(p) == 3 and all(math.isfinite(v) for v in p) for p in triangle), "Nonfinite source geometry")
            output[current].append(triangle)
    require(output.keys() == ids, "Missing source stove geometry")
    return output


def verify_source(directory):
    directory = Path(directory)
    scene = json.loads((directory / "scene.json").read_text())
    require(scene["objSha256"] == sha(directory / "dom-mm.obj"), "Source OBJ SHA changed")
    guards = {**GUARDS, **PRESERVED}
    selected = [r for r in scene["objects"] if r["id"] in guards]
    records = {r["id"]: r for r in selected}
    require(records.keys() == guards.keys() and len(selected)==len(records), "Missing or duplicated guarded source stove record")
    triangles = obj_geometry(directory / "dom-mm.obj", guards.keys())
    for id_, (suffix, material, count, collide) in guards.items():
        r = records[id_]
        require(r["name"] == BASE+suffix and r["sourceId"] == BASE+suffix and r["enabled"] is True,
                "Stove source identity changed: "+id_)
        require(r["materialSlots"] == [material] and r["triangles"] == count
                and len(triangles[id_]) == count and r["metadata"]["babylonCheckCollisions"] is collide,
                "Stove source geometry/material/collision changed: "+id_)
        bounds = r["boundsMm"]
        points = [p for tri in triangles[id_] for p in tri]
        for i in range(3):
            require(abs(min(p[i] for p in points)-bounds["min"][i]) < 0.011
                    and abs(max(p[i] for p in points)-bounds["max"][i]) < 0.011,
                    "Stove source OBJ/manifest bounds differ: "+id_)
    body = records["DOM_00522"]["boundsMm"]
    require(all(abs((body["max"][i]-body["min"][i])-size) < 0.001 for i,size in enumerate((510,510,1520)))
            and abs(body["min"][2]-30) < 0.001 and abs(body["max"][2]-1550) < 0.001,
            "Stove exterior envelope changed")
    require(records["DOM_00522"]["metadata"].get("designSourceId") == "SRC-CLIENT-FIREPLACE-POSITION-20260825",
            "Stove design revision changed")
    center = [(body["min"][i]+body["max"][i])/2 for i in (0,1)]
    glass=[p for triangle in triangles["DOM_00526"] for p in triangle]
    require(max(abs(math.hypot(p[0]-center[0],p[1]-center[1])-264) for p in glass)<0.001
            and abs(min(p[2] for p in glass)-430)<0.001 and abs(max(p[2] for p in glass)-1030)<0.001,
            "Source curved glass radius/elevations changed")
    angles=[math.degrees(math.atan2(p[1]-center[1],p[0]-center[0])) for p in glass]
    require(abs(min(angles)+59)<0.001 and abs(max(angles)-59)<0.001,"Source curved glass angle changed")
    return scene, records, triangles, center


class Mesh:
    def __init__(self, name, role):
        self.name, self.role, self.positions, self.normals, self.uvs, self.indices = name, role, [], [], [], []

    def triangle(self, a, b, c, uvs=((0,0),(1,0),(1,1)), normals=None):
        ab, ac = [b[i]-a[i] for i in range(3)], [c[i]-a[i] for i in range(3)]
        n = (ab[1]*ac[2]-ab[2]*ac[1], ab[2]*ac[0]-ab[0]*ac[2], ab[0]*ac[1]-ab[1]*ac[0])
        length = math.sqrt(sum(v*v for v in n))
        require(length > 0.000001, "Degenerate derivative triangle")
        n = tuple(v/length for v in n)
        for point, uv, normal in zip((a,b,c), uvs, normals or (n,n,n)):
            self.indices.append(len(self.positions)); self.positions.append(tuple(point)); self.uvs.append(uv); self.normals.append(normal)

    def quad(self, a,b,c,d, uvs=((0,0),(1,0),(1,1),(0,1)), normals=None):
        self.triangle(a,b,c,uvs[:3], normals[:3] if normals else None)
        self.triangle(a,c,d,(uvs[0],uvs[2],uvs[3]), (normals[0],normals[2],normals[3]) if normals else None)


def geometry(source_triangles, center):
    shell, chamber, logs, flames = [Mesh("STOVEV_"+name.upper(), name) for name in ("shell","chamber","logs","flames")]
    # Keep the source's exact 64-sided exterior polygon; newly cut jamb points
    # intersect its chords instead of expanding to a perfect analytic circle.
    unique = {(round(p[0]-center[0],6),round(p[1]-center[1],6)) for tri in source_triangles["DOM_00522"] for p in tri
              if math.hypot(p[0]-center[0],p[1]-center[1]) > 250}
    require(len(unique) == 64, "Expected the source 64-sided shell perimeter")
    polygon = sorted((math.atan2(y,x),x,y) for x,y in unique)
    half = math.radians(59)

    def point(angle):
        ray = (math.cos(angle),math.sin(angle))
        for i,(a,x,y) in enumerate(polygon):
            b,u,v = polygon[(i+1)%len(polygon)]
            b = b if b > a else b+math.tau
            theta = angle if angle >= a else angle+math.tau
            if a-1e-10 <= theta <= b+1e-10:
                dx,dy = u-x,v-y
                cross = ray[0]*dy-ray[1]*dx
                t = (x*dy-y*dx)/cross
                return (ray[0]*t,ray[1]*t)
        raise ValueError("Cannot intersect source perimeter")

    angles = sorted(set([a for a,_,_ in polygon]+[-half,half]))
    for i,a in enumerate(angles):
        b = angles[(i+1)%len(angles)]
        if b <= a: b += math.tau
        p,q = point(a),point(b-math.tau if b > math.pi else b)
        ranges = [(30,430),(1030,1550)]
        if not (-half < (a+b)/2 < half): ranges.append((430,1030))
        for lo,hi in ranges:
            shell.quad((*p,lo),(*q,lo),(*q,hi),(*p,hi), normals=tuple((x/255,y/255,0) for x,y in (p,q,q,p)))
        inner_p=(245*math.cos(a),245*math.sin(a))
        inner_q=(245*math.cos(b),245*math.sin(b))
        shell.quad((*p,430),(*q,430),(*inner_q,440),(*inner_p,440))
        shell.quad((*q,1030),(*p,1030),(*inner_p,1020),(*inner_q,1020))
        shell.triangle((0,0,30),(*q,30),(*p,30))
        shell.triangle((0,0,1550),(*p,1550),(*q,1550))
    # Firebox inner lining, floor and ceiling. No geometry projects outside the
    # original radius255 envelope or alters any collision mesh.
    steps = 72
    for i in range(steps):
        a = half+(math.tau-2*half)*i/steps
        b = half+(math.tau-2*half)*(i+1)/steps
        p,q = (245*math.cos(a),245*math.sin(a)),(245*math.cos(b),245*math.sin(b))
        chamber.quad((*q,440),(*p,440),(*p,1020),(*q,1020))
    for i in range(96):
        a,b = i*math.tau/96,(i+1)*math.tau/96
        p,q = (245*math.cos(a),245*math.sin(a)),(245*math.cos(b),245*math.sin(b))
        chamber.triangle((0,0,440),(*p,440),(*q,440))
        chamber.triangle((0,0,1020),(*q,1020),(*p,1020))
    # Opaque reveals close the 10mm annular wall thickness at both jambs.
    for angle in (-half,half):
        p = point(angle); q = (245*math.cos(angle),245*math.sin(angle))
        shell.quad((*p,430),(*p,1030),(*q,1020),(*q,440))
    # Two irregular, charred logs; source lengths/heights and Y offsets remain.
    transforms = []
    for j,(cy,z,rotation) in enumerate(((-62,500,-0.18),(54,535,0.22))):
        rings,segments = 6,24
        def lp(k,i):
            along = -122.5+245*k/rings
            angle = i*math.tau/segments
            r = 25*(1+0.045*math.sin(i*2.31+j)+0.025*math.sin(k*1.7+i*0.6))
            across = r*math.cos(angle)
            return (100+across*math.cos(rotation)-along*math.sin(rotation), cy+along*math.cos(rotation)+across*math.sin(rotation), z+r*math.sin(angle))
        for k in range(rings):
            for i in range(segments):
                # Winding points outward for an axis along positive Y.
                logs.quad(lp(k,i),lp(k+1,i),lp(k+1,(i+1)%segments),lp(k,(i+1)%segments),
                          ((i/segments,k/rings),(i/segments,(k+1)/rings),((i+1)/segments,(k+1)/rings),((i+1)/segments,k/rings)))
        for k in (0,rings):
            end = (100-(-122.5+245*k/rings)*math.sin(rotation),cy+(-122.5+245*k/rings)*math.cos(rotation),z)
            for i in range(segments):
                a,b = lp(k,i),lp(k,(i+1)%segments)
                logs.triangle(end,a,b) if k == 0 else logs.triangle(end,b,a)
        transforms.append({"visualOf":"DOM_00531" if j==0 else "DOM_00532", "centerRelativeMm":[100,cy,z], "lengthMm":245,"meanRadiusMm":25,"rotationRad":rotation})
    for j,(cy,height,width,bottom) in enumerate(((-75,200,100,520),(0,290,120,535),(82,170,90,520))):
        # Two crossed cards per flame. UV bands carry a deterministic phase;
        # geometry is static, the opacity/emission shape animates in the shader.
        for angle in (0,math.pi/2):
            dx,dy = math.sin(angle)*width/2,math.cos(angle)*width/2
            flames.quad((145-dx,cy-dy,bottom),(145+dx,cy+dy,bottom),(145+dx,cy+dy,bottom+height),(145-dx,cy-dy,bottom+height),
                        ((j*2,0),(j*2+1,0),(j*2+1,1),(j*2,1)))
        transforms.append({"visualOf":f"DOM_{533+j:05d}","centerRelativeMm":[145,cy,bottom+height/2],"heightMm":height,"widthMm":width,"cards":2})
    meshes = [shell,chamber,logs,flames]
    validation = validate_vertices(meshes)
    return meshes, transforms, validation


def validate_vertices(meshes):
    evidence = {}
    for mesh in meshes:
        require(mesh.positions and all(math.isfinite(v) for p in mesh.positions for v in p), "Nonfinite or empty stove geometry")
        maximum_radius = max(math.hypot(x,y) for x,y,z in mesh.positions)
        require(maximum_radius <= 255.011 and all(29.99 <= z <= 1550.01 for x,y,z in mesh.positions), "Derivative exceeds source exterior envelope")
        if mesh.role in ("logs","flames"):
            require(maximum_radius <= 245 and all(440 <= z <= 1020 for x,y,z in mesh.positions), "Fire detail escapes inner chamber")
            # Curved glass inner radius is source264mm, leaving >=19mm air.
            require(all(x < math.sqrt(264**2-y*y)-19 for x,y,z in mesh.positions), "Fire detail is in front of curved glass")
        if mesh.role == "shell":
            for tri in [mesh.positions[i:i+3] for i in range(0,len(mesh.positions),3)]:
                c = [sum(p[i] for p in tri)/3 for i in range(3)]
                require(not (441 < c[2] < 1019 and abs(math.atan2(c[1],c[0])) < math.radians(58.999)
                             and math.hypot(c[0],c[1]) > 248), "Opaque shell closes the source window")
        evidence[mesh.name] = {"triangles":len(mesh.indices)//3,"maximumRadiusMm":maximum_radius,
            "minElevationMm":min(p[2] for p in mesh.positions),"maxElevationMm":max(p[2] for p in mesh.positions)}
    return evidence


def write_glb(meshes, center, path):
    document = {"asset":{"version":"2.0","generator":"Brezí source-bound stove derivative"},"scene":0,
                "scenes":[{"nodes":list(range(len(meshes)))}],"nodes":[],"meshes":[],"accessors":[],"bufferViews":[],"buffers":[],
                "materials":[{"name":"StoveVisualUVValidation","pbrMetallicRoughness":{"baseColorFactor":[0.04,0.04,0.04,1],"metallicFactor":0,"roughnessFactor":0.8}}]}
    binary = bytearray()
    def data(values, size, kind, component, code, target):
        while len(binary)%4: binary.append(0)
        offset = len(binary)
        flat = [v for row in values for v in row]
        binary.extend(struct.pack("<"+code*len(flat),*flat))
        view = len(document["bufferViews"])
        document["bufferViews"].append({"buffer":0,"byteOffset":offset,"byteLength":len(binary)-offset,"target":target})
        accessor = {"bufferView":view,"componentType":component,"count":len(values),"type":kind}
        if kind == "VEC3":
            accessor.update(min=[min(row[i] for row in values) for i in range(size)],max=[max(row[i] for row in values) for i in range(size)])
        index=len(document["accessors"]); document["accessors"].append(accessor); return index
    records=[]
    for mesh in meshes:
        positions=[((p[0]+center[0])/1000,p[2]/1000,-(p[1]+center[1])/1000) for p in mesh.positions]
        normals=[(n[0],n[2],-n[1]) for n in mesh.normals]
        normals=[tuple(v/math.sqrt(sum(c*c for c in n)) for v in n) for n in normals]
        p=data(positions,3,"VEC3",5126,"f",34962); n=data(normals,3,"VEC3",5126,"f",34962); uv=data(mesh.uvs,2,"VEC2",5126,"f",34962)
        ix=data([(i,) for i in mesh.indices],1,"SCALAR",5125,"I",34963)
        index=len(document["meshes"])
        document["meshes"].append({"name":mesh.name,"primitives":[{"attributes":{"POSITION":p,"NORMAL":n,"TEXCOORD_0":uv},"indices":ix,"mode":4,"material":0}]})
        document["nodes"].append({"name":mesh.name,"mesh":index,"extras":{"visual_revision":REVISION,"collision_authorized":False}})
        pts=[(p[0]*100,p[2]*100,p[1]*100) for p in positions]
        records.append({"id":mesh.name,"role":mesh.role,"triangles":len(mesh.indices)//3,"vertices":len(mesh.positions),
                        "nativeBoundsCm":{"min":[min(p[i] for p in pts) for i in range(3)],"max":[max(p[i] for p in pts) for i in range(3)]},
                        "sourceRelativeVerticesMm":mesh.positions})
    while len(binary)%4: binary.append(0)
    document["buffers"]=[{"byteLength":len(binary)}]
    js=json.dumps(document,separators=(",",":"),allow_nan=False).encode(); js+=b" "*((-len(js))%4)
    raw=struct.pack("<4sII",b"glTF",2,28+len(js)+len(binary))+struct.pack("<II",len(js),0x4e4f534a)+js+struct.pack("<II",len(binary),0x004e4942)+binary
    Path(path).write_bytes(raw)
    return records


def read_glb_positions(path, center):
    raw=Path(path).read_bytes()
    require(raw[:4]==b"glTF" and struct.unpack_from("<II",raw,4)==(2,len(raw)),"Invalid stove GLB header")
    length,kind=struct.unpack_from("<II",raw,12); require(kind==0x4e4f534a,"Invalid stove GLB JSON")
    doc=json.loads(raw[20:20+length]); binary=raw[28+length:]
    require(struct.unpack_from("<II",raw,20+length)==(len(binary),0x004e4942),"Invalid stove GLB BIN")
    result={}
    for node in doc["nodes"]:
        require(not any(key in node for key in ("translation","rotation","scale","matrix","children")),"Stove GLB has an unexpected transform")
        id_=node["name"]; require(id_ not in result,"Duplicate stove GLB node")
        mesh=doc["meshes"][node["mesh"]]; require(mesh["name"]==id_ and len(mesh["primitives"])==1,"Unexpected stove GLB mesh")
        primitive=mesh["primitives"][0]; require(primitive["mode"]==4,"Unexpected stove primitive mode")
        accessor=doc["accessors"][primitive["attributes"]["POSITION"]]; view=doc["bufferViews"][accessor["bufferView"]]
        require(accessor["type"]=="VEC3" and accessor["componentType"]==5126 and not accessor.get("sparse")
                and not accessor.get("normalized") and not view.get("byteStride"),"Unsupported stove GLB positions")
        offset=view.get("byteOffset",0)+accessor.get("byteOffset",0); size=accessor["count"]*12
        require(offset+size<=len(binary),"Stove positions exceed BIN")
        positions=list(struct.iter_unpack("<fff",binary[offset:offset+size]))
        index=doc["accessors"][primitive["indices"]]; iv=doc["bufferViews"][index["bufferView"]]
        require(index["componentType"]==5125 and index["type"]=="SCALAR" and index["count"]==len(positions),"Unexpected stove indices")
        start=iv.get("byteOffset",0)+index.get("byteOffset",0)
        require([v[0] for v in struct.iter_unpack("<I",binary[start:start+index["count"]*4])]==list(range(len(positions))),"Stove topology changed")
        result[id_]=[(x*1000-center[0],-z*1000-center[1],y*1000) for x,y,z in positions]
    return result


def build(directory, output, validate=True):
    directory,output = Path(directory),Path(output)
    scene,records,triangles,center = verify_source(directory)
    meshes,transforms,validation = geometry(triangles,center)
    output.mkdir(parents=True,exist_ok=True)
    glb=output/"stove-visuals.glb"
    derivative=write_glb(meshes,center,glb)
    decoded=read_glb_positions(glb,center)
    maximum_glb_error=max(abs(v-actual) for mesh in meshes for p,q in zip(mesh.positions,decoded[mesh.name]) for v,actual in zip(p,q))
    require(maximum_glb_error<=0.002,"Stove GLB position quantization exceeds 0.002mm")
    actual_meshes=[]
    for original in meshes:
        actual=Mesh(original.name,original.role); actual.positions=decoded[original.name]; actual.indices=original.indices; actual_meshes.append(actual)
    validate_vertices(actual_meshes)
    issues = None
    if validate:
        script="import{readFile}from'node:fs/promises';import{validateBytes}from'gltf-validator';const r=await validateBytes(new Uint8Array(await readFile(process.argv[1])),{maxIssues:0});process.stdout.write(JSON.stringify(r.issues));"
        issues=json.loads(subprocess.check_output(["node","--input-type=module","-e",script,str(glb)],cwd=ROOT,text=True))
        require(issues["numErrors"] == 0 and issues["numWarnings"] == 0 and not issues["truncated"], "Stove GLB failed Khronos validation: "+json.dumps(issues))
    report={"schemaVersion":1,"status":"stove-visual-geometry-validated" if validate else "cpu-fixture-only", "revision":REVISION,
            "sourceManifestSha256":sha(directory/"scene.json"),"sourceObjSha256":sha(directory/"dom-mm.obj"),"generatorSha256":sha(__file__),
            "file":glb.name,"sha256":sha(glb),"sourceRecords":records,"sourceRecordHashes":{k:canonical_hash(v) for k,v in records.items()},
            "hiddenProxyIds":sorted(GUARDS),"preservedSourceIds":sorted(PRESERVED),"stoveAxisSourceMm":center,
            "envelope":{"diameterMm":510,"bottomMm":30,"topMm":1550,"windowBottomMm":430,"windowTopMm":1030,"windowArcDegrees":118,"chamberRadiusMm":245},
            "visualTransforms":transforms,"objects":derivative,"vertexValidation":validation,"maximumGlbPositionErrorMm":maximum_glb_error,"khronosValidation":issues,
            "limitations":["Authored illustrative chamber, char and flame geometry; no measured stove product internals.",
                           "Flames are animated opacity/emission cards, not a physical combustion simulation or calibrated radiometry.",
                           "Canonical source meshes and collision must remain unchanged; native saved/reloaded, Metal motion and 4K cost validation are separate."]}
    (output/"stove-visuals.json").write_text(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False)+"\n")
    return report


if __name__ == "__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--geometry",type=Path,default=ROOT/"output/unreal/geometry")
    parser.add_argument("--output",type=Path,default=ROOT/"output/unreal/stove-visuals")
    args=parser.parse_args()
    result=build(args.geometry,args.output)
    print(json.dumps({"status":result["status"],"objects":len(result["objects"]),"triangles":sum(o["triangles"] for o in result["objects"]),"khronos":result["khronosValidation"]}))
