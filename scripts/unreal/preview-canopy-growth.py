"""Matched Cycles comparison of old canopy and three successor variants.

Photographic recipes are reproduced approximately for source inspection. This is
supporting geometry evidence; native Unreal pixels decide visual acceptance.
"""
import argparse
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source',required=True);parser.add_argument('--reference',required=True)
parser.add_argument('--family',choices=['broadleaf','upright','orchard'],default='upright')
parser.add_argument('--lod',type=int,default=0);parser.add_argument('--render',required=True)
opt=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);source,reference,render=map(lambda p:Path(p).resolve(),(opt.source,opt.reference,opt.render))
if render.exists():raise ValueError('Choose a fresh immutable diagnostic image')
bpy.ops.wm.read_factory_settings(use_empty=True)
manifest=json.loads((source/'geometry-manifest.json').read_text());old=json.loads((reference/'geometry-manifest.json').read_text())
recipes=json.loads((source/'material-manifest.json').read_text())
selected=[r for r in manifest['meshes']if r['id'].startswith('canopy_growth_'+opt.family+'_' )]
oldrow=next(r for r in old['meshes']if r['id']==f'canopy_{opt.family}_r1_b')
rows=[oldrow,*selected];objects=[]
for index,row in enumerate(rows):
    before=set(bpy.data.objects);bpy.ops.import_scene.gltf(filepath=row['glbPath'])
    wanted=row['lods'][opt.lod]['nodeName']
    for obj in list(set(bpy.data.objects)-before):
        if obj.name!=wanted:bpy.data.objects.remove(obj,do_unlink=True)
        else:objects.append(obj);obj.location=(index*7.-10.5,0,0)
for material in bpy.data.materials:
    key=material.name.split('.')[0]
    if key not in recipes:continue
    recipe=recipes[key];material.use_nodes=True;nodes=material.node_tree.nodes;links=material.node_tree.links;nodes.clear()
    output=nodes.new('ShaderNodeOutputMaterial');bsdf=nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Specular IOR Level'].default_value=recipe.get('specular',.25)
    textures={}
    for role,spec in recipe['maps'].items():
        texture=nodes.new('ShaderNodeTexImage');texture.image=bpy.data.images.load(spec['path'],check_existing=True)
        if role!='albedo':texture.image.colorspace_settings.name='Non-Color'
        textures[role]=texture
    colour=nodes.new('ShaderNodeMixRGB');colour.blend_type='MULTIPLY';colour.inputs[0].default_value=1
    colour.inputs[2].default_value=(*(v*recipe.get('albedoScale',1)for v in recipe.get('tint',[1,1,1])),1)
    links.new(textures['albedo'].outputs['Color'],colour.inputs[1]);links.new(colour.outputs[0],bsdf.inputs['Base Color'])
    links.new(textures['roughness'].outputs['Color'],bsdf.inputs['Roughness'])
    normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=recipe.get('normalStrength',1)
    split=nodes.new('ShaderNodeSeparateXYZ');join=nodes.new('ShaderNodeCombineXYZ');invert=nodes.new('ShaderNodeMath')
    invert.operation='SUBTRACT';invert.inputs[0].default_value=1
    links.new(textures['normal'].outputs['Color'],split.inputs[0]);links.new(split.outputs['X'],join.inputs['X'])
    links.new(split.outputs['Y'],invert.inputs[1]);links.new(invert.outputs[0],join.inputs['Y']);links.new(split.outputs['Z'],join.inputs['Z'])
    links.new(join.outputs[0],normal.inputs['Color']);links.new(normal.outputs[0],bsdf.inputs['Normal'])
    if 'alpha'in textures:
        transparent=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader')
        links.new(textures['alpha'].outputs['Color'],mix.inputs[0]);links.new(transparent.outputs[0],mix.inputs[1]);links.new(bsdf.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],output.inputs['Surface'])
    else:links.new(bsdf.outputs[0],output.inputs['Surface'])
    material.use_backface_culling=False
floor=bpy.data.materials.new('Neutral diagnostic ground');floor.use_nodes=True
floor.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.08,.082,.066,1)
floor.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.92
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.003));bpy.context.object.data.materials.append(floor)
height=oldrow['heightCm']/100
bpy.ops.object.camera_add(location=(0,-35,height*.85));camera=bpy.context.object;camera.data.type='ORTHO';camera.data.ortho_scale=29
camera.rotation_euler=(Vector((0,0,height*.49))-camera.location).to_track_quat('-Z','Y').to_euler()
scene=bpy.context.scene;scene.camera=camera;scene.render.engine='CYCLES';scene.cycles.samples=32;scene.cycles.use_denoising=True
scene.cycles.transparent_max_bounces=24
scene.world=bpy.data.worlds.new('Neutral inspection sky');scene.world.use_nodes=True
scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.20,.22,.25,1)
bpy.ops.object.light_add(type='SUN',location=(3,-4,10));sun=bpy.context.object
sun.rotation_euler=(math.radians(22),math.radians(-32),math.radians(-25));sun.data.energy=2.;sun.data.angle=math.radians(4)
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
scene.render.resolution_x=2200;scene.render.resolution_y=1100;scene.render.resolution_percentage=100
render.parent.mkdir(parents=True,exist_ok=True);scene.render.filepath=str(render);bpy.ops.render.render(write_still=True)
print('OFFLINE_STUDY_LEFT_R7_THEN_GROWTH_ABC',render,flush=True)
