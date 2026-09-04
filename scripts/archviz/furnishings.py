"""Render-only CC0 furnishings, separate from the authoritative house model."""

import math
import bpy
from mathutils import Matrix, Vector


def add_furnishings(scene, records, assets):
    path = assets / "outdoor_table_chair_set_01/outdoor_table_chair_set_01_2k.blend"
    with bpy.data.libraries.load(str(path), link=False) as (src, dst):
        dst.objects = [
            n for n in src.objects if n.startswith("outdoor_table_chair_set_01")
        ]
    objects = [o for o in dst.objects if o and o.type == "MESH"]
    if len(objects) != 3:
        raise RuntimeError("Incomplete terrace furniture library")
    corners = [o.matrix_world @ Vector(v) for o in objects for v in o.bound_box]
    low = Vector(tuple(min(v[i] for v in corners) for i in range(3)))
    high = Vector(tuple(max(v[i] for v in corners) for i in range(3)))
    origin = Vector(((low.x + high.x) / 2, (low.y + high.y) / 2, low.z))
    transform = (
        Matrix.Translation((-6.3, 1.4, 0.02))
        @ Matrix.Rotation(math.pi / 2, 4, "Z")
        @ Matrix.Translation(-origin)
    )
    collection = bpy.data.collections.new("ArchViz | Terrace furniture")
    scene.collection.children.link(collection)
    for obj in objects:
        collection.objects.link(obj)
        obj.matrix_world = transform @ obj.matrix_world
        bottom = min((obj.matrix_world @ Vector(v)).z for v in obj.bound_box)
        obj.location.z += 0.02 - bottom
        obj["asset_license"] = "CC0 | James Ray Cock | Poly Haven"
    hidden = 0
    for obj, rec in records:
        if any(
            s in rec["name"].lower()
            for s in ("záhradné kreslo", "operadlo záhradného kresla", "noha kresla")
        ):
            obj.hide_render = True
            obj.hide_set(True)
            hidden += 1
    return {"objects": len(objects), "replacedIllustrativeParts": hidden}
