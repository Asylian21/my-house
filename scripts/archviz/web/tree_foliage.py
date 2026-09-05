"""Portable tree LOD: preserve full scanned leaf UV islands; simplify woody parts separately."""
import bpy,bmesh,collections,random,numpy as np
from mathutils import Vector

def build_leaf_safe_tree(obj):
 mesh=obj.data;leaf_index=next(i for i,m in enumerate(mesh.materials) if 'leaves' in m.name)
 parent=list(range(len(mesh.vertices)))
 def find(x):
  while parent[x]!=x:parent[x]=parent[parent[x]];x=parent[x]
  return x
 polys=[f for f in mesh.polygons if f.material_index==leaf_index]
 for f in polys:
  a=find(f.vertices[0])
  for v in f.vertices[1:]:parent[find(v)]=a
 groups=collections.defaultdict(list)
 for f in polys:groups[find(f.vertices[0])].append(f)
 components=list(groups.values());large=[];small=[]
 for group in components:
  (large if sum(len(f.vertices)-2 for f in group)>8 else small).append(group)
 rng=random.Random(601226);rng.shuffle(small)
 selected=large+small[:4000]
 verts=[];faces=[];uvfaces=[];mat_indices=[]
 sourceuv=mesh.uv_layers.active.data
 failures=0;retained_area=0
 for group in selected:
  points=[];uv=[]
  for f in group:
   for li in f.loop_indices:
    points.append(tuple(mesh.vertices[mesh.loops[li].vertex_index].co));uv.append(tuple(sourceuv[li].uv))
  a=np.array(uv,dtype=float);v=np.array(points,dtype=float)
  design=np.column_stack((a,np.ones(len(a))))
  coefficients,_,rank,_=np.linalg.lstsq(design,v,rcond=None)
  if rank<3:failures+=1;continue
  lo=a.min(axis=0);hi=a.max(axis=0)
  corners=np.array([[lo[0],lo[1]],[hi[0],lo[1]],[hi[0],hi[1]],[lo[0],hi[1]]])
  positions=np.column_stack((corners,np.ones(4)))@coefficients
  center=positions.mean(axis=0);positions=center+(positions-center)*1.25
  # Existing source UV islands determine leaf silhouette; no collapsed needle triangles.
  normal=Vector(positions[1]-positions[0]).cross(Vector(positions[2]-positions[0]));expected=sum((f.normal*f.area for f in group),Vector())
  if normal.dot(expected)<0:positions=positions[::-1];corners=corners[::-1]
  offset=len(verts);verts.extend(tuple(p) for p in positions);faces.append(tuple(range(offset,offset+4)));uvfaces.append([tuple(p) for p in corners]);mat_indices.append(leaf_index);retained_area+=sum(f.area for f in group)
 for index,material in enumerate(mesh.materials):
  if index==leaf_index:continue
  bm=bmesh.new();bm.from_mesh(mesh);bmesh.ops.delete(bm,geom=[f for f in bm.faces if f.material_index!=index],context='FACES');bmesh.ops.delete(bm,geom=[v for v in bm.verts if not v.link_faces],context='VERTS')
  part=bpy.data.meshes.new('Web tree '+material.name);bm.to_mesh(part);bm.free()
  for m in mesh.materials:part.materials.append(m)
  tmp=bpy.data.objects.new('Web tree LOD working part',part);bpy.context.scene.collection.objects.link(tmp)
  tri=sum(len(p.vertices)-2 for p in part.polygons);target=2500 if 'branches' in material.name else 1500
  dec=tmp.modifiers.new('Woody part budget','DECIMATE');dec.ratio=min(1,target/max(tri,1));dg=bpy.context.evaluated_depsgraph_get();evaluated=bpy.data.meshes.new_from_object(tmp.evaluated_get(dg),preserve_all_data_layers=True,depsgraph=dg)
  offset=len(verts);verts.extend(tuple(v.co) for v in evaluated.vertices);uv=evaluated.uv_layers.active
  for f in evaluated.polygons:
   faces.append(tuple(offset+i for i in f.vertices));mat_indices.append(index);uvfaces.append([tuple(uv.data[i].uv) for i in f.loop_indices])
  bpy.data.objects.remove(tmp,do_unlink=True)
 new=bpy.data.meshes.new('Tree | leaf-safe scanned canopy');new.from_pydata(verts,[],faces)
 for m in mesh.materials:new.materials.append(m)
 uvlayer=new.uv_layers.new(name='UVMap')
 for f,uvs,idx in zip(new.polygons,uvfaces,mat_indices):
  f.material_index=idx;f.use_smooth=idx!=leaf_index
  for li,uv in zip(f.loop_indices,uvs):uvlayer.data[li].uv=uv
 new.update();report={'method':'Whole scanned UV islands fitted to leaf cards; woody parts independently simplified','sourceLeafComponents':len(components),'retainedLeafCards':len(selected)-failures,'originalLeafSurfaceArea':sum(f.area for f in polys),'retainedLeafSourceSurfaceArea':retained_area,'leafLinearCoverageScale':1.25,'failedDegenerateUVFits':failures,'triangles':sum(len(f.vertices)-2 for f in new.polygons)}
 print('LEAF_SAFE_TREE',report,flush=True);return new,report
