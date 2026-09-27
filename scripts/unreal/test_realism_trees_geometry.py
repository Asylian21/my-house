"""Growth connectivity, immutable placements, LOD budget and native transport."""
import copy
import importlib.util
import json
import math
from pathlib import Path
import struct
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('trees', Path(__file__).with_name('realism-trees-geometry.py'))
trees = importlib.util.module_from_spec(spec); spec.loader.exec_module(trees)


class Trees(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Canonical generator creates the original six exact prototypes. A
        # synthetic placement fixture checks transfer independently of a saved
        # historical project's transient native actor paths.
        rural = trees.load_module('rural-geometry.py')
        cls.source = {'meshes': [], 'groups': []}
        for v in range(3):
            levels = [[m.data(lod) for m in rural.tree_prototype(v,lod)] for lod in range(3)]
            for part in range(2):
                row=levels[0][part]; row['lods']=[levels[1][part],levels[2][part]]; cls.source['meshes'].append(row)
                cls.source['groups'].append({'id':f'windbreak_{v}_{part}', 'meshId':row['id'],
                    'instances':[{'positionCm':[v*123.25,-1300.37,-19], 'yawDeg':42.69, 'scale':[.934]*3}],
                    'cullStartCm':37500,'cullEndCm':50000,'castShadow':True,'collision':'NoCollision'})
        cls.before=copy.deepcopy(cls.source)
        cls.plan=trees.build_plan(cls.source)

    def test_every_child_and_leaf_grows_from_its_parent(self):
        for v in range(3):
            branches,leaves=trees.skeleton(v)
            self.assertEqual({b['order'] for b in branches},{0,1,2,3})
            for b in branches[1:]:
                self.assertLess(b['parent'],b['id'])
                self.assertLess(math.dist(b['points'][0],trees.curve(branches[b['parent']]['points'],b['parentT'])),1e-9)
            for leaf in leaves:
                self.assertEqual(branches[leaf['branch']]['order'],3)
                self.assertLess(math.dist(leaf['base'],trees.curve(branches[leaf['branch']]['points'],leaf['t'])),1e-9)

    def test_no_source_mutation_and_exact_instance_order(self):
        self.assertEqual(self.source,self.before)
        for old,new in zip(self.source['groups'],self.plan['groups']):
            self.assertEqual(old['instances'],new['instances'])
            self.assertEqual(old['meshId'],new['sourceMeshId'])
            self.assertEqual(old['id'],new['sourceGroupId'])
            for p in ('collision','cullStartCm','cullEndCm','castShadow'): self.assertEqual(old[p],new[p])

    def test_same_height_inside_all_original_envelopes(self):
        for witness in self.plan['prototypes']:
            envelope=witness['sourceEnvelopeCm']
            for lod in witness['lods']:
                self.assertAlmostEqual(lod['boundsCm']['max'][2],envelope['max'][2],places=5)
                for axis in range(3):
                    self.assertGreaterEqual(lod['boundsCm']['min'][axis],envelope['min'][axis]-1e-6)
                    self.assertLessEqual(lod['boundsCm']['max'][axis],envelope['max'][axis]+1e-6)

    def test_bounded_triangle_cost_each_lod_and_three_distinct_profiles(self):
        for witness in self.plan['prototypes']:
            counts=[l['triangles'] for l in witness['lods']]
            self.assertGreater(counts[0],counts[1]); self.assertGreater(counts[1],counts[2])
            for lod in witness['lods']: self.assertLess(lod['triangles'],lod['oldTriangles']*1.5)
        self.assertEqual(len({r['growthHierarchySha256'] for r in self.plan['prototypes']}),3)
        self.assertEqual(len({r['profile'] for r in self.plan['prototypes']}),3)

    def test_no_degenerate_triangles_finite_uvs_and_cm(self):
        for row in self.plan['meshes']:
            for lod in [row,*row['lods']]:
                points,indices=lod['verticesCm'],lod['indices']
                self.assertEqual(len(points),len(lod['uvs']))
                self.assertTrue(all(math.isfinite(c) for p in points+lod['uvs'] for c in p))
                for i in range(0,len(indices),3):
                    a,b,c=(points[j] for j in indices[i:i+3])
                    self.assertGreater(trees.norm(trees.cross(trees.sub(b,a),trees.sub(c,a))),1e-7)

    def test_fail_closed_when_source_binding_or_collision_changes(self):
        source=copy.deepcopy(self.source); source['groups'][0]['collision']='QueryAndPhysics'
        with self.assertRaisesRegex(ValueError,'collision'):trees.source_contract(source)
        source=copy.deepcopy(self.source); source['groups'][1]['instances'][0]['yawDeg']=0
        with self.assertRaisesRegex(ValueError,'placement'):trees.source_contract(source)
        source=copy.deepcopy(self.source); source['groups'][0]['meshId']='another_tree'
        with self.assertRaisesRegex(ValueError,'binding'):trees.source_contract(source)

    def test_generation_is_deterministic(self):
        self.assertEqual(trees.digest(trees.skeleton(1)),trees.digest(trees.skeleton(1)))
        self.assertNotEqual(trees.digest(trees.skeleton(0)),trees.digest(trees.skeleton(1)))

    def test_glb_preserves_all_lods_triangle_uv_and_axis_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'trees.glb'
            trees.load_module('rural-import.py').write_glb(path,self.plan)
            raw=path.read_bytes(); magic,version,length=struct.unpack_from('<III',raw)
            self.assertEqual((magic,version,length),(0x46546c67,2,len(raw)))
            size,kind=struct.unpack_from('<II',raw,12)
            self.assertEqual(kind,0x4e4f534a)
            glb=json.loads(raw[20:20+size]); binary=raw[28+size:]
            self.assertEqual(len(glb['meshes']),18)
            records=[(row['id']+'_LOD'+str(i),lod) for row in self.plan['meshes'] for i,lod in enumerate([row,*row['lods']])]
            for (name,lod),mesh in zip(records,glb['meshes']):
                self.assertEqual(mesh['name'],name)
                primitive=mesh['primitives'][0]
                accessor=glb['accessors'][primitive['attributes']['POSITION']]
                self.assertEqual(accessor['count'],len(lod['verticesCm']))
                self.assertEqual(glb['accessors'][primitive['indices']]['count'],len(lod['indices']))
                self.assertEqual(glb['accessors'][primitive['attributes']['TEXCOORD_0']]['count'],len(lod['uvs']))
                view=glb['bufferViews'][accessor['bufferView']]
                actual=struct.unpack_from('<fff',binary,view['byteOffset'])
                x,y,z=lod['verticesCm'][0]
                for a,b in zip(actual,(x/100,z/100,y/100)):self.assertAlmostEqual(a,b,places=6)


if __name__=='__main__':unittest.main()
