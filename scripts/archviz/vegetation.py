"""Deterministic CC0 linked plant geometry. No image billboards in final view."""

import math
import random
import bpy
from mathutils import Vector, Matrix
from materials import make_hedge_material, make_grass_material


def append_objects(path, predicate):
    with bpy.data.libraries.load(str(path), link=False) as (src, dst):
        dst.objects = [name for name in src.objects if predicate(name)]
    return [o for o in dst.objects if o and o.type == "MESH"]


def add_plants(scene, records, assets, config, manifest):
    rng = random.Random(config["seed"])
    collection = bpy.data.collections.new("ArchViz | Living vegetation")
    scene.collection.children.link(collection)
    prototypes = bpy.data.collections.new("ArchViz | Plant library")
    scene.collection.children.link(prototypes)
    grass = append_objects(
        assets / "grass_bermuda_01/grass_bermuda_01_1k.blend",
        lambda n: n.startswith("grass_bermuda_01_small_")
        or n.startswith("grass_bermuda_01_medium_"),
    )
    shrubs = append_objects(
        assets / "shrub_02/shrub_02_1k.blend", lambda n: n.endswith("_LOD1")
    )
    trees = append_objects(
        assets / "tree_small_02/tree_small_02_1k.blend",
        lambda n: n == "tree_small_02_LOD1",
    )
    if not grass or not shrubs or not trees:
        raise RuntimeError("Incomplete plant library. Run npm run archviz:assets.")
    hedge_material = make_hedge_material(assets)
    for shrub in shrubs:
        for index in range(len(shrub.data.materials)):
            shrub.data.materials[index] = hedge_material
    grass_material = make_grass_material(assets)
    for blade in grass:
        for index in range(len(blade.data.materials)):
            blade.data.materials[index] = grass_material
    # A tuft consists of 28 real scanned/alpha-cut blades. Its geometry is shared.
    tuft_parts = []
    for i in range(28):
        src = grass[i % len(grass)]
        obj = bpy.data.objects.new("blade", src.data.copy())
        prototypes.objects.link(obj)
        obj.location = (rng.uniform(-0.07, 0.07), rng.uniform(-0.07, 0.07), 0)
        obj.rotation_euler.z = rng.uniform(0, math.tau)
        tuft_parts.append(obj)
    bpy.ops.object.select_all(action="DESELECT")
    for obj in tuft_parts:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = tuft_parts[0]
    bpy.ops.object.join()
    tuft = tuft_parts[0]
    tuft.name = "Bermuda tuft | shared geometry"
    # Put origin at zero; object-info GN uses original mesh coordinate space.
    tuft.data.transform(tuft.matrix_world)
    tuft.matrix_world = Matrix.Identity(4)
    tuft.hide_render = True
    tuft.hide_set(True)
    for obj in shrubs + trees:
        obj.data = obj.data.copy()
        obj.data.transform(obj.matrix_world.to_3x3().to_4x4())
        obj.matrix_world = Matrix.Identity(4)
        prototypes.objects.link(obj)
        obj.hide_render = True
        obj.hide_set(True)
    lawns = []
    hedge_cores = []
    cards = []
    for obj, rec in records:
        mats = " ".join(rec["materialNames"])
        name = rec["name"].lower()
        if mats in ("real-grass", "real-grass-context") and "dmr" not in name:
            lawns.append(obj)
        if "hedge" in mats:
            obj.hide_render = True
            if "real-hedge-dark" in mats and (
                "jadro" in name or "základ" in name or "telo" in name
            ):
                hedge_cores.append((obj, rec))
        if "real-plant-" in mats:
            obj.hide_render = True
            cards.append((obj, rec))
    # Ray blockers prevent blades protruding through floors, deck boards and
    # paving. Keep this invisible mesh separate from authoritative geometry.
    vertices = []
    faces = []
    for obj, rec in records:
        lo, hi = rec["boundsMm"]["min"], rec["boundsMm"]["max"]
        if (
            rec["enabled"]
            and rec["group"] in ("Walls", "Floors", "Decking", "Hardscape", "Interior")
            and lo[2] < 300
            and hi[2] > -65
        ):
            offset = len(vertices)
            vertices.extend(tuple(obj.matrix_world @ v.co) for v in obj.data.vertices)
            faces.extend(
                tuple(offset + i for i in p.vertices) for p in obj.data.polygons
            )
    blocker_mesh = bpy.data.meshes.new("Grass exclusion surfaces")
    blocker_mesh.from_pydata(vertices, [], faces)
    blocker_mesh.update()
    blocker = bpy.data.objects.new("Grass exclusion surfaces", blocker_mesh)
    prototypes.objects.link(blocker)
    blocker.hide_render = True
    blocker.hide_set(True)
    for lawn in lawns:
        mod = lawn.modifiers.new("Living blades at true scale", "NODES")
        group = bpy.data.node_groups.new("Bermuda distribution", "GeometryNodeTree")
        mod.node_group = group
        group.interface.new_socket(
            name="Geometry", in_out="INPUT", socket_type="NodeSocketGeometry"
        )
        group.interface.new_socket(
            name="Geometry", in_out="OUTPUT", socket_type="NodeSocketGeometry"
        )
        n, l = group.nodes, group.links
        inp = n.new("NodeGroupInput")
        out = n.new("NodeGroupOutput")
        distribute = n.new("GeometryNodeDistributePointsOnFaces")
        distribute.distribute_method = "RANDOM"
        distribute.inputs["Density"].default_value = config["grassDensity"]
        distribute.inputs["Seed"].default_value = config["seed"] % 10000
        l.new(inp.outputs["Geometry"], distribute.inputs["Mesh"])
        info = n.new("GeometryNodeObjectInfo")
        info.inputs["Object"].default_value = tuft
        info.inputs["As Instance"].default_value = True
        instance = n.new("GeometryNodeInstanceOnPoints")
        l.new(distribute.outputs["Points"], instance.inputs["Points"])
        l.new(info.outputs["Geometry"], instance.inputs["Instance"])
        obstacle = n.new("GeometryNodeObjectInfo")
        obstacle.inputs["Object"].default_value = blocker
        ray = n.new("GeometryNodeRaycast")
        ray.inputs["Ray Direction"].default_value = (0, 0, 1)
        ray.inputs["Ray Length"].default_value = 0.5
        position = n.new("GeometryNodeInputPosition")
        l.new(position.outputs[0], ray.inputs["Source Position"])
        l.new(obstacle.outputs["Geometry"], ray.inputs["Target Geometry"])
        clear = n.new("FunctionNodeBooleanMath")
        clear.operation = "NOT"
        l.new(ray.outputs["Is Hit"], clear.inputs[0])
        l.new(clear.outputs[0], instance.inputs["Selection"])
        rot = n.new("FunctionNodeRandomValue")
        rot.data_type = "FLOAT_VECTOR"
        rot.inputs["Min"].default_value = (0, 0, 0)
        rot.inputs["Max"].default_value = (0, 0, math.tau)
        l.new(rot.outputs["Value"], instance.inputs["Rotation"])
        scale = n.new("FunctionNodeRandomValue")
        scale.data_type = "FLOAT"
        scale.inputs["Min"].default_value = 0.65
        scale.inputs["Max"].default_value = 1.2
        l.new(scale.outputs["Value"], instance.inputs["Scale"])
        join = n.new("GeometryNodeJoinGeometry")
        l.new(inp.outputs["Geometry"], join.inputs[0])
        l.new(instance.outputs["Instances"], join.inputs[0])
        l.new(join.outputs[0], out.inputs[0])

    def plant(src, position, height):
        obj = bpy.data.objects.new("Living | " + src.name, src.data)
        collection.objects.link(obj)
        z = [v.co.z for v in src.data.vertices]
        extent = max(z) - min(z)
        scale = height / max(extent, 0.001)
        obj.scale = (scale, scale, scale)
        obj.location = Vector(position) - Vector((0, 0, min(z) * scale))
        obj.rotation_euler.z = rng.uniform(0, math.tau)
        return obj

    # Original hedge volumes identify exact beds; replace only their visible cores.
    center = manifest["sceneCenterMm"]
    for run in manifest["fence"]["physicalFixedRuns"]:
        if run["treatment"] != "LIVING_HEDGE":
            continue
        a, b = [
            Vector(
                ((p["x"] - center["x"]) / 1000, (p["y"] - center["y"]) / 1000, -0.08)
            )
            for p in run["pointsMm"]
        ]
        direction = (b - a).normalized()
        inward = Vector((-direction.y, direction.x, 0))
        length = (b - a).length
        count = max(1, math.ceil(length / 0.45))
        for row in range(2):
            for i in range(count):
                p = (
                    a
                    + (b - a) * min(1, ((i + 0.25 + row * 0.5) / count))
                    + inward * (0.15 + row * 0.35 + rng.uniform(-0.035, 0.035))
                )
                plant(rng.choice(shrubs), p, rng.uniform(1.5, 1.7))
    for obj, rec in cards:
        lo = rec["boundsMm"]["min"]
        hi = rec["boundsMm"]["max"]
        plant(
            rng.choice(shrubs),
            ((lo[0] + hi[0]) / 2000, (lo[1] + hi[1]) / 2000, lo[2] / 1000),
            max(0.35, min(1.1, (hi[2] - lo[2]) / 1000 * rng.uniform(0.7, 0.9))),
        )
    # Illustrative off-parcel vegetation, never represented as surveyed objects.
    for p, h in [
        ((-20, 24, -0.08), 6),
        ((-6, 29, -0.08), 7),
        ((10, 30, -0.08), 6.4),
        ((24, 25, -0.08), 5.8),
        ((-25, 7, -0.08), 5.5),
        ((-14, -24, -0.08), 9.5),
        ((2, -28, -0.08), 10.0),
        ((23, -23, -0.08), 8.5),
    ]:
        plant(trees[0], p, h)
    # Distant, clearly illustrative shelter belt supplies a real silhouette
    # and reflections instead of exposing the edge of a flat terrain plane.
    for i in range(36):
        angle = math.tau * (i + rng.uniform(-0.25, 0.25)) / 36
        radius = rng.uniform(42, 54)
        plant(
            trees[0],
            (math.cos(angle) * radius, math.sin(angle) * radius, -0.2),
            rng.uniform(10, 16),
        )
    return {
        "lawnEmitters": len(lawns),
        "hedgeVolumes": len(hedge_cores),
        "plantObjects": len(collection.objects),
        "seed": config["seed"],
    }
