"""Independent R6 whole-crown, continuity and unchanged-source verification."""
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import unittest

import numpy as np
import shapely
from shapely.geometry import Polygon, Point, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = ROOT / 'output/unreal/exterior-context-20260926-r6'


def sha(path):
    # This suite verifies historical R6. Its generator was archived before the
    # R7 metadata correction; the separate revision suite checks the live owner.
    if Path(path).resolve() == ROOT / 'scripts/unreal/exterior-meadow-blades.py':
        path = DIRECTORY / 'inputs/exterior-meadow-blades-r6.py'
    if Path(path).resolve() == ROOT / 'output/unreal/exterior-tools-py312-20260926/lib/python3.12/site-packages/numpy/__init__.py':
        # Official PyPI wheel member matches the exact original R6 hash. The
        # shared live runtime moved to NumPy2.4.6 before R7 and stays untouched.
        path = DIRECTORY / 'inputs/runtime-snapshot/numpy-2.5.3/numpy/__init__.py'
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


class NativeBladeMeadow(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads((DIRECTORY / 'context-plan.json').read_text())
        cls.base = json.loads((ROOT / 'output/unreal/exterior-context-20260926-r5/context-plan.json').read_text())
        cls.rows = cls.plan['meadowBladePlacements']
        cls.xyz = np.array([row['positionCm'] for row in cls.rows])
        cls.points = shapely.points(cls.xyz[:, 0], cls.xyz[:, 1])
        cls.selected = {r['meshId']: r for r in cls.plan['surfaces'] if r['material'] == 'context_meadow'}
        cls.triangles, cls.coords, cls.mesh_ids = [], [], []
        for mesh in cls.plan['meshes']:
            if mesh['id'] not in cls.selected:
                continue
            for i in range(0, len(mesh['indices']), 3):
                vertices = [mesh['verticesCm'][j] for j in mesh['indices'][i:i + 3]]
                triangle = Polygon([p[:2] for p in vertices])
                if triangle.area < .00001:
                    continue
                cls.triangles.append(triangle)
                cls.coords.append(vertices)
                cls.mesh_ids.append(mesh['id'])
        cls.coords = np.array(cls.coords)
        cls.raw_union = unary_union(shapely.set_precision(cls.triangles, .0001))
        # Global single-pass union can leave a <2-micrometre sliver between
        # adjacent triangulated shoulders. Close this only in the independent
        # analysis; actual mesh vertices, positions and input plan remain exact.
        cls.union = cls.raw_union.buffer(.0002, join_style='mitre').buffer(-.0002, join_style='mitre')
        cls.protected = unary_union([Polygon(tri) for tri in cls.plan['protectedTrianglesCm']])

    def test_only_rejected_meadow_array_and_derivation_metadata_replaced(self):
        changed = {'generatorSha256', 'derivedFrom', 'meadowBasePlacements', 'meadowBasePolicy'}
        for key, value in self.base.items():
            if key in changed:
                continue
            self.assertEqual(self.plan[key], value, key)
            encoded = (json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + '\n').encode()
            self.assertEqual(self.plan['derivedFrom']['preservedFieldHashes'][key], hashlib.sha256(encoded).hexdigest())
        self.assertNotIn('meadowBasePlacements', self.plan)
        self.assertNotIn('meadowBasePolicy', self.plan)
        self.assertEqual(self.plan['generatorSha256'], sha(ROOT / 'scripts/unreal/exterior-meadow-blades.py'))
        self.assertEqual(self.plan['derivedFrom']['sha256'], sha(self.plan['derivedFrom']['path']))
        receipt = json.loads((DIRECTORY / 'build-environment.json').read_text())
        for path, expected in receipt['inputFiles'].items():
            self.assertEqual(sha(path), expected, path)

    def test_every_full_crown_fits_meadow_and_clears_protected_source(self):
        self.assertLess(self.raw_union.symmetric_difference(self.union).area, 1)
        self.assertTrue(np.all(shapely.covers(self.union, self.points)))
        self.assertGreaterEqual(float(shapely.distance(self.points, self.union.boundary).min()), 14)
        self.assertGreaterEqual(float(shapely.distance(self.points, self.protected).min()), 16)
        self.assertLessEqual(float(np.hypot(self.xyz[:, 0], self.xyz[:, 1]).max()) + 14, 9000)
        self.assertTrue(np.all(np.isfinite(self.xyz)))

    def test_every_root_matches_actual_unchanged_meadow_triangle_plane(self):
        # Independently derive plane normals, not the generator's barycentric
        # formula, and verify all 382k roots, source ids and rounded output Z.
        pairs = STRtree(self.triangles).query(self.points, predicate='within')
        indices, first = np.unique(pairs[0], return_index=True)
        self.assertEqual(len(indices), len(self.points))
        tri_indices = pairs[1, first]
        vertices = self.coords[tri_indices]
        normals = np.cross(vertices[:, 1] - vertices[:, 0], vertices[:, 2] - vertices[:, 0])
        error_z = np.sum(normals * (self.xyz - vertices[:, 0]), axis=1) / normals[:, 2]
        self.assertLess(float(np.abs(error_z).max()), .0000051)
        self.assertTrue(all(row['sourceMeshId'] == self.mesh_ids[index] for row, index in zip(self.rows, tri_indices)))

    def test_density_scale_budget_and_all_road_shoulders(self):
        self.assertTrue(350000 <= len(self.rows) <= 400000)
        area = self.union.intersection(Point(0, 0).buffer(9000, quad_segs=256)).area / 10000
        self.assertGreaterEqual(len(self.rows) / area, 30)
        self.assertGreater(sum(r['sourceFinish'] == 'shoulder' for r in self.rows), 35000)
        self.assertTrue(all(r['role'] == 'grass' and r['radiusCm'] == 14 and 14 <= r['heightCm'] <= 25
                            and 0 <= r['yawDeg'] <= 360 for r in self.rows))
        self.assertEqual(self.plan['meadowBladePolicy']['cullEndCm'], 9000)
        count = Counter(r['sourceMeshId'] for r in self.rows)
        for identity in self.selected:
            # Only surfaces with area within the radius are relevant.
            if identity in count:
                self.assertGreater(count[identity], 0)
        self.assertEqual(len(count), 25)

    def test_continuous_nonempty_five_metre_coverage_and_jitter(self):
        allowed = self.union.buffer(-14.02).difference(self.protected.buffer(16.02))
        allowed = allowed.intersection(Point(0, 0).buffer(8986, quad_segs=256))
        counts = Counter(zip(np.floor(self.xyz[:, 0] / 500).astype(int), np.floor(self.xyz[:, 1] / 500).astype(int)))
        audited = 0
        for i in range(-18, 18):
            for j in range(-18, 18):
                area = allowed.intersection(box(i * 500, j * 500, (i + 1) * 500, (j + 1) * 500)).area / 10000
                if area >= 10:
                    audited += 1
                    self.assertGreater(counts[(i, j)] / area, 28, (i, j, area))
        self.assertGreater(audited, 350)
        # Inverse rotation still leaves broad sub-cell residuals; blade centres
        # are not a visually regimented exact row/column lattice.
        yaw = math.radians(31.7)
        u = self.xyz[:, 0] * math.cos(yaw) + self.xyz[:, 1] * math.sin(yaw)
        residual = np.remainder(u + 12800 + 8.5, 17) - 8.5
        self.assertGreater(float(np.std(residual)), 3)
        self.assertGreater(len({r['yawDeg'] for r in self.rows}), 150000)


if __name__ == '__main__':
    unittest.main()
