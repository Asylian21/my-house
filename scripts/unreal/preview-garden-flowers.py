"""Blender/Cycles close view of spatial pink flowers; diagnostic, not native QA."""
import argparse
import json
from pathlib import Path
import sys

import bpy
from mathutils import Vector

args=sys.argv[sys.argv.index('--')+1:]if '--'in sys.argv else []
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',required=True);parser.add_argument('--render',required=True)
opt=parser.parse_args(args);source=Path(opt.source).resolve();render=Path(opt.render).resolve()
if render.exists():raise ValueError('Diagnostic render is immutable; choose a fresh path')
bpy.ops.wm.read_factory_settings(use_empty=True)
manifest=json.loads((source/'geometry-manifest.json').read_text())
bpy.ops.import_scene.gltf(filepath=manifest['meshes'][0]['glbPath'])
recipes=json.loads((source/'material-manifest.json').read_text())
keep=[row['lods'][0]['nodeName']for row in manifest['meshes']]
objects={o.name:o for o in bpy.data.objects if o.name in keep}
for obj in list(bpy.data.objects):
    if obj.name not in keep:bpy.data.objects.remove(obj,do_unlink=True)
for key,recipe in recipes.items():
    material=bpy.data.materials.get(key)
    if material is None:continue
    material.use_nodes=True;nodes=material.node_tree.nodes;links=material.node_tree.links;nodes.clear()
    out=nodes.new('ShaderNodeOutputMaterial');bsdf=nodes.new('ShaderNodeBsdfPrincipled');links.new(bsdf.outputs['BSDF'],out.inputs['Surface'])
    bsdf.inputs['Roughness'].default_value=recipe.get('roughness',.8)
    bsdf.inputs['Specular IOR Level'].default_value=recipe.get('specular',.12)
    if recipe['kind']=='authored-foliage':
        rgb=nodes.new('ShaderNodeRGB');rgb.outputs[0].default_value=(*recipe['linearColor'],1)
        attribute=nodes.new('ShaderNodeVertexColor')
        attribute.layer_name=next((o.data.color_attributes[0].name for o in objects.values()if o.data.color_attributes),'Color')
        blend=nodes.new('ShaderNodeMixRGB');blend.blend_type='MULTIPLY';blend.inputs[0].default_value=1
        links.new(rgb.outputs[0],blend.inputs[1]);links.new(attribute.outputs['Color'],blend.inputs[2]);links.new(blend.outputs[0],bsdf.inputs['Base Color'])
    else:
        for channel,spec in recipe['maps'].items():
            texture=nodes.new('ShaderNodeTexImage');texture.image=bpy.data.images.load(spec['path'])
            if channel!='albedo':texture.image.colorspace_settings.name='Non-Color'
            if channel=='albedo':
                colour=nodes.new('ShaderNodeMixRGB');colour.blend_type='MULTIPLY';colour.inputs[0].default_value=1
                colour.inputs[2].default_value=(*(v*recipe.get('albedoScale',1)for v in recipe.get('tint',[1,1,1])),1)
                links.new(texture.outputs['Color'],colour.inputs[1]);links.new(colour.outputs[0],bsdf.inputs['Base Color'])
            elif channel=='roughness':links.new(texture.outputs['Color'],bsdf.inputs['Roughness'])
            elif channel=='alpha':links.new(texture.outputs['Color'],bsdf.inputs['Alpha']);material.surface_render_method='DITHERED'
    material.use_backface_culling=False
objects[keep[0]].location=(-.28,0,0);objects[keep[1]].location=(.29,.11,0)
ground=bpy.data.materials.new('Neutral flower diagnostic');ground.diffuse_color=(.045,.036,.022,1);ground.use_nodes=True
ground.node_tree.nodes.get('Principled BSDF').inputs['Roughness'].default_value=.94
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.001));bpy.context.object.data.materials.append(ground)
bpy.ops.object.light_add(type='AREA',location=(-2,-3,4));light=bpy.context.object;light.data.energy=650;light.data.size=3
light.rotation_euler=(Vector((0,0,.22))-light.location).to_track_quat('-Z','Y').to_euler()
bpy.ops.object.camera_add(location=(.95,-1.70,.85));camera=bpy.context.object;camera.data.lens=58
camera.rotation_euler=(Vector((0,0,.24))-camera.location).to_track_quat('-Z','Y').to_euler()
scene=bpy.context.scene;scene.camera=camera;scene.render.engine='CYCLES';scene.cycles.samples=64;scene.cycles.use_denoising=True
scene.world=bpy.data.worlds.new('Diagnostic world');scene.world.color=(.17,.20,.25)
scene.render.resolution_x=1600;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
scene.view_settings.view_transform='AgX';render.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(render)
bpy.ops.render.render(write_still=True)
print('OFFLINE_CYCLES_DIAGNOSTIC_NOT_NATIVE',render)
