"""Independent GLB, leaf-map and connected-growth audit for regional assets."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
import numpy as np
from PIL import Image

ROOT=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

class Glb:
 def __init__(self,path):
  raw=Path(path).read_bytes();magic,version,size=struct.unpack_from('<III',raw)
  assert magic==0x46546c67 and version==2 and size==len(raw)
  length,kind=struct.unpack_from('<II',raw,12);assert kind==0x4e4f534a
  self.data=json.loads(raw[20:20+length]);offset=20+length;length,kind=struct.unpack_from('<II',raw,offset);assert kind==0x004e4942
  self.raw=raw[offset+8:offset+8+length]
 def array(self,index):
  a=self.data['accessors'][index];v=self.data['bufferViews'][a['bufferView']];assert not a.get('sparse')
  dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]
  width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];item=np.dtype(dtype).itemsize
  offset=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',width*item)
  return np.ndarray((a['count'],width),dtype=dtype,buffer=self.raw,offset=offset,strides=(stride,item)).copy()

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
 folder=(ROOT/args.output).resolve();manifest=json.loads((folder/'geometry-manifest.json').read_text());materials=json.loads((folder/'material-manifest.json').read_text());source=json.loads((folder/'asset-manifest.json').read_text());skeletons=json.loads((folder/'growth-skeletons.json').read_text())
 report={'schemaVersion':1,'status':'geometry-uv-pbr-cpu-validated-awaiting-native','checks':[],'meshes':[],'materials':{}}
 inputs={**source['inputFiles'],**manifest['inputFiles']}
 for path,expected in inputs.items():assert sha(path)==expected,('Input drift',path)
 for key,recipe in materials.items():
  assert recipe['license']=='CC0-1.0' and recipe['normalConvention']=='DirectX' and recipe['powerOfTwoMode']=='stretch'
  sizes=[]
  for spec in recipe['maps'].values():
   assert sha(spec['path'])==spec['sha256'];sizes.append(Image.open(spec['path']).size)
  assert len(set(sizes))==1
  alpha=np.asarray(Image.open(recipe['maps']['alpha']['path']).convert('L'));rgb=np.asarray(Image.open(recipe['maps']['albedo']['path']).convert('RGB'))
  opaque=alpha>=253;transparent=alpha==0
  assert opaque.any() and transparent.any()
  # Detect the demonstrated R1/R2 white-background fringe failure up front.
  background=rgb[transparent].mean(axis=0)/255
  assert float(background.max())<.65 and background[1]>background[2]*1.1,('Unsafe leaf RGB background',key,background)
  report['materials'][key]={'sourceDimensions':list(sizes[0]),'opaqueCoverage':float(opaque.mean()),
                           'transparentRGBMeanSrgb':background.tolist(),'normalConvention':'DirectX','nativeMipPreparation':'STRETCH_TO_POWER_OF_TWO; unchanged provider source bytes'}
 for record in manifest['meshes']:
  assert record['placementPolicy']=='explicit-only' and len(record['lods'])==3
  assert sha(record['glbPath'])==record['glbSha256'];g=Glb(record['glbPath']);all_points=[];lod_reports=[]
  for lod in record['lods']:
   node=next(n for n in g.data['nodes'] if n['name']==lod['nodeName']);assert all(k not in node for k in ('matrix','translation','rotation','scale'))
   primitives=g.data['meshes'][node['mesh']]['primitives'];slots=[g.data['materials'][p['material']]['name'] for p in primitives]
   assert slots==record['materialKeys'];count=0;points=[];normal_error=0.;basis_error=0.;minimum_area=1e9;opposed=0;leaf_area=0.
   for p in primitives:
    attrs=p['attributes'];assert {'POSITION','NORMAL','TEXCOORD_0','TANGENT'}<=set(attrs)
    position=g.array(attrs['POSITION']).astype(float);normal=g.array(attrs['NORMAL']).astype(float);tangent=g.array(attrs['TANGENT']).astype(float);uv=g.array(attrs['TEXCOORD_0']).astype(float);indices=g.array(p['indices']).reshape(-1,3)
    assert all(np.isfinite(v).all() for v in (position,normal,tangent,uv));assert indices.max()<len(position)
    nerr=float(abs(np.linalg.norm(normal,axis=1)-1).max());terr=float(abs(np.linalg.norm(tangent[:,:3],axis=1)-1).max());dot=float(abs(np.sum(normal*tangent[:,:3],axis=1)).max())
    normal_error=max(normal_error,nerr,terr);basis_error=max(basis_error,dot)
    assert nerr<1e-5 and terr<1e-5 and dot<1e-4 and np.isin(tangent[:,3],[-1,1]).all(),('Invalid normal/tangent frame',record['id'],lod['level'],nerr,terr,dot)
    triangles=position[indices];cross=np.cross(triangles[:,1]-triangles[:,0],triangles[:,2]-triangles[:,0]);areas=np.linalg.norm(cross,axis=1)*.5
    assert areas.min()>1e-14,('Degenerate geometry',record['id'],lod['level'],areas.min())
    face_normals=cross/np.linalg.norm(cross,axis=1)[:,None];agreement=np.sum(face_normals*normal[indices].mean(axis=1),axis=1)
    opposed+=int((agreement<-.0001).sum());assert not (agreement<-.0001).any(),('Inverted source normals',record['id'],lod['level'],int((agreement<-.0001).sum()))
    minimum_area=min(minimum_area,float(areas.min()));count+=len(indices);native=position[:,[0,2,1]]*100;points.append(native)
    if g.data['materials'][p['material']]['name'].startswith('regional_'):
     assert uv.min()>=0 and uv.max()<=1;leaf_area=float(areas.sum())*report['materials'][record['materialKeys'][1]]['opaqueCoverage']
   points=np.concatenate(points);all_points.append(points);actual={'min':points.min(axis=0).tolist(),'max':points.max(axis=0).tolist()}
   error=max(abs(actual[k][i]-lod['expectedBoundsCm'][k][i]) for k in ('min','max') for i in range(3))
   assert error<.001 and count==lod['triangles'];assert abs(actual['min'][2])<.2
   assert count <=(180000,50000,7000)[lod['level']]
   lod_reports.append({'level':lod['level'],'triangles':count,'nativeBoundsErrorCm':error,'minimumTriangleAreaM2':minimum_area,
                       'maxUnitBasisError':normal_error,'maxAbsNormalDotTangent':basis_error,'opposedFaces':opposed,
                       'alphaWeightedLeafAreaM2':leaf_area})
  points=np.concatenate(all_points);radial=float(np.linalg.norm(points[:,:2],axis=1).max());assert abs(radial-record['radialEnvelopeCm'])<.001
  tree=skeletons[record['id']];max_error=0
  def curve(points,t):return np.asarray(points[0])*(1-t)**2+np.asarray(points[1])*(2*t*(1-t))+np.asarray(points[2])*t*t
  for i,b in enumerate(tree['branches']):
   if b['parent'] is not None:
    assert b['parent']<i;max_error=max(max_error,float(np.linalg.norm(curve(tree['branches'][b['parent']]['points'],b['parentT'])-b['points'][0]))*100)
  for leaf in tree['leaves']:max_error=max(max_error,float(np.linalg.norm(curve(tree['branches'][leaf['branch']]['points'],leaf['t'])-leaf['base']))*100)
  assert max_error<.001
  width=np.ptp(points[:,0])/100;depth=np.ptp(points[:,1])/100;area=math.pi*width*depth/4
  report['meshes'].append({'id':record['id'],'lods':lod_reports,'radialEnvelopeCm':radial,'branches':len(tree['branches']),
                           'leafCount':len(tree['leaves']),'maximumAttachmentErrorCm':max_error,
                           'approximateCrownFootprintM2':area,'LOD0LeafAreaPerCrownArea':lod_reports[0]['alphaWeightedLeafAreaM2']/area})
 report['checks']=['Source/GLB SHA256','Explicit-only placement','All3LOD triangles and bounds','Unbaked node transforms','Named material slot order',
                   'Finite positions/UV0/unit normals/tangents','Normal/tangent orthogonality and handedness','Nondegenerate geometry and face-normal agreement',
                   'Connected branch and leaf attachment hierarchy','Source alpha and nonwhite RGB padding','Source image dimensions and DirectX normal convention']
 report['inputFiles']={**inputs,str(Path(__file__).resolve()):sha(__file__),str(folder/'geometry-manifest.json'):sha(folder/'geometry-manifest.json')}
 for row in manifest['meshes']:report['inputFiles'][row['glbPath']]=row['glbSha256']
 (folder/'geometry-validation.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS',len(report['meshes']),'variants /12LODs;',[(m['id'],round(m['LOD0LeafAreaPerCrownArea'],2))for m in report['meshes']],flush=True)

if __name__=='__main__':main()
