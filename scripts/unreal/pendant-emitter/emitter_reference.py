"""CPU source/photometric contract for one outward opaque pendant emitter."""
import copy
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "lib/twin-site.ts").is_file())
ID = "DOM_01375"
SLOT = "MAT_0046"
SOURCE_ID = "LIVING-103-DINING · centrálne závesné svietidlo · 2700 K difúzor"
SCENE_SHA = "61ba228f4b72a5ee5fc754e60e112ff70d03605f8cf56fec97bccc3519b8863b"
OBJ_SHA = "a42e9eb169d929bc67056ad21bf3885e3f1a32838f15c328cb98bacd008fa455"
AREA_M2 = 0.12528184603012782
FLUX_LM = 800.0
CCT_K = 2700.0
Y_WEIGHTS = (.2126, .7152, .0722)
CHROMATICITIES = {"red": (.64, .33), "green": (.30, .60), "blue": (.15, .06), "white": (.3127, .3290)}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()).hexdigest()


def dot(a, b):
    return sum(x*y for x, y in zip(a, b))


def cross(a, b):
    return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])


def source_triangles(path):
    positions, triangles, current, slot, occurrences = [], [], None, None, 0
    for line in Path(path).read_text().splitlines():
        fields = line.split()
        if not fields:
            continue
        if fields[0] == "v":
            p = tuple(map(float, fields[1:]))
            require(len(p) == 3 and all(math.isfinite(v) for v in p), "Invalid OBJ position")
            positions.append(p)
        elif fields[0] == "o":
            current, slot = fields[1], None
            occurrences += current == ID
        elif fields[0] == "usemtl":
            slot = fields[1]
        elif fields[0] == "f" and current == ID:
            require(len(fields) == 4 and slot == SLOT, "Pendant OBJ face/material differs")
            indices = [int(value.split("/")[0]) for value in fields[1:]]
            require(all(0 < i <= len(positions) for i in indices), "Unsupported OBJ index")
            triangles.append(tuple(positions[i-1] for i in indices))
    require(occurrences == 1 and len(triangles) == 2704, "Exact source pendant geometry missing")
    return triangles


def geometry_metrics(triangles, bounds):
    """Source mm triangles; retain zero-area poles in the count, not flux/edges."""
    center = tuple((a+b)/2 for a, b in zip(bounds["min"], bounds["max"]))
    edges, faces, vertices = Counter(), Counter(), set()
    area, zeros, outward = 0.0, 0, 0
    for triangle in triangles:
        require(len(triangle) == 3, "Nontriangular emitter")
        require(all(len(p) == 3 and all(math.isfinite(v) for v in p) for p in triangle), "Nonfinite emitter geometry")
        require(all(bounds["min"][axis]-.000002 <= p[axis] <= bounds["max"][axis]+.000002 for p in triangle for axis in range(3)), "Emitter vertex escaped source envelope")
        a, b, c = triangle
        n = cross(tuple(b[i]-a[i] for i in range(3)), tuple(c[i]-a[i] for i in range(3)))
        triangle_area = math.sqrt(dot(n, n))/2
        if triangle_area < 1e-7:
            zeros += 1
            continue
        require(dot(n, tuple(sum(p[i] for p in triangle)/3-center[i] for i in range(3))) > 0, "Emitter triangle is not outward")
        outward += 1
        area += triangle_area / 1e6
        keys = [tuple(round(v, 5) for v in p) for p in triangle]
        vertices.update(keys)
        faces[tuple(sorted(keys))] += 1
        for i in range(3):
            edges[tuple(sorted((keys[i], keys[(i+1) % 3])))] += 1
    require(bool(edges) and all(n == 2 for n in edges.values()), "Emitter is not closed after 0.00001 mm positional weld")
    require(all(n == 1 for n in faces.values()), "Duplicated emitting surface")
    return {"surfaceAreaM2": area, "triangles": len(triangles), "zeroAreaPoleTriangles": zeros,
            "outwardNondegenerateTriangles": outward, "weldedVertices": len(vertices), "weldedEdges": len(edges),
            "closedAfterPositionWeld": True, "weldPrecisionMm": .00001}


def temperature_rgb(temperature):
    """UE5.8 Color.cpp MakeFromColorTemperature polynomial, double CPU reference."""
    require(math.isfinite(temperature) and 1000 <= temperature <= 15000, "Unsupported CCT")
    t = temperature
    u = (.860117757 + 1.54118254e-4*t + 1.28641212e-7*t*t)/(1 + 8.42420235e-4*t + 7.08145163e-7*t*t)
    v = (.317398726 + 4.22806245e-5*t + 4.20481691e-8*t*t)/(1 - 2.89741816e-5*t + 1.61456053e-7*t*t)
    x, y = 3*u/(2*u-8*v+4), 2*v/(2*u-8*v+4)
    X, Y, Z = x/y, 1.0, (1-x-y)/y
    return tuple(max(0, dot(row, (X, Y, Z))) for row in ((3.2404542,-1.5371385,-.4985314),(-.9692660,1.8760108,.0415560),(.0556434,-.2040259,1.0572252)))


def photometry(area_m2, flux_lm=FLUX_LM, cct_k=CCT_K):
    require(math.isfinite(area_m2) and area_m2 > 0 and math.isfinite(flux_lm) and flux_lm >= 0, "Invalid Lambertian source power/area")
    rgb = temperature_rgb(cct_k)
    normalized = tuple(c/dot(rgb, Y_WEIGHTS) for c in rgb)
    luminance = flux_lm / (math.pi*area_m2)
    emission = tuple(c*luminance for c in normalized)
    return {"authoredIntrinsicFluxLumens": flux_lm, "fluxIsVendorMeasured": False,
            "fluxDefinition": "Entire outward globe before opaque source shade occlusion; not delivered fixture lumens",
            "surfaceAreaM2": area_m2, "luminanceCdPerM2": luminance, "sourceLabelCctK": cct_k,
            "luminanceWeightsRGB": list(Y_WEIGHTS), "colorNormalizedToY1": list(normalized), "emissionRGB": list(emission),
            "reconstructedFluxLumens": math.pi*area_m2*dot(emission, Y_WEIGHTS), "dayNightSamePower": True}


def verify_working_space(choice_value, chromaticities):
    # Native enum integer is declared EWorkingColorSpace::sRGB=1; avoid Python enum-name guesses.
    require(choice_value == 1, "Pendant requires sRGB/BT.709 working space, not a custom/wide-gamut setting")
    require(set(chromaticities) == set(CHROMATICITIES), "Incomplete native working color space readback")
    require(all(len(chromaticities[k]) == 2 and all(math.isfinite(a) and abs(a-b) <= 1e-6 for a,b in zip(chromaticities[k], expected)) for k,expected in CHROMATICITIES.items()), "BT.709/D65 native chromaticities differ or were not initialized")


def verify_inputs(scene, geometry_dir):
    directory = Path(geometry_dir)
    require(sha(directory/"scene.json") == SCENE_SHA and sha(directory/"dom-mm.obj") == OBJ_SHA, "Pendant source scene/OBJ pin drift")
    require(scene == json.loads((directory/"scene.json").read_text()), "Caller scene differs from pinned source")
    records = {r["id"]:r for r in scene["objects"]}
    require(len(records) == len(scene["objects"]), "Duplicate source object IDs")
    r = records[ID]
    require(r["sourceId"] == SOURCE_ID and r["materialSlots"] == [SLOT] and r["materialNames"] == ["real-interior-warm-light"] and r["triangles"] == 2704 and r["enabled"] and r["instances"] == 1, "Pendant exact source identity differs")
    require(r["metadata"]["babylonCheckCollisions"] is False, "Source pendant gained collision")
    require(all(abs(b-a-200) < 1e-8 for a,b in zip(r["boundsMm"]["min"],r["boundsMm"]["max"])), "Source globe is not 200 mm")
    metrics = geometry_metrics(source_triangles(directory/"dom-mm.obj"), r["boundsMm"])
    require(abs(metrics["surfaceAreaM2"]-AREA_M2) < 1e-12 and metrics["zeroAreaPoleTriangles"] == 104 and metrics["outwardNondegenerateTriangles"] == 2600 and metrics["weldedVertices"] == 1302 and metrics["weldedEdges"] == 3900, "Source emitting surface metric differs")
    warm_ids = {r["id"] for r in scene["objects"] if SLOT in r["materialSlots"]}
    require(len(warm_ids) == 29 and ID in warm_ids, "Shared warm-material scope differs")
    return {"scene":scene, "record":r, "protectedIds":sorted(warm_ids | {"DOM_01373","DOM_01374"}),
            "sourceRecordSha256":digest(r), "geometry":metrics, "photometry":photometry(metrics["surfaceAreaM2"])}


def expected_components(before, material_path=None, restored=None):
    result = copy.deepcopy(before)
    require(ID in result, "Selected native component missing")
    if restored is None:
        require(isinstance(material_path,str) and material_path.startswith("/Game/Brezi/MaterialStudies/PendantEmitter/"), "Foreign candidate material")
        result[ID].update(effectiveMaterial=material_path, overrides=[material_path], emissiveLightSource=True)
    else:
        validate_prior(restored)
        values = restored["overrides"]
        result[ID].update(effectiveMaterial=values[0] if values and values[0] else result[ID]["meshMaterial"], overrides=values, emissiveLightSource=restored["emissiveLightSource"])
    return result


def validate_prior(prior):
    require(isinstance(prior,dict) and set(prior) == {"overrides","emissiveLightSource"}, "Invalid retained pendant state")
    require(type(prior["emissiveLightSource"]) is bool and isinstance(prior["overrides"],list) and len(prior["overrides"]) <= 1, "Invalid retained flag/slot count")
    require(all(p is None or isinstance(p,str) and p.startswith("/") and len(p) > 1 for p in prior["overrides"]), "Invalid retained material reference")
