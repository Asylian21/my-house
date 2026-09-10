"""Synthetic CPU fixtures only. Does not validate a Metal shader or GPU capture."""
import importlib.util,json,math,struct,tempfile,hashlib
from pathlib import Path
from shutil import copyfile
BASE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('validate_capture',BASE/'validate_capture.py');validator=importlib.util.module_from_spec(spec);spec.loader.exec_module(validator);r=validator.ref
c=json.loads((BASE.parent/'Resources/receiver-contract.json').read_text());objects=c['receiverObjects'];ids=[o['id'] for o in objects];floor=objects[ids.index('DOM_01720')];low,high=floor['boundsMm']['min'],floor['boundsMm']['max'];x0,x1=low[0]/1000,high[0]/1000;y0,y1=-high[1]/1000,-low[1]/1000;z=c['waterMeanPlaneMetres'];i=r.unit(c['sunRayTravelDirection']);triangles=[]
for t in c['triangles']:
 a,b,d=t['verticesMetres'];triangles.append({'sourceObjectId':t['objectId'],'a':a,'e1':r.sub(b,a),'e2':r.sub(d,a),'low':tuple(min(v[j] for v in [a,b,d]) for j in range(3)),'high':tuple(max(v[j] for v in [a,b,d]) for j in range(3))})
bvh=r.BVH(triangles);nx,ny,ax,ay=64,29,128,64;area=(x1-x0)*(y1-y0);packet=-i[2]*area/(nx*ny);pixel_area=area/(ax*ay);ext=[a+s for a,s in zip(c['absorptionPerMetre'],c['scatteringPerMetre'])];binary=bytearray();atlas=[[0.,0.,0.,0.] for _ in range(ax*ay)]
for row in range(ny):
 for col in range(nx):
  x=x0+(col+.5)*(x1-x0)/nx;y=y0+(row+.5)*(y1-y0)/ny;direction,f=r.refract(i,r.normal(x,y,0,c['authoredWaves']));hit,distance=bvh.first((x,y,z),direction);ti=hit[0];id_=triangles[ti]['sourceObjectId'];q=r.add((x,y,z),r.mul(direction,distance));rgb=[packet*(1-f)*math.exp(-s*distance) for s in ext];p=(*q,0 if id_=='DOM_01720' else 1,*rgb,distance,f,ids.index(id_),ti,0);data=struct.pack('<12f',*p);binary.extend(data);p=struct.unpack('<12f',data)
  if p[3]:continue
  u=(p[0]-x0)/(x1-x0)*ax-.5;v=(p[1]-y0)/(y1-y0)*ay-.5;ix,iy=math.floor(u),math.floor(v);fx,fy=u-ix,v-iy;splats=[(xx,yy,wx*wy) for xx,wx in [(ix,1-fx),(ix+1,fx)] for yy,wy in [(iy,1-fy),(iy+1,fy)] if 0<=xx<ax and 0<=yy<ay];total=sum(w for _,_,w in splats)
  for xx,yy,w in splats:
   for ch in range(3):atlas[yy*ax+xx][ch]+=p[4+ch]*w/total/pixel_area
   atlas[yy*ax+xx][3]+=w/total
atlas_bytes=b''.join(struct.pack('<4e',*p) for p in atlas)
with tempfile.TemporaryDirectory(prefix='brezi-caustics-cpu-fixture-') as directory:
 p=Path(directory);copyfile(BASE.parent/'Resources/receiver-contract.json',p/'receiver-contract.json');meta={'shaderTimeSeconds':0,'launchSize':[nx,ny],'atlasSize':[ax,ay],'sunRayDirection':i,'photonStrideBytes':48,'productionLightingBound':False,'sunVisibilityImplemented':False,'syntheticCPUFixture':True,'finiteSolarDiskImplemented':False,'sourceContractSha256':hashlib.sha256((BASE.parent/'Resources/receiver-contract.json').read_bytes()).hexdigest()};(p/'capture.json').write_text(json.dumps(meta));(p/'photons-f32le.bin').write_bytes(binary);(p/'atlas-rgba16f-le.bin').write_bytes(atlas_bytes)
 good=validator.validate(p,allow_synthetic=True);assert good['status']=='synthetic-validator-fixture-passed'
 failures=[]
 for name,bad in [('truncated-photon',bytes(binary[:-1])),('nan-photon',struct.pack('<f',math.nan)+bytes(binary[4:])),('foreign-triangle',bytes(binary[:40])+struct.pack('<f',999999)+bytes(binary[44:]))]:
  (p/'photons-f32le.bin').write_bytes(bad)
  try:validator.validate(p,allow_synthetic=True)
  except AssertionError:
   failures.append(name)
   assert json.loads((p/'reference-validation.json').read_text())['status']=='validation-failed'
  else:raise AssertionError(name+' accepted')
 (p/'photons-f32le.bin').write_bytes(binary)
 (p/'atlas-rgba16f-le.bin').write_bytes(b''.join(struct.pack('<4e',*(v*2 for v in a)) for a in atlas))
 try:validator.validate(p,allow_synthetic=True)
 except AssertionError:failures.append('doubled-atlas-energy')
 else:raise AssertionError('Energy duplication accepted')
 (p/'atlas-rgba16f-le.bin').write_bytes(atlas_bytes)
 # Nonfloor perturbations isolate Fresnel/Beer gates without changing the floor atlas.
 samples=list(struct.iter_unpack('<12f',binary));ni=next(i for i,a in enumerate(samples) if a[3]==1)
 modifications=[]
 fresnel=list(samples[ni]);fresnel[8]+=.02
 for ch in range(3):fresnel[4+ch]=packet*(1-fresnel[8])*math.exp(-ext[ch]*fresnel[7])
 modifications.append(('fresnel-disagreement',fresnel,'Snell location/Fresnel disagreement'))
 beer=list(samples[ni]);beer[4]*=.95
 modifications.append(('beer-lambert-disagreement',beer,'Snell location/Fresnel disagreement'))
 floor_status=list(samples[ni]);floor_status[3]=0
 modifications.append(('floor-reclassification',floor_status,'Floor receiver classification changed'))
 for name,record,expected_error in modifications:
  bad=bytearray(binary);bad[ni*48:(ni+1)*48]=struct.pack('<12f',*record);(p/'photons-f32le.bin').write_bytes(bad)
  try:validator.validate(p,allow_synthetic=True)
  except AssertionError as error:
   if expected_error not in str(error):raise
   failures.append(name)
  else:raise AssertionError(name+' accepted')
 (p/'photons-f32le.bin').write_bytes(binary)
 atlas_records=list(struct.iter_unpack('<4e',atlas_bytes))
 (p/'atlas-rgba16f-le.bin').write_bytes(b''.join(struct.pack('<4e',*a) for a in reversed(atlas_records)))
 try:validator.validate(p,allow_synthetic=True)
 except AssertionError as error:
  if 'HDR atlas differs spatially' not in str(error):raise
  failures.append('atlas-spatial-rearrangement-with-same-energy')
 else:raise AssertionError('Spatially rearranged atlas accepted')
 (p/'atlas-rgba16f-le.bin').write_bytes(atlas_bytes)
 try:validator.validate(p)
 except AssertionError:failures.append('synthetic-native-evidence')
 else:raise AssertionError('Synthetic fixture accepted as native capture')
 changed=json.loads((p/'receiver-contract.json').read_text());changed['triangles'][0]['verticesMetres'][0][0]+=.1;(p/'receiver-contract.json').write_text(json.dumps(changed))
 try:validator.validate(p,allow_synthetic=True)
 except AssertionError:failures.append('unreviewed-receiver-contract')
 else:raise AssertionError('Changed canonical receiver accepted')
 report={'status':'CPU-validator-fixtures-passed','nativeBuildOrGPUExecuted':False,'positive':'double-reference photons and half-float bilinear atlas','negativeRejected':failures,'positiveAtlasFluxErrorRGB':good['atlasFluxRelativeErrorRGB']};print(json.dumps(report,indent=2))
