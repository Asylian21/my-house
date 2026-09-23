"""Source-policy and physical mapping tests. These do not claim native renders."""
import copy
import importlib.util
import json
import math
import unittest
from pathlib import Path

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('exterior',HERE/'photoreal-exterior.py')
e=importlib.util.module_from_spec(spec);spec.loader.exec_module(e)
GEOMETRY=e.ROOT/'output/unreal/kitchen-archviz-20260922-r2/geometry'


def scene():
    names=[('facade','real-larch-garden-field-0:1.35x2.75','Walls'),
        ('soffit','real-larch-porch-ceiling-0:4.25x2.48','Decking'),
        ('deck','TERR-D1-GARDEN · PBR materiál','Decking'),
        ('roof','real-roof','Roof'),('GARAGE-DOOR · sekcia 1','real-roof-edge','Roof'),
        ('Plné antracitové dverné krídlo','real-roof-edge','Roof'),
        ('Orezaný falc · MAIN_FRONT_SEAM_1','real-roof-edge','Roof'),
        ('Nízky stolík · doska','real-larch-table:0.90x0.55','Interior'),
        ('Súvislý podhľad strešnej roviny','real-soffit','Interior')]
    s={'activeDesign':{'variant':'C','heatingLayout':'B','livingLayout':'B'},
        'deckBoardLayout':{'widthMm':145,'jointMm':8},'materials':{},'objects':[]}
    for i,(label,name,group) in enumerate(names):
        key='slot-'+str(i);s['materials'][key]={'name':name,'alpha':1}
        s['objects'].append({'id':'object-'+str(i),'sourceId':label,'name':label,'group':group,'enabled':True,
            'instances':1,'materialSlots':[key],'boundsMm':{'min':[0,0,0],'max':[3500,2480,2450]}})
    return s


class ExteriorTests(unittest.TestCase):
    def test_shared_roof_material_does_not_recolor_doors(self):
        selected=e.select_targets(scene());names={r['name'] for r in selected}
        self.assertNotIn('GARAGE-DOOR · sekcia 1',names)
        self.assertNotIn('Plné antracitové dverné krídlo',names)
        self.assertIn('Orezaný falc · MAIN_FRONT_SEAM_1',names)

    def test_interior_table_and_white_underside_are_not_reclassified(self):
        names={r['name'] for r in e.select_targets(scene())}
        self.assertNotIn('Nízky stolík · doska',names)
        self.assertNotIn('Súvislý podhľad strešnej roviny',names)

    def test_selection_survives_reordered_source_ordinals(self):
        s=scene();before={r['name']:r['recipe'] for r in e.select_targets(s)}
        s['objects'].reverse()
        for i,r in enumerate(s['objects']):
            r['id']='NEW_'+str(i);old=r['materialSlots'][0];new='MAT_REORDER_'+str(i)
            s['materials'][new]=s['materials'].pop(old);r['materialSlots']=[new]
        self.assertEqual(before,{r['name']:r['recipe'] for r in e.select_targets(s)})

    def test_rejects_archive_or_changed_deck_design(self):
        for path,value in [('activeDesign',{'variant':'C','heatingLayout':'A','livingLayout':'B'}),('deckBoardLayout',{'widthMm':140,'jointMm':8})]:
            s=scene();s[path]=value
            with self.assertRaises(RuntimeError):e.select_targets(s)

    def test_undercladding_grain_follows_slope(self):
        s=scene();r=next(t for t in e.select_targets(s) if t['recipe']['kind']=='soffit')
        g=r['recipe']['grain'];self.assertAlmostEqual(sum(x*x for x in g),1)
        self.assertGreater(g[0],0);self.assertGreater(g[2],0);self.assertEqual(g[1],0)
        s['materials']['slot-1']['name']='real-larch-porch-ceiling-1:4.25x2.48'
        other=next(t for t in e.select_targets(s) if t['recipe']['kind']=='soffit')
        self.assertLess(other['recipe']['grain'][2],0)

    def test_deck_grid_anchor_in_gap_even_with_trimmed_perimeter(self):
        vertices=[]
        for row in range(11):
            lo=8+row*153
            for y in [lo,lo+145]:vertices.extend([(0,y,20)]*20)
        vertices.extend([(0,43,20),(0,901,20)])
        anchor=e.deck_grid_anchor(vertices)
        for row in range(11):
            ends=[(-y/10-anchor)/15.3 for y in [8+row*153,153+row*153]]
            self.assertEqual(math.floor(ends[0]),math.floor(ends[1]))

    def test_missing_physical_gap_is_rejected(self):
        with self.assertRaises(RuntimeError):e.deck_grid_anchor([(0,0,0),(0,100,0)])

    def test_palette_shared_and_wood_remains_matte(self):
        recipes=[t['recipe'] for t in e.select_targets(scene()) if t['recipe']['kind']!='roof']
        self.assertTrue(all(r['palette']==e.PALETTE for r in recipes))
        self.assertTrue(all(.6<=r['roughness']<=.8 for r in recipes))

    @unittest.skipUnless((GEOMETRY/'scene.json').is_file(),'Current native source export not present')
    def test_every_current_deck_triangle_avoids_material_boundary(self):
        s=json.loads((GEOMETRY/'scene.json').read_text());targets=e.prepare_targets(s,GEOMETRY)
        decks=[r for r in targets if r['recipe']['kind']=='deck']
        positions=e.source_deck_positions(GEOMETRY/'dom-mm.obj',{r['id'] for r in decks})
        checked=0
        for row in decks:
            points=positions[row['id']];anchor=row['recipe']['anchorCm'][1]
            for i in range(0,len(points),3):
                span=[(-p[1]/10-anchor)/15.3 for p in points[i:i+3]]
                self.assertEqual(math.floor(min(span)),math.floor(max(span)),row['name']);checked+=1
        self.assertGreater(checked,2000)

    @unittest.skipUnless((e.ROOT/'output/unreal/facade-wood-study/hinoki_planks/ao-4k.jpg').is_file(),'Restore 4K source scans first')
    def test_input_provenance_all_maps_verified(self):
        data=e.load_inputs();self.assertEqual(len(data['assets']),2)
        self.assertTrue(all(a['license']=='CC0-1.0' for a in data['assets'].values()))
        self.assertEqual(sum(len(a['maps']) for a in data['assets'].values()),8)


if __name__=='__main__':unittest.main()
