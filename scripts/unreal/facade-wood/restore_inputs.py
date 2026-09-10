"""Explicit missing-only restore of pinned facade photographs/evidence.

Never called by the importer. Existing different bytes are refused, not replaced.
Run python3 scripts/unreal/facade-wood/restore_inputs.py after adopting the draft.
"""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import urllib.request

HERE=Path(__file__).resolve().parent
ROOT=next(p for p in HERE.parents if (p/'lib/twin-site.ts').is_file())
REFERENCE_SHA='fc4ad519dc82f729c1783455b134db96d77d23e636f80c5bc76be840b2469bdc'


def sha(data): return hashlib.sha256(data).hexdigest()
def need(ok,msg):
    if not ok: raise RuntimeError(msg)


def target(relative):
    p=Path(relative)
    safe_parent=p.parent in (Path('output/unreal/facade-wood-study'),Path('output/unreal/facade-wood-study/hinoki_planks'))
    need(not p.is_absolute() and '..' not in p.parts and safe_parent,
         'Facade restore path outside reviewed output scope')
    result=ROOT/p
    for q in [result,*result.parents]:
        if q==ROOT: break
        need(not q.is_symlink(),'Facade restore refuses symlink path')
    return result


def publish(path,data,expected):
    need(sha(data)==expected,'Restored data hash differs')
    path.parent.mkdir(parents=True,exist_ok=True)
    name=None
    try:
        with tempfile.NamedTemporaryFile(prefix='.facade-input-',dir=path.parent,delete=False) as f:
            name=f.name;f.write(data);f.flush();os.fsync(f.fileno())
        # A competing writer must not be overwritten between the precheck and
        # publication. Hard-link creation is atomic and fails if target exists.
        os.link(name,path)
    finally:
        if name is not None: os.unlink(name)
    need(sha(path.read_bytes())==expected,'Restored file readback differs')


def restore():
    raw=(HERE/'reference.json').read_bytes();need(sha(raw)==REFERENCE_SHA,'Facade restore reference changed')
    ref=json.loads(raw);restored=[];verified=[]
    for relative,expected in ref['evidence'].items():
        path=target(relative)
        if path.exists():need(path.is_file() and sha(path.read_bytes())==expected,'Existing facade evidence differs')
        else:
            src=HERE/'evidence'/path.name;need(not src.is_symlink(),'Bundled evidence is a symlink')
            publish(path,src.read_bytes(),expected);restored.append(relative)
        verified.append(relative)
    for spec in ref['maps'].values():
        path=target(spec['path'])
        if path.exists():
            need(path.is_file() and path.stat().st_size==spec['bytes'] and sha(path.read_bytes())==spec['sha256'],
                 'Existing facade photo differs; refusing overwrite')
        else:
            need(spec['url'].startswith('https://dl.polyhaven.org/file/ph-assets/Textures/jpg/4k/hinoki_planks/'),
                 'Facade URL outside exact official asset family')
            request=urllib.request.Request(spec['url'],headers={'User-Agent':'Brezi-facade-pinned-input-restore/1'})
            with urllib.request.urlopen(request,timeout=90) as response:
                data=response.read(spec['bytes']+1)
            need(len(data)==spec['bytes'],'Facade download length differs')
            need(hashlib.md5(data).hexdigest()==spec['md5'],'Facade official file MD5 differs')
            publish(path,data,spec['sha256']);restored.append(spec['path'])
        verified.append(spec['path'])
    return {'status':'facade-inputs-verified','restored':restored,'verified':verified,
            'existingFilesOverwritten':False,'nativePerformed':False}


if __name__=='__main__':print(json.dumps(restore(),indent=2))
