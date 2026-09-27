"""Controlled Blender silhouette comparison; never a native Unreal acceptance."""
import argparse
import json
from pathlib import Path
import sys


def main(source, candidate, output):
    import bpy
    from mathutils import Vector
    source = json.loads(Path(source).read_text())
    candidate = json.loads(Path(candidate).read_text())
    output = Path(output); output.mkdir(parents=True, exist_ok=True)
    original = {m['id']:m for m in source['meshes']}
    updated = {m['id']:m for m in candidate['meshes']}
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'; scene.cycles.samples = 24
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1600; scene.render.resolution_y = 1100; scene.render.resolution_percentage = 100
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.60, .71, .85, 1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .5
    scene.view_settings.view_transform = 'AgX'
    materials = {}
    for key, color, roughness in [('bark', (.100,.071,.041,1),.96), ('leaf',(.080,.133,.035,1),.76)]:
        material = bpy.data.materials.new(key); material.use_nodes = True
        node = material.node_tree.nodes.get('Principled BSDF')
        node.inputs['Base Color'].default_value = color
        node.inputs['Roughness'].default_value = roughness
        if key == 'leaf':
            tree = material.node_tree; translucent = tree.nodes.new('ShaderNodeBsdfTranslucent')
            translucent.inputs['Color'].default_value = tuple(v*.55 for v in color[:3])+(1,)
            blend = tree.nodes.new('ShaderNodeMixShader'); blend.inputs[0].default_value = .25
            tree.links.new(node.outputs[0], blend.inputs[1]); tree.links.new(translucent.outputs[0], blend.inputs[2])
            tree.links.new(blend.outputs[0], tree.nodes['Material Output'].inputs[0])
        materials[key] = material
    for variant in range(3):
        for lod in (0, 2):
            bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
            for stage, records, prefix, offset in [('before', original, '', -3.2), ('after', updated, 'realism_', 3.2)]:
                for kind in ('bark', 'leaf'):
                    row = records[f'{prefix}tree_{kind}_{variant}']; level = [row,*row['lods']][lod]
                    data = bpy.data.meshes.new(stage+'_'+kind)
                    # Undo native clockwise winding for a right-handed preview.
                    indices = level['indices']; faces = [(indices[i],indices[i+2],indices[i+1]) for i in range(0,len(indices),3)]
                    data.from_pydata([(p[0]/100,p[1]/100,p[2]/100) for p in level['verticesCm']],[],faces)
                    data.materials.append(materials[kind]); data.update()
                    for polygon in data.polygons: polygon.use_smooth = kind == 'bark'
                    obj = bpy.data.objects.new(stage+'_'+kind,data); bpy.context.collection.objects.link(obj)
                    obj.location.x = offset
            bpy.ops.mesh.primitive_plane_add(size=200, location=(0,0,-.025))
            ground = bpy.data.materials.new('ground'); ground.diffuse_color = (.17,.17,.15,1)
            ground.use_nodes=True; ground.node_tree.nodes['Principled BSDF'].inputs['Base Color'].default_value=(.17,.17,.15,1)
            ground.node_tree.nodes['Principled BSDF'].inputs['Roughness'].default_value=.9
            bpy.context.object.data.materials.append(ground)
            bpy.ops.object.light_add(type='SUN', location=(2,-4,8)); sun=bpy.context.object
            sun.rotation_euler=(.48,-.42,-.7); sun.data.energy=2.5; sun.data.angle=.055
            target_z=candidate['prototypes'][variant]['sourceEnvelopeCm']['max'][2]/200
            bpy.ops.object.camera_add(location=(0,-23,target_z+5.6)); camera=bpy.context.object
            camera.rotation_euler=(Vector((0,0,target_z))-camera.location).to_track_quat('-Z','Y').to_euler()
            camera.data.type='ORTHO'; camera.data.ortho_scale=16.5; scene.camera=camera
            scene.render.filepath=str(output/f'variant-{variant}-lod-{lod}-before-left-after-right.png')
            bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--source',required=True); parser.add_argument('--candidate',required=True); parser.add_argument('--output',required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:])
    main(args.source,args.candidate,args.output)
