"""Derive foliage colour padding from hash-pinned opaque photograph pixels.

Run with a Python environment containing numpy, Pillow and scipy. This never
edits provider files or alpha masks. It removes contaminated semitransparent
RGB fringes, then fills RGB-only atlas padding by exact Euclidean nearest
opaque colour. Native alpha masking remains sourced from the provider map.
"""
import argparse
import copy
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image
import scipy
from scipy.ndimage import distance_transform_edt

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-alpha-dilate.py'
AFFECTED = {'ph_grass_medium_02', 'ph_tree_small_02_leaves', 'ph_celandine_01',
            'ph_grass_bermuda_01', 'ph_grass_medium_01'}
OPAQUE_THRESHOLD = .99
CLIP_THRESHOLD = .333


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(ok, message):
    if not ok: raise RuntimeError(message)


def load_alpha(path):
    raw = np.asarray(Image.open(path))
    require(raw.ndim == 2 and raw.dtype in (np.uint8, np.uint16), 'Expected original one-channel 8/16-bit alpha')
    return raw.astype(np.float32)/(65535. if raw.dtype == np.uint16 else 255.)


def linear(rgb):
    value = rgb.astype(np.float32)/255.
    return np.where(value <= .04045, value/12.92, ((value+.055)/1.055)**2.4)


def nearest_opaque_rgb(rgb, alpha, threshold=OPAQUE_THRESHOLD):
    require(rgb.ndim == 3 and rgb.shape[2] == 3 and rgb.dtype == np.uint8, 'Expected RGB8 source')
    require(rgb.shape[:2] == alpha.shape and np.isfinite(alpha).all(), 'Colour/alpha dimensions differ')
    opaque = alpha >= threshold
    require(opaque.any(), 'Atlas has no opaque colour donors')
    nearest = distance_transform_edt(~opaque, return_distances=False, return_indices=True)
    result = rgb[nearest[0], nearest[1]]
    require(np.array_equal(result[opaque], rgb[opaque]), 'Opaque source texels changed')
    return result


def mean(value):
    return [round(float(v), 6) for v in value.mean(axis=0)] if value.size else None


def mip_audit(rgb, alpha):
    """Linear box mips with quantile coverage matching; diagnostic, not UE DDC."""
    target = float(np.mean(alpha >= CLIP_THRESHOLD)); colour = linear(rgb)
    levels = []
    for level in range(9):
        threshold = max(float(np.quantile(alpha, 1-target)), 1e-8)
        visible = alpha >= threshold
        levels.append({'level': level, 'dimensions': list(alpha.shape),
                       'coveragePreservingThreshold': threshold,
                       'visibleMeanLinearRGB': mean(colour[visible]),
                       'nearWhiteVisibleFraction': float(np.mean(np.min(colour[visible], axis=-1) > .6))})
        if min(alpha.shape) <= 8: break
        h,w = alpha.shape
        require(h%2 == 0 and w%2 == 0, 'Atlas is not power-of-two')
        alpha = alpha.reshape(h//2,2,w//2,2).mean(axis=(1,3))
        colour = colour.reshape(h//2,2,w//2,2,3).mean(axis=(1,3))
    return levels


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args(); source_path = args.source.resolve(); output = args.output.resolve()
    require(source_path.is_relative_to(ROOT) and output.is_relative_to(ROOT), 'Paths must stay in workspace')
    output.mkdir(parents=True, exist_ok=True)
    manifest = json.loads(source_path.read_text()); derived = copy.deepcopy(manifest)
    records = {}; inputs = {str(source_path): sha(source_path)}
    for key in sorted(AFFECTED):
        recipe = manifest[key]; colour_source = recipe['maps']['albedo']; alpha_source = recipe['maps']['alpha']
        for spec in (colour_source, alpha_source):
            require(sha(spec['path']) == spec['sha256'], 'Provider map hash differs')
            inputs[spec['path']] = spec['sha256']
        image = Image.open(colour_source['path'])
        require(image.mode == 'RGBA', 'Affected source must be the audited RGBA PNG')
        rgb = np.asarray(image)[:,:,:3].copy(); alpha = load_alpha(alpha_source['path'])
        edge = (alpha > .001) & (alpha < CLIP_THRESHOLD)
        require(edge.any() and float(np.mean(np.min(rgb[edge], axis=-1) > 204)) > .35,
                'Expected measured white-fringe contamination not present')
        corrected = nearest_opaque_rgb(rgb, alpha)
        target = output / (key + '_diff_rgb_dilated.png')
        require(not target.exists(), 'Refusing to replace an earlier derived atlas')
        Image.fromarray(corrected, 'RGB').save(target, compress_level=6)
        require(Image.open(target).mode == 'RGB', 'Derived colour must have no embedded alpha')
        require(np.array_equal(np.asarray(Image.open(target)), corrected), 'Lossless derivative roundtrip differs')
        proof = {'schemaVersion': 1, 'operation': 'nearest-opaque-rgb-padding', 'owner': OWNER,
                 'opaqueThreshold': OPAQUE_THRESHOLD, 'opacityMaskClipValue': recipe['opacityMaskClipValue'],
                 'algorithm': 'scipy.ndimage.distance_transform_edt Euclidean donor indices; replace RGB only below alpha .99; output RGB8 PNG',
                 'sourceAlbedo': copy.deepcopy(colour_source), 'sourceAlpha': copy.deepcopy(alpha_source),
                 'derivedAlbedo': {'path': str(target), 'sha256': sha(target)},
                 'sourceGenerator': {'path': str(Path(__file__).resolve()), 'sha256': sha(__file__)},
                 'sourceProvider': recipe['sourceUrl'], 'license': recipe['license'],
                 'providerTexturesUnmodified': True, 'alphaMapUnmodified': True, 'opaqueRGBByteExact': True,
                 'replacedTexelFraction': float(np.mean(alpha < OPAQUE_THRESHOLD)),
                 'sourceOpaqueLinearRGB': mean(linear(rgb)[alpha >= OPAQUE_THRESHOLD]),
                 'sourceFringeLinearRGB': mean(linear(rgb)[edge]),
                 'derivedFringeLinearRGB': mean(linear(corrected)[edge]),
                 'beforeMips': mip_audit(rgb,alpha.copy()), 'afterMips': mip_audit(corrected,alpha.copy()),
                 'simulationLimit': 'CPU linear box-filter/coverage simulation does not prove native Metal texture sampling or final rendered appearance'}
        derived[key]['maps']['albedo'] = copy.deepcopy(proof['derivedAlbedo'])
        derived[key]['albedoDerivation'] = {k: proof[k] for k in ('operation','opaqueThreshold','sourceAlbedo','sourceAlpha','sourceGenerator','opaqueRGBByteExact','alphaMapUnmodified')}
        records[key] = proof
        print(key, 'mip4 before', proof['beforeMips'][4]['visibleMeanLinearRGB'], 'after', proof['afterMips'][4]['visibleMeanLinearRGB'], flush=True)
    for path, expected in inputs.items(): require(sha(path) == expected, 'A provider input changed during derivation')
    report = {'status': 'derived-rgb-atlases-cpu-validated-awaiting-native', 'materials': records, 'inputFiles': inputs,
              'generator': {'path': str(Path(__file__).resolve()), 'sha256': sha(__file__)},
              'dependencies': {'numpy': np.__version__, 'scipy': scipy.__version__}}
    (output/'derived-material-manifest.json').write_text(json.dumps(derived,indent=2)+'\n')
    (output/'derivation-report.json').write_text(json.dumps(report,indent=2)+'\n')


if __name__ == '__main__': main()
