"""Matched actual-placement Cycles lawn study; native pixels decide acceptance.

Reads frozen GLBs and plan rows only. Each panel uses the same square metre of
the source garden, with a neutral shared floor. Native Unreal ground, lighting
and foliage shading are intentionally not simulated by this diagnostic.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', required=True)
parser.add_argument('--reference', required=True)
parser.add_argument('--render', required=True)
opt = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, reference, render = (Path(p).resolve() for p in (opt.source, opt.reference, opt.render))
if render.exists():
    raise ValueError('Use a fresh diagnostic output image')
bpy.ops.wm.read_factory_settings(use_empty=True)
pins = {}
counts = []
for index, folder in enumerate([reference, source]):
    for name in ['lawn-natural.glb', 'lawn-natural-plan.json', 'material-manifest.json']:
        path = folder / name
        pins[str(path)] = hashlib.sha256(path.read_bytes()).hexdigest()
    plan = json.loads((folder / 'lawn-natural-plan.json').read_text())
    recipe = json.loads((folder / 'material-manifest.json').read_text())['lawn_natural_blade']
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(folder / 'lawn-natural.glb'))
    imported = list(set(bpy.data.objects) - before)
    masters = {}
    for obj in imported:
        if obj.type == 'MESH' and obj.name.endswith('_LOD0'):
            masters[obj.name.rsplit('_LOD', 1)[0].split('.')[0]] = obj
        else:
            bpy.data.objects.remove(obj, do_unlink=True)
    material = bpy.data.materials.new('Reference leaf response' if index == 0 else 'Fine leaf response')
    material.use_nodes = True
    nodes = material.node_tree.nodes
    links = material.node_tree.links
    bsdf = nodes.get('Principled BSDF')
    bsdf.inputs['Roughness'].default_value = recipe['roughness']
    bsdf.inputs['Specular IOR Level'].default_value = recipe['specular']
    bsdf.inputs['Subsurface Weight'].default_value = recipe['subsurfaceScale']
    colour = nodes.new('ShaderNodeVertexColor')
    colour.layer_name = next(iter(masters.values())).data.color_attributes.active_color.name
    multiply = nodes.new('ShaderNodeMixRGB')
    multiply.blend_type = 'MULTIPLY'
    multiply.inputs[0].default_value = 1
    multiply.inputs[2].default_value = (*recipe['linearColor'], 1)
    links.new(colour.outputs['Color'], multiply.inputs[1])
    links.new(multiply.outputs[0], bsdf.inputs['Base Color'])
    for obj in masters.values():
        obj.data.materials.clear()
        obj.data.materials.append(material)
    count = 0
    offset = -.64 if index == 0 else .64
    for row in plan['lawnPlacements']:
        x, y, z = row['positionCm']
        if abs(x + 630) > 58 or abs(y + 650) > 58:
            continue
        mesh = masters[row['meshId']]
        obj = bpy.data.objects.new('Actual saved patch', mesh.data)
        bpy.context.collection.objects.link(obj)
        # glTF's Y-up conversion makes Blender XY=(native X,-native Y).
        obj.location = ((x + 630) / 100 + offset, -(y + 650) / 100, 0)
        obj.rotation_euler.z = -math.radians(row['yawDeg'])
        obj.scale = tuple(row['scale'])
        count += 1
    counts.append(count)
    for obj in masters.values():
        bpy.data.objects.remove(obj, do_unlink=True)
floor = bpy.data.materials.new('Shared neutral study floor')
floor.use_nodes = True
floor.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value = (.065, .075, .049, 1)
floor.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value = .94
for x in [-.64, .64]:
    bpy.ops.mesh.primitive_plane_add(size=1.18, location=(x, 0, -.0002))
    bpy.context.object.data.materials.append(floor)
bpy.ops.object.camera_add(location=(0, -2.8, .75))
camera = bpy.context.object
camera.data.type = 'ORTHO'
camera.data.ortho_scale = 2.62
camera.rotation_euler = (Vector((0, .04, .018)) - camera.location).to_track_quat('-Z', 'Y').to_euler()
scene = bpy.context.scene
scene.camera = camera
scene.render.engine = 'CYCLES'
scene.cycles.samples = 24
scene.cycles.use_denoising = True
scene.world = bpy.data.worlds.new('Neutral inspection sky')
scene.world.use_nodes = True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value = (.24, .27, .30, 1)
bpy.ops.object.light_add(type='SUN', location=(3, -4, 10))
sun = bpy.context.object
sun.rotation_euler = (math.radians(28), math.radians(-30), math.radians(-25))
sun.data.energy = 2
sun.data.angle = math.radians(5)
scene.view_settings.view_transform = 'AgX'
scene.view_settings.look = 'AgX - Medium High Contrast'
scene.render.resolution_x = 1800
scene.render.resolution_y = 760
scene.render.resolution_percentage = 100
render.parent.mkdir(parents=True, exist_ok=True)
scene.render.filepath = str(render)
bpy.ops.render.render(write_still=True)
receipt = {'status': 'OFFLINE_GEOMETRY_COMPARISON_NOT_NATIVE', 'sourcePins': pins,
           'panels': [{'side': 'left', 'source': str(reference), 'actualInstances': counts[0]},
                      {'side': 'right', 'source': str(source), 'actualInstances': counts[1]}],
           'nativeAppearanceAccepted': False}
render.with_suffix('.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
