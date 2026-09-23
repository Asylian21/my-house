"""Restore checksum-pinned CC0 4K sources; refuse to replace different files."""
import hashlib
import json
import os
import urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]


def main():
    manifest=json.loads((ROOT/'scripts/unreal/photoreal-exterior-inputs.json').read_text())
    for name,asset in manifest['assets'].items():
        for role,spec in asset['maps'].items():
            target=(ROOT/spec['path']).resolve()
            if not target.is_relative_to(ROOT/'output/unreal'): raise RuntimeError('Input destination escaped exterior output')
            if target.exists():
                if target.stat().st_size!=spec['bytes'] or hashlib.sha256(target.read_bytes()).hexdigest()!=spec['sha256']:
                    raise RuntimeError('Existing source differs; no overwrite: '+str(target))
                print(name+'/'+role+': verified existing 4K input');continue
            request=urllib.request.Request(spec['url'],headers={'User-Agent':'BreziTwin ArchViz pinned CC0 asset restore'})
            with urllib.request.urlopen(request,timeout=60) as response:data=response.read(spec['bytes']+1)
            if len(data)!=spec['bytes'] or hashlib.sha256(data).hexdigest()!=spec['sha256'] or hashlib.md5(data).hexdigest()!=spec['md5']:
                raise RuntimeError('Downloaded scan identity differs: '+name+'/'+role)
            target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as stream:
                stream.write(data);stream.flush();os.fsync(stream.fileno())
            print(name+'/'+role+': restored verified 4K input')


if __name__=='__main__':main()
