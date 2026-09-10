"""Verified CC0 plant prototypes; Blender CPU data conversion only, never render.

/Applications/Blender.app/Contents/MacOS/Blender --background --factory-startup \
  --disable-autoexec --python scripts/unreal/vegetation-convert.py

Loads only 4 shrub LOD1 and 12 small/medium Bermuda mesh objects from locked
model libraries. Bakes existing object rotation/scale, centres the footprint and
puts its lowest vertex at Z=0; no decimation or invented leaf cards. Source .blend
files are never saved. All output stays below output/unreal/vegetation-prototypes.
"""

import argparse
import hashlib
import json
import math
import os
import random
from pathlib import Path
import shutil
import struct
import subprocess
import sys

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(Path(__file__).resolve().parent))
from vegetation import audit_assets, digest, require, hedge_source_components

ASSETS = ROOT / "output/archviz/assets"
LOCK = ROOT / "scripts/archviz/assets.lock.json"
NAMES = {
    "shrub_02": [f"shrub_02_{letter}_LOD1" for letter in "abcd"],
    "grass_bermuda_01": [f"grass_bermuda_01_{size}_{letter}" for size in ("small", "medium") for letter in "abcdef"],
}


def save_json(path, data):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(data, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    temporary.replace(path)


def texture_maps(asset_id, output):
    """Re-encode EXR data maps without film/color transforms; keep albedo/alpha bytes."""
    lock = json.loads(LOCK.read_text())["models"][asset_id]
    roles = {"albedo": "_diff_", "alpha": "_alpha_", "normal": "_nor_gl_", "roughness": "_rough_"}
    maps = {}
    for role, suffix in roles.items():
        entries = [e for e in lock["include"].values() if suffix in Path(e["path"]).name]
        require(len(entries) == 1, "Ambiguous model texture role: " + asset_id + "/" + role)
        source = ASSETS / entries[0]["path"]
        destination = output / "textures" / (asset_id + "_" + role + (".png" if source.suffix == ".exr" else source.suffix))
        destination.parent.mkdir(exist_ok=True)
        conversion_error = 0.0
        if source.suffix == ".exr":
            import numpy as np
            image = bpy.data.images.load(str(source), check_existing=False)
            image.colorspace_settings.name = "Non-Color"
            original = np.empty(len(image.pixels), dtype=np.float32)
            image.pixels.foreach_get(original)
            image.filepath_raw, image.file_format = str(destination), "PNG"
            image.save()
            decoded = bpy.data.images.load(str(destination), check_existing=False)
            decoded.colorspace_settings.name = "Non-Color"
            pixels = np.empty(len(decoded.pixels), dtype=np.float32)
            decoded.pixels.foreach_get(pixels)
            require(len(original) == len(pixels), "Data texture dimensions changed")
            conversion_error = float(np.max(np.abs(np.clip(original, 0, 1) - pixels)))
            require(conversion_error <= 1 / 255 + 0.00001, "Non-color texture re-encoding changed values")
            bpy.data.images.remove(image)
            bpy.data.images.remove(decoded)
        else:
            shutil.copyfile(source, destination)
            require(digest(source) == digest(destination), "Texture copy differs")
        image = bpy.data.images.load(str(destination), check_existing=False)
        image.colorspace_settings.name = "sRGB" if role == "albedo" else "Non-Color"
        maps[role] = {"path": str(destination.relative_to(output)), "sha256": digest(destination),
                      "sourcePath": entries[0]["path"], "sourceSha256": digest(source),
                      "role": role, "colorSpace": "sRGB" if role == "albedo" else "linear",
                      "size": list(image.size), "maxLinearReencodingError": conversion_error}
        if role == "alpha":
            samples = list(image.pixels)[::4]
            maps[role]["range"] = [min(samples), max(samples)]
            require(min(samples) < 0.01 and max(samples) > 0.99, "Expected nonempty alpha silhouette")
        bpy.data.images.remove(image)
    return maps


def make_material(asset_id, maps, output):
    material = bpy.data.materials.new("VEG_" + asset_id)
    material.use_nodes = True
    material.surface_render_method = "DITHERED"
    material.use_backface_culling = False
    material.diffuse_color = (1, 1, 1, 1)
    nodes, links = material.node_tree.nodes, material.node_tree.links
    nodes.clear()
    shader, surface = nodes.new("ShaderNodeBsdfPrincipled"), nodes.new("ShaderNodeOutputMaterial")
    links.new(shader.outputs["BSDF"], surface.inputs["Surface"])
    shader.inputs["Metallic"].default_value = 0
    for role, record in maps.items():
        image = bpy.data.images.load(str(output / record["path"]), check_existing=False)
        image.colorspace_settings.name = "sRGB" if role == "albedo" else "Non-Color"
        texture = nodes.new("ShaderNodeTexImage")
        texture.image = image
        if role == "normal":
            normal = nodes.new("ShaderNodeNormalMap")
            normal.inputs["Strength"].default_value = 1
            links.new(texture.outputs["Color"], normal.inputs["Color"])
            links.new(normal.outputs["Normal"], shader.inputs["Normal"])
        else:
            links.new(texture.outputs["Color"], shader.inputs[{"albedo": "Base Color", "alpha": "Alpha", "roughness": "Roughness"}[role]])
    return material


def parse_glb(path):
    data = path.read_bytes()
    require(data[:4] == b"glTF" and struct.unpack_from("<II", data, 4) == (2, len(data)), "Invalid GLB header")
    length, kind = struct.unpack_from("<II", data, 12)
    require(kind == 0x4E4F534A, "Missing GLB JSON")
    document = json.loads(data[20:20 + length])
    offset = 20 + length
    binary_length, kind = struct.unpack_from("<II", data, offset)
    require(kind == 0x004E4942, "Missing GLB binary buffer")
    return document, data[offset + 8:offset + 8 + binary_length]


def write_masked_glb(path):
    document, binary = parse_glb(path)
    binary = bytearray(binary)
    repaired = 0
    # A clipping intersection can leave an undefined tangent at a collapsed UV
    # derivative. Keep geometry/UV intact and provide a valid orthogonal basis.
    for mesh in document["meshes"]:
        for primitive in mesh["primitives"]:
            attrs = primitive["attributes"]
            if "TANGENT" not in attrs:
                continue
            tangents = accessor(document, binary, attrs["TANGENT"])
            normals = accessor(document, binary, attrs["NORMAL"])
            record = document["accessors"][attrs["TANGENT"]]
            view = document["bufferViews"][record["bufferView"]]
            offset = view.get("byteOffset", 0) + record.get("byteOffset", 0)
            stride = view.get("byteStride", 16)
            for index, tangent in enumerate(tangents):
                if sum(v*v for v in tangent[:3]) > 0.000001:
                    continue
                normal = Vector(normals[index])
                require(normal.length > 0.99, "Cannot repair tangent without a valid normal")
                axis = Vector((1, 0, 0)) if abs(normal.x) < 0.8 else Vector((0, 1, 0))
                replacement = (axis-normal*normal.dot(axis)).normalized()
                struct.pack_into("<ffff", binary, offset+index*stride, *replacement, tangent[3])
                repaired += 1
    document["asset"].setdefault("extras", {})["breziZeroTangentRepairs"] = repaired
    for material in document["materials"]:
        material.update(alphaMode="MASK", alphaCutoff=0.45, doubleSided=True)
    payload = json.dumps(document, separators=(",", ":"), ensure_ascii=False).encode()
    payload += b" " * (-len(payload) % 4)
    binary += b"\0" * (-len(binary) % 4)
    data = struct.pack("<4sII", b"glTF", 2, 12 + 8 + len(payload) + 8 + len(binary))
    data += struct.pack("<II", len(payload), 0x4E4F534A) + payload
    data += struct.pack("<II", len(binary), 0x004E4942) + binary
    path.write_bytes(data)
    return repaired


def validate_glb(path):
    """Actual local Khronos validator, no browser/renderer/network."""
    code = """import{readFile}from'node:fs/promises';import{validateBytes}from'gltf-validator';
const r=await validateBytes(new Uint8Array(await readFile(process.argv[1])),{maxIssues:0});
console.log(JSON.stringify(r.issues));if(r.issues.numErrors||r.issues.numWarnings)process.exitCode=1;"""
    process = subprocess.run([shutil.which("node") or "node", "--input-type=module", "-e", code, str(path)],
                             cwd=ROOT, capture_output=True, text=True, check=False)
    require(process.returncode == 0, "Khronos glTF validation failed: " + process.stdout + process.stderr)
    issues = json.loads(process.stdout)
    require(not issues["truncated"], "Khronos issue output was truncated")
    return issues


def accessor(document, binary, index):
    record = document["accessors"][index]
    require("sparse" not in record, "Sparse prototype accessor unsupported")
    view = document["bufferViews"][record["bufferView"]]
    component = {5121: "B", 5123: "H", 5125: "I", 5126: "f"}[record["componentType"]]
    components = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[record["type"]]
    stride = view.get("byteStride", struct.calcsize(component) * components)
    offset = view.get("byteOffset", 0) + record.get("byteOffset", 0)
    values = [struct.unpack_from("<" + component * components, binary, offset + i * stride) for i in range(record["count"])]
    require(all(all(math.isfinite(v) for v in row) for row in values), "Non-finite GLB data")
    return values


def export_object(source, asset_id, material, output):
    require(source.type == "MESH" and not source.modifiers and not source.constraints and not source.parent,
            "Prototype needs reviewed evaluation policy: " + source.name)
    obj = source.copy()
    obj.data = source.data.copy()
    bpy.context.scene.collection.objects.link(obj)
    # Remove model-library display translation; preserve its actual rotation/scale.
    matrix = source.matrix_world.to_3x3().to_4x4()
    obj.data.transform(matrix)
    points = [v.co.copy() for v in obj.data.vertices]
    lo, hi = [min(p[i] for p in points) for i in range(3)], [max(p[i] for p in points) for i in range(3)]
    pivot = Vector(((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, lo[2]))
    obj.data.transform(Matrix.Translation(-pivot))
    obj.matrix_world = Matrix.Identity(4)
    obj.name = source.name + "_ROOT"
    obj.data.materials.clear()
    obj.data.materials.append(material)
    for face in obj.data.polygons:
        face.material_index = 0
    require(obj.data.uv_layers.active is not None, "No source UVs: " + source.name)
    uv = [tuple(loop.uv) for loop in obj.data.uv_layers.active.data]
    require(uv and all(all(math.isfinite(v) for v in pair) for pair in uv), "Invalid source UVs")
    obj.data.calc_loop_triangles()
    triangles = len(obj.data.loop_triangles)
    vertices = [tuple(float(v) for v in p.co) for p in obj.data.vertices]
    bounds = {"min": [min(p[i] for p in vertices) for i in range(3)],
              "max": [max(p[i] for p in vertices) for i in range(3)]}
    require(0 < bounds["max"][2] < 5 and min(bounds["min"][0:2]) > -5, "Unexpected prototype physical scale")
    obj["source_asset"] = asset_id
    obj["source_object"] = source.name
    obj["license"] = "CC0-1.0"
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    destination = output / (source.name + ".glb")
    bpy.ops.export_scene.gltf(filepath=str(destination), export_format="GLB", use_selection=True,
                              export_yup=True, export_normals=True, export_tangents=True,
                              export_texcoords=True, export_materials="EXPORT", export_animations=False,
                              export_extras=True, export_apply=False)
    repaired_tangents = write_masked_glb(destination)
    document, binary = parse_glb(destination)
    require(len(document["nodes"]) == 1 and len(document["meshes"]) == 1, "Prototype export swallowed extra objects")
    require(all(k not in document["nodes"][0] for k in ("matrix", "rotation", "translation", "scale")), "Unbaked GLB transform")
    primitive = document["meshes"][0]["primitives"]
    require(len(primitive) == 1, "Expected one source foliage material")
    attributes = primitive[0]["attributes"]
    require(all(k in attributes for k in ("POSITION", "NORMAL", "TEXCOORD_0", "TANGENT")), "UV/normal/tangent data lost")
    positions = accessor(document, binary, attributes["POSITION"])
    texcoords = accessor(document, binary, attributes["TEXCOORD_0"])
    indices = accessor(document, binary, primitive[0]["indices"])
    require(len(indices) == triangles * 3, "Triangle geometry changed during export")
    expected = [(p[0], p[2], -p[1]) for p in vertices]
    error = max(abs(fn(p[i] for p in positions) - fn(p[i] for p in expected)) for i in range(3) for fn in (min, max))
    require(error < 1e-5, "GLB bounds roundtrip exceeds 0.01mm")
    expected_uv = [(u, 1 - v) for u, v in uv]
    uv_error = max(abs(fn(p[i] for p in texcoords) - fn(p[i] for p in expected_uv)) for i in range(2) for fn in (min, max))
    require(uv_error < 1e-5, "Source UV0 range changed")
    require(document["materials"][0]["alphaMode"] == "MASK" and document["materials"][0]["doubleSided"], "Alpha material lost")
    result = {"id": source.name, "assetId": asset_id, "sourceObject": source.name,
              "file": destination.name, "sha256": digest(destination), "bytes": destination.stat().st_size,
              "units": "metres", "axes": "glTF [sourceX,sourceZ,-sourceY]; UE cm [100X,-100Y,100Z]",
              "rootConvention": "source object rotation/scale baked; XY footprint centre; lowest vertex Z=0",
              "sourceRotationScale": [list(row) for row in matrix], "pivotBeforeRootingMetres": list(pivot),
              "boundsSourceZUpMetres": bounds, "verticesSourceZUpMetres": vertices,
              "triangles": triangles, "exportedVertices": len(positions), "maxBoundsErrorMm": error * 1000,
              "uv0MaxRangeError": uv_error, "alphaMode": "MASK", "alphaCutoff": 0.45, "doubleSided": True}
    result["zeroTangentRepairs"] = repaired_tangents
    result["khronosValidation"] = validate_glb(destination)
    bpy.data.objects.remove(obj, do_unlink=True)
    print("BREZI_PLANT_EXPORTED " + json.dumps({"id": result["id"], "triangles": triangles, "bounds": bounds}), flush=True)
    return result


def export_hedge_detail(report, output, geometry):
    """Two clipped scanned crown layers; exact original convex proxy containment.

    This is illustrative clipped hedge detail, not 306 newly planted shrubs.
    Eight spatial batches retain all 153 component identities in their receipt.
    """
    import bmesh
    import numpy as np
    scene = json.loads((geometry / "scene.json").read_text())
    patch, crowns = hedge_source_components(scene, geometry / "dom-mm.obj")
    source = bpy.data.objects["shrub_02_a_LOD1"]
    prototype = next(p for p in report["prototypes"] if p["id"] == source.name)
    material = bpy.data.materials["VEG_shrub_02"]
    base = source.data.copy()
    base.transform(source.matrix_world.to_3x3().to_4x4())
    base.transform(Matrix.Translation(-Vector(prototype["pivotBeforeRootingMetres"])))
    base.materials.clear()
    base.materials.append(material)
    alpha = bpy.data.images.load(str(output / report["models"]["shrub_02"]["textures"]["alpha"]["path"]), check_existing=False)
    alpha.colorspace_settings.name = "Non-Color"
    pixels = np.empty(len(alpha.pixels), dtype=np.float32)
    alpha.pixels.foreach_get(pixels)
    pixels = pixels.reshape(alpha.size[1], alpha.size[0], 4)
    uv = base.uv_layers.active.data
    opaque = []
    for loop in base.loops:
        u, v = uv[loop.index].uv
        x, y = min(alpha.size[0]-1, max(0, int(u*alpha.size[0]))), min(alpha.size[1]-1, max(0, int(v*alpha.size[1])))
        if pixels[y, x, 0] >= 0.7:
            opaque.append(base.vertices[loop.vertex_index].co.copy())
    require(opaque, "No opaque source foliage vertices")
    peak = max(opaque, key=lambda p: p.z)
    chunks, crown_receipts = {}, []
    run_a, run_b = patch["canonicalRun"]["pointsMm"]
    origin = Vector((run_a["x"]-scene["sceneCenterMm"]["x"], run_a["y"]-scene["sceneCenterMm"]["y"], 0))
    direction = Vector((run_b["x"]-run_a["x"], run_b["y"]-run_a["y"], 0)).normalized()
    for index, crown in enumerate(crowns):
        center = Vector(crown["centerMm"]) / 1000
        lo, hi = crown["boundsMm"]["min"], crown["boundsMm"]["max"]
        rng = random.Random(crown["id"] + "/601226")
        bm = bmesh.new()
        for layer in range(2):
            rotation = Matrix.Rotation(rng.uniform(-math.pi, math.pi), 4, "Z")
            scale = rng.uniform(0.76, 0.84)  # uniform, actual leaf proportions retained
            transformed_peak = rotation @ (peak * scale)
            if layer == 1:
                location = Vector((center.x-transformed_peak.x, center.y-transformed_peak.y,
                                   hi[2]/1000-0.006-transformed_peak.z))
            else:
                location = Vector((center.x, center.y, lo[2]/1000-0.02))
            part = base.copy()
            part.transform(Matrix.Translation(location) @ rotation @ Matrix.Scale(scale, 4))
            bm.from_mesh(part)
            bpy.data.meshes.remove(part)
        # Crop to the exact existing convex volume; no caps on cut leaf surfaces.
        planes = [(Vector(p[:3]), p[3]/1000) for p in crown["planesMm"]]
        for axis in range(3):
            n = Vector((0, 0, 0)); n[axis] = 1
            planes.insert(0, (n, hi[axis]/1000))
            planes.insert(0, (-n, -lo[axis]/1000))
        for normal, distance in planes:
            if not bm.verts:
                break
            if max(normal.dot(v.co)-distance for v in bm.verts) <= 0.000001:
                continue
            bmesh.ops.bisect_plane(bm, geom=list(bm.verts)+list(bm.edges)+list(bm.faces),
                                  plane_co=normal*distance, plane_no=normal, dist=0.0000001,
                                  clear_outer=True, clear_inner=False)
        require(bm.faces, "Source crown clipping produced no foliage")
        bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
        bmesh.ops.triangulate(bm, faces=list(bm.faces))
        # UE StaticMeshBuilder always drops identical float32-centimetre corner
        # pairs, even when bRemoveDegenerates=false. Remove exactly those clipping
        # slivers here, before the coverage/volume/triangle receipts are computed.
        native_points = {v: tuple(float(np.float32(np.float32(c)*np.float32(100))) for c in v.co) for v in bm.verts}
        collapsed = [f for f in bm.faces if len({native_points[v] for v in f.verts}) < 3]
        collapsed_count = len(collapsed)
        if collapsed:
            bmesh.ops.delete(bm, geom=collapsed, context="FACES_ONLY")
            bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context="VERTS")
        mesh = bpy.data.meshes.new("Clipped_" + crown["id"].replace("/", "_"))
        bm.to_mesh(mesh)
        bm.free()
        points = np.array([tuple(v.co) for v in mesh.vertices], dtype=np.float64)
        normals = np.array([p[:3] for p in crown["planesMm"]], dtype=np.float64)
        distances = np.array([p[3]/1000 for p in crown["planesMm"]], dtype=np.float64)
        violation = float(np.max(points @ normals.T - distances))
        top_gap = hi[2]/1000 - float(points[:, 2].max())
        require(violation <= 0.00002, "Clipped vertices exceed the source crown volume")
        require(top_gap <= 0.025, "Crown top coverage gap exceeds 25mm: " + crown["id"])
        s = (Vector(crown["centerMm"])-origin).dot(direction)
        chunk_id = max(0, min(7, math.floor(s / 4000)))
        chunk = chunks.setdefault(chunk_id, {"vertices": [], "faces": [], "uv": [], "crowns": []})
        offset, first_triangle = len(chunk["vertices"]), len(chunk["faces"])
        chunk["vertices"].extend(tuple(v.co) for v in mesh.vertices)
        source_uv = mesh.uv_layers.active.data
        for face in mesh.polygons:
            chunk["faces"].append(tuple(offset+i for i in face.vertices))
            chunk["uv"].append([tuple(source_uv[i].uv) for i in face.loop_indices])
        chunk["crowns"].append(crown["id"])
        crown_receipts.append({"id": crown["id"], "sourceObjectId": crown["sourceObjectId"],
                               "sourceBoundsMm": crown["boundsMm"], "layers": 2, "sourcePrototype": source.name,
                               "chunk": chunk_id, "firstTriangle": first_triangle, "triangles": len(mesh.polygons),
                               "removedUnrealDegenerateTriangles": collapsed_count,
                               "maxVolumeViolationMm": max(0, violation*1000), "topCoverageGapMm": top_gap*1000,
                               "detailBoundsMm": {"min": list(points.min(axis=0)*1000), "max": list(points.max(axis=0)*1000)}})
        bpy.data.meshes.remove(mesh)
        if index % 10 == 0:
            print("BREZI_HEDGE_CLIPPED " + str(index+1) + "/153", flush=True)
    batch_objects, batch_receipts = [], []
    total = sum(len(c["faces"]) for c in chunks.values())
    require(0 < total <= 750000, "Hedge detail geometry budget exceeded")
    bpy.ops.object.select_all(action="DESELECT")
    for chunk_id, chunk in sorted(chunks.items()):
        name = "HEDGE_DETAIL_" + str(chunk_id).zfill(2)
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(chunk["vertices"], [], chunk["faces"])
        mesh.materials.append(material)
        layer = mesh.uv_layers.new(name="UVMap")
        for face, coordinates in zip(mesh.polygons, chunk["uv"]):
            face.use_smooth = True
            for loop, coordinate in zip(face.loop_indices, coordinates):
                layer.data[loop].uv = coordinate
        obj = bpy.data.objects.new(name, mesh)
        bpy.context.scene.collection.objects.link(obj)
        obj.select_set(True)
        obj["role"] = "illustrative clipped hedge crown detail"
        obj["source_crown_ids"] = json.dumps(chunk["crowns"])
        obj["source_patch_id"] = patch["id"]
        batch_objects.append(obj)
        bounds = {"min": [min(p[i] for p in chunk["vertices"])*1000 for i in range(3)],
                  "max": [max(p[i] for p in chunk["vertices"])*1000 for i in range(3)]}
        batch_receipts.append({"id": name, "chunk": chunk_id, "crowns": chunk["crowns"],
                               "triangles": len(mesh.polygons), "boundsSourceMm": bounds})
    bpy.context.view_layer.objects.active = batch_objects[0]
    glb = output / "hedge-detail.glb"
    bpy.ops.export_scene.gltf(filepath=str(glb), export_format="GLB", use_selection=True,
                              export_yup=True, export_normals=True, export_tangents=True,
                              export_texcoords=True, export_materials="EXPORT", export_animations=False,
                              export_extras=True, export_apply=False)
    repaired_tangents = write_masked_glb(glb)
    doc, binary = parse_glb(glb)
    require(len(doc["nodes"]) == len(chunks), "Hedge GLB swallowed unrelated objects")
    exported_triangles, max_export_error = 0, 0
    by_name = {p["id"]: p for p in batch_receipts}
    for node in doc["nodes"]:
        record = by_name[node["name"]]
        primitives = doc["meshes"][node["mesh"]]["primitives"]
        require(len(primitives) == 1, "Unexpected hedge material slots")
        primitive = primitives[0]
        require(all(k in primitive["attributes"] for k in ("POSITION", "NORMAL", "TEXCOORD_0", "TANGENT")), "Hedge UV/tangents lost")
        positions = accessor(doc, binary, primitive["attributes"]["POSITION"])
        count = len(accessor(doc, binary, primitive["indices"]))//3
        require(count == record["triangles"], "Hedge triangle count changed on export")
        exported_triangles += count
        lo, hi = record["boundsSourceMm"]["min"], record["boundsSourceMm"]["max"]
        expected = {"min": [lo[0]/1000, lo[2]/1000, -hi[1]/1000], "max": [hi[0]/1000, hi[2]/1000, -lo[1]/1000]}
        for i in range(3):
            max_export_error = max(max_export_error, abs(min(p[i] for p in positions)-expected["min"][i]), abs(max(p[i] for p in positions)-expected["max"][i]))
    require(max_export_error*1000 <= 0.05, "Hedge GLB bounds changed")
    result = {"schemaVersion": 1, "status": "clipped-hedge-geometry-validated", "nativeApplied": False,
              "role": "illustrative clipped hedge crown detail", "sourcePatch": patch,
              "sourceManifestSha256": digest(geometry / "scene.json"), "sourceObjSha256": scene["objSha256"],
              "converterSha256": digest(Path(__file__)), "auditorSha256": digest(Path(__file__).with_name("vegetation.py")),
              "sourcePrototypeSha256": prototype["sha256"], "file": glb.name, "sha256": digest(glb),
              "sourceCrowns": len(crowns), "layersPerCrown": 2, "spatialBatches": batch_receipts,
              "crowns": crown_receipts, "trianglesLOD0": exported_triangles,
              "removedUnrealDegenerateTriangles": sum(c["removedUnrealDegenerateTriangles"] for c in crown_receipts),
              "maximumTopCoverageGapMm": max(c["topCoverageGapMm"] for c in crown_receipts),
              "maximumSourceVolumeViolationMm": max(c["maxVolumeViolationMm"] for c in crown_receipts),
              "maxExportBoundsErrorMm": max_export_error*1000, "renderedFrames": 0,
              "zeroTangentRepairs": repaired_tangents, "khronosValidation": validate_glb(glb),
              "lawnInstances": 0, "treePlacements": 0,
              "limitations": ["Species is illustrative; source fence design remains authoritative.",
                              "Geometry height/containment is validated; alpha coverage/privacy and packaged appearance require rendered QA.",
                              "Eight HISM spatial batches are single mesh instances; draw-call batching, not cross-crown mesh deduplication.",
                              "Native LOD reduction must be built and actual triangle counts recorded before deployment."]}
    save_json(output / "hedge-detail.json", result)
    for obj in batch_objects:
        bpy.data.objects.remove(obj, do_unlink=True)
    print("BREZI_HEDGE " + json.dumps({"status": result["status"], "crowns": len(crowns), "triangles": total}), flush=True)
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--geometry", type=Path, default=Path(os.environ.get("BREZI_GEOMETRY", ROOT / "output/unreal/geometry")))
    parser.add_argument("--output", type=Path)
    parser.add_argument("--hedge-detail", action="store_true")
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
    output = (args.output or args.geometry.parent / "vegetation-prototypes").resolve()
    output.mkdir(parents=True, exist_ok=True)
    receipt = output / "prototypes.json"
    save_json(receipt, {"status": "pending", "nativeApplied": False})
    try:
        require(not bpy.app.autoexec_fail, "Unexpected auto-exec state")
        assets = audit_assets(LOCK, ASSETS)
        for obj in list(bpy.data.objects):
            bpy.data.objects.remove(obj, do_unlink=True)
        bpy.context.scene.unit_settings.system = "METRIC"
        bpy.context.scene.unit_settings.scale_length = 1.0
        report = {"schemaVersion": 1, "status": "pending", "nativeApplied": False,
                  "converterSha256": digest(Path(__file__)), "auditorSha256": digest(Path(__file__).with_name("vegetation.py")),
                  "blenderVersion": bpy.app.version_string, "units": "metres", "renderedFrames": 0,
                  "assetAudit": assets, "models": {}, "prototypes": [], "treePlacements": 0}
        lock = json.loads(LOCK.read_text())
        for asset_id, names in NAMES.items():
            maps = texture_maps(asset_id, output)
            report["models"][asset_id] = {"textures": maps}
            material = make_material(asset_id, maps, output)
            with bpy.data.libraries.load(str(ASSETS / lock["models"][asset_id]["path"]), link=False) as (available, loaded):
                require(all(name in available.objects for name in names), "Required source prototype missing")
                loaded.objects = names
            for source in loaded.objects:
                report["prototypes"].append(export_object(source, asset_id, material, output))
        require(assets == audit_assets(LOCK, ASSETS), "Source asset bytes changed during conversion")
        report["status"] = "prototype-conversion-validated"
        save_json(receipt, report)
        if args.hedge_detail:
            save_json(output / "hedge-detail.json", {"status": "pending", "nativeApplied": False})
            export_hedge_detail(report, output, args.geometry.resolve())
        print("BREZI_PLANTS " + json.dumps({"status": report["status"], "prototypes": len(report["prototypes"]), "renderedFrames": 0}), flush=True)
    except Exception as error:
        save_json(receipt, {"schemaVersion": 1, "status": "failed", "nativeApplied": False, "error": str(error)})
        if args.hedge_detail:
            save_json(output / "hedge-detail.json", {"status": "failed", "nativeApplied": False, "error": str(error)})
        raise


if __name__ == "__main__":
    main()
