"""Source and coordinate contract for a three-object photographed oak study. CPU only."""
import hashlib
import json
import math
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "lib/twin-site.ts").is_file())
STUDY = ROOT / "output/unreal/wood-study"
GEOMETRY = ROOT / "output/unreal/geometry"
SCENE_SHA = "61ba228f4b72a5ee5fc754e60e112ff70d03605f8cf56fec97bccc3519b8863b"
OBJ_SHA = "a42e9eb169d929bc67056ad21bf3885e3f1a32838f15c328cb98bacd008fa455"
IDS = frozenset({"DOM_01293", "DOM_01296", "DOM_01300"})
RECORD_HASHES = {
    "DOM_01293": "534ac4a7318a46ec5c5a1ba45c843fc1beca69bcaf94c7dab7c2f45019a98039",
    "DOM_01296": "6d46a6fe02db85d661666b15c50ca5be5f311dbf5deff51ed665344ceefab1d7",
    "DOM_01300": "a3fe5c37765dc4aa1fff4e829590c200a4f7013dc8796150ac5fdae1ba25ec5b",
    "DOM_01326": "1b2aed1d49513c9bb78b7c8932f049f74c9399973ba865394561afbb51f5cade",
}
MATERIAL_SHA = "b48bccf5dc0432fd439e42caf04e62359d67025c7e2fd605f99b3ca9a5e9a127"
WOOD_SLOTS = frozenset({"MAT_0064", "MAT_0031", "MAT_0080", "MAT_0078", "MAT_0065", "MAT_0039"})
WOOD_IDS_SHA = "0268168d9a9326406de7918f282cf67076e3d1a061a625f48e7deea43945448a"
FILES = {
    "candidate.json": "cc55af12711bf8217ac391ac2546239794cb7858a20c4c8348b4d2d5a5876122",
    "material-study.json": "b167181d574ad4c67e87c56cc4fa285728f92bb013e6cfe78ea5809cdf5a6408",
    "source-uv-metric.json": "29fe76ec660d485b4dd17dea0cef960956200c0e615dcc7d413c72a29b455686",
}
MAP_HASHES = {
    "Diffuse": "7e8c64811e580ef6664c20524606359c739e6fe030eff5c2c06c3482ecc8b1cf",
    "nor_gl": "e9bb26f63682773895ce3f0dfd9a43554a719c4caae65b6bcf41712ecfaf3d26",
    "Rough": "3e7eb00705c173babfc01443de1ed1e8d40d055b97de278a6e817b65e8decb38",
}
PERIOD_CM = 183.00000429153442
PALETTE = (1.4281032377635254, 1.4204015551734712, 1.3308024765112707)
ROUGH_MEAN = 0.5304041633418962
ROUGH_AMPLITUDE = 0.12
NORMAL_STRENGTH = 0.25


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def normalize(v):
    length = math.sqrt(dot(v, v))
    require(length > 0 and math.isfinite(length), "Invalid source normal")
    return tuple(x / length for x in v)


def basis(normal):
    n = normalize(normal)
    require(sum(abs(v) > 1e-8 for v in n) == 1, "Only guarded axis-aligned cabinet faces are supported")
    axis = max(range(3), key=lambda i: abs(n[i]))
    sign = 1 if n[axis] > 0 else -1
    if axis == 0:
        t, v = (0, -sign, 0), (0, 0, -1)
    elif axis == 1:
        t, v = (sign, 0, 0), (0, 0, -1)
    else:
        t, v = (0, sign, 0), (-1, 0, 0)
    require(cross(t, v) == n, "Projection basis does not follow the source outward normal")
    return t, v, n


def project(position_cm, normal, anchor_cm):
    t, v, _ = basis(normal)
    p = tuple(x - a for x, a in zip(position_cm, anchor_cm))
    return dot(p, t) / PERIOD_CM, dot(p, v) / PERIOD_CM


def projected_normal(gl_normal, normal, strength=NORMAL_STRENGTH):
    """Normal sampler decodes BC5 after GL→DX green flip; explicit world T/V/N."""
    t, v, n = basis(normal)
    dx = (gl_normal[0], -gl_normal[1], gl_normal[2])
    return normalize(tuple(t[i]*dx[0]*strength + v[i]*dx[1]*strength + n[i]*max(dx[2], .001) for i in range(3)))


def jpeg_size(data):
    require(data[:2] == b"\xff\xd8", "Candidate is not a JPEG")
    i = 2
    while i + 4 <= len(data):
        require(data[i] == 255, "Invalid JPEG marker")
        while data[i] == 255:
            i += 1
        marker = data[i]; i += 1
        if marker in (0xD8, 0xD9) or 0xD0 <= marker <= 0xD7:
            continue
        length = int.from_bytes(data[i:i+2], "big")
        require(length >= 2 and i + length <= len(data), "Truncated JPEG segment")
        if marker in (0xC0, 0xC1, 0xC2):
            return int.from_bytes(data[i+5:i+7], "big"), int.from_bytes(data[i+3:i+5], "big")
        i += length
    raise ValueError("JPEG dimensions are missing")


def read_boxes(path, records, ids=IDS, expected_slots=None):
    selected=frozenset(ids)
    require(bool(selected), "No selected source boxes")
    slots=expected_slots if expected_slots is not None else {id_:"MAT_0078" for id_ in selected}
    require(set(slots)==selected,"Source box material scope differs")
    positions, normals, found, current, slot = [], [], {}, None, None
    for line in Path(path).read_text().splitlines():
        f = line.split()
        if not f:
            continue
        if f[0] == "o":
            current, slot = f[1], None
            if current in selected:
                require(current not in found, "Duplicate selected OBJ object")
                found[current] = []
        elif f[0] == "usemtl":
            slot = f[1]
        elif f[0] == "v":
            positions.append(tuple(map(float, f[1:])))
        elif f[0] == "vn":
            normals.append(tuple(map(float, f[1:])))
        elif f[0] == "f" and current in selected:
            require(len(f) == 4 and slot == slots[current], "Selected OBJ triangle/material changed")
            indices = [tuple(int(x) for x in ref.split("/")) for ref in f[1:]]
            p = [positions[index[0]-1] for index in indices]
            ns = [normals[index[2]-1] for index in indices]
            require(all(len(v) == 3 and all(math.isfinite(x) for x in v) for v in p + ns), "Nonfinite source triangle")
            require(all(n == ns[0] for n in ns), "Smoothed cabinet source normals are unsupported")
            n = ns[0]
            basis((n[0], -n[1], n[2]))
            require(all(abs(dot(n, tuple(q[i]-p[0][i] for i in range(3)))) < 1e-7 for q in p), "Source face and normal disagree")
            bounds = records[current]["boundsMm"]
            require(all(all(min(abs(point[i]-bounds["min"][i]), abs(point[i]-bounds["max"][i])) < .001 for i in range(3)) for point in p), "Source cabinet is no longer the guarded box")
            found[current].append({"positionsMm": p, "normalSite": n})
    require(found.keys() == selected, "Missing selected source geometry")
    for id_, triangles in found.items():
        require(len(triangles) == 12, "Expected twelve source cabinet triangles")
        counts = {}
        for t in triangles:
            n = tuple(t["normalSite"]); counts[n] = counts.get(n, 0) + 1
        require(len(counts) == 6 and set(counts.values()) == {2}, "Expected exactly two triangles on each of six source faces")
    return found


def verify_inputs(scene=None, geometry=GEOMETRY, study=STUDY):
    geometry, study = Path(geometry), Path(study)
    require(sha(geometry/"scene.json") == SCENE_SHA and sha(geometry/"dom-mm.obj") == OBJ_SHA, "Pinned canonical scene/OBJ bytes changed")
    loaded = json.loads((geometry/"scene.json").read_text())
    require(scene is None or digest(scene) == digest(loaded), "Supplied scene differs from pinned source")
    require(loaded["objSha256"] == OBJ_SHA, "Scene OBJ binding changed")
    records = {o["id"]: o for o in loaded["objects"]}
    require(len(records) == len(loaded["objects"]), "Duplicate canonical IDs")
    require(digest(loaded["materials"]["MAT_0078"]) == MATERIAL_SHA, "Source cabinet finish changed")
    for id_, value in RECORD_HASHES.items():
        require(id_ in records and digest(records[id_]) == value, "Pinned object/source ID or geometry changed: " + id_)
    require({o["id"] for o in loaded["objects"] if "MAT_0078" in o["materialSlots"]} == RECORD_HASHES.keys(), "Shared cabinet/oval material scope changed")
    wood = [o["id"] for o in loaded["objects"] if any(slot in WOOD_SLOTS for slot in o["materialSlots"])]
    require(len(wood) == 158 and digest(wood) == WOOD_IDS_SHA, "Existing six-slot wood scope changed")
    for file, expected in FILES.items():
        require(sha(study/file) == expected, "Pinned study input changed: " + file)
    candidate = json.loads((study/"candidate.json").read_text())
    require(candidate["dimensionsMillimetres"] == [PERIOD_CM*10]*2 and candidate["license"] == "CC0-1.0", "Candidate physical period/license binding changed")
    for role, expected in MAP_HASHES.items():
        spec = candidate["maps"][role]
        path = ROOT/spec["path"]
        require(path.parent == study and spec["sha256"] == expected, "Candidate map escaped its pinned path")
        data = path.read_bytes()
        require(hashlib.sha256(data).hexdigest() == expected and hashlib.md5(data).hexdigest() == spec["md5"]
                and len(data) == spec["size"] and jpeg_size(data) == (4096,4096), "Photographed candidate bytes/dimensions changed: " + role)
    boxes = read_boxes(geometry/"dom-mm.obj", records)
    anchor = (min(records[i]["boundsMm"]["min"][0] for i in IDS)/10,
              -max(records[i]["boundsMm"]["max"][1] for i in IDS)/10,
              min(records[i]["boundsMm"]["min"][2] for i in IDS)/10)
    return {"scene": loaded, "records": records, "woodIds": wood, "boxes": boxes, "anchorCm": anchor,
            "candidate": candidate, "sourceRoughness": .74, "selectedIds": sorted(IDS), "preservedWoodObjects": len(wood)-len(IDS)}
