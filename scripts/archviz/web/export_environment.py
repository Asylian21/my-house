"""Render the saved Blender world only as a canonical RH Y-up web environment.
Install in scripts/archviz/web and run: blender -b --python SCRIPT -- --root REPO.
Never saves the source .blend. HDR contains linear radiance including world strength.
"""
import bpy,math,json,argparse,sys,time,hashlib
from pathlib import Path
from mathutils import Vector
parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[3]);parser.add_argument('--output',type=Path);parser.add_argument('--source',type=Path);parser.add_argument('--width',type=int,default=2048);parser.add_argument('--samples',type=int,default=16);args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
ROOT=args.root.resolve();OUT=(args.output or ROOT/'output/archviz/web').resolve();OUT.mkdir(parents=True,exist_ok=True);SOURCE=(args.source or ROOT/'output/archviz/dom-archviz.blend').resolve()
started=time.monotonic();bpy.ops.wm.open_mainfile(filepath=str(SOURCE));scene=bpy.context.scene
sun=next(o for o in scene.objects if o.type=='LIGHT' and o.data.type=='SUN')
ray=sun.matrix_world.to_quaternion()@Vector((0,0,-1));ray.normalize()
world=scene.world;sky=next(n for n in world.node_tree.nodes if n.type=='TEX_SKY');bg=next(n for n in world.node_tree.nodes if n.type=='BACKGROUND')
metadata={'source':SOURCE.name,'sourceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'skyType':sky.sky_type,'skySunDisc':sky.sun_disc,'worldStrengthIncludedInHDR':bg.inputs['Strength'].default_value,'skySunElevation':sky.sun_elevation,'skySunRotation':sky.sun_rotation,'sourceSunEnergy':sun.data.energy,'sourceSunColor':list(sun.data.color),'sourceSunAngularDiameter':sun.data.angle,'blenderSunRayDirection':list(ray),'babylonSunRayDirection':[ray.x,ray.z,-ray.y],'babylonDirectionTowardSun':[-ray.x,-ray.z,ray.y],'sourceViewTransform':scene.view_settings.view_transform,'sourceViewLook':scene.view_settings.look,'sourceExposureEV':scene.view_settings.exposure,'solarDateTime':scene.get('solar_datetime'),'coordinates':'Right-handed Y-up; native [BlenderX,BlenderZ,-BlenderY]','panoramaOrientation':{'u0.5v0.5':'+X','u0.75v0.5':'+Z','u0.25v0.5':'-Z','u0.5v0':'+Y','rotationY':0,'horizontalFlip':False},'recommendation':{'environmentIntensity':1,'imageProcessingExposure':2**scene.view_settings.exposure,'directSunIntensity':sun.data.energy,'directSunIntensityNote':'Source Blender sun energy is 3.5 W/m2-like irradiance; Babylon standard PBR intensity is not a physical unit equivalence. Start 3.5 and tune after IBL at 1 using neutral grey/white surfaces.','hdrUse':'HDRCubeTexture with gammaSpace=false and prefiltering; source world strength is already included.','backgroundUse':'sky.jpg is the same render with original AgX Medium High Contrast and exposure applied. Do not apply display tonemapping twice to the JPEG.','sunDiscNote':'Original source sky has sun_disc=false; a separate directional light is required and avoids duplicate sun in IBL.'}}
# Remove geometry and lights from this in-memory scene. Leave the exact saved world nodes.
for obj in list(bpy.data.objects):bpy.data.objects.remove(obj,do_unlink=True)
cam_data=bpy.data.cameras.new('Web environment | canonical equirectangular');camera=bpy.data.objects.new(cam_data.name,cam_data);scene.collection.objects.link(camera);scene.camera=camera
cam_data.type='PANO';cam_data.panorama_type='EQUIRECTANGULAR';camera.location=(0,0,0);camera.rotation_euler=(math.pi/2,0,-math.pi/2)
scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=args.samples;scene.cycles.use_denoising=False;scene.cycles.use_adaptive_sampling=False
scene.render.resolution_x=args.width;scene.render.resolution_y=args.width//2;scene.render.resolution_percentage=100;scene.render.film_transparent=False
scene.render.image_settings.file_format='OPEN_EXR';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.color_depth='32';scene.render.image_settings.exr_codec='ZIP';scene.render.filepath=str(OUT/'sky-linear.exr')
bpy.ops.render.render(write_still=True)
raw=bpy.data.images.load(str(OUT/'sky-linear.exr'),check_existing=False)
_ = raw.pixels[0]  # Force lazy EXR decoding before changing its output file path.
raw.file_format='HDR';raw.filepath_raw=str(OUT/'sky.hdr');raw.save()
scene.render.image_settings.file_format='JPEG';scene.render.image_settings.color_mode='RGB';scene.render.image_settings.quality=94
raw.save_render(str(OUT/'sky.jpg'),scene=scene)
# Record actual HDR range for sensible web exposure, and verify it remains HDR.
import numpy as np
pixels=np.empty(len(raw.pixels),dtype=np.float32);raw.pixels.foreach_get(pixels);rgb=pixels.reshape(-1,4)[:,:3];lum=rgb@np.array([.2126,.7152,.0722]);metadata['linearRadiance']={'min':float(rgb.min()),'max':float(rgb.max()),'meanLuminance':float(lum.mean()),'p50Luminance':float(np.percentile(lum,50)),'p95Luminance':float(np.percentile(lum,95))};metadata['width']=args.width;metadata['height']=args.width//2;metadata['samples']=args.samples;metadata['renderedMeshObjects']=0;metadata['elapsedSeconds']=round(time.monotonic()-started,2)
metadata['files']=[{'file':name,'bytes':(OUT/name).stat().st_size,'sha256':hashlib.sha256((OUT/name).read_bytes()).hexdigest()} for name in ('sky.hdr','sky.jpg')]
(OUT/'environment-manifest.json').write_text(json.dumps(metadata,indent=2))
print('ENVIRONMENT_READY',json.dumps(metadata),flush=True)
