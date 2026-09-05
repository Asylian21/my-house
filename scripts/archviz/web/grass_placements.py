"""Evaluate actual saved grass GN with original floor/path exclusion mesh, at web density."""
import bpy,json,random,math,hashlib,argparse,sys
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
parser=argparse.ArgumentParser();parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[3]);parser.add_argument('--output',type=Path);parser.add_argument('--source',type=Path);args=parser.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
ROOT=args.root.resolve();OUT=(args.output or ROOT/'output/archviz/web').resolve();OUT.mkdir(parents=True,exist_ok=True);SOURCE=(args.source or ROOT/'output/archviz/dom-archviz.blend').resolve()
if Path(bpy.data.filepath).resolve()!=SOURCE:bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
lawns=[]
for o in bpy.data.objects:
 for mod in o.modifiers:
  if mod.type!='NODES' or not mod.node_group or not mod.node_group.name.startswith('Bermuda distribution'):continue
  for n in mod.node_group.nodes:
   if n.bl_idname=='GeometryNodeDistributePointsOnFaces':
    n.inputs['Density'].default_value=18 if 'Parcela' in o.get('source_name','') else 2
  lawns.append(o)
print('LAWN_EMITTERS',[(o.name,len(o.data.polygons)) for o in lawns],flush=True)
# Evaluate the saved nodes including original raycast against floors, paths, pool deck.
bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();rows=[];counts={};excluded=0
blocker=bpy.data.objects['Grass exclusion surfaces'];bvh=BVHTree.FromPolygons([blocker.matrix_world@v.co for v in blocker.data.vertices],[list(p.vertices) for p in blocker.data.polygons])
water=[o for o in bpy.data.objects if o.type=='MESH' and 'real-pool-water' in o.get('source_materials','')]
pools=[]
for o in water:
 corners=[o.matrix_world@Vector(v) for v in o.bound_box];pools.append((min(v.x for v in corners)-.12,max(v.x for v in corners)+.12,min(v.y for v in corners)-.12,max(v.y for v in corners)+.12))
def blocked(p):
 if any(a<=p.x<=b and c<=p.y<=d for a,b,c,d in pools):return True
 return any(bvh.ray_cast(Vector((p.x+dx,p.y+dy,p.z-.005)),Vector((0,0,1)),.7)[0] is not None for dx,dy in [(0,0)]+[(math.cos(a*math.pi/4)*.10,math.sin(a*math.pi/4)*.10) for a in range(8)])
for instance in dg.object_instances:
 if not instance.is_instance or not instance.parent:continue
 parent=instance.parent.original
 if parent not in lawns:continue
 location,rotation,scale=instance.matrix_world.decompose()
 if blocked(location):excluded+=1;continue
 # A rejected ray is already filtered by the Geometry Nodes instance selection.
 # Original prototype includes local blades; origin is at the surveyed lawn elevation.
 row=[round(location.x,5),round(location.z,5),round(-location.y,5),round(rotation.to_euler('XYZ').z,5),round(scale.x,5)]
 rows.append(row);counts[parent.name]=counts.get(parent.name,0)+1
random.Random(20260905).shuffle(rows)
rows=rows[:8192]
doc={'version':1,'prototype':'dom-grass-prototype.glb','coordinates':'glTF right-handed Y-up metres before Babylon glTF root transform','stride':5,'fields':['x','y','z','yawRadians','uniformScale'],'yawAxis':'+Y','seed':20260905,'desktopCount':len(rows),'mobileCount':min(2048,len(rows)),'source':'Actual saved Bermuda Geometry Nodes instances; original upward-ray exclusion against Grass exclusion surfaces retained.','sourceCountsBeforeCap':counts,'excludedByAdditionalPoolAndPavingMargin':excluded,'pavingClearanceMetres':.1,'poolClearanceMetres':.12,'placements':[v for row in rows for v in row]}
(OUT/'grass-placements.json').write_text(json.dumps(doc,separators=(',',':'),ensure_ascii=False))
print('GRASS_DONE',len(rows),counts,(OUT/'grass-placements.json').stat().st_size,flush=True)
