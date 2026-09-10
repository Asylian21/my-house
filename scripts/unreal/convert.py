"""Exact OBJ -> glTF bridge. Run using Blender --background --python-exit-code 1."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/archviz"))
from solar import solar_position, site_sun_direction


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_bounds(objects, records):
    maximum = 0.0
    for rec in records:
        obj = objects[rec["id"]]
        corners = [obj.matrix_world @ Vector(v) for v in obj.bound_box]
        for key, fn in [("min", min), ("max", max)]:
            for axis in range(3):
                error = abs(fn(v[axis] for v in corners) * 1000 - rec["boundsMm"][key][axis])
                if not math.isfinite(error) or error > 0.5:
                    raise RuntimeError(f'{rec["id"]} {key}[{axis}]: {error} mm > 0.5 mm')
                maximum = max(maximum, error)
    return maximum


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", required=True)
    args = parser.parse_args(sys.argv[sys.argv.index("--") + 1:])
    out = Path(args.output).resolve()
    data = json.loads((out / "scene.json").read_text())
    if sha(out / "dom-mm.obj") != data["objSha256"]:
        raise RuntimeError("OBJ checksum mismatch; export the current source again")
    for name, digest in data["sourceFiles"].items():
        if sha(ROOT / name) != digest:
            raise RuntimeError(f"Source changed during export: {name}")

    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1
    bpy.ops.wm.obj_import(filepath=str(out / "dom-mm.obj"), forward_axis="Y", up_axis="Z",
                          global_scale=0.001, use_split_objects=True, use_split_groups=False)
    objects = {o.name: o for o in scene.objects}
    if set(objects) != {r["id"] for r in data["objects"]}:
        raise RuntimeError("OBJ object set differs from source manifest")

    # Preserve scalar PBR and emission. Procedural Babylon maps are deliberately
    # listed as pending shader authoring, never passed off as portable textures.
    for slot, src in data["materials"].items():
        mat = bpy.data.materials.get(slot)
        if mat is None:  # an unused MultiMaterial slot need not create a Blender material
            continue
        mat.use_nodes = True
        node = mat.node_tree.nodes.get("Principled BSDF")
        node.inputs["Base Color"].default_value = (*src["color"], src["alpha"])
        node.inputs["Alpha"].default_value = src["alpha"]
        node.inputs["Roughness"].default_value = src["roughness"]
        node.inputs["Metallic"].default_value = src["metallic"]
        node.inputs["Emission Color"].default_value = (*src["emission"], 1)
        node.inputs["Emission Strength"].default_value = 1
        mat["source_material_name"] = src["name"]
        mat["source_material_slot"] = slot

    parts = {"brezi-twin.glb": [], "brezi-archive.glb": []}
    for rec in data["objects"]:
        obj = objects[rec["id"]]
        obj.data.transform(obj.matrix_world)
        obj.matrix_world = Matrix.Identity(4)
        # Names remain compact/stable across Blender/Unreal name restrictions.
        obj["source_id"] = rec["sourceId"]
        obj["source_object_id"] = rec["id"]
        obj["source_name"] = rec["name"]
        obj["source_group"] = rec["group"]
        obj["source_enabled"] = rec["enabled"]
        obj["source_metadata_json"] = json.dumps(rec.get("metadata"), ensure_ascii=False)
        obj["source_bounds_mm_json"] = json.dumps(rec["boundsMm"])
        obj["layout_id"] = data["layoutId"]
        proxy = any(s in rec["name"].lower() for s in ("odlesk vod", "kaustick", "odraz oblohy"))
        # enabled already encodes exact foundation/utility entity membership in
        # scene-export.ts. Display group names can also match a utility sink or
        # the base of a monitor; never hide physical furniture by that heuristic.
        archive = not rec["enabled"] or proxy
        rec["unrealArchiveReason"] = "source-disabled-or-technical" if archive else None
        if proxy:
            rec["unrealArchiveReason"] = "browser-lighting-overlay"
        parts["brezi-archive.glb" if archive else "brezi-twin.glb"].append(rec)
    bpy.context.view_layer.update()
    import_error = validate_bounds(objects, data["objects"])
    for filename, records in parts.items():
        bpy.ops.object.select_all(action="DESELECT")
        for rec in records:
            objects[rec["id"]].select_set(True)
        bpy.ops.export_scene.gltf(filepath=str(out / filename), export_format="GLB",
                                  use_selection=True, export_yup=True, export_extras=True,
                                  export_animations=False, export_cameras=False, export_lights=False)

    # Read exported GLB back independently, checking every object's identity and
    # bounds after the Y-up/metres conversion (not just the original OBJ import).
    roundtrip_error = 0.0
    for filename, records in parts.items():
        bpy.ops.object.select_all(action="SELECT")
        bpy.ops.object.delete(use_global=False)
        bpy.ops.import_scene.gltf(filepath=str(out / filename))
        imported = {o.get("source_object_id"): o for o in scene.objects if o.type == "MESH"}
        if set(imported) != {r["id"] for r in records}:
            raise RuntimeError(f"{filename}: GLB roundtrip object set mismatch")
        roundtrip_error = max(roundtrip_error, validate_bounds(imported, records))

    config = json.loads((ROOT / "scripts/archviz/config.json").read_text())
    views = []
    for id_, source, label in [("interior", "interior", "Obývačka"), ("terrace", "courtyard", "Terasa"),
                                ("pool", "garden", "Bazén"), ("street", "street", "Ulica")]:
        camera = config["cameras"][source]
        def ue(v):
            return [v[0] * 100, -v[1] * 100, v[2] * 100]
        views.append({"id": id_, "label": label, "eyeCm": ue(camera["eye"]),
                      "targetCm": ue(camera["target"]),
                      "horizontalFovDegrees": math.degrees(2 * math.atan(36 / (2 * camera["lens"]))),
                      "source": f"scripts/archviz/config.json:cameras.{source}"})
        if id_ == "pool":
            # The original garden overview stands outside the privacy hedge.
            # Frame the water from the existing one-metre deck instead. This
            # changes only presentation; source dimensions and privacy stay intact.
            deck, pool = data["poolDeck"], data["pool"]
            bounds = deck["outerBoundsMm"]
            eye_mm = [bounds["x0"] + deck["longitudinalWidthMm"] / 2,
                      bounds["y1"] - deck["rearWidthMm"] / 2, 1800]
            target_mm = [pool["centerMm"]["x"], pool["centerMm"]["y"], 600]
            def plan_ue(v):
                return [(v[0] - 15200) / 10, -(v[1] - 10800) / 10, v[2] / 10]
            views[-1].update({"eyeCm": plan_ue(eye_mm), "targetCm": plan_ue(target_mm),
                              "horizontalFovDegrees": 74,
                              "source": "scene.json:poolDeck.outerBoundsMm and pool.centerMm",
                              "presentation": {"eyeElevationMm": 1800, "targetElevationMm": 600,
                                               "intent": "Pool view from the existing narrow deck inside the privacy hedge"}})
    geo = data["geolocation"]
    elevation, azimuth = solar_position(config["dateTime"], geo["latitude"], geo["longitude"])
    direction = site_sun_direction(elevation, azimuth, geo["northAngleRadians"])
    # A directional light points away from the sun, with plan +Y mapped to UE -Y.
    ray = [-direction[0], direction[1], -direction[2]]
    viewpoints = {"coordinateSystem": "unreal-centimeters", "defaultView": "street", "views": views,
                  "sun": {"dayRotationDegrees": [math.degrees(math.atan2(ray[2], math.hypot(ray[0], ray[1]))),
                                                   math.degrees(math.atan2(ray[1], ray[0])), 0],
                          "dayLux": 80000, "dateTime": config["dateTime"], "geolocation": geo,
                          "illuminanceNote": "clear-sky artistic exposure input; not measured site illuminance"}}
    (out / "viewpoints.json").write_text(json.dumps(viewpoints, ensure_ascii=False, indent=2) + "\n")
    report = {"schemaVersion": 1, "status": "geometry-converted", "blenderVersion": bpy.app.version_string,
              "sourceCommit": data["sourceCommit"], "layoutId": data["layoutId"],
              "sourceObjSha256": data["objSha256"], "sceneSha256": sha(out / "scene.json"),
              "viewpointsSha256": sha(out / "viewpoints.json"),
              "sourceFiles": data["sourceFiles"],
              "pipelineFiles": {str(p.relative_to(ROOT)): sha(p) for p in [Path(__file__), ROOT / "scripts/archviz/solar.py", ROOT / "scripts/archviz/config.json"]},
              "maxObjImportBoundsErrorMm": import_error, "maxGlbRoundtripBoundsErrorMm": roundtrip_error,
              "units": {"source": "integer millimetres", "obj": "millimetres Z-up right-handed", "glb": "metres Y-up right-handed",
                        "unreal": "centimetres Z-up left-handed; importer converts units once",
                        "unrealFromPlanMm": "X=(planX-15200)/10; Y=-(planY-10800)/10; Z=elevation/10"},
              "files": {name: {"sha256": sha(out / name), "bytes": (out / name).stat().st_size,
                                "objects": len(records), "triangles": sum(r["triangles"] for r in records),
                                "objectIds": [r["id"] for r in records]} for name, records in parts.items()},
              "archiveReasons": {r["id"]: r["unrealArchiveReason"] for r in data["objects"] if r["unrealArchiveReason"]},
              "materials": {slot: {**src, "visualStatus": "scalar PBR only; Unreal shader/maps pending"}
                            for slot, src in data["materials"].items()},
              "limitations": ["No Unreal import or packaged-app verification is implied by this report.",
                              "GLB carries scalar PBR; procedural textures, refraction, caustics and final vegetation require native materials.",
                              "Source proposed/unresolved revisions remain proposed/unresolved; no regulatory approval is inferred."]}
    (out / "bridge-report.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print("UNREAL_BRIDGE", json.dumps({"objects": len(data["objects"]), "maxErrorMm": roundtrip_error}))


if __name__ == "__main__":
    main()
