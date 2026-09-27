"""Freeze one reviewed candidate for optional native BaseColor modulation."""
import argparse,hashlib,json
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--study',required=True);p.add_argument('--candidate',choices=['moderate','strong'],default='moderate');a=p.parse_args()
study_path=Path(a.study).resolve();study=json.loads(study_path.read_text());output=study_path.parent/'field-macro-manifest.json'
if output.exists():raise ValueError('Final manifest already exists')
for path,digest in study['inputFiles'].items():
    if sha(path)!=digest:raise ValueError('Source pin differs: '+path)
selected=next(c for c in study['candidates'] if c['name']==a.candidate)
assert sha(selected['texture']['path'])==selected['texture']['sha256']
manifest={k:v for k,v in study.items() if k not in ('candidates','status')}
manifest.update({'kind':'field-macro-scalar','status':'FROZEN_FOR_NATIVE_QA_NOT_ACCEPTED','selectedCandidate':a.candidate,'factorRange':selected['factorRange'],'texture':selected['texture'],'statistics':selected['statistics'],'review':{'cpuPreview':{'path':str(study_path.parent/'cpu-field-macro-comparison.png'),'sha256':sha(study_path.parent/'cpu-field-macro-comparison.png')},'decision':'Moderate bounded detail; native view is required before visual acceptance. No acquisition RGB is applied.'},'nativeTexturePolicy':{'compression':'TC_VectorDisplacementmap','samplerType':'LinearColor','sRGB':False,'neverStream':True,'containmentSamplerMip':0,'automaticViewMipBias':False,'factorSamplerMip':'automatic'}})
manifest['inputFiles']={**manifest['inputFiles'],str(study_path):sha(study_path),str(Path(__file__).resolve()):sha(__file__)}
manifest['derivation']['featherDistance']='Conservative 8-neighbour Chebyshev pixel distance, capped at8pixels; lower-bounds Euclidean distance'
output.write_text(json.dumps(manifest,indent=2,ensure_ascii=False,allow_nan=False)+'\n')
print(json.dumps({'path':str(output),'sha256':sha(output),'texture':manifest['texture'],'factorRange':manifest['factorRange']},indent=2))
