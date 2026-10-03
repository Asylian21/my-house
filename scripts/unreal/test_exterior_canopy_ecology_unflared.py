"""Exact non-collar preservation and strict native successor validation."""
from collections import Counter
from copy import deepcopy
import importlib.util
from pathlib import Path
import json
import unittest

HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
def module(name,file):
    spec=importlib.util.spec_from_file_location(name,HERE/file);value=importlib.util.module_from_spec(spec);spec.loader.exec_module(value);return value
G=module('unflared_source','exterior-canopy-ecology-unflared.py')
N=module('unflared_native','exterior-canopy-native.py')
DIRECTORY=ROOT/'output/unreal/exterior-canopy-ecology-20260930-r4'
SOURCE=ROOT/'output/unreal/exterior-canopy-ecology-20260930-r3'

class UnflaredEcology(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan=G.read(DIRECTORY/'canopy-ecology-plan.json');cls.old=G.read(SOURCE/'canopy-ecology-plan.json')
        cls.geometry=G.read(DIRECTORY/'geometry-manifest.json')
        cls.context=G.read(cls.plan['sourceContext']['path'])
        cls.merged=G.read(ROOT/'output/unreal/exterior-assets-greenery-20260930-r3/geometry-manifest.json')
    def validate(self,plan):return N.validated_ecology(plan,self.geometry,self.context,self.merged,plan['sourceSceneSha256'],plan['sourceObjSha256'])
    def test_only_new_collar_instances_are_omitted(self):
        self.assertEqual(len(self.plan['groups']),130);self.assertEqual(len(self.plan['ecologyPlacements']),24773)
        self.assertEqual(self.plan['groups'],[g for g in self.old['groups']if not g['meshId'].startswith('canopy_ecology_flare_')])
        expected=[r for r in self.old['ecologyPlacements']if r['ecologyFamily']!='flare']
        self.assertEqual(Counter(map(G.digest,self.plan['ecologyPlacements'])),Counter(map(G.digest,expected)))
    def test_original_tree_ground_domain_geometry_and_textures_survive(self):
        for key in ('existingTrees','sourceRegion','ecologyDomainCm','exclusionDomainsCm','policy','activeDesign','housePlacement'):
            self.assertEqual(self.plan[key],self.old[key],key)
        self.assertEqual(self.geometry['meshes'],G.read(SOURCE/'geometry-manifest.json')['meshes'])
        self.assertEqual(G.read(DIRECTORY/'material-manifest.json'),G.read(SOURCE/'material-manifest.json'))
        self.assertEqual(self.plan['audit']['collarRemoval']['inheritedNativeActorsHidden'],0)
    def test_all_source_and_bundle_pins_are_exact(self):
        for path,value in self.plan['inputFiles'].items():self.assertEqual(G.sha(path),value,path)
        bundle=G.read(DIRECTORY/'canopy-ecology-manifest.json')
        for key in ('plan','geometryManifest','materialManifest','geometryProof','glb'):
            self.assertEqual(G.sha(bundle[key]['path']),bundle[key]['sha256'],key)
    def test_actual_decoded_native_helper_accepts_retained_footprints(self):
        result=self.validate(self.plan)
        self.assertEqual(result['audit']['instances'],24773);self.assertEqual(result['audit']['groups'],130)
        self.assertEqual(result['audit']['basalGroups'],0);self.assertEqual(result['audit']['existingTrees'],78)
        self.assertTrue(result['audit']['sourceGroundUnchanged'])
    def test_changed_non_collar_row_or_tree_cannot_pass(self):
        for key in ('detail','tree','domain','scope'):
            broken=deepcopy(self.plan)
            if key=='detail':broken['groups'][0]['instances'][0]['positionCm'][0]+=.01
            if key=='tree':broken['existingTrees'][0]['yawDeg']+=1
            if key=='domain':
                domain=json.loads(broken['ecologyDomainCm']);domain['coordinates'][0][0][0][0]+=.1
                broken['ecologyDomainCm']=json.dumps(domain)
            if key=='scope':broken['audit']['collarRemoval']['removedInstances']=79
            with self.assertRaises(RuntimeError,msg=key):self.validate(broken)

if __name__=='__main__':unittest.main()
