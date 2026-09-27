"""Offline stove construction preview, using the verified installed Epic atlas.

This is an explicitly illustrative Blender render, never Unreal acceptance.
Only a new output directory is written; source geometry and textures are read-only.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
SPEC = importlib.util.spec_from_file_location('realism_stove_geometry', Path(__file__).with_name('realism-stove-geometry.py'))
G = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(G)
MATERIAL_SPEC = importlib.util.spec_from_file_location('realism_stove_materials', Path(__file__).with_name('realism-stove-materials.py'))
M = importlib.util.module_from_spec(MATERIAL_SPEC); MATERIAL_SPEC.loader.exec_module(M)
R = M.RECIPE


def main(study, probe, output):
    import bpy
    from mathutils import Vector
    study, probe, output = map(lambda value: Path(value).resolve(), (study, probe, output))
    G.require(not output.exists() and output.is_relative_to(ROOT/'output/unreal'), 'Use a new preview output directory')
    report = json.loads((study/'geometry-report.json').read_text())
    verified = json.loads((probe/'verified.json').read_text())
    G.require(report['generatorSha256'] == G.sha(G.__file__) and G.sha(study/report['glb']) == report['glbSha256'], 'Study source changed')
    G.require(verified['status'] == 'native-texture-probe-verified', 'Full native texture proof required')
    atlas = Path(verified['exports']['T_Fire_SubUV']['path'])
    G.require(G.sha(atlas) == verified['exports']['T_Fire_SubUV']['sha256'], 'Verified atlas bytes changed')
    source_dir = Path(report['sourceGeometry'])
    source, records, local, center = G.source(source_dir)
    meshes, _, _ = G.geometry(local)
    decoded = G.G.read_glb_positions(study/report['glb'], center)
    G.require(max(abs(x-y) for mesh in meshes for a,b in zip(mesh.positions, decoded[mesh.name])
                  for x,y in zip(a,G.rotate(b,-G.FACING))) < .002, 'Preview geometry differs from GLB')
    source_ids = {f'DOM_{n:05}' for n in range(553,572)}
    all_source = {row['id']:row for row in source['objects'] if row['id'] in source_ids}
    triangles = G.G.obj_geometry(source_dir/'dom-mm.obj', source_ids)
    output.mkdir(parents=True)
    bpy.ops.object.select_all(action='SELECT'); bpy.ops.object.delete(use_global=False)
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'; scene.cycles.device = 'CPU'; scene.cycles.samples = 32
    scene.cycles.use_denoising = True
    scene.render.resolution_x = 1500; scene.render.resolution_y = 1100; scene.render.resolution_percentage = 100
    scene.world.use_nodes = True
    scene.world.node_tree.nodes['Background'].inputs[0].default_value = (.63,.69,.76,1)
    scene.world.node_tree.nodes['Background'].inputs[1].default_value = .35
    scene.view_settings.view_transform = 'AgX'

    def material(name, color, roughness=.8, metal=0):
        mat = bpy.data.materials.new(name); mat.use_nodes = True
        shader = mat.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Base Color'].default_value = (*color,1)
        shader.inputs['Roughness'].default_value = roughness
        shader.inputs['Metallic'].default_value = metal
        return mat

    def linear(value):
        return value/12.92 if value <= .04045 else ((value+.055)/1.055)**2.4

    source_mats = {}
    for key in {row['materialSlots'][0] for row in all_source.values()}:
        row = source['materials'][key]
        mat = material(row['name'],tuple(linear(v) for v in row['color']),row['roughness'],row['metallic'])
        tree = mat.node_tree; shader = tree.nodes.get('Principled BSDF')
        if max(row['emission']) > 0:
            shader.inputs['Emission Color'].default_value = (*row['emission'],1)
            shader.inputs['Emission Strength'].default_value = 1
        if row['alpha'] < 1:
            transparent = tree.nodes.new('ShaderNodeBsdfTransparent')
            mix = tree.nodes.new('ShaderNodeMixShader'); mix.inputs[0].default_value = row['alpha']
            tree.links.new(transparent.outputs[0],mix.inputs[1]); tree.links.new(shader.outputs[0],mix.inputs[2])
            tree.links.new(mix.outputs[0],tree.nodes['Material Output'].inputs[0])
        source_mats[key] = mat

    chamber = material('Illustrative soot-black firebox',(.009,.007,.006),.95)
    char = material('Illustrative rough charcoal',(.014,.010,.008),.96)
    nodes, links = char.node_tree.nodes,char.node_tree.links
    tex = nodes.new('ShaderNodeTexNoise'); tex.inputs['Scale'].default_value=90; tex.inputs['Detail'].default_value=4
    bump = nodes.new('ShaderNodeBump'); bump.inputs['Strength'].default_value=.6; bump.inputs['Distance'].default_value=.0009
    links.new(tex.outputs['Fac'],bump.inputs['Height']); links.new(bump.outputs[0],nodes['Principled BSDF'].inputs['Normal'])
    ember = material('Illustrative restrained ember bed',(.016,.004,.001),.98)
    shader = ember.node_tree.nodes['Principled BSDF']
    shader.inputs['Emission Color'].default_value=(1,.025,.0006,1)
    noise=ember.node_tree.nodes.new('ShaderNodeTexNoise'); noise.inputs['Scale'].default_value=145; noise.inputs['Detail'].default_value=3
    ramp=ember.node_tree.nodes.new('ShaderNodeValToRGB'); ramp.color_ramp.elements[0].position=.42; ramp.color_ramp.elements[0].color=(0,0,0,1)
    ramp.color_ramp.elements[1].position=.72; ramp.color_ramp.elements[1].color=(.45,.45,.45,1)
    ember.node_tree.links.new(noise.outputs['Fac'],ramp.inputs[0]); ember.node_tree.links.new(ramp.outputs[0],shader.inputs['Emission Strength'])

    image = bpy.data.images.load(str(atlas),check_existing=True)
    flame_mats, clocks = [], []
    for index in range(3):
        mat = bpy.data.materials.new('Actual Epic atlas dual phase '+str(index)); mat.use_nodes=True
        nodes,links=mat.node_tree.nodes,mat.node_tree.links
        nodes.clear(); out=nodes.new('ShaderNodeOutputMaterial')
        def mathnode(operation,*values):
            node=nodes.new('ShaderNodeMath'); node.operation=operation
            for slot,value in enumerate(values):
                if isinstance(value,(int,float)): node.inputs[slot].default_value=value
                else: links.new(value,node.inputs[slot])
            return node.outputs[0]
        uv=nodes.new('ShaderNodeTexCoord'); separate=nodes.new('ShaderNodeSeparateXYZ'); links.new(uv.outputs['UV'],separate.inputs[0])
        local_u,local_v=separate.outputs['X'],separate.outputs['Y']
        clock=nodes.new('ShaderNodeValue'); clock.label='Seconds'; clock.outputs[0].default_value=.7; clocks.append(clock)
        phase=mathnode('FRACT',mathnode('MULTIPLY_ADD',clock.outputs[0],R['cycleHz'],index*R['cardPhaseStep']))
        def sample_frame(frame):
            col=mathnode('MODULO',frame,R['atlasGrid']); row=mathnode('FLOOR',mathnode('DIVIDE',frame,R['atlasGrid']))
            combine=nodes.new('ShaderNodeCombineXYZ')
            # Blender image UV origin is bottom-left, unlike Unreal's top-left.
            # Crop the bottom 4% of atlas padding to keep roots within the logs.
            u=mathnode('DIVIDE',mathnode('ADD',col,mathnode('MULTIPLY_ADD',local_u,R['uvScaleU'],R['uvInset'])),R['atlasGrid'])
            v=mathnode('SUBTRACT',1,mathnode('DIVIDE',mathnode('ADD',row,mathnode('MULTIPLY_ADD',mathnode('SUBTRACT',1,local_v),R['uvScaleV'],R['uvInset'])),R['atlasGrid']))
            links.new(u,combine.inputs['X']); links.new(v,combine.inputs['Y'])
            sample=nodes.new('ShaderNodeTexImage'); sample.image=image; sample.extension='EXTEND'; links.new(combine.outputs[0],sample.inputs[0])
            return sample.outputs['Color']
        values=[]
        for p in (phase,mathnode('FRACT',mathnode('ADD',phase,R['phaseOffset']))):
            frame=mathnode('MULTIPLY_ADD',p,R['frameMax']-R['frameMin'],R['frameMin']); lo=mathnode('FLOOR',frame); fraction=mathnode('FRACT',frame)
            a=sample_frame(lo); b=sample_frame(mathnode('MINIMUM',mathnode('ADD',lo,1),R['frameMax']))
            lerp=mathnode('ADD',mathnode('MULTIPLY',a,mathnode('SUBTRACT',1,fraction)),mathnode('MULTIPLY',b,fraction))
            weight=mathnode('POWER',mathnode('SINE',mathnode('MULTIPLY',p,math.pi)),2)
            values.append(mathnode('MULTIPLY',lerp,weight))
        intensity=mathnode('ADD',*values)
        # Limit the broad cap of the source plume without erasing its real texture.
        vertical=mathnode('POWER',mathnode('MAXIMUM',mathnode('SUBTRACT',1,local_v),0),R['tipPower'])
        sideways=mathnode('ABSOLUTE',mathnode('SUBTRACT',mathnode('MULTIPLY',local_u,2),1))
        width=mathnode('MULTIPLY_ADD',local_v,-R['taperSlope'],1)
        taper=mathnode('MINIMUM',mathnode('MAXIMUM',mathnode('MULTIPLY',mathnode('SUBTRACT',width,sideways),R['taperStrength']),0),1)
        root_t=mathnode('MINIMUM',mathnode('MAXIMUM',mathnode('DIVIDE',mathnode('SUBTRACT',local_v,R['rootFadeStart']),R['rootFadeEnd']-R['rootFadeStart']),0),1)
        root=mathnode('MULTIPLY',mathnode('MULTIPLY',root_t,root_t),mathnode('MULTIPLY_ADD',root_t,-2,3))
        intensity=mathnode('MULTIPLY',intensity,mathnode('MULTIPLY',root,mathnode('MULTIPLY',vertical,taper)))
        intensity=mathnode('MINIMUM',mathnode('MAXIMUM',intensity,0),1)
        emission=nodes.new('ShaderNodeEmission'); links.new(mathnode('MULTIPLY',intensity,R['emissionStrength']),emission.inputs[1])
        tint=nodes.new('ShaderNodeValToRGB')
        for element,stop in zip((tint.color_ramp.elements[0],tint.color_ramp.elements.new(R['tintStops'][1][0]),tint.color_ramp.elements[-1]),R['tintStops']):
            element.position=stop[0]; element.color=(*stop[1],1)
        links.new(intensity,tint.inputs[0]); links.new(tint.outputs[0],emission.inputs[0])
        transparent=nodes.new('ShaderNodeBsdfTransparent'); add=nodes.new('ShaderNodeAddShader')
        links.new(transparent.outputs[0],add.inputs[0]); links.new(emission.outputs[0],add.inputs[1]); links.new(add.outputs[0],out.inputs[0])
        flame_mats.append(mat)

    groups={'before':[],'after':[]}
    def mesh_object(name,positions,indices,materials,group,uvs=None):
        data=bpy.data.meshes.new(name)
        data.from_pydata([(x/1000,y/1000,z/1000) for x,y,z in positions],[],[indices[i:i+3] for i in range(0,len(indices),3)]); data.update()
        for mat in materials: data.materials.append(mat)
        if uvs:
            layer=data.uv_layers.new()
            for polygon in data.polygons:
                for index in polygon.loop_indices:
                    uv=uvs[data.loops[index].vertex_index]
                    layer.data[index].uv=(uv[0]%2,uv[1])
                if len(materials)>1:
                    polygon.material_index=int(uvs[data.loops[polygon.loop_start].vertex_index][0]//2)
        obj=bpy.data.objects.new(name,data); bpy.context.collection.objects.link(obj); groups[group].append(obj)
        return obj

    for group in groups:
        for id_,row in all_source.items():
            if group=='after' and id_ in report['hiddenSourceIds']: continue
            points=[G.rotate((p[0]-center[0],p[1]-center[1],p[2]),-G.FACING) for tri in triangles[id_] for p in tri]
            obj=mesh_object(group+'_'+id_,points,list(range(len(points))),[source_mats[row['materialSlots'][0]]],group)
            if id_ in ('DOM_00553','DOM_00555','DOM_00557','DOM_00571'):
                for face in obj.data.polygons: face.use_smooth=True
    for mesh in meshes:
        materials={'shell':[source_mats['MAT_0034']], 'chamber':[chamber], 'logs':[char], 'embers':[ember], 'flames':flame_mats}[mesh.role]
        obj=mesh_object(mesh.name,mesh.positions,mesh.indices,materials,'after',mesh.uvs)
        if mesh.role in ('shell','logs'):
            obj.data.normals_split_custom_set_from_vertices(mesh.normals)
            for face in obj.data.polygons: face.use_smooth=True

    bpy.ops.mesh.primitive_plane_add(size=200,location=(0,0,0)); bpy.context.object.data.materials.append(material('Preview ground',(.13,.12,.11),.9))
    for location,power,size in [((2,-3,4),450,4),((-2,1,2),200,3)]:
        bpy.ops.object.light_add(type='AREA',location=location); obj=bpy.context.object
        obj.rotation_euler=(Vector((0,0,.8))-obj.location).to_track_quat('-Z','Y').to_euler(); obj.data.energy=power; obj.data.shape='DISK'; obj.data.size=size
    bpy.ops.object.camera_add(); camera=bpy.context.object; camera.data.type='ORTHO'; scene.camera=camera
    outputs=[]
    for label,location,target,scale in [('full',(2.6,-1.0,1.3),(0,0,.79),1.8),('window',(2.4,-.65,1.2),(0,0,.71),.83)]:
        camera.location=location; camera.rotation_euler=(Vector(target)-camera.location).to_track_quat('-Z','Y').to_euler(); camera.data.ortho_scale=scale
        for group in groups:
            for name,objects in groups.items():
                for obj in objects: obj.hide_render=name!=group
            file=output/(label+'-'+group+'.png'); scene.render.filepath=str(file); bpy.ops.render.render(write_still=True)
            outputs.append({'path':str(file),'sha256':G.sha(file),'view':label,'variant':group})
    # A 4.5s moving preview spans two complete plume cycles and their seam.
    scene.render.resolution_x=800; scene.render.resolution_y=600; scene.cycles.samples=8
    frames=output/'frames'; frames.mkdir()
    for name,objects in groups.items():
        for obj in objects: obj.hide_render=name!='after'
    for frame in range(108):
        seconds=frame/24
        for clock in clocks: clock.outputs[0].default_value=seconds
        angle=-.3+.10*math.sin(seconds*math.tau/4.5)
        camera.location=(2.4*math.cos(angle),2.4*math.sin(angle),1.2)
        camera.rotation_euler=(Vector((0,0,.71))-camera.location).to_track_quat('-Z','Y').to_euler()
        scene.render.filepath=str(frames/f'{frame:04d}.png'); bpy.ops.render.render(write_still=True)
    video=output/'stove-animation-offline.mp4'
    subprocess.run(['/opt/homebrew/bin/ffmpeg','-hide_banner','-loglevel','error','-framerate','24','-i',str(frames/'%04d.png'),'-c:v','libx264','-crf','20','-pix_fmt','yuv420p',str(video)],check=True)
    receipt={'status':'offline-preview-rendered','nativeRenderedVerified':False,'blenderVersion':bpy.app.version_string,
             'sourceStudyReportSha256':G.sha(study/'geometry-report.json'),'sourceGlbSha256':report['glbSha256'],
             'nativeTextureVerifiedSha256':G.sha(probe/'verified.json'),'atlasPngSha256':G.sha(atlas),'scriptSha256':G.sha(__file__),
             'sourceIdsPreserved':report['preservedSourceIds'],'outputs':outputs,
             'animation':{'path':str(video),'sha256':G.sha(video),'seconds':4.5,'frames':108,'fps':24,
                          'recipe':R,'recipeSha256':hashlib.sha256(json.dumps(R,sort_keys=True,separators=(',',':')).encode()).hexdigest(),
                          'weight':'sin(pi*phase)^2','adjacentFrameInterpolation':True,'shaderBlend':'Transparent+Emission additive'},
             'limitations':['Illustrative Blender material/lighting translation, not native Unreal rendering.',
                            'Actual exported Epic atlas animates with two interpolated phases; native glass sorting remains unverified.',
                            'No world light is added for fire; all original scene lighting remains outside this study.']}
    (output/'preview-report.json').write_text(json.dumps(receipt,indent=2)+'\n')


if __name__=='__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('--study',required=True); parser.add_argument('--probe',required=True); parser.add_argument('--output',required=True)
    args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]); main(args.study,args.probe,args.output)
