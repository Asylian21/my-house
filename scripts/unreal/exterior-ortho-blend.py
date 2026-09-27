"""Create a new photographic distance-blend revision without changing pixels."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', default=str(ROOT/'output/unreal/exterior-ortho-20260926-r1/orthophoto-manifest.json'))
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    source_path = Path(args.source).resolve(); folder = Path(args.output).resolve()
    if folder.exists():
        raise ValueError('Create a new output revision')
    source = json.loads(source_path.read_text())
    if source['materialProposal']['distanceBlendCm'] != [30000, 90000]:
        raise ValueError('Unexpected baseline photographic transition')
    for path, digest in source['inputFiles'].items():
        if sha(path) != digest:
            raise ValueError('Frozen source input drift: '+path)
    result = copy.deepcopy(source)
    result['status'] = 'LICENSE_UV_VALIDATED_EARLIER_PHOTO_BLEND_AWAITING_NATIVE'
    result['materialProposal']['distanceBlendCm'] = [18000, 36000]
    result['materialProposal']['distanceBlend'] = 'smoothstep over radial distance from world0; zero photographic contribution through180m, full contribution from360m on owned distant/fallback ground only'
    result['materialProposal']['terrainHeightBlendUnchangedCm'] = [30000, 90000]
    result['materialProposal']['artDirection'] = 'Earlier photographic context around the village; physical terrain, near context meshes, original house and lighting remain unchanged. Existing parcel/road meshes may occlude this underlying layer through255m.'
    result['derivedFrom'] = {'path': str(source_path), 'sha256': sha(source_path),
                             'changedFields': ['status', 'materialProposal.distanceBlendCm', 'materialProposal.distanceBlend'],
                             'sourcePixelsChanged': False, 'sourceUvChanged': False, 'terrainGeometryChanged': False,
                             'reason': 'Explicitly authorized R7 distant-context visual iteration; prior R6 sources/packages remain frozen.'}
    result['inputFiles'][str(source_path)] = sha(source_path)
    result['inputFiles'][str(Path(__file__).resolve())] = sha(__file__)
    if result['layers'] != source['layers'] or result['worldFrame'] != source['worldFrame']:
        raise ValueError('Source geographic/pixel contract changed')
    folder.mkdir(parents=True)
    target = folder/'orthophoto-manifest.json'
    target.write_text(json.dumps(result, indent=2, ensure_ascii=False)+'\n')
    (folder/'README.md').write_text('''# R7 earlier distant photographic context

Only the photographic material distance transition changes from 300–900m to
180–360m. This is a separate art-directed context revision, awaiting native
visual review. The DMR terrain height transition stays 300–900m; no mesh, height,
UV, provider image, original house, near-ground material or lighting is changed.

The existing unresolved flat backdrop begins outside the original 240×200m
baseline rectangle, so it can receive the earlier photograph without extending
geometry. Higher explicit parcel/road surfaces continue to occlude this layer
locally through about255m. Photography remains absent within180m. Source
coverage/extent and the detail atlas's100m edge feather remain unchanged.

All original geographic, image and licensing records remain in the frozen R1
folder. The derived manifest pins R1 plus this generator, reuses the exact same
image paths/SHA256 and documents the changed transition. Run the generator into
a new output folder to reproduce. Native appearance/performance acceptance is
not implied by numeric material tests.

Attribution: ČÚZK, 2024 · Ortofoto ČR · CC BY4.0. Photographic mapping to the visual
terrain and its blend distance are separately recorded adaptations; no provider
endorsement or measured reflectance is asserted.
''')
    print(str(target)); print(sha(target))


if __name__ == '__main__':
    main()
