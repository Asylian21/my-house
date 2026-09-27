"""Current C/B/B stove placement, occlusion and containment checks; no UE."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import tempfile
import unittest

SPEC = importlib.util.spec_from_file_location('stove_study', Path(__file__).with_name('realism-stove-geometry.py'))
M = importlib.util.module_from_spec(SPEC); SPEC.loader.exec_module(M)


class StoveStudyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.directory = M.ROOT/'output/unreal/realism-20260926-r4/geometry'
        cls.scene,cls.records,cls.local,cls.center = M.source(cls.directory)
        cls.meshes,cls.transforms,cls.validation = M.geometry(cls.local)

    def test_current_design_source_and_exact_visual_scope(self):
        self.assertEqual(M.IDS, [f'DOM_{n:05}' for n in (553,556,562,563,564,565,566)])
        self.assertNotIn(M.GLASS_ID,M.IDS)
        self.assertAlmostEqual(self.center[0],6653,places=3)
        self.assertAlmostEqual(self.center[1],7820,places=3)
        self.assertEqual(self.records['DOM_00553']['metadata']['babylonCheckCollisions'],True)

    def test_only_current_source_identity_collision_and_design_accepted(self):
        for mutation in ('design','id','collision'):
            with tempfile.TemporaryDirectory() as tmp:
                scene = copy.deepcopy(self.scene)
                body = next(r for r in scene['objects'] if r['id'] == 'DOM_00553')
                if mutation == 'design':scene['activeDesign']['livingLayout']='A'
                elif mutation == 'id':body['name']=body['name'].replace('-B-2026-09-11','-2026-08-24')
                else:body['metadata']['babylonCheckCollisions']=False
                p = Path(tmp); (p/'scene.json').write_text(json.dumps(scene)); (p/'dom-mm.obj').symlink_to(self.directory/'dom-mm.obj')
                with self.subTest(mutation=mutation), self.assertRaises(ValueError):M.source(p)

    def test_fire_is_six_cards_inside_glass_and_body(self):
        flame = next(m for m in self.meshes if m.role=='flames')
        self.assertEqual(len(flame.indices)//3,12)
        self.assertLess(self.validation[flame.name]['maximumRadiusMm'],210)
        self.assertLess(self.validation['RFIRE_LOGS']['maximumRadiusMm'],214)
        self.assertLess(self.validation['RFIRE_EMBERS']['maximumRadiusMm'],200)
        # The visible fire begins inside the logs' elevation/plan envelope;
        # opaque wood can occlude its roots from moving viewpoints.
        self.assertAlmostEqual(min(p[2] for p in flame.positions),485)
        self.assertLess(max(p[0] for p in flame.positions),175)
        for row in self.transforms:
            if 'cards' in row:self.assertEqual(row['centerRelativeMm'][0],110)
        for m in self.meshes:self.assertLessEqual(self.validation[m.name]['maximumRadiusMm'],255.011)

    def test_reclosed_window_or_escaped_fire_rejected(self):
        for mutation in ('window','flame','ember'):
            meshes = copy.deepcopy(self.meshes)
            if mutation=='window':
                next(m for m in meshes if m.role=='shell').triangle((250,-2,600),(250,2,600),(250,0,800))
            elif mutation=='flame':next(m for m in meshes if m.role=='flames').positions[0]=(260,0,700)
            else:next(m for m in meshes if m.role=='embers').positions[0]=(0,0,800)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):M.validate(meshes)

    def test_rotation_follows_current_minus45_facing(self):
        point = M.rotate((100,0,700),M.FACING)
        self.assertAlmostEqual(point[0],math.sqrt(5000))
        self.assertAlmostEqual(point[1],-math.sqrt(5000))
        for m in self.meshes:
            for p in m.positions:
                back = M.rotate(M.rotate(p,M.FACING),-M.FACING)
                self.assertLess(max(abs(a-b) for a,b in zip(p,back)),1e-10)

    def test_unreal_coordinate_roundtrip_is_submillimetre(self):
        with tempfile.TemporaryDirectory() as tmp:
            meshes = copy.deepcopy(self.meshes)
            for mesh in meshes:
                mesh.positions = [M.rotate(p,M.FACING) for p in mesh.positions]
                mesh.normals = [M.rotate(p,M.FACING) for p in mesh.normals]
            p = Path(tmp)/'stove.glb'; M.G.write_glb(meshes,self.center,p)
            actual = M.G.read_glb_positions(p,self.center)
            for mesh in meshes:
                error = max(abs(a-b) for p,q in zip(mesh.positions,actual[mesh.name]) for a,b in zip(p,q))
                self.assertLess(error,.002)


if __name__=='__main__':unittest.main()
