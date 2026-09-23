"""Semantic scope and optical topology checks; no Unreal process required."""
import importlib.util
import json
import math
import tempfile
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('photoreal_interior',HERE/'photoreal-interior.py')
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)


def source(name,**kwargs):
    return {'name':name,'alpha':1,'metallic':0,'texture':None,'color':[.5,.5,.5],**kwargs}


class InteriorContractTest(unittest.TestCase):
    def test_scope_does_not_capture_fireplace_water_black_glass_or_oak(self):
        for name in ['real-interior-fireplace-glass','real-interior-black-glass',
            'real-office-whiteboard-glass','real-pool-water','Kitchen 2026 · prírodný dub','unrelated-upholstery']:
            self.assertIsNone(m.recipe(source(name)),name)
        self.assertIsNotNone(m.recipe(source('Living warm sofa | real-interior-upholstery')))

    def test_glass_fresnel_ior_and_transmission_are_dielectric(self):
        r=m.recipe(source('real-glass',alpha=.14))
        fresnel=r['specular']*.08
        self.assertAlmostEqual(fresnel,((1.52-1)/(1.52+1))**2)
        # Two interfaces in UE's ThinTranslucentCommon.ush, single visible shell.
        transmittance=[(1-fresnel)**2*c for c in r['transmittance']]
        self.assertTrue(all(.90<t<.93 for t in transmittance))
        self.assertEqual(r['opacity'],0)
        self.assertFalse(r['twoSided'])
        self.assertEqual(r['refraction'],'RM_NONE')

    def test_stone_without_texture_has_matte_recipe(self):
        self.assertAlmostEqual(m.recipe(source('real-interior-media-stone'))['roughness'],.58)
        self.assertAlmostEqual(m.recipe(source('real-interior-worktop',texture='/assets/textures/stone-dark-albedo.jpg'))['roughness'],.46)

    def test_live_scene_semantics_exclude_water_alias_and_find_real_glass_shells(self):
        folder=m.ROOT/'output/unreal/kitchen-archviz-20260922-r2'
        if not folder.is_dir():self.skipTest('Accepted native fixture not present')
        scene=json.loads((folder/'geometry/scene.json').read_text())
        baseline=json.loads((folder/'model-refresh-import-report.json').read_text())
        selected=m.selected_bindings(scene,baseline)
        self.assertFalse(any('UTILITY-SINK' in b['sourceId'] for b in selected))
        glass=[b for b in selected if b['recipe']['kind']=='architectural-thin-glass']
        self.assertEqual(len(glass),20)
        audit=m.glass_source_audit(scene,folder/'geometry',selected)
        # This is a real source regression: gable is a duplicated prism, boxes
        # are single shells. Both must transmit once after the coverage gate.
        self.assertEqual(sorted((v['outward'],v['inward']) for v in audit.values()),[(8,8)]+[(12,0)]*19)
        changed=json.loads(json.dumps(scene)); pane=next(r for r in changed['objects'] if r['id']==glass[0]['id'])
        pane['triangles']=24
        with self.assertRaisesRegex(RuntimeError,'reviewed thin closed shell'):m.selected_bindings(changed,baseline)

    def test_solid_palette_keeps_mean_and_discards_source_pattern(self):
        source_color=[.69,.72,.72]
        r=m.recipe(source('Living warm sofa | real-interior-upholstery',color=source_color,texture='/assets/textures/living-boucle-ecru-albedo.jpg'))
        self.assertTrue(r['sourceTexturePatternRemoved'])
        self.assertTrue(all(0<c<s for c,s in zip(r['solidColorLinear'],source_color)))
        self.assertGreater(r['solidColorLinear'][0],r['solidColorLinear'][2])
        self.assertEqual(r['scan'],'rough_linen')
        self.assertEqual(r['colorVariation'],.08)

    def test_texture_identity_resolution_and_physical_dimensions(self):
        data=m.inputs()['assets']['rough_linen']
        self.assertEqual(set(data['maps']),{'albedo','normal','roughness','ao'})
        self.assertTrue(all(min(v['width'],v['height'])>=4096 for v in data['maps'].values()))
        # Provider API270.708mm width. Prevent a10x
        # textile scale regression caused by interpreting millimetres as cm.
        self.assertAlmostEqual(data['maps']['albedo']['width']/data['physicalSizeCm'][0],151.31,delta=.1)
        self.assertAlmostEqual(data['physicalSizeCm'][1],27.13,places=3)


if __name__=='__main__':unittest.main()
