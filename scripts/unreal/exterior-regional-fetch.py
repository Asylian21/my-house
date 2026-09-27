"""Acquire public CC0 leaf scans without editing provider pixels."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[2]
SOURCES = [('OakLeaf01','oak_leaf_01','oak-leaf-01','regional_oak_leaf'),
           ('GreenLeaf12','green_leaf_12','green-leaf-12','regional_green_leaf')]

def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def fetch(url, path):
    if path.is_file(): return
    request=urllib.request.Request(url,headers={'User-Agent':'Mozilla/5.0','Referer':'https://www.cgbookcase.com/'})
    with urllib.request.urlopen(request,timeout=120) as response: data=response.read()
    path.write_bytes(data)

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--output',required=True);args=parser.parse_args()
    folder=(ROOT/args.output).resolve();folder.mkdir(parents=True,exist_ok=True);inputs=folder/'inputs';inputs.mkdir(exist_ok=True)
    assert not (folder/'asset-manifest.json').exists(),'Create a new revision; existing receipt is immutable'
    records=[];materials={}
    for prefix,slug,page,key in SOURCES:
        url='https://cgbookcase-volume.b-cdn.net/t/'+prefix+'_MR_2K.zip';archive=inputs/(prefix+'_MR_2K.zip')
        fetch(url,archive);target=folder/slug;target.mkdir(exist_ok=True)
        with zipfile.ZipFile(archive) as z:
            for info in z.infolist():
                assert Path(info.filename).name==info.filename and info.filename.endswith('.png')
                raw=z.read(info);p=target/info.filename
                if p.exists(): assert p.read_bytes()==raw,'Existing source bytes changed'
                else:p.write_bytes(raw)
        page_url='https://www.cgbookcase.com/textures/'+page;page_file=inputs/(slug+'-provider-page.html');fetch(page_url,page_file)
        maps={role:{'path':str(target/(prefix+'_2K_front_'+suffix+'.png')),'sha256':sha(target/(prefix+'_2K_front_'+suffix+'.png'))}
              for role,suffix in [('albedo','BaseColor'),('normal','Normal'),('roughness','Roughness'),('alpha','Opacity')]}
        materials[key]={'kind':'foliage','maps':maps,'normalConvention':'DirectX','license':'CC0-1.0','sourceUrl':page_url,
                        'tint':[1,1,1],'uvScale':1,'opacityMaskClipValue':.333,'albedoScale':.90,'specular':.12,
                        'subsurfaceScale':.08,'normalStrength':1,'powerOfTwoMode':'stretch',
                        'artDirection':'Photographic green leaf colour with bounded 0.90 brightness response; native NPOT stretch preserves complete UV range; no source pixels edited. Regional form is authored, not species identification.'}
        records.append({'asset':slug,'provider':'Dorian Zgraggen / CGBookcase','license':'CC0-1.0','page':page_url,
                        'archive':{'url':url,'path':str(archive),'bytes':archive.stat().st_size,'sha256':sha(archive)},
                        'originalFiles':{str(p):sha(p) for p in target.glob('*.png')},'sourcePage':{'path':str(page_file),'sha256':sha(page_file)},
                        'sourcePixelEdits':False,'normalConventionEvidence':'Provider asset page explicitly labels Normal (DirectX) | front'})
    license_url='https://www.cgbookcase.com/textures';license_file=inputs/'provider-license.html';fetch(license_url,license_file)
    assert 'CC0' in license_file.read_text(),'Provider license evidence missing'
    receipt={'schemaVersion':1,'status':'acquired-original-cc0-source-pixels','providerLicenseUrl':license_url,
             'license':'CC0-1.0','credit':'Leaf photographs: CGBookcase / Dorian Zgraggen, CC0. Bark: Poly Haven / Rico Cilliers, CC0. Procedural branching and regional forms authored for DOM; no measured botanical inventory claim.',
             'assets':records,'inputFiles':{str(license_file):sha(license_file),str(Path(__file__).resolve()):sha(__file__)}}
    for record in records:
        receipt['inputFiles'].update(record['originalFiles'])
        for name in ('archive','sourcePage'):v=record[name];receipt['inputFiles'][v['path']]=v['sha256']
    (folder/'material-manifest.json').write_text(json.dumps(materials,indent=2)+'\n')
    (folder/'asset-manifest.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print('ACQUIRED',len(records),'CC0 leaf sets; all original image bytes preserved')

if __name__=='__main__':main()
