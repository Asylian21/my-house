"""CPU geometry regressions for the real placement module; no native mocks.

Only source_context/checked_prototypes are replaced for small analytic fixtures.
The production sampler, footprint, disk, transform and bounds code runs unchanged.
"""
import importlib.util
import math
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = next(p for p in Path(__file__).resolve().parents if (p/'lib/twin-site.ts').is_file())
spec = importlib.util.spec_from_file_location('lawn_placement_under_test', ROOT/'scripts/unreal/lawn-detail/placement.py')
p = importlib.util.module_from_spec(spec)
spec.loader.exec_module(p)
v = p.vegetation()


def rectangle(x0, y0, x1, y1, z=0):
    a, b, c, d = (x0,y0,z), (x1,y0,z), (x1,y1,z), (x0,y1,z)
    return [(a,b,c), (a,c,d)]


def prototype(points=((0,0,0), (.04,0,.04), (0,.03,0))):
    return {'verticesSourceZUpMetres': list(points), 'boundsSourceZUpMetres': {
        'min': [min(a[i] for a in points) for i in range(3)],
        'max': [max(a[i] for a in points) for i in range(3)]}}


def plan_for(faces, exclusions=(), seed=601226):
    prototypes = {id_: dict(prototype(), id=id_) for id_ in p.IDS}
    context = (v, {'sourceIdentity':'analytic-test-domain'}, faces, list(exclusions))
    with patch.object(p, 'source_context', return_value=context), patch.object(p, 'checked_prototypes', return_value=({},prototypes,{})):
        return p.build_plan({}, Path('/unused'), seed=seed, density=10)


def instances(plan):
    return [row for group in plan['groups'] for row in group['instances']]


class Footprints(unittest.TestCase):
    def test_concave_l_keeps_notch_open_instead_of_aabb(self):
        faces = rectangle(0,0,4,1) + rectangle(0,1,1,4)
        polys = p.footprint_polygons(faces)
        self.assertEqual(sum(abs(p.signed_area(*x))/2 for x in polys), 7)
        self.assertFalse(any(v.inside_polygon((3,3), x) for x in polys))
        self.assertTrue(any(v.inside_polygon((3,.5), x) for x in polys))
        self.assertTrue(any(v.inside_polygon((.5,3), x) for x in polys))

    def test_box_top_bottom_deduplicate_and_vertical_faces_drop(self):
        low = rectangle(0,0,4,3)
        high = [tuple((x,y,50) for x,y,z in reversed(t)) for t in low]
        side = [((0,0,0),(4,0,0),(4,0,50))]
        self.assertEqual(len(p.footprint_polygons(low+high+side)), 2)

    def test_only_zero_area_projections_refused(self):
        with self.assertRaisesRegex(ValueError, 'no projected footprint'):
            p.footprint_polygons([((0,0,0),(0,0,1),(0,0,2))])

    def test_buffer_tangent_contact_refused(self):
        polygon = [(0,0),(10,0),(10,10),(0,10)]
        self.assertTrue(v.intersects_buffered_polygon((11,5), polygon, 1))
        self.assertFalse(v.intersects_buffered_polygon((11.001,5), polygon, 1))


class Boundaries(unittest.TestCase):
    def test_shared_internal_diagonal_is_not_boundary(self):
        edges, cumulative, area = p.boundary_and_areas(rectangle(0,0,4,3))
        self.assertEqual(len(edges), 4)
        self.assertEqual(cumulative, [6,12])
        self.assertEqual(area, 12)

    def test_hole_has_its_own_four_edges(self):
        faces=[]; grid=(0,3000,5000,8000)
        for x in range(3):
            for y in range(3):
                if (x,y)!=(1,1): faces += rectangle(grid[x],grid[y],grid[x+1],grid[y+1])
        edges, _, area = p.boundary_and_areas(faces)
        inner = [e for e in edges if all(3000<=a[0]<=5000 and 3000<=a[1]<=5000 for a in e)]
        self.assertEqual(len(inner), 4)
        self.assertEqual(len(edges), 16)
        self.assertEqual(area, 60_000_000)
        result=plan_for(faces)
        for row in instances(result):
            x,y,z=row['positionUnrealCm']; yaw=-row['yawDegreesUnreal']
            actual=p.transform_vertices(prototype(), (x*10,-y*10,z*10), yaw, row['uniformScale'])
            for a,b,_ in actual:
                self.assertTrue(0<a<8000 and 0<b<8000)
                self.assertFalse(3000<=a<=5000 and 3000<=b<=5000)
        self.assertGreater(result['rejected']['edgeOrHole'], 0)

    def test_nonmanifold_edge_refused(self):
        a,b=(0,0,0),(2,0,0)
        with self.assertRaisesRegex(ValueError, 'Nonmanifold'):
            p.boundary_and_areas([(a,b,(0,2,0)),(b,a,(0,-2,0)),(a,b,(1,3,0))])

    def test_duplicate_face_refused(self):
        faces=rectangle(0,0,4,3)
        with self.assertRaisesRegex(ValueError, 'Nonmanifold'):
            p.boundary_and_areas(faces+[faces[0]])

    def test_degenerate_and_sloped_source_refused(self):
        for face, message in [(((0,0,0),(1,1,0),(2,2,0)), 'Degenerate'),
                              (((0,0,0),(1,0,0),(0,1,.051)), 'slope')]:
            with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                p.boundary_and_areas([face])

    def test_no_boundary_refused(self):
        with self.assertRaisesRegex(ValueError, 'Missing lawn boundary'):
            p.boundary_and_areas([])


class TransformAndSampler(unittest.TestCase):
    def assertPoint(self, actual, expected):
        for a,e in zip(actual,expected):self.assertAlmostEqual(a,e,places=9)

    def test_source_yaw_positive_and_negative_90(self):
        proto=prototype([(1,0,1)])
        self.assertPoint(p.transform_vertices(proto,(100,200,-65),90,.5)[0], (100,700,435))
        self.assertPoint(p.transform_vertices(proto,(100,200,-65),-90,.5)[0], (100,-300,435))

    def test_unreal_reflection_swaps_y_extrema(self):
        bounds=p.unreal_bounds([[10,-40,-65],[30,20,35]])
        self.assertEqual(bounds, {'min':[1,-2,-6.5], 'max':[3,4,3.5]})

    def test_native_negative_yaw_matches_reflected_source(self):
        # Rotate original point in source, then reflect Y. Independently rotate
        # the reflected point by opposite yaw in native units.
        x,y,z=.02,.03,.04; yaw=37; scale=1.1
        actual=p.transform_vertices(prototype([(x,y,z)]),(100,200,-65),yaw,scale)[0]
        c,s=math.cos(math.radians(-yaw)),math.sin(math.radians(-yaw))
        expected=(10+scale*(c*x*100-s*(-y)*100), -20+scale*(s*x*100+c*(-y)*100), -6.5+z*scale*100)
        self.assertPoint((actual[0]/10,-actual[1]/10,actual[2]/10),expected)

    def test_rotation_of_mesh_box_is_conservative(self):
        proto=prototype(); verts=p.transform_vertices(proto,(0,0,0),37,1.15)
        box=p.transform_vertices({'verticesSourceZUpMetres':p.mesh_aabb_vertices(proto)},(0,0,0),37,1.15)
        bounds=p.unreal_bounds(box)
        for a in verts:
            for i,v_ in enumerate((a[0]/10,-a[1]/10,a[2]/10)):
                self.assertLessEqual(bounds['min'][i],v_+1e-12); self.assertLessEqual(v_,bounds['max'][i]+1e-12)

    def test_real_sampler_preserves_concave_exclusion_notch(self):
        # This L excludes both arms, but its open upper-right region remains
        # plantable. An AABB replacement would incorrectly delete that region.
        polygons=p.footprint_polygons(rectangle(1000,1000,7000,2000)+rectangle(1000,2000,2000,7000))
        exclusions=[{'id':'L/'+str(i),'polygonSourceMm':poly} for i,poly in enumerate(polygons)]
        result=plan_for(rectangle(0,0,8000,8000),exclusions)
        notch=0
        for row in instances(result):
            x,y,_=row['positionUnrealCm'];x,y=x*10,-y*10
            self.assertFalse(1000<=x<=7000 and 1000<=y<=2000)
            self.assertFalse(1000<=x<=2000 and 2000<=y<=7000)
            if 3000<x<6000 and 3000<y<6000:notch+=1
        self.assertGreater(notch,20)
        self.assertGreater(result['rejected']['hardscape'],0)

    def test_repeatable_seed_and_unique_ids(self):
        a=plan_for(rectangle(0,0,8000,8000));b=plan_for(rectangle(0,0,8000,8000))
        self.assertEqual(a,b)
        ids=[r['id'] for r in instances(a)]
        self.assertEqual(len(ids),len(set(ids)))
        self.assertNotEqual(a['groups'],plan_for(rectangle(0,0,8000,8000),seed=601227)['groups'])

    def test_density_budget_fails_before_sources_are_read(self):
        for density in (0,-1,101,float('nan'),float('inf')):
            with self.subTest(density=density), patch.object(p,'source_context') as source, self.assertRaisesRegex(ValueError,'Density'):
                p.build_plan({},Path('/unused'),density=density)
            source.assert_not_called()


if __name__=='__main__':unittest.main()
