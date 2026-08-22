#!/usr/bin/env python3
"""Deterministický generátor PBR textúr a IBL oblohy pre režim Realita.

Spustenie:  python3 tools/generate-visual-assets.py            (úplná sada)
            python3 tools/generate-visual-assets.py interior   (iba interiér)
Vygeneruje všetky procedurálne assety do public/assets (omietka, modřín,
terasové dosky, falcovaný plech, kačírek, betón, normálová mapa trávnika a
obloha). Žiadne externé zdroje ani licencie — všetko vzniká lokálne.
"""
import numpy as np
from PIL import Image, ImageFilter, ImageDraw
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "public", "assets", "textures")
ENV = os.path.join(ROOT, "public", "assets", "environment")
os.makedirs(OUT, exist_ok=True)
os.makedirs(ENV, exist_ok=True)
rng = np.random.default_rng(6012)


def fbm(shape, octaves=5, persistence=0.55, seed=0):
    r = np.random.default_rng(seed)
    h, w = shape
    total = np.zeros(shape, dtype=np.float64)
    amp, freq_h, freq_w = 1.0, 4, 4
    norm = 0.0
    for _ in range(octaves):
        g = r.random((freq_h + 1, freq_w + 1))
        gi = np.array(Image.fromarray((g * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC), dtype=np.float64) / 255.0
        total += gi * amp
        norm += amp
        amp *= persistence
        freq_h *= 2
        freq_w *= 2
    return total / norm


def normal_from_height(height, strength=2.0):
    gy, gx = np.gradient(height.astype(np.float64))
    nx = -gx * strength
    ny = -gy * strength
    nz = np.ones_like(height)
    l = np.sqrt(nx * nx + ny * ny + nz * nz)
    n = np.stack([(nx / l * 0.5 + 0.5), (ny / l * 0.5 + 0.5), (nz / l * 0.5 + 0.5)], axis=-1)
    return (n * 255).astype(np.uint8)


def save(img_arr, path, quality=90):
    Image.fromarray(img_arr).save(path, quality=quality)
    print("saved", path)


# ---------------------------------------------------------------- larch cladding (vertical boards 50 mm)
def gen_larch(size=1024, boards=20, fname="larch"):
    h = w = size
    albedo = np.zeros((h, w, 3), dtype=np.float64)
    height = np.zeros((h, w), dtype=np.float64)
    bw = w // boards
    # warm larch palette (like reference photo: golden-honey siberian larch)
    base_colors = [(196, 148, 92), (188, 138, 82), (203, 157, 102), (181, 131, 78), (192, 145, 95), (172, 122, 72)]
    grain = fbm((h, w), octaves=6, seed=11)
    fine = fbm((h, w // 8), octaves=4, seed=12)
    fine = np.array(Image.fromarray((fine * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)) / 255.0
    for b in range(boards):
        x0, x1 = b * bw, (b + 1) * bw
        c = np.array(base_colors[b % len(base_colors)], dtype=np.float64)
        tone = 0.86 + 0.28 * rng.random()
        col = c * tone
        # vertical grain: stretch noise column-wise
        g = grain[:, x0:x1]
        gg = np.array(Image.fromarray((g * 255).astype(np.uint8)).resize((x1 - x0, h * 4), Image.BICUBIC).resize((x1 - x0, h), Image.LANCZOS)) / 255.0
        streak = (fine[:, x0:x1] - 0.5) * 18 + (gg - 0.5) * 60
        for ch in range(3):
            albedo[:, x0:x1, ch] = np.clip(col[ch] + streak * (1.1 - ch * 0.18), 40, 240)
        height[:, x0:x1] = 0.5 + (gg - 0.5) * 0.25
        # board gap (shadow line)
        gap = max(2, bw // 24)
        albedo[:, x1 - gap:x1] *= 0.42
        height[:, x1 - gap:x1] -= 0.45
    save(albedo.astype(np.uint8), f"{OUT}/{fname}-albedo.jpg")
    save(normal_from_height(height, 3.2), f"{OUT}/{fname}-normal.jpg")


# ---------------------------------------------------------------- white ETICS plaster
def gen_plaster(size=1024):
    n1 = fbm((size, size), octaves=7, persistence=0.62, seed=21)
    n2 = fbm((size, size), octaves=3, seed=22)
    base = 243 - n1 * 10 - n2 * 6
    albedo = np.stack([base + 1.5, base + 0.5, base - 3.0], axis=-1)
    albedo = np.clip(albedo, 215, 250).astype(np.uint8)
    save(albedo, f"{OUT}/plaster-white-albedo.jpg")
    save(normal_from_height(n1 * 0.5 + n2 * 0.2, 1.7), f"{OUT}/plaster-white-normal.jpg")


# ---------------------------------------------------------------- deck boards (running lengthwise, u axis)
def gen_deck(size=1024, fname="deck-plank"):
    # single wide board texture with horizontal grain; per-plank tint via uv offsets
    h = w = size
    grain = fbm((h // 8, w), octaves=6, seed=31)
    grain = np.array(Image.fromarray((grain * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)) / 255.0
    rings = fbm((h, w), octaves=4, seed=32)
    base = np.array((176, 132, 86), dtype=np.float64)  # weathered warm larch deck
    streak = (grain - 0.5) * 74 + (rings - 0.5) * 8
    albedo = np.zeros((h, w, 3))
    for ch in range(3):
        albedo[:, :, ch] = np.clip(base[ch] + streak * (1.12 - ch * 0.2), 40, 235)
    save(albedo.astype(np.uint8), f"{OUT}/{fname}-albedo.jpg")
    save(normal_from_height(grain * 0.6 + rings * 0.2, 2.2), f"{OUT}/{fname}-normal.jpg")


# ---------------------------------------------------------------- anthracite standing-seam metal (micro)
def gen_metal(size=512):
    n = fbm((size, size), octaves=5, seed=41)
    brush = fbm((size, size // 16), octaves=3, seed=42)
    brush = np.array(Image.fromarray((brush * 255).astype(np.uint8)).resize((size, size), Image.BICUBIC)) / 255.0
    base = 52 + n * 10 + brush * 7
    albedo = np.stack([base * 0.96, base * 1.0, base * 1.05], axis=-1)
    save(np.clip(albedo, 30, 90).astype(np.uint8), f"{OUT}/metal-anthracite-albedo.jpg")
    save(normal_from_height(n * 0.3 + brush * 0.15, 0.9), f"{OUT}/metal-anthracite-normal.jpg")


# ---------------------------------------------------------------- concrete paving
def gen_concrete(size=1024):
    n = fbm((size, size), octaves=6, seed=51)
    spots = fbm((size, size), octaves=2, seed=52)
    base = 172 - n * 26 - spots * 14
    albedo = np.stack([base + 3, base + 2, base - 2], axis=-1)
    save(np.clip(albedo, 120, 200).astype(np.uint8), f"{OUT}/concrete-albedo.jpg")
    save(normal_from_height(n * 0.6, 1.6), f"{OUT}/concrete-normal.jpg")


# ---------------------------------------------------------------- gravel strip
def gen_gravel(size=1024):
    h = w = size
    albedo = np.full((h, w, 3), 150.0)
    height = np.zeros((h, w))
    yy, xx = np.mgrid[0:h, 0:w]
    for _ in range(6000):
        cx, cy = rng.integers(0, w), rng.integers(0, h)
        r = rng.integers(3, 11)
        tone = 105 + rng.random() * 105
        tint = rng.random() * 14 - 7
        mask = (xx - cx) ** 2 + (yy - cy) ** 2 < r * r
        albedo[mask] = [tone + tint + 6, tone + 2, tone - tint]
        height[mask] = rng.random() * 0.8 + 0.2
    blur = np.array(Image.fromarray((height * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.4))) / 255.0
    save(np.clip(albedo, 60, 230).astype(np.uint8), f"{OUT}/gravel-albedo.jpg")
    save(normal_from_height(blur, 3.4), f"{OUT}/gravel-normal.jpg")


# ---------------------------------------------------------------- lawn normal (from existing albedo) + refresh
def gen_lawn():
    src = Image.open(f"{OUT}/lawn-albedo.jpg").convert("RGB")
    arr = np.array(src, dtype=np.float64)
    # vivid mowed lawn tint like the reference photo
    lum = arr.mean(axis=-1, keepdims=True)
    tinted = arr * 0.55 + np.concatenate([lum * 0.42, lum * 0.62, lum * 0.30], axis=-1)
    tinted[:, :, 1] *= 1.06
    save(np.clip(tinted, 15, 235).astype(np.uint8), f"{OUT}/lawn-albedo-v2.jpg")
    small = np.array(src.convert("L").resize((512, 512)), dtype=np.float64) / 255.0
    save(normal_from_height(small, 1.5), f"{OUT}/lawn-normal.jpg")


# ---------------------------------------------------------------- partly cloudy sky equirect (IBL + dome upper half)
def gen_sky(w=2048, h=1024):
    yy = np.linspace(0, 1, h)[:, None]  # 0 top .. 1 bottom
    xx = np.linspace(0, 1, w)[None, :]
    # gradient: zenith blue -> horizon pale warm grey
    t = np.clip((yy - 0.02) / 0.5, 0, 1) ** 0.62
    t = t * np.ones((1, w))
    yy = yy * np.ones((1, w))
    xx = xx * np.ones((h, 1))
    zen = np.array([96, 138, 189], dtype=np.float64)
    hor = np.array([214, 219, 221], dtype=np.float64)
    sky = zen[None, None, :] * (1 - t)[:, :, None] + hor[None, None, :] * t[:, :, None]
    # sun glow (soft, matching photo's diffuse light) at azimuth ~0.22, elevation ~35deg
    sun_x, sun_y = 0.24, 0.30
    d = np.sqrt(((xx - sun_x) * 1.6) ** 2 + (yy - sun_y) ** 2)
    d2 = np.sqrt(((xx - sun_x + 1.0) * 1.6) ** 2 + (yy - sun_y) ** 2)  # wrap
    d = np.minimum(d, d2)
    glow = np.exp(-(d ** 2) / 0.03) * 46 + np.exp(-(d ** 2) / 0.0018) * 78
    sky += glow[:, :, None] * np.array([1.0, 0.97, 0.9])[None, None, :]
    # clouds: stratocumulus field, denser near horizon
    c = fbm((h, w), octaves=6, persistence=0.58, seed=61)
    c2 = fbm((h, w), octaves=3, seed=62)
    cl = np.clip((c * 0.85 + c2 * 0.55 - 0.60) * 3.0, 0, 1)
    horizon_boost = np.clip((yy - 0.18) * 2.2, 0, 1)
    cl = cl * (0.35 + horizon_boost * 0.65)
    cl = cl * np.clip((0.52 - np.abs(yy - 0.3)) * 6, 0, 1)
    cloud_col = np.array([238, 240, 242], dtype=np.float64)
    shade = 1 - cl * 0.18
    sky = sky * (1 - cl[:, :, None]) + (cloud_col * shade[:, :, None] * np.ones(3)[None, None, :]) * cl[:, :, None] if False else sky * (1 - cl[:, :, None]) + cloud_col[None, None, :] * (shade * cl)[:, :, None]
    # ground half: soft green-grey (bounce light for IBL)
    ground_mask = (yy >= 0.5)
    g_t = np.clip((yy - 0.5) / 0.5, 0, 1) ** 0.7
    g_col_top = np.array([150, 158, 138], dtype=np.float64)
    g_col_bot = np.array([92, 104, 76], dtype=np.float64)
    ground = g_col_top[None, None, :] * (1 - g_t)[:, :, None] + g_col_bot[None, None, :] * g_t[:, :, None]
    gn = fbm((h, w), octaves=4, seed=63)
    ground += ((gn - 0.5) * 18)[:, :, None]
    sky = np.where(ground_mask[:, :, None], ground, sky)
    # horizon treeline silhouette band
    tree = fbm((1, w), octaves=5, seed=64)[0]
    tree_h = (0.505 + tree * 0.02)
    band = np.clip((yy - tree_h[None, :] + 0.012) / 0.012, 0, 1) * np.clip((tree_h[None, :] + 0.035 - yy) / 0.035, 0, 1)
    tree_col = np.array([74, 88, 64], dtype=np.float64)
    sky = sky * (1 - band[:, :, None] * 0.85) + tree_col[None, None, :] * band[:, :, None] * 0.85
    out = np.clip(sky, 0, 255).astype(np.uint8)
    img = Image.fromarray(out).filter(ImageFilter.GaussianBlur(1.1))
    img.save(f"{ENV}/sky-partly-cloudy.jpg", quality=92)
    print("saved", f"{ENV}/sky-partly-cloudy.jpg")


# ---------------------------------------------------------------- interior: vinyl oak planks (1.02–1.04, 1.08–1.10, 1.03)
def gen_vinyl_oak(size=1024, rows=8, fname="vinyl-oak"):
    """Svetlý dubový vinyl: 8 dosiek na dlaždicu, posunuté škáry, jemná kresba."""
    h = w = size
    albedo = np.zeros((h, w, 3), dtype=np.float64)
    height = np.zeros((h, w), dtype=np.float64)
    r = np.random.default_rng(612)
    bh = h // rows
    base_colors = [(214, 188, 150), (206, 178, 138), (220, 196, 160), (199, 170, 130), (211, 184, 146), (224, 200, 166)]
    for i in range(rows):
        grain = fbm((bh, w), octaves=6, seed=700 + i)
        fine = fbm((bh, w), octaves=7, persistence=0.7, seed=760 + i)
        col = np.array(base_colors[i % len(base_colors)], dtype=np.float64)
        streak = (grain - 0.5) * 34 + (fine - 0.5) * 10
        y0, y1 = i * bh, (i + 1) * bh
        for ch in range(3):
            albedo[y0:y1, :, ch] = np.clip(col[ch] + streak * (1.1 - ch * 0.12), 90, 245)
        height[y0:y1, :] = grain * 0.35 + fine * 0.15
        joint = int((r.random() * 0.6 + 0.2) * w)
        albedo[y0:y1, joint:joint + 2, :] *= 0.72
        height[y0:y1, joint:joint + 2] -= 0.5
        albedo[y0:y0 + 2, :, :] *= 0.74
        height[y0:y0 + 2, :] -= 0.5
    save(albedo.astype(np.uint8), f"{OUT}/{fname}-albedo.jpg")
    save(normal_from_height(height, 2.0), f"{OUT}/{fname}-normal.jpg")


# ---------------------------------------------------------------- interior: porcelain floor tile 600 × 600 (2 × 2 per tile)
def gen_tile(size=1024, per_side=2, fname="tile-porcelain"):
    h = w = size
    n = fbm((h, w), octaves=5, seed=811)
    fine = fbm((h, w), octaves=7, persistence=0.65, seed=812)
    base = np.array((196, 194, 188), dtype=np.float64)
    albedo = np.zeros((h, w, 3), dtype=np.float64)
    tone = (n - 0.5) * 22 + (fine - 0.5) * 8
    for ch in range(3):
        albedo[:, :, ch] = np.clip(base[ch] + tone, 120, 230)
    height = n * 0.2 + fine * 0.1
    step = w // per_side
    grout = 5
    for k in range(per_side + 1):
        a = min(w - grout, k * step)
        albedo[a:a + grout, :, :] = (150, 148, 144)
        albedo[:, a:a + grout, :] = (150, 148, 144)
        height[a:a + grout, :] -= 0.9
        height[:, a:a + grout] -= 0.9
    save(albedo.astype(np.uint8), f"{OUT}/{fname}-albedo.jpg")
    save(normal_from_height(height, 1.8), f"{OUT}/{fname}-normal.jpg")


# ---------------------------------------------------------------- interior: epoxy floor (garage, technical room)
def gen_epoxy(size=512, fname="epoxy-grey"):
    h = w = size
    n = fbm((h, w), octaves=4, seed=901)
    flakes = np.random.default_rng(902).random((h, w)) > 0.992
    base = np.array((142, 146, 148), dtype=np.float64)
    albedo = np.zeros((h, w, 3), dtype=np.float64)
    for ch in range(3):
        albedo[:, :, ch] = np.clip(base[ch] + (n - 0.5) * 12, 100, 190)
    albedo[flakes] = (210, 210, 206)
    save(albedo.astype(np.uint8), f"{OUT}/{fname}-albedo.jpg")
    save(normal_from_height(n * 0.08, 0.6), f"{OUT}/{fname}-normal.jpg")


# ---------------------------------------------------------------- interior: wall tiles 300 × 600 (wet rooms up to 2 100)
def gen_wall_tile(size=1024, fname="tile-wall"):
    h = w = size
    n = fbm((h, w), octaves=4, seed=921)
    base = np.array((226, 226, 222), dtype=np.float64)
    albedo = np.zeros((h, w, 3), dtype=np.float64)
    for ch in range(3):
        albedo[:, :, ch] = np.clip(base[ch] + (n - 0.5) * 10, 180, 245)
    height = n * 0.1
    grout = 4
    for k in range(0, w + 1, w // 2):
        a = min(w - grout, k)
        albedo[:, a:a + grout, :] = (190, 190, 186)
        height[:, a:a + grout] -= 0.8
    for k in range(0, h + 1, h // 4):
        a = min(h - grout, k)
        albedo[a:a + grout, :, :] = (190, 190, 186)
        height[a:a + grout, :] -= 0.8
    save(albedo.astype(np.uint8), f"{OUT}/{fname}-albedo.jpg")
    save(normal_from_height(height, 1.6), f"{OUT}/{fname}-normal.jpg")



# ---------------------------------------------------------------- interior: oak veneer kitchen fronts (matt, straight grain)
def gen_oak_veneer(size=1024, fname="oak-veneer"):
    h = w = size
    grain = fbm((h, w // 16), octaves=6, persistence=0.6, seed=1201)
    grain = np.array(Image.fromarray((grain * 255).astype(np.uint8)).resize((w, h), Image.BICUBIC)) / 255.0
    fine = fbm((h, w), octaves=7, persistence=0.7, seed=1202)
    base = np.array((205, 176, 134), dtype=np.float64)
    albedo = np.zeros((h, w, 3), dtype=np.float64)
    streak = (grain - 0.5) * 26 + (fine - 0.5) * 8
    for ch in range(3):
        albedo[:, :, ch] = np.clip(base[ch] + streak * (1.1 - ch * 0.15), 110, 235)
    save(albedo.astype(np.uint8), f"{OUT}/{fname}-albedo.jpg")
    save(normal_from_height(grain * 0.25 + fine * 0.08, 1.2), f"{OUT}/{fname}-normal.jpg")


# ---------------------------------------------------------------- interior: dark quartz worktop
def gen_stone_dark(size=1024, fname="stone-dark"):
    h = w = size
    n = fbm((h, w), octaves=5, seed=1301)
    r = np.random.default_rng(1302)
    speck = r.random((h, w))
    base = np.array((58, 60, 62), dtype=np.float64)
    albedo = np.zeros((h, w, 3), dtype=np.float64)
    for ch in range(3):
        albedo[:, :, ch] = np.clip(base[ch] + (n - 0.5) * 14, 35, 90)
    albedo[speck > 0.985] = (120, 122, 124)
    albedo[speck < 0.006] = (22, 22, 24)
    save(albedo.astype(np.uint8), f"{OUT}/{fname}-albedo.jpg")
    save(normal_from_height(n * 0.05, 0.4), f"{OUT}/{fname}-normal.jpg")

import sys

if "interior" in sys.argv:
    # Only the interior set; the exterior assets above stay byte-identical
    # to the committed files and are regenerated only on an explicit full run.
    gen_vinyl_oak()
    gen_tile()
    gen_epoxy()
    gen_wall_tile()
    gen_oak_veneer()
    gen_stone_dark()
    print("INTERIOR DONE")
    sys.exit(0)


gen_larch()
gen_plaster()
gen_deck()
gen_metal()
gen_concrete()
gen_gravel()
gen_lawn()
gen_sky()
print("ALL DONE")
