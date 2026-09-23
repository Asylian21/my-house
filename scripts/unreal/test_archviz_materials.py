import copy
import json
import math
import runpy
import unittest
from types import SimpleNamespace
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
M=runpy.run_path(str(Path(__file__).with_name('archviz-materials.py')))

class ArchvizMaterialsTests(unittest.TestCase):
    def source(self,name='Kitchen 2026 · prírodný dub',texture='/assets/textures/living-natural-oak-albedo.jpg'):
        return {'name':name,'texture':texture,'roughness':.72,'metallic':0,'alpha':1,'emission':[0,0,0]}

    def test_kitchen_and_floor_get_physical_photo_detail_without_ordinal_binding(self):
        source=self.source();before=copy.deepcopy(source);r=M['recipe'](source)
        self.assertEqual(r['asset'],'oak_veneer_01');self.assertEqual(r['roughness'],source['roughness'])
        self.assertEqual(source,before);self.assertFalse(r['geometryModified'])
        floor=M['recipe'](self.source('real-interior-vinyl-oak','/assets/textures/vinyl-oak-albedo.jpg'))
        self.assertEqual(floor['sourceNormal'],'vinyl-oak') # original plank joints retained
        self.assertEqual(floor['normalSpace'],'local')

    def test_transparent_glass_and_emitter_never_receive_surface_texture(self):
        s=self.source('real-glass',None);s['alpha']=.14
        self.assertIsNone(M['recipe'](s))
        s=self.source('Kitchen 2026 · pracovné svetlo',None);s['emission']=[3,2,1]
        self.assertIsNone(M['recipe'](s))

    def test_coincident_white_surfaces_are_not_reclassified_by_color(self):
        self.assertIsNone(M['recipe'](self.source('arbitrary white object',None)))
        self.assertEqual(M['recipe'](self.source('real-interior-door-leaf',None))['kind'],'coated-finish')
        self.assertIsNone(M['recipe'](self.source('real-interior-black-glass',None)))

    def test_source_tile_grid_and_worktop_palette_keep_their_uv(self):
        r=M['recipe'](self.source('real-interior-tile','/assets/textures/tile-porcelain-albedo.jpg'))
        self.assertEqual(r['normalSpace'],'tangent');self.assertEqual(r['sourceNormal'],'tile-porcelain')
        r=M['recipe'](self.source('Kitchen 2026 · čierny kameň · saténový povrch','/assets/textures/stone-dark-albedo.jpg'))
        self.assertEqual(r['albedoStrength'],0);self.assertNotIn('asset',r)

    def test_existing_inputs_match_fixed_provider_and_project_hashes(self):
        inputs=M['load_inputs']()['assets']
        self.assertAlmostEqual(inputs['oak_veneer_01']['periodCm'],183,places=4)
        self.assertEqual(inputs['white_plaster_02']['license'],'CC0-1.0')
        self.assertEqual(inputs['tile-wall']['license'],'project-procedural')
        self.assertTrue(all(spec['sha256'] for asset in inputs.values() for spec in asset['maps'].values()))

    def test_physical_projection_is_not_uv_or_camera_dependent(self):
        code=M['PROJECTION'];self.assertIn('LocalPosition',code);self.assertIn('/ PeriodCm',code)
        self.assertNotIn('Camera',code);self.assertNotIn('UV',code)
        # The stored scan period maps1.83m to one repetition regardless of size.
        period=M['load_inputs']()['assets']['oak_veneer_01']['periodCm']
        self.assertAlmostEqual(183/period,1,places=6)
        self.assertIn('fwidth',M['DETAIL']);self.assertIn('smoothstep',M['DETAIL'])

    def test_world_normal_graph_multiplies_world_output_by_one_face_sign(self):
        writer=M['DetailWriter'].__new__(M['DetailWriter'])
        writer.u=SimpleNamespace(MaterialExpressionTwoSidedSign=object(),MaterialExpressionMultiply=object())
        created=[];connections=[]
        def node(material,name,kind):
            value=SimpleNamespace(name=name,kind=kind);created.append(value);return value
        writer.node=node;writer.connect=lambda *args:connections.append(args)
        normal=object();result=writer.face_world_normal(object(),normal)
        self.assertEqual(len(created),2)
        sign,facing=created
        self.assertIs(sign.kind,writer.u.MaterialExpressionTwoSidedSign)
        self.assertIs(facing.kind,writer.u.MaterialExpressionMultiply)
        self.assertIs(result,facing)
        self.assertEqual(connections,[(normal,'',facing,'A'),(sign,'',facing,'B')])
        self.assertTrue(M['recipe'](self.source())['twoSidedWorldNormalCorrected'])
        tile=M['recipe'](self.source('tile','/assets/textures/tile-porcelain-albedo.jpg'))
        self.assertNotIn('twoSidedWorldNormalCorrected',tile) # UE already flips tangent normals.

if __name__=='__main__':unittest.main()
