"""Spatial contract tests against the freshly exported canonical C/B/B OBJ."""
import importlib.util
import json
import math
import os
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[2]
spec=importlib.util.spec_from_file_location('rural_geometry',ROOT/'scripts/unreal/rural-geometry.py')
rural=importlib.util.module_from_spec(spec);spec.loader.exec_module(rural)
GEOMETRY=Path(os.environ.get('BREZI_RURAL_GEOMETRY',ROOT/'output/unreal/rural-context-20260923-r4/geometry'))


def in_poly(p,polygon):
    value=False
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        if (a[1]>p[1])!=(b[1]>p[1]) and p[0]<(b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:value=not value
    return value


def in_triangle(p,triangle):
    signs=[]
    for a,b in zip(triangle,triangle[1:]+triangle[:1]):signs.append((p[0]-a[0])*(b[1]-a[1])-(p[1]-a[1])*(b[0]-a[0]))
    return all(s>=-1e-7 for s in signs) or all(s<=1e-7 for s in signs)


@unittest.skipUnless((GEOMETRY/'scene.json').exists(),'Fresh source export required')
class SpatialContracts(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scene=json.loads((GEOMETRY/'scene.json').read_text())
        cls.data=rural.build(cls.scene,GEOMETRY/'dom-mm.obj')
        cls.meshes={m['id']:m for m in cls.data['meshes']}
        ids=[o['id'] for o in cls.scene['objects'] if 'real-road' in o['materialNames'] or o['id'] in cls.data['hideSourceIds']]
        cls.source=rural.read_obj(GEOMETRY/'dom-mm.obj',ids)
        cls.road=[t for o in cls.scene['objects'] if 'real-road' in o['materialNames'] for t in cls.source[o['id']]]
        for mesh in cls.data['meshes']:
            if mesh['material']!='road':continue
            cls.road.extend(tuple(tuple(mesh['verticesCm'][j]) for j in mesh['indices'][i:i+3]) for i in range(0,len(mesh['indices']),3))
        cls.road_edges=rural.boundary_segments(cls.road)
        cls.paths=[]
        for name,value in cls.scene['surfaces'].items():
            if name.startswith('superseded') or not isinstance(value,dict) or not value.get('polygonMm'):continue
            cls.paths.append([((p['x']-15200)/10,(10800-p['y'])/10) for p in value['polygonMm']])

    def test_architectural_authority_and_source_scope(self):
        self.assertEqual(self.data['metadata']['activeDesign'],{'variant':'C','heatingLayout':'B','livingLayout':'B'})
        self.assertEqual(self.data['metadata']['housePlacement']['streetSetbackMm'],3000)
        self.assertEqual(self.data['metadata']['housePlacement']['eastSetbackMm'],3000)
        for id_ in self.data['hideSourceIds']:
            source=next(o for o in self.scene['objects'] if o['id']==id_)
            if source['materialNames']==['real-plant-grass']:
                self.assertTrue(source['name'].startswith('Riedka náletová vegetácia krajnice '))
                self.assertEqual(source['group'],'Landscape')
            elif id_ in ('DOM_01835','DOM_01837','DOM_01838','DOM_01839'):
                self.assertEqual(source['metadata']['entityId'],'SITE-FENCE')
                self.assertTrue(source['materialNames'][0].startswith('real-hedge-'))
            else:
                self.assertEqual(source['materialNames'],['real-road-reserve'])
        self.assertEqual(len(self.data['hideSourceIds']),36)
        self.assertNotIn('DOM_01836',self.data['hideSourceIds'])
        background=next(o for o in self.scene['objects'] if o.get('metadata',{}).get('visualizationBackground'))
        self.assertGreaterEqual(max(background['boundsMm']['max'][:2]),500000)
        self.assertTrue(any(r['sourceId']==background['id'] and r['material']=='field' for r in self.data['replacementMaterials']))

    def test_generator_passes_actual_native_import_schema_preflight(self):
        native_spec=importlib.util.spec_from_file_location('rural_native_preflight',ROOT/'scripts/unreal/rural-import.py')
        native=importlib.util.module_from_spec(native_spec);native_spec.loader.exec_module(native)
        native.validate_plan(self.data,self.scene)

    def test_non_degenerate_clockwise_mesh_and_lod_budget(self):
        for mesh in self.data['meshes']:
            self.assertEqual(mesh['winding'],'clockwise')
            previous=len(mesh['indices'])
            for level in [mesh]+mesh.get('lods',[]):
                vertices=level['verticesCm'];indices=level['indices']
                self.assertEqual(len(level['uvs']),len(vertices))
                self.assertTrue(all(math.isfinite(v) for p in vertices for v in p))
                if level is not mesh:self.assertLess(len(indices),previous)
                previous=len(indices)
                for i in range(0,len(indices),3):
                    a,b,c=[vertices[j] for j in indices[i:i+3]]
                    normal=rural.cross([b[k]-a[k] for k in range(3)],[c[k]-a[k] for k in range(3)])
                    self.assertGreater(sum(v*v for v in normal),1e-12,mesh['id'])

    def test_dense_canopy_lod_area_and_instanced_triangle_budget(self):
        def area(mesh):
            total=0;vertices=mesh['verticesCm']
            for i in range(0,len(mesh['indices']),3):
                a,b,c=[vertices[j] for j in mesh['indices'][i:i+3]]
                n=rural.cross([b[k]-a[k] for k in range(3)],[c[k]-a[k] for k in range(3)])
                total+=math.sqrt(sum(v*v for v in n))/2
            return total
        grouped={group['meshId'] for group in self.data['groups']}
        budget=sum(len(group['instances'])*len(self.meshes[group['meshId']]['indices'])//3 for group in self.data['groups'])
        budget+=sum(len(m['indices'])//3 for m in self.data['meshes'] if m['id'] not in grouped)
        self.assertLessEqual(budget,12000000)
        for mesh in self.data['meshes']:
            if mesh['material'] not in ('leaf','drygrass','weed'):continue
            baseline=area(mesh)
            for lod in mesh['lods']:
                ratio=area(lod)/baseline
                self.assertGreaterEqual(ratio,.70,mesh['id'])
                self.assertLessEqual(ratio,1.25,mesh['id'])
            if mesh['material']=='leaf':
                self.assertGreaterEqual(len(mesh['indices'])//12,7000)

    def test_entire_plant_envelope_clears_road_and_access_paths(self):
        plants=[g for g in self.data['groups'] if self.meshes[g['meshId']]['material'] in ('drygrass','weed','leaf','bark')]
        for group in plants:
            mesh=self.meshes[group['meshId']]
            radius=max(math.hypot(p[0],p[1]) for lod in [mesh]+mesh.get('lods',[]) for p in lod['verticesCm'])
            for instance in group['instances']:
                p=instance['positionCm'];r=radius*max(instance['scale'])
                self.assertFalse(any(in_triangle(p,t) for t in self.road),group['id'])
                self.assertTrue(rural.edge_clear(p,self.road_edges,r),group['id'])
                for path in self.paths:
                    self.assertFalse(in_poly(p,path),group['id'])
                    self.assertTrue(rural.edge_clear(p,list(zip(path,path[1:]+path[:1])),r),group['id'])
                if mesh['material']=='drygrass':
                    height=max(q[2] for q in mesh['verticesCm'])*instance['scale'][2]
                    self.assertLessEqual(height,80)

    def test_manhole_is_inside_actual_source_carriageway(self):
        mesh=self.meshes['road_manhole_cover']
        for p in mesh['verticesCm']:
            self.assertTrue(any(in_triangle(p,t) for t in self.road))
        width=max(p[0] for p in mesh['verticesCm'])-min(p[0] for p in mesh['verticesCm'])
        self.assertAlmostEqual(width,60)

    def test_microrelief_stays_on_source_verge_and_above_upward_faces(self):
        for id_ in self.data['hideSourceIds']:
            if 'verge_'+id_ not in self.meshes: continue
            mesh=self.meshes['verge_'+id_]
            for i in range(0,len(mesh['indices']),3):
                a,b,c=[mesh['verticesCm'][j] for j in mesh['indices'][i:i+3]]
                center=tuple((a[k]+b[k]+c[k])/3 for k in range(3))
                self.assertTrue(any(in_triangle(center,t) for t in self.source[id_]),id_)
                self.assertFalse(any(in_triangle(center,t) for t in self.road),id_)
                self.assertLess(rural.cross([b[k]-a[k] for k in range(3)],[c[k]-a[k] for k in range(3)])[2],0)

    def test_windbreak_roots_beyond_rear_boundary(self):
        run=next(r for r in self.scene['fence']['fixedRuns'] if r['id']=='FENCE-FIXED-REAR')['pointsMm']
        a,b=run[1],run[0];dx=b['x']-a['x'];dy=b['y']-a['y'];length=math.hypot(dx,dy)
        poses=[]
        for group in self.data['groups']:
            if not group['id'].startswith('windbreak_') or not group['id'].endswith('_0'):continue
            poses.extend(group['instances'])
        self.assertGreaterEqual(len(poses),50)
        self.assertLessEqual(len(poses),62)
        for p in poses:
            x=p['positionCm'][0]*10+15200;y=10800-p['positionCm'][1]*10
            self.assertGreaterEqual((dx*(y-a['y'])-dy*(x-a['x']))/length,1100-1e-4)
        for variant in range(3):
            leaf=self.meshes['tree_leaf_'+str(variant)]
            self.assertGreater(len(leaf['indices'])//3,9000)
            self.assertEqual(len(leaf['indices'])%12,0) # folded four-triangle individual laminae
        shrubs=next(g for g in self.data['groups'] if g['id']=='windbreak_natural_understorey')
        mesh=self.meshes[shrubs['meshId']]
        self.assertGreaterEqual(len(shrubs['instances']),40)
        for shrub in shrubs['instances']:
            height=max(p[2] for p in mesh['verticesCm'])*shrub['scale'][2]
            self.assertGreaterEqual(height,110)
            self.assertLessEqual(height,160)
            x=shrub['positionCm'][0]*10+15200;y=10800-shrub['positionCm'][1]*10
            self.assertGreaterEqual((dx*(y-a['y'])-dy*(x-a['x']))/length,900-1e-4)

    def test_continuations_match_exact_source_terminals_and_extend_one_kilometre(self):
        self.assertEqual(len(self.data['roadContinuations']),3)
        for row in self.data['roadContinuations']:
            edges=rural.boundary_segments(self.source[row['sourceObjectId']])
            actual={tuple(round(v,4) for v in p) for p in row['terminalEdgeCm']}
            self.assertTrue(any(actual=={tuple(round(v,4) for v in a),tuple(round(v,4) for v in b)} for a,b in edges))
            self.assertEqual(row['collision'],'NoCollision')
            self.assertEqual(row['distanceCm'],100000)
            self.assertNotIn(row['sourceObjectId'],self.data['hideSourceIds'])
            mesh=self.meshes['road_extension_'+row['id']]
            self.assertTrue(mesh['nanite'])
            self.assertEqual(mesh['collision'],'NoCollision')
            curb=self.meshes['road_extension_curb_'+row['id']]
            self.assertTrue(curb['nanite'])
            self.assertEqual(curb['collision'],'NoCollision')
            tangent_vectors=[]
            seam=[tuple(p) for p in row['terminalEdgeCm']]
            for endpoint in seam:
                neighbours=[b if a==endpoint else a for a,b in edges
                            if (a==endpoint or b==endpoint) and {a,b}!=set(seam)]
                self.assertEqual(len(neighbours),1)
                tangent_vectors.append(rural.normal([endpoint[k]-neighbours[0][k] for k in range(3)]))
            expected=rural.normal([sum(v[k] for v in tangent_vectors) for k in range(3)])
            self.assertLess(math.dist(row['tangent'],expected),1e-12)
            for start,end in zip(row['terminalEdgeCm'],row['endEdgeCm']):
                self.assertAlmostEqual(math.dist(start,end),100000,places=5)
                self.assertTrue(any(math.dist(start,p)<1e-4 for p in mesh['verticesCm']))
            for i in range(0,len(mesh['indices']),3):
                a,b,c=[mesh['verticesCm'][j] for j in mesh['indices'][i:i+3]]
                self.assertLess(rural.cross([b[k]-a[k] for k in range(3)],[c[k]-a[k] for k in range(3)])[2],0)
        for variant in range(3):
            bark=next(g for g in self.data['groups'] if g['id']==f'windbreak_{variant}_0')['instances']
            leaves=next(g for g in self.data['groups'] if g['id']==f'windbreak_{variant}_1')['instances']
            self.assertEqual(bark,leaves)

    def test_lawn_keep_and_raw_regions_have_no_overlap(self):
        raw=self.meshes['parcel_outer_raw_soil'];polygons=self.data['managedLawnKeepPolygonsCm']
        for i in range(0,len(raw['indices']),3):
            vertices=[raw['verticesCm'][j] for j in raw['indices'][i:i+3]]
            center=[sum(p[k] for p in vertices)/3 for k in range(2)]
            self.assertFalse(any(in_poly(center,p) for p in polygons))


if __name__=='__main__':unittest.main()
