"""CPU source inspection render; this is not native Unreal evidence."""
import argparse,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--asset',default='regional_broadleaf_a');parser.add_argument('--lod',type=int,default=0)
args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);folder=(ROOT/args.output).resolve()
bpy.ops.wm.open_mainfile(filepath=str(folder/'regional-authored.blend'))
manifest=json.loads((folder/'geometry-manifest.json').read_text());record=next(v for v in manifest['meshes'] if v['id']==args.asset)
recipes=json.loads((folder/'material-manifest.json').read_text());old=json.loads((ROOT/'output/unreal/exterior-assets-20260926-r5/material-manifest.json').read_text());recipes['ph_tree_small_02_branches']=old['ph_tree_small_02_branches']
for key,recipe in recipes.items():
 material=bpy.data.materials[key];nodes=material.node_tree.nodes;links=material.node_tree.links;nodes.clear()
 output=nodes.new('ShaderNodeOutputMaterial');bsdf=nodes.new('ShaderNodeBsdfPrincipled');bsdf.inputs['Specular IOR Level'].default_value=recipe.get('specular',.25);bsdf.inputs['Roughness'].default_value=.7
 textures={}
 for role,spec in recipe['maps'].items():
  if role=='mask':continue
  texture=nodes.new('ShaderNodeTexImage');texture.image=bpy.data.images.load(spec['path'],check_existing=True)
  if role!='albedo':texture.image.colorspace_settings.name='Non-Color'
  textures[role]=texture
 color=nodes.new('ShaderNodeMixRGB');color.blend_type='MULTIPLY';color.inputs[0].default_value=1;color.inputs[2].default_value=(*([recipe.get('albedoScale',1.)]*3),1)
 links.new(textures['albedo'].outputs['Color'],color.inputs[1]);links.new(color.outputs[0],bsdf.inputs['Base Color']);links.new(textures['roughness'].outputs['Color'],bsdf.inputs['Roughness'])
 normal=nodes.new('ShaderNodeNormalMap');normal.inputs['Strength'].default_value=recipe.get('normalStrength',1.)
 split=nodes.new('ShaderNodeSeparateXYZ');join=nodes.new('ShaderNodeCombineXYZ');invert=nodes.new('ShaderNodeMath');invert.operation='SUBTRACT';invert.inputs[0].default_value=1
 links.new(textures['normal'].outputs['Color'],split.inputs[0]);links.new(split.outputs['X'],join.inputs['X']);links.new(split.outputs['Y'],invert.inputs[1]);links.new(invert.outputs[0],join.inputs['Y']);links.new(split.outputs['Z'],join.inputs['Z']);links.new(join.outputs[0],normal.inputs['Color']);links.new(normal.outputs[0],bsdf.inputs['Normal'])
 if 'alpha' in textures:
  transparent=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader');links.new(textures['alpha'].outputs['Color'],mix.inputs[0]);links.new(transparent.outputs[0],mix.inputs[1]);links.new(bsdf.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],output.inputs[0])
 else:links.new(bsdf.outputs[0],output.inputs[0])
for obj in bpy.data.objects:obj.hide_render=obj.name!=args.asset+'_LOD'+str(args.lod)
height=record['heightCm']/100
bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,-.002));floor=bpy.context.object;mat=bpy.data.materials.new('neutral inspection ground');mat.diffuse_color=(.11,.13,.10,1);floor.data.materials.append(mat)
bpy.ops.object.camera_add(location=(height*1.3,-height*1.75,height*.77));camera=bpy.context.object;target=Vector((0,0,height*.48));camera.rotation_euler=(target-camera.location).to_track_quat('-Z','Y').to_euler();camera.data.type='ORTHO';camera.data.ortho_scale=max(height*1.16,record['radialEnvelopeCm']/100*2.15)
scene=bpy.context.scene;scene.camera=camera;scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.cycles.transparent_max_bounces=16
scene.render.resolution_x=1024;scene.render.resolution_y=1024;scene.render.resolution_percentage=100
scene.world=bpy.data.worlds.new('Neutral inspection sky');scene.world.use_nodes=True;scene.world.node_tree.nodes['Background'].inputs['Color'].default_value=(.18,.18,.18,1)
bpy.ops.object.light_add(type='SUN',location=(3,-4,10));sun=bpy.context.object;sun.rotation_euler=(math.radians(22),math.radians(-32),math.radians(-25));sun.data.energy=2.;sun.data.angle=math.radians(4)
scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast'
target=folder/'preview';target.mkdir(exist_ok=True);scene.render.filepath=str(target/(args.asset+'-lod'+str(args.lod)+'.png'));bpy.ops.render.render(write_still=True)
print('SOURCE PREVIEW',scene.render.filepath,flush=True)
