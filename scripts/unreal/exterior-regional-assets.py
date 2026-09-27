"""Blender: connected regional broadleaf architecture and photographed leaf PBR.

No spheres, whole-tree billboards or random detached foliage clouds. One growth
hierarchy drives every LOD. These are regional shape studies, not species surveys.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import random
import struct
import sys

import bpy
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
SEED=60122761
PROFILES=[
 {'id':'regional_broadleaf_a','height':6.,'radius':2.5,'primaries':24,'crownBase':.28,'leafLength':.145,'leafMaterial':'regional_oak_leaf','form':'spreading deciduous field tree','role':'tree'},
 {'id':'regional_upright_b','height':8.,'radius':2.3,'primaries':26,'crownBase':.24,'leafLength':.145,'leafMaterial':'regional_green_leaf','form':'ascending oval deciduous tree','role':'tree'},
 {'id':'regional_orchard_c','height':4.5,'radius':2.45,'primaries':22,'crownBase':.27,'leafLength':.14,'leafMaterial':'regional_green_leaf','form':'low forked orchard-like deciduous tree','role':'tree'},
 {'id':'regional_hedge_a','height':1.8,'radius':1.05,'primaries':14,'crownBase':.07,'leafLength':.082,'leafMaterial':'regional_green_leaf','form':'irregular multi-stem broadleaf hedgerow clump','role':'shrub'},
]

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def vec(v):return Vector(v)
def curve(points,t):return points[0]*(1-t)**2+points[1]*(2*t*(1-t))+points[2]*t*t
def frame(direction):
 d=direction.normalized();reference=vec((0,0,1)) if abs(d.z)<.92 else vec((1,0,0));side=d.cross(reference).normalized()
 return side,d.cross(side).normalized()
def native_bounds(points):
 return {'min':[min(p.x for p in points)*100,-max(p.y for p in points)*100,min(p.z for p in points)*100],
         'max':[max(p.x for p in points)*100,-min(p.y for p in points)*100,max(p.z for p in points)*100]}

def orthogonalize_glb(path):
 """Repair exporter quantization of tangents; preserve all non-tangent bytes."""
 raw=bytearray(path.read_bytes());before=bytes(raw);json_length=struct.unpack_from('<I',raw,12)[0]
 document=json.loads(raw[20:20+json_length]);binary=20+json_length+8;allowed=bytearray(len(raw));seen=set();count=0;largest=0.
 def layout(accessor):
  a=document['accessors'][accessor];view=document['bufferViews'][a['bufferView']];assert a['componentType']==5126
  width={'VEC3':3,'VEC4':4}[a['type']]
  return binary+view.get('byteOffset',0)+a.get('byteOffset',0),view.get('byteStride',width*4),a['count']
 for mesh in document['meshes']:
  for primitive in mesh['primitives']:
   attrs=primitive['attributes'];pair=(attrs['TANGENT'],attrs['NORMAL'])
   if pair in seen:continue
   seen.add(pair);to,ts,n=layout(pair[0]);no,ns,nn=layout(pair[1]);assert n==nn
   for i in range(n):
    normal=struct.unpack_from('<3f',raw,no+ns*i);tangent=struct.unpack_from('<3f',raw,to+ts*i)
    length=math.sqrt(sum(v*v for v in normal));normal=tuple(v/length for v in normal)
    dot=sum(a*b for a,b in zip(normal,tangent));largest=max(largest,abs(dot));orthogonal=tuple(tangent[j]-normal[j]*dot for j in range(3));length=math.sqrt(sum(v*v for v in orthogonal));assert length>.5
    offset=to+ts*i;struct.pack_into('<3f',raw,offset,*(v/length for v in orthogonal));allowed[offset:offset+12]=b'\x01'*12;count+=1
 assert all(a==b or permitted for a,b,permitted in zip(before,raw,allowed))
 path.write_bytes(raw)
 return {'operation':'Gram-Schmidt tangent orthogonalization after glTF export','vertices':count,'maximumPreCorrectionAbsNormalDotTangent':largest,
         'positionsNormalsUVsIndicesHandednessAndOtherBytesUnchanged':True,'beforeSha256':hashlib.sha256(before).hexdigest(),'afterSha256':sha(path)}

def growth(profile,index,density):
 rng=random.Random(SEED+index*997);h=profile['height'];r=profile['radius'];branches=[];leaves=[]
 def branch(parent,t,end,radius,order,curve_bias=None):
  start=curve(branches[parent]['points'],t) if parent is not None else vec(end[0])
  end=vec(end if parent is not None else end[1]);delta=end-start
  mid=start+delta*.5+(curve_bias if curve_bias is not None else vec((rng.uniform(-.05,.05),rng.uniform(-.05,.05),-.03))*h*.12)
  record={'parent':parent,'parentT':t,'points':[start,mid,end],'radius':radius,'order':order,'tipRadius':max(.0007,radius*(.018 if order==0 else .15 if order<3 else .12))}
  branches.append(record);return len(branches)-1
 # Competing leaders share one genuine trunk crotch; hedge stems root separately.
 trunk=branch(None,None,[(0,0,0),(h*.025,-h*.012,h*.91)],h*(.023 if index!=2 else .031),0,vec((-.03*h,.018*h,0)))
 leaders=[trunk]
 if index==3:
  for j in range(4):
   az=j*2.39996;leaders.append(branch(None,None,[(math.cos(az)*.10,math.sin(az)*.10,0),(math.cos(az)*r*.27,math.sin(az)*r*.27,h*(.75+.12*rng.random()))],.026,0))
 else:
  for j in range(2):
   az=j*2.8+.7+index*.8;t=.24+j*.1
   leaders.append(branch(trunk,t,(math.cos(az)*r*.32,math.sin(az)*r*.32,h*(.88-j*.06)),h*.011,0,vec((math.cos(az)*r*-.08,math.sin(az)*r*-.08,.04*h))))
 primary_ids=[]
 for i in range(profile['primaries']):
  parent=leaders[i%len(leaders)];lower=.36 if index==0 else .30 if index==1 else .08 if index==3 else .25
  fraction=lower+(.95-lower)*(i/profile['primaries'])
  fraction=max(profile['crownBase'],fraction)+rng.uniform(-.025,.025)
  fraction=min(.94,fraction);start=curve(branches[parent]['points'],fraction)
  az=i*2.399963+index*.83+rng.uniform(-.18,.18)
  zrel=(start.z/h-.56)/.47;spread=math.sqrt(max(.12,1-zrel*zrel))
  reach=r*spread*rng.uniform(.61,.92)
  endpoint=vec((math.cos(az)*reach,math.sin(az)*reach,start.z+h*(.09+rng.uniform(.01,.055))))
  primary_ids.append(branch(parent,fraction,endpoint,max(.012,h*.014*(1-fraction)**.7),1,vec((-.08*reach*math.cos(az),-.08*reach*math.sin(az),-.055*h))))
 # Living apical growth closes the former sawn-off leader silhouette. Several
 # small unequal upright shoots create a broken crown top, never a flat cap.
 for j,parent in enumerate(leaders):
  for k in range(2):
   t=.79+k*.13;start=curve(branches[parent]['points'],t);az=j*2.37+k*1.7
   endpoint=start+vec((math.cos(az)*r*.17,math.sin(az)*r*.17,h*(.13-k*.045)))
   primary_ids.append(branch(parent,t,endpoint,max(.006,h*.004*(1-k*.35)),1))
 for primary in primary_ids:
  pb=branches[primary];base_az=math.atan2(pb['points'][-1].y,pb['points'][-1].x)
  for j in range(4):
   t=.33+j*.205;start=curve(pb['points'],t);sign=-1 if j%2 else 1
   az=base_az+sign*rng.uniform(.48,1.04)
   reach=r*rng.uniform(.23,.35)*(1-.28*t)
   end=start+vec((math.cos(az)*reach,math.sin(az)*reach,h*rng.uniform(.028,.08)))
   secondary=branch(primary,t,end,pb['radius']*.37,2)
   for k in range(4):
    f=.25+k*.225;start2=curve(branches[secondary]['points'],f)
    az2=az+(-1 if k%2 else 1)*rng.uniform(.58,1.05)
    reach2=r*rng.uniform(.12,.19)
    end2=start2+vec((math.cos(az2)*reach2,math.sin(az2)*reach2,h*rng.uniform(.008,.035)))
    tertiary=branch(secondary,f,end2,branches[secondary]['radius']*.40,3)
    for n in range(3):
     f2=.30+n*.32;start3=curve(branches[tertiary]['points'],f2)
     az3=az2+(-1 if n%2 else 1)*rng.uniform(.40,1.1)
     reach3=profile['leafLength']*rng.uniform(1.65,2.7)
     end3=start3+vec((math.cos(az3)*reach3,math.sin(az3)*reach3,rng.uniform(-.025,.09)*h))
     twig=branch(tertiary,f2,end3,max(.0009,branches[tertiary]['radius']*.32),4)
     count=max(6,round(9*density))
     for q in range(count):
      f3=.12+.87*q/(count-1);side=-1 if q%2 else 1
      leaves.append({'branch':twig,'t':f3,'base':curve(branches[twig]['points'],f3),
                     'length':profile['leafLength']*rng.uniform(.77,1.14),
                     'yaw':az3+side*rng.uniform(.55,1.35),'tilt':rng.uniform(-.85,1.05),
                     'roll':rng.uniform(-.8,.8),'curl':rng.uniform(.7,1.3),'mirror':rng.random()<.5})
 # Primary axes/attachments are recorded so topology continuity can be audited.
 assert all((curve(branches[b['parent']]['points'],b['parentT'])-b['points'][0]).length<1e-9 for b in branches if b['parent'] is not None)
 assert all((curve(branches[l['branch']]['points'],l['t'])-l['base']).length<1e-9 for l in leaves)
 return branches,leaves

class Mesh:
 def __init__(self):self.vertices=[];self.faces=[];self.uvs=[];self.slots=[]
 def vert(self,p,uv):self.vertices.append(tuple(p));self.uvs.append(tuple(uv));return len(self.vertices)-1
 def face(self,vertices,slot):
  for j in range(1,len(vertices)-1):self.faces.append((vertices[0],vertices[j],vertices[j+1]));self.slots.append(slot)
 def branch(self,b,level):
  order=b['order']
  if level==1 and order>=4:return
  if level==2 and order>=3:return
  segments=(8 if order==0 else 4 if order<3 else 2) if level==0 else (5 if order==0 else 3) if level==1 else (4 if order==0 else 2)
  sides=(10 if order==0 else 7 if order<3 else 4) if level==0 else (7 if order==0 else 5) if level==1 else (6 if order==0 else 4)
  rings=[];length=(b['points'][-1]-b['points'][0]).length
  for j in range(segments+1):
   t=j/segments;center=curve(b['points'],t);direction=curve(b['points'],min(1,t+.001))-curve(b['points'],max(0,t-.001));side,up=frame(direction)
   radius=b['radius']*(1-t)+b['tipRadius']*t
   ring=[]
   for k in range(sides+1):
    a=math.tau*k/sides;ring.append(self.vert(center+(side*math.cos(a)+up*math.sin(a))*radius,(k/sides*math.tau*b['radius']/.25,t*length/.25)))
   rings.append(ring)
  for lo,hi in zip(rings,rings[1:]):
   for k in range(sides):self.face((lo[k],lo[k+1],hi[k+1],hi[k]),0)
  self.face(tuple(reversed(rings[0][:-1])),0);self.face(tuple(rings[-1][:-1]),0)
 def leaf(self,l,level,aspect,scale=1):
  length=l['length']*scale;width=length*aspect;az=l['yaw'];tilt=l['tilt'];roll=l['roll']
  along=vec((math.cos(az)*math.cos(tilt),math.sin(az)*math.cos(tilt),math.sin(tilt)))
  side=vec((math.sin(az),-math.cos(az),0));normal=side.cross(along).normalized()
  side,normal=side*math.cos(roll)+normal*math.sin(roll),normal*math.cos(roll)-side*math.sin(roll)
  cols=(0,.5,1) if level<2 else (0,1);rows=(0,.45,1) if level==0 else (0,1)
  grid=[]
  for v in rows:
   row=[]
   for u in cols:
    bend=length*(.045*math.sin(math.pi*v)-.075*v*v)*l['curl']+width*.055*abs(2*u-1)*math.sin(math.pi*v)
    p=l['base']+along*(length*v)+side*(width*(u-.53))+normal*bend
    row.append(self.vert(p,(1-u if l['mirror'] else u,v)))
   grid.append(row)
  for lo,hi in zip(grid,grid[1:]):
   for j in range(len(cols)-1):self.face((lo[j],lo[j+1],hi[j+1],hi[j]),1)
 def object(self,name,materials):
  data=bpy.data.meshes.new(name);data.from_pydata(self.vertices,[],self.faces);data.update()
  for m in materials:data.materials.append(m)
  uv=data.uv_layers.new(name='UVMap')
  for polygon,slot in zip(data.polygons,self.slots):
   polygon.material_index=slot;polygon.use_smooth=True
   for loop in polygon.loop_indices:uv.data[loop].uv=self.uvs[data.loops[loop].vertex_index]
  obj=bpy.data.objects.new(name,data);bpy.context.scene.collection.objects.link(obj)
  return obj

def material(name):
 m=bpy.data.materials.new(name);m.use_nodes=True;return m

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);parser.add_argument('--density',type=float,default=1.)
 args=parser.parse_args(sys.argv[sys.argv.index('--')+1:]);assert .75<=args.density<=1.3
 folder=(ROOT/args.output).resolve();assert (folder/'asset-manifest.json').is_file()
 assert not (folder/'geometry-manifest.json').exists(),'Use a new output revision after export'
 bpy.ops.wm.read_factory_settings(use_empty=True)
 recipes=json.loads((folder/'material-manifest.json').read_text());old=json.loads((ROOT/'output/unreal/exterior-assets-20260926-r5/material-manifest.json').read_text())
 bark='ph_tree_small_02_branches';materials={key:material(key) for key in [bark]+list(recipes)}
 (folder/'glb').mkdir(exist_ok=True);records=[];skeletons={}
 for index,profile in enumerate(PROFILES):
  branches,leaves=growth(profile,index,args.density);leaf_key=profile['leafMaterial']
  image=bpy.data.images.load(recipes[leaf_key]['maps']['albedo']['path']);aspect=image.size[0]/image.size[1];bpy.data.images.remove(image)
  objects=[];selected=[]
  # Preserve outer representative leaf groups at every LOD; culling uses the
  # measured union of all resulting LOD bounds, never an assumed crown radius.
  extremes=set()
  for axis in range(3):
   ordered=sorted(range(len(leaves)),key=lambda i:leaves[i]['base'][axis])
   extremes.update(ordered[:8]+ordered[-8:])
  for level in range(3):
   mesh=Mesh()
   for branch in branches:mesh.branch(branch,level)
   stride=(1,3,10)[level];ids=[i for i in range(len(leaves)) if i%stride==0 or i in extremes]
   for i in ids:
    # Distant leaves are area-compensated only inside the crown. Boundary
    # foliage stays its authored size and keeps an irregular silhouette.
    factor=1. if i in extremes else (1.,1.50,2.45)[level]
    mesh.leaf(leaves[i],level,aspect,factor)
   name=profile['id']+'_LOD'+str(level);obj=mesh.object(name,[materials[bark],materials[leaf_key]])
   objects.append(obj);selected.append(len(ids))
  # Shared uniform normalization; LODs are never independently reoriented or fit.
  low=min(v.co.z for v in objects[0].data.vertices);high=max(v.co.z for v in objects[0].data.vertices);factor=profile['height']/(high-low)
  for obj in objects:
   for v in obj.data.vertices:v.co=vec((v.co.x,v.co.y,v.co.z-low))*factor
   obj.data.update();obj.data.calc_loop_triangles()
  lods=[]
  for level,obj in enumerate(objects):
   points=[v.co for v in obj.data.vertices];lods.append({'level':level,'nodeName':obj.name,'vertices':len(points),
       'triangles':len(obj.data.loop_triangles),'expectedBoundsCm':native_bounds(points),'leafCount':selected[level],
       'derivation':'Shared connected branching and deterministic nested photo-leaf selection; interior leaf area compensation at distant LOD only'})
  for obj in bpy.context.selected_objects:obj.select_set(False)
  for obj in objects:obj.select_set(True)
  output=folder/'glb'/(profile['id']+'.glb')
  bpy.ops.export_scene.gltf(filepath=str(output),export_format='GLB',use_selection=True,export_apply=False,
                          export_yup=True,export_normals=True,export_tangents=True,export_materials='EXPORT',
                          export_animations=False,export_cameras=False,export_lights=False)
  tangent_repair=orthogonalize_glb(output)
  points=[v.co for obj in objects for v in obj.data.vertices];bound=native_bounds(points)
  record={'id':profile['id'],'role':profile['role'],'placementPolicy':'explicit-only','form':profile['form'],
          'heightCm':profile['height']*100,'materialKeys':[bark,leaf_key],'glbPath':str(output),'glbSha256':sha(output),
          'sourceAsset':'authored-connected-regional-broadleaf','sourceUrl':recipes[leaf_key]['sourceUrl'],
          'regionalStatus':'Plausible Central European deciduous growth form; artistic reconstruction, not surveyed species, tree age or exact canopy.',
          'lods':lods,'allLodBoundsCm':bound,'radialEnvelopeCm':max(math.hypot(p.x,p.y) for p in points)*100,
          'trunkRootRadiusCm':profile['height']*.031*100,'branches':len(branches),'leafCount':len(leaves),
          'originalPhotosUnmodified':True,'normalConvention':'DirectX','sourceLeafAspectRatio':aspect,
          'densityScale':args.density,'seed':SEED+index*997,'growthAttachmentMaximumErrorCm':0.}
  record['tangentBasisCorrection']=tangent_repair
  records.append(record)
  skeletons[profile['id']]={'branches':[{**b,'points':[[float(v) for v in p] for p in b['points']]} for b in branches],
                           'leaves':[{**l,'base':[float(v) for v in l['base']]} for l in leaves],'sharedUniformScale':factor}
  for obj in objects:obj.hide_render=obj.name.endswith(('LOD1','LOD2'))
  print('EXPORTED',profile['id'],[x['triangles'] for x in lods],round(record['radialEnvelopeCm'],2),'cm crown radius',flush=True)
 growth_path=folder/'growth-skeletons.json';growth_path.write_text(json.dumps(skeletons,separators=(',',':'))+'\n')
 manifest={'schema':1,'units':'metres','axes':'glTF Y-up; Unreal native = [100*x,100*z,100*y]',
           'sourceBasis':'Blender metres Z-up -> glTF [x,z,-y] -> Unreal [100*x,-100*y,100*z]',
           'rootPolicy':'Shared ground root and common uniform normalization for all LODs; no display transform',
           'revision':'R6 regional connected deciduous canopy extension with photographed CC0 individual leaf surfaces',
           'inputFiles':{str(Path(__file__).resolve()):sha(__file__),str(folder/'asset-manifest.json'):sha(folder/'asset-manifest.json'),
                         str(folder/'material-manifest.json'):sha(folder/'material-manifest.json'),str(growth_path):sha(growth_path)},'meshes':records}
 (folder/'geometry-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 bpy.ops.wm.save_as_mainfile(filepath=str(folder/'regional-authored.blend'))
 print('REGIONAL GEOMETRY READY',len(records),'variants',flush=True)

if __name__=='__main__':main()
