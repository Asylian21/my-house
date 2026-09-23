"""Restore pinned CC0 interior inputs; never select floating latest assets."""
import hashlib
import json
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
manifest=json.loads((ROOT/'scripts/unreal/photoreal-interior-inputs.json').read_text())
for asset in manifest['assets'].values():
    for spec in asset['maps'].values():
        path=ROOT/spec['path'];path.parent.mkdir(parents=True,exist_ok=True)
        if path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==spec['sha256']:continue
        temporary=path.with_suffix(path.suffix+'.download')
        subprocess.run(['curl','-fsSL','--retry','2','-A','BreziArchvizResearch/1.0',spec['url'],'-o',str(temporary)],check=True)
        if hashlib.sha256(temporary.read_bytes()).hexdigest()!=spec['sha256']:raise RuntimeError('Pinned texture checksum changed: '+spec['url'])
        temporary.replace(path)
print('Pinned interior input checksums verified')
