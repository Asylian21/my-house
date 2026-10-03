"""CPU orthographic original-mesh preview, explicitly not an Unreal screenshot.

The original source UVs/base-color/normalized16-bit Alpha.R are sampled; no
scene, engine light, normal map, temporal AA, native material or pixel edit is
represented by these source inspection panels.
"""
import hashlib
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[2]
OWNER = 'scripts/unreal/exterior-garden-fern-preview-r25.py'
STUDY = ROOT/'output/unreal/exterior-garden-fern-20261002-r25-study'
OUTPUT = ROOT/'output/unreal/exterior-garden-fern-20261002-r25-source-review'


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def pin(path):
    return {'path': str(path), 'sha256': sha(path), 'bytes': path.stat().st_size}


def sample(texture, uv):
    # glTF texture origin is top-left. UVs retain their original glTF values.
    h, w = texture.shape[:2]
    p = np.clip(uv, 0., 1.)*np.array([w-1, h-1])
    lo = np.floor(p).astype(int)
    hi = np.minimum(lo+1, [w-1, h-1])
    f = p-lo
    if texture.ndim == 3:
        f = f[..., None, :]
        x, y = f[..., 0], f[..., 1]
    else:
        x, y = f[..., 0], f[..., 1]
    return ((1-x)*(1-y)*texture[lo[..., 1], lo[..., 0]]
            + x*(1-y)*texture[lo[..., 1], hi[..., 0]]
            + (1-x)*y*texture[hi[..., 1], lo[..., 0]]
            + x*y*texture[hi[..., 1], hi[..., 0]])


def render(points, indices, uvs, color, alpha, view, width=960, height=960):
    eye = np.array(view, dtype=float)
    eye /= np.linalg.norm(eye)
    up = np.array([0., 1., 0.]) if abs(eye[2]) > .99 else np.array([0., 0., 1.])
    right = np.cross(up, eye)
    right /= np.linalg.norm(right)
    up = np.cross(eye, right)
    projection = points@np.array([right, up, eye]).T
    low, high = projection[:, :2].min(axis=0), projection[:, :2].max(axis=0)
    scale = min((width-80)/(high[0]-low[0]), (height-80)/(high[1]-low[1]))
    screen = projection.copy()
    screen[:, 0] = (projection[:, 0]-(high[0]+low[0])/2)*scale+width/2
    screen[:, 1] = height/2-(projection[:, 1]-(high[1]+low[1])/2)*scale
    depth = np.full((height, width), -np.inf)
    result = np.full((height, width, 3), .93)
    hits = np.zeros((height, width), dtype=bool)
    for triangle in indices.reshape(-1, 3):
        p = screen[triangle]
        x0 = max(0, int(np.floor(p[:, 0].min())))
        x1 = min(width-1, int(np.ceil(p[:, 0].max())))
        y0 = max(0, int(np.floor(p[:, 1].min())))
        y1 = min(height-1, int(np.ceil(p[:, 1].max())))
        if x1 < x0 or y1 < y0:
            continue
        a, b, c = p[:, :2]
        den = (b[1]-c[1])*(a[0]-c[0])+(c[0]-b[0])*(a[1]-c[1])
        if abs(den) < 1e-9:
            continue
        y, x = np.mgrid[y0:y1+1, x0:x1+1]
        x, y = x+.5, y+.5
        u = ((b[1]-c[1])*(x-c[0])+(c[0]-b[0])*(y-c[1]))/den
        v = ((c[1]-a[1])*(x-c[0])+(a[0]-c[0])*(y-c[1]))/den
        w = 1-u-v
        bary = np.stack([u, v, w], axis=-1)
        inside = np.all(bary >= -1e-9, axis=-1)
        z = bary@p[:, 2]
        old = depth[y0:y1+1, x0:x1+1]
        tex = bary@uvs[triangle]
        mask = inside & (z > old) & (sample(alpha, tex) >= .5)
        if not mask.any():
            continue
        rgb = sample(color, tex)
        old[mask] = z[mask]
        result[y0:y1+1, x0:x1+1][mask] = rgb[mask]
        hits[y0:y1+1, x0:x1+1][mask] = True
    srgb = np.where(result <= .0031308, 12.92*result, 1.055*result**(1/2.4)-.055)
    return Image.fromarray(np.clip(srgb*255+.5, 0, 255).astype('uint8')), int(hits.sum())


def main():
    if OUTPUT.exists():
        raise RuntimeError('Refusing to overwrite source preview')
    plan_path = STUDY/'fern-pilot-source-plan.json'
    plan = json.loads(plan_path.read_text())
    geometry_path = Path(plan['selectedOriginalGeometry']['path'])
    if sha(geometry_path) != plan['selectedOriginalGeometry']['sha256']:
        raise RuntimeError('Original selected geometry pin changed')
    geometry = json.loads(geometry_path.read_text())
    material = plan['materialProposal']
    files = [Path(material[k]['path']) for k in ('baseColor', 'normalGL', 'arm')]
    files += [Path(material['explicitAlpha']['requiredExplicitAlphaMap']['path']), plan_path, geometry_path, Path(__file__)]
    before = {str(p): sha(p) for p in files}
    for k in ('baseColor', 'normalGL', 'arm'):
        if sha(material[k]['path']) != material[k]['sha256']:
            raise RuntimeError('Original material source changed')
    alpha_pin = material['explicitAlpha']['requiredExplicitAlphaMap']
    if sha(alpha_pin['path']) != alpha_pin['sha256']:
        raise RuntimeError('Original alpha source changed')
    positions = np.array(geometry['_positions'], dtype=float)
    points = positions[:, [0, 2, 1]]*100*plan['placementProposal']['uniformScale']
    indices = np.array(geometry['_indices'], dtype=int)
    uv = np.array(geometry['_uv'], dtype=float)
    rgb = np.array(Image.open(material['baseColor']['path']), dtype=float)/255
    color = np.where(rgb <= .04045, rgb/12.92, ((rgb+.055)/1.055)**2.4)
    alpha = np.array(Image.open(alpha_pin['path']), dtype=float)/65535
    OUTPUT.mkdir()
    panels = []
    for name, view in (('top', [0, 0, 1]), ('oblique', [.7, -1, .55])):
        panel, hit_pixels = render(points, indices, uv, color, alpha, view)
        canvas = Image.new('RGB', (960, 1020), 'white')
        canvas.paste(panel, (0, 60))
        draw = ImageDraw.Draw(canvas)
        draw.text((20, 12), 'CPU SOURCE ONLY - original Fern02.b | '+name, fill='#111111')
        draw.text((20, 33), 'Original geometry + BaseColor + normalized16-bit Alpha.R; no Unreal lighting.', fill='#333333')
        file = OUTPUT/('fern-original-'+name+'-cpu.png')
        canvas.save(file)
        panels.append({**pin(file), 'view': view, 'maskedRasterPixels': hit_pixels,
                       'width': canvas.width, 'height': canvas.height})
    if not all(sha(path) == digest for path, digest in before.items()):
        raise RuntimeError('Source changed during CPU rendering')
    receipt = {'owner': OWNER, 'status': 'rendered-original-fern-cpu-source-inspection-only',
        'plan': pin(plan_path), 'producer': pin(Path(__file__)), 'inputPinsBefore': before,
        'inputPinsAfterUnchanged': True, 'originalSourcePixelsEdited': False,
        'panels': panels, 'sampling': 'Orthographic; bilinear linear-sRGB BaseColor; bilinear Alpha normalized65535; cutoff.5; no mipmaps',
        'nativeScreenshot': False, 'nativeMaterialEvaluated': False, 'nativeAppearanceAccepted': False,
        'fullPhotorealismAccepted': False, 'performanceAccepted': False,
        'sourceFitHeightCm': plan['placementProposal']['abovePivotHeightCm'],
        'sourceFitRadiusCm': plan['placementProposal']['radialEnvelopeCm']}
    file = OUTPUT/'source-render-receipt.json'
    file.write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(pin(file)))


if __name__ == '__main__':
    main()
