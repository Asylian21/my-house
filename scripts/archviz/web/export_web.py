"""Read-only source scene to portable glTF. Run blender -b SOURCE.blend --python export_web.py.
Outputs only beside this script. Source .blend is never saved.
"""
import bpy,bmesh,json,re,math,time,hashlib,struct,argparse,sys
from pathlib import Path
from mathutils import Vector
sys.path.insert(0,str(Path(__file__).resolve().parent))
from tree_foliage import build_leaf_safe_tree
START=time.monotonic()
parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[3]);parser.add_argument('--output',type=Path);parser.add_argument('--source',type=Path);args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
ROOT=args.root.resolve();OUT=(args.output or ROOT/'output/archviz/web').resolve();OUT.mkdir(parents=True,exist_ok=True);SOURCE=(args.source or ROOT/'output/archviz/dom-archviz.blend').resolve()
if Path(bpy.data.filepath).resolve()!=SOURCE:bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
SCENE=json.loads((ROOT/'output/archviz/scene.json').read_text()); RECORDS={r['id']:r for r in SCENE['objects']}
TEXTURES=json.loads((OUT/'texture-index.json').read_text()); ASSETS=ROOT/'output/archviz/assets'
manifest={'version':1,'source':'dom-archviz.blend','sourceSha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),'blender':bpy.app.version_string,'units':'metres','up':'Y','files':[],'hiddenSourceNames':[],'appearanceHiddenSourceNames':[],'disabledSourceNames':[],'plantPrototypes':[],'notes':['Source .blend remains unchanged.','Cycles shaders converted to portable PBR with original scanned source maps, 1024px maximum.','World-position box materials converted to metre-scaled UVs; foliage uses alpha cutout.','No baked global illumination; web renderer supplies sun, IBL, shadows and ambient occlusion.']}
def progress(*a):print('WEB_EXPORT',*a,flush=True)
# Remove lawn geometry-node distribution before dependency graph evaluation.
for o in list(bpy.data.objects):
 for mod in list(o.modifiers):
  if mod.type=='NODES':o.modifiers.remove(mod)
 for mod in o.modifiers:
  if mod.type=='BEVEL':mod.segments=min(mod.segments,2)
  # Keep optical water volume in the source; browser water remains a single shell.
 if 'real-pool-water' in o.get('source_materials',''):
  for mod in list(o.modifiers):o.modifiers.remove(mod)
source_objects=[]
for o in bpy.context.scene.objects:
 if o.type!='MESH' or not o.get('source_name'):continue
 rec=RECORDS.get(o.name.split(' | ')[0])
 if not rec:continue
 o['source_group']=rec['group'];o['source_enabled']=rec['enabled'];o['source_export_id']=rec['id']
 if o.hide_render or not rec['enabled']:
  manifest['hiddenSourceNames'].append(o['source_name'])
  manifest['appearanceHiddenSourceNames' if rec['enabled'] and rec['group'] not in ('Foundations','Services') else 'disabledSourceNames'].append(o['source_name']);continue
 source_objects.append(o)
living=list(bpy.data.collections['ArchViz | Living vegetation'].objects)
terrace=list(bpy.data.collections['ArchViz | Terrace furniture'].objects)
grass=bpy.data.objects.get('Bermuda tuft | shared geometry')
# Reduce one mesh of each linked prototype, then reuse it for all placements.
for mesh in set(o.data for o in living):
 objects=[o for o in living if o.data==mesh];ob=objects[0]
 before=sum(len(p.vertices)-2 for p in mesh.polygons)
 if 'tree' in ob.name:
  new,canopy_report=build_leaf_safe_tree(ob)
  manifest['treeFoliageCorrection']=canopy_report
  for obj in objects:obj.data=new
 else:
  ratio=min(1,1800/max(before,1))
  if ratio<1:
   mod=ob.modifiers.new('Web shared prototype budget','DECIMATE');mod.ratio=ratio
   dg=bpy.context.evaluated_depsgraph_get();new=bpy.data.meshes.new_from_object(ob.evaluated_get(dg),depsgraph=dg)
   for mod in list(ob.modifiers):ob.modifiers.remove(mod)
   for obj in objects:obj.data=new
 after=sum(len(p.vertices)-2 for p in ob.data.polygons)
 manifest['plantPrototypes'].append({'name':ob.name,'instances':len(objects),'trianglesBefore':before,'trianglesAfter':after})
 progress('prototype',ob.name,len(objects),before,'->',after)
for o in living+terrace:
 o['source_name']=o.name;o['source_id']=o.name;o['source_group']='ArchVizVegetation' if o in living else 'ArchVizTerrace';o['source_enabled']=True;o['visualization_only']=True;o['asset_license']='CC0 | Poly Haven'
if grass:
 grass['source_name']='Bermuda tuft | shared geometry';grass['source_id']='archviz-grass-prototype';grass['source_group']='ArchVizGrass';grass['visualization_only']=True
all_objects=source_objects+living+terrace+([grass] if grass else [])
# Convert EXR non-color maps using Blender's actual image decoder, with no film transform.
for src in sorted(ASSETS.glob('*/textures/*.exr')):
 if not any(k in src.stem for k in ('_rough_','_nor_gl_')):continue
 key=src.stem.replace('_1k','').replace('_2k','')
 if key in TEXTURES and Path(TEXTURES[key]).suffix=='.jpg':continue
 im=bpy.data.images.load(str(src),check_existing=False);im.colorspace_settings.name='Non-Color'
 cap=512 if '_rough_' in src.stem else 1024
 if max(im.size)>cap:im.scale(cap,cap)
 dest=OUT/'textures'/(key+'.jpg');im.filepath_raw=str(dest);im.file_format='JPEG';im.save()
 TEXTURES[key]=str(dest)
(OUT/'texture-index.json').write_text(json.dumps(TEXTURES,indent=2))
cache={}
def tex(nodes,key,color=False):
 if key not in TEXTURES:return None
 ckey=(key,color)
 if ckey not in cache:
  image=bpy.data.images.load(TEXTURES[key],check_existing=False);image.colorspace_settings.name='sRGB' if color else 'Non-Color';cache[ckey]=image
 n=nodes.new('ShaderNodeTexImage');n.image=cache[ckey];n.interpolation='Linear';n.extension='REPEAT';return n
material_uv={};alpha_materials=[]
materials=set(m for o in all_objects for m in o.data.materials if m)
for old in materials:
 src_name=old.get('source_material',old.name);asset=old.get('asset');tile=old.get('tile_size_m',1)
 old_bs=next((n for n in old.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None) if old.use_nodes else None
 defaults={}
 if old_bs:
  for k in ('Base Color','Metallic','Roughness','IOR','Transmission Weight','Coat Weight','Coat Roughness','Sheen Weight','Emission Color','Emission Strength','Specular IOR Level'):
   if k in old_bs.inputs:
    v=old_bs.inputs[k].default_value;defaults[k]=list(v) if hasattr(v,'__len__') else v
 images=[n.image for n in old.node_tree.nodes if n.type=='TEX_IMAGE' and n.image] if old.use_nodes else []
 old.use_nodes=True;nodes,links=old.node_tree.nodes,old.node_tree.links;nodes.clear()
 bs=nodes.new('ShaderNodeBsdfPrincipled');output=nodes.new('ShaderNodeOutputMaterial');links.new(bs.outputs[0],output.inputs['Surface'])
 for k,v in defaults.items():bs.inputs[k].default_value=v
 diffuse=rough=normal=metal=None;alpha=False;normal_strength=.55
 if asset in ('white_plaster_02','leafy_grass','gravel_floor_02','hinoki_planks','concrete_pavement'):
  diffuse=('mulch' if src_name=='real-mulch' else asset)+'-diffuse';rough=asset+'-roughness';normal=asset+'-normal'
  if asset=='leafy_grass':rough=None;bs.inputs['Roughness'].default_value=1
  cladding=re.search(r'larch-.*:([0-9.]+)x([0-9.]+)$',src_name)
  material_uv[old]=('larch',float(cladding[1])/tile,float(cladding[2])/tile) if cladding else ('box',tile)
  normal_strength=.2 if asset=='white_plaster_02' else .55
 elif old.name=='ArchViz | Living hedge leaves':
  diffuse='shrub_02_diff';rough='shrub_02_rough';normal='shrub_02_nor_gl';alpha=True;bs.inputs['Roughness'].default_value=.75
 elif old.name=='ArchViz | Dry living grass blades':
  diffuse='grass_bermuda_01_diff';alpha=True;bs.inputs['Roughness'].default_value=.95
 elif old.name.startswith('tree_small_02') or old.name.startswith('outdoor_table_chair_set_01'):
  for im in images:
   key=Path(im.filepath).stem.replace('_1k','').replace('_2k','')
   if '_diff' in key:diffuse=key
   elif '_rough' in key:rough=key
   elif '_nor_gl' in key:normal=key
   elif '_metal' in key:metal=key
   elif '_alpha' in key:alpha=True
 else:
  linked_color=old_bs is not None # Known source material rules below discard unused tint textures.
  for im in images:
   stem=Path(im.filepath).stem
   if 'albedo' in stem:
    diffuse='native-'+stem;normal=diffuse.replace('albedo','normal')
    break
  if src_name in ('real-glass-frame','real-glass-frame-wood','real-fence-metal','real-roof-edge'):
   diffuse=None;normal='native-metal-anthracite-normal';material_uv[old]=('box',.15);normal_strength=.08
  if src_name=='real-roof':
   diffuse=None;normal='native-metal-anthracite-normal';material_uv[old]=('box',.7);normal_strength=.18
  if any(x in src_name for x in ('fabric','linen','wool','throw','upholstery','cork')) and not normal:
   normal='native-boucle-taupe-normal';material_uv[old]=('box',.35);normal_strength=.2
  if 'ember' in src_name or 'warm-light' in src_name or 'pool-led' in src_name:
   bs.inputs['Emission Color'].default_value=(1,.48,.17,1);bs.inputs['Emission Strength'].default_value=2 if 'ember' in src_name else 1
 dn=tex(nodes,diffuse,True) if diffuse else None
 if dn:
  links.new(dn.outputs['Color'],bs.inputs['Base Color'])
  if alpha:links.new(dn.outputs['Alpha'],bs.inputs['Alpha'])
 rn=tex(nodes,rough) if rough else None
 if rn:links.new(rn.outputs['Color'],bs.inputs['Roughness'])
 mn=tex(nodes,metal) if metal else None
 if mn:links.new(mn.outputs['Color'],bs.inputs['Metallic'])
 nn=tex(nodes,normal) if normal else None
 if nn:
  nm=nodes.new('ShaderNodeNormalMap');nm.inputs['Strength'].default_value=normal_strength;links.new(nn.outputs['Color'],nm.inputs['Color']);links.new(nm.outputs[0],bs.inputs['Normal'])
 if alpha:
  alpha_materials.append(old.name);old.surface_render_method='DITHERED';old.use_backface_culling=False
 old['web_pbr']=True;old['web_source_shader']='Cycles Principled converted to explicit glTF PBR textures'
progress('materials',len(materials),'textures',len(cache))
# Apply static bevels and convert triplanar world UVs into portable UV coordinates.
dg=bpy.context.evaluated_depsgraph_get()
for i,o in enumerate(source_objects):
 if o.modifiers:
  new=bpy.data.meshes.new_from_object(o.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg)
  for mod in list(o.modifiers):o.modifiers.remove(mod)
  o.data=new
 mesh=o.data
 if any(m in material_uv for m in mesh.materials):
  uv=mesh.uv_layers.active or mesh.uv_layers.new(name='UVMap')
  for p in mesh.polygons:
   if p.material_index>=len(mesh.materials):continue
   mode=material_uv.get(mesh.materials[p.material_index])
   if not mode:continue
   if mode[0]=='larch':
    for index in p.loop_indices:
     v=uv.data[index].uv.copy();uv.data[index].uv=(-v.y*mode[2],v.x*mode[1])
   else:
    axis=max(range(3),key=lambda a:abs(p.normal[a]));tile=mode[1]
    for index in p.loop_indices:
     v=o.matrix_world@mesh.vertices[mesh.loops[index].vertex_index].co
     pair=(v.y,v.z) if axis==0 else (v.x,v.z) if axis==1 else (v.x,v.y)
     uv.data[index].uv=(pair[0]/tile,pair[1]/tile)
 if i%250==0:progress('geometry',i,len(source_objects))
# Triangulate only ngons so glTF gets an explicit tangent basis on every normal-mapped mesh.
for mesh in set(o.data for o in all_objects):
 if any(len(p.vertices)>4 for p in mesh.polygons):
  bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.triangulate(bm,faces=[f for f in bm.faces if len(f.verts)>4]);bm.to_mesh(mesh);bm.free();mesh.update()
# Ensure source selection isn't blocked by viewport visibility from the render scene.
for o in all_objects:o.hide_set(False);o.hide_viewport=False
bpy.context.view_layer.update()
def read_glb(path):
 data=path.read_bytes();length,typ=struct.unpack_from('<II',data,12);doc=json.loads(data[20:20+length]);return doc,data[20+length:]
def write_glb(path,doc,tail):
 raw=json.dumps(doc,separators=(',',':'),ensure_ascii=False).encode();raw+=b' '*((-len(raw))%4)
 path.write_bytes(struct.pack('<III',0x46546C67,2,12+8+len(raw)+len(tail))+struct.pack('<II',len(raw),0x4E4F534A)+raw+tail)
def export(objects,name,kind,depth=0):
 if not objects:return
 bpy.ops.object.select_all(action='DESELECT')
 for o in objects:o.select_set(True)
 path=OUT/name
 bpy.ops.export_scene.gltf(filepath=str(path),export_format='GLB',use_selection=True,export_yup=True,export_extras=True,export_animations=False,export_apply=False,export_cameras=False,export_lights=False,export_image_format='AUTO',export_image_quality=88,export_shared_accessors=True,export_tangents=True)
 doc,tail=read_glb(path)
 for m in doc.get('materials',[]):
  if m.get('name') in alpha_materials:m['alphaMode']='MASK';m['alphaCutoff']=.45;m['doubleSided']=True
 write_glb(path,doc,tail)
 if path.stat().st_size>20*1024*1024 and len(objects)>1:
  path.unlink();mid=len(objects)//2
  export(objects[:mid],name.replace('.glb','-a.glb'),kind,depth+1);export(objects[mid:],name.replace('.glb','-b.glb'),kind,depth+1);return
 tri=sum(doc['accessors'][p['indices']]['count']//3 for m in doc.get('meshes',[]) for p in m['primitives'] if 'indices'in p)
 sources=[o.get('source_name',o.name) for o in objects]
 stats={'file':name,'kind':kind,'bytes':path.stat().st_size,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'objects':len(objects),'nodes':len(doc.get('nodes',[])),'meshes':len(doc.get('meshes',[])),'uniqueTriangles':tri,'placedTriangles':sum(sum(len(p.vertices)-2 for p in o.data.polygons) for o in objects),'materials':len(doc.get('materials',[])),'images':len(doc.get('images',[])),'sourceNames':sources,'extensions':doc.get('extensionsUsed',[])}
 manifest['files'].append(stats);progress('file',name,stats['bytes'],stats['meshes'],tri,stats['images'])
architecture=[o for o in source_objects if o['source_group'] not in ('Interior','Landscape','Site','Fence','Hardscape')]
interior=[o for o in source_objects if o['source_group']=='Interior']
landscape=[o for o in source_objects if o['source_group'] in ('Landscape','Site','Fence','Hardscape')]
export(architecture,'dom-architecture.glb','architecture')
# Split large interior by triangle budget to keep hosting files comfortably below 25 MiB.
chunks=[[]];count=0
for o in interior:
 tris=sum(len(p.vertices)-2 for p in o.data.polygons)
 if count+tris>95000 and chunks[-1]:chunks.append([]);count=0
 chunks[-1].append(o);count+=tris
for i,chunk in enumerate(chunks):export(chunk,f'dom-interior-{i+1:02}.glb','interior')
export(landscape,'dom-landscape.glb','landscape');export(living,'dom-living.glb','living');export(terrace,'dom-terrace.glb','terrace')
if grass:export([grass],'dom-grass-prototype.glb','grass-prototype')
manifest['elapsedSeconds']=round(time.monotonic()-START,2);manifest['textureMaxSize']=1024
(OUT/'export-manifest.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False))
lock=json.loads((ROOT/'scripts/archviz/assets.lock.json').read_text())
used={'white_plaster_02','leafy_grass','gravel_floor_02','hinoki_planks','concrete_pavement','shrub_02','tree_small_02','grass_bermuda_01','outdoor_table_chair_set_01'}
credits={'title':'DOM | Blender web assets','credit':lock.get('credit','Powered by Poly Haven'),'license':lock.get('license','CC0-1.0'),'licenseUrl':lock.get('licenseUrl','https://polyhaven.com/license'),'assets':[{'id':key,'page':spec.get('page','https://polyhaven.com/a/'+key),'authors':spec.get('authors',{}),'license':'CC0-1.0'} for key,spec in {**lock['assets'],**lock.get('models',{})}.items() if key in used],'projectMaterials':'Additional interior material maps are existing DOM project assets.'}
(OUT/'credits.json').write_text(json.dumps(credits,indent=2,ensure_ascii=False))
progress('COMPLETE',manifest['elapsedSeconds'],'seconds',sum(f['bytes'] for f in manifest['files']),'bytes')
