"""blender -b --factory-startup --python build.py -- --quality preview --render"""

import argparse
import hashlib
import json
import math
import sys
import time
from pathlib import Path
import bpy
from mathutils import Vector, Matrix

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from materials import make_material
from vegetation import add_plants
from furnishings import add_furnishings
from solar import solar_position, site_sun_direction

parser = argparse.ArgumentParser()
parser.add_argument("--output", default=str(HERE.parent.parent / "output/archviz"))
parser.add_argument("--quality", choices=["preview", "final"], default="final")
parser.add_argument("--camera", choices=["garden", "courtyard", "street", "interior"])
parser.add_argument("--date-time")
parser.add_argument("--render", action="store_true")
parser.add_argument("--device", choices=["auto", "cpu"], default="auto")
parser.add_argument("--samples", type=int)
args = parser.parse_args(
    sys.argv[sys.argv.index("--") + 1 :] if "--" in sys.argv else []
)
if args.samples is not None and args.samples < 1:
    parser.error("--samples must be positive")
started = time.monotonic()
output = Path(args.output).resolve()
root = HERE.parent.parent
manifest = json.loads((output / "scene.json").read_text())
config = json.loads((HERE / "config.json").read_text())
lock = json.loads((HERE / "assets.lock.json").read_text())
assets = output / "assets"
if (
    hashlib.sha256((output / "dom-mm.obj").read_bytes()).hexdigest()
    != manifest["objSha256"]
):
    raise RuntimeError(
        "OBJ checksum differs from scene.json; re-export before rendering."
    )
scene = bpy.context.scene
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 1
scene.unit_settings.length_unit = "MILLIMETERS"
bpy.ops.wm.obj_import(
    filepath=str(output / "dom-mm.obj"),
    forward_axis="Y",
    up_axis="Z",
    global_scale=0.001,
    use_split_objects=True,
    use_split_groups=False,
)
objects = {o.name: o for o in scene.objects}
records = []
collections = {}
for rec in manifest["objects"]:
    obj = objects.get(rec["id"])
    if obj is None:
        raise RuntimeError("Missing imported object " + rec["id"])
    # OBJ global_scale is an OBJECT transform. Bake it before metre-based GN
    # density, bevels and water thickness, otherwise density is per square mm.
    obj.data.transform(obj.matrix_world)
    obj.matrix_world = Matrix.Identity(4)
    obj["source_name"] = rec["name"]
    obj.name = rec["id"] + " | " + rec["name"]
    obj["source_id"] = rec["sourceId"]
    obj["source_bounds_mm"] = json.dumps(rec["boundsMm"])
    obj["source_materials"] = " | ".join(rec["materialNames"])
    group = rec["group"]
    if group not in collections:
        collections[group] = bpy.data.collections.new("DOM | " + group)
        scene.collection.children.link(collections[group])
    for c in list(obj.users_collection):
        c.objects.unlink(obj)
    collections[group].objects.link(obj)
    records.append((obj, rec))
bpy.context.view_layer.update()
# Validate imported world bounds against exported mm, before modifiers/enhancement.
max_error = 0
for obj, rec in records:
    corners = [obj.matrix_world @ Vector(v) for v in obj.bound_box]
    for key, fun in [("min", min), ("max", max)]:
        for axis in range(3):
            error = abs(
                fun(v[axis] for v in corners) * 1000 - rec["boundsMm"][key][axis]
            )
            max_error = max(max_error, error)
if max_error > 0.5:
    raise RuntimeError(f"Import dimension error {max_error:.6f} mm exceeds .5 mm")
print(
    "ARCHVIZ_IMPORT",
    len(records),
    "objects; max bound error",
    max_error,
    "mm",
    flush=True,
)
# Standard metre GLB of exact base geometry, before render-only enhancements.
bpy.ops.export_scene.gltf(
    filepath=str(output / "dom.glb"),
    export_format="GLB",
    export_yup=True,
    export_extras=True,
    export_animations=False,
)
material_map = {
    slot: make_material(slot, src, assets, lock, root)
    for slot, src in manifest["materials"].items()
}
asphalt_material = make_material(
    "ARCHVIZ_ASPHALT",
    {"name": "archviz-asphalt", "color": [0.25] * 3, "roughness": 0.9, "metallic": 0},
    assets,
    lock,
    root,
)
asphalt_material.use_fake_user = True
water_objects = []
pool_objects = []
embers = []
for obj, rec in records:
    imported_slots = [m.name for m in obj.data.materials]
    polygon_slots = [p.material_index for p in obj.data.polygons]
    obj.data.materials.clear()
    for slot in rec["materialSlots"]:
        obj.data.materials.append(material_map[slot])
    for polygon, old_index in zip(obj.data.polygons, polygon_slots):
        polygon.material_index = rec["materialSlots"].index(imported_slots[old_index])
    obj.hide_render = not rec["enabled"] or rec["group"] in ("Foundations", "Services")
    mats = " ".join(rec["materialNames"])
    if "real-pool-water" in mats:
        water_objects.append(obj)
        obj.cycles.is_caustics_caster = config["caustics"]
        # Source is already a 48x48 grid; one subdivision is ample for ripples.
        subdiv = obj.modifiers.new("Small water waves", "SUBSURF")
        subdiv.subdivision_type = "SIMPLE"
        subdiv.levels = 1
        subdiv.render_levels = 1
        texture = bpy.data.textures.new("Water wave geometry", type="CLOUDS")
        texture.noise_scale = 0.3
        texture.noise_depth = 2
        wave = obj.modifiers.new("Physical surface for refractive caustics", "DISPLACE")
        wave.texture = texture
        wave.strength = 0.004
        # Source is an open water surface. Close its optical volume to basin depth.
        solid = obj.modifiers.new("Water optical volume", "SOLIDIFY")
        solid.thickness = manifest["pool"]["proposedWaterDepthMm"] / 1000
        solid.offset = -1
    elif rec["group"] == "Pool":
        pool_objects.append(obj)
        obj.cycles.is_caustics_receiver = config["caustics"]
    if "ember" in mats:
        embers.append(obj)
    if (
        rec["group"] in ("Walls", "Windows", "Decking", "Floors", "Interior", "Fence")
        and len(obj.data.polygons) < 10000
        and not any(x in mats for x in ("glass", "plant", "hedge", "curtain"))
    ):
        bevel = obj.modifiers.new("Light-catching edges, 1.2 mm", "BEVEL")
        bevel.width = config["bevelMm"] / 1000
        bevel.segments = 3
        bevel.limit_method = "ANGLE"
        if "real-fabric" in mats:
            bevel.width = 0.025
            bevel.segments = 5
    # Babylon overlays imitating light do not belong in a path-traced scene.
    if any(
        x in rec["name"].lower() for x in ("odlesk vod", "kaustick", "odraz oblohy")
    ):
        obj.hide_render = True
plants = add_plants(scene, records, assets, config, manifest)
furnishings = add_furnishings(scene, records, assets)
instant = args.date_time or config["dateTime"]
geo = manifest["geolocation"]
elevation, azimuth = solar_position(instant, geo["latitude"], geo["longitude"])
direction = Vector(site_sun_direction(elevation, azimuth, geo["northAngleRadians"]))
world = bpy.data.worlds.new("Březí | physical atmosphere")
world.use_nodes = True
scene.world = world
nodes = world.node_tree.nodes
links = world.node_tree.links
sky = nodes.new("ShaderNodeTexSky")
sky.sky_type = "MULTIPLE_SCATTERING" if bpy.app.version >= (5, 1, 0) else "NISHITA"
sky.sun_elevation = elevation
sky.sun_rotation = math.atan2(direction.x, direction.y)
sky.sun_disc = False
sky.altitude = 200
if hasattr(sky, "aerosol_density"):
    sky.aerosol_density = 1.1
links.new(sky.outputs[0], nodes.get("Background").inputs["Color"])
nodes.get("Background").inputs["Strength"].default_value = 0.23
sun_data = bpy.data.lights.new("Sun | dated true geographic direction", "SUN")
sun = bpy.data.objects.new(sun_data.name, sun_data)
scene.collection.objects.link(sun)
sun.rotation_euler = (-direction).to_track_quat("-Z", "Y").to_euler()
sun_data.energy = config["sunStrength"] if elevation > 0 else 0
sun_data.color = (1.0, 0.93, 0.83)
sun_data.angle = math.radians(0.545)
sun_data.cycles.is_caustics_light = config["caustics"]
for i, obj in enumerate(embers):
    light = bpy.data.lights.new("Stove | 1850 K " + str(i), "POINT")
    light.energy = 9
    light.color = (1, 0.42, 0.13)
    light.shadow_soft_size = 0.11
    lamp = bpy.data.objects.new(light.name, light)
    scene.collection.objects.link(lamp)
    lamp.location = (
        sum((obj.matrix_world @ Vector(v) for v in obj.bound_box), Vector()) / 8
    )
camera_name = args.camera or config["camera"]
for name, spec in config["cameras"].items():
    data = bpy.data.cameras.new("Camera | " + name)
    obj = bpy.data.objects.new(data.name, data)
    scene.collection.objects.link(obj)
    obj.location = spec["eye"]
    obj.rotation_euler = (
        (Vector(spec["target"]) - obj.location).to_track_quat("-Z", "Y").to_euler()
    )
    data.lens = spec["lens"]
    data.sensor_width = 36
    data.shift_y = spec["shiftY"]
    data.clip_start = 0.05
    data.clip_end = 2000
    data.dof.use_dof = False
    if name == camera_name:
        scene.camera = obj
scene.render.engine = "CYCLES"
scene.cycles.device = "CPU"
devices = []
if args.device == "auto":
    try:
        pref = bpy.context.preferences.addons["cycles"].preferences
        pref.compute_device_type = "METAL"
        pref.refresh_devices()
        for d in pref.devices:
            d.use = d.type == "METAL"
        devices = [d.name for d in pref.devices if d.use]
        if devices:
            scene.cycles.device = "GPU"
    except (TypeError, RuntimeError):
        pass
quality = config["quality"][args.quality]
scene.render.resolution_x = quality["width"]
scene.render.resolution_y = quality["height"]
scene.render.resolution_percentage = 100
scene.cycles.samples = args.samples or quality["samples"]
scene.cycles.use_adaptive_sampling = True
scene.cycles.adaptive_threshold = quality["noiseThreshold"]
scene.cycles.use_denoising = True
scene.cycles.max_bounces = 12
scene.cycles.transmission_bounces = 12
scene.cycles.transparent_max_bounces = 16
scene.cycles.diffuse_bounces = 6
scene.cycles.glossy_bounces = 6
scene.cycles.sample_clamp_indirect = 8
scene.cycles.seed = config["seed"]
scene.render.film_transparent = False
scene.view_settings.view_transform = "AgX"
scene.view_settings.look = "AgX - Medium High Contrast"
scene.view_settings.exposure = config["exposure"]
scene.render.image_settings.file_format = "PNG"
scene.render.image_settings.color_mode = "RGB"
scene.render.image_settings.color_depth = "16"
scene.render.filepath = str(output / f"{camera_name}-{args.quality}.png")
scene["geolocation"] = json.dumps(geo)
scene["solar_datetime"] = instant
scene["attribution"] = "Powered by Poly Haven | CC0 assets, see assets.lock.json"
scene["geometry_note"] = (
    "Base geometry from DOM; added vegetation and edge bevels are visualization only."
)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type == "VIEW_3D":
            area.spaces.active.clip_end = 2000
            area.spaces.active.region_3d.view_perspective = "CAMERA"
            area.spaces.active.shading.type = "MATERIAL"
bpy.ops.file.pack_all()
blend = output / "dom-archviz.blend"
bpy.ops.wm.save_as_mainfile(filepath=str(blend))
report = {
    "blender": bpy.app.version_string,
    "device": scene.cycles.device,
    "devices": devices,
    "objects": len(records),
    "maxImportBoundsErrorMm": max_error,
    "sourceObjSha256": manifest["objSha256"],
    "vegetation": plants,
    "furnishings": furnishings,
    "pipelineFiles": {
        name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
        for name in (
            "build.py",
            "materials.py",
            "vegetation.py",
            "furnishings.py",
            "solar.py",
            "config.json",
            "assets.lock.json",
        )
    },
    "solar": {
        "dateTime": instant,
        "elevationDegrees": math.degrees(elevation),
        "azimuthDegrees": math.degrees(azimuth),
        "siteDirection": list(direction),
    },
    "resolution": [quality["width"], quality["height"]],
    "samples": scene.cycles.samples,
    "causticsEnabled": config["caustics"],
    "waterObjects": len(water_objects),
    "status": "scene-prepared",
    "render": scene.render.filepath,
}
(output / "build-report.json").write_text(json.dumps(report, indent=2))
print("ARCHVIZ_READY", json.dumps(report), flush=True)
if args.render:
    report_path = output / f"{camera_name}-{args.quality}-report.json"
    report_path.unlink(missing_ok=True)
    bpy.ops.render.render(write_still=True)
    report["status"] = "render-complete"
    report["elapsedSeconds"] = round(time.monotonic() - started, 2)
    report["pngSha256"] = hashlib.sha256(
        Path(scene.render.filepath).read_bytes()
    ).hexdigest()
    report_path.write_text(json.dumps(report, indent=2))
    print("ARCHVIZ_RENDER_COMPLETE", scene.render.filepath, flush=True)
