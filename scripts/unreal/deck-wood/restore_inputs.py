"""Restore three exact CC0 source JPEGs without overwriting different local data."""
import hashlib
import os
import urllib.request
from pathlib import Path

from deck_wood import ROOT, MAPS


def main():
    folder = ROOT / 'output/unreal/deck-material-study/wood_planks'
    folder.mkdir(parents=True, exist_ok=True)
    for role, (name, expected, size) in MAPS.items():
        target = folder / (name + '-4k.jpg')
        if target.exists():
            if target.stat().st_size != size or hashlib.sha256(target.read_bytes()).hexdigest() != expected:
                raise RuntimeError('Existing local input differs: ' + str(target))
            print(role + ': verified existing 4K map')
            continue
        token = 'diff' if role == 'Diffuse' else name
        url = 'https://dl.polyhaven.org/file/ph-assets/Textures/jpg/4k/wood_planks/wood_planks_' + token + '_4k.jpg'
        request = urllib.request.Request(url, headers={'User-Agent': 'BreziTwin source asset restore'})
        with urllib.request.urlopen(request, timeout=60) as response:
            data = response.read(size + 1)
        if len(data) != size or hashlib.sha256(data).hexdigest() != expected:
            raise RuntimeError('Downloaded input differs: ' + role)
        # Exclusive creation preserves a file written by another process.
        with target.open('xb') as stream:
            stream.write(data)
            stream.flush()
            os.fsync(stream.fileno())
        print(role + ': restored verified 4K map')


if __name__ == '__main__':
    main()
