"""Isolated seasonal-field shader prototype; never changes source ortho or UE.

This is an explicitly artistic growing-season illustration of reviewed field
interiors, not a current satellite observation or a correction to 2024 imagery.
The material importer does not load this module until a later approved revision.
"""
import argparse
import hashlib
import json
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
LUMA = np.array([.2126, .7152, .0722], dtype=np.float64)
PARAMETERS = {'strength': .88, 'referenceLuminance': .18,
              'greenLinearRgb': [.065, .115, .030], 'textureExponent': .82,
              'chromaResidual': .07, 'maximumLinearReflectance': .32}

# Inputs: Source=linear photographic RGB; Mask=separate linear R8 mask sample.
# Alpha/extent validity and distance fade remain in the existing ortho graph.
SEASONAL_FIELD_HLSL = '''float y=dot(Source,float3(.2126,.7152,.0722));
float warmth=(Source.r-Source.g)/max(Source.r+Source.g,.00001);
float dry=smoothstep(-.02,.10,warmth);
float earth=1.0-smoothstep(.82,1.10,Source.b/max(Source.g,.00001));
float lit=smoothstep(.008,.035,y)*(1.0-smoothstep(.45,.70,y));
float w=saturate(Mask)*dry*earth*lit*.88;
float3 target=float3(.065,.115,.030)*pow(max(y,.004)/.18,.82);
float targetY=dot(target,float3(.2126,.7152,.0722));
target+=clamp(Source/max(y,.004)-1.0,-.8,.8)*targetY*.07;
target=clamp(target,0.0,.32);
return lerp(Source,target,w);'''


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def smoothstep(low, high, value):
    t = np.clip((np.asarray(value)-low)/(high-low), 0., 1.)
    return t*t*(3.-2.*t)


def srgb_to_linear(value):
    value = np.asarray(value, dtype=np.float64)
    return np.where(value <= .04045, value/12.92, ((value+.055)/1.055)**2.4)


def linear_to_srgb(value):
    value = np.clip(value, 0., 1.)
    return np.where(value <= .0031308, value*12.92, 1.055*value**(1/2.4)-.055)


def seasonal_color(source, mask):
    """Vectorized linear-light oracle matching SEASONAL_FIELD_HLSL constants."""
    source = np.asarray(source, dtype=np.float64)
    if source.shape[-1] != 3 or not np.isfinite(source).all():
        raise ValueError('Expected finite linear RGB')
    if np.any(source < 0) or np.any(source > 1):
        raise ValueError('Linear RGB outside [0,1]')
    mask = np.asarray(mask, dtype=np.float64)
    if not np.isfinite(mask).all():
        raise ValueError('Non-finite mask')
    y = source @ LUMA
    warmth = (source[..., 0]-source[..., 1])/np.maximum(source[..., 0]+source[..., 1], .00001)
    dry = smoothstep(-.02, .10, warmth)
    earth = 1.-smoothstep(.82, 1.10, source[..., 2]/np.maximum(source[..., 1], .00001))
    lit = smoothstep(.008, .035, y)*(1.-smoothstep(.45, .70, y))
    weight = np.clip(mask, 0., 1.)*dry*earth*lit*PARAMETERS['strength']
    target = np.asarray(PARAMETERS['greenLinearRgb'])*(np.maximum(y, .004)/PARAMETERS['referenceLuminance'])[..., None]**PARAMETERS['textureExponent']
    target_y = target @ LUMA
    target += np.clip(source/np.maximum(y[..., None], .004)-1., -.8, .8)*target_y[..., None]*PARAMETERS['chromaResidual']
    target = np.clip(target, 0., PARAMETERS['maximumLinearReflectance'])
    return source+(target-source)*weight[..., None], weight


def world_to_pixel(points_cm, layer):
    points = np.asarray(points_cm, dtype=np.float64)
    homogeneous = np.column_stack((points[:, :2], np.ones(len(points))))
    return (homogeneous @ np.asarray(layer['worldCmToUvRows']).T)*[layer['width'], layer['height']]


def raster_polygon(points_cm, layer):
    image = Image.new('L', (layer['width'], layer['height']))
    points = world_to_pixel(points_cm, layer)
    # UV maps pixel edges, whereas polygon raster coordinates address centers.
    ImageDraw.Draw(image).polygon([tuple(p-.5) for p in points], fill=255)
    return np.asarray(image) != 0


def interior_mask(binary, metres_per_pixel, inset_cm=1000., feather_cm=2000.):
    """Conservative inside-only physical feather, including pixel uncertainty."""
    from scipy.ndimage import distance_transform_edt
    if inset_cm < 0 or feather_cm <= 0 or metres_per_pixel <= 0:
        raise ValueError('Invalid physical feather')
    binary = np.asarray(binary, dtype=bool)
    # Explicit zero border prevents EDT treating atlas edges as unbounded field.
    distance = distance_transform_edt(np.pad(binary, 1))[1:-1, 1:-1]*metres_per_pixel*100.
    distance = np.maximum(0., distance-np.sqrt(2)*metres_per_pixel*100.)
    return smoothstep(inset_cm, inset_cm+feather_cm, distance)*binary


def build_mask(plan, layer, coverage):
    from scipy.ndimage import distance_transform_edt
    size = (layer['height'], layer['width'])
    px_m = layer['pixelSizeMetres']
    if abs(px_m[0]-px_m[1]) > 1e-9:
        raise ValueError('Only square projected pixels supported')
    blocked = np.zeros(size, dtype=bool)
    for row in plan.get('exclusions', []):
        shape = raster_polygon(row['polygonCm'], layer)
        if shape.any():
            distance = distance_transform_edt(~shape)*px_m[0]*100.
            blocked |= distance <= row.get('bufferCm', 1000.)+np.sqrt(2)*px_m[0]*100.
    valid = (np.asarray(coverage) >= .99) & ~blocked
    mask = np.zeros(size, dtype=np.float64)
    for row in plan['regions']:
        if row['kind'] != 'field-season-illustration':
            raise ValueError('Unreviewed field category')
        binary = raster_polygon(row['polygonCm'], layer) & valid
        local = interior_mask(binary, px_m[0], row.get('conservativeInsetCm', 1000.), row.get('innerFeatherCm', 2000.))
        mask = np.maximum(mask, local)
    return mask


def apply_preview(rgba, mask):
    """CPU shader simulation; source alpha and all zero-weight RGB stay exact."""
    original = np.asarray(rgba, dtype=np.uint8)
    result = original.copy()
    linear = srgb_to_linear(original[..., :3]/255.)
    color, weight = seasonal_color(linear, np.asarray(mask)*(original[..., 3] >= 253))
    changed = weight > 0
    result[..., :3][changed] = np.rint(linear_to_srgb(color[changed])*255).astype(np.uint8)
    return result, weight


def save_comparison(source, result, mask, target, synthetic=False):
    """A labelled data diagnostic, not rendered or fabricated native evidence."""
    width = 720
    a = Image.fromarray(source).convert('RGB'); a.thumbnail((width, width))
    b = Image.fromarray(result).convert('RGB'); b.thumbnail((width, width))
    c = Image.fromarray(np.rint(mask*255).astype(np.uint8)).convert('RGB'); c.thumbnail((width, width))
    canvas = Image.new('RGB', (a.width*3, a.height+40), '#202020')
    draw = ImageDraw.Draw(canvas)
    source_label = 'SYNTHETIC INPUT - NO MAP DATA' if synthetic else 'SOURCE ORTHOPHOTO 2024'
    mask_label = 'SYNTHETIC FIELD MASK' if synthetic else 'REVIEWED FIELD INTERIOR MASK'
    for i, (im, text) in enumerate(((a, source_label), (b, 'CPU SEASONAL PROTOTYPE - NOT NATIVE'), (c, mask_label))):
        canvas.paste(im, (i*a.width, 40)); draw.text((i*a.width+10, 12), text, fill='white')
    canvas.save(target)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan', required=True)
    parser.add_argument('--ortho', default=str(ROOT/'output/unreal/exterior-ortho-20260926-r1/orthophoto-manifest.json'))
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    plan_path = Path(args.plan).resolve(); ortho_path = Path(args.ortho).resolve(); folder = Path(args.output).resolve()
    if folder.exists():
        raise ValueError('Use a new output; source revisions are immutable')
    plan = json.loads(plan_path.read_text()); ortho = json.loads(ortho_path.read_text())
    if not plan.get('regions'):
        raise ValueError('No reviewed field interiors')
    inputs = {str(plan_path): sha(plan_path), str(ortho_path): sha(ortho_path), str(Path(__file__).resolve()): sha(__file__)}
    for path, digest in plan.get('inputFiles', {}).items():
        if sha(path) != digest:
            raise ValueError('Field evidence drift: '+path)
        inputs[path] = digest
    folder.mkdir(parents=True)
    layers = []; metrics = []
    for layer in ortho['layers']:
        path = Path(layer['rgbaPath'])
        if sha(path) != layer['rgbaSha256']:
            raise ValueError('Source ortho drift')
        inputs[str(path)] = sha(path)
        rgba = np.asarray(Image.open(path).convert('RGBA'))
        mask = build_mask(plan, layer, rgba[..., 3]/255.)
        # Stored R8 quantization is shared by the shader and CPU preview oracle.
        mask_bytes = np.rint(mask*255).astype(np.uint8); mask = mask_bytes/255.
        mask_path = folder/(layer['id']+'-field-mask.png'); Image.fromarray(mask_bytes).save(mask_path)
        # Full-resolution CPU conversion is processed in small strips to bound RAM.
        derived = rgba.copy(); changed = np.zeros(mask.shape, dtype=bool); positive = 0
        for y in range(0, len(rgba), 128):
            derived[y:y+128], weight = apply_preview(rgba[y:y+128], mask[y:y+128])
            changed[y:y+128] = np.any(derived[y:y+128, :, :3] != rgba[y:y+128, :, :3], axis=-1)
            positive += int((weight > 0).sum())
        unchanged_outside = bool(np.array_equal(derived[mask == 0], rgba[mask == 0]))
        assert unchanged_outside and np.array_equal(derived[..., 3], rgba[..., 3])
        Image.fromarray(derived).save(folder/(layer['id']+'-cpu-seasonal-preview.png'))
        save_comparison(rgba, derived, mask, folder/(layer['id']+'-comparison.png'))
        layers.append({'id': layer['id'], 'maskPath': str(mask_path), 'maskSha256': sha(mask_path),
                       'width': layer['width'], 'height': layer['height'], 'sRGB': False, 'addressMode': 'clamp',
                       'samplerMipPolicy': 'explicit-level-zero-for-geographic-containment',
                       'worldCmToUvRows': layer['worldCmToUvRows'], 'sourceRgbaSha256': layer['rgbaSha256'],
                       'maskSemantic': 'R8 reviewed field interior growing-season weight; not provider coverage'})
        metrics.append({'id': layer['id'], 'maskPixels': int((mask > 0).sum()), 'eligiblePixels': positive,
                        'changedPixels': int(changed.sum()), 'outsideMaskPixelsByteExact': unchanged_outside,
                        'sourceAlphaByteExact': True, 'sourcePngUnchanged': sha(path) == layer['rgbaSha256']})
    hlsl_path = folder/'seasonal-field.hlsl'; hlsl_path.write_text(SEASONAL_FIELD_HLSL+'\n')
    manifest = {'schemaVersion': 1, 'status': 'CPU_PROTOTYPE_AWAITING_NATIVE_REVIEW', 'parameters': PARAMETERS,
                'orthoManifest': {'path': str(ortho_path), 'sha256': sha(ortho_path)}, 'layers': layers,
                'inputFiles': inputs, 'shader': {'path': str(hlsl_path), 'sha256': sha(hlsl_path)},
                'application': 'Each ortho layer RGB before existing source alpha/extent/radial blend; only context_distant_terrain BaseColor.',
                'sourceObservationUnchanged': True, 'claim': 'Artist-authored green growing-season illustration; not observed current crop state.',
                'attribution': 'ČÚZK, 2024 · Ortofoto ČR · CC BY 4.0. Reviewed field interiors receive a separately recorded artistic growing-season colour transformation; no provider endorsement.'}
    (folder/'seasonal-fields-manifest.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False)+'\n')
    (folder/'preview-validation.json').write_text(json.dumps({'status': 'cpu-only', 'layers': metrics}, indent=2)+'\n')
    print(json.dumps(metrics, indent=2))


if __name__ == '__main__':
    main()
