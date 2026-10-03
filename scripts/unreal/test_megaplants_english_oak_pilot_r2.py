"""Meaningful source/path/scope guards; no Unreal or project mutations."""
import copy
import importlib.util
from pathlib import Path
import unittest
import zipfile

def module(name):
    p=Path(__file__).with_name(name+'.py');s=importlib.util.spec_from_file_location(name.replace('-','_'),p)
    m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
g=module('megaplants-english-oak-pilot-guards-r2')
e=module('megaplants-english-oak-source-r1')

class SourceGuards(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.extraction=g.read(g.SOURCE/'source-extraction-receipt.json')
        cls.inspection=g.read(g.SOURCE/'usd-source-inspection-r1.json')
    def test_original_whole_d(self):
        selected=g.validate_source(self.extraction,self.inspection)
        self.assertEqual(selected['basePlusExpandedFanTrianglesSourceEstimate'],3680767)
    def test_reject_unsafe_zip_paths(self):
        for name in ('../x.usd','/x.usd','C:/x.usd','x\\y.usd','./x.usd','x//y.usd'):
            with self.subTest(name=name),self.assertRaises(ValueError):e.validate_member(zipfile.ZipInfo(name))
    def test_reject_symlink_and_unapproved_members(self):
        r=zipfile.ZipInfo('Tree_English_Oak_01_Foliage.usd');r.file_size=e.EXPECTED[r.filename]
        r.external_attr=(0o120777<<16)
        with self.assertRaises(ValueError):e.validate_member(r)
        with self.assertRaises(ValueError):e.validate_member(zipfile.ZipInfo('replacement.png'))
    def test_reject_texture_or_shader_substitution(self):
        for field in ('asset','shader'):
            v=copy.deepcopy(self.inspection)
            if field=='asset':v['usdLayers'][0]['assetAttributes']=[{'value':'invented.png'}]
            else:v['usdLayers'][0]['materialsAndShaders'][1]['attributes'].append({'name':'inputs:roughness','value':.3,'authored':True})
            with self.subTest(field=field),self.assertRaises(RuntimeError):g.validate_source(self.extraction,v)
    def test_reject_unit_or_assembly_change(self):
        for field in ('units','assembly'):
            v=copy.deepcopy(self.inspection)
            if field=='units':v['usdLayers'][-1]['metersPerUnit']=.01
            else:v['usdLayers'][-1]['pointInstancers'][0]['instanceCount']=1
            with self.subTest(field=field),self.assertRaises(RuntimeError):g.validate_source(self.extraction,v)
    def test_only_own_map_packages_and_camera_delta(self):
        b={'Content/Brezi/Maps/Brezi.umap':{'sha256':'a','bytes':1},'Content/Data/viewpoints.json':{'sha256':'b','bytes':1},
           'BreziTwin.uproject':{'sha256':'c','bytes':1}}
        a=copy.deepcopy(b);a['Content/Data/viewpoints.json']['sha256']='d'
        a['Content/Brezi/EnglishOakPilot20261002R1/Maps/EnglishOakPilot.umap']={'sha256':'e','bytes':1}
        self.assertTrue(g.validate_delta(b,a)['originalMainMapUnchanged'])
        for key in ('Content/Brezi/Maps/Brezi.umap','BreziTwin.uproject'):
            bad=copy.deepcopy(a);bad[key]['sha256']='f'
            with self.subTest(key=key),self.assertRaises(RuntimeError):g.validate_delta(b,bad)
        bad=copy.deepcopy(a);bad['Content/Brezi/Outside.uasset']={'sha256':'f','bytes':1}
        with self.assertRaises(RuntimeError):g.validate_delta(b,bad)

if __name__=='__main__':unittest.main()
