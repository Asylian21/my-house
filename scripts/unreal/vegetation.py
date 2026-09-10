"""Source-bounded vegetation planning and explicitly invoked native hedge authoring.

Run with ordinary Python (no Unreal, Blender, GPU or network):
    python3 scripts/unreal/vegetation.py

The CLI JSON is a proposal and deterministic lawn root candidate set, never a native
import receipt. It verifies the three existing CC0 model downloads, current OBJ
and manifest, registers exact source patches and excludes active hardscape from
the actual triangulated lawn. Original actors/assets are never modified.

Native integration contract (apply_hedge_detail is invoked by the coordinated importer):
1. In a separate, coordinated Blender process, export individual grass/shrub
   prototypes from the verified .blend files. Preserve original leaf UV islands,
   alpha and normals; bake source object transforms, put the pivot at the root,
   and record actual vertices/bounds, material slots, source and output SHA256.
   Do not reuse the whole historical landscape or put a scan atlas on a box.
2. Import those prototypes to /Game/Brezi/VegetationGenerated. Build MASKED,
   TwoSidedFoliage materials with UV0 albedo(sRGB), alpha(linear) -> OpacityMask,
   normal(linear, OpenGL green flipped once), roughness(linear), two-sided=true.
   SubsurfaceColor/transmission must be a separate documented artistic parameter:
   the downloaded files contain no calibrated transmission map. Woody tree parts
   remain opaque DefaultLit; a tree has no placement permission in this scene.
3. Resolve each source ID to its existing actor. Reject unknown, missing, merged,
   disabled or multiply-consumed source objects. Recheck all hashes. Measure every
   transformed prototype's vertices against its registered patch and exclusion
   polygons; candidates below are NOT a substitute for that final geometry gate.
4. Create HISM components grouped by source patch + prototype + spatial cell, with
   stable IDs, no collision/navigation and bounded culling. Add instances in batches,
   preserve UV0, use per-instance random variation only within a documented range.
   Component serialization and packaged survival must be verified with UE5.8.2.
5. Lawn is additive: NEVER hide the base terrain/walk surface. Only after all
   instances/materials/bounds for a replacement patch pass validation, hide its
   explicitly listed proxy components using SetVisibility(false) and record their
   original visibility. Do not delete source actors, meshes, collision or metadata.
   Save generated IDs, source IDs, prior visibility, all asset/map hashes in a new
   receipt. A rerun restores previous proxy visibility before replacing its own
   generated instances. A failure restores visibility and must not emit success.
6. A future opt-in hook belongs after canonical actor/bounds verification and
   materials, before map save/hash receipts in import_scene.py. That hook must
   include this file, prototype converter, textures and native asset hashes in
   pipelineFiles and package provenance. No hook is installed by this module.

Density/culling/transmission are proposals awaiting native visual/performance QA;
this module makes no standalone-app, photorealism or 4K performance claims.
"""

from __future__ import annotations

import argparse
import bisect
import hashlib
import json
import math
import os
from pathlib import Path
import random
import re
import sys


ROOT = Path(__file__).resolve().parents[2]
MODEL_IDS = ("grass_bermuda_01", "shrub_02", "tree_small_02")
CARD_RE = re.compile(
    r"^(Riedka náletová vegetácia krajnice|Trvalkový záhon|Okrasná tráva) ([1-9][0-9]*)"
    r" · (fotografia stavebníka|ilustračný koncept) · krížená botanická karta ([123])$"
)
CARD_RULES = {
    "Riedka náletová vegetácia krajnice": ("fotografia stavebníka", "real-plant-grass"),
    "Trvalkový záhon": ("ilustračný koncept", "real-plant-perennial"),
    "Okrasná tráva": ("ilustračný koncept", "real-plant-grass"),
}
HEDGE_RULES = {
    "Zadná hranica · súvislé tmavé jadro živého plota": ("Landscape", "real-hedge-dark"),
    "Zadná hranica · hustý živý plot · tón 1": ("Fence", "real-hedge-dark"),
    "Zadná hranica · hustý živý plot · tón 2": ("Fence", "real-hedge-mid"),
    "Zadná hranica · hustý živý plot · tón 3": ("Fence", "real-hedge-light"),
}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def digest(path, algorithm="sha256"):
    h = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def checked_child(root, relative):
    """The lock may name files only inside the supplied asset root, no symlinks."""
    part = Path(relative)
    require(not part.is_absolute() and part.parts and ".." not in part.parts,
            "Unsafe asset path in lock")
    path = root
    require(not path.is_symlink(), "Asset root must not be a symlink")
    for segment in part.parts:
        path = path / segment
        require(not path.is_symlink(), "Symlink asset refused: " + relative)
    require(path.is_file(), "Missing asset: " + relative)
    return path


def audit_assets(lock_path, asset_root):
    lock = json.loads(lock_path.read_text())
    require(lock.get("license") == "CC0-1.0" and lock.get("source") == "Poly Haven",
            "Expected existing Poly Haven CC0 lock")
    require(lock.get("licenseUrl") == "https://polyhaven.com/license", "License URL changed")
    result = []
    for model_id in MODEL_IDS:
        model = lock["models"][model_id]
        require(model["page"] == "https://polyhaven.com/a/" + model_id, "Asset identity changed")
        files = []
        for entry in [model, *model["include"].values()]:
            path = checked_child(asset_root, entry["path"])
            require(path.stat().st_size == entry["size"], "Asset size mismatch: " + entry["path"])
            require(digest(path, "md5") == entry["md5"], "Asset MD5 mismatch: " + entry["path"])
            files.append({"path": entry["path"], "bytes": entry["size"], "md5": entry["md5"],
                          "sha256": digest(path)})
        result.append({"id": model_id, "page": model["page"], "license": "CC0-1.0",
                       "authors": model["authors"], "verifiedFiles": files,
                       "nativePrototypeStatus": "not-created-or-verified-by-this-module"})
    return {"licenseUrl": lock["licenseUrl"], "lockSha256": digest(lock_path), "models": result,
            "verifiedFileCount": sum(len(m["verifiedFiles"]) for m in result)}


def audit_legacy_grass():
    """An intact old GLB is insufficient without a reproducible source chain."""
    manifest_path = ROOT / "public/assets/archviz/export-manifest.json"
    prototype_path = ROOT / "public/assets/archviz/dom-grass-prototype.glb"
    source_path = ROOT / "output/archviz/dom-archviz.blend"
    if not all(p.is_file() and not p.is_symlink() for p in (manifest_path, prototype_path, source_path)):
        return {"reuseAllowed": False, "reason": "Historical prototype/source chain unavailable"}
    manifest = json.loads(manifest_path.read_text())
    entries = [e for e in manifest["files"] if e["file"] == prototype_path.name]
    require(len(entries) == 1, "Ambiguous historical grass prototype receipt")
    return {"reuseAllowed": False, "prototypeSha256": digest(prototype_path),
            "prototypeMatchesHistoricalExport": digest(prototype_path) == entries[0]["sha256"],
            "currentSourceBlendMatchesHistoricalExport": digest(source_path) == manifest["sourceSha256"],
            "reason": "Require a new prototype conversion receipt bound to the current verified model lock; do not import a historical landscape."}


def union_bounds(records):
    return {"min": [min(o["boundsMm"]["min"][i] for o in records) for i in range(3)],
            "max": [max(o["boundsMm"]["max"][i] for o in records) for i in range(3)]}


def patch_id(source_identity):
    return "VEG_" + hashlib.sha256(source_identity.encode()).hexdigest()[:16]


def register_patches(scene):
    """Strict source names + semantic metadata, never broad Landscape grouping."""
    objects = scene["objects"]
    require(len({o["id"] for o in objects}) == len(objects), "Duplicate canonical object IDs")
    patches, cards, hedge, lawns = [], {}, {}, []
    registered = set()
    for obj in objects:
        materials = set(obj["materialNames"])
        name, metadata = obj["name"], obj.get("metadata") or {}
        if metadata.get("walkSurfaceId") == "parcel-6012-26":
            require(obj["enabled"] and materials == {"real-grass"} and obj["group"] == "Landscape",
                    "Parcel lawn source changed")
            lawns.append(obj)
        elif match := CARD_RE.fullmatch(name):
            kind, index, provenance, card = match.groups()
            expected_provenance, material = CARD_RULES[kind]
            require(obj["enabled"] and obj["group"] == "Landscape" and materials == {material}
                    and provenance == expected_provenance and obj["sourceId"] == name,
                    "Botanical card identity changed: " + obj["id"])
            key = (kind, index, provenance)
            require(card not in cards.setdefault(key, {}), "Duplicate botanical card: " + name)
            cards[key][card] = obj
        elif name in HEDGE_RULES:
            group, material = HEDGE_RULES[name]
            require(obj["enabled"] and obj["group"] == group and materials == {material}
                    and metadata.get("entityId") == "SITE-FENCE", "Hedge identity changed")
            require(name not in hedge, "Duplicate hedge source")
            hedge[name] = obj
        elif any(m.startswith(("real-plant-", "real-hedge-")) or m == "real-grass" for m in materials):
            raise ValueError("Unregistered vegetation source; no automatic replacement: " + obj["id"])
    require(len(lawns) == 1, "Expected exactly one canonical parcel lawn")

    def register(identity, records, kind, status, allow_source_aggregate=False, **extra):
        ids = sorted(o["id"] for o in records)
        require(not registered.intersection(ids), "Source geometry consumed by multiple patches")
        registered.update(ids)
        require(allow_source_aggregate or all(o.get("instances") == 1 for o in records),
                "Merged/instanced source needs explicit mapping")
        patches.append({"id": patch_id(identity), "sourceIdentity": identity, "kind": kind,
                        "sourceObjectIds": ids, "sourceBoundsMm": union_bounds(records),
                        "sourceInstanceCounts": {o["id"]: o["instances"] for o in records},
                        "status": status, "hideSourceObjectIdsNow": [], **extra})

    register("parcel-6012-26", lawns, "lawn", "candidate-roots-only",
             proposedModel="grass_bermuda_01", sourcePolicy="additive; retain base lawn and walk collision")
    for (kind, index, provenance), members in sorted(cards.items()):
        require(set(members) == {"1", "2", "3"}, "Incomplete botanical card patch: " + kind + " " + index)
        records = [members[str(i)] for i in range(1, 4)]
        # buildPlantCard deliberately offsets cards 2/3 by 55mm and lifts card 3
        # by 25mm. Validate that exact source contract instead of treating a
        # shared name or overlapping AABB as enough evidence for one patch.
        centers = [[(o["boundsMm"]["min"][i] + o["boundsMm"]["max"][i]) / 2 for i in range(3)]
                   for o in records]
        heights = [o["boundsMm"]["max"][2] - o["boundsMm"]["min"][2] for o in records]
        widths = [math.hypot(*(o["boundsMm"]["max"][i] - o["boundsMm"]["min"][i] for i in (0, 1)))
                  for o in records]
        require(all(abs(math.dist(c[:2], centers[0][:2]) - 55) <= 0.05 for c in centers[1:])
                and abs(centers[1][2] - centers[0][2]) <= 0.05
                and abs(centers[2][2] - centers[0][2] - 25) <= 0.05
                and abs(heights[1] - heights[0] * 0.94) <= 0.05
                and abs(heights[2] - heights[0]) <= 0.05
                and abs(widths[1] - widths[0]) <= 0.05
                and abs(widths[2] - widths[0] * 0.88) <= 0.05,
                "Botanical cards do not match the canonical root/layout: " + kind + " " + index)
        register(f"{kind} {index} · {provenance}", records, "botanical-card-patch",
                 "deferred-matching-plant-prototype-required", provenance=provenance,
                 reason="Low Bermuda lawn blades are not a measured replacement for tall ornamental/roadside plants; shrub_02 is not a flowering perennial.")
    require(set(hedge) == set(HEDGE_RULES), "Rear hedge sources incomplete or changed")
    runs = [r for r in scene["fence"]["physicalFixedRuns"] if r.get("treatment") == "LIVING_HEDGE"]
    require(len(runs) == 1 and runs[0]["id"] == "FENCE-PHYSICAL-REAR", "Unregistered living hedge alignment")
    run = runs[0]
    register(run["id"], list(hedge.values()), "hedge", "prototype-footprint-validation-pending",
             allow_source_aggregate=True,
             proposedModel="shrub_02", canonicalRun=run,
             aggregationPolicy="Only the four explicitly registered hedge source objects; preserve each full object's triangle identity. Their existing source instances are already baked in the verified OBJ.",
             sourcePolicy="replace only four listed proxy visuals after complete bounded coverage; preserve design proposal status")
    return patches


def read_source_triangles(obj_path, scene, required_ids):
    """Read source world-space millimetres. Refuse missing/extra/merged OBJ objects."""
    require(digest(obj_path) == scene["objSha256"], "Source OBJ hash does not match scene.json")
    expected = {o["id"]: o for o in scene["objects"]}
    vertices, triangles, counts, seen = [], {}, {}, set()
    current = None
    with obj_path.open() as stream:
        for line in stream:
            fields = line.split()
            if not fields:
                continue
            if fields[0] == "o":
                current = fields[1]
                require(current in expected and current not in seen, "Unknown or merged/repeated OBJ object")
                seen.add(current)
                counts[current] = 0
                if current in required_ids:
                    triangles[current] = []
            elif fields[0] == "v":
                point = tuple(float(v) for v in fields[1:])
                require(len(point) == 3 and all(math.isfinite(v) for v in point), "Invalid OBJ vertex")
                vertices.append(point)
            elif fields[0] == "f":
                require(current is not None and len(fields) == 4, "Expected triangulated named source OBJ")
                indices = [int(f.split("/")[0]) for f in fields[1:]]
                require(all(1 <= i <= len(vertices) for i in indices), "Invalid source OBJ index")
                counts[current] += 1
                if current in required_ids:
                    triangles[current].append(tuple(vertices[i - 1] for i in indices))
    require(seen == set(expected), "Source OBJ/manifest identity set differs")
    require(all(counts[k] == expected[k]["triangles"] for k in expected), "OBJ triangle counts changed")
    for id_, faces in triangles.items():
        require(faces, "Empty registered patch geometry: " + id_)
        points = [v for face in faces for v in face]
        bounds = {"min": [min(p[i] for p in points) for i in range(3)],
                  "max": [max(p[i] for p in points) for i in range(3)]}
        require(all(abs(bounds[key][i] - expected[id_]["boundsMm"][key][i]) <= 0.05
                    for key in ("min", "max") for i in range(3)), "Source bounds changed: " + id_)
    return triangles


def hedge_source_components(scene, obj_path):
    """Recover the 153 exact existing convex crowns, never invent plant positions.

    Source instances were baked into OBJ; connected coordinate components recover
    their original identity. The registered continuous core is retained separately.
    Every component must be convex and counts must match the canonical instance
    count. Returned planes are outward-facing in source millimetres.
    """
    patch = next(p for p in register_patches(scene) if p["kind"] == "hedge")
    records = {o["id"]: o for o in scene["objects"]}
    triangles = read_source_triangles(obj_path, scene, set(patch["sourceObjectIds"]))
    result = []
    for id_, faces in triangles.items():
        if "jadro" in records[id_]["name"]:
            continue
        parent, point_faces = list(range(len(faces))), {}

        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i

        for index, face in enumerate(faces):
            for point in face:
                key = tuple(round(v, 3) for v in point)
                if key in point_faces:
                    parent[find(index)] = find(point_faces[key])
                else:
                    point_faces[key] = index
        groups = {}
        for index, face in enumerate(faces):
            groups.setdefault(find(index), []).append(face)
        require(len(groups) == records[id_]["instances"], "Hedge component identity/count changed: " + id_)
        for component_faces in groups.values():
            vertices = list(set(p for face in component_faces for p in face))
            bounds = {"min": [min(p[i] for p in vertices) for i in range(3)],
                      "max": [max(p[i] for p in vertices) for i in range(3)]}
            center = [(bounds["min"][i] + bounds["max"][i]) / 2 for i in range(3)]
            planes = {}
            for a, b, c in component_faces:
                u, v = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
                n = [u[1]*v[2]-u[2]*v[1], u[2]*v[0]-u[0]*v[2], u[0]*v[1]-u[1]*v[0]]
                length = math.sqrt(sum(v*v for v in n))
                if length < 1e-6:
                    continue
                n = [v / length for v in n]
                if sum(n[i] * (a[i] - center[i]) for i in range(3)) < 0:
                    n = [-v for v in n]
                d = sum(n[i] * a[i] for i in range(3))
                key = tuple(round(v, 7) for v in n) + (round(d, 3),)
                planes[key] = [*n, d]
            require(planes, "Empty hedge convex volume")
            # Local sphere seams differ by a few microns after OBJ serialization.
            require(all(sum(plane[i] * point[i] for i in range(3)) - plane[3] <= 0.02
                        for plane in planes.values() for point in vertices), "Non-convex hedge source requires explicit policy")
            identity = id_ + "/" + hashlib.sha256(json.dumps([round(v, 3) for v in center]).encode()).hexdigest()[:12]
            result.append({"id": identity, "sourceObjectId": id_, "centerMm": center,
                           "boundsMm": bounds, "sourceTriangles": len(component_faces),
                           "verticesMm": vertices, "planesMm": list(planes.values())})
    require(len(result) == 153, "Expected the current 153 registered hedge crowns")
    return patch, sorted(result, key=lambda c: c["id"])


def polygon_from_rect(rect):
    return [[rect["x0"], rect["y0"]], [rect["x1"], rect["y0"]],
            [rect["x1"], rect["y1"]], [rect["x0"], rect["y1"]]]


def exclusion_polygons(scene):
    """Explicit active semantics; superseded envelopes never suppress current lawn."""
    center = scene["sceneCenterMm"]
    records = []

    def add(identity, points):
        local = [[p["x"] - center["x"], p["y"] - center["y"]] if isinstance(p, dict)
                 else [p[0] - center["x"], p[1] - center["y"]] for p in points]
        if local[0] == local[-1]:
            local.pop()
        require(len(local) >= 3 and all(all(math.isfinite(v) for v in p) for p in local), "Bad exclusion polygon")
        records.append({"id": identity, "polygonSourceMm": local})

    add(scene["house"]["id"], scene["house"]["footprintMm"])
    add(scene["pool"]["id"], scene["pool"]["copingFootprintMm"])
    for key in ("timberTerrace", "driveway", "entry", "sideEntryApproach"):
        source = scene["surfaces"][key]
        require("SUPERSEDED" not in source.get("placementStatus", ""), "Active hardscape became superseded")
        add(source["id"], source["polygonMm"])
    for source in [*scene["terraces"], scene["poolDeck"]]:
        for index, rect in enumerate(source["rectsMm"]):
            add(source["id"] + "/" + str(index), polygon_from_rect(rect))
    for index, cutout in enumerate(scene["lawnCutouts"]):
        add("LAWN-CUTOUT/" + str(index), cutout)
    return records


def segment_distance_squared(point, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    length2 = dx * dx + dy * dy
    t = min(1.0, max(0.0, ((point[0] - a[0]) * dx + (point[1] - a[1]) * dy) / length2)) if length2 else 0
    return (point[0] - a[0] - t * dx) ** 2 + (point[1] - a[1] - t * dy) ** 2


def inside_polygon(point, polygon):
    x, y = point[:2]
    inside = False
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        if segment_distance_squared(point, a, b) <= 1e-12:
            return True
        if (a[1] > y) != (b[1] > y) and x < (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]) + a[0]:
            inside = not inside
    return inside


def intersects_buffered_polygon(point, polygon, radius_mm):
    return inside_polygon(point, polygon) or any(
        segment_distance_squared(point, a, b) <= radius_mm ** 2
        for a, b in zip(polygon, polygon[1:] + polygon[:1]))


def lawn_candidates(patch, faces, exclusions, seed=601226, density=24.0, clearance_mm=150.0):
    """Area-weighted on source triangles with hole/edge and hardscape clearance.

    The 150mm clearance is a conservative provisional envelope, NOT measured
    prototype extent. A future importer must revalidate complete transformed
    prototype geometry. Candidate positions cannot be passed straight to HISM.
    """
    require(math.isfinite(density) and 0 < density <= 100, "Density must be in (0,100] tufts/m²")
    require(math.isfinite(clearance_mm) and clearance_mm >= 0, "Invalid clearance")
    cumulative, total, edges = [], 0.0, {}
    for a, b, c in faces:
        require(max(a[2], b[2], c[2]) - min(a[2], b[2], c[2]) <= 0.05, "Slope requires an explicit surface-normal policy")
        area = abs((b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])) / 2
        require(area > 0, "Degenerate lawn triangle")
        total += area
        cumulative.append(total)
        for u, v in ((a, b), (b, c), (c, a)):
            key = tuple(sorted((u, v)))
            edges[key] = edges.get(key, 0) + 1
    require(all(n <= 2 for n in edges.values()), "Non-manifold/duplicated lawn faces")
    boundary = [edge for edge, count in edges.items() if count == 1]
    require(boundary, "Lawn has no outer boundary")
    sample_count = math.floor(total / 1_000_000 * density)
    require(sample_count <= 100000, "Candidate budget exceeded")
    rng = random.Random(int(hashlib.sha256(f"{seed}/{patch['sourceIdentity']}".encode()).hexdigest(), 16))
    instances, rejected = [], {"edgeOrHole": 0, "hardscape": 0}
    for candidate_index in range(sample_count):
        a, b, c = faces[bisect.bisect_right(cumulative, rng.random() * total)]
        root, v = math.sqrt(rng.random()), rng.random()
        weights = (1 - root, root * (1 - v), root * v)
        point = [sum(weights[j] * p[i] for j, p in enumerate((a, b, c))) for i in range(3)]
        yaw, scale = rng.uniform(-180, 180), rng.uniform(0.8, 1.15)
        if any(segment_distance_squared(point, a, b) < clearance_mm ** 2 for a, b in boundary):
            rejected["edgeOrHole"] += 1
            continue
        if any(intersects_buffered_polygon(point, e["polygonSourceMm"], clearance_mm) for e in exclusions):
            rejected["hardscape"] += 1
            continue
        # Root coordinates are centred OBJ Z-up mm; UE is cm with Y reflected.
        position = [round(v, 3) for v in point]
        instances.append({"id": patch["id"] + "/" + str(candidate_index), "positionSourceMm": position,
                          "positionUnrealCm": [position[0] / 10, -position[1] / 10, position[2] / 10],
                          "yawDegreesSource": round(yaw, 5), "yawDegreesUnreal": round(-yaw, 5),
                          "uniformScale": round(scale, 6),
                          "cell": [math.floor(point[0] / 4000), math.floor(point[1] / 4000)]})
    return {"patchId": patch["id"], "status": "candidate-roots-not-native-instances",
            "seed": seed, "densityTuftsPerM2": density, "provisionalClearanceMm": clearance_mm,
            "sourceTriangleAreaM2": total / 1_000_000, "sourceTriangles": len(faces),
            "boundarySegments": len(boundary), "sampledCandidates": sample_count,
            "rejected": rejected, "candidateCount": len(instances), "candidates": instances}


def build_plan(geometry, lock_path, asset_root, seed=601226, density=24.0):
    scene_path = geometry / "scene.json"
    scene = json.loads(scene_path.read_text())
    require(scene["units"] == "millimetres" and scene["coordinateSystem"] == "right-handed Z-up",
            "Unsupported canonical coordinate convention")
    assets = audit_assets(lock_path, asset_root)
    patches = register_patches(scene)
    required = {id_ for patch in patches for id_ in patch["sourceObjectIds"]}
    triangles = read_source_triangles(geometry / "dom-mm.obj", scene, required)
    exclusions = exclusion_polygons(scene)
    lawn = next(p for p in patches if p["kind"] == "lawn")
    roots = lawn_candidates(lawn, triangles[lawn["sourceObjectIds"][0]], exclusions, seed, density)
    return {"schemaVersion": 1, "status": "plan-only-native-vegetation-pending", "nativeApplied": False,
            "sourceManifestSha256": digest(scene_path), "sourceObjSha256": scene["objSha256"],
            "plannerSha256": digest(Path(__file__)), "assets": assets, "patches": patches,
            "historicalGrassPrototype": audit_legacy_grass(),
            "exclusions": exclusions, "lawnCandidates": roots,
            "treePlacement": {"count": 0, "status": "refused-no-registered-tree-patches",
                              "reason": "Asset availability does not authorize arbitrary new tree positions or historical off-parcel scenery."},
            "sourceMutation": {"deletedObjects": [], "hiddenObjects": [], "modifiedAssets": []},
            "proposedNativeSettings": {
                "component": "HierarchicalInstancedStaticMeshComponent", "spatialCellSizeMm": 4000,
                "collision": "NoCollision", "navigation": False, "grassNanite": False,
                "grassCullStartCm": 3500, "grassCullEndCm": 7000,
                "material": "UV0 / Masked / TwoSidedFoliage / explicit subsurface color",
                "transmissionStatus": "artistic-parameter-pending; no calibrated transmission texture",
                "performanceStatus": "unmeasured; tune density/overdraw in actual 4K packaged app"},
            "requiredBeforeNativeApply": [
                "Root-coordinated Blender prototype export from exact locked .blend objects with UV/alpha and bounds receipts.",
                "Full prototype geometry containment and exclusions, not only root/AABB tests; preserve canonical source identity.",
                "Native masked TwoSidedFoliage graph compile + UV/normal/alpha orientation checks, serialized HISM and packaged culling tests.",
                "Hedge species/height/footprint fit within the registered source geometry; retain current design-proposal provenance.",
                "Matching prototypes for tall roadside/ornamental grass and perennials before hiding any of those cards.",
                "Opt-in importer integration with rollback visibility and current input/native output hashes; actual 4K QA."]}


def apply_hedge_detail(scene_manifest, output_dir, geometry_dir=None):
    """Editor-only, explicitly invoked native detail pass; no engine is launched.

    Hook after canonical bounds/materials and before the parent's map save. Merge
    returned pipelineFiles and assetHashes into the parent's final receipt. The
    standalone converter must have already validated all 153 clipped crowns.
    On success only the four exact source proxy components become invisible;
    their actors, meshes, collision and canonical geometry remain intact.
    """
    import unreal
    from materials import _asset_hashes

    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    geometry_dir = Path(geometry_dir or os.environ.get("BREZI_GEOMETRY", output_dir / "geometry"))
    prototype_dir = output_dir / "vegetation-prototypes"
    report_path = output_dir / "vegetation-report.json"
    prefix = "/Game/Brezi/VegetationGenerated"
    owner = "scripts/unreal/vegetation.py"
    tag = "BreziVegetationDetail"
    actor_system = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    level_system = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
    assets = unreal.EditorAssetLibrary
    unreal.AssetRegistryHelpers.get_asset_registry().scan_paths_synchronous(
        ["/Game/Brezi", "/Interchange/Pipelines"], force_rescan=True)
    lib = unreal.MaterialEditingLibrary
    tools = unreal.AssetToolsHelpers.get_asset_tools()
    report = {"schemaVersion": 1, "status": "pending", "nativeApplied": False,
              "role": "illustrative clipped hedge crown detail", "pipelineFiles": {}, "assetHashes": {}}
    created, visibility_before = [], []

    def write_report():
        temporary = report_path.with_suffix(".tmp")
        temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
        temporary.replace(report_path)

    def tag_asset(asset):
        require(asset.get_path_name().startswith(prefix + "/"), "Generated asset escaped vegetation namespace")
        assets.set_metadata_tag(asset, "BreziGeneratedBy", owner)

    def owned_asset(path):
        asset = assets.load_asset(path) if assets.does_asset_exist(path) else None
        if asset:
            require(assets.get_metadata_tag(asset, "BreziGeneratedBy") == owner,
                    "Refusing to mutate unowned vegetation asset: " + path)
        return asset

    def save(asset):
        require(assets.save_loaded_asset(asset, only_if_is_dirty=False), "Vegetation asset save failed")

    def enum_value(enum, token):
        names = [name for name in dir(enum) if token in name.replace("_", "")]
        require(len(names) == 1, "Ambiguous Unreal enum: " + token)
        return getattr(enum, names[0])

    def node(material, kind, **settings):
        expression = lib.create_material_expression(material, kind, -600, 0)
        require(expression is not None, "Material expression creation failed")
        for key, value in settings.items():
            expression.set_editor_property(key, value)
        return expression

    def prop(expression, output, material_property):
        require(lib.connect_material_property(expression, output, material_property), "Foliage material pin connection failed")

    def connect(a, output, b, pin):
        require(lib.connect_material_expressions(a, output, b, pin), "Foliage material expression connection failed")

    write_report()
    try:
        prototype_report = json.loads((prototype_dir / "prototypes.json").read_text())
        detail = json.loads((prototype_dir / "hedge-detail.json").read_text())
        require(prototype_report["status"] == "prototype-conversion-validated"
                and detail["status"] == "clipped-hedge-geometry-validated", "Plant conversion is not validated")
        issues = detail["khronosValidation"]
        require(issues["numErrors"] == 0 and issues["numWarnings"] == 0 and not issues["truncated"],
                "Clipped hedge did not pass full Khronos validation")
        require(detail["sourceManifestSha256"] == digest(geometry_dir / "scene.json")
                and detail["sourceObjSha256"] == scene_manifest["objSha256"], "Hedge source manifest changed")
        require(detail["converterSha256"] == digest(Path(__file__).with_name("vegetation-convert.py")), "Hedge converter changed")
        require(detail["sourceCrowns"] == 153 and len(detail["crowns"]) == 153
                and detail["maximumTopCoverageGapMm"] <= 25
                and detail["maximumSourceVolumeViolationMm"] <= 0.02, "Hedge coverage/volume gate failed")
        require(detail["lawnInstances"] == 0 and detail["treePlacements"] == 0, "Unregistered plant placement")
        require(digest(prototype_dir / detail["file"]) == detail["sha256"], "Clipped hedge GLB changed")
        current_audit = audit_assets(ROOT / "scripts/archviz/assets.lock.json", ROOT / "output/archviz/assets")
        require(current_audit == prototype_report["assetAudit"], "Plant source asset lock changed")
        patch = next(p for p in register_patches(scene_manifest) if p["kind"] == "hedge")
        require(patch["sourceObjectIds"] == detail["sourcePatch"]["sourceObjectIds"], "Hedge source mapping changed")
        originals = {}
        previous_layers = []
        for actor in actor_system.get_all_level_actors():
            if actor.actor_has_tag(tag):
                previous_layers.append(actor)
            matches = [id_ for id_ in patch["sourceObjectIds"] if actor.actor_has_tag(id_)]
            if matches:
                require(len(matches) == 1 and matches[0] not in originals, "Source hedge actor is missing/merged/duplicated")
                component = actor.get_component_by_class(unreal.StaticMeshComponent)
                require(component is not None, "Source hedge component missing")
                originals[matches[0]] = (actor, component)
        require(set(originals) == set(patch["sourceObjectIds"]), "Exact four source hedge actors were not found")
        actor_class = unreal.load_class(None, "/Script/BreziTwin.BreziVegetationPatch")
        require(actor_class is not None, "Native vegetation actor requires editor rebuild")

        # Explicit own textures; GLB material/texture import is disabled below.
        texture_assets = {}
        for role, entry in prototype_report["models"]["shrub_02"]["textures"].items():
            path = prototype_dir / entry["path"]
            require(digest(path) == entry["sha256"], "Converted plant texture changed")
            name = "T_Shrub_" + role
            texture = owned_asset(prefix + "/Textures/" + name)
            if texture is None:
                task = unreal.AssetImportTask()
                for key, value in {"filename": str(path), "destination_path": prefix + "/Textures",
                                   "destination_name": name, "automated": True, "save": False,
                                   "replace_existing": False, "factory": unreal.TextureFactory()}.items():
                    task.set_editor_property(key, value)
                tools.import_asset_tasks([task])
                objects = task.get_objects()
                require(len(objects) == 1 and isinstance(objects[0], unreal.Texture2D), "Expected one foliage texture")
                texture = objects[0]
                tag_asset(texture)
            elif assets.get_metadata_tag(texture, "source_sha256") not in ("", entry["sha256"]):
                raise ValueError("Existing generated plant texture has different source bytes")
            texture.set_editor_property("srgb", role == "albedo")
            texture.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP if role == "normal"
                                        else unreal.TextureCompressionSettings.TC_DEFAULT if role == "albedo" else unreal.TextureCompressionSettings.TC_MASKS)
            if role == "normal":
                texture.set_editor_property("flip_green_channel", True)
            assets.set_metadata_tag(texture, "source_sha256", entry["sha256"])
            save(texture)
            texture_assets[role] = texture

        material_path = prefix + "/Materials/M_ShrubLeafBranch"
        material = owned_asset(material_path)
        if material is None:
            material = tools.create_asset("M_ShrubLeafBranch", prefix + "/Materials", unreal.Material, unreal.MaterialFactoryNew())
            require(material is not None, "Native foliage material creation failed")
            tag_asset(material)
        # Delete from a snapshot: UE 5.8's bulk helper mutates the collection
        # it is iterating and can leave disconnected expressions behind.
        for expression in list(lib.get_material_expressions(material)):
            lib.delete_material_expression(material, expression)
        require(not list(lib.get_material_expressions(material)), "Foliage graph did not clear completely")
        material.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
        material.set_editor_property("two_sided", True)
        material.set_editor_property("opacity_mask_clip_value", 0.45)
        material.set_editor_property("shading_model", enum_value(unreal.MaterialShadingModel, "TWOSIDEDFOLIAGE"))
        material.set_editor_property("tangent_space_normal", True)
        instanced_usage = enum_value(unreal.MaterialUsage, "INSTANCEDSTATICMESHES")
        lib.set_base_material_usage(material, instanced_usage, True)
        require(lib.has_material_usage(material, instanced_usage), "Foliage instancing material usage missing")
        samples = {}
        for role, texture in texture_assets.items():
            sampler = unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL if role == "normal" else unreal.MaterialSamplerType.SAMPLERTYPE_COLOR if role == "albedo" else unreal.MaterialSamplerType.SAMPLERTYPE_MASKS
            samples[role] = node(material, unreal.MaterialExpressionTextureSample, texture=texture, sampler_type=sampler)
        prop(samples["albedo"], "RGB", unreal.MaterialProperty.MP_BASE_COLOR)
        prop(samples["normal"], "RGB", unreal.MaterialProperty.MP_NORMAL)
        prop(samples["alpha"], "R", unreal.MaterialProperty.MP_OPACITY_MASK)
        prop(samples["roughness"], "R", unreal.MaterialProperty.MP_ROUGHNESS)
        transmission = node(material, unreal.MaterialExpressionMultiply, const_b=0.35)
        connect(samples["albedo"], "RGB", transmission, "A")
        prop(transmission, "", unreal.MaterialProperty.MP_SUBSURFACE_COLOR)
        prop(node(material, unreal.MaterialExpressionConstant, r=0.5), "", unreal.MaterialProperty.MP_OPACITY)
        errors = list(lib.recompile_material(material))
        require(not errors, "Foliage graph compilation failed: " + "; ".join(str(e) for e in errors))
        save(material)

        # Synchronous Interchange asset-only import. Each spatial batch stays separate.
        pipeline_path = prefix + "/Pipeline/HedgeAssets"
        pipeline = owned_asset(pipeline_path)
        if pipeline is None:
            pipeline = assets.duplicate_asset("/Interchange/Pipelines/DefaultGLTFSceneAssetsPipeline.DefaultGLTFSceneAssetsPipeline", pipeline_path)
            require(pipeline is not None, "Interchange foliage pipeline missing")
            tag_asset(pipeline)
        pipeline.set_editor_property("use_source_name_for_asset", False)
        mesh_pipeline = pipeline.get_editor_property("mesh_pipeline")
        for key, value in {"combine_static_meshes_behavior": unreal.InterchangeCombineStaticMeshesBehavior.DO_NOT_COMBINE,
                           "collision": False, "build_nanite": False, "generate_lightmap_u_vs": False}.items():
            mesh_pipeline.set_editor_property(key, value)
        common = pipeline.get_editor_property("common_meshes_properties")
        for key, value in {"remove_degenerates": False, "recompute_normals": False, "recompute_tangents": False,
                           "use_high_precision_tangent_basis": True, "use_full_precision_u_vs": True}.items():
            common.set_editor_property(key, value)
        pipeline.get_editor_property("material_pipeline").set_editor_property("import_materials", False)
        pipeline.get_editor_property("material_pipeline").get_editor_property("texture_pipeline").set_editor_property("import_textures", False)
        save(pipeline)
        mesh_directory = prefix + "/Meshes"
        registry = unreal.AssetRegistryHelpers.get_asset_registry()
        registry.scan_paths_synchronous([prefix], force_rescan=True)
        for existing in assets.list_assets(mesh_directory, recursive=True, include_folder=False):
            owned_asset(existing)
        manager = unreal.InterchangeManager.get_interchange_manager_scripted()
        parameters = unreal.ImportAssetParameters()
        for key, value in {"is_automated": True, "replace_existing": True, "force_show_dialog": False,
                           "override_pipelines": [unreal.SoftObjectPath(pipeline.get_path_name())]}.items():
            parameters.set_editor_property(key, value)
        require(manager.import_asset(mesh_directory, manager.create_source_data(str(prototype_dir / detail["file"])), parameters),
                "Native foliage asset import failed")
        registry.scan_paths_synchronous([mesh_directory], force_rescan=True)
        meshes = {}
        for asset_path in assets.list_assets(mesh_directory, recursive=True, include_folder=False):
            mesh = assets.load_asset(asset_path)
            if isinstance(mesh, unreal.StaticMesh):
                matches = [b["id"] for b in detail["spatialBatches"] if b["id"] in mesh.get_name()]
                require(len(matches) == 1 and matches[0] not in meshes, "Unexpected/merged native hedge mesh")
                tag_asset(mesh)
                meshes[matches[0]] = mesh
        require(set(meshes) == {b["id"] for b in detail["spatialBatches"]}, "Native hedge batch identity mismatch")
        batches = []
        for batch in detail["spatialBatches"]:
            mesh = meshes[batch["id"]]
            mesh.set_material(0, material)
            require(mesh.get_material(0) == material, "Hedge mesh has no native foliage material bound")
            require(mesh.get_num_tex_coords(0) >= 1, "Native hedge UV0 missing")
            triangles_before = mesh.get_num_triangles(0)
            lod_counts = list(unreal.BreziVegetationPatch.configure_detail_lods(mesh))
            unreal.log("BREZI_HEDGE_LOD " + json.dumps({"id": batch["id"], "sourceTriangles": batch["triangles"],
                "nativeBeforeLods": triangles_before, "nativeAfterLods": lod_counts,
                "removeDegenerates": pipeline.get_editor_property("common_meshes_properties").get_editor_property("remove_degenerates")}))
            require(len(lod_counts) == 3 and 0 < lod_counts[2] < lod_counts[1] < lod_counts[0], "Real foliage LOD reduction failed")
            require(lod_counts[0] == batch["triangles"], "Native foliage LOD0 topology changed: " + json.dumps({"batch": batch["id"], "source": batch["triangles"], "before": triangles_before, "after": lod_counts}))
            require(not mesh.get_editor_property("nanite_settings").get_editor_property("enabled"), "Foliage Nanite must remain disabled")
            save(mesh)
            actor = actor_system.spawn_actor_from_class(actor_class, unreal.Vector(0, 0, 0), unreal.Rotator())
            require(actor is not None, "Foliage actor spawn failed")
            created.append(actor)
            actor.set_actor_label("Živý plot · skenované listy · " + batch["id"])
            actor.set_editor_property("tags", [unreal.Name("BreziGenerated"), unreal.Name(tag), unreal.Name(batch["id"]), unreal.Name(patch["id"])])
            component = actor.get_component_by_class(unreal.HierarchicalInstancedStaticMeshComponent)
            require(component is not None, "Serializable native HISM missing")
            component.set_visibility(False)
            component.set_static_mesh(mesh)
            component.set_collision_profile_name("NoCollision")
            component.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)
            component.set_cull_distances(0, 0)  # keep the privacy boundary at every architectural viewpoint
            indices = component.add_instances([unreal.Transform()], True, False, False)
            require(len(indices) == 1 and component.get_instance_count() == 1, "HISM batch serialization input mismatch")
            actor.synchronize_instance_bounds()
            origin, extent, _ = unreal.SystemLibrary.get_component_bounds(component)
            actual = {"min": [getattr(origin, k)-getattr(extent, k) for k in ("x", "y", "z")],
                      "max": [getattr(origin, k)+getattr(extent, k) for k in ("x", "y", "z")]}
            lo, hi = batch["boundsSourceMm"]["min"], batch["boundsSourceMm"]["max"]
            expected = {"min": [lo[0]/10, -hi[1]/10, lo[2]/10], "max": [hi[0]/10, -lo[1]/10, hi[2]/10]}
            error = max(abs(actual[key][i]-expected[key][i]) for key in ("min", "max") for i in range(3))
            require(error <= 0.05, "Native foliage bounds changed beyond 0.5mm")
            assets.set_metadata_tag(actor, "BreziSourceCrowns", json.dumps(batch["crowns"]))
            batches.append({"id": batch["id"], "actor": actor.get_path_name(), "mesh": mesh.get_path_name(),
                            "sourceCrowns": batch["crowns"], "instances": 1, "lodTriangles": lod_counts,
                            "nativeBoundsCm": actual, "maxBoundsErrorCm": error})
        # Commit visual replacement only after all native assets, LODs and bounds pass.
        for id_, (actor, component) in originals.items():
            prior = bool(component.get_editor_property("visible"))
            visibility_before.append((component, prior))
            if assets.get_metadata_tag(actor, "BreziVegetationOriginalVisibility") == "":
                assets.set_metadata_tag(actor, "BreziVegetationOriginalVisibility", json.dumps(prior))
            assets.set_metadata_tag(actor, "BreziVegetationReplacementPatch", patch["id"])
            component.set_visibility(False)
            require(not component.get_editor_property("visible"), "Original hedge visibility did not change")
        for actor in created:
            actor.get_component_by_class(unreal.HierarchicalInstancedStaticMeshComponent).set_visibility(True)
        for actor in previous_layers:
            require(actor_system.destroy_actor(actor), "Old owned foliage layer could not be replaced")
        require(level_system.save_current_level(), "Native foliage map save failed")
        own_assets = assets.list_assets(prefix, recursive=True, include_folder=False)
        for path in own_assets:
            asset = assets.load_asset(path)
            if asset:
                save(asset)
        pipeline_files = [Path(__file__), Path(__file__).with_name("vegetation-convert.py"),
                          ROOT / "scripts/archviz/assets.lock.json", prototype_dir / "prototypes.json",
                          prototype_dir / "hedge-detail.json", prototype_dir / detail["file"],
                          ROOT / "unreal/BreziTwin/Source/BreziTwin/BreziVegetationPatch.h",
                          ROOT / "unreal/BreziTwin/Source/BreziTwin/BreziVegetationPatch.cpp"]
        pipeline_files += [ROOT / "output/archviz/assets" / entry["path"] for model in current_audit["models"] for entry in model["verifiedFiles"]]
        pipeline_files += [prototype_dir / entry["path"] for entry in prototype_report["models"]["shrub_02"]["textures"].values()]
        report.update(status="hedge-native-validated", nativeApplied=True, sourceObjectIds=patch["sourceObjectIds"],
                      originalProxyObjectsHidden=4, originalObjectsDeleted=0, sourceCrowns=153,
                      batches=batches, hismComponents=len(batches), hismInstances=len(batches), lawnInstances=0, treePlacements=0,
                      maximumTopCoverageGapMm=detail["maximumTopCoverageGapMm"],
                      maximumSourceVolumeViolationMm=detail["maximumSourceVolumeViolationMm"],
                      removedUnrealDegenerateTriangles=detail["removedUnrealDegenerateTriangles"],
                      buildSettings={"nanite": False, "removeDegenerates": False, "recomputeNormals": False,
                                     "recomputeTangents": False, "fullPrecisionUV": True, "highPrecisionTangents": True},
                      material={"asset": material.get_path_name(), "shadingModel": "TwoSidedFoliage", "alphaCutoff": 0.45,
                                "subsurfaceAlbedoFactor": 0.35, "opacity": 0.5, "transmissionCalibration": "artistic; no measured leaf transmission map"},
                      assetHashes=_asset_hashes(own_assets),
                      pipelineFiles={os.path.relpath(path, ROOT): digest(path) for path in pipeline_files},
                      savedMap=True, packagedVerification=False, renderedVerification=False,
                      limitations=detail["limitations"] + ["Native LODs are reduced geometry; masked-leaf appearance and overdraw require packaged 4K QA."])
        write_report()
        unreal.log("BREZI_VEGETATION " + json.dumps({k: report[k] for k in ("status", "sourceCrowns", "hismComponents", "originalProxyObjectsHidden")}))
        return report
    except Exception as error:
        for component, previous in visibility_before:
            component.set_visibility(previous)
        for actor in created:
            actor_system.destroy_actor(actor)
        report.update(status="failed", nativeApplied=False, error=str(error))
        write_report()
        raise


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--geometry", type=Path, default=ROOT / "output/unreal/geometry")
    parser.add_argument("--lock", type=Path, default=ROOT / "scripts/archviz/assets.lock.json")
    parser.add_argument("--assets", type=Path, default=ROOT / "output/archviz/assets")
    parser.add_argument("--output", type=Path, default=ROOT / "output/unreal/vegetation-plan.json")
    parser.add_argument("--seed", type=int, default=601226)
    parser.add_argument("--density", type=float, default=24.0)
    args = parser.parse_args()
    try:
        report = build_plan(args.geometry, args.lock, args.assets, args.seed, args.density)
        exit_code = 0
    except (ValueError, KeyError, OSError, TypeError) as error:
        # Replace any stale proposal with explicit failure, never leave success-looking output.
        report = {"schemaVersion": 1, "status": "failed", "nativeApplied": False, "error": str(error)}
        exit_code = 1
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(args.output.suffix + ".tmp")
    temporary.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    temporary.replace(args.output)
    print(json.dumps({"status": report["status"], "nativeApplied": False,
                      "verifiedFiles": report.get("assets", {}).get("verifiedFileCount", 0),
                      "patches": len(report.get("patches", [])),
                      "lawnCandidateCount": report.get("lawnCandidates", {}).get("candidateCount", 0),
                      **({"error": report["error"]} if "error" in report else {})}, ensure_ascii=False))
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
