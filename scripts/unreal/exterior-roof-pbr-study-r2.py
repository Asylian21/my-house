"""CPU-only official roof_tiles source option for four existing R18 red roofs.

Downloads original provider bytes, checks published MD5/size and existing
metric roof UVs. Creates no Unreal asset, geometry, edited pixel or preview.
"""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import hashlib
import json
import math
from pathlib import Path
import shutil
import urllib.parse
import urllib.request

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-roof-pbr-study-r2.py'
OUTPUT = ROOT/'output/unreal/exterior-roof-pbr-20261002-r2-study'
ORIGINAL_DOWNLOAD = ROOT/'output/unreal/exterior-roof-pbr-20261002-r1-study'
ASSET = 'roof_tiles'
API = 'https://api.polyhaven.com'
PAGE = 'https://polyhaven.com/a/roof_tiles'
LICENSE = 'https://polyhaven.com/license'
BASE = ROOT/'output/unreal/exterior-20261001-r18b/neighbor-finish-overlay-report-r3.json'
BASE_SHA = '40ccc7cc686e2beafc05e5248eb8abe371f23bc8ad470c05284d4c442ed950da'
GEOMETRY = ROOT/'output/unreal/exterior-neighbor-finish-20261001-r18-study/neighbor-finish-geometry.json'
GEOMETRY_SHA = 'f3f94c01c4806bf89c90bd774ce0b2ce10425f0261cca8ad9eccfeb3e4842387'
CHOICES = {'albedo': ('Diffuse','jpg'), 'normal': ('nor_gl','png'), 'roughness': ('Rough','png')}

def sha(data): return hashlib.sha256(data).hexdigest()
def pin(path):
    data=path.read_bytes();return {'path':str(path.resolve()),'sha256':sha(data),'bytes':len(data)}
def load(path): return json.loads(path.read_text())
def write(path,value):
    with path.open('x') as f: json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n')
def request(url,maximum):
    response=urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'BreziTwin/roof-pbr-source-study'}),timeout=45)
    with response:
        data=response.read(maximum+1)
        assert len(data)<=maximum
        return data, response.geturl()
def download(item):
    role,spec=item;url=spec['url'];parsed=urllib.parse.urlparse(url)
    assert parsed.scheme=='https' and parsed.hostname=='dl.polyhaven.org' and '/roof_tiles/' in parsed.path
    path=ORIGINAL_DOWNLOAD/'maps'/Path(parsed.path).name
    data=path.read_bytes();final=url;assert len(data)==spec['size'] and hashlib.md5(data).hexdigest()==spec['md5']
    return role,dict(pin(path),url=url,finalUrl=final,publishedMD5=spec['md5'],actualMD5=hashlib.md5(data).hexdigest(),
                     publishedBytes=spec['size'],publishedIdentityVerified=True,sourcePixelsEdited=False)
def metric_uv(mesh):
    assert len(mesh['uvs'])==len(mesh['verticesCm'])==len(mesh['normals'])==len(mesh['tangents'])==len(mesh['tangentHandedness'])
    maximum=0.; minimum_determinant=float('inf');normal_axes={}
    for start in range(0,len(mesh['indices']),3):
        ids=mesh['indices'][start:start+3];p=[mesh['verticesCm'][i] for i in ids];uv=[mesh['uvs'][i] for i in ids]
        for a,b in [(0,1),(1,2),(2,0)]:maximum=max(maximum,abs(math.dist(p[a],p[b])-100*math.dist(uv[a],uv[b])))
        du1,dv1=[uv[1][i]-uv[0][i] for i in range(2)];du2,dv2=[uv[2][i]-uv[0][i] for i in range(2)]
        minimum_determinant=min(minimum_determinant,abs(du1*dv2-du2*dv1))
        n=mesh['normals'][ids[0]];axis=tuple(round(v,7) for v in n);normal_axes[axis]=normal_axes.get(axis,0)+1
    assert maximum<1e-8 and minimum_determinant>1e-10
    return {'sourceMeshId':mesh['id'],'triangles':len(mesh['indices'])//3,'vertices':len(mesh['verticesCm']),
            'uv0Units':'one UV unit =100cm on source triangle surface','maximumMetricEdgeErrorCm':maximum,
            'minimumUVTriangleDeterminant':minimum_determinant,'sourceNormalDirectionCount':len(normal_axes),
            'geometryPositionsIndicesNormalsTangentsAndUVUnmodified':True}

def main():
    assert not OUTPUT.exists(), 'A previous source study is immutable.'
    OUTPUT.mkdir();(OUTPUT/'maps').mkdir();(OUTPUT/'source').mkdir()
    started=datetime.now(timezone.utc).isoformat()
    assert pin(BASE)['sha256']==BASE_SHA and pin(GEOMETRY)['sha256']==GEOMETRY_SHA
    base,geometry=load(BASE),load(GEOMETRY)
    assert base['schemaVersion']==3 and base['status']=='neighbor-finish-native-overlay-validated' and base['savedReloaded'] is True
    process_path=BASE.parent/'neighbor-finish-native-r3-process.json';process=load(process_path);actual=load(Path(process['processFile']))
    assert actual['code']==0 and actual['signal'] is None and actual['pid']==base['nativeProcessId']==32105
    assert process['reportSha256']==BASE_SHA and process['sourcePinsUnchangedAfterNative'] is True
    api_pins={};documents={}
    for endpoint in ['info','files']:
        url=API+'/'+endpoint+'/'+ASSET;data=(ORIGINAL_DOWNLOAD/(endpoint+'.json')).read_bytes();final=url
        path=OUTPUT/(endpoint+'.json')
        with path.open('xb') as f:f.write(data)
        documents[endpoint]=json.loads(data);api_pins[endpoint]=dict(pin(path),url=url,finalUrl=final)
    info,files=documents['info'],documents['files']
    assert info['type']==1 and info['name']=='Roof Tiles' and info['dimensions']==[2000,2000]
    assert info['authors']=={'Stephan Seeliger':'All'} and 'terracotta' in info['tags']
    specs={role:files[key]['2k'][fmt] for role,(key,fmt) in CHOICES.items()}
    assert sum(row['size'] for row in specs.values())<50*1024*1024
    with ThreadPoolExecutor(max_workers=3) as pool:maps=dict(pool.map(download,specs.items()))
    saved=load(Path(base['savedActorWitness']['path']));targets=[];measurements=[]
    material=base['materials']['materials']['neighbor_roof_red']['asset']
    red=[mesh for mesh in geometry['candidateMeshes'] if mesh['material']=='neighbor_roof_red']
    assert len(red)==4 and sum(len(m['indices'])//3 for m in red)==332
    for mesh in red:
        actor=base['addedActors'][mesh['id']];native_mesh=base['meshes'][mesh['id']];witness=saved[actor]
        components=[c for c in witness['components'] if c.get('mesh')==native_mesh]
        assert len(components)==1 and components[0]['materials']==[material] and components[0]['overrideMaterials']==[]
        targets.append({'sourceMeshId':mesh['id'],'buildingSourceId':mesh['buildingSourceId'],'role':mesh['role'],
                        'actor':actor,'componentName':components[0]['name'],'componentClass':components[0]['class'],'mesh':native_mesh,'oldMaterial':material,'slot':0,
                        'nativeComponentPathRecorded':False,
                        'onlyProposedChange':'new component material override; no static mesh asset rebind or mutation',
                        'originalSavedActorWitness':witness})
        measurements.append(metric_uv(mesh))
    generator=pin(Path(__file__));snapshot=OUTPUT/'source'/Path(__file__).name;shutil.copyfile(Path(__file__),snapshot)
    assert pin(snapshot)['sha256']==generator['sha256']
    receipt={'schemaVersion':1,'owner':OWNER,'status':'verified-original-provider-roof-map-bytes-source-only',
             'startedAt':started,'endedAt':datetime.now(timezone.utc).isoformat(),'assetId':ASSET,'sourcePage':PAGE,
             'license':{'id':'CC0-1.0','sourcePage':LICENSE},'apiDocuments':api_pins,'maps':maps,
             'originalMapFilesReferenced':3,'originalMapBytes':sum(r['bytes'] for r in maps.values()),'downloadedMapFilesHere':0,
             'originalDownloadAttempt':pin(ORIGINAL_DOWNLOAD/'source-failure.json'),
             'allPublishedMD5AndBytesVerified':True,'sourcePixelsEdited':False,'nativeExecuted':False}
    write(OUTPUT/'source-download-receipt.json',receipt)
    recipe={'id':'roof_tiles_original_terracotta_r1','kind':'original-provider-roof-pbr-material-only-proposal',
            'maps':maps,'sourcePage':PAGE,'license':'CC0-1.0','author':'Stephan Seeliger','physicalPeriodMm':[2000,2000],
            'inputUVChannel':0,'existingUV0PhysicalPeriodCm':100,'proposedUVMultiplier':[.5,.5],
            'albedo':'original diffuse RGB; sRGB source; no tint/contrast/AO multiplication',
            'normal':'original OpenGL RGB tangent normal; native green flip true; TCNormalmap; no custom normal strength',
            'roughness':'original roughness R data; linear/no sRGB; TCMasks; no scalar variation',
            'metallic':0.,'blendMode':'Opaque','displacementApplied':False,'worldPositionOffsetApplied':False,
            'newNativeMaterialGraphsProposed':1,'newNativeTextureObjectsProposed':3,'newNativeMeshObjectsProposed':0,
            'newImportPipelineAssetsProposed':0,'sourcePixelsEdited':False,'nativeApplied':False,'nativeAppearanceAccepted':False}
    write(OUTPUT/'roof-material-proposal.json',recipe)
    write(OUTPUT/'roof-source-measurement.json',{'owner':OWNER,'sourceGeometry':pin(GEOMETRY),'rows':measurements,
         'redRoofTargetComponents':4,'sourceTriangles':332,'existingMetricUV0Verified':True,'geometryModified':False,
         'limitation':'Each source face uses an authored local tangent frame. This edge metric check does not establish seamless tile courses, aligned ridges, silhouette relief or native texture filtering.'})
    plan={'schemaVersion':1,'schema':'brezi-original-roof-pbr-source-option-r1','owner':OWNER,
          'status':'source-only-original-roof-pbr-material-option-native-pending','assetId':ASSET,
          'baseNativeReport':pin(BASE),'baseNativeProcessReceipt':pin(process_path),'sourceGeometry':pin(GEOMETRY),
          'baseSavedActorWitness':base['savedActorWitness'],'sourceDownloadReceipt':pin(OUTPUT/'source-download-receipt.json'),
          'materialProposal':pin(OUTPUT/'roof-material-proposal.json'),'sourceMeasurement':pin(OUTPUT/'roof-source-measurement.json'),
          'generator':{'live':generator,'snapshot':pin(snapshot)},'targets':targets,
          'protectedScope':{'activeDesign':{'variant':'C','heatingLayout':'B','livingLayout':'B'},'setbacksMm':{'street':3000,'east':3000},
                           'originalMeshesTransformsAndActorPoliciesUnchanged':True,'charcoalRoofUntouched':True,'doorsWallsWindowsGroundUntouched':True},
          'preservedPriorSourceFailure':pin(ORIGINAL_DOWNLOAD/'source-failure.json'),'sourceReviewPending':True,'nativeExecuted':False,'nativeApplied':False,'nativeAppearanceAccepted':False,
          'performanceAccepted':False,'fullPhotorealismAccepted':False,'shippingVerified':False,'packageVerified':False,
          'limits':['This source option preserves existing332 roof/ridge triangles. It cannot add physical tile silhouette/depth or correct building massing.',
                    'Photo-source maps may still repeat at2m and cross existing tangent/UV seams. Same native diagnostic camera is needed before selection.',
                    'The source surface is provider-described weathered terracotta. No unverified whole-roof scanning claim is made.',
                    'Original2k maps are unedited provider bytes. Any future native compression/green-flip interpretation needs saved native readback.',
                    'The current flat door/window/ground and wider neighborhood realism goals remain open.']}
    write(OUTPUT/'roof-pbr-source-plan.json',plan)
    for row in maps.values():assert pin(Path(row['path']))['sha256']==row['sha256']
    assert pin(BASE)['sha256']==BASE_SHA and pin(GEOMETRY)['sha256']==GEOMETRY_SHA and pin(Path(__file__))['sha256']==generator['sha256']
    print(json.dumps({'plan':pin(OUTPUT/'roof-pbr-source-plan.json'),'receipt':pin(OUTPUT/'source-download-receipt.json'),
                      'mapFiles':3,'mapBytes':receipt['originalMapBytes'],'targetComponents':4,'sourceTriangles':332,
                      'sourceInputsUnchanged':True,'nativeExecuted':False,'nativeAppearanceAccepted':False}))

if __name__=='__main__':main()
