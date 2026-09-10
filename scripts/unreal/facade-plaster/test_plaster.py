"""Portable policy regressions; these do not claim native graph/render proof."""
import copy,importlib.util,unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('plaster',Path(__file__).with_name('plaster.py'));p=importlib.util.module_from_spec(spec);spec.loader.exec_module(p)

class PlasterPolicy(unittest.TestCase):
 def graph(self):
  return {'normalMix':'normal','nodes':{'normal':{'properties':{'const_alpha':.20000000298023224},'inputs':['flat','scan']},'albedo':{'properties':{'const_alpha':.15}},'roughness':{'properties':{'map':'source'}}},'settings':{'tangent_space_normal':False},'textures':['a','n','r']}
 def test_only_normal_weight(self):
  before=self.graph();after=copy.deepcopy(before);after['nodes']['normal']['properties']['const_alpha']=.5
  self.assertTrue(p.assert_only_normal_changed(before,after));self.assertNotEqual(before,after)
 def test_reject_other_graph_changes(self):
  for change in ('normal','albedo','roughness','edge','basis','texture','extra'):
   with self.subTest(change=change):
    before=self.graph();after=copy.deepcopy(before);after['nodes']['normal']['properties']['const_alpha']=.5
    if change in ('normal','albedo'):after['nodes'][change]['properties']['const_alpha']=.6
    elif change=='roughness':after['nodes']['roughness']['properties']['map']='other'
    elif change=='edge':after['nodes']['normal']['inputs'].reverse()
    elif change=='basis':after['settings']['tangent_space_normal']=True
    elif change=='texture':after['textures'][0]='other'
    else:after['nodes']['extra']={}
    with self.assertRaises(RuntimeError):p.assert_only_normal_changed(before,after)
 def test_reject_changed_source_strength(self):
  before=self.graph();before['nodes']['normal']['properties']['const_alpha']=.3
  with self.assertRaises(RuntimeError):p.assert_only_normal_changed(before,copy.deepcopy(before))
 def test_exact_binding_modes(self):
  own='/own';self.assertEqual(p.binding_policy([],p.BASE,own),'source');self.assertEqual(p.binding_policy([own],own,own),'active')
  for args in [([],p.BASE,own,'active'),([own],own,own,'source'),([None],p.BASE,own),(['/foreign'],'/foreign',own),([],own,own),([own,own],own,own)]:
   with self.subTest(args=args),self.assertRaises(RuntimeError):p.binding_policy(*args)
 def world(self):
  selected={i:{'actor':i,'component':'mesh'} for i in p.IDS};world={'actors':{i:{'components':[{'name':'mesh','overrides':[],'materials':[p.BASE],'collision':'unchanged'}]} for i in p.IDS},'protectedAssetHashes':{'source':'hash'},'grassInstanceCount':33769}
  wanted={i:['/own'] for i in p.IDS};after=copy.deepcopy(world)
  for a in after['actors'].values():a['components'][0].update(overrides=['/own'],materials=['/own'])
  return world,after,selected,wanted
 def test_scope_and_protected_world(self):
  a,b,s,w=self.world();self.assertTrue(p.compare_world(a,b,s,w))
  for change in ('collision','sourceAsset','grass','actor','scope'):
   with self.subTest(change=change):
    a,b,s,w=self.world()
    if change=='collision':b['actors'][p.IDS[0]]['components'][0]['collision']='disabled'
    elif change=='sourceAsset':b['protectedAssetHashes']['source']='changed'
    elif change=='grass':b['grassInstanceCount']=0
    elif change=='actor':b['actors']['foreign']={}
    else:w.pop(p.IDS[0])
    with self.assertRaises(RuntimeError):p.compare_world(a,b,s,w)
 def test_json_numeric_value_equivalence(self):
  a,b,s,w=self.world();a['number']=(0.,1.);b['number']=[0,1];self.assertTrue(p.compare_world(a,b,s,w))
  b['number'][0]=.001
  with self.assertRaises(RuntimeError):p.compare_world(a,b,s,w)

class StableGraphIdentity(unittest.TestCase):
 def raw(self):
  def link(pin,node):return {'pin':pin,'node':node,'output':'' if node else None}
  def node(kind,inputs=(),**props):return {'class':kind,'properties':props,'inputs':[link(*v) for v in inputs],'outputs':['']}
  return {'nodes':{
   'normalize_14':node('Normalize',[('Input','mix_83')]),
   'mix_83':node('Lerp',[('A','flat_2'),('B','scan_9'),('Alpha',None)],const_alpha=.2),
   'flat_2':node('VertexNormal'),
   'scan_9':node('Function',[('U','size_5'),('V','size_6')],function='same-source'),
   'size_5':node('Constant',r=100.),'size_6':node('Constant',r=100.),
   'color_51':node('Lerp',[('A','flat_2'),('B','scan_9')],const_alpha=.15)},
   'outputs':{'NORMAL':['normalize_14',''],'BASE_COLOR':['color_51',''],'ROUGHNESS':None},
   'settings':{'naniteUsage':True},'normalMix':'mix_83','textureAssets':['same-texture'],'textureAssetHashes':{'texture':'unchanged'}}
 def renamed(self,g):
  g=copy.deepcopy(g);names={n:'different_'+str(i+500) for i,n in enumerate(reversed(g['nodes']))}
  for n in g['nodes'].values():
   for v in n['inputs']:
    if v['node'] is not None:v['node']=names[v['node']]
  for v in g['outputs'].values():
   if v is not None:v[0]=names[v[0]]
  g['normalMix']=names[g['normalMix']];g['nodes']={names[n]:v for n,v in reversed(list(g['nodes'].items()))};g['outputs']=dict(reversed(list(g['outputs'].items())));return g
 def test_transient_names_and_storage_order_only(self):
  source=self.raw();original=copy.deepcopy(source);after=self.renamed(source)
  self.assertEqual(p.canonical_graph(source),p.canonical_graph(after));self.assertEqual(source,original)
  after['nodes'][after['normalMix']]['properties']['const_alpha']=.5
  self.assertTrue(p.assert_only_normal_changed(p.canonical_graph(source),p.canonical_graph(after)))
 def test_preserve_properties_channels_aliasing_and_multiplicity(self):
  for change in ('property','input-channel','output-channel','merge-equal-nodes','split-shared-node','texture','wrong-normal-role'):
   with self.subTest(change=change):
    source=self.raw();after=copy.deepcopy(source);after['nodes']['mix_83']['properties']['const_alpha']=.5
    if change=='property':after['nodes']['color_51']['properties']['const_alpha']=.2
    elif change=='input-channel':after['nodes']['mix_83']['inputs'][1]['output']='R'
    elif change=='output-channel':after['outputs']['BASE_COLOR'][1]='R'
    elif change=='merge-equal-nodes':after['nodes']['scan_9']['inputs'][1]['node']='size_5';del after['nodes']['size_6']
    elif change=='split-shared-node':after['nodes']['flat_copy']=copy.deepcopy(after['nodes']['flat_2']);after['nodes']['color_51']['inputs'][0]['node']='flat_copy'
    elif change=='texture':after['textureAssetHashes']['texture']='changed'
    else:after['normalMix']='color_51'
    with self.assertRaises(RuntimeError):p.assert_only_normal_changed(p.canonical_graph(source),p.canonical_graph(after))
 def test_reject_disconnected_dangling_cycle_and_duplicate_pin(self):
  for change in ('disconnected','dangling','cycle','duplicate-pin','missing-normal'):
   with self.subTest(change=change):
    g=self.raw()
    if change=='disconnected':g['nodes']['extra']=copy.deepcopy(g['nodes']['flat_2'])
    elif change=='dangling':g['nodes']['mix_83']['inputs'][0]['node']='missing'
    elif change=='cycle':g['nodes']['mix_83']['inputs'][0]['node']='normalize_14'
    elif change=='duplicate-pin':g['nodes']['mix_83']['inputs'][1]['pin']='A'
    else:g['normalMix']='missing'
    with self.assertRaises(RuntimeError):p.canonical_graph(g)

if __name__=='__main__':unittest.main()
